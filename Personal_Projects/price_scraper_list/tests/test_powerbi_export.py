from datetime import date, datetime

import duckdb

from src import client_report as cr
from src import powerbi_export as pbx
from src import probe
from src.config import AppConfig, ClientConfig, ZoneConfig
from src.scraper import parse_store_header

TODAY = date(2026, 11, 23)
CLIENT = ClientConfig(name="Tienda Test", store_id="1", store_slug="1-tienda", zone_id="z",
                      opening_hours={"weekday": "10-18", "weekend": "10-18"},
                      rappi_listings={"cut": "1", "nostock": "2"})
CONFIG = AppConfig(zones=[ZoneConfig(id="z", name="Z", city="C", lat=0, lng=0, address="A")],
                   search_queries=["q"], client=CLIENT)


def stores(*ids):
    return [{"rank": i + 1, "store_id": sid, "name": f"Store {sid}", "slug": "s",
             "header": [f"Store {sid}", "38 min o prog.", "•", "$ 3.500"]} for i, sid in enumerate(ids)]


def read(path):
    with duckdb.connect() as con:
        cur = con.execute(f"SELECT * FROM read_parquet('{path.as_posix()}')")
        names = [d[0] for d in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]


def test_write_tables_parquet(tmp_path):
    # synthetic figures only
    inv = [cr.InventoryItem("cut", "ALFA GATO 1 KG", "CONCENTRADOS", 7000, 10000, 2),
           cr.InventoryItem("nostock", "BETA GATO 1 KG", "CONCENTRADOS", 7000, 10000, 0)]
    catalog = [cr.Offer("1", "Tienda Test", "Alfa Gato 1 Kg", 14000, None, None, TODAY, "1"),
               cr.Offer("1", "Tienda Test", "Beta Gato 1 Kg", 14000, None, None, TODAY, "2")]
    offers = [cr.Offer("9", "Rival", "Alfa Gato 1 Kg", 13000, None, None, TODAY)]
    checks = cr.listing_checks(CLIENT, inv, catalog, offers)
    sugg = [cr.suggest_price(inv[0], CLIENT, offers[0], 14000)]
    base = probe.stamp(datetime(2026, 11, 23, 17, 15), "z")
    probe_rows = [probe.store_page_row(base, 29, "u"),
                  probe.search_row(base, "alfa gato", stores("1", "8"), "1", parse_store_header),
                  probe.search_row(base, "comida perro", stores("7"), "1", parse_store_header)]
    vis = {"history": [(TODAY, 9, 1, 1.0)],
           "history_by_type": [(TODAY, cr.GENERAL_SEARCHES, 9, 0, None), (TODAY, cr.PRODUCT_SEARCHES, 3, 1, 1.0)]}

    store_rows = [s for r in probe_rows for s in r.get("_stores", [])]
    counts = pbx.write_tables(CONFIG, sugg, vis, TODAY, checks, probe_rows, out_dir=tmp_path, store_rows=store_rows)
    assert counts == {"acciones": 2, "productos": 1, "visibilidad_hora": 1, "visibilidad_busqueda": 2,
                      "visibilidad_semanal": 2, "competencia_hora": 3, "reporte": 1}
    comp = read(tmp_path / "competencia_hora.parquet")
    assert [(c["Tienda"], c["Es su tienda"], c["Estado"]) for c in comp if c["Búsqueda"] == "alfa gato"] ==         [("Store 1", "Sí", "Abierta"), ("Store 8", "No", "Abierta")]
    assert not list(tmp_path.glob(".*.tmp"))

    acc = {r["Acción"]: r for r in read(tmp_path / "acciones.parquet")}
    cut = acc["Bajar precio"]
    assert cut["Precio sugerido"] == 12900 and cut["Orden acción"] == 1 and cut["Color acción"] == "#0072B2"
    assert cut["Utilidad sugerida"] < cut["Utilidad actual"]
    assert acc["Desactivar"]["Color acción"] == "#D55E00"

    prod = read(tmp_path / "productos.parquet")[0]
    assert prod["Publicado en Rappi"] == "Sí" and prod["Competidor confiable"] == "Sí"
    assert abs(prod["Brecha vs competidor"] - (14000 / 13000 - 1)) < 1e-9

    hour = read(tmp_path / "visibilidad_hora.parquet")[0]
    assert (hour["Hora"], hour["Según su horario"], hour["Página abre"], hour["Aparece en"]) == ("17:00", "Abierta", 1, 1)
    search = {r["Búsqueda"]: r for r in read(tmp_path / "visibilidad_busqueda.parquet")}
    assert search["alfa gato"]["Posición"] == 1 and search["comida perro"]["Aparece"] == 0
    weekly = {r["Tipo de búsqueda"]: r for r in read(tmp_path / "visibilidad_semanal.parquet")}
    assert weekly[cr.GENERAL_SEARCHES]["Aparece en"] == 0 and weekly[cr.PRODUCT_SEARCHES]["Aparece en"] == 1
    assert read(tmp_path / "reporte.parquet")[0]["Visibilidad hasta"] == datetime(2026, 11, 23, 17, 15)


def test_write_tables_without_probe_or_checks(tmp_path):
    counts = pbx.write_tables(CONFIG, [], {"history": []}, TODAY, out_dir=tmp_path)
    assert counts["acciones"] == 0 and counts["visibilidad_hora"] == 0
    assert (tmp_path / "visibilidad_busqueda.parquet").exists()


def test_visibility_splits_general_and_product_searches(tmp_path):
    from src.database import PriceDatabase
    db = PriceDatabase(tmp_path / "t.duckdb")
    base = {"snapshot_date": TODAY, "week_id": "2026-W48", "extracted_at": TODAY, "zone_id": "z", "zone": "Z",
            "eta_text": None, "fee_text": None}
    db.insert_store_ranks([
        {**base, "search_query": "comida gato", "rank": 1, "store_id": "7", "store_name": "Otra"},
        {**base, "search_query": "arena gato", "rank": 1, "store_id": "8", "store_name": "Otra 2"},
        {**base, "search_query": "alfa gato 1 kg", "rank": 2, "store_id": "1", "store_name": "Tienda Test"},
    ])
    vis = cr.visibility(db, CLIENT, ["comida gato", "arena gato"], min_searches=1)
    assert vis["history_by_type"] == [(TODAY, cr.GENERAL_SEARCHES, 2, 0, None), (TODAY, cr.PRODUCT_SEARCHES, 1, 1, 2.0)]
    assert cr.visibility(db, CLIENT, min_searches=1)["history_by_type"] == [(TODAY, cr.PRODUCT_SEARCHES, 3, 1, 2.0)]
    # default: a type with fewer than 5 searches that day is not a comparable sample
    assert cr.visibility(db, CLIENT, ["comida gato", "arena gato"])["history_by_type"] == []
