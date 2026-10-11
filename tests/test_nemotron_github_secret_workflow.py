"""Contract tests: protected GitHub Actions secret is never used from PR events."""
from pathlib import Path

WORKFLOW = Path(".github/workflows/nemotron-secret-presence-prepare-only.yml")


def test_secret_presence_workflow_requires_manual_dispatch_only() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in content
    assert "pull_request:" not in content
    assert "pull_request_target:" not in content
    assert "push:" not in content
    assert "workflow_run:" not in content
    assert "environment: nvidia-connection-check" in content
    assert "permissions:\n  contents: read" in content


def test_secret_presence_never_contacts_provider_or_discloses_value() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "${{ secrets.NVIDIA_API_KEY }}" in content
    assert "${{ vars.AGIA_PRIMARY_LLM_PROVIDER }}" not in content
    assert "AGIA_PRIMARY_LLM_PROVIDER" not in content
    assert "PROVIDER_SELECTION=NOT_ATTEMPTED" in content
    assert '[[ -z "${NVIDIA_API_KEY:-}" ]]' in content
    assert "NVIDIA_SECRET_PRESENT=YES" in content
    assert "NVIDIA_API_CONTACT=NOT_ATTEMPTED" in content
    assert "curl " not in content
    assert "chat/completions" not in content
    assert "printenv" not in content
    assert "echo ${NVIDIA_API_KEY}" not in content
    assert "set +x" in content


def test_secret_check_demands_exact_main_sha_and_no_activation() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")
    assert 'refs/heads/main' in content
    assert 'CHECK_NVIDIA_SECRET_PRESENCE_ONLY' in content
    assert "EXPECTED_SHA" in content
    assert "ACTUAL_SHA" in content
    assert "PROVIDER_DEFAULT=DENY" not in content
    assert "PRODUCTION_AUTHORIZED=false" in content
    assert "MAX_AUTONOMOUS_CAPITAL_USD=0" in content
