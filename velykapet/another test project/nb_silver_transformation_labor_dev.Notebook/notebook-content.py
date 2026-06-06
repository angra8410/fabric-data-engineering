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
# FABRIC DRIFT ARCHITECT - SILVER TRANSFORMATION (CORRECTED JOIN KEYS)
# ==============================================================================
from pyspark.sql import functions as F

print("[*] Iniciando capa Silver con llaves de cruce corregidas...")

# ── Site normalization maps ──────────────────────────────────────────────────
site_map_dcm = {
    'health union': 'HealthUnion', 'health union, llc': 'HealthUnion',
    'media iq': 'MediaIQ', 'medicx': 'Medicx', 'medicx media solutions': 'Medicx',
    'myhealthteams, inc.': 'MyHealthTeams', 'skin disease news today': 'SkinDiseaseNewsToday',
    'sharecare': 'Sharecare', 'swoop': 'Swoop', 'webmd': 'WebMD',
    'zeta global': 'Zeta', 'goodrx': 'GoodRx', 'goodrx.com': 'GoodRx',
    'remedy health': 'RemedyHealth', 'remedy health media, llc': 'RemedyHealth',
    'facebook': 'Facebook', 'aptus health': 'Aptus', 'emodo': 'Emodo',
    'adprime media inc': 'AdPrime', 'adtheorent': 'AdTheorent', 'healthline': 'Healthline'
}
site_map_ga = {
    'healthunion': 'HealthUnion', 'mediaiq': 'MediaIQ', 'medicx': 'Medicx',
    'myhealthteams': 'MyHealthTeams', 'skindiseasenewstoday': 'SkinDiseaseNewsToday',
    'sharecare': 'Sharecare', 'swoop': 'Swoop', 'webmd': 'WebMD',
    'zeta': 'Zeta', 'goodrx': 'GoodRx', 'remedyhealth': 'RemedyHealth',
    'facebook': 'Facebook', 'aptus': 'Aptus', 'emodo': 'Emodo',
    'adprime': 'AdPrime', 'adtheorent': 'AdTheorent', 'healthline': 'Healthline',
    'acuity': 'Acuity', 'miq': 'MiQ', 'parkinsonsnewstoday': 'ParkinsonsNewsToday',
    'pulsepoint': 'PulsePoint'
}

# Build mapping expressions
from itertools import chain
def build_map_expr(col_expr, mapping):
    expr = F.lit(None).cast("string")
    for k, v in mapping.items():
        expr = F.when(F.lower(F.trim(col_expr)) == k, v).otherwise(expr)
    return F.coalesce(expr, F.trim(col_expr))  # fallback to original if no match

# ── DCM Silver ───────────────────────────────────────────────────────────────
try:
    df_dcm = spark.read.table("marketing_dcm_raw")

    df_dcm_silver = (df_dcm
        .withColumn("Month_Key",     F.date_format(F.to_date(F.col("Month"), "yyyy-MM"), "yyyy-MM"))
        .withColumn("Site_Key",      build_map_expr(F.col("Site_Site_Directory"), site_map_dcm))
        .withColumn("Campaign",      F.trim(F.col("Campaign")))
        .withColumn("Impressions",   F.coalesce(F.col("Impressions").cast("long"), F.lit(0)))
        .withColumn("Clicks",        F.coalesce(F.col("Clicks").cast("long"), F.lit(0)))
        .withColumn("_transformed_at", F.current_timestamp())
        # ── Creative display name: "SD 1624 v3 Symptom (728x90)" ────────────────────
        .withColumn("Creative_Clean",
            F.concat(
                F.regexp_replace(F.trim(F.col("Creative")), "_", " "),
                F.lit(" ("),
                F.trim(F.col("Creative_Dimensions")),
                F.lit(")")
    )
)
    )

    df_dcm_silver.write.format("delta").mode("overwrite") \
        .option("overwriteSchema", "true").saveAsTable("marketing_dcm_cleaned")
    print("[✓] marketing_dcm_cleaned OK — rows:", df_dcm_silver.count())

except Exception as e:
    print(f"[-] Error DCM Silver: {e}"); raise e

# ── GA Silver ────────────────────────────────────────────────────────────────
try:
    df_ga = spark.read.table("marketing_ga_raw")

    df_ga_silver = (df_ga
        # Month of Year is numeric YYYYMM → convert to yyyy-MM string
        .withColumn("Month_Key",
            F.concat(
                F.substring(F.col("Month_of_Year").cast("string"), 1, 4), F.lit("-"),
                F.substring(F.col("Month_of_Year").cast("string"), 5, 2)
            )
        )
        .withColumn("Site_Key",      build_map_expr(F.col("Source"), site_map_ga))
        .withColumn("Ad_Content_Clean", F.trim(F.col("Ad_Content")))
        .withColumn("Sessions",      F.coalesce(F.col("Sessions").cast("long"), F.lit(0)))
        .withColumn("Users",         F.coalesce(F.col("Users").cast("long"), F.lit(0)))
        .withColumn("_transformed_at", F.current_timestamp())
    )

    df_ga_silver.write.format("delta").mode("overwrite") \
        .option("overwriteSchema", "true").saveAsTable("marketing_ga_cleaned")
    print("[✓] marketing_ga_cleaned OK — rows:", df_ga_silver.count())

except Exception as e:
    print(f"[-] Error GA Silver: {e}"); raise e

print("\n" + "="*80)
print("[🚀 SILVER LISTA — llaves Site_Key + Month_Key listas para el join en Gold]")
print("="*80)

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
