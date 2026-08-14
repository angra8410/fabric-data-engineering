# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "85a8b62f-66cf-4fdb-bcfe-3f3563b677d5",
# META       "default_lakehouse_name": "dane_bronze_lh",
# META       "default_lakehouse_workspace_id": "f1ec50d7-8db7-405b-b670-b3a23240da2f",
# META       "known_lakehouses": [
# META         {
# META           "id": "85a8b62f-66cf-4fdb-bcfe-3f3563b677d5"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# =====================================================================
# 🧱 0. IMPORTACIONES Y CONFIGURACIÓN INICIAL
# =====================================================================
from pyspark.sql.functions import current_timestamp, input_file_name, lower, col
from pyspark.sql.types import *
import hashlib
import json

print("🚀 Iniciando Pipeline de Ingesta Bronze: DANE Labor Market...")

# Variables de entorno
entity = "labor"
source_system = "dane"
raw_path = "Files/raw/dane"
bronze_table = "bronze_dane_clean_v3"

# =====================================================================
# 📥 1. EXTRACCIÓN: LEER RAW DATA (Data Lake)
# =====================================================================
print(f"📥 Leyendo archivos crudos desde: {raw_path}")

df_raw = spark.read \
    .format("csv") \
    .option("header", True) \
    .option("delimiter", ";") \
    .option("recursiveFileLookup", "true") \
    .load(raw_path)

# Agregar linaje de datos (Trazabilidad)
df_raw = df_raw.withColumn("file_name", input_file_name())

# =====================================================================
# 🧹 2. TRANSFORMACIÓN LIGERA (Filtro de archivos relevantes)
# =====================================================================
print("🧹 Filtrando archivos relevantes de ocupabilidad...")

df_filtered = df_raw.filter(
    lower(col("file_name")).rlike("ocupados|desocupados|no.?ocupados")
)

print(f"✅ Archivos filtrados. Columnas detectadas: {len(df_filtered.columns)}")

# =====================================================================
# 🧠 3. MOTOR DE VALIDACIÓN DE SCHEMA Y CONTRATOS (Schema Registry)
# =====================================================================
print("🧠 Validando Schema y Data Contracts...")

def normalize_type(t):
    if isinstance(t, IntegerType): return "INT"
    elif isinstance(t, LongType): return "BIGINT"
    elif isinstance(t, DoubleType): return "DOUBLE"
    elif isinstance(t, FloatType): return "FLOAT"
    elif isinstance(t, BooleanType): return "BOOLEAN"
    elif isinstance(t, DateType): return "DATE"
    elif isinstance(t, TimestampType): return "TIMESTAMP"
    else: return "STRING"

# 3.1 Capturar schema actual
current_schema = {field.name: normalize_type(field.dataType) for field in df_filtered.schema.fields}
schema_json = df_filtered.schema.json()
schema_hash = hashlib.md5(schema_json.encode()).hexdigest()

# 3.2 Obtener schema anterior (Nota: Asegúrate de que esta tabla exista en tu nuevo entorno)
try:
    prev_schema_df = spark.sql(f"""
        SELECT schema_json FROM schema_registry 
        WHERE entity = '{entity}' AND is_active = true LIMIT 1
    """)
    has_prev_schema = prev_schema_df.count() > 0
except Exception as e:
    print("⚠️ Tabla schema_registry no encontrada o vacía. Se asume carga inicial.")
    has_prev_schema = False

# 3.3 Obtener Data Contracts
try:
    contract_df = spark.sql(f"SELECT source_column, is_critical, allow_type_change FROM column_mapping WHERE entity = '{entity}' AND is_active = true")
    contract = {row["source_column"]: {"is_critical": row["is_critical"] or False, "allow_type_change": row["allow_type_change"] or True} for row in contract_df.collect()}
except:
    contract = {} # Si no hay contrato, se asume permisivo

# 3.4 Detección de Drift
if has_prev_schema:
    prev_schema_json = prev_schema_df.collect()[0]["schema_json"]
    prev_fields = {f["name"]: f["type"] for f in json.loads(prev_schema_json)["fields"]}

    for col_name, current_type in current_schema.items():
        if col_name in prev_fields:
            prev_type = prev_fields[col_name]
            if prev_type != current_type:
                print(f"⚠️ TYPE DRIFT DETECTED → {col_name}: {prev_type} → {current_type}")
                rules = contract.get(col_name, {"is_critical": False, "allow_type_change": True})

                if rules["is_critical"] and not rules["allow_type_change"]:
                    raise Exception(f"❌ DATA CONTRACT VIOLATION: Column '{col_name}' changed from {prev_type} to {current_type}")
                else:
                    # Registrar en Drift Log
                    details = json.dumps({"column": col_name, "from": prev_type, "to": current_type})
                    log_schema = StructType([
                        StructField("entity", StringType(), True), StructField("detected_at", TimestampType(), True),
                        StructField("drift_type", StringType(), True), StructField("schema_json", StringType(), True),
                        StructField("details_json", StringType(), True)
                    ])
                    df_log = spark.createDataFrame([(entity, None, "TYPE_CHANGE", prev_schema_json, details)], log_schema).withColumn("detected_at", current_timestamp())
                    df_log.write.mode("append").saveAsTable("schema_drift_log")

