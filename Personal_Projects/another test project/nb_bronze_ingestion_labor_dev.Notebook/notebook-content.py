# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e4ab5a3e-7d4e-480f-84a0-cdbf419c7399",
# META       "default_lakehouse_name": "lh_digital_campaign_dev",
# META       "default_lakehouse_workspace_id": "b14581ac-9906-43e2-809c-c2fd4315ad5b",
# META       "known_lakehouses": [
# META         {
# META           "id": "e4ab5a3e-7d4e-480f-84a0-cdbf419c7399"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# ==============================================================================
# FABRIC DRIFT ARCHITECT - SECURE LOCAL BRONZE INGESTION (DATETIME TIME FIX)
# ==============================================================================
import pandas as pd
import datetime
from pyspark.sql import functions as F

# Ruta física de tu archivo Excel
FULL_LOCAL_PATH = "/lakehouse/default/Files/raw-data/Analytics Test & Data Set - Instructions.xlsx"

SHEET_CONFIGS = {
    "RFI Data": {
        "local_table_name": "marketing_dcm_raw",
        "skip": 0
    },
    "Raw GA Data": {
        "local_table_name": "marketing_ga_raw",
        "skip": 3
    }
}

print("[*] Iniciando Ingesta Controlada en Lakehouse Local contra Time-Drift...")

for sheet_name, config in SHEET_CONFIGS.items():
    print(f"\n[*] Procesando Hoja '{sheet_name}' -> Tabla Local Delta: {config['local_table_name']}")
    
    try:
        # Ingesta rápida con Pandas
        pdf = pd.read_excel(FULL_LOCAL_PATH, sheet_name=sheet_name, skiprows=config["skip"], engine="openpyxl")
        pdf.dropna(how="all", inplace=True)
        
        # 🔥 EL ANTÍDOTO CONTRA EL ATTRIBUTE-ERROR: 
        # Buscamos cualquier columna que contenga objetos 'datetime.time' y la convertimos a string
        for col in pdf.columns:
            # Si la columna tiene tipos de tiempo puros que rompen Spark, la casteamos de forma segura
            if pdf[col].dtype == 'object':
                pdf[col] = pdf[col].apply(lambda x: x.strftime('%H:%M:%S') if isinstance(x, datetime.time) else x)
            # Aseguramos que si hay columnas de fechas en Pandas, se manejen limpias
            elif pd.api.types.is_datetime64_any_dtype(pdf[col]):
                pdf[col] = pdf[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Convertimos a Spark DataFrame local de forma segura
        df_spark = spark.createDataFrame(pdf)
        
        # Metadatos de auditoría y linaje
        df_ready = (df_spark
                    .withColumn("_file_source_path", F.lit("Analytics Test & Data Set - Instructions.xlsx"))
                    .withColumn("_origin_sheet_name", F.lit(sheet_name))
                    .withColumn("_ingested_at", F.current_timestamp()))
        
        # Sanitización de caracteres especiales para compatibilidad Delta Lake
        for col_name in df_ready.columns:
            clean_col = (col_name.replace(" ", "_")
                                 .replace("(", "")
                                 .replace(")", "")
                                 .replace("-", "_")
                                 .replace("&", "and")
                                 .replace("/", "_"))
            df_ready = df_ready.withColumnRenamed(col_name, clean_col)
            
        # Escritura atómica local
        (df_ready.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(config["local_table_name"])
        )
        print(f"[📊 SUCCESS] Tabla '{config['local_table_name']}' guardada con éxito con {pdf.shape[0]} filas.")
        
    except Exception as e:
        print(f"[-] Error crítico en la hoja '{sheet_name}': {str(e)}")
        raise e

print("\n================================================================================")
print("[🚀 LOCAL BRONZE COMPLETADO SIN ALERTAS DE TIPADO]")
print("================================================================================")

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
