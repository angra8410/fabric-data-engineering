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
# META         },
# META         {
# META           "id": "b08baa46-ed61-4e0b-bd16-6a73991ec1ba"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

## ============================================================================
## 🚀 SILVER 2021: VERSIÓN SANADA (LÍNEAS LIBERADAS + SOPORTE MULTIDIMENSIONAL)
## ============================================================================
from pyspark.sql import functions as F

year = 2021
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print("🕵️‍♂️ Iniciando escaneo nativo profundo...")

# 1. Buscamos archivos liberando 'fuerza' y 'caracteristicas' de la lista negra
all_files = spark.createDataFrame(
    spark.sparkContext.wholeTextFiles(f"{bronze_path}*/*", minPartitions=1)
).select(F.col("_1").alias("path")).filter(F.lower(F.col("path")).rlike("ocupa|deso|fuerza|caracteristicas")) \
 .filter(F.lower(F.col("path")).rlike("\.csv$")) \
 .filter(~F.lower(F.col("path")).rlike("ingresos|vivienda|seguridad|formas|inactivos")) # 🌟 ¡Lista negra saneada de raíz!

files_list = [row['path'] for row in all_files.collect()]
print(f"📂 Se encontraron {len(files_list)} archivos válidos. Procesando la serie completa...")

final_list = []

