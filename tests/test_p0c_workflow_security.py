from pathlib import Path


def test_p0c_runtime_workflow_is_manual_and_exact_sha_bound() -> None:
    text = Path(".github/workflows/p0c-runtime-certification.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "runs-on: [self-hosted, linux, x64, agentic-ai-brief-runtime]" in text
    assert "environment: agentic-ai-brief-runtime" in text
    assert "ref: ${{ inputs.expected_sha }}" in text
    assert "persist-credentials: false" in text
    assert "actions/upload-artifact" not in text


def test_ephemeral_runner_bootstrap_is_fail_closed() -> None:
    text = Path("scripts/register_ephemeral_runner.sh").read_text(encoding="utf-8")
    assert "--ephemeral" in text
    assert "--disableupdate" in text
    assert "REFUSE_ROOT_RUNNER" in text
    assert "RUNNER_SHA256" in text
    assert "sha256sum --check --strict" in text
    assert "RUNNER_LOG_FORWARDING_ACK" in text
    assert "unset GITHUB_RUNNER_TOKEN" in text
