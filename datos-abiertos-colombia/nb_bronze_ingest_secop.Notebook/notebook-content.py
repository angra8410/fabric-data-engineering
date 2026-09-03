# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "f95e26b3-c404-4e86-be37-c64906ebe3f9",
# META       "default_lakehouse_name": "datos_abiertos_lh_dev",
# META       "default_lakehouse_workspace_id": "2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e",
# META       "known_lakehouses": [
# META         {
# META           "id": "f95e26b3-c404-4e86-be37-c64906ebe3f9"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # 🇨🇴 Datos Abiertos Colombia - Ingesta Bronze SECOP II
# ### Medallion Architecture: SODA API -> Fabric Lakehouse (`datos_abiertos_lh_dev`)
# Este notebook implementa el desarrollo guiado por especificaciones (**Spec-Driven Development**) definido en `spec.md` y `decisions.md`:
# - **Fuente:** Portal oficial de Datos Abiertos Colombia (`datos.gov.co`) - SECOP II Contratos Electrónicos (`jbjy-vk9h`).
# - **Estrategia Anticaídas:** Paginación por lotes ($limit, $offset), control de tasa (*throttling*) y reintentos con *Exponential Backoff* ante errores HTTP 429 / 5xx.
# - **Sincronización Incremental:** Seguimiento automático de marca de agua (*watermark*) sobre `fecha_de_firma`.
# - **Destino:** Tabla Delta Lake `bronze_secop_contratos` en `datos_abiertos_lh_dev` con linaje y auditoría.

# PARAMETERS CELL ********************

# =====================================================================
# ⚙️ CELDA DE PARÁMETROS CONFIGURABLES
# =====================================================================
DATASET_ID = 'jbjy-vk9h'               # Identificador 4x4 SODA (SECOP II)
TARGET_TABLE = 'bronze_secop_contratos' # Tabla Delta en datos_abiertos_lh_dev
BATCH_SIZE = 50000                     # Tamaño de lote por llamada (máx 50,000 en Socrata)
MAX_RECORDS = None                     # None para sincronizar todo, o entero (ej. 50000) para pruebas
WATERMARK_COLUMN = 'fecha_de_firma'    # Columna temporal para filtrado incremental
RATE_LIMIT_DELAY_SEC = 0.5             # Pausa preventiva entre llamadas (segundos)
MAX_RETRIES = 5                        # Reintentos máximos con espera exponencial
APP_TOKEN = None                       # Socrata App Token (opcional para mayor cuota)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 🛡️ MOTOR DE EXTRACCIÓN SODA CON RESILIENCIA Y EXPONENTIAL BACKOFF
# =====================================================================
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pyspark.sql import functions as F

class FabricSodaExtractor:
    BASE_URL = 'https://www.datos.gov.co/resource'
    
    def __init__(self, dataset_id, app_token=None, delay=0.5, retries=5):
        self.dataset_id = dataset_id
        self.app_token = app_token
        self.delay = delay
        self.retries = retries
        
    def execute_request(self, params):
        clean_params = {k: v for k, v in params.items() if v is not None}
        url = f'{self.BASE_URL}/{self.dataset_id}.json'
        if clean_params:
            url += f'?{urllib.parse.urlencode(clean_params)}'
            
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'FabricDataEngineering/1.0 (DatosAbiertosColombia; PySpark)'
        }
        if self.app_token:
            headers['X-App-Token'] = self.app_token
            
        attempt = 0
        while attempt <= self.retries:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=90) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                attempt += 1
                status = e.code
                if status in (429, 500, 502, 503, 504) and attempt <= self.retries:
                    wait = max(2.0 ** attempt, 5.0 if status == 429 else 2.0)
                    print(f'⚠️ HTTP {status}. Pausa preventiva de {wait:.1f}s antes de reintentar (intento {attempt}/{self.retries})...')
                    time.sleep(wait)
                else:
                    raise
            except Exception as e:
                attempt += 1
                if attempt <= self.retries:
                    wait = 2.0 ** attempt
                    print(f'⚠️ Error de conexión ({e}). Reintentando en {wait:.1f}s...')
                    time.sleep(wait)
                else:
                    raise
                    
    def get_count(self, where_clause=None):
        res = self.execute_request({'$select': 'count(*)', '$where': where_clause})
        if res and isinstance(res, list) and 'count' in res[0]:
            return int(res[0]['count'])
        return 0