for path in files_list:
    fn = path.lower()
    # Clasificación semántica adaptada a la estructura real del DANE 2021
    label = "desocupado" if any(x in fn for x in ["deso", "no%20ocu", "no_ocu", "fuerza"]) else "ocupado"
    geo = "cabecera" if any(x in fn for x in ["cabe", "urban"]) else ("resto" if any(x in fn for x in ["resto", "rural"]) else "area")
    
    # Extraemos el mes manejando el cero (ej: month=05 -> 5)
    month_str = path.split("month=")[1].split("/")[0]
    month = int(month_str)
    
    df_temp = spark.read.text(path)
    header_row = df_temp.filter(F.upper(F.col("value")).rlike("DIRECTORIO|SECUENCIA")).limit(1).collect()
    
    if not header_row: continue
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper() for c in val.split(delim)]
    
    try:
        # Indexación dinámica de variables críticas
        idx_peso = next(i for i, c in enumerate(cols) if any(p in c for p in ["FEX", "PESO", "FACTOR"]))
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
        
        # Mapeo posicional dinámico de geografía si viene dentro del archivo
        geo_expr = F.lit(geo)
        if idx_clase is not None:
            geo_expr = F.when(F.split(F.col("value"), delim)[idx_clase].rlike("1"), "cabecera") \
                        .when(F.split(F.col("value"), delim)[idx_clase].rlike("2"), "resto") \
                        .otherwise(F.lit(geo))

        # Extracción y casteo estructurado
        processed = df_temp.filter(~F.upper(F.col("value")).rlike("DIRECTORIO|SECUENCIA")) \
            .withColumn("split_data", F.split(F.col("value"), delim)) \
            .select(
                F.lit(year).alias("year"),
                F.lit(month).alias("month"),
                F.lit(label).alias("status"),
                geo_expr.alias("geo_source"),
                (F.lpad(F.regexp_replace(F.split(F.col("value"), delim)[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")).alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.split(F.col("value"), delim)[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("weight")
            ).filter(F.col("weight").isNotNull() & (F.col("weight") > 0))
        
        final_list.append(processed)
    except:
        continue

# 2. Unión y Guardado Físico en Silver
if final_list:
    df_silver_2021 = final_list[0]
    for d in final_list[1:]: df_silver_2021 = df_silver_2021.unionByName(d)
    
    # Forzar consistencia estricta de coberturas
    df_silver_2021 = df_silver_2021.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2021.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n📊 RESUMEN FINAL SILVER {year} - AUDITORÍA DE CONTROL:")
    df_silver_2021.groupBy("month", "status").count().orderBy("month", "status").show(24, False)
else:
    print("❌ Error fatal: La lista de archivos quedó vacía tras el filtrado.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Verificación rápida de la estructura real guardada en Silver 2021
print("👀 Muestra de control geográfico en la tabla Silver:")
spark.sql("""
    SELECT month, codigo_departamento, status, COUNT(*) as registros 
    FROM dane_silver_lh.labor_2021 
    WHERE month = 2 AND codigo_departamento IN ('05', '08', '11')
    GROUP BY month, codigo_departamento, status 
    ORDER BY codigo_departamento, status
""").show()

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

print(f"🕵️‍♂️ Iniciando escaneo definitivo para {year}...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 FILTRO SEMÁNTICO PERFECTO: Solo Ocupados y Desocupados reales
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingresos|vivienda|seguridad|formas|inact|area|inactivos|fuerza|caracteristicas|otras")) 
     # 'fuerza', 'area' e 'inactivos' están bloqueados para evitar datos falsos

    unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
    
    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para el año {year}.")
    else:
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
            ).orderBy("month", "status").show()
        else:
            print(f"❌ Error: Ningún archivo pudo alinearse para el año {year}.")

except Exception as e:
     print(f"❌ Error crítico en el año {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## ----------------------------------------------------
# ## RECREACIÒN DE SILVER 2021 DE MANERA CORRECTA
# ## ----------------------------------------------------

# CELL ********************

# ============================================
# 🧱 CONFIG
# ============================================

from pyspark.sql.functions import (
    input_file_name, col, lower, split, size
)

bronze_path = "Files/raw/dane/year=2026"

# ============================================
# 📥 1. LEER RAW
# ============================================

df_raw = spark.read \
    .format("text") \
    .option("recursiveFileLookup", "true") \
    .load(bronze_path)

df_raw = df_raw.withColumn("file_name", input_file_name())

print("✅ Archivos leídos")

# ============================================
# 🧠 2. IDENTIFICAR DATASETS
# ============================================

df_raw = df_raw.withColumn(
    "file_name_clean",
    lower(col("file_name"))
)

# ============================================
# 🔍 3. CLASIFICACIÓN AMPLIA
# ============================================

from pyspark.sql.functions import when

df_raw = df_raw.withColumn(
    "dataset",
    when(col("file_name_clean").contains("ocupados"), "ocupados")
    .when(col("file_name_clean").contains("no%20ocupados"), "no_ocupados")
    .when(col("file_name_clean").contains("fuerza"), "fuerza_trabajo")
    .when(col("file_name_clean").contains("hogar"), "hogar")
    .otherwise("otros")
)

# ============================================
# 🔬 4. SPLIT COLUMNAS
# ============================================

df_raw = df_raw.withColumn(
    "cols",
    split(col("value"), ";")
)

df_raw = df_raw.withColumn(
    "num_columns",
    size(col("cols"))
)

# ============================================
# 📊 5. DISTRIBUCIÓN
# ============================================

print("📊 Distribución por dataset:")
df_raw.groupBy("dataset", "num_columns").count().show(100, False)

# ============================================
# 🧠 6. EXTRAER HEADER POR DATASET
# ============================================

datasets = ["ocupados", "no_ocupados", "fuerza_trabajo"]

for ds in datasets:
    print(f"\n🔎 DATASET: {ds}")
    
    df_ds = df_raw.filter(col("dataset") == ds)
    
    header = df_ds \
        .filter(col("value").rlike("MES|AREA|FT|OCI")) \
        .select("cols") \
        .first()
    
    if header:
        cols = header[0]
        print(f"✔ Columnas detectadas: {len(cols)}")
        print(cols[:20])  # primeras columnas
    else:
        print("❌ No se detectó header")

# ============================================
# 🔍 7. SAMPLE REAL POR DATASET
# ============================================

for ds in datasets:
    print(f"\n📄 SAMPLE: {ds}")
    
    df_raw.filter(col("dataset") == ds) \
        .select("value") \
        .show(5, False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ============================================
# 🧱 CONFIG
# ============================================

from pyspark.sql.functions import (
    col, when, input_file_name, lower, trim,
    lit, regexp_extract, current_timestamp,
    to_json, struct
)
from pyspark.sql.types import StringType

bronze_path = "Files/raw/dane"

silver_table = "dane_silver_lh.labor_silver_real"
quarantine_table = "dane_silver_lh.labor_quarantine"

# ============================================
# 📥 1. READ BRONZE
# ============================================

df = spark.read \
    .format("csv") \
    .option("header", True) \
    .option("delimiter", ";") \
    .option("recursiveFileLookup", "true") \
    .load(bronze_path)

print("✅ Archivos leídos")

# ============================================
# 🧠 2. FILE NAME NORMALIZADO
# ============================================

df = df.withColumn("file_name", lower(input_file_name()))

# ============================================
# 🧠 3. STATUS DESDE ARCHIVO
# ============================================

df = df.withColumn(
    "status_from_file",
    when(col("file_name").rlike("no.?ocupados|desocupados"), "desocupado")
    .when(col("file_name").rlike("ocupados"), "ocupado")
)

# ============================================
# 🧠 4. DETECTAR SI EXISTE DSI
# ============================================

has_dsi = "DSI" in df.columns

if has_dsi:
    df = df.withColumn("DSI_clean", trim(col("DSI")))

    df = df.withColumn(
        "status_from_dsi",
        when(col("DSI_clean") == "1", "ocupado")
        .when(col("DSI_clean") == "2", "desocupado")
        .when(col("DSI_clean") == "3", "inactivo")
    )
else:
    df = df.withColumn("status_from_dsi", lit(None).cast(StringType()))

# ============================================
# 🧠 5. STATUS FINAL UNIFICADO
# ============================================

df = df.withColumn(
    "status",
    when(col("status_from_file").isNotNull(), col("status_from_file"))
    .otherwise(col("status_from_dsi"))
)

print("✅ Status unificado")

# ============================================
# 🧠 6. EXTRAER YEAR DESDE PATH
# ============================================

df = df.withColumn(
    "year",
    regexp_extract(col("file_name"), r"year=(\d{4})", 1).cast("int")
)

# ============================================
# 🧠 7. SELECCIÓN SEGURA DE COLUMNAS
# ============================================

# Validar columnas mínimas
required_cols = ["MES", "AREA", "DPTO"]

for c in required_cols:
    if c not in df.columns:
        raise Exception(f"❌ Columna {c} no existe en dataset")

# Detectar si existe peso (encuestas)
has_weight = "fex_c_2011" in df.columns

# ============================================
# 🧱 8. NORMALIZAR
# ============================================

df_clean = df.select(
    col("MES").cast("int").alias("month"),
    col("AREA").alias("area_code"),
    col("DPTO").alias("depto_code"),
    col("status"),
    col("year"),
    col("file_name"),
    col("fex_c_2011").cast("double").alias("weight") if has_weight else lit(1.0).alias("weight")
)

# ============================================
# 🧪 9. DATA QUALITY
# ============================================

df_valid = df_clean.filter(
    col("month").between(1, 12) &
    col("year").isNotNull() &
    col("status").isNotNull()
)

df_invalid = df_clean.subtract(df_valid)

valid_count = df_valid.count()
invalid_count = df_invalid.count()

print(f"✔ Registros válidos: {valid_count}")
print(f"❌ Registros inválidos: {invalid_count}")

# ============================================
# 🚨 10. QUARANTINE
# ============================================

if invalid_count > 0:
    df_quarantine = df_invalid.select(
        to_json(struct(*df_invalid.columns)).alias("raw_payload"),
        current_timestamp().alias("detected_at")
    )

    df_quarantine.write \
        .format("delta") \
        .mode("append") \
        .saveAsTable(quarantine_table)

    print(f"⚠️ Enviados a quarantine: {invalid_count}")
else:
    print("✅ No hay inválidos")

# ============================================
# 🧮 11. AGREGACIÓN CORRECTA
# ============================================

df_agg = df_valid.groupBy(
    "year",
    "month",
    "area_code",
    "depto_code",
    "status"
).sum("weight").withColumnRenamed("sum(weight)", "population")

print("✅ Agregación lista")

# ============================================
# 💾 12. WRITE SILVER
# ============================================

df_agg.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(silver_table)

print("✅ Silver creado correctamente")

# ============================================
# 🧪 13. VALIDACIÓN FINAL
# ============================================

spark.table(silver_table).show(50)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## EXTENDER COLUMN MAPPING

# CELL ********************

spark.sql("""
ALTER TABLE column_mapping
ADD COLUMNS (
    is_critical BOOLEAN,
    allow_type_change BOOLEAN
)
""")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## CONFIGURAR CONTRATO

# CELL ********************

spark.sql("""
UPDATE column_mapping
SET 
    is_critical = true,
    allow_type_change = false
WHERE source_column IN ('Year', 'Month')
""")

spark.sql("""
UPDATE column_mapping
SET 
    is_critical = false,
    allow_type_change = true
WHERE source_column IN ('Metric', 'Geography')
""")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## CREAR TABLA DE CUARENTENA

# CELL ********************

spark.sql("""
CREATE TABLE IF NOT EXISTS dane_silver_lh.labor_quarantine (
    raw_payload STRING,
    error_reason STRING,
    detected_at TIMESTAMP
)
USING DELTA
""")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DEFINIR REGLAS DE CALIDAD

# CELL ********************

## Year → no null + numérico
## Month → no null + entre 1 y 12

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ============================================
# 🧱 CONFIG
# ============================================

from pyspark.sql.functions import col, input_file_name, lower, when, regexp_extract

bronze_path = "Files/raw/dane"
silver_table = "dane_silver_lh.labor_silver_clean"

# ============================================
# 📥 1. LEER CSV
# ============================================

df = spark.read \
    .format("csv") \
    .option("header", True) \
    .option("delimiter", ";") \
    .option("recursiveFileLookup", "true") \
    .load(bronze_path)

df = df.withColumn("file_name", input_file_name())

print("✅ Archivos leídos")

# ============================================
# 🔥 2. FILTRAR SOLO DATA RELEVANTE
# ============================================

df = df.filter(
    (lower(col("file_name")).rlike("ocupados|desocupados|no.?ocupados")) &
    (~lower(col("file_name")).rlike("directorio|secuencia|hogar"))
)

print("✅ Archivos filtrados")

# ============================================
# 🧠 3. NORMALIZAR
# ============================================

df_clean = df.select(
    col("MES").cast("int").alias("month"),
    col("AREA").alias("area_code"),
    col("DPTO").alias("depto_code"),
    col("file_name")
)

# ============================================
# 🧠 4. STATUS
# ============================================

df_clean = df_clean.withColumn(
    "status",
    when(lower(col("file_name")).rlike("no.?ocupados|desocupados"), "desocupado")
    .when(lower(col("file_name")).rlike("ocupados"), "ocupado")
)

# ============================================
# 🧠 5. YEAR DESDE PATH
# ============================================

df_clean = df_clean.withColumn(
    "year",
    regexp_extract(col("file_name"), r"year=(\d{4})", 1).cast("int")
)

print("✅ Silver limpio listo")

# ============================================
# 💾 6. WRITE SILVER
# ============================================

df_clean.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(silver_table)

print("✅ Silver guardado")

spark.table(silver_table).show(10)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import input_file_name

df_files = spark.read \
    .format("binaryFile") \
    .option("recursiveFileLookup", "true") \
    .load("Files/raw/dane")

df_files.select("path").show(50, False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import lower

df_files = df_files.withColumn("path_lower", lower(col("path")))

df_files = df_files.withColumn(
    "file_type",
    when(col("path_lower").rlike("ocupados"), "ocupados")
    .when(col("path_lower").rlike("desocupados"), "desocupados")
    .when(col("path_lower").rlike("no.?ocupados"), "desocupados")
    .otherwise("microdata")
)

df_files.groupBy("file_type").count().show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_paths = df_files.filter(col("file_type") != "microdata")

paths = [row["path"] for row in df_paths.select("path").collect()]

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read \
    .format("csv") \
    .option("header", True) \
    .option("delimiter", ";") \
    .load(paths)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col, lower, regexp_extract

# ============================================
# 📂 LEER TODOS LOS ARCHIVOS DEL DATALAKE
# ============================================

df_files = spark.read \
    .format("binaryFile") \
    .option("recursiveFileLookup", "true") \
    .load("Files/")

print("✅ Inventario completo generado")

df_files.select("path").show(20, False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ============================================
# 🧠 EXTRAER METADATA DEL PATH
# ============================================

df_files = df_files.withColumn("path_lower", lower(col("path")))

df_files = df_files.withColumn(
    "year",
    regexp_extract(col("path"), r"year=(\d{4})", 1).cast("int")
)

df_files = df_files.withColumn(
    "month",
    regexp_extract(col("path"), r"month=(\d{2})", 1).cast("int")
)

print("✅ Metadata extraída")

df_files.select("path", "year", "month").show(20, False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import when

# ============================================
# 🧠 CLASIFICACIÓN ROBUSTA
# ============================================

df_files = df_files.withColumn(
    "file_type",
    
    # 🔴 desocupados (variantes)
    when(col("path_lower").rlike("des.?ocup|no.?ocup|desemple"), "desocupados")
    
    # 🟢 ocupados
    .when(
        (col("path_lower").rlike("ocup")) &
        (~col("path_lower").rlike("des.?ocup|no.?ocup")),
        "ocupados"
    )
    
    # 🔵 microdata (encuestas)
    .when(col("path_lower").rlike("directorio|secuencia|hogar|p[0-9]"), "microdata")
    
    # ⚫ otros
    .otherwise("otros")
)

print("✅ Clasificación completa")

df_files.groupBy("file_type").count().show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_files = df_files.withColumn(
    "file_type",
    
    # 🔴 desocupados (TODAS las variantes)
    when(col("path_lower").rlike("no.?ocup|des.?ocup"), "desocupados")
    
    # 🟢 ocupados
    .when(
        (col("path_lower").rlike("ocup")) &
        (~col("path_lower").rlike("no.?ocup|des.?ocup")),
        "ocupados"
    )
    
    # 🔵 microdata
    .when(col("path_lower").rlike("directorio|secuencia|hogar"), "microdata")
    
    # ⚫ otros datasets (ignorar)
    .otherwise("otros")
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_target = df_files.filter(
    col("file_type").isin("ocupados", "desocupados")
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_target.groupBy("year", "month", "file_type") \
    .count() \
    .orderBy("year", "month") \
    .show(200, False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DEFINIR COLUMNAS VALIOSAS

# CELL ********************

from pyspark.sql.functions import when

df_clean = df.select(
    col("MES").cast("int").alias("month"),
    col("AREA").alias("area_code"),
    col("DPTO").alias("depto_code"),
    col("file_name")
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DERIVAR STATUS

# MARKDOWN ********************

# ## SILVER 2004 CON DEPARTAMENTO

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2004
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def process_geih_2004_final(path, geo, status_label):
    try:
        # 1. Leer la primera línea para diagnosticar
        rdd = spark.sparkContext.textFile(path)
        first_line = rdd.first()
        delim = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
        parts = first_line.split(delim)
        
        # 2. ¿Tiene cabecera?
        has_header = not parts[0].isdigit()
        
        if has_header:
            # Lectura normal para los 10 meses buenos
            df = spark.read.format("csv").option("header","true").option("delimiter",delim).load(path)
            for c in df.columns: df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
            
            # Buscar columna de peso
            fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in df.columns), None)
            if not fex_col: return None
            
            # --- MODIFICACIÓN 1: Capturar DPTO si existe en la cabecera ---
            if "DPTO" in df.columns:
                df_final = df.select(
                    F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight"),
                    F.lpad(F.col("DPTO").cast("string"), 2, "0").alias("codigo_departamento")
                )
            else:
                df_final = df.select(
                    F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight"),
                    F.lit("00").alias("codigo_departamento")
                )
        else:
            # Lectura especial para Marzo y Noviembre (Sin cabecera)
            last_idx = len(parts) - 1
            data_rdd = rdd.map(lambda x: x.split(delim))
            df = data_rdd.toDF()
            
            target_col = f"_{last_idx + 1}"  # Última columna para el peso
            depto_col = "_2"                 # Segunda columna para el DPTO en la estructura fija ECH 2004
            
            # --- MODIFICACIÓN 2: Extraer DPTO usando el índice de columna fija ---
            df_final = df.select(
                F.regexp_replace(F.col(target_col), ",", ".").cast("double").alias("weight"),
                F.lpad(F.col(depto_col).cast("string"), 2, "0").alias("codigo_departamento")
            )

        # 3. Agregar metadatos
        month = int(re.search(r'month=(\d+)', path).group(1))
        return df_final.select(
            F.lit(year).alias("year"),
            F.lit(month).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo).alias("geo_source"),
            F.col("codigo_departamento"),
            F.col("weight").alias("total_weight")
        ).filter(F.col("total_weight") > 1)

    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando {year} (Extrayendo Departamentos en ECH con Marzo y Noviembre fijos)...")
    all_paths = []
    for m in range(1, 13):
        p_m = f"{bronze_path}month={m:02d}/"
        try:
            for f in mssparkutils.fs.ls(p_m): all_paths.append(f.path)
        except: pass

    final_dfs = []
    for p in all_paths:
        name_low = p.lower()
        if "area" in name_low: continue
        
        geo = "cabecera" if "cabecera" in name_low else "resto"
        status = "desocupado" if "desocupado" in name_low else ("ocupado" if "principal" in name_low else None)
        
        if status:
            res = process_geih_2004_final(p, geo, status)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]: df_silver = df_silver.unionByName(next_df)
        
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✨ ¡MISIÓN CUMPLIDA! Tabla {silver_table} con geografía integrada para los 12 meses.")
        
        # --- MODIFICACIÓN 3: Mostrar agregación desglosada por Departamento ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar ningún archivo.")
except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2005 CON DEPARTAMENTO

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2005
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def process_geih_2005_final(path, geo, status_label):
    try:
        # 1. Leer la primera línea para diagnosticar
        rdd = spark.sparkContext.textFile(path)
        first_line = rdd.first()
        delim = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
        parts = first_line.split(delim)
        
        # 2. ¿Tiene cabecera? 
        has_header = not parts[0].isdigit()
        
        if has_header:
            # Lectura normal para los 10 meses buenos
            df = spark.read.format("csv").option("header","true").option("delimiter",delim).load(path)
            for c in df.columns: df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
            
            # Buscar columna de peso
            fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in df.columns), None)
            if not fex_col: return None
            
            # --- MODIFICACIÓN 1: Capturar DPTO desde la cabecera si existe ---
            if "DPTO" in df.columns:
                df_final = df.select(
                    F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight"),
                    F.lpad(F.col("DPTO").cast("string"), 2, "0").alias("codigo_departamento")
                )
            else:
                df_final = df.select(
                    F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight"),
                    F.lit("00").alias("codigo_departamento")
                )
        else:
            # Lectura especial para Marzo y Noviembre (Sin cabecera)
            last_idx = len(parts) - 1
            data_rdd = rdd.map(lambda x: x.split(delim))
            df = data_rdd.toDF()
            
            target_col = f"_{last_idx + 1}"  # Última columna para el peso
            depto_col = "_2"                 # Segunda columna para el DPTO
            
            # --- MODIFICACIÓN 2: Extraer DPTO usando el índice de columna fija ---
            df_final = df.select(
                F.regexp_replace(F.col(target_col), ",", ".").cast("double").alias("weight"),
                F.lpad(F.col(depto_col).cast("string"), 2, "0").alias("codigo_departamento")
            )

        # 3. Agregar metadatos
        month = int(re.search(r'month=(\d+)', path).group(1))
        return df_final.select(
            F.lit(year).alias("year"),
            F.lit(month).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo).alias("geo_source"),
            F.col("codigo_departamento"),
            F.col("weight").alias("total_weight")
        ).filter(F.col("total_weight") > 1)

    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando {year} (Extrayendo Departamentos en ECH con Marzo y Noviembre fijos)...")
    all_paths = []
    for m in range(1, 13):
        p_m = f"{bronze_path}month={m:02d}/"
        try:
            for f in mssparkutils.fs.ls(p_m): all_paths.append(f.path)
        except: pass

    final_dfs = []
    for p in all_paths:
        name_low = p.lower()
        if "area" in name_low: continue
        
        geo = "cabecera" if "cabecera" in name_low else "resto"
        status = "desocupado" if "desocupado" in name_low else ("ocupado" if "principal" in name_low else None)
        
        if status:
            res = process_geih_2005_final(p, geo, status)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]: df_silver = df_silver.unionByName(next_df)
        
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✨ ¡MISIÓN CUMPLIDA! Tabla {silver_table} con geografía integrada para los 12 meses.")
        
        # --- MODIFICACIÓN 3: Mostrar agregación desglosada por Departamento ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar ningún archivo.")
except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2008 CON DEPARTAMENTO

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2008
bronze_path = f"Files/raw/dane/year={year}/"
# Guardaremos los datos en tu tabla original labor_2008
silver_table = f"dane_silver_lh.labor_{year}"

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9/._-]', ' ', text)

def process_geih_2008_master(path, geo, status_label):
    try:
        rdd = spark.sparkContext.textFile(path)
        first_line = rdd.first()
        delim = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
        parts = first_line.split(delim)
        
        has_header = not parts[0].strip().isdigit()
        
        if has_header:
            header_clean = first_line.encode('ascii', 'ignore').decode('ascii')
            header_cols = [c.upper().strip().replace('"', '') for c in header_clean.split(delim)]
            
            final_cols = []
            seen = {}
            for i, c in enumerate(header_cols):
                name = c if c != "" else f"COL_{i}"
                if name in seen:
                    seen[name] += 1
                    final_cols.append(f"{name}_{seen[name]}")
                else:
                    seen[name] = 0
                    final_cols.append(name)
            
            data_rdd = rdd.zipWithIndex().filter(lambda x: x[1] > 0).map(lambda x: x[0].split(delim))
            df = spark.createDataFrame(data_rdd, schema=final_cols)
            
            fex_col = None
            posibles = ["FEX_C_2011", "FEX_C", "PESO", "FEX"]
            for p in posibles:
                if p in df.columns:
                    fex_col = p
                    break
                    
            if not fex_col:
                if len(df.columns) > 4: fex_col = df.columns[-1]
                
            if not fex_col: return None
            
            # --- MODIFICACIÓN 1: Capturar la columna DPTO junto con el peso ---
            # Si el archivo tiene la columna DPTO, la usamos y la forzamos a 2 dígitos con lpad
            if "DPTO" in df.columns:
                df_final = df.select(
                    F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight"),
                    F.lpad(F.col("DPTO").cast("string"), 2, "0").alias("codigo_departamento")
                )
            else:
                df_final = df.select(
                    F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight"),
                    F.lit("00").alias("codigo_departamento")
                )
        else:
            last_idx = len(parts) - 1
            data_rdd = rdd.map(lambda x: x.split(delim))
            df = data_rdd.toDF()
            
            target_col = f"_{last_idx + 1}"
            df_final = df.select(
                F.regexp_replace(F.col(target_col), ",", ".").cast("double").alias("weight"),
                F.lit("00").alias("codigo_departamento")
            )

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # Agregamos codigo_departamento al dataframe final de este archivo
        return df_final.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo).alias("geo_source"),
            F.col("codigo_departamento"),
            F.col("weight").alias("total_weight")
        ).filter((F.col("total_weight").isNotNull()) & (F.col("total_weight") > 1))

    except Exception as e:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando {year} (Modo Maestro con Extracción de Departamentos)...")
    
    all_paths = []
    carpetas_mes = mssparkutils.fs.ls(bronze_path)
    for m in carpetas_mes:
        if m.isDir:
            try:
                for f in mssparkutils.fs.ls(m.path): 
                    if f.path.endswith(".txt"):
                        all_paths.append(f.path)
            except: pass

    final_dfs = []
    for p in all_paths:
        name_clean = normalize_text(p.split('/')[-1])
        if name_clean.startswith("area"): continue
        
        geo = "cabecera" if "cabecera" in name_clean else ("resto" if "resto" in name_clean else None)
        status = "desocupado" if "desocupado" in name_clean else ("ocupado" if "ocupado" in name_clean else None)
        
        if geo and status:
            res = process_geih_2008_master(p, geo, status)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]: df_silver = df_silver.unionByName(next_df)
        
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✨ ¡MISIÓN CUMPLIDA! Tabla {silver_table} corregida con geografía.")
        
        # --- MODIFICACIÓN 2: Añadir codigo_departamento al groupBy para ver el desglose en el output ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar ningún archivo. El caché de Fabric podría seguir bloqueado.")
except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Leer el archivo DIVIPOLA desde Files

# CELL ********************

from pyspark.sql.functions import col, lpad

# 1. Volvemos a leer tu archivo CSV original desde Files
df_divipola_raw = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .option("sep", ",") \
    .load("Files/davipola-departamentos/DIVIPOLA-_Códigos_municipios_20260522.csv")

# 2. Limpiamos para dejar solo códigos y nombres únicos de departamento
df_departamentos = df_divipola_raw.select(
    col("Código Departamento").alias("id_departamento"),
    col("Nombre Departamento").alias("nombre_departamento")
).distinct()

# 3. Forzamos los dos dígitos en el ID (ej: '5' -> '05')
df_departamentos = df_departamentos.withColumn(
    "id_departamento", 
    lpad(col("id_departamento").cast("string"), 2, "0")
)

# 4. ¡EL TRUCO MAESTRO!: Forzar el guardado físico directo en la carpeta de Tablas Delta
df_departamentos.write.format("delta") \
    .mode("overwrite") \
    .save("abfss://f5879c16-6832-4003-90dd-eb2c10497cc0@onelake.dfs.fabric.microsoft.com/d1606b19-cb83-4884-94c6-6c003287b794/Tables/dim_departamentos")

print("¡Hecho! dim_departamentos se guardó físicamente en las tablas de Silver.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Limpieza Técnica de la DIVIPOLA

# CELL ********************

from pyspark.sql.functions import col, lpad

# 1. Seleccionar solo las columnas de Departamento y eliminar duplicados
# Nota: Ajusta los nombres 'Código Departamento' y 'Nombre Departamento' si en tu archivo varían ligeramente
df_departamentos = df_divipola_raw.select(
    col("Código Departamento").alias("id_departamento"),
    col("Nombre Departamento").alias("nombre_departamento")
).distinct()

# 2. Truco Pro: Asegurar que el código tenga 2 dígitos (ej: '5' pasa a '05')
# Esto es vital porque el DANE a veces guarda los códigos como números y se borra el cero a la izquierda.
df_departamentos = df_departamentos.withColumn(
    "id_departamento", 
    lpad(col("id_departamento").cast("string"), 2, "0")
)

# Mostrar el resultado limpio
display(df_departamentos.orderBy("id_departamento"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## GUARDAR EN LAKEHOUSE SILVER

# CELL ********************

# Guardar la tabla limpia en la capa Silver para que esté disponible en todo el pipeline
df_departamentos.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("dim_departamentos")

print("¡Tabla dim_departamentos guardada exitosamente en Silver!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2008
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9/._-]', ' ', text)

def process_geih_2008_master(path, geo, status_label):
    try:
        # 1. Leer la primera línea de forma robusta
        rdd = spark.sparkContext.textFile(path)
        first_line = rdd.first()
        delim = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
        parts = first_line.split(delim)
        
        # 2. ¿Tiene cabecera rota o datos directos?
        has_header = not parts[0].strip().isdigit()
        
        if has_header:
            # Limpiamos la cabecera manualmente para evitar el error de columnas duplicadas
            header_clean = first_line.encode('ascii', 'ignore').decode('ascii')
            header_cols = [c.upper().strip().replace('"', '') for c in header_clean.split(delim)]
            
            final_cols = []
            seen = {}
            for i, c in enumerate(header_cols):
                name = c if c != "" else f"COL_{i}"
                if name in seen:
                    seen[name] += 1
                    final_cols.append(f"{name}_{seen[name]}")
                else:
                    seen[name] = 0
                    final_cols.append(name)
            
            data_rdd = rdd.zipWithIndex().filter(lambda x: x[1] > 0).map(lambda x: x[0].split(delim))
            df = spark.createDataFrame(data_rdd, schema=final_cols)
            
            # Buscar el peso (FEX)
            fex_col = None
            posibles = ["FEX_C_2011", "FEX_C", "PESO", "FEX"]
            for p in posibles:
                if p in df.columns:
                    fex_col = p
                    break
                    
            if not fex_col:
                if len(df.columns) > 4: fex_col = df.columns[-1] # En 2008, si falla el nombre, suele estar al final
                
            if not fex_col: return None
            
            df_final = df.select(
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight")
            )
        else:
            # Si no tiene cabecera, agarra la última columna (comportamiento típico de DANE en archivos sin cabecera)
            last_idx = len(parts) - 1
            data_rdd = rdd.map(lambda x: x.split(delim))
            df = data_rdd.toDF()
            
            target_col = f"_{last_idx + 1}"
            df_final = df.select(
                F.regexp_replace(F.col(target_col), ",", ".").cast("double").alias("weight")
            )

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df_final.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo).alias("geo_source"),
            F.col("weight").alias("total_weight")
        ).filter((F.col("total_weight").isNotNull()) & (F.col("total_weight") > 1))

    except Exception as e:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando {year} (Modo Maestro Inmune a Errores de Fabric)...")
    
    # Recolectar rutas esquivando el bug de Fabric
    all_paths = []
    carpetas_mes = mssparkutils.fs.ls(bronze_path)
    for m in carpetas_mes:
        if m.isDir:
            try:
                for f in mssparkutils.fs.ls(m.path): 
                    all_paths.append(f.path)
            except: pass

    final_dfs = []
    for p in all_paths:
        name_clean = normalize_text(p.split('/')[-1])
        
        # Ignorar las 13 ciudades
        if name_clean.startswith("area"): continue
        
        geo = "cabecera" if "cabecera" in name_clean else ("resto" if "resto" in name_clean else None)
        status = "desocupado" if "desocupado" in name_clean else ("ocupado" if "ocupado" in name_clean else None)
        
        if geo and status:
            res = process_geih_2008_master(p, geo, status)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]: df_silver = df_silver.unionByName(next_df)
        
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✨ ¡MISIÓN CUMPLIDA! Tabla {silver_table} corregida.")
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar ningún archivo. El caché de Fabric podría seguir bloqueado.")
except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2004
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def process_geih_2004_final(path, geo, status_label):
    try:
        # 1. Leer la primera línea para diagnosticar
        rdd = spark.sparkContext.textFile(path)
        first_line = rdd.first()
        delim = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
        parts = first_line.split(delim)
        
        # 2. ¿Tiene cabecera? 
        # Si la primera columna es un número (60, 70), es DATA, no CABECERA.
        has_header = not parts[0].isdigit()
        
        if has_header:
            # Lectura normal para los 10 meses buenos
            df = spark.read.format("csv").option("header","true").option("delimiter",delim).load(path)
            for c in df.columns: df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
            
            # Buscar columna de peso
            fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in df.columns), None)
            if not fex_col: return None
            
            df_final = df.select(
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight")
            )
        else:
            # Lectura especial para Marzo y Noviembre (Sin cabecera)
            # El peso está en la ÚLTIMA columna (visto en la radiografía)
            last_idx = len(parts) - 1
            data_rdd = rdd.map(lambda x: x.split(delim))
            df = data_rdd.toDF()
            
            target_col = f"_{last_idx + 1}"
            df_final = df.select(
                F.regexp_replace(F.col(target_col), ",", ".").cast("double").alias("weight")
            )

        # 3. Agregar metadatos
        month = int(re.search(r'month=(\d+)', path).group(1))
        return df_final.select(
            F.lit(year).alias("year"),
            F.lit(month).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo).alias("geo_source"),
            F.col("weight").alias("total_weight")
        ).filter(F.col("total_weight") > 1)

    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando {year} (Corrigiendo Marzo y Noviembre sin cabecera)...")
    all_paths = []
    for m in range(1, 13):
        p_m = f"{bronze_path}month={m:02d}/"
        try:
            for f in mssparkutils.fs.ls(p_m): all_paths.append(f.path)
        except: pass

    final_dfs = []
    for p in all_paths:
        name_low = p.lower()
        if "area" in name_low: continue
        
        geo = "cabecera" if "cabecera" in name_low else "resto"
        status = "desocupado" if "desocupado" in name_low else ("ocupado" if "principal" in name_low else None)
        
        if status:
            res = process_geih_2004_final(p, geo, status)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]: df_silver = df_silver.unionByName(next_df)
        
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✨ ¡MISIÓN CUMPLIDA! Tabla {silver_table} con los 12 meses perfectos.")
        df_silver.groupBy("month", "status").agg(F.sum("total_weight")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar ningún archivo.")
except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2005
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def process_geih_2005_final(path, geo, status_label):
    try:
        # 1. Leer la primera línea para diagnosticar
        rdd = spark.sparkContext.textFile(path)
        first_line = rdd.first()
        delim = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
        parts = first_line.split(delim)
        
        # 2. ¿Tiene cabecera? 
        # Si la primera columna es un número (60, 70), es DATA, no CABECERA.
        has_header = not parts[0].isdigit()
        
        if has_header:
            # Lectura normal para los 10 meses buenos
            df = spark.read.format("csv").option("header","true").option("delimiter",delim).load(path)
            for c in df.columns: df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
            
            # Buscar columna de peso
            fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in df.columns), None)
            if not fex_col: return None
            
            df_final = df.select(
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight")
            )
        else:
            # Lectura especial para Marzo y Noviembre (Sin cabecera)
            # El peso está en la ÚLTIMA columna (visto en la radiografía)
            last_idx = len(parts) - 1
            data_rdd = rdd.map(lambda x: x.split(delim))
            df = data_rdd.toDF()
            
            target_col = f"_{last_idx + 1}"
            df_final = df.select(
                F.regexp_replace(F.col(target_col), ",", ".").cast("double").alias("weight")
            )

        # 3. Agregar metadatos
        month = int(re.search(r'month=(\d+)', path).group(1))
        return df_final.select(
            F.lit(year).alias("year"),
            F.lit(month).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo).alias("geo_source"),
            F.col("weight").alias("total_weight")
        ).filter(F.col("total_weight") > 1)

    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando {year} (Corrigiendo Marzo y Noviembre sin cabecera)...")
    all_paths = []
    for m in range(1, 13):
        p_m = f"{bronze_path}month={m:02d}/"
        try:
            for f in mssparkutils.fs.ls(p_m): all_paths.append(f.path)
        except: pass

    final_dfs = []
    for p in all_paths:
        name_low = p.lower()
        if "area" in name_low: continue
        
        geo = "cabecera" if "cabecera" in name_low else "resto"
        status = "desocupado" if "desocupado" in name_low else ("ocupado" if "principal" in name_low else None)
        
        if status:
            res = process_geih_2005_final(p, geo, status)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]: df_silver = df_silver.unionByName(next_df)
        
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✨ ¡MISIÓN CUMPLIDA! Tabla {silver_table} con los 12 meses perfectos.")
        df_silver.groupBy("month", "status").agg(F.sum("total_weight")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar ningún archivo.")
except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2005
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2005(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2005(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2004
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def normalize_diag(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9/._-]', ' ', text)

def read_geih_2004(path, geo_source, status_label):
    try:
        # En 2004 el separador suele ser TAB o COMA
        df = spark.read.format("csv").option("header","true").option("delimiter","\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header","true").option("delimiter",",").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        # El peso detectado en tu auditoría fue FEX_C_2011
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in df.columns), None)
        if not fex_col: return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

try:
    print(f"🚀 Procesando Total Nacional {year} (Ene-Jun)...")
    
    # Listar archivos de los meses disponibles
    all_paths = []
    for m in range(1, 13): # Solo meses 1 al 6
        path_month = f"{bronze_path}month={m:02d}/"
        try:
            for f in mssparkutils.fs.ls(path_month):
                all_paths.append(f.path)
        except: pass
    
    final_dfs = []
    for p in all_paths:
        nombre = p.split('/')[-1]
        p_clean = normalize_diag(nombre)
        
        # 1. Ignorar carpetas de AREA (duplicidad)
        if p_clean.startswith("area"): continue
        
        geo = "cabecera" if "cabecera" in p_clean else ("resto" if "resto" in p_clean else None)
        if not geo: continue

        # 2. SELECCIÓN QUIRÚRGICA: 
        # Solo Desocupados y Ocupados-Principal para evitar el conteo triple.
        target_file = False
        status = None
        
        if "desocupado" in p_clean:
            target_file = True
            status = "desocupado"
        elif "ocupado" in p_clean and "principal" in p_clean:
            target_file = True
            status = "ocupado"
            
        if target_file:
            res = read_geih_2004(p, geo, status)
            if res:
                final_dfs.append(res)
                print(f"✅ Cargado: {geo.upper()} -> {nombre}")

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"\n📊 TOTAL NACIONAL {year} SIN DUPLICADOS:")
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show()
    else:
        print("❌ No se encontró data para procesar.")

