"""Offline negative tests for G3 account evidence. No network or credentials."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from agentic_ai_brief import nvidia_g3_account_evidence as g3


def template():
    return json.loads(Path("config/nvidia-g3-account-evidence-template.json").read_text())


def optimistic_claims():
    report = template()
    report["source_kind"] = "OFFICIAL_AUTHENTICATED_NVIDIA_ACCOUNT_VIEW"
    report["observed_at_utc"] = "2026-10-11T20:00:00Z"
    for name, expected in g3.POSITIVE_ASSERTIONS.items():
        report[name] = expected
    return report


def test_template_remains_no_go():
    result = g3.assess_account_evidence(template())
    assert result["status"] == "NO_GO"
    assert result["account_entitlement_certified"] is False
    assert result["billing_certified"] is False
    assert result["g3_live_inference_authorized"] is False
    assert result["credential_contact"] == "NOT_ATTEMPTED"
    assert len(result["missing_or_unfavorable_fields"]) == 7


def test_optimistic_claims_cannot_certify_account():
    result = g3.assess_account_evidence(optimistic_claims())
    assert result["missing_or_unfavorable_fields"] == []
    assert result["human_review"] == "REQUIRED"
    assert result["status"] == "NO_GO"
    assert result["g3_live_inference_authorized"] is False
    assert result["claims_require_independent_verification"] is True


@pytest.mark.parametrize("extra", [
    {"api_key": "test-secret"}, {"account_id": "test-account"},
    {"billing_certified": True}, {"g3_live_inference_authorized": True},
    {"external_approval": "test-signature"},
])
def test_unknown_fields_cannot_embed_credentials_or_approvals(extra):
    report = optimistic_claims()
    report.update(extra)
    with pytest.raises(g3.InvalidAccountEvidence) as error:
        g3.assess_account_evidence(report)
    assert str(error.value) == "G3_EVIDENCE_SCHEMA_INVALID"
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize("field,bad", [
    ("schema_version", "2.0.0"), ("model", "other"),
    ("environment", "production"), ("source_kind", "APPROVED"),
    ("developer_program_entitlement", "VERIFIED"),
    ("billing_terms", "FREE"), ("automatic_charges", True),
    ("enforced_zero_charge", "yes"), ("remaining_quota", 100),
    ("human_review", "APPROVED"), ("usage_rights", "PRODUCTION"),
])
def test_invalid_enums_and_identity_fail_closed(field, bad):
    report = optimistic_claims()
    report[field] = bad
    with pytest.raises(g3.InvalidAccountEvidence):
        g3.assess_account_evidence(report)


@pytest.mark.parametrize("bad", [
    "", "2026-10-11", "2026-10-11T20:00:00+00:00",
    "2026-13-11T20:00:00Z", "2026-10-11T25:00:00Z",
    "2026-10-11T20:00:00.123Z", 0, False, [],
])
def test_observation_time_rejects_unexpected_forms(bad):
    report = optimistic_claims()
    report["observed_at_utc"] = bad
    with pytest.raises(g3.InvalidAccountEvidence, match="G3_EVIDENCE_TIME_INVALID"):
        g3.assess_account_evidence(report)


def test_unobserved_source_cannot_assert_entitlement():
    report = template()
    report["model_access"] = "CONFIRMED_IN_ACCOUNT"
    with pytest.raises(g3.InvalidAccountEvidence, match="G3_EVIDENCE_UNSUPPORTED_CLAIM"):
        g3.assess_account_evidence(report)


@pytest.mark.parametrize("field,claim", [
    ("developer_program_entitlement", "NOT_ENTITLED"),
    ("model_access", "NOT_AVAILABLE"),
    ("billing_terms", "CHARGES_POSSIBLE"),
    ("automatic_charges", "ENABLED_IN_ACCOUNT"),
    ("enforced_zero_charge", "NOT_ENFORCED"),
    ("remaining_quota", "EXHAUSTED"),
    ("usage_rights", "OTHER_TERMS_REQUIRE_REVIEW"),
])
def test_unobserved_source_cannot_assert_negative_or_risky_claims(field, claim):
    report = template()
    report[field] = claim
    with pytest.raises(g3.InvalidAccountEvidence, match="G3_EVIDENCE_UNSUPPORTED_CLAIM"):
        g3.assess_account_evidence(report)


def test_claimed_authenticated_view_requires_timestamp():
    report = optimistic_claims()
    report["observed_at_utc"] = None
    with pytest.raises(g3.InvalidAccountEvidence, match="G3_EVIDENCE_TIME_REQUIRED"):
        g3.assess_account_evidence(report)


def test_unsafe_billing_reports_missing_field():
    report = optimistic_claims()
    report["automatic_charges"] = "ENABLED_IN_ACCOUNT"
    result = g3.assess_account_evidence(report)
    assert "automatic_charges" in result["missing_or_unfavorable_fields"]
    assert result["status"] == "NO_GO"


def test_input_is_not_mutated():
    data = optimistic_claims()
    original = deepcopy(data)
    g3.assess_account_evidence(data)
    assert data == original


def test_cli_returns_nonzero_without_printing_account_observation(tmp_path, capsys):
    path = tmp_path / "redacted.json"
    path.write_text(json.dumps(optimistic_claims()))
    assert g3.main([str(path)]) == 1
    output = capsys.readouterr().out
    assert '"status": "NO_GO"' in output
    assert "2026-10-11" not in output
    assert "OFFICIAL_AUTHENTICATED" not in output


def test_cli_invalid_input_redacted(tmp_path, capsys):
    path = tmp_path / "contains-secret.json"
    path.write_text('{"api_key":"test-secret"}')
    assert g3.main([str(path)]) == 2
    assert capsys.readouterr().out == "G3_EVIDENCE=INVALID\n"


def test_existing_runtime_and_probe_locks_remain_untouched():
    from agentic_ai_brief import nemotron_g3_probe as probe
    from agentic_ai_brief import nemotron_provider as provider

    g3.assess_account_evidence(optimistic_claims())
    assert probe.G3_AUTHENTICATED_PROBE_LOCKED is True
    assert probe.G3_BILLING_CERTIFICATION_LOCKED is True
    assert probe.G3_EXECUTION_APPROVAL_LOCKED is True
    assert probe.G3_MAX_AUTONOMOUS_SPEND_USD == 0
    assert provider.NEMOTRON_ACTIVATION_LOCKED is True


def test_template_claims_nothing():
    source = template()
    assert source["human_review"] == "PENDING"
    assert source["source_kind"] == "NOT_CAPTURED"
    assert source["enforced_zero_charge"] == "UNKNOWN"
    assert source["billing_terms"] == "UNKNOWN"
