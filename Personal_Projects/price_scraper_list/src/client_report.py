"""
Competitive report for one Rappi store owner ("client"):

* Pricing sheet: for every product she has in stock or sold recently, find the
  same product at competitors visible from her address, then suggest a Rappi
  price from her cost, Rappi's commission and the cheapest competitor.
* Visibility: in which searches her store appears, and where.

Client data (inventory workbook, report) is private: it lives in data/client/,
which is git-ignored. Report texts are in Spanish (the store owner's language).
"""
import math
import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from src.config import AppConfig, ClientConfig, resolve_path
from src.database import PriceDatabase
from src.parser import ProductParser
from src.scraper import CATALOG_QUERY

GENERIC_TOKENS = {"perro", "gato", "adulto", "cachorro", "gatito", "raza", "pequeno", "mediano",
                  "grande", "humedo", "seco", "pollo", "carne", "salmon", "cordero", "arroz", "mix",
                  "arena", "dieta", "diet", "snack", "snacks", "premio", "premios", "antipulgas",
                  # category nouns / manufacturer prefixes that precede the real brand in Rappi names
                  "antiparasitario", "desparasitante", "interno", "externo", "suplemento", "probiotico",
                  "probioticos", "purina", "racao", "mascotas", "mascota", "y", "o"}
SIZE_CODES = {"xs", "s", "m", "l", "xl", "xxl"}
MIN_MATCH_SCORE = 0.7
MIN_MATCH_SCORE_SIZE_UNKNOWN = 0.85   # stricter when the package size cannot be verified

# Words that make two otherwise similar names different products. If both names
# use words of the same group and share none of them, they cannot match.
CONDITIONS = {"gastrointestinal", "renal", "urinary", "urinario", "hypoallergenic", "hipoalergenico",
              "obesidad", "light", "hepatic", "derm", "dermatology", "mobility", "diabetic", "cardiac",
              "struvite", "castrado", "sensitive", "satiety", "piel", "skin",
              "ur", "en", "om", "ha", "nf", "jm", "dm"}           # Pro Plan Veterinary Diets codes
NON_DEFAULT_STAGES = {"cachorro", "gatito", "senior", "mature", "junior"}
BREED_SIZES = {"pequeno", "mini", "mediano", "grande", "gigante", "toy"}
FLAVOURS = {"pollo", "cordero", "salmon", "carne", "res", "atun", "pavo", "cerdo", "pescado", "conejo", "pato",
            "bonito", "camaron", "cangrejo", "queso", "vieira", "mariscos"}
# Sub-lines of a brand that are different products ("Churu Pops" is not "Churu").
PRODUCT_LINES = {"pops", "bites", "rolls"}
VARIANT_GROUPS = [
    {"perro", "gato"},
    {"cachorro", "gatito", "adulto", "senior", "mature", "junior"},
    BREED_SIZES,
    CONDITIONS,
    {"humedo", "seco"},
    FLAVOURS,
]
# Groups where one name specifying a value and the other not is already a mismatch
# (e.g. "Agility Gold Obeso" is not plain "Agility Gold").
MUST_AGREE_ON_PRESENCE = [CONDITIONS, NON_DEFAULT_STAGES, BREED_SIZES, PRODUCT_LINES]
_PREP = [
    (r"gastro[\s-]*intestinal|gastroenteric", "gastrointestinal"),
    (r"\b(sterilised|sterilized|esterilizad[oa]s?|castrad[oa]s?)\b", "castrado"),
    (r"\b(obes[oa]s?|obesity|weight)\b", "obesidad"),
    (r"\b(lata|pouch|wet)\b", "humedo"),
    (r"\b(dry)\b", "seco"),
    (r"\b(cachorros?|puppy|junior)\b", "cachorro"),
    # flavours written in English (Inaba/Churu names carry both languages)
    (r"\btuna\b", "atun"),
    (r"\bshrimps?\b", "camaron"),
    (r"\bcrabs?\b", "cangrejo"),
    (r"\bcheese\b", "queso"),
    (r"\b(scallops?|vieiras)\b", "vieira"),
    (r"\b(seafood|sabores del mar|frutos del mar)\b", "mariscos"),
]


def _prep(name: str) -> str:
    text = (name or "").lower()
    for pattern, repl in _PREP:
        text = re.sub(pattern, repl, text)
    return text


def _tokens(name: str, inventory: bool = False) -> List[str]:
    toks = ProductParser.key_tokens(_prep(name), inventory=inventory)
    out = []
    for t in toks:
        if re.fullmatch(r"\d+(k|kl)", t):
            continue
        out.append(t)
        if t == "gatito":
            out.append("gato")
    return out


