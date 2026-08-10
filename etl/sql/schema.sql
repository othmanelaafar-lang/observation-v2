CREATE TABLE IF NOT EXISTS experts (
    id BIGSERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    primary_affiliation TEXT,
    country_code TEXT,
    domains JSONB NOT NULL DEFAULT '[]'::jsonb,
    github_login TEXT,
    github_url TEXT,
    openalex_id TEXT,
    orcid_id TEXT,
    scholar_id TEXT,
    source_rank DOUBLE PRECISION NOT NULL DEFAULT 0,
    score DOUBLE PRECISION NOT NULL DEFAULT 0,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    raw JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_experts_full_name ON experts (full_name);
CREATE INDEX IF NOT EXISTS idx_experts_country_code ON experts (country_code);
