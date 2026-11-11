"""
DuckDB price analysis report for Rappi Colombia (Medellín: El Poblado & Sabaneta).
Run anytime after `main.py run` to inspect prices, medical diets, stores and zones.
"""
import sys

from src.config import DEFAULT_CONFIG_PATH, load_config
from src.database import PriceDatabase

SECTIONS = [
    ("[1] Snapshot Overview by Zone & Pet Type (latest run)", """
        SELECT zone, pet_type,
               COUNT(*)                                AS offers,
               COUNT(DISTINCT store_id)                AS stores,
               COUNT(*) FILTER (WHERE is_medical)      AS medical_offers,
               ROUND(AVG(price_current), 0)            AS avg_price_cop,
               MIN(price_current)                      AS min_price_cop,
               MAX(price_current)                      AS max_price_cop
        FROM v_latest_snapshots
        GROUP BY zone, pet_type
        ORDER BY zone, pet_type
    """),
    ("[2] Prescription & Veterinary Food by Brand (latest run)", """
        SELECT brand,
               COUNT(*)                                  AS offers,
               ROUND(AVG(price_current), 0)              AS avg_price_cop,
               MIN(price_current)                        AS min_price_cop,
               MAX(price_current)                        AS max_price_cop,
               COUNT(*) FILTER (WHERE discount_pct > 0)  AS promo_count
        FROM v_latest_snapshots
        WHERE is_medical
        GROUP BY brand
        ORDER BY offers DESC
    """),
    ("[3] Top Discounts on Medical / Veterinary Food", """
        SELECT zone, store_name, brand, product_name, price_current, price_regular, discount_pct, savings_cop
        FROM v_top_medical_discounts
        LIMIT 10
    """),
    ("[4] Same Product, Different Store: Biggest Gaps Inside a Zone", """
        SELECT zone, product_name, pack_size, best_store, best_price, worst_store, worst_price,
               worst_price - best_price AS gap_cop
        FROM v_best_price_by_zone
        WHERE stores_offering > 1 AND worst_price > best_price
        ORDER BY gap_cop DESC
        LIMIT 10
    """),
    ("[5] Zone Comparison: Best Price in Each Zone for the Same Product", """
        SELECT product_name, pack_size, brand, cheapest_zone, cheapest_store, cheapest_price,
               priciest_zone, priciest_price, price_diff_cop, price_diff_pct
        FROM v_zone_price_comparison
        WHERE price_diff_cop > 1000
        ORDER BY price_diff_cop DESC
        LIMIT 10
    """),
]


def run_analysis(config_path=DEFAULT_CONFIG_PATH):
    config = load_config(config_path)
    db = PriceDatabase(config.database_file)
    with db.get_connection() as con:
        print("\n" + "=" * 100)
        print("          PET FOOD PRICE ANALYSIS REPORT — MEDELLÍN (RAPPI)")
        print("=" * 100)
        for title, sql in SECTIONS:
            print(f"\n{title}:")
            con.sql(sql).show(max_width=160)
        print("=" * 100 + "\n")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    run_analysis(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH)
