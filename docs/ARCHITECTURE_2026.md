# Agentic-AI-Brief — Target Architecture 2026

## Decision rule

Every production change must justify: PROBLEM -> EVIDENCE -> ALTERNATIVES -> DECISION -> BENEFIT -> COST -> RISK -> VALIDATION.

## Planes

1. Research: public-source discovery, source verification, adversarial search, claim extraction.
2. Agentic: bounded supervisor plus specialist agents; agents may propose but never authorize critical side effects.
3. Durable execution: Temporal owns long waits, retries, timers, replay, and human approval state.
4. Policy: OPA/Rego is authoritative for tool and side-effect authorization. Default deny.
5. Tooling: MCP and typed function tools are behind an application policy gateway. Tool metadata and untrusted outputs never grant privilege.
6. Knowledge: PostgreSQL is source of truth; episodic memory lives in relational/event tables; pgvector is optional semantic memory and must preserve provenance.
7. Evidence: every source, claim, approval, tool call, model decision and artifact is attributable and hashable.
8. Operations: OpenTelemetry traces model turns, tool calls, approvals, latency and cost without recording sensitive content by default.
9. Identity: OpenBao workload identity / short-lived credentials; no static production tokens in agent prompts or repositories.
10. Supply chain: immutable CI actions, dependency audit, SBOM, SLSA provenance and Sigstore verification before release.

## Orchestration

Prefer one supervisor with bounded specialists:

- ResearchAgent: discovery and source collection.
- VerificationAgent: contradicting evidence, freshness, provenance and claim support.
- BriefWriterAgent: synthesis from verified claims only.
- Optional CostRouter: deterministic model choice based on eval-backed task class.

Use `Agent.as_tool()` for bounded specialist work. Use handoffs only when the specialist must own the next interaction. Critical state transitions belong to deterministic code/Temporal, not LLM conversation state.

## Retrieval

Start with PostgreSQL full-text + pgvector. Add dedicated search infrastructure or GraphRAG only after an evaluation dataset demonstrates material quality or latency improvement.

## Production evidence levels

- IMPLEMENTED: source/config exists.
- CI_VERIFIED: tests/static/security gates pass.
- RUNTIME_VERIFIED: target environment proves database, identity, Temporal replay and trace roundtrip.
- PRODUCTION_VERIFIED: quality, safety, SLO, backup/restore, kill switch and supply-chain attestations all pass.

CI alone can never promote PRODUCTION_VERIFIED.
