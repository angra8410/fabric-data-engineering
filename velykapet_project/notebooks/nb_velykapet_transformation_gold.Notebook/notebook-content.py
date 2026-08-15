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
    col, sum as _sum, count as _count, avg as _avg, current_timestamp, round as _round, to_date, lit
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
    df_products = spark.read.table(f"{SILVER_SCHEMA}.silver_products")

    items_cols = df_items.columns
    sales_cols = df_sales.columns
    prod_cols = df_products.columns

    sales_join_i = "sale_id" if "sale_id" in items_cols else ("id" if "id" in items_cols else items_cols[0])
    sales_join_s = "id" if "id" in sales_cols else ("sale_id" if "sale_id" in sales_cols else sales_cols[0])

    item_prod_col = "product_name" if "product_name" in items_cols else ("product_id" if "product_id" in items_cols else items_cols[0])
    prod_pk_col = "id" if "id" in prod_cols else ("product_id" if "product_id" in prod_cols else prod_cols[0])

    df_joined = df_items.alias("i") \
        .join(df_sales.alias("s"), col(f"i.{sales_join_i}") == col(f"s.{sales_join_s}"), "inner") \
        .join(df_products.alias("p"), col(f"i.{item_prod_col}") == col(f"p.{prod_pk_col}"), "left")

    origin_col = col("s.origin") if "origin" in sales_cols else lit("POS")
    pm_col = col("s.payment_method") if "payment_method" in sales_cols else lit("Cash")
    ts_col = col("s.created_at") if "created_at" in sales_cols else col("s.timestamp")
    unit_cost_col = col("i.unit_cost").cast("double") if "unit_cost" in items_cols else lit(0.0)
    unit_price_col = col("i.unit_price").cast("double") if "unit_price" in items_cols else lit(0.0)
    revenue_col = col("i.total_price").cast("double") if "total_price" in items_cols else (col("i.subtotal").cast("double") if "subtotal" in items_cols else lit(0.0))
    profit_col = col("i.profit").cast("double") if "profit" in items_cols else lit(0.0)

    df_fact = df_joined.select(
        col("i.id").alias("item_id"),
        col(f"i.{sales_join_i}").alias("sale_id"),
        origin_col.alias("sale_origin"),
        pm_col.alias("payment_method"),
        ts_col.alias("sale_timestamp"),
        to_date(ts_col).alias("sale_date"),
        col(f"i.{item_prod_col}").alias("product_name"),
        col("i.quantity").cast("int").alias("quantity"),
        unit_cost_col.alias("unit_cost"),
        unit_price_col.alias("unit_price"),
        revenue_col.alias("total_item_revenue"),
        profit_col.alias("item_gross_profit")
    ).withColumn("_updated_at", current_timestamp())

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
    """4. Dimensión: DimProducts."""
    print("🏷️ Generating Gold 'dim_products'...")
    df_prod = spark.read.table(f"{SILVER_SCHEMA}.silver_products")
    cols = df_prod.columns

    name_col = col("name") if "name" in cols else (col("product_name") if "product_name" in cols else col("id").cast("string"))

    df_dim = df_prod.select(
        col("id").cast("string").alias("product_id"),
        name_col.alias("product_name"),
        (col("barcode") if "barcode" in cols else lit("N/A")).alias("barcode"),
        (col("supplier") if "supplier" in cols else lit("N/A")).alias("supplier"),
        (col("cost_price").cast("double") if "cost_price" in cols else lit(0.0)).alias("cost_price"),
        (col("sale_price").cast("double") if "sale_price" in cols else lit(0.0)).alias("sale_price"),
        (col("stock").cast("int") if "stock" in cols else lit(0)).alias("current_stock")
    ).withColumn("_updated_at", current_timestamp())

    df_dim.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.dim_products")
    print(f"✅ 'dim_products' generated ({df_dim.count()} records). Columns: {df_dim.columns}")

def build_kpi_whatsapp_funnel():
    """5. Analítica de Conversión del Bot de WhatsApp."""
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
    """6. Tablas de KPIs Analíticos."""
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
    print("EJECUTANDO CAPA GOLD COMPLETA (INCLUYENDO BOT WHATSAPP) - VELYKAPET")
    print("==================================================")
    
    build_fact_sales()
    build_fact_expenses()
    build_fact_purchases()
    build_dim_products()
    build_dim_dates()
    build_kpi_whatsapp_funnel()
    build_kpis()

def build_dim_dates():
    """Build DimDates table in Gold Lakehouse."""
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
    
    print("🏁 Capa Gold completada exitosamente.")

run_gold_pipeline()


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
