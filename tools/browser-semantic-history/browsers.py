"""
browsers.py — Catalog of browsers with semantic / AI-powered history.

Each entry documents:
  - platform availability
  - how semantic history works
  - history export / API access
  - verdict for pet-project integration
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrowserProfile:
    name: str
    url: str
    platforms: list[str]
    semantic_features: list[str]
    history_access: str          # how to get history data out
    embedding_approach: str      # how it stores/queries semantically
    open_source: bool
    free_tier: bool
    verdict: str                 # integration suitability for dreamer-sidekick
    notes: str = ""
    caveats: list[str] = field(default_factory=list)


BROWSERS: list[BrowserProfile] = [
    BrowserProfile(
        name="Arc (The Browser Company)",
        url="https://arc.net",
        platforms=["macOS", "iOS", "Windows"],
        semantic_features=[
            "Arc Search — summarises pages on-device before storing",
            "AI pinned tabs with topic clustering",
            "Browse for Me — single-query full-page synthesis",
            "Conversation with browsing history via Arc Max",
        ],
        history_access=(
            "No public API. History SQLite at "
            "~/Library/Application Support/Arc/StorableSidebar.json "
            "and LevelDB; community tools exist to extract it."
        ),
        embedding_approach=(
            "Proprietary on-device embeddings via Arc Max; "
            "not exposed externally."
        ),
        open_source=False,
        free_tier=True,
        verdict=(
            "Best UX for semantic browsing, but closed history store. "
            "Workaround: extract SQLite history → embed externally into pgvector."
        ),
        caveats=["macOS/iOS/Windows only — no Linux", "history export requires workaround"],
    ),

    BrowserProfile(
        name="Atlas Browser",
        url="https://browser.company",  # Atlas by The Browser Company successor concept
        platforms=["macOS"],
        semantic_features=[
            "AI-native tab organisation by topic",
            "Semantic search across all visited pages",
            "Page content indexed locally for natural-language recall",
        ],
        history_access=(
            "Early-access product; no documented API. "
            "Local index likely in SQLite under Application Support."
        ),
        embedding_approach="Local LLM embeddings; architecture not published.",
        open_source=False,
        free_tier=False,
        verdict=(
            "Purpose-built for semantic history but early-stage and closed. "
            "Monitor for API access; not yet suitable for programmatic integration."
        ),
        caveats=["Invite-only / early access", "No export API"],
    ),

    BrowserProfile(
        name="Brave (with Leo AI)",
        url="https://brave.com",
        platforms=["macOS", "Windows", "Linux", "iOS", "Android"],
        semantic_features=[
            "Leo AI — on-page Q&A and summarisation",
            "AI-powered history search (Brave Search integration)",
            "Privacy-preserving: all inference local or via private endpoint",
        ],
        history_access=(
            "Standard Chromium SQLite history at "
            "~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History. "
            "Well-documented schema; easy to extract."
        ),
        embedding_approach=(
            "Leo uses Mixtral/Llama locally; history is plain-text in SQLite. "
            "Embeddings must be generated externally."
        ),
        open_source=True,
        free_tier=True,
        verdict=(
            "Best choice for programmatic integration. "
            "History is standard Chromium SQLite → easy to pipe into pgvector. "
            "Cross-platform including Linux."
        ),
        notes="Chromium history schema is stable and well-documented.",
    ),

    BrowserProfile(
        name="Perplexity Browser (Android / iOS)",
        url="https://perplexity.ai",
        platforms=["iOS", "Android"],
        semantic_features=[
            "Every page visit auto-generates an AI summary",
            "History searchable by natural language via Perplexity engine",
            "Answers cite visited pages as sources",
        ],
        history_access="Mobile only; no desktop; no export API.",
        embedding_approach="Server-side Perplexity embeddings; not user-accessible.",
        open_source=False,
        free_tier=True,
        verdict=(
            "Excellent semantic recall UX but mobile-only and fully closed. "
            "Not suitable for dreamer-sidekick integration."
        ),
        caveats=["Mobile only", "No history export"],
    ),

    BrowserProfile(
        name="SigmaOS",
        url="https://sigmaos.com",
        platforms=["macOS"],
        semantic_features=[
            "Airis AI assistant with page-level memory",
            "Workspace-scoped semantic search",
            "Auto-tagging and topic clustering of tabs",
        ],
        history_access=(
            "No documented API. "
            "Local storage in ~/Library/Application Support/SigmaOS/."
        ),
        embedding_approach="Proprietary; likely server-side.",
        open_source=False,
        free_tier=False,
        verdict=(
            "Good UX but macOS-only, closed, paid. "
            "Lower priority than Brave for integration."
        ),
        caveats=["macOS only", "Paid product"],
    ),

    BrowserProfile(
        name="Chrome / Edge (with History Embedder sidecar)",
        url="https://google.com/chrome",
        platforms=["macOS", "Windows", "Linux", "iOS", "Android"],
        semantic_features=[
            "No native semantic history",
            "Chrome History SQLite is the richest, most accessible source",
            "Pair with external embedder (this project) for semantic layer",
        ],
        history_access=(
            "~/Library/Application Support/Google/Chrome/Default/History — "
            "SQLite, well-documented, 'urls' and 'visits' tables."
        ),
        embedding_approach=(
            "None natively. dreamer-sidekick adds the semantic layer "
            "via pgvector."
        ),
        open_source=False,
        free_tier=True,
        verdict=(
            "Best history data source for dreamer-sidekick: "
            "richest metadata, most accessible, cross-platform. "
            "Pair with this project's pgvector store for semantics."
        ),
        notes="Also works identically with Edge (Chromium-based).",
    ),
]


def get_by_name(name: str) -> Optional[BrowserProfile]:
    for b in BROWSERS:
        if b.name.lower().startswith(name.lower()):
            return b
    return None


def recommended_for_integration() -> list[BrowserProfile]:
    """Return browsers most suitable for dreamer-sidekick pgvector pipeline."""
    return [b for b in BROWSERS if "pgvector" in b.verdict.lower()
            or "easy" in b.verdict.lower()
            or "best choice" in b.verdict.lower()
            or "richest" in b.verdict.lower()]
