"""Tests the same strict schema validator the SDK uses for writer output.

These fixtures do NOT certify NVIDIA's real JSON/tool-calling compatibility.
"""
import pytest
from agents.agent_output import AgentOutputSchema
from agents.exceptions import ModelBehaviorError

from agentic_ai_brief.domain import BriefResult


@pytest.mark.parametrize("payload", [
    "not JSON",
    "[]",
    "{}",
    '{"request":{"topic":"valid topic"},"claims":[],"sources":[]}',
    '{"request":{"topic":"valid topic"},"claims":[{"claim_id":"c1","text":"claim","confidence":2.0,"evidence_kind":"fact"}],"sources":[],"policy_decision_id":"a"}',
    '{"request":{"topic":"valid topic"},"claims":[],"sources":[{"source_id":"s1","url":"not a URL","title":"t","publisher":"p","kind":"fact","content_sha256":"short"}],"policy_decision_id":"a"}',
])
def test_invalid_provider_payload_never_becomes_brief(payload: str) -> None:
    schema = AgentOutputSchema(BriefResult)
    with pytest.raises(ModelBehaviorError):
        schema.validate_json(payload)


def test_nemotron_writer_uses_sdk_structured_output_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    from agentic_ai_brief import agent_runtime
    agents = agent_runtime.build_agents()
    assert agents["writer"].output_type is BriefResult
