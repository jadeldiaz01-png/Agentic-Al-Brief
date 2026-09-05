from agentic_ai_brief.agent_runtime import BASE_MODEL, build_agents


def test_bounded_agent_topology() -> None:
    agents = build_agents()
    assert set(agents) == {"supervisor", "research", "verifier", "writer"}
    assert BASE_MODEL == "gpt-5.6-luna"
    assert agents["supervisor"].name == "BriefSupervisorAgent"
    assert len(agents["supervisor"].tools) == 3
