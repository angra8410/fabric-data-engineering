# Code Review & Learning Log: Exercise 2.2 (Fabric Medallion Architecture: Bronze $\rightarrow$ Silver $\rightarrow$ Gold)

- **Date:** 2026-09-17
- **Topic:** Medallion Architecture, Lossless Bronze Ingestion, Deduplication (`dropDuplicates`), Deterministic Surrogate Keys (`xxhash64`), Silver Cleansing, and Gold Business Aggregations for Power BI
- **Domain:** Credit Union / Financial Loan Portfolio Analytics (`df_landing_tx` $\rightarrow$ `df_bronze_tx` $\rightarrow$ `df_silver_tx` $\rightarrow$ `df_gold_branch_daily_summary`)
- **Module:** Módulo 2: Fabric Lakehouse & PySpark Engineering

---

## 1. Business Requirement & Challenge Prompt

### 📋 Challenge 2.2 Context & Business Problem
In the Credit Union, the Core Banking platform emits daily transaction batches into the Lakehouse Landing Zone. Previously, analysts attempted to consume these raw landing files directly in Power BI, introducing three major failure modes:
1. **Pipeline Retries & Duplicate Transactions:** Transient network failures trigger automated ingestion retries, dumping identical transaction IDs (`TX1001`) into landing files and skewing loan balance reporting.
2. **Surrogate Key Fragmentation in Distributed Systems:** Traditional data warehouse sequence generators (`IDENTITY` / `AUTO_INCREMENT`) require centralized synchronization locks, causing massive performance degradation in distributed Spark engines. The modern Lakehouse pattern requires **deterministic surrogate keys via hashing (`xxhash64`)**.
3. **Absence of Audit Lineage:** No record existed of ingestion timestamps or the physical source file from which records originated.

Your objective as Data Engineer is to construct an end-to-end **Medallion Architecture pipeline** (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) in Microsoft Fabric using PySpark and Delta Lake standards.

---

## 2. Input Mock Dataset (Bronze Landing Zone)

Run this cell in your Fabric Notebook (`lh_practice_smash_interview`) to simulate the dirty landing batch:

```python
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType

# Simulating raw landing feed arriving from Core Banking
raw_transactions_data = [
    # (tx_id, loan_id, member_id, branch_id, tx_date, tx_type, tx_amount, source_file)
    ("TX1001", "L-901", "M101", "BR-01", "2023-06-01", "PAYMENT", "450.00", "core_batch_20230601.csv"),
    ("TX1002", "L-902", "M102", "BR-02", "2023-06-01", "DISBURSEMENT", "15000.00", "core_batch_20230601.csv"),
    ("TX1003", "L-903", "M103", "BR-01", "2023-06-01", "payment", "320.50", "core_batch_20230601.csv"),
    # EXACT DUPLICATE of TX1001 caused by pipeline retry:
    ("TX1001", "L-901", "M101", "BR-01", "2023-06-01", "PAYMENT", "450.00", "core_batch_20230601_retry.csv"),
    # Invalid transaction with negative fee / corrupt amount:
    ("TX1004", "L-904", "M105", "BR-03", "2023-06-01", "FEE", "-25.00", "core_batch_20230601.csv"),
    # Corrupt transaction with blank type:
    ("TX1005", "L-905", "M101", "BR-01", "2023-06-01", "  ", "100.00", "core_batch_20230601.csv"),
]

raw_tx_schema = StructType([
    StructField("raw_tx_id", StringType(), True),
    StructField("raw_loan_id", StringType(), True),
    StructField("raw_member_id", StringType(), True),
    StructField("raw_branch_id", StringType(), True),
    StructField("raw_tx_date", StringType(), True),
    StructField("raw_tx_type", StringType(), True),
    StructField("raw_tx_amount", StringType(), True),
    StructField("_source_file", StringType(), True)
])

df_landing_tx = spark.createDataFrame(data=raw_transactions_data, schema=raw_tx_schema)
display(df_landing_tx)
```

---

## 3. Acceptance Criteria & Technical Requirements