# 3.5 Actualizar Schema Registry si es nuevo
try:
    existing = spark.sql(f"SELECT 1 FROM schema_registry WHERE entity = '{entity}' AND schema_hash = '{schema_hash}' AND is_active = true")
    if existing.count() == 0:
        next_version = spark.sql(f"SELECT COALESCE(MAX(version), 0) + 1 as nv FROM schema_registry WHERE entity = '{entity}'").collect()[0]["nv"]
        spark.sql(f"UPDATE schema_registry SET is_active = false, effective_to = current_timestamp() WHERE entity = '{entity}' AND is_active = true")
        spark.sql(f"""
            INSERT INTO schema_registry VALUES 
            ('{source_system}', '{entity}', {next_version}, '{schema_json}', '{schema_hash}', current_timestamp(), NULL, true, current_timestamp())
        """)
        print(f"📌 Nuevo schema registrado (Versión {next_version})")
except Exception as e:
    pass # Falla silenciosa si las tablas de metadatos aún no existen en la migración

# =====================================================================
# 💾 4. CARGA: ESCRIBIR EN CAPA BRONZE
# =====================================================================
print(f"💾 Escribiendo datos en Delta Table: {bronze_table}...")

df_filtered.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(bronze_table)

print("✅ ¡Pipeline finalizado con éxito! Datos almacenados en Bronze.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DETECTAR ESQUEMA

# CELL ********************

from pyspark.sql.functions import input_file_name, col, lower, size, split, when

# ============================================
# 📥 1. LEER ARCHIVOS COMO TEXTO (RAW)
# ============================================

df_raw = spark.read \
    .format("text") \
    .load("Files/raw/dane/year=2026")

df_raw = df_raw.withColumn("file_name", input_file_name())

print("✅ Archivos leídos en modo raw")

# ============================================
# 🧠 2. CONTAR COLUMNAS REALES (split por ;)
# ============================================

df_cols = df_raw.withColumn(
    "num_columns",
    size(split(col("value"), ";"))
)

# ============================================
# 🧠 3. CLASIFICAR ARCHIVOS
# ============================================

df_cols = df_cols.withColumn(
    "file_type",
    when(lower(col("file_name")).rlike("no.?ocupados"), "desocupados")
    .when(lower(col("file_name")).rlike("ocupados"), "ocupados")
    .otherwise("otros")
)

# ============================================
# 📊 4. VALIDACIÓN GLOBAL
# ============================================

df_cols.groupBy("file_type", "num_columns") \
    .count() \
    .orderBy("file_type", "num_columns") \
    .show(100, False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

spark.table("schema_registry").show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# MARKDOWN ********************

# ## BLOQUE NUEVO: DETECTAR TYPE DRIFT

# CELL ********************

# ============================================
# 🧱 CONFIG
# ============================================

from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import *
import hashlib
import json

entity = "labor"
source_system = "dane"

bronze_table = "dane_bronze_lh.bronze_dane_clean_v3"

# ============================================
# 📥 1. LEER BRONZE
# ============================================

df = spark.table(bronze_table)

print("✅ Bronze leído")
print("Columnas:", df.columns)

# ============================================
# 🧠 2. NORMALIZAR TIPOS
# ============================================

def normalize_type(t):
    if isinstance(t, IntegerType):
        return "INT"
    elif isinstance(t, LongType):
        return "BIGINT"
    elif isinstance(t, DoubleType):
        return "DOUBLE"
    elif isinstance(t, FloatType):
        return "FLOAT"
    elif isinstance(t, BooleanType):
        return "BOOLEAN"
    elif isinstance(t, DateType):
        return "DATE"
    elif isinstance(t, TimestampType):
        return "TIMESTAMP"
    else:
        return "STRING"

# ============================================
# 📊 3. SCHEMA ACTUAL
# ============================================

current_schema = {
    field.name: normalize_type(field.dataType)
    for field in df.schema.fields
}

schema_json = df.schema.json()
schema_hash = hashlib.md5(schema_json.encode()).hexdigest()

print("Schema hash:", schema_hash)

# ============================================
# 📜 4. SCHEMA ANTERIOR
# ============================================

prev_schema_df = spark.sql(f"""
SELECT schema_json
FROM schema_registry
WHERE entity = '{entity}'
AND is_active = true
LIMIT 1
""")

# ============================================
# 📜 5. DATA CONTRACTS
# ============================================

contract_df = spark.sql(f"""
SELECT source_column, is_critical, allow_type_change
FROM column_mapping
WHERE entity = '{entity}'
AND is_active = true
""")

contract = {
    row["source_column"]: {
        "is_critical": row["is_critical"] if row["is_critical"] is not None else False,
        "allow_type_change": row["allow_type_change"] if row["allow_type_change"] is not None else True
    }
    for row in contract_df.collect()
}

type_drift_detected = False

# ============================================
# 🔍 6. TYPE DRIFT DETECTION + CONTRACT ENFORCEMENT
# ============================================

if prev_schema_df.count() > 0:

    prev_schema_json = prev_schema_df.collect()[0]["schema_json"]
    prev_schema = json.loads(prev_schema_json)

    prev_fields = {
        f["name"]: f["type"]
        for f in prev_schema["fields"]
    }

    for col_name, current_type in current_schema.items():

        if col_name in prev_fields:

            prev_type = prev_fields[col_name]

            if prev_type != current_type:

                print(f"⚠️ TYPE DRIFT DETECTED → {col_name}: {prev_type} → {current_type}")

                type_drift_detected = True

                rules = contract.get(col_name, {
                    "is_critical": False,
                    "allow_type_change": True
                })

                # ============================================
                # 🚨 DATA CONTRACT ENFORCEMENT
                # ============================================

                if rules["is_critical"] and not rules["allow_type_change"]:
                    
                    print(f"❌ CONTRACT VIOLATION → {col_name}")

                    raise Exception(f"""
                    DATA CONTRACT VIOLATION:
                    Column: {col_name}
                    From: {prev_type}
                    To: {current_type}
                    """)

                else:
                    print(f"⚠️ Drift permitido → {col_name}")

                    # ============================================
                    # 🧾 JSON DETALLE
                    # ============================================

                    details = json.dumps({
                        "column": col_name,
                        "from": prev_type,
                        "to": current_type
                    })

                    # ============================================
                    # 🧠 SCHEMA LOG
                    # ============================================

                    log_schema = StructType([
                        StructField("entity", StringType(), True),
                        StructField("detected_at", TimestampType(), True),
                        StructField("drift_type", StringType(), True),
                        StructField("schema_json", StringType(), True),
                        StructField("details_json", StringType(), True)
                    ])

                    log_data = [(
                        entity,
                        None,
                        "TYPE_CHANGE",
                        prev_schema_json,
                        details
                    )]

                    df_log = spark.createDataFrame(log_data, log_schema) \
                        .withColumn("detected_at", current_timestamp())

                    df_log.write.mode("append").saveAsTable("schema_drift_log")

# ============================================
# 🔄 7. REGISTRAR NUEVO SCHEMA
# ============================================

existing = spark.sql(f"""
SELECT *
FROM schema_registry
WHERE entity = '{entity}'
AND schema_hash = '{schema_hash}'
AND is_active = true
""")

if existing.count() == 0:

    print("⚠️ Nuevo schema detectado")

    version_df = spark.sql(f"""
        SELECT COALESCE(MAX(version), 0) + 1 as next_version
        FROM schema_registry
        WHERE entity = '{entity}'
    """)

    next_version = version_df.collect()[0]["next_version"]

    print(f"📌 Nueva versión: {next_version}")

    # desactivar anterior
    spark.sql(f"""
        UPDATE schema_registry
        SET is_active = false,
            effective_to = current_timestamp()
        WHERE entity = '{entity}'
        AND is_active = true
    """)

    # insertar nuevo
    spark.sql(f"""
        INSERT INTO schema_registry
        VALUES (
            '{source_system}',
            '{entity}',
            {next_version},
            '{schema_json}',
            '{schema_hash}',
            current_timestamp(),
            NULL,
            true,
            current_timestamp()
        )
    """)

    print("✅ Schema registrado")

else:
    print("✅ Schema ya existente")

# ============================================
# 🧪 8. VALIDACIÓN
# ============================================

print("===== SCHEMA REGISTRY =====")
spark.table("schema_registry").show(truncate=False)

print("===== DRIFT LOG =====")
spark.table("schema_drift_log").show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

df = spark.read \
    .format("csv")\
    .option("header", True) \
    .option("delimiter", ";") \
    .option("recursiveFileLookup", "true") \
    .load("Files/raw/dane")

from pyspark.sql.functions import input_file_name

df = df.withColumn("file_name", input_file_name())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql.functions import lower, col

df = df.filter(
    lower(col("file_name")).rlike("ocupados|desocupados|no.?ocupados")
)

print("✅ Solo archivos relevantes")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

print("Columnas detectadas:")
print(df.columns)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql.functions import col, input_file_name

df_2019_raw = spark.read \
    .format("text") \
    .option("recursiveFileLookup", "true") \
    .load("Files/raw/dane/year=2019")

df_2019_raw = df_2019_raw.withColumn("file_name", input_file_name())

print("Total registros:")
print(df_2019_raw.count())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

df_2019_raw.select("value").show(10, False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql.functions import length, regexp_replace

df_2019_raw.select(
    (length(col("value")) - length(regexp_replace(col("value"), ";", ""))).alias("semicolon_count"),
    (length(col("value")) - length(regexp_replace(col("value"), ",", ""))).alias("comma_count")
).groupBy("semicolon_count", "comma_count").count().show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql.functions import split, size

df_2019_cols = df_2019_raw.withColumn(
    "num_columns",
    size(split(col("value"), ";"))
)

df_2019_cols.groupBy("num_columns").count().show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# MARKDOWN ********************

# ## PRUEBAS INGESTIÓN EN BRONZE

# CELL ********************

# ============================================
# 🔍 BRONZE INSPECTION — FILE NAMES
# ============================================

from pyspark.sql import functions as F
from pyspark.sql.functions import input_file_name

year = 2021
bronze_path = f"Files/raw/dane/year={year}"

df = spark.read \
    .format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load(bronze_path)

# ✅ FIX CLAVE — crear file_name
df = df.withColumn("file_name", input_file_name())

# ============================================
# 📊 LIST FILES
# ============================================

df.select("file_name").distinct().show(truncate=False)

# ============================================
# 📊 COUNT BY FILE
# ============================================

df.groupBy("file_name").count().orderBy("file_name").show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

# Usamos las herramientas de sistema de archivos nativas de Fabric
print("🔍 Escaneando directamente el almacenamiento de Enero 2021...")

try:
    archivos_reales = mssparkutils.fs.ls("Files/raw/dane/year=2021/month=01/")
    
    if not archivos_reales:
        print("⚠️ El sistema de archivos reporta que la carpeta está vacía.")
    else:
        print(f"✅ Se encontraron {len(archivos_reales)} elementos físicos en disco:\n")
        print(f"{'Nombre del Archivo':<60} | {'Tamaño (Bytes)':<15}")
        print("-" * 80)
        for f in archivos_reales:
            print(f"{f.name:<60} | {f.size:<15}")
            
except Exception as e:
    print(f"❌ Error al acceder a la ruta física: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2021
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo definitivo para {year} (Motor de Deduplicación y Filtro Estricto)...")

try:
    # 1. Lectura distribuida perezosa
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # =========================================================================
    # 🚨 FILTRO SEMÁNTICO Y DEDUPLICADOR
    # =========================================================================
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingresos|vivienda|seguridad|formas|inact|inactivos|fuerza|caracteristicas|otras|area"))
     # ⛔ Volvemos a bloquear 'area' para evitar multiplicar la población urbana

    # 🛡️ DEDUPLICADOR DE CLONES: Evita procesar el mismo archivo si existe en .CSV y .csv
    # Seleccionamos un archivo único por cada ruta en minúsculas
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]
    # =========================================================================

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para el año {year}.")
    else:
        print(f"📂 Se detectaron {len(unique_files)} archivos únicos. Iniciando procesamiento...")
        processed_dfs = []

        for fn in unique_files:
            match = re.search(r"month=(\d+)", fn)
            if not match: continue
            m = int(match.group(1))

            df_file = df_meta.filter(F.col("file_name") == fn)
            first_rows = df_file.limit(5).collect() 
            if not first_rows: continue
            
            label = first_rows[0]['status_file']
            
            header_val = None
            for row in first_rows:
                if any(x in row['value'].upper() for x in ["FEX", "DIRECTORIO", "DPTO", "MES", "AREA"]):
                    header_val = row['value']
                    break
            
            if not header_val: continue

            # WHITESPACE SNIFFER
            if ";" in header_val:
                py_delim, sp_delim = ";", ";"
            elif "," in header_val:
                py_delim, sp_delim = ",", ","
            else:
                py_delim, sp_delim = None, r"\s+"
            
            if py_delim:
                cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else:
                cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn(
                        "geo_source",
                        F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
                         .otherwise("resto") 
                    )
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"),
                    F.lit(m).alias("month"),
                    F.lit(label).alias("status"),
                    F.col("geo_source"),
                    depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        # Unión de todos los meses procesados
        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y EN LIMPIO!")
            
            for d in processed_dfs: d.unpersist()
            
            print(f"\n📊 Control de Calidad Rápido para {year}:")
            df_silver_unified.groupBy("month", "status").agg(
                F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")
            ).orderBy("month", "status").show(24)
        else:
            print(f"❌ Error: Ningún archivo pudo alinearse para el año {year}.")

except Exception as e:
     print(f"❌ Error crítico en el año {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
