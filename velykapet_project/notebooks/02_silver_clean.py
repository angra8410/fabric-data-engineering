"""
===============================================================================
Velykapet Data Engineering Pipeline - Capa Silver (Inicialización a Cero)
===============================================================================
Descripción:
  Script PySpark para Microsoft Fabric.
  - Mantiene las 9 tablas activas del negocio (Ventas, Catálogo, Gastos, Compras).
  - Inicializa a CERO (0 registros) todas las tablas del Bot de WhatsApp y Backlog
    (whatsapp_orders, whatsapp_order_items, processed_whatsapp_messages, 
     whatsapp_contacts, demand_backlog, customer_last_search, customer_cart)
    para limpiar datos de pruebas anteriores y dejar un baseline limpio para la salida a producción.
===============================================================================
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp

spark = SparkSession.builder \
    .appName("Velykapet_Silver_Clean_Initialization") \
    .getOrCreate()

print("📥 Leyendo tablas desde 'lh_velykapet_bronze_dev.public'...")

# 1. Tablas Activas del Negocio POS
df_sales = spark.read.table("lh_velykapet_bronze_dev.public.sales")
df_sale_items = spark.read.table("lh_velykapet_bronze_dev.public.sale_items")
df_products = spark.read.table("lh_velykapet_bronze_dev.public.products")
df_master_catalog = spark.read.table("lh_velykapet_bronze_dev.public.master_catalog")
df_purchases = spark.read.table("lh_velykapet_bronze_dev.public.purchases")
df_expenses = spark.read.table("lh_velykapet_bronze_dev.public.expenses")
df_devolutions = spark.read.table("lh_velykapet_bronze_dev.public.devolutions")
df_devolution_items = spark.read.table("lh_velykapet_bronze_dev.public.devolution_items")
df_stock = spark.read.table("lh_velykapet_bronze_dev.public.v_product_stock")

# 2. Tablas del Bot de WhatsApp & Comportamiento (Filtro 1=0 para inicializar en CERO registros)
df_whatsapp_orders = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_orders").filter("1 = 0")
df_whatsapp_order_items = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_order_items").filter("1 = 0")
df_processed_whatsapp = spark.read.table("lh_velykapet_bronze_dev.public.processed_whatsapp_messages").filter("1 = 0")
df_whatsapp_contacts = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_contacts").filter("1 = 0")
df_demand_backlog = spark.read.table("lh_velykapet_bronze_dev.public.demand_backlog").filter("1 = 0")
df_customer_search = spark.read.table("lh_velykapet_bronze_dev.public.customer_last_search").filter("1 = 0")
df_customer_cart = spark.read.table("lh_velykapet_bronze_dev.public.customer_cart").filter("1 = 0")

tables_map = {
    # Tablas Core POS
    "silver_sales": df_sales,
    "silver_sale_items": df_sale_items,
    "silver_products": df_products,
    "silver_master_catalog": df_master_catalog,
    "silver_purchases": df_purchases,
    "silver_expenses": df_expenses,
    "silver_devolutions": df_devolutions,
    "silver_devolution_items": df_devolution_items,
    "silver_stock": df_stock,
    
    # Tablas de WhatsApp & Backlog (Inicializadas en 0)
    "silver_whatsapp_orders": df_whatsapp_orders,
    "silver_whatsapp_order_items": df_whatsapp_order_items,
    "silver_processed_whatsapp_messages": df_processed_whatsapp,
    "silver_whatsapp_contacts": df_whatsapp_contacts,
    "silver_demand_backlog": df_demand_backlog,
    "silver_customer_last_search": df_customer_search,
    "silver_customer_cart": df_customer_cart
}

print("🚀 Escribiendo tablas en Silver ('lh_velykapet_silver_dev.dbo')...")

for target_table, df in tables_map.items():
    full_target = f"lh_velykapet_silver_dev.dbo.{target_table}"
    df_clean = df.withColumn("_processed_at", current_timestamp())
    
    df_clean.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(full_target)
        
    print(f"  └── 📊 {target_table} -> {df_clean.count()} registros (limpio).")

print("✅ Tablas Silver escritas exitosamente (WhatsApp y Backlog inicializadas en 0 registros).")
