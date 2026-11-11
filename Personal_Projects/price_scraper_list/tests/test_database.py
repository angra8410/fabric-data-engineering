import base64
import json
import urllib.parse
from datetime import datetime

import duckdb

from src.config import AppConfig, ZoneConfig
from src.database import PriceDatabase
from src.scraper import raw_to_record


def rec(date, zone_id, zone, store_id, store, product_id, name, price, **kw):
    return {
        "snapshot_date": date, "week_id": "2026-W45", "extracted_at": datetime(2026, 11, 5, 12),
        "country": "CO", "city": "Medellín", "zone_id": zone_id, "zone": zone,
        "store_id": store_id, "store_name": store, "product_id": product_id, "search_query": "q",
        "brand": "Hill's", "pet_type": "Dog", "is_medical": kw.pop("is_medical", False),
        "product_name": name, "price_current": price, **kw,
    }


def test_upsert_is_idempotent_per_day_zone_store_product(tmp_path):
    db = PriceDatabase(tmp_path / "t.duckdb")
    db.insert_snapshots([rec("2026-11-05", "poblado", "El Poblado", "1", "Puppis", "10", "Hills A", 100.0)])
    db.insert_snapshots([rec("2026-11-05", "poblado", "El Poblado", "1", "Puppis", "10", "Hills A", 90.0)])
    with db.get_connection() as con:
        assert con.execute("SELECT COUNT(*), MAX(price_current) FROM product_snapshots").fetchone() == (1, 90.0)


def test_same_product_in_two_stores_is_kept_separately(tmp_path):
    db = PriceDatabase(tmp_path / "t.duckdb")
    db.insert_snapshots([
        rec("2026-11-05", "poblado", "El Poblado", "1", "Puppis", "10", "Hills A", 100.0),
        rec("2026-11-05", "poblado", "El Poblado", "2", "Turbo", "77", "Hills A", 120.0),
    ])
    with db.get_connection() as con:
        row = con.execute(
            "SELECT best_price, best_store, worst_price, stores_offering FROM v_best_price_by_zone"
        ).fetchone()
    assert row == (100.0, "Puppis", 120.0, 2)


def test_pack_sizes_derived_from_unit_price_are_not_mixed(tmp_path):
    db = PriceDatabase(tmp_path / "t.duckdb")
    db.insert_snapshots([
        rec("2026-11-05", "poblado", "El Poblado", "1", "A", "1", "Vet Life Urinary", 42930.0,
            unit_price_value=107.33, unit_measure="g"),
        rec("2026-11-05", "poblado", "El Poblado", "2", "B", "2", "Vet Life Urinary", 172710.0,
            unit_price_value=86.36, unit_measure="g"),
        rec("2026-11-05", "poblado", "El Poblado", "3", "C", "3", "Vet Life Urinary", 196600.0,
            unit_price_value=98.3, unit_measure="g"),
    ])
    with db.get_connection() as con:
        rows = con.execute(
            "SELECT pack_size, best_price, worst_price FROM v_best_price_by_zone ORDER BY pack_size"
        ).fetchall()
    assert rows == [(400, 42930.0, 42930.0), (2000, 172710.0, 196600.0)]


def test_zone_comparison_and_trends(tmp_path):
    db = PriceDatabase(tmp_path / "t.duckdb")
    db.insert_snapshots([
        rec("2026-10-29", "poblado", "El Poblado", "1", "Puppis", "10", "Hills A", 110.0),
        rec("2026-11-05", "poblado", "El Poblado", "1", "Puppis", "10", "Hills A", 100.0),
        rec("2026-11-05", "sabaneta", "Sabaneta", "3", "Tierragro", "55", "HILLS  A", 95.0),
        rec("2026-11-05", "sabaneta", "Sabaneta", "3", "Tierragro", "56", "Hills k/d", 200.0,
            is_medical=True, price_regular=250.0, discount_pct=20.0),
    ])
    with db.get_connection() as con:
        cmp_ = con.execute(
            "SELECT cheapest_zone, cheapest_store, priciest_zone, price_diff_cop FROM v_zone_price_comparison"
        ).fetchall()
        trend = con.execute("SELECT prev_price, price_current, pct_change FROM v_weekly_trends").fetchall()
        disc = con.execute("SELECT product_name, savings_cop FROM v_top_medical_discounts").fetchall()
        latest = con.execute("SELECT COUNT(*) FROM v_latest_snapshots").fetchone()[0]
    assert cmp_ == [("Sabaneta", "Tierragro", "El Poblado", 5.0)]
    assert trend == [(110.0, 100.0, -9.09)]
    assert disc == [("Hills k/d", 50.0)]
    assert latest == 3