print('✅ Extractor SODA inicializado correctamente.')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 🔍 ANÁLISIS DE WATERMARK Y RECONOCIMIENTO DEL LAKEHOUSE
# =====================================================================
extractor = FabricSodaExtractor(DATASET_ID, app_token=APP_TOKEN, delay=RATE_LIMIT_DELAY_SEC, retries=MAX_RETRIES)

watermark_filter = None
is_incremental = False

try:
    existing_df = spark.table(TARGET_TABLE)
    max_val_row = existing_df.select(F.max(F.col(WATERMARK_COLUMN))).collect()
    max_watermark = max_val_row[0][0] if max_val_row and max_val_row[0][0] else None
    
    if max_watermark:
        watermark_filter = f"{WATERMARK_COLUMN} > '{max_watermark}'"
        is_incremental = True
        print(f'📌 Sincronización Incremental activada. Último watermark ({WATERMARK_COLUMN}): {max_watermark}')
    else:
        print('📌 Tabla vacía. Se realizará carga inicial.')
except Exception:
    print(f'📌 La tabla [{TARGET_TABLE}] no existe aún. Iniciando primera creación.')

total_available = extractor.get_count(where_clause=watermark_filter)
print(f'📊 Registros identificados en datos.gov.co para extracción: {total_available:,}')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 📥 DESCARGA POR LOTES, ENRIQUECIMIENTO Y PERSISTENCIA EN DELTA
# =====================================================================
if total_available == 0:
    print('✅ No hay registros nuevos por sincronizar. Proceso completado.')
else:
    offset = 0
    batch_num = 1
    total_written = 0
    batch_run_id = f'run_{int(time.time())}'
    
    while True:
        limit = BATCH_SIZE
        if MAX_RECORDS is not None:
            remaining = MAX_RECORDS - total_written
            if remaining <= 0:
                break
            limit = min(limit, remaining)
            
        print(f'📦 Descargando lote #{batch_num}: offset={offset:,}, limit={limit:,}...')
        batch_data = extractor.execute_request({
            '$limit': limit,
            '$offset': offset,
            '$where': watermark_filter,
            '$order': ':id'
        })
        
        if not batch_data:
            print('🏁 Fin de los datos retornados por el endpoint.')
            break
            
        # Convertir a Spark DataFrame
        batch_rdd = spark.sparkContext.parallelize([json.dumps(row) for row in batch_data])
        batch_df = spark.read.json(batch_rdd)
        
        # Enriquecer con metadatos de auditoría
        enriched_df = (
            batch_df
            .withColumn('_ingestion_timestamp', F.current_timestamp())
            .withColumn('_source_dataset_id', F.lit(DATASET_ID))
            .withColumn('_batch_id', F.lit(f'{batch_run_id}_{batch_num}'))
        )
        
        # Persistir en tabla Delta del Lakehouse
        enriched_df.write.format('delta').mode('append').saveAsTable(TARGET_TABLE)
        
        total_written += len(batch_data)
        offset += len(batch_data)
        batch_num += 1
        print(f'  💾 Guardados {len(batch_data):,} registros en [{TARGET_TABLE}]. Total acumulado: {total_written:,}/{total_available:,}')
        
        if len(batch_data) < limit:
            break
            
        # Pausa preventiva entre lotes (throttling)
        if RATE_LIMIT_DELAY_SEC > 0:
            time.sleep(RATE_LIMIT_DELAY_SEC)

    print(f'\n🎉 Ingesta Bronze completada. Total registros persistidos: {total_written:,}')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 📊 RESUMEN Y MUESTRA DE DATOS ATERRIZADOS EN LAKEHOUSE
