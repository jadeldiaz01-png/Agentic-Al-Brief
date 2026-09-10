# P0-CF-CHANGE-READY

## Purpose

This gate is the final fail-closed stage before any Cloudflare resource creation. It proves that the exact source SHA, ephemeral GitHub runner, Tailscale federated path, Kubernetes identity, OpenBao secret delivery contract, Cloudflare egress path, immutable `cloudflared` image, R2 credential model, Bucket Lock plan, and rollback constraints are all compatible in one execution.

Passing this gate does **not** create a Cloudflare Tunnel, R2 bucket, DNS record, Kubernetes deployment, OpenBao secret, or R2 object. It only promotes the change to `CHANGE_READY`.

## Adjudicated cloudflared image

The selected release is `2026.8.3`, pinned by the multi-platform OCI index digest:

`cloudflare/cloudflared@sha256:51c9cefcb4569df44e1ad403ab1d3d8065aa8e84339bcfc6aee75502e1140339`

The linux/amd64 manifest digest is `sha256:9be48e4b4e996da851bf78f7782bfab150dd4d8889e469d004802e7d7afb63b1` and the linux/arm64 manifest digest is `sha256:4ecc4283c0f7cc127522e5ef261595cfe8571ee28f5c8d3751b24f52f9d04ebe`.

The release was chosen conservatively because it was the latest Cloudflare GitHub release visible during the adjudication. A newer Docker tag must not silently replace it; any upgrade requires a new digest review and CI/runtime evidence.

## Kubernetes/OpenBao design

`cloudflared` runs as an adjacent Deployment, never as an application sidecar. It has two replicas, a PDB, topology spreading, no autoscaler, UID/GID 65532, `RuntimeDefault` seccomp, read-only root filesystem, no privilege escalation, and all Linux capabilities dropped.

The workload uses the dedicated ServiceAccount `cloudflared-runtime` with `automountServiceAccountToken: false`. The Cloudflare Tunnel token is mounted as a file through the Secrets Store CSI Driver using the OpenBao provider. No Kubernetes Secret synchronization is declared, so the credential is not intentionally persisted into a Kubernetes Secret object.

The OpenBao role must be bound only to `system:serviceaccount:agentic-ai-brief-runtime:cloudflared-runtime` and grant read access only to `kv/data/agentic-ai-brief/cloudflare-tunnel`. The actual OpenBao policy/role is external runtime state and must be verified before creation.

## Network design

The cloudflared pods are isolated by default for ingress and egress. DNS is explicitly allowed. Tunnel traffic is allowed only to the Cloudflare edge CIDRs `198.41.192.0/24` and `198.41.200.0/24` on TCP/UDP 7844.

Standard Kubernetes NetworkPolicy cannot express an FQDN allowlist. Therefore the host/edge firewall remains a required independent gate and must enforce Cloudflare's published destinations. The preflight performs live TCP checks to representative endpoints and verifies the UDP policy declaration; UDP runtime behavior is certified later by the real tunnel connection/failover drills.

## R2 design

Target bucket: `agentic-ai-brief-runtime-evidence`.

Certified evidence prefix: `runtime-evidence/`.

Before the first certified evidence write, Bucket Lock must be configured for at least 7,776,000 seconds (90 days). Lifecycle rules must never shorten that retention.

The runtime must not reuse `CLOUDFLARE_API_TOKEN` as an S3 credential. A dedicated R2 parent API token/access key is required. Runtime object access is delegated through temporary credentials with `object-read-write`, scoped to the target bucket and `runtime-evidence/` prefix, with a maximum TTL of 900 seconds for this project.

## Required protected Environment values

The `agentic-ai-brief-runtime` GitHub Environment must provide the existing Cloudflare/Tailscale/Kubernetes values plus two dedicated R2 parent values:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `TS_OAUTH_CLIENT_ID`
- `TS_AUDIENCE`
- `RUNTIME_KUBECONFIG_B64`
- `R2_PARENT_ACCESS_KEY_ID`
- `R2_PARENT_API_TOKEN`

Secret values must never be printed, committed, uploaded as workflow artifacts, or copied into issue/PR text.

## Execution

Run `.github/workflows/p0-cf-change-ready.yml` manually with:

- `expected_sha`: exact 40-character SHA on `main` to certify.
- `expected_context`: exact Kubernetes context expected in the protected kubeconfig.
- `runtime_namespace`: `agentic-ai-brief-runtime` unless an approved ADR changes it.

A legitimate success must emit `P0_CF_CHANGE_READY=YES` after all checks in the same run. A CI pass alone, an old successful run, or a manually written boolean does not satisfy this gate.

## First creation stage after CHANGE_READY

Only after authentic `P0_CF_CHANGE_READY=YES` may a separate creation workflow be enabled. That workflow must require the exact confirmation phrase `CREATE_CLOUDFLARE_RUNTIME_RESOURCES` and must be idempotent/create-only:

- Create Tunnel `agentic-ai-brief-runtime` only if absent.
- Create R2 bucket `agentic-ai-brief-runtime-evidence` only if absent.
- Configure Bucket Lock before any certified evidence object is written.
- Retrieve the Tunnel token without logging it and write it directly to OpenBao; do not store it in GitHub.
- Apply the pinned Kubernetes manifests only after the OpenBao secret path is proven.
- Do not mutate DNS in the first change.
- Do not delete Cloudflare resources.
- Do not overwrite or adopt an existing resource unless its exact contract is verified.

Creation is not `RUNTIME_VERIFIED`. Runtime promotion still requires two healthy tunnel replicas/connections, real R2 checksum round-trip, retention enforcement, tunnel failover, credential rotation, OTel observability and SHA-bound evidence.

## Rollback

Before runtime certification, rollback is logical rather than destructive: stop deployment rollout or scale down the not-yet-certified Kubernetes deployment, revoke/rotate the OpenBao-held tunnel token, revoke the dedicated R2 parent token, and keep Cloudflare resources quarantined for investigation. Automated deletion is prohibited in this phase because deleting a tunnel/bucket would destroy evidence and can conflict with Bucket Lock.
