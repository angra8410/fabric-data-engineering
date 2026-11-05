from datetime import date

import openpyxl
import pytest

from src import client_report as cr
from src.config import AppConfig, ClientConfig, ZoneConfig, merge_overlay
from src.database import PriceDatabase
from src.scraper import CATALOG_QUERY, parse_store_header

TODAY = date(2026, 11, 5)


def item(name, cost=10000, price=12000, stock=1, category="CONCENTRADOS", sold=0):
    return cr.InventoryItem("1", name, category, cost, price, stock, sold)


def offer(name, price, unit_price=None, unit="g", store="Comp"):
    return cr.Offer("99", store, name, price, unit_price, unit, TODAY)


CLIENT = ClientConfig(name="Tienda Test", store_id="1", store_slug="1-tienda", zone_id="z")


# ------------------------------------------------------------------ matching
@pytest.mark.parametrize("mine,theirs", [
    ("BIOCANIS X 14 G", "Biocanis Our Jeringa X 14 Gr (probioticos)"),
    ("ARENA MAIZ CAT 4 KG", "Arena De Maiz Para Gatos Maiz Cat 4 Kg"),
    ("VET NAT CANINE GASTRO INTESTINAL X 2 KG", "Vet Life Alimento Para Perro Gastrointestinal"),
    ("AGILITY GOLD PERRO ADULTO OBESO X 1.5 KG", "Agility Gold Alimento Seco para Perro Adultos Obesos"),
    ("PRO PLAN VETE DIETS UR URINARY PERRO 2 KG", "Comida para perro Purina Pro Plan Veterinary Diets UR Urinary"),
    ("NEXGARD SPECTRA  DE 7.5 A 15 KG (M)", "Nexgard Spectra M Antipulgas Para Perro 7.5-15 Kg"),
])
def test_same_product_matches(mine, theirs):
    assert cr.match_score(item(mine), theirs) >= cr.MIN_MATCH_SCORE


@pytest.mark.parametrize("mine,theirs", [
    ("AGILITY ADULTO GATO X 1.5 KG", "Agility Gold Grandes Adultos X1.5kl"),               # dog vs cat
    ("VET NAT CANINE GASTRO INTESTINAL X 2 KG", "Vet Life Alimento Para Gato Gastro Intestinal"),
    ("VET NAT FELINE URINARY STRUVITE 2 KG", "ração vet life natural renal para gatos adultos"),
    ("ARENA MAIZ CAT 10 KG", "Arena Smile Cats Aroma A Limon 10 Kg Arena De Maiz"),     # other brand
    ("AGILITY GOLD PERRO ADULTO OBESO X 1.5 KG", "Agility Gold Alimento para Perro Grande Adulto"),
    ("ROYAL CANIN SIAMESE CAT 2KG", "Royal Canin Feline Indoor Adult X 2 Kg"),
    ("ROYAL CANIN SIAMESE CAT 2KG", "Royal Canin Alimento para Gato Esterilizado"),
    ("PRO PLAN VETE DIETS UR URINARY PERRO 2 KG", "Pro Plan Veterinary Diets EN Gastroenteric Perro 2 kg"),
    ("AGILITY GOLD GRANDES ADULTOS 8 KG", "Agility Gold Grandes Adultos Piel X8kl"),
    ("CHUNKY GATOS SALMON Y CORDERO 1.5 KG", "Chunky Alimento para Perro Adulto Sabor a Cordero"),
])
def test_different_products_do_not_match(mine, theirs):
    assert cr.match_score(item(mine), theirs) < cr.MIN_MATCH_SCORE


def test_size_mismatch_is_rejected_and_unknown_size_needs_high_score():
    it = item("ARENA MAIZ CAT 10 KG")
    assert cr.best_matches(it, [offer("Arena De Maiz Para Gatos Maiz Cat 4 Kg", 20000, 5.0)]) == []
    m = cr.best_matches(it, [offer("Arena De Maiz Para Gatos Maiz Cat", 49000, 4.9)])
    assert m and m[0][1] is True                       # 49000 / 4.9 = 10 kg -> size verified


def test_search_query_drops_sizes_and_expands_abbreviations():
    assert item("VET NAT CANINE GASTRO INTESTINAL X 2 KG").search_query == "vet life natural canine gastro"
    assert item("BIOCANIS X 14 G").search_query == "biocanis"


# ------------------------------------------------------------------ pricing
def test_commission_by_category():
    assert round(CLIENT.commission_rate("CONCENTRADOS"), 4) == 0.1428
    assert round(CLIENT.commission_rate("ARENA"), 4) == 0.1666


def test_cheaper_competitor_within_margin_suggests_undercut():
    s = cr.suggest_price(item("X", cost=10000, price=15000), CLIENT, offer("X", 16000))
    assert s.suggested == 15800 and s.action.startswith("Bajar")
    assert s.margin(s.suggested) > CLIENT.min_margin_pct / 100


def test_competitor_below_cost_is_not_chased():
    s = cr.suggest_price(item("X", cost=30000, price=33000, category="MEDICAMENTOS"), CLIENT, offer("X", 32000))
    assert s.action.startswith("No competir")
    assert s.suggested == 38500                         # keeps the shop margin: 33000 / (1 - 14.28%)


def test_room_above_store_margin_and_already_cheapest():
    s = cr.suggest_price(item("X", cost=15000, price=26000, category="SUPLEMENTOS"), CLIENT, offer("X", 35000))
    assert s.action.startswith("Puede ser") and s.suggested == 34600
    s = cr.suggest_price(item("X", cost=15000, price=26000, category="SUPLEMENTOS"), CLIENT, offer("X", 35000),
                         rappi_price=31000)
    assert s.action.startswith("Ya es la más barata: puede subir") and s.suggested == 34600
    s = cr.suggest_price(item("X", cost=15000, price=26000, category="SUPLEMENTOS"), CLIENT, offer("X", 35000),
                         rappi_price=34700)
    assert s.action == "Ya es la más barata: mantener precio" and s.suggested == 34700


