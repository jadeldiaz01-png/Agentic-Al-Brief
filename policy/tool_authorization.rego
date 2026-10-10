package agentic_ai_brief.tool_authorization

# PREPARE_ONLY: permissions are evaluated outside the LLM. No write authority
# can be inferred from a model-generated approval boolean or MCP annotation.
# A separately certified external approval adapter is required before an
# additional allow rule for writes may be introduced.
default allow := false

allow if {
  input.source_trust == "verified"
  input.read_only == true
  input.external_write == false
  input.financial == false
  input.identity_or_legal == false
}
