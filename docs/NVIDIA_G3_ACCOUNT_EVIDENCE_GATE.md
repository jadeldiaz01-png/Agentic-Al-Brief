# G3 account evidence intake — OFFLINE / FAIL-CLOSED

This package adds a redacted, offline-only and never-authorizing contract for
human inspection of account entitlement and billing. It proves neither billing
conditions nor the rights of the protected account.

## Public facts versus account verification

- NVIDIA advertises a free prototype endpoint for Nemotron 3 Ultra:
  https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b/build
- The NVIDIA NIM FAQ restricts Developer Program API use to research,
  development, evaluation and prototyping:
  https://docs.api.nvidia.com/nim/docs/product
- Neither source proves that the specific protected credential belongs to a
  currently entitled account, has free quota remaining, cannot accrue charges,
  or is allowed to serve commercial users.

## Future human check (not performed or approved by this PR)

1. The account owner must independently inspect their account via an
   authenticated NVIDIA console. Never share the NVIDIA_API_KEY with ChatGPT,
   commit it to the repo, or paste screenshots containing private account data.
2. Confirm developer-program membership, model availability, service/account
   pricing, charging eligibility, remaining quota, and any genuine provider-side
   hard zero-charge enforcement; a free-tier label is not a billing guarantee.
3. Confirm that intended use falls under prototype rights. Production requires
   independent license and payment approval.
4. Populate a PRIVATE LOCAL copy of the source-controlled redacted template
   config/nvidia-g3-account-evidence-template.json with ENUM STATUSES ONLY and
   a UTC timestamp formatted YYYY-MM-DDTHH:MM:SSZ. Do not commit filled forms.
5. Run offline: python -m agentic_ai_brief.nvidia_g3_account_evidence /private/redacted.json
   A valid report returns exit code 1 with NO_GO and HUMAN_REVIEW_REQUIRED.
   Invalid reports return 2 and a sanitized error. An optimistic report
   still returns NO_GO, since it is not independent account proof.
6. The authorized human reviewer must independently verify console evidence
   and document a separate decision. This validator can NEVER produce GO,
   update secrets, approve production or release locks.

## Source-controlled constraints

G3_AUTHENTICATED_PROBE_LOCKED=True
G3_BILLING_CERTIFICATION_LOCKED=True
G3_EXECUTION_APPROVAL_LOCKED=True
NEMOTRON_ACTIVATION_LOCKED=True
PRODUCTION_AUTHORIZED=false
MAX_AUTONOMOUS_CAPITAL_USD=0

No calls to NVIDIA, OpenAI or a billing API are made by this package, and no
automatic fallback, workflow dispatch, account mutation, deployment, payment,
source unlock, or merge is authorized.

NEXT GATE: independently review the exact PR HEAD and complete human
account-entitlement verification. Separate approvals are needed for merge,
any code unlock, and a single authenticated inference request.
