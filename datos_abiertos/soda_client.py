"""
SocrataClient: Cliente modular y resiliente para la API SODA de Socrata (datos.gov.co).
Diseñado para la extracción masiva de datos en Microsoft Fabric / Python.
Soporta:
- Paginación automática por lotes ($limit, $offset)
- Manejo de rate limiting con pausas (throttling)
- Reintentos exponenciales (Exponential Backoff) ante HTTP 429 y 5xx
- Consultas SoQL ($select, $where, $order)
- Extracción incremental mediante marca de agua (watermark)
"""

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Generator, List, Optional

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SocrataClient")


class SocrataClient:
    """
    Cliente para consumir endpoints SODA en datos.gov.co con protección anticaídas.
    """

    DEFAULT_DOMAIN = "www.datos.gov.co"

    def __init__(
        self,
        domain: str = DEFAULT_DOMAIN,
        app_token: Optional[str] = None,
        timeout: int = 60,
        rate_limit_delay_sec: float = 0.5,
        max_retries: int = 5,
        backoff_factor: float = 2.0,
    ):
        """
        :param domain: Dominio de la instancia Socrata (ej. www.datos.gov.co).
        :param app_token: Socrata App Token (X-App-Token) para cuota ampliada.
        :param timeout: Tiempo máximo de espera por petición en segundos.
        :param rate_limit_delay_sec: Pausa entre peticiones sucesivas para evitar saturación.
        :param max_retries: Número de reintentos ante errores transitorios (429, 500, 502, 503, 504).
        :param backoff_factor: Multiplicador para espera exponencial.
        """
        self.domain = domain.rstrip("/")
        self.app_token = app_token or os.getenv("SOCRATA_APP_TOKEN")
        self.timeout = timeout
        self.rate_limit_delay_sec = rate_limit_delay_sec
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _build_url(self, endpoint_path: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Construye la URL completa con parámetros codificados."""
        url = f"https://{self.domain}/{endpoint_path.lstrip('/')}"
        if params:
            # Filtrar valores None
            clean_params = {k: v for k, v in params.items() if v is not None}
            query_string = urllib.parse.urlencode(clean_params)
            if query_string:
                url = f"{url}?{query_string}"
        return url

    def _execute_request(self, url: str) -> Any:
        """
        Ejecuta una petición HTTP GET con reintentos y retroceso exponencial ante 429 y 5xx.
        """
        headers = {
            "Accept": "application/json",
            "User-Agent": "FabricDataEngineering/1.0 (DatosAbiertosColombia; Python 3)",
        }
        if self.app_token:
            headers["X-App-Token"] = self.app_token

        req = urllib.request.Request(url, headers=headers)
        attempt = 0

        while attempt <= self.max_retries:
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    status_code = resp.getcode()
                    content = resp.read().decode("utf-8")
                    return json.loads(content)

            except urllib.error.HTTPError as e:
                attempt += 1
                status = e.code
                err_body = e.read().decode("utf-8", errors="ignore")

                # HTTP 429 (Rate Limit) o 5xx (Errores temporales de servidor)
                if status in (429, 500, 502, 503, 504):
                    if attempt > self.max_retries:
                        logger.error(f"❌ Agotados {self.max_retries} reintentos. HTTP {status}: {err_body}")
                        raise

                    # Calcular tiempo de espera exponencial
                    wait_time = self.backoff_factor ** attempt
                    if status == 429:
                        wait_time = max(wait_time, 5.0)  # Pausa mínima de 5s ante 429
                        logger.warning(f"⚠️ HTTP 429 (Rate limit alcanzado). Esperando {wait_time:.1f}s antes de reintentar...")
                    else:
                        logger.warning(f"⚠️ HTTP {status} del servidor. Esperando {wait_time:.1f}s antes de reintentar...")

                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Error HTTP {status} irreversible: {err_body}")
                    raise

            except (urllib.error.URLError, TimeoutError) as e:
                attempt += 1
                if attempt > self.max_retries:
                    logger.error(f"❌ Fallo de red/timeout tras {self.max_retries} reintentos: {e}")
                    raise
                wait_time = self.backoff_factor ** attempt
                logger.warning(f"⚠️ Fallo de conexión ({e}). Reintentando en {wait_time:.1f}s...")
                time.sleep(wait_time)

    def get_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """
        Obtiene los metadatos y esquema oficial del dataset desde la API de vistas de Socrata.
        """
        url = self._build_url(f"api/views/{dataset_id}.json")
        logger.info(f"Consultando metadatos para el dataset [{dataset_id}]...")
        return self._execute_request(url)

    def get_row_count(self, dataset_id: str, where: Optional[str] = None) -> int:
        """
        Calcula el total de registros disponibles en el dataset aplicando un filtro opcional SoQL.
        """
        params = {"$select": "count(*)"}
        if where:
            params["$where"] = where

        url = self._build_url(f"resource/{dataset_id}.json", params)
        data = self._execute_request(url)
        if isinstance(data, list) and len(data) > 0 and "count" in data[0]:
            return int(data[0]["count"])
        return 0

    def fetch_page(
        self,
        dataset_id: str,
        limit: int = 10000,
        offset: int = 0,
        where: Optional[str] = None,
        select: Optional[str] = None,
        order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Descarga una única página de registros con parámetros SoQL.
        """
        params = {
            "$limit": limit,
            "$offset": offset,
            "$where": where,
            "$select": select,
            "$order": order,
        }
        url = self._build_url(f"resource/{dataset_id}.json", params)
        return self._execute_request(url)

    def fetch_all_generator(
        self,
        dataset_id: str,
        batch_size: int = 10000,
        max_records: Optional[int] = None,
        where: Optional[str] = None,
        select: Optional[str] = None,
        order: str = ":id",
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Generador que itera descargando lotes completos del dataset protegiendo el API con pausas.
        
        :param dataset_id: Código 4x4 del dataset (ej. 'jbjy-vk9h').
        :param batch_size: Cantidad de registros por lote (máx 50,000 según Socrata; recomendado 10,000).
        :param max_records: Límite máximo total a descargar (None para descargar todo).
        :param where: Cláusula de filtrado SoQL (ej. "fecha_de_firma > '2026-01-01'").
        :param select: Columnas a extraer (None para todas).
        :param order: Ordenamiento SoQL (por defecto ':id' para paginación determinista).
        :return: Generador de listas de diccionarios (un lote por yield).
        """
        offset = 0
        total_fetched = 0

        logger.info(f"Iniciando extracción por lotes para [{dataset_id}] con lote de {batch_size:,} filas...")

        while True:
            current_limit = batch_size
            if max_records is not None:
                remaining = max_records - total_fetched
                if remaining <= 0:
                    break
                if remaining < batch_size:
                    current_limit = remaining

            logger.info(f"Descargando lote: offset={offset:,}, limit={current_limit:,}...")
            batch = self.fetch_page(
                dataset_id=dataset_id,
                limit=current_limit,
                offset=offset,
                where=where,
                select=select,
                order=order,
            )

            if not batch:
                logger.info("Fin de los registros disponibles en el endpoint.")
                break

            total_fetched += len(batch)
            offset += len(batch)
            yield batch

            if len(batch) < current_limit:
                # El lote trajo menos de lo solicitado, se llegó al final
                break

            # Throttling preventivo entre lotes
            if self.rate_limit_delay_sec > 0:
                time.sleep(self.rate_limit_delay_sec)

        logger.info(f"Extracción finalizada. Total registros obtenidos: {total_fetched:,}")


# CLI para pruebas rápidas
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cliente SODA Datos Abiertos Colombia")
    parser.add_argument("--dataset", default="jbjy-vk9h", help="ID de 4x4 del dataset (default: jbjy-vk9h SECOP II)")
    parser.add_argument("--count", action="store_true", help="Obtener conteo total")
    parser.add_argument("--sample", type=int, default=5, help="Descargar muestra de N registros")
    args = parser.parse_args()

    client = SocrataClient()
    print(f"\n🔍 Conectando a datos.gov.co con dataset: {args.dataset}")

    if args.count:
        total = client.get_row_count(args.dataset)
        print(f"📊 Total de registros en el dataset [{args.dataset}]: {total:,}")

    if args.sample > 0:
        sample = client.fetch_page(args.dataset, limit=args.sample)
        print(f"\n📋 Muestra de {len(sample)} registros obtenidos exitosamente:")
        for idx, row in enumerate(sample, 1):
            print(f"--- Fila {idx} ---")
            for k in list(row.keys())[:5]:
                print(f"  {k}: {row[k]}")
