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
    human_approval_verified: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_tool_intent(intent: ToolIntent) -> PolicyDecision:
    """Align with Rego: allow verified read-only tools; deny *all* writes.

    A bool or model statement cannot authenticate a real human approval.
    Write authority stays unavailable until an external verified approval
    adapter and a distinct human gate have been implemented and tested.
    """
    reasons: list[str] = []
    if intent.source_trust != "verified":
        reasons.append("untrusted_tool_source")
    if intent.financial:
        reasons.append("financial_action_requires_separate_authorization")
    if intent.identity_or_legal:
        reasons.append("identity_or_legal_action_requires_human")
    if not intent.read_only:
        reasons.append("non_read_only_tool_forbidden")
    if intent.external_write:
        if not intent.requires_human_approval:
            reasons.append("external_write_without_approval")
        elif not intent.human_approval_verified:
            reasons.append("external_write_without_verified_human_approval")
        reasons.append("external_write_blocked_until_external_approval_adapter")
    return PolicyDecision(allowed=not reasons, reasons=tuple(reasons))
