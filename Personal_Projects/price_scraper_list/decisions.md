# Architecture Decisions — price_scraper_list

## ADR-001 — Snapshot grain: day + zone + store + product (2026-11-05)
**Context:** Rappi search results are grouped by store; the same product appears 2–5 times per zone at different prices. v1 stored no store, so views produced cartesian joins and trends mixed stores.
**Decision:** Read Rappi's own ids from `data-qa="product-item-cpgs-<storeId>_<productId>"`. `snapshot_id = hash(date, zone_id, store_id, product_id)`; `INSERT OR REPLACE` so same-day re-runs overwrite.
**Consequences:** Trends partition by zone + store + product. v1 databases are migrated by renaming the old table to `product_snapshots_legacy_v1` (kept, not deleted).

## ADR-002 — Pack size derived from the unit price (2026-11-05)
**Context:** Names often omit the package size; name-only matching compared 400 g vs 2 kg bags (fake 295% gaps).
**Decision:** `pack_size = price_current / unit_price_value` (Rappi "PUM", e.g. `(57.88/g)`), rounded to 2 significant digits, computed in `v_latest_snapshots`. Comparisons group by `product_key + pack_size + unit_measure`.
**Consequences:** 7256 g vs 7257 g collapse to 7300; sizes closer than ~5% may merge. PUM was present on 100% of cards on 2026-11-05.

## ADR-003 — Normalized `product_key` for cross-store matching (2026-11-05)
**Context:** Stores word the same product differently.
**Decision:** Store `product_key = ProductParser.match_key(product_name)`: accent-stripped, lowercase, weights removed, filler words dropped, synonyms unified, tokens de-duplicated and sorted. Computed in Python at insert; v2 DBs are backfilled on open.
**Consequences:** Changing `match_key` requires re-backfilling (`UPDATE product_snapshots SET product_key = NULL`, then open the DB). On 2026-11-05 data: 601 names → 553 keys; cross-store matches 399 → 404 (Rappi mostly reuses catalog names, so the gain is modest).

## ADR-004 — Relevance filter on search results (2026-11-05)
**Context:** Rappi fuzzy-matches all queries; medical queries returned medicines, vaccines, toys; nonsense queries still return ~50 products.
**Decision:** Keep a result only if its `match_key` shares ≥1 token with the query's (`cachorro`→`perro`, `gatito`→`gato` count as the species).
**Consequences:** 203 of 1,621 rows removed from the 2026-11-05 data (all 380 medical-food rows kept; backup in `data/rappi_prices.backup-20261105.duckdb`). Some store-brand foods whose name lacks the species word (e.g. "Meow Mix Indoor") are dropped — acceptable since the focus is premium/veterinary diets.

## ADR-005 — Run health and exit codes (2026-11-05)
**Decision:** `main.py run` / `run_weekly.ps1` exit `0` ok, `1` nothing saved (or export failed), `2` degraded: ≥50% queries empty/failed or ≥50% cards parsed by the text fallback (markup drift). On empty/unparseable pages, HTML + screenshot go to `logs/debug/`. Degraded runs still export.

## ADR-006 — Local time and paths (2026-11-05)
**Decision:** Snapshot date / ISO week use fixed UTC-5 (`utc_offset_hours`; Colombia has no DST, avoids a `tzdata` dependency on Windows). All relative paths resolve against the project root so Task Scheduler (cwd `System32`) works.

## ADR-008 — Weekly schedule: Wednesday 10:00 local (2026-11-05)
**Context:** Only consistency week to week matters for trends, but store availability and promos skew snapshots.
**Decision:** Run Wednesdays 10:00 (`register_task.ps1`). Reasons: specialty pet stores are open (closed stores vanish from search results, which would look like missing products); outside the 12:00–14:00 delivery peak; Mondays are frequently *festivos* (Ley Emiliani) with reduced hours; mid-week avoids weekend campaigns and the 15th/30th payday promos.
**Consequences:** `StartWhenAvailable` runs a missed slot later the same day/next boot — such snapshots may include fewer stores (late evening). Interactive logon only: no run while signed out (no stored password).

## ADR-009 — Client analysis: private overlay, store ranks, catalog crawl (2026-11-05)
**Context:** The real goal became diagnosing a client's Rappi store. Her location, store id, inventory (costs) and sales are private.
**Decision:** Client specifics live only in git-ignored `config/settings.local.yaml` (merged over `settings.yaml`; `extra_zones` appended, other keys replace) and `data/client/`. Committed code stays generic. Zones may carry their own `search_queries`. Every search now stores the ordered store sections in `search_store_ranks` (+ ETA/fee text) → `v_store_visibility`. The client store's own catalog is crawled each run (home → aisles → sub-aisles, `data-qa="product-item-<id>"`) and stored with `search_query = '[catalogo tienda]'`. The sales sheet's customer columns are never read.
**Consequences:** Weekly run time grows with the client zone (~24 searches + catalog). Client report is skipped silently when no client is configured.

## ADR-010 — Inventory ↔ Rappi matching and price suggestion (2026-11-05)
**Context:** First matching pass paired dog with cat food, urinary with renal, other brands of corn litter — a wrong match yields a harmful price.
**Decision:** Precision over recall. Match requires: score ≥ 0.7 (≥ 0.85 if pack size cannot be verified); first brand word present both ways; all distinctive words when ≤3 (all but one otherwise); no conflict in dog/cat, life stage, breed size, medical line (incl. Pro Plan codes UR/EN/OM/HA/NF, skin), wet/dry, flavour; and the same presence of condition / non-adult stage / breed size on both sides; pack size within 12% (from Rappi unit price). Inventory abbreviations (VET NAT, VETE DIETS, FRANGO…) are expanded only for matching, not for stored product keys.
Price rule (commission = contract Anexo 1 rate × 1.19 IVA by product family; arena/aseo/juguetes/accesorios = 14%): keep-store-margin price = store price / (1 − commission); suggest 1% under the cheapest matching competitor when that still leaves ≥ 10% margin after commission; otherwise keep the store-margin price and say "no competir". Out-of-stock items are flagged "no publicar" (cancellations are charged to her).
**Consequences:** Many products stay unmatched; the sheet shows the matched competitor name + score for human review. Contract clause 6(viii) (price parity) is surfaced in "Supuestos".

## ADR-007 — Data not versioned (2026-11-05)
**Decision:** `data/` contents (DuckDB, Parquet, CSV, backups) and `logs/` are git-ignored; the DB grows weekly and is binary. Backups are manual copies in `data/`.
