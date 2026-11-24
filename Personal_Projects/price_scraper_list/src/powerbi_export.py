"""
Parquet tables for the client's local Power BI dashboard (ADR-015).

Same figures as the Excel client report, one Parquet file per table, overwritten on
every `client-report` run so a Refresh in Power BI Desktop shows the latest run.
Files live under the git-ignored client folder (client.powerbi_dir). No customer data.
"""
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import duckdb

from src.config import AppConfig

# Action -> (sort order, hex color). Okabe-Ito colors, same as the report spec.
ACTION_STYLE = {
    "Bajar precio": (1, "#0072B2"),
    "Subir precio": (2, "#009E73"),
    "Desactivar": (3, "#D55E00"),
    "Vincular": (4, "#CC79A7"),
    "No aparece en Rappi": (5, "#CC79A7"),
    "Revisar vínculo": (6, "#CC79A7"),
    "Revisar inventario": (7, "#767676"),
    "No competir": (8, "#767676"),
    "Mantener": (9, "#767676"),
    "Sin competidor": (10, "#767676"),
}
OTHER_STYLE = (11, "#767676")

Column = Tuple[str, str]   # (name, DuckDB type)

ACCIONES: List[Column] = [
    ("Fecha reporte", "DATE"), ("Acción", "VARCHAR"), ("Orden acción", "INTEGER"), ("Color acción", "VARCHAR"),
    ("Producto", "VARCHAR"), ("Publicación en Rappi", "VARCHAR"), ("Stock", "DOUBLE"), ("Costo", "DOUBLE"),
    ("Comisión", "DOUBLE"), ("Precio Rappi actual", "DOUBLE"), ("Utilidad actual", "DOUBLE"),
    ("Margen actual", "DOUBLE"), ("Competidor más barato", "VARCHAR"), ("Precio competidor", "DOUBLE"),
    ("Producto del competidor", "VARCHAR"), ("Precio sugerido", "DOUBLE"), ("Utilidad sugerida", "DOUBLE"),
    ("Margen sugerido", "DOUBLE"), ("Precio WhatsApp", "DOUBLE"), ("Nota", "VARCHAR"),
]
PRODUCTOS: List[Column] = [
    ("Fecha reporte", "DATE"), ("Producto", "VARCHAR"), ("Categoría", "VARCHAR"), ("Stock", "DOUBLE"),
    ("Vendidas recientes", "DOUBLE"), ("Costo", "DOUBLE"), ("Precio WhatsApp", "DOUBLE"), ("Comisión", "DOUBLE"),
    ("Publicado en Rappi", "VARCHAR"), ("Precio Rappi actual", "DOUBLE"), ("Margen actual", "DOUBLE"),
    ("Competidor más barato", "VARCHAR"), ("Precio competidor", "DOUBLE"), ("Producto del competidor", "VARCHAR"),
    ("Competidor confiable", "VARCHAR"), ("Coincidencia", "DOUBLE"), ("Tiendas con el producto", "INTEGER"),
    ("Precio sugerido", "DOUBLE"), ("Utilidad con el sugerido", "DOUBLE"), ("Margen sugerido", "DOUBLE"),
    ("Brecha vs competidor", "DOUBLE"), ("Acción", "VARCHAR"), ("Notas", "VARCHAR"),
]
VIS_HORA: List[Column] = [
    ("Probado en", "TIMESTAMP"), ("Fecha", "DATE"), ("Día", "VARCHAR"), ("Hora", "VARCHAR"), ("Hora num", "INTEGER"),
    ("Tipo de día", "VARCHAR"), ("Según su horario", "VARCHAR"), ("Según Rappi", "VARCHAR"),
    ("Página abre", "INTEGER"), ("Productos en página", "INTEGER"), ("Búsquedas medidas", "INTEGER"),
    ("Aparece en", "INTEGER"), ("Mejor posición", "INTEGER"), ("Dónde aparece", "VARCHAR"),
]
VIS_BUSQUEDA: List[Column] = [
    ("Probado en", "TIMESTAMP"), ("Búsqueda", "VARCHAR"), ("Aparece", "INTEGER"), ("Posición", "INTEGER"),
    ("Tiendas listadas", "INTEGER"),
]
VIS_SEMANAL: List[Column] = [
    ("Fecha", "DATE"), ("Tipo de búsqueda", "VARCHAR"), ("Búsquedas medidas", "INTEGER"), ("Aparece en", "INTEGER"), ("Posición promedio", "DOUBLE"),
]
COMPETENCIA: List[Column] = [
    ("Probado en", "TIMESTAMP"), ("Búsqueda", "VARCHAR"), ("Posición", "INTEGER"), ("Tienda", "VARCHAR"),
    ("Es su tienda", "VARCHAR"), ("Estado", "VARCHAR"), ("Tiempo de entrega", "VARCHAR"), ("Envío", "VARCHAR"),
]
REPORTE: List[Column] = [
    ("Fecha reporte", "DATE"), ("Tienda", "VARCHAR"), ("Visibilidad hasta", "TIMESTAMP"), ("Generado", "TIMESTAMP"),
]


def _write(con, out_dir: Path, name: str, columns: Sequence[Column], rows: List[Sequence[Any]]) -> int:
    cols = ", ".join(f'"{c}" {t}' for c, t in columns)
    con.execute(f'CREATE OR REPLACE TABLE "{name}" ({cols})')
    if rows:
        con.executemany(f'INSERT INTO "{name}" VALUES ({", ".join("?" * len(columns))})', [tuple(r) for r in rows])
    final = out_dir / f"{name}.parquet"
    tmp = out_dir / f".{name}.parquet.tmp"
    con.execute(f"COPY \"{name}\" TO '{tmp.as_posix()}' (FORMAT PARQUET)")
    tmp.replace(final)   # never leave a half-written file for Power BI
    return len(rows)