# =====================================================================
result_df = spark.table(TARGET_TABLE)
count_final = result_df.count()
print(f'🏛️ Total de filas en la tabla Delta [{TARGET_TABLE}]: {count_final:,}')

display(result_df.select(
    'nombre_entidad',
    'valor_del_contrato',
    'departamento',
    'ciudad',
    'fecha_de_firma',
    '_ingestion_timestamp'
).limit(10))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ==============================================================================
# 🚀 CIERRE DE BRECHA: DESCARGA DEL FALTANTE HISTÓRICO HASTA EL 100%
# ==============================================================================
import json
import time
from pyspark.sql import functions as F

print("🏁 Iniciando sincronización del faltante histórico...")

# 1. Punto de partida: arrancamos exactamente desde la fila donde está tu tabla
total_actual = spark.table(TARGET_TABLE).count()
total_objetivo = extractor.get_count()
faltantes_reales = total_objetivo - total_actual

print(f"📍 Registros en tabla:   {total_actual:,}")
print(f"🎯 Total en la API:      {total_objetivo:,}")
print(f"📦 Por descargar:        {faltantes_reales:,}")

if faltantes_reales <= 0:
    print("🎉 ¡Tu tabla ya tiene el 100% de los datos!")
else:
    # Parámetros optimizados para volumen masivo
    LOTE_SIZE = 50000  # Máximo por lote permitido por Socrata
    offset = total_actual
    total_descargado_sesion = 0
    batch_num = 1
    run_id = f"gap_fill_{int(time.time())}"

    while offset < total_objetivo:
        limite = min(LOTE_SIZE, total_objetivo - offset)
        print(f"📦 Lote #{batch_num}: offset={offset:,}, límite={limite:,}...")

        # Consulta sin filtro WHERE para capturar tanto históricos como sin fecha_de_firma
        batch_data = extractor.execute_request({
            "$limit": limite,
            "$offset": offset,
            "$order": ":id"
        })

        if not batch_data:
            print("🏁 No hay más registros devueltos por el endpoint.")
            break

        # Convertir a DataFrame Spark y enriquecer
        batch_rdd = spark.sparkContext.parallelize([json.dumps(row) for row in batch_data])
        batch_df = spark.read.json(batch_rdd)

        enriched_df = (
            batch_df
            .withColumn("_ingestion_timestamp", F.current_timestamp())
            .withColumn("_source_dataset_id", F.lit(DATASET_ID))
            .withColumn("_batch_id", F.lit(f"{run_id}_{batch_num}"))
        )

        # Append en la tabla Delta
        enriched_df.write.format("delta").mode("append").saveAsTable(TARGET_TABLE)

        filas_lote = len(batch_data)
        total_descargado_sesion += filas_lote
        offset += filas_lote
        batch_num += 1

        progreso_global = ((total_actual + total_descargado_sesion) / total_objetivo) * 100
        print(f"  💾 Guardados {filas_lote:,} registros. Progreso total: {total_actual + total_descargado_sesion:,}/{total_objetivo:,} ({progreso_global:.2f}%)")

        if filas_lote < limite:
            break

        # Pausa preventiva para no saturar SODA
        time.sleep(RATE_LIMIT_DELAY_SEC)

    print(f"\n🎉 ¡Sincronización de faltantes completada! Registros nuevos agregados: {total_descargado_sesion:,}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 🔍 VERIFICACIÓN DE COBERTURA: API vs LAKEHOUSE
# =====================================================================
# 1. Conteo total oficial en datos.gov.co (sin filtros)
total_api = extractor.get_count()

# 2. Conteo total en tu tabla Delta de Fabric
total_lakehouse = spark.table(TARGET_TABLE).count()

# 3. Métricas de sincronización
cobertura_pct = (total_lakehouse / total_api) * 100
faltantes = total_api - total_lakehouse

print(f"🌐 Total en Socrata API (datos.gov.co): {total_api:,}")
print(f"🏛️ Total en tu Lakehouse Delta:          {total_lakehouse:,}")
print(f"📊 Cobertura actual:                     {cobertura_pct:.2f}%")
print(f"⏳ Registros restantes por sincronizar:  {faltantes:,}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
