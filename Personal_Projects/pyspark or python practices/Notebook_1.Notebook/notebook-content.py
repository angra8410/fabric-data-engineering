# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "cd23cf30-fd21-42d0-822e-530bdc5993d8",
# META       "default_lakehouse_name": "AdventureWorks_Dev_LH",
# META       "default_lakehouse_workspace_id": "8dee4490-4f0e-468b-9a33-10b32f49df49",
# META       "known_lakehouses": [
# META         {
# META           "id": "cd23cf30-fd21-42d0-822e-530bdc5993d8"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

df = spark.read.table("AdventureWorks_Dev_LH.Sales.SalesOrderHeader")

online_sales = df[(df['OnlineOrderFlag'])== True]

display(online_sales)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.table("AdventureWorks_Dev_LH.Production.Product")

product_weight = df['Weight'] > 10
product_color = df['Color'] == 'Black'

filtered_df = df[product_weight & product_color]

display(filtered_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.table("AdventureWorks_Dev_LH.Production.Product")
weight = df['Weight'] < 10
color = df['Color'] == 'Black'
filtered_df_test = df[weight & color]
display(filtered_df_test)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.table("AdventureWorks_Dev_LH.Person.Person")
filtered_title = df['Title'].isNull()
filtered_name = df['FirstName'] == 'Ken'
filtered_df_test1 = df[filtered_title | filtered_name]
display(filtered_df_test1)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.table("AdventureWorks_Dev_LH.Person.Person")
filtered_title1 = df['Title'].isNotNull()
filtered_name1 = df['FirstName'] == 'Ken'
filtered_df_test2 = df[filtered_title1 & filtered_name1]
display(filtered_df_test2)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.table("AdventureWorks_Dev_LH.Person.Person").groupby('PersonType')
df_count = df.count()
df_count = df_count.sort('count')
display(df_count)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.table("AdventureWorks_Dev_LH.Person.Person").groupby('PersonType')
df_count = df.count()
df_count = df_count.sort('count', ascending=False)
display(df_count)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT *
# MAGIC FROM AdventureWorks_Dev_LH.Person.Person 
# MAGIC WHERE Title IS NULL OR FirstName = 'Ken'

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT PersonType, COUNT(*) AS NumberOfRows
# MAGIC FROM AdventureWorks_Dev_LH.Person.Person 
# MAGIC GROUP BY PersonType 
# MAGIC ORDER BY NumberOfRows DESC

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT 
# MAGIC     CASE WHEN Color IS NULL THEN 'Multi-Tone' ELSE Color END AS CleanedColor,
# MAGIC     CASE WHEN ListPrice > 1000 THEN 'Premium' ELSE 'Standard' END as PriceCategory 
# MAGIC  FROM AdventureWorks_Dev_LH.Production.Product 

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Create a fresh cell right below this one, open it with %%sql, and write a query where:
# 
# The product Size must be exactly one of these sizes: 'M', 'L', or 'XL'. (Hint: Use the IN (...) operator).
# 
# The product Name must contain the word 'Bike' anywhere inside it. (Hint: Use the LIKE '%...%' wildcard operator).
# 
# Completely exclude any items where the Style is missing (IS NOT NULL).

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT *
# MAGIC FROM AdventureWorks_Dev_LH.Production.Product AS p
# MAGIC WHERE p.Size IN ('M', 'L', 'XL') 
# MAGIC AND p.Name LIKE '%Bike%' AND p.Style IS NOT NULL


# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Performs an INNER JOIN to connect both tables together using their shared ProductID column.
# 
# Groups the joined records by the product Name.
# 
# Calculates the total volume ordered using SUM(OrderQty) and assigns it an alias column name.
# 
# Sorts the output in descending order so the highest-selling products appear at the top.
# 
# Hint: Since both tables contain a column named ProductID, use short table aliases (like FROM Sales.SalesOrderDetail AS sod and JOIN Production.Product AS p) to tell SQL exactly which table you are referencing when joining!

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT p.Name, SUM(OrderQty) AS OrderQuantity
# MAGIC FROM AdventureWorks_Dev_LH.Production.Product AS p 
# MAGIC INNER JOIN AdventureWorks_Dev_LH.Sales.SalesOrderDetail AS s 
# MAGIC ON p.ProductID=s.ProductID
# MAGIC GROUP BY p.Name
# MAGIC ORDER BY OrderQuantity DESC;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Let's look at your Sales.SalesOrderDetail table. The finance team wants a report that shows every individual line item sale, but they also want to see a column next to it showing the highest single order quantity ever placed for that specific product so they can compare individual rows against the record high.
# 
# Create a new cell with %%sql and try to complete this query:
# 
# Select SalesOrderID, ProductID, and OrderQty.
# 
# Add a window function using MAX(OrderQty).
# 
# Use PARTITION BY ProductID inside the OVER() clause so the maximum value recalculates from scratch for each unique product.
# 
# Alias this new window column as MaxProductQty.
# 
# Read FROM AdventureWorks_Dev_LH.Sales.SalesOrderDetail.

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT s.SalesOrderID, s.ProductID, s.OrderQty,
# MAGIC MAX(s.OrderQty) OVER (PARTITION BY s.ProductID ) as MaxProductQty
# MAGIC FROM AdventureWorks_Dev_LH.Sales.SalesOrderDetail AS s


# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Select SalesOrderID, ProductID, and OrderQty.
# 
# Add a ranking window function: ROW_NUMBER() OVER (...) (Note: ROW_NUMBER() takes no column arguments inside its own function parentheses).
# 
# Inside your OVER() statement, PARTITION BY s.ProductID and ORDER BY s.OrderQty DESC.
# 
# Alias it as OrderRank.

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT s.SalesOrderID, s.ProductID, s.OrderQty,
# MAGIC ROW_NUMBER() OVER (PARTITION BY s.ProductID ORDER BY s.OrderQty DESC) AS OrderRank
# MAGIC FROM AdventureWorks_Dev_LH.Sales.SalesOrderDetail AS s

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }
