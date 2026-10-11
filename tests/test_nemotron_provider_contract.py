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


def test_private_client_constructor_is_locked_even_with_valid_credentials(isolated):
    with pytest.raises(provider.ProviderConfigurationError, match="NVIDIA_ACTIVATION_BLOCKED"):
        provider._prepare_nvidia_model({
            "NVIDIA_API_KEY": "synthetic-test-value",
            "AGIA_NVIDIA_MODEL": provider.NEMOTRON_MODEL_ID,
            "AGIA_NVIDIA_BASE_URL": provider.NVIDIA_BASE_URL,
            "AGIA_PRIMARY_LLM_PROVIDER": "nvidia",
        })
    assert isolated == []


@pytest.mark.parametrize("override", [
    {},
    {"AGIA_NVIDIA_APPROVED": "true"},
    {"PRODUCTION_AUTHORIZED": "true"},
    {"AGIA_NVIDIA_RUNTIME_CERTIFIED": "true"},
])
def test_environment_flags_cannot_activate_nvidia_client(isolated, override):
    env = {"NVIDIA_API_KEY": "synthetic-test-value", "AGIA_PRIMARY_LLM_PROVIDER": "nvidia", **override}
    with pytest.raises(provider.ProviderConfigurationError, match="NVIDIA_ACTIVATION_BLOCKED"):
        provider.select_primary_model(env)
    with pytest.raises(provider.ProviderConfigurationError, match="NVIDIA_ACTIVATION_BLOCKED"):
        provider._prepare_nvidia_model(env)
    assert isolated == []


@pytest.mark.parametrize("env", [
    {},
    {"NVIDIA_API_KEY": ""},
    {"NVIDIA_API_KEY": "PLACEHOLDER"},
    {"NVIDIA_API_KEY": "synthetic", "AGIA_NVIDIA_MODEL": "not-allowed"},
    {"NVIDIA_API_KEY": "synthetic", "AGIA_NVIDIA_BASE_URL": "http://localhost"},
])
def test_private_constructor_is_closed_for_all_unverified_configs(isolated, env):
    with pytest.raises(provider.ProviderConfigurationError, match="NVIDIA_ACTIVATION_BLOCKED"):
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


def test_declarative_primary_and_secondary_never_construct_clients(isolated):
    plan = provider.describe_provider_routing()
    assert plan.target_primary == "nvidia"
    assert plan.target_primary_model == provider.NEMOTRON_MODEL_ID
    assert plan.target_secondary == "openai"
    assert plan.target_secondary_model == provider.LEGACY_MODEL_ID
    assert plan.runtime_default_while_locked == "openai"
    assert plan.primary_activation_locked is True
    assert plan.automatic_failover is False
    assert plan.secondary_promotion_requires_human_gate is True
    assert provider.AUTO_FAILOVER_ENABLED is False
    assert isolated == []


@pytest.mark.parametrize("flags", [
    {"AGIA_AUTO_FALLBACK": "openai"},
    {"AGIA_SECONDARY_LLM_PROVIDER": "openai"},
    {"AGIA_ALLOW_SECONDARY_ON_FAILURE": "true"},
    {"AGIA_NVIDIA_APPROVED": "true", "PRODUCTION_AUTHORIZED": "true"},
])
def test_unverified_nvidia_never_falls_back_to_openai(isolated, flags):
    # A failed NVIDIA request must fail closed, never silently use OpenAI.
    env = {
        "AGIA_PRIMARY_LLM_PROVIDER": "nvidia",
        "NVIDIA_API_KEY": "synthetic-test-value",
        **flags,
    }
    with pytest.raises(provider.ProviderConfigurationError, match="NVIDIA_ACTIVATION_BLOCKED"):
        provider.select_primary_model(env)
    assert isolated == []


def test_openai_is_explicit_interim_route_not_automatic_fallback(isolated):
    selection = provider.select_primary_model({"AGIA_PRIMARY_LLM_PROVIDER": "openai"})
    assert selection.provider == "openai"
    assert selection.model == provider.OPENAI_SECONDARY_MODEL_ID
    assert isolated == []


def test_manifest_provider_plan_preserves_prepare_only_and_no_fallback():
    data = json.loads(Path("config/nemotron-3-ultra-primary.json").read_text())
    plan = provider.describe_provider_routing()
    assert data["primary_provider_target"] == plan.target_primary
    assert data["primary_model_target"] == plan.target_primary_model
    assert data["secondary_provider_target"] == plan.target_secondary
    assert data["secondary_model_id"] == plan.target_secondary_model
    assert data["secondary_selection_policy"] == "EXPLICIT_HUMAN_GATE_NO_AUTOMATIC_FAILOVER"
    assert data["secondary_runtime_mode"] == "EXISTING_OPENAI_DEFAULT_UNTIL_NVIDIA_CERTIFIED"
    assert data["fallback_on_primary_failure"] is False
    assert data["auto_fallback"] is False
    assert data["runtime_provider_default"] == "openai"
    assert data["activation_status"] == "PREPARE_ONLY_CODE_LOCKED"
    assert data["production_authorized"] is False
    assert data["max_autonomous_capital_usd"] == 0
