import json
from pathlib import Path

import pytest

from scripts.collect_p0c_runtime_evidence import ARTIFACTS, REQUIRED_ASSERTIONS, build_bundle

EXECUTION_ID = "p0c-test-execution"


def _write_artifacts(root: Path, source_sha: str, execution_id: str = EXECUTION_ID) -> None:
    for gate, filename in ARTIFACTS.items():
        payload = {
            "source_sha": source_sha,
            "execution_id": execution_id,
            "verified": True,
            "generated_at_utc": "2026-09-06T18:00:00Z",
            "assertions": {name: True for name in REQUIRED_ASSERTIONS[gate]},
        }
        (root / filename).write_text(json.dumps(payload), encoding="utf-8")


def test_build_bundle_requires_every_independent_artifact(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, "a" * 40)
    bundle = build_bundle(tmp_path, "a" * 40, EXECUTION_ID)
    assert bundle["source_sha"] == "a" * 40
    assert bundle["execution_id"] == EXECUTION_ID
    assert len(bundle["evidence"]) == len(ARTIFACTS)
    for item in bundle["evidence"].values():
        assert item["verified"] is True
        assert item["evidence_ref"].startswith("sha256:")


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, "b" * 40)
    (tmp_path / "temporal-replay.json").unlink()
    with pytest.raises(FileNotFoundError, match="temporal-replay.json"):
        build_bundle(tmp_path, "b" * 40, EXECUTION_ID)


def test_source_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, "c" * 40)
    with pytest.raises(ValueError, match="SOURCE_SHA_MISMATCH"):
        build_bundle(tmp_path, "d" * 40, EXECUTION_ID)


def test_execution_id_mismatch_fails_closed(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, "d" * 40, "different-execution")
    with pytest.raises(ValueError, match="EXECUTION_ID_MISMATCH"):
        build_bundle(tmp_path, "d" * 40, EXECUTION_ID)


def test_boolean_without_gate_specific_assertions_is_not_proof(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, "e" * 40)
    path = tmp_path / "postgresql-pitr.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["assertions"].pop("restore_drill_verified")
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="restore_drill_verified:NOT_VERIFIED"):
        build_bundle(tmp_path, "e" * 40, EXECUTION_ID)


def test_secret_material_is_rejected(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, "f" * 40)
    path = tmp_path / "openbao-identity.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["token"] = "must-never-enter-evidence"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="SECRET_MATERIAL_FORBIDDEN"):
        build_bundle(tmp_path, "f" * 40, EXECUTION_ID)
