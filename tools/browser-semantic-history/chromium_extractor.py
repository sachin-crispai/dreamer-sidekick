"""
chromium_extractor.py — Extract history from Chromium-based browsers (Chrome, Brave, Edge).

These browsers store history in a SQLite database at a well-known path.
We copy the file before reading because Chrome keeps it locked while running.
"""
from __future__ import annotations

import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .pgvector_store import HistoryEntry

# Chrome epoch starts 1601-01-01; convert to Unix epoch
_CHROME_EPOCH_OFFSET = 11644473600_000_000  # microseconds


def _chrome_time_to_datetime(chrome_us: int) -> datetime:
    """Convert Chrome's microseconds-since-1601 to a timezone-aware datetime."""
    unix_us = chrome_us - _CHROME_EPOCH_OFFSET
    return datetime.fromtimestamp(unix_us / 1_000_000, tz=timezone.utc)


KNOWN_PATHS: dict[str, str] = {
    "chrome": "~/Library/Application Support/Google/Chrome/Default/History",
    "brave":  "~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History",
    "edge":   "~/Library/Application Support/Microsoft Edge/Default/History",
    # Linux paths
    "chrome_linux": "~/.config/google-chrome/Default/History",
    "brave_linux":  "~/.config/BraveSoftware/Brave-Browser/Default/History",
}


def extract(
    browser: str = "brave",
    history_path: str | None = None,
    limit: int = 10_000,
    since: datetime | None = None,
) -> Iterator[HistoryEntry]:
    """
    Yield HistoryEntry objects from a Chromium-based browser's SQLite history.

    Args:
        browser:      key in KNOWN_PATHS or 'chrome'/'brave'/'edge'
        history_path: override the default path
        limit:        max rows to yield
        since:        only yield entries after this datetime
    """
    if history_path is None:
        template = KNOWN_PATHS.get(browser)
        if template is None:
            raise ValueError(f"Unknown browser '{browser}'. "
                             f"Valid options: {list(KNOWN_PATHS)}")
        history_path = str(Path(template).expanduser())

    src = Path(history_path)
    if not src.exists():
        raise FileNotFoundError(
            f"History file not found: {src}\n"
            "Make sure the browser has been launched at least once, "
            "or pass an explicit history_path."
        )

    # SQLite is locked while browser runs — work on a temp copy
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        shutil.copy2(src, tmp.name)
        tmp_path = tmp.name

    since_chrome: int | None = None
    if since is not None:
        since_ts = since.timestamp() if since.tzinfo else since.replace(tzinfo=timezone.utc).timestamp()
        since_chrome = int(since_ts * 1_000_000) + _CHROME_EPOCH_OFFSET

    conn = sqlite3.connect(tmp_path)
    conn.row_factory = sqlite3.Row
    try:
        where = "WHERE v.visit_time > :since" if since_chrome else ""
        sql = f"""
            SELECT
                u.url,
                u.title,
                v.visit_time,
                u.visit_count,
                u.typed_count
            FROM visits v
            JOIN urls   u ON u.id = v.url
            {where}
            ORDER BY v.visit_time DESC
            LIMIT :limit
        """
        params: dict = {"limit": limit}
        if since_chrome:
            params["since"] = since_chrome

        for row in conn.execute(sql, params):
            yield HistoryEntry(
                browser=browser.split("_")[0],  # strip '_linux' suffix
                url=row["url"],
                title=row["title"] or None,
                visited_at=_chrome_time_to_datetime(row["visit_time"]),
                metadata={
                    "visit_count": row["visit_count"],
                    "typed_count": row["typed_count"],
                },
            )
    finally:
        conn.close()
        Path(tmp_path).unlink(missing_ok=True)
