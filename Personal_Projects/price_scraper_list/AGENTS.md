# AGENTS.md — Rappi Pet Food Price Tracker (`price_scraper_list`)

Weekly Playwright scraper of pet-food prices on Rappi Colombia (El Poblado & Sabaneta,
Medellín) stored in DuckDB. Python 3.14, Windows, PowerShell. User-facing docs: [README.md](README.md).

## 1. Startup Workflow (every session, before writing code)

1. Read [feature_list.json](feature_list.json): find the active feature (`in-progress`) or the next `not-started` one whose dependencies are `done`.
2. Read [progress.md](progress.md): last session, blockers, open questions.
3. Read [decisions.md](decisions.md) before touching the data model, matching logic or exit codes.
4. Run `.\init.ps1`. If it fails, fix that first — do not build on a red baseline.
5. Work on **one feature at a time**. Stay inside this folder (monorepo scope lock).

## 2. Verification gates

| Gate | Command | When |
| :--- | :--- | :--- |
| Unit tests + setup | `.\init.ps1` | Every change |
| Live smoke (1 zone, 1 query) | `.\init.ps1 -Smoke` | Any change to `src/scraper.py`, `src/parser.py`, config |
| Full pipeline | `.\run_weekly.ps1` (exit 0) | Changes to views, exports, scripts, or before closing a scraper feature |
| Report | `.venv\Scripts\python.exe analysis.py` | Changes to views / `analysis.py` |

`init.ps1` is the verification entrypoint and fails fast (`$ErrorActionPreference = "Stop"` + exit-code check per step).

### Definition of Done
A feature is done only when:
1. Every acceptance criterion in `feature_list.json` is met.
2. The gates above that apply to the change have passed in this session (never from memory).
3. `feature_list.json` holds the command, outcome and date as `evidence`, and `progress.md` is updated.
4. Docs follow the code: README (user-facing), `decisions.md` (architecture), this file (agent rules).
Do not close a feature with failing or skipped gates; record it as `blocked` with the reason instead.

## 3. Rules specific to this project

- **Live scraping writes to the real DB** (`data/rappi_prices.duckdb`). Never run exploratory or nonsense queries through `main.py run`: Rappi fuzzy-matches everything and the rows get stored. Explore with a throwaway script and a temp DB, or pass `--config` pointing at a config whose `database_path` is a temp file.
- **Back up the DB before any manual data change**: `Copy-Item data\rappi_prices.duckdb data\rappi_prices.backup-<yyyymmdd>.duckdb`. `data/` is git-ignored — the DB is not in version control.
- **Schema changes need a migration** in `PriceDatabase.init_db()` (see `_migrate_legacy_schema`, `_migrate_add_product_key`) plus a test that opens an old-schema DB. Never drop user tables.
- **DuckDB 2.0:** fully consume every `execute()` result (`fetchall()`) before running another statement on the same connection; `relation.fetchone()` no longer exists.
- **Selectors:** extraction depends on Rappi `data-qa` attributes (`product-item-cpgs-<store>_<product>`, `product-name`, `product-price`, `product-real-price`, `product-pum`, `product-discount`, `store-item-cpgs-<store>`). If they change, a run exits `2`/`1` and dumps the page to `logs/debug/` — inspect that before guessing.
- **Client confidentiality:** client store id/location/inventory/sales/reports live only in `config/settings.local.yaml` and `data/client/` (both git-ignored). Never copy client figures, costs or customer data into committed files (README, decisions, progress, tests, commit messages). Never read the customer columns of the client's sales sheet (tower/apartment/notes). Don't publish client reports anywhere without the user's explicit OK.
- **Be polite to Rappi:** keep `delay_between_queries_ms` ≥ 1500 and one browser context per zone; no parallel scraping.
- No secrets are needed; if any appear (proxies, API keys), use environment variables.

## 4. Map

| Path | Role |
| :--- | :--- |
| `config/settings.yaml` | Zones (lat/lng → location cookie), search queries, scraper timings |
| `src/config.py` | Pydantic config, project-root path resolution, Rappi cookie encoder |
| `src/scraper.py` | Playwright run, in-page extraction (`EXTRACT_JS`), relevance filter, run health (`RunResult`) |
| `src/parser.py` | COP prices, discounts, unit price, brand/pet/medical detection, `match_key`, `is_relevant` |
| `src/database.py` | Schema, migrations, upsert, analytical views, exports, `search_store_ranks` |
| `src/client_report.py` | Client inventory ↔ Rappi matching, price suggestions, Spanish Excel report |
| `src/probe.py` | Hourly client visibility probe: rows, separate DB `data/visibility_probe.duckdb`, hourly summaries (ADR-013) |
| `run_probe.ps1` / `register_probe_task.ps1` | Hourly probe runner (skips while the weekly task runs) / time-limited scheduled task |
| `config/settings.local.yaml` | PRIVATE overlay: client store + its zone/queries, listing links, probe queries/hours (git-ignored) |
| `main.py` | CLI: `run`, `stats`, `export`, `query` (exit 0/1/2) |
| `analysis.py` | Printed report over the views |
| `run_weekly.ps1` | Scheduled entry point (logs to `logs/`) |
| `tests/` | pytest suite (no network) |

## 5. End of session

1. Update `progress.md` (what changed, evidence, blockers, next step) and `feature_list.json` statuses/evidence.
2. Record new architecture decisions in `decisions.md`.
3. Commit only files of this project, and only when `.\init.ps1` passes, so the next session is restartable from a clean `init`. Write the next step in `progress.md` → "Next step".