def test_legacy_v1_table_is_preserved_and_replaced(tmp_path):
    path = tmp_path / "legacy.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("CREATE TABLE product_snapshots (snapshot_id VARCHAR PRIMARY KEY, zone VARCHAR)")
        con.execute("INSERT INTO product_snapshots VALUES ('a', 'El Poblado')")
        con.execute("CREATE VIEW v_latest_snapshots AS SELECT * FROM product_snapshots")
    db = PriceDatabase(path)
    with db.get_connection() as con:
        assert con.execute("SELECT COUNT(*) FROM product_snapshots_legacy_v1").fetchone()[0] == 1
        cols = {r[0] for r in con.execute("DESCRIBE product_snapshots").fetchall()}
    assert {"store_id", "store_name", "product_id", "zone_id"} <= cols


def test_export_paths_with_quotes(tmp_path):
    db = PriceDatabase(tmp_path / "t.duckdb")
    db.insert_snapshots([rec("2026-11-05", "poblado", "El Poblado", "1", "Puppis", "10", "Hills A", 100.0)])
    out = tmp_path / "it's" / "out.csv"
    db.export_to_csv(out)
    assert out.read_text(encoding="utf-8").startswith("snapshot_id,")


def test_raw_card_to_record_uses_store_and_falls_back_to_text():
    base = {"snapshot_date": "2026-11-05", "zone_id": "poblado", "zone": "El Poblado"}
    r = raw_to_record({"store_id": "9", "product_id": "1", "store_name": None, "store_slug": "turbo-fresh-medellin",
                       "name": None, "price": None,
                       "text": "Agregar\n0\n$ 50.000,00\nHills Perro Adulto 2 kg"}, base)
    assert r["store_name"] == "Turbo Fresh Medellin"
    assert r["price_current"] == 50000.0 and r["product_name"] == "Hills Perro Adulto 2 kg"


def test_location_cookie_roundtrip_and_domain():
    z = ZoneConfig(id="p", name="El Poblado", city="Medellín", lat=6.2, lng=-75.5, address="El Poblado")
    cfg = AppConfig(zones=[z], search_queries=["x"])
    cookie = z.to_rappi_cookie(cfg.cookie_domain)
    payload = json.loads(urllib.parse.unquote(base64.b64decode(cookie["value"]).decode()))
    assert cookie["domain"] == ".rappi.com.co"
    assert payload["lat"] == 6.2 and payload["city"] == "Medellín"


def test_differently_worded_names_are_compared_across_stores(tmp_path):
    db = PriceDatabase(tmp_path / "t.duckdb")
    db.insert_snapshots([
        rec("2026-11-05", "poblado", "El Poblado", "1", "Puppis", "10",
            "Hill's Comida Perro Adulto Small Bites", 100000.0, unit_price_value=50.0, unit_measure="g"),
        rec("2026-11-05", "poblado", "El Poblado", "2", "Turbo", "20",
            "Alimento Hills Small Bites para Perros Adultos 2 kg", 110000.0, unit_price_value=55.0, unit_measure="g"),
    ])
    with db.get_connection() as con:
        rows = con.execute("SELECT stores_offering, best_store, pack_size FROM v_best_price_by_zone").fetchall()
    assert rows == [(2, "Puppis", 2000)]


def test_v2_database_gets_product_key_backfilled(tmp_path):
    path = tmp_path / "v2.duckdb"
    db = PriceDatabase(path)
    db.insert_snapshots([rec("2026-11-05", "poblado", "El Poblado", "1", "Puppis", "10", "Hill's Perro", 1.0)])
    with duckdb.connect(str(path)) as con:  # simulate the v2 schema (no product_key)
        for v in ["v_weekly_trends", "v_top_medical_discounts", "v_zone_price_comparison",
                  "v_best_price_by_zone", "v_latest_snapshots"]:
            con.execute(f"DROP VIEW {v}")
        con.execute("ALTER TABLE product_snapshots DROP COLUMN product_key")
    db = PriceDatabase(path)
    with db.get_connection() as con:
        assert con.execute("SELECT product_key FROM product_snapshots").fetchone()[0] == "hills perro"


def test_run_result_exit_codes():
    from src.scraper import RunResult
    assert RunResult(saved=0).exit_code == 1
    assert RunResult(saved=10, queries=10, cards=100).exit_code == 0
    assert RunResult(saved=10, queries=10, cards=100, empty=["a"] * 5).exit_code == 2
    assert RunResult(saved=10, queries=10, cards=100, fallback_cards=60).exit_code == 2


def test_raw_card_flags_fallback_parsing():
    base = {"snapshot_date": "2026-11-05", "zone_id": "poblado", "zone": "El Poblado"}
    structured = raw_to_record({"store_id": "1", "product_id": "2", "store_name": "Puppis",
                                "name": "Hills Perro", "price": "$ 10.000"}, base)
    fallback = raw_to_record({"store_id": "1", "product_id": "3", "store_name": "Puppis",
                              "text": "$ 10.000\nHills Perro"}, base)
    assert structured["_fallback"] is False and fallback["_fallback"] is True
