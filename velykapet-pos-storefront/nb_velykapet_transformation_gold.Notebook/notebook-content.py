# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "0e61ae20-b07e-4fde-9ae3-017c07caace2",
# META       "default_lakehouse_name": "lh_velykapet_silver_dev",
# META       "default_lakehouse_workspace_id": "b5af9286-d297-491a-a1bf-5ea0b186665d",
# META       "known_lakehouses": [
# META         {
# META           "id": "0e61ae20-b07e-4fde-9ae3-017c07caace2"
# META         },
# META         {
# META           "id": "0861f9d6-6a11-44cb-8a6d-bf98110b977b"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

"""
===============================================================================
Velykapet Data Engineering Pipeline - Capa Gold (Data Warehouse & Bot WhatsApp)
===============================================================================
Descripción:
  Script PySpark para Microsoft Fabric.
  Construye el Modelo Estrella completo y la analítica de conversión para el
  Bot de WhatsApp en 'lh_velykapet_gold_dev.dbo'.
===============================================================================
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as _sum, count as _count, avg as _avg, current_timestamp, round as _round, to_date, lit, coalesce
)

spark = SparkSession.builder \
    .appName("Velykapet_Gold_Reporting") \
    .getOrCreate()

SILVER_SCHEMA = "lh_velykapet_silver_dev.dbo"
GOLD_SCHEMA = "lh_velykapet_gold_dev.dbo"

def build_fact_sales():
    """1. Tabla de Hechos: FactSales."""
    print("📊 Generating Gold 'fact_sales'...")
    df_sales = spark.read.table(f"{SILVER_SCHEMA}.silver_sales")
    df_items = spark.read.table(f"{SILVER_SCHEMA}.silver_sale_items")

    s_cols = df_sales.columns
    i_cols = df_items.columns

    sales_join_i = "sale_id" if "sale_id" in i_cols else ("id" if "id" in i_cols else i_cols[0])
    sales_join_s = "id" if "id" in s_cols else ("sale_id" if "sale_id" in s_cols else s_cols[0])
    item_prod_name = "product_name" if "product_name" in i_cols else ("product_id" if "product_id" in i_cols else i_cols[0])

    df_joined = df_items.alias("i") \
        .join(df_sales.alias("s"), col(f"i.{sales_join_i}") == col(f"s.{sales_join_s}"), "inner")

    origin_col = col("s.origin") if "origin" in s_cols else lit("POS")
    pm_col = col("s.payment_method") if "payment_method" in s_cols else lit("Cash")
    ts_col = col("s.created_at") if "created_at" in s_cols else col("s.timestamp")

    select_exprs = [
        col("i.id").alias("item_id"),
        col(f"i.{sales_join_i}").alias("sale_id"),
        col(f"i.{item_prod_name}").alias("product_id"),
        col(f"i.{item_prod_name}").alias("product_name"),
        origin_col.alias("sale_origin"),
        pm_col.alias("payment_method"),
        ts_col.alias("sale_timestamp"),
        to_date(ts_col).alias("sale_date"),
        col("i.quantity").cast("int").alias("quantity"),
        (col("i.unit_cost").cast("double") if "unit_cost" in i_cols else lit(0.0)).alias("unit_cost"),
        (col("i.unit_price").cast("double") if "unit_price" in i_cols else lit(0.0)).alias("unit_price"),
        (col("i.total_price").cast("double") if "total_price" in i_cols else col("i.subtotal").cast("double")).alias("total_item_revenue"),
        (col("i.profit").cast("double") if "profit" in i_cols else lit(0.0)).alias("item_gross_profit")
    ]

    df_fact = df_joined.select(*select_exprs).withColumn("_updated_at", current_timestamp())
    df_fact.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_sales")
    print(f"✅ 'fact_sales' generated ({df_fact.count()} records).")

def build_fact_expenses():
    """2. Tabla de Hechos: FactExpenses."""
    print("💸 Generating Gold 'fact_expenses'...")
    df_exp = spark.read.table(f"{SILVER_SCHEMA}.silver_expenses")
    cols = df_exp.columns
    
    date_col = col("expense_date") if "expense_date" in cols else (col("created_at") if "created_at" in cols else current_timestamp())
    desc_col = col("description") if "description" in cols else lit("N/A")
    cat_col = col("category") if "category" in cols else lit("General")

    df_fact = df_exp.select(
        col("id").alias("expense_id"),
        desc_col.alias("description"),
        col("amount").cast("double").alias("expense_amount"),
        cat_col.alias("category"),
        to_date(date_col).alias("expense_date")
    ).withColumn("_updated_at", current_timestamp())

    df_fact.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_expenses")
    print(f"✅ 'fact_expenses' generated ({df_fact.count()} records). Columns: {df_fact.columns}")

def build_fact_purchases():
    """3. Tabla de Hechos: FactPurchases."""
    print("📦 Generating Gold 'fact_purchases'...")
    df_pur = spark.read.table(f"{SILVER_SCHEMA}.silver_purchases")
    cols = df_pur.columns

    date_col = col("purchase_date") if "purchase_date" in cols else (col("created_at") if "created_at" in cols else current_timestamp())
    supplier_col = col("supplier_id") if "supplier_id" in cols else (col("supplier") if "supplier" in cols else lit("Unknown"))
    amount_col = col("amount").cast("double") if "amount" in cols else lit(0.0)

    df_fact = df_pur.select(
        col("id").alias("purchase_id"),
        supplier_col.alias("supplier"),
        amount_col.alias("purchase_amount"),
        to_date(date_col).alias("purchase_date")
    ).withColumn("_updated_at", current_timestamp())

    df_fact.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_purchases")
    print(f"✅ 'fact_purchases' generated ({df_fact.count()} records). Columns: {df_fact.columns}")

def build_dim_products():
    """4. Dimensión: DimProducts (Integración de Catálogo Maestro y Precios)."""
    print("🏷️ Generating Gold 'dim_products'...")
    df_cat = spark.read.table(f"{SILVER_SCHEMA}.silver_master_catalog")
    df_prod = spark.read.table(f"{SILVER_SCHEMA}.silver_products")
    df_items = spark.read.table(f"{SILVER_SCHEMA}.silver_sale_items")

    # Unir catálogo maestro con precios y stock por barcode
    df_dim_cat = df_cat.alias("c") \
        .join(df_prod.alias("p"), col("c.barcode") == col("p.barcode"), "left") \
        .select(
            col("c.product_name").alias("product_id"),
            col("c.product_name").alias("product_name"),
            col("c.barcode").alias("barcode"),
            coalesce(col("p.supplier"), lit("N/A")).alias("supplier"),
            coalesce(col("p.cost_price").cast("double"), lit(0.0)).alias("cost_price"),
            coalesce(col("p.sale_price").cast("double"), lit(0.0)).alias("sale_price"),
            coalesce(col("p.stock").cast("int"), lit(0)).alias("current_stock")
        ).dropDuplicates(["product_name"])

    # Asegurar que cualquier producto vendido también esté presente
    df_items_prod = df_items.select(
        col("product_name").alias("product_id"),
        col("product_name").alias("product_name"),
        col("barcode").alias("barcode"),
        lit("Velykapet").alias("supplier"),
        coalesce(col("unit_cost").cast("double"), lit(0.0)).alias("cost_price"),
        coalesce(col("unit_price").cast("double"), lit(0.0)).alias("sale_price"),
        lit(10).cast("int").alias("current_stock")
    ).distinct()

    df_dim = df_dim_cat.unionByName(df_items_prod, allowMissingColumns=True) \
        .dropDuplicates(["product_name"]) \
        .withColumn("_updated_at", current_timestamp())

    df_dim.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.dim_products")
    print(f"✅ 'dim_products' generated ({df_dim.count()} records). Columns: {df_dim.columns}")

def build_dim_dates():
    """5. Dimensión: DimDates."""
    print("📅 Generating Gold 'dim_dates'...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE {GOLD_SCHEMA}.dim_dates AS
        SELECT 
            to_date(datum) AS date_key,
            YEAR(datum) AS year,
            QUARTER(datum) AS quarter,
            MONTH(datum) AS month_number,
            DATE_FORMAT(datum, 'MMMM') AS month_name,
            DATE_FORMAT(datum, 'yyyy-MM') AS year_month,
            DAYOFMONTH(datum) AS day_of_month,
            DAYOFWEEK(datum) AS day_of_week,
            DATE_FORMAT(datum, 'EEEE') AS day_name,
            CASE WHEN DAYOFWEEK(datum) IN (1, 7) THEN true ELSE false END AS is_weekend
        FROM (
            SELECT EXPLODE(SEQUENCE(DATE'2025-01-01', DATE'2026-12-31', INTERVAL 1 DAY)) AS datum
        )
    """)
    print("✅ 'dim_dates' generated.")

