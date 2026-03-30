-- dreamer_sidekick schema — browser semantic history
-- Requires: PostgreSQL 14+ with pgvector extension
--
-- Install pgvector:  CREATE EXTENSION IF NOT EXISTS vector;
-- Run this file:     psql -d <dbname> -f schema.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- for fast LIKE / trigram search

-- ── Top-level schema ────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS dreamer_sidekick;

-- ── Browser sources ─────────────────────────────────────────────────────────
-- Which browser the history came from
CREATE TABLE IF NOT EXISTS dreamer_sidekick.browser_source (
    id          SMALLSERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,          -- 'chrome', 'brave', 'arc'
    platform    TEXT,                          -- 'macOS', 'Windows', 'Linux'
    history_path TEXT,                         -- local path template
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO dreamer_sidekick.browser_source (name, platform, history_path) VALUES
    ('chrome',  'macOS',   '~/Library/Application Support/Google/Chrome/Default/History'),
    ('brave',   'macOS',   '~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History'),
    ('arc',     'macOS',   '~/Library/Application Support/Arc/StorableSidebar.json'),
    ('edge',    'macOS',   '~/Library/Application Support/Microsoft Edge/Default/History')
ON CONFLICT (name) DO NOTHING;

-- ── Core history table ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dreamer_sidekick.browser_history (
    id              BIGSERIAL PRIMARY KEY,
    browser_id      SMALLINT REFERENCES dreamer_sidekick.browser_source(id),
    url             TEXT NOT NULL,
    title           TEXT,
    -- Raw page content or cleaned text (used to generate embedding)
    content_text    TEXT,
    -- AI-generated summary of the page (optional, generated at ingest)
    summary         TEXT,
    visited_at      TIMESTAMPTZ NOT NULL,
    imported_at     TIMESTAMPTZ DEFAULT NOW(),
    -- pgvector column: 1536 dims for text-embedding-3-small / voyage-3-lite
    -- Use 3072 for text-embedding-3-large or voyage-3
    embedding       vector(1536),
    -- Flexible metadata: tags, domain, visit_count, etc.
    metadata        JSONB DEFAULT '{}',

    UNIQUE (browser_id, url, visited_at)
);

-- ── Indexes ──────────────────────────────────────────────────────────────────

-- Semantic similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS idx_browser_history_embedding_cosine
    ON dreamer_sidekick.browser_history
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Fast URL lookup
CREATE INDEX IF NOT EXISTS idx_browser_history_url
    ON dreamer_sidekick.browser_history (url);

-- Time-range queries
CREATE INDEX IF NOT EXISTS idx_browser_history_visited_at
    ON dreamer_sidekick.browser_history (visited_at DESC);

-- Full-text trigram search on title + summary (fallback / hybrid)
CREATE INDEX IF NOT EXISTS idx_browser_history_title_trgm
    ON dreamer_sidekick.browser_history
    USING gin (title gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_browser_history_summary_trgm
    ON dreamer_sidekick.browser_history
    USING gin (summary gin_trgm_ops);

-- JSONB metadata index
CREATE INDEX IF NOT EXISTS idx_browser_history_metadata
    ON dreamer_sidekick.browser_history
    USING gin (metadata);

-- ── Semantic search helper view ──────────────────────────────────────────────
-- Query: SELECT * FROM dreamer_sidekick.v_history_search
--        ORDER BY embedding <=> '[...]'::vector LIMIT 10;
CREATE OR REPLACE VIEW dreamer_sidekick.v_history_search AS
SELECT
    h.id,
    s.name          AS browser,
    h.url,
    h.title,
    h.summary,
    h.visited_at,
    h.metadata,
    h.embedding
FROM dreamer_sidekick.browser_history h
JOIN dreamer_sidekick.browser_source  s ON s.id = h.browser_id
WHERE h.embedding IS NOT NULL;

-- ── Tags convenience table ───────────────────────────────────────────────────
-- Auto-generated or user-assigned topic tags per URL
CREATE TABLE IF NOT EXISTS dreamer_sidekick.history_tags (
    history_id  BIGINT REFERENCES dreamer_sidekick.browser_history(id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    source      TEXT DEFAULT 'auto',    -- 'auto' | 'user'
    PRIMARY KEY (history_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_history_tags_tag
    ON dreamer_sidekick.history_tags (tag);
