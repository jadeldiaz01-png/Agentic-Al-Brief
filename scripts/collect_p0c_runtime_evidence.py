from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ARTIFACTS = {
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_verified(path: Path, expected_sha: str) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path.name}:INVALID_JSON_OBJECT")
    if raw.get("source_sha") != expected_sha:
        raise ValueError(f"{path.name}:SOURCE_SHA_MISMATCH")
    if raw.get("verified") is not True:
        raise ValueError(f"{path.name}:NOT_VERIFIED")
    generated_at = raw.get("generated_at_utc")
    if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
        raise ValueError(f"{path.name}:INVALID_GENERATED_AT_UTC")
    if any(key.lower() in {"token", "password", "secret", "api_key"} for key in raw):
        raise ValueError(f"{path.name}:SECRET_MATERIAL_FORBIDDEN")
    return raw


def build_bundle(evidence_dir: Path, expected_sha: str) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for gate, filename in ARTIFACTS.items():
        path = evidence_dir / filename
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"{filename}:MISSING_OR_UNSAFE")
        _load_verified(path, expected_sha)
        evidence[gate] = {
            "verified": True,
            "evidence_ref": f"sha256:{_sha256(path)}",
            "artifact": filename,
        }
    return {
        "schema_version": "1.0.0",
        "source_sha": expected_sha,
        "generated_at_utc": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = build_bundle(Path(args.evidence_dir), args.expected_sha)
    Path(args.output).write_text(json.dumps(bundle, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
