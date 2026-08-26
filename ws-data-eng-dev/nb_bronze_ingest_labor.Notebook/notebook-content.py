# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "4a3cc7ca-f052-4b3e-b7ff-591fedda430a",
# META       "default_lakehouse_name": "dane_bronze_lh",
# META       "default_lakehouse_workspace_id": "13ed579f-4a14-414c-8f38-f62e44db2afc",
# META       "known_lakehouses": [
# META         {
# META           "id": "4a3cc7ca-f052-4b3e-b7ff-591fedda430a"
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
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
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
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
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
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

# =====================================================================
# 🚀 MOTOR CALIBRADO DANE 2004-2026 (METODOLOGÍA OFICIAL GEIH)
# =====================================================================
from pyspark.sql import functions as F
from pyspark.sql.types import *
import re

raw_base_path = "abfss://13ed579f-4a14-414c-8f38-f62e44db2afc@onelake.dfs.fabric.microsoft.com/4a3cc7ca-f052-4b3e-b7ff-591fedda430a/Files/raw/dane"
silver_table_path = "abfss://13ed579f-4a14-414c-8f38-f62e44db2afc@onelake.dfs.fabric.microsoft.com/4a3cc7ca-f052-4b3e-b7ff-591fedda430a/Tables/dbo/silver_dane_labor_market"

years_available = [2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

print("🚀 Iniciando Ingesta Calibrada DANE (2004 - 2026)...")

for yr in years_available:
    year_path = f"{raw_base_path}/year={yr}"
    print(f"\n==================================================")
    print(f"⏳ PROCESANDO AÑO: {yr}")
    print(f"==================================================")

    try:
        # Delimitadores por época
        if yr <= 2015:
            delim = "\t"
            path_glob = f"{year_path}/*/*.txt"
        elif yr == 2016:
            delim = ";"
            path_glob = f"{year_path}/*/*/*.csv"
        elif 2017 <= yr <= 2019:
            delim = ";"
            path_glob = f"{year_path}/*/*.csv"
        elif yr in [2020, 2021]:
            delim = ","
            path_glob = f"{year_path}/*/*.CSV"
        else:
            delim = ";"
            path_glob = f"{year_path}/*/*.[cC][sS][vV]"

        # 1. Cargar archivos del año
        df_raw = spark.read \
            .format("csv") \
            .option("header", "true") \
            .option("delimiter", delim) \
            .load(path_glob) \
            .withColumn("source_file", F.input_file_name()) \
            .withColumn("fn_low", F.lower(F.col("source_file")))

        # 2. FILTRADO ESTRICTO DE MÓDULOS (Evita duplicar población con módulos de subempleo o secundario)
        # Excluye 'area' para no doblar cabecera+resto
        df_mod = df_raw.filter(
            ~F.col("fn_low").rlike("(?i)ingresos|vivienda|seguridad|formas|inact|inactivos|fuerza|caracteristicas|otras|subempleo|secundario|area") &
            F.col("fn_low").rlike("(?i)ocupa|desocu|no.*ocu")
        )

        # 3. Normalizar nombres de columna a mayúsculas
        cols_map = {c: c.upper().strip() for c in df_mod.columns}
        df_upper = df_mod
        for old_c, new_c in cols_map.items():
            df_upper = df_upper.withColumnRenamed(old_c, new_c)

        cols_list = df_upper.columns
        dpto_col = next((c for c in ["DPTO", "COD_DPTO", "DEP"] if c in cols_list), None)
        fex_col = next((c for c in ["FEX_C18", "FEX_C_2011", "FEX_C", "PESO", "FACTOR"] if c in cols_list), None)
        dsi_col = next((c for c in ["DSI", "P49", "FT"] if c in cols_list), None)

        if not dpto_col or not fex_col:
            print(f"⚠️ Columnas no encontradas en {yr} (DPTO={dpto_col}, FEX={fex_col})")
            continue

        # 4. Clasificación y filtro de Desempleo (DSI == 1 para No Ocupados)
        df_proc = df_upper.withColumn(
            "status",
            F.when(F.col("FN_LOW").rlike("(?i)desocu|no.*ocu"), "desocupado").otherwise("ocupado")
        ).withColumn(
            "month",
            F.coalesce(F.regexp_extract(F.col("SOURCE_FILE"), r"month=(\d+)", 1).cast("int"), F.lit(1))
        ).withColumn(
            "geo_source",
            F.when(F.col("FN_LOW").rlike("(?i)resto"), "resto").otherwise("cabecera")
        )

        # Si el módulo es de No Ocupados (2022-2026), filtrar solo DSI=1 (Desocupados reales)
        if yr >= 2022 and dsi_col:
            df_proc = df_proc.filter(
                (F.col("status") == "ocupado") |
                ((F.col("status") == "desocupado") & (F.trim(F.col(dsi_col)).isin("1", "1.0", "1,0")))
            )

        # 5. Seleccionar y limpiar columnas
        df_clean = df_proc.select(
            F.lit(yr).alias("year"),
            F.col("month"),
            F.col("status"),
            F.col("geo_source"),
            F.lpad(F.regexp_replace(F.col(dpto_col), r'[\s"]', ''), 2, "0").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(F.col(fex_col), r'[\s"]', ''), ",", ".").cast("double").alias("total_weight"),
            F.col("SOURCE_FILE").alias("source_file"),
            F.current_timestamp().alias("ingestion_timestamp")
        ).filter(
            F.col("total_weight").isNotNull() & 
            (F.col("total_weight") > 0) & 
            (F.col("codigo_departamento") != "00")
        )

        mode_w = "overwrite" if yr == 2004 else "append"
        df_clean.write \
            .format("delta") \
            .mode(mode_w) \
            .option("overwriteSchema", "true" if yr == 2004 else "false") \
            .partitionBy("year") \
            .save(silver_table_path)

        count_yr = df_clean.count()
        print(f"✅ Año {yr} procesado: {count_yr:,} registros guardados en Silver. (DPTO={dpto_col}, FEX={fex_col})")

    except Exception as e:
        print(f"❌ Error en año {yr}: {e}")

