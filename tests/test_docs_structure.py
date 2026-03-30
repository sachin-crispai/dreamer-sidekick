"""Baseline test: verify docs structure is intact in GOLDEN (master).

Each feature branch adds its own test_<category>.py.
This test ensures the shared scaffold never regresses.
"""
from pathlib import Path

DOCS_ROOT = Path(__file__).parent.parent / "docs"
TOOLS_ROOT = Path(__file__).parent.parent / "tools"

CATEGORIES = [
    "web-scraping",
    "ai-ml",
    "apis-integrations",
    "data-processing",
    "search-research",
    "document-processing",
    "code-analysis",
    "visualization",
    "devops-infra",
]


def test_docs_index_exists():
    assert (DOCS_ROOT / "index.md").exists()


def test_docs_tool_pages_exist():
    for cat in CATEGORIES:
        page = DOCS_ROOT / "tools" / f"{cat}.md"
        assert page.exists(), f"Missing docs page: {page}"


def test_tools_directories_exist():
    for cat in CATEGORIES:
        d = TOOLS_ROOT / cat
        assert d.exists(), f"Missing tools directory: {d}"


def test_docs_pages_not_empty():
    for cat in CATEGORIES:
        page = DOCS_ROOT / "tools" / f"{cat}.md"
        assert page.stat().st_size > 0, f"Empty docs page: {page}"
