from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class EvidenceEvent:
    event_id: str
    event_type: str
    payload: dict[str, Any]
    occurred_at: str
    previous_hash: str | None
    event_hash: str


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def create_event(
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
    previous_hash: str | None = None,
) -> EvidenceEvent:
    occurred_at = datetime.now(UTC).isoformat()
    unsigned = {
        "event_id": event_id,
        "event_type": event_type,
        "payload": payload,
        "occurred_at": occurred_at,
        "previous_hash": previous_hash,
    }
    event_hash = hashlib.sha256(canonical_json(unsigned)).hexdigest()
    return EvidenceEvent(**unsigned, event_hash=event_hash)


def verify_event(event: EvidenceEvent) -> bool:
    data = asdict(event)
    expected = data.pop("event_hash")
    return hashlib.sha256(canonical_json(data)).hexdigest() == expected
