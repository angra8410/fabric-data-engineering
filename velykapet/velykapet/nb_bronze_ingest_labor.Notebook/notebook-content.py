# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "abe92425-50d3-48f4-baa0-ebbfadd93f25",
# META       "default_lakehouse_name": "lh_bronze_velykapet",
# META       "default_lakehouse_workspace_id": "b14581ac-9906-43e2-809c-c2fd4315ad5b",
# META       "known_lakehouses": [
# META         {
# META           "id": "abe92425-50d3-48f4-baa0-ebbfadd93f25"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import re
import fsspec
import openpyxl
import pandas as pd
from pyspark.sql.functions import lit, current_timestamp

# Rutas ABFSS validadas
base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"
excel_file_path = f"{base_abfss_path}/Files/raw-data/Data_Cliente_Multidominio.xlsx"
tables_destination_path = f"{base_abfss_path}/Tables"

print(f"Iniciando conexión OneLake nativa a: {excel_file_path}")

try:
    # Abrir el archivo y listar pestañas
    with fsspec.open(excel_file_path, "rb") as f:
        wb = openpyxl.load_workbook(f, read_only=True)
        all_sheets = wb.sheetnames

    print(f"Pestañas totales detectadas: {all_sheets}")

    # Dominios permitidos: GASTOS, VENTAS e Inventario
    allowed_domains = ["GASTOS", "VENTAS", "COMPRAS_INVENTARIO", "INVENTARIO DEFINITIVO"]

    target_table_map = {
        "GASTOS": "stg_gastos_raw",
        "VENTAS": "stg_ventas_raw",
        "COMPRAS_INVENTARIO": "stg_compras_inventario_raw",
        "INVENTARIO DEFINITIVO": "stg_inventario_definitivo_raw",
    }

    # Procesamiento filtrado
    with fsspec.open(excel_file_path, "rb") as f:
        for sheet in all_sheets:
            sheet_upper = sheet.upper().strip()

            if sheet_upper not in allowed_domains:
                print(f"-> [Omitida] Pestaña '{sheet}' ignorada.")
                continue

            target_table = target_table_map[sheet_upper]
            target_delta_path = f"{tables_destination_path}/{target_table}"

            print(f"\n-> [Procesando] Pestaña '{sheet}' hacia la ruta Delta: {target_delta_path}")

            # Leer pestaña como texto plano para evitar drift de tipos
            df_pandas = pd.read_excel(f, sheet_name=sheet, dtype=str)

            # ---------------------------------------------------------------------------------
            # SANEAMIENTO AVANZADO DE COLUMNAS (Solución a DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES)
            # - Remover paréntesis, corchetes, llaves y caracteres especiales problemáticos
            # - Reemplazar espacios múltiples por un solo guion bajo
            # - Limpiar guiones bajos duplicados al inicio o final
            # ---------------------------------------------------------------------------------
            cleaned_columns = []
            for col in df_pandas.columns:
                col_str = str(col).strip()
                # Reemplazar caracteres prohibidos por Delta (' ,;{}()\n\t=') y otros comunes por guion bajo
                col_cleaned = re.sub(r'[\s,;{}()\[\]\n\t=\-\.\/\$%\?¿!¡]', '_', col_str)
                # Contraer múltiples guiones bajos seguidos '___' en uno solo '_'
                col_cleaned = re.sub(r'_+', '_', col_cleaned)
                # Remover guiones bajos sobrantes al inicio o al final
                col_cleaned = col_cleaned.strip('_')
                cleaned_columns.append(col_cleaned)

            df_pandas.columns = cleaned_columns
            print(f"   [Columnas Saneadas]: {df_pandas.columns.tolist()}")
            # ---------------------------------------------------------------------------------

            # Convertir a Spark DataFrame
            df_spark = spark.createDataFrame(df_pandas)

            # Añadir metadatos de auditoría y linaje
            df_bronze = df_spark.withColumn("_nombre_pestaña", lit(sheet)) \
                                .withColumn("_fecha_ingestion", current_timestamp())

            # Guardar en OneLake con evolución de esquema permitida
            df_bronze.write \
                .format("delta") \
                .mode("overwrite") \
                .option("overwriteSchema", "true") \
                .save(target_delta_path)

            print(f"   [Éxito] Tabla Delta '{target_table}' actualizada correctamente.")

    print("\n¡Proceso Bronze finalizado con éxito! GASTOS, VENTAS e Inventario están en OneLake sin caracteres inválidos.")

except Exception as e:
    print(f"\nError en la ejecución del Pipeline Bronze: {str(e)}")
    raise e

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

for t in ["stg_gastos_raw", "stg_ventas_raw", "stg_compras_inventario_raw", "stg_inventario_definitivo_raw"]:
    path = f"{tables_destination_path}/{t}"
    df = spark.read.format("delta").load(path)
    print(f"{t}: {df.count()} filas, columnas: {df.columns}")

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
