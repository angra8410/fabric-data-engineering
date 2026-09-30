# ==============================================================================
# UNIVERSAL READING TRACKER - MICROSOFT FABRIC LAKEHOUSE INGESTION PIPELINE
# PySpark Notebook script for Medallion Architecture (Bronze -> Silver -> Gold)
# Compatible with: Microsoft Fabric Synapse Data Engineering / Lakehouse / Power BI Direct Lake
# ==============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, explode, from_unixtime, to_date, to_timestamp, 
    round as spark_round, when, lit, current_timestamp, date_format
)
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, IntegerType, 
    BooleanType, DoubleType, TimestampType
)

# ------------------------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# ------------------------------------------------------------------------------
# When running in Microsoft Fabric, 'spark' session is pre-initialized.
# Default OneLake Files path for the exported JSON:
JSON_INPUT_PATH = "Files/reading_tracker/universal_reading_tracker_export_*.json"

# Target Lakehouse Delta Table Names:
TABLE_SESSIONS = "silver_reading_sessions"
TABLE_DAILY = "silver_daily_reading_summaries"
TABLE_BOOKS = "silver_books_catalog"
TABLE_GOALS = "silver_reading_goals"
TABLE_MILESTONES = "silver_milestones"

print(">>> [1/5] Iniciando lectura de JSON multilínea desde OneLake...")

# ------------------------------------------------------------------------------
# 2. BRONZE LAYER: INGESTA MULTILÍNEA DEL EXPORT JSON
# ------------------------------------------------------------------------------
# El exportador de la app genera un JSON jerárquico enriquecido.
# spark.read con option('multiline', 'true') deserializa el documento raíz.
raw_df = spark.read \
    .option("multiline", "true") \
    .json(JSON_INPUT_PATH)

print(f">>> Esquema raíz detectado:")
raw_df.printSchema()

# ------------------------------------------------------------------------------
# 3. SILVER LAYER: NORMALIZACIÓN Y TIPADO FUERTE
# ------------------------------------------------------------------------------
print(">>> [2/5] Transformando y normalizando colecciones a Silver Delta Tables...")

# --- A. READING SESSIONS (Historial detallado de cada lectura) ---
df_sessions = raw_df.select(explode("sessions").alias("s")).select(
    col("s.id").cast(LongType()).alias("session_id"),
    col("s.bookId").cast(LongType()).alias("book_id"),
    col("s.bookTitle").cast(StringType()).alias("book_title"),
    col("s.bookAuthor").cast(StringType()).alias("book_author"),
    col("s.modality").cast(StringType()).alias("modality"),
    col("s.providerId").cast(StringType()).alias("provider_id"),
    to_timestamp(from_unixtime(col("s.startTimeEpoch") / 1000)).alias("start_time"),
    to_timestamp(from_unixtime(col("s.endTimeEpoch") / 1000)).alias("end_time"),
    col("s.durationMinutes").cast(IntegerType()).alias("duration_minutes"),
    col("s.realDurationSeconds").cast(LongType()).alias("real_duration_seconds"),
    col("s.startPage").cast(IntegerType()).alias("start_page"),
    col("s.endPage").cast(IntegerType()).alias("end_page"),
    col("s.pagesRead").cast(IntegerType()).alias("pages_read"),
    col("s.status").cast(StringType()).alias("status"),
    col("s.notes").cast(StringType()).alias("notes")
)

# Cálculo de KPIs derivados: Horas leídas y velocidad págs/hora
df_sessions = df_sessions.withColumn(
    "duration_hours", spark_round(col("duration_minutes") / 60.0, 2)
).withColumn(
    "pages_per_hour",
    when(
        (col("duration_minutes") > 0) & (col("pages_read") > 0),
        spark_round((col("pages_read") / col("duration_minutes")) * 60.0, 1)
    ).otherwise(lit(None))
).withColumn(
    "has_notes", when(col("notes") != "", lit(True)).otherwise(lit(False))
).withColumn(
    "_ingested_at", current_timestamp()
)