def build_kpi_whatsapp_funnel():
    """6. Analítica de Conversión del Bot de WhatsApp."""
    print("📲 Generating Gold 'kpi_whatsapp_conversion' for WhatsApp Bot launch...")
    
    df_wa_orders = spark.read.table(f"{SILVER_SCHEMA}.silver_whatsapp_orders")
    df_wa_msgs = spark.read.table(f"{SILVER_SCHEMA}.silver_processed_whatsapp_messages")

    df_kpi = df_wa_orders.agg(
        _count("id").alias("total_whatsapp_orders"),
        lit(df_wa_msgs.count()).alias("total_processed_messages")
    ).withColumn("_calculated_at", current_timestamp())

    df_kpi.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.kpi_whatsapp_conversion")
    print("✅ KPI 'kpi_whatsapp_conversion' ready for live WhatsApp Bot traffic.")

def build_kpis():
    """7. Tablas de KPIs Analíticos."""
    print("📈 Generating Gold KPIs (Daily Sales Trend, Inventory Health)...")
    
    df_sales_fact = spark.read.table(f"{GOLD_SCHEMA}.fact_sales")
    df_trend = df_sales_fact.groupBy("sale_date") \
        .agg(
            _count("sale_id").alias("total_transactions"),
            _sum("quantity").alias("total_units_sold"),
            _round(_sum("total_item_revenue"), 2).alias("gross_revenue"),
            _round(_sum("item_gross_profit"), 2).alias("gross_profit")
        ).withColumn("_calculated_at", current_timestamp())
    
    df_trend.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.kpi_daily_sales_trend")

    df_dim_p = spark.read.table(f"{GOLD_SCHEMA}.dim_products")
    df_inv = df_dim_p.agg(
        _count("product_id").alias("total_skus"),
        _sum("current_stock").alias("total_stock_units"),
        _round(_sum(col("current_stock") * col("cost_price")), 2).alias("total_inventory_cost_value"),
        _round(_sum(col("current_stock") * col("sale_price")), 2).alias("total_inventory_retail_value")
    ).withColumn("_calculated_at", current_timestamp())

    df_inv.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.kpi_inventory_health")
    print("✅ KPIs 'kpi_daily_sales_trend' and 'kpi_inventory_health' generated.")

