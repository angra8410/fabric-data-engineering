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

import re
import pandas as pd
from datetime import datetime
from pyspark.sql import functions as F
from pyspark.sql.window import Window

gold_prefix = "gold_"
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

print("=====================================================================")
print("🚀 INICIANDO PROCESAMIENTO MAESTRO: CAPA GOLD (MODELO ESTRELLA)")
print("=====================================================================\n")

spark.catalog.clearCache()
silver_tables = ["silver_discovery", "silver_engagement", "silver_top_posts", "silver_followers", "silver_demographics"]

for t in silver_tables:
    try:
        spark.catalog.refreshTable(t)
    except Exception as e:
        print(f"⚠️ Aviso al refrescar {t}: {e}")

print("➔ Caché limpia y tablas Silver sincronizadas.")


# =====================================================================
# BLOQUE 1. TABLA DE HECHOS: Desempeño Diario (Daily Performance)
# =====================================================================
print("\n[1/5] Generando hechos diarios: gold_fact_daily_performance...")

df_eng = spark.read.table("silver_engagement").drop("silver_load_timestamp")
df_fol = spark.read.table("silver_followers").drop("silver_load_timestamp")

df_daily_perf = df_eng.join(df_fol, on="date", how="outer")

numeric_cols = ["impressions", "engagements", "new_followers"]
df_daily_perf = df_daily_perf.fillna(0, subset=numeric_cols)

df_daily_perf = df_daily_perf.withColumn(
    "engagement_rate",
    F.when(F.col("impressions") > 0, F.col("engagements") / F.col("impressions")).otherwise(0.0)
)

window_spec = Window.orderBy("date").rowsBetween(Window.unboundedPreceding, Window.currentRow)
df_daily_perf_updated = df_daily_perf.withColumn(
    "cumulative_followers",
    F.sum("new_followers").over(window_spec)
)

