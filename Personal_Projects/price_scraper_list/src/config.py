import base64
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field

# Project root = folder that contains main.py / config / src. All relative paths
# (config file, database, exports) resolve against it, so the scripts work no
# matter which directory they are launched from (e.g. Windows Task Scheduler).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


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


class AppConfig(BaseModel):
    country: str = "co"
    base_url: str = "https://www.rappi.com.co"
    database_path: str = "data/rappi_prices.duckdb"
    # Colombia is UTC-5 all year (no DST). Snapshot dates/weeks use local time.
    utc_offset_hours: int = -5
    zones: List[ZoneConfig] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)
    scraper: ScraperSettings = Field(default_factory=ScraperSettings)

    @property
    def database_file(self) -> Path:
        return resolve_path(self.database_path)

    @property
    def cookie_domain(self) -> str:
        host = urllib.parse.urlparse(self.base_url).hostname or "www.rappi.com.co"
        return "." + host.removeprefix("www.")

    def local_now(self) -> datetime:
        return datetime.now(timezone(timedelta(hours=self.utc_offset_hours)))


def load_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    p = Path(config_path)
    if not p.is_absolute() and not p.exists():
        p = resolve_path(p)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    config = AppConfig(**data)
    if not config.zones:
        raise ValueError(f"No zones configured in {p}")
    if not config.search_queries:
        raise ValueError(f"No search_queries configured in {p}")
    return config
