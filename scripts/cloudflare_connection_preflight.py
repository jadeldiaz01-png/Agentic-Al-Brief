from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.cloudflare.com/client/v4"
ZONE_NAME = "jadeltechrd.com"


def _request(path: str, token: str) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
            return response.status, body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"success": False, "errors": [{"code": exc.code, "message": "non-json response"}]}
        return exc.code, body


def _ok(status: int, body: dict[str, object]) -> bool:
    return 200 <= status < 300 and body.get("success") is True


def _active(status: int, body: dict[str, object]) -> bool:
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    return _ok(status, body) and result.get("status") == "active"


def main() -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()

    print(f"CLOUDFLARE_TOKEN_PRESENT={'YES' if token else 'NO'}")
    print(f"CLOUDFLARE_ACCOUNT_ID_PRESENT={'YES' if account_id else 'NO'}")
    if not token or not account_id:
        print("CLOUDFLARE_CONNECTION_READY=NO")
        return 2

    if len(account_id) != 32 or any(ch not in "0123456789abcdefABCDEF" for ch in account_id):
        print("CLOUDFLARE_ACCOUNT_ID_FORMAT=INVALID")
        print("CLOUDFLARE_CONNECTION_READY=NO")
        return 3
    print("CLOUDFLARE_ACCOUNT_ID_FORMAT=VALID")

    # Correct primary check for account-owned/account-scoped API tokens.
    account_status, account_body = _request(f"/accounts/{account_id}/tokens/verify", token)
    account_active = _active(account_status, account_body)
    print(f"CLOUDFLARE_ACCOUNT_TOKEN_ACTIVE={'YES' if account_active else 'NO'}")

    # Compatibility check for user-owned API tokens; this is not used to override
    # a failed account-token verification for this account-scoped runtime.
    user_status, user_body = _request("/user/tokens/verify", token)
    user_active = _active(user_status, user_body)
    print(f"CLOUDFLARE_USER_TOKEN_ACTIVE={'YES' if user_active else 'NO'}")

    if not account_active:
        print("CLOUDFLARE_TOKEN_ACTIVE=NO")
        print("CLOUDFLARE_CONNECTION_READY=NO")
        return 4
    print("CLOUDFLARE_TOKEN_ACTIVE=YES")

    tunnel_status, tunnel_body = _request(
        f"/accounts/{account_id}/cfd_tunnel?is_deleted=false&per_page=1", token
    )
    tunnel_ok = _ok(tunnel_status, tunnel_body)
    print(f"CLOUDFLARE_TUNNEL_READ_VERIFIED={'YES' if tunnel_ok else 'NO'}")

    r2_status, r2_body = _request(f"/accounts/{account_id}/r2/buckets?per_page=1", token)
    r2_ok = _ok(r2_status, r2_body)
    print(f"CLOUDFLARE_R2_READ_VERIFIED={'YES' if r2_ok else 'NO'}")

    query = urllib.parse.urlencode({"name": ZONE_NAME, "account.id": account_id, "per_page": 1})
    zone_status, zone_body = _request(f"/zones?{query}", token)
    zone_result = zone_body.get("result") if isinstance(zone_body.get("result"), list) else []
    zone_ok = _ok(zone_status, zone_body) and any(
        isinstance(item, dict) and item.get("name") == ZONE_NAME for item in zone_result
    )
    print(f"CLOUDFLARE_ZONE_JADELTECHRD_COM_READ_VERIFIED={'YES' if zone_ok else 'NO'}")

    ready = account_active and tunnel_ok and r2_ok and zone_ok
    print(f"CLOUDFLARE_CONNECTION_READY={'YES' if ready else 'NO'}")
    return 0 if ready else 5


if __name__ == "__main__":
    sys.exit(main())
