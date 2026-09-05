from agentic_ai_brief.policy import ToolIntent, evaluate_tool_intent


def test_read_only_verified_tool_allowed() -> None:
    decision = evaluate_tool_intent(
        ToolIntent(
            tool_name="web_search",
            read_only=True,
            external_write=False,
            financial=False,
            identity_or_legal=False,
            requires_human_approval=False,
            source_trust="verified",
        )
    )
    assert decision.allowed is True


def test_untrusted_tool_denied() -> None:
    decision = evaluate_tool_intent(
        ToolIntent(
            tool_name="mcp_unknown",
            read_only=True,
            external_write=False,
            financial=False,
            identity_or_legal=False,
            requires_human_approval=False,
            source_trust="untrusted",
        )
    )
    assert decision.allowed is False
    assert "untrusted_tool_source" in decision.reasons


def test_external_write_without_approval_denied() -> None:
    decision = evaluate_tool_intent(
        ToolIntent(
            tool_name="publish",
            read_only=False,
            external_write=True,
            financial=False,
            identity_or_legal=False,
            requires_human_approval=False,
            source_trust="verified",
        )
    )
    assert decision.allowed is False
    assert "external_write_without_approval" in decision.reasons
