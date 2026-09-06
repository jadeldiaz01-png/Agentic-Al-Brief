from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"


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


def main() -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()

    if not token:
        print("CLOUDFLARE_TOKEN_PRESENT=NO")
        print("CLOUDFLARE_CONNECTION_READY=NO")
        return 2

    print("CLOUDFLARE_TOKEN_PRESENT=YES")
    status, body = _request("/user/tokens/verify", token)
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    active = _ok(status, body) and result.get("status") == "active"
    print(f"CLOUDFLARE_TOKEN_ACTIVE={'YES' if active else 'NO'}")
    if not active:
        print("CLOUDFLARE_CONNECTION_READY=NO")
        return 3

    if not account_id:
        print("CLOUDFLARE_ACCOUNT_ID_PRESENT=NO")
        print("CLOUDFLARE_TUNNEL_READ_VERIFIED=NOT_TESTED")
        print("CLOUDFLARE_R2_READ_VERIFIED=NOT_TESTED")
        print("CLOUDFLARE_CONNECTION_READY=NO")
        return 4

    if len(account_id) != 32 or any(ch not in "0123456789abcdefABCDEF" for ch in account_id):
        print("CLOUDFLARE_ACCOUNT_ID_PRESENT=YES")
        print("CLOUDFLARE_ACCOUNT_ID_FORMAT=INVALID")
        print("CLOUDFLARE_CONNECTION_READY=NO")
        return 5

    print("CLOUDFLARE_ACCOUNT_ID_PRESENT=YES")
    print("CLOUDFLARE_ACCOUNT_ID_FORMAT=VALID")

    tunnel_status, tunnel_body = _request(
        f"/accounts/{account_id}/cfd_tunnel?is_deleted=false&per_page=1", token
    )
    tunnel_ok = _ok(tunnel_status, tunnel_body)
    print(f"CLOUDFLARE_TUNNEL_READ_VERIFIED={'YES' if tunnel_ok else 'NO'}")

    r2_status, r2_body = _request(f"/accounts/{account_id}/r2/buckets?per_page=1", token)
    r2_ok = _ok(r2_status, r2_body)
    print(f"CLOUDFLARE_R2_READ_VERIFIED={'YES' if r2_ok else 'NO'}")

    ready = tunnel_ok and r2_ok
    print(f"CLOUDFLARE_CONNECTION_READY={'YES' if ready else 'NO'}")
    return 0 if ready else 6


if __name__ == "__main__":
    sys.exit(main())
