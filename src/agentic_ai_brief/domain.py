from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EvidenceKind(StrEnum):
    FACT = "fact"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    UNVERIFIED = "unverified"


class SourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1)
    url: HttpUrl
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    kind: EvidenceKind
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    evidence_kind: EvidenceKind
    source_ids: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)


class BriefRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    depth: Literal["standard", "deep"] = "deep"
    max_sources: int = Field(default=30, ge=3, le=100)


class BriefResult(BaseModel):
    request: BriefRequest
    claims: tuple[Claim, ...]
    sources: tuple[SourceRecord, ...]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    policy_decision_id: str
