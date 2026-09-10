from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.cloudflare.com/client/v4"
CONFIG = Path("config/cloudflare-runtime-integration.json")


def _request(path: str, token: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"success": False}
        return exc.code, body


def _ok(status: int, body: dict[str, Any]) -> bool:
    return 200 <= status < 300 and body.get("success") is True


def _account_token_active(account_id: str, token: str) -> bool:
    status, body = _request(f"/accounts/{account_id}/tokens/verify", token)
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    return _ok(status, body) and result.get("status") == "active"


def _load_config() -> dict[str, Any]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    if data.get("writes_enabled") is not False or data.get("destructive_operations_enabled") is not False:
        raise RuntimeError("Cloudflare discovery must remain read-only")
    return data


def main() -> int:
    cfg = _load_config()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if not token or len(account_id) != 32 or any(c not in "0123456789abcdefABCDEF" for c in account_id):
        print("CLOUDFLARE_RUNTIME_DISCOVERY_VERIFIED=NO")
        return 2

    token_active = _account_token_active(account_id, token)
    print(f"CLOUDFLARE_ACCOUNT_TOKEN_ACTIVE={'YES' if token_active else 'NO'}")
    if not token_active:
        print("CLOUDFLARE_RUNTIME_DISCOVERY_VERIFIED=NO")
        return 3

    zone = str(cfg["zone"])
    zone_query = urllib.parse.urlencode({"name": zone, "account.id": account_id, "per_page": 1})
    zone_status, zone_body = _request(f"/zones?{zone_query}", token)
    zone_result = zone_body.get("result") if isinstance(zone_body.get("result"), list) else []
    zone_ok = _ok(zone_status, zone_body) and len(zone_result) == 1 and zone_result[0].get("name") == zone
    print(f"CLOUDFLARE_ZONE_JADELTECHRD_COM_READ_VERIFIED={'YES' if zone_ok else 'NO'}")

    tunnel_name = str(cfg["tunnel"]["desired_name"])
    tunnel_query = urllib.parse.urlencode({"is_deleted": "false", "name": tunnel_name, "per_page": 50})
    tunnel_status, tunnel_body = _request(f"/accounts/{account_id}/cfd_tunnel?{tunnel_query}", token)
    tunnel_api_ok = _ok(tunnel_status, tunnel_body)
    tunnel_rows = tunnel_body.get("result") if isinstance(tunnel_body.get("result"), list) else []
    exact_tunnels = [row for row in tunnel_rows if row.get("name") == tunnel_name]
    tunnel_present = tunnel_api_ok and len(exact_tunnels) == 1
    print(f"CLOUDFLARE_TUNNEL_API_READ_VERIFIED={'YES' if tunnel_api_ok else 'NO'}")
    print(f"CLOUDFLARE_TARGET_TUNNEL_PRESENT={'YES' if tunnel_present else 'NO'}")

    tunnel_connections = 0
    if tunnel_present:
        tunnel_id = exact_tunnels[0].get("id")
        if not isinstance(tunnel_id, str):
            print("CLOUDFLARE_TARGET_TUNNEL_STATE_KNOWN=NO")
            return 4
        conn_status, conn_body = _request(f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/connections", token)
        conn_rows = conn_body.get("result") if isinstance(conn_body.get("result"), list) else []
        if not _ok(conn_status, conn_body):
            print("CLOUDFLARE_TARGET_TUNNEL_STATE_KNOWN=NO")
            return 4
        tunnel_connections = len(conn_rows)
    print("CLOUDFLARE_TARGET_TUNNEL_STATE_KNOWN=YES")
    print(f"CLOUDFLARE_TARGET_TUNNEL_CONNECTIONS={tunnel_connections}")

    bucket = str(cfg["r2"]["desired_bucket"])
    bucket_path = urllib.parse.quote(bucket, safe="")
    bucket_status, bucket_body = _request(f"/accounts/{account_id}/r2/buckets/{bucket_path}", token)
    if bucket_status == 404:
        bucket_api_ok = True
        bucket_present = False
    else:
        bucket_api_ok = _ok(bucket_status, bucket_body)
        bucket_present = bucket_api_ok
    print(f"CLOUDFLARE_R2_API_READ_VERIFIED={'YES' if bucket_api_ok else 'NO'}")
    print(f"CLOUDFLARE_TARGET_R2_BUCKET_PRESENT={'YES' if bucket_present else 'NO'}")

    lock_verified = False
    lock_state_known = False
    if bucket_present:
        lock_status, lock_body = _request(f"/accounts/{account_id}/r2/buckets/{bucket_path}/lock", token)
        if _ok(lock_status, lock_body):
            lock_state_known = True
            result = lock_body.get("result") if isinstance(lock_body.get("result"), dict) else {}
            rules = result.get("rules") if isinstance(result.get("rules"), list) else []
            prefix = str(cfg["r2"]["evidence_prefix"])
            minimum = int(cfg["r2"]["bucket_lock"]["retention_seconds"])
            for rule in rules:
                if not isinstance(rule, dict) or rule.get("enabled") is not True:
                    continue
                if rule.get("prefix", "") not in ("", prefix):
                    continue
                condition = rule.get("condition") if isinstance(rule.get("condition"), dict) else {}
                if condition.get("type") == "Indefinite":
                    lock_verified = True
                elif condition.get("type") == "Age" and int(condition.get("maxAgeSeconds", 0)) >= minimum:
                    lock_verified = True
    else:
        lock_state_known = True

    print(f"CLOUDFLARE_TARGET_R2_BUCKET_STATE_KNOWN={'YES' if bucket_api_ok and lock_state_known else 'NO'}")
    print(f"CLOUDFLARE_R2_BUCKET_LOCK_VERIFIED={'YES' if lock_verified else 'NO'}")
    print("CLOUDFLARE_DISCOVERY_USES_GET_ONLY=YES")

    discovery_ok = zone_ok and tunnel_api_ok and bucket_api_ok and lock_state_known
    healthy_required = int(cfg["tunnel"]["health_connections_minimum"])
    runtime_integrated = tunnel_present and tunnel_connections >= healthy_required and bucket_present and lock_verified
    print(f"CLOUDFLARE_RUNTIME_DISCOVERY_VERIFIED={'YES' if discovery_ok else 'NO'}")
    print(f"CLOUDFLARE_RUNTIME_INTEGRATED={'YES' if runtime_integrated else 'NO'}")
    print("CLOUDFLARE_WRITES_ENABLED=NO")
    print("CLOUDFLARE_DESTRUCTIVE_OPERATIONS_ENABLED=NO")
    return 0 if discovery_ok else 5


if __name__ == "__main__":
    sys.exit(main())