df_daily_perf_updated = df_daily_perf_updated.withColumn("gold_load_timestamp", F.current_timestamp())
(df_daily_perf_updated.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_daily_performance"))

print("  ➔ Éxito: Tabla 'gold_fact_daily_performance' creada y actualizada.")


# =====================================================================
# BLOQUE 2. TABLA DE DIMENSIÓN: Demografía de la Audiencia
# =====================================================================
print("\n[2/5] Generando dimensión: gold_dim_demographics...")

df_demo = spark.read.table("silver_demographics")

df_demo_clean = df_demo.select(
    F.col("start_date").cast("date").alias("start_date"),
    F.col("end_date").cast("date").alias("end_date"),
    F.col("top_demographics").alias("demographic_category"),
    F.col("value").alias("demographic_value"),
    F.col("percentage")
)

df_demo_clean = df_demo_clean.withColumn("gold_load_timestamp", F.current_timestamp())
(df_demo_clean.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}dim_demographics"))

print("  ➔ Éxito: Tabla 'gold_dim_demographics' actualizada con rangos de fecha reales.")


# =====================================================================
# BLOQUE 3. TABLA DE HECHOS: Desempeño de Posts Principales (Top Posts)
# =====================================================================
print("\n[3/5] Generando hechos de contenido: gold_fact_top_posts...")

df_posts = spark.read.table("silver_top_posts")

df_posts_clean = df_posts.withColumn(
    "post_engagement_rate",
    F.when(F.col("impressions") > 0, F.col("engagements") / F.col("impressions")).otherwise(0.0)
)

df_posts_clean = df_posts_clean.withColumn(
    "post_slug",
    F.when(
        F.col("post_url").contains("antoniogutierrez-data_"),
        F.split(F.split(F.col("post_url"), "antoniogutierrez-data_").getItem(1), "-ugcPost").getItem(0)
    ).otherwise(F.lit("Other Post"))
)

df_posts_clean = df_posts_clean.withColumn(
    "post_title",
    F.initcap(F.regexp_replace(F.col("post_slug"), "[-_]", " "))
)

df_posts_updated = df_posts_clean.withColumn(
    "engagement_tier",
    F.when(F.col("engagements") >= 10, "1. Viral (10+ Engagements)")
     .when(F.col("engagements") >= 5, "2. High (5-9 Engagements)")
     .when(F.col("engagements") >= 1, "3. Active (1-4 Engagements)")
     .otherwise("4. No Engagement")
)

df_posts_reporting = df_posts_updated.select(
    F.col("post_publish_date"),
    F.col("post_title"),
    F.col("post_url"),
    F.col("impressions"),
    F.col("engagements"),
    F.col("post_engagement_rate"),
    F.col("engagement_tier"),
    F.current_timestamp().alias("gold_load_timestamp")
)

(df_posts_reporting.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_top_posts"))

print("  ➔ Éxito: Tabla 'gold_fact_top_posts' con clasificación de rendimiento.")


# =====================================================================
# BLOQUE 4. TABLA DE HECHOS: Resumen Semanal Agregado
# =====================================================================
print("\n[4/5] Creando agregados: gold_fact_weekly_summary...")

df_weekly_summary = df_daily_perf_updated.groupBy(
    F.to_date(F.date_trunc("week", F.col("date"))).alias("week_start_date")
).agg(
    F.sum("impressions").alias("total_impressions"),
    F.sum("engagements").alias("total_engagements"),
    F.sum("new_followers").alias("total_new_followers"),
    F.when(F.sum("impressions") > 0,
           F.sum("engagements") / F.sum("impressions")
          ).otherwise(0.0).alias("weekly_engagement_rate")
)

df_weekly_summary = df_weekly_summary.withColumn("gold_load_timestamp", F.current_timestamp())

(df_weekly_summary.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_weekly_summary"))

print("  ➔ Éxito: Tabla de tendencias agregadas 'gold_fact_weekly_summary' lista.")


# =====================================================================
# BLOQUE 5. TABLA DE DIMENSIÓN: Calendario Dinámico (Rolling Calendar)
# =====================================================================
print("\n[5/5] Generando dimensión temporal: gold_dim_date...")

current_year = datetime.now().year

try:
    min_date_val = df_daily_perf_updated.select(F.min("date")).first()[0]
    start_year = min_date_val.year if min_date_val else (current_year - 2)
except Exception:
    start_year = current_year - 2

try:
    max_date_val = df_daily_perf_updated.select(F.max("date")).first()[0]
    max_fact_year = max_date_val.year if max_date_val else current_year
except Exception:
    max_fact_year = current_year

end_year = max(max_fact_year, current_year + 1)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

print(f"   -> Límites de calendario inteligente: {start_date} hasta {end_date}")

df_dates_base = spark.sql(f"""
    SELECT explode(sequence(to_date('{start_date}'), to_date('{end_date}'), interval 1 day)) as date
""")

df_dim_date = df_dates_base.select(
    F.col("date"),
    F.year("date").alias("year"),
    F.quarter("date").alias("quarter"),
    F.concat(F.lit("Q"), F.quarter("date")).alias("quarter_name"),
    F.concat(F.lit("Q"), F.quarter("date"), F.lit(" "), F.year("date")).alias("quarter_year"),
    F.month("date").alias("month_number"),
    F.date_format("date", "MMMM").alias("month_name"),
    F.date_format("date", "MMM").alias("month_short"),
    F.date_format("date", "yyyy-MM").alias("year_month"),
    F.date_format("date", "MMM yyyy").alias("year_month_short"),
    F.dayofmonth("date").alias("day_of_month"),
    F.dayofyear("date").alias("day_of_year"),
    F.dayofweek("date").alias("day_of_week_number"),
    F.date_format("date", "EEEE").alias("day_name"),
    F.date_format("date", "E").alias("day_short"),
    F.when(F.dayofweek("date").isin(1, 7), 1).otherwise(0).alias("is_weekend"),
    F.weekofyear("date").alias("week_of_year"),
    F.to_date(F.date_trunc("week", F.col("date"))).alias("week_start_date"),
    F.date_add(F.to_date(F.date_trunc("week", F.col("date"))), 6).alias("week_end_date"),
    F.datediff(F.col("date"), F.current_date()).alias("day_offset"),
    (
        ((F.year("date") - F.year(F.current_date())) * 12) +
        (F.month("date") - F.month(F.current_date()))
    ).alias("month_offset"),
    (F.year("date") - F.year(F.current_date())).alias("year_offset"),
    F.current_timestamp().alias("gold_load_timestamp")
)

(df_dim_date.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable("gold_dim_date"))

print("  ➔ Éxito: Dimensión temporal 'gold_dim_date' recalculada correctamente.")

print("\n=====================================================================")
print("🚀 ¡PROCESO FINALIZADO EXITOSAMENTE! Capa Gold guardada al 100% en OneLake.")
print("=====================================================================")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import re
import pandas as pd
from datetime import datetime
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Configuración de prefijos y entornos
gold_prefix = "gold_"
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

print("=====================================================================")
print("🚀 INICIANDO PROCESAMIENTO MAESTRO: CAPA GOLD (MODELO ESTRELLA)")
print("=====================================================================\n")

# 1. Limpieza de caché y refresco de tablas Silver
spark.catalog.clearCache()
silver_tables = ["silver_discovery", "silver_engagement", "silver_top_posts", "silver_followers", "silver_demographics"]

for t in silver_tables:
    try:
        spark.catalog.refreshTable(t)
    except Exception as e:
        print(f"⚠️ Aviso al refrescar {t}: {e}")

print("➔ Caché limpia y tablas Silver sincronizadas.")


# =====================================================================
# BLOQUE 1. TABLA DE HECHOS: Desempeño Diario (Daily Performance)
# =====================================================================
print("\n[1/5] Generando hechos diarios: gold_fact_daily_performance...")

# Eliminar marcas de tiempo de carga de Silver para evitar columnas duplicadas en el Join
df_eng = spark.read.table("silver_engagement").drop("silver_load_timestamp")
df_fol = spark.read.table("silver_followers").drop("silver_load_timestamp")

# Outer join por fecha
df_daily_perf = df_eng.join(df_fol, on="date", how="outer")

# Rellenar métricas numéricas con cero para evitar nulos en Power BI
numeric_cols = ["impressions", "engagements", "new_followers"]
df_daily_perf = df_daily_perf.fillna(0, subset=numeric_cols)

# Calcular tasa de engagement diaria
df_daily_perf = df_daily_perf.withColumn(
    "engagement_rate",
    F.when(F.col("impressions") > 0, F.col("engagements") / F.col("impressions")).otherwise(0.0)
)

# Añadir métricas de ventana (Acumulado histórico de seguidores)
window_spec = Window.orderBy("date").rowsBetween(Window.unboundedPreceding, Window.currentRow)
df_daily_perf_updated = df_daily_perf.withColumn(
    "cumulative_followers",
    F.sum("new_followers").over(window_spec)
)

# Agregar auditoría y guardar
df_daily_perf_updated = df_daily_perf_updated.withColumn("gold_load_timestamp", F.current_timestamp())
(df_daily_perf_updated.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_daily_performance"))

print("  ➔ Éxito: Tabla 'gold_fact_daily_performance' creada y actualizada.")


# =====================================================================
# BLOQUE 2. TABLA DE DIMENSIÓN: Demografía de la Audiencia (Protected)
# =====================================================================
print("\n[2/5] Generando dimensión protegida: gold_dim_demographics...")

df_demo = spark.read.table("silver_demographics")

# Blindaje contra Schema Drift: Inyectamos start_date y end_date como NULL tipo fecha
df_demo_clean = df_demo.select(
    F.lit(None).cast("date").alias("start_date"),  
    F.lit(None).cast("date").alias("end_date"),    
    F.col("top_demographics").alias("demographic_category"),
    F.col("value").alias("demographic_value"),
    F.col("percentage")
)

df_demo_clean = df_demo_clean.withColumn("gold_load_timestamp", F.current_timestamp())
(df_demo_clean.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}dim_demographics"))

print("  ➔ Éxito: Tabla 'gold_dim_demographics' estructurada de forma segura.")


# =====================================================================
# BLOQUE 3. TABLA DE HECHOS: Desempeño de Posts Principales (Top Posts)
# =====================================================================
print("\n[3/5] Generando hechos de contenido: gold_fact_top_posts...")

df_posts = spark.read.table("silver_top_posts")

# Calcular tasa de engagement individual por post
df_posts_clean = df_posts.withColumn(
    "post_engagement_rate",
    F.when(F.col("impressions") > 0, F.col("engagements") / F.col("impressions")).otherwise(0.0)
)

# Limpiar URLs para extraer un título legible (slug)
df_posts_clean = df_posts_clean.withColumn(
    "post_slug",
    F.when(
        F.col("post_url").contains("antoniogutierrez-data_"),
        F.split(F.split(F.col("post_url"), "antoniogutierrez-data_").getItem(1), "-ugcPost").getItem(0)
    ).otherwise(F.lit("Other Post"))
)

# Formatear título (Mayúsculas iniciales y quitar guiones)
df_posts_clean = df_posts_clean.withColumn(
    "post_title",
    F.initcap(F.regexp_replace(F.col("post_slug"), "[-_]", " "))
)

# Clasificación analítica por Tiers de rendimiento (Paréntesis corregido)
df_posts_updated = df_posts_clean.withColumn(
    "engagement_tier",
    F.when(F.col("engagements") >= 10, "1. Viral (10+ Engagements)")
     .when(F.col("engagements") >= 5, "2. High (5-9 Engagements)")
     .when(F.col("engagements") >= 1, "3. Active (1-4 Engagements)")
     .otherwise("4. No Engagement")
)

# Reordenar y limpiar layout final
df_posts_reporting = df_posts_updated.select(
    F.col("post_publish_date"),
    F.col("post_title"),
    F.col("post_url"),
    F.col("impressions"),
    F.col("engagements"),
    F.col("post_engagement_rate"),
    F.col("engagement_tier"),
    F.current_timestamp().alias("gold_load_timestamp")
)

(df_posts_reporting.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_top_posts"))

print("  ➔ Éxito: Tabla 'gold_fact_top_posts' con clasificación de rendimiento.")


# =====================================================================
# BLOQUE 4. TABLA DE HECHOS: Resumen Semanal Agregado
# =====================================================================
print("\n[4/5] Creando agregados: gold_fact_weekly_summary...")

# Agrupación y resumen basados en la tabla de hechos diarios actualizada
df_weekly_summary = df_daily_perf_updated.groupBy(
    F.to_date(F.date_trunc("week", F.col("date"))).alias("week_start_date")
).agg(
    F.sum("impressions").alias("total_impressions"),
    F.sum("engagements").alias("total_engagements"),
    F.sum("new_followers").alias("total_new_followers"),
    F.when(F.sum("impressions") > 0, 
           F.sum("engagements") / F.sum("impressions")
          ).otherwise(0.0).alias("weekly_engagement_rate")
)

df_weekly_summary = df_weekly_summary.withColumn("gold_load_timestamp", F.current_timestamp())

(df_weekly_summary.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_weekly_summary"))

print("  ➔ Éxito: Tabla de tendencias agregadas 'gold_fact_weekly_summary' lista.")


# =====================================================================
# BLOQUE 5. TABLA DE DIMENSIÓN: Calendario Dinámico (Rolling Calendar)
# =====================================================================
print("\n[5/5] Generando dimensión temporal: gold_dim_date...")

current_year = datetime.now().year

# Buscar límites dinámicos en los hechos diarios reales
try:
    min_date_val = df_daily_perf_updated.select(F.min("date")).first()[0]
    start_year = min_date_val.year if min_date_val else (current_year - 2)
except Exception:
    start_year = current_year - 2

try:
    max_date_val = df_daily_perf_updated.select(F.max("date")).first()[0]
    max_fact_year = max_date_val.year if max_date_val else current_year
except Exception:
    max_fact_year = current_year

end_year = max(max_fact_year, current_year + 1)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

print(f"   -> Límites de calendario inteligente: {start_date} hasta {end_date}")

df_dates_base = spark.sql(f"""
    SELECT explode(sequence(to_date('{start_date}'), to_date('{end_date}'), interval 1 day)) as date
""")

df_dim_date = df_dates_base.select(
    F.col("date"),
    F.year("date").alias("year"),
    F.quarter("date").alias("quarter"),
    F.concat(F.lit("Q"), F.quarter("date")).alias("quarter_name"),
    F.concat(F.lit("Q"), F.quarter("date"), F.lit(" "), F.year("date")).alias("quarter_year"),
    F.month("date").alias("month_number"),
    F.date_format("date", "MMMM").alias("month_name"),
    F.date_format("date", "MMM").alias("month_short"),
    F.date_format("date", "yyyy-MM").alias("year_month"),
    F.date_format("date", "MMM yyyy").alias("year_month_short"),
    F.dayofmonth("date").alias("day_of_month"),
    F.dayofyear("date").alias("day_of_year"),
    F.dayofweek("date").alias("day_of_week_number"),
    F.date_format("date", "EEEE").alias("day_name"),
    F.date_format("date", "E").alias("day_short"),
    F.when(F.dayofweek("date").isin(1, 7), 1).otherwise(0).alias("is_weekend"),
    F.weekofyear("date").alias("week_of_year"),
    F.to_date(F.date_trunc("week", F.col("date"))).alias("week_start_date"),
    F.date_add(F.to_date(F.date_trunc("week", F.col("date"))), 6).alias("week_end_date"),
    
    # Atributos dinámicos de desplazamiento (Offsets relativos a hoy)
    F.datediff(F.col("date"), F.current_date()).alias("day_offset"),
    (
        ((F.year("date") - F.year(F.current_date())) * 12) + 
        (F.month("date") - F.month(F.current_date()))
    ).alias("month_offset"),
    (F.year("date") - F.year(F.current_date())).alias("year_offset"),
    
    F.current_timestamp().alias("gold_load_timestamp")
)

(df_dim_date.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable("gold_dim_date"))

print("  ➔ Éxito: Dimensión temporal 'gold_dim_date' recalculada correctamente.")

print("\n=====================================================================")
print("🚀 ¡PROCESO FINALIZADO EXITOSAMENTE! Capa Gold guardada al 100% en OneLake.")
print("=====================================================================")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

import pandas as pd
from pyspark.sql import functions as F

# 1. Clear cache and refresh Silver tables
spark.catalog.clearCache()
silver_tables = ["silver_discovery", "silver_engagement", "silver_top_posts", "silver_followers", "silver_demographics"]
gold_prefix = "gold_"

for t in silver_tables:
    try:
        spark.catalog.refreshTable(t)
    except Exception as e:
        print(f"Refresh warning for {t}: {e}")

# Enable schema auto-merge
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

print("--- BUILDING GOLD REPORTING LAYER ---")

# =====================================================================
# 1. FACT TABLE: Daily Performance (Engagement + Followers)
# =====================================================================
print("\nCreating gold_fact_daily_performance...")

# Drop the silver metadata timestamps before joining to avoid duplicate column errors
df_eng = spark.read.table("silver_engagement").drop("silver_load_timestamp")
df_fol = spark.read.table("silver_followers").drop("silver_load_timestamp")

# Outer join on date
df_daily_perf = df_eng.join(df_fol, on="date", how="outer")

# Fill any null metrics with 0 (using only the columns that exist in your tables)
numeric_cols = ["impressions", "engagements", "new_followers"]
df_daily_perf = df_daily_perf.fillna(0, subset=numeric_cols)

# Re-calculate daily engagement rate using engagements and impressions
df_daily_perf = df_daily_perf.withColumn(
    "engagement_rate",
    F.when(F.col("impressions") > 0, 
           F.col("engagements") / F.col("impressions")
          ).otherwise(0.0)
)

# Add load metadata
df_daily_perf = df_daily_perf.withColumn("gold_load_timestamp", F.current_timestamp())

# Save Daily Fact Table
(df_daily_perf.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_daily_performance"))

print("  -> Created table: gold_fact_daily_performance")
display(df_daily_perf.limit(5))


# =====================================================================
# 2. DIMENSION TABLE: Audience Demographics
# =====================================================================
print("\nCreating gold_dim_demographics...")

df_demo = spark.read.table("silver_demographics")

# Clean up column names and structure for better Power BI visualization
df_demo_clean = df_demo.select(
    F.col("start_date"),
    F.col("end_date"),
    F.col("top_demographics").alias("demographic_category"),
    F.col("value").alias("demographic_value"),
    F.col("percentage")
)

# Add load metadata
df_demo_clean = df_demo_clean.withColumn("gold_load_timestamp", F.current_timestamp())

# Save Demographics Dimension Table
(df_demo_clean.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}dim_demographics"))

print("  -> Created table: gold_dim_demographics")
display(df_demo_clean.limit(5))


# =====================================================================
# 3. FACT TABLE: Top Posts Performance
# =====================================================================
print("\nCreating gold_fact_top_posts...")

df_posts = spark.read.table("silver_top_posts")

# Calculate individual post engagement rate
df_posts_clean = df_posts.withColumn(
    "post_engagement_rate",
    F.when(F.col("impressions") > 0, F.col("engagements") / F.col("impressions")).otherwise(0.0)
)

# Extract a clean Post Title / Topic from the URL for better dashboard labels
# Handle potential variations in URL slugs safely
df_posts_clean = df_posts_clean.withColumn(
    "post_slug",
    F.when(
        F.col("post_url").contains("antoniogutierrez-data_"),
        F.split(F.split(F.col("post_url"), "antoniogutierrez-data_").getItem(1), "-ugcPost").getItem(0)
    ).otherwise(F.lit("Other Post"))
)

# Replace underscores/hyphens with spaces and capitalize for readability
df_posts_clean = df_posts_clean.withColumn(
    "post_title",
    F.initcap(F.regexp_replace(F.col("post_slug"), "[-_]", " "))
)

# Reorder columns for reporting clean layout
df_posts_reporting = df_posts_clean.select(
    F.col("post_publish_date"),
    F.col("post_title"),
    F.col("post_url"),
    F.col("impressions"),
    F.col("engagements"),
    F.col("post_engagement_rate"),
    F.current_timestamp().alias("gold_load_timestamp")
)

# Save Top Posts Fact Table
(df_posts_reporting.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{gold_prefix}fact_top_posts"))

print("  -> Created table: gold_fact_top_posts")
display(df_posts_reporting.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

import re
import pandas as pd
from datetime import datetime
from pyspark.sql import functions as F

print("\nCreating gold_dim_date (Rolling Calendar)...")

# 1. Get the current calendar year
current_year = datetime.now().year

# 2. Dynamically determine start year from fact data (default to 2 years ago if empty)
try:
    min_date_val = spark.read.table("gold_fact_daily_performance").select(F.min("date")).first()[0]
    start_year = min_date_val.year if min_date_val else (current_year - 2)
except Exception:
    start_year = current_year - 2

# 3. Dynamically determine end year: Max of fact data year OR current year + 1 (rolling buffer)
try:
    max_date_val = spark.read.table("gold_fact_daily_performance").select(F.max("date")).first()[0]
    max_fact_year = max_date_val.year if max_date_val else current_year
except Exception:
    max_fact_year = current_year

end_year = max(max_fact_year, current_year + 1)

# Set full-year boundaries
start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

print(f"  -> Rolling Calendar bounds: {start_date} to {end_date} (End Year is rolling: Current + 1)")

# 4. Generate the dates sequence
df_dates_base = spark.sql(f"""
    SELECT explode(sequence(to_date('{start_date}'), to_date('{end_date}'), interval 1 day)) as date
""")

# 5. Derive Time Intelligence attributes
df_dim_date = df_dates_base.select(
    F.col("date"),
    F.year("date").alias("year"),
    F.quarter("date").alias("quarter"),
    F.concat(F.lit("Q"), F.quarter("date")).alias("quarter_name"),
    F.concat(F.lit("Q"), F.quarter("date"), F.lit(" "), F.year("date")).alias("quarter_year"),
    F.month("date").alias("month_number"),
    F.date_format("date", "MMMM").alias("month_name"),
    F.date_format("date", "MMM").alias("month_short"),
    F.date_format("date", "yyyy-MM").alias("year_month"),
    F.date_format("date", "MMM yyyy").alias("year_month_short"),
    F.dayofmonth("date").alias("day_of_month"),
    F.dayofyear("date").alias("day_of_year"),
    # Spark Day of Week: 1 = Sunday, 7 = Saturday
    F.dayofweek("date").alias("day_of_week_number"),
    F.date_format("date", "EEEE").alias("day_name"),
    F.date_format("date", "E").alias("day_short"),
    F.when(F.dayofweek("date").isin(1, 7), 1).otherwise(0).alias("is_weekend"),
    F.weekofyear("date").alias("week_of_year"),
    F.to_date(F.date_trunc("week", F.col("date"))).alias("week_start_date"),
    F.date_add(F.to_date(F.date_trunc("week", F.col("date"))), 6).alias("week_end_date"),
    
    # --- RELATIVE OFFSETS (Recalculated relative to today on every run) ---
    F.datediff(F.col("date"), F.current_date()).alias("day_offset"),
    (
        ((F.year("date") - F.year(F.current_date())) * 12) + 
        (F.month("date") - F.month(F.current_date()))
    ).alias("month_offset"),
    (F.year("date") - F.year(F.current_date())).alias("year_offset"),
    
    F.current_timestamp().alias("gold_load_timestamp")
)

# 6. Save to Gold table
(df_dim_date.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable("gold_dim_date"))

print("  -> Rolling table gold_dim_date successfully updated.")
display(df_dim_date.limit(10))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql.window import Window

# Window spec ordered by date to calculate running total of new followers
window_spec = Window.orderBy("date").rowsBetween(Window.unboundedPreceding, Window.currentRow)

df_daily_perf = df_daily_perf.withColumn(
    "cumulative_followers",
    F.sum("new_followers").over(window_spec)
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

df_posts_reporting = df_posts_reporting.withColumn(
    "engagement_tier",
    F.when(F.col("engagements") >= 10, "1. Viral (10+ Engagements)")
     .when(F.col("engagements") >= 5, "2. High (5-9 Engagements)")
     .when(F.col("engagements") >= 1, "3. Active (1-4 Engagements)")
     .otherwise("4. No Engagement")
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql import functions as F

# Group daily performance by week start date (derived on the fly from the daily date)
df_weekly_summary = df_daily_perf.groupBy(
    F.to_date(F.date_trunc("week", F.col("date"))).alias("week_start_date")
).agg(
    F.sum("impressions").alias("total_impressions"),
    F.sum("engagements").alias("total_engagements"),
    F.sum("new_followers").alias("total_new_followers"),
    # Re-calculate weekly average engagement rate safely (prevent divide by zero)
    F.when(F.sum("impressions") > 0, 
           F.sum("engagements") / F.sum("impressions")
          ).otherwise(0.0).alias("weekly_engagement_rate")
)

# Add load metadata
df_weekly_summary = df_weekly_summary.withColumn("gold_load_timestamp", F.current_timestamp())

# Save as gold_fact_weekly_summary
(df_weekly_summary.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable("gold_fact_weekly_summary"))

print("Successfully created Weekly Summary Fact Table: gold_fact_weekly_summary")
display(df_weekly_summary)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

# =====================================================================
# BLOQUE 6. ENRIQUECIMIENTO: gold_fact_top_posts + contenido real
# =====================================================================
print("\n[6/7] Generando gold_fact_top_posts_enriched...")

df_top_posts_keyed = spark.read.table("gold_fact_top_posts").withColumn(
    "linkedin_urn",
    F.regexp_extract(F.col("post_url"), r"(?:ugcPost|share|activity|document|posts)-([0-9]{15,})", 1)
)

df_content = spark.read.table("silver_post_content")

df_enriched = df_top_posts_keyed.join(
    df_content.select(
        F.col("linkedin_post_id").alias("linkedin_urn"),
        F.col("pillar"),
        F.col("media_format"),
        F.col("post_title").alias("real_post_title"),
    ),
    on="linkedin_urn",
    how="left"
).withColumn("gold_load_timestamp", F.current_timestamp())

(df_enriched.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true").saveAsTable("gold_fact_top_posts_enriched"))
print("  ➔ Éxito: 'gold_fact_top_posts_enriched' — métricas reales de LinkedIn + pillar/formato/título reales de la app.")


# =====================================================================
# BLOQUE 7. PUENTE: gold_bridge_post_hashtags (muchos-a-muchos)
# =====================================================================
print("\n[7/7] Generando gold_bridge_post_hashtags...")

df_bridge = (spark.read.table("silver_post_hashtags")
    .join(spark.read.table("silver_post_content").select("post_id", "linkedin_post_id"), on="post_id", how="left")
    .withColumnRenamed("linkedin_post_id", "linkedin_urn")
    .withColumn("gold_load_timestamp", F.current_timestamp()))

(df_bridge.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true").saveAsTable("gold_bridge_post_hashtags"))
print("  ➔ Éxito: 'gold_bridge_post_hashtags' lista para el modelo semántico.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
