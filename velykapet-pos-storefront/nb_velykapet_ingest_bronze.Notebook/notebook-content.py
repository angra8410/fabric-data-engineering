# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   }
# META }

# CELL ********************

"""
===============================================================================
Velykapet Data Engineering Pipeline - Capa Bronze (Ingesta Raw & Auditoría)
===============================================================================
Descripción:
  Script PySpark optimizado para Microsoft Fabric.
  Lee las 16 tablas crudas copiadas desde PostgreSQL mediante el Copy Job
  hacia el espacio de nombres 'lh_velykapet_bronze_dev.public.<tabla>'.
  Adiciona metadatos de trazabilidad y auditoría (_ingested_at, _batch_id).

Lakehouse Destino: lh_velykapet_bronze_dev (Esquema: public)
===============================================================================
"""

from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

spark = SparkSession.builder \
    .appName("Velykapet_Bronze_Ingestion") \
    .getOrCreate()

BRONZE_LAKEHOUSE = "lh_velykapet_bronze_dev"
SCHEMA_BRONZE = "public"

BRONZE_TABLES = [
    "sales",
    "sale_items",
    "master_catalog",
    "products",
    "purchases",
    "expenses",
    "devolutions",
    "devolution_items",
    "v_product_stock",
    "whatsapp_orders",
    "whatsapp_order_items",
    "processed_whatsapp_messages",
    "whatsapp_contacts",
    "demand_backlog",
    "customer_last_search",
    "customer_cart"
]

def process_bronze_audit(table_name: str):
    """Inspecciona y enriquece la tabla cruda en Bronze con columnas de auditoría."""
    full_table_name = f"{BRONZE_LAKEHOUSE}.{SCHEMA_BRONZE}.{table_name}"
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"🚀 Leyendo y verificando Bronze: '{full_table_name}'...")
    try:
        df_raw = spark.read.table(full_table_name)
        
        df_bronze = df_raw \
            .withColumn("_ingested_at", current_timestamp()) \
            .withColumn("_batch_id", lit(batch_id))

        df_bronze.write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(full_table_name)
            
        print(f"✅ Bronze '{table_name}': {df_bronze.count()} registros verificados.")
    except Exception as e:
        print(f"⚠️ Nota al procesar '{table_name}': {str(e)}")

if __name__ == "__main__":
    print("==================================================")
    print("EJECUTANDO VERIFICACIÓN CAPA BRONZE - VELYKAPET")
    print("==================================================")
    
    for tbl in BRONZE_TABLES:
        process_bronze_audit(tbl)
        
    print("🏁 Proceso de verificación Bronze completado.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
