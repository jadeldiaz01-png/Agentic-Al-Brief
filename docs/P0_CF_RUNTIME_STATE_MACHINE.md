# P0-CF runtime promotion state machine

## Decision

Cloudflare runtime integration is promoted through explicit evidence states. No later state may be inferred from configuration, CI, or a successful earlier state.

`NO_GO -> CONNECTION_VERIFIED -> DISCOVERY_VERIFIED -> CHANGE_READY -> CREATE_ONLY_APPLIED -> POST_CREATE_VERIFIED -> RUNTIME_VERIFIED -> PRODUCTION_VERIFIED`

## Why CHANGE_READY and POST_CREATE are separate

Two earlier prerequisites were circular and are intentionally split:

1. A remotely managed Tunnel token cannot be stored in OpenBao until the Tunnel exists and Cloudflare can issue/retrieve its runtime token.
2. R2 temporary credentials are scoped to a bucket, so a functional mint/roundtrip test against `agentic-ai-brief-runtime-evidence` cannot be completed before that bucket exists.

Therefore CHANGE_READY proves that the creation operation is safe to attempt, while POST_CREATE proves that the resources and runtime credentials actually work.

## CHANGE_READY

Must be one manual exact-SHA execution and must prove:

- GitHub-hosted runner and exact source SHA.
- Tailscale GitHub OIDC WIF workflow path plus actual `tag:agentic-ai-brief-runtime` on the ephemeral node.
- Exact Kubernetes context and namespace.
- No cluster-admin and no Kubernetes Secret read/list permission.
- Immutable `cloudflared` OCI digest.
- Secrets Store CSI CRD discoverability and server-side schema admission for the OpenBao SecretProviderClass.
- Hardened Kubernetes manifest and Cloudflare edge NetworkPolicy contract.
- Runner-side TCP and UDP 7844 precheck as an advisory connectivity signal.
- R2 target state known, parent credential present without disclosure, temporary credential mint plan and >=90-day Bucket Lock plan.
- Rollback plan present and Cloudflare writes still disabled.

CHANGE_READY does **not** prove that the OpenBao provider can mount the future Tunnel token and does **not** prove the cluster runtime path can reach Cloudflare.

## CREATE_ONLY_APPLIED

Requires separate explicit human confirmation `CREATE_CLOUDFLARE_RUNTIME_RESOURCES`.

Permitted first-change operations are limited to creating an absent Tunnel, creating an absent R2 bucket, and applying the planned Bucket Lock. DNS mutation, deletion, and overwrite of a nonmatching existing resource remain forbidden.

## POST_CREATE_VERIFIED

Requires real evidence after creation:

- Tunnel and R2 bucket exist.
- Bucket Lock is actually active before certified evidence writes.
- Tunnel token is stored in OpenBao, never GitHub.
- A real CSI mount proves Secrets Store CSI + OpenBao provider + OpenBao auth role/path work.
- Connectivity is tested from the actual `cloudflared` pod network path, not merely from GitHub Actions.
- R2 parent credential is functionally valid and mints <=900-second `object-read-write` temporary credentials scoped to `runtime-evidence/`.
- `cloudflared` is deployed by immutable digest with the required healthy replicas.

## RUNTIME_VERIFIED

Requires failure/recovery drills and immutable evidence: R2 checksum roundtrip, overwrite/delete denial while locked, Tunnel failover, credential rotation, OTel signals, and evidence refs bound to exact source SHA and execution ID.

## Production boundary

Cloudflare RUNTIME_VERIFIED is only one subsystem gate. It does not authorize full Agentic-AI-Brief production without the PostgreSQL PITR, OpenBao workload identity, OPA, Temporal replay, OTel, crash recovery, supply-chain, safety, quality, SLO/DR and governance gates in `config/production-readiness.json`.
