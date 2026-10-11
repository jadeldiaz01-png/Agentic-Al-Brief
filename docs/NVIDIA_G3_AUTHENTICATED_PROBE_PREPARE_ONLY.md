# NVIDIA Nemotron 3 Ultra — G3 authenticated probe (PREPARE_ONLY)

This package prepares a **single-request** authenticated inference test. It does not
run real inference and does not activate the provider in the agent runtime.

## Fixed request

- Official API endpoint: https://integrate.api.nvidia.com/v1/chat/completions
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Only one request, max 64 output tokens, non-streaming, 45-second timeout,
  retries disabled; deterministic fixed synthetic prompt and exact expected marker.
- Thinking disabled; no tools, no arbitrary user prompts, no private information,
  no JSON structured-output certification at this stage.
- Response validation requires model, marker, stop finish reason and numeric
  usage data within the quote; evidence contains only sanitized status and counts.
- Input quote assumes at most 128 tokens, but this is **not server-enforced**;
  the eventual authenticated test must record actual usage and explicitly report
  whether the quote was exceeded.

## Finance and security

- Autonomous spend allowed: USD 0. No verified account-specific hosted
  NVIDIA pricing, entitlement or invoice budget is available.
- Conservative input/output rate estimator rounds UP to USD 0.000001;
  this is **not a guaranteed cap on provider billing**. Free trial labels are
  not sufficient evidence that this particular API key is free.
- Source constant G3_AUTHENTICATED_PROBE_LOCKED=True forbids every live call
  even when a credential or environment variable is present. The runtime
  NEMOTRON_ACTIVATION_LOCKED=True remains unchanged.
- All client SDK errors are redacted; no key, request, response or raw SDK
  exception may be logged or published. No automatic fallback to OpenAI.
- Only synthetic offline unit tests use mocked OpenAI clients.

## Independent human gates before a call

1. Pass exact-SHA CI and independent review of this PREPARE_ONLY PR.
2. Authorize merge separately; certify actual provider pricing and account
   quotas without reading any secret values.
3. Certify a strict externally enforced zero-charge entitlement or obtain
   separate explicit spending authorization. A quote alone is insufficient.
4. Prepare an environment-approved exact-main-SHA GitHub Actions runner for
   a **single attempt** (run_attempt=1, reviewer flotaopd-del, restricted
   credentials, no raw artifacts/logs, no retries).
5. Separate reviewed PR to unlock the G3 probe only, preserving runtime
   NVIDIA activation lock and no provider failover.
6. Authorize exactly one authenticated call against exact main SHA and inspect
   only redacted usage/result. Tool calling, JSON validation and deployment
   require independent later approvals.

No new workflow_dispatch, external calls, secrets, deployment or merge is
authorized in this proposal.

NVIDIA source pages:
https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b
https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-ultra-550b-a55b-infer


## G3 billing/readiness evidence update (2026-10-11; public-only)

**Confirmed publicly**: the NVIDIA-hosted Nemotron 3 Ultra model page displays
"Free Endpoint: Available" and "Start building with a free API endpoint".
NVIDIA NIM documents free developer access for **prototyping** and distinguishes
development/testing from production. Sources:

- https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b
- https://docs.api.nvidia.com/nim/docs/product
- https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-ultra-550b-a55b-infer

**Not certified for the protected NVIDIA_API_KEY**: model entitlement, remaining
credits/quotas, billing account status, pricing after trial or exhausted credits,
hard provider-enforced zero-spend conditions, exact API rate limits, and contractual
rights for any commercial or production usage. Public "Free Endpoint" messaging
does NOT prove this secret is entitled or that unexpected charges are impossible.

**Before any authenticated request**, a human authorized for the account should
check the official NVIDIA API catalog while authenticated, recording only
redacted evidence of service/account tier, remaining credits, whether billing
is enabled or automatic charge is possible, current quota/rate limits and
an explicit account-specific no-charge guarantee or separately approved
spending ceiling. Never copy/paste the NVIDIA_API_KEY or account identifiers.

Source-controlled independent guards added to the G3 probe:

- G3_AUTHENTICATED_PROBE_LOCKED=True (unchanged)
- G3_BILLING_CERTIFICATION_LOCKED=True (new)
- G3_EXECUTION_APPROVAL_LOCKED=True (new)

Clearing only the probe lock, using zero-valued quotes, or adding environment
variables cannot bypass the additional guards. Removing any lock requires
separate independently reviewed source code and explicit authorization.
Offline tests simulate all gates with in-memory dummy clients; that does
not certify NVIDIA connectivity, usage, or billing.

**Decision as of this revision: G3_ACCOUNT_BILLING=NO_GO**.
No live calls, workflow dispatches, changes to secrets, provider activation,
merges or deployments are authorized by this document.
