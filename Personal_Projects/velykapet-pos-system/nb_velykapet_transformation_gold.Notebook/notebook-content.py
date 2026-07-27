# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "9316cdc2-2907-455e-bee8-87f5ce154663",
# META       "default_lakehouse_name": "lh_velykapet_gold_dev",
# META       "default_lakehouse_workspace_id": "44037812-2812-42bd-8ee4-1d0412816215",
# META       "known_lakehouses": [
# META         {
# META           "id": "9316cdc2-2907-455e-bee8-87f5ce154663"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Print actual schemas for all silver tables
tables = [
    "silver_sales", "silver_sale_items", "silver_master_catalog",
    "silver_products", "silver_purchases", "silver_expenses",
    "silver_devolutions", "silver_devolution_items", "silver_stock"
]

for t in tables:
    df = spark.read.table(f"lh_velykapet_silver_dev.dbo.{t}")
    print(f"--- {t} ---")
    print(df.columns)
    print()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

# 1. Read cleaned Silver tables from lh_velykapet_silver_dev
df_sales = spark.read.table("lh_velykapet_silver_dev.dbo.silver_sales")
df_sale_items = spark.read.table("lh_velykapet_silver_dev.dbo.silver_sale_items")
df_master_catalog = spark.read.table("lh_velykapet_silver_dev.dbo.silver_master_catalog")
df_products = spark.read.table("lh_velykapet_silver_dev.dbo.silver_products")
df_purchases = spark.read.table("lh_velykapet_silver_dev.dbo.silver_purchases")
df_expenses = spark.read.table("lh_velykapet_silver_dev.dbo.silver_expenses")
df_devolutions = spark.read.table("lh_velykapet_silver_dev.dbo.silver_devolutions")
df_devolution_items = spark.read.table("lh_velykapet_silver_dev.dbo.silver_devolution_items")
df_stock = spark.read.table("lh_velykapet_silver_dev.dbo.silver_stock")

# Create Temp Views
df_sales.createOrReplaceTempView("silver_sales")
df_sale_items.createOrReplaceTempView("silver_sale_items")
df_master_catalog.createOrReplaceTempView("silver_master_catalog")
df_products.createOrReplaceTempView("silver_products")
df_purchases.createOrReplaceTempView("silver_purchases")
df_expenses.createOrReplaceTempView("silver_expenses")
df_devolutions.createOrReplaceTempView("silver_devolutions")
df_devolution_items.createOrReplaceTempView("silver_devolution_items")
df_stock.createOrReplaceTempView("silver_stock")

# -----------------------------------------------------------------------------
# 1. dim_products (Combining master_catalog, products metadata, and stock)
# -----------------------------------------------------------------------------
spark.sql("""
WITH product_base AS (
    SELECT 
        p.barcode,
        p.product_name,
        p.category
    FROM silver_master_catalog p
),
product_details AS (
    SELECT 
        barcode,
        FIRST(supplier) AS supplier,
        FIRST(cost_price) AS cost_price,
        FIRST(sale_price) AS standard_sale_price,
        FIRST(rappi_price) AS rappi_price
    FROM silver_products
    GROUP BY barcode
)
SELECT 
    b.barcode,
    b.product_name,
    b.category,
    COALESCE(d.supplier, 'N/A') AS supplier,
    COALESCE(d.cost_price, 0) AS cost_price,
    COALESCE(d.standard_sale_price, 0) AS standard_sale_price,
    COALESCE(d.rappi_price, 0) AS rappi_price,
    (COALESCE(d.standard_sale_price, 0) - COALESCE(d.cost_price, 0)) AS standard_unit_margin,
    CASE 
        WHEN COALESCE(d.standard_sale_price, 0) > 0 
        THEN ROUND(((d.standard_sale_price - d.cost_price) / d.standard_sale_price) * 100, 2) 
        ELSE 0 
    END AS standard_margin_pct,
    COALESCE(s.calculated_stock, 0) AS current_stock_qty,
    COALESCE(s.total_purchased, 0) AS total_purchased_qty,
    COALESCE(s.total_sold, 0) AS total_sold_qty,
    COALESCE(s.total_returned, 0) AS total_returned_qty
FROM product_base b
LEFT JOIN product_details d ON b.barcode = d.barcode
LEFT JOIN silver_stock s ON b.barcode = s.barcode
""").write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_gold_dev.dbo.dim_products")

# -----------------------------------------------------------------------------
# 2. dim_dates
# -----------------------------------------------------------------------------
spark.sql("""
WITH date_range AS (
    SELECT sequence(to_date('2024-01-01'), to_date('2030-12-31'), interval 1 day) AS date_array
),
exploded_dates AS (
    SELECT explode(date_array) AS date_key FROM date_range
)
SELECT 
    date_key,
    year(date_key) AS year,
    quarter(date_key) AS quarter,
    month(date_key) AS month_number,
    date_format(date_key, 'MMMM') AS month_name,
    date_format(date_key, 'yyyy-MM') AS year_month,
    day(date_key) AS day_of_month,
    dayofweek(date_key) AS day_of_week,
    date_format(date_key, 'EEEE') AS day_name,
    CASE WHEN dayofweek(date_key) IN (1, 7) THEN true ELSE false END AS is_weekend
FROM exploded_dates
""").write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_gold_dev.dbo.dim_dates")

