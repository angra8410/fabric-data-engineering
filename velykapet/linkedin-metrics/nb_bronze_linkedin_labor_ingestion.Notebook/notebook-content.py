# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a",
# META       "default_lakehouse_name": "lh_bronze_linkedin_ingestion_labor",
# META       "default_lakehouse_workspace_id": "b14581ac-9906-43e2-809c-c2fd4315ad5b",
# META       "known_lakehouses": [
# META         {
# META           "id": "e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import warnings
import pandas as pd
import re
from datetime import datetime
from notebookutils import mssparkutils
from pyspark.sql import functions as F
from delta.tables import DeltaTable

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

target_tables = ["discovery", "engagement", "top_posts", "followers", "demographics"]

merge_keys = {
    "discovery": ["start_date", "end_date"],
    "engagement": ["date"],
    "followers": ["date"],
    "top_posts": ["post_url", "post_publish_date"],
    "demographics": ["start_date", "end_date", "top_demographics", "value"],
}

folder_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a/Files/raw_data"
date_keywords = {"date", "start date", "start_date", "end date", "post publish date"}

print("--- ESCANEANDO CARPETA ONELAKE ---")

files = mssparkutils.fs.ls(folder_path)
excel_files = sorted([f.path for f in files if f.path.endswith('.xlsx')])

if not excel_files:
    raise FileNotFoundError("❌ No se encontraron archivos de Excel (.xlsx) en la carpeta raw_data.")

print(f"Se encontraron {len(excel_files)} archivo(s). Procesando en orden cronológico:")
for fp in excel_files:
    print(f"   - {fp.split('/')[-1]}")

table_frames = {t: [] for t in target_tables}