def variants_conflict(a: set, b: set) -> bool:
    for group in VARIANT_GROUPS:
        ga, gb = a & group, b & group
        if ga and gb and not ga & gb:
            return True
    # flavours: when both name them, they must name the same ones
    # ("atún con salmón" is not "atún con bonito")
    fa, fb = a & FLAVOURS, b & FLAVOURS
    if fa and fb and fa != fb:
        return True
    return any(bool(a & group) != bool(b & group) for group in MUST_AGREE_ON_PRESENCE)


def first_brand_token(tokens: List[str]) -> Optional[str]:
    return next((t for t in tokens if t not in GENERIC_TOKENS and not t.isdigit() and len(t) > 1), None)


# --------------------------------------------------------------------------- inventory
@dataclass
class InventoryItem:
    barcode: str
    name: str
    category: str
    cost: float
    store_price: float
    stock: float
    sold_recent: float = 0.0

    @property
    def tokens(self) -> List[str]:
        return _tokens(self.name, inventory=True)

    @property
    def size(self) -> Optional[float]:
        return ProductParser.size_in_base_units(self.name)

    @property
    def search_query(self) -> str:
        """Words a shopper would type: first informative words of her name, no sizes."""
        text = re.sub(r"\(.*?\)", " ", self.name)
        for pattern, repl in ProductParser.INVENTORY_ABBREVIATIONS:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        text = ProductParser.SIZE_PATTERN.sub(" ", text)
        words = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9/]+", text)
                 if len(w) > 2 and w.lower() not in ProductParser.KEY_STOPWORDS and not w.isdigit()]
        return " ".join(words[:5]).lower()


def _header_index(header: tuple, *names: str) -> int:
    norm = [str(h or "").strip().lower() for h in header]
    for n in names:
        if n.lower() in norm:
            return norm.index(n.lower())
    raise KeyError(f"Column not found: {names} in {header}")


