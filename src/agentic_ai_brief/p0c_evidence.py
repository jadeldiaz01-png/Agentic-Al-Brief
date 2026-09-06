from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ARTIFACTS = {
    "runner_security_verified": "runner-security.json",
    "postgresql_pitr_verified": "postgresql-pitr.json",
    "openbao_workload_identity_verified": "openbao-identity.json",
    "opa_fail_closed_verified": "opa-enforcement.json",
    "temporal_replay_verified": "temporal-replay.json",
    "otel_trace_roundtrip_verified": "otel-roundtrip.json",
    "crash_recovery_verified": "crash-recovery.json",
    "artifact_signature_verified": "artifact-signature.json",
    "sbom_verified": "sbom-verification.json",
    "slsa_provenance_verified": "slsa-provenance-verification.json",
}

REQUIRED_ASSERTIONS = {
    "runner_security_verified": (
        "ephemeral_or_jit_verified",
        "single_job_lifecycle_verified",
        "pull_request_trigger_absent",
        "clean_execution_environment_verified",
        "external_runner_logs_verified",
    ),
    "postgresql_pitr_verified": (
        "wal_archiving_verified",
        "base_backup_verified",
        "restore_drill_verified",
        "restore_target_verified",
    ),
    "openbao_workload_identity_verified": (
        "service_account_auth_verified",
        "static_token_absent",
        "short_lived_credential_verified",
    ),
    "opa_fail_closed_verified": (
        "deny_case_verified",
        "allow_case_verified",
        "decision_id_present",
    ),
    "temporal_replay_verified": (
        "history_replay_verified",
        "workflow_completed_verified",
        "nondeterminism_absent",
    ),
    "otel_trace_roundtrip_verified": (
        "collector_health_verified",
        "synthetic_trace_exported",
        "backend_trace_observed",
    ),
    "crash_recovery_verified": (
        "activity_retry_verified",
        "worker_restart_verified",
        "duplicate_persistence_absent",
    ),
    "artifact_signature_verified": (
        "cosign_verify_passed",
        "oidc_identity_verified",
        "digest_verified",
    ),
    "sbom_verified": (
        "cyclonedx_schema_verified",
        "artifact_digest_bound",
    ),
    "slsa_provenance_verified": (
        "provenance_schema_verified",
        "subject_digest_verified",
        "source_sha_verified",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_verified(path: Path, gate: str, expected_sha: str, execution_id: str) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path.name}:INVALID_JSON_OBJECT")
    if raw.get("source_sha") != expected_sha:
        raise ValueError(f"{path.name}:SOURCE_SHA_MISMATCH")
    if raw.get("execution_id") != execution_id:
        raise ValueError(f"{path.name}:EXECUTION_ID_MISMATCH")
    if raw.get("verified") is not True:
        raise ValueError(f"{path.name}:NOT_VERIFIED")
    generated_at = raw.get("generated_at_utc")
    if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
        raise ValueError(f"{path.name}:INVALID_GENERATED_AT_UTC")
    lowered_keys = {str(key).lower() for key in raw}
    if lowered_keys & {"token", "password", "secret", "api_key", "private_key"}:
        raise ValueError(f"{path.name}:SECRET_MATERIAL_FORBIDDEN")
    assertions = raw.get("assertions")
    if not isinstance(assertions, dict):
        raise TypeError(f"{path.name}:ASSERTIONS_MISSING")
    for assertion in REQUIRED_ASSERTIONS[gate]:
        if assertions.get(assertion) is not True:
            raise ValueError(f"{path.name}:{assertion}:NOT_VERIFIED")
    return raw


def build_bundle(evidence_dir: Path, expected_sha: str, execution_id: str) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for gate, filename in ARTIFACTS.items():
        path = evidence_dir / filename
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"{filename}:MISSING_OR_UNSAFE")
        _load_verified(path, gate, expected_sha, execution_id)
        evidence[gate] = {
            "verified": True,
            "evidence_ref": f"sha256:{_sha256(path)}",
            "artifact": filename,
        }
    return {
        "schema_version": "1.1.0",
        "source_sha": expected_sha,
        "execution_id": execution_id,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence": evidence,
    }
