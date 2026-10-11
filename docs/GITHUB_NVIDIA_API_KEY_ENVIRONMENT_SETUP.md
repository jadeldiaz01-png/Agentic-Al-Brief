# GitHub Actions: NVIDIA_API_KEY (environment secret)

Status: **PREPARE_ONLY / not configured and not verified in GitHub**.

The GitHub connection used for this implementation cannot create/read secret
values. The repository owner must enter the value directly in GitHub Settings;
do not disclose or paste a token into chat, issues, source files, logs or PRs.

## Scope

- Code owner: `jadeldiaz01-png/Agentic-Al-Brief` (PRJ-INTEL-001).
- Runtime/infrastructure owner: `jadeldiaz01-png/universal-multi-project-runtime`.
- Environment name: `nvidia-connection-check`.
- Environment **secret name**: `NVIDIA_API_KEY` (the actual key is not stored in Git).
- Environment **variable**: `AGIA_PRIMARY_LLM_PROVIDER`, value `openai`.
- Optional model setting when a later runtime gate is approved:
  `AGIA_NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b` (already pinned in code).
- An Actions environment secret is NOT automatically a secret in OpenBao,
  a deployed application or another repository. It is scoped to jobs referencing
  this exact environment.

## Operator steps (in GitHub UI)

1. Open the repository **Settings > Environments**; create
   `nvidia-connection-check`.
2. Set deployment branch restrictions to `main` only. Configure required
   reviewers if supported and appropriate for the repository plan.
3. In that environment select **Environment secrets > Add secret**.
   Name: `NVIDIA_API_KEY`. Value: the API key copied locally from NVIDIA.
   Never paste it into Variables.
4. In the same environment choose **Environment variables > Add variable**.
   Name: `AGIA_PRIMARY_LLM_PROVIDER`. Value: `openai`.
5. Verify the **names** in Settings without revealing any values.

Repository-wide secrets are not recommended here because more workflows could
read them. Avoid the `pull_request_target` event for code that can reach
third-party secrets. Do not pass the secret to PR CI jobs.

## Check (not authorized by creating this PR)

The proposed workflow is
`.github/workflows/nemotron-secret-presence-prepare-only.yml`.
It is *only* `workflow_dispatch`, *only* on main, and requires an exact SHA
and confirmation `CHECK_NVIDIA_SECRET_PRESENCE_ONLY`. It has read-only
GITHUB_TOKEN permissions and no third-party network calls.

**The workflow can be manually selected in GitHub Actions only after the
workflow file exists on the default branch.** Preparing this PR does not
authorize merging it, dispatching the workflow, rotating a secret, performing
NVIDIA inference, using a privileged runner or deploying any runtime.

Outputs are limited to `NVIDIA_SECRET_PRESENT=YES/NO`, source SHA checks,
and `NVIDIA_API_CONTACT=NOT_ATTEMPTED`. A present value is NOT evidence of
an authenticated/authorized API call, request quotas, tool calling, structured
outputs, privacy compliance or live runtime readiness.

The existing agent opt-in variable is not read directly from GitHub repository
settings by deployed processes; authorized deployment configuration would need
to inject a scoped secret via OpenBao and set provider selection after separate
gates. Keep `PRODUCTION_AUTHORIZED=false` and
`MAX_AUTONOMOUS_CAPITAL_USD=0`.

Official docs:
- https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
- https://docs.github.com/en/actions/learn-github-actions/variables
- https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment
