# Browser Semantic History

Store and query your browser history by *meaning*, not just keywords,
using PostgreSQL + pgvector under the `dreamer_sidekick` schema.

---

## Browser Evaluation

| Browser | Semantic Features | History Access | Platform | Verdict |
|---------|------------------|----------------|----------|---------|
| **Brave** | Leo AI (local LLM), AI search | Standard Chromium SQLite | All | ✅ Best for integration |
| **Arc** | Arc Max, Browse-for-Me, topic clustering | SQLite (workaround needed) | macOS/Win | ✅ Best UX, closed store |
| **Chrome / Edge** | None natively | Standard Chromium SQLite | All | ✅ Richest data source |
| **Atlas** | AI-native, semantic recall | No API (early access) | macOS | ⏳ Watch for API |
| **Perplexity Browser** | Auto-summary, NL history search | No export | iOS/Android | ❌ Mobile only |
| **SigmaOS** | Airis AI, workspace search | No API | macOS | ❌ Closed + paid |

### Recommended Pipeline

```
Brave / Chrome history (SQLite)
        │
        ▼
chromium_extractor.py       ← copies + reads locked SQLite
        │  list[HistoryEntry]
        ▼
embed each entry            ← any embedding API (Voyage, OpenAI, etc.)
        │  list[float] 1536d
        ▼
BrowserHistoryStore.upsert  ← pgvector in dreamer_sidekick schema
        │
        ▼
semantic_search(query_embedding)  ← cosine similarity via ivfflat index
```

---

## PostgreSQL Schema

All objects live under the **`dreamer_sidekick`** schema.

```sql
dreamer_sidekick.browser_source    -- which browser the row came from
dreamer_sidekick.browser_history   -- core table with vector(1536) embedding column
dreamer_sidekick.history_tags      -- auto/user topic tags per URL
dreamer_sidekick.v_history_search  -- convenience view (embedding IS NOT NULL)
```

### Quick start

```bash
# 1. Apply schema
psql -d mydb -f tools/browser-semantic-history/schema.sql

# 2. Install Python deps
uv pip install psycopg2-binary

# 3. Set connection string
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
```

```python
from tools.browser_semantic_history.chromium_extractor import extract
from tools.browser_semantic_history.pgvector_store import BrowserHistoryStore

entries = list(extract(browser="brave", limit=500))

# Add your embeddings here (e.g. via Anthropic, OpenAI, or Voyage)
# entry.embedding = embed(entry.title + " " + (entry.content_text or ""))

with BrowserHistoryStore.from_env() as store:
    store.upsert_many(entries)
    print(f"Stored {store.count()} history entries")
```

### Semantic search

```python
query_vec = embed("vector databases for pet projects")
results = store.semantic_search(query_vec, top_k=5)
for r in results:
    print(f"{r.cosine_distance:.3f}  {r.title}  {r.url}")
```

---

## Embedding Dimensions

| Provider | Model | Dims | Notes |
|----------|-------|------|-------|
| Voyage AI | voyage-3-lite | 512 | Cheapest, good quality |
| Voyage AI | voyage-3 | 1024 | Recommended |
| OpenAI | text-embedding-3-small | 1536 | Default in schema |
| OpenAI | text-embedding-3-large | 3072 | Change `vector(1536)` → `vector(3072)` |
| Anthropic | (via SDK) | varies | Use voyage-3 via Anthropic API |

> Change the `vector(1536)` column dimension in `schema.sql` to match your chosen model
> **before** running `apply_schema` — it cannot be altered in-place.

---

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | PostgreSQL DDL — schema, tables, indexes, view |
| `pgvector_store.py` | Python store: upsert + semantic_search |
| `chromium_extractor.py` | Read history from Chrome/Brave/Edge SQLite |
| `browsers.py` | Catalog of semantic browsers with verdicts |
