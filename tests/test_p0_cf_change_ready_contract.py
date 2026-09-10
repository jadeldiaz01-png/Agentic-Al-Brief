from __future__ import annotations

import json
from pathlib import Path


CHANGE_READY = Path("config/p0-cf-change-ready.json")
CLOUDFLARE = Path("config/cloudflare-runtime-integration.json")
DEPLOYMENT = Path("deploy/cloudflare/cloudflared-runtime.yaml")
NETWORK_POLICY = Path("deploy/cloudflare/cloudflared-networkpolicy.yaml")
PREFLIGHT = Path("scripts/p0_cf_change_ready_preflight.sh")
WORKFLOW = Path(".github/workflows/p0-cf-change-ready.yml")


def test_change_ready_contract_is_fail_closed() -> None:
    cfg = json.loads(CHANGE_READY.read_text(encoding="utf-8"))
    assert cfg["gate_id"] == "P0-CF-CHANGE-READY"
    assert cfg["default_decision"] == "NO_GO"
    policy = cfg["non_destructive_creation_policy"]
    assert policy["create_only_if_absent"] is True
    assert policy["delete_forbidden"] is True
    assert policy["overwrite_existing_resource_forbidden"] is True
    assert policy["dns_mutation_forbidden_in_first_change"] is True
    assert policy["explicit_human_confirmation_required"] is True


def test_cloudflared_release_is_immutable_and_consistent() -> None:
    cfg = json.loads(CHANGE_READY.read_text(encoding="utf-8"))
    image = cfg["cloudflared"]["image"]
    assert image == (
        "cloudflare/cloudflared@sha256:"
        "51c9cefcb4569df44e1ad403ab1d3d8065aa8e84339bcfc6aee75502e1140339"
    )
    deployment = DEPLOYMENT.read_text(encoding="utf-8")
    assert f"image: {image}" in deployment
    assert "image: cloudflare/cloudflared:" not in deployment
    assert "--no-autoupdate" in deployment


def test_cloudflared_pod_security_and_availability() -> None:
    text = DEPLOYMENT.read_text(encoding="utf-8")
    for required in (
        "replicas: 2",
        "automountServiceAccountToken: false",
        "runAsNonRoot: true",
        "runAsUser: 65532",
        "allowPrivilegeEscalation: false",
        "readOnlyRootFilesystem: true",
        'drop: ["ALL"]',
        "type: RuntimeDefault",
        "minAvailable: 1",
        "topologySpreadConstraints:",
        "provider: openbao",
        "driver: secrets-store.csi.k8s.io",
    ):
        assert required in text
    assert "secretObjects:" not in text


def test_network_policy_is_default_deny_and_edge_scoped() -> None:
    text = NETWORK_POLICY.read_text(encoding="utf-8")
    assert "cloudflared-default-deny" in text
    assert "198.41.192.0/24" in text
    assert "198.41.200.0/24" in text
    assert "port: 7844" in text
    assert "protocol: TCP" in text
    assert "protocol: UDP" in text
    assert "port: 53" in text


def test_r2_contract_uses_short_lived_scoped_credentials_and_lock() -> None:
    cfg = json.loads(CHANGE_READY.read_text(encoding="utf-8"))
    r2 = cfg["r2"]
    assert r2["temporary_credentials_required"] is True
    assert r2["temporary_permission"] == "object-read-write"
    assert r2["temporary_prefixes"] == ["runtime-evidence/"]
    assert r2["temporary_ttl_seconds"] <= 900
    assert r2["minimum_lock_seconds"] >= 7_776_000
    assert r2["control_plane_token_as_s3_credential_forbidden"] is True


def test_preflight_and_workflow_cannot_apply_cloudflare_changes() -> None:
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "P0_CF_CHANGE_READY=YES" in preflight
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "push:" not in workflow
    assert "ref: ${{ inputs.expected_sha }}" in workflow
    for forbidden in ("curl -X POST", "curl -X PUT", "curl -X PATCH", "curl -X DELETE"):
        assert forbidden not in preflight
        assert forbidden not in workflow


def test_production_manifest_requires_change_ready() -> None:
    prod = json.loads(Path("config/production-readiness.json").read_text(encoding="utf-8"))
    assert "CHANGE_READY" in prod["evidence_levels"]
    assert "p0_cf_change_ready_verified" in prod["required_for_production"]["runtime"]


def test_cloudflare_manifest_and_change_ready_contract_match() -> None:
    cf = json.loads(CLOUDFLARE.read_text(encoding="utf-8"))
    cr = json.loads(CHANGE_READY.read_text(encoding="utf-8"))
    assert cf["tunnel"]["cloudflared_image"] == cr["cloudflared"]["image"]
    assert cf["r2"]["desired_bucket"] == cr["r2"]["bucket"]
    assert cf["r2"]["temporary_credential_ttl_seconds"] == cr["r2"]["temporary_ttl_seconds"]
    assert cf["writes_enabled"] is False
    assert cf["destructive_operations_enabled"] is False
