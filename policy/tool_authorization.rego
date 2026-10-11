package agentic_ai_brief.tool_authorization

# PREPARE_ONLY: permissions are evaluated outside the LLM. No write authority
# can be inferred from a model-generated approval boolean or MCP annotation.
# A separately certified external approval adapter is required before an
# additional allow rule for writes may be introduced.
default allow := false

allow if {
  # Match Python ToolIntent's constructor: reject any unknown JSON property.
  # Optional human_approval_verified defaults to false in both engines.
  is_object(input)
  allowed_keys := {
    "tool_name",
    "read_only",
    "external_write",
    "financial",
    "identity_or_legal",
    "requires_human_approval",
    "source_trust",
    "human_approval_verified",
  }
  count(object.keys(input) - allowed_keys) == 0

  # All permission fields are typed strictly before applying any allow rule.
  # The verified-approval field is optional (Python dataclass defaults False).
  is_string(input.tool_name)
  count(input.tool_name) > 0
  is_boolean(input.requires_human_approval)
  is_boolean(object.get(input, "human_approval_verified", false))
  input.source_trust == "verified"
  input.read_only == true
  input.external_write == false
  input.financial == false
  input.identity_or_legal == false
}
