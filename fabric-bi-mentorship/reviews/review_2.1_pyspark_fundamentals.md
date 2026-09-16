# Code Review & Learning Log: Exercise 2.1 (PySpark Fundamentals & Safe Data Cleansing)

- **Date:** 2026-09-16
- **Topic:** PySpark DataFrames, Schemas (`StructType`), Safe Casts, Conditional Logic (`F.when`), String Sanitization & Audit Metadata
- **Domain:** Credit Union / Financial Loan Portfolio Analytics (`raw_members` $\rightarrow$ `silver_members_cleaned`)
- **Module:** Módulo 2: Fabric Lakehouse & PySpark Engineering

---

## 1. Business Requirement & Challenge Prompt

### 📋 Challenge 2.1 Context & Business Problem
The Credit Union is migrating its member onboarding pipeline to **Microsoft Fabric Lakehouse**. 
Daily member registration batches arrive at the **Bronze** storage layer as raw, semi-structured records with several real-world data quality defects:
1. Inconsistent capitalization and surrounding whitespace in member names and emails.
2. Missing or blank emails that need fallback governance.
3. String-based numeric fields with dirty values (`"invalid_score"`, `"corrupt"`, `"NaN"`) that would crash naive ETL jobs if parsed without safeguards.
4. Non-standardized member status codes (`"active"`, `"INACTIVE"`, `"Suspended"`).

Your objective as Data Engineer is to write a **clean, modular, and production-grade PySpark transformation pipeline** that cleanses and standardizes this raw batch before downstream Silver ingestion.

---

### 🛠️ Input Mock Dataset (Run this in your Fabric Notebook / Local Spark Session)

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

# Initialize Spark if running locally; in Fabric Notebooks 'spark' is already active
spark = SparkSession.builder.appName("Module2_Exercise_2.1").getOrCreate()

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
```

---

### 🎯 Acceptance Criteria & Technical Requirements

1. **Schema Integrity & Explicit Data Types:**
   - Define and apply transformations ensuring the final output adheres to clean typed columns (`IntegerType` for scores, `DoubleType` for ratios, `TimestampType` for ingestion timestamps).
2. **Text Normalization & Hygiene:**
   - `full_name`: Trim surrounding whitespaces and apply Title Case / Initcap formatting (`"   robert T. kiYOSAKI  "` $\rightarrow$ `"Robert T. Kiyosaki"`).
   - `email`: Trim spaces, convert to lowercase. If email is `NULL` or empty (`""`), substitute with `'not_provided@creditunion.org'`.
   - `status`: Trim spaces and convert to uppercase (`"ACTIVE"`).
3. **Safe Numeric Parsing & Quality Handling:**
   - `credit_score`: Cast `raw_credit_score` safely to `int`. Any non-numeric string (e.g. `"invalid_score"`) must safely evaluate to `NULL` without throwing a runtime exception.
   - `debt_to_income_ratio`: Cast `raw_dti` safely to `double`.
4. **Credit Policy Risk Flag (`is_valid_credit_profile`):**
   - Create a boolean column `is_valid_credit_profile`:
     - `True` if `credit_score >= 600` AND `debt_to_income_ratio <= 0.43`.
     - `False` otherwise (including cases where either value is `NULL`).
5. **Operational Audit Column:**
   - Add `_ingestion_timestamp` using Spark's `F.current_timestamp()`.
6. **Filtering for Active Portfolio:**
   - Filter the resulting dataset so only members with `status == "ACTIVE"` are included in the final output.
7. **Projection & Readability:**
   - Final projection must include:
     - `member_id`
     - `full_name`
     - `ssn`
     - `email`
     - `credit_score`
     - `debt_to_income_ratio`
     - `status`
     - `joined_date`
     - `is_valid_credit_profile`
     - `_ingestion_timestamp`
   - Use clean modular expressions or chained DataFrame operations avoiding Python UDFs.

---

## 2. Candidate Submission & Progress Log

### Phase 1 Submission: Text Sanitization & Email Fallback
```python
# Candidate tested and validated in Microsoft Fabric Notebook:
df_with_email = df_raw_members.withColumn(
    "email",
    # If empty string, turn into NULL; then coalesce with the fallback
    F.coalesce(
        F.nullif(F.lower(F.trim(F.col("email"))), F.lit("")), 
        F.lit("not_provided@creditunion.org")
    )
)
```

---

## 3. Senior PR Review Analysis & Study Notes

### 🧠 Core Mental Model 1: The "Onion Principle" (Inside-Out Functional Composition)
When transforming data in declarative engines (SQL & PySpark), avoid procedural `if/else` loops. Think of data moving through concentric layers from the center outward:

```text
Layer 4: [ GOVERNANCE ] Fallback/Default value -> F.coalesce( ..., F.lit("fallback") )
  Layer 3: [ MISSINGNESS ] Convert blank ghost values to NULL -> F.nullif( ..., F.lit("") )
    Layer 2: [ HYGIENE ] Strip whitespace & normalize casing -> F.lower( F.trim( ... ) )
      Layer 1: [ RAW SIGNAL ] The source column -> F.col("email")
