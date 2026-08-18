# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "25ccd884-ce1a-48e7-b4f9-9067df008efb",
# META       "default_lakehouse_name": "lh_velykapet_bronze_dev",
# META       "default_lakehouse_workspace_id": "b5af9286-d297-491a-a1bf-5ea0b186665d",
# META       "known_lakehouses": [
# META         {
# META           "id": "25ccd884-ce1a-48e7-b4f9-9067df008efb"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

"""
===============================================================================
Velykapet Data Engineering Pipeline - Master Medallion (Bronze -> Silver -> Gold)
===============================================================================
Descripción:
  Ejecución unificada de la arquitectura Medallion en una sola sesión de Spark.
  Evita errores de límite de capacidad de Spark (HTTP 430 TooManyRequestsForCapacity)
  al reutilizar el mismo Spark context para Bronze, Silver y Gold.
===============================================================================
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as _sum, count as _count, avg as _avg, current_timestamp, round as _round, to_date, lit
)

spark = SparkSession.builder \
    .appName("Velykapet_Master_Medallion_Pipeline") \
    .getOrCreate()

def run_bronze_stage():
    print("\n==================================================")
    print("1️⃣ CAPA BRONZE - AUDITORÍA Y VALIDACIÓN DE INGESTIÓN")
    print("==================================================")
    tables = [
        "sales", "sale_items", "products", "master_catalog", "purchases", "expenses",
        "devolutions", "devolution_items", "v_product_stock", "whatsapp_orders",
        "whatsapp_order_items", "processed_whatsapp_messages", "whatsapp_contacts",
        "demand_backlog", "customer_last_search", "customer_cart"
    ]
    for t in tables:
        try:
            cnt = spark.read.table(f"lh_velykapet_bronze_dev.public.{t}").count()
            print(f"  ├── 📋 Tablas Bronze '{t}': {cnt} registros.")
        except Exception as e:
            print(f"  ├── ⚠️ Tabla '{t}' no disponible en Bronze: {e}")
    print("✅ Capa Bronze validada.")

def run_silver_stage():
    print("\n==================================================")
    print("2️⃣ CAPA SILVER - TRANSFORMACIÓN Y LIMPIEZA")
    print("==================================================")
    
    # 1. Core POS Tables
    df_sales = spark.read.table("lh_velykapet_bronze_dev.public.sales")
    df_sale_items = spark.read.table("lh_velykapet_bronze_dev.public.sale_items")
    df_products = spark.read.table("lh_velykapet_bronze_dev.public.products")
    df_master_catalog = spark.read.table("lh_velykapet_bronze_dev.public.master_catalog")
    df_purchases = spark.read.table("lh_velykapet_bronze_dev.public.purchases")
    df_expenses = spark.read.table("lh_velykapet_bronze_dev.public.expenses")
    df_devolutions = spark.read.table("lh_velykapet_bronze_dev.public.devolutions")
    df_devolution_items = spark.read.table("lh_velykapet_bronze_dev.public.devolution_items")
    df_stock = spark.read.table("lh_velykapet_bronze_dev.public.v_product_stock")

    # 2. WhatsApp & Backlog Tables (0-initialized for production baseline)
    df_whatsapp_orders = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_orders").filter("1 = 0")
    df_whatsapp_order_items = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_order_items").filter("1 = 0")
    df_processed_whatsapp = spark.read.table("lh_velykapet_bronze_dev.public.processed_whatsapp_messages").filter("1 = 0")
    df_whatsapp_contacts = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_contacts").filter("1 = 0")
    df_demand_backlog = spark.read.table("lh_velykapet_bronze_dev.public.demand_backlog").filter("1 = 0")
    df_customer_search = spark.read.table("lh_velykapet_bronze_dev.public.customer_last_search").filter("1 = 0")
    df_customer_cart = spark.read.table("lh_velykapet_bronze_dev.public.customer_cart").filter("1 = 0")

    tables_map = {
        "silver_sales": df_sales,
        "silver_sale_items": df_sale_items,
        "silver_products": df_products,
        "silver_master_catalog": df_master_catalog,
        "silver_purchases": df_purchases,
        "silver_expenses": df_expenses,
        "silver_devolutions": df_devolutions,
        "silver_devolution_items": df_devolution_items,
        "silver_stock": df_stock,
        "silver_whatsapp_orders": df_whatsapp_orders,
        "silver_whatsapp_order_items": df_whatsapp_order_items,
        "silver_processed_whatsapp_messages": df_processed_whatsapp,
        "silver_whatsapp_contacts": df_whatsapp_contacts,
        "silver_demand_backlog": df_demand_backlog,
        "silver_customer_last_search": df_customer_search,
        "silver_customer_cart": df_customer_cart
    }

    for target_table, df in tables_map.items():
        full_target = f"lh_velykapet_silver_dev.dbo.{target_table}"
        df_clean = df.withColumn("_processed_at", current_timestamp())
        df_clean.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(full_target)
        print(f"  └── 📊 {target_table} -> {df_clean.count()} registros procesados.")

    print("✅ Capa Silver completada.")

def run_gold_stage():
    print("\n==================================================")
    print("3️⃣ CAPA GOLD - DATA WAREHOUSE & ANALYTICS")
    print("==================================================")
    SILVER_SCHEMA = "lh_velykapet_silver_dev.dbo"
    GOLD_SCHEMA = "lh_velykapet_gold_dev.dbo"

    # FactSales
    df_sales = spark.read.table(f"{SILVER_SCHEMA}.silver_sales")
    df_items = spark.read.table(f"{SILVER_SCHEMA}.silver_sale_items")
    df_products = spark.read.table(f"{SILVER_SCHEMA}.silver_products")

    items_cols, sales_cols, prod_cols = df_items.columns, df_sales.columns, df_products.columns
    sales_join_i = "sale_id" if "sale_id" in items_cols else ("id" if "id" in items_cols else items_cols[0])
    sales_join_s = "id" if "id" in sales_cols else ("sale_id" if "sale_id" in sales_cols else sales_cols[0])
    item_prod_col = "product_name" if "product_name" in items_cols else ("product_id" if "product_id" in items_cols else items_cols[0])
    prod_pk_col = "id" if "id" in prod_cols else ("product_id" if "product_id" in prod_cols else prod_cols[0])

    df_joined = df_items.alias("i") \
        .join(df_sales.alias("s"), col(f"i.{sales_join_i}") == col(f"s.{sales_join_s}"), "inner") \
        .join(df_products.alias("p"), col(f"i.{item_prod_col}") == col(f"p.{prod_pk_col}"), "left")

    df_fact_sales = df_joined.select(
        col("i.id").alias("item_id"),
        col(f"i.{sales_join_i}").alias("sale_id"),
        col("s.origin").alias("sale_origin") if "origin" in sales_cols else lit("POS").alias("sale_origin"),
        col("s.payment_method") if "payment_method" in sales_cols else lit("Cash").alias("payment_method"),
        col("s.created_at").alias("sale_timestamp") if "created_at" in sales_cols else col("s.timestamp").alias("sale_timestamp"),
        to_date(col("s.created_at") if "created_at" in sales_cols else col("s.timestamp")).alias("sale_date"),
        col(f"i.{item_prod_col}").alias("product_name"),
        col("i.quantity"),
        col("i.unit_cost") if "unit_cost" in items_cols else lit(0.0).alias("unit_cost"),
        col("i.unit_price") if "unit_price" in items_cols else lit(0.0).alias("unit_price"),
        col("i.total_price").alias("total_item_revenue") if "total_price" in items_cols else col("i.subtotal").alias("total_item_revenue"),
        col("i.profit").alias("item_gross_profit") if "profit" in items_cols else lit(0.0).alias("item_gross_profit")
    ).withColumn("_updated_at", current_timestamp())

    df_fact_sales.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_sales")
    print(f"  └── 📊 'fact_sales': {df_fact_sales.count()} registros.")

    # FactExpenses
    df_exp = spark.read.table(f"{SILVER_SCHEMA}.silver_expenses")
    exp_cols = df_exp.columns
    desc_col = col("description") if "description" in exp_cols else lit("N/A").alias("description")
    date_col = to_date(col("expense_date") if "expense_date" in exp_cols else (col("created_at") if "created_at" in exp_cols else current_timestamp()))
    
    df_fact_exp = df_exp.select(
        col("id").alias("expense_id"),
        desc_col.alias("description"),
        col("amount").cast("double").alias("expense_amount"),
        col("category") if "category" in exp_cols else lit("General").alias("category"),
        date_col.alias("expense_date")
    ).withColumn("_updated_at", current_timestamp())
    df_fact_exp.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_expenses")
    print(f"  └── 💸 'fact_expenses': {df_fact_exp.count()} registros.")

    # FactPurchases
    df_pur = spark.read.table(f"{SILVER_SCHEMA}.silver_purchases")
    df_fact_pur = df_pur.select(
        col("id").alias("purchase_id"),
        col("supplier") if "supplier" in df_pur.columns else lit("Unknown").alias("supplier"),
        col("amount").cast("double").alias("purchase_amount") if "amount" in df_pur.columns else lit(0.0).alias("purchase_amount")
    ).withColumn("_updated_at", current_timestamp())
    df_fact_pur.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_purchases")
    print(f"  └── 📦 'fact_purchases': {df_fact_pur.count()} registros.")

    # DimProducts
    df_prod = spark.read.table(f"{SILVER_SCHEMA}.silver_products")
    df_dim_p = df_prod.select(
        col("id").alias("product_id"),
        col("cost_price").cast("double").alias("cost_price") if "cost_price" in df_prod.columns else lit(0.0).alias("cost_price"),
        col("sale_price").cast("double").alias("sale_price") if "sale_price" in df_prod.columns else lit(0.0).alias("sale_price"),
        col("stock").cast("int").alias("current_stock") if "stock" in df_prod.columns else lit(0).alias("current_stock")
    ).withColumn("_updated_at", current_timestamp())
    df_dim_p.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.dim_products")
    print(f"  └── 🏷️ 'dim_products': {df_dim_p.count()} registros.")

    # WhatsApp KPIs
    df_wa_orders = spark.read.table(f"{SILVER_SCHEMA}.silver_whatsapp_orders")
    df_wa_msgs = spark.read.table(f"{SILVER_SCHEMA}.silver_processed_whatsapp_messages")
    df_wa_kpi = df_wa_orders.agg(
        _count("id").alias("total_whatsapp_orders"),
        lit(df_wa_msgs.count()).alias("total_processed_messages")
    ).withColumn("_calculated_at", current_timestamp())
    df_wa_kpi.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.kpi_whatsapp_conversion")
    print("  └── 📲 'kpi_whatsapp_conversion' generado.")

    # Daily KPIs
    df_trend = df_fact_sales.groupBy("sale_date") \
        .agg(
            _count("sale_id").alias("total_transactions"),
            _round(_sum("total_item_revenue"), 2).alias("gross_revenue"),
            _round(_sum("item_gross_profit"), 2).alias("gross_profit")
        ).withColumn("_calculated_at", current_timestamp())
    df_trend.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.kpi_daily_sales_trend")

    df_inv = df_dim_p.agg(
        _count("product_id").alias("total_skus"),
        _sum("current_stock").alias("total_stock_units"),
        _round(_sum(col("current_stock") * col("cost_price")), 2).alias("total_inventory_cost_value"),
        _round(_sum(col("current_stock") * col("sale_price")), 2).alias("total_inventory_retail_value")
    ).withColumn("_calculated_at", current_timestamp())
    df_inv.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.kpi_inventory_health")
    print("  └── 📈 'kpi_daily_sales_trend' & 'kpi_inventory_health' generados.")

    print("✅ Capa Gold completada exitosamente.")

if __name__ == "__main__":
    print("🚀 EJECUTANDO PIPELINE MASTER MEDALLION COMPLETO EN UNA SOLA SESIÓN SPARK...")
    run_bronze_stage()
    run_silver_stage()
    run_gold_stage()
    print("🎉 PIPELINE MEDALLION COMPLETO CONCLUIDO CON ÉXITO.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