print("\n🎉 ¡Procesamiento Silver Calibrado Finalizado!")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# CELL ********************

# =====================================================================
# 🎯 CALIBRACIÓN ESTRICTA ERA PANDEMIA (2020 Y 2021)
# =====================================================================
import re
from pyspark.sql import functions as F

silver_table_path = "abfss://13ed579f-4a14-414c-8f38-f62e44db2afc@onelake.dfs.fabric.microsoft.com/4a3cc7ca-f052-4b3e-b7ff-591fedda430a/Tables/dbo/silver_dane_labor_market"
raw_base_path = "abfss://13ed579f-4a14-414c-8f38-f62e44db2afc@onelake.dfs.fabric.microsoft.com/4a3cc7ca-f052-4b3e-b7ff-591fedda430a/Files/raw/dane"

for yr in [2020, 2021]:
    year_path = f"{raw_base_path}/year={yr}"
    print(f"\n==================== PROCESANDO AÑO {yr} ====================")
    
    processed_dfs = []
    
    for month_dir in mssparkutils.fs.ls(year_path):
        m_val = int(re.search(r"month=(\d+)", month_dir.name).group(1))
        month_files = mssparkutils.fs.ls(month_dir.path)
        file_names = [f.name for f in month_files]
        
        has_desocu_file = any("desocu" in f.lower() or "desoucp" in f.lower() for f in file_names)
        
        for f in month_files:
            fn = f.name
            fn_low = fn.lower()
            
            # En 2021: solo tomamos Cabecera y Resto (ignoramos archivos que empiecen con 'Area - ')
            if yr == 2021 and fn.startswith("Area - "):
                continue
                
            # Identificar qué archivo procesar
            is_ocupado = "ocupados" in fn_low and not ("desocu" in fn_low or "desoucp" in fn_low or "no" in fn_low)
            is_desocupado = "desocu" in fn_low or "desoucp" in fn_low
            is_fuerza = "fuerza" in fn_low and not has_desocu_file  # Usar Fuerza de trabajo solo si falta Desocupados
            
            if not (is_ocupado or is_desocupado or is_fuerza):
                continue
                
            sample = spark.read.format("text").load(f.path).limit(1).collect()[0]['value']
            delim = ";" if ";" in sample else ("," if "," in sample else "\t")
            
            df_f = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(f.path)
            
            # Normalizar columnas
            for c in df_f.columns:
                df_f = df_f.withColumnRenamed(c, c.upper().strip())
                
            cols = df_f.columns
            dpto_col = next((c for c in ["DPTO", "COD_DPTO", "DEP"] if c in cols), None)
            fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "FEX_C18", "PESO", "FACTOR"] if c in cols), None)
            dsi_col = next((c for c in ["DSI", "P49", "FT", "RAMA4D_D_R4"] if c in cols), None)
            
            if not dpto_col or not fex_col:
                continue
                
            if is_ocupado:
                status_label = "ocupado"
            elif is_desocupado:
                status_label = "desocupado"
            elif is_fuerza:
                # Filtrar solo desempleados dentro de Fuerza de Trabajo
                status_label = "desocupado"
                if dsi_col:
                    df_f = df_f.filter(F.trim(F.col(dsi_col)).isin("1", "1.0", "1,0", "2"))
                    
            geo_label = "resto" if "resto" in fn_low else "cabecera"
            
            df_clean = df_f.select(
                F.lit(yr).alias("year"),
                F.lit(m_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_label).alias("geo_source"),
                F.lpad(F.regexp_replace(F.col(dpto_col), r'[\s"]', ''), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col(fex_col), r'[\s"]', ''), ",", ".").cast("double").alias("total_weight"),
                F.lit(f.path).alias("source_file"),
                F.current_timestamp().alias("ingestion_timestamp")
            ).filter(F.col("total_weight") > 0)
            
            processed_dfs.append(df_clean)

    if processed_dfs:
        df_yr_unified = processed_dfs[0]
        for d in processed_dfs[1:]:
            df_yr_unified = df_yr_unified.unionByName(d)
            
        df_yr_unified.write \
            .format("delta") \
            .mode("overwrite") \
            .option("replaceWhere", f"year = {yr}") \
            .save(silver_table_path)
            
        print(f"✅ ¡Año {yr} completado con éxito! {df_yr_unified.count():,} registros.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 🎯 CALIBRACIÓN DEFINITIVA AÑO PANDEMIA 2020
# =====================================================================
import re
from pyspark.sql import functions as F

silver_table_path = "abfss://13ed579f-4a14-414c-8f38-f62e44db2afc@onelake.dfs.fabric.microsoft.com/4a3cc7ca-f052-4b3e-b7ff-591fedda430a/Tables/dbo/silver_dane_labor_market"
raw_base_path = "abfss://13ed579f-4a14-414c-8f38-f62e44db2afc@onelake.dfs.fabric.microsoft.com/4a3cc7ca-f052-4b3e-b7ff-591fedda430a/Files/raw/dane/year=2020"

yr = 2020
print(f"🚀 Procesando Año {yr} con Calibración Exacta FT...")

processed_2020_dfs = []

for month_dir in mssparkutils.fs.ls(raw_base_path):
    m_val = int(re.search(r"month=(\d+)", month_dir.name).group(1))
    month_files = mssparkutils.fs.ls(month_dir.path)
    file_names = [f.name for f in month_files]
    
    # 1. Leer Ocupados del mes
    ocu_file = next((f.path for f in month_files if "ocupados" in f.name.lower() and not any(x in f.name.lower() for x in ["desocu", "no"])), None)
    if ocu_file:
        df_ocu = spark.read.format("csv").option("header", "true").option("delimiter", ",").load(ocu_file)
        for c in df_ocu.columns: df_ocu = df_ocu.withColumnRenamed(c, c.upper().strip())
        
        df_clean_ocu = df_ocu.select(
            F.lit(yr).alias("year"),
            F.lit(m_val).alias("month"),
            F.lit("ocupado").alias("status"),
            F.lit("cabecera").alias("geo_source"),
            F.lpad(F.regexp_replace(F.col("DPTO"), r'[\s"]', ''), 2, "0").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(F.col("FEX_C"), r'[\s"]', ''), ",", ".").cast("double").alias("total_weight"),
            F.lit(ocu_file).alias("source_file"),
            F.current_timestamp().alias("ingestion_timestamp")
        ).filter(F.col("total_weight") > 0)
        processed_2020_dfs.append(df_clean_ocu)
        
    # 2. Leer Desocupados del mes (o de Fuerza de trabajo si falta el archivo)
    desocu_file = next((f.path for f in month_files if "desocu" in f.name.lower() or "desoucp" in f.name.lower()), None)
    
    if desocu_file:
        df_des = spark.read.format("csv").option("header", "true").option("delimiter", ",").load(desocu_file)
        for c in df_des.columns: df_des = df_des.withColumnRenamed(c, c.upper().strip())
        
        df_clean_des = df_des.select(
            F.lit(yr).alias("year"),
            F.lit(m_val).alias("month"),
            F.lit("desocupado").alias("status"),
            F.lit("cabecera").alias("geo_source"),
            F.lpad(F.regexp_replace(F.col("DPTO"), r'[\s"]', ''), 2, "0").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(F.col("FEX_C"), r'[\s"]', ''), ",", ".").cast("double").alias("total_weight"),
            F.lit(desocu_file).alias("source_file"),
            F.current_timestamp().alias("ingestion_timestamp")
        ).filter(F.col("total_weight") > 0)
        processed_2020_dfs.append(df_clean_des)
    else:
        # Extraer desempleados desde Fuerza de Trabajo (Ft == 2 o DSI == 1)
        fuerza_file = next((f.path for f in month_files if "fuerza" in f.name.lower()), None)
        if fuerza_file:
            df_ft = spark.read.format("csv").option("header", "true").option("delimiter", ",").load(fuerza_file)
            for c in df_ft.columns: df_ft = df_ft.withColumnRenamed(c, c.upper().strip())
            
            # FT == 2 es la definición de desocupados en el módulo Fuerza de trabajo
            df_ft_des = df_ft.filter(F.trim(F.col("FT")) == "2")
            
            df_clean_ft = df_ft_des.select(
                F.lit(yr).alias("year"),
                F.lit(m_val).alias("month"),
                F.lit("desocupado").alias("status"),
                F.lit("cabecera").alias("geo_source"),
                F.lpad(F.regexp_replace(F.col("DPTO"), r'[\s"]', ''), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col("FEX_C"), r'[\s"]', ''), ",", ".").cast("double").alias("total_weight"),
                F.lit(fuerza_file).alias("source_file"),
                F.current_timestamp().alias("ingestion_timestamp")
            ).filter(F.col("total_weight") > 0)
            processed_2020_dfs.append(df_clean_ft)

if processed_2020_dfs:
    df_2020_unified = processed_2020_dfs[0]
    for d in processed_2020_dfs[1:]:
        df_2020_unified = df_2020_unified.unionByName(d)
        
    df_2020_unified.write \
        .format("delta") \
        .mode("overwrite") \
        .option("replaceWhere", "year = 2020") \
        .save(silver_table_path)
        
    print(f"✅ ¡Año 2020 calibrado con éxito! {df_2020_unified.count():,} registros.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
