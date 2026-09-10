# Cloudflare Tunnel + R2 runtime integration

## Decision

Cloudflare is an auxiliary Zero Trust and evidence layer for Agentic-AI-Brief. It does not replace Kubernetes, OpenBao, PostgreSQL, OPA, Temporal, OpenTelemetry, or the private Tailscale runner-to-cluster path.

The integration is fail closed. `writes_enabled=false` and `destructive_operations_enabled=false` remain authoritative until the explicit change gates in `config/cloudflare-runtime-integration.json` are satisfied.

## Target architecture

GitHub Actions uses the protected `agentic-ai-brief-runtime` Environment only for Cloudflare control-plane discovery. The account-scoped Cloudflare API token must never be printed. Tunnel runtime credentials must not be stored in GitHub; the target secret manager is OpenBao.

A remotely-managed Cloudflare Tunnel named `agentic-ai-brief-runtime` is the desired runtime connector. `cloudflared` runs as a separate Kubernetes Deployment with two fixed replicas, non-root, no public origin IP, no inbound firewall opening, and outbound TCP/UDP 7844 only as required for tunnel operation. Autoscaling is intentionally disabled because removing replicas can terminate existing connections.

The R2 target is a private bucket named `agentic-ai-brief-runtime-evidence`. Evidence is stored under `runtime-evidence/`. Before evidence writes are authorized, a bucket lock must retain evidence for at least 90 days. Lifecycle deletion must never shorten the lock. Runtime data-plane access must use short-lived R2 temporary credentials scoped to the target bucket/prefix rather than the broad Cloudflare control-plane token.

## Evidence levels

`CONNECTION_VERIFIED` means the account token is active and read-only Cloudflare APIs for the account, Tunnel, R2, and `jadeltechrd.com` responded successfully.

`DISCOVERY_VERIFIED` means the exact desired Tunnel and R2 bucket state was queried with GET-only requests and is known, whether present or absent. A push-triggered branch discovery is CI evidence only and cannot promote runtime state.

`CHANGE_READY` requires a human-approved change, exact source SHA binding, immutable cloudflared image digest, OpenBao tunnel-token handling, least-privilege Kubernetes authorization, egress-only firewall proof, scoped R2 parent credential, temporary-credential proof, bucket-lock plan, and rollback plan.

`RUNTIME_VERIFIED` requires real resources plus real drills: at least two healthy tunnel connectors, R2 bucket and lock present, checksum-bound write/read roundtrip, overwrite/delete denial while locked, tunnel failover, credential rotation, observable signals, and evidence references tied to the exact source SHA.

No configuration-only or CI-only result may be reported as `RUNTIME_VERIFIED` or `PRODUCTION_VERIFIED`.

## Production hardening still required before first write

1. Pin the full multi-architecture image digest for the approved `cloudflare/cloudflared` release. A mutable tag is never sufficient production evidence.
2. Create or adopt the exact target tunnel and R2 bucket only through an approved change run. The discovery workflow is intentionally incapable of POST/PUT/PATCH/DELETE.
3. Store the Cloudflare Tunnel token in OpenBao and project it to Kubernetes with least privilege. Do not add it to GitHub secrets.
4. Configure two `cloudflared` replicas and verify outbound-only firewall connectivity on TCP/UDP 7844.
5. Configure R2 bucket lock before the first certified evidence object is written.
6. Use a dedicated R2 parent credential and derive short-lived bucket/prefix-scoped temporary credentials for runtime object operations.
7. Execute failure and recovery drills and preserve immutable evidence bound to the exact source SHA/execution ID.

## Safety invariant

A successful read-only Cloudflare preflight authorizes discovery only. It does not authorize resource creation, DNS mutation, R2 object writes, tunnel token rotation, route changes, or deletion.
