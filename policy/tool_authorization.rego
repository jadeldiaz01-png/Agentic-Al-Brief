package agentic_ai_brief.tool_authorization

default allow := false

allow if {
  input.source_trust == "verified"
  input.read_only == true
  input.external_write == false
  input.financial == false
  input.identity_or_legal == false
}

allow if {
  input.source_trust == "verified"
  input.external_write == true
  input.requires_human_approval == true
  input.human_approval_verified == true
  input.financial == false
  input.identity_or_legal == false
}
