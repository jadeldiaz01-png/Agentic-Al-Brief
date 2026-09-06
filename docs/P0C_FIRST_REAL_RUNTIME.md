# P0-C — First Real Certified Runtime Execution

Baseline source SHA: `eb749e5911f7586226a4ba8da442e86ec675b379`.

P0-C is fail-closed. A merge, configuration file, mocked test, service health page, or boolean `verified=true` is not runtime evidence by itself. Promotion is allowed only when all artifacts below are produced by one real execution, share the exact deployed source SHA and one `execution_id`, contain no secret material, and are independently hash-bound into `runtime-evidence.json`.

## Required runtime evidence

- `runner-security.json`: ephemeral/JIT runner, single-job lifecycle, no pull-request trigger for the privileged runtime workflow, clean execution environment, and external runner-log retention all verified.
- `postgresql-pitr.json`: WAL archiving, physical base backup, restore drill and restore target all verified on a disposable restored instance.
- `openbao-identity.json`: Kubernetes ServiceAccount authentication, absence of a static OpenBao token, and a short-lived credential verified.
- `opa-enforcement.json`: one allowed case, one denied case, and an auditable OPA `decision_id` verified.
- `temporal-replay.json`: completed durable workflow history replayed successfully with no nondeterminism.
- `otel-roundtrip.json`: Collector health plus a synthetic trace exported and observed in the configured backend.
- `crash-recovery.json`: worker/activity failure followed by retry/restart with no duplicate persistence.
- `artifact-signature.json`: Cosign verification, expected OIDC identity and artifact digest verified.
- `sbom-verification.json`: CycloneDX schema validated and bound to the exact artifact digest.
- `slsa-provenance-verification.json`: provenance schema, subject digest and source SHA verified.

## Public-repository runner security

This repository is public. GitHub recommends against persistent self-hosted runners for public repositories because untrusted workflow code can persistently compromise the host. P0-C therefore requires an ephemeral or just-in-time runner that accepts at most one privileged job and is destroyed or cleaned after completion. The runtime workflow must remain `workflow_dispatch`-only, and runner logs must be forwarded to an external log store before certification.

A helper is included at `scripts/register_ephemeral_runner.sh`. It refuses root execution, requires an exact runner version and published tarball SHA-256, requires a time-limited registration token, registers the custom `agentic-ai-brief-runtime` label, uses `--ephemeral`, and disables automatic runner updates so the binary remains explicitly pinned. The registration token must never be committed or written into runtime evidence.

## Runtime sequence

1. Provision a clean isolated Linux x64 VM/host context for the one-job runner. Configure external runner-log forwarding first.
2. Obtain a time-limited GitHub runner registration token or JIT configuration using an authorized administrative path. Prefer JIT when available. Register only labels `self-hosted`, `linux`, `x64`, `agentic-ai-brief-runtime` and produce sanitized `runner-security.json`.
3. Deploy the exact signed application artifact by digest. Record source SHA and image/package digest before any drill.
4. PostgreSQL 18: enable durable WAL archiving, take a physical base backup, insert a before-marker, create a restore point, insert an after-marker, restore a disposable clone to the restore point, verify before-marker present and after-marker absent.
5. Temporal: execute an authentic `BriefRequest` through Research → Verification → deterministic Policy → Persistence. Export workflow history and replay it with the deployed workflow code. Then terminate/restart a worker during an activity and prove retry/recovery without duplicate persisted brief/evidence rows.
6. OpenBao: authenticate the workload using Kubernetes ServiceAccount identity/Auto-Auth; prove no static token is supplied to the application and record only sanitized identity/TTL/policy evidence.
7. OPA: evaluate deterministic allow and deny fixtures through the same production policy endpoint used by the worker; record returned decision identifiers and policy/bundle digest without sensitive inputs.
8. OpenTelemetry: emit a synthetic trace from the worker, prove Collector health, export success and backend observation of the same trace identifier.
9. Supply chain: verify artifact signature, SBOM and provenance against the exact deployed digest and source SHA.
10. Write the ten sanitized JSON artifacts to `/var/lib/agentic-ai-brief/p0c-evidence` with restrictive permissions and the same unique `execution_id`.
11. Execute `p0c-runtime-certification` with the exact deployed SHA and execution id. Only a zero-blocker certificate may promote `CI_VERIFIED` to `RUNTIME_VERIFIED`.

## Production remains separately gated

`RUNTIME_VERIFIED` is not `PRODUCTION_VERIFIED`. Production still requires adversarial agent evaluations, citation/quality thresholds, SLO/error-budget evidence, alerting, backup/DR repetition, kill-switch proof, sustained operation and incident-response readiness.

## Primary technical basis

PostgreSQL 18 documents continuous archiving/PITR as WAL archiving plus base backup and recovery. OpenBao Kubernetes Auto-Auth reads the workload ServiceAccount token and exchanges it through the Kubernetes auth method. OPA decision logging provides auditable decision events and decision IDs. OpenTelemetry Collector health checks must be paired with an actual telemetry round-trip; health alone is not delivery proof. GitHub recommends ephemeral self-hosted runners for autoscaling and warns that persistent self-hosted runners should almost never be attached to public repositories.
