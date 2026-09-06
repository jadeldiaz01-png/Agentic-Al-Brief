# Secure Runtime Connector — Tailscale + GitHub JIT + Kubernetes

## Decision

Use Tailscale Personal as the private network layer and GitHub JIT/ephemeral self-hosted runners as the execution bridge to the Kubernetes runtime. This avoids exposing SSH or the Kubernetes API to the public Internet and does not depend on ConoHa VPS.

This repository remains fail-closed: connector readiness does not imply `RUNTIME_VERIFIED` or `PRODUCTION_GO`.

## Why this path

- Tailscale Personal provides a free tier suitable for individual secure connectivity and supports SSH/Kubernetes use cases.
- GitHub recommends ephemeral/JIT runners for autoscaling and warns against persistent self-hosted runners for public repositories.
- The runner reaches GitHub using outbound HTTPS; no inbound GitHub port is required on the runtime host.
- Kubernetes access is namespace-scoped and must not have cluster-admin or Secret read/list permissions.

## Required topology

```text
ChatGPT / authorized GitHub control plane
                |
                v
      workflow_dispatch only
                |
                v
        clean JIT/ephemeral runner
                |
        Tailscale private network
                |
                v
      Kubernetes API (private/TLS)
                |
                v
    namespace: agentic-ai-brief-runtime
```

## Host prerequisites

Install and authenticate these components on the clean runner image or disposable VM before the privileged job starts:

- GitHub Actions runner registered as JIT or ephemeral, single-job lifecycle.
- Tailscale authenticated using an ephemeral or otherwise short-lived machine identity.
- `kubectl` configured with a short-lived Kubernetes identity.
- No static kubeconfig token, long-lived Tailscale auth key, private SSH key, or OpenBao token stored in the repository.

The preferred Kubernetes principal is a dedicated ServiceAccount or another short-lived exec credential scoped to `agentic-ai-brief-runtime`.

## Minimum Kubernetes RBAC

Grant only the exact operations needed for runtime deployment and drills. Explicitly deny or omit:

- `*` verbs/resources
- cluster-admin
- get/list/watch on Secret objects
- access to namespaces unrelated to Agentic-AI-Brief
- unrelated pod exec

Before any deployment, run:

```bash
RUNTIME_NAMESPACE=agentic-ai-brief-runtime \
EXPECTED_KUBE_CONTEXT=<expected-context> \
bash scripts/secure_runtime_connector_preflight.sh
```

A non-zero exit is `CONNECTOR_NO_GO`.

## GitHub workflow

`.github/workflows/secure-runtime-connector-preflight.yml` is intentionally `workflow_dispatch` only and requires the existing self-hosted labels:

- `self-hosted`
- `linux`
- `x64`
- `agentic-ai-brief-runtime`

It references the protected GitHub Environment `agentic-ai-brief-runtime`, uses read-only repository permissions and refuses any non-`workflow_dispatch` event.

## ChatGPT connection boundary

At the time this integration was added, the ChatGPT plugin directory available to this session did not expose a Tailscale, Kubernetes, SSH, or Cloudflare connector. Therefore this repository integration prepares the authorized execution bridge but does not falsely claim that ChatGPT has direct shell access to the host.

The final external control-plane requirement is one of:

1. an authorized GitHub connector action capable of `workflow_dispatch`, or
2. a separately registered custom MCP/connector that invokes only the allowlisted preflight/deployment workflow, never arbitrary shell.

The second option should use OAuth/short-lived identity, strict tool schemas, no raw shell tool, approval for privileged deployment actions, and complete audit logging.

## Promotion rule

`CONNECTOR_READY` requires one clean ephemeral/JIT execution with all connector preflight checks green. Only after that may P0-C execute the runtime drills and produce the authenticated runtime evidence bundle.
