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
# META         },
# META         {
# META           "id": "0e61ae20-b07e-4fde-9ae3-017c07caace2"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

"""
===============================================================================
Velykapet Data Engineering Pipeline - Capa Silver (Bronze -> Silver Completo)
===============================================================================
Descripción:
  Script PySpark para Microsoft Fabric.
  Lee las 16 tablas crudas desde 'lh_velykapet_bronze_dev.public.<tabla>' y
  escribe las 16 tablas procesadas y estandarizadas en 'lh_velykapet_silver_dev.dbo.silver_<tabla>'.

Mapeo completo de Origen (Bronze public) -> Destino (Silver dbo):
  1. sales                       -> silver_sales
  2. sale_items                  -> silver_sale_items
  3. master_catalog               -> silver_master_catalog
  4. products                     -> silver_products
  5. purchases                    -> silver_purchases
  6. expenses                     -> silver_expenses
  7. devolutions                  -> silver_devolutions
  8. devolution_items             -> silver_devolution_items
  9. v_product_stock              -> silver_stock
 10. whatsapp_orders             -> silver_whatsapp_orders
 11. whatsapp_order_items        -> silver_whatsapp_order_items
 12. processed_whatsapp_messages -> silver_processed_whatsapp_messages
 13. whatsapp_contacts           -> silver_whatsapp_contacts
 14. demand_backlog               -> silver_demand_backlog
 15. customer_last_search        -> silver_customer_last_search
 16. customer_cart                -> silver_customer_cart
===============================================================================
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp

spark = SparkSession.builder \
    .appName("Velykapet_Silver_Transformation") \
    .getOrCreate()

# 1. Leer las 16 tablas Bronze desde 'lh_velykapet_bronze_dev.public'
print("📥 Leyendo las 16 tablas Bronze desde 'lh_velykapet_bronze_dev.public'...")

df_sales = spark.read.table("lh_velykapet_bronze_dev.public.sales")
df_sale_items = spark.read.table("lh_velykapet_bronze_dev.public.sale_items")
df_master_catalog = spark.read.table("lh_velykapet_bronze_dev.public.master_catalog")
df_products = spark.read.table("lh_velykapet_bronze_dev.public.products")
df_purchases = spark.read.table("lh_velykapet_bronze_dev.public.purchases")
df_expenses = spark.read.table("lh_velykapet_bronze_dev.public.expenses")
df_devolutions = spark.read.table("lh_velykapet_bronze_dev.public.devolutions")
df_devolution_items = spark.read.table("lh_velykapet_bronze_dev.public.devolution_items")
df_stock = spark.read.table("lh_velykapet_bronze_dev.public.v_product_stock")

# Tablas de interacción y engagement (WhatsApp & Carrito)
df_whatsapp_orders = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_orders")
df_whatsapp_order_items = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_order_items")
df_processed_whatsapp = spark.read.table("lh_velykapet_bronze_dev.public.processed_whatsapp_messages")
df_whatsapp_contacts = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_contacts")
df_demand_backlog = spark.read.table("lh_velykapet_bronze_dev.public.demand_backlog")
df_customer_search = spark.read.table("lh_velykapet_bronze_dev.public.customer_last_search")
df_customer_cart = spark.read.table("lh_velykapet_bronze_dev.public.customer_cart")

# 2. Mapa completo de las 16 tablas hacia Silver (lh_velykapet_silver_dev.dbo)
print("🚀 Escribiendo las 16 tablas en Silver ('lh_velykapet_silver_dev.dbo')...")

tables_map = {
    "silver_sales": df_sales,
    "silver_sale_items": df_sale_items,
    "silver_master_catalog": df_master_catalog,
    "silver_products": df_products,
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
    
    df_clean.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(full_target)
        
    print(f"  └── 📊 {target_table} -> {df_clean.count()} registros procesados.")

print("✅ All 16 Silver tables populated successfully in lh_velykapet_silver_dev!")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
===============================================================================
Velykapet Data Engineering Pipeline - Capa Silver (16 Tablas Completas + WhatsApp Bot)
===============================================================================
Descripción:
  Script PySpark para Microsoft Fabric.
  Lee las 16 tablas desde 'lh_velykapet_bronze_dev.public.<tabla>' y escribe
  las 16 tablas procesadas en 'lh_velykapet_silver_dev.dbo.silver_<tabla>'.

  Prepara la infraestructura completa para la salida a producción del Bot de WhatsApp.

Tablas Procesadas:
  [Ventas, Catálogo & Operaciones]
  1. sales                       -> silver_sales
  2. sale_items                  -> silver_sale_items
  3. products                     -> silver_products
  4. master_catalog               -> silver_master_catalog
  5. purchases                    -> silver_purchases
  6. expenses                     -> silver_expenses
  7. devolutions                  -> silver_devolutions
  8. devolution_items             -> silver_devolution_items
  9. v_product_stock              -> silver_stock

  [Integración Bot de WhatsApp & Comportamiento]
 10. whatsapp_orders             -> silver_whatsapp_orders
 11. whatsapp_order_items        -> silver_whatsapp_order_items
 12. processed_whatsapp_messages -> silver_processed_whatsapp_messages
 13. whatsapp_contacts           -> silver_whatsapp_contacts
 14. demand_backlog               -> silver_demand_backlog
 15. customer_last_search        -> silver_customer_last_search
 16. customer_cart                -> silver_customer_cart
===============================================================================
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp

spark = SparkSession.builder \
    .appName("Velykapet_Silver_Full_Transformation") \
    .getOrCreate()

print("📥 Leyendo las 16 tablas Bronze desde 'lh_velykapet_bronze_dev.public'...")

df_sales = spark.read.table("lh_velykapet_bronze_dev.public.sales")
df_sale_items = spark.read.table("lh_velykapet_bronze_dev.public.sale_items")
df_products = spark.read.table("lh_velykapet_bronze_dev.public.products")
df_master_catalog = spark.read.table("lh_velykapet_bronze_dev.public.master_catalog")
df_purchases = spark.read.table("lh_velykapet_bronze_dev.public.purchases")
df_expenses = spark.read.table("lh_velykapet_bronze_dev.public.expenses")
df_devolutions = spark.read.table("lh_velykapet_bronze_dev.public.devolutions")
df_devolution_items = spark.read.table("lh_velykapet_bronze_dev.public.devolution_items")
df_stock = spark.read.table("lh_velykapet_bronze_dev.public.v_product_stock")

# WhatsApp Bot & Customer Behavior Tables
df_whatsapp_orders = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_orders")
df_whatsapp_order_items = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_order_items")
df_processed_whatsapp = spark.read.table("lh_velykapet_bronze_dev.public.processed_whatsapp_messages")
df_whatsapp_contacts = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_contacts")
df_demand_backlog = spark.read.table("lh_velykapet_bronze_dev.public.demand_backlog")
df_customer_search = spark.read.table("lh_velykapet_bronze_dev.public.customer_last_search")
df_customer_cart = spark.read.table("lh_velykapet_bronze_dev.public.customer_cart")

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

print("🚀 Escribiendo las 16 tablas en Silver ('lh_velykapet_silver_dev.dbo')...")

for target_table, df in tables_map.items():
    full_target = f"lh_velykapet_silver_dev.dbo.{target_table}"
    df_clean = df.withColumn("_processed_at", current_timestamp())
    
    df_clean.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(full_target)
        
    print(f"  └── 📊 {target_table} -> {df_clean.count()} registros procesados.")

print("✅ Las 16 tablas Silver (incluyendo Bot WhatsApp) procesadas exitosamente!")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
