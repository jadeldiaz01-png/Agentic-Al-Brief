"""Execute the exact Rego policy in OPA and compare with the Python guard.

OPA v1.9.0 is installed by CI with a SHA256-pinned official binary.
No mock evaluator, simulated Rego engine, secret, or provider request is used.
"""
import json
import subprocess

import pytest

from agentic_ai_brief.policy import ToolIntent, evaluate_tool_intent

OPA_QUERY = "data.agentic_ai_brief.tool_authorization.allow"
BASE = {
    "tool_name": "web_search",
    "read_only": True,
    "external_write": False,
    "financial": False,
    "identity_or_legal": False,
    "requires_human_approval": False,
    "source_trust": "verified",
    "human_approval_verified": False,
}


def python_allows(payload: dict[str, object]) -> bool:
    try:
        return evaluate_tool_intent(ToolIntent(**payload)).allowed
    except (TypeError, ValueError):
        return False


def rego_allows(payload: dict[str, object]) -> bool:
    process = subprocess.run(
        [
            "opa", "eval", "--data", "policy/tool_authorization.rego",
            "--input", "/dev/stdin", "--format", "raw", OPA_QUERY,
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        timeout=15,
    )
    result = process.stdout.strip()
    assert result in {"true", "false"}, f"Unexpected OPA result: {result!r}"
    return result == "true"


CASE_INPUTS = [
    ("baseline", {}),
    ("approved_read_only", {"requires_human_approval": True, "human_approval_verified": True}),
    ("optional_approval_default", {"__omit_human_approval_verified__": True}),
    ("untrusted", {"source_trust": "untrusted"}),
    ("trusted_not_verified", {"source_trust": "trusted"}),
    ("blank_name", {"tool_name": ""}),
    ("write_no_approval", {"read_only": False, "external_write": True}),
    ("write_claimed_approved", {"read_only": False, "external_write": True,
                                "requires_human_approval": True, "human_approval_verified": True}),
    ("non_read_only", {"read_only": False}),
    ("inconsistent_read_only_write", {"external_write": True}),
    ("financial", {"financial": True}),
    ("identity_or_legal", {"identity_or_legal": True}),
]
for field in (
    "read_only", "external_write", "financial", "identity_or_legal",
    "requires_human_approval", "human_approval_verified",
):
    for value in ("false", "true", 0, 1, None, [], {}):
        CASE_INPUTS.append((f"bad_{field}_{type(value).__name__}_{str(value)}", {field: value}))
for field in (
    "tool_name", "read_only", "external_write", "financial",
    "identity_or_legal", "requires_human_approval", "source_trust",
):
    CASE_INPUTS.append((f"missing_{field}", {f"__omit_{field}__": True}))
for field in ("tool_name", "source_trust"):
    for value in (None, True, 1, [], {}):
        CASE_INPUTS.append((f"bad_{field}_{type(value).__name__}", {field: value}))


@pytest.mark.parametrize("name,changes", CASE_INPUTS, ids=[x[0] for x in CASE_INPUTS])
def test_real_opa_and_python_policy_are_equivalent(name: str, changes: dict[str, object]) -> None:
    payload: dict[str, object] = BASE.copy()
    for key, value in changes.items():
        if key.startswith("__omit_") and value is True:
            payload.pop(key.removeprefix("__omit_").removesuffix("__"), None)
        else:
            payload[key] = value
    py = python_allows(payload)
    rego = rego_allows(payload)
    assert py == rego, f"{name}: Python={py}, OPA={rego}, input={payload!r}"
    assert py is (name in {"baseline", "approved_read_only", "optional_approval_default"}), name
