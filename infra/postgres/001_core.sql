CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS brief_runs (
    run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    topic text NOT NULL,
    status text NOT NULL CHECK (status IN ('CREATED','RESEARCHING','VERIFYING','WRITING','WAITING_APPROVAL','COMPLETED','FAILED','CANCELLED')),
    source_commit_sha text NOT NULL CHECK (source_commit_sha ~ '^[0-9a-f]{40}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_records (
    source_id text PRIMARY KEY,
    url text NOT NULL,
    publisher text NOT NULL,
    published_at timestamptz,
    retrieved_at timestamptz NOT NULL,
    evidence_kind text NOT NULL CHECK (evidence_kind IN ('fact','inference','hypothesis','unverified')),
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id text PRIMARY KEY,
    run_id uuid NOT NULL REFERENCES brief_runs(run_id) ON DELETE CASCADE,
    claim_text text NOT NULL,
    evidence_kind text NOT NULL CHECK (evidence_kind IN ('fact','inference','hypothesis','unverified')),
    confidence numeric(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE IF NOT EXISTS claim_sources (
    claim_id text NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    source_id text NOT NULL REFERENCES source_records(source_id) ON DELETE RESTRICT,
    PRIMARY KEY (claim_id, source_id)
);

CREATE TABLE IF NOT EXISTS evidence_events (
    event_id text PRIMARY KEY,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    occurred_at timestamptz NOT NULL,
    previous_hash text,
    event_hash text NOT NULL UNIQUE CHECK (event_hash ~ '^[0-9a-f]{64}$')
);

CREATE INDEX IF NOT EXISTS idx_claims_run_id ON claims(run_id);
CREATE INDEX IF NOT EXISTS idx_sources_published_at ON source_records(published_at DESC);
