# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "datos_abiertos_lh_dev"
# META     }
# META   }
# META }

# CELL ********************

# ==============================================================================
# 🇨🇴 DATOS ABIERTOS COLOMBIA (datos.gov.co) - INGESTA BRONZE SECOP II
# Spec-Driven Development: RF-01 al RF-05 (spec.md / decisions.md)
# ==============================================================================
import json
import logging
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pyspark.sql import functions as F
from pyspark.sql.types import *

print("🚀 Iniciando Notebook de Ingesta Bronze: Datos Abiertos Colombia (SECOP II)...")

# CELL ********************

# PARAMETERS CELL
# Parámetros configurables para ejecución manual o agendada en Data Pipeline
DATASET_ID = "jbjy-vk9h"               # SECOP II - Contratos Electrónicos
TARGET_TABLE = "bronze_secop_contratos" # Tabla Delta en datos_abiertos_lh_dev
BATCH_SIZE = 10000                     # Tamaño de lote por petición
MAX_RECORDS = None                     # None para carga completa o entero para muestreo
WATERMARK_COLUMN = "fecha_de_firma"    # Columna para filtrado incremental
RATE_LIMIT_DELAY_SEC = 0.5             # Pausa entre llamadas para proteger la API de caídas
MAX_RETRIES = 5                        # Reintentos con Exponential Backoff

# CELL ********************

# ==============================================================================
# 🛡️ MOTOR DE EXTRACCIÓN SODA CON RESILIENCIA Y EXPONENTIAL BACKOFF
# ==============================================================================
class FabricSodaExtractor:
    """Cliente SODA integrado para notebooks de Microsoft Fabric."""
    
    BASE_URL = "https://www.datos.gov.co/resource"
    
    def __init__(self, dataset_id, app_token=None, delay=0.5, retries=5):
        self.dataset_id = dataset_id
        self.app_token = app_token
        self.delay = delay
        self.retries = retries
        
    def execute_request(self, params):
        url = f"{self.BASE_URL}/{self.dataset_id}.json"
        clean_params = {k: v for k, v in params.items() if v is not None}
        if clean_params:
            url += f"?{urllib.parse.urlencode(clean_params)}"
            
        headers = {"Accept": "application/json", "User-Agent": "FabricDataEngineering/1.0"}
        if self.app_token:
            headers["X-App-Token"] = self.app_token
            
        attempt = 0
        while attempt <= self.retries:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=90) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                attempt += 1
                status = e.code
                if status in (429, 500, 502, 503, 504) and attempt <= self.retries:
                    wait = max(2.0 ** attempt, 5.0 if status == 429 else 2.0)
                    print(f"⚠️ HTTP {status}. Esperando {wait:.1f}s antes del reintento {attempt}/{self.retries}...")
                    time.sleep(wait)
                else:
                    raise
            except Exception as e:
                attempt += 1
                if attempt <= self.retries:
                    wait = 2.0 ** attempt
                    print(f"⚠️ Error de red ({e}). Reintentando en {wait:.1f}s...")
                    time.sleep(wait)
                else:
                    raise

    def get_count(self, where_clause=None):
        res = self.execute_request({"$select": "count(*)", "$where": where_clause})
        if res and isinstance(res, list) and "count" in res[0]:
            return int(res[0]["count"])
        return 0

# CELL ********************

# ==============================================================================
# 🔍 1. DETERMINACIÓN DEL WATERMARK INCREMENTAL
# ==============================================================================
extractor = FabricSodaExtractor(DATASET_ID, delay=RATE_LIMIT_DELAY_SEC, retries=MAX_RETRIES)

watermark_filter = None
is_incremental = False

try:
    # Verificar si la tabla existe en el Lakehouse para obtener el último registro
    existing_df = spark.table(TARGET_TABLE)
    max_val_row = existing_df.select(F.max(F.col(WATERMARK_COLUMN))).collect()
    max_watermark = max_val_row[0][0] if max_val_row and max_val_row[0][0] else None
    
    if max_watermark:
        watermark_filter = f"{WATERMARK_COLUMN} > '{max_watermark}'"
        is_incremental = True
        print(f"📌 Sincronización Incremental activada. Último watermark ({WATERMARK_COLUMN}): {max_watermark}")
    else:
        print("📌 Tabla vacía. Se realizará carga inicial.")
except Exception:
    print(f"📌 La tabla [{TARGET_TABLE}] no existe aún. Iniciando primera creación.")

# Consultar total de registros en alcance
total_available = extractor.get_count(where_clause=watermark_filter)
print(f"📊 Registros identificados en datos.gov.co para extracción: {total_available:,}")

# CELL ********************

# ==============================================================================
# 📥 2. EXTRACCIÓN POR LOTES Y PERSISTENCIA EN DELTA LAKE
# ==============================================================================
if total_available == 0:
    print("✅ No hay registros nuevos por sincronizar. Proceso completado.")
else:
    offset = 0
    batch_num = 1
    run_timestamp = datetime.now(timezone.utc).isoformat()
    total_written = 0
    
    while True:
        limit = BATCH_SIZE
        if MAX_RECORDS is not None:
            remaining = MAX_RECORDS - total_written
            if remaining <= 0:
                break
            limit = min(limit, remaining)
            
        print(f"📦 Extrayendo Lote #{batch_num}: offset={offset:,}, limit={limit:,}...")
        
        batch_data = extractor.execute_request({
            "$limit": limit,
            "$offset": offset,
            "$where": watermark_filter,
            "$order": ":id"
        })
        
        if not batch_data:
            print("🏁 Fin de los datos retornados por el endpoint.")
            break
            
        # Convertir a Spark DataFrame
        batch_rdd = spark.sparkContext.parallelize([json.dumps(row) for row in batch_data])
        batch_df = spark.read.json(batch_rdd)
        
        # Enriquecer con metadatos de auditoría y linaje
        enriched_df = (
            batch_df
            .withColumn("_ingestion_timestamp", F.current_timestamp())
            .withColumn("_source_dataset_id", F.lit(DATASET_ID))
            .withColumn("_batch_id", F.lit(f"batch_{batch_num}_{int(time.time())}"))
        )
        
        # Guardar en la tabla Delta del Lakehouse
        (
            enriched_df.write
            .format("delta")
            .mode("append")
            .saveAsTable(TARGET_TABLE)
        )
        
        total_written += len(batch_data)
        offset += len(batch_data)
        batch_num += 1
        
        print(f"  💾 Guardados {len(batch_data):,} registros en '{TARGET_TABLE}'. Progreso acumulado: {total_written:,}/{total_available:,}")
        
        if len(batch_data) < limit:
            break
            
        # Pausa para prevención de saturación del API
        if RATE_LIMIT_DELAY_SEC > 0:
            time.sleep(RATE_LIMIT_DELAY_SEC)

    print(f"\n🎉 Ingesta Bronze completada con éxito. Total registros persistidos: {total_written:,}")
