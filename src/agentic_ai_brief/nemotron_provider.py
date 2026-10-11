"""Governed NVIDIA Nemotron 3 Ultra adapter, permanently locked in this revision.

Operator variables and credentials are insufficient authority to activate a provider.
The lock may be lifted only in a separately reviewed source revision after runtime
certifications and human approvals. Importing this module never contacts NVIDIA.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from agents import ModelSettings, OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI

NEMOTRON_MODEL_ID = "nvidia/nemotron-3-ultra-550b-a55b"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
LEGACY_MODEL_ID = "gpt-5.6-luna"
NEMOTRON_ACTIVATION_LOCKED = True
NemotronRole = Literal["supervisor", "research", "verifier", "writer"]


class ProviderConfigurationError(ValueError):
    """A fail-closed error that must never contain credentials or prompt data."""


@dataclass(frozen=True)
class PrimaryModelSelection:
    provider: Literal["openai", "nvidia"]
    model: str | OpenAIChatCompletionsModel
    model_settings: ModelSettings | None


def nemotron_settings(role: NemotronRole = "research") -> ModelSettings:
    """Documented NVIDIA chat-template parameters; no unsupported budget keys.

    Constrained output and supervisor tools run with thinking disabled, given
    documented server-dependent JSON and required tool-call limitations.
    This is a candidate setting only, not certified against NVIDIA's API.
    """
    if role not in ("supervisor", "research", "verifier", "writer"):
        raise ProviderConfigurationError("Unsupported agent role")
    thinking = role in ("research", "verifier")
    template: dict[str, bool] = {
        "enable_thinking": thinking,
        "force_nonempty_content": True,
    }
    if thinking:
        template["medium_effort"] = True
    return ModelSettings(
        temperature=1.0,
        top_p=0.95,
        max_tokens=4096,
        extra_body={"chat_template_kwargs": template},
    )


def _prepare_nvidia_model(environ: Mapping[str, str]) -> PrimaryModelSelection:
    """Enforce source-controlled activation at the client-construction boundary.

    This entrypoint is deliberately locked even for a correct NVIDIA key,
    endpoint and environment selector. A future certified revision must
    implement a separate, externally verified authorization boundary.
    """
    if NEMOTRON_ACTIVATION_LOCKED:
        raise ProviderConfigurationError("NVIDIA_ACTIVATION_BLOCKED_PENDING_CERTIFICATION")
    if environ.get("AGIA_NVIDIA_MODEL", NEMOTRON_MODEL_ID) != NEMOTRON_MODEL_ID:
        raise ProviderConfigurationError("Unapproved NVIDIA model")
    if environ.get("AGIA_NVIDIA_BASE_URL", NVIDIA_BASE_URL) != NVIDIA_BASE_URL:
        raise ProviderConfigurationError("Unapproved NVIDIA endpoint")
    key = environ.get("NVIDIA_API_KEY", "").strip()
    if not key or key in ("YOUR_KEY", "CHANGE_ME", "PLACEHOLDER"):
        raise ProviderConfigurationError("NVIDIA_API_KEY missing")
    # SDK tracing is disabled for third-party data flows, not a runtime SLO proof.
    set_tracing_disabled(True)
    client = AsyncOpenAI(
        api_key=key,
        base_url=NVIDIA_BASE_URL,
        timeout=60.0,
        max_retries=0,
    )
    return PrimaryModelSelection(
        "nvidia",
        OpenAIChatCompletionsModel(model=NEMOTRON_MODEL_ID, openai_client=client),
        nemotron_settings(),
    )


def select_primary_model(
    environ: Mapping[str, str] | None = None,
) -> PrimaryModelSelection:
    """Never activate NVIDIA through an env var or secret alone."""
    env = os.environ if environ is None else environ
    provider = env.get("AGIA_PRIMARY_LLM_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return PrimaryModelSelection("openai", LEGACY_MODEL_ID, None)
    if provider != "nvidia":
        raise ProviderConfigurationError("Unknown primary LLM provider")
    if NEMOTRON_ACTIVATION_LOCKED:
        raise ProviderConfigurationError("NVIDIA_ACTIVATION_BLOCKED_PENDING_CERTIFICATION")
    return _prepare_nvidia_model(env)
