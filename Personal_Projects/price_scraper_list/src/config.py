import base64
import json
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

# Project root = folder that contains main.py / config / src. All relative paths
# (config file, database, exports) resolve against it, so the scripts work no
# matter which directory they are launched from (e.g. Windows Task Scheduler).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
# Optional, git-ignored overlay next to the config file (client data, private zones).
LOCAL_OVERLAY_NAME = "settings.local.yaml"


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


class ZoneConfig(BaseModel):
    id: str
    name: str
    city: str
    lat: float
    lng: float
    address: str
    # Optional per-zone search list; falls back to AppConfig.search_queries.
    search_queries: Optional[List[str]] = None

    def to_rappi_cookie(self, domain: str = ".rappi.com.co") -> dict:
        """
        Encodes geographic coordinates and address into the format
        expected by Rappi's 'currentLocation' session cookie
        (URL-encoded JSON, then Base64).
        """
        loc_dict = {
            "city": self.city,
            "lat": self.lat,
            "lng": self.lng,
            "url": self.city.lower().replace(" ", "-"),
            "address": self.address,
            "autoLocation": False,
            "active": True,
            "id": 1,
            "isInitialLocation": False,
        }
        encoded_json = urllib.parse.quote(json.dumps(loc_dict))
        b64_val = base64.b64encode(encoded_json.encode("utf-8")).decode("utf-8")
        return {"name": "currentLocation", "value": b64_val, "domain": domain, "path": "/"}


class ScraperSettings(BaseModel):
    navigation_timeout_ms: int = 45000
    results_timeout_ms: int = 15000
    max_scroll_rounds: int = 8
    delay_between_queries_ms: int = 1500
    retries: int = 1


class ClientConfig(BaseModel):
    """A Rappi store we analyse on behalf of its owner (lives in settings.local.yaml)."""
    name: str
    store_id: str
    store_slug: str                      # e.g. "900483846-velykapet-mt-enc"
    zone_id: str                         # zone (usually the store address) to measure from
    inventory_path: Optional[str] = None # owner's inventory workbook (costs, store prices, stock)
    report_dir: str = "data/client/reports"
    # Rappi platform fee by product family, % before IVA (contract Anexo 1).
    commission_pct: Dict[str, float] = Field(default_factory=lambda: {
        "alimento": 12.0, "medicina": 12.0, "accesorios": 14.0})
    iva_pct: float = 19.0
    # Inventory category -> product family (anything not listed is "alimento").
    category_family: Dict[str, str] = Field(default_factory=lambda: {
        "MEDICAMENTOS": "medicina", "SUPLEMENTOS": "medicina", "BIENESTAR Y CUIDADO": "medicina",
        "ACCESORIOS": "accesorios", "ACCESORIOS NO PET": "accesorios", "JUGUETES": "accesorios",
        "COMEDERO": "accesorios", "ASEO": "accesorios", "ARENA": "accesorios"})
    min_margin_pct: float = 10.0         # lowest margin (after commission) we suggest pricing at
    undercut_cop: float = 100.0          # suggest this many COP below the cheapest competitor
    # A competitor priced outside [min, max] x her direct price is most likely another
    # product or pack size: it is shown for review but never priced against.
    competitor_price_ratio_min: float = 0.4
    competitor_price_ratio_max: float = 2.5
    # Barcode -> units in one Rappi listing, for items whose inventory cost/price is per
    # unit but sold as a pack on Rappi (e.g. a 4-tube pack she sells tube by tube).
    units_per_listing: Dict[str, int] = Field(default_factory=dict)
    # Barcode -> Rappi product id of HER listing (names on Rappi are rewritten, so her own
    # listings are linked explicitly instead of matched by name).
    rappi_listings: Dict[str, str] = Field(default_factory=dict)
    # Hourly visibility probe (ADR-013): searches to check, declared opening hours
    # ("weekday"/"weekend" -> "10-20"; holidays use the weekend hours).
    probe_queries: List[str] = Field(default_factory=list)
    opening_hours: Dict[str, str] = Field(default_factory=dict)
    holidays: List[date] = Field(default_factory=list)
    sales_window_days: int = 90          # "recently sold" window for picking products
    product_search_max_age_days: int = 30
    max_product_searches: int = 200

    @property
    def report_path(self) -> Path:
        return resolve_path(self.report_dir)

    def commission_rate(self, category: Optional[str]) -> float:
        family = self.category_family.get((category or "").strip().upper(), "alimento")
        return self.commission_pct.get(family, 12.0) / 100 * (1 + self.iva_pct / 100)


class AppConfig(BaseModel):
    country: str = "co"
    base_url: str = "https://www.rappi.com.co"
    database_path: str = "data/rappi_prices.duckdb"
    # Colombia is UTC-5 all year (no DST). Snapshot dates/weeks use local time.
    utc_offset_hours: int = -5
    zones: List[ZoneConfig] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)
    scraper: ScraperSettings = Field(default_factory=ScraperSettings)
    client: Optional[ClientConfig] = None

    def queries_for(self, zone: ZoneConfig) -> List[str]:
        return zone.search_queries or self.search_queries

    def zone(self, zone_id: str) -> ZoneConfig:
        for z in self.zones:
            if z.id == zone_id:
                return z
        raise ValueError(f"Zone '{zone_id}' is not configured")

    @property
    def database_file(self) -> Path:
        return resolve_path(self.database_path)

    @property
    def cookie_domain(self) -> str:
        host = urllib.parse.urlparse(self.base_url).hostname or "www.rappi.com.co"
        return "." + host.removeprefix("www.")

    def local_now(self) -> datetime:
        return datetime.now(timezone(timedelta(hours=self.utc_offset_hours)))


def merge_overlay(base: dict, overlay: dict) -> dict:
    """`extra_zones` is appended to `zones`; every other overlay key replaces the base value."""
    merged = {**base, **{k: v for k, v in overlay.items() if k != "extra_zones"}}
    merged["zones"] = list(base.get("zones") or []) + list(overlay.get("extra_zones") or [])
    return merged


def load_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    p = Path(config_path)
    if not p.is_absolute() and not p.exists():
        p = resolve_path(p)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    overlay = p.parent / LOCAL_OVERLAY_NAME
    if overlay.exists():
        with open(overlay, "r", encoding="utf-8") as f:
            data = merge_overlay(data, yaml.safe_load(f) or {})
    config = AppConfig(**data)
    if not config.zones:
        raise ValueError(f"No zones configured in {p}")
    if not config.search_queries:
        raise ValueError(f"No search_queries configured in {p}")
    return config
