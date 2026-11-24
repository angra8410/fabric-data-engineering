"""
Hourly visibility probe for the client store (ADR-013).

Every run records, for the client's zone: whether her store page opens, and for a
few searches where Rappi ranks her store (Rappi lists ~5 stores per search). Rows
go to a separate DuckDB file so the probe never locks or touches the weekly price
database. The client report summarises it by hour of day ("Visibilidad por hora").
"""
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb

from src.config import ClientConfig, resolve_path

PROBE_DB = "data/visibility_probe.duckdb"
STORE_PAGE_CHECK = "[pagina tienda]"

CREATE_PROBE_SQL = """
CREATE TABLE IF NOT EXISTS visibility_probe (
    probed_at           TIMESTAMP NOT NULL,   -- local (Colombia) time of the run
    probe_date          DATE NOT NULL,
    probe_hour          INTEGER NOT NULL,
    zone_id             VARCHAR NOT NULL,
    check_name          VARCHAR NOT NULL,     -- search text, or '[pagina tienda]'
    ok                  BOOLEAN NOT NULL,     -- page loaded with products
    n_stores            INTEGER,              -- stores Rappi listed for the search
    her_rank            INTEGER,              -- NULL = not listed
    her_eta             VARCHAR,
    her_fee             VARCHAR,
    store_page_products INTEGER,
    top_stores          VARCHAR,
    PRIMARY KEY (probed_at, zone_id, check_name)
);
"""
COLUMNS = ["probed_at", "probe_date", "probe_hour", "zone_id", "check_name", "ok", "n_stores", "her_rank",
           "her_eta", "her_fee", "store_page_products", "top_stores"]

# Every store Rappi lists in a probed search, with its own open/closed signal, so the hours
# when fewer competitors are open can be found (separate table: no migration of the one above).
CREATE_STORES_SQL = """
CREATE TABLE IF NOT EXISTS visibility_probe_stores (
    probed_at   TIMESTAMP NOT NULL,
    zone_id     VARCHAR NOT NULL,
    check_name  VARCHAR NOT NULL,
    rank        INTEGER NOT NULL,
    store_id    VARCHAR,
    store_name  VARCHAR,
    eta_text    VARCHAR,
    fee_text    VARCHAR,
    is_open     BOOLEAN,              -- NULL = no delivery-time text to tell
    PRIMARY KEY (probed_at, zone_id, check_name, rank)
);
"""
STORE_COLUMNS = ["probed_at", "zone_id", "check_name", "rank", "store_id", "store_name", "eta_text", "fee_text",
                 "is_open"]


def is_open(eta: Optional[str]) -> Optional[bool]:
    """Rappi shows '25 min' style times for open stores and an opening time ('Mañana 10:00 am') otherwise."""
    if not eta:
        return None
    return "min" in eta.lower()


def probe_db_path() -> Path:
    return resolve_path(PROBE_DB)


def save(rows: List[Dict[str, Any]], path: Optional[Path] = None) -> int:
    path = path or probe_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(path)) as con:
        con.execute(CREATE_PROBE_SQL)
        con.execute(CREATE_STORES_SQL)
        if rows:
            con.executemany(
                f"INSERT OR REPLACE INTO visibility_probe ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
                [tuple(r.get(c) for c in COLUMNS) for r in rows])
        listed = [s for r in rows for s in r.get("_stores", [])]
        if listed:
            con.executemany(
                f"INSERT OR REPLACE INTO visibility_probe_stores ({', '.join(STORE_COLUMNS)}) "
                f"VALUES ({', '.join('?' * len(STORE_COLUMNS))})",
                [tuple(s.get(c) for c in STORE_COLUMNS) for s in listed])
    return len(rows)


