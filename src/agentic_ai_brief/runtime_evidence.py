from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

REQUIRED_RUNTIME_GATES = (
    "postgresql_pitr_verified",
    "openbao_workload_identity_verified",
    "opa_fail_closed_verified",
    "temporal_replay_verified",
    "otel_trace_roundtrip_verified",
    "crash_recovery_verified",
    "artifact_signature_verified",
    "sbom_verified",
    "slsa_provenance_verified",
)


@dataclass(frozen=True)
class RuntimeCertificate:
    source_sha: str
    decision: str
    blockers: tuple[str, ...]
    evidence_sha256: str


def canonical_sha256(value: dict[str, Any]) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(data).hexdigest()


def certify_runtime_bundle(bundle: dict[str, Any], expected_sha: str) -> RuntimeCertificate:
    blockers: list[str] = []
    source_sha = str(bundle.get("source_sha", ""))
    if source_sha != expected_sha:
        blockers.append("source_sha_mismatch")

    evidence = bundle.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
        blockers.append("evidence_missing")

    for gate in REQUIRED_RUNTIME_GATES:
        item = evidence.get(gate)
        if not isinstance(item, dict) or item.get("verified") is not True:
            blockers.append(gate)
            continue
        ref = item.get("evidence_ref")
        if not isinstance(ref, str) or not ref.startswith("sha256:") or len(ref) != 71:
            blockers.append(f"{gate}:invalid_evidence_ref")

    decision = "RUNTIME_VERIFIED" if not blockers else "NO_GO"
    return RuntimeCertificate(
        source_sha=source_sha,
        decision=decision,
        blockers=tuple(blockers),
        evidence_sha256=canonical_sha256(bundle),
    )
