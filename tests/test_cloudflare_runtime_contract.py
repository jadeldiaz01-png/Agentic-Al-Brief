from __future__ import annotations

import json
from pathlib import Path

CONFIG = Path("config/cloudflare-runtime-integration.json")
SCRIPT = Path("scripts/cloudflare_runtime_discovery.py")


def test_cloudflare_runtime_contract_is_fail_closed() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["default_decision"] == "NO_GO"
    assert cfg["mode"] == "STATE_MACHINE_FAIL_CLOSED"
    assert cfg["writes_enabled"] is False
    assert cfg["destructive_operations_enabled"] is False
    assert cfg["credentials"]["raw_secret_logging_forbidden"] is True
    assert cfg["credentials"]["tunnel_token_in_github_forbidden"] is True
    assert cfg["credentials"]["tunnel_token_secret_manager"] == "openbao"


def test_tunnel_production_baseline_is_hardened() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    tunnel = cfg["tunnel"]
    assert tunnel["replicas"] >= 2
    assert tunnel["autoscaling"] is False
    assert tunnel["run_as_non_root"] is True
    assert tunnel["public_origin_ip_required"] is False
    assert tunnel["public_inbound_ports_required"] is False
    assert tunnel["egress"]["port"] == 7844
    assert set(tunnel["egress"]["protocols"]) == {"TCP", "UDP"}
    assert tunnel["immutable_image_digest_required_before_apply"] is True


def test_r2_evidence_store_requires_retention_and_temporary_credentials() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    r2 = cfg["r2"]
    assert r2["public_access"] is False
    assert r2["bucket_lock"]["required"] is True
    assert r2["bucket_lock"]["minimum_retention_days"] >= 90
    assert r2["lifecycle_delete_before_lock_expiry_forbidden"] is True
    assert cfg["credentials"]["r2_data_plane_temporary_credentials_required"] is True
    assert r2["presigned_url_max_ttl_seconds"] <= 900


def test_discovery_code_has_no_cloudflare_write_http_methods() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'method="GET"' in text
    for forbidden in ('method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"'):
        assert forbidden not in text


def test_post_create_and_runtime_promotion_require_real_evidence() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    post_create = set(cfg["required_immediately_after_create_only"])
    runtime = set(cfg["required_before_runtime_verified"])
    assert {
        "target_tunnel_present",
        "target_tunnel_healthy_with_minimum_replicas",
        "target_r2_bucket_present",
        "r2_bucket_lock_verified",
        "tunnel_token_stored_in_openbao",
        "openbao_csi_secret_mount_verified",
        "r2_temporary_credentials_verified",
    }.issubset(post_create)
    assert {
        "r2_write_read_checksum_roundtrip_verified",
        "r2_overwrite_delete_denied_during_lock_verified",
        "tunnel_failover_drill_verified",
        "credential_rotation_drill_verified",
        "evidence_refs_bound_to_exact_source_sha",
    }.issubset(runtime)