def action_rows(checks, today: date) -> List[list]:
    rows = []
    for a in checks:
        price = a.listing.price if a.listing else None
        comp = a.competitor
        order, color = ACTION_STYLE.get(a.action, OTHER_STYLE)
        rows.append([
            today, a.action, order, color,
            a.item.name if a.item else (a.listing.product_name if a.listing else a.barcode),
            a.listing.product_name if a.listing else None,
            a.item.stock if a.item else None, a.cost, a.commission or None,
            price, a.profit(price), a.margin(price),
            comp.store_name if comp else None, comp.price if comp else None, comp.product_name if comp else None,
            a.suggested, a.profit(a.suggested) if a.suggested else None,
            a.margin(a.suggested) if a.suggested else None,
            a.whatsapp, "; ".join(a.notes) or None,
        ])
    return rows


def product_rows(suggestions, today: date) -> List[list]:
    rows = []
    for s in suggestions:
        comp = s.competitor
        trusted = comp is not None and not s.competitor_suspect
        rows.append([
            today, s.item.name, s.item.category, s.item.stock, s.item.sold_recent, s.item.cost, s.item.store_price,
            s.commission, "Sí" if s.rappi_price else "No", s.rappi_price, s.margin(s.rappi_price),
            comp.store_name if comp else None, comp.price if comp else None, comp.product_name if comp else None,
            ("Sí" if trusted else "No") if comp else None, s.competitor_score, s.competitors_found or None,
            s.suggested, s.profit(s.suggested), s.margin(s.suggested),
            (s.rappi_price / comp.price - 1) if (trusted and s.rappi_price) else None,
            s.action.split(":")[0], "; ".join(s.notes) or None,
        ])
    return rows


def probe_tables(client, probe_rows: List[Dict[str, Any]]) -> Tuple[List[list], List[list]]:
    from src import probe
    hours, searches = [], []
    for run in probe.runs(probe_rows):
        at = run.probed_at
        holiday = at.date() in set(client.holidays)
        kind = "Fin de semana / festivo" if (at.weekday() >= 5 or holiday) else "Lunes a viernes"
        open_ = probe.declared_open(client, at)
        hours.append([
            at, at.date(), probe.DAY_NAMES[at.weekday()], f"{at.hour:02d}:00", at.hour, kind,
            {True: "Abierta", False: "Cerrada", None: "-"}[open_], run.rappi_status or "-",
            None if run.store_page_ok is None else int(run.store_page_ok), run.store_page_products,
            run.searches, run.appeared, run.best_rank, run.where or None,
        ])
    for r in probe_rows:
        if r["check_name"] == probe.STORE_PAGE_CHECK or not r["ok"]:
            continue
        searches.append([r["probed_at"], r["check_name"], int(bool(r["her_rank"])), r["her_rank"], r["n_stores"]])
    return hours, searches


def competitor_rows(client, store_rows: List[Dict[str, Any]]) -> List[list]:
    """Every store Rappi listed in a probed search and whether Rappi showed it open (ADR-016)."""
    state = {True: "Abierta", False: "Cerrada", None: "-"}
    return [[s["probed_at"], s["check_name"], s["rank"], s["store_name"],
             "Sí" if str(s["store_id"]) == str(client.store_id) else "No", state[s["is_open"]],
             s["eta_text"], s["fee_text"]] for s in store_rows]


def write_tables(config: AppConfig, suggestions, vis: Dict[str, list], today: date, checks=None,
                 probe_rows: Optional[List[Dict[str, Any]]] = None, out_dir: Optional[Path] = None,
                 store_rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, int]:
    """Write the dashboard tables; returns {table: rows}."""
    client = config.client
    out_dir = out_dir or client.powerbi_path
    out_dir.mkdir(parents=True, exist_ok=True)
    probe_rows = probe_rows or []
    hours, searches = probe_tables(client, probe_rows)
    last_probe = max((r["probed_at"] for r in probe_rows), default=None)
    counts = {}
    with duckdb.connect(":memory:") as con:
        counts["acciones"] = _write(con, out_dir, "acciones", ACCIONES, action_rows(checks or [], today))
        counts["productos"] = _write(con, out_dir, "productos", PRODUCTOS, product_rows(suggestions, today))
        counts["visibilidad_hora"] = _write(con, out_dir, "visibilidad_hora", VIS_HORA, hours)
        counts["visibilidad_busqueda"] = _write(con, out_dir, "visibilidad_busqueda", VIS_BUSQUEDA, searches)
        weekly = vis.get("history_by_type")
        if weekly is None:   # no split available: one series
            weekly = [(h[0], "Todas", *h[1:]) for h in vis.get("history", [])]
        counts["visibilidad_semanal"] = _write(con, out_dir, "visibilidad_semanal", VIS_SEMANAL,
                                               [list(h) for h in weekly])
        counts["competencia_hora"] = _write(con, out_dir, "competencia_hora", COMPETENCIA,
                                            competitor_rows(client, store_rows or []))
        counts["reporte"] = _write(con, out_dir, "reporte", REPORTE,
                                   [[today, client.name, last_probe, datetime.now().replace(microsecond=0)]])
    return counts