except Exception as e:
    print(f"❌ Error: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

year = 2005
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def normalize_diag(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9/._-]', ' ', text)

def read_geih_2005_extreme(path, geo_source, status_label):
    try:
        # 1. Leemos el archivo como texto plano para evitar el error de columnas duplicadas
        rdd = spark.sparkContext.textFile(path)
        header_raw = rdd.first()
        
        # Detectar delimitador
        delim = "\t" if "\t" in header_raw else (";" if ";" in header_raw else ",")
        
        # Limpiar la cabecera manualmente
        header_cols = [c.upper().strip().replace('"', '') for c in header_raw.split(delim)]
        
        # Corregir nombres duplicados en la lista de columnas
        seen = {}
        final_cols = []
        for c in header_cols:
            if c == "" or c in seen:
                seen[c] = seen.get(c, 0) + 1
                final_cols.append(f"{c}_{seen[c]}")
            else:
                seen[c] = 0
                final_cols.append(c)
        
        # 2. Cargar la data saltando la primera línea (cabecera corrupta)
        data_rdd = rdd.zipWithIndex().filter(lambda x: x[1] > 0).map(lambda x: x[0].split(delim))
        
        # Crear DataFrame con las columnas limpias
        df = spark.createDataFrame(data_rdd, schema=final_cols)
        
        # 3. Buscar la columna de PESO (FEX)
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO", "FEX"] if c in df.columns), None)
        if not fex_col: return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

try:
    print(f"🚀 Procesando Total Nacional {year} (Modo Super-Robusto)...")
    
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        nombre = p.split('/')[-1]
        p_clean = normalize_diag(nombre)
        
        if p_clean.startswith("area"): continue
        
        geo = "cabecera" if "cabecera" in p_clean else ("resto" if "resto" in p_clean else None)
        if not geo: continue

        status = "desocupado" if "desocupado" in p_clean else ("ocupado" if "ocupado" in p_clean and "principal" in p_clean else None)
            
        if status:
            res = read_geih_2005_extreme(p, geo, status)
            if res:
                final_dfs.append(res)
                # print(f"✅ Cargado: {nombre}")

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA {silver_table} COMPLETADA (12 MESES).")
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data de ningún mes.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2006
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def normalize_diag(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9/._-]', ' ', text)

def read_geih_2006(path, geo_source, status_label):
    try:
        # En 2006 el separador suele ser TAB o COMA
        df = spark.read.format("csv").option("header","true").option("delimiter","\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header","true").option("delimiter",",").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        # El peso detectado en tu auditoría fue FEX_C_2011
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in df.columns), None)
        if not fex_col: return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

try:
    print(f"🚀 Procesando Total Nacional {year} (Ene-Jun)...")
    
    # Listar archivos de los meses disponibles
    all_paths = []
    for m in range(1, 7): # Solo meses 1 al 6
        path_month = f"{bronze_path}month={m:02d}/"
        try:
            for f in mssparkutils.fs.ls(path_month):
                all_paths.append(f.path)
        except: pass
    
    final_dfs = []
    for p in all_paths:
        nombre = p.split('/')[-1]
        p_clean = normalize_diag(nombre)
        
        # 1. Ignorar carpetas de AREA (duplicidad)
        if p_clean.startswith("area"): continue
        
        geo = "cabecera" if "cabecera" in p_clean else ("resto" if "resto" in p_clean else None)
        if not geo: continue

        # 2. SELECCIÓN QUIRÚRGICA: 
        # Solo Desocupados y Ocupados-Principal para evitar el conteo triple.
        target_file = False
        status = None
        
        if "desocupado" in p_clean:
            target_file = True
            status = "desocupado"
        elif "ocupado" in p_clean and "principal" in p_clean:
            target_file = True
            status = "ocupado"
            
        if target_file:
            res = read_geih_2006(p, geo, status)
            if res:
                final_dfs.append(res)
                print(f"✅ Cargado: {geo.upper()} -> {nombre}")

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"\n📊 TOTAL NACIONAL {year} SIN DUPLICADOS:")
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show()
    else:
        print("❌ No se encontró data para procesar.")

except Exception as e:
    print(f"❌ Error: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2006 CON DEPARTAMENTOS

# CELL ********************

import re
import unicodedata
from pyspark.sql import functions as F

year = 2006
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def normalize_diag(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9/._-]', ' ', text)

def cargar_modulo_dane(path):
    try:
        df = spark.read.format("csv").option("header","true").option("delimiter","\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header","true").option("delimiter",",").load(path)
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        return df
    except:
        return None

try:
    print(f"🚀 Iniciando Procesamiento Final {year} con Homologación DIVIPOLA Oficial...")
    
    final_dfs = []
    
    # Diccionario de traducción ECH -> DIVIPOLA
    # Mapea el índice interno del DANE al código de departamento real de Colombia
    divipola_map = {
        "01": "05", "02": "08", "03": "11", "04": "13", "05": "15",
        "06": "17", "07": "23", "08": "25", "09": "41", "10": "47",
        "11": "52", "12": "54", "13": "66", "14": "68", "15": "76"
    }
    # Convertimos a formato Spark literal para mapeo eficiente
    spark_map_expr = F.create_map([F.lit(x) for x in sum(divipola_map.items(), ())])
    
    for m in range(1, 7):
        path_month = f"{bronze_path}month={m:02d}/"
        print(f"📅 Procesando Mes {m:02d}...")
        
        try:
            archivos_mes = mssparkutils.fs.ls(path_month)
        except:
            continue
            
        for geo_zona in ["cabecera", "resto"]:
            file_cg = next((f.path for f in archivos_mes if geo_zona in normalize_diag(f.name) and "caracteristicas" in normalize_diag(f.name)), None)
            if not file_cg: continue
                
            df_cg = cargar_modulo_dane(file_cg)
            if not df_cg: continue
                
            col_geografica = "P3" if "P3" in df_cg.columns else ("DPTO" if "DPTO" in df_cg.columns else None)
            if not col_geografica or "LLAVE_VIV" not in df_cg.columns: continue
                
            df_geo_map = df_cg.select(
                F.col("LLAVE_VIV"), 
                F.lpad(F.col(col_geografica).cast("string"), 2, "0").alias("ech_dpto")
            ).distinct()
            
            for status_label in ["desocupado", "ocupado"]:
                file_empleo = None
                if status_label == "desocupado":
                    file_empleo = next((f.path for f in archivos_mes if geo_zona in normalize_diag(f.name) and "desocupados" in normalize_diag(f.name)), None)
                else:
                    file_empleo = next((f.path for f in archivos_mes if geo_zona in normalize_diag(f.name) and "ocupados" in normalize_diag(f.name) and "principal" in normalize_diag(f.name)), None)
                    
                if not file_empleo: continue
                    
                df_emp = cargar_modulo_dane(file_empleo)
                if not df_emp or "LLAVE_VIV" not in df_emp.columns: continue
                    
                fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in df_emp.columns), None)
                if not fex_col: continue
                    
                df_emp_clean = df_emp.select(
                    F.col("LLAVE_VIV"),
                    F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_enriquecido = df_emp_clean.join(df_geo_map, "LLAVE_VIV", "inner")
                
                df_final_modulo = df_enriquecido.select(
                    F.lit(year).alias("year"),
                    F.lit(m).alias("month"),
                    F.lit(status_label).alias("status"),
                    F.lit(geo_zona).alias("geo_source"),
                    # Aplicamos la traducción y si no encuentra el código, conserva el original por seguridad
                    F.coalesce(spark_map_expr[F.col("ech_dpto")], F.col("ech_dpto")).alias("codigo_departamento"),
                    F.col("total_weight")
                )
                
                final_dfs.append(df_final_modulo)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"\n📊 🌟 ¡SÚPER MISIÓN CUMPLIDA! Capa Silver de {year} estandarizada con DIVIPOLA:")
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(20)
    else:
        print("❌ No se pudo enlazar la información.")

