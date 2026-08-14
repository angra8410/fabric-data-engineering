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
# META     },
# META     "warehouse": {
# META       "known_warehouses": []
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

year = 2026
bronze_table = f"compras_or_{year}_bronze"
silver_table = f"compras_or_{year}_silver"

print(f"Transforming Bronze ({bronze_table}) to Silver ({silver_table})...")

# 1. Read the immutable Bronze data
df_bronze = spark.read.table(bronze_table)

# 2. Apply Data Quality & Standardization Transformations
df_silver = (
    df_bronze
    .withColumn("Item_Name_Clean", F.upper(F.trim(F.col("Item_Name"))))
    .withColumn("Price_Current_COP", 
                F.regexp_replace(
                    F.regexp_extract(F.col("Price"), r"(?i)Ahora\s*\$([\d\.]+)", 1), 
                    r"\.", ""
                ).cast(IntegerType()))
    .withColumn("Price_Original_COP", 
                F.regexp_replace(
                    F.regexp_extract(F.col("Price"), r"(?i)Antes\s*\$([\d\.]+)", 1), 
                    r"\.", ""
                ).cast(IntegerType()))
    .withColumn("Discount_Pct", 
                F.regexp_extract(F.col("Discount"), r"(\d+)%", 1).cast(IntegerType()))
    .dropDuplicates(["Item_Name_Clean", "source_sheet_name"])
    .withColumn("silver_processing_date", F.current_timestamp())
)

# 3. Handle cases where the price is just a flat number
df_silver = df_silver.withColumn(
    "Price_Current_COP",
    F.when(F.col("Price_Current_COP").isNull(),
           F.regexp_replace(F.regexp_extract(F.col("Price"), r"\$([\d\.]+)", 1), r"\.", "").cast(IntegerType())
          ).otherwise(F.col("Price_Current_COP"))
)

# 4. Select final columns and write to Delta
df_silver_final = df_silver.select(
    "Item_Name_Clean",
    "Price_Current_COP",
    "Price_Original_COP",
    "Discount_Pct",
    "Store",
    "source_file_path",
    "ingestion_date",
    "silver_processing_date"
)

# 5. Write to Delta
(
    df_silver_final.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(silver_table)
)

