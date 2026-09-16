# Guía Maestra: De SQL a PySpark (Construyendo el Puente Mental)

- **Propósito:** Servir como documento de referencia rápida y guía de estudio para desarrolladores con sólida experiencia en SQL que inician su transición a PySpark y la arquitectura Medallion en Microsoft Fabric.
- **Principio Fundamental:** Si dominas SQL, ya dominas el 80% de la lógica de PySpark. Por debajo, ambos comparten el mismo motor de ejecución y optimización (**Catalyst Optimizer**).

---

## 1. El Puente Conceptual (Mental Model)

En SQL relacional tradicional escribes sentencias declarativas (`SELECT ... FROM ... WHERE ...`). En PySpark trabajas con **DataFrames distribuidos** aplicando transformaciones encadenadas mediante métodos (`df.select().filter()`).

### 🔑 Reglas de Oro en PySpark
1. **`F.col("nombre")` vs. `F.lit("valor")`:**
   - Para referenciar una columna existente en el DataFrame, siempre usa `F.col("nombre_columna")`.
   - Para introducir un valor fijo o constante (string, número, booleano), siempre usa `F.lit("mi_texto")` o `F.lit(10)`.
2. **Operadores Lógicos y Paréntesis Obligatorios:**
   - En SQL: `WHERE credit_score >= 600 AND dti <= 0.43`
   - En PySpark: `F.when((F.col("credit_score") >= 600) & (F.col("dti") <= 0.43), True)`
   - *Nota crítica:* En PySpark **siempre** debes envolver cada condición individual en paréntesis `()` al usar `&` (AND), `|` (OR) o `~` (NOT), debido a la precedencia de operadores en Python.
3. **Casting Seguro Sin Excepciones:**
   - En PySpark, `.cast("int")` o `.cast("double")` maneja cadenas de texto inválidas (como `"invalid_score"` o `"NaN"`) convirtiéndolas automáticamente a `null` de forma segura, evitando caídas (*runtime crashes*) en el pipeline.

---

## 2. Tabla de Equivalencias Directas: De SQL a PySpark

A continuación se detallan las cláusulas más comunes de SQL y su equivalente directo en la API de PySpark (`from pyspark.sql import functions as F`):

| Operación / Concepto | Sintaxis SQL Estándar | Sintaxis PySpark (`functions as F`) |
| :--- | :--- | :--- |
| **Seleccionar columnas** | `SELECT col_a, col_b FROM df` | `df.select("col_a", "col_b")` |
| **Renombrar columnas** | `SELECT col_a AS nueva_col FROM df` | `df.select(F.col("col_a").alias("nueva_col"))` o `df.withColumnRenamed("col_a", "nueva_col")` |
| **Agregar/Modificar columna** | `SELECT *, UPPER(name) AS name FROM df` | `df.withColumn("name", F.upper(F.col("name")))` |
| **Filtrar registros** | `WHERE status = 'ACTIVE'` | `df.filter(F.col("status") == "ACTIVE")` o `df.where(...)` |
| **Filtros múltiples** | `WHERE status = 'A' AND amount > 100` | `df.filter((F.col("status") == "A") & (F.col("amount") > 100))` |
| **Lógica Condicional** | `CASE WHEN score >= 600 THEN 'A' ELSE 'B' END` | `F.when(F.col("score") >= 600, "A").otherwise("B")` |
| **Manejo de Nulos** | `COALESCE(email, 'sin_correo')` | `F.coalesce(F.col("email"), F.lit("sin_correo"))` |
| **Reemplazo de Nulos** | `NULLIF(col_a, '')` | `F.when(F.col("col_a") == "", None).otherwise(F.col("col_a"))` |
| **Conversión de Tipos (Cast)**| `CAST(raw_score AS INT)` | `F.col("raw_score").cast("int")` |
| **Limpieza de Cadenas** | `TRIM(col)`, `INITCAP(col)`, `UPPER(col)` | `F.trim(F.col("col"))`, `F.initcap(F.col("col"))`, `F.upper(F.col("col"))` |
| **Fechas y Auditoría** | `CURRENT_TIMESTAMP()`, `CURRENT_DATE()` | `F.current_timestamp()`, `F.current_date()` |
| **Deduplicación** | `SELECT DISTINCT col_a, col_b FROM df` | `df.select("col_a", "col_b").distinct()` o `df.dropDuplicates(["col_a"])` |

---

## 3. Desglose Práctico: Caso de Estudio (Reto 2.1 - Ingesta de Clientes)

### El Escenario de Negocio
Un lote de clientes (*borrowers*) de la Cooperativa llega a la capa **Bronze** en formato crudo con valores mixtos, espacios en blanco, correos en mayúsculas/minúsculas y textos corruptos en campos numéricos (`"invalid_score"`, `"NaN"`).

### Comparativa: La Solución en SQL vs. La Solución en PySpark

#### Opción A: En SQL Relacional
```sql
SELECT 
    member_id,
    INITCAP(TRIM(full_name)) AS full_name,
    LOWER(COALESCE(email, 'not_provided@creditunion.org')) AS email,
    CAST(raw_credit_score AS INT) AS credit_score,
    CAST(raw_dti AS DOUBLE) AS debt_to_income_ratio,
    joined_date,
    UPPER(status) AS status,
    CASE 
        WHEN CAST(raw_credit_score AS INT) >= 600 
         AND CAST(raw_dti AS DOUBLE) <= 0.43 
        THEN TRUE 
        ELSE FALSE 
    END AS is_valid_credit_profile,
    CURRENT_TIMESTAMP() AS _ingestion_timestamp
FROM raw_data;
```

