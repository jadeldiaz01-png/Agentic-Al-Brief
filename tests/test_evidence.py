from agentic_ai_brief.evidence import create_event, verify_event


def test_evidence_event_hash_verifies() -> None:
    event = create_event("evt-1", "source_ingested", {"source_id": "src-1"})
    assert verify_event(event) is True


def test_evidence_chain_links_previous_hash() -> None:
    first = create_event("evt-1", "source_ingested", {"source_id": "src-1"})
    second = create_event("evt-2", "claim_verified", {"claim_id": "c-1"}, first.event_hash)
    assert second.previous_hash == first.event_hash
    assert verify_event(second) is True
