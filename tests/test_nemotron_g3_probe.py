"""Offline G3 tests: synthetic client responses only; no network or credentials."""
import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentic_ai_brief import nemotron_g3_probe as g3


def response(text="NVIDIA_G3_OK", model=g3.NEMOTRON_MODEL_ID, inp=18, out=8, finish="stop"):
    return SimpleNamespace(
        model=model,
        choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason=finish)],
        usage=SimpleNamespace(prompt_tokens=inp, completion_tokens=out, total_tokens=inp + out),
    )


def fixture_quote():
    # Zero rates are synthetic unit-test fixtures; NOT NVIDIA billing evidence.
    return g3.G3PricingQuote(Decimal(0), Decimal(0), "SYNTHETIC_TEST_ONLY")


def test_source_lock_blocks_before_credentials_and_client(monkeypatch):
    monkeypatch.setattr(g3, "OpenAI", lambda **kwargs: pytest.fail("Network client forbidden"))
    with pytest.raises(g3.G3ProbeDenied, match="G3_SOURCE_LOCKED"):
        g3.run_authenticated_probe(credential="synthetic-test-key", quote=fixture_quote())
    assert g3.G3_AUTHENTICATED_PROBE_LOCKED is True
    assert g3.G3_MAX_AUTONOMOUS_SPEND_USD == Decimal(0)


def test_request_is_fixed_one_call_no_tools_and_output_limited():
    request = g3.fixed_request()
    assert request["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert request["messages"] == [{"role": "user", "content": g3.G3_FIXED_PROMPT}]
    assert request["max_tokens"] == 64 and request["stream"] is False
    assert "tools" not in request and "response_format" not in request
    assert request["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False
    assert g3.G3_MAX_CALLS == 1


@pytest.mark.parametrize("rate1,rate2,expected", [
    ("0", "0", Decimal("0.000000")),
    ("1", "1", Decimal("0.000192")),
    ("2", "3", Decimal("0.000448")),
])
def test_conservative_cost_quote(rate1, rate2, expected):
    quote = g3.G3PricingQuote(Decimal(rate1), Decimal(rate2), "SYNTHETIC")
    assert g3.estimate_quoted_max_usd(quote) == expected


@pytest.mark.parametrize("rate1,rate2,source", [
    ("NaN", "0", "test"), ("Infinity", "0", "test"),
    ("-1", "0", "test"), ("0", "-1", "test"),
    ("0", "0", ""), ("0", "0", " "),
])
def test_invalid_pricing_is_rejected(rate1, rate2, source):
    quote = g3.G3PricingQuote(Decimal(rate1), Decimal(rate2), source)
    with pytest.raises(g3.G3ProbeDenied):
        g3.estimate_quoted_max_usd(quote)


@pytest.mark.parametrize("bad", [
    response(text="unexpected"),
    response(model="other"),
    response(inp=129),
    response(out=65),
    response(finish="length"),
    SimpleNamespace(model=g3.NEMOTRON_MODEL_ID, choices=[], usage=None),
    SimpleNamespace(model=g3.NEMOTRON_MODEL_ID, choices=[SimpleNamespace()], usage=None),
])
def test_bad_provider_result_fails_closed(bad):
    with pytest.raises(g3.G3ProbeDenied):
        g3.validate_response(bad)


def test_good_fake_response_emits_only_sanitized_usage():
    evidence = g3.validate_response(response())
    assert evidence == {
        "status": "PASS", "request_count": 1,
        "prompt_tokens": 18, "completion_tokens": 8, "total_tokens": 26,
    }
    assert "NVIDIA_G3_OK" not in str(evidence)


def test_positive_spend_blocks_client_even_in_simulated_unlocked_path(monkeypatch):
    monkeypatch.setattr(g3, "G3_AUTHENTICATED_PROBE_LOCKED", False)
    monkeypatch.setattr(g3, "OpenAI", lambda **kwargs: pytest.fail("Client must not be called"))
    price = g3.G3PricingQuote(Decimal(1), Decimal(1), "SYNTHETIC")
    with pytest.raises(g3.G3ProbeDenied, match="G3_COST_NOT_AUTHORIZED"):
        g3.run_authenticated_probe(credential="synthetic-key", quote=price)


def test_single_synthetic_call_no_retries_and_no_secret_in_evidence(monkeypatch):
    created, calls = [], []
    class FakeClient:
        def __init__(self, **kwargs):
            created.append(kwargs)
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def create(self, **kwargs):
            calls.append(kwargs)
            return response()
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
    monkeypatch.setattr(g3, "G3_AUTHENTICATED_PROBE_LOCKED", False)
    monkeypatch.setattr(g3, "OpenAI", FakeClient)
    data = g3.run_authenticated_probe(credential="synthetic-key", quote=fixture_quote())
    assert data["status"] == "PASS" and len(calls) == len(created) == 1
    assert created[0]["max_retries"] == 0 and created[0]["timeout"] == 45.0
    assert created[0]["base_url"] == "https://integrate.api.nvidia.com/v1"
    assert calls[0] == g3.fixed_request()
    assert "synthetic-key" not in str(data)


def test_provider_errors_hide_exception_payload(monkeypatch):
    class FakeBadClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def create(self, **kwargs):
            raise RuntimeError("synthetic-key private provider response")
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
    monkeypatch.setattr(g3, "G3_AUTHENTICATED_PROBE_LOCKED", False)
    monkeypatch.setattr(g3, "OpenAI", FakeBadClient)
    with pytest.raises(g3.G3ProbeDenied) as denied:
        g3.run_authenticated_probe(credential="synthetic-key", quote=fixture_quote())
    assert str(denied.value) == "G3_PROVIDER_OR_NETWORK_DENIED"
    assert denied.value.__cause__ is None


def test_g3_manifest_is_not_live():
    data = json.loads(Path("config/nvidia-g3-inference-probe.json").read_text())
    assert data["mode"] == "G3_PREPARE_ONLY_SOURCE_LOCKED"
    assert data["g3_source_locked"] is True
    assert data["actual_pricing_verified"] is False
    assert data["authenticated_inference_authorized"] is False
    assert data["max_calls"] == g3.G3_MAX_CALLS
    assert data["max_output_tokens"] == g3.G3_MAX_OUTPUT_TOKENS
    assert data["max_quote_input_tokens"] == g3.G3_QUOTED_INPUT_TOKENS
    assert data["max_autonomous_spend_usd"] == "0"
    assert data["fallback_to_openai"] is False
