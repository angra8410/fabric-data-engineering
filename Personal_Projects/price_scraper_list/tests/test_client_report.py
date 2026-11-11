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
    ("INABA GATO CHURU ATUN CON HOJUELAS DE BONITO 4 PIEZAS 56 GR",
     "Inaba Cat Snack Churu 4 Piezas - Tuna With Bonito Flakes - Hojuelas Atun - 56 Gr"),
    ("INABA GATO CHURU ATUN 4 PIEZAS 56 GR", "Inaba Churu Snack Para Gato Atún 4 Piezas 56 Gr - Tuna"),
    ("INABA GATO CHURU ATUN CON VIEIRA (TUNA RECIPE WITH SCALLOP) 4 PIEZAS 56 GR",
     "Inaba Churu Gato Tuna With Scallop Atún Y Vieira 4 Piezas 56 Gr"),
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
    # flavours must agree when both names give them; sub-lines are other products
    ("INABA GATO CHURU ATUN CON SALMON (TUNA RECIPE WITH SALMON) 4 PIEZAS 56 GR",
     "Inaba Cat Snack Churu 4 Piezas - Tuna With Bonito Flakes - Hojuelas Atun - 56 Gr"),
    ("INABA GATO CHURU ATUN CON POLLO (TUNA RECIPE WITH CHICKEN) 4 PIEZAS 56 GR",
     "Inaba Cat Snack Churu 4 Piezas - Tuna With Bonito Flakes - Hojuelas Atun - 56 Gr"),
    ("INABA GATO CHURU ATUN 4 PIEZAS 56 GR", "inaba cat snack churu pops 4 piezas - tuna - atun 60 gr"),
    ("INABA GATO CHURU ATUN CON CAMARON (TUNA RECIPE WITH SHRIMP) 4 PIEZAS 56 GR",
     "Inaba Churu Gato Atún 4 Piezas 56 Gr"),
    ("INABA GATO CHURU ATUN 4 PIEZAS 56 GR", "Inaba Churu Cat Tuna Recipe With Scallop 4 Pzs 56 g"),
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
    assert s.suggested == 15900 and s.action.startswith("Bajar")      # 100 COP under the competitor
    assert s.margin(s.suggested) > CLIENT.min_margin_pct / 100


def test_competitor_below_cost_is_not_chased():
    s = cr.suggest_price(item("X", cost=30000, price=33000, category="MEDICAMENTOS"), CLIENT, offer("X", 32000))
    assert s.action.startswith("No competir")
    assert s.suggested == 38500                         # keeps the shop margin: 33000 / (1 - 14.28%)


def test_room_above_store_margin_and_already_cheapest():
    s = cr.suggest_price(item("X", cost=15000, price=26000, category="SUPLEMENTOS"), CLIENT, offer("X", 35000))
    assert s.action.startswith("Puede ser") and s.suggested == 34900
    s = cr.suggest_price(item("X", cost=15000, price=26000, category="SUPLEMENTOS"), CLIENT, offer("X", 35000),
                         rappi_price=31000)
    assert s.action.startswith("Ya es la más barata: puede subir") and s.suggested == 34900
    s = cr.suggest_price(item("X", cost=15000, price=26000, category="SUPLEMENTOS"), CLIENT, offer("X", 35000),
                         rappi_price=34950)
    assert s.action == "Ya es la más barata: mantener precio" and s.suggested == 34950


def test_already_cheapest_with_thin_margin_is_never_told_to_go_above_competitor():
    # synthetic: thin margin at the current Rappi price, competitor slightly above her
    s = cr.suggest_price(item("X", cost=130000, price=170000), CLIENT, offer("X", 165000), rappi_price=158000)
    assert s.suggested == 164900 and s.suggested < 165000
    assert s.margin(s.suggested) > s.margin(158000)
    assert any("Margen bajo" in n for n in s.notes)


def test_implausible_competitor_price_is_shown_but_not_priced_against():
    # synthetic: generic accessory matched to a branded one at 10x her price
    s = cr.suggest_price(item("PANOLETA PEQUENA", cost=1000, price=2000, category="ACCESORIOS"), CLIENT,
                         offer("Pañoleta Marca Pequeña", 20000))
    assert s.competitor_suspect and s.competitor.price == 20000
    assert s.action.startswith("Revisar") and s.suggested == cr.round_up(2000 / (1 - s.commission))
    # far below her price is suspicious too
    s = cr.suggest_price(item("X", cost=10000, price=50000), CLIENT, offer("X", 15000))
    assert s.competitor_suspect


def test_per_unit_price_against_pack_hints_the_pack():
    s = cr.suggest_price(item("MARCA SNACK 4 PIEZAS 56 GR", cost=2000, price=3000), CLIENT, offer("Marca Snack", 12000))
    assert s.competitor_suspect
    assert any("paquete de 4" in n and "3.000 por unidad" in n for n in s.notes)
    assert cr.pack_count("MARCA 4 PIEZAS 56 GR") == 4 and cr.pack_count("MARCA X 100 G") is None


