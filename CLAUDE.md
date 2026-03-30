# CLAUDE.md — dreamer-sidekick

This file is read by every Claude session working in this repository.

## Blueprint
Standards, templates, and best practices: /Volumes/WORK900_CRISPAI/CRISPAI-BLUEPRINT
- New project checklist:  docs/guides/new-project-checklist.md
- Model routing table:    docs/practices/model-routing.md
- API key conventions:    docs/practices/api-keys.md
- Worktree guide:         docs/practices/worktree.md
- General best practices: docs/practices/general.md

## API Keys
Keys follow convention: `CRISPAI-<VENDOR>-<PROJECT-ID>`

| Key | Used For |
|-----|----------|
| `CRISPAI-GEMINI-DREAMER-SIDEKICK` | Web search, light research (flash-lite / flash) |
| `CRISPAI-NEBIUS-DREAMER-SIDEKICK` | Embeddings overflow, batch writing, fast structured output |
| `CRISPAI-OPENAI-DREAMER-SIDEKICK` | GPT-4o / embeddings fallback |
| `CRISPAI-ANTHROPIC-DREAMER-SIDEKICK` | Final QA, tool use, assembly (claude-sonnet-4-6) |
| `CRISPAI-GITHUB-DREAMER-SIDEKICK` | GitHub API / repo automation |

## Model Routing
| Task | Model | Why |
|------|-------|-----|
| Summaries, drafts | `qwen2.5:32b-ctx128k` via Ollama | Free local |
| Embeddings | `nomic-embed-text` via Ollama | Free local, 768-dim |
| Web search | `gemini-2.5-flash-lite` via Gemini | Unlimited RPD |
| Quality research | `gemini-2.5-flash` via Gemini | Better reasoning |
| Long-form writing | `Qwen/Qwen3-235B-A22B-Instruct-2507` via Nebius batch | $0.10/$0.30 |
| Reasoning | `deepseek-ai/DeepSeek-R1-0528` via Nebius | Chain-of-thought |
| Fast structured output | `Qwen/Qwen3-32B-fast` via Nebius | Speed + structure |
| Final QA + assembly | Claude Sonnet 4.6 | Tool use, consistency |

## Nebius Endpoint
Base URL: https://api.studio.nebius.com/v1/
Auth: Bearer $CRISPAI-NEBIUS-DREAMER-SIDEKICK

## Repository Layout

```
CRISPAI-DREAMER-SIDEKICK/
├── .bare/          git object store (do not touch)
├── .git            file pointer → .bare
├── GOLDEN/         master branch worktree  ← you are here
└── features/       one subdirectory per feature worktree
    ├── tools-web-scraping/
    ├── tools-ai-ml/
    └── ...
```

## Rules for Claude Sessions

1. **GOLDEN is master.** Never commit directly to master from a feature session.
   Only the GOLDEN session (or merge commits from PRs) touches master.

2. **Feature sessions stay in their directory.** If you are working on
   `features/tools-ai-ml/`, do not read or write files outside that directory
   (except to reference GOLDEN/CLAUDE.md for conventions).

3. **Branch naming:** `feature/tools-<category>` — lowercase, hyphenated.

4. **Every feature MUST include a test** in `tests/test_<category>.py` that:
   - Validates all markdown files render (no broken links, valid frontmatter)
   - Runs any Python tool stubs and asserts expected output
   - Generates or updates a `docs/<category>.md` summary that will be visible
     in GOLDEN after merge (via GitHub Pages / local server)

5. **PR template:** Link the PR to its GitHub issue with `Closes #<n>`.

6. **Sync:** After every merge to master, run `git -C GOLDEN pull` from the
   container root to keep GOLDEN current.

## Viewing Content in the Browser

**Local:** From GOLDEN/, run:
```bash
python serve.py
```
Opens a live-reloading MkDocs server at http://localhost:8000

**Remote:** GitHub Pages is enabled on the `master` branch `/docs` folder.
Every merged feature's docs appear at:
https://sachin-crispai.github.io/dreamer-sidekick/

## Tool Category → Issue Mapping

| Category              | Issue | Worktree path                         |
|-----------------------|-------|---------------------------------------|
| web-scraping          | #1    | features/tools-web-scraping/          |
| ai-ml                 | #2    | features/tools-ai-ml/                 |
| apis-integrations     | #3    | features/tools-apis-integrations/     |
| data-processing       | #4    | features/tools-data-processing/       |
| search-research       | #5    | features/tools-search-research/       |
| document-processing   | #6    | features/tools-document-processing/   |
| code-analysis         | #7    | features/tools-code-analysis/         |
| visualization         | #8    | features/tools-visualization/         |
| devops-infra          | #9    | features/tools-devops-infra/          |
