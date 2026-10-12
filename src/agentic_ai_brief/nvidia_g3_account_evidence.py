"""Offline fail-closed NVIDIA G3 account-evidence intake. Never grants authorization."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

EXPECTED_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
EXPECTED_ENVIRONMENT = "nvidia-connection-check"
STATUS_VALUES = {
    "source_kind": {"NOT_CAPTURED", "OFFICIAL_AUTHENTICATED_NVIDIA_ACCOUNT_VIEW"},
    "developer_program_entitlement": {"UNKNOWN", "CONFIRMED_IN_ACCOUNT", "NOT_ENTITLED"},
    "model_access": {"UNKNOWN", "CONFIRMED_IN_ACCOUNT", "NOT_AVAILABLE"},
    "billing_terms": {"UNKNOWN", "EXPLICIT_NO_CHARGE", "CHARGES_POSSIBLE"},
    "automatic_charges": {"UNKNOWN", "DISABLED_IN_ACCOUNT", "ENABLED_IN_ACCOUNT"},
    "enforced_zero_charge": {"UNKNOWN", "PROVIDER_ENFORCED", "NOT_ENFORCED"},
    "remaining_quota": {"UNKNOWN", "AVAILABLE_IN_ACCOUNT", "EXHAUSTED"},
    "usage_rights": {"UNKNOWN", "PROTOTYPE_ONLY", "OTHER_TERMS_REQUIRE_REVIEW"},
    "human_review": {"PENDING"},
}
POSITIVE_ASSERTIONS = {
    "developer_program_entitlement": "CONFIRMED_IN_ACCOUNT",
    "model_access": "CONFIRMED_IN_ACCOUNT",
    "billing_terms": "EXPLICIT_NO_CHARGE",
    "automatic_charges": "DISABLED_IN_ACCOUNT",
    "enforced_zero_charge": "PROVIDER_ENFORCED",
    "remaining_quota": "AVAILABLE_IN_ACCOUNT",
    "usage_rights": "PROTOTYPE_ONLY",
}
ALL_FIELDS = set(STATUS_VALUES) | {
    "schema_version", "model", "environment", "observed_at_utc"
}


class InvalidAccountEvidence(ValueError):
    """Sanitized schema error; never echo untrusted input."""


def valid_utc(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        return False
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%SZ") == value
    except ValueError:
        return False


def assess_account_evidence(evidence: object) -> dict[str, Any]:
    """Always reject execution even for optimistic, unverified account assertions."""
    if type(evidence) is not dict or set(evidence) != ALL_FIELDS:
        raise InvalidAccountEvidence("G3_EVIDENCE_SCHEMA_INVALID")
    if (
        evidence["schema_version"] != "1.0.0"
        or evidence["model"] != EXPECTED_MODEL
        or evidence["environment"] != EXPECTED_ENVIRONMENT
    ):
        raise InvalidAccountEvidence("G3_EVIDENCE_IDENTITY_INVALID")
    for name, allowed in STATUS_VALUES.items():
        value = evidence[name]
        if type(value) is not str or value not in allowed:
            raise InvalidAccountEvidence("G3_EVIDENCE_ENUM_INVALID")
    observed = evidence["observed_at_utc"]
    if observed is not None and not valid_utc(observed):
        raise InvalidAccountEvidence("G3_EVIDENCE_TIME_INVALID")
    if evidence["source_kind"] == "NOT_CAPTURED":
        # With no captured source, no account field—positive or negative—may
        # be asserted. Keep the intake strictly unknown until human observation.
        unobserved_claims = (
            name for name in STATUS_VALUES
            if name not in {"source_kind", "human_review"}
        )
        if observed is not None or any(evidence[name] != "UNKNOWN" for name in unobserved_claims):
            raise InvalidAccountEvidence("G3_EVIDENCE_UNSUPPORTED_CLAIM")
    elif observed is None:
        raise InvalidAccountEvidence("G3_EVIDENCE_TIME_REQUIRED")
    unresolved = [name for name, expectation in POSITIVE_ASSERTIONS.items() if evidence[name] != expectation]
    # Self-reported statuses are not signed approvals or real account billing evidence.
    return {
        "status": "NO_GO",
        "human_review": "REQUIRED",
        "credential_contact": "NOT_ATTEMPTED",
        "nvidia_api_contact": "NOT_ATTEMPTED",
        "account_entitlement_certified": False,
        "billing_certified": False,
        "g3_live_inference_authorized": False,
        "missing_or_unfavorable_fields": unresolved,
        "claims_require_independent_verification": True,
    }


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("G3_EVIDENCE=INVALID_ARGUMENTS")
        return 2
    try:
        path = Path(args[0])
        if not path.is_file() or path.stat().st_size > 8192:
            raise InvalidAccountEvidence("G3_EVIDENCE_FILE_INVALID")
        data = json.loads(path.read_text(encoding="utf-8"))
        result = assess_account_evidence(data)
    except (OSError, UnicodeError, ValueError):
        print("G3_EVIDENCE=INVALID")
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1  # Valid evidence still has NO_GO status, not authorization.


if __name__ == "__main__":
    raise SystemExit(main())