except Exception as e:
    print(f"❌ Error crítico en el pipeline: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2007
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2007(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2007(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2007 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2007
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2007(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        p_low = path.lower()
        if "desocupado" in p_low:
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # --- MODIFICACIÓN: Captura y estandarización de la columna DPTO ---
        if "DPTO" in df.columns:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lpad(F.col("DPTO").cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de contingencia por si el DANE cambia el nombre de la columna en algún mes
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
            
        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} con Extracción Geográfica Integrada...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2007(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA CON GEOGRAFÍA: {silver_table}")
        print("-" * 60)
        
        # --- MODIFICACIÓN: Mostrar resumen desglosado por Departamento para auditoría ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2008
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2008(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2008(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2009
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2009(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2009(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2009 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2009
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2009(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        p_low = path.lower()
        if "desocupado" in p_low:
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # --- MODIFICACIÓN CLAVE: Tolerancia a variantes de nombres de columnas del DANE ---
        # El DANE a veces usa DPTO y otras COD_DPTO según el mes o módulo en 2009
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de contingencia por si llega a faltar en algún archivo específico
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
            
        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} con Extracción de Geografía Dinámica...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2009(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA CON ÉXITO: {silver_table}")
        print("-" * 60)
        
        # --- MODIFICACIÓN: Mostrar agregación desglosada por Departamento ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2010 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2010
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2010(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        p_low = path.lower()
        if "desocupado" in p_low:
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # --- BLINDAJE GEOGRÁFICO: Buscar variantes comunes de la columna de departamento ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de contingencia por si algún mes o zona viene huérfano
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
            
        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} con Extracción de Geografía Dinámica...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2010(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA CON ÉXITO: {silver_table}")
        print("-" * 60)
        
        # --- RESUMEN DE CONTROL: Agregación desglosada por departamento ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2010
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2010(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2010(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2011 CON DEPARTAMENTOS

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2011
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2011(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        p_low = path.lower()
        if "desocupado" in p_low:
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # --- BLINDAJE GEOGRÁFICO DINÁMICO ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de escape preventivo por si algún mes se desalinea
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
            
        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} con Extracción de Geografía Dinámica y FEX_C_2011...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2011(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA CON ÉXITO: {silver_table}")
        print("-" * 60)
        
        # --- AGREGACIÓN DE CONTROL DESGLOSADA ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2011
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2011(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2011(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2012 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2012
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2012(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        p_low = path.lower()
        if "desocupado" in p_low:
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # --- BLINDAJE GEOGRÁFICO DINÁMICO ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan preventivo por si las moscas
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
            
        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} con Extracción Geográfica Dinámica...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2012(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA CON ÉXITO: {silver_table}")
        print("-" * 60)
        
        # --- RESUMEN DE CONTROL TERRITORIAL ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2012
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2012(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2012(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2013 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2013
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2013(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        p_low = path.lower()
        if "desocupado" in p_low:
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # --- BLINDAJE GEOGRÁFICO DINÁMICO ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de respaldo por si el DANE se pone creativo en algún mes
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
            
        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} con Extracción Geográfica Dinámica...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2013(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA CON ÉXITO: {silver_table}")
        print("-" * 60)
        
        # --- RESUMEN DE CONTROL GEOGRÁFICO ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2013
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2013(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2013(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2014
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2014(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        p_low = path.lower()
        if "desocupado" in p_low:
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        # --- BLINDAJE GEOGRÁFICO DINÁMICO ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de contingencia por si las moscas
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(status_label).alias("status"),
                F.lit(geo_source).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
            
        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} con Extracción Geográfica Dinámica...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2014(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA CON ÉXITO: {silver_table}")
        print("-" * 60)
        
        # --- RESUMEN DE CONTROL GEOGRÁFICO ---
        df_silver.groupBy("month", "codigo_departamento", "status") \
            .agg(F.sum("total_weight").alias("total")) \
            .orderBy("month", "codigo_departamento", "status") \
            .show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2014
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

def read_geih_2014(path, geo_source):
    try:
        df = spark.read.format("csv").option("header", "true").option("delimiter", "\t").load(path)
        if len(df.columns) <= 1:
            df = spark.read.format("csv").option("header", "true").option("delimiter", ";").load(path)
        
        for c in df.columns:
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None

        # --- CORRECCIÓN DE LÓGICA AQUÍ ---
        p_low = path.lower()
        if "desocupado" in p_low: # Priorizamos 'desocupado' para evitar falsos positivos
            status_label = "desocupado"
        elif "ocupado" in p_low:
            status_label = "ocupado"
        else:
            return None

        month_match = re.search(r'month=(\d+)', path)
        month_val = int(month_match.group(1)) if month_match else 0
        
        return df.select(
            F.lit(year).alias("year"),
            F.lit(month_val).alias("month"),
            F.lit(status_label).alias("status"),
            F.lit(geo_source).alias("geo_source"),
            F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
        ).filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- EJECUCIÓN ---
try:
    print(f"🚀 Procesando Total Nacional {year} (Corrigiendo categorías)...")
    
    # Obtener lista de archivos
    all_paths = []
    for m in mssparkutils.fs.ls(bronze_path):
        if m.isDir:
            for f in mssparkutils.fs.ls(m.path):
                all_paths.append(f.path)
    
    final_dfs = []
    for p in all_paths:
        p_low = p.lower()
        if "area" in p_low: continue
        
        geo = "cabecera" if "cabecera" in p_low else ("resto" if "resto" in p_low else None)
        
        if geo and ("ocupado" in p_low or "desocupado" in p_low):
            res = read_geih_2014(p, geo)
            if res:
                final_dfs.append(res)

    if final_dfs:
        df_silver = final_dfs[0]
        for next_df in final_dfs[1:]:
            df_silver = df_silver.unionByName(next_df)
            
        spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
        df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
        
        print(f"✅ TABLA ACTUALIZADA: {silver_table}")
        print("-" * 60)
        # Mostrar resumen con ambas categorías
        df_silver.groupBy("month", "status").agg(F.sum("total_weight").alias("total")).orderBy("month", "status").show(40)
    else:
        print("❌ Error: No se pudo cargar data.")

except Exception as e:
    print(f"❌ Error crítico: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2015 CON DEPARTAMENTOS

# CELL ********************

import re
import os
from pyspark.sql import functions as F

year = 2015
bronze_path = f"Files/raw/dane/year={year}/" 
silver_table = f"dane_silver_lh.labor_{year}"

def read_exact_file(path, label, geo):
    try:
        # Detección de delimitador para .txt
        raw_head = spark.read.text(path).limit(1).collect()[0]['value']
        delim = "\t" if "\t" in raw_head else (";" if ";" in raw_head else ",")
        
        df = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(path)
        for c in df.columns: 
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        # Buscamos el Peso (FEX)
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None
        
        month_val = int(path.split("month=")[1].split("/")[0])
        
        # --- BLINDAJE GEOGRÁFICO DINÁMICO ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(label).alias("status"),
                F.lit(geo).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de contingencia regional
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(label).alias("status"),
                F.lit(geo).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )

        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- ESCANEO RESTRINGIDO Y BLINDADO CONTRA TILDES ---
def get_files_recursively(path):
    files = []
    for i in mssparkutils.fs.ls(path):
        if i.isDir: files.extend(get_files_recursively(i.path))
        else: files.append(i.path)
    return files

all_paths = get_files_recursively(bronze_path)
final_dfs = []

print("🚀 Procesando estrictamente Ocupados y Desocupados con Geografía Dinámica (2015)...")

for p in all_paths:
    p_clean = p.lower()
    p_clean = re.sub(r'[áàäâ]', 'a', p_clean)
    p_clean = re.sub(r'[éèëê]', 'e', p_clean)
    p_clean = re.sub(r'[íìïî]', 'i', p_clean)
    p_clean = re.sub(r'[óòöô]', 'o', p_clean)
    p_clean = re.sub(r'[úùüû]', 'u', p_clean)

    if not any(x in p_clean for x in ["cabecera", "resto"]): continue
    if "area" in p_clean: continue 
    
    status = None
    if "desocupado" in p_clean:
        status = "desocupado"
    elif "ocupado" in p_clean:
        status = "ocupado"
    
    if status:
        geo = "cabecera" if "cabecera" in p_clean else "resto"
        res = read_exact_file(p, status, geo)
        if res: 
            final_dfs.append(res)

if final_dfs:
    df_silver = final_dfs[0]
    for next_df in final_dfs[1:]:
        df_silver = df_silver.unionByName(next_df)
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print("\n✅ SILVER 2015 NORMALIZADO, ENRIQUECIDO Y VALIDADO")
    print("-" * 60)
    df_silver.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ No se encontraron los archivos de Ocupados o Desocupados. Revisa las rutas de origen.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

## ============================================================================
## 🎯 SILVER 2015: FILTRO EXCLUSIVO (SOLO OCUPADOS Y DESOCUPADOS)
## ============================================================================
from pyspark.sql import functions as F

year = 2015
bronze_path = f"Files/raw/dane/year={year}/" 
silver_table = f"dane_silver_lh.labor_{year}"

def read_exact_file(path, label, geo):
    # Detección de delimitador para .txt
    raw_head = spark.read.text(path).limit(1).collect()[0]['value']
    delim = "\t" if "\t" in raw_head else (";" if ";" in raw_head else ",")
    
    df = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(path)
    for c in df.columns: df = df.withColumnRenamed(c, c.upper().strip())
    
    # Buscamos el Peso (FEX)
    cols = df.columns
    fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
    if not fex_col: return None
    
    month_val = int(path.split("month=")[1].split("/")[0])

    return df.select(
        F.lit(year).alias("year"),
        F.lit(month_val).alias("month"),
        F.lit(label).alias("status"),
        F.lit(geo).alias("geo_source"),
        F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight")
    ).filter(F.col("weight").isNotNull())

# --- ESCANEO RESTRINGIDO Y BLINDADO CONTRA TILDES ---
import os
import re

def get_files_recursively(path):
    files = []
    for i in mssparkutils.fs.ls(path):
        if i.isDir: files.extend(get_files_recursively(i.path))
        else: files.append(i.path)
    return files

all_paths = get_files_recursively(bronze_path)
final_dfs = []

print("🚀 Procesando estrictamente Ocupados y Desocupados (Versión Inmune a Tildes)...")

for p in all_paths:
    # 1. Normalizar el path: pasar a minúsculas y limpiar caracteres rotos o tildes comunes
    p_clean = p.lower()
    # Reemplazamos las vocales con tilde y el caracter raro de interrogación de Windows ()
    p_clean = re.sub(r'[áàäâ]', 'a', p_clean)
    p_clean = re.sub(r'[éèëê]', 'e', p_clean)
    p_clean = re.sub(r'[íìïî]', 'i', p_clean)
    p_clean = re.sub(r'[óòöô]', 'o', p_clean)
    p_clean = re.sub(r'[úùüû]', 'u', p_clean)
    p_clean = p_clean.replace("", "") # Borra el rombo con signo de pregunta si aparece

    # 2. REGLA DE ORO: Solo Cabecera y Resto (Evitamos "area" para no duplicar datos)
    if not any(x in p_clean for x in ["cabecera", "resto"]): continue
    if "area" in p_clean: continue 
    
    # 3. FILTRO FLEXIBLE: Detectar si contiene "ocupado" o "desocupado" sin importar lo que tenga al lado
    status = None
    if "desocupado" in p_clean:
        status = "desocupado"
    elif "ocupado" in p_clean:
        status = "ocupado"
    
    if status:
        geo = "cabecera" if "cabecera" in p_clean else "resto"
        res = read_exact_file(p, status, geo) # Le pasamos el path original 'p' para que no falle la lectura física
        if res: 
            final_dfs.append(res)
            print(p) # Agregamos un log para ver exactamente qué archivo mapeó exitosamente

if final_dfs:
    df_silver = final_dfs[0]
    for next_df in final_dfs[1:]:
        df_silver = df_silver.unionByName(next_df)
    
    df_silver = df_silver.withColumn("is_national_total", F.lit(True))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print("\n✅ SILVER 2015 NORMALIZADO Y VALIDADO")
    df_silver.groupBy("month", "status").agg(F.sum("weight").alias("total_weight")).orderBy("month", "status").show()
else:
    print("❌ No se encontraron los archivos de Ocupados o Desocupados. Revisa las rutas de origen.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2016 CON DEPARTAMENTOS

# CELL ********************

import re
import os
from pyspark.sql import functions as F

year = 2016
bronze_path = f"Files/raw/dane/year={year}/" 
silver_table = f"dane_silver_lh.labor_{year}"

def read_exact_file(path, label, geo):
    try:
        # Detección de delimitador para .txt
        raw_head = spark.read.text(path).limit(1).collect()[0]['value']
        delim = "\t" if "\t" in raw_head else (";" if ";" in raw_head else ",")
        
        df = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(path)
        for c in df.columns: 
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        # Buscamos el Peso (FEX)
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None
        
        month_val = int(path.split("month=")[1].split("/")[0])
        
        # --- BLINDAJE GEOGRÁFICO DINÁMICO ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(label).alias("status"),
                F.lit(geo).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de contingencia regional por seguridad
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(label).alias("status"),
                F.lit(geo).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )

        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- ESCANEO RESTRINGIDO Y BLINDADO CONTRA TILDES ---
def get_files_recursively(path):
    files = []
    for i in mssparkutils.fs.ls(path):
        if i.isDir: files.extend(get_files_recursively(i.path))
        else: files.append(i.path)
    return files

all_paths = get_files_recursively(bronze_path)
final_dfs = []

print("🚀 Procesando estrictamente Ocupados y Desocupados con Geografía Dinámica (2016)...")

for p in all_paths:
    p_clean = p.lower()
    p_clean = re.sub(r'[áàäâ]', 'a', p_clean)
    p_clean = re.sub(r'[éèëê]', 'e', p_clean)
    p_clean = re.sub(r'[íìïî]', 'i', p_clean)
    p_clean = re.sub(r'[óòöô]', 'o', p_clean)
    p_clean = re.sub(r'[úùüû]', 'u', p_clean)

    if not any(x in p_clean for x in ["cabecera", "resto"]): continue
    if "area" in p_clean: continue 
    
    status = None
    if "desocupado" in p_clean:
        status = "desocupado"
    elif "ocupado" in p_clean:
        status = "ocupado"
    
    if status:
        geo = "cabecera" if "cabecera" in p_clean else "resto"
        res = read_exact_file(p, status, geo)
        if res: 
            final_dfs.append(res)

if final_dfs:
    df_silver = final_dfs[0]
    for next_df in final_dfs[1:]:
        df_silver = df_silver.unionByName(next_df)
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print("\n✅ SILVER 2016 NORMALIZADO, ENRIQUECIDO Y VALIDADO")
    print("-" * 60)
    df_silver.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ No se encontraron los archivos de Ocupados o Desocupados. Revisa las rutas de origen.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

## ============================================================================
## 🎯 SILVER 2016: FILTRO EXCLUSIVO (SOLO OCUPADOS Y DESOCUPADOS)
## ============================================================================
from pyspark.sql import functions as F

year = 2016
bronze_path = f"Files/raw/dane/year={year}/" 
silver_table = f"dane_silver_lh.labor_{year}"

def read_exact_file(path, label, geo):
    # Detección de delimitador para .txt
    raw_head = spark.read.text(path).limit(1).collect()[0]['value']
    delim = "\t" if "\t" in raw_head else (";" if ";" in raw_head else ",")
    
    df = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(path)
    for c in df.columns: df = df.withColumnRenamed(c, c.upper().strip())
    
    # Buscamos el Peso (FEX)
    cols = df.columns
    fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
    if not fex_col: return None
    
    month_val = int(path.split("month=")[1].split("/")[0])

    return df.select(
        F.lit(year).alias("year"),
        F.lit(month_val).alias("month"),
        F.lit(label).alias("status"),
        F.lit(geo).alias("geo_source"),
        F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight")
    ).filter(F.col("weight").isNotNull())

# --- ESCANEO RESTRINGIDO Y BLINDADO CONTRA TILDES ---
import os
import re

def get_files_recursively(path):
    files = []
    for i in mssparkutils.fs.ls(path):
        if i.isDir: files.extend(get_files_recursively(i.path))
        else: files.append(i.path)
    return files

all_paths = get_files_recursively(bronze_path)
final_dfs = []

print("🚀 Procesando estrictamente Ocupados y Desocupados (Versión Inmune a Tildes)...")

for p in all_paths:
    # 1. Normalizar el path: pasar a minúsculas y limpiar caracteres rotos o tildes comunes
    p_clean = p.lower()
    # Reemplazamos las vocales con tilde y el caracter raro de interrogación de Windows ()
    p_clean = re.sub(r'[áàäâ]', 'a', p_clean)
    p_clean = re.sub(r'[éèëê]', 'e', p_clean)
    p_clean = re.sub(r'[íìïî]', 'i', p_clean)
    p_clean = re.sub(r'[óòöô]', 'o', p_clean)
    p_clean = re.sub(r'[úùüû]', 'u', p_clean)
    p_clean = p_clean.replace("", "") # Borra el rombo con signo de pregunta si aparece

    # 2. REGLA DE ORO: Solo Cabecera y Resto (Evitamos "area" para no duplicar datos)
    if not any(x in p_clean for x in ["cabecera", "resto"]): continue
    if "area" in p_clean: continue 
    
    # 3. FILTRO FLEXIBLE: Detectar si contiene "ocupado" o "desocupado" sin importar lo que tenga al lado
    status = None
    if "desocupado" in p_clean:
        status = "desocupado"
    elif "ocupado" in p_clean:
        status = "ocupado"
    
    if status:
        geo = "cabecera" if "cabecera" in p_clean else "resto"
        res = read_exact_file(p, status, geo) # Le pasamos el path original 'p' para que no falle la lectura física
        if res: 
            final_dfs.append(res)
            print(p) # Agregamos un log para ver exactamente qué archivo mapeó exitosamente

if final_dfs:
    df_silver = final_dfs[0]
    for next_df in final_dfs[1:]:
        df_silver = df_silver.unionByName(next_df)
    
    df_silver = df_silver.withColumn("is_national_total", F.lit(True))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print("\n✅ SILVER 2016 NORMALIZADO Y VALIDADO")
    df_silver.groupBy("month", "status").agg(F.sum("weight").alias("total_weight")).orderBy("month", "status").show()
else:
    print("❌ No se encontraron los archivos de Ocupados o Desocupados. Revisa las rutas de origen.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2017 CON DEPARTAMENTOS

# CELL ********************

import re
import os
from pyspark.sql import functions as F

year = 2017
bronze_path = f"Files/raw/dane/year={year}/" 
silver_table = f"dane_silver_lh.labor_{year}"

def read_exact_file(path, label, geo):
    try:
        # Detección de delimitador para .txt
        raw_head = spark.read.text(path).limit(1).collect()[0]['value']
        delim = "\t" if "\t" in raw_head else (";" if ";" in raw_head else ",")
        
        df = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(path)
        for c in df.columns: 
            df = df.withColumnRenamed(c, c.upper().strip().replace('"', ''))
        
        # Buscamos el Peso (FEX)
        cols = df.columns
        fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
        if not fex_col: return None
        
        month_val = int(path.split("month=")[1].split("/")[0])
        
        # --- BLINDAJE GEOGRÁFICO DINÁMICO ---
        target_depto_col = next((c for c in ["DPTO", "COD_DPTO"] if c in df.columns), None)
        
        if target_depto_col:
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(label).alias("status"),
                F.lit(geo).alias("geo_source"),
                F.lpad(F.col(target_depto_col).cast("string"), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )
        else:
            # Plan de contingencia regional
            df_final = df.select(
                F.lit(year).alias("year"),
                F.lit(month_val).alias("month"),
                F.lit(label).alias("status"),
                F.lit(geo).alias("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("total_weight")
            )

        return df_final.filter(F.col("total_weight").isNotNull())
    except:
        return None

# --- ESCANEO RESTRINGIDO CON ADAPTACIÓN DE FILTROS ---
def get_files_recursively(path):
    files = []
    for i in mssparkutils.fs.ls(path):
        if i.isDir: files.extend(get_files_recursively(i.path))
        else: files.append(i.path)
    return files

all_paths = get_files_recursively(bronze_path)
final_dfs = []

print("🚀 Procesando Ocupados y Desocupados con Inyección Geográfica Dinámica (2017)...")

for p in all_paths:
    p_low = p.lower()
    
    # REGLA DE ORO: Solo Cabecera y Resto
    if not any(x in p_low for x in ["cabecera", "resto"]): continue
    if "area" in p_low: continue 
    
    # Filtro flexible para evitar que el DANE nos engañe con el plural/singular o guiones
    status = None
    if "desocupado" in p_low:
        status = "desocupado"
    elif "ocupado" in p_low:
        status = "ocupado"
    
    if status:
        geo = "cabecera" if "cabecera" in p_low else "resto"
        res = read_exact_file(p, status, geo)
        if res: final_dfs.append(res)

if final_dfs:
    df_silver = final_dfs[0]
    for next_df in final_dfs[1:]:
        df_silver = df_silver.unionByName(next_df)
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print("\n✅ SILVER 2017 NORMALIZADO, ENRIQUECIDO Y VALIDADO")
    print("-" * 60)
    df_silver.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ No se encontraron los archivos de Ocupados o Desocupados.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

## ============================================================================
## 🎯 SILVER 2017: FILTRO EXCLUSIVO (SOLO OCUPADOS Y DESOCUPADOS)
## ============================================================================
from pyspark.sql import functions as F

year = 2017
bronze_path = f"Files/raw/dane/year={year}/" 
silver_table = f"dane_silver_lh.labor_{year}"

def read_exact_file(path, label, geo):
    # Detección de delimitador para .txt
    raw_head = spark.read.text(path).limit(1).collect()[0]['value']
    delim = "\t" if "\t" in raw_head else (";" if ";" in raw_head else ",")
    
    df = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(path)
    for c in df.columns: df = df.withColumnRenamed(c, c.upper().strip())
    
    # Buscamos el Peso (FEX)
    cols = df.columns
    fex_col = next((c for c in ["FEX_C_2011", "FEX_C", "PESO"] if c in cols), None)
    if not fex_col: return None
    
    month_val = int(path.split("month=")[1].split("/")[0])

    return df.select(
        F.lit(year).alias("year"),
        F.lit(month_val).alias("month"),
        F.lit(label).alias("status"),
        F.lit(geo).alias("geo_source"),
        F.regexp_replace(F.col(fex_col), ",", ".").cast("double").alias("weight")
    ).filter(F.col("weight").isNotNull())

# --- ESCANEO RESTRINGIDO ---
import os
def get_files_recursively(path):
    files = []
    for i in mssparkutils.fs.ls(path):
        if i.isDir: files.extend(get_files_recursively(i.path))
        else: files.append(i.path)
    return files

all_paths = get_files_recursively(bronze_path)
final_dfs = []

print("🚀 Procesando estrictamente Ocupados.txt y Desocupados.txt...")

for p in all_paths:
    p_low = p.lower()
    
    # 1. REGLA DE ORO: Solo Cabecera y Resto (Ignoramos AREA para evitar duplicidad)
    if not any(x in p_low for x in ["cabecera", "resto"]): continue
    if "area" in p_low: continue 
    
    # 2. REGLA DE ORO: Solo los archivos con estos nombres exactos
    status = None
    if "desocupados.txt" in p_low:
        status = "desocupado"
    elif "ocupados.txt" in p_low:
        status = "ocupado"
    
    if status:
        geo = "cabecera" if "cabecera" in p_low else "resto"
        res = read_exact_file(p, status, geo)
        if res: final_dfs.append(res)

if final_dfs:
    df_silver = final_dfs[0]
    for next_df in final_dfs[1:]:
        df_silver = df_silver.unionByName(next_df)
    
    df_silver = df_silver.withColumn("is_national_total", F.lit(True))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print("\n✅ SILVER 2017 NORMALIZADO")
    # Este resumen debe mostrar ~22M para ocupados en cada mes
    df_silver.groupBy("month", "status").agg(F.sum("weight").alias("total_weight")).orderBy("month", "status").show()
else:
    print("❌ No se encontraron los archivos Ocupados.txt o Desocupados.txt")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2018 CON DEPARTAMENTOS

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2018
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo anti-caos de {year}...")

# 1. Leemos TODO como texto plano para evitar errores de rutas físicas rotas
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación por contenido en rutas
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas"))

# 3. Función Quirúrgica Dinámica con Extracción de Índices
def process_2018_chaos(df_input, label):
    df_group = df_input.filter(F.col("status_file") == label)
    if df_group.count() == 0: 
        print(f"⚠️ No encontré datos para {label}")
        return None
    
    # Extraemos la primera fila para detectar separador y mapear los índices reales de las columnas
    first_row = df_group.filter(F.lower(F.col("value")).like("%directorio%")).limit(1).collect()
    if not first_row: return None
    
    header_val = first_row[0]['value']
    delim = ";" if ";" in header_val else ("," if "," in header_val else "\t")
    cols = [c.strip().upper().replace('"', '') for c in header_val.split(delim)]
    
    try:
        # Localización dinámica del Peso (FEX)
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        
        # Localización dinámica del Departamento (DPTO)
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        
        depto_str = f"'{cols[idx_depto]}' (idx {idx_depto})" if idx_depto is not None else "⚠️ NO ENCONTRADO (Usa contingencia '00')"
        print(f"   ✅ {label.upper()}: Delim '{delim}' | Peso: '{cols[idx_peso]}' (idx {idx_peso}) | Depto: {depto_str}")
    except StopIteration:
        print(f"   ❌ {label.upper()}: No se pudo mapear las columnas críticas en: {cols[:5]}...")
        return None

    # Procesamiento y armado de columnas de la capa Silver
    df_parsed = df_group.filter(~F.lower(F.col("value")).like("%directorio%")) \
        .withColumn("month", F.regexp_extract(F.col("file_name"), r"month=(\d+)", 1).cast("int")) \
        .withColumn("split_data", F.split(F.col("value"), delim)) \
        .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                     .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                     .otherwise("area"))
    
    # Construcción del SELECT dinámico según el índice geográfico hallado
    if idx_depto is not None:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lpad(F.regexp_replace(df_parsed["split_data"][idx_depto], '"', ''), 2, "0").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '"', ''), ",", ".").cast("double").alias("total_weight")
        )
    else:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lit("00").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '"', ''), ",", ".").cast("double").alias("total_weight")
        )
        
    return df_final.filter(F.col("total_weight").isNotNull())

# 4. Ejecución de la lógica integrada
df_ocu = process_2018_chaos(df_meta, "ocupado")
df_des = process_2018_chaos(df_meta, "desocupado")

# 5. Unión y Persistencia en Delta
final_dfs = [df for df in [df_ocu, df_des] if df is not None]
if final_dfs:
    df_silver_2018 = final_dfs[0]
    if len(final_dfs) > 1:
        df_silver_2018 = df_silver_2018.unionByName(final_dfs[1])
        
    # Filtrar Cabecera y Resto para evitar duplicaciones en agregaciones globales
    df_silver_2018 = df_silver_2018.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2018.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n✅ TABLA DE 2018 GUARDADA CON ÉXITO: {silver_table}")
    print("-" * 60)
    
    # Reporte de Auditoría Territorial
    df_silver_2018.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ Error fatal: No se pudo procesar ningún set de datos para 2018.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

## ============================================================================
## 🚀 SILVER 2018: RECONSTRUCCIÓN TOTAL (ANTI-CAOS)
## ============================================================================
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2018
bronze_path = f"Files/raw/dane/year={year}/" # Asegúrate de que termine en /
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo de {year}...")

# 1. Leemos TODO como texto plano para evitar errores de PATH_NOT_FOUND individuales
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación por contenido (No por nombre exacto)
# Buscamos patrones: si tiene "deso", es desocupado. Si tiene "ocu" pero no "deso", es ocupado.
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas"))

# 3. Función Mágica para procesar el desorden
def process_2018_chaos(df_input, label):
    df_group = df_input.filter(F.col("status_file") == label)
    if df_group.count() == 0: 
        print(f"⚠️ No encontré datos para {label}")
        return None
    
    # Extraemos la primera fila para detectar separador y columnas
    first_row = df_group.filter(F.upper(F.col("value")).contains("DIRECTORIO")).limit(1).collect()
    if not first_row: return None
    
    header_val = first_row[0]['value']
    delim = ";" if ";" in header_val else ","
    cols = [c.strip().upper() for c in header_val.split(delim)]
    
    # Buscamos el Peso (FEX) dinámicamente
    try:
        # En 2019 suele ser FEX_C_2011 o FEX_C
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        print(f"   ✅ {label}: Separador '{delim}' | Columna peso: '{cols[idx_peso]}' (idx {idx_peso})")
    except StopIteration:
        print(f"   ❌ {label}: No encontré columna de peso en: {cols[:5]}...")
        return None

    # Procesamos
    return df_group.filter(~F.upper(F.col("value")).contains("DIRECTORIO")) \
        .withColumn("month", F.regexp_extract(F.col("file_name"), r"month=(\d+)", 1).cast("int")) \
        .withColumn("split_data", F.split(F.col("value"), delim)) \
        .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                 .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                     .otherwise("area")) \
        .select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            # Limpiamos el peso de comillas y basura
            F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '"', ''), ",", ".").cast("double").alias("weight")
        ).filter(F.col("weight").isNotNull())

# 4. Ejecución Quirúrgica
df_ocu = process_2018_chaos(df_meta, "ocupado")
df_des = process_2018_chaos(df_meta, "desocupado")

# 5. Unión y Guardado
final_dfs = [df for df in [df_ocu, df_des] if df is not None]
if final_dfs:
    df_silver_2018 = final_dfs[0]
    if len(final_dfs) > 1:
        df_silver_2018 = df_silver_2018.unionByName(final_dfs[1])
    
    # Flag para Gold
    df_silver_2018 = df_silver_2018.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2018.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n📊 RESUMEN SILVER {year}:")
    df_silver_2018.groupBy("status", "month").count().orderBy("month", "status").show()
else:
    print("❌ Error fatal: No se pudo procesar nada de 2019.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2019 CON DEPARTAMENTOS

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2019
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo anti-caos de {year}...")

# 1. Leemos todo en texto plano con búsqueda recursiva profunda
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación por contenido semántico en las rutas
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas"))

# 3. Función Quirúrgica Dinámica (Extracción Multivariable por Índices)
def process_2019_chaos(df_input, label):
    df_group = df_input.filter(F.col("status_file") == label)
    if df_group.count() == 0: 
        print(f"⚠️ No encontré datos para {label}")
        return None
    
    # Captura infalible del encabezado (sin importar mayúsculas/minúsculas)
    first_row = df_group.filter(F.lower(F.col("value")).like("%directorio%")).limit(1).collect()
    if not first_row: return None
    
    header_val = first_row[0]['value']
    delim = ";" if ";" in header_val else ("," if "," in header_val else "\t")
    cols = [c.strip().upper().replace('"', '') for c in header_val.split(delim)]
    
    try:
        # Búsqueda dinámica de índices críticos
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        
        depto_str = f"'{cols[idx_depto]}' (idx {idx_depto})" if idx_depto is not None else "⚠️ NO ENCONTRADO (Usa contingencia '00')"
        print(f"   ✅ {label.upper()}: Delim '{delim}' | Peso: '{cols[idx_peso]}' (idx {idx_peso}) | Depto: {depto_str}")
    except StopIteration:
        print(f"   ❌ {label.upper()}: No se pudo mapear las columnas críticas en: {cols[:5]}...")
        return None

    # Limpieza de datos y tokenización por fila
    df_parsed = df_group.filter(~F.lower(F.col("value")).like("%directorio%")) \
        .withColumn("month", F.regexp_extract(F.col("file_name"), r"month=(\d+)", 1).cast("int")) \
        .withColumn("split_data", F.split(F.col("value"), delim)) \
        .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                     .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                     .otherwise("area"))
    
    # Proyección dinámica controlando nulos en geografía
    if idx_depto is not None:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lpad(F.regexp_replace(df_parsed["split_data"][idx_depto], '"', ''), 2, "0").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '"', ''), ",", ".").cast("double").alias("total_weight")
        )
    else:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lit("00").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '"', ''), ",", ".").cast("double").alias("total_weight")
        )
        
    return df_final.filter(F.col("total_weight").isNotNull())

# 4. Ejecución del motor analítico
df_ocu = process_2019_chaos(df_meta, "ocupado")
df_des = process_2019_chaos(df_meta, "desocupado")

# 5. Unión de bloques y persistencia en Delta
final_dfs = [df for df in [df_ocu, df_des] if df is not None]
if final_dfs:
    df_silver_2019 = final_dfs[0]
    if len(final_dfs) > 1:
        df_silver_2019 = df_silver_2019.unionByName(final_dfs[1])
        
    # Filtro estricto para evitar duplicidad de datos en la capa Gold
    df_silver_2019 = df_silver_2019.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2019.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n✅ TABLA DE 2019 CONSOLIDADA: {silver_table}")
    print("-" * 60)
    
    # Reporte de control de calidad territorial
    df_silver_2019.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ Error crítico: No se pudo generar ningún set de datos para 2019.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## RECONSTRUCCIÓN TOTAL SILVER 2019

# CELL ********************

## ============================================================================
## 🚀 SILVER 2019: RECONSTRUCCIÓN TOTAL (ANTI-CAOS)
## ============================================================================
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2019
bronze_path = f"Files/raw/dane/year={year}/" # Asegúrate de que termine en /
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo de {year}...")

# 1. Leemos TODO como texto plano para evitar errores de PATH_NOT_FOUND individuales
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación por contenido (No por nombre exacto)
# Buscamos patrones: si tiene "deso", es desocupado. Si tiene "ocu" pero no "deso", es ocupado.
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas"))

# 3. Función Mágica para procesar el desorden
def process_2019_chaos(df_input, label):
    df_group = df_input.filter(F.col("status_file") == label)
    if df_group.count() == 0: 
        print(f"⚠️ No encontré datos para {label}")
        return None
    
    # Extraemos la primera fila para detectar separador y columnas
    first_row = df_group.filter(F.upper(F.col("value")).contains("DIRECTORIO")).limit(1).collect()
    if not first_row: return None
    
    header_val = first_row[0]['value']
    delim = ";" if ";" in header_val else ","
    cols = [c.strip().upper() for c in header_val.split(delim)]
    
    # Buscamos el Peso (FEX) dinámicamente
    try:
        # En 2019 suele ser FEX_C_2011 o FEX_C
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        print(f"   ✅ {label}: Separador '{delim}' | Columna peso: '{cols[idx_peso]}' (idx {idx_peso})")
    except StopIteration:
        print(f"   ❌ {label}: No encontré columna de peso en: {cols[:5]}...")
        return None

    # Procesamos
    return df_group.filter(~F.upper(F.col("value")).contains("DIRECTORIO")) \
        .withColumn("month", F.regexp_extract(F.col("file_name"), r"month=(\d+)", 1).cast("int")) \
        .withColumn("split_data", F.split(F.col("value"), delim)) \
        .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                 .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                     .otherwise("area")) \
        .select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            # Limpiamos el peso de comillas y basura
            F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '"', ''), ",", ".").cast("double").alias("weight")
        ).filter(F.col("weight").isNotNull())

# 4. Ejecución Quirúrgica
df_ocu = process_2019_chaos(df_meta, "ocupado")
df_des = process_2019_chaos(df_meta, "desocupado")

# 5. Unión y Guardado
final_dfs = [df for df in [df_ocu, df_des] if df is not None]
if final_dfs:
    df_silver_2019 = final_dfs[0]
    if len(final_dfs) > 1:
        df_silver_2019 = df_silver_2019.unionByName(final_dfs[1])
    
    # Flag para Gold
    df_silver_2019 = df_silver_2019.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2019.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n📊 RESUMEN SILVER {year}:")
    df_silver_2019.groupBy("status", "month").count().orderBy("month", "status").show()
else:
    print("❌ Error fatal: No se pudo procesar nada de 2019.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2020 CON DEPARTAMENTOS

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2020
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando Reconstrucción Total 2020 basada en Microdatos...")

# 1. Lectura masiva en texto plano
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación semántica de archivos (Ignorando módulos basura de contingencia)
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos"))

# 3. Procesador Quirúrgico de Microdatos Geográficos
def process_2020_chaos(df_input, label):
    df_group = df_input.filter(F.col("status_file") == label)
    if df_group.count() == 0: 
        print(f"⚠️ No hay datos para {label}")
        return None
    
    # Captura segura del header
    header_row = df_group.filter(F.lower(F.col("value")).like("%directorio%")).limit(1).collect()
    if not header_row: return None
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ("," if "," in val else "\t")
    cols = [c.strip().upper().replace('"', '') for c in val.split(delim)]
    
    try:
        # BÚSQUEDA DINÁMICA TRIPLE: Peso, Departamento y la Variable Crítica CLASE
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
        
        depto_str = f"'{cols[idx_depto]}' (idx {idx_depto})" if idx_depto is not None else "⚠️ NO ENCONTRADO"
        clase_str = f"'{cols[idx_clase]}' (idx {idx_clase})" if idx_clase is not None else "⚠️ NO ENCONTRADA (Fuga urbana/rural)"
        
        print(f"   ✅ {label.upper()}: Delim '{delim}' | Peso: (idx {idx_peso}) | Depto: {depto_str} | Clase: {clase_str}")
    except StopIteration:
        print(f"   ❌ {label.upper()}: Falta columna crítica en encabezado {cols[:5]}")
        return None

    # Limpieza de encabezados y tokenización por fila
    df_parsed = df_group.filter(~F.lower(F.col("value")).like("%directorio%")) \
        .withColumn("month", F.regexp_extract(F.col("file_name"), r"month=(\d+)", 1).cast("int")) \
        .withColumn("split_data", F.split(F.col("value"), delim))
    
    # Mapeo dinámico de la columna GEO_SOURCE mirando la variable 'CLASE' interna
    if idx_clase is not None:
        df_parsed = df_parsed.withColumn(
            "geo_source",
            F.when(F.regexp_replace(F.col("split_data")[idx_clase], '"', '') == "1", "cabecera")
             .when(F.regexp_replace(F.col("split_data")[idx_clase], '"', '') == "2", "resto")
             .otherwise("cabecera") # Valor por defecto seguro para salvaguardar data
        )
    else:
        df_parsed = df_parsed.withColumn("geo_source", F.lit("cabecera"))

    # Construcción final de proyecciones
    if idx_depto is not None:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lpad(F.regexp_replace(df_parsed["split_data"][idx_depto], '"', ''), 2, "0").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '"', ''), ",", ".").cast("double").alias("total_weight")
        )
    else:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lit("00").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '"', ''), ",", ".").cast("double").alias("total_weight")
        )
        
    return df_final.filter(F.col("total_weight").isNotNull())

