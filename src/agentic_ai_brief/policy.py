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
    # Runtime data can come from JSON, MCP or external tooling. Python type
    # hints are not runtime validators: "false", 0, [], and null must never
    # acquire boolean authority through truthiness.
    if not isinstance(intent, ToolIntent):
        return PolicyDecision(allowed=False, reasons=("invalid_tool_intent_schema",))
    if type(intent.tool_name) is not str or not intent.tool_name:
        return PolicyDecision(allowed=False, reasons=("invalid_tool_intent_schema",))
    if type(intent.source_trust) is not str:
        return PolicyDecision(allowed=False, reasons=("invalid_tool_intent_schema",))
    for key in (
        "read_only",
        "external_write",
        "financial",
        "identity_or_legal",
        "requires_human_approval",
        "human_approval_verified",
    ):
        if type(getattr(intent, key)) is not bool:
            return PolicyDecision(allowed=False, reasons=("invalid_tool_intent_schema",))

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
