import argparse
import asyncio
import sys
from datetime import timedelta

from src.config import DEFAULT_CONFIG_PATH, PROJECT_ROOT, load_config, resolve_path
from src.database import PriceDatabase

PRESET_QUERIES = {
    "latest": "SELECT zone, store_name, brand, pet_type, is_medical, product_name, price_current, discount_pct "
              "FROM v_latest_snapshots ORDER BY zone, brand, price_current LIMIT 30",
    "discounts": "SELECT zone, store_name, brand, pet_type, product_name, price_current, discount_pct, savings_cop "
                 "FROM v_top_medical_discounts LIMIT 20",
    "compare_zones": "SELECT product_name, pack_size, brand, cheapest_zone, cheapest_store, cheapest_price, priciest_zone, "
                     "priciest_price, price_diff_cop, price_diff_pct FROM v_zone_price_comparison "
                     "WHERE price_diff_cop > 0 ORDER BY price_diff_cop DESC LIMIT 20",
    "best_prices": "SELECT zone, product_name, pack_size, best_store, best_price, worst_store, worst_price, stores_offering "
                   "FROM v_best_price_by_zone WHERE stores_offering > 1 "
                   "ORDER BY worst_price - best_price DESC LIMIT 20",
    "trends": "SELECT snapshot_date, zone, store_name, product_name, price_current, prev_price, pct_change "
              "FROM v_weekly_trends WHERE price_change_cop <> 0 ORDER BY snapshot_date DESC, ABS(pct_change) DESC "
              "LIMIT 20",
}


def open_db(args) -> tuple:
    config = load_config(args.config)
    return config, PriceDatabase(config.database_file)


def cmd_run(args) -> int:
    from src.scraper import RappiScraper  # Playwright is only needed for scraping

    config, db = open_db(args)
    result = asyncio.run(
        RappiScraper(config, db).run(zone_filter=args.zone, query_filter=args.query, headless=not args.headed)
    )
    # 0 = ok, 1 = nothing saved, 2 = saved but degraded (see DEGRADED RUN lines)
    if result.exit_code == 1:
        print("ERROR: no snapshots were saved. Rappi markup or location handling may have changed; "
              "check logs/debug/ or run `main.py run --query \"hills perro\" --headed`.", file=sys.stderr)
    return result.exit_code


def cmd_stats(args) -> int:
    _, db = open_db(args)
    s = db.get_summary()
    brands = s["brands"]
    print("\n" + "=" * 50)
    print("           RAPPI PRICE TRACKER STATS")
    print("=" * 50)
    print(f"Total Snapshots Stored : {s['total_records']}")
    print(f"Run Dates              : {s['snapshot_dates']} (last: {s['last_snapshot'] or '-'})")
    print(f"Zones Covered          : {', '.join(s['zones']) or 'None'}")
    print(f"Stores Seen            : {s['stores']}")
    print(f"Brands Identified      : {len(brands)} ({', '.join(brands[:6])}{'...' if len(brands) > 6 else ''})")
    print(f"Medical Food Snapshots : {s['medical_products_count']}")
    print("=" * 50 + "\n")
    return 0


def cmd_export(args) -> int:
    _, db = open_db(args)
    db.export_to_parquet(resolve_path(args.output_parquet))
    db.export_to_csv(resolve_path(args.output_csv))
    print("Export complete!")
    return 0


def cmd_query(args) -> int:
    _, db = open_db(args)
    sql = args.sql or PRESET_QUERIES[args.preset or "latest"]
    with db.get_connection() as con:
        print("\n" + "=" * 90)
        print(f"SQL Query: {sql.strip()}")
        print("=" * 90)
        con.sql(sql).show(max_rows=50, max_width=160)
        print("=" * 90 + "\n")
    return 0


