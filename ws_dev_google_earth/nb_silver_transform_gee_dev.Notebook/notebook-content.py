# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "14acc6d2-d9ab-4557-9c49-55cb7b72003d",
# META       "default_lakehouse_name": "lh_bronze_gee_dev",
# META       "default_lakehouse_workspace_id": "85e0e274-9471-4771-9513-327c77561998",
# META       "known_lakehouses": [
# META         {
# META           "id": "14acc6d2-d9ab-4557-9c49-55cb7b72003d"
# META         },
# META         {
# META           "id": "1a0041c3-a122-4327-938f-fbf771ef6941"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import col, round, upper, trim, current_timestamp

# =====================================================================
# 1. EXTRACCIÓN (Leer desde la cápsula del tiempo en Bronze)
# =====================================================================
print("⏳ Leyendo datos históricos desde la capa Bronze...")

# Ruta directa a tu tabla Bronze en Fabric usando ABFS
# (Si tienes un Shortcut creado, también podrías usar spark.table("lh_bronze_gee_dev.raw_gee_forest_metrics"))
ruta_bronze = "abfss://ws_dev_google_earth@onelake.dfs.fabric.microsoft.com/lh_bronze_gee_dev.Lakehouse/Tables/raw_gee_forest_metrics"

df_bronze = spark.read.format("delta").load(ruta_bronze)

# =====================================================================
# 2. TRANSFORMACIÓN (Reglas de Negocio y Limpieza)
# =====================================================================
print("⚙️ Aplicando reglas de calidad, estandarización y conversión a Hectáreas...")

df_silver = df_bronze \
    .withColumn("departamento", upper(trim(col("admin_name")))) \
    .withColumn("pais", upper(trim(col("country")))) \
    .withColumn("hectareas_deforestadas", round(col("forest_loss_sq_meters") / 10000, 2)) \
    .withColumn("anio_reporte", col("report_year").cast("integer")) \
    .withColumn("version_algoritmo", col("gee_dataset_version")) \
    .withColumn("fecha_procesamiento_silver", current_timestamp()) \
    .select(
        "anio_reporte",
        "pais",
        "departamento",
        "hectareas_deforestadas",
        "version_algoritmo",
        "fecha_procesamiento_silver"
    ) \
    .filter(col("hectareas_deforestadas") >= 0) # Filtro de calidad para evitar valores negativos anómalos

# Te mostramos una pequeña previsualización de cómo quedan los datos limpios
print("👀 Así se ve tu nueva capa Silver:")
display(df_silver.orderBy("anio_reporte", "departamento").limit(10))

# =====================================================================
# 3. CARGA (Aterrizaje en Silver Lakehouse)
# =====================================================================
tabla_silver_destino = "Tables/silver_forest_metrics"

print(f"⏳ Escribiendo datos limpios en {tabla_silver_destino}...")

# En Silver solemos usar "overwrite" en tablas dimensionales pequeñas/medianas
# para asegurarnos de que la tabla refleje exactamente la última lógica de negocio aplicada.
df_silver.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(tabla_silver_destino)

print("✅ ¡Transformación completada! Tus datos están estandarizados y listos para la capa Gold.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 3. CARGA (Aterrizaje Forzado en Silver Lakehouse)
# =====================================================================
# Usamos la ruta absoluta nativa de Fabric referenciando tu workspace y lakehouse explícitamente
tabla_silver_destino = "abfss://ws_dev_google_earth@onelake.dfs.fabric.microsoft.com/lh_silver_gee_dev.Lakehouse/Tables/silver_forest_metrics"

print(f"⏳ Escribiendo datos limpios forzadamente en lh_silver_gee_dev...")

df_silver.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(tabla_silver_destino)

print("✅ ¡Guardado blindado! Tu tabla Silver está exactamente donde debe estar.")

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
