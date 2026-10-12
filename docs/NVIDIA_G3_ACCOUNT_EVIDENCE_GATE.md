# G3 account evidence intake — OFFLINE / FAIL-CLOSED

This package adds a redacted, offline-only and never-authorizing contract for
inspection of account entitlement and billing. It proves neither billing
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

## Privacy-preserving review alternative

For the code-review portion of this change, the repository owner may choose a
machine-verifiable review path instead of sharing private account information
with another collaborator. This is an explicit alternative evidence path, not
a claim that automation is a human reviewer or that the checks are independent
of the author.

The automated path is acceptable only for the code/supply-chain portion when
all of these conditions are documented against the exact PR HEAD SHA:

1. GitHub Actions CI succeeds, including Ruff, Mypy, pytest with the configured
   coverage threshold, manifest validation, and immutable-action validation.
2. The security/supply-chain workflow succeeds, including dependency audit and
   committed-secret checks.
3. The reviewed diff and tests show strict schema rejection, sanitized errors,
   no credential/network contact, fail-closed handling of unobserved positive
   and negative claims, and unchanged runtime/financial locks.
4. The run URLs, exact commit SHA, conclusions, and any limitations are recorded
   in the PR discussion. A later commit invalidates the evidence until checks
   succeed for that new HEAD.
5. Repository branch protection and required-review rules still apply. This
   document does not bypass GitHub settings or manufacture a review approval.

The account owner can perform the account-specific check privately. No API key,
password, account identifier, billing screenshot, or filled evidence form should
be sent to a collaborator or committed to the repository. The account-owner
check is not a substitute for code-review evidence, and automated code checks
cannot establish actual account entitlements or billing terms.

## Account-owner verification (private; not performed by CI)

1. The account owner inspects their authenticated NVIDIA console locally.
2. Confirm developer-program membership, model availability, service/account
   pricing, charging eligibility, remaining quota, provider-side zero-charge
   enforcement (if any), and the permitted use case. A free-tier label is not
   a billing guarantee.
3. Confirm that intended use falls within applicable prototype rights.
   Production requires separate license and payment approval.
4. If recording an observation, use a PRIVATE LOCAL copy of
   config/nvidia-g3-account-evidence-template.json with ENUM STATUSES ONLY and
   a UTC timestamp formatted YYYY-MM-DDTHH:MM:SSZ. Do not commit filled forms.
5. Run offline:
   python -m agentic_ai_brief.nvidia_g3_account_evidence /private/redacted.json
   A valid report still returns exit code 1 with NO_GO and human review required;
   invalid reports return 2 and a sanitized error. Even optimistic self-reported
   statuses do not certify account entitlement or authorize execution.

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

NEXT GATE: evaluate the privacy-preserving automated code-review evidence for
the exact PR HEAD and complete the account-owner verification privately.
Separate explicit gates remain for merge, any source unlock, and a single
authenticated inference request. This addendum does not turn NO_GO into GO.
