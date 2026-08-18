-- ===============================================================================
-- Esquemas DDL Esperados - Capa Gold (Data Warehouse & KPIs Analíticos)
-- Lakehouse/Warehouse: lh_velykapet_gold_dev.dbo
-- ===============================================================================

-- 1. Tablas de Hechos (Fact Tables)
CREATE TABLE IF NOT EXISTS lh_velykapet_gold_dev.dbo.fact_sales (
    item_id STRING NOT NULL,
    sale_id STRING NOT NULL,
    product_id STRING NOT NULL,
    sale_origin STRING,
    payment_method STRING,
    sale_timestamp TIMESTAMP,
    sale_date DATE,
    product_name STRING,
    quantity INT,
    unit_cost DOUBLE,
    unit_price DOUBLE,
    total_item_revenue DOUBLE,
    item_gross_profit DOUBLE,
    _updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_gold_dev.dbo.fact_expenses (
    expense_id STRING NOT NULL,
    description STRING,
    expense_amount DOUBLE,
    category STRING,
    expense_date DATE,
    _updated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_gold_dev.dbo.fact_purchases (
    purchase_id STRING NOT NULL,
    supplier STRING,
    purchase_amount DOUBLE,
    purchase_date DATE,
    _updated_at TIMESTAMP
) USING DELTA;

-- 2. Tablas de Dimensiones (Dimension Tables)
CREATE TABLE IF NOT EXISTS lh_velykapet_gold_dev.dbo.dim_products (
    product_id STRING NOT NULL,
    product_name STRING,
    barcode STRING,
    supplier STRING,
    cost_price DOUBLE,
    sale_price DOUBLE,
    current_stock INT,
    _updated_at TIMESTAMP
) USING DELTA;

-- 3. Tablas de KPIs (Executive Summaries)
CREATE TABLE IF NOT EXISTS lh_velykapet_gold_dev.dbo.kpi_daily_sales_trend (
    sale_date DATE NOT NULL,
    total_transactions BIGINT,
    total_units_sold BIGINT,
    gross_revenue DOUBLE,
    gross_profit DOUBLE,
    _calculated_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_gold_dev.dbo.kpi_inventory_health (
    total_skus BIGINT,
    total_stock_units BIGINT,
    total_inventory_cost_value DOUBLE,
    total_inventory_retail_value DOUBLE,
    _calculated_at TIMESTAMP
) USING DELTA;
