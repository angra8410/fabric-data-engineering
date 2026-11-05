# Session Progress Log: price_scraper_list

**Last Updated:** 2026-11-05
**Active Feature:** None (F1–F5 done). Next: F6 (register Task Scheduler job).
**Harness Status:** Healthy — `.\init.ps1` passes (47 tests).

---

## Current state
- DB `data/rappi_prices.duckdb`: 1,418 relevant offers from the 2026-11-05 run (2 zones, 10 queries, 25 stores, 380 medical). Schema v3 (store ids + `product_key`).
- Side tables/backups: `product_snapshots_legacy_v1` (171 rows from the 2026-11-04 test run, v1 schema); `data/rappi_prices.backup-20261105.duckdb` (1,621 rows before the relevance filter and product_key backfill).
- Exports refreshed: `data/rappi_prices.parquet`, `data/rappi_prices.csv`.

## Blockers / open items
- **F6** needs the user to create (or approve creating) the Windows scheduled task.
- **F7** blocked until a second weekly snapshot exists.
- Known limits: store-brand foods whose name lacks a species word are filtered out (ADR-004); pack sizes within ~5% can merge (ADR-002).

## Session log

### 2026-11-05 — Review, refactor, harness (Claude Code)
- Reviewed the 2026-11-04 prototype. Found: no store dimension (duplicate offers, broken comparisons/trends), relative paths breaking Task Scheduler, UTC dates, UTF-16 requirements, print-only test.
- Implemented F2–F5 (see `feature_list.json` evidence and `decisions.md` ADR-001…007).
- Incident: a nonsense live test query stored 47 fuzzy-matched rows; rows removed (none pre-existed) — led to ADR-004 and the "no exploratory live runs against the real DB" rule in AGENTS.md.
- Verification: `run_weekly.ps1` from System32 exit 0 (1,621 offers, ~5 min); `init.ps1 -Smoke` exit 0; pytest 47 passed; `analysis.py` renders.
- Harness created: AGENTS.md, feature_list.json, progress.md, decisions.md.

## Next step
F6: `Register-ScheduledTask` (weekly, Monday 07:00) with action `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<project>\run_weekly.ps1"`, then confirm Last Run Result after the first run.
