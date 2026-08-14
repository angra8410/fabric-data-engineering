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
# FABRIC DRIFT ARCHITECT - GOLD PERFORMANCE MODEL (CORRECTED JOIN)
# ==============================================================================
from pyspark.sql import functions as F

print("[*] Construyendo Gold con join correcto: Site_Key + Month_Key...")

df_dcm = spark.read.table("marketing_dcm_cleaned")
df_ga  = spark.read.table("marketing_ga_cleaned")

# Aggregate DCM to Site+Month+Creative+Dimensions+Platform level
dcm_agg = (df_dcm
    .groupBy("Site_Key", "Month_Key", "Campaign",
             "Site_Site_Directory", "Creative_Clean", "Creative_Dimensions", "Platform_Type")
    .agg(
        F.sum("Impressions").alias("Impressions"),
        F.sum("Clicks").alias("Clicks")
    )
)

# Aggregate GA to Site+Month+Device level
ga_agg = (df_ga
    .groupBy("Site_Key", "Month_Key", "Device_Category")
    .agg(
        F.sum("Sessions").alias("Sessions"),
        F.sum("Users").alias("Users")
    )
)

# FULL OUTER JOIN on Site_Key + Month_Key
df_gold = (dcm_agg.join(ga_agg, on=["Site_Key", "Month_Key"], how="full_outer")
    .select(
        F.to_date(F.coalesce(dcm_agg["Month_Key"], ga_agg["Month_Key"]), "yyyy-MM").alias("Date"),
        F.coalesce(dcm_agg["Site_Key"],  ga_agg["Site_Key"]) .alias("Media_Placement_Site"),
        F.col("Campaign"),
        F.col("Campaign").alias("Campaign_Group"),          # ← ADD THIS
        F.col("Creative_Clean").alias("Creative_Name"),
        F.col("Creative_Dimensions"),
        F.col("Platform_Type").alias("Device_Category_DCM"),
        F.col("Device_Category"),
        F.coalesce(dcm_agg["Site_Key"], ga_agg["Site_Key"]).alias("GA_Web_Source"),  # ← ADD THIS
        F.coalesce(F.col("Impressions"), F.lit(0)).alias("Impressions"),
        F.coalesce(F.col("Clicks"),      F.lit(0)).alias("Clicks"),
        F.coalesce(F.col("Sessions"),    F.lit(0)).alias("Sessions"),
        F.coalesce(F.col("Users"),       F.lit(0)).alias("Users")
    )
)

# Validation
print("\n[📋] Gold preview by placement:")
df_gold.groupBy("Media_Placement_Site").agg(
    F.sum("Impressions").alias("Impressions"),
    F.sum("Clicks").alias("Clicks"),
    F.sum("Sessions").alias("Sessions")
).orderBy(F.desc("Impressions")).show(25, truncate=False)

df_gold.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable("fact_marketing_performance")

print("\n" + "="*80)
print("[🚀 GOLD CONSOLIDADA — join correcto por Site_Key + Month_Key]")
print(f"Total rows: {df_gold.count()}")
print("="*80)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ==============================================================================
# FABRIC DRIFT ARCHITECT - GOLD DIM_DATE GENERATION (TIME INTELLIGENCE READY)
# ==============================================================================
from pyspark.sql import functions as F
from pyspark.sql.types import *

print("[*] Generando Dimensión de Tiempo (Dim_Date) en la capa Gold...")

# 1. Definir el rango del calendario
start_date = "2020-01-01"
end_date   = "2021-12-31"

# FIXED: spark.range(0, 1) — only ONE row so sequence runs exactly once
df_date_base = spark.range(0, 1).select(
    F.expr(f"sequence(to_date('{start_date}'), to_date('{end_date}'), interval 1 day)").alias("DateArray")
).select(F.explode("DateArray").alias("DateKey"))

# 2. Enriquecer con Atributos de Calendario exigidos por Power BI
df_dim_date = (df_date_base
    .withColumn("Year",         F.year(F.col("DateKey")))
    .withColumn("Month_Number", F.month(F.col("DateKey")))
    .withColumn("Month_Short",  F.date_format(F.col("DateKey"), "MMM"))
    .withColumn("Quarter",      F.concat(F.lit("Q"), F.quarter(F.col("DateKey"))))
    .withColumn("YearMonthKey", (F.year(F.col("DateKey")) * 100 + F.month(F.col("DateKey"))).cast("integer"))
    .withColumn("Day_of_Month", F.dayofmonth(F.col("DateKey")))
    .withColumn("Day_of_Week",  F.dayofweek(F.col("DateKey")))
)

# 3. Validar unicidad antes de guardar (evita romper el modelo semántico)
total_rows    = df_dim_date.count()
distinct_rows = df_dim_date.select("DateKey").distinct().count()
assert total_rows == distinct_rows, \
    f"[ERROR] dim_date tiene duplicados: {total_rows} filas vs {distinct_rows} fechas únicas"

print(f"[✓] Validación OK: {total_rows} fechas únicas generadas ({start_date} → {end_date})")

# 4. Guardar en Delta Lake
df_dim_date.write.format("delta").mode("overwrite").saveAsTable("dim_date")

print("\n" + "="*80)
print("[🚀 SUCCESS] TABLA 'dim_date' MATERIALIZADA EN ONELAKE")
print("="*80)
print(f"Campos: DateKey, Year, Month_Number, Month_Short, Quarter, YearMonthKey, Day_of_Month, Day_of_Week")
print(f"Total filas: {total_rows}")

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