# 4. Ejecución del motor analítico
df_ocu = process_2020_chaos(df_meta, "ocupado")
df_des = process_2020_chaos(df_meta, "desocupado")

# 5. Unión, Filtro y Persistencia en Capa Silver
final_dfs = [df for df in [df_ocu, df_des] if df is not None]
if final_dfs:
    df_silver_2020 = final_dfs[0]
    if len(final_dfs) > 1: 
        df_silver_2020 = df_silver_2020.unionByName(final_dfs[1])
    
    # Ahora que 'geo_source' sí tiene las etiquetas reales basadas en CLASE, filtramos con total seguridad
    df_silver_2020 = df_silver_2020.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2020.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n✅ LA RATONERA SE CERRÓ: TABLA DE 2018 RECONSTRUIDA: {silver_table}")
    print("-" * 60)
    
    # Reporte Final de Control Territorial
    df_silver_2020.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ Error crítico terminal: 2020 se resiste al procesamiento.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2020- RECONSTRUIDO

# CELL ********************

## ============================================================================
## 🚀 SILVER 2020: LA BATALLA CONTRA EL "ASCO" DE LA PANDEMIA
## ============================================================================
from pyspark.sql import functions as F

year = 2020
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo profundo de {year}...")

# 1. Lectura masiva (Anti-PathNotFound)
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación por contenido
# En 2020 aparecen archivos de "Fuerza de Trabajo" que hay que ignorar
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos"))

# 3. Procesador de Caos 2020
def process_2020_chaos(df_input, label):
    df_group = df_input.filter(F.col("status_file") == label)
    if df_group.count() == 0: 
        print(f"⚠️ No hay datos para {label}")
        return None
    
    # Buscamos el header (DIRECTORIO)
    header_row = df_group.filter(F.upper(F.col("value")).contains("DIRECTORIO")).limit(1).collect()
    if not header_row: return None
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper() for c in val.split(delim)]
    
    try:
        # En 2020 el nombre suele ser 'FEX_C' o 'FEX_C18'
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        print(f"   ✅ {label}: Delim '{delim}' | Col '{cols[idx_peso]}' (idx {idx_peso})")
    except StopIteration:
        print(f"   ❌ {label}: Sin columna de peso en {cols[:5]}")
        return None

    return df_group.filter(~F.upper(F.col("value")).contains("DIRECTORIO")) \
        .withColumn("month", F.regexp_extract(F.col("file_name"), r"month=(\d+)", 1).cast("int")) \
        .withColumn("split_data", F.split(F.col("value"), delim)) \
        .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                 .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                 .otherwise("area")) \
        .select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '"', ''), ",", ".").cast("double").alias("weight")
        ).filter(F.col("weight").isNotNull())

# 4. Ejecución
df_ocu = process_2020_chaos(df_meta, "ocupado")
df_des = process_2020_chaos(df_meta, "desocupado")

# 5. Unión y Guardado
final_dfs = [df for df in [df_ocu, df_des] if df is not None]
if final_dfs:
    df_silver_2020 = final_dfs[0]
    if len(final_dfs) > 1: df_silver_2020 = df_silver_2020.unionByName(final_dfs[1])
    
    df_silver_2020 = df_silver_2020.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2020.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n📊 RESUMEN SILVER {year}:")
    df_silver_2020.groupBy("status", "month").count().orderBy("month", "status").show()