```

- **Unify Missingness into Canonical `NULL`:** Real-world data disguises missing values as `None`, `""`, `"   "`, `"N/A"`. By stripping whitespace and using `F.nullif(..., F.lit(""))`, empty strings become standard `NULL`s.
- **Single Coalesce Resolution:** Once missingness is standardized to `NULL`, a single `F.coalesce()` cleanly handles both genuine `NULL`s and previously blank strings.

---

### 🧱 Core Mental Model 2: DataFrame Immutability & Method Chaining
- **DataFrames are 100% Immutable:** Every `.withColumn()`, `.filter()`, or `.select()` produces a **new** DataFrame. Spark never modifies data in place.
- **The Notebook Trap:** Running `df.withColumn("colA", ...)` in Cell 1 and `df.withColumn("colB", ...)` in Cell 2 starting from `df_raw` creates two separate branches. Cell 2 will not see the changes from Cell 1.
- **Production Method Chaining:** Group transformations in a single fluent chain wrapped in parentheses `( ... )`:

```python
df_cleaned_text = (
    df_raw_members
    .withColumn("full_name", F.initcap(F.trim(F.col("full_name"))))
    .withColumn("status", F.upper(F.trim(F.col("status"))))
    .withColumn(
        "email",
        F.coalesce(
            F.nullif(F.lower(F.trim(F.col("email"))), F.lit("")),
            F.lit("not_provided@creditunion.org")
        )
    )
)
```

---

### 📜 Core Mental Model 3: Explicit Schemas (`StructType`) as Data Contracts
In PySpark:
```python
raw_schema = StructType([
    StructField("member_id", StringType(), False),
    StructField("full_name", StringType(), True),
    ...
])
```
is the programmatic equivalent of SQL DDL (`CREATE TABLE raw_members (...)`).
- **3 Parameters:** `StructField(name, dataType, nullable)`
  - `False` = `NOT NULL`
  - `True` = `NULL` allowed
- **Architectural Value:**
  1. **Performance:** Eliminates double-reading and expensive schema inference passes over storage.
  2. **Data Governance:** Prevents silent corruption (e.g. leading zeros in IDs/Zip Codes being dropped if auto-inferred as integers).
  3. **Data Contract:** Enforces schema boundary at Bronze ingestion.

---

### ⚠️ Common Syntax Gotchas & Traps Identified
1. **PySpark vs. Pandas Naming:**
   - PySpark Column methods use camelCase: `.isNull()` (with capital **N**), **not** `.isnull()`.
2. **`F.col()` vs. `F.lit()`:**
   - `F.col("name")` refers to a column in the DataFrame.
   - `F.lit("constant")` injects a literal scalar value into Catalyst. Hardcoded values (e.g. `""`, `"fallback"`) must be wrapped in `F.lit()`.
3. **Operator Precedence in Conditions:**
   - Bitwise `&` (AND) and `|` (OR) have higher precedence than comparison operators in Python.
   - **Always** wrap each sub-condition in parentheses: `(F.col("a") >= 10) & (F.col("b") <= 20)`.

---

## 4. Next Step: Completing Exercise 2.1 Full Pipeline Reference

*(To be finalized with numeric safe casting, boolean risk flag `is_valid_credit_profile`, and `_ingestion_timestamp`)*

