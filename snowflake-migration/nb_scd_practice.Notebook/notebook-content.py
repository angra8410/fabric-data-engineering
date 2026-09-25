# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "0adad52a-91cc-4d11-9e1c-5179fecfed26",
# META       "default_lakehouse_name": "SCD_Practice_Lakehouse",
# META       "default_lakehouse_workspace_id": "cfeefa92-730d-43b2-b2b1-9c46826d5807",
# META       "known_lakehouses": [
# META         {
# META           "id": "0adad52a-91cc-4d11-9e1c-5179fecfed26"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

df = spark.read.format("csv")\
               .option("header", "true")\
               .load("Files/raw/clientes_ejemplo.csv")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df.write.format('delta')\
        .mode("overwrite")\
        .saveAsTable("clientes_ejemplo_delta")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.types import StructType, StructField, StringType

# Define dummy data representing updates
# Assume 'id_cliente' = 1 changed their email, and 'id_cliente' = 3 is a new customer
updates_data = [
    ("1", "Carlos Gomez", "carlos.nuevo@email.com", "Bogota"),  # SCD Type 1 Update
    ("3", "Maria Rojas", "maria.rojas@email.com", "Medellin")   # New insert
]

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Define schema matching your table structure
schema = StructType([
    StructField("id_cliente", StringType(), True),
    StructField("nombre", StringType(), True),
    StructField("correo", StringType(), True),
    StructField("ciudad", StringType(), True)
])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create the DataFrame and register it as a temporary view
updates_df = spark.createDataFrame(updates_data, schema)
updates_df.createOrReplaceTempView("nuevos_datos_temp")

print("Temporary view 'nuevos_datos_temp' is now ready for SQL!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC MERGE INTO clientes_ejemplo_delta AS destino
# MAGIC USING nuevos_datos_temp AS origen
# MAGIC ON destino.id_cliente = origen.id_cliente
# MAGIC WHEN MATCHED THEN
# MAGIC   UPDATE SET 
# MAGIC     destino.correo = origen.correo,
# MAGIC     destino.ciudad = origen.ciudad
# MAGIC WHEN NOT MATCHED THEN
# MAGIC   INSERT (id_cliente, nombre, correo, ciudad) 
# MAGIC   VALUES (origen.id_cliente, origen.nombre, origen.correo, origen.ciudad)

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC SELECT * FROM clientes_ejemplo_delta
# MAGIC ORDER BY id_cliente

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
