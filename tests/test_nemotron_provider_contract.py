"""Offline provider contracts. Nothing in this suite contacts NVIDIA."""
import json
from pathlib import Path

import pytest

from agentic_ai_brief import nemotron_provider as provider


class DummyClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.fixture
def isolated(monkeypatch):
    traces = []
    monkeypatch.setattr(provider, "AsyncOpenAI", DummyClient)
    monkeypatch.setattr(provider, "OpenAIChatCompletionsModel", DummyModel)
    monkeypatch.setattr(provider, "set_tracing_disabled", lambda value: traces.append(value))
    return traces


def test_default_route_preserved(isolated):
    route = provider.select_primary_model({})
    assert route.provider == "openai"
    assert route.model == provider.LEGACY_MODEL_ID
    assert isolated == []


@pytest.mark.parametrize("key", ["", "synthetic-test-value"])
def test_nvidia_activation_denied_even_with_key(isolated, key):
    with pytest.raises(provider.ProviderConfigurationError, match="NVIDIA_ACTIVATION_BLOCKED"):
        provider.select_primary_model({
            "AGIA_PRIMARY_LLM_PROVIDER": "nvidia",
            "NVIDIA_API_KEY": key,
        })
    assert isolated == []


def test_non_authorized_provider_denied(isolated):
    with pytest.raises(provider.ProviderConfigurationError):
        provider.select_primary_model({"AGIA_PRIMARY_LLM_PROVIDER": "unknown"})
    assert isolated == []


def test_private_constructor_contract_is_offline_only(isolated):
    route = provider._prepare_nvidia_model({
        "NVIDIA_API_KEY": "synthetic-test-value"
    })
    assert route.model.kwargs["model"] == provider.NEMOTRON_MODEL_ID
    assert route.model.kwargs["openai_client"].kwargs["base_url"] == provider.NVIDIA_BASE_URL
    assert route.model_settings.max_tokens == 4096
    assert isolated == [True]


@pytest.mark.parametrize("env", [
    {},
    {"NVIDIA_API_KEY": ""},
    {"NVIDIA_API_KEY": "PLACEHOLDER"},
    {"NVIDIA_API_KEY": "synthetic", "AGIA_NVIDIA_MODEL": "not-allowed"},
    {"NVIDIA_API_KEY": "synthetic", "AGIA_NVIDIA_BASE_URL": "http://localhost"},
])
def test_private_constructor_checks_credentials_and_allowlist(isolated, env):
    with pytest.raises(provider.ProviderConfigurationError):
        provider._prepare_nvidia_model(env)
    assert isolated == []


def test_role_based_thinking_and_safe_parameters():
    for role in ("research", "verifier", "supervisor", "writer"):
        settings = provider.nemotron_settings(role)
        template = settings.extra_body["chat_template_kwargs"]
        assert template["force_nonempty_content"] is True
        assert template["enable_thinking"] is (role in ("research", "verifier"))
        assert template.get("medium_effort", False) is (role in ("research", "verifier"))
        assert "reasoning_budget" not in settings.extra_body
        assert "reasoning_effort" not in settings.extra_body
        assert settings.max_tokens == 4096


def test_unapproved_role_denied():
    with pytest.raises(provider.ProviderConfigurationError):
        provider.nemotron_settings("administrator")


def test_canonical_manifest_remains_locked():
    data = json.loads(Path("config/nemotron-3-ultra-primary.json").read_text())
    assert data["repository"] == "jadeldiaz01-png/Agentic-Al-Brief"
    assert data["production_authorized"] is False
    assert data["max_autonomous_capital_usd"] == 0
    assert data["activation_status"] == "PREPARE_ONLY_CODE_LOCKED"
    assert data["activation_switch"] == "UNAVAILABLE_IN_THIS_REVISION"
    assert data["auto_fallback"] is False
    assert provider.NEMOTRON_ACTIVATION_LOCKED is True