else:
    print("❌ Error: 2020 no se pudo procesar.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# 📂 LISTADO REAL DE CARPETAS DE MESES
year = 2021
path_root = f"Files/raw/dane/year={year}/"

print(f"📁 Analizando estructura de carpetas para {year}...")

# Listamos solo los nombres de los directorios
carpetas = mssparkutils.fs.ls(path_root)
for c in carpetas:
    if c.isDir:
        print(f"✅ Carpeta encontrada: '{c.name}'")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2021 CON DEPARTAMENTOS

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2021
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo nativo ultra-veloz para {year}...")

# 1. Lectura masiva en texto plano aprovechando las particiones de Fabric
# Usamos recursiveFileLookup para entrar directo a los CSVs dentro de month=XX
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación semántica (Ignoramos módulos que no sean Ocupados o Desocupados)
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos"))

# 3. Función Quirúrgica de Microdatos (Extracción por Índices Dinámicos)
def process_2021_structure(df_input, label):
    df_group = df_input.filter(F.col("status_file") == label)
    if df_group.count() == 0: 
        print(f"⚠️ No hay datos mapeados para {label}")
        return None
    
    # Captura segura del encabezado (Buscamos Directorio o Secuencia)
    header_row = df_group.filter(F.lower(F.col("value")).rlike("directorio|secuencia")).limit(1).collect()
    if not header_row: return None
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper().replace('"', '') for c in val.split(delim)]
    
    try:
        # Búsqueda triple indexada en el header detectado
        idx_peso = next(i for i, c in enumerate(cols) if any(p in c for p in ["FEX", "PESO", "FACTOR"]))
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
        
        depto_str = f"'{cols[idx_depto]}' (idx {idx_depto})" if idx_depto is not None else "⚠️ NO ENCONTRADO"
        clase_str = f"'{cols[idx_clase]}' (idx {idx_clase})" if idx_clase is not None else "⚠️ NO ENCONTRADA"
        print(f"   ✅ {label.upper()}: Delim '{delim}' | Peso: (idx {idx_peso}) | Depto: {depto_str} | Clase: {clase_str}")
    except StopIteration:
        print(f"   ❌ {label.upper()}: Error al buscar columnas críticas en {cols[:5]}")
        return None

    # Limpieza e inyección del mes extrayéndolo directamente del path de la partición (month=XX)
    df_parsed = df_group.filter(~F.lower(F.col("value")).rlike("directorio|secuencia")) \
        .withColumn("month", F.regexp_extract(F.col("file_name"), r"month=(\d+)", 1).cast("int")) \
        .withColumn("split_data", F.split(F.col("value"), delim))
    
    # Decodificación interna de la geografía urbana/rural (CLASE)
    if idx_clase is not None:
        df_parsed = df_parsed.withColumn(
            "geo_source",
            F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
             .when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "2", "resto")
             .otherwise("cabecera")
        )
    else:
        df_parsed = df_parsed.withColumn("geo_source", F.lit("cabecera"))

    # Armado final del DataFrame alineado al estándar corporativo
    if idx_depto is not None:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lpad(F.regexp_replace(df_parsed["split_data"][idx_depto], '[ "]', ''), 2, "0").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
        )
    else:
        df_final = df_parsed.select(
            F.lit(year).alias("year"),
            F.col("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.lit("00").alias("codigo_departamento"),
            F.regexp_replace(F.regexp_replace(df_parsed["split_data"][idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
        )
        
    return df_final.filter(F.col("total_weight").isNotNull())

# 4. Ejecución paralela en el clúster
df_ocu = process_2021_structure(df_meta, "ocupado")
df_des = process_2021_structure(df_meta, "desocupado")

# 5. Consolidación y Guardado Delta
final_dfs = [df for df in [df_ocu, df_des] if df is not None]
if final_dfs:
    df_silver_2021 = final_dfs[0]
    if len(final_dfs) > 1:
        df_silver_2021 = df_silver_2021.unionByName(final_dfs[1])
        
    # Filtro estricto urbano/rural para blindar agregaciones globales
    df_silver_2021 = df_silver_2021.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2021.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n✅ CAPA SILVER {year} FINALIZADA CON ÉXITO: {silver_table}")
    print("-" * 65)
    
    # Reporte de Auditoría Territorial para revisar la reactivación económica del 2021
    df_silver_2021.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ Error fatal: El pipeline no pudo procesar la estructura del 2021.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2021- RECONSTRUIDO

# CELL ********************

## ============================================================================
## 🚀 SILVER 2021: VERSIÓN DEFINITIVA (CASE-INSENSITIVE + ZERO-PADDING)
## ============================================================================
from pyspark.sql import functions as F

year = 2021
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

# 1. Buscamos TODO (usamos * sin extensión para no perder los .csv minúsculas)
all_files = spark.createDataFrame(
    spark.sparkContext.wholeTextFiles(f"{bronze_path}*/*", minPartitions=1)
).select(F.col("_1").alias("path")).filter(F.lower(F.col("path")).rlike("ocupa|deso")) \
 .filter(F.lower(F.col("path")).rlike("\.csv$")) \
 .filter(~F.lower(F.col("path")).rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos"))

files_list = [row['path'] for row in all_files.collect()]
print(f"📂 Se encontraron {len(files_list)} archivos. Procesando la serie completa...")

final_list = []

for path in files_list:
    fn = path.lower()
    label = "desocupado" if any(x in fn for x in ["deso", "no%20ocu", "no_ocu"]) else "ocupado"
    geo = "cabecera" if any(x in fn for x in ["cabe", "urban"]) else ("resto" if any(x in fn for x in ["resto", "rural"]) else "area")
    
    # Extraemos el mes manejando el cero (ej: month=05 -> 5)
    month_str = path.split("month=")[1].split("/")[0]
    month = int(month_str)
    
    df_temp = spark.read.text(path)
    header_row = df_temp.filter(F.upper(F.col("value")).rlike("DIRECTORIO|SECUENCIA")).limit(1).collect()
    
    if not header_row: continue
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper() for c in val.split(delim)]
    
    try:
        idx_peso = next(i for i, c in enumerate(cols) if any(p in c for p in ["FEX", "PESO", "FACTOR"]))
        
        processed = df_temp.filter(~F.upper(F.col("value")).rlike("DIRECTORIO|SECUENCIA")) \
            .withColumn("split_data", F.split(F.col("value"), delim)) \
            .select(
                F.lit(year).alias("year"),
                F.lit(month).alias("month"),
                F.lit(label).alias("status"),
                F.lit(geo).alias("geo_source"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("weight")
            ).filter(F.col("weight").isNotNull())
        
        final_list.append(processed)
    except:
        continue

# 2. Unión y Guardado
if final_list:
    df_silver_2021 = final_list[0]
    for d in final_list[1:]: df_silver_2021 = df_silver_2021.unionByName(d)
    
    df_silver_2021 = df_silver_2021.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2021.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n📊 RESUMEN 2021 - ¡TODOS LOS MESES CAPTURADOS!")
    df_silver_2021.groupBy("month").agg(
        F.sum(F.when(F.col("status")=="ocupado", F.col("weight"))).alias("Ocupados_Brutos")
    ).orderBy("month").show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2022 CON DEPARTAMENTOS

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2022
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo quirúrgico de la nueva GEIH Marco 2018 ({year})...")

# 1. Lectura total en texto plano
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación semántica de archivos (Evitando módulos no laborales)
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos|juvenil|migracion"))

# 3. Procesamiento dinámico archivo por archivo
unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
all_dfs = []

print(f"📂 Procesando {len(unique_files)} archivos con mapeo interno de microdatos...")

for fn in unique_files:
    # Extracción segura del mes mediante regex de Python
    match = re.search(r"month=(\d+)", fn)
    if not match: continue
    m = int(match.group(1))

    df_file = df_meta.filter(F.col("file_name") == fn)
    label = df_file.select("status_file").limit(1).collect()[0][0]

    # Localizar la fila del encabezado
    header_row = df_file.filter(F.lower(F.col("value")).like("%directorio%")).limit(1).collect()
    if not header_row: continue
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper().replace('"', '') for c in val.split(delim)]
    
    try:
        # --- RASTREADOR CUÁDRUPLE DE ÍNDICES ---
        idx_peso = next(i for i, c in enumerate(cols) if any(p in c for p in ["FEX", "PESO", "FACTOR"]))
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
        idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
        
        # Tokenización de las filas de datos
        df_proc = df_file.filter(~F.lower(F.col("value")).like("%directorio%")) \
            .withColumn("split_data", F.split(F.col("value"), delim))
        
        # Mapeo geográfico de alta fidelidad basado en el microdato CLASE (1=Cabecera, 2=Resto)
        if idx_clase is not None:
            df_proc = df_proc.withColumn(
                "geo_source",
                F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
                 .when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "2", "resto")
                 .otherwise("cabecera")
            )
        else:
            # Plan de respaldo por si el path da pistas
            df_proc = df_proc.withColumn(
                "geo_source", 
                F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                 .when(F.col("fn_low").rlike("resto|rural"), "resto")
                 .otherwise("cabecera")
            )
        
        # Filtro metodológico DSI para el archivo de desocupados
        if label == "desocupado" and idx_dsi is not None:
            df_proc = df_proc.filter(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', '') == "1")

        # Proyección alineada al estándar corporativo estricto
        if idx_depto is not None:
            df_final = df_proc.select(
                F.lit(year).alias("year"),
                F.lit(m).alias("month"),
                F.lit(label).alias("status"),
                F.col("geo_source"),
                F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
            )
        else:
            df_final = df_proc.select(
                F.lit(year).alias("year"),
                F.lit(m).alias("month"),
                F.lit(label).alias("status"),
                F.col("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
            )
        
        all_dfs.append(df_final.filter(F.col("total_weight").isNotNull()))
        
    except Exception as e:
        print(f"   ⚠️ Saltando archivo por desalineación estructural: {fn.split('/')[-1]} -> {str(e)[:40]}")
        continue

# 4. Unión y Persistencia Delta
if all_dfs:
    df_silver_2022 = all_dfs[0]
    for d in all_dfs[1:]: df_silver_2022 = df_silver_2022.unionByName(d)
    
    # Filtro estricto para limpiar el set antes de la unificación Gold
    df_silver_2022 = df_silver_2022.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2022.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n✅ SILVER {year} CONSOLIDADO CON ÉXITO: {silver_table}")
    print("-" * 65)
    
    # Reporte de control de calidad territorial marco 2018
    df_silver_2022.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ Error crítico: Ningún archivo pudo alinearse al validador de la capa Silver.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2022- RECONSTRUIDO

# CELL ********************

## ============================================================================
## 🛠️ SILVER 2022: RECONSTRUCCIÓN DEFINITIVA (RE-FIXED)
## ============================================================================
from pyspark.sql import functions as F
import re  # Usamos el motor de regex de Python para los nombres de archivos

year = 2022
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo de {year}...")

# 1. Lectura total
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación "Red de Pesca"
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos|juvenil|migracion"))

# 3. Procesamiento archivo por archivo
unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]

all_dfs = []
print(f"📂 Procesando {len(unique_files)} archivos de 2022...")

for fn in unique_files:
    # --- 🛠️ FIX AQUÍ: Usamos Python puro para el mes ---
    match = re.search(r"month=(\d+)", fn)
    if not match: continue
    m = int(match.group(1))

    df_file = df_meta.filter(F.col("file_name") == fn)
    label = df_file.select("status_file").limit(1).collect()[0][0]

    # Buscar el header
    header_row = df_file.filter(F.upper(F.col("value")).contains("DIRECTORIO")).limit(1).collect()
    if not header_row: continue
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper() for c in val.split(delim)]
    
    try:
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
        
        df_proc = df_file.filter(~F.upper(F.col("value")).contains("DIRECTORIO")) \
            .withColumn("split_data", F.split(F.col("value"), delim)) \
            .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                     .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                     .otherwise("area"))
        
        # Filtro DSI para desocupados
        if label == "desocupado" and idx_dsi is not None:
            df_proc = df_proc.filter(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', '') == "1")

        df_final = df_proc.select(
            F.lit(year).alias("year"),
            F.lit(m).alias("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '"', ''), ",", ".").cast("double").alias("weight")
        ).filter(F.col("weight").isNotNull())
        
        all_dfs.append(df_final)
    except Exception as e:
        # Si un archivo falla, lo saltamos pero avisamos
        print(f"   ⚠️ Error en archivo {fn.split('/')[-1]}: {str(e)[:50]}")
        continue

# 4. Unión y Guardado
if all_dfs:
    df_silver_2022 = all_dfs[0]
    for d in all_dfs[1:]: df_silver_2022 = df_silver_2022.unionByName(d)
    
    df_silver_2022 = df_silver_2022.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2022.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"✅ SILVER {year} RECONSTRUIDO")
    df_silver_2022.groupBy("month", "status").count().orderBy("month", "status").show(24)
else:
    print("❌ No se pudo procesar ningún archivo. Revisa los delimitadores.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2023 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2023
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo definitivo de la serie: GEIH Marco 2018 ({year})...")

# 1. Lectura total en texto plano
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación semántica estricta
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos|juvenil"))

# 3. Procesamiento dinámico indexado archivo por archivo
unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
all_dfs = []

print(f"📂 Procesando {len(unique_files)} archivos con decodificación de microdatos...")

for fn in unique_files:
    match = re.search(r"month=(\d+)", fn)
    if not match: continue
    m = int(match.group(1))

    df_file = df_meta.filter(F.col("file_name") == fn)
    label = df_file.select("status_file").limit(1).collect()[0][0]

    # Localizar el header dinámicamente
    header_row = df_file.filter(F.lower(F.col("value")).like("%directorio%")).limit(1).collect()
    if not header_row: continue
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper().replace('"', '') for c in val.split(delim)]
    
    try:
        # --- RASTREADOR CUÁDRUPLE INTEGRADO ---
        idx_peso = next(i for i, c in enumerate(cols) if any(p in c for p in ["FEX", "PESO", "FACTOR"]))
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
        idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
        
        df_proc = df_file.filter(~F.lower(F.col("value")).like("%directorio%")) \
            .withColumn("split_data", F.split(F.col("value"), delim))
        
        # Separación cabecera/resto mirando el microdato interno CLASE
        if idx_clase is not None:
            df_proc = df_proc.withColumn(
                "geo_source",
                F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
                 .when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "2", "resto")
                 .otherwise("cabecera")
            )
        else:
            df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
        
        # Control DSI para desocupación
        if label == "desocupado" and idx_dsi is not None:
            df_proc = df_proc.filter(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', '') == "1")

        # Proyección final homogeneizada
        if idx_depto is not None:
            df_final = df_proc.select(
                F.lit(year).alias("year"),
                F.lit(m).alias("month"),
                F.lit(label).alias("status"),
                F.col("geo_source"),
                F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
            )
        else:
            df_final = df_proc.select(
                F.lit(year).alias("year"),
                F.lit(m).alias("month"),
                F.lit(label).alias("status"),
                F.col("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
            )
        
        all_dfs.append(df_final.filter(F.col("total_weight").isNotNull()))
        
    except Exception as e:
        print(f"   ⚠️ Desalineación en archivo {fn.split('/')[-1]}: {str(e)[:40]}")
        continue

# 4. Unión y Persistencia Delta
if all_dfs:
    df_silver_2023 = all_dfs[0]
    for d in all_dfs[1:]: df_silver_2023 = df_silver_2023.unionByName(d)
    
    # Filtro estricto para limpieza en agregaciones Gold
    df_silver_2023 = df_silver_2023.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2023.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n✅ SILVER {year} CERRADO RECIEDUMBRE DE MANERA IMPECABLE: {silver_table}")
    print("-" * 65)
    
    # Reporte territorial final para el 2023
    df_silver_2023.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ Error fatal: 2023 no pudo procesarse.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2023- RECONSTRUCCION

# CELL ********************

## ============================================================================
## 🚀 SILVER 2023: EL CIERRE DE LA SERIE HISTÓRICA
## ============================================================================
from pyspark.sql import functions as F
import re

year = 2023
bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo final de {year}...")

# 1. Lectura total
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|ingresos|vivienda|fuerza|seguridad|formas|inactivos|juvenil"))

# 3. Procesamiento por archivo
unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
all_dfs = []

for fn in unique_files:
    match = re.search(r"month=(\d+)", fn)
    if not match: continue
    m = int(match.group(1))

    df_file = df_meta.filter(F.col("file_name") == fn)
    label = df_file.select("status_file").limit(1).collect()[0][0]

    header_row = df_file.filter(F.upper(F.col("value")).contains("DIRECTORIO")).limit(1).collect()
    if not header_row: continue
    
    val = header_row[0]['value']
    delim = ";" if ";" in val else ","
    cols = [c.strip().upper() for c in val.split(delim)]
    
    try:
        idx_peso = next(i for i, c in enumerate(cols) if "FEX" in c or "PESO" in c)
        idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
        
        df_proc = df_file.filter(~F.upper(F.col("value")).contains("DIRECTORIO")) \
            .withColumn("split_data", F.split(F.col("value"), delim)) \
            .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                     .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                     .otherwise("area"))
        
        # Filtro DSI para asegurar que no contamos inactivos en desocupados
        if label == "desocupado" and idx_dsi is not None:
            df_proc = df_proc.filter(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', '') == "1")

        df_final = df_proc.select(
            F.lit(year).alias("year"),
            F.lit(m).alias("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '"', ''), ",", ".").cast("double").alias("weight")
        ).filter(F.col("weight").isNotNull())
        
        all_dfs.append(df_final)
    except: continue

# 4. Unión y Guardado
if all_dfs:
    df_silver_2023 = all_dfs[0]
    for d in all_dfs[1:]: df_silver_2023 = df_silver_2023.unionByName(d)
    
    df_silver_2023 = df_silver_2023.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2023.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"✅ SILVER {year} COMPLETADO")
    df_silver_2023.groupBy("month", "status").count().orderBy("month", "status").show(24)
else:
    print("❌ 2023 falló.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2024 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2024
bronze_path = f"abfss://f5879c16-6832-4003-90dd-eb2c10497cc0@onelake.dfs.fabric.microsoft.com/ecf22981-1012-4b17-861f-62880aa61238/Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo definitivo en OneLake para {year}...")

# 1. Lectura masiva distribuida
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación semántica (2024 hereda 'No ocupados')
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|generales|seguridad|salud|educaci|otras|formas|vivienda"))

# 3. Procesamiento dinámico indexado archivo por archivo
unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
all_dfs = []

print(f"📂 Procesando {len(unique_files)} archivos clave encontrados con inyección geográfica...")

for fn in unique_files:
    match = re.search(r"month=(\d+)", fn)
    if not match: continue
    m = int(match.group(1))

    df_file = df_meta.filter(F.col("file_name") == fn)
    label = df_file.select("status_file").limit(1).collect()[0][0]

    sample_rows = df_file.limit(2).collect()
    if not sample_rows: continue
    
    header_val = sample_rows[0]['value']
    if "FEX" not in header_val.upper() and "DIRECTORIO" not in header_val.upper() and len(sample_rows) > 1:
        header_val = sample_rows[1]['value']

    delim = ";" if ";" in header_val else ","
    cols = [c.strip().upper().replace('"', '') for c in header_val.split(delim)]
    
    try:
        # --- RASTREADOR DINÁMICO CUÁDRUPLE EN ONELAKE ---
        idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR"]))
        idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
        idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
        idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
        
        df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
            .withColumn("split_data", F.split(F.col("value"), delim))
        
        # Mapeo urbano/rural basado en el microdato interno CLASE
        if idx_clase is not None:
            df_proc = df_proc.withColumn(
                "geo_source",
                F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
                 .when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "2", "resto")
                 .otherwise("cabecera")
            )
        else:
            df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
        
        # Limpieza y validación de DSI para desocupados (Manejando decimales .00 del 2024)
        if label == "desocupado" and idx_dsi is not None:
            df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

        # Proyección final del esquema corporativo
        if idx_depto is not None:
            df_final = df_proc.select(
                F.lit(year).alias("year"),
                F.lit(m).alias("month"),
                F.lit(label).alias("status"),
                F.col("geo_source"),
                F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
            )
        else:
            df_final = df_proc.select(
                F.lit(year).alias("year"),
                F.lit(m).alias("month"),
                F.lit(label).alias("status"),
                F.col("geo_source"),
                F.lit("00").alias("codigo_departamento"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
            )
        
        all_dfs.append(df_final.filter(F.col("total_weight").isNotNull()))
    except Exception as e:
        continue

# 4. Unión y Persistencia Delta
if all_dfs:
    df_silver_2024 = all_dfs[0]
    for d in all_dfs[1:]: df_silver_2024 = df_silver_2024.unionByName(d)
    
    # Filtro estricto para evitar duplicidad de datos en la unificación global
    df_silver_2024 = df_silver_2024.filter(F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2024.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"\n✅ SILVER {year} PROCESADO SIN ERRORES DE IDENTIDAD")
    print("-" * 65)
    
    # Reporte territorial del nuevo año procesado
    df_silver_2024.groupBy("month", "codigo_departamento", "status") \
        .agg(F.sum("total_weight").alias("total")) \
        .orderBy("month", "codigo_departamento", "status") \
        .show(20)
else:
    print("❌ 2024 sigue rebelde. Revisa si los archivos están vacíos.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2024- RECONSTRUIDO

# CELL ********************

## ============================================================================
## 🚀 SILVER 2024: EL GRAN RESCATE (ANTI-CODIFICACIÓN RARA)
## ============================================================================
from pyspark.sql import functions as F
import re

year = 2024
bronze_path = f"abfss://f5879c16-6832-4003-90dd-eb2c10497cc0@onelake.dfs.fabric.microsoft.com/ecf22981-1012-4b17-861f-62880aa61238/Files/raw/dane/year={year}/"
silver_table = f"dane_silver_lh.labor_{year}"

print(f"🕵️‍♂️ Iniciando reconstrucción total de {year}...")

# 1. Lectura masiva
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
              .withColumn("file_name", F.input_file_name()) \
              .withColumn("fn_low", F.lower(F.col("file_name")))

# 2. Clasificación mejorada (2024 usa mucho 'No ocupados')
df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file").isin("ocupado", "desocupado")) \
 .filter(~F.col("fn_low").rlike("caracteristicas|generales|seguridad|salud|educaci|otras|formas|vivienda"))

# 3. Procesamiento archivo por archivo con detección de cabecera flexible
unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
all_dfs = []

print(f"📂 Procesando {len(unique_files)} archivos clave encontrados...")

for fn in unique_files:
    # Extraer mes
    match = re.search(r"month=(\d+)", fn)
    if not match: continue
    m = int(match.group(1))

    df_file = df_meta.filter(F.col("file_name") == fn)
    label = df_file.select("status_file").limit(1).collect()[0][0]

    # Tomamos la primera fila para detectar el esquema (sea header o no)
    sample_rows = df_file.limit(2).collect()
    if not sample_rows: continue
    
    # Buscamos cuál de las primeras dos filas es el header (la que tenga FEX o DIRECTORIO)
    header_val = sample_rows[0]['value']
    if "FEX" not in header_val.upper() and "DIRECTORIO" not in header_val.upper() and len(sample_rows) > 1:
        header_val = sample_rows[1]['value']

    delim = ";" if ";" in header_val else ","
    cols = [c.strip().upper() for c in header_val.split(delim)]
    
    try:
        # Buscamos peso con un radar más amplio
        idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR"]))
        idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
        
        # Filtramos la fila del header si aparece en los datos
        df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
            .withColumn("split_data", F.split(F.col("value"), delim)) \
            .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                     .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                     .otherwise("area"))
        
        if label == "desocupado" and idx_dsi is not None:
            # En 2024 el DSI puede venir con decimales .00, limpiamos todo
            df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

        df_final = df_proc.select(
            F.lit(year).alias("year"),
            F.lit(m).alias("month"),
            F.lit(label).alias("status"),
            F.col("geo_source"),
            F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '"', ''), ",", ".").cast("double").alias("weight")
        ).filter(F.col("weight").isNotNull())
        
        all_dfs.append(df_final)
    except Exception as e:
        continue

# 4. Unión y Guardado
if all_dfs:
    df_silver_2024 = all_dfs[0]
    for d in all_dfs[1:]: df_silver_2024 = df_silver_2024.unionByName(d)
    
    df_silver_2024 = df_silver_2024.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
    
    spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
    df_silver_2024.write.format("delta").mode("overwrite").saveAsTable(silver_table)
    
    print(f"✅ SILVER {year} RECONSTRUIDO")
    df_silver_2024.groupBy("month", "status").count().orderBy("month", "status").show(24)
else:
    print("❌ 2024 sigue rebelde. Revisa si los archivos están vacíos.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2025-2026 CON DEPARTAMENTO

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

new_years = [2025, 2026]

for y in new_years:
    print(f"\n🚀 Procesando Silver {y} con Inyección Geográfica de Microdatos...")
    bronze_path = f"abfss://f5879c16-6832-4003-90dd-eb2c10497cc0@onelake.dfs.fabric.microsoft.com/ecf22981-1012-4b17-861f-62880aa61238/Files/raw/dane/year={y}/"
    silver_table = f"dane_silver_lh.labor_{y}"

    try:
        # 1. Lectura total en texto plano
        df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
                      .withColumn("file_name", F.input_file_name()) \
                      .withColumn("fn_low", F.lower(F.col("file_name")))

        # 2. Clasificación semántica de archivos
        df_meta = df_raw.withColumn(
            "status_file",
            F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
            .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
            .otherwise("otro")
        ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
         .filter(~F.col("fn_low").rlike("caracteristicas|generales|seguridad|salud|educaci|otras|formas|vivienda"))

        unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
        all_dfs = []

        print(f"  📂 Se detectaron {len(unique_files)} archivos clave para el año {y}.")

        for fn in unique_files:
            # Extraer mes mediante regex
            match = re.search(r"month=(\d+)", fn)
            if not match: continue
            m = int(match.group(1))

            df_file = df_meta.filter(F.col("file_name") == fn)
            label = df_file.select("status_file").limit(1).collect()[0][0]

            sample_rows = df_file.limit(2).collect()
            if not sample_rows: continue
            
            header_val = sample_rows[0]['value']
            if "FEX" not in header_val.upper() and "DIRECTORIO" not in header_val.upper() and len(sample_rows) > 1:
                header_val = sample_rows[1]['value']

            delim = ";" if ";" in header_val else ","
            cols = [c.strip().upper().replace('"', '') for c in header_val.split(delim)]
            
            try:
                # --- RASTREADOR DINÁMICO CUÁDRUPLE ---
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR"]))
                idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
                idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), delim))
                
                # Desglose urbano/rural mirando la variable interna CLASE
                if idx_clase is not None:
                    df_proc = df_proc.withColumn(
                        "geo_source",
                        F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
                         .when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "2", "resto")
                         .otherwise("cabecera")
                    )
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                # Filtro DSI metodológico para desocupados
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                # Proyección estricta del esquema Silver
                if idx_depto is not None:
                    df_final = df_proc.select(
                        F.lit(y).alias("year"),
                        F.lit(m).alias("month"),
                        F.lit(label).alias("status"),
                        F.col("geo_source"),
                        F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0").alias("codigo_departamento"),
                        F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                    )
                else:
                    df_final = df_proc.select(
                        F.lit(y).alias("year"),
                        F.lit(m).alias("month"),
                        F.lit(label).alias("status"),
                        F.col("geo_source"),
                        F.lit("00").alias("codigo_departamento"),
                        F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                    )
                
                all_dfs.append(df_final.filter(F.col("total_weight").isNotNull()))
            except:
                continue

        if all_dfs:
            df_silver = all_dfs[0]
            for d in all_dfs[1:]: df_silver = df_silver.unionByName(d)
            
            # Filtro de limpieza final urbana/rural
            df_silver = df_silver.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"   ✅ Tabla Delta {silver_table} creada exitosamente.")
            
            # Breve reporte de control para verificar que cargó departamentos
            df_silver.groupBy("month", "status").count().orderBy("month", "status").show(4)
        else:
            print(f"   ⚠️ No se encontraron datos válidos para {y}.")
            
    except Exception as e:
        print(f"   ❌ Error crítico en el año {y}: {str(e)[:100]}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

silver_table_2025 = "dane_silver_lh.labor_2025"

print("🕵️‍♂️ Iniciando auditoría de integridad para el año 2025 (Nuevo Esquema)...")

# 1. Cargamos la tabla Silver del 2025
df_2025 = spark.read.table(silver_table_2025)

# 2. Agregación de control analítico: Totales expandidos por Mes, Departamento y Estado Laboral
df_audit = df_2025.groupBy("month", "codigo_departamento", "status") \
    .agg(
        F.count("*").alias("total_encuestas_microdato"), # Conteo de registros puros en el archivo plano
        F.sum("total_weight").alias("poblacion_expandida")  # Sumatoria con el FEX homogeneizado
    ) \
    .orderBy("month", "codigo_departamento", "status")

# 3. Guardamos en caché para acelerar las múltiples vistas de la auditoría
df_audit.cache()

print("\n📊 1. Vista General: Población Expandida para principales Departamentos (Enero 2025):")
print("-" * 80)
# Mostramos una muestra del comportamiento de los principales motores económicos en el mes 1
df_audit.filter(F.col("month") == 1) \
        .filter(F.col("codigo_departamento").isin("05", "08", "11", "13", "15")) \
        .withColumn("poblacion_expandida", F.format_number("poblacion_expandida", 2)) \
        .show(20, truncate=False)

print("\n📈 2. Consolidado Nacional Mensual (Verificación de Estacionalidad del Mercado Laboral):")
print("-" * 80)
# Esto nos permite ver la consistencia total mes a mes del año completo
df_2025.groupBy("month", "status") \
    .agg(F.format_number(F.sum("total_weight"), 2).alias("total_poblacion_nacional")) \
    .orderBy("month", "status") \
    .show(24, truncate=False)

print("\n🛡️ 3. Check de Calidad de Datos (Reglas de Oro del Data Governance):")
print("-" * 80)
nulos_depto = df_2025.filter(F.col("codigo_departamento").isNull() | (F.col("codigo_departamento") == "")).count()
nulos_peso = df_2025.filter(F.col("total_weight").isNull() | (F.col("total_weight") <= 0)).count()
geo_sources_unicos = [r.geo_source for r in df_2025.select("geo_source").distinct().collect()]

print(f"🔹 Registros con código de departamento huérfano (Nulo/Vacío): {nulos_depto}")
print(f"🔹 Registros con factor de expansión corrupto (Nulo o <= 0): {nulos_peso}")
print(f"🔹 Categorías geográficas mapeadas internamente (CLASE): {geo_sources_unicos}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## SILVER 2025 Y 2026 JUNTOS: RESTAURADOS

# CELL ********************

## ============================================================================
## 🚀 SILVER 2025-2026: EL CIERRE DE LA SERIE
## ============================================================================
from pyspark.sql import functions as F
import re

new_years = [2025, 2026]

for y in new_years:
    print(f"\n🚀 Procesando Silver {y}...")
    bronze_path = f"abfss://f5879c16-6832-4003-90dd-eb2c10497cc0@onelake.dfs.fabric.microsoft.com/ecf22981-1012-4b17-861f-62880aa61238/Files/raw/dane/year={y}/"
    silver_table = f"dane_silver_lh.labor_{y}"

    try:
        df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
                      .withColumn("file_name", F.input_file_name()) \
                      .withColumn("fn_low", F.lower(F.col("file_name")))

        df_meta = df_raw.withColumn(
            "status_file",
            F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
            .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
            .otherwise("otro")
        ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
         .filter(~F.col("fn_low").rlike("caracteristicas|generales|seguridad|salud|educaci|otras|formas|vivienda"))

        unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
        all_dfs = []

        for fn in unique_files:
            match = re.search(r"month=(\d+)", fn)
            if not match: continue
            m = int(match.group(1))

            df_file = df_meta.filter(F.col("file_name") == fn)
            label = df_file.select("status_file").limit(1).collect()[0][0]

            sample_rows = df_file.limit(2).collect()
            if not sample_rows: continue
            
            header_val = sample_rows[0]['value']
            if "FEX" not in header_val.upper() and "DIRECTORIO" not in header_val.upper() and len(sample_rows) > 1:
                header_val = sample_rows[1]['value']

            delim = ";" if ";" in header_val else ","
            cols = [c.strip().upper() for c in header_val.split(delim)]
            
            idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR"]))
            idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
            
            df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                .withColumn("split_data", F.split(F.col("value"), delim)) \
                .withColumn("geo_source", F.when(F.col("fn_low").rlike("cabe|urban"), "cabecera")
                                         .when(F.col("fn_low").rlike("resto|rural"), "resto")
                                         .otherwise("area"))
            
            if label == "desocupado" and idx_dsi is not None:
                df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

            df_final = df_proc.select(
                F.lit(y).alias("year"),
                F.lit(m).alias("month"),
                F.lit(label).alias("status"),
                F.col("geo_source"),
                F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '"', ''), ",", ".").cast("double").alias("weight")
            ).filter(F.col("weight").isNotNull())
            
            all_dfs.append(df_final)

        if all_dfs:
            df_silver = all_dfs[0]
            for d in all_dfs[1:]: df_silver = df_silver.unionByName(d)
            df_silver = df_silver.withColumn("is_national_total", F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"   ✅ Silver {y} guardado exitosamente.")
        else:
            print(f"   ⚠️ No se encontraron datos válidos para {y}.")
    except Exception as e:
        print(f"   ❌ Error en {y}: {str(e)[:100]}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

# =====================================================================
# 🧱 CONFIGURATION & ENVIRONMENT
# =====================================================================
print("🚀 Initializing Unified Silver Pipeline: DANE Labor Market...")

# Target years to process
target_years = [2022, 2023, 2024, 2025, 2026]

# Note: We replaced the hardcoded abfss:// URLs with standard relative paths 
# since we fixed the Workspace connection in the Bronze layer.
base_bronze_path = "Files/raw/dane"
silver_db = "dane_silver_lh" # Make sure this Lakehouse exists and is connected!

# =====================================================================
# ⚙️ CORE PROCESSING ENGINE
# =====================================================================
def process_dane_year(year):
    print(f"\n=======================================================")
    print(f"🕵️‍♂️ Processing Year: {year} | GEIH Microdata Scanner")
    print(f"=======================================================")
    
    bronze_path = f"{base_bronze_path}/year={year}/"
    silver_table = f"labor_{year}"
    
    try:
        # 1. Read files and extract metadata
        df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
            .withColumn("file_name", F.input_file_name()) \
            .withColumn("fn_low", F.lower(F.col("file_name")))
            
        # 2. Semantic Classification
        df_meta = df_raw.withColumn(
            "status_file",
            F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
            .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
            .otherwise("otro")
        ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
         .filter(~F.col("fn_low").rlike("caracteristicas|generales|seguridad|salud|educaci|otras|formas|vivienda|ingresos|fuerza|inactivos|juvenil|migracion"))

        unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
        
        if not unique_files:
            print(f"⚠️ No valid labor data found for {year}.")
            return

        print(f"📂 Detected {len(unique_files)} core files. Commencing index tracking...")
        
        processed_dfs = []

        # 3. Dynamic Schema Tracker (File by File)
        for fn in unique_files:
            match = re.search(r"month=(\d+)", fn)
            if not match: continue
            m = int(match.group(1))

            df_file = df_meta.filter(F.col("file_name") == fn)
            
            # Use safe collection with fallback
            first_rows = df_file.limit(3).collect()
            if not first_rows: continue
            
            label = first_rows[0]['status_file']
            
            # Find the header row robustly
            header_val = None
            for row in first_rows:
                if "FEX" in row['value'].upper() or "DIRECTORIO" in row['value'].upper() or "DPTO" in row['value'].upper():
                    header_val = row['value']
                    break
            
            if not header_val: continue

            delim = ";" if ";" in header_val else ","
            cols = [c.strip().upper().replace('"', '') for c in header_val.split(delim)]
            
            try:
                # --- DYNAMIC QUAD-TRACKER ---
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR"]))
                idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
                idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                # Remove header row and tokenize
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), delim))
                
                # Geographic Mapping (Cabecera vs Resto)
                if idx_clase is not None:
                    df_proc = df_proc.withColumn(
                        "geo_source",
                        F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
                         .when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "2", "resto")
                         .otherwise("cabecera")
                    )
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                # DSI Methodological Filter for Unemployed
                if label == "desocupado" and idx_dsi is not None:
                    # Added robust split for floats (e.g., "1.0")
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                # Final Schema Projection
                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"),
                    F.lit(m).alias("month"),
                    F.lit(label).alias("status"),
                    F.col("geo_source"),
                    depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                # Write to an intermediate checkpoint to break the execution graph!
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                # Silently skip misaligned structural files as per original logic
                continue

        # 4. Global Union and Persistence
        if processed_dfs:
            # Reconstruct the DataFrame from the cached parts
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: 
                df_silver_unified = df_silver_unified.unionByName(d)
            
            # Final Clean
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            # Write to Lakehouse
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            
            print(f"✅ SILVER {year} CONSOLIDATED SUCCESSFULLY: {silver_table}")
            
            # Free up RAM
            for d in processed_dfs:
                d.unpersist()
        else:
            print(f"❌ Critical Error: No files could be aligned for {year}.")

    except Exception as e:
         print(f"❌ Fatal error processing year {year}: {str(e)[:100]}")

