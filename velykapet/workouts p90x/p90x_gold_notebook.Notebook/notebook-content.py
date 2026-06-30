# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "5846138b-520e-429b-8e30-7d9a17223730",
# META       "default_lakehouse_name": "p90x_workout_lh",
# META       "default_lakehouse_workspace_id": "b14581ac-9906-43e2-809c-c2fd4315ad5b",
# META       "known_lakehouses": [
# META         {
# META           "id": "5846138b-520e-429b-8e30-7d9a17223730"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Gold Layer - p90x workout aggregations
from pyspark.sql import functions as F
from pyspark.sql.window import Window

lakehouse = "p90x_workout_lh"

# ── Load silver tables ──────────────────────────────────────────
ex = spark.read.format("delta").load(f"Tables/dbo/silver_exercise_records")
ws = spark.read.format("delta").load(f"Tables/dbo/silver_workout_sessions")

# ── 1. gold_session_summary ─────────────────────────────────────
# One row per session: date, difficulty, total sets, total reps, total volume
session_stats = ex.groupBy("session_id").agg(
    F.count("*").alias("total_sets"),
    F.sum("reps").alias("total_reps"),
    F.sum(F.when(F.col("weight").isNotNull(), F.col("reps") * F.col("weight")).otherwise(0)).alias("total_volume_lbs")
)

gold_session_summary = ws.join(session_stats, "session_id", "left") \
    .select(
        "session_id",
        "completed_at",
        "difficulty",
        "recovery_days_since_previous",
        "total_sets",
        "total_reps",
        "total_volume_lbs"
    )

gold_session_summary.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold_session_summary")

print("✅ gold_session_summary done:", gold_session_summary.count(), "rows")

# ── 2. gold_weekly_volume ───────────────────────────────────────
# Aggregate by ISO week: sets, reps, volume, sessions count
ws_with_week = ws.withColumn("week_start", F.date_trunc("week", F.col("completed_at"))) \
                 .withColumn("year_week", F.concat(
                    F.year(F.col("completed_at")).cast("string"),
                    F.lit("-W"),
                    F.lpad(F.weekofyear(F.col("completed_at")).cast("string"), 2, "0")
))

sessions_per_week = ws_with_week.groupBy("week_start", "year_week").agg(
    F.count("session_id").alias("sessions_count")
)

ex_with_week = ex.join(ws_with_week.select("session_id", "week_start", "year_week"), "session_id", "left")

weekly_ex = ex_with_week.groupBy("week_start", "year_week").agg(
    F.count("*").alias("total_sets"),
    F.sum("reps").alias("total_reps"),
    F.sum(F.when(F.col("weight").isNotNull(), F.col("reps") * F.col("weight")).otherwise(0)).alias("total_volume_lbs")
)

gold_weekly_volume = sessions_per_week.join(weekly_ex, ["week_start", "year_week"], "left") \
    .orderBy("week_start")

gold_weekly_volume.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold_weekly_volume")

print("✅ gold_weekly_volume done:", gold_weekly_volume.count(), "rows")

# ── 3. gold_exercise_prs ────────────────────────────────────────
# Best performance per exercise:
# - Max weight ever lifted (for REPS_WEIGHT)
# - Max reps at that weight
# - Date it was achieved

weight_ex = ex.filter(F.col("weight").isNotNull()) \
    .join(ws.select("session_id", "completed_at"), "session_id", "left")

window_pr = Window.partitionBy("exercise_name").orderBy(
    F.col("weight").desc(), F.col("reps").desc()
)

gold_exercise_prs = weight_ex \
    .withColumn("rank", F.row_number().over(window_pr)) \
    .filter(F.col("rank") == 1) \
    .select(
        "exercise_name",
        "weight",
        "reps",
        "completed_at",
        "workout_part"
    ) \
    .withColumnRenamed("completed_at", "pr_achieved_at")

gold_exercise_prs.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold_exercise_prs")

print("✅ gold_exercise_prs done:", gold_exercise_prs.count(), "rows")

# ── 4. gold_workout_streak ──────────────────────────────────────
window_streak = Window.orderBy("completed_at")

gold_workout_streak = ws \
    .withColumn("workout_date", F.to_date("completed_at")) \
    .select("session_id", "workout_date", "completed_at", "recovery_days_since_previous", "difficulty") \
    .withColumn("cumulative_sessions", F.row_number().over(window_streak)) \
    .withColumn("is_rest_day", F.col("recovery_days_since_previous") > 1) \
    .drop("completed_at")

gold_workout_streak.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold_workout_streak")

print("✅ gold_workout_streak done:", gold_workout_streak.count(), "rows")

print("\n🏆 All gold tables created successfully!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── dim_date ────────────────────────────────────────────────────
from pyspark.sql import functions as F
from pyspark.sql.types import *
import pandas as pd

# Generate date range covering your data + future buffer
date_range = pd.date_range(start="2026-01-01", end="2027-12-31", freq="D")

df_dates = spark.createDataFrame(
    [(d.date(),) for d in date_range], ["date"]
)

dim_date = df_dates \
    .withColumn("date_key", F.date_format("date", "yyyyMMdd").cast("int")) \
    .withColumn("year", F.year("date")) \
    .withColumn("month_num", F.month("date")) \
    .withColumn("month_name", F.date_format("date", "MMMM")) \
    .withColumn("month_short", F.date_format("date", "MMM")) \
    .withColumn("quarter", F.quarter("date")) \
    .withColumn("quarter_label", F.concat(F.lit("Q"), F.quarter("date").cast("string"))) \
    .withColumn("week_of_year", F.weekofyear("date")) \
    .withColumn("year_week", F.concat(
        F.year("date").cast("string"),
        F.lit("-W"),
        F.lpad(F.weekofyear("date").cast("string"), 2, "0")
    )) \
    .withColumn("week_start", F.date_trunc("week", F.col("date").cast("timestamp"))) \
    .withColumn("day_of_week_num", F.dayofweek("date")) \
    .withColumn("day_name", F.date_format("date", "EEEE")) \
    .withColumn("day_short", F.date_format("date", "EEE")) \
    .withColumn("is_weekend", F.dayofweek("date").isin([1, 7])) \
    .withColumn("day_of_month", F.dayofmonth("date")) \
    .withColumn("day_of_year", F.dayofyear("date"))

dim_date.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("dim_date")

print("✅ dim_date done:", dim_date.count(), "rows")

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
