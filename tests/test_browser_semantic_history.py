"""
Tests for browser-semantic-history feature.

Validates:
 1. Browser catalog integrity
 2. Schema SQL is well-formed
 3. pgvector_store data model
 4. Chromium extractor handles missing files gracefully
 5. Docs page exists and is complete
"""
from __future__ import annotations

import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

FEATURE_ROOT = Path(__file__).parent.parent
TOOLS_DIR = FEATURE_ROOT / "tools" / "browser-semantic-history"
DOCS_PAGE = FEATURE_ROOT / "docs" / "tools" / "browser-semantic-history.md"

import sys
sys.path.insert(0, str(FEATURE_ROOT))

from tools.browser_semantic_history.browsers import (
    BROWSERS, get_by_name, recommended_for_integration, BrowserProfile,
)
from tools.browser_semantic_history.pgvector_store import (
    HistoryEntry, SearchResult, BrowserHistoryStore,
)
from tools.browser_semantic_history.chromium_extractor import (
    _chrome_time_to_datetime, _CHROME_EPOCH_OFFSET,
)


# ── Browser catalog ──────────────────────────────────────────────────────────

class TestBrowserCatalog:
    def test_catalog_not_empty(self):
        assert len(BROWSERS) >= 4

    def test_all_have_required_fields(self):
        for b in BROWSERS:
            assert isinstance(b, BrowserProfile)
            assert b.name
            assert b.url
            assert b.platforms
            assert b.verdict

    def test_brave_is_present(self):
        b = get_by_name("brave")
        assert b is not None
        assert "Linux" in b.platforms

    def test_arc_is_present(self):
        b = get_by_name("arc")
        assert b is not None

    def test_recommended_not_empty(self):
        recs = recommended_for_integration()
        assert len(recs) >= 1

    def test_recommended_includes_brave_or_chrome(self):
        names = [b.name.lower() for b in recommended_for_integration()]
        assert any("brave" in n or "chrome" in n for n in names)


# ── Schema SQL ───────────────────────────────────────────────────────────────

class TestSchemaSQL:
    def setup_method(self):
        self.sql = (TOOLS_DIR / "schema.sql").read_text()

    def test_schema_file_exists(self):
        assert (TOOLS_DIR / "schema.sql").exists()

    def test_creates_dreamer_sidekick_schema(self):
        assert "CREATE SCHEMA IF NOT EXISTS dreamer_sidekick" in self.sql

    def test_browser_history_table_defined(self):
        assert "dreamer_sidekick.browser_history" in self.sql

    def test_vector_column_present(self):
        assert re.search(r"vector\(\d+\)", self.sql)

    def test_ivfflat_index_defined(self):
        assert "ivfflat" in self.sql

    def test_browser_source_table_defined(self):
        assert "dreamer_sidekick.browser_source" in self.sql

    def test_view_defined(self):
        assert "dreamer_sidekick.v_history_search" in self.sql

    def test_tags_table_defined(self):
        assert "dreamer_sidekick.history_tags" in self.sql


# ── HistoryEntry dataclass ───────────────────────────────────────────────────

class TestHistoryEntry:
    def test_minimal_entry(self):
        e = HistoryEntry(
            browser="brave",
            url="https://example.com",
            visited_at=datetime.now(tz=timezone.utc),
        )
        assert e.embedding is None
        assert e.metadata == {}

    def test_entry_with_embedding(self):
        vec = [0.1] * 1536
        e = HistoryEntry(
            browser="chrome",
            url="https://pgvector.github.io",
            visited_at=datetime.now(tz=timezone.utc),
            embedding=vec,
        )
        assert len(e.embedding) == 1536


# ── BrowserHistoryStore (unit — no real DB) ──────────────────────────────────

class TestBrowserHistoryStore:
    def test_from_env_raises_without_env(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(EnvironmentError, match="DATABASE_URL"):
            BrowserHistoryStore.from_env()

    def test_requires_psycopg2(self, monkeypatch):
        import tools.browser_semantic_history.pgvector_store as mod
        original = mod.psycopg2
        mod.psycopg2 = None
        try:
            with pytest.raises(ImportError, match="psycopg2"):
                BrowserHistoryStore("dsn").connect()
        finally:
            mod.psycopg2 = original


# ── Chromium extractor ───────────────────────────────────────────────────────

class TestChromiumExtractor:
    def test_chrome_epoch_conversion(self):
        # Chrome time 0 should map to 1601-01-01
        dt = _chrome_time_to_datetime(0)
        assert dt.year == 1601

    def test_modern_timestamp_roundtrip(self):
        now = datetime(2025, 3, 30, 12, 0, 0, tzinfo=timezone.utc)
        chrome_us = int(now.timestamp() * 1_000_000) + _CHROME_EPOCH_OFFSET
        recovered = _chrome_time_to_datetime(chrome_us)
        assert abs((recovered - now).total_seconds()) < 1

    def test_missing_file_raises(self):
        from tools.browser_semantic_history.chromium_extractor import extract
        with pytest.raises(FileNotFoundError):
            list(extract(browser="brave", history_path="/nonexistent/path/History"))

    def test_extract_from_synthetic_sqlite(self):
        """Build a minimal Chromium-style SQLite and extract from it."""
        from tools.browser_semantic_history.chromium_extractor import extract

        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE urls (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                visit_count INTEGER DEFAULT 1,
                typed_count INTEGER DEFAULT 0
            );
            CREATE TABLE visits (
                id INTEGER PRIMARY KEY,
                url INTEGER REFERENCES urls(id),
                visit_time INTEGER
            );
            INSERT INTO urls VALUES (1, 'https://pgvector.github.io', 'pgvector', 3, 1);
            INSERT INTO visits VALUES (1, 1, 13369439200000000);
        """)
        conn.close()

        entries = list(extract(browser="brave", history_path=db_path, limit=10))
        assert len(entries) == 1
        assert entries[0].url == "https://pgvector.github.io"
        assert entries[0].title == "pgvector"
        assert entries[0].browser == "brave"
        assert isinstance(entries[0].visited_at, datetime)

        Path(db_path).unlink(missing_ok=True)


# ── Docs page ────────────────────────────────────────────────────────────────

class TestDocsPage:
    def test_docs_page_exists(self):
        assert DOCS_PAGE.exists(), f"Missing: {DOCS_PAGE}"

    def test_docs_page_not_empty(self):
        assert DOCS_PAGE.stat().st_size > 500

    def test_docs_covers_key_browsers(self):
        text = DOCS_PAGE.read_text()
        for browser in ("Brave", "Arc", "Chrome"):
            assert browser in text, f"Docs missing section for {browser}"

    def test_docs_mentions_dreamer_sidekick_schema(self):
        assert "dreamer_sidekick" in DOCS_PAGE.read_text()

    def test_docs_has_schema_section(self):
        assert "schema.sql" in DOCS_PAGE.read_text()

    def test_docs_has_code_example(self):
        text = DOCS_PAGE.read_text()
        assert "```" in text  # at least one code block
