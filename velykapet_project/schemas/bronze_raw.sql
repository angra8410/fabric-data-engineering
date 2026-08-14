-- ===============================================================================
-- Esquemas DDL Esperados - Capa Bronze (PostgreSQL CopyJob -> public)
-- Lakehouse: lh_velykapet_bronze_dev.public
-- ===============================================================================

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.sales (
    id STRING,
    customer_id STRING,
    total_amount STRING,
    payment_method STRING,
    created_at STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.sale_items (
    id STRING,
    sale_id STRING,
    product_id STRING,
    quantity STRING,
    unit_price STRING,
    subtotal STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.master_catalog (
    id STRING,
    sku STRING,
    name STRING,
    category STRING,
    price STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.products (
    id STRING,
    name STRING,
    category STRING,
    price STRING,
    stock STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.purchases (
    id STRING,
    supplier_id STRING,
    amount STRING,
    created_at STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.expenses (
    id STRING,
    description STRING,
    amount STRING,
    category STRING,
    expense_date STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.devolutions (
    id STRING,
    sale_id STRING,
    reason STRING,
    total_refund STRING,
    created_at STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.devolution_items (
    id STRING,
    devolution_id STRING,
    product_id STRING,
    quantity STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_bronze_dev.public.v_product_stock (
    product_id STRING,
    product_name STRING,
    available_stock STRING,
    _ingested_at TIMESTAMP,
    _batch_id STRING
) USING DELTA;
