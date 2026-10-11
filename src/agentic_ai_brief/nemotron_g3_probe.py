"""G3 PREPARE_ONLY single-request NVIDIA probe, with a mandatory source lock."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from typing import Any

from openai import OpenAI

from .nemotron_provider import NEMOTRON_MODEL_ID, NVIDIA_BASE_URL

G3_AUTHENTICATED_PROBE_LOCKED = True
# Additional source-controlled gates; never infer approval from API-key presence.
G3_BILLING_CERTIFICATION_LOCKED = True
G3_EXECUTION_APPROVAL_LOCKED = True
G3_MAX_CALLS = 1
G3_QUOTED_INPUT_TOKENS = 128  # Quote only: NOT a tokenizer-enforced maximum.
G3_MAX_OUTPUT_TOKENS = 64
G3_MAX_AUTONOMOUS_SPEND_USD = Decimal(0)
G3_TIMEOUT_SECONDS = 45.0
G3_FIXED_PROMPT = "Reply with exactly NVIDIA_G3_OK and no other text."
G3_EXPECTED = "NVIDIA_G3_OK"


class G3ProbeDenied(RuntimeError):
    """Redacted error. Never include a provider exception, body, or credential."""


@dataclass(frozen=True)
class G3PricingQuote:
    """Caller-provided evidence metadata; NOT a certificate of real pricing."""
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal
    pricing_evidence_reference: str


def estimate_quoted_max_usd(quote: G3PricingQuote) -> Decimal:
    """Conservative price quote; token estimates are not hard billing limits."""
    if not isinstance(quote, G3PricingQuote):
        raise G3ProbeDenied("G3_PRICE_QUOTE_REQUIRED")
    if not isinstance(quote.pricing_evidence_reference, str) or not quote.pricing_evidence_reference.strip():
        raise G3ProbeDenied("G3_PRICING_EVIDENCE_REQUIRED")
    for value in (quote.input_usd_per_million, quote.output_usd_per_million):
        if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
            raise G3ProbeDenied("G3_PRICE_INVALID")
    estimate = (
        Decimal(G3_QUOTED_INPUT_TOKENS) * quote.input_usd_per_million
        + Decimal(G3_MAX_OUTPUT_TOKENS) * quote.output_usd_per_million
    ) / Decimal(1_000_000)
    return estimate.quantize(Decimal("0.000001"), rounding=ROUND_CEILING)


def fixed_request() -> dict[str, Any]:
    """Static synthetic prompt; no customer data, tool calls, or dynamic content."""
    return {
        "model": NEMOTRON_MODEL_ID,
        "messages": [{"role": "user", "content": G3_FIXED_PROMPT}],
        "temperature": 1.0,
        "top_p": 0.95,
        "max_tokens": G3_MAX_OUTPUT_TOKENS,
        "stream": False,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False,
                "force_nonempty_content": True,
            }
        },
    }


def validate_response(result: Any) -> dict[str, int | str]:
    """Validate an SDK completion without returning its raw text or metadata."""
    try:
        if result.model != NEMOTRON_MODEL_ID:
            raise G3ProbeDenied("G3_MODEL_MISMATCH")
        if not isinstance(result.choices, list) or len(result.choices) != 1:
            raise G3ProbeDenied("G3_RESPONSE_INVALID")
        choice = result.choices[0]
        if not isinstance(choice.message.content, str) or choice.message.content.strip() != G3_EXPECTED:
            raise G3ProbeDenied("G3_RESPONSE_CONTENT_INVALID")
        if choice.finish_reason != "stop":
            raise G3ProbeDenied("G3_RESPONSE_INCOMPLETE")
        prompt_tokens = result.usage.prompt_tokens
        completion_tokens = result.usage.completion_tokens
        total_tokens = result.usage.total_tokens
    except (AttributeError, IndexError, KeyError, TypeError):
        raise G3ProbeDenied("G3_RESPONSE_INVALID") from None
    if any(type(value) is not int or value <= 0 for value in (prompt_tokens, completion_tokens, total_tokens)):
        raise G3ProbeDenied("G3_USAGE_INVALID")
    if (
        prompt_tokens > G3_QUOTED_INPUT_TOKENS
        or completion_tokens > G3_MAX_OUTPUT_TOKENS
        or total_tokens != prompt_tokens + completion_tokens
    ):
        raise G3ProbeDenied("G3_USAGE_OUT_OF_BOUNDS")
    return {
        "status": "PASS",
        "request_count": G3_MAX_CALLS,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def run_authenticated_probe(*, credential: str, quote: G3PricingQuote) -> dict[str, int | str]:
    """Must never run live on this revision, regardless of env or key presence."""
    if G3_AUTHENTICATED_PROBE_LOCKED:
        raise G3ProbeDenied("G3_SOURCE_LOCKED")
    if G3_BILLING_CERTIFICATION_LOCKED:
        raise G3ProbeDenied("G3_BILLING_NOT_CERTIFIED")
    if G3_EXECUTION_APPROVAL_LOCKED:
        raise G3ProbeDenied("G3_EXECUTION_NOT_AUTHORIZED")
    # Even after independent promotion, a caller-supplied zero-price quote
    # alone is not billing proof: certified account-level controls are required.
    if estimate_quoted_max_usd(quote) > G3_MAX_AUTONOMOUS_SPEND_USD:
        raise G3ProbeDenied("G3_COST_NOT_AUTHORIZED")
    if not isinstance(credential, str) or not credential.strip():
        raise G3ProbeDenied("G3_CREDENTIAL_ABSENT")
    try:
        with OpenAI(
            base_url=NVIDIA_BASE_URL, api_key=credential,
            timeout=G3_TIMEOUT_SECONDS, max_retries=0,
        ) as client:
            result = client.chat.completions.create(**fixed_request())
        return validate_response(result)
    except G3ProbeDenied:
        raise
    except Exception:  # noqa: BLE001 - sanitize arbitrary SDK exceptions before logging
        raise G3ProbeDenied("G3_PROVIDER_OR_NETWORK_DENIED") from None
