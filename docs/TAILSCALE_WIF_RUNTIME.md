# Tailscale Workload Identity Federation for the runtime connector

This repository uses Tailscale Workload Identity Federation (WIF) for the privileged runtime connector instead of a long-lived Tailscale auth key.

## Security properties

- GitHub Actions OIDC (`id-token: write`) is the authentication root for the workflow.
- The Tailscale GitHub Action is pinned to immutable commit `780049a30b6ff5c378a9e7b389d15ece7a204888` (v4.1.3).
- The workflow creates an ephemeral Tailscale node tagged `tag:agentic-ai-brief-runtime`.
- The node is cleaned up after the job.
- Kubernetes access remains namespace-scoped and the preflight rejects cluster-admin and Secret read/list authority.
- No public SSH or public Kubernetes API is required.
- `CONNECTOR_READY` remains fail-closed until a real workflow_dispatch execution succeeds against the intended cluster.

## Required protected Environment configuration

Environment: `agentic-ai-brief-runtime`

Required secrets:

- `TS_OAUTH_CLIENT_ID`: Tailscale federated identity client ID.
- `TS_AUDIENCE`: Tailscale federated identity audience.

The Tailscale trust credential must have writable `auth_keys` scope and be restricted to `tag:agentic-ai-brief-runtime`.

## Tailnet policy

Grant `tag:agentic-ai-brief-runtime` only the network reachability required to contact the intended Kubernetes API endpoint and explicitly required observability endpoints. Do not grant broad tailnet access.

## Promotion rule

A configuration or successful GitHub CI check is not evidence of real connectivity. Promotion to `CONNECTOR_READY` requires one authentic `workflow_dispatch` run where:

1. Tailscale WIF authentication succeeds.
2. The ephemeral node is created and usable.
3. The expected kubectl context is active.
4. The runtime namespace is reachable.
5. cluster-admin authority is absent.
6. Secrets read/list authority is absent.
7. The Kubernetes API uses TLS.
8. The fail-closed preflight exits zero.
