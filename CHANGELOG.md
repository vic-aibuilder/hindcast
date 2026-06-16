# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Repository scaffolding: directory structure, config files, CI workflow.
- Root docs: README.md, PRD.md, ARCHITECTURE.md, AGENTS.md, CLAUDE.md, ROADMAP.md.
- Definition layer: docs/schema.md (Schema v2.2, verbatim).
- GitHub config: CI workflow, issue templates, PR template, CODEOWNERS, setup notes.

### Fixed
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
- Per-image `year` no longer fabricated — derived from title, omitted when unknown (#33).
- Docs synced to the SQLite storage layer and real seed counts (#27).
