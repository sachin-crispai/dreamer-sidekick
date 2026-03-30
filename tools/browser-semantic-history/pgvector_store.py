"""
pgvector_store.py — Store and query browser history semantically via pgvector.

Schema: dreamer_sidekick (PostgreSQL)
Embedding: any provider that returns a list[float] of length 1536 or 3072.

Usage example
-------------
    store = BrowserHistoryStore.from_env()
    store.upsert(HistoryEntry(
        browser="brave",
        url="https://example.com",
        title="Example",
        content_text="Full page text...",
        visited_at=datetime.now(),
    ))
    results = store.semantic_search("vector databases for pet projects", top_k=5)
"""
from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore


@dataclass
class HistoryEntry:
    browser: str                        # must match dreamer_sidekick.browser_source.name
    url: str
    visited_at: datetime
    title: Optional[str] = None
    content_text: Optional[str] = None
    summary: Optional[str] = None
    embedding: Optional[list[float]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    id: int
    browser: str
    url: str
    title: Optional[str]
    summary: Optional[str]
    visited_at: datetime
    cosine_distance: float
    metadata: dict


class BrowserHistoryStore:
    """Thin wrapper around psycopg2 for the dreamer_sidekick schema."""

    SCHEMA = "dreamer_sidekick"

    def __init__(self, dsn: str) -> None:
        if psycopg2 is None:
            raise ImportError("psycopg2 is required: uv pip install psycopg2-binary")
        self._dsn = dsn
        self._conn: Any = None

    # ── Connection ────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "BrowserHistoryStore":
        """Construct from DATABASE_URL env var."""
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            raise EnvironmentError("DATABASE_URL is not set")
        return cls(dsn)

    def connect(self) -> None:
        self._conn = psycopg2.connect(self._dsn)
        self._conn.autocommit = False
        # Register pgvector type so psycopg2 handles vector columns
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "BrowserHistoryStore":
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Schema bootstrap ──────────────────────────────────────────────────────

    def apply_schema(self, sql_path: str) -> None:
        """Run the schema.sql file against the connected database."""
        with open(sql_path) as f:
            sql = f.read()
        with self._conn.cursor() as cur:
            cur.execute(sql)
        self._conn.commit()

    # ── Write ──────────────────────────────────────────────────────────────────

    def upsert(self, entry: HistoryEntry) -> int:
        """Insert or ignore a history entry. Returns the row id."""
        embedding_str = (
            "[" + ",".join(str(x) for x in entry.embedding) + "]"
            if entry.embedding
            else None
        )
        with self._conn.cursor() as cur:
            # Resolve browser_id
            cur.execute(
                f"SELECT id FROM {self.SCHEMA}.browser_source WHERE name = %s",
                (entry.browser,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Unknown browser '{entry.browser}'. "
                                 "Insert it into dreamer_sidekick.browser_source first.")
            browser_id = row[0]

            cur.execute(
                f"""
                INSERT INTO {self.SCHEMA}.browser_history
                    (browser_id, url, title, content_text, summary,
                     visited_at, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)
                ON CONFLICT (browser_id, url, visited_at) DO UPDATE
                    SET title        = EXCLUDED.title,
                        summary      = EXCLUDED.summary,
                        embedding    = EXCLUDED.embedding,
                        metadata     = EXCLUDED.metadata
                RETURNING id
                """,
                (
                    browser_id,
                    entry.url,
                    entry.title,
                    entry.content_text,
                    entry.summary,
                    entry.visited_at,
                    embedding_str,
                    json.dumps(entry.metadata),
                ),
            )
            row_id: int = cur.fetchone()[0]
        self._conn.commit()
        return row_id

    def upsert_many(self, entries: list[HistoryEntry]) -> int:
        """Bulk upsert. Returns count of rows processed."""
        for entry in entries:
            self.upsert(entry)
        return len(entries)

    # ── Read ───────────────────────────────────────────────────────────────────

    def semantic_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        browser: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> list[SearchResult]:
        """
        Return top_k rows ordered by cosine similarity to query_embedding.

        Args:
            query_embedding: pre-computed embedding for the query string
            top_k:           number of results
            browser:         filter by browser name (optional)
            since:           only return entries visited after this time (optional)
        """
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        filters = ["h.embedding IS NOT NULL"]
        params: list[Any] = [embedding_str, top_k]

        if browser:
            filters.append("s.name = %s")
            params.insert(-1, browser)  # before LIMIT param
        if since:
            filters.append("h.visited_at >= %s")
            params.insert(-1, since)

        where = " AND ".join(filters)

        # Re-order params: embedding must be first (used in ORDER BY)
        # Rebuild cleanly:
        select_params: list[Any] = [embedding_str]
        if browser:
            select_params.append(browser)
        if since:
            select_params.append(since)
        select_params.append(top_k)

        sql = f"""
            SELECT
                h.id,
                s.name                               AS browser,
                h.url,
                h.title,
                h.summary,
                h.visited_at,
                h.embedding <=> %s::vector           AS cosine_distance,
                h.metadata
            FROM {self.SCHEMA}.browser_history h
            JOIN {self.SCHEMA}.browser_source   s ON s.id = h.browser_id
            WHERE {where}
            ORDER BY cosine_distance ASC
            LIMIT %s
        """

        with self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, select_params)
            rows = cur.fetchall()

        return [
            SearchResult(
                id=r["id"],
                browser=r["browser"],
                url=r["url"],
                title=r["title"],
                summary=r["summary"],
                visited_at=r["visited_at"],
                cosine_distance=float(r["cosine_distance"]),
                metadata=r["metadata"] or {},
            )
            for r in rows
        ]

    def count(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self.SCHEMA}.browser_history")
            return cur.fetchone()[0]
