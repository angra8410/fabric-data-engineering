from datetime import date, datetime

import openpyxl

from src import client_report as cr
from src import probe
from src.config import AppConfig, ClientConfig, ZoneConfig
from src.scraper import parse_store_header

CLIENT = ClientConfig(name="Tienda Test", store_id="1", store_slug="1-tienda", zone_id="z",
                      opening_hours={"weekday": "10-20", "weekend": "10-18"}, holidays=[date(2026, 11, 16)])


def stores(*ids):
    return [{"rank": i + 1, "store_id": sid, "name": f"Store {sid}", "slug": "s",
             "header": [f"Store {sid}", "38 min o prog.", "•", "$ 3.500"]} for i, sid in enumerate(ids)]


def run_rows(when, page_products, listed_in):
    base = probe.stamp(when, "z")
    rows = [probe.store_page_row(base, page_products, "https://x/tiendas/tipo/market")]
    rows.append(probe.search_row(base, "comida perro", stores("7", "8", "9"), "1", parse_store_header))
    rows.append(probe.search_row(base, "agility adulto gato",
                                 stores("1", "8") if listed_in else stores("8"), "1", parse_store_header))
    return rows


def test_search_row_finds_her_rank_and_header():
    base = probe.stamp(datetime(2026, 11, 12, 15, 15, 42), "z")
    row = probe.search_row(base, "q", stores("5", "1"), "1", parse_store_header)
    assert row["her_rank"] == 2 and row["n_stores"] == 2 and row["her_fee"] == "$ 3.500"
    assert row["probed_at"] == datetime(2026, 11, 12, 15, 15) and row["probe_hour"] == 15
    assert probe.search_row(base, "q", [], "1", parse_store_header)["ok"] is False


def test_declared_hours_weekday_weekend_holiday():
    assert probe.declared_open(CLIENT, datetime(2026, 11, 12, 19, 15)) is True     # Thursday
    assert probe.declared_open(CLIENT, datetime(2026, 11, 14, 19, 15)) is False    # Saturday after 18
    assert probe.declared_open(CLIENT, datetime(2026, 11, 16, 19, 15)) is False    # holiday Monday
    assert probe.declared_open(CLIENT, datetime(2026, 11, 12, 9, 15)) is False
    assert probe.declared_open(ClientConfig(name="x", store_id="1", store_slug="s", zone_id="z"),
                               datetime(2026, 11, 12, 12)) is None


def test_save_load_and_hourly_summary(tmp_path):
    path = tmp_path / "probe.duckdb"
    rows = (run_rows(datetime(2026, 11, 12, 10, 15), 40, True) + run_rows(datetime(2026, 11, 12, 15, 15), 0, False)
            + run_rows(datetime(2026, 11, 13, 15, 15), 0, True))
    probe.save(rows, path)
    probe.save(rows, path)                                   # re-running the same hour replaces, no duplicates
    loaded = probe.load("z", path)
    assert len(loaded) == len(rows)
    runs = probe.runs(loaded)
    assert [(r.store_page_ok, r.appeared, r.searches) for r in runs] == [(True, 1, 2), (False, 0, 2), (False, 1, 2)]
    table = {(k, h): rest for k, h, *rest in probe.by_hour(CLIENT, loaded)}
    assert table[("Lunes a viernes", "15:00")][:3] == [2, 0.0, 0.5]   # 2 runs, page never opens, 0.5 hits avg
    assert "does NOT open" in probe.summary_line(rows[-3:])
    assert probe.load("other", path) == [] and probe.load("z", tmp_path / "missing.duckdb") == []


def test_report_adds_hourly_sheets_only_with_probe_data(tmp_path):
    config = AppConfig(zones=[ZoneConfig(id="z", name="Z", city="C", lat=0, lng=0, address="A")],
                       search_queries=["q"], client=CLIENT)
    vis = {"latest": None, "per_query": [], "history": []}
    plain = openpyxl.load_workbook(cr.write_report(config, [], vis, tmp_path / "a.xlsx", date(2026, 11, 12)))
    assert "Visibilidad por hora" not in plain.sheetnames
    rows = run_rows(datetime(2026, 11, 12, 15, 15), 0, True)
    wb = openpyxl.load_workbook(cr.write_report(config, [], vis, tmp_path / "b.xlsx", date(2026, 11, 12),
                                                probe_rows=rows))
    assert wb.sheetnames[-3:] == ["Visibilidad por hora", "Visibilidad hora a hora", "Supuestos"]
    detail = wb["Visibilidad hora a hora"]
    assert [c.value for c in detail[2]][:8] == ["2026-11-12", "jueves", "15:15", "Abierta",
                                                "Abierta (38 min o prog.)", "No abre", 2, 1]


def test_rappi_status_from_delivery_time_text():
    assert probe.rappi_status("29 min o prog.") == "Abierta (29 min o prog.)"
    assert probe.rappi_status("Hoy, 4 PM") == "Cerrada, abre Hoy, 4 PM"
    assert probe.rappi_status(None) is None
