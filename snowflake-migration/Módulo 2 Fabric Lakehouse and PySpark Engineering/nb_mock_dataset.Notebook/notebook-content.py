# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "86204f05-6d46-4c76-a76d-9cb8a5fa5cb6",
# META       "default_lakehouse_name": "lh_practice_smash_interview",
# META       "default_lakehouse_workspace_id": "cfeefa92-730d-43b2-b2b1-9c46826d5807",
# META       "known_lakehouses": [
# META         {
# META           "id": "86204f05-6d46-4c76-a76d-9cb8a5fa5cb6"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

raw_data = [
    ("M101", "   robert T. kiYOSAKI  ", "987-65-4321", "Robert@RichDad.COM", "740", "0.25", "active", "2023-01-15"),
    ("M102", "alice cooper   ", "123-45-6789", None, "invalid_score", "0.38", "ACTIVE", "2023-02-20"),
    ("M103", "  ELIZABETH bennet", "456-78-1234", "lizzie@pemberley.org", "580", "0.41", "active", "2023-03-10"),
    ("M104", "charles foster kane", None, "kane@xanadu.net", "810", "corrupt_dti", "suspended", "2023-04-05"),
    ("M105", "  david copperfield ", "333-22-1111", "  ", "620", "0.48", "Active", "2023-05-12"),
    ("M106", "Scrooge McDuck", "000-00-0001", "scrooge@vault.com", "850", "0.05", "INACTIVE", "2022-11-01"),
]

raw_schema = StructType([
    StructField("member_id", StringType(), False),
    StructField("full_name", StringType(), True),
    StructField("ssn", StringType(), True),
    StructField("email", StringType(), True),
    StructField("raw_credit_score", StringType(), True),
    StructField("raw_dti", StringType(), True),
    StructField("status", StringType(), True),
    StructField("joined_date", StringType(), True)
])

df_raw_members = spark.createDataFrame(data=raw_data, schema=raw_schema)

# 1. Check schema definition
df_raw_members.printSchema()

# 2. View the uncleaned rows
df_raw_members.show(truncate=False)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_silver_members = (
    df_raw_members
    # 1. Text Normalization & String Hygiene
    .withColumn("full_name", F.initcap(F.trim(F.col("full_name"))))
    .withColumn("status", F.upper(F.trim(F.col("status"))))
    
    # 2. Onion Principle: Empty string -> NULL, then fallback default
    .withColumn("email", F.coalesce(
        F.nullif(F.lower(F.trim(F.col("email"))), F.lit("")),
        F.lit("not_provided@creditunion.org")
    ))
    
    # 3. Safe Numeric Casting (fault-tolerant: dirty strings turn to null automatically)
    .withColumn("credit_score", F.col("raw_credit_score").cast(IntegerType()))
    .withColumn("debt_to_income_ratio", F.col("raw_dti").cast(DoubleType()))
    
    # 4. Business Policy Boolean Flag
    .withColumn(
        "is_valid_credit_profile",
        (F.col("credit_score") >= 600) & (F.col("debt_to_income_ratio") <= 0.43)
    )
    
    # 5. Operational Audit Metadata
    .withColumn("_ingestion_timestamp", F.current_timestamp())
    
    # 6. Active Portfolio Filter (discards INACTIVE and SUSPENDED)
    .filter(F.col("status") == "ACTIVE")
    
    # 7. Explicit Silver Projection (prune unneeded raw columns)
    .select(
        "member_id",
        "full_name",
        "ssn",
        "email",
        "credit_score",
        "debt_to_income_ratio",
        "status",
        "joined_date",
        "is_valid_credit_profile",
        "_ingestion_timestamp"
    )
)

# Display the transformed Silver DataFrame in Fabric's interactive viewer
display(df_silver_members)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Verify Spark physical data types
df_silver_members.printSchema()

# Inspect count (should be 4 active rows out of 6)
print(f"Total cleansed active records: {df_silver_members.count()}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

(
    df_silver_members
    .write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("silver_members")
)

print("Saved successfully to silver_members Delta table!")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT * FROM lh_practice_smash_interview.dbo.silver_members

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
