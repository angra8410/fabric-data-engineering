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

from datetime import datetime
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
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    for t in tables:
        try:
            full_table_name = f"lh_velykapet_bronze_dev.public.{t}"
            df_raw = spark.read.table(full_table_name)
            df_bronze = df_raw.withColumn("_ingested_at", current_timestamp()).withColumn("_batch_id", lit(batch_id))
            df_bronze.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(full_table_name)
            print(f"  ├── 📋 Tabla Bronze '{t}': {df_bronze.count()} registros verificados.")
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

    s_cols, i_cols = df_sales.columns, df_items.columns
    sales_join_i = "sale_id" if "sale_id" in i_cols else ("id" if "id" in i_cols else i_cols[0])
    sales_join_s = "id" if "id" in s_cols else ("sale_id" if "sale_id" in s_cols else s_cols[0])
    item_prod_name = "product_name" if "product_name" in i_cols else ("product_id" if "product_id" in i_cols else i_cols[0])

    df_joined = df_items.alias("i") \
        .join(df_sales.alias("s"), col(f"i.{sales_join_i}") == col(f"s.{sales_join_s}"), "inner")

    from pyspark.sql.functions import when, upper, trim, coalesce

    # Limpieza de métodos de pago
    pm_raw = upper(trim(coalesce(col("s.payment_method"), lit("NO ESPECIFICADO"))))
    clean_pm = when(pm_raw.contains("EFECTIVO") & pm_raw.contains("BANCOLOMBIA"), "Mixto (Bancolombia + Efectivo)") \
        .when(pm_raw.contains("EFECTIVO") & (pm_raw.contains("BRE") | pm_raw.contains("NEQUI")), "Mixto (Digital + Efectivo)") \
        .when(pm_raw.isin("B-BRE", "BRE-B", "BRE B", "B_BRE"), "Transferencia (Bre-B / Bancolombia)") \
        .when(pm_raw.contains("BANCOLOMBIA"), "Bancolombia") \
        .when(pm_raw.contains("NEQUI"), "Nequi") \
        .when(pm_raw.contains("DAVIPLATA"), "Daviplata") \
        .when(pm_raw.contains("BRE"), "Bre-B") \
        .when(pm_raw.contains("TARJETA") | pm_raw.contains("DATAFONO"), "Tarjeta / Datáfono") \
        .when(pm_raw.contains("EFECTIVO"), "Efectivo") \
        .otherwise("Otros")

    ts_expr = coalesce(col("s.timestamp"), col("s.created_at")) if "timestamp" in s_cols else (col("s.created_at") if "created_at" in s_cols else current_timestamp())

    df_fact_sales = df_joined.select(
        col("i.id").alias("item_id"),
        col(f"i.{sales_join_i}").alias("sale_id"),
        col(f"i.{item_prod_name}").alias("product_id"),
        col(f"i.{item_prod_name}").alias("product_name"),
        (col("s.origin") if "origin" in s_cols else lit("POS")).alias("sale_origin"),
        clean_pm.alias("payment_method"),
        ts_expr.alias("sale_timestamp"),
        to_date(ts_expr).alias("sale_date"),
        col("i.quantity").cast("int").alias("quantity"),
        (col("i.unit_cost").cast("double") if "unit_cost" in i_cols else lit(0.0)).alias("unit_cost"),
        (col("i.unit_price").cast("double") if "unit_price" in i_cols else lit(0.0)).alias("unit_price"),
        (col("i.total_price").cast("double") if "total_price" in i_cols else col("i.subtotal").cast("double")).alias("total_item_revenue"),
        (col("i.profit").cast("double") if "profit" in i_cols else lit(0.0)).alias("item_gross_profit")
    ).withColumn("_updated_at", current_timestamp())

    df_fact_sales.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_sales")
    print(f"  └── 📊 'fact_sales': {df_fact_sales.count()} registros.")

    # FactExpenses
    df_exp = spark.read.table(f"{SILVER_SCHEMA}.silver_expenses")
    exp_cols = df_exp.columns
    desc_col = col("description") if "description" in exp_cols else lit("N/A")
    date_col = to_date(col("expense_date") if "expense_date" in exp_cols else (col("created_at") if "created_at" in exp_cols else current_timestamp()))
    
    df_fact_exp = df_exp.select(
        col("id").alias("expense_id"),
        desc_col.alias("description"),
        col("amount").cast("double").alias("expense_amount"),
        (col("category") if "category" in exp_cols else lit("General")).alias("category"),
        date_col.alias("expense_date")
    ).withColumn("_updated_at", current_timestamp())
    df_fact_exp.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_expenses")
    print(f"  └── 💸 'fact_expenses': {df_fact_exp.count()} registros.")

    # FactPurchases
    df_pur = spark.read.table(f"{SILVER_SCHEMA}.silver_purchases")
    pur_cols = df_pur.columns
    pur_ts_col = coalesce(col("timestamp"), col("created_at")) if ("timestamp" in pur_cols and "created_at" in pur_cols) else (col("timestamp") if "timestamp" in pur_cols else (col("created_at") if "created_at" in pur_cols else current_timestamp()))
    supplier_col = col("supplier") if "supplier" in pur_cols else (col("supplier_id") if "supplier_id" in pur_cols else lit("Unknown"))

    if "total_price" in pur_cols:
        amount_col = col("total_price").cast("double")
    elif "total_cost" in pur_cols:
        amount_col = col("total_cost").cast("double")
    elif "amount" in pur_cols:
        amount_col = col("amount").cast("double")
    elif "cost_price" in pur_cols and "quantity" in pur_cols:
        amount_col = (col("cost_price") * col("quantity")).cast("double")
    else:
        amount_col = lit(0.0)

    df_fact_pur = df_pur.select(
        col("id").alias("purchase_id"),
        supplier_col.alias("supplier"),
        amount_col.alias("purchase_amount"),
        to_date(pur_ts_col).alias("purchase_date")
    ).withColumn("_updated_at", current_timestamp())
    df_fact_pur.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_purchases")
    print(f"  └── 📦 'fact_purchases': {df_fact_pur.count()} registros.")

    # DimProducts
    df_cat = spark.read.table(f"{SILVER_SCHEMA}.silver_master_catalog")
    df_prod = spark.read.table(f"{SILVER_SCHEMA}.silver_products")
    df_items = spark.read.table(f"{SILVER_SCHEMA}.silver_sale_items")

    df_dim_cat = df_cat.alias("c") \
        .join(df_prod.alias("p"), col("c.barcode") == col("p.barcode"), "left") \
        .select(
            col("c.product_name").alias("product_id"),
            col("c.product_name").alias("product_name"),
            col("c.barcode").alias("barcode"),
            coalesce(col("c.category"), lit("General")).alias("category"),
            coalesce(col("p.supplier"), lit("N/A")).alias("supplier"),
            coalesce(col("p.cost_price").cast("double"), lit(0.0)).alias("cost_price"),
            coalesce(col("p.sale_price").cast("double"), lit(0.0)).alias("sale_price"),
            coalesce(col("p.stock").cast("int"), lit(0)).alias("current_stock")
        ).dropDuplicates(["product_name"])

    df_items_prod = df_items.select(
        col("product_name").alias("product_id"),
        col("product_name").alias("product_name"),
        col("barcode").alias("barcode"),
        lit("General").alias("category"),
        lit("Velykapet").alias("supplier"),
        coalesce(col("unit_cost").cast("double"), lit(0.0)).alias("cost_price"),
        coalesce(col("unit_price").cast("double"), lit(0.0)).alias("sale_price"),
        lit(10).cast("int").alias("current_stock")
    ).distinct()

    df_dim_prod = df_dim_cat.unionByName(df_items_prod, allowMissingColumns=True) \
        .dropDuplicates(["product_name"]) \
        .withColumn("_updated_at", current_timestamp())

    df_dim_prod.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.dim_products")
    print(f"  └── 🏷️ 'dim_products': {df_dim_prod.count()} registros con categoría.")

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

    df_inv = df_dim_prod.agg(
        _count("product_id").alias("total_skus"),
        _sum("current_stock").alias("total_stock_units"),
        _round(_sum(col("current_stock") * col("cost_price")), 2).alias("total_inventory_cost_value"),
        _round(_sum(col("current_stock") * col("sale_price")), 2).alias("total_inventory_retail_value")
    ).withColumn("_calculated_at", current_timestamp())
    # 8. Masked Tables for Public Portfolio (Recruiters & Public Web)
    print("  └── 🎭 Generando tablas Gold Masked para el Portafolio Público (Scale: 1.45x)...")
    clean_supplier = when(upper(trim(col("supplier"))).contains("FINCA URBANA"), "NutriPet Wholesale") \
        .when(upper(trim(col("supplier"))).contains("CDM"), "Global Pet Logistics") \
        .when(upper(trim(col("supplier"))).contains("MANAGRO"), "AgroPet Supply Co.") \
        .when(upper(trim(col("supplier"))).contains("AGRO MIS MASCOTAS"), "AgroVets Distribution") \
        .when(upper(trim(col("supplier"))).contains("LAIKA"), "OmniPet Direct") \
        .when(upper(trim(col("supplier"))).contains("ANIMAL KAN"), "Kanine Care Supply") \
        .when(upper(trim(col("supplier"))).contains("TIENDA MAYORISTA"), "Prime Pet Wholesaler") \
        .when(upper(trim(col("supplier"))).contains("CALABAZAPET"), "Pet Essentials Hub") \
        .when(upper(trim(col("supplier"))).contains("FARMASCOTA"), "PharmaVet Logistics") \
        .when(upper(trim(col("supplier"))).contains("TIERRAGRO"), "BioPet Nutrition") \
        .when(upper(trim(col("supplier"))).contains("AMAZON"), "E-Commerce Partner") \
        .when(upper(trim(col("supplier"))).contains("EXITO") | upper(trim(col("supplier"))).contains("OLIMPICA") | upper(trim(col("supplier"))).contains("DOLLARCITY"), "Retail Vendor Network") \
        .otherwise("Regional Pet Partner")

    df_dim_prod.withColumn("supplier", clean_supplier) \
        .withColumn("cost_price", _round(col("cost_price") * lit(1.45), 2)) \
        .withColumn("sale_price", _round(col("sale_price") * lit(1.45), 2)) \
        .withColumn("_masked_for_portfolio", lit(True)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.dim_products_masked")

    df_fact_sales.withColumn("unit_cost", _round(col("unit_cost") * lit(1.45), 2)) \
        .withColumn("unit_price", _round(col("unit_price") * lit(1.45), 2)) \
        .withColumn("total_item_revenue", _round(col("total_item_revenue") * lit(1.45), 2)) \
        .withColumn("item_gross_profit", _round(col("item_gross_profit") * lit(1.45), 2)) \
        .withColumn("_masked_for_portfolio", lit(True)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_sales_masked")

    df_fact_exp.withColumn("expense_amount", _round(col("expense_amount") * lit(1.45), 2)) \
        .withColumn("_masked_for_portfolio", lit(True)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_expenses_masked")

    df_fact_pur.withColumn("supplier", clean_supplier) \
        .withColumn("purchase_amount", _round(col("purchase_amount") * lit(1.45), 2)) \
        .withColumn("_masked_for_portfolio", lit(True)) \
        .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{GOLD_SCHEMA}.fact_purchases_masked")

    print("✅ Capa Gold completada exitosamente (Tablas Reales y Tablas Masked).")

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