# --- B. DAILY READING SUMMARIES (Consolidado por fecha y racha de 164+ días) ---
df_daily = raw_df.select(explode("dailySummaries").alias("d")).select(
    to_date(col("d.date")).alias("reading_date"),
    col("d.totalMinutesRead").cast(IntegerType()).alias("total_minutes_read"),
    col("d.audioMinutes").cast(IntegerType()).alias("audio_minutes"),
    col("d.kindleMinutes").cast(IntegerType()).alias("kindle_minutes"),
    col("d.physicalMinutes").cast(IntegerType()).alias("physical_minutes"),
    col("d.goalReached").cast(BooleanType()).alias("goal_reached"),
    col("d.isHistoricalBackfill").cast(BooleanType()).alias("is_historical_backfill"),
    col("d.isBimodal").cast(BooleanType()).alias("is_bimodal")
).withColumn(
    "day_of_week", date_format(col("reading_date"), "EEEE")
).withColumn(
    "total_hours_read", spark_round(col("total_minutes_read") / 60.0, 2)
).withColumn(
    "audio_percentage",
    when(col("total_minutes_read") > 0, spark_round((col("audio_minutes") / col("total_minutes_read")) * 100, 1)).otherwise(lit(0))
).withColumn(
    "kindle_percentage",
    when(col("total_minutes_read") > 0, spark_round((col("kindle_minutes") / col("total_minutes_read")) * 100, 1)).otherwise(lit(0))
).withColumn(
    "_ingested_at", current_timestamp()
)

# --- C. BOOKS CATALOG (Catálogo de obras y progreso) ---
df_books = raw_df.select(explode("books").alias("b")).select(
    col("b.id").cast(LongType()).alias("book_id"),
    col("b.title").cast(StringType()).alias("title"),
    col("b.author").cast(StringType()).alias("author"),
    col("b.format").cast(StringType()).alias("format"),
    col("b.primaryProvider").cast(StringType()).alias("primary_provider"),
    col("b.progressUnit").cast(StringType()).alias("progress_unit"),
    col("b.currentPosition").cast(IntegerType()).alias("current_position"),
    col("b.totalUnits").cast(IntegerType()).alias("total_units"),
    col("b.progressPercentage").cast(IntegerType()).alias("progress_percentage"),
    col("b.isCurrentlyReading").cast(BooleanType()).alias("is_currently_reading"),
    col("b.isCompleted").cast(BooleanType()).alias("is_completed")
).withColumn(
    "_ingested_at", current_timestamp()
)

# --- D. MILESTONES & GOALS (Metas e Insignias Obsidian) ---
df_milestones = raw_df.select(explode("milestones").alias("m")).select(
    col("m.id").cast(StringType()).alias("milestone_id"),
    col("m.title").cast(StringType()).alias("title"),
    col("m.description").cast(StringType()).alias("description"),
    col("m.iconEmoji").cast(StringType()).alias("emoji"),
    col("m.isUnlocked").cast(BooleanType()).alias("is_unlocked"),
    col("m.progressLabel").cast(StringType()).alias("progress_label"),
    col("m.progressPercent").cast(DoubleType()).alias("progress_percent"),
    col("m.tierName").cast(StringType()).alias("tier_name"),
    current_timestamp().alias("_ingested_at")
)

df_goals = raw_df.select("goals.*").withColumn("_ingested_at", current_timestamp())

# ------------------------------------------------------------------------------
# 4. PERSISTENCIA EN DELTA LAKE (FABRIC LAKEHOUSE)
# ------------------------------------------------------------------------------
print(">>> [3/5] Guardando tablas Delta en el Lakehouse...")

df_sessions.write.format("delta").mode("overwrite").saveAsTable(TABLE_SESSIONS)
df_daily.write.format("delta").mode("overwrite").saveAsTable(TABLE_DAILY)
df_books.write.format("delta").mode("overwrite").saveAsTable(TABLE_BOOKS)
df_milestones.write.format("delta").mode("overwrite").saveAsTable(TABLE_MILESTONES)
df_goals.write.format("delta").mode("overwrite").saveAsTable(TABLE_GOALS)

