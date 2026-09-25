-- Fabric notebook source

-- METADATA ********************

-- META {
-- META   "kernel_info": {
-- META     "name": "synapse_pyspark"
-- META   },
-- META   "dependencies": {
-- META     "lakehouse": {
-- META       "default_lakehouse": "86204f05-6d46-4c76-a76d-9cb8a5fa5cb6",
-- META       "default_lakehouse_name": "lh_practice_smash_interview",
-- META       "default_lakehouse_workspace_id": "cfeefa92-730d-43b2-b2b1-9c46826d5807",
-- META       "known_lakehouses": [
-- META         {
-- META           "id": "86204f05-6d46-4c76-a76d-9cb8a5fa5cb6"
-- META         }
-- META       ]
-- META     }
-- META   }
-- META }

-- CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

# Simulamos la ingesta cruda que llega al Lakehouse
raw_transactions_data = [
    # (tx_id, loan_id, member_id, branch_id, tx_date, tx_type, tx_amount, source_file)
    ("TX1001", "L-901", "M101", "BR-01", "2023-06-01", "PAYMENT", "450.00", "core_batch_20230601.csv"),
    ("TX1002", "L-902", "M102", "BR-02", "2023-06-01", "DISBURSEMENT", "15000.00", "core_batch_20230601.csv"),
    ("TX1003", "L-903", "M103", "BR-01", "2023-06-01", "payment", "320.50", "core_batch_20230601.csv"),
    # DUPLICADO EXACTO de TX1001 (reintento del pipeline de origen):
    ("TX1001", "L-901", "M101", "BR-01", "2023-06-01", "PAYMENT", "450.00", "core_batch_20230601_retry.csv"),
    # Transacción con monto corrupto / inválido:
    ("TX1004", "L-904", "M105", "BR-03", "2023-06-01", "FEE", "-25.00", "core_batch_20230601.csv"),
    # Transacción con tipo nulo / espacio:
    ("TX1005", "L-905", "M101", "BR-01", "2023-06-01", "  ", "100.00", "core_batch_20230601.csv"),
]

raw_tx_schema = StructType([
    StructField("raw_tx_id", StringType(), True),
    StructField("raw_loan_id", StringType(), True),
    StructField("raw_member_id", StringType(), True),
    StructField("raw_branch_id", StringType(), True),
    StructField("raw_tx_date", StringType(), True),
    StructField("raw_tx_type", StringType(), True),
    StructField("raw_tx_amount", StringType(), True),
    StructField("_source_file", StringType(), True)
])

df_landing_tx = spark.createDataFrame(data=raw_transactions_data, schema=raw_tx_schema)
display(df_landing_tx)



-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

df_silver_adding_columns = (
    df_landing_tx
    .withColumn("_Ingestion_Timestamp",F.current_timestamp())
)
display(df_silver_adding_columns)

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DateType, DecimalType
from datetime import date
from decimal import Decimal
# 1. Customers
customers_data = [
    (1, "Alice Smith", "New York", date(2023, 1, 15)),
    (2, "Bob Jones", "Chicago", date(2023, 2, 20)),
    (3, "Charlie Brown", "Los Angeles", date(2023, 3, 5)),
    (4, "Diana Prince", "New York", date(2023, 4, 12)),
    (5, "Evan Wright", "Austin", date(2023, 5, 18)),
]
customers_schema = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("name", StringType(), True),
    StructField("city", StringType(), True),
    StructField("signup_date", DateType(), True),
])
df_customers = spark.createDataFrame(customers_data, customers_schema)
df_customers.write.format("delta").mode("overwrite").saveAsTable("customers")
# 2. Products
products_data = [
    (101, "Wireless Mouse", "Electronics"),
    (102, "Mechanical Keyboard", "Electronics"),
    (103, "Office Desk Chair", "Furniture"),
    (104, "Standing Desk", "Furniture"),
    (105, "USB-C Cable", "Accessories"),
    (106, "Coffee Mug", "Accessories"),
]
products_schema = StructType([
    StructField("product_id", IntegerType(), False),
    StructField("product_name", StringType(), True),
    StructField("category", StringType(), True),
])
df_products = spark.createDataFrame(products_data, products_schema)
df_products.write.format("delta").mode("overwrite").saveAsTable("products")
# 3. Orders
orders_data = [
    (1001, 1, date(2023, 6, 1), "completed"),
    (1002, 2, date(2023, 6, 2), "completed"),
    (1003, 1, date(2023, 6, 5), "cancelled"),
    (1004, 3, date(2023, 6, 10), "completed"),
    (1005, 4, date(2023, 6, 12), "pending"),
    (1006, 2, date(2023, 6, 15), "completed"),
    (1007, 5, date(2023, 6, 18), "cancelled"),
]
orders_schema = StructType([
    StructField("order_id", IntegerType(), False),
    StructField("customer_id", IntegerType(), False),
    StructField("order_date", DateType(), True),
    StructField("status", StringType(), True),
])
df_orders = spark.createDataFrame(orders_data, orders_schema)
df_orders.write.format("delta").mode("overwrite").saveAsTable("orders")
# 4. Order Items
order_items_data = [
    (1, 1001, 101, 2, Decimal("25.00")),
    (2, 1001, 102, 1, Decimal("75.00")),
    (3, 1002, 103, 1, Decimal("150.00")),
    (4, 1003, 105, 3, Decimal("12.00")),
    (5, 1004, 104, 1, Decimal("300.00")),
    (6, 1004, 102, 1, Decimal("75.00")),
    (7, 1005, 106, 4, Decimal("15.00")),
    (8, 1006, 101, 1, Decimal("25.00")),
    (9, 1006, 105, 2, Decimal("12.00")),
    (10, 1007, 103, 1, Decimal("150.00")),
]
order_items_schema = StructType([
    StructField("order_item_id", IntegerType(), False),
    StructField("order_id", IntegerType(), False),
    StructField("product_id", IntegerType(), False),
    StructField("quantity", IntegerType(), True),
    StructField("unit_price", DecimalType(10, 2), True),
])
df_order_items = spark.createDataFrame(order_items_data, order_items_schema)
df_order_items.write.format("delta").mode("overwrite").saveAsTable("order_items")
print("All 4 tables created and saved as Delta tables successfully!")

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark",
-- META   "frozen": false,
-- META   "editable": true
-- META }

