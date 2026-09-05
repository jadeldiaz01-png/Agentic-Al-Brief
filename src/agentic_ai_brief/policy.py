from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolIntent:
    tool_name: str
    read_only: bool
    external_write: bool
    financial: bool
    identity_or_legal: bool
    requires_human_approval: bool
    source_trust: str


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_tool_intent(intent: ToolIntent) -> PolicyDecision:
    reasons: list[str] = []
    if intent.source_trust not in {"trusted", "verified"}:
        reasons.append("untrusted_tool_source")
    if intent.financial:
        reasons.append("financial_action_requires_separate_authorization")
    if intent.identity_or_legal:
        reasons.append("identity_or_legal_action_requires_human")
    if intent.external_write and not intent.requires_human_approval:
        reasons.append("external_write_without_approval")
    allowed = not reasons
    return PolicyDecision(allowed=allowed, reasons=tuple(reasons))
