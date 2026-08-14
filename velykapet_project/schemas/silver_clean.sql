-- ===============================================================================
-- Esquemas DDL Esperados - Capa Silver (16 Tablas Bronze public -> Silver dbo)
-- Lakehouse: lh_velykapet_silver_dev.dbo
-- ===============================================================================

-- 1. Ventas & Transacciones
CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_sales (
    id STRING NOT NULL,
    customer_id STRING,
    total_amount DOUBLE,
    payment_method STRING,
    created_at TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_sale_items (
    id STRING NOT NULL,
    sale_id STRING NOT NULL,
    product_id STRING NOT NULL,
    quantity INT,
    unit_price DOUBLE,
    subtotal DOUBLE,
    _processed_at TIMESTAMP
) USING DELTA;

-- 2. Catálogos & Productos
CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_master_catalog (
    id STRING NOT NULL,
    sku STRING,
    name STRING,
    category STRING,
    price DOUBLE,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_products (
    id STRING NOT NULL,
    name STRING,
    category STRING,
    price DOUBLE,
    stock INT,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_stock (
    product_id STRING NOT NULL,
    product_name STRING,
    available_stock INT,
    _processed_at TIMESTAMP
) USING DELTA;

-- 3. Compras, Gastos & Devoluciones
CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_purchases (
    id STRING NOT NULL,
    supplier_id STRING,
    amount DOUBLE,
    created_at TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_expenses (
    id STRING NOT NULL,
    description STRING,
    amount DOUBLE,
    category STRING,
    expense_date DATE,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_devolutions (
    id STRING NOT NULL,
    sale_id STRING,
    reason STRING,
    total_refund DOUBLE,
    created_at TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_devolution_items (
    id STRING NOT NULL,
    devolution_id STRING,
    product_id STRING,
    quantity INT,
    _processed_at TIMESTAMP
) USING DELTA;

-- 4. Engagement & WhatsApp
CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_whatsapp_orders (
    id STRING NOT NULL,
    customer_phone STRING,
    order_status STRING,
    created_at TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_whatsapp_order_items (
    id STRING NOT NULL,
    whatsapp_order_id STRING,
    product_id STRING,
    quantity INT,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_processed_whatsapp_messages (
    id STRING NOT NULL,
    sender_phone STRING,
    message_body STRING,
    processed_at TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_whatsapp_contacts (
    phone STRING NOT NULL,
    name STRING,
    last_interaction TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

-- 5. Comportamiento & Demanda
CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_demand_backlog (
    id STRING NOT NULL,
    product_name STRING,
    requested_qty INT,
    created_at TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_customer_last_search (
    customer_id STRING NOT NULL,
    search_query STRING,
    search_timestamp TIMESTAMP,
    _processed_at TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS lh_velykapet_silver_dev.dbo.silver_customer_cart (
    cart_id STRING NOT NULL,
    customer_id STRING,
    product_id STRING,
    quantity INT,
    _processed_at TIMESTAMP
) USING DELTA;