def test_already_cheapest_with_thin_margin_is_never_told_to_go_above_competitor():
    # synthetic: thin margin at the current Rappi price, competitor slightly above her
    s = cr.suggest_price(item("X", cost=130000, price=170000), CLIENT, offer("X", 165000), rappi_price=158000)
    assert s.suggested == 163300 and s.suggested < 165000
    assert s.margin(s.suggested) > s.margin(158000)
    assert any("Margen bajo" in n for n in s.notes)


def test_no_competitor_and_out_of_stock_notes():
    s = cr.suggest_price(item("X", price=10000, stock=0), CLIENT, None)
    assert s.action.startswith("Sin competencia") and s.suggested == 11700
    assert any("Sin stock" in n for n in s.notes)


# ------------------------------------------------------------------ io
def _workbook(path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventario DEFINITIVO"
    ws.append(["Barcode", "Nombre Producto", "Categoría", "Proveedor", "Costo Unitario (COP)",
               "Precio Venta (COP)", "Stock Actual", "Valor Total Inventario (COP)"])
    ws.append(["111", "BIOCANIS X 14 G", "SUPLEMENTOS", "P", 15000, 26000, 0, 0])
    ws.append(["222", "ARENA MAIZ CAT 4 KG", "ARENA", "P", 14000, 18000, 3, 42000])
    ws.append(["333", "JUGUETE VIEJO", "JUGUETES", "P", 5000, 9000, 0, 0])
    v = wb.create_sheet("VENTAS")
    v.append(["Año", "Fecha", "Factura / Ref", "Barcode", "Producto", "Categoría", "Cantidad", "Torre", "Apto"])
    v.append([2026, "2026-10-20", "F1", "111", "BIOCANIS", "SUPLEMENTOS", 2, "4", "1026"])
    v.append([2026, "2025-01-01", "F0", "333", "JUGUETE", "JUGUETES", 1, "1", "1"])
    wb.save(path)


def test_inventory_selection_and_report(tmp_path):
    path = tmp_path / "inv.xlsx"
    _workbook(path)
    items = cr.products_to_price(cr.load_inventory(path, 90, TODAY))
    assert [i.barcode for i in items] == ["111", "222"]          # sold recently first; old toy excluded
    assert items[0].sold_recent == 2

    db = PriceDatabase(tmp_path / "t.duckdb")
    base = {"snapshot_date": TODAY, "week_id": "2026-W45", "extracted_at": TODAY, "zone_id": "z", "zone": "Z",
            "brand": "Other", "pet_type": "Dog", "is_medical": False, "in_stock": True}
    db.insert_snapshots([
        {**base, "store_id": "99", "store_name": "Puppy House", "product_id": "5", "search_query": "biocanis",
         "product_name": "Biocanis Our Jeringa X 14 Gr", "price_current": 36800.0},
        {**base, "store_id": "1", "store_name": "Tienda Test", "product_id": "6", "search_query": CATALOG_QUERY,
         "product_name": "Maíz Cat Arena Ecológica para Gato", "price_current": 22800.0,
         "unit_price_value": 5.7, "unit_measure": "g"},
    ])
    db.insert_store_ranks([{"snapshot_date": TODAY, "week_id": "2026-W45", "extracted_at": TODAY, "zone_id": "z",
                            "zone": "Z", "search_query": "biocanis", "rank": 1, "store_id": "99",
                            "store_name": "Puppy House", "eta_text": "Hoy, 5 PM", "fee_text": "$ 6.000"}])
    config = AppConfig(zones=[ZoneConfig(id="z", name="Z", city="C", lat=0, lng=0, address="A")],
                       search_queries=["q"], client=CLIENT)
    assert cr.queries_needing_search(db, "z", ["biocanis", "arena maiz cat"], 30, TODAY) == ["arena maiz cat"]

    sugg = cr.build_suggestions(config, db, items, TODAY)
    bio, arena = sugg
    assert bio.competitor.price == 36800 and bio.rappi_price is None
    assert arena.rappi_price == 22800 and arena.competitor is None
    vis = cr.visibility(db, CLIENT)
    assert vis["per_query"][0][1] is None and vis["competitor_fee_median"] == 6000

    out = cr.write_report(config, sugg, vis, tmp_path / "r.xlsx", TODAY)
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Resumen", "Precios Rappi", "Visibilidad", "Visibilidad semanal", "Supuestos"]
    assert wb["Precios Rappi"]["A2"].value == "BIOCANIS X 14 G"
    assert wb["Visibilidad"]["B2"].value == "No aparece"


# ------------------------------------------------------------------ config / scraper helpers
def test_overlay_appends_zones_and_replaces_other_keys():
    merged = merge_overlay({"zones": [{"id": "a"}], "database_path": "x"},
                           {"extra_zones": [{"id": "b"}], "database_path": "y", "client": {"name": "c"}})
    assert [z["id"] for z in merged["zones"]] == ["a", "b"]
    assert merged["database_path"] == "y" and merged["client"] == {"name": "c"}


def test_parse_store_header():
    assert parse_store_header(["Puppis", "Hoy, 5 PM", "•", "$ 6.000", "Ir a la tienda"]) == \
        {"eta_text": "Hoy, 5 PM", "fee_text": "$ 6.000"}
    assert parse_store_header(["Turbo", "7 - 10 min", "•", "Envío gratis"]) == \
        {"eta_text": "7 - 10 min", "fee_text": "Envío gratis"}
