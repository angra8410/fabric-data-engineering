# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "dc3c62ea-5e72-4253-b521-a9b6a5628475",
# META       "default_lakehouse_name": "lh_gold_gee_dev",
# META       "default_lakehouse_workspace_id": "affccd3f-b4a3-4e0c-84cb-de356f76d982",
# META       "known_lakehouses": [
# META         {
# META           "id": "cb78da87-a470-4885-9fb1-c9897f41c1f6"
# META         },
# META         {
# META           "id": "dc3c62ea-5e72-4253-b521-a9b6a5628475"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import col, when
from pyspark.sql.types import StructType, StructField, StringType

# =====================================================================
# 1. CREACIÓN DE LA DIMENSIÓN DIVIPOLA (100% ÚNICA)
# =====================================================================
print("Cargando catálogo maestro dim_divipola (Sin duplicados)...")

# Eliminamos la fila de Buenaventura. Solo quedan los 33 oficiales.
data_divipola = [
    ("91", "AMAZONAS", "Amazonia"), ("05", "ANTIOQUIA", "Andina"), 
    ("81", "ARAUCA", "Orinoquia"), ("08", "ATLANTICO", "Caribe"), 
    ("11", "BOGOTA", "Andina"), ("13", "BOLIVAR", "Caribe"), 
    ("15", "BOYACA", "Andina"), ("17", "CALDAS", "Andina"), 
    ("18", "CAQUETA", "Amazonia"), ("85", "CASANARE", "Orinoquia"), 
    ("19", "CAUCA", "Pacifica"), ("20", "CESAR", "Caribe"), 
    ("27", "CHOCO", "Pacifica"), ("23", "CORDOBA", "Caribe"), 
    ("25", "CUNDINAMARCA", "Andina"), ("94", "GUAINIA", "Amazonia"), 
    ("95", "GUAVIARE", "Amazonia"), ("41", "HUILA", "Andina"), 
    ("44", "LA GUAJIRA", "Caribe"), ("47", "MAGDALENA", "Caribe"), 
    ("50", "META", "Orinoquia"), ("52", "NARINO", "Pacifica"), 
    ("54", "NORTE DE SANTANDER", "Andina"), ("86", "PUTUMAYO", "Amazonia"), 
    ("63", "QUINDIO", "Andina"), ("66", "RISARALDA", "Andina"), 
    ("88", "SAN ANDRES", "Caribe"), ("68", "SANTANDER", "Andina"), 
    ("70", "SUCRE", "Caribe"), ("73", "TOLIMA", "Andina"), 
    ("76", "VALLE DEL CAUCA", "Pacifica"), ("97", "VAUPES", "Amazonia"), 
    ("99", "VICHADA", "Orinoquia")
]

schema_divipola = StructType([
    StructField("cod_dane", StringType(), True),
    StructField("nombre_departamento", StringType(), True),
    StructField("region", StringType(), True)
])

df_dim_divipola = spark.createDataFrame(data_divipola, schema=schema_divipola)
df_dim_divipola.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_divipola")


# =====================================================================
# 2. LECTURA DE SILVER Y CRUCE (Traducción al vuelo)
# =====================================================================
print("Leyendo capa Silver y mapeando Buenaventura...")

ruta_absoluta_silver = "abfss://ws_dev_google_earth@onelake.dfs.fabric.microsoft.com/lh_silver_gee_dev.Lakehouse/Tables/silver_forest_metrics"
df_silver = spark.read.format("delta").load(ruta_absoluta_silver)

# 🚨 La Magia: Convertimos Buenaventura en Valle del Cauca ANTES de cruzar
df_silver_arreglado = df_silver.withColumn(
    "departamento_limpio",
    when(col("departamento") == "BUENAVENTURA", "VALLE DEL CAUCA").otherwise(col("departamento"))
)

# Hacemos el cruce usando la columna limpia
df_cruzado = df_silver_arreglado.join(
    df_dim_divipola,
    df_silver_arreglado.departamento_limpio == df_dim_divipola.nombre_departamento,
    "left"
)

# =====================================================================
# 3. CREACIÓN DE LA TABLA DE HECHOS (Sin NULLs)
# =====================================================================
df_fact = df_cruzado.select(
    col("anio_reporte").alias("id_anio"),
    col("cod_dane").alias("id_divipola"),
    col("hectareas_deforestadas"),
    col("version_algoritmo")
).filter(col("id_divipola").isNotNull()) # 🚨 Aquí eliminamos los horribles NULLs

print("👀 Así se ve tu Tabla de Hechos IMPECABLE:")
display(df_fact.orderBy("id_anio", "id_divipola").limit(10))

# =====================================================================
# 4. CREACIÓN DE LA DIMENSIÓN ALGORITMO (dim_algoritmo)
# =====================================================================
print("Construyendo dim_algoritmo...")

# Extraemos los valores únicos de la versión del algoritmo de nuestra capa Silver
df_dim_algoritmo = df_silver.select(
    col("version_algoritmo").alias("id_algoritmo"),
    col("version_algoritmo").alias("nombre_version")
).distinct()

# Guardamos y registramos oficialmente
df_dim_algoritmo.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_algoritmo")


# =====================================================================
# 5. CREACIÓN DE LA DIMENSIÓN FECHA (dim_fecha corregida)
# =====================================================================
print("Construyendo dim_fecha inteligente...")

# Usamos 'id_anio' sin espacios ni caracteres especiales
df_anios = df_silver.select(col("anio_reporte").alias("id_anio")).distinct()

from pyspark.sql.functions import when, concat, lit, floor

# Reemplazamos los espacios por guiones bajos (_) en los nombres de las columnas
df_dim_fecha = df_anios \
    .withColumn("decada", concat(floor(col("id_anio") / 10) * 10, lit("s"))) \
    .withColumn("etiqueta_anio", concat(lit("Año "), col("id_anio").cast("string"))) \
    .withColumn("es_anio_reciente", when(col("id_anio") >= 2020, True).otherwise(False)) \
    .withColumn("periodo_paz", when(col("id_anio") >= 2017, "Post-Acuerdo (2017+)").otherwise("Pre-Acuerdo (<2017)")) \
    .withColumn("value", col("id_anio")) 

# Guardamos y registramos oficialmente
df_dim_fecha.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("dim_fecha")

print("✅ dim_fecha construida con nombres de columna 100% compatibles con Delta Lake.")


# =====================================================================
# 6. ACTUALIZACIÓN DE FACT_DEFORESTACION (Usando saveAsTable)
# =====================================================================
# Pequeña corrección arquitectónica: Para que Power BI no moleste, 
# asegúrate de que tu tabla de hechos también se guarde con saveAsTable, no con .save()

print("Re-registrando fact_deforestacion...")
df_fact.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_deforestacion")
df_dim_divipola.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_divipola")

print("✅ ¡Estrella completa! Todas las dimensiones están registradas en el Metastore.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(df_fact.orderBy("id_anio", "id_divipola"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