#### Opción B: En PySpark (Construcción Modular y Limpia)
```python
from pyspark.sql import functions as F

# 1. Definición de transformaciones modulares de texto
c_full_name = F.initcap(F.trim(F.col("full_name")))
c_email = F.lower(F.coalesce(F.col("email"), F.lit("not_provided@creditunion.org")))
c_status = F.upper(F.col("status"))

# 2. Castings numéricos seguros (Safe Parsing)
# Valores como "invalid_score" se transforman automáticamente en NULL
c_credit_score = F.col("raw_credit_score").cast("int")
c_dti = F.col("raw_dti").cast("double")

# 3. Reglas de negocio y banderas de calidad (CASE WHEN ... THEN ... ELSE ...)
c_valid_profile = (
    F.when((c_credit_score >= 600) & (c_dti <= 0.43), True)
     .otherwise(False)
)

# 4. Proyección final (Equivalente al bloque SELECT)
df_silver_members = df_raw.select(
    F.col("member_id"),
    c_full_name.alias("full_name"),
    c_email.alias("email"),
    c_credit_score.alias("credit_score"),
    c_dti.alias("debt_to_income_ratio"),
    F.col("joined_date"),
    c_status.alias("status"),
    c_valid_profile.alias("is_valid_credit_profile"),
    F.current_timestamp().alias("_ingestion_timestamp")
)
```

---

## 4. Agrupaciones y Joins: El Próximo Escalón

| Concepto SQL | SQL | PySpark |
| :--- | :--- | :--- |
| **GROUP BY con Agregación** | `SELECT branch_id, COUNT(*), SUM(amount) FROM loans GROUP BY branch_id` | `df_loans.groupBy("branch_id").agg(F.count("*").alias("total_loans"), F.sum("amount").alias("total_originated"))` |
| **HAVING (Filtro post-agrupación)**| `GROUP BY branch_id HAVING SUM(amount) > 50000` | `df_loans.groupBy("branch_id").agg(F.sum("amount").alias("total")).filter(F.col("total") > 50000)` |
| **Relational JOIN** | `FROM loans l INNER JOIN members m ON l.member_id = m.member_id` | `df_loans.join(df_members, on="member_id", how="inner")` |
| **CTE (Common Table Expression)**| `WITH pre_agg AS (SELECT ...) SELECT ... FROM pre_agg` | Simplemente asignas el DataFrame resultante a una variable intermedia: `df_pre_agg = df_loans.groupBy(...)...` y luego `df_final = df_pre_agg.join(...)` |

---

## 5. Resumen de Buenas Prácticas en Fabric Lakehouse
- **Evitar bucles `for` o funciones Python nativas en filas individuales:** Siempre usa las funciones nativas de `pyspark.sql.functions` para que el optimizador Catalyst ejecute el cálculo compilado en C++ / Java bytecode.
- **DataFrames Intermedios:** Crear variables (`df_step1`, `df_step2`) no consume memoria adicional porque Spark opera bajo **Lazy Evaluation** (evaluación perezosa): no calcula nada hasta que se ejecuta una acción (como escribir a Delta Lake con `.write.format("delta").save()`).

---

## 6. Core Mental Models & Production Patterns (Master Notes)

### A. The "Onion Principle" (Inside-Out Functional Composition)
Instead of procedural loops or nested `if/else`, compose data transformations in concentric layers from the inside out:
```text
Layer 4: [ GOVERNANCE ] Fallback Default      -> F.coalesce( ..., F.lit("not_provided@creditunion.org") )
  Layer 3: [ MISSINGNESS ] Standardize to NULL -> F.nullif( ..., F.lit("") )
    Layer 2: [ HYGIENE ] Clean & Normalize     -> F.lower( F.trim( ... ) )
      Layer 1: [ RAW SIGNAL ] Source Column    -> F.col("email")
```

**Production Implementation:**
```python
F.coalesce(
    F.nullif(F.lower(F.trim(F.col("email"))), F.lit("")),
    F.lit("not_provided@creditunion.org")
)
```

### B. DataFrame Immutability & Method Chaining
- **DataFrames never mutate in-place:** Every method (`.withColumn()`, `.filter()`, `.select()`) returns a new DataFrame instance.
- **Method Chaining:** Enclose DataFrame pipelines in parentheses `( ... )` to chain transformations clearly and avoid accidental state bifurcation across notebook cells:
```python
df_cleaned = (
    df_raw
    .withColumn("full_name", F.initcap(F.trim(F.col("full_name"))))
    .withColumn("status", F.upper(F.trim(F.col("status"))))
    .withColumn("email", F.coalesce(
        F.nullif(F.lower(F.trim(F.col("email"))), F.lit("")),
        F.lit("not_provided@creditunion.org")
    ))
)
```

### C. Explicit Schemas (`StructType`) vs. Schema Inference
- **Syntax:** `StructField(name, dataType, nullable)` where `False` means `NOT NULL`.
- **Architectural Benefits:**
  1. **Performance:** Eliminates double-reading and expensive schema inference passes over storage.
  2. **Zero Corruption:** Prevents loss of leading zeros in numeric-like identifiers (e.g., zip codes, member IDs).
  3. **Data Contract:** Guarantees strict boundary enforcement at Bronze ingestion.

### D. Critical Syntax Differences vs. Pandas
- **Null check:** Use `.isNull()` (capital **N**), not `.isnull()`.
- **Constants:** Always inject literal values into Spark expressions using `F.lit("constant")`.
- **Conditions:** Always wrap logical conditions in parentheses: `(F.col("a") >= 10) & (F.col("b") <= 20)`.

