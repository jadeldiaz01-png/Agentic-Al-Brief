# Agentic-AI-Brief Security Model 2026

## Trust boundaries

1. Untrusted: internet content, documents, emails, user-provided files, MCP metadata and tool output.
2. Research: agents may parse and reason over untrusted content but receive no production credentials.
3. Policy: deterministic authorization evaluates every side effect. Untrusted content cannot alter policy or grant privilege.
4. Execution: approved tools run with least privilege, scoped identities and bounded network/data access.
5. Evidence: immutable/append-oriented audit records capture decision, approval, tool, source and artifact provenance.

## Threats and mandatory controls

- Direct/indirect prompt injection: isolate retrieved instructions as data; system/tool policy is authoritative.
- Tool/MCP poisoning: pin trusted servers/tools, verify identity and schemas, do not trust descriptions/annotations, require policy evaluation before invocation.
- Data exfiltration: egress allowlists, secret redaction, no production secrets in prompts, logs or browser/computer-use sandboxes.
- Confused deputy: audience-bound authorization, no token passthrough, separate upstream credentials.
- Privilege escalation: default deny, least privilege, workload identity, short-lived credentials, explicit approvals.
- Memory poisoning: provenance on memory writes, confidence/evidence type, quarantine untrusted memories, support expiry/forgetting.
- Malicious documents: parse in unprivileged sandbox; never execute embedded instructions/macros as authority.
- Approval bypass: approval state is durable and bound to exact tool, arguments, actor and policy version.
- Autonomous destructive actions: kill switch and deterministic side-effect guard are outside the LLM.

## Credential policy

OpenBao workload identity is preferred. Static long-lived production tokens are forbidden in source, prompts and agent memory. MCP OAuth access tokens must be audience-bound, short-lived where possible, and never passed unchanged to downstream services.

## Telemetry privacy

Record operation names, model, token counts, latency, tool identity, policy decision and error classes. Prompt/completion/tool content is opt-in only because it may contain user, proprietary or PII data. Apply filtering, truncation and retention policy before export.

## Release security

Production release requires dependency audit, SBOM, SLSA provenance, artifact signing/verification, immutable CI actions, exact source SHA and container digest, and verified rollback/kill-switch runbooks.