def run_gold_pipeline():
    """Ejecución del pipeline Gold completo."""
    print("==================================================")
    print("EJECUTANDO CAPA GOLD COMPLETA - VELYKAPET")
    print("==================================================")
    
    build_fact_sales()
    build_fact_expenses()
    build_fact_purchases()
    build_dim_products()
    build_dim_dates()
    build_kpi_whatsapp_funnel()
    build_kpis()
    
    print("🏁 Capa Gold completada exitosamente.")

if __name__ == "__main__":
    run_gold_pipeline()


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# CELL ********************

df_fs = spark.read.table("lh_velykapet_gold_dev.dbo.fact_sales")
df_dp = spark.read.table("lh_velykapet_gold_dev.dbo.dim_products")

print(f"📊 Total ventas en fact_sales: {df_fs.count()}")
print(f"🏷️ Total productos en dim_products: {df_dp.count()}")

print("\n--- Muestra de fact_sales (product_id y product_name) ---")
df_fs.select("sale_id", "product_id", "product_name", "total_item_revenue").show(5, truncate=False)

print("\n--- Muestra de dim_products (product_id y product_name) ---")
df_dp.select("product_id", "product_name").show(5, truncate=False)

# Validación de match entre tablas
df_match = df_fs.join(df_dp, df_fs.product_id == df_dp.product_id, "inner")
print(f"\n🔍 Coincidencias entre fact_sales y dim_products por product_id: {df_match.count()} filas")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

print("--- silver_master_catalog ---")
spark.read.table("lh_velykapet_silver_dev.dbo.silver_master_catalog").show(5, truncate=False)

print("--- silver_products (todas las columnas) ---")
spark.read.table("lh_velykapet_silver_dev.dbo.silver_products").show(5, truncate=False)

print("--- silver_sale_items ---")
spark.read.table("lh_velykapet_silver_dev.dbo.silver_sale_items").show(5, truncate=False)


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
