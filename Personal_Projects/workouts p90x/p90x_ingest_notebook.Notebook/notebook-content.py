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

# MARKDOWN ********************

# # P90X Workout Tracker — Ingestion Notebook
# 
# Loads a single backup JSON file from  into Bronze (append, raw lineage) and
# Silver (typed, deduplicated, upserted) Delta tables in this Lakehouse.
# 
# Designed to be called once per file by the  pipeline, with
#  injected as a pipeline parameter — but can also be run interactively by
# setting  manually in the cell below.

# PARAMETERS CELL ********************

# Parameters cell — mark this cell as a "Parameters" cell (Edit > Toggle parameter cell)
# so the pipeline Notebook activity can override file_path at runtime.
file_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/5846138b-520e-429b-8e30-7d9a17223730/Files/raw"          # full path to ONE backup json file, injected by the pipeline
lakehouse_name = "p90x_workout_lh"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, LongType, StringType, BooleanType, DoubleType
)
from delta.tables import DeltaTable
import json

if not file_path:
    raise ValueError("file_path parameter is required (path to a single p90x backup json file)")

print(f"Ingesting backup file: {file_path}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 1. Load raw JSON
# The backup file is a single JSON document (not JSON-lines), with four arrays:
# , , , . Spark's JSON reader
# expects one JSON object/array per line by default, so we read the whole file with
# Python first, then parallelize each collection separately. This also lets us tag every
# row with source-file lineage before anything hits Delta.

# CELL ********************

raw_text = spark.read.text(file_path, wholetext=True).collect()[0][0]
backup = json.loads(raw_text)

schema_version = backup.get("schemaVersion")
exported_at_millis = backup.get("exportedAtEpochMillis")
source_file_name = file_path.split("/")[-1]

print(f"schemaVersion={schema_version}, exportedAtEpochMillis={exported_at_millis}")
print({k: len(v) for k, v in backup.items() if isinstance(v, list)})

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 2. Bronze layer
# Land each collection as-is (flattened to columns, types coerced) plus lineage columns.
# Bronze is append-friendly and kept close to the source shape — no business logic here.

# CELL ********************

ingest_ts = F.current_timestamp()

def add_lineage(df):
    return (
        df.withColumn("_source_file", F.lit(source_file_name))
          .withColumn("_schema_version", F.lit(schema_version))
          .withColumn("_exported_at_epoch_millis", F.lit(exported_at_millis))
          .withColumn("_ingested_at", ingest_ts)
    )

runs_schema = StructType([
    StructField("id", LongType()),
    StructField("variant", StringType()),
    StructField("createdAtEpochMillis", LongType()),
    StructField("isActive", BooleanType()),
])

queue_entries_schema = StructType([
    StructField("id", LongType()),
    StructField("runId", LongType()),
    StructField("sequenceIndex", LongType()),
    StructField("blockLabel", StringType()),
    StructField("dayLabel", StringType()),
    StructField("displayTitle", StringType()),
    StructField("mainWorkout", StringType()),
    StructField("accessoryWorkout", StringType()),
    StructField("amWorkout", StringType()),
    StructField("pmWorkout", StringType()),
    StructField("restOption", StringType()),
    StructField("isCompleted", BooleanType()),
    StructField("completedAtEpochMillis", LongType()),
    StructField("chosenRecoveryOption", StringType()),
])

workout_sessions_schema = StructType([
    StructField("id", LongType()),
    StructField("runId", LongType()),
    StructField("queueEntryId", LongType()),
    StructField("completedAtEpochMillis", LongType()),
    StructField("notes", StringType()),
    StructField("difficulty", LongType()),
    StructField("recoveryDaysSincePrevious", LongType()),
])

exercise_records_schema = StructType([
    StructField("id", LongType()),
    StructField("sessionId", LongType()),
    StructField("workoutPart", StringType()),
    StructField("exerciseName", StringType()),
    StructField("trackingType", StringType()),
    StructField("setNumber", LongType()),
    StructField("reps", LongType()),
    StructField("seconds", LongType()),
    StructField("weight", DoubleType()),
    StructField("bandColor", StringType()),
    StructField("notes", StringType()),
])

bronze_runs_df = add_lineage(
    spark.createDataFrame(backup.get("runs", []), schema=runs_schema)
)
bronze_queue_entries_df = add_lineage(
    spark.createDataFrame(backup.get("queueEntries", []), schema=queue_entries_schema)
)
bronze_workout_sessions_df = add_lineage(
    spark.createDataFrame(backup.get("workoutSessions", []), schema=workout_sessions_schema)
)
bronze_exercise_records_df = add_lineage(
    spark.createDataFrame(backup.get("exerciseRecords", []), schema=exercise_records_schema)
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Write Bronze as append-only history (every ingestion run adds rows, even if file is
# reprocessed — Bronze is the immutable raw log; dedup happens in Silver).
bronze_runs_df.write.format("delta").mode("append").saveAsTable("bronze_runs")
bronze_queue_entries_df.write.format("delta").mode("append").saveAsTable("bronze_queue_entries")
bronze_workout_sessions_df.write.format("delta").mode("append").saveAsTable("bronze_workout_sessions")
bronze_exercise_records_df.write.format("delta").mode("append").saveAsTable("bronze_exercise_records")

print("Bronze load complete.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 3. Silver layer
# Typed, deduplicated, business-ready tables:
# -  — one row per P90X program run-through
# -  — the full scheduled plan (91 days), with  derived
#   and timestamps converted
# -  — actual logged/completed sessions
# -  — exercise/set-level detail
# 
# Natural keys (uid=0(root) gid=0(root) groups=0(root) columns from the source app) are stable across exports, so we use
#  to upsert — safe to rerun the same or an updated backup file without creating
# duplicates.

# CELL ********************

silver_runs_df = (
    bronze_runs_df
    .withColumn("created_at", (F.col("createdAtEpochMillis") / 1000).cast("timestamp"))
    .select(
        F.col("id").alias("run_id"),
        F.col("variant"),
        "created_at",
        F.col("isActive").alias("is_active"),
        "_source_file", "_ingested_at",
    )
)

silver_queue_entries_df = (
    bronze_queue_entries_df
    .withColumn("completed_at", (F.col("completedAtEpochMillis") / 1000).cast("timestamp"))
    .withColumn("is_rest_day", F.col("restOption").isNotNull())
    .select(
        F.col("id").alias("queue_entry_id"),
        F.col("runId").alias("run_id"),
        F.col("sequenceIndex").alias("sequence_index"),
        F.col("blockLabel").alias("block_label"),
        F.col("dayLabel").alias("day_label"),
        F.col("displayTitle").alias("display_title"),
        F.col("mainWorkout").alias("main_workout"),
        F.col("accessoryWorkout").alias("accessory_workout"),
        F.col("amWorkout").alias("am_workout"),
        F.col("pmWorkout").alias("pm_workout"),
        F.col("restOption").alias("rest_option"),
        "is_rest_day",
        F.col("isCompleted").alias("is_completed"),
        "completed_at",
        F.col("chosenRecoveryOption").alias("chosen_recovery_option"),
        "_source_file", "_ingested_at",
    )
)

silver_workout_sessions_df = (
    bronze_workout_sessions_df
    .withColumn("completed_at", (F.col("completedAtEpochMillis") / 1000).cast("timestamp"))
    .select(
        F.col("id").alias("session_id"),
        F.col("runId").alias("run_id"),
        F.col("queueEntryId").alias("queue_entry_id"),
        "completed_at",
        F.col("notes"),
        F.col("difficulty"),
        F.col("recoveryDaysSincePrevious").alias("recovery_days_since_previous"),
        "_source_file", "_ingested_at",
    )
)

silver_exercise_records_df = (
    bronze_exercise_records_df
    .select(
        F.col("id").alias("exercise_record_id"),
        F.col("sessionId").alias("session_id"),
        F.col("workoutPart").alias("workout_part"),
        F.col("exerciseName").alias("exercise_name"),
        F.col("trackingType").alias("tracking_type"),
        F.col("setNumber").alias("set_number"),
        F.col("reps"),
        F.col("seconds"),
        F.col("weight"),
        F.col("bandColor").alias("band_color"),
        F.col("notes"),
        "_source_file", "_ingested_at",
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def upsert(df, table_name, key_col):
    """MERGE df into table_name on key_col. Creates the table on first run."""
    if not spark.catalog.tableExists(table_name):
        df.write.format("delta").mode("overwrite").saveAsTable(table_name)
        print(f"Created {table_name} ({df.count()} rows)")
        return

    delta_tbl = DeltaTable.forName(spark, table_name)
    (
        delta_tbl.alias("t")
        .merge(df.alias("s"), f"t.{key_col} = s.{key_col}")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    print(f"Upserted into {table_name}")


upsert(silver_runs_df, "silver_runs", "run_id")
upsert(silver_queue_entries_df, "silver_queue_entries", "queue_entry_id")
upsert(silver_workout_sessions_df, "silver_workout_sessions", "session_id")
upsert(silver_exercise_records_df, "silver_exercise_records", "exercise_record_id")

print("Silver load complete.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 4. Sanity checks
# Quick row counts + a join smoke-test so a bad ingestion fails loudly in the pipeline
# rather than silently producing an empty/partial table.

# CELL ********************

counts = {
    "silver_runs": spark.table("silver_runs").count(),
    "silver_queue_entries": spark.table("silver_queue_entries").count(),
    "silver_workout_sessions": spark.table("silver_workout_sessions").count(),
    "silver_exercise_records": spark.table("silver_exercise_records").count(),
}
print(counts)

orphaned_sessions = (
    spark.table("silver_workout_sessions").alias("s")
    .join(spark.table("silver_queue_entries").alias("q"), "queue_entry_id", "left_anti")
    .count()
)
orphaned_records = (
    spark.table("silver_exercise_records").alias("r")
    .join(spark.table("silver_workout_sessions").alias("s"), "session_id", "left_anti")
    .count()
)

print(f"orphaned_sessions (no matching queue_entry): {orphaned_sessions}")
print(f"orphaned_records (no matching session): {orphaned_records}")

if counts["silver_runs"] == 0:
    raise ValueError("Sanity check failed: silver_runs is empty after load.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Last cell: return a value to the pipeline (notebookutils)
result_summary = {
    "source_file": source_file_name,
    "row_counts": counts,
    "orphaned_sessions": orphaned_sessions,
    "orphaned_records": orphaned_records,
}

notebookutils.notebook.exit(json.dumps(result_summary))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
One-time bootstrap script — run this once (as a notebook cell, or temporarily
paste into the ingestion notebook and execute) before the pipeline's first run.
 
Creates the control table the pipeline uses to track which backup files have
already been processed, so re-running the pipeline never reprocesses the same
file twice (Bronze would just grow unnecessarily; Silver MERGE is safe either
way, but there's no reason to do the extra work).
"""
 
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
 
schema = StructType([
    StructField("source_file", StringType()),
    StructField("processed_at", TimestampType()),
])
 
spark.createDataFrame([], schema).write.format("delta").mode("overwrite") \
    .saveAsTable("control_processed_files")
 
print("control_processed_files table created.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql 
# MAGIC INSERT INTO control_processed_files VALUES ('<file_name>', current_timestamp())

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
