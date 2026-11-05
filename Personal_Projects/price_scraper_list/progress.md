# Session Progress Log: price_scraper_list

**Last Updated:** 2026-11-05
**Active Feature:** F8 — client store diagnosis (VelykaPet). F7 after the 2026-11-11 scheduled run.
**Harness Status:** Healthy — `.\init.ps1` passes (47 tests).

---

## Current state
- Scheduled task **"Rappi Price Scraper (weekly)"** registered: Wednesdays 10:00 (ADR-008), current user, interactive logon. Next run 2026-11-11 10:00.
- DB `data/rappi_prices.duckdb`: 1,422 relevant offers for 2026-11-05 (2 zones, 10 queries, 25 stores, 382 medical). Schema v3 (store ids + `product_key`).
- Side tables/backups: `product_snapshots_legacy_v1` (171 rows from the 2026-11-04 test run, v1 schema); `data/rappi_prices.backup-20261105.duckdb` (1,621 rows before the relevance filter and product_key backfill).
- Exports refreshed: `data/rappi_prices.parquet`, `data/rappi_prices.csv`.
- Logs: `logs/run_20261105_124424.log` is the first Task Scheduler run (written with the old transcript logging, so El Poblado's lines are missing — fixed since).

## Blockers / open items
- **F7** blocked until the second weekly snapshot (2026-11-11).
- Known limits: store-brand foods whose name lacks a species word are filtered out (ADR-004); pack sizes within ~5% can merge (ADR-002); no run while the user is signed out (ADR-008).

## Session log

### 2026-11-05 (c) — F8 client diagnosis started (Claude Code)
- Real goal clarified: the user's client runs a Rappi store (VelykaPet, Itagüí) with low sales; this project is to diagnose why.
- **Confidentiality:** client sales/costs and all findings live only in `data/client/` (git-ignored). Never copy figures into committed files.
- Probes (throwaway scripts, no writes to the main DB) from the store's own coordinates: search visibility for 18 queries, full store catalog, competitor offers. Diagnosis: `data/client/diagnosis_velykapet_2026-11-05.md`.
- Waiting on client answers (commission, price uplift, delisted best sellers, partner-portal data).

### 2026-11-05 (b) — Scheduling (Claude Code)
- Chose Wednesday 10:00 (ADR-008); wrote `register_task.ps1` (agent auto mode blocks creating scheduled tasks, so the user ran it).
- User test via `Start-ScheduledTask`: LastTaskResult 0, 1,496 offers saved/updated, exports refreshed.
- Found Windows PowerShell 5.1 `Start-Transcript` drops python output in hidden windows; `run_weekly.ps1` now logs every line itself (UTF-8). Re-verified hidden from System32 with a temp 1-query config: exit 0, complete log; real exports re-generated afterwards.

### 2026-11-05 (a) — Review, refactor, harness (Claude Code)
- Reviewed the 2026-11-04 prototype. Found: no store dimension (duplicate offers, broken comparisons/trends), relative paths breaking Task Scheduler, UTC dates, UTF-16 requirements, print-only test.
- Implemented F2–F5 (see `feature_list.json` evidence and `decisions.md` ADR-001…007).
- Incident: a nonsense live test query stored 47 fuzzy-matched rows; rows removed (none pre-existed) — led to ADR-004 and the "no exploratory live runs against the real DB" rule in AGENTS.md.
- Verification: `run_weekly.ps1` from System32 exit 0 (1,621 offers, ~5 min); `init.ps1 -Smoke` exit 0; pytest 47 passed; `analysis.py` renders.
- Harness created: AGENTS.md, feature_list.json, progress.md, decisions.md.

## Next step
After Wednesday 2026-11-11 10:00: check `Get-ScheduledTaskInfo -TaskName "Rappi Price Scraper (weekly)"` (LastTaskResult 0) and the newest `logs\run_*.log`, then do F7: `main.py query --trends` must return rows; spot-check 5 offers against Rappi.