def load(zone_id: str, path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """All probe rows of a zone; [] when the probe never ran (or its file is busy)."""
    path = path or probe_db_path()
    if not path.exists():
        return []
    try:
        with duckdb.connect(str(path), read_only=True) as con:
            cur = con.execute(f"SELECT {', '.join(COLUMNS)} FROM visibility_probe WHERE zone_id = ? ORDER BY probed_at",
                              [zone_id])
            return [dict(zip(COLUMNS, r)) for r in cur.fetchall()]
    except duckdb.Error as e:
        print(f"  visibility probe data not available: {e.__class__.__name__}")
        return []


# --------------------------------------------------------------------------- rows
def stamp(now: datetime, zone_id: str) -> Dict[str, Any]:
    return {"probed_at": now.replace(second=0, microsecond=0), "probe_date": now.date(), "probe_hour": now.hour,
            "zone_id": zone_id}


def search_row(base: Dict[str, Any], query: str, stores: List[Dict[str, Any]], store_id: str,
               header_parser) -> Dict[str, Any]:
    """One search result page -> probe row (stores as returned by scraper.STORES_JS)."""
    her = next((s for s in stores if str(s["store_id"]) == str(store_id)), None)
    info = header_parser(her["header"]) if her else {}
    listed = []
    for s in stores:
        h = header_parser(s["header"])
        listed.append({"probed_at": base["probed_at"], "zone_id": base["zone_id"], "check_name": query,
                       "rank": s["rank"], "store_id": str(s["store_id"]), "store_name": s["name"],
                       "eta_text": h.get("eta_text"), "fee_text": h.get("fee_text"),
                       "is_open": is_open(h.get("eta_text"))})
    return {**base, "check_name": query, "ok": bool(stores), "n_stores": len(stores),
            "her_rank": her["rank"] if her else None, "her_eta": info.get("eta_text"), "her_fee": info.get("fee_text"),
            "top_stores": "  |  ".join(f"{s['rank']}. {s['name']}" for s in stores), "_stores": listed}


def load_stores(zone_id: str, path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Stores listed per probed search ([] before the first run that recorded them)."""
    path = path or probe_db_path()
    if not path.exists():
        return []
    try:
        with duckdb.connect(str(path), read_only=True) as con:
            if not con.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'visibility_probe_stores'"
                               ).fetchall():
                return []
            cur = con.execute(f"SELECT {', '.join(STORE_COLUMNS)} FROM visibility_probe_stores WHERE zone_id = ? "
                              "ORDER BY probed_at, check_name, rank", [zone_id])
            return [dict(zip(STORE_COLUMNS, r)) for r in cur.fetchall()]
    except duckdb.Error as e:
        print(f"  visibility probe store data not available: {e.__class__.__name__}")
        return []


def store_page_row(base: Dict[str, Any], products: int, final_url: str) -> Dict[str, Any]:
    return {**base, "check_name": STORE_PAGE_CHECK, "ok": products > 0, "store_page_products": products,
            "top_stores": None if products else f"redirige a {final_url}"}


# --------------------------------------------------------------------------- opening hours
def declared_open(client: ClientConfig, when: datetime) -> Optional[bool]:
    """Is the store open at `when` by its declared hours? None when hours are not configured."""
    holiday = when.date() in set(client.holidays)
    key = "weekend" if (when.weekday() >= 5 or holiday) else "weekday"
    span = client.opening_hours.get(key)
    if not span:
        return None
    start, end = (int(x) for x in span.split("-"))
    return start <= when.hour < end


DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


@dataclass
class HourRun:
    probed_at: datetime
    store_page_ok: Optional[bool]
    store_page_products: Optional[int]
    searches: int
    appeared: int
    best_rank: Optional[int]
    where: str
    rappi_status: Optional[str] = None   # her delivery-time text: "29 min o prog." = open, "Hoy, 4 PM" = opens at 4


def rappi_status(eta: Optional[str]) -> Optional[str]:
    """Rappi's own open/closed signal from the delivery-time text next to her store."""
    if not eta:
        return None
    if "min" in eta.lower():
        return f"Abierta ({eta})"
    return f"Cerrada, abre {eta}"


def runs(rows: List[Dict[str, Any]]) -> List[HourRun]:
    """Probe rows grouped per run (one run per hour)."""
    by_run: Dict[datetime, List[Dict[str, Any]]] = {}
    for r in rows:
        by_run.setdefault(r["probed_at"], []).append(r)
    out = []
    for at, rs in sorted(by_run.items()):
        page = next((r for r in rs if r["check_name"] == STORE_PAGE_CHECK), None)
        searches = [r for r in rs if r["check_name"] != STORE_PAGE_CHECK and r["ok"]]
        hits = [r for r in searches if r["her_rank"]]
        out.append(HourRun(
            probed_at=at, store_page_ok=page["ok"] if page else None,
            store_page_products=page["store_page_products"] if page else None,
            searches=len(searches), appeared=len(hits),
            best_rank=min((r["her_rank"] for r in hits), default=None),
            where=", ".join(f"{r['check_name']} (#{r['her_rank']})" for r in hits),
            rappi_status=rappi_status(next((r["her_eta"] for r in hits if r.get("her_eta")), None))))
    return out


def by_hour(client: ClientConfig, rows: List[Dict[str, Any]]) -> List[list]:
    """[day type, hour, runs, store page opened %, searches where she appears (avg), best rank]."""
    groups: Dict[tuple, List[HourRun]] = {}
    for run in runs(rows):
        holiday = run.probed_at.date() in set(client.holidays)
        kind = "Fin de semana / festivo" if (run.probed_at.weekday() >= 5 or holiday) else "Lunes a viernes"
        groups.setdefault((kind, run.probed_at.hour), []).append(run)
    out = []
    for (kind, hour), rs in sorted(groups.items()):
        pages = [r.store_page_ok for r in rs if r.store_page_ok is not None]
        out.append([kind, f"{hour:02d}:00", len(rs), (sum(pages) / len(pages)) if pages else None,
                    sum(r.appeared for r in rs) / len(rs), sum(r.searches for r in rs) / len(rs),
                    min((r.best_rank for r in rs if r.best_rank), default=None)])
    return out


def summary_line(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "no checks recorded"
    run = runs(rows)[-1]
    page = {True: f"store page opens ({run.store_page_products} products)", False: "store page does NOT open",
            None: "store page not checked"}[run.store_page_ok]
    return (f"{run.probed_at:%Y-%m-%d %H:%M}: {page}; listed in {run.appeared}/{run.searches} searches"
            + (f" ({run.where})" if run.where else "")
            + (f"; Rappi status: {run.rappi_status}" if run.rappi_status else ""))
