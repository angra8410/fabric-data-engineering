# 🛠️ PySpark Fundamentals Cheat-Sheet (Production & Fabric Lakehouse Edition)

A quick-reference guide for DataFrame transformations, column operations, text hygiene, safe casting, conditional expressions, and audit metadata in Microsoft Fabric notebooks.

---

## 0. Mandatory Imports & Spark Session Setup

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType, BooleanType, 
    TimestampType, DateType, LongType, DecimalType
)

# In Microsoft Fabric Notebooks, the SparkSession 'spark' is pre-initialized.
# In local development:
# spark = SparkSession.builder.appName("Fabric_Mentorship").getOrCreate()
```

---

## 1. DataFrame Structural Operations (Flow & Projections)

| Method | Syntax | Description | Example |
| :--- | :--- | :--- | :--- |
| **`.withColumn()`** | `df.withColumn(colName, colExpr)` | Adds a new column or replaces an existing one if the name matches. Returns a *new* DataFrame. | `df.withColumn("status", F.upper(F.col("status")))` |
| **`.withColumnRenamed()`** | `df.withColumnRenamed(oldName, newName)` | Renames an existing column without mutating contents. | `df.withColumnRenamed("raw_dti", "debt_to_income_ratio")` |
| **`.filter()`** / **`.where()`** | `df.filter(booleanCondition)` | Keeps only rows where condition evaluates to `True`. (`where` is an exact alias). | `df.filter(F.col("status") == "ACTIVE")` |
| **`.select()`** | `df.select(*cols_or_exprs)` | Projects a specific subset of columns or computed expressions; drops unselected columns. | `df.select("member_id", "full_name", "email")` |
| **`.drop()`** | `df.drop(*cols)` | Drops specified columns from DataFrame. | `df.drop("raw_credit_score", "raw_dti")` |
| **`.distinct()`** | `df.distinct()` | Returns unique rows across all columns. | `df.select("status").distinct()` |
| **`.dropDuplicates()`** | `df.dropDuplicates([subset])` | Deduplicates rows based on a subset of key columns. | `df.dropDuplicates(["member_id"])` |
| **`.printSchema()`** | `df.printSchema()` | Prints the schema tree (column names, types, nullability). | `df.printSchema()` |
| **`.show()`** | `df.show(n=20, truncate=False)` | Action that prints tabular rows to the console/notebook. | `df.show(5, truncate=False)` |

---

## 2. Text Normalization & Hygiene (`pyspark.sql.functions`)

| Function | Syntax | Description | Example Transformation |
| :--- | :--- | :--- | :--- |
| **`F.trim()`** | `F.trim(col)` | Strips leading and trailing whitespace. | `"  alice  "` $\rightarrow$ `"alice"` |
| **`F.lower()`** | `F.lower(col)` | Converts string to all lowercase characters. | `"Robert@RichDad.COM"` $\rightarrow$ `"robert@richdad.com"` |
| **`F.upper()`** | `F.upper(col)` | Converts string to all uppercase characters. | `"active"` $\rightarrow$ `"ACTIVE"` |
| **`F.initcap()`** | `F.initcap(col)` | Capitalizes first letter of each word (Title Case). | `"robert t. kiYOSAKI"` $\rightarrow$ `"Robert T. Kiyosaki"` |
| **`F.length()`** | `F.length(col)` | Returns string character count. | `F.length(F.col("ssn")) == 11` |
| **`F.concat_ws()`** | `F.concat_ws(sep, *cols)` | Concatenates multiple columns with separator, ignoring nulls. | `F.concat_ws(" ", F.col("first_name"), F.col("last_name"))` |
| **`F.regexp_replace()`** | `F.regexp_replace(col, pattern, replacement)` | Replaces regex matches in strings. | `F.regexp_replace(F.col("ssn"), "-", "")` |

---

## 3. Handling Missingness, NULLs, and Safe Fallbacks

| Function / Method | Syntax | Description | Best Practice Example |
| :--- | :--- | :--- | :--- |
| **`F.lit()`** | `F.lit(value)` | Injects literal scalar value into Catalyst. **Mandatory** when comparing or creating constant values. | `F.lit("not_provided@creditunion.org")` |
| **`F.nullif()`** | `F.nullif(col1, col2)` | Returns `NULL` if `col1 == col2`; else returns `col1`. Ideal for turning empty strings `""` into canonical `NULL`. | `F.nullif(F.trim(F.col("email")), F.lit(""))` |
| **`F.coalesce()`** | `F.coalesce(*cols_or_lits)` | Evaluates left-to-right and returns first non-null value. | `F.coalesce(F.col("email"), F.lit("fallback@org.com"))` |
| **`.isNull()`** | `col.isNull()` | Returns `True` if column value is `NULL`. *(Note capital **N**, unlike Pandas `isnull`)*. | `F.col("ssn").isNull()` |
| **`.isNotNull()`** | `col.isNotNull()` | Returns `True` if column value is not `NULL`. | `F.col("credit_score").isNotNull()` |
| **`F.isnan()`** | `F.isnan(col)` | Returns `True` if float/double column is NaN. | `F.isnan(F.col("debt_to_income_ratio"))` |

---

## 4. Safe Numeric Casting & Type Conversions

| Cast Type | Syntax | Behavior on Corrupt Strings (`"invalid_score"`) |
| :--- | :--- | :--- |
| **`.cast()`** | `F.col("raw_score").cast(IntegerType())`<br>`F.col("raw_score").cast("int")` | In Spark default mode: silently evaluates malformed strings to `NULL`. |
| **`F.try_cast()`** | `F.try_cast(F.col("raw_score"), IntegerType())`<br>`F.try_cast(F.col("raw_score"), "int")` | **Production Standard:** Explicitly guarantees safe conversion to `NULL` without throwing runtime exceptions, even if Spark ANSI mode is enabled. |

### Supported Type Constructors:
- `StringType()`
- `IntegerType()` (32-bit int)
- `LongType()` (64-bit int / BigInt)
- `DoubleType()` (float64, ideal for ratios/rates)
- `DecimalType(precision, scale)` (fixed precision, ideal for financial amounts e.g. `DecimalType(18, 2)`)
- `BooleanType()`
- `DateType()`
- `TimestampType()`

---

## 5. Conditional Logic (`CASE WHEN`) & Boolean Operators

### The `F.when().otherwise()` Pattern:
```python
# Equivalent to SQL: CASE WHEN condition THEN val1 ELSE val2 END
F.when(condition, value_if_true).otherwise(value_if_false)