for file_path in excel_files:
    file_name = file_path.split('/')[-1]
    print(f"\n=== Procesando archivo: {file_name} ===")

    file_dates = re.findall(r'\d{4}-\d{2}-\d{2}', file_name)
    file_start_date = datetime.strptime(file_dates[0], "%Y-%m-%d").date() if len(file_dates) >= 2 else None
    file_end_date = datetime.strptime(file_dates[1], "%Y-%m-%d").date() if len(file_dates) >= 2 else None

    excel_reader = pd.ExcelFile(file_path)
    sheet_names = excel_reader.sheet_names

    for sheet in sheet_names:
        table_name = sheet.strip().replace(" ", "_").replace("-", "_").lower()

        if table_name not in target_tables:
            continue

        print(f"  -> Procesando pestaña: {sheet}")
        pdf_raw = pd.read_excel(file_path, sheet_name=sheet, header=None)

        header_row_index = 0
        for idx, row in pdf_raw.iterrows():
            row_values = {str(val).strip().lower() for val in row.values if pd.notnull(val)}
            if row_values.intersection(date_keywords):
                header_row_index = idx
                break

        if table_name == "top_posts":
            pdf_eng = pdf_raw.iloc[header_row_index + 1:, 0:3].copy()
            pdf_eng.columns = ["post_url", "post_publish_date", "engagements"]
            pdf_eng = pdf_eng.dropna(subset=["post_url"])

            pdf_imp = pdf_raw.iloc[header_row_index + 1:, 4:7].copy()
            pdf_imp.columns = ["post_url", "post_publish_date", "impressions"]
            pdf_imp = pdf_imp.dropna(subset=["post_url"])

            pdf_eng["post_publish_date"] = pd.to_datetime(pdf_eng["post_publish_date"], errors='coerce')
            pdf_eng["engagements"] = pd.to_numeric(pdf_eng["engagements"], errors='coerce').fillna(0).astype(int)

            pdf_imp["post_publish_date"] = pd.to_datetime(pdf_imp["post_publish_date"], errors='coerce')
            pdf_imp["impressions"] = pd.to_numeric(pdf_imp["impressions"], errors='coerce').fillna(0).astype(int)

            pdf = pd.merge(pdf_eng, pdf_imp, on=["post_url", "post_publish_date"], how="outer")
            pdf["engagements"] = pdf["engagements"].fillna(0).astype(int)
            pdf["impressions"] = pdf["impressions"].fillna(0).astype(int)

            # Drop rows with no post_url (can collide on merge key otherwise)
            pdf = pdf.dropna(subset=["post_url"])
            pdf = pdf[pdf["post_url"].astype(str).str.strip() != ""]

        elif table_name == "discovery":
            # Summary Card layout: 2 columns, metric name + a dynamically-named
            # value column containing the date range (e.g. "6/1/2026 - 6/7/2026").
            pdf_sheet = pd.read_excel(file_path, sheet_name=sheet)

            date_range_col = None
            for col in pdf_sheet.columns:
                if re.search(r'\d{1,2}/\d{1,2}/\d{4}', str(col).replace("_", " ")):
                    date_range_col = col
                    break

            if date_range_col is not None and len(pdf_sheet.columns) == 2:
                dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', str(date_range_col).replace("_", " "))
                sheet_start = datetime.strptime(dates[0], "%m/%d/%Y").date() if len(dates) >= 2 else file_start_date
                sheet_end = datetime.strptime(dates[1], "%m/%d/%Y").date() if len(dates) >= 2 else file_end_date

                metric_col = [c for c in pdf_sheet.columns if c != date_range_col][0]

                # Pivot: one row, columns = metric names, values = metric values
                pdf_pivoted = pdf_sheet.set_index(metric_col).T.reset_index(drop=True)
                pdf_pivoted.columns = [
                    str(c).strip().replace(" ", "_").replace("(", "").replace(")", "").lower()
                    for c in pdf_pivoted.columns
                ]

                for col in pdf_pivoted.columns:
                    pdf_pivoted[col] = pd.to_numeric(pdf_pivoted[col], errors='coerce').fillna(0).astype('int64')

                pdf_pivoted["start_date"] = sheet_start
                pdf_pivoted["end_date"] = sheet_end
                pdf = pdf_pivoted
            else:
                # Fallback: already wide-format, just tag with file dates
                pdf = pdf_sheet.copy()
                pdf.columns = [str(c).strip().replace(" ", "_").replace("(", "").replace(")", "").lower() for c in pdf.columns]
                pdf["start_date"] = file_start_date
                pdf["end_date"] = file_end_date

        else:
            pdf = pd.read_excel(file_path, sheet_name=sheet, header=header_row_index)
            pdf.columns = [str(col).strip().replace(" ", "_").replace("(", "").replace(")", "").lower() for col in pdf.columns]

            for col in pdf.columns:
                if "date" in col:
                    pdf[col] = pd.to_datetime(pdf[col], errors='coerce')

        if table_name == "demographics":
            if "start_date" not in pdf.columns:
                pdf["start_date"] = file_start_date
            if "end_date" not in pdf.columns:
                pdf["end_date"] = file_end_date

        table_frames[table_name].append(pdf)

print("\n--- CONSOLIDANDO Y FUSIONANDO (MERGE) EN CAPA BRONZE ---")

for table_name, frames in table_frames.items():
    if not frames:
        continue

    pdf_all = pd.concat(frames, ignore_index=True)

    keys = merge_keys[table_name]

    # Deduplicate on merge key to avoid DELTA_MULTIPLE_SOURCE_ROW_MATCHING errors.
    # Keep the LAST occurrence (later file in chronological order wins if dates collide).
    if all(k in pdf_all.columns for k in keys):
        before = len(pdf_all)
        pdf_all = pdf_all.drop_duplicates(subset=keys, keep="last").reset_index(drop=True)
        after = len(pdf_all)
        if before != after:
            print(f"  -> '{table_name}': eliminadas {before - after} fila(s) duplicadas por clave de merge {keys}.")

    spark_df = spark.createDataFrame(pdf_all)

    table_exists = spark.catalog.tableExists(table_name)

    if table_exists:
        existing_cols = set(spark.read.table(table_name).columns)
        required_key_cols = set(merge_keys[table_name])
        if not required_key_cols.issubset(existing_cols):
            print(f"  -> Esquema antiguo incompatible detectado en '{table_name}'. Recreando tabla.")
            table_exists = False

    if not table_exists:
        (spark_df.write
         .format("delta")
         .mode("overwrite")
         .option("overwriteSchema", "true")
         .saveAsTable(table_name))
        print(f"  -> Tabla Bronze '{table_name}' creada con {spark_df.count()} fila(s).")
    else:
        delta_table = DeltaTable.forName(spark, table_name)
        merge_condition = " AND ".join([f"target.{k} = source.{k}" for k in keys])

        (delta_table.alias("target")
         .merge(spark_df.alias("source"), merge_condition)
         .whenMatchedUpdateAll()
         .whenNotMatchedInsertAll()
         .execute())

        total = spark.read.table(table_name).count()
        print(f"  -> Tabla Bronze '{table_name}' fusionada (MERGE). Total filas: {total}")

