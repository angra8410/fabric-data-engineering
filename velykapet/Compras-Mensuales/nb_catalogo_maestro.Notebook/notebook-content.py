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

from pyspark.sql import functions as F
# 1. Cargar el catálogo actual (si existe) o crear base vacía
try:
    df_dim = spark.read.table("dim_productos")
except:
    # Si no existe, creamos la estructura base inicial
    df_dim = spark.createDataFrame([], schema="Item_Name_Clean string, Item_Name_Standard string, Category string, EAN_Reference string")

# 2. Identificar nuevos productos desde Gold
df_gold = spark.read.table("compras_master_gold")
new_products = df_gold.select("Item_Name_Clean").distinct() \
    .join(df_dim, "Item_Name_Clean", "left_anti") \
    .withColumn("Item_Name_Standard", F.initcap(F.col("Item_Name_Clean"))) \
    .withColumn("Category", F.lit("Pendiente")) \
    .withColumn("EAN_Reference", F.lit(None).cast("string"))

# 3. Guardar las novedades en la tabla maestra
new_products.write.format("delta").mode("append").saveAsTable("dim_productos")

print(f" [✓] Se han agregado {new_products.count()} nuevos productos al catálogo.")


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
