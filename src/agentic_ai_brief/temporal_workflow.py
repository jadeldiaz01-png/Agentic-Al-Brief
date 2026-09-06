from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow


@dataclass(frozen=True)
class DurableBriefRequest:
    request_id: str
    topic: str
    source_sha: str


@workflow.defn(name="AgenticAIBriefWorkflow")
class AgenticAIBriefWorkflow:
    @workflow.run
    async def run(self, request: DurableBriefRequest) -> dict[str, Any]:
        research = await workflow.execute_activity(
            "research_activity",
            asdict(request),
            start_to_close_timeout=timedelta(minutes=10),
        )
        verified = await workflow.execute_activity(
            "verification_activity",
            research,
            start_to_close_timeout=timedelta(minutes=10),
        )
        policy = await workflow.execute_activity(
            "policy_activity",
            verified,
            start_to_close_timeout=timedelta(minutes=2),
        )
        if not isinstance(policy, dict) or policy.get("allowed") is not True:
            raise RuntimeError("POLICY_DENY")
        result = await workflow.execute_activity(
            "persist_brief_activity",
            {"request": asdict(request), "verified": verified, "policy": policy},
            start_to_close_timeout=timedelta(minutes=5),
        )
        if not isinstance(result, dict):
            raise RuntimeError("INVALID_ACTIVITY_RESULT")
        return result
