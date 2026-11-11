# Session Progress Log: price_scraper_list

**Last Updated:** 2026-11-11
**Active Feature:** F12 hourly visibility probe (collecting data once the task is registered). Also open: F7.
**Harness Status:** Healthy — `.\init.ps1` passes (91 tests).

---

## Current state
- Scheduled task **"Rappi Price Scraper (weekly)"** registered: Wednesdays 10:00 (ADR-008), current user, interactive logon. Next run 2026-11-11 10:00.
- DB `data/rappi_prices.duckdb`: 1,422 relevant offers for 2026-11-05 (2 zones, 10 queries, 25 stores, 382 medical). Schema v3 (store ids + `product_key`).
- Side tables/backups: `product_snapshots_legacy_v1` (171 rows from the 2026-11-04 test run, v1 schema); `data/rappi_prices.backup-20261105.duckdb` (1,621 rows before the relevance filter and product_key backfill).
- Client analysis (private): `config/settings.local.yaml` adds the client zone + 24 queries and the client store; weekly run now also crawls her catalog and writes `data/client/reports/<name>_Rappi_<date>.xlsx`. First report 2026-11-05.
- Exports refreshed: `data/rappi_prices.parquet`, `data/rappi_prices.csv`.
- Logs: `logs/run_20261105_124424.log` is the first Task Scheduler run (written with the old transcript logging, so El Poblado's lines are missing — fixed since).

## Blockers / open items
- **F7** blocked until the second weekly snapshot (2026-11-11).
- Known limits: store-brand foods whose name lacks a species word are filtered out (ADR-004); pack sizes within ~5% can merge (ADR-002); no run while the user is signed out (ADR-008).

## Session log

### 2026-11-11 — Scheduled run check + F10 client report fixes (Claude Code)
- Second scheduled run OK: Task Scheduler LastRunTime 2026-11-11 10:00, LastTaskResult 0, 2,968 snapshots (3 zones), client report written. DB now 3 run dates.
- Review of the client report found wrong suggestions: per-unit items compared with competitors' packs, a brand-less accessory matched a branded one, mismatched flavours / sub-lines. Fixed in F10 (ADR-011); 12 per-unit pack barcodes configured in the private overlay.
- Verification: `.\init.ps1` exit 0 (85 tests); report rebuilt offline to `data/client/reports/*_2026-11-11_v2.xlsx` (the original 10:00 report is kept).
- Not done: F7 (trends validation) — now unblocked.
- F11: "Ajustar en Rappi" tab (her WhatsApp +20% rule, ADR-012). 24 of her 27 listings linked by hand in the overlay; 3 left as "Vincular" (ambiguous: Br For Dogs cordero adult/puppy, Disugual conejo two barcodes, Dogzymes without barcode). Inventory switched to the 2026-11-10 backup via `VelyKaPet_Backup_*.xlsx` (newest wins). Report v3 rebuilt offline.
- F12 (in progress): hourly visibility probe (ADR-013). Live finding 2026-11-11: Rappi lists exactly 5 stores per search (no "more"); her store home redirected to the store directory at 15:35-15:40 (loaded fine at ~10:08) while she ranked #1 for "agility adulto gato". Declared hours: Mon-Fri 10-20, weekends/holidays 10-18. Task registered by the user; first scheduled run 16:15 OK (result 0). The client was away until 16:00 (store closed: Rappi showed "Hoy, 4 PM"); from 16:15 Rappi shows "29 min o prog." (open) but the store home page still redirects — open question, separate from opening hours. Hour-by-hour sheet now shows Rappi's status.
- Caveat for the client: several inventory "Precio Venta" values look like Rappi prices (e.g. cost + 20%), so some "Subir" rows may be data errors; she should confirm WhatsApp prices.

### 2026-11-05 (d) — F9 client pricing sheet + visibility tracker (Claude Code)
- Added private overlay config, per-zone queries, `search_store_ranks` + `v_store_visibility`, client catalog crawl, `client-report` command and Spanish Excel (ADR-009/010); wired into `run_weekly.ps1`; added openpyxl.
- Matching hardened after review of real false positives (dog/cat, urinary/renal, other brands, product lines); pricing fixed so an already-cheapest product is never told to go above the competitor.
- Privacy: tests use synthetic costs; leak scan of committed files clean. Sales-sheet customer columns are never read.
- Live: client zone run exit 0; client-report exit 0 (123 product searches).
- Note: background runs should use `python -u` so logs stream.

### 2026-11-05 (c) — F8 client diagnosis (Claude Code)
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
F12: confirm the hourly task runs (`Get-ScheduledTaskInfo -TaskName "Rappi Visibility Probe (hourly)"`, `logs\probe_*.log`); after the period, read 'Visibilidad por hora' in the client report, deliver findings, run `.\register_probe_task.ps1 -Remove`. F7: `main.py query --trends` must return rows (runs 2026-11-05/06/11 exist); spot-check 5 offers against Rappi. Client: inventory per-tube costs for the 4-pack items may be stale vs the current pack cost — ask the user to update the workbook.
