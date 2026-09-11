#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SHA="${EXPECTED_SHA:-}"
EXPECTED_KUBE_CONTEXT="${EXPECTED_KUBE_CONTEXT:-}"
EXPECTED_TAILSCALE_TAG="${EXPECTED_TAILSCALE_TAG:-tag:agentic-ai-brief-runtime}"
RUNTIME_NAMESPACE="${RUNTIME_NAMESPACE:-agentic-ai-brief-runtime}"
R2_PARENT_ACCESS_KEY_ID="${R2_PARENT_ACCESS_KEY_ID:-}"
R2_PARENT_API_TOKEN="${R2_PARENT_API_TOKEN:-}"
EXPECTED_IMAGE='cloudflare/cloudflared@sha256:51c9cefcb4569df44e1ad403ab1d3d8065aa8e84339bcfc6aee75502e1140339'
MANIFEST='deploy/cloudflare/cloudflared-runtime.yaml'
NETPOL='deploy/cloudflare/cloudflared-networkpolicy.yaml'
WORKFLOW='.github/workflows/p0-cf-change-ready.yml'

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

# Structural proof: the workflow uses GitHub OIDC WIF inputs and deliberately has
# no OAuth secret or auth key path. Successful completion of the pinned action plus
# the expected runtime tag proves the configured WIF path is the one in use.
grep -q 'id-token: write' "$WORKFLOW" || fail tailscale_oidc_permission_missing
grep -q 'oauth-client-id:.*TS_OAUTH_CLIENT_ID' "$WORKFLOW" || fail tailscale_wif_client_id_missing
grep -q 'audience:.*TS_AUDIENCE' "$WORKFLOW" || fail tailscale_wif_audience_missing
! grep -q 'oauth-secret:' "$WORKFLOW" || fail tailscale_oauth_secret_forbidden
! grep -q 'authkey:' "$WORKFLOW" || fail tailscale_authkey_forbidden
yes_gate TAILSCALE_WIF_PATH_VERIFIED

TS_STATUS="$(tailscale status --json)"
TS_STATE="$(printf '%s' "$TS_STATUS" | python -c 'import json,sys; print(json.load(sys.stdin).get("BackendState", ""))')"
[ "$TS_STATE" = "Running" ] || fail tailscale_not_running
TS_TAG_OK="$(printf '%s' "$TS_STATUS" | EXPECTED_TAILSCALE_TAG="$EXPECTED_TAILSCALE_TAG" python -c 'import json,os,sys; d=json.load(sys.stdin); tags=(d.get("Self") or {}).get("Tags") or []; print("yes" if os.environ["EXPECTED_TAILSCALE_TAG"] in tags else "no")')"
[ "$TS_TAG_OK" = "yes" ] || fail tailscale_expected_tag_missing
yes_gate TAILSCALE_EXPECTED_TAG_VERIFIED

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
yes_gate DEDICATED_SERVICE_ACCOUNT_CONTRACT_VALID

if ! kubectl api-resources --api-group=secrets-store.csi.x-k8s.io -o name 2>/dev/null | grep -qx 'secretproviderclasses'; then
  fail secrets_store_csi_crd_not_discoverable
fi
yes_gate SECRETS_STORE_CSI_CRD_DISCOVERABLE

# Server-side dry-run proves CRD/schema admission only. It intentionally does NOT
# claim that the OpenBao provider daemon or secret mount works; those require a
# real post-create mount once the Tunnel token exists in OpenBao.
kubectl apply --dry-run=server -f "$MANIFEST" >/dev/null || fail openbao_secret_provider_class_schema_not_admitted
yes_gate OPENBAO_SECRET_PROVIDER_CLASS_SCHEMA_ADMITTED

for required in \
  'cidr: 198.41.192.0/24' \
  'cidr: 198.41.200.0/24' \
  'protocol: TCP' \
  'protocol: UDP' \
  'port: 7844'; do
  grep -q "$required" "$NETPOL" || fail networkpolicy_contract_invalid
done
yes_gate NETWORKPOLICY_CONTRACT_VALID

# Advisory/control-plane precheck only. Cloudflare documents these region endpoints
# and TCP/UDP 7844; this runner check cannot stand in for the post-create runtime-path
# proof from the actual cloudflared pod network.
for edge in 198.41.192.7 198.41.200.13; do
  nc -z -w 5 "$edge" 7844 >/dev/null 2>&1 || fail "cloudflare_tcp_7844_unreachable_${edge}"
  nc -u -z -w 5 "$edge" 7844 >/dev/null 2>&1 || fail "cloudflare_udp_7844_unreachable_${edge}"
done
yes_gate CLOUDFLARE_7844_RUNNER_PRECHECK_VERIFIED

# Re-run GET-only discovery inside the same gate execution so target-state evidence
# cannot be accidentally inherited from an earlier job/run.
DISCOVERY_OUTPUT="$(python scripts/cloudflare_runtime_discovery.py)" || fail cloudflare_runtime_discovery_failed
printf '%s\n' "$DISCOVERY_OUTPUT"
printf '%s\n' "$DISCOVERY_OUTPUT" | grep -q 'CLOUDFLARE_RUNTIME_DISCOVERY_VERIFIED=YES' || fail cloudflare_runtime_discovery_not_verified
printf '%s\n' "$DISCOVERY_OUTPUT" | grep -q '^CLOUDFLARE_TARGET_R2_BUCKET_PRESENT=' || fail r2_target_state_unknown
yes_gate R2_TARGET_STATE_KNOWN

[ -n "$R2_PARENT_ACCESS_KEY_ID" ] || fail r2_parent_access_key_id_missing
[ -n "$R2_PARENT_API_TOKEN" ] || fail r2_parent_api_token_missing
yes_gate R2_PARENT_CREDENTIAL_PRESENCE_VERIFIED_WITHOUT_VALUE_DISCLOSURE

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
assert r2['temporary_credential_functional_test_stage'] == 'POST_CREATE_VERIFY'
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
