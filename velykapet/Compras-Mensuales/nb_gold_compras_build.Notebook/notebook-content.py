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

print("Consolidating Silver tables into Gold Master table (with explicit catalog)...")

# Define the catalog name (your Lakehouse name)
catalog = "compras_bronze_lh"

# 1. Read the Silver tables using the full path
df_or = spark.read.table(f"{catalog}.dbo.compras_or_2026_silver").select(
    F.col("Item_Name_Clean"), 
    F.col("Price_Current_COP").alias("Price_COP"), 
    F.lit(1).alias("Quantity_Clean"), 
    F.lit(None).cast("date").alias("Transaction_Date"), 
    F.lit("ENTREGADO").alias("Status_Clean"), 
    F.col("Store")
)

df_exito = spark.read.table(f"{catalog}.dbo.compras_exito_2026_silver").select(
    "Item_Name_Clean", "Price_COP", "Quantity_Clean", "Transaction_Date", "Status_Clean", "Store"
)

df_d1 = spark.read.table(f"{catalog}.dbo.compras_d1_2026_silver").select(
    "Item_Name_Clean", "Price_COP", "Quantity_Clean", "Transaction_Date", "Status_Clean", "Store"
)

# 2. Perform the Union
df_gold = df_or.unionAll(df_exito).unionAll(df_d1)

# 3. Write to Gold Delta Table
# We write this to the same Lakehouse
df_gold.write.format("delta").mode("overwrite").saveAsTable("compras_master_gold")

print(" [✓] Master Gold table 'compras_master_gold' created successfully!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import DateType

# 1. Create a range of dates for the year 2026
start_date = "2026-01-01"
end_date = "2026-12-31"

# Generate sequence of dates
df_date = spark.sql(f"SELECT explode(sequence(to_date('{start_date}'), to_date('{end_date}'), interval 1 day)) as Date")

# 2. Add time attributes
df_dim_date = df_date.select(
    F.col("Date").alias("DateKey"),
    F.year("Date").alias("Year"),
    F.month("Date").alias("Month"),
    F.date_format("Date", "MMMM").alias("Month_Name"),
    F.quarter("Date").alias("Quarter"),
    F.dayofweek("Date").alias("Day_of_Week"),
    F.date_format("Date", "EEEE").alias("Day_Name"),
    F.when(F.dayofweek("Date").isin(1, 7), "Weekend").otherwise("Weekday").alias("Day_Type")
)

# 3. Write to Delta
df_dim_date.write.format("delta").mode("overwrite").saveAsTable("dim_date")

print(" [✓] dim_date table created successfully for 2026!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

# 1. Force a clean read of the Silver tables (ignoring cache)
# This ensures we get the version that includes the new 'Transaction_Date'
spark.catalog.clearCache()

df_or = spark.read.table("compras_or_2026_silver").select(
    "Item_Name_Clean", F.col("Price_Current_COP").alias("Price_COP"), 
    F.lit(1).alias("Quantity_Clean"), "Transaction_Date", 
    F.lit("ENTREGADO").alias("Status_Clean"), "Store"
)

df_exito = spark.read.table("compras_exito_2026_silver").select(
    "Item_Name_Clean", "Price_COP", "Quantity_Clean", "Transaction_Date", "Status_Clean", "Store"
)

df_d1 = spark.read.table("compras_d1_2026_silver").select(
    "Item_Name_Clean", "Price_COP", "Quantity_Clean", "Transaction_Date", "Status_Clean", "Store"
)

# 2. Union and force overwrite of Gold
df_gold = df_or.unionAll(df_exito).unionAll(df_d1)

# Using overwriteSchema here ensures the Gold table resets its structure to the latest
df_gold.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("compras_master_gold")

print(" [✓] Gold Master table has been force-refreshed with the new dates!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

# Re-leer todas las tablas Silver confirmadas
df_or = spark.read.table("compras_or_2026_silver").select(
    "Item_Name_Clean", 
    F.col("Price_Current_COP").alias("Price_COP"), 
    F.lit(1).alias("Quantity_Clean"), 
    "Transaction_Date", 
    F.lit("ENTREGADO").alias("Status_Clean"), 
    "Store"
)

df_exito = spark.read.table("compras_exito_2026_silver").select("Item_Name_Clean", "Price_COP", "Quantity_Clean", "Transaction_Date", "Status_Clean", "Store")
df_d1 = spark.read.table("compras_d1_2026_silver").select("Item_Name_Clean", "Price_COP", "Quantity_Clean", "Transaction_Date", "Status_Clean", "Store")

# Ejemplo: agrega una columna 'Origen_Dato'
df_or_silver = df_or_silver.withColumn("Origen_Dato", F.lit("Precio_Referencia"))
df_exito_silver = df_exito_silver.withColumn("Origen_Dato", F.lit("Compra_Real"))
df_d1_silver = df_d1_silver.withColumn("Origen_Dato", F.lit("Compra_Real"))

# Realizar la unión final
df_gold = df_or.unionAll(df_exito).unionAll(df_d1)



# Escribir con overwriteSchema para asegurar que no queden rastros de estructuras viejas
df_gold.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("compras_master_gold")

print(" [✓] ¡La tabla 'compras_master_gold' está finalmente consolidada y lista para Power BI!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

print(" [✓] Consolidating Gold table with Data Source origin...")

# 1. Read and add origin flag to each DataFrame individually
df_or = spark.read.table("compras_or_2026_silver").select(
    "Item_Name_Clean", 
    F.col("Price_Current_COP").alias("Price_COP"), 
    F.lit(1).alias("Quantity_Clean"), 
    "Transaction_Date", 
    F.lit("ENTREGADO").alias("Status_Clean"), 
    "Store"
).withColumn("Origen_Dato", F.lit("Precio_Referencia"))

df_exito = spark.read.table("compras_exito_2026_silver").select(
    "Item_Name_Clean", 
    "Price_COP", 
    "Quantity_Clean", 
    "Transaction_Date", 
    "Status_Clean", 
    "Store"
).withColumn("Origen_Dato", F.lit("Compra_Real"))

df_d1 = spark.read.table("compras_d1_2026_silver").select(
    "Item_Name_Clean", 
    "Price_COP", 
    "Quantity_Clean", 
    "Transaction_Date", 
    "Status_Clean", 
    "Store"
).withColumn("Origen_Dato", F.lit("Compra_Real"))

# 2. Perform the Union
df_gold = df_or.unionAll(df_exito).unionAll(df_d1)

# 3. Write to Gold with schema overwrite
df_gold.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("compras_master_gold")

print(" [✓] Gold Master table created with 'Origen_Dato' column!")

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