print(f"    ✓ Tabla Delta '{TABLE_SESSIONS}' guardada ({df_sessions.count()} filas)")
print(f"    ✓ Tabla Delta '{TABLE_DAILY}' guardada ({df_daily.count()} días)")
print(f"    ✓ Tabla Delta '{TABLE_BOOKS}' guardada ({df_books.count()} libros)")
print(f"    ✓ Tabla Delta '{TABLE_MILESTONES}' guardada ({df_milestones.count()} insignias)")

# ------------------------------------------------------------------------------
# 5. GOLD LAYER: VISTAS ANALÍTICAS PARA POWER BI DIRECT LAKE
# ------------------------------------------------------------------------------
print(">>> [4/5] Creando vistas Gold analíticas para Power BI...")

# Vista 1: Resumen ejecutivo general (KPIs)
spark.sql(f"""
CREATE OR REPLACE VIEW gold_reading_kpis AS
SELECT
    COUNT(DISTINCT reading_date) AS total_tracked_days,
    SUM(total_minutes_read) AS total_minutes_all_time,
    ROUND(SUM(total_minutes_read) / 60.0, 1) AS total_hours_all_time,
    SUM(audio_minutes) AS total_audio_minutes,
    SUM(kindle_minutes) AS total_kindle_minutes,
    ROUND(SUM(audio_minutes) * 100.0 / NULLIF(SUM(total_minutes_read), 0), 1) AS audio_share_pct,
    ROUND(SUM(kindle_minutes) * 100.0 / NULLIF(SUM(total_minutes_read), 0), 1) AS kindle_share_pct,
    COUNT(CASE WHEN is_bimodal THEN 1 END) AS bimodal_days_count,
    COUNT(CASE WHEN goal_reached THEN 1 END) AS days_with_goal_met
FROM {TABLE_DAILY}
""")

# Vista 2: Rendimiento y ritmo por libro
spark.sql(f"""
CREATE OR REPLACE VIEW gold_book_reading_velocity AS
SELECT
    b.book_id,
    b.title,
    b.author,
    b.format,
    b.progress_percentage,
    b.is_completed,
    COUNT(s.session_id) AS total_sessions,
    SUM(s.duration_minutes) AS total_minutes_invested,
    ROUND(SUM(s.duration_minutes) / 60.0, 1) AS total_hours_invested,
    SUM(s.pages_read) AS total_pages_read,
    ROUND(AVG(s.pages_per_hour), 1) AS avg_speed_pages_per_hour,
    MAX(s.end_time) AS last_read_timestamp
FROM {TABLE_BOOKS} b
LEFT JOIN {TABLE_SESSIONS} s ON b.book_id = s.book_id
GROUP BY b.book_id, b.title, b.author, b.format, b.progress_percentage, b.is_completed
ORDER BY total_minutes_invested DESC
""")

# Vista 3: Tendencia mensual de minutos para reportes periódicos
spark.sql(f"""
CREATE OR REPLACE VIEW gold_monthly_reading_trend AS
SELECT
    DATE_FORMAT(reading_date, 'yyyy-MM') AS year_month,
    COUNT(reading_date) AS active_reading_days,
    SUM(total_minutes_read) AS monthly_minutes,
    ROUND(SUM(total_minutes_read) / 60.0, 1) AS monthly_hours,
    SUM(audio_minutes) AS monthly_audio_mins,
    SUM(kindle_minutes) AS monthly_kindle_mins,
    COUNT(CASE WHEN goal_reached THEN 1 END) AS days_goal_reached
FROM {TABLE_DAILY}
GROUP BY DATE_FORMAT(reading_date, 'yyyy-MM')
ORDER BY year_month DESC
""")

print(">>> [5/5] ¡Pipeline completado con éxito! Tablas y Vistas listas para Direct Lake en Power BI.")
