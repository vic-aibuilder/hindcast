# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Repository scaffolding: directory structure, config files, CI workflow.
- Root docs: README.md, PRD.md, ARCHITECTURE.md, AGENTS.md, CLAUDE.md, ROADMAP.md.
- Definition layer: docs/schema.md (Schema v2.2, verbatim).
- GitHub config: CI workflow, issue templates, PR template, CODEOWNERS, setup notes.
- Deploy config: `Procfile` + `.python-version` (Railway/FastAPI), `netlify.toml` (Vite
  frontend), env-driven CORS (`ALLOWED_ORIGINS`) and port (`$PORT`) in `api.py`, and
  `docs/DEPLOY.md`. Stack: Netlify (frontend) + Railway (backend).

### Changed
- Pattern descriptions: lift the closing data-observation sentence into a distinct muted
  data line with clearer paragraph spacing, so longer descriptions are scannable (#29).

### Removed
- Output page: removed the post-query "Pipeline log" panel from the results view; the
  loading-screen reasoning log is unchanged (#29).
- Loading screen: dropped the inaccurate "First run may take 1–5 minutes." copy.

### Fixed
- Pattern grids now hide pre-2025 evidence images (e.g. Supreme 2018, Flight Club 2016,
  Kith 2023/24 surfaced via the `source_url` year) so the grid matches the locked
  2025–present window. Display-only — year-unknown images are kept and synthesis still
  spans the full corpus, so percentages are unchanged (#56, demo-safe half; hard retrieval
  enforcement + seed re-source is post-demo).
- `/query` no longer blocks the event loop: the handler is now a sync `def`, so FastAPI
  runs the blocking pipeline in its threadpool and `/health` stays responsive (and queries
  can overlap) instead of the whole server freezing mid-query (#54). Robust multi-user
  concurrency tracked separately in #66.
- Schema round-trip + aggregator (P0/P0-assist): nested schema was stored as a
  stringified dict and dropped by `_aggregate`, which also failed silently on non-dict
  categories. Legacy rows purged (`purge_legacy_extractions()`), requiring re-extraction (#26).
- Saturation/synthesis now denominate over the extracted set (`schema_extractions`)
  instead of a 500-row raw-table window, so seed images surface even when live retrieval
  dominates (#30).
- Pattern cards now serve term-matched `evidence_images` instead of a positional slice of
  retrieval (#41, June 13).
- Off-subject retrieval filtered via a vision subject check (fail-open), removing
  logos/headshots/non-NYC stores from the grid. Filter checks only the first 60 candidates,
  so junk past that still reaches the grid — follow-up in #56 (#38, June 13).
- Pattern evidence grids now group by store (hero → interior order) instead of showing the
  retrieval round-robin interleave — display-only sort in `_evidence_images_for_pattern_ids` (#55).
- Per-image `year` no longer fabricated — derived from title, omitted when unknown (#33).
- Docs synced to the SQLite storage layer and real seed counts (#27).