def cmd_client_report(args) -> int:
    from src import client_report as cr
    from src.scraper import RappiScraper

    config, db = open_db(args)
    client = config.client
    if client is None:
        print("No client configured (config/settings.local.yaml) - skipping client report.")
        return 0
    today = config.local_now().date()
    inventory = cr.load_inventory(cr.inventory_file(client), client.sales_window_days, today)
    items = cr.products_to_price(inventory)
    print(f"Client {client.name}: {len(items)} products in stock or sold in the last {client.sales_window_days} days")

    if args.catalog:   # refresh her own Rappi listings and prices first
        saved = asyncio.run(RappiScraper(config, db).crawl_client_catalog(config.zone(client.zone_id), client,
                                                                          headless=not args.headed))
        print(f"  her Rappi catalog: {saved} listings saved")

    queries = [i.search_query for i in items]
    if args.search == "all":
        pending = list(dict.fromkeys(q for q in queries if q))
    elif args.search == "stock":   # every in-stock product, however recent its last search (ADR-014)
        pending = list(dict.fromkeys(i.search_query for i in items if i.stock > 0 and i.search_query))
    elif args.search == "none":
        pending = []
    else:
        pending = cr.queries_needing_search(db, client.zone_id, queries, client.product_search_max_age_days, today)
    pending = pending[: args.max_searches or client.max_product_searches]
    if pending:
        print(f"Searching Rappi for {len(pending)} products from zone '{client.zone_id}'...")
        res = asyncio.run(RappiScraper(config, db).search_queries(config.zone(client.zone_id), pending,
                                                                    headless=not args.headed))
        print(f"  {res.saved} offers saved; {len(res.empty)} searches without relevant results, {len(res.failed)} failed")

    suggestions = cr.build_suggestions(config, db, items, today)
    vis = cr.visibility(db, client)
    offers = cr.load_offers(db, client.zone_id, today - timedelta(days=client.product_search_max_age_days),
                            client.store_id)
    checks = cr.listing_checks(client, inventory, cr.load_client_catalog(db, client), offers)
    from src import probe
    probe_rows = probe.load(client.zone_id)
    out = cr.write_report(config, suggestions, vis, resolve_path(args.out) if args.out else
                          cr.default_report_path(client, today), today, checks, probe_rows)
    matched = sum(1 for s in suggestions if s.competitor)
    print(f"Report written: {out}")
    print(f"  {len(suggestions)} products, {matched} matched to a competitor, "
          f"{sum(1 for s in suggestions if s.rappi_price)} currently published")
    counts = {}
    for a in checks:
        counts[a.action] = counts.get(a.action, 0) + 1
    print(f"  Cambiar precio en Rappi: {len(checks)} listings -> "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return 0


def cmd_probe(args) -> int:
    """Hourly visibility probe of the client store (separate DB, see src/probe.py)."""
    from src import probe
    from src.scraper import RappiScraper

    config = load_config(args.config)
    client = config.client
    if client is None or not client.probe_queries:
        print("No client probe_queries configured (config/settings.local.yaml) - nothing to probe.")
        return 0
    zone = config.zone(client.zone_id)
    print(f"Visibility probe {config.local_now():%Y-%m-%d %H:%M} | {client.name} | zone {zone.name} | "
          f"{len(client.probe_queries)} searches")
    rows = asyncio.run(RappiScraper(config, db=_NoDb()).probe_visibility(
        zone, client.store_id, client.store_slug, client.probe_queries, headless=not args.headed))
    probe.save(rows)
    print("  " + probe.summary_line(rows))
    return 0 if any(r["ok"] for r in rows) else 1


class _NoDb:
    """The probe never touches the price database."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rappi Pet Food Price Scraper & Analytics (DuckDB)")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to settings.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run the price scraper")
    run_p.add_argument("--zone", help="Filter by zone id or name (e.g. poblado, sabaneta)")
    run_p.add_argument("--query", help="Scrape a single search query instead of the configured list")
    run_p.add_argument("--headed", action="store_true", help="Show the browser window")
    run_p.set_defaults(func=cmd_run)

    sub.add_parser("stats", help="Display summary stats from DuckDB").set_defaults(func=cmd_stats)

    exp_p = sub.add_parser("export", help="Export snapshots to Parquet and CSV")
    exp_p.add_argument("--output-parquet", default="data/rappi_prices.parquet")
    exp_p.add_argument("--output-csv", default="data/rappi_prices.csv")
    exp_p.set_defaults(func=cmd_export)

    q_p = sub.add_parser("query", help="Query DuckDB price data")
    group = q_p.add_mutually_exclusive_group()
    group.add_argument("--sql", help="Custom SQL statement to execute")
    for flag, key, help_text in [
        ("--discounts", "discounts", "Active discounts on medical food"),
        ("--compare-zones", "compare_zones", "Same product: cheapest vs priciest zone"),
        ("--best-prices", "best_prices", "Cheapest vs most expensive store per product in each zone"),
        ("--trends", "trends", "Week-over-week price changes"),
    ]:
        group.add_argument(flag, dest="preset", action="store_const", const=key, help=help_text)
    q_p.set_defaults(func=cmd_query, preset=None)

    c_p = sub.add_parser("client-report",
                         help="Pricing + visibility Excel for the client store (config/settings.local.yaml)")
    c_p.add_argument("--search", choices=["auto", "stock", "all", "none"], default="auto",
                     help="Per-product Rappi searches: auto = only those older than "
                          "client.product_search_max_age_days (default), stock = every in-stock product, all, or none")
    c_p.add_argument("--catalog", action="store_true",
                     help="Refresh the client's own Rappi listings and prices before the report")
    c_p.add_argument("--max-searches", type=int, help="Cap the number of product searches in this run")
    c_p.add_argument("--out", help="Output .xlsx (default: client.report_dir/<name>_Rappi_<date>.xlsx)")
    c_p.add_argument("--headed", action="store_true", help="Show the browser window")
    c_p.set_defaults(func=cmd_client_report)

    p_p = sub.add_parser("probe", help="Hourly visibility check of the client store (data/visibility_probe.duckdb)")
    p_p.add_argument("--headed", action="store_true", help="Show the browser window")
    p_p.set_defaults(func=cmd_probe)
    return parser


def main() -> int:
    # Windows consoles / Task Scheduler logs default to cp1252; DuckDB tables use box chars.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