print("\n🚀 PROCESO TERMINADO: Todas las tablas Bronze acumulan historial de todos los archivos.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import warnings
import pandas as pd
from notebookutils import mssparkutils  # Herramienta nativa de Fabric

# 1. Eliminar advertencias molestas
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# 2. Tu ruta base de la carpeta contenedora
folder_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a/Files/raw_data"

print("--- ESCANEANDO CARPETA ONELAKE ---")

try:
    # Listar todos los archivos dentro de la carpeta
    files = mssparkutils.fs.ls(folder_path)
    
    # Filtrar para asegurarnos de abrir solo archivos .xlsx
    excel_files = [f.path for f in files if f.path.endswith('.xlsx')]

    if not excel_files:
        print("⚠️ No se encontraron archivos de Excel (.xlsx) en la carpeta.")
    else:
        print(f"Se encontraron {len(excel_files)} archivos de Excel.")
        
        # PROCESAR EL ARCHIVO MÁS RECIENTE
        # Como tus archivos tienen la fecha en el nombre (ej. 2026-06-01), 
        # al ordenarlos de forma descendente, el primero siempre será el último que llegó.
        excel_files.sort(reverse=True)
        file_path = excel_files[0]
        
        print(f"\nProcesando el archivo más nuevo encontrado: \n👉 {file_path.split('/')[-1]}")
        print("----------------------------------")

        # 3. Escanear las pestañas del archivo seleccionado
        excel_reader = pd.ExcelFile(file_path)
        sheet_names = excel_reader.sheet_names

        print(f"El archivo contiene {len(sheet_names)} pestañas:")
        for idx, sheet in enumerate(sheet_names, 1):
            print(f"   [{idx}] {sheet}")

except Exception as e:
    print(f"❌ Ocurrió un error al intentar leer la carpeta: {e}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

import warnings
import pandas as pd
import re
from notebookutils import mssparkutils  # Herramienta nativa de Fabric

# 1. Eliminar advertencias molestas de openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# 2. Limpiar esquemas viejos en Spark antes de empezar
target_tables = ["discovery", "engagement", "top_posts", "followers", "demographics"]
for t in target_tables:
    spark.sql(f"DROP TABLE IF EXISTS {t}")

# 3. Ruta base de la carpeta donde caen los archivos semanales
folder_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a/Files/raw_data"

print("--- ESCANEANDO CARPETA ONELAKE ---")

try:
    # Listar contenido de la carpeta
    files = mssparkutils.fs.ls(folder_path)
    excel_files = [f.path for f in files if f.path.endswith('.xlsx')]

    if not excel_files:
        raise FileNotFoundError("❌ No se encontraron archivos de Excel (.xlsx) en la carpeta raw_data.")

    # Ordenar de forma descendente (el archivo con la fecha más reciente en el nombre quedará de primero)
    excel_files.sort(reverse=True)
    file_path = excel_files[0]

    print(f"Archivo más nuevo detectado automáticamente:")
    print(f"👉 {file_path.split('/')[-1]}\n")
    print("--- INICIANDO PROCESAMIENTO MEDALLION (BRONZE) ---")

    # 4. Inicializar lector de Excel con el archivo dinámico
    excel_reader = pd.ExcelFile(file_path)
    sheet_names = excel_reader.sheet_names

    # Palabras clave para identificar cabeceras de tiempo
    date_keywords = {"date", "start date", "start_date", "end date", "post publish date"}

    for sheet in sheet_names:
        table_name = sheet.strip().replace(" ", "_").replace("-", "_").lower()
        
        if table_name not in target_tables:
            continue
            
        print(f"\nProcesando pestaña: {sheet}")
        pdf_raw = pd.read_excel(file_path, sheet_name=sheet, header=None)
        
        # Identificar el índice de la fila que contiene las cabeceras
        header_row_index = 0
        for idx, row in pdf_raw.iterrows():
            row_values = {str(val).strip().lower() for val in row.values if pd.notnull(val)}
            if row_values.intersection(date_keywords):
                header_row_index = idx
                break
                
        print(f"  -> Índice de cabecera detectado: {header_row_index}")
        
        # Procesamiento especial para la pestaña compleja 'top_posts'
        if table_name == "top_posts":
            print("  -> Dividiendo y uniendo tablas paralelas (Engagements & Impressions)")
            
            # 1. Tabla Izquierda: Engagements (Columnas A-C)
            pdf_eng = pdf_raw.iloc[header_row_index + 1:, 0:3].copy()
            pdf_eng.columns = ["post_url", "post_publish_date", "engagements"]
            pdf_eng = pdf_eng.dropna(subset=["post_url"])
            
            # 2. Tabla Derecha: Impressions (Columnas E-G)
            pdf_imp = pdf_raw.iloc[header_row_index + 1:, 4:7].copy()
            pdf_imp.columns = ["post_url", "post_publish_date", "impressions"]
            pdf_imp = pdf_imp.dropna(subset=["post_url"])
            
            # 3. Convertir tipos de datos en Pandas
            pdf_eng["post_publish_date"] = pd.to_datetime(pdf_eng["post_publish_date"], errors='coerce')
            pdf_eng["engagements"] = pd.to_numeric(pdf_eng["engagements"], errors='coerce').fillna(0).astype(int)
            
            pdf_imp["post_publish_date"] = pd.to_datetime(pdf_imp["post_publish_date"], errors='coerce')
            pdf_imp["impressions"] = pd.to_numeric(pdf_imp["impressions"], errors='coerce').fillna(0).astype(int)
            
            # 4. Outer Join para consolidar ambas métricas por Post
            pdf = pd.merge(pdf_eng, pdf_imp, on=["post_url", "post_publish_date"], how="outer")
            
            # 5. Rellenar nulos producidos por el Join
            pdf["engagements"] = pdf["engagements"].fillna(0).astype(int)
            pdf["impressions"] = pdf["impressions"].fillna(0).astype(int)
            
        else:
            # Procesamiento estándar para las demás pestañas
            pdf = pd.read_excel(file_path, sheet_name=sheet, header=header_row_index)
            
            # Limpiar nombres de columnas (reemplazar espacios y quitar paréntesis)
            pdf.columns = [str(col).strip().replace(" ", "_").replace("(", "").replace(")", "").lower() for col in pdf.columns]
            
            # Convertir columnas que contengan "date" a tipo datetime
            for col in pdf.columns:
                if "date" in col:
                    pdf[col] = pd.to_datetime(pdf[col], errors='coerce')
        
        # 5. Escribir a OneLake en formato Delta Table
        spark_df = spark.createDataFrame(pdf)
        (spark_df.write
         .format("delta")
         .mode("overwrite")
         .option("overwriteSchema", "true")
         .saveAsTable(table_name))
         
        print(f"  -> Exito: Tabla Delta '{table_name}' actualizada en capa Bronze.")

    print("\n🚀 PROCESO TERMINADO: Todas las tablas se actualizaron con el archivo más reciente.")

except Exception as e:
    print(f"\n❌ ERROR CRÍTICO EN EL PIPELINE: {e}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

import warnings
import pandas as pd

# 1. Suppress the openpyxl stylesheet warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Define your file path
file_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a/Files/raw_data"

# Scan Excel tabs
excel_reader = pd.ExcelFile(file_path)
sheet_names = excel_reader.sheet_names

print("--- EXCEL SCAN ---")
print(f"File contains {len(sheet_names)} tabs:")
for idx, sheet in enumerate(sheet_names, 1):
    print(f"  [{idx}] {sheet}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

import warnings
import pandas as pd
import re

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# 1. Drop old tables to recreate clean schemas
target_tables = ["discovery", "engagement", "top_posts", "followers", "demographics"]
for t in target_tables:
    spark.sql(f"DROP TABLE IF EXISTS {t}")

file_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a/Files/raw_data/AggregateAnalytics_Antonio Gutierrez_2026-06-01_2026-06-07.xlsx"

excel_reader = pd.ExcelFile(file_path)
sheet_names = excel_reader.sheet_names

# Identify time-series headers
date_keywords = {"date", "start date", "start_date", "end date", "post publish date"}

for sheet in sheet_names:
    table_name = sheet.strip().replace(" ", "_").replace("-", "_").lower()
    
    if table_name not in target_tables:
        continue
        
    print(f"\nProcessing tab structure: {sheet}")
    pdf_raw = pd.read_excel(file_path, sheet_name=sheet, header=None)
    
    # Identify header row index
    header_row_index = 0
    for idx, row in pdf_raw.iterrows():
        row_values = {str(val).strip().lower() for val in row.values if pd.notnull(val)}
        if row_values.intersection(date_keywords):
            header_row_index = idx
            break
            
    print(f"  -> Selected header row index: {header_row_index}")
    
    # Custom processing for the double-framework 'top_posts' sheet
    if table_name == "top_posts":
        print("  -> Splitting and merging side-by-side Top Posts tables (Engagements & Impressions)")
        
        # 1. Left Table: Top Posts by Engagements (Columns A-C / 0 to 2)
        pdf_eng = pdf_raw.iloc[header_row_index + 1:, 0:3].copy()
        pdf_eng.columns = ["post_url", "post_publish_date", "engagements"]
        pdf_eng = pdf_eng.dropna(subset=["post_url"])
        
        # 2. Right Table: Top Posts by Impressions (Columns E-G / 4 to 6)
        pdf_imp = pdf_raw.iloc[header_row_index + 1:, 4:7].copy()
        pdf_imp.columns = ["post_url", "post_publish_date", "impressions"]
        pdf_imp = pdf_imp.dropna(subset=["post_url"])
        
        # 3. Cast columns in Pandas
        pdf_eng["post_publish_date"] = pd.to_datetime(pdf_eng["post_publish_date"], errors='coerce')
        pdf_eng["engagements"] = pd.to_numeric(pdf_eng["engagements"], errors='coerce').fillna(0).astype(int)
        
        pdf_imp["post_publish_date"] = pd.to_datetime(pdf_imp["post_publish_date"], errors='coerce')
        pdf_imp["impressions"] = pd.to_numeric(pdf_imp["impressions"], errors='coerce').fillna(0).astype(int)
        
        # 4. Outer Join on post_url & post_publish_date
        pdf = pd.merge(pdf_eng, pdf_imp, on=["post_url", "post_publish_date"], how="outer")
        
        # 5. Fill missing metrics with 0
        pdf["engagements"] = pdf["engagements"].fillna(0).astype(int)
        pdf["impressions"] = pdf["impressions"].fillna(0).astype(int)
        
    else:
        # Standard sheets
        pdf = pd.read_excel(file_path, sheet_name=sheet, header=header_row_index)
        
        # Clean column names
        pdf.columns = [str(col).strip().replace(" ", "_").replace("(", "").replace(")", "").lower() for col in pdf.columns]
        
        # Parse standard date columns
        for col in pdf.columns:
            if "date" in col:
                pdf[col] = pd.to_datetime(pdf[col], errors='coerce')
    
    # Save to Bronze
    spark_df = spark.createDataFrame(pdf)
    (spark_df.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .saveAsTable(table_name))
     
    print(f"  -> Successfully ingested Bronze Table: {table_name}")

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