print(f" [✓] Transformations applied. Silver table ready: {silver_table}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

year = 2026
stores_to_process = ["exito", "d1"]

for store in stores_to_process:
    bronze_table = f"compras_{store}_{year}_bronze"
    silver_table = f"compras_{store}_{year}_silver"
    
    print(f"Transforming Bronze ({bronze_table}) to Silver ({silver_table})...")
    
    try:
        # 1. Read the now-existing Bronze data
        df_bronze = spark.read.table(bronze_table)
    except Exception as e:
        print(f" [!] Error reading {bronze_table}: {e}\n")
        continue

    # 2. Apply Data Quality & Standardization Transformations
    df_silver = (
        df_bronze
        # Standardize the item names
        .withColumn("Item_Name_Clean", F.upper(F.trim(F.col("Item_Name"))))
        
        # Clean Price: Strip the '$', dots, and spaces, then cast to Integer
        .withColumn("Price_COP", 
                    F.regexp_replace(F.col("Price"), r"[^\d]", "").cast(IntegerType()))
        
        # Clean Quantity: Extract just the numbers from strings like "24 unds"
        .withColumn("Quantity_Clean", 
                    F.regexp_extract(F.col("Quantity"), r"(\d+)", 1).cast(IntegerType()))
        
        # Clean Date: Convert string format to proper DateType
        .withColumn("Transaction_Date", 
                    F.to_date(F.col("Date"), "d/M/yyyy"))
        
        # Clean Status: Uppercase and trim
        .withColumn("Status_Clean", F.upper(F.trim(F.col("Status"))))
        
        # Deduplicate to ensure idempotent runs
        .dropDuplicates(["Item_Name_Clean", "Transaction_Date", "source_file_path"])
        
        # Add Silver lineage tracking
        .withColumn("silver_processing_date", F.current_timestamp())
    )

    # 3. Select final columns and write to Delta
    df_silver_final = df_silver.select(
        "Item_Name_Clean",
        "Price_COP",
        "Quantity_Clean",
        "Transaction_Date",
        "Status_Clean",
        F.lit(store.upper()).alias("Store"),
        "source_file_path",
        "ingestion_date",
        "silver_processing_date"
    )

    # 4. Write to Delta
    (
        df_silver_final.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
    )

    print(f" [✓] Transformations applied. Silver table ready: {silver_table}\n")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pandas as pd
from pyspark.sql import functions as F

# 1. Path setup
file_path = "/lakehouse/default/Files/raw/compras/year=2026/Trazabilidad de Estudio (3)_v2.xlsx"

# 2. Re-process 'OR' tab
pdf_or = pd.read_excel(file_path, sheet_name="OR")
pdf_or.columns = [c.replace(' ', '_') for c in pdf_or.columns]
df_or_bronze = spark.createDataFrame(pdf_or.astype(str))

# Transform to Silver
df_or_silver = df_or_bronze.select(
    F.upper(F.trim(F.col("Item_Name"))).alias("Item_Name_Clean"),
    F.regexp_replace(F.col("Price"), r"[^\d]", "").cast("int").alias("Price_Current_COP"),
    F.to_date(F.col("Date"), "d/M/yyyy").alias("Transaction_Date"),
    F.col("Store")
)

# 3. Overwrite Silver table with schema overwrite enabled
df_or_silver.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("compras_or_2026_silver")

# 4. Rebuild Gold
# We must re-read the OR silver table we just wrote
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

# Union all
df_gold = df_or.unionAll(df_exito).unionAll(df_d1)

# Write Gold
df_gold.write.format("delta").mode("overwrite").saveAsTable("compras_master_gold")

print(" [✓] Gold table successfully updated with the new date schema!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pandas as pd
# Force an update to the Silver table with a more robust date parsing
from pyspark.sql import functions as F

pdf_or = pd.read_excel("/lakehouse/default/Files/raw/compras/year=2026/Trazabilidad de Estudio (3)_v2.xlsx", sheet_name="OR")
pdf_or.columns = [c.replace(' ', '_') for c in pdf_or.columns]
df_or_bronze = spark.createDataFrame(pdf_or.astype(str))

# Use a more flexible date parsing (casting directly instead of assuming d/M/yyyy)
df_or_silver = df_or_bronze.select(
    F.upper(F.trim(F.col("Item_Name"))).alias("Item_Name_Clean"),
    F.regexp_replace(F.col("Price"), r"[^\d]", "").cast("int").alias("Price_Current_COP"),
    # Try casting directly if it's already a string, or parse specifically
    F.to_date(F.col("Date")).alias("Transaction_Date"), 
    F.col("Store")
)

df_or_silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("compras_or_2026_silver")

# Re-run the Gold union only after verifying this step produces dates!


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

# 1. Refresh EXITO Silver with correct date format
df_exito = spark.read.table("compras_exito_2026_bronze")
df_exito_silver = df_exito.select(
    F.upper(F.trim(F.col("Item_Name"))).alias("Item_Name_Clean"),
    F.regexp_replace(F.col("Price"), r"[^\d]", "").cast("int").alias("Price_COP"),
    F.regexp_extract(F.col("Quantity"), r"(\d+)", 1).cast("int").alias("Quantity_Clean"),
    # FIXED: Changed "d/M/yyyy" to "yyyy-MM-dd"
    F.to_date(F.col("Date"), "yyyy-MM-dd").alias("Transaction_Date"),
    F.upper(F.trim(F.col("Status"))).alias("Status_Clean"),
    F.lit("EXITO").alias("Store")
)
df_exito_silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("compras_exito_2026_silver")

# 2. Refresh D1 Silver with correct date format
df_d1 = spark.read.table("compras_d1_2026_bronze")
df_d1_silver = df_d1.select(
    F.upper(F.trim(F.col("Item_Name"))).alias("Item_Name_Clean"),
    F.regexp_replace(F.col("Price"), r"[^\d]", "").cast("int").alias("Price_COP"),
    F.regexp_extract(F.col("Quantity"), r"(\d+)", 1).cast("int").alias("Quantity_Clean"),
    # FIXED: Changed "d/M/yyyy" to "yyyy-MM-dd"
    F.to_date(F.col("Date"), "yyyy-MM-dd").alias("Transaction_Date"),
    F.upper(F.trim(F.col("Status"))).alias("Status_Clean"),
    F.lit("D1").alias("Store")
)
df_d1_silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("compras_d1_2026_silver")

# 3. Final Gold Union
df_or = spark.read.table("compras_or_2026_silver").select("Item_Name_Clean", F.col("Price_Current_COP").alias("Price_COP"), F.lit(1).alias("Quantity_Clean"), "Transaction_Date", F.lit("ENTREGADO").alias("Status_Clean"), "Store")
df_exito = spark.read.table("compras_exito_2026_silver")
df_d1 = spark.read.table("compras_d1_2026_silver")

df_gold = df_or.unionAll(df_exito).unionAll(df_d1)
df_gold.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("compras_master_gold")

print(" [✓] Dates parsed correctly! Gold table now has complete date data.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# 1. Drop the existing Gold table to clear any bad metadata
spark.sql("DROP TABLE IF EXISTS compras_master_gold")

# 2. Re-run the Gold Union
from pyspark.sql import functions as F

df_or = spark.read.table("compras_or_2026_silver").select("Item_Name_Clean", F.col("Price_Current_COP").alias("Price_COP"), F.lit(1).alias("Quantity_Clean"), "Transaction_Date", F.lit("ENTREGADO").alias("Status_Clean"), "Store")
df_exito = spark.read.table("compras_exito_2026_silver")
df_d1 = spark.read.table("compras_d1_2026_silver")

df_gold = df_or.unionAll(df_exito).unionAll(df_d1)

# 3. Create the table completely fresh
df_gold.write.format("delta").saveAsTable("compras_master_gold")

print(" [✓] Gold table has been completely dropped and recreated!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Peek at the raw EXITO bronze data
display(spark.read.table("compras_exito_2026_bronze").limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT Transaction_Date, Store, SUM(Price_COP) FROM compras_master_gold GROUP BY Transaction_Date, Store

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
