# CLAUDE.md — dreamer-sidekick

This file is read by every Claude session working in this repository.

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
