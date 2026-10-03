# Agent changelog

## 2026-10-03 — V4.1 targeted corrections

- Added `MIN_AI_ROUGH_SCORE` (default `55`). The 70/20/10 bucket preference uses only qualifying candidates; unused slots go to the highest-scoring remaining candidates across buckets. Shortlists may remain below the limit.
- Clamped deterministic scores to 0–100.
- Removed APAC/EMEA and generic cross-border mentions as sufficient remote eligibility evidence. Explicit global/India remote scope is required; foreign-country location restrictions and explicit residency restrictions block GLOBAL_REMOTE.
- Explicit no-sponsorship/work-authorization requirements override relocation wording. Relocation alone no longer supplies sponsorship evidence.
- `skipped.csv` contains only SKIP decisions from successful Gemini analyses or cached Gemini results. Fallback-only results and unanalyzed jobs are excluded. `not_analyzed.csv` contains qualifying candidates omitted by the analysis limit.
- Added an idempotent SQLite migration for `jobs.search_bucket` and persisted it on insert/update while retaining job status.
- Retained `search_bucket` in `ai_matches_v4.json`.
- Preserved scraper functions, Gemini calls/prompt, cache functions, and country detection.

Validation: `py_compile` passed. Focused offline checks passed for Belgrade/Serbia with US mentioned in the JD; Ontario, EMEA, APAC, Worldwide and work-from-India remote cases; sponsorship negatives plus relocation; score threshold/clamping and redistribution; legacy SQLite migration and status preservation; and mocked CSV/JSON output. No live scraping or Gemini calls were made.

## 2026-10-03 — Reviewed application status tracking

- Added idempotent `applied_at TEXT` migration; existing statuses and rows remain intact.
- Added ranked, deduplicated application batches with fresh APPLIED checks and fail-closed handling of unknown jobs.
- Replaced blind URL marking with approval/submission/observed-confirmation gated outcome recording. Successful applications receive UTC applied_at; failed/unclear attempts become APPLICATION_BLOCKED. Repeated recording preserves the original application timestamp.
- V4.1 excludes APPLIED jobs before AI selection and from apply_now.csv, while retaining historical database rows.
- Documented the browser review/confirmation loop and factual-material requirements. CLI helpers do not automatically inspect or submit browser forms.
- Validation: py_compile and all seven tracking/prefilter test groups passed using temporary databases and mocked generation. Applied the additive migration to the real database, verified all existing row statuses were preserved, and checked the current apply_now.csv for APPLIED entries. No applications were opened or submitted.