# =====================================================================
# 🚀 EXECUTION TRIGGER
# =====================================================================
for y in target_years:
    process_dane_year(y)

print("\n🎉 ALL YEARS PROCESSED. SILVER LAYER COMPLETE.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pyspark.sql.functions as F

print("📊 Initiating Full Historical Silver QA Protocol (2022-2026)...")

# 1. Cargar y unir dinámicamente toda la historia
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
df_all_years = None

for y in years:
    try:
        df_temp = spark.table(f"labor_{y}")
        if df_all_years is None:
            df_all_years = df_temp
        else:
            df_all_years = df_all_years.unionByName(df_temp)
    except Exception as e:
        print(f"⚠️ No se pudo cargar labor_{y}. Saltando...")

# ==========================================
# TEST: Validación Macroeconómica Histórica
# ==========================================
print("🧮 Validación Demográfica Histórica (Verificando promedios mensuales)")

df_macro_history = df_all_years.groupBy("year", "status").agg(
    F.count("*").alias("raw_survey_rows"),
    F.round(F.sum("total_weight"), 0).alias("total_yearly_weight"),
    # Dividimos el peso total entre los meses distintos reportados ese año
    F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_population")
).orderBy("year", "status")

display(df_macro_history)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

# =====================================================================
# 🧱 CONFIGURATION & ENVIRONMENT
# =====================================================================
print("🚀 Initializing Master Silver Pipeline: DANE Historical (2018-2026)...")

target_years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
base_bronze_path = "Files/raw/dane"
silver_db = "dane_silver_lh" 

# =====================================================================
# 🕰️ ENGINE 1: LEGACY SCANNER (Marco 2005 | Years 2018-2021)
# =====================================================================
def process_legacy_year(year):
    print(f"\n=======================================================")
    print(f"🕰️ Processing Legacy Year: {year} | GEIH Marco 2005 Scanner")
    print(f"=======================================================")
    
    bronze_path = f"{base_bronze_path}/year={year}/"
    silver_table = f"labor_{year}"
    
    try:
        df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
            .withColumn("file_name", F.input_file_name()) \
            .withColumn("fn_low", F.lower(F.col("file_name")))
            
        df_meta = df_raw.withColumn(
            "status_file",
            F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu|inact|des"), "desocupado")
            .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no|inact"), "ocupado")
            .otherwise("otro")
        ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
         .filter(~F.col("fn_low").rlike("caracteristicas|generales|vivienda|fuerza|seguridad|ingresos"))

        unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
        if not unique_files:
            print(f"⚠️ No valid legacy data found for {year}.")
            return
            
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

            if "\t" in header_val: delim = "\t"
            elif ";" in header_val: delim = ";"
            else: delim = ","
            
            cols = [c.strip().upper().replace('"', '') for c in header_val.split(delim)]
            
            try:
                # --- LEGACY SUPER-TRACKER ---
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), delim))
                
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

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ LEGACY SILVER {year} CONSOLIDATED SUCCESSFULLY")
            for d in processed_dfs: d.unpersist()
        else:
            print(f"❌ Critical Error: No legacy files aligned for {year}.")

    except Exception as e:
         print(f"❌ Fatal error in legacy year {year}: {str(e)[:100]}")

