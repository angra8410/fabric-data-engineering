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
    
    df_fact = df_exp.select(
        col("id").alias("expense_id"),
        col("description") if "description" in cols else lit("N/A").alias("description"),
        col("amount").cast("double").alias("expense_amount"),
        col("category") if "category" in cols else lit("General").alias("category"),
        col("expense_date") if "expense_date" in cols else to_date(col("created_at")).alias("expense_date")
    ).withColumn("_updated_at", current_timestamp())

    df_fact.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_expenses")
    print(f"✅ 'fact_expenses' generated ({df_fact.count()} records).")

def build_fact_purchases():
    """3. Tabla de Hechos: FactPurchases."""
    print("📦 Generating Gold 'fact_purchases'...")
    df_pur = spark.read.table(f"{SILVER_SCHEMA}.silver_purchases")
    cols = df_pur.columns

    df_fact = df_pur.select(
        col("id").alias("purchase_id"),
        col("supplier_id") if "supplier_id" in cols else col("supplier").alias("supplier") if "supplier" in cols else lit("Unknown").alias("supplier"),
        col("amount").cast("double").alias("purchase_amount") if "amount" in cols else lit(0.0).alias("purchase_amount"),
        to_date(col("created_at")).alias("purchase_date") if "created_at" in cols else current_timestamp().alias("purchase_date")
    ).withColumn("_updated_at", current_timestamp())

    df_fact.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_purchases")
    print(f"✅ 'fact_purchases' generated ({df_fact.count()} records).")

def build_dim_products():
    """4. Dimensión: DimProducts."""
    print("🏷️ Generating Gold 'dim_products'...")
    df_cat = spark.read.table(f"{SILVER_SCHEMA}.silver_master_catalog")
    df_prod = spark.read.table(f"{SILVER_SCHEMA}.silver_products")
    df_items = spark.read.table(f"{SILVER_SCHEMA}.silver_sale_items")

    from pyspark.sql.functions import coalesce

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
    print(f"✅ 'dim_products' generated ({df_dim.count()} records).")

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
    build_kpi_whatsapp_funnel()
    build_kpis()
    
    print("🏁 Capa Gold completada exitosamente.")

run_gold_pipeline()
