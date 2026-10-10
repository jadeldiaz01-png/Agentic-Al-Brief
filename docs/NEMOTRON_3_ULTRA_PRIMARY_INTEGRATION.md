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
- Operator-controlled opt-in: AGIA_PRIMARY_LLM_PROVIDER=nvidia.
- Protected runtime-only key: NVIDIA_API_KEY; do not paste its value into chat,
  GitHub, workflows, logs, browser clients, documentation or prompts.
- No automatic fallback when the requested NVIDIA route is unhealthy.
- Initial max_tokens 4096 and reasoning_budget 1024 are proposed limits, not
  measured safe operating envelopes.

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
Keep AGIA_PRIMARY_LLM_PROVIDER unset for this PR.

This PR must not add, change or rotate secrets; start a real inference;
configure network egress; run workflow_dispatch; deploy; merge automatically;
or enable trading and autonomous financial operations.

Official reference: https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b
