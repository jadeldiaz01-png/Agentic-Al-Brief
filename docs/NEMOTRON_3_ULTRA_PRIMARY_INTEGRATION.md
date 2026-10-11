# Nemotron 3 Ultra — candidate primary model (G0 PREPARE_ONLY)

This repository is the human-confirmed owner of Multi-Agent Orchestration
under project PRJ-INTEL-001 / BRIEF-LAB. The infrastructure and
certification owner remains jadeldiaz01-png/universal-multi-project-runtime.
This documentation does not supersede the shared runtime registry, which
requires a separate controlled update.

## Architecture and deployment boundary

- Primary model target: nvidia/nemotron-3-ultra-550b-a55b.
- NVIDIA OpenAI-compatible API base: https://integrate.api.nvidia.com/v1.
- Transport: AsyncOpenAI + OpenAIChatCompletionsModel from OpenAI Agents SDK.
- Agent topology remains supervisor, research, verifier, writer.
- DEFAULT selection is the existing OpenAI model; no NVIDIA inference is enabled.
- Provider selection is CODE-LOCKED in this revision. The environment selector alone cannot authorize NVIDIA; a separate reviewed promotion commit and runtime evidence are required.
- Protected runtime-only key: NVIDIA_API_KEY; do not paste its value into chat,
  GitHub, workflows, logs, browser clients, documentation or prompts.
- No automatic fallback when the requested NVIDIA route is unhealthy.
- Candidate max_tokens 4096; NVIDIA chat_template_kwargs.enable_thinking and medium_effort for research/verification; thinking disabled for writer and supervisor pending actual JSON/tool-calling certification. These are not measured safe operating envelopes.

## Separate human and evidence gates

1. CI of the exact draft PR head, including lint, mypy, tests and supply-chain.
2. Independently review model selection, prompt/response confidentiality and
   policy-bound tool invocation. Prompt text never authorizes critical writes.
3. Verify the presence of the runtime key with output restricted to present/absent,
   and separately verify the key is scoped to the intended service identity.
4. Only after a new human approval, run exactly one minimally sized authenticated
   NVIDIA completion. A successful GET /v1/models does not establish entitlement.
5. Certify real tool calling and typed BriefResult writer output, including
   malformed JSON, 401/403/404/429/5xx, rate limits, usage/cost and timeout cases.
6. Certify SLO, egress policy, audit redaction, fail-closed behavior and rollback.
7. Separate approvals for changing runtime selection, secrets, privileged workflows,
   external access, merge and any deployment. Production remains NO_GO.

## Critical safety conditions

NVIDIA prompts, replies and tool payloads may include customer data.
The runtime must enforce consent, minimization, retention policy, PII redaction
and provider privacy assessment before external transmission.
Never use an LLM reply or MCP tool output to grant privileges.
Keep AGIA_PRIMARY_LLM_PROVIDER unset for this PR. No presence-only workflow or secret value authorizes inferencing.

This PR must not add, change or rotate secrets; start a real inference;
configure network egress; run workflow_dispatch; deploy; merge automatically;
or enable trading and autonomous financial operations.

Official reference: https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b

## P1 independent review addendum

- `NEMOTRON_ACTIVATION_LOCKED = True` prevents environment-only activation.
  Removing this source lock requires a separate human-approved revision, exact
  deployed SHA verification and actual provider/tool/JSON safety evidence.
- NVIDIA's published examples use `chat_template_kwargs` for thinking and
  `medium_effort`; the previous arbitrary `reasoning_budget` and
  `reasoning_effort` request fields are removed.
- Agent SDK strict `BriefResult` validation is exercised with malformed
  responses in offline tests. Passing these fixtures is NOT an authenticated
  test of NVIDIA's JSON schema feature or tool-calling behavior.
- Python and Rego policies now both deny **all external writes**, even if a
  model/tool supplies `requires_human_approval=true` and
  `human_approval_verified=true`. A trusted approval receipt verified by an
  external authority does not yet exist; no write allowance is introduced.
- No model, workflow, runtime, secret or GitHub permissions are activated.


## G1 provider routing plan — PREPARE_ONLY (2026-10-11)

- **Target primary:** NVIDIA Nemotron 3 Ultra; this is the desired
  architecture, not an activated network connection.
- **Target secondary:** existing OpenAI route, for separately approved
  human-controlled selection only. The existing runtime default remains
  OpenAI until NVIDIA credentials, real inference, tool calling, JSON output,
  egress, costs, rollback and human promotion are certified.
- **No automatic failover:** if NVIDIA is selected while its code lock is
  in force, the application raises a fail-closed configuration error; it
  never silently routes that request to OpenAI, even with override flags.
- `describe_provider_routing()` is a pure declarative plan: importing it
  or reading the manifest does not instantiate clients or make any calls.
- `NEMOTRON_ACTIVATION_LOCKED=True` remains in source; removing it,
  changing the default provider, allowing fallback, and deploying each
  require new, independent, exact-SHA human gates.
- **Secret presence PREPARE_ONLY:** the GitHub Actions manual, protected
  environment job is independent of the desired provider selector. It
  checks only whether the protected `NVIDIA_API_KEY` value is nonempty,
  emits YES/NO, and never connects to the provider or selects a model.
  It still requires exact main SHA, manual confirmation and environment
  reviewer approval. Merging this PR **does not authorize any dispatch**.
- No provider-level credentials are included in this PR, no NVIDIA calls
  are made, and production remains unauthorized.
