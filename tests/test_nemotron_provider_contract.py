"""Offline provider tests; no real network or credentials."""
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


def test_default_remains_disabled(isolated):
    route = provider.select_primary_model({})
    assert route.provider == "openai"
    assert route.model == provider.LEGACY_MODEL_ID
    assert isolated == []


def test_explicit_nvidia_uses_pinned_model(isolated):
    route = provider.select_primary_model({
        "AGIA_PRIMARY_LLM_PROVIDER": "nvidia", "NVIDIA_API_KEY": "synthetic-test-value"
    })
    assert route.provider == "nvidia"
    assert route.model.kwargs["model"] == provider.NEMOTRON_MODEL_ID
    assert route.model.kwargs["openai_client"].kwargs["base_url"] == provider.NVIDIA_BASE_URL
    assert route.model_settings.max_tokens == 4096
    assert isolated == [True]


@pytest.mark.parametrize("env", [
    {"AGIA_PRIMARY_LLM_PROVIDER": "nvidia"},
    {"AGIA_PRIMARY_LLM_PROVIDER": "nvidia", "NVIDIA_API_KEY": ""},
    {"AGIA_PRIMARY_LLM_PROVIDER": "nvidia", "NVIDIA_API_KEY": "PLACEHOLDER"},
    {"AGIA_PRIMARY_LLM_PROVIDER": "other"},
    {"AGIA_PRIMARY_LLM_PROVIDER": "nvidia", "NVIDIA_API_KEY": "sample", "AGIA_NVIDIA_MODEL": "different"},
    {"AGIA_PRIMARY_LLM_PROVIDER": "nvidia", "NVIDIA_API_KEY": "sample", "AGIA_NVIDIA_BASE_URL": "http://localhost"},
])
def test_invalid_configuration_rejected(isolated, env):
    with pytest.raises(provider.ProviderConfigurationError):
        provider.select_primary_model(env)
    assert isolated == []


def test_canonical_manifest_is_not_activated():
    data = json.loads(Path("config/nemotron-3-ultra-primary.json").read_text())
    assert data["repository"] == "jadeldiaz01-png/Agentic-Al-Brief"
    assert data["production_authorized"] is False
    assert data["max_autonomous_capital_usd"] == 0
    assert data["activation_status"] == "PREPARE_ONLY_DISABLED"
    assert data["auto_fallback"] is False
