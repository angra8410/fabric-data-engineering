# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "ddae96c1-6160-478e-871f-1998d698e5c6",
# META       "default_lakehouse_name": "lh_velykapet_bronze_dev",
# META       "default_lakehouse_workspace_id": "44037812-2812-42bd-8ee4-1d0412816215",
# META       "known_lakehouses": [
# META         {
# META           "id": "ddae96c1-6160-478e-871f-1998d698e5c6"
# META         },
# META         {
# META           "id": "c39aad70-5351-4ce5-b36b-3a0249935654"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# 1. Read clean Bronze tables
df_sales = spark.read.table("lh_velykapet_bronze_dev.public.sales")
df_sale_items = spark.read.table("lh_velykapet_bronze_dev.public.sale_items")
df_master_catalog = spark.read.table("lh_velykapet_bronze_dev.public.master_catalog")
df_products = spark.read.table("lh_velykapet_bronze_dev.public.products")
df_purchases = spark.read.table("lh_velykapet_bronze_dev.public.purchases")
df_expenses = spark.read.table("lh_velykapet_bronze_dev.public.expenses")
df_devolutions = spark.read.table("lh_velykapet_bronze_dev.public.devolutions")
df_devolution_items = spark.read.table("lh_velykapet_bronze_dev.public.devolution_items")
df_stock = spark.read.table("lh_velykapet_bronze_dev.public.v_product_stock")

# 2. Write/Overwrite Silver tables in lh_velykapet_silver_dev
df_sales.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_sales")
df_sale_items.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_sale_items")
df_master_catalog.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_master_catalog")
df_products.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_products")
df_purchases.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_purchases")
df_expenses.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_expenses")
df_devolutions.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_devolutions")
df_devolution_items.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_devolution_items")
df_stock.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_stock")

print("✅ Silver tables populated successfully in lh_velykapet_silver_dev!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