def test_units_per_listing_prices_the_pack(tmp_path):
    db = PriceDatabase(tmp_path / "t.duckdb")
    base = {"snapshot_date": TODAY, "week_id": "2026-W45", "extracted_at": TODAY, "zone_id": "z", "zone": "Z",
            "brand": "Other", "pet_type": "Cat", "is_medical": False, "in_stock": True}
    db.insert_snapshots([{**base, "store_id": "99", "store_name": "Comp", "product_id": "7", "search_query": "q",
                          "product_name": "Marca Gato Snack Tubos 4 Piezas 56 Gr", "price_current": 12000.0}])
    client = CLIENT.model_copy(update={"units_per_listing": {"1": 4}})
    config = AppConfig(zones=[ZoneConfig(id="z", name="Z", city="C", lat=0, lng=0, address="A")],
                       search_queries=["q"], client=client)
    it = item("MARCA GATO SNACK TUBOS 4 PIEZAS 56 GR", cost=2000, price=3000, category="SNACKS")
    (s,) = cr.build_suggestions(config, db, [it], TODAY)
    assert s.units == 4 and s.item.cost == 8000 and s.item.store_price == 12000
    assert not s.competitor_suspect and s.suggested == 11900 and s.action.startswith("Bajar")
    assert any("Paquete de 4" in n for n in s.notes)


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

    client = CLIENT.model_copy(update={"rappi_listings": {"222": "6"}})
    checks = cr.listing_checks(client, items, cr.load_client_catalog(db, client), [])
    assert [(c.action, c.listing.price) for c in checks] == [("Sin competidor", 22800)]
    out = cr.write_report(config, sugg, vis, tmp_path / "r.xlsx", TODAY, checks)
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Resumen", "Cambiar precio en Rappi", "Precios Rappi", "Visibilidad",
                             "Visibilidad semanal", "Supuestos"]
    assert wb["Precios Rappi"]["A2"].value == "BIOCANIS X 14 G"
    assert wb["Cambiar precio en Rappi"]["B2"].value == "ARENA MAIZ CAT 4 KG"
    assert wb["Visibilidad"]["B2"].value == "No aparece"


def test_inventory_path_pattern_picks_newest_backup(tmp_path):
    for d in ("2026-11-05", "2026-11-10", "2026-10-30"):
        (tmp_path / f"Tienda_Backup_{d}.xlsx").write_bytes(b"")
    client = CLIENT.model_copy(update={"inventory_path": str(tmp_path / "Tienda_Backup_*.xlsx")})
    assert cr.inventory_file(client).name == "Tienda_Backup_2026-11-10.xlsx"


# ------------------------------------------------------------------ cambiar precio en Rappi
def test_listing_checks_price_100_under_cheapest_competitor():
    # synthetic: each product has its own brand so it only matches its own competitor offer
    client = CLIENT.model_copy(update={"rappi_listings": {
        "cut": "1", "up": "2", "keep": "3", "thin": "4", "solo": "5", "nostock": "6", "gone": "7", "old": "8"}})
    inv = [cr.InventoryItem("cut", "ALFA GATO 1 KG", "CONCENTRADOS", 7000, 10000, 2),
           cr.InventoryItem("up", "BETA GATO 1 KG", "CONCENTRADOS", 7000, 10000, 2),
           cr.InventoryItem("keep", "GAMA GATO 1 KG", "CONCENTRADOS", 7000, 10000, 2),
           cr.InventoryItem("thin", "DELTA GATO 1 KG", "CONCENTRADOS", 7500, 10000, 2),
           cr.InventoryItem("solo", "EPSILON GATO 1 KG", "CONCENTRADOS", 7500, 9000, 2),
           cr.InventoryItem("nostock", "ZETA GATO 1 KG", "CONCENTRADOS", 7000, 10000, 0),
           cr.InventoryItem("gone", "ETA GATO 1 KG", "CONCENTRADOS", 7000, 10000, 2)]
    mine = lambda pid, price, regular=None: cr.Offer("1", "Tienda", f"Listing {pid}", price, None, None, TODAY,
                                                     pid, regular)
    catalog = [mine("1", 12000, 13000), mine("2", 9000), mine("3", 10950), mine("4", 12000), mine("5", 8000),
               mine("6", 12000), mine("9", 5000)]
    offers = [offer("Alfa Gato 1 Kg", 11000), offer("Alfa Gato 1 Kg", 11500, store="Otra"),
              offer("Beta Gato 1 Kg", 11000), offer("Gama Gato 1 Kg", 11000), offer("Delta Gato 1 Kg", 8000),
              offer("Zeta Gato 1 Kg", 11000)]
    checks = cr.listing_checks(client, inv, catalog, offers)
    c = {(x.barcode or x.listing.product_id): x for x in checks}
    assert c["cut"].action == "Bajar precio" and c["cut"].suggested == 10900      # cheapest (11000) - 100
    assert any("descuento" in n for n in c["cut"].notes)
    assert c["up"].action == "Subir precio" and c["up"].suggested == 10900        # already cheapest, room to rise
    assert c["keep"].action == "Mantener" and c["keep"].suggested is None         # 10950 vs 10900: not worth it
    assert c["thin"].action == "No competir" and c["thin"].suggested is None      # 7900 leaves < 10% margin
    assert c["solo"].action == "Sin competidor" and any("Pierde plata" in n for n in c["solo"].notes)
    assert c["nostock"].action == "Desactivar"
    assert c["gone"].action == "No aparece en Rappi"
    assert c["old"].action == "Revisar vínculo"
    assert c["9"].action == "Vincular"
    commission = CLIENT.commission_rate("CONCENTRADOS")
    assert round(c["cut"].profit(10900)) == round(10900 * (1 - commission) - 7000)
    assert c["cut"].margin(10900) >= CLIENT.min_margin_pct / 100
    assert checks[0].needs_change and checks[-1].action == "Sin competidor"


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
