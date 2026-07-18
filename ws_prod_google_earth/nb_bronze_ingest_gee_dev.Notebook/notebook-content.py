# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "87232684-edfa-4e54-a68a-5ddb9a4288c7",
# META       "default_lakehouse_name": "lh_bronze_gee_dev",
# META       "default_lakehouse_workspace_id": "dccfbb1c-04b0-495e-a6cb-6c714244fd65",
# META       "known_lakehouses": [
# META         {
# META           "id": "87232684-edfa-4e54-a68a-5ddb9a4288c7"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

%pip install earthengine-api geemap

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import ee
import pandas as pd
from google.oauth2 import service_account

# =====================================================================
# 1. AUTENTICACIÓN AUTOMÁTICA (Data Factory / Pipeline Ready)
# =====================================================================
# REEMPLAZA ESTO con el nombre exacto de tu archivo JSON
nombre_archivo_json = "token.json" 
key_path = f"/lakehouse/default/Files/{nombre_archivo_json}"

# REEMPLAZA ESTO con el ID de tu proyecto en Google Cloud
id_proyecto_gcp = "excellent-tide-498415-b7"

try:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
    ee.Initialize(scoped_credentials, project=id_proyecto_gcp)
    print("✅ [1/4] Autenticación exitosa con Service Account.")
except Exception as e:
    print(f"❌ Error de autenticación: {e}")
    raise

# =====================================================================
# 2. EXTRACCIÓN DE DATOS (Google Earth Engine)
# =====================================================================
anio_analisis = 2022
print(f"⏳ [2/4] Calculando deforestación de Colombia para el año {anio_analisis} en Google...")

# Fronteras de Colombia (Departamentos)
colombia_deptos = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM0_NAME', 'Colombia'))

# Dataset global de Hansen
hansen_dataset = ee.Image('UMD/hansen/global_forest_change_2022_v1_10')
loss_year = hansen_dataset.select('lossyear')
tree_cover = hansen_dataset.select('treecover2000')

# Máscara: Bosque > 30% y pérdida en el año de análisis
year_mask = loss_year.eq(anio_analisis - 2000).And(tree_cover.gte(30))
loss_area_image = ee.Image.pixelArea().updateMask(year_mask)

# Calcular el área por departamento (Resolución 30m)
loss_by_depto = loss_area_image.reduceRegions(
    collection=colombia_deptos,
    reducer=ee.Reducer.sum(),
    scale=30 
)

# =====================================================================
# 3. TRANSFORMACIÓN A DATAFRAME CRUDO
# =====================================================================
features = loss_by_depto.getInfo()['features']
datos_crudos = []

for f in features:
    props = f['properties']
    datos_crudos.append({
        'admin_name': props.get('ADM1_NAME', 'Desconocido'),
        'country': 'Colombia',
        'forest_loss_sq_meters': props.get('sum', 0),
        'report_year': anio_analisis,
        'gee_dataset_version': 'UMD/hansen/v1_10' # Metadato para control de Drift
    })

pdf_bronze = pd.DataFrame(datos_crudos)
print(f"✅ [3/4] Datos extraídos: {len(pdf_bronze)} departamentos.")
display(pdf_bronze.head())

# =====================================================================
# 4. ATERRIZAJE EN BRONZE (Tolerante a Schema Drift)
# =====================================================================
# Convertir a Spark y guardar como Delta Table
df_spark = spark.createDataFrame(pdf_bronze)

tabla_destino = "Tables/raw_gee_forest_metrics"

df_spark.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(tabla_destino)

