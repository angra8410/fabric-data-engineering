import hashlib
from pathlib import Path
from typing import Any, Dict, List

import duckdb

from src.parser import ProductParser

# Column order of product_snapshots (schema v2). Inserts use this explicit list
# so adding a column never silently shifts values.
COLUMNS = [
    "snapshot_id", "snapshot_date", "week_id", "extracted_at",
    "country", "city", "zone_id", "zone",
    "store_id", "store_name", "product_id", "search_query",
    "brand", "pet_type", "is_medical", "product_name", "product_key",
    "price_current", "price_regular", "discount_pct",
    "unit_price_value", "unit_measure", "package_weight", "in_stock",
]

VIEWS = ["v_weekly_trends", "v_top_medical_discounts", "v_zone_price_comparison",
         "v_best_price_by_zone", "v_latest_snapshots"]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS product_snapshots (
    snapshot_id      VARCHAR PRIMARY KEY,   -- hash(date, zone, store, product)
    snapshot_date    DATE NOT NULL,         -- local (Colombia) date of the run
    week_id          VARCHAR NOT NULL,      -- ISO week, e.g. 2026-W45
    extracted_at     TIMESTAMP NOT NULL,    -- UTC
    country          VARCHAR NOT NULL,
    city             VARCHAR NOT NULL,
    zone_id          VARCHAR NOT NULL,
    zone             VARCHAR NOT NULL,
    store_id         VARCHAR NOT NULL,      -- Rappi store id (branch level)
    store_name       VARCHAR NOT NULL,
    product_id       VARCHAR NOT NULL,      -- Rappi product id within the store
    search_query     VARCHAR NOT NULL,
    brand            VARCHAR NOT NULL,
    pet_type         VARCHAR NOT NULL,
    is_medical       BOOLEAN NOT NULL,
    product_name     VARCHAR NOT NULL,
    product_key      VARCHAR,               -- normalized name for cross-store matching
    price_current    DOUBLE NOT NULL,
    price_regular    DOUBLE,
    discount_pct     DOUBLE,
    unit_price_value DOUBLE,
    unit_measure     VARCHAR,
    package_weight   VARCHAR,
    in_stock         BOOLEAN NOT NULL DEFAULT TRUE
);
"""

CREATE_VIEWS_SQL = r"""
-- 1. Latest snapshot per zone (a zone scraped on a different day is still visible).
--    pack_size = price / Rappi unit price (PUM), rounded to 2 significant digits:
--    names often omit the size, so this separates 400 g from 2 kg bags.
CREATE OR REPLACE VIEW v_latest_snapshots AS
WITH latest AS (
    SELECT *, price_current / NULLIF(unit_price_value, 0) AS _raw_size
    FROM product_snapshots
    QUALIFY snapshot_date = MAX(snapshot_date) OVER (PARTITION BY zone_id)
)
SELECT * EXCLUDE (_raw_size),
    CAST(ROUND(_raw_size / POW(10, FLOOR(LOG10(_raw_size)) - 1))
         * POW(10, FLOOR(LOG10(_raw_size)) - 1) AS BIGINT) AS pack_size
FROM latest;

-- 2. Cheapest in-stock offer per product (name + pack size) inside each zone
CREATE OR REPLACE VIEW v_best_price_by_zone AS
SELECT
    zone,
    COALESCE(product_key, LOWER(TRIM(product_name)))
        || COALESCE(' | ' || pack_size || COALESCE(unit_measure, ''), '') AS offer_key,
    ANY_VALUE(pack_size)                   AS pack_size,
    ANY_VALUE(unit_measure)                AS unit_measure,
    ANY_VALUE(product_name)                AS product_name,
    ANY_VALUE(brand)                       AS brand,
    ANY_VALUE(pet_type)                    AS pet_type,
    BOOL_OR(is_medical)                    AS is_medical,
    MIN(price_current)                     AS best_price,
    ARG_MIN(store_name, price_current)     AS best_store,
    MAX(price_current)                     AS worst_price,
    ARG_MAX(store_name, price_current)     AS worst_store,
    COUNT(DISTINCT store_id)               AS stores_offering
FROM v_latest_snapshots
WHERE in_stock
GROUP BY zone, offer_key;

-- 3. Zone comparison: best price of the same product across zones
CREATE OR REPLACE VIEW v_zone_price_comparison AS
SELECT
    offer_key,
    ANY_VALUE(product_name)              AS product_name,
    ANY_VALUE(pack_size)                 AS pack_size,
    ANY_VALUE(unit_measure)              AS unit_measure,
    ANY_VALUE(brand)                     AS brand,
    ANY_VALUE(pet_type)                  AS pet_type,
    BOOL_OR(is_medical)                  AS is_medical,
    COUNT(*)                             AS zones_found,
    ARG_MIN(zone, best_price)            AS cheapest_zone,
    ARG_MIN(best_store, best_price)      AS cheapest_store,
    MIN(best_price)                      AS cheapest_price,
    ARG_MAX(zone, best_price)            AS priciest_zone,
    MAX(best_price)                      AS priciest_price,
    MAX(best_price) - MIN(best_price)    AS price_diff_cop,
    ROUND((MAX(best_price) - MIN(best_price)) / MIN(best_price) * 100, 2) AS price_diff_pct
FROM v_best_price_by_zone
GROUP BY offer_key
HAVING COUNT(*) >= 2;

-- 4. Active discounts on medical / veterinary food (latest snapshot)
CREATE OR REPLACE VIEW v_top_medical_discounts AS
SELECT
    snapshot_date, zone, store_name, brand, pet_type, product_name,
    price_current, price_regular, discount_pct,
    (price_regular - price_current) AS savings_cop
FROM v_latest_snapshots
WHERE is_medical AND discount_pct > 0
ORDER BY discount_pct DESC, savings_cop DESC NULLS LAST;

-- 5. Week-over-week price changes of the exact same offer (zone + store + product)
CREATE OR REPLACE VIEW v_weekly_trends AS
WITH ranked AS (
    SELECT
        snapshot_date, week_id, zone, store_name, product_name, brand, price_current,
        LAG(price_current) OVER w AS prev_price,
        LAG(snapshot_date) OVER w AS prev_date
    FROM product_snapshots
    WINDOW w AS (PARTITION BY zone_id, store_id, product_id ORDER BY snapshot_date)
)
SELECT
    snapshot_date, week_id, zone, store_name, product_name, brand,
    price_current, prev_price, prev_date,
    (price_current - prev_price) AS price_change_cop,
    ROUND((price_current - prev_price) / prev_price * 100, 2) AS pct_change
FROM ranked
WHERE prev_price IS NOT NULL;
"""


def _sql_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


class PriceDatabase:
    def __init__(self, db_path: str | Path = "data/rappi_prices.duckdb"):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as con:
            self._migrate_legacy_schema(con)
            con.execute(CREATE_TABLE_SQL)
            self._migrate_add_product_key(con)
            con.execute(CREATE_VIEWS_SQL)

    @staticmethod
    def _migrate_legacy_schema(con: duckdb.DuckDBPyConnection):
        """
        Schema v1 had no store columns, so the same product sold by several
        stores collided. Keep those rows untouched in a side table and start a
        clean v2 table.
        """
        cols = {r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'product_snapshots'"
        ).fetchall()}
        if not cols or "store_id" in cols:
            return
        for v in VIEWS:
            con.execute(f"DROP VIEW IF EXISTS {v}")
        backup = "product_snapshots_legacy_v1"
        n = 1
        while con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [backup]
        ).fetchall()[0][0]:
            n += 1
            backup = f"product_snapshots_legacy_v1_{n}"
        con.execute(f"ALTER TABLE product_snapshots RENAME TO {backup}")
        print(f"[db] Legacy schema detected: old rows moved to table '{backup}'.")

    @staticmethod
    def _migrate_add_product_key(con: duckdb.DuckDBPyConnection):
        """Schema v2 -> v3: add product_key and backfill it for existing rows."""
        cols = {r[0] for r in con.execute("DESCRIBE product_snapshots").fetchall()}
        if "product_key" not in cols:
            for v in VIEWS:
                con.execute(f"DROP VIEW IF EXISTS {v}")
            con.execute("ALTER TABLE product_snapshots ADD COLUMN product_key VARCHAR")
        names = [r[0] for r in con.execute(
            "SELECT DISTINCT product_name FROM product_snapshots WHERE product_key IS NULL"
        ).fetchall()]
        if names:
            con.executemany(
                "UPDATE product_snapshots SET product_key = ? WHERE product_name = ? AND product_key IS NULL",
                [(ProductParser.match_key(n), n) for n in names],
            )
            print(f"[db] Backfilled product_key for {len(names)} product names.")

    @staticmethod
    def generate_snapshot_id(date_str: str, zone_id: str, store_id: str, product_id: str) -> str:
        key = f"{date_str}:{zone_id.lower()}:{store_id}:{product_id}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def insert_snapshots(self, records: List[Dict[str, Any]]) -> int:
        """Upsert: re-running the same day overwrites that day's offer prices."""
        if not records:
            return 0

        defaults = {"country": "CO", "city": "Medellín", "search_query": "", "in_stock": True}
        rows = {}
        for r in records:
            row = {**defaults, **r}
            row.setdefault("product_key", ProductParser.match_key(row["product_name"]))
            row["snapshot_id"] = self.generate_snapshot_id(
                str(row["snapshot_date"]), row["zone_id"], str(row["store_id"]), str(row["product_id"])
            )
            rows[row["snapshot_id"]] = tuple(row.get(c) for c in COLUMNS)

        placeholders = ", ".join("?" for _ in COLUMNS)
        with self.get_connection() as con:
            con.executemany(
                f"INSERT OR REPLACE INTO product_snapshots ({', '.join(COLUMNS)}) VALUES ({placeholders})",
                list(rows.values()),
            )
        return len(rows)

    def get_summary(self) -> Dict[str, Any]:
        with self.get_connection() as con:
            q = lambda sql: con.execute(sql).fetchall()
            return {
                "total_records": q("SELECT COUNT(*) FROM product_snapshots")[0][0],
                "snapshot_dates": q("SELECT COUNT(DISTINCT snapshot_date) FROM product_snapshots")[0][0],
                "last_snapshot": q("SELECT MAX(snapshot_date) FROM product_snapshots")[0][0],
                "zones": [r[0] for r in q("SELECT DISTINCT zone FROM product_snapshots ORDER BY 1")],
                "stores": q("SELECT COUNT(DISTINCT store_id) FROM product_snapshots")[0][0],
                "brands": [r[0] for r in q(
                    "SELECT brand FROM product_snapshots GROUP BY brand ORDER BY COUNT(*) DESC"
                )],
                "medical_products_count": q("SELECT COUNT(*) FROM product_snapshots WHERE is_medical")[0][0],
            }

    def export_to_parquet(self, output_path: str | Path):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as con:
            con.execute(f"COPY product_snapshots TO {_sql_literal(output_path)} (FORMAT PARQUET);")
        print(f"Exported to {output_path}")

    def export_to_csv(self, output_path: str | Path):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as con:
            con.execute(f"COPY product_snapshots TO {_sql_literal(output_path)} (HEADER, DELIMITER ',');")
        print(f"Exported to {output_path}")
