from agentic_ai_brief.runtime_evidence import REQUIRED_RUNTIME_GATES, certify_runtime_bundle


def _bundle(source_sha: str) -> dict[str, object]:
    evidence = {
        gate: {"verified": True, "evidence_ref": "sha256:" + ("a" * 64)}
        for gate in REQUIRED_RUNTIME_GATES
    }
    return {"source_sha": source_sha, "evidence": evidence}


def test_runtime_verified_requires_every_gate() -> None:
    cert = certify_runtime_bundle(_bundle("abc"), "abc")
    assert cert.decision == "RUNTIME_VERIFIED"
    assert cert.blockers == ()
    assert len(cert.evidence_sha256) == 64


def test_missing_gate_fails_closed() -> None:
    bundle = _bundle("abc")
    evidence = bundle["evidence"]
    assert isinstance(evidence, dict)
    evidence.pop("temporal_replay_verified")
    cert = certify_runtime_bundle(bundle, "abc")
    assert cert.decision == "NO_GO"
    assert "temporal_replay_verified" in cert.blockers


def test_source_sha_mismatch_fails_closed() -> None:
    cert = certify_runtime_bundle(_bundle("wrong"), "expected")
    assert cert.decision == "NO_GO"
    assert "source_sha_mismatch" in cert.blockers


def test_boolean_without_evidence_reference_is_not_proof() -> None:
    bundle = _bundle("abc")
    evidence = bundle["evidence"]
    assert isinstance(evidence, dict)
    evidence["postgresql_pitr_verified"] = {"verified": True}
    cert = certify_runtime_bundle(bundle, "abc")
    assert cert.decision == "NO_GO"
    assert "postgresql_pitr_verified:invalid_evidence_ref" in cert.blockers
