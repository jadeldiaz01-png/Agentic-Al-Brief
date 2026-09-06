#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/jadeldiaz01-png/Agentic-Al-Brief"
LABEL="agentic-ai-brief-runtime"

: "${GITHUB_RUNNER_TOKEN:?temporary GitHub runner registration token required}"
: "${RUNNER_VERSION:?exact actions/runner version required}"
: "${RUNNER_SHA256:?published runner tarball sha256 required}"
: "${RUNNER_LOG_FORWARDING_ACK:?set to 1 only after external runner log forwarding is configured}"

if [[ "${RUNNER_LOG_FORWARDING_ACK}" != "1" ]]; then
  echo "RUNNER_LOG_FORWARDING_NOT_VERIFIED" >&2
  exit 2
fi
if [[ "$(id -u)" -eq 0 ]]; then
  echo "REFUSE_ROOT_RUNNER" >&2
  exit 2
fi
if [[ ! "${RUNNER_VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "INVALID_RUNNER_VERSION" >&2
  exit 2
fi
if [[ ! "${RUNNER_SHA256}" =~ ^[0-9a-f]{64}$ ]]; then
  echo "INVALID_RUNNER_SHA256" >&2
  exit 2
fi

install_dir="${HOME}/actions-runner-agentic-ai-brief"
archive="${TMPDIR:-/tmp}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
url="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"

rm -rf "${install_dir}"
mkdir -p "${install_dir}"
curl --fail --location --proto '=https' --tlsv1.2 --output "${archive}" "${url}"
printf '%s  %s\n' "${RUNNER_SHA256}" "${archive}" | sha256sum --check --strict

tar -xzf "${archive}" -C "${install_dir}"
rm -f "${archive}"
cd "${install_dir}"

runner_name="aab-p0c-$(hostname)-$(date -u +%Y%m%dT%H%M%SZ)"
./config.sh \
  --unattended \
  --url "${REPO_URL}" \
  --token "${GITHUB_RUNNER_TOKEN}" \
  --name "${runner_name}" \
  --labels "${LABEL}" \
  --work _work \
  --ephemeral \
  --disableupdate

unset GITHUB_RUNNER_TOKEN
exec ./run.sh