```
[ Landing Zone / Files ]
         │
         ▼
 🥉 BRONZE LAYER (Raw & Lossless)
    • Retain all incoming raw columns without destructive casting.
    • Add operational audit metadata: `_ingestion_timestamp`.
         │
         ▼
 🥈 SILVER LAYER (Cleansed, Deduplicated & Conformed)
    • Deduplicate on business key: `.dropDuplicates(["raw_tx_id"])`.
    • Text hygiene: normalize `tx_type` with `F.upper(F.trim(...))`.
    • Type casting: `tx_amount` to Double/Decimal, `tx_date` to Date.
    • Quality validation: filter out `tx_amount <= 0` and empty/null `tx_type`.
    • Distributed Surrogate Keys: generate `loan_sk` and `member_sk` using `F.xxhash64()`.
    • Explicit projection with standardized enterprise column names.
         │
         ▼
 🥇 GOLD LAYER (Business Aggregates / Data Mart for Power BI)
    • Group by `branch_id`, `tx_date`, `tx_type`.
    • Compute `total_transaction_amount` (rounded to 2 decimals) and `transaction_count`.
```

---

## 4. Production Master Implementation

### 🥉 Step 1: Bronze Layer (Raw Append-Only + Audit Metadata)
```python
df_bronze_tx = (
    df_landing_tx
    .withColumn("_ingestion_timestamp", F.current_timestamp())
)
display(df_bronze_tx)
```

### 🥈 Step 2: Silver Layer (Cleansed, Deduplicated & Surrogate Hashing)
```python
df_silver_tx = (
    df_bronze_tx
    # 1. Deduplicate by business key
    .dropDuplicates(["raw_tx_id"])
    
    # 2. Text Hygiene
    .withColumn("tx_type", F.upper(F.trim(F.col("raw_tx_type"))))
    
    # 3. Safe Type Casting
    .withColumn("tx_amount", F.col("raw_tx_amount").cast(DoubleType()))
    .withColumn("tx_date", F.to_date(F.col("raw_tx_date"), "yyyy-MM-dd"))
    
    # 4. Data Quality Quarantine / Filter
    .filter(
        (F.col("tx_amount") > 0) & 
        (F.nullif(F.col("tx_type"), F.lit("")).isNotNull())
    )
    
    # 5. Distributed Deterministic Surrogate Keys (xxhash64)
    .withColumn("loan_sk", F.xxhash64(F.col("raw_loan_id")))
    .withColumn("member_sk", F.xxhash64(F.col("raw_member_id")))
    
    # 6. Explicit Silver Projection
    .select(
        F.col("raw_tx_id").alias("transaction_id"),
        "loan_sk",
        "member_sk",
        F.col("raw_branch_id").alias("branch_id"),
        "tx_date",
        "tx_type",
        "tx_amount",
        "_source_file",
        "_ingestion_timestamp"
    )
)
display(df_silver_tx)
```

### 🥇 Step 3: Gold Layer (Executive Business Aggregation for Power BI)
```python
df_gold_branch_daily_summary = (
    df_silver_tx
    .groupBy("branch_id", "tx_date", "tx_type")
    .agg(
        F.round(F.sum("tx_amount"), 2).alias("total_transaction_amount"),
        F.count("transaction_id").alias("transaction_count")
    )
    .orderBy("branch_id", "tx_date", "tx_type")
)
display(df_gold_branch_daily_summary)
```

---

## 5. Architectural Deep Dive & Senior Interview Takeaways

### 💡 1. Why `F.xxhash64()` Instead of Auto-Incrementing IDs?
- **The MPP Problem:** Traditional SQL databases generate keys sequentially (`1, 2, 3...`) using a central transaction log lock. In Spark/Fabric, executors run across distributed nodes. Asking nodes to synchronize sequential IDs causes massive serialization bottlenecks.
- **`monotonically_increasing_id()` Trap:** Generates unique 64-bit integers, but they are **non-deterministic** across pipeline runs (the same member ID could receive a different surrogate key tomorrow if partitions shift).
- **The `xxhash64()` Solution:** 
  - Produces an ultra-fast 64-bit hash.
  - Fully **deterministic**: `F.xxhash64("M101")` will produce the exact same integer every time, anywhere across the cluster, without requiring cross-partition locks or lookup dimension joins.

### 💡 2. The Bronze Lossless Principle
- Never apply business filters or lossy casts in Bronze. If a downstream logic bug is found in Silver or Gold, the Bronze table serves as the immutable single source of truth allowing full historical reprocessing without requesting re-extracts from source systems.

### 💡 3. Development vs. Production Architecture
- **Interactive Dev:** A single notebook with Bronze $\rightarrow$ Silver $\rightarrow$ Gold cells enables rapid testing and full lineage visibility.
- **Enterprise Prod:** Decouple into 3 distinct notebooks (`nb_ingest_bronze`, `nb_transform_silver`, `nb_aggregate_gold`) triggered sequentially by a **Microsoft Fabric Data Pipeline** to ensure failure isolation, independent scheduling, and optimal resource allocation.
