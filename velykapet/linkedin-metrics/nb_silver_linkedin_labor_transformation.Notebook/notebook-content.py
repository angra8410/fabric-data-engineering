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

spark.catalog.clearCache()
bronze_tables = ["discovery", "engagement", "top_posts", "followers", "demographics"]
silver_prefix = "silver_"

for t in bronze_tables:
    try:
        spark.catalog.refreshTable(t)
    except Exception as e:
        print(f"Refresh warning for {t}: {e}")

spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

def clean_pct(val):
    if pd.isnull(val):
        return 0.0
    val_str = str(val).replace("%", "").replace("<", "").strip()
    try:
        return float(val_str) / 100.0
    except:
        return 0.0

for table in bronze_tables:
    print(f"\nProcessing Bronze Table: {table}...")

    df_bronze = spark.read.table(table)
    pdf = df_bronze.toPandas()

    if table == "discovery":
        print(f"  -> Detected Discovery (summary, pre-pivoted) layout for: {table}")
        # Bronze already stores one row per (start_date, end_date) with metric columns.
        numeric_cols = [c for c in pdf.columns if c not in ("start_date", "end_date")]
        for col in numeric_cols:
            pdf[col] = pd.to_numeric(pdf[col], errors='coerce').fillna(0).astype('int64')
        final_df = spark.createDataFrame(pdf)

    elif table == "demographics":
        print(f"  -> Detected Demographics layout for: {table}")
        if "percentage" in pdf.columns:
            pdf["percentage"] = pdf["percentage"].apply(clean_pct)
        # start_date/end_date already populated by bronze ingestion
        final_df = spark.createDataFrame(pdf)

    else:
        print(f"  -> Detected Standard/List layout for: {table}")

        date_col = "post_publish_date" if "post_publish_date" in df_bronze.columns else ("date" if "date" in df_bronze.columns else "start_date")

        if date_col not in df_bronze.columns:
            print(f"Columns found in {table}: {df_bronze.columns}")
            raise ValueError(f"Could not find date column in table: {table}")

        cleaned_df = df_bronze.withColumn(date_col, F.to_date(F.col(date_col)))
        numeric_cols = [c for c, t in cleaned_df.dtypes if t in ["int", "double", "bigint", "long"]]
        cleaned_df = cleaned_df.fillna(0, subset=numeric_cols)

        # Deduplicate (Keep one row per unique post_url, or per date)
        dedup_key = "post_url" if table == "top_posts" else date_col
        final_df = cleaned_df.dropDuplicates([dedup_key])

    if table == "engagement":
        required_cols = ["reactions", "comments", "shares", "clicks", "impressions"]
        if all(col in final_df.columns for col in required_cols):
            final_df = final_df.withColumn(
                "engagement_rate",
                F.when(F.col("impressions") > 0,
                       (F.col("reactions") + F.col("comments") + F.col("shares") + F.col("clicks")) / F.col("impressions")
                      ).otherwise(0.0)
            )

    final_silver_df = final_df.withColumn("silver_load_timestamp", F.current_timestamp())

    silver_table_name = f"{silver_prefix}{table}"
    (final_silver_df.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .saveAsTable(silver_table_name))

    print(f"Successfully created Silver table: {silver_table_name}")
    display(final_silver_df.limit(5))

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

# 1. Clear Spark's catalog cache and refresh tables
spark.catalog.clearCache()
bronze_tables = ["discovery", "engagement", "top_posts", "followers", "demographics"]
silver_prefix = "silver_"

for t in bronze_tables:
    try:
        spark.catalog.refreshTable(t)
    except Exception as e:
        print(f"Refresh warning for {t}: {e}")

spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# File path to parse date metadata
file_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/e7bac705-a51a-4a6d-a8c4-e81b7cdeef2a/Files/raw_data"

# Parse start/end dates from the filename
file_dates = re.findall(r'\d{4}-\d{2}-\d{2}', file_path)
file_start_date = datetime.strptime(file_dates[0], "%Y-%m-%d").date() if len(file_dates) >= 2 else None
file_end_date = datetime.strptime(file_dates[1], "%Y-%m-%d").date() if len(file_dates) >= 2 else None

# Helper to clean demographics percentages (e.g. '2%', '< 1%')
def clean_pct(val):
    if pd.isnull(val):
        return 0.0
    val_str = str(val).replace("%", "").replace("<", "").strip()
    try:
        return float(val_str) / 100.0
    except:
        return 0.0

