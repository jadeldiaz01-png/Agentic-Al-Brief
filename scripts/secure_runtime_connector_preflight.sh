#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${RUNTIME_NAMESPACE:-agentic-ai-brief-runtime}"
EXPECTED_CONTEXT="${EXPECTED_KUBE_CONTEXT:-}"

fail() { echo "CONNECTOR_NO_GO:$1" >&2; exit 2; }
pass() { echo "CONNECTOR_PASS:$1"; }

command -v tailscale >/dev/null 2>&1 || fail "tailscale_missing"
command -v kubectl >/dev/null 2>&1 || fail "kubectl_missing"

# Tailscale must be connected. Do not print full status JSON because it can
# contain peer metadata that is unnecessary for certification logs.
TAILSCALE_STATE="$(tailscale status --json 2>/dev/null | python -c 'import json,sys; print(json.load(sys.stdin).get("BackendState", ""))')" || true
[[ "$TAILSCALE_STATE" == "Running" ]] || fail "tailscale_not_running"
pass "tailscale_connected"

CURRENT_CONTEXT="$(kubectl config current-context 2>/dev/null)" || fail "kubectl_context_unavailable"
[[ -n "$CURRENT_CONTEXT" ]] || fail "kubectl_context_empty"
if [[ -n "$EXPECTED_CONTEXT" && "$CURRENT_CONTEXT" != "$EXPECTED_CONTEXT" ]]; then
  fail "unexpected_kube_context"
fi
pass "kubectl_context_verified"

kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || fail "runtime_namespace_unreachable"
pass "runtime_namespace_reachable"

# Fail closed on dangerous authority. The connector must not be cluster-admin.
if kubectl auth can-i '*' '*' --all-namespaces 2>/dev/null | grep -qx 'yes'; then
  fail "cluster_admin_forbidden"
fi
pass "cluster_admin_absent"

# Runtime connector must not be able to read Kubernetes Secret objects.
if kubectl auth can-i get secrets -n "$NAMESPACE" 2>/dev/null | grep -qx 'yes'; then
  fail "secrets_read_forbidden"
fi
if kubectl auth can-i list secrets -n "$NAMESPACE" 2>/dev/null | grep -qx 'yes'; then
  fail "secrets_list_forbidden"
fi
pass "secrets_read_absent"

# Require useful but namespace-scoped operational access.
for check in \
  "get deployments" \
  "get pods" \
  "get jobs"; do
  verb="${check%% *}"
  resource="${check#* }"
  if ! kubectl auth can-i "$verb" "$resource" -n "$NAMESPACE" 2>/dev/null | grep -qx 'yes'; then
    fail "missing_${verb}_${resource}_permission"
  fi
done
pass "namespace_scope_verified"

# Refuse accidental public-server configuration when an explicit private
# suffix/pattern is supplied. This is intentionally optional because private
# Kubernetes endpoints can have many naming schemes.
API_SERVER="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null)"
[[ "$API_SERVER" == https://* ]] || fail "kube_api_tls_required"
if [[ -n "${EXPECTED_PRIVATE_API_PATTERN:-}" ]]; then
  [[ "$API_SERVER" == *"${EXPECTED_PRIVATE_API_PATTERN}"* ]] || fail "kube_api_not_private_expected_pattern"
fi
pass "kube_api_tls_verified"

cat <<EOF
CONNECTOR_READY
namespace=$NAMESPACE
context=$CURRENT_CONTEXT
security=fail_closed
EOF
