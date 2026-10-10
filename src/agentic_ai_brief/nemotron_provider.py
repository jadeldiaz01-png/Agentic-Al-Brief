"""Opt-in NVIDIA Nemotron 3 Ultra adapter; no network call on import.

Never activate by a model response, retrieved document or tool output.
Missing credentials and unapproved overrides fail closed.
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


class ProviderConfigurationError(ValueError):
    """Configuration error that never includes a secret value."""


@dataclass(frozen=True)
class PrimaryModelSelection:
    provider: Literal["openai", "nvidia"]
    model: str | OpenAIChatCompletionsModel
    model_settings: ModelSettings | None


def nemotron_settings() -> ModelSettings:
    """Pilot-only conservative limits; compatibility requires real staging proof."""
    return ModelSettings(
        temperature=1.0,
        max_tokens=4096,
        extra_body={
            "reasoning_effort": "medium",
            "reasoning_budget": 1024,
            "chat_template_kwargs": {"force_nonempty_content": True},
        },
    )


def select_primary_model(
    environ: Mapping[str, str] | None = None,
) -> PrimaryModelSelection:
    """Return a model only from an operator-controlled, approved allowlist.

    Default behavior preserves the pre-existing OpenAI route. Opting into
    NVIDIA requires a protected runtime credential. No silent fallback.
    """
    env = os.environ if environ is None else environ
    provider = env.get("AGIA_PRIMARY_LLM_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return PrimaryModelSelection("openai", LEGACY_MODEL_ID, None)
    if provider != "nvidia":
        raise ProviderConfigurationError("AGIA_PRIMARY_LLM_PROVIDER must be openai or nvidia")
    if env.get("AGIA_NVIDIA_MODEL", NEMOTRON_MODEL_ID) != NEMOTRON_MODEL_ID:
        raise ProviderConfigurationError("NVIDIA model override is not on the approved allowlist")
    if env.get("AGIA_NVIDIA_BASE_URL", NVIDIA_BASE_URL) != NVIDIA_BASE_URL:
        raise ProviderConfigurationError("NVIDIA endpoint override is not on the approved allowlist")
    key = env.get("NVIDIA_API_KEY", "").strip()
    if not key or key in ("YOUR_KEY", "CHANGE_ME", "PLACEHOLDER"):
        raise ProviderConfigurationError("NVIDIA_API_KEY missing; fail closed without fallback")
    # Third-party SDK calls must not export prompts or tool outputs to SDK tracing.
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
