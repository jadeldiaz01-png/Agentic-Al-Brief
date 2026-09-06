import asyncio
from typing import Any

import pytest
from temporalio import workflow

from agentic_ai_brief.temporal_workflow import AgenticAIBriefWorkflow, DurableBriefRequest


def _request() -> DurableBriefRequest:
    return DurableBriefRequest(request_id="req-1", topic="agentic AI", source_sha="abc123")


def test_workflow_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def fake_execute_activity(name: str, payload: object, **kwargs: Any) -> object:
        del kwargs
        calls.append(name)
        if name == "research_activity":
            assert isinstance(payload, dict)
            return {"sources": ["source-1"]}
        if name == "verification_activity":
            return {"verified_claims": ["claim-1"]}
        if name == "policy_activity":
            return {"allowed": True, "decision_id": "policy-1"}
        if name == "persist_brief_activity":
            assert isinstance(payload, dict)
            return {"brief_id": "brief-1", "persisted": True}
        raise AssertionError(name)

    monkeypatch.setattr(workflow, "execute_activity", fake_execute_activity)
    result = asyncio.run(AgenticAIBriefWorkflow().run(_request()))
    assert result == {"brief_id": "brief-1", "persisted": True}
    assert calls == [
        "research_activity",
        "verification_activity",
        "policy_activity",
        "persist_brief_activity",
    ]


def test_workflow_policy_deny_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_execute_activity(name: str, payload: object, **kwargs: Any) -> object:
        del payload, kwargs
        if name == "research_activity":
            return {"sources": []}
        if name == "verification_activity":
            return {"verified_claims": []}
        if name == "policy_activity":
            return {"allowed": False}
        raise AssertionError("persistence must not execute after policy denial")

    monkeypatch.setattr(workflow, "execute_activity", fake_execute_activity)
    with pytest.raises(RuntimeError, match="POLICY_DENY"):
        asyncio.run(AgenticAIBriefWorkflow().run(_request()))


def test_workflow_rejects_invalid_persist_result(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_execute_activity(name: str, payload: object, **kwargs: Any) -> object:
        del payload, kwargs
        if name == "research_activity":
            return {"sources": []}
        if name == "verification_activity":
            return {"verified_claims": []}
        if name == "policy_activity":
            return {"allowed": True}
        if name == "persist_brief_activity":
            return "not-a-dict"
        raise AssertionError(name)

    monkeypatch.setattr(workflow, "execute_activity", fake_execute_activity)
    with pytest.raises(TypeError, match="INVALID_ACTIVITY_RESULT"):
        asyncio.run(AgenticAIBriefWorkflow().run(_request()))