print(f"✅ [4/4] Ingesta completada en {tabla_destino}. ¡Listo para la capa Silver!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import ee
import pandas as pd
from google.oauth2 import service_account

# =====================================================================
# 1. AUTENTICACIÓN (Usando el robot que descubrimos)
# =====================================================================
# Cambia 'tu_archivo.json' por el nombre de tu llave de colombia-deforestation
key_path = "/lakehouse/default/Files/token.json" 
id_proyecto_gcp = "excellent-tide-498415-b7"

try:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
    ee.Initialize(scoped_credentials, project=id_proyecto_gcp)
    print("✅ Autenticación exitosa.")
except Exception as e:
    print(f"❌ Error de autenticación: {e}")
    raise

# =====================================================================
# 2. CONFIGURACIÓN DEL BACKFILL HISTÓRICO
# =====================================================================
# ¡Actualizado a la versión v1_13 que Google nos recomendó!
dataset_version = 'UMD/hansen/global_forest_change_2025_v1_13'
hansen_dataset = ee.Image(dataset_version)

loss_year = hansen_dataset.select('lossyear')
tree_cover = hansen_dataset.select('treecover2000')
colombia_deptos = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM0_NAME', 'Colombia'))

# Lista de años a procesar (Saltamos 2022 y frenamos en 2023 por disponibilidad satelital)
anios_historicos = [2019, 2020, 2021, 2023]
tabla_destino = "Tables/raw_gee_forest_metrics"

print(f"🚀 Iniciando carga histórica para los años: {anios_historicos}")
print("-" * 50)

# =====================================================================
# 3. BUCLE DE EXTRACCIÓN Y ATERRIZAJE EN BRONZE
# =====================================================================
for anio in anios_historicos:
    print(f"⏳ Procesando año {anio} en Google Earth Engine...")
    
    try:
        # En el dataset, los años se representan con dos dígitos (ej. 2019 es 19)
        year_mask = loss_year.eq(anio - 2000).And(tree_cover.gte(30))
        loss_area_image = ee.Image.pixelArea().updateMask(year_mask)

        # Cómputo distribuido en Google
        loss_by_depto = loss_area_image.reduceRegions(
            collection=colombia_deptos,
            reducer=ee.Reducer.sum(),
            scale=30 
        )

        features = loss_by_depto.getInfo()['features']
        datos_crudos = []

        for f in features:
            props = f['properties']
            datos_crudos.append({
                'admin_name': props.get('ADM1_NAME', 'Desconocido'),
                'country': 'Colombia',
                'forest_loss_sq_meters': props.get('sum', 0),
                'report_year': anio,
                'gee_dataset_version': dataset_version # Anotamos la versión nueva
            })

        # Guardar el año específico en Fabric
        df_spark = spark.createDataFrame(pd.DataFrame(datos_crudos))
        
        df_spark.write \
            .format("delta") \
            .mode("append") \
            .option("mergeSchema", "true") \
            .save(tabla_destino)

        print(f"🟢 Año {anio} completado y guardado en {tabla_destino}.")
        
    except Exception as e:
        print(f"🔴 Error procesando el año {anio}: {e}")

print("-" * 50)
print("🎉 ¡Carga Histórica Finalizada! Revisa tu tabla en el Lakehouse.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import ee
import pandas as pd
from google.oauth2 import service_account

# 1. AUTENTICACIÓN
key_path = "/lakehouse/default/Files/token.json" 
id_proyecto_gcp = "excellent-tide-498415-b7"

try:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
    ee.Initialize(scoped_credentials, project=id_proyecto_gcp)
    print("✅ Autenticación exitosa.")
except Exception as e:
    print(f"❌ Error de autenticación: {e}")
    raise

# 2. CONFIGURACIÓN (Años Recientes)
dataset_version = 'UMD/hansen/global_forest_change_2025_v1_13' # Si Google te arroja un warning de nueva versión, actualiza este string
hansen_dataset = ee.Image(dataset_version)

loss_year = hansen_dataset.select('lossyear')
tree_cover = hansen_dataset.select('treecover2000')
colombia_deptos = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM0_NAME', 'Colombia'))

# Vamos por los años recientes. El pipeline resistirá si alguno no existe.
anios_historicos = [2024, 2025, 2026]
tabla_destino = "Tables/raw_gee_forest_metrics"

print(f"🚀 Buscando datos recientes para los años: {anios_historicos}")
print("-" * 50)

# 3. BUCLE DE EXTRACCIÓN
for anio in anios_historicos:
    print(f"⏳ Intentando procesar año {anio}...")
    
    try:
        # En Hansen, el año es de 2 dígitos (ej. 2024 es 24)
        year_mask = loss_year.eq(anio - 2000).And(tree_cover.gte(30))
        loss_area_image = ee.Image.pixelArea().updateMask(year_mask)

        loss_by_depto = loss_area_image.reduceRegions(
            collection=colombia_deptos,
            reducer=ee.Reducer.sum(),
            scale=30 
        )

        features = loss_by_depto.getInfo()['features']
        datos_crudos = []

        for f in features:
            props = f['properties']
            datos_crudos.append({
                'admin_name': props.get('ADM1_NAME', 'Desconocido'),
                'country': 'Colombia',
                'forest_loss_sq_meters': props.get('sum', 0),
                'report_year': anio,
                'gee_dataset_version': dataset_version
            })

        # Filtrar si Google nos devuelve todo en 0 (Significa que el año aún no está mapeado en esta versión)
        df_temp = pd.DataFrame(datos_crudos)
        total_loss = df_temp['forest_loss_sq_meters'].sum()
        
        if total_loss == 0:
             print(f"⚠️ El año {anio} devolvió 0 metros cuadrados. Es probable que la data satelital anual aún no esté publicada por UMD/Google.")
        else:
            df_spark = spark.createDataFrame(df_temp)
            df_spark.write \
                .format("delta") \
                .mode("append") \
                .option("mergeSchema", "true") \
                .save(tabla_destino)
            print(f"🟢 Año {anio} completado y guardado en {tabla_destino}.")
        
    except Exception as e:
        print(f"🔴 Error procesando el año {anio} (Posiblemente no exista en la API aún): {e}")

print("-" * 50)
print("🎉 Extracción de años recientes finalizada.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import ee
import pandas as pd
from google.oauth2 import service_account

# 1. AUTENTICACIÓN
key_path = "/lakehouse/default/Files/token.json" 
id_proyecto_gcp = "excellent-tide-498415-b7"

try:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
    ee.Initialize(scoped_credentials, project=id_proyecto_gcp)
    print("✅ Autenticación exitosa. Preparando motores de viaje en el tiempo...")
except Exception as e:
    print(f"❌ Error de autenticación: {e}")
    raise

# 2. CONFIGURACIÓN (La Gran Década)
dataset_version = 'UMD/hansen/global_forest_change_2025_v1_13'
hansen_dataset = ee.Image(dataset_version)

loss_year = hansen_dataset.select('lossyear')
tree_cover = hansen_dataset.select('treecover2000')
colombia_deptos = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM0_NAME', 'Colombia'))

# Generamos automáticamente los años desde el 2010 hasta el 2018 (el 2019 no se incluye en este rango)
anios_historicos = list(range(2010, 2019)) 
tabla_destino = "Tables/raw_gee_forest_metrics"

print(f"🚀 Iniciando extracción masiva para los años: {anios_historicos}")
print("-" * 50)

# 3. BUCLE DE EXTRACCIÓN MASIVA
for anio in anios_historicos:
    print(f"⏳ Viajando al año {anio}...")
    
    try:
        # En Hansen, el año 2010 es el valor 10
        year_mask = loss_year.eq(anio - 2000).And(tree_cover.gte(30))
        loss_area_image = ee.Image.pixelArea().updateMask(year_mask)

        loss_by_depto = loss_area_image.reduceRegions(
            collection=colombia_deptos,
            reducer=ee.Reducer.sum(),
            scale=30 
        )

        features = loss_by_depto.getInfo()['features']
        datos_crudos = []

        for f in features:
            props = f['properties']
            datos_crudos.append({
                'admin_name': props.get('ADM1_NAME', 'Desconocido'),
                'country': 'Colombia',
                'forest_loss_sq_meters': props.get('sum', 0),
                'report_year': anio,
                'gee_dataset_version': dataset_version
            })

        df_spark = spark.createDataFrame(pd.DataFrame(datos_crudos))
        
        # Guardamos en la misma tabla Delta, apilando los datos históricos
        df_spark.write \
            .format("delta") \
            .mode("append") \
            .option("mergeSchema", "true") \
            .save(tabla_destino)

        print(f"🟢 Año {anio} extraído y guardado con éxito.")
        
    except Exception as e:
        print(f"🔴 Error procesando el año {anio}: {e}")

print("-" * 50)
print("🎉 ¡Viaje en el tiempo completado! Tienes historia forestal desde 2010 en tu Bronze Lakehouse.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import ee
import pandas as pd
from google.oauth2 import service_account

# 1. AUTENTICACIÓN
key_path = "/lakehouse/default/Files/token.json" 
id_proyecto_gcp = "excellent-tide-498415-b7"

try:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/earthengine'])
    ee.Initialize(scoped_credentials, project=id_proyecto_gcp)
    print("✅ Autenticación exitosa. Viajando a la década de los 2000s...")
except Exception as e:
    print(f"❌ Error de autenticación: {e}")
    raise

# 2. CONFIGURACIÓN
dataset_version = 'UMD/hansen/global_forest_change_2025_v1_13'
hansen_dataset = ee.Image(dataset_version)

loss_year = hansen_dataset.select('lossyear')
tree_cover = hansen_dataset.select('treecover2000')
colombia_deptos = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM0_NAME', 'Colombia'))

# Generamos los años desde el 2004 hasta el 2009
anios_historicos = list(range(2004, 2010)) 
tabla_destino = "Tables/raw_gee_forest_metrics"

print(f"🚀 Iniciando extracción masiva para los años: {anios_historicos}")
print("-" * 50)

# 3. BUCLE DE EXTRACCIÓN MASIVA
for anio in anios_historicos:
    print(f"⏳ Procesando el año {anio}...")
    
    try:
        # En Hansen, el 2004 se representa con el valor 4
        year_mask = loss_year.eq(anio - 2000).And(tree_cover.gte(30))
        loss_area_image = ee.Image.pixelArea().updateMask(year_mask)

        loss_by_depto = loss_area_image.reduceRegions(
            collection=colombia_deptos,
            reducer=ee.Reducer.sum(),
            scale=30 
        )

        features = loss_by_depto.getInfo()['features']
        datos_crudos = []

        for f in features:
            props = f['properties']
            datos_crudos.append({
                'admin_name': props.get('ADM1_NAME', 'Desconocido'),
                'country': 'Colombia',
                'forest_loss_sq_meters': props.get('sum', 0),
                'report_year': anio,
                'gee_dataset_version': dataset_version
            })

        df_temp = pd.DataFrame(datos_crudos)
        total_loss = df_temp['forest_loss_sq_meters'].sum()
        
        if total_loss == 0:
             print(f"⚠️ El año {anio} devolvió 0. Algo inusual pasó con el mapa satelital de este año.")
        else:
            df_spark = spark.createDataFrame(df_temp)
            df_spark.write \
                .format("delta") \
                .mode("append") \
                .option("mergeSchema", "true") \
                .save(tabla_destino)
            print(f"🟢 Año {anio} guardado en Bronze.")
        
    except Exception as e:
        print(f"🔴 Error procesando el año {anio}: {e}")

print("-" * 50)
print("🎉 ¡Carga de los 2000s finalizada! Tu tabla Delta ahora es una verdadera cápsula del tiempo.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col, count

# =====================================================================
# RADIOGRAFÍA DE LA CAPA BRONZE
# =====================================================================
tabla_bronze = "Tables/raw_gee_forest_metrics"

print("⏳ Leyendo la cápsula del tiempo desde Bronze...")
df_bronze = spark.read.format("delta").load(tabla_bronze)

# 1. Conteo Total
total_registros = df_bronze.count()
print(f"📊 Total de registros históricos: {total_registros}")
print("-" * 50)

# 2. El Esquema (Para verificar nuestro mergeSchema)
print("🔎 Esquema detectado en la tabla:")
df_bronze.printSchema()
print("-" * 50)

# 3. Resumen por Año (La prueba del viaje en el tiempo)
print("📅 Años procesados y cantidad de departamentos por año:")
# Agrupamos por año y contamos. Deberíamos ver ~33 departamentos por cada año que procesamos.
resumen_anios = df_bronze.groupBy("report_year").count().orderBy("report_year")
display(resumen_anios)

# 4. Resumen por Versión (Nuestra auditoría de Drift)
print("🏷️ Versiones del algoritmo satelital utilizadas:")
# Esto nos mostrará cuántos datos se procesaron con la v1_10 vs la v1_13
resumen_versiones = df_bronze.groupBy("gee_dataset_version").count().orderBy("gee_dataset_version")
display(resumen_versiones)

# 5. Muestra rápida de los datos crudos
print("👀 Muestra rápida de 5 registros (Aleatorios):")
display(df_bronze.sample(fraction=0.1).limit(5))

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
