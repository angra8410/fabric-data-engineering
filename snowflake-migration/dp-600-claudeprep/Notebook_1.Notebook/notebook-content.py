# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "5a1c0148-1c53-4d0b-94d0-f2d54ce4cae0",
# META       "default_lakehouse_name": "PracticeLH",
# META       "default_lakehouse_workspace_id": "cfeefa92-730d-43b2-b2b1-9c46826d5807",
# META       "known_lakehouses": [
# META         {
# META           "id": "5a1c0148-1c53-4d0b-94d0-f2d54ce4cae0"
# META         }
# META       ]
# META     },
# META     "warehouse": {
# META       "known_warehouses": []
# META     }
# META   }
# META }

# CELL ********************

df = spark.read.table("dbo.Customers")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pyspark.sql.functions as F

df.groupBy("CustomerID") \
.agg(F.count("CustomerID").alias("TotalPedidos")) \
.sort("TotalPedidos", ascending=False) \
.show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

spark.read.table("orders")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pyspark.sql.functions as F

df.groupBy("CustomerID")\
.agg(F.count("CustomerID").alias("TotalOrders")) \
.sort("TotalOrders", ascending=False) \
.show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df.groupBy("CustomerID").count().sort("count", ascending=False).show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df.describe().show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT * FROM orders

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT 
# MAGIC     OrderID, 
# MAGIC     CustomerID, 
# MAGIC     OrderTotal, 
# MAGIC     OrderDate
# MAGIC FROM dbo.Orders
# MAGIC WHERE MONTH(OrderDate) = 1 AND YEAR(OrderDate) = 2024;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT 
# MAGIC     c.Name,
# MAGIC     c.Region,
# MAGIC     o.OrderTotal,
# MAGIC     o.OrderDate
# MAGIC FROM Customers c 
# MAGIC LEFT JOIN Orders o 
# MAGIC ON c.CustomerID=o.CustomerID
# MAGIC WHERE month(o.OrderDate)= 1 AND YEAR(o.OrderDate) = 2024 AND o.OrderID IS NULL

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
