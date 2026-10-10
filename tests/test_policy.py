from agentic_ai_brief.policy import ToolIntent, evaluate_tool_intent


def intent(**overrides):
    params = dict(
        tool_name="web_search",
        read_only=True,
        external_write=False,
        financial=False,
        identity_or_legal=False,
        requires_human_approval=False,
        source_trust="verified",
        human_approval_verified=False,
    )
    params.update(overrides)
    return ToolIntent(**params)


def test_read_only_verified_tool_allowed() -> None:
    assert evaluate_tool_intent(intent()).allowed is True


def test_untrusted_tool_denied() -> None:
    decision = evaluate_tool_intent(intent(source_trust="untrusted"))
    assert decision.allowed is False
    assert "untrusted_tool_source" in decision.reasons


def test_trusted_but_unverified_tool_denied_matches_rego() -> None:
    assert evaluate_tool_intent(intent(source_trust="trusted")).allowed is False


def test_external_write_without_approval_denied() -> None:
    decision = evaluate_tool_intent(intent(tool_name="publish", read_only=False, external_write=True))
    assert decision.allowed is False
    assert "external_write_without_approval" in decision.reasons


def test_claimed_human_approval_still_cannot_grant_write() -> None:
    decision = evaluate_tool_intent(intent(
        tool_name="publish", read_only=False, external_write=True,
        requires_human_approval=True, human_approval_verified=True,
    ))
    assert decision.allowed is False
    assert "external_write_blocked_until_external_approval_adapter" in decision.reasons


def test_required_flag_is_not_a_human_approval() -> None:
    decision = evaluate_tool_intent(intent(
        read_only=False, external_write=True, requires_human_approval=True,
    ))
    assert decision.allowed is False
    assert "external_write_without_verified_human_approval" in decision.reasons


def test_non_read_only_tool_cannot_hide_as_non_write() -> None:
    assert evaluate_tool_intent(intent(read_only=False, external_write=False)).allowed is False


def test_inconsistent_read_only_plus_external_write_denied() -> None:
    assert evaluate_tool_intent(intent(read_only=True, external_write=True)).allowed is False


def test_financial_and_identity_actions_denied() -> None:
    assert evaluate_tool_intent(intent(financial=True)).allowed is False
    assert evaluate_tool_intent(intent(identity_or_legal=True)).allowed is False