for table in bronze_tables:
    print(f"\nProcessing Bronze Table: {table}...")
    
    df_bronze = spark.read.table(table)
    pdf = df_bronze.toPandas()
    
    # --- DETECT TABLE TYPE ---
    is_summary_card = False
    date_range_col = None
    
    for col in pdf.columns:
        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', col.replace("_", " ")):
            date_range_col = col
            is_summary_card = True
            break
            
    if is_summary_card and len(pdf.columns) == 2:
        print(f"  -> Detected Summary Card layout for: {table}")
        
        # 1. Extract dates from header
        dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', date_range_col.replace("_", " "))
        start_date = datetime.strptime(dates[0], "%m/%d/%Y").date() if len(dates) >= 2 else file_start_date
        end_date = datetime.strptime(dates[1], "%m/%d/%Y").date() if len(dates) >= 2 else file_end_date
        
        # 2. Pivot rows to columns
        metric_col = [c for c in pdf.columns if c != date_range_col][0]
        pdf_pivoted = pdf.set_index(metric_col).T.reset_index(drop=True)
        pdf_pivoted.columns = [str(c).strip().replace(" ", "_").replace("(", "").replace(")", "").lower() for c in pdf_pivoted.columns]
        
        # 3. Add dates and cast values
        pdf_pivoted["start_date"] = start_date
        pdf_pivoted["end_date"] = end_date
        for col in pdf_pivoted.columns:
            if col not in ["start_date", "end_date"]:
                pdf_pivoted[col] = pd.to_numeric(pdf_pivoted[col], errors='coerce').fillna(0).astype('int64')
        
        final_df = spark.createDataFrame(pdf_pivoted)
        
    elif table == "demographics":
        print(f"  -> Detected Demographics layout for: {table}")
        # Clean percentage column and add start/end dates parsed from file
        if "percentage" in pdf.columns:
            pdf["percentage"] = pdf["percentage"].apply(clean_pct)
        pdf["start_date"] = file_start_date
        pdf["end_date"] = file_end_date
        
        final_df = spark.createDataFrame(pdf)
        
    else:
        print(f"  -> Detected Standard/List layout for: {table}")
        
        # Determine the date column dynamically
        date_col = "post_publish_date" if "post_publish_date" in df_bronze.columns else ("date" if "date" in df_bronze.columns else "start_date")
        
        if date_col not in df_bronze.columns:
            print(f"Columns found in {table}: {df_bronze.columns}")
            raise ValueError(f"Could not find date column in table: {table}")
            
        # Cast date and clean null metrics
        cleaned_df = df_bronze.withColumn(date_col, F.to_date(F.col(date_col)))
        numeric_cols = [c for c, t in cleaned_df.dtypes if t in ["int", "double", "bigint", "long"]]
        cleaned_df = cleaned_df.fillna(0, subset=numeric_cols)
        
        # Deduplicate (Keep latest entry per unique post url or date)
        dedup_key = "post_url" if table == "top_posts" else date_col
        final_df = cleaned_df.dropDuplicates([dedup_key])
        
    # --- ENRICHMENT ---
    if table == "engagement":
        required_cols = ["reactions", "comments", "shares", "clicks", "impressions"]
        if all(col in final_df.columns for col in required_cols):
            final_df = final_df.withColumn(
                "engagement_rate",
                F.when(F.col("impressions") > 0, 
                       (F.col("reactions") + F.col("comments") + F.col("shares") + F.col("clicks")) / F.col("impressions")
                      ).otherwise(0.0)
            )
            
    # Add Silver load timestamp
    final_silver_df = final_df.withColumn("silver_load_timestamp", F.current_timestamp())
    
    # Save to Silver Table
    silver_table_name = f"{silver_prefix}{table}"
    (final_silver_df.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .saveAsTable(silver_table_name))
     
    print(f"Successfully created Silver table: {silver_table_name}")
    display(final_silver_df.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

for table in ["silver_discovery", "silver_engagement", "silver_top_posts", "silver_followers", "silver_demographics"]:
    count = spark.read.table(table).count()
    print(f"Table: {table:<25} | Total Rows: {count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

content_bronze_tables = ["post_content", "post_hashtags"]
for t in content_bronze_tables:
    try:
        spark.catalog.refreshTable(t)
    except Exception as e:
        print(f"Refresh warning for {t}: {e}")

df_content_silver = (spark.read.table("post_content")
    .withColumn("posted_at", F.to_timestamp("posted_at"))
    .dropDuplicates(["post_id"])
    .withColumn("silver_load_timestamp", F.current_timestamp()))
(df_content_silver.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true").saveAsTable("silver_post_content"))
print("Successfully created Silver table: silver_post_content")

df_hashtags_silver = (spark.read.table("post_hashtags")
    .dropDuplicates(["post_id", "hashtag"])
    .withColumn("silver_load_timestamp", F.current_timestamp()))
(df_hashtags_silver.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true").saveAsTable("silver_post_hashtags"))
print("Successfully created Silver table: silver_post_hashtags")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

spark.sql("DESCRIBE silver_post_content").filter("col_name = 'linkedin_post_id'").show()

# check for potential precision collisions
spark.read.table("silver_post_content") \
    .groupBy(F.col("linkedin_post_id").cast("decimal(38,0)").cast("string")) \
    .count() \
    .filter("count > 1") \
    .show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

spark.read.table("silver_post_content") \
    .filter(F.col("linkedin_post_id").cast("decimal(38,0)").isNull()) \
    .select("post_id", "linkedin_post_id", "notes") \
    .show(20, truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