# Chained / Multi-condition:
F.when(cond1, val1).when(cond2, val2).otherwise(default_val)
```

### Direct Boolean Column Generation:
When generating a boolean flag (`True`/`False`), you can assign the boolean expression directly without `F.when`:
```python
.withColumn(
    "is_valid_credit_profile",
    (F.col("credit_score") >= 600) & (F.col("debt_to_income_ratio") <= 0.43)
)
```

### Logical Operators and Precedence Rules:
- `&` : Logical AND
- `|` : Logical OR
- `~` : Logical NOT
- ⚠️ **Mandatory Parentheses:** Because Python bitwise operators have higher operator precedence than comparison operators (`>=`, `<=`, `==`), **always enclose each condition in parentheses**:
  ```python
  # ❌ FAILS with TypeError or incorrect precedence:
  F.col("credit_score") >= 600 & F.col("dti") <= 0.43

  # ✅ CORRECT:
  (F.col("credit_score") >= 600) & (F.col("debt_to_income_ratio") <= 0.43)
  ```

---

## 6. Audit Metadata & Date/Time Functions

| Function | Syntax | Output Data Type | Use Case |
| :--- | :--- | :--- | :--- |
| **`F.current_timestamp()`** | `F.current_timestamp()` | `TimestampType` | Ingestion timestamp metadata (`_ingestion_timestamp`). |
| **`F.current_date()`** | `F.current_date()` | `DateType` | Batch execution date. |
| **`F.to_date()`** | `F.to_date(col, format)` | `DateType` | Parses date strings: `F.to_date(F.col("joined_date"), "yyyy-MM-dd")`. |
| **`F.date_format()`** | `F.date_format(col, format)` | `StringType` | Formats date into string (`"yyyyMM"`). |

---

## 7. Master Production Pipeline Pattern (Exercise 2.1 Complete Blueprint)

```python
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType

df_silver_members = (
    df_raw_members
    # 1. Text Normalization & String Hygiene
    .withColumn("full_name", F.initcap(F.trim(F.col("full_name"))))
    .withColumn("status", F.upper(F.trim(F.col("status"))))
    
    # 2. Onion Principle: Missingness standardization + Fallback Governance
    .withColumn("email", F.coalesce(
        F.nullif(F.lower(F.trim(F.col("email"))), F.lit("")),
        F.lit("not_provided@creditunion.org")
    ))
    
    # 3. Safe Numeric Casting (fault-tolerant against corrupt strings)
    .withColumn("credit_score", F.col("raw_credit_score").cast(IntegerType()))
    .withColumn("debt_to_income_ratio", F.col("raw_dti").cast(DoubleType()))
    
    # 4. Business Policy Boolean Flag
    .withColumn(
        "is_valid_credit_profile",
        (F.col("credit_score") >= 600) & (F.col("debt_to_income_ratio") <= 0.43)
    )
    
    # 5. Operational Audit Metadata
    .withColumn("_ingestion_timestamp", F.current_timestamp())
    
    # 6. Active Portfolio Filter
    .filter(F.col("status") == "ACTIVE")
    
    # 7. Explicit Silver Projection
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
```