# =====================================================================
# 🚀 ENGINE 2: MODERN SCANNER (Marco 2018 | Years 2022-2026)
# =====================================================================
def process_modern_year(year):
    print(f"\n=======================================================")
    print(f"🕵️‍♂️ Processing Modern Year: {year} | GEIH Marco 2018 Scanner")
    print(f"=======================================================")
    
    bronze_path = f"{base_bronze_path}/year={year}/"
    silver_table = f"labor_{year}"
    
    try:
        df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
            .withColumn("file_name", F.input_file_name()) \
            .withColumn("fn_low", F.lower(F.col("file_name")))
            
        df_meta = df_raw.withColumn(
            "status_file",
            F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
            .when(F.col("fn_low").rlike("ocupa") & ~F.col("fn_low").contains("deso"), "ocupado")
            .otherwise("otro")
        ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
         .filter(~F.col("fn_low").rlike("caracteristicas|generales|seguridad|salud|educaci|otras|formas|vivienda|ingresos|fuerza|inactivos|juvenil|migracion"))

        unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
        if not unique_files:
            print(f"⚠️ No valid modern data found for {year}.")
            return
            
        processed_dfs = []

        for fn in unique_files:
            match = re.search(r"month=(\d+)", fn)
            if not match: continue
            m = int(match.group(1))

            df_file = df_meta.filter(F.col("file_name") == fn)
            first_rows = df_file.limit(3).collect()
            if not first_rows: continue
            
            label = first_rows[0]['status_file']
            
            header_val = None
            for row in first_rows:
                if "FEX" in row['value'].upper() or "DIRECTORIO" in row['value'].upper() or "DPTO" in row['value'].upper():
                    header_val = row['value']
                    break
            
            if not header_val: continue

            delim = ";" if ";" in header_val else ","
            cols = [c.strip().upper().replace('"', '') for c in header_val.split(delim)]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR"]))
                idx_depto = next((i for i, c in enumerate(cols) if c in ["DPTO", "COD_DPTO"]), None)
                idx_clase = next((i for i, c in enumerate(cols) if c == "CLASE"), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn(
                        "geo_source",
                        F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera")
                         .when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "2", "resto")
                         .otherwise("cabecera")
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

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ MODERN SILVER {year} CONSOLIDATED SUCCESSFULLY")
            for d in processed_dfs: d.unpersist()
        else:
            print(f"❌ Critical Error: No modern files aligned for {year}.")

    except Exception as e:
         print(f"❌ Fatal error in modern year {year}: {str(e)[:100]}")

# =====================================================================
# 🚦 EXECUTION ROUTER (The Architectural Fork)
# =====================================================================
for y in target_years:
    if y < 2022:
        process_legacy_year(y)
    else:
        process_modern_year(y)

print("\n🎉 ALL YEARS PROCESSED. HISTORICAL SILVER LAYER COMPLETE.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

print("🚀 Initiating Legacy Patch: Repairing 2018-2021 with Whitespace Sniffer...")

base_bronze_path = "Files/raw/dane"
legacy_years = [2018, 2019, 2020]

def process_legacy_patch(year):
    print(f"\n=======================================================")
    print(f"🔧 Patching Legacy Year: {year} | GEIH Marco 2005")
    print(f"=======================================================")
    
    bronze_path = f"{base_bronze_path}/year={year}/"
    silver_table = f"labor_{year}"
    
    try:
        df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
            .withColumn("file_name", F.input_file_name()) \
            .withColumn("fn_low", F.lower(F.col("file_name")))
            
        df_meta = df_raw.withColumn(
            "status_file",
            F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu|inact|des"), "desocupado")
            .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no|inact"), "ocupado")
            .otherwise("otro")
        ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
         .filter(~F.col("fn_low").rlike("caracteristicas|generales|vivienda|fuerza|seguridad|ingresos"))

        unique_files = [row.file_name for row in df_meta.select("file_name").distinct().collect()]
        if not unique_files: return
            
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

            # ========================================================
            # 🚨 THE FIX: ULTIMATE WHITESPACE SNIFFER
            # ========================================================
            if ";" in header_val:
                py_delim, sp_delim = ";", ";"
            elif "," in header_val:
                py_delim, sp_delim = ",", ","
            else:
                py_delim, sp_delim = None, r"\s+" # Regex for ANY whitespace (spaces or tabs)
            
            # Split the Python array to find indexes
            if py_delim:
                cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else:
                cols = [c.strip().upper().replace('"', '') for c in header_val.split()] # Default handles all whitespace
            # ========================================================
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                # Apply the specific delimiter to Spark
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

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ LEGACY SILVER {year} PATCHED SUCESSFULLY")
            for d in processed_dfs: d.unpersist()

    except Exception as e:
         print(f"❌ Error patching {year}: {str(e)[:100]}")

# Run the patch
for y in legacy_years:
    process_legacy_patch(y)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

# 👉 CAMBIA ESTO A 2018, 2019, o 2020
year = 2018 

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo para {year} (Bloqueo Total de 'Area' Reactivado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingresos|vivienda|seguridad|formas|inact|inactivos|fuerza|caracteristicas|otras|area"))
     # ⛔ NOTA ARQUITECTÓNICA: 'area' está de vuelta en la lista negra para evitar el doble conteo.

    # DEDUPLICADOR: Ignorar archivos clonados (.CSV vs .csv)
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            if ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

# 👉 CAMBIA ESTO A 2018, 2019, o 2020
year = 2019

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo para {year} (Bloqueo Total de 'Area' Reactivado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingresos|vivienda|seguridad|formas|inact|inactivos|fuerza|caracteristicas|otras|area"))
     # ⛔ NOTA ARQUITECTÓNICA: 'area' está de vuelta en la lista negra para evitar el doble conteo.

    # DEDUPLICADOR: Ignorar archivos clonados (.CSV vs .csv)
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            if ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

# 👉 Ejecuta esto primero con 2021, y luego cámbialo a 2015
year = 2021 

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Aplicando Deduplicador Extremo para {year} (Extracción de Nombre Base)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(
        F.col("status_file").isin("ocupado", "desocupado")
    ).filter(
        ~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|trim|secundario|subempleo|area|área")
    )

    # =========================================================================
    # 🛡️ DEDUPLICADOR EXTREMO
    # Quitamos la extensión (.csv o .txt) y nos quedamos solo con el nombre base y el mes.
    # Garantiza que sin importar cuántos clones o subcarpetas haya, solo pasa 1 archivo.
    # =========================================================================
    df_meta = df_meta.withColumn("base_name", F.regexp_replace(F.element_at(F.split(F.col("fn_low"), "/"), -1), r"\.[a-z0-9]+$", ""))
    df_meta = df_meta.withColumn("mes_ruta", F.regexp_extract(F.col("fn_low"), r"month=(\d+)", 1))
    
    df_unique_files = df_meta.select("file_name", "mes_ruta", "base_name").dropDuplicates(["mes_ruta", "base_name"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            if "\t" in header_val: py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} DEDUPLICADO Y PROCESADO CON ÉXITO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2017 

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2016

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Aplicando Deduplicador Extremo para {year} (El Bug de 'NOviembre' Resuelto)...")

try:
    # Mantenemos el lineSep por los archivos raros de Mac/Windows
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true") \
        .option("lineSep", "\n") \
        .load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 LA CORRECCIÓN MAESTRA: Especificamos "no ocu" para que no mate a la palabra "noviembre"
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu|no ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no%20ocu|no_ocu|no ocu"), "ocupado")
        .otherwise("otro")
    ).filter(
        F.col("status_file").isin("ocupado", "desocupado")
    ).filter(
        ~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|trim|secundario|subempleo|area|área")
    )

    df_meta = df_meta.withColumn("base_name", F.regexp_replace(F.element_at(F.split(F.col("fn_low"), "/"), -1), r"\.[a-z0-9]+$", ""))
    df_meta = df_meta.withColumn("mes_ruta", F.regexp_extract(F.col("fn_low"), r"month=(\d+)", 1))
    
    df_unique_files = df_meta.select("file_name", "mes_ruta", "base_name").dropDuplicates(["mes_ruta", "base_name"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
        processed_dfs = []
        for fn in unique_files:
            match = re.search(r"month=(\d+)", fn)
            if not match: continue
            m = int(match.group(1))

            df_file = df_meta.filter(F.col("file_name") == fn)
            first_rows = df_file.limit(30).collect() 
            if not first_rows: continue
            
            label = first_rows[0]['status_file']
            
            header_val = None
            for row in first_rows:
                if any(x in row['value'].upper() for x in ["FEX", "DIRECTORIO", "DPTO", "MES", "AREA"]):
                    header_val = row['value']
                    break
            
            if not header_val: continue

            if "\t" in header_val: py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y MES 11 REPARADO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2015 

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Aplicando Deduplicador Extremo para {year} (El Bug de 'NOviembre' Resuelto)...")

try:
    # Mantenemos el lineSep por los archivos raros de Mac/Windows
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true") \
        .option("lineSep", "\n") \
        .load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 LA CORRECCIÓN MAESTRA: Especificamos "no ocu" para que no mate a la palabra "noviembre"
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu|no ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no%20ocu|no_ocu|no ocu"), "ocupado")
        .otherwise("otro")
    ).filter(
        F.col("status_file").isin("ocupado", "desocupado")
    ).filter(
        ~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|trim|secundario|subempleo|area|área")
    )

    df_meta = df_meta.withColumn("base_name", F.regexp_replace(F.element_at(F.split(F.col("fn_low"), "/"), -1), r"\.[a-z0-9]+$", ""))
    df_meta = df_meta.withColumn("mes_ruta", F.regexp_extract(F.col("fn_low"), r"month=(\d+)", 1))
    
    df_unique_files = df_meta.select("file_name", "mes_ruta", "base_name").dropDuplicates(["mes_ruta", "base_name"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
        processed_dfs = []
        for fn in unique_files:
            match = re.search(r"month=(\d+)", fn)
            if not match: continue
            m = int(match.group(1))

            df_file = df_meta.filter(F.col("file_name") == fn)
            first_rows = df_file.limit(30).collect() 
            if not first_rows: continue
            
            label = first_rows[0]['status_file']
            
            header_val = None
            for row in first_rows:
                if any(x in row['value'].upper() for x in ["FEX", "DIRECTORIO", "DPTO", "MES", "AREA"]):
                    header_val = row['value']
                    break
            
            if not header_val: continue

            if "\t" in header_val: py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y MES 11 REPARADO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import traceback
from pyspark.sql import functions as F

year = 2015

print("🔍 INICIANDO CIRUGÍA DE PRECISIÓN EN MES 11...")

# Decodificamos la URL automáticamente (%20 a espacio) para evitar trampas
df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(f"Files/raw/dane/year={year}/month=11/") \
    .withColumn("file_name", F.expr("url_decode(input_file_name())")) \
    .withColumn("fn_low", F.lower(F.col("file_name")))

df_meta = df_raw.withColumn(
    "status_file",
    F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu|no ocu"), "desocupado")
    .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
    .otherwise("otro")
).filter(F.col("status_file") == "ocupado") \
 .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|trim|secundario|subempleo|area|área"))

df_unique_files = df_meta.select("file_name").distinct()
files = [r.file_name for r in df_unique_files.collect()]

print(f"Archivos a procesar detectados: {len(files)}\n")

for fn in files:
    print("-" * 60)
    print(f"🚀 Intentando procesar: {fn.split('/')[-1]}")
    try:
        df_file = df_meta.filter(F.col("file_name") == fn)
        first_rows = df_file.limit(30).collect()
        
        if not first_rows:
            print("❌ El archivo está vacío o no se pudo particionar en filas.")
            continue
        
        header_val = None
        for row in first_rows:
            if any(x in row['value'].upper() for x in ["FEX", "DIRECTORIO", "DPTO", "MES", "AREA"]):
                header_val = row['value']
                break
        
        if not header_val:
            print("❌ No se encontró el encabezado en las primeras 30 filas.")
            continue

        print(f"✔️ Encabezado detectado (primeros 40 chars): {header_val[:40]}")
        
        # Detectamos delimitador
        if "\t" in header_val: sp_delim = "\t"
        elif ";" in header_val: sp_delim = ";"
        elif "," in header_val: sp_delim = ","
        else: sp_delim = r"\s+" 
        
        cols = [c.strip().upper().replace('"', '') for c in header_val.split(sp_delim)]
        
        # Buscamos índices
        idx_peso = next((i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"])), None)
        idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
        
        print(f"✔️ Índices -> Peso: {idx_peso}, Clase: {idx_clase}")
        
        if idx_peso is None:
            print("❌ ERROR: No se encontró la columna de Peso (FEX) en este archivo.")
            continue
            
        df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
            .withColumn("split_data", F.split(F.col("value"), sp_delim))
        
        # Cálculo de prueba
        peso_val = F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double")
        df_final = df_proc.select(peso_val.alias("total_weight")).filter(F.col("total_weight").isNotNull())
        
        # Acción en Spark (Aquí es donde suele estallar si hay error de datos)
        count_rows = df_final.count()
        sum_weight = df_final.agg(F.sum("total_weight")).collect()[0][0]
        
        print(f"✅ ¡ÉXITO! Filas procesadas: {count_rows} | Población Total: {sum_weight}")
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN SPARK: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2014

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2013

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2012

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2011

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2010

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2009

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2008

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2007

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo adaptativo para {year} (Motor TSV y Tildes Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ORTOGRÁFICA: Bloqueo de raíces y tildes de 2017
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # 🚨 EL DETECTOR DE TABULADORES (TSV - El Salvador del 2017)
            if "\t" in header_val: 
                py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: 
                py_delim, sp_delim = ";", ";"
            elif "," in header_val: 
                py_delim, sp_delim = ",", ","
            else: 
                py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO Y PARCHEADO PARA TXT!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2006 

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo para {year} (Filtro Anti-Triple Empleo Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ECH: Bloqueo de empleos secundarios y subempleo
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área|secundario|subempleo"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # DETECTOR DE TABULADORES (TSV)
            if "\t" in header_val: py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2005

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo para {year} (Filtro Anti-Triple Empleo Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ECH: Bloqueo de empleos secundarios y subempleo
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área|secundario|subempleo"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # DETECTOR DE TABULADORES (TSV)
            if "\t" in header_val: py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F
from pyspark.sql.types import *

year = 2004

bronze_path = f"Files/raw/dane/year={year}/"
silver_table = f"labor_{year}"

print(f"🕵️‍♂️ Iniciando escaneo para {year} (Filtro Anti-Triple Empleo Activado)...")

try:
    df_raw = spark.read.format("text").option("recursiveFileLookup", "true").load(bronze_path) \
        .withColumn("file_name", F.input_file_name()) \
        .withColumn("fn_low", F.lower(F.col("file_name")))
        
    # 🚨 ACTUALIZACIÓN ECH: Bloqueo de empleos secundarios y subempleo
    df_meta = df_raw.withColumn(
        "status_file",
        F.when(F.col("fn_low").rlike("deso|no%20ocu|no_ocu"), "desocupado")
        .when(F.col("fn_low").rlike("ocupa|ocu") & ~F.col("fn_low").rlike("deso|no"), "ocupado")
        .otherwise("otro")
    ).filter(F.col("status_file").isin("ocupado", "desocupado")) \
     .filter(~F.col("fn_low").rlike("ingreso|vivienda|seguridad|forma|inact|fuerza|caracter|otra|area|área|secundario|subempleo"))

    # DEDUPLICADOR
    df_unique_files = df_meta.select("file_name", "fn_low").dropDuplicates(["fn_low"])
    unique_files = [row.file_name for row in df_unique_files.collect()]

    if not unique_files:
        print(f"⚠️ No se encontraron archivos válidos para {year}.")
    else:
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

            # DETECTOR DE TABULADORES (TSV)
            if "\t" in header_val: py_delim, sp_delim = "\t", "\t"
            elif ";" in header_val: py_delim, sp_delim = ";", ";"
            elif "," in header_val: py_delim, sp_delim = ",", ","
            else: py_delim, sp_delim = None, r"\s+" 
            
            if py_delim: cols = [c.strip().upper().replace('"', '') for c in header_val.split(py_delim)]
            else: cols = [c.strip().upper().replace('"', '') for c in header_val.split()]
            
            try:
                idx_peso = next(i for i, c in enumerate(cols) if any(x in c for x in ["FEX", "PESO", "FACTOR", "FAC"]))
                idx_depto = next((i for i, c in enumerate(cols) if any(x in c for x in ["DPTO", "COD_DPTO", "DEP", "DEPTO"])), None)
                idx_clase = next((i for i, c in enumerate(cols) if c in ["CLASE", "AREA"]), None)
                idx_dsi = next((i for i, c in enumerate(cols) if "DSI" in c), None)
                
                df_proc = df_file.filter(~F.col("value").contains(header_val[:20])) \
                    .withColumn("split_data", F.split(F.col("value"), sp_delim))
                
                if idx_clase is not None:
                    df_proc = df_proc.withColumn("geo_source", F.when(F.regexp_replace(F.col("split_data")[idx_clase], '[ "]', '') == "1", "cabecera").otherwise("resto"))
                else:
                    df_proc = df_proc.withColumn("geo_source", F.lit("cabecera"))
                
                if label == "desocupado" and idx_dsi is not None:
                    df_proc = df_proc.filter(F.split(F.regexp_replace(F.trim(F.col("split_data")[idx_dsi]), '"', ''), "\.")[0] == "1")

                depto_col = F.lpad(F.regexp_replace(F.col("split_data")[idx_depto], '[ "]', ''), 2, "0") if idx_depto is not None else F.lit("00")
                
                df_final = df_proc.select(
                    F.lit(year).alias("year"), F.lit(m).alias("month"), F.lit(label).alias("status"),
                    F.col("geo_source"), depto_col.alias("codigo_departamento"),
                    F.regexp_replace(F.regexp_replace(F.col("split_data")[idx_peso], '[ "]', ''), ",", ".").cast("double").alias("total_weight")
                ).filter(F.col("total_weight").isNotNull())
                
                df_final.cache()
                processed_dfs.append(df_final)
                
            except Exception as e:
                continue

        if processed_dfs:
            df_silver_unified = processed_dfs[0]
            for d in processed_dfs[1:]: df_silver_unified = df_silver_unified.unionByName(d)
            df_silver_unified = df_silver_unified.filter(F.col("geo_source").isin("cabecera", "resto"))
            
            spark.sql(f"DROP TABLE IF EXISTS {silver_table}")
            df_silver_unified.write.format("delta").mode("overwrite").saveAsTable(silver_table)
            print(f"✅ ¡AÑO {year} PROCESADO CON ÉXITO!")
            for d in processed_dfs: d.unpersist()
            
            df_silver_unified.groupBy("month", "status").agg(F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop")).orderBy("month", "status").show(24)

except Exception as e:
     print(f"❌ Error Crítico en {year}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pyspark.sql.functions as F

print("🔍 INICIANDO AUDITORÍA GLOBAL DE LA CAPA SILVER (2004 - 2026)...")
print("-" * 65)

years_to_check = list(range(2004, 2027))
audit_results = []

for y in years_to_check:
    table_name = f"labor_{y}"
    try:
        # Validamos si la tabla existe en tu Lakehouse
        if spark.catalog.tableExists(table_name):
            df = spark.table(table_name)
            
            # Calculamos las métricas macro
            metrics = df.groupBy("status").agg(
                F.round(F.sum("total_weight") / F.countDistinct("month"), 0).alias("avg_monthly_pop"),
                F.countDistinct("month").alias("meses_procesados")
            ).collect()
            
            for row in metrics:
                audit_results.append({
                    "Año": y,
                    "Estado": row["status"],
                    "Meses_con_Datos": row["meses_procesados"],
                    "Poblacion_Mensual_Promedio": int(row["avg_monthly_pop"])
                })
            print(f"✔️ {y}: Tabla encontrada y auditada.")
        else:
            print(f"⚠️ {y}: Tabla NO encontrada (Falta procesar).")
            
    except Exception as e:
         print(f"❌ {y}: Error al leer la tabla - {str(e)[:40]}")

print("-" * 65)

# Mostramos el reporte final consolidado
if audit_results:
    df_audit = spark.createDataFrame(audit_results).orderBy("Año", "Estado")
    print("\n📊 REPORTE DE CALIDAD HISTÓRICA:")
    display(df_audit)
else:
    print("\n❌ No se encontró ninguna tabla en la capa Silver.")

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
