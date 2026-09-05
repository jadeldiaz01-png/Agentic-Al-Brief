import json
from pathlib import Path


def test_architecture_manifest_is_fail_closed() -> None:
    data = json.loads(Path("config/architecture-2026.json").read_text(encoding="utf-8"))
    assert data["default_decision"] == "NO_GO"
    assert data["governance"]["probabilistic_output_may_authorize_critical_action"] is False
    assert data["governance"]["external_write_default"] == "DENY"
    assert "unbounded-agent-swarms" in data["technology_radar"]["hold"]


def test_production_readiness_requires_runtime_and_safety() -> None:
    data = json.loads(Path("config/production-readiness.json").read_text(encoding="utf-8"))
    required = data["required_for_production"]
    assert "temporal_replay_verified" in required["runtime"]
    assert "prompt_injection_eval_pass" in required["agent_safety"]
    assert "slsa_provenance_present" in required["supply_chain"]
    assert "kill_switch_verified" in required["operations"]