def load_inventory(path: Path, sales_window_days: int, today: Optional[date] = None) -> List[InventoryItem]:
    """
    Reads 'Inventario DEFINITIVO' (costs, prices, stock) and units sold in the last
    `sales_window_days` from 'VENTAS'. Only product columns are read — the sales
    sheet's customer columns (tower, apartment...) are never touched.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    inv_ws = wb["Inventario DEFINITIVO"]
    rows = inv_ws.iter_rows(values_only=True)
    h = next(rows)
    ix = {k: _header_index(h, *v) for k, v in {
        "barcode": ("Barcode",), "name": ("Nombre Producto",), "category": ("Categoría", "Categoria"),
        "cost": ("Costo Unitario (COP)",), "price": ("Precio Venta (COP)",), "stock": ("Stock Actual",),
    }.items()}
    items = {}
    for r in rows:
        if not r or r[ix["barcode"]] in (None, ""):
            continue
        bc = str(r[ix["barcode"]]).strip()
        items[bc] = InventoryItem(
            barcode=bc, name=str(r[ix["name"]] or "").strip(), category=str(r[ix["category"]] or "").strip(),
            cost=float(r[ix["cost"]] or 0), store_price=float(r[ix["price"]] or 0), stock=float(r[ix["stock"]] or 0),
        )

    if "VENTAS" in wb.sheetnames:
        since = (today or date.today()) - timedelta(days=sales_window_days)
        rows = wb["VENTAS"].iter_rows(values_only=True)
        h = next(rows)
        i_date, i_bc, i_qty = (_header_index(h, "Fecha"), _header_index(h, "Barcode"), _header_index(h, "Cantidad"))
        for r in rows:
            try:
                d = r[i_date] if isinstance(r[i_date], (date, datetime)) else datetime.strptime(str(r[i_date])[:10], "%Y-%m-%d")
            except (TypeError, ValueError):
                continue
            d = d.date() if isinstance(d, datetime) else d
            bc = str(r[i_bc] or "").strip()
            if d >= since and bc in items:
                items[bc].sold_recent += float(r[i_qty] or 0)
    wb.close()
    return list(items.values())


def products_to_price(items: List[InventoryItem]) -> List[InventoryItem]:
    """In stock or recently sold, with a usable cost and price; best sellers first."""
    keep = [i for i in items if (i.stock > 0 or i.sold_recent > 0) and i.cost > 0 and i.store_price > 0]
    return sorted(keep, key=lambda i: (-i.sold_recent, -i.stock, i.name))


# --------------------------------------------------------------------------- matching
@dataclass
class Offer:
    store_id: str
    store_name: str
    product_name: str
    price: float
    unit_price: Optional[float]
    unit_measure: Optional[str]
    snapshot_date: date
    product_id: Optional[str] = None

    @property
    def size(self) -> Optional[float]:
        if self.unit_price and self.unit_measure in ("g", "ml") and self.unit_price > 0:
            return self.price / self.unit_price
        return ProductParser.size_in_base_units(self.product_name)


def match_score(item: InventoryItem, offer_name: str) -> float:
    """
    0..1 similarity between her inventory name and a Rappi product name.
    Mostly "how much of her name is covered" (Rappi names carry extra filler).
    Her first non-generic word (usually the brand) must be present.
    """
    mine = item.tokens
    their_list = _tokens(offer_name)
    theirs = set(their_list)
    if not mine or not theirs:
        return 0.0
    # brand check both ways: her brand in their name and their brand in hers
    for brand, other in ((first_brand_token(mine), theirs), (first_brand_token(their_list), set(mine))):
        if brand and brand not in other:
            return 0.0
    # her distinctive words (product line, formula) must be there: all of them when she
    # has 3 or fewer, all but one otherwise ("Royal Canin Siamese" is not "Royal Canin Indoor")
    distinctive = {t for t in mine if t not in GENERIC_TOKENS and t not in SIZE_CODES
                   and not t.isdigit() and len(t) > 1}
    if len(distinctive - theirs) > (0 if len(distinctive) <= 3 else 1):
        return 0.0
    if variants_conflict(set(mine), theirs):
        return 0.0
    common = len(set(mine) & theirs)
    return round(0.75 * common / len(set(mine)) + 0.25 * common / len(theirs), 3)


def sizes_compatible(a: Optional[float], b: Optional[float], tolerance: float = 0.12) -> Optional[bool]:
    if not a or not b:
        return None
    return abs(a - b) / max(a, b) <= tolerance


def best_matches(item: InventoryItem, offers: List[Offer]) -> List[tuple]:
    """[(score, size_checked, offer)] above the threshold, cheapest first."""
    out = []
    for o in offers:
        score = match_score(item, o.product_name)
        if score < MIN_MATCH_SCORE:
            continue
        ok = sizes_compatible(item.size, o.size)
        if ok is False or (ok is None and score < MIN_MATCH_SCORE_SIZE_UNKNOWN):
            continue
        out.append((score, ok is True, o))
    return sorted(out, key=lambda t: (t[2].price, -t[0]))


# --------------------------------------------------------------------------- pricing
def round_up(x: float, step: int = 100) -> float:
    return math.ceil(x / step) * step


def round_down(x: float, step: int = 100) -> float:
    return math.floor(x / step) * step


@dataclass
class PriceSuggestion:
    item: InventoryItem
    commission: float
    rappi_price: Optional[float] = None
    rappi_name: Optional[str] = None
    competitor: Optional[Offer] = None
    competitor_score: Optional[float] = None
    competitor_size_checked: bool = False
    competitors_found: int = 0
    competitor_suspect: bool = False     # matched by name but price too far off to trust
    units: int = 1                       # inventory units in one Rappi listing
    suggested: float = 0.0
    action: str = ""
    notes: List[str] = field(default_factory=list)

    def profit(self, price: Optional[float]) -> Optional[float]:
        return None if not price else price * (1 - self.commission) - self.item.cost

    def margin(self, price: Optional[float]) -> Optional[float]:
        p = self.profit(price)
        return None if p is None else p / price


PACK_COUNT = re.compile(r"\b(\d{1,2})\s*(?:piezas|pzs|unidades|und|uds|tubos|sobres)\b", re.IGNORECASE)


def pack_count(name: str) -> Optional[int]:
    """Units stated in an inventory name ('4 PIEZAS 56 GR' -> 4), if more than one."""
    m = PACK_COUNT.search(name or "")
    return int(m.group(1)) if m and int(m.group(1)) > 1 else None


def competitor_price_plausible(item: InventoryItem, client: ClientConfig, price: float) -> bool:
    if item.store_price <= 0:
        return True
    ratio = price / item.store_price
    return client.competitor_price_ratio_min <= ratio <= client.competitor_price_ratio_max


def suggest_price(item: InventoryItem, client: ClientConfig, competitor: Optional[Offer],
                  rappi_price: Optional[float] = None) -> PriceSuggestion:
    c = client.commission_rate(item.category)
    s = PriceSuggestion(item=item, commission=c, rappi_price=rappi_price, competitor=competitor)
    keep_store_margin = round_up(item.store_price / (1 - c))          # nets the same as a direct (WhatsApp) sale
    floor = round_up(item.cost / (1 - c - client.min_margin_pct / 100))  # lowest price we recommend
    break_even = item.cost / (1 - c)

    if competitor is not None and not competitor_price_plausible(item, client, competitor.price):
        # Same name, but a price this far from hers means another product or pack size:
        # show it for review, never price against it.
        s.competitor_suspect = True
        s.suggested = keep_store_margin
        s.action = ("Revisar coincidencia: el precio del competidor es muy distinto "
                    "(posible otro producto o presentación); se usa el precio que conserva el margen de venta directa")
        n = pack_count(item.name)
        if n and competitor_price_plausible(item, client, competitor.price / n):
            s.notes.append(f"Parece precio por unidad y el competidor vende el paquete de {n} "
                           f"(${competitor.price / n:,.0f} por unidad)".replace(",", "."))
        competitor = None
    elif competitor is None:
        s.suggested = keep_store_margin
        s.action = "Sin competencia visible: usar precio que conserva el margen de venta directa"
    else:
        target = round_down(competitor.price * (1 - client.undercut_pct / 100))
        if target >= keep_store_margin:
            s.suggested = target
            s.action = "Puede ser la más barata ganando igual o más que en venta directa"
        elif target >= floor:
            s.suggested = target
            s.action = "Bajar para ser la más barata (margen menor que en venta directa)"
        elif competitor.price < break_even:
            s.suggested = keep_store_margin
            s.action = "No competir en precio: el competidor vende por debajo de tu costo + comisión de Rappi"
        else:
            s.suggested = keep_store_margin
            s.action = f"No competir en precio: igualarlo deja menos de {client.min_margin_pct:.0f}% de margen"
        # Already the cheapest: never suggest giving that up; capture the room below the competitor.
        if rappi_price and rappi_price <= competitor.price:
            if target > rappi_price:
                s.suggested = target
                s.action = "Ya es la más barata: puede subir al precio sugerido y seguir siéndolo"
            else:
                s.suggested = rappi_price
                s.action = "Ya es la más barata: mantener precio"
            m = s.margin(s.suggested)
            if m < client.min_margin_pct / 100:
                s.notes.append(f"Margen bajo ({m:.1%}) aun siendo la más barata: revisar costo con el proveedor")
    if item.stock <= 0:
        s.notes.append("Sin stock: no publicar hasta reponer (las cancelaciones se le cobran)")
    elif rappi_price is None:
        s.notes.append("No está publicado en Rappi: publicar")
    return s


# --------------------------------------------------------------------------- data access
def load_offers(db: PriceDatabase, zone_id: str, since: date, exclude_store: str) -> List[Offer]:
    with db.get_connection() as con:
        rows = con.execute(
            """SELECT store_id, store_name, product_name, price_current, unit_price_value, unit_measure, snapshot_date
               FROM product_snapshots
               WHERE zone_id = ? AND snapshot_date >= ? AND store_id <> ? AND in_stock
               QUALIFY ROW_NUMBER() OVER (PARTITION BY store_id, product_id ORDER BY snapshot_date DESC) = 1""",
            [zone_id, since, exclude_store],
        ).fetchall()
    return [Offer(*r) for r in rows]


def load_client_catalog(db: PriceDatabase, client: ClientConfig) -> List[Offer]:
    with db.get_connection() as con:
        rows = con.execute(
            """SELECT store_id, store_name, product_name, price_current, unit_price_value, unit_measure, snapshot_date,
                      product_id
               FROM product_snapshots
               WHERE store_id = ? AND zone_id = ?
                 AND snapshot_date = (SELECT MAX(snapshot_date) FROM product_snapshots
                                      WHERE store_id = ? AND search_query = ?)""",
            [client.store_id, client.zone_id, client.store_id, CATALOG_QUERY],
        ).fetchall()
    return [Offer(*r) for r in rows]


def queries_needing_search(db: PriceDatabase, zone_id: str, queries: List[str], max_age_days: int,
                           today: date) -> List[str]:
    since = today - timedelta(days=max_age_days)
    with db.get_connection() as con:
        done = {r[0] for r in con.execute(
            "SELECT DISTINCT search_query FROM search_store_ranks WHERE zone_id = ? AND snapshot_date >= ?",
            [zone_id, since]).fetchall()}
    return [q for q in dict.fromkeys(queries) if q and q not in done]


def visibility(db: PriceDatabase, client: ClientConfig) -> Dict[str, list]:
    with db.get_connection() as con:
        latest = con.execute("SELECT MAX(snapshot_date) FROM search_store_ranks WHERE zone_id = ?",
                             [client.zone_id]).fetchall()[0][0]
        if latest is None:
            return {"latest": None, "per_query": [], "history": []}
        per_query = con.execute(
            """SELECT search_query,
                      MAX(CASE WHEN store_id = ? THEN rank END) AS her_rank,
                      STRING_AGG(rank || '. ' || store_name || COALESCE(' (' || fee_text || ')', ''), '  |  ' ORDER BY rank) AS stores
               FROM search_store_ranks WHERE zone_id = ? AND snapshot_date = ?
               GROUP BY search_query ORDER BY her_rank NULLS LAST, search_query""",
            [client.store_id, client.zone_id, latest]).fetchall()
        history = con.execute(
            """WITH t AS (SELECT snapshot_date, COUNT(DISTINCT search_query) AS n FROM search_store_ranks
                          WHERE zone_id = ? GROUP BY 1)
               SELECT t.snapshot_date, t.n, COUNT(DISTINCT r.search_query) AS appeared, ROUND(AVG(r.rank), 1)
               FROM t LEFT JOIN search_store_ranks r
                 ON r.snapshot_date = t.snapshot_date AND r.zone_id = ? AND r.store_id = ?
               GROUP BY t.snapshot_date, t.n ORDER BY t.snapshot_date""",
            [client.zone_id, client.zone_id, client.store_id]).fetchall()
        fees = con.execute(
            """SELECT fee_text FROM search_store_ranks WHERE zone_id = ? AND snapshot_date = ? AND store_id <> ?""",
            [client.zone_id, latest, client.store_id]).fetchall()
    fee_values = [ProductParser.parse_price_text(f[0]) for f in fees if f[0] and f[0].startswith("$")]
    return {"latest": latest, "per_query": per_query, "history": history,
            "competitor_fee_median": sorted(fee_values)[len(fee_values) // 2] if fee_values else None}


# --------------------------------------------------------------------------- report
def build_suggestions(config: AppConfig, db: PriceDatabase, items: List[InventoryItem],
                      today: date) -> List[PriceSuggestion]:
    client = config.client
    offers = load_offers(db, client.zone_id, today - timedelta(days=client.product_search_max_age_days),
                         client.store_id)
    catalog = load_client_catalog(db, client)
    out = []
    for item in items:
        # Sold by the unit directly but listed as a pack on Rappi: price the pack.
        units = client.units_per_listing.get(item.barcode, 1)
        if units > 1:
            item = replace(item, cost=item.cost * units, store_price=item.store_price * units)
        mine = best_matches(item, catalog)
        rappi = mine[0][2] if mine else None
        matches = best_matches(item, offers)
        comp = matches[0] if matches else None
        s = suggest_price(item, client, comp[2] if comp else None, rappi.price if rappi else None)
        s.rappi_name = rappi.product_name if rappi else None
        s.units = units
        if units > 1:
            s.notes.append(f"Paquete de {units} en Rappi: costo y precio de venta directa × {units} "
                           f"(stock y ventas en unidades); sugerido por unidad ${s.suggested / units:,.0f}"
                           .replace(",", "."))
        if comp:
            s.competitor_score, s.competitor_size_checked = comp[0], comp[1]
            s.competitors_found = len({m[2].store_id for m in matches})
            if not comp[1]:
                s.notes.append("Tamaño no verificado: revisar que sea la misma presentación")
        out.append(s)
    return out


# --------------------------------------------------------------------------- her own Rappi prices
PRICE_TOLERANCE = 100   # COP; Rappi shows prices rounded, so smaller gaps are not a change


@dataclass
class RappiAdjustment:
    """One of her Rappi listings checked against her rule: Rappi = WhatsApp price + markup."""
    item: Optional[InventoryItem]
    listing: Optional[Offer]
    units: int = 1
    commission: float = 0.0
    target: Optional[float] = None
    action: str = ""
    notes: List[str] = field(default_factory=list)
    barcode: Optional[str] = None

    @property
    def label(self) -> str:
        return self.item.name if self.item else self.listing.product_name if self.listing else (self.barcode or "")

    @property
    def needs_change(self) -> bool:
        return self.action in ("Subir precio", "Bajar precio")

    @property
    def whatsapp(self) -> Optional[float]:
        return self.item.store_price * self.units if self.item else None

    @property
    def cost(self) -> Optional[float]:
        return self.item.cost * self.units if self.item else None

    def profit(self) -> Optional[float]:
        return None if not (self.target and self.item) else self.target * (1 - self.commission) - self.cost


def rappi_adjustments(client: ClientConfig, inventory: List[InventoryItem],
                      catalog: List[Offer]) -> List[RappiAdjustment]:
    """Her linked listings (client.rappi_listings) vs her markup rule, plus listings not linked yet."""
    by_id = {str(o.product_id): o for o in catalog if o.product_id}
    inv = {i.barcode: i for i in inventory}
    markup = 1 + client.rappi_markup_pct / 100
    out: List[RappiAdjustment] = []
    for barcode, pid in client.rappi_listings.items():
        item, listing = inv.get(barcode), by_id.get(str(pid))
        a = RappiAdjustment(item=item, listing=listing, units=client.units_per_listing.get(barcode, 1),
                            barcode=barcode)
        if item is None:
            a.action = "Revisar vínculo"
            a.notes.append(f"El código de barras vinculado ({barcode}) ya no está en el inventario")
            out.append(a)
            continue
        a.commission = client.commission_rate(item.category)
        if a.whatsapp:
            a.target = round(a.whatsapp * markup)
        if listing is None:
            a.action = "No aparece en Rappi"
            a.notes.append("Agotado o desactivado esta semana")
        elif not a.target:
            a.action = "Revisar inventario"
            a.notes.append("Sin precio de venta en el inventario")
        elif abs(listing.price - a.target) <= PRICE_TOLERANCE:
            a.action = "OK"
        else:
            a.action = "Subir precio" if listing.price < a.target else "Bajar precio"
        if listing is not None and item.stock <= 0:
            a.notes.append("Sin stock: desactivar en Rappi hasta reponer (las cancelaciones se le cobran)")
        if a.target and item.cost and a.profit() < 0:
            a.notes.append("Pierde plata a este precio: revisar costo o precio de venta")
        if a.units > 1:
            a.notes.append(f"Paquete de {a.units}: precio WhatsApp por unidad × {a.units}")
        out.append(a)
    linked = {str(p) for p in client.rappi_listings.values()}
    for o in catalog:
        if str(o.product_id) not in linked:
            out.append(RappiAdjustment(item=None, listing=o, action="Vincular",
                                       notes=["Publicación sin producto del inventario vinculado: no se puede revisar"]))
    order = {"Subir precio": 0, "Bajar precio": 0, "Revisar inventario": 1, "Revisar vínculo": 1, "Vincular": 2,
             "No aparece en Rappi": 3, "OK": 4}
    return sorted(out, key=lambda a: (order.get(a.action, 5), a.label))


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
ACTION_FILLS = {
    "Ya es": "C6EFCE", "Puede ser": "C6EFCE", "Bajar": "FFEB9C", "No competir": "F8CBAD", "Sin competencia": "DDEBF7",
    "Revisar": "E4DFEC",
}
COP = '#,##0'
PCT = '0.0%'


def _sheet(wb, title: str, headers: List[str], rows: List[list], widths: List[int], formats: Dict[int, str] = None):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEADER_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for col, fmt in (formats or {}).items():
        for cell in ws.iter_cols(min_col=col, max_col=col, min_row=2):
            for c in cell:
                c.number_format = fmt
    ws.freeze_panes = "B2"
    if rows:
        ws.auto_filter.ref = ws.dimensions
    return ws


def write_report(config: AppConfig, suggestions: List[PriceSuggestion], vis: Dict[str, list],
                 out_path: Path, today: date, adjustments: Optional[List[RappiAdjustment]] = None,
                 probe_rows: Optional[List[dict]] = None) -> Path:
    client = config.client
    adjustments = adjustments or []
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # --- Resumen
    with_comp = [s for s in suggestions if s.competitor and not s.competitor_suspect]
    cheapest_now = [s for s in with_comp if s.rappi_price and s.rappi_price <= s.competitor.price]
    published = [s for s in suggestions if s.rappi_price]
    hist = vis["history"][-1] if vis["history"] else None
    actions: Dict[str, int] = {}
    for s in suggestions:
        key = s.action.split(":")[0]
        actions[key] = actions.get(key, 0) + 1
    summary = [
        ["Tienda", client.name],
        ["Fecha del análisis", today.isoformat()],
        ["Productos analizados (con stock o vendidos en los últimos %d días)" % client.sales_window_days, len(suggestions)],
        ["Publicados en Rappi", len(published)],
        ["Con stock y NO publicados", sum(1 for s in suggestions if s.item.stock > 0 and not s.rappi_price)],
        ["Con el mismo producto en la competencia", len(with_comp)],
        ["Publicados y hoy los más baratos", len(cheapest_now)],
        ["Búsquedas medidas (última semana)", hist[1] if hist else "-"],
        ["Búsquedas donde aparece la tienda", hist[2] if hist else "-"],
        ["Costo de envío mediano de la competencia", vis.get("competitor_fee_median") or "-"],
        [f"Precios a corregir en Rappi (pestaña 'Ajustar en Rappi', regla +{client.rappi_markup_pct:g}%)",
         sum(1 for a in adjustments if a.needs_change)],
        [],
        ["Acción sugerida", "Productos"],
        *[[k, v] for k, v in sorted(actions.items(), key=lambda kv: -kv[1])],
    ]
    ws = wb.create_sheet("Resumen")
    for r in summary:
        ws.append(r)
    ws.column_dimensions["A"].width = 70
    ws.column_dimensions["B"].width = 28
    for row in (1, summary.index(["Acción sugerida", "Productos"]) + 1):
        for c in ws[row]:
            c.font = Font(bold=True)

    # --- Ajustar en Rappi: her listings vs her own rule (WhatsApp + markup)
    adj_rows = []
    for a in adjustments:
        live = a.listing.price if a.listing else None
        p = a.profit()
        adj_rows.append([
            a.action, a.item.name if a.item else None, a.listing.product_name if a.listing else None,
            a.item.stock if a.item else None, a.units if a.item else None, a.cost, a.whatsapp, a.target, live,
            (live - a.target) if (live and a.target) else None, p, (p / a.target) if (p is not None and a.target) else None,
            "; ".join(a.notes),
        ])
    ws = _sheet(wb, "Ajustar en Rappi",
                ["Acción", "Producto (inventario)", "Publicación en Rappi", "Stock", "Unidades por publicación",
                 "Costo", "Precio WhatsApp", f"Precio Rappi según su regla (+{client.rappi_markup_pct:g}%)",
                 "Precio Rappi actual", "Diferencia (actual - regla)", "Utilidad en Rappi con la regla",
                 "Margen en Rappi con la regla", "Notas"],
                adj_rows, [16, 46, 46, 8, 11, 11, 11, 14, 12, 12, 13, 11, 60],
                {6: COP, 7: COP, 8: COP, 9: COP, 10: '+#,##0;-#,##0', 11: COP, 12: PCT})
    adj_fills = {"Subir": "FFEB9C", "Bajar": "FFEB9C", "OK": "C6EFCE", "Revisar": "F8CBAD", "Vincular": "E4DFEC",
                 "No aparece": "DDEBF7"}
    for r in range(2, ws.max_row + 1):
        action = ws.cell(r, 1).value or ""
        for prefix, color in adj_fills.items():
            if action.startswith(prefix):
                ws.cell(r, 1).fill = PatternFill("solid", fgColor=color)
                break

    # --- Precios Rappi
    headers = ["Producto (inventario)", "Categoría", "Stock", f"Vendidas {client.sales_window_days} días",
               "Costo", "Precio venta directa (WhatsApp)", "Comisión Rappi (con IVA)", "Precio Rappi actual", "Margen actual",
               "Competidor más barato", "Precio competidor", "Producto del competidor", "Coincidencia",
               "Tiendas con el producto", "Precio sugerido", "Utilidad por unidad", "Margen sugerido",
               "Diferencia vs competidor", "Acción", "Notas"]
    rows = []
    for s in suggestions:
        comp = s.competitor
        rows.append([
            s.item.name, s.item.category, s.item.stock, s.item.sold_recent, s.item.cost, s.item.store_price,
            s.commission, s.rappi_price, s.margin(s.rappi_price),
            comp.store_name if comp else None, comp.price if comp else None, comp.product_name if comp else None,
            s.competitor_score, s.competitors_found or None,
            s.suggested, s.profit(s.suggested), s.margin(s.suggested),
            (s.suggested / comp.price - 1) if comp and not s.competitor_suspect else None,
            s.action, "; ".join(s.notes),
        ])
    ws = _sheet(wb, "Precios Rappi", headers, rows,
                [48, 20, 8, 10, 11, 11, 11, 11, 10, 24, 11, 48, 11, 10, 11, 11, 10, 11, 52, 50],
                {5: COP, 6: COP, 7: PCT, 8: COP, 9: PCT, 11: COP, 13: '0.00', 15: COP, 16: COP, 17: PCT, 18: '+0.0%;-0.0%'})
    for r in range(2, ws.max_row + 1):
        action = ws.cell(r, 19).value or ""
        for prefix, color in ACTION_FILLS.items():
            if action.startswith(prefix):
                ws.cell(r, 19).fill = PatternFill("solid", fgColor=color)
                break

    # --- Visibilidad
    _sheet(wb, "Visibilidad", ["Búsqueda", "Posición de la tienda", "Tiendas que muestra Rappi (posición, envío)"],
           [[q, r if r else "No aparece", st] for q, r, st in vis["per_query"]], [32, 18, 140])
    _sheet(wb, "Visibilidad semanal", ["Fecha", "Búsquedas medidas", "Aparece en", "Posición promedio"],
           [list(h) for h in vis["history"]], [14, 18, 14, 18])

    # --- Visibilidad por hora (hourly probe, only once it has data)
    if probe_rows:
        from src import probe
        _sheet(wb, "Visibilidad por hora",
               ["Tipo de día", "Hora", "Mediciones", "Página de la tienda abre (% de veces)",
                "Búsquedas donde aparece (promedio)", "Búsquedas medidas (promedio)", "Mejor posición"],
               probe.by_hour(client, probe_rows), [24, 8, 12, 20, 20, 18, 12], {4: PCT, 5: '0.0', 6: '0.0'})
        detail = []
        for run in probe.runs(probe_rows):
            open_ = probe.declared_open(client, run.probed_at)
            detail.append([run.probed_at.date().isoformat(), probe.DAY_NAMES[run.probed_at.weekday()],
                           f"{run.probed_at:%H:%M}", {True: "Abierta", False: "Cerrada", None: "-"}[open_],
                           run.rappi_status or "-",
                           {True: "Abre", False: "No abre", None: "-"}[run.store_page_ok],
                           run.searches, run.appeared, run.best_rank, run.where])
        _sheet(wb, "Visibilidad hora a hora",
               ["Fecha", "Día", "Hora", "Según su horario", "Según Rappi (tiempo de entrega)", "Página de la tienda",
                "Búsquedas medidas", "Aparece en", "Mejor posición", "Dónde aparece"],
               detail, [12, 11, 8, 16, 28, 18, 16, 11, 13, 80])

    # --- Supuestos
    ws = wb.create_sheet("Supuestos")
    notes = [
        ["Supuesto / regla", "Valor"],
        ["Comisión Rappi alimento (contrato, Anexo 1)", f"{client.commission_pct.get('alimento')}% + IVA"],
        ["Comisión Rappi medicina", f"{client.commission_pct.get('medicina')}% + IVA"],
        ["Comisión Rappi accesorios (incluye arena, aseo, juguetes)", f"{client.commission_pct.get('accesorios')}% + IVA"],
        ["IVA", f"{client.iva_pct}%"],
        ["Precio venta directa", "Columna 'Precio Venta' del inventario (lo que cobra por WhatsApp / venta directa)"],
        ["Precio que conserva el margen de venta directa", "Precio venta directa / (1 - comisión con IVA), redondeado a 100"],
        ["Margen mínimo aceptado después de comisión", f"{client.min_margin_pct}%"],
        ["Para ser la más barata", f"{client.undercut_pct}% por debajo del competidor más barato, redondeado a 100"],
        ["Competencia considerada", f"Tiendas que Rappi muestra desde la dirección de la tienda, últimos {client.product_search_max_age_days} días"],
        ["Coincidencia", f"0 a 1; se exige {MIN_MATCH_SCORE} o más, la misma marca y el mismo tamaño cuando se puede verificar"],
        ["Precio del competidor creíble",
         f"Entre {client.competitor_price_ratio_min:g} y {client.competitor_price_ratio_max:g} veces el precio de venta directa; "
         "fuera de ese rango se muestra para revisar pero no se usa para sugerir precio"],
        ["Ajustar en Rappi", f"Regla de la tienda: precio Rappi = precio WhatsApp + {client.rappi_markup_pct:g}% "
                             f"(cubre la comisión). Se compara con el precio que Rappi muestra hoy; diferencias de hasta "
                             f"${PRICE_TOLERANCE} se consideran iguales"],
        ["Visibilidad por hora", "Medición cada hora desde la dirección de la tienda: si la página de la tienda abre y en "
                                 "qué posición la muestra Rappi en algunas búsquedas (Rappi muestra unas 5 tiendas por "
                                 "búsqueda). 'Según su horario' usa el horario declarado por la tienda"],
        ["Productos vendidos por unidad", "Si en Rappi se publica el paquete, costo y precio de venta directa se multiplican "
                                          "por las unidades del paquete (ver Notas)"],
        ["Importante", "El contrato (cláusula 6 viii) pide ofrecer en Rappi los mismos precios que en sus demás canales "
                       "(incluye WhatsApp). Confirmar con el ejecutivo de Rappi antes de usar precios distintos."],
        ["Importante", "Revisar las coincidencias marcadas 'Tamaño no verificado' antes de cambiar precios."],
    ]
    for r in notes:
        ws.append(r)
    ws.column_dimensions["A"].width = 60
    ws.column_dimensions["B"].width = 110
    for c in ws[1]:
        c.font = Font(bold=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def default_report_path(client: ClientConfig, today: date) -> Path:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", client.name).strip("_")
    return client.report_path / f"{safe}_Rappi_{today.isoformat()}.xlsx"


def inventory_file(client: ClientConfig) -> Path:
    if not client.inventory_path:
        raise ValueError("client.inventory_path is not set in config/settings.local.yaml")
    p = resolve_path(client.inventory_path)
    if "*" in p.name:
        # e.g. "data/client/Store_Backup_*.xlsx": newest backup by name (dates sort as text)
        matches = sorted(p.parent.glob(p.name))
        if not matches:
            raise FileNotFoundError(f"No inventory workbook matches: {p}")
        return matches[-1]
    if not p.exists():
        raise FileNotFoundError(f"Inventory workbook not found: {p}")
    return p