# -----------------------------------------------------------------------------
# 3. fact_sales
# -----------------------------------------------------------------------------
spark.sql("""
SELECT 
    s.id AS sale_id,
    s.local_id,
    CAST(s.timestamp AS DATE) AS date_key,
    s.timestamp AS sale_timestamp,
    COALESCE(s.origin, 'In-Store') AS sales_channel,
    s.payment_method,
    s.sale_type,
    s.invoice_number,
    s.transaction_code,
    s.total_amount AS total_revenue,
    s.delivery_tower,
    s.delivery_apartment,
    s.delivery_complex,
    s.notes
FROM silver_sales s
""").write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_gold_dev.dbo.fact_sales")

# -----------------------------------------------------------------------------
# 4. fact_sale_items (INNER JOIN guarantees ZERO orphaned rows)
# -----------------------------------------------------------------------------
spark.sql("""
SELECT 
    si.id AS sale_item_id,
    si.sale_id,
    si.barcode,
    si.product_name,
    si.quantity,
    si.unit_cost,
    si.unit_price,
    si.total_cost,
    si.total_price AS total_revenue,
    si.profit AS gross_profit,
    si.returned_quantity,
    COALESCE(s.origin, 'In-Store') AS sales_channel,
    CAST(s.timestamp AS DATE) AS date_key
FROM silver_sale_items si
INNER JOIN silver_sales s ON si.sale_id = s.id
""").write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_gold_dev.dbo.fact_sale_items")

# -----------------------------------------------------------------------------
# 5. fact_expenses
# -----------------------------------------------------------------------------
spark.sql("""
SELECT 
    e.id AS expense_id,
    CAST(e.timestamp AS DATE) AS date_key,
    e.timestamp AS expense_timestamp,
    e.description,
    e.amount,
    e.payment_method,
    e.notes,
    CASE 
        WHEN LOWER(e.category) LIKE '%marketing%' OR LOWER(e.description) LIKE '%marketing%' OR LOWER(e.description) LIKE '%publicidad%' OR LOWER(e.description) LIKE '%ads%' THEN 'Marketing'
        WHEN LOWER(e.category) LIKE '%rappi%' OR LOWER(e.description) LIKE '%rappi%' OR LOWER(e.description) LIKE '%comision%' THEN 'Channel Commission'
        WHEN LOWER(e.category) LIKE '%arriendo%' OR LOWER(e.description) LIKE '%rent%' THEN 'Rent'
        ELSE COALESCE(e.category, 'Other Operational')
    END AS expense_category
FROM silver_expenses e
""").write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_gold_dev.dbo.fact_expenses")

# -----------------------------------------------------------------------------
# 6. fact_purchases
# -----------------------------------------------------------------------------
spark.sql("""
SELECT 
    p.id AS purchase_id,
    p.local_id,
    p.barcode,
    p.supplier,
    p.quantity,
    p.cost_price AS unit_cost,
    p.total_price AS total_cost,
    p.status,
    p.lot_reference,
    p.notes,
    p.timestamp AS purchase_timestamp,
    CAST(p.timestamp AS DATE) AS date_key
FROM silver_purchases p
""").write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_gold_dev.dbo.fact_purchases")

# -----------------------------------------------------------------------------
# 7. fact_devolution_items
# -----------------------------------------------------------------------------
spark.sql("""
SELECT 
    di.id AS devolution_item_id,
    di.devolution_id,
    di.sale_item_id,
    di.barcode,
    di.product_name,
    di.quantity AS returned_quantity,
    di.unit_cost,
    di.unit_price,
    di.total_refund,
    d.devolution_number,
    d.refund_method,
    d.reason AS return_reason,
    CAST(d.timestamp AS DATE) AS date_key
FROM silver_devolution_items di
LEFT JOIN silver_devolutions d ON di.devolution_id = d.id
""").write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_gold_dev.dbo.fact_devolution_items")

print("🏆 Gold Star Schema tables built 100% cleanly in lh_velykapet_gold_dev!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(spark.sql("""
SELECT
    (SELECT COUNT(*) FROM lh_velykapet_gold_dev.dbo.fact_sales) AS total_sales_transactions,
    (SELECT SUM(total_revenue) FROM lh_velykapet_gold_dev.dbo.fact_sales) AS header_revenue,
    (SELECT SUM(total_revenue) FROM lh_velykapet_gold_dev.dbo.fact_sale_items) AS line_item_revenue,
    (SELECT SUM(amount) FROM lh_velykapet_gold_dev.dbo.fact_expenses) AS total_expenses
"""))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
