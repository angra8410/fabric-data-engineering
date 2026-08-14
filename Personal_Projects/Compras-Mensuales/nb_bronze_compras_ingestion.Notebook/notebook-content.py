# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "daf0bb05-c5d0-4388-9708-23e3b630b4e2",
# META       "default_lakehouse_name": "compras_bronze_lh",
# META       "default_lakehouse_workspace_id": "b14581ac-9906-43e2-809c-c2fd4315ad5b",
# META       "known_lakehouses": [
# META         {
# META           "id": "daf0bb05-c5d0-4388-9708-23e3b630b4e2"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

pip install pandas openpyxl

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
from pyspark.sql import functions as F

year = 2026
file_name = "Trazabilidad de Estudio (3)(OR).csv"
csv_file_path = f"Files/raw/compras/year={year}/{file_name}"
bronze_table = f"compras_or_{year}_bronze"

print("Iniciando aterrizaje de la pestaña OR en la tabla Bronze...")

# 1. Read the raw data with explicit delimiter and encoding
df_raw = spark.read.format("csv") \
    .option("header", "true") \
    .option("sep", ";") \
    .option("encoding", "ISO-8859-1") \
    .option("inferSchema", "true") \
    .load(csv_file_path)

# 2. Clean the column names (Replacing spaces with underscores)
clean_columns = [re.sub(r'[ ,;{}()\n\t=]', '_', col).strip('_') for col in df_raw.columns]
df_clean_schema = df_raw.toDF(*clean_columns)

print(f"Esquema corregido: {df_clean_schema.columns}")

# 3. Inject core bronze audit tracking fields
df_bronze = df_clean_schema.select(
    "*",
    F.input_file_name().alias("source_file_path"),
    F.lit("OR").alias("source_sheet_name"),
    F.current_timestamp().alias("ingestion_date")
)

# 4. Write cleanly out to Delta
df_bronze.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(bronze_table)

print(f" [✓] Evidencia guardada exitosamente en Delta Table: {bronze_table}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pandas as pd
import re
from pyspark.sql import functions as F

year = 2026

# Explicitly target the exact file name we know has the correct tabs
excel_file_name = "Trazabilidad de Estudio (3).xlsx"
excel_local_path = f"/lakehouse/default/Files/raw/compras/year={year}/{excel_file_name}"

tabs_to_process = ["EXITO", "D1", "OR"]

print(f"Targeting specific file: {excel_local_path}...\n")

for tab in tabs_to_process:
    bronze_table = f"compras_{tab.lower()}_{year}_bronze"
    print(f"Extracting tab '{tab}'...")
    
    try:
        # 1. Read specific tab using Pandas
        pdf = pd.read_excel(excel_local_path, sheet_name=tab)
        
        # 2. Clean column names in Pandas to prevent Delta schema errors
        pdf.columns = [re.sub(r'[ ,;{}()\n\t=]', '_', col).strip('_') for col in pdf.columns]
        
        # 3. Convert to Spark DataFrame (casting all to string to prevent schema inference conflicts)
        df_sheet = spark.createDataFrame(pdf.astype(str))
        
        # 4. Inject core bronze audit tracking fields
        df_bronze = df_sheet.select(
            "*",
            F.lit(excel_file_name).alias("source_file_path"),
            F.lit(tab).alias("source_sheet_name"),
            F.current_timestamp().alias("ingestion_date")
        )
        
        # 5. Write cleanly out to Delta
        df_bronze.write \
            .format("delta") \
            .mode("overwrite") \
            .saveAsTable(bronze_table)
            
        print(f" [✓] Successfully saved to Delta table: {bronze_table}\n")
        
    except Exception as e:
        print(f" [!] Error processing tab '{tab}': {e}\n")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

year = 2026
raw_path = f"Files/raw/compras/year={year}/"
bronze_table = f"compras_{year}_raw"

print(f"Iniciando aterrizaje crudo de compras para {year}...")
# 1. El escáner recursivo: leemos todo como texto plano
df_raw = spark.read.format("text") \
    .option("recursiveFileLookup", "true") \
    .load(raw_path)

df_raw_clean = df_raw.select(
    F.col("value").alias("raw_content"),
    F.input_file_name().alias("file_path"),
    F.current_timestamp().alias("ingestion_date")
)

spark.sql(f"DROP TABLE IF EXISTS {bronze_table}")


df_raw_clean.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(bronze_table)

print(f"Evidencia guardada exitosamente en: {bronze_table} ")



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
