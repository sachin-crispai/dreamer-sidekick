# dreamer-sidekick

A curated inventory of tools for researching and building pet projects.

## Browse the Docs

- **Remote (GitHub Pages):** https://sachin-crispai.github.io/dreamer-sidekick/
- **Local:** `python serve.py` → http://localhost:8000

## Tool Categories

| Category | Description |
|----------|-------------|
| [web-scraping](tools/web-scraping/) | Playwright, Scrapy, BeautifulSoup |
| [ai-ml](tools/ai-ml/) | Anthropic SDK, OpenAI, LangChain |
| [apis-integrations](tools/apis-integrations/) | httpx, aiohttp, requests |
| [data-processing](tools/data-processing/) | Polars, Pandas, DuckDB |
| [search-research](tools/search-research/) | Tavily, SerpAPI, Exa |
| [document-processing](tools/document-processing/) | pypdf, markitdown, docling |
| [code-analysis](tools/code-analysis/) | tools/code-analysis/ |
| [visualization](tools/visualization/) | Plotly, Altair, Rich |
| [devops-infra](tools/devops-infra/) | Docker SDK, Fabric, invoke |

## Repository Layout

```
GOLDEN/          ← master branch (this directory)
features/        ← one worktree per feature branch
.bare/           ← git object store
```

## Development

See [CLAUDE.md](CLAUDE.md) for conventions used by all Claude sessions.
