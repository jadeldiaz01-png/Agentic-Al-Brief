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