-- CELL ********************

-- MAGIC %%sql 
-- MAGIC SELECT
-- MAGIC c.name, 
-- MAGIC c.city,
-- MAGIC COUNT(*) AS completed_orders
-- MAGIC FROM customers c
-- MAGIC LEFT JOIN orders o ON  
-- MAGIC c.customer_id=o.customer_id AND o.status = 'completed'
-- MAGIC --WHERE o.status = 'completed'
-- MAGIC GROUP BY c.name, c.city;
-- MAGIC 
-- MAGIC 
-- MAGIC 
-- MAGIC 
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql 
-- MAGIC SELECT * FROM orders

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql
-- MAGIC SELECT * FROM customers

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql
-- MAGIC SELECT * FROM order_items

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql 
-- MAGIC SELECT * FROM products

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql 
-- MAGIC SELECT 
-- MAGIC     p.category,
-- MAGIC     ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
-- MAGIC FROM products p      
-- MAGIC JOIN order_items oi ON p.product_id = oi.product_id
-- MAGIC JOIN orders o ON oi.order_id = o.order_id
-- MAGIC WHERE o.status = 'completed'
-- MAGIC GROUP BY p.category
-- MAGIC ORDER BY revenue DESC

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql
-- MAGIC SELECT
-- MAGIC     c.name,
-- MAGIC     o.order_date,
-- MAGIC     row_number() OVER (PARTITION BY c.customer_id ORDER BY o.order_date DESC) as rank_orders 
-- MAGIC FROM customers c 
-- MAGIC LEFT JOIN orders o ON c.customer_id=o.customer_id AND o.status='completed'


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql 
-- MAGIC SELECT 
-- MAGIC     p.product_name,
-- MAGIC     count(o.order_id) times_ordered
-- MAGIC FROM    
-- MAGIC     products p
-- MAGIC LEFT JOIN order_items oi ON 
-- MAGIC     p.product_id=oi.product_id
-- MAGIC LEFT JOIN orders o ON oi.order_id=o.order_id AND o.status= 'completed'
-- MAGIC GROUP BY p.product_name

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%sql 
-- MAGIC WITH revenue_products AS(
-- MAGIC SELECT
-- MAGIC     p.category,
-- MAGIC     p.product_name,
-- MAGIC     sum(oi.quantity * oi.unit_price) revenue_per_product
-- MAGIC FROM
-- MAGIC     products p 
-- MAGIC LEFT JOIN 
-- MAGIC     order_items oi ON p.product_id=oi.product_id
-- MAGIC LEFT JOIN
-- MAGIC     orders o ON oi.order_id=o.order_id AND o.status= 'completed'
-- MAGIC GROUP BY p.category, p.product_name
-- MAGIC ),
-- MAGIC rank_products AS(
-- MAGIC SELECT
-- MAGIC     rp.category,
-- MAGIC     rp.product_name,
-- MAGIC     rp.revenue_per_product,
-- MAGIC     rank() OVER (PARTITION BY rp.category ORDER BY rp.revenue_per_product DESC) as ranking_products
-- MAGIC FROM 
-- MAGIC     revenue_products rp 
-- MAGIC )
-- MAGIC SELECT
-- MAGIC     rnp.category,
-- MAGIC     rnp.product_name,
-- MAGIC     rnp.revenue_per_product,
-- MAGIC     rnp.ranking_products
-- MAGIC FROM
-- MAGIC     rank_products rnp
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

SELECT 
    c1.city,
    c1.name,
    c2.name
FROM
    customers c1
INNER JOIN
    customers c2 ON c1.customer_id<c2.customer_id AND c1.city=c2.city

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

SELECT * FROM orders
WHERE status LIKE '%d'

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }
