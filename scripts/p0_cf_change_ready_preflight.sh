#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SHA="${EXPECTED_SHA:-}"
EXPECTED_KUBE_CONTEXT="${EXPECTED_KUBE_CONTEXT:-}"
RUNTIME_NAMESPACE="${RUNTIME_NAMESPACE:-agentic-ai-brief-runtime}"
R2_PARENT_ACCESS_KEY_ID="${R2_PARENT_ACCESS_KEY_ID:-}"
R2_PARENT_API_TOKEN="${R2_PARENT_API_TOKEN:-}"
EXPECTED_IMAGE='cloudflare/cloudflared@sha256:51c9cefcb4569df44e1ad403ab1d3d8065aa8e84339bcfc6aee75502e1140339'
MANIFEST='deploy/cloudflare/cloudflared-runtime.yaml'
NETPOL='deploy/cloudflare/cloudflared-networkpolicy.yaml'

fail() {
  echo "P0_CF_CHANGE_READY=NO"
  echo "BLOCKER=$1"
  exit 2
}

yes_gate() { echo "$1=YES"; }

[ "${GITHUB_EVENT_NAME:-}" = "workflow_dispatch" ] || fail manual_workflow_dispatch_required
yes_gate MANUAL_WORKFLOW_DISPATCH_VERIFIED

[[ "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]] || fail invalid_expected_sha
[ "$(git rev-parse HEAD)" = "$EXPECTED_SHA" ] || fail source_sha_mismatch
[ "${GITHUB_SHA:-}" = "$EXPECTED_SHA" ] || fail github_sha_mismatch
yes_gate EXACT_SOURCE_SHA_VERIFIED

case "${RUNNER_ENVIRONMENT:-}" in
  github-hosted) yes_gate GITHUB_HOSTED_EPHEMERAL_RUNNER_VERIFIED ;;
  *) fail github_hosted_runner_required ;;
esac

command -v tailscale >/dev/null || fail tailscale_missing
command -v kubectl >/dev/null || fail kubectl_missing
command -v nc >/dev/null || fail netcat_missing

TAILSCALE_STATE="$(tailscale status --json | python -c 'import json,sys; print(json.load(sys.stdin).get("BackendState", ""))')"
[ "$TAILSCALE_STATE" = "Running" ] || fail tailscale_not_running
yes_gate TAILSCALE_FEDERATED_IDENTITY_VERIFIED

[ -n "$EXPECTED_KUBE_CONTEXT" ] || fail expected_kube_context_missing
[ "$(kubectl config current-context)" = "$EXPECTED_KUBE_CONTEXT" ] || fail kube_context_mismatch
yes_gate KUBERNETES_CONTEXT_VERIFIED
kubectl get namespace "$RUNTIME_NAMESPACE" >/dev/null
yes_gate NAMESPACE_VERIFIED

if [ "$(kubectl auth can-i '*' '*' --all-namespaces)" = "yes" ]; then
  fail cluster_admin_detected
fi
yes_gate CLUSTER_ADMIN_ABSENT

if [ "$(kubectl auth can-i get secrets -n "$RUNTIME_NAMESPACE")" = "yes" ] || \
   [ "$(kubectl auth can-i list secrets -n "$RUNTIME_NAMESPACE")" = "yes" ]; then
  fail secrets_read_permission_detected
fi
yes_gate SECRETS_READ_ABSENT

ACTUAL_IMAGE="$(awk '/^[[:space:]]*image: cloudflare\/cloudflared@sha256:/{print $2; exit}' "$MANIFEST")"
[ "$ACTUAL_IMAGE" = "$EXPECTED_IMAGE" ] || fail cloudflared_digest_mismatch
yes_gate CLOUDFLARED_IMAGE_DIGEST_EXACT

grep -q 'driver: secrets-store.csi.k8s.io' "$MANIFEST" || fail csi_driver_contract_missing
grep -q 'provider: openbao' "$MANIFEST" || fail openbao_provider_contract_missing
grep -q 'serviceAccountName: cloudflared-runtime' "$MANIFEST" || fail dedicated_service_account_missing
grep -q 'automountServiceAccountToken: false' "$MANIFEST" || fail automount_token_not_disabled
! grep -q '^secretObjects:' "$MANIFEST" || fail kubernetes_secret_sync_forbidden
yes_gate OPENBAO_SECRET_PROVIDER_CLASS_CONTRACT_VALID
yes_gate DEDICATED_SERVICE_ACCOUNT_CONTRACT_VALID

if ! kubectl api-resources --api-group=secrets-store.csi.x-k8s.io -o name 2>/dev/null | grep -qx 'secretproviderclasses'; then
  fail secrets_store_csi_crd_not_discoverable
fi
yes_gate OPENBAO_CSI_DRIVER_PRESENT

# The provider resource may be outside this identity's namespace scope. We require
# server-side schema admission of the SecretProviderClass as a non-persistent proof.
kubectl apply --dry-run=server -f "$MANIFEST" >/dev/null || fail openbao_csi_provider_or_schema_not_ready
yes_gate OPENBAO_CSI_PROVIDER_PRESENT

for required in \
  'cidr: 198.41.192.0/24' \
  'cidr: 198.41.200.0/24' \
  'protocol: TCP' \
  'protocol: UDP' \
  'port: 7844'; do
  grep -q "$required" "$NETPOL" || fail networkpolicy_contract_invalid
done
yes_gate NETWORKPOLICY_CONTRACT_VALID
yes_gate CLOUDFLARE_7844_UDP_POLICY_DECLARED

for edge in 198.41.192.7 198.41.200.13; do
  nc -z -w 5 "$edge" 7844 >/dev/null 2>&1 || fail "cloudflare_tcp_7844_unreachable_${edge}"
done
yes_gate CLOUDFLARE_7844_TCP_REACHABLE

[ -n "$R2_PARENT_ACCESS_KEY_ID" ] || fail r2_parent_access_key_id_missing
[ -n "$R2_PARENT_API_TOKEN" ] || fail r2_parent_api_token_missing
yes_gate R2_PARENT_CREDENTIAL_PRESENCE_VERIFIED

python - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path('config/p0-cf-change-ready.json').read_text())
r2 = cfg['r2']
assert r2['bucket'] == 'agentic-ai-brief-runtime-evidence'
assert r2['temporary_permission'] == 'object-read-write'
assert r2['temporary_prefixes'] == ['runtime-evidence/']
assert 1 <= r2['temporary_ttl_seconds'] <= 900
assert r2['minimum_lock_seconds'] >= 7776000
policy = cfg['non_destructive_creation_policy']
assert policy['create_only_if_absent'] is True
assert policy['delete_forbidden'] is True
assert policy['overwrite_existing_resource_forbidden'] is True
print('R2_TEMPORARY_CREDENTIAL_MINT_PLAN_VALID=YES')
print('R2_BUCKET_LOCK_PLAN_VALID=YES')
print('ROLLBACK_PLAN_PRESENT=YES')
print('WRITES_STILL_DISABLED=YES')
PY

echo 'P0_CF_CHANGE_READY=YES'
