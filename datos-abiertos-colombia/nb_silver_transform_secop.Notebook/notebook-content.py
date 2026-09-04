# Fabric notebook source

# METADATA ********************

# META {
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "dee59c18-2af7-4f0f-9100-fd6655a63309",
# META       "default_lakehouse_name": "datos_abiertos_silver_lh_dev",
# META       "default_lakehouse_workspace_id": "2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e",
# META       "known_lakehouses": [
# META         {
# META           "id": "dee59c18-2af7-4f0f-9100-fd6655a63309"
# META         },
# META         {
# META           "id": "f95e26b3-c404-4e86-be37-c64906ebe3f9"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # 🇨🇴 Capa Silver: Transformación y Modelo Estrella SECOP II
# ### Medallion Architecture: Bronze (`datos_abiertos_lh_dev`) ➔ Silver (`datos_abiertos_silver_lh_dev`)
# Este notebook implementa el desarrollo guiado por especificaciones (**Spec-Driven Development**) definido en `spec.md` (RF-06, RF-07, RF-08) y `decisions.md` (ADR-005, ADR-006, ADR-007):
# - **Origen:** 6,013,832 contratos crudos en `bronze_secop_contratos`.
# - **Destino:** Lakehouse dedicado `datos_abiertos_silver_lh_dev`.
# - **Modelo Dimensional Estrella:**
#   1. `fact_contratos`: Métricas monetarias, duraciones, rangos de cuantía y claves foráneas.
#   2. `dim_entidades`: Catálogo maestro de entidades estatales (Nacional/Territorial, Sectores).
#   3. `dim_proveedores`: Directorio deduplicado de contratistas adjudicados y representantes legales.
#   4. `dim_geografia`: Normalización geográfica de departamentos y municipios de Colombia.
# - **Reglas de Calidad:** Preservación del 100% histórico con bandera `es_cuantia_cero = True` para contratos <= $0 o nulos.

# PARAMETERS CELL ********************

# =====================================================================
# ⚙️ CELDA DE PARÁMETROS Y CONFIGURACIÓN MEDALLION
# =====================================================================
# Identificadores canónicos de Microsoft Fabric
WORKSPACE_ID = '2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e'     # ws-datos-abiertos-colombia
BRONZE_LH_ID = 'f95e26b3-c404-4e86-be37-c64906ebe3f9'     # datos_abiertos_lh_dev
BRONZE_TABLE = 'bronze_secop_contratos'

# Tablas destino en Silver (se persisten en el default lakehouse: datos_abiertos_silver_lh_dev)
FACT_TABLE = 'fact_contratos'
DIM_ENTIDADES_TABLE = 'dim_entidades'
DIM_PROVEEDORES_TABLE = 'dim_proveedores'
DIM_GEOGRAFIA_TABLE = 'dim_geografia'

# Ruta canónica OneLake ABFSS inter-lakehouse (con esquema dbo habilitado)
BRONZE_PATH = f'abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{BRONZE_LH_ID}/Tables/dbo/{BRONZE_TABLE}'

print(f'🚀 Origen canónico Bronze OneLake: {BRONZE_PATH}')


# CELL ********************

# =====================================================================
# 📥 1. LECTURA Y PERFILAMIENTO INICIAL DE LA CAPA BRONZE
# =====================================================================
from pyspark.sql import functions as F
from pyspark.sql.types import *

print(f'Cargando 6 millones de registros desde Bronze OneLake: {BRONZE_PATH}...')
df_raw = spark.read.format('delta').load(BRONZE_PATH)

total_bronze = df_raw.count()
print(f'✅ Total registros cargados desde Bronze: {total_bronze:,}')


# CELL ********************

# =====================================================================
# 🧹 2. LIMPIEZA, NORMALIZACIÓN Y ENRIQUECIMIENTO BASE
# =====================================================================
# Función de limpieza textual: mayúsculas, sin espacios redundantes
def clean_str(col_name):
    return F.upper(F.trim(F.coalesce(F.col(col_name), F.lit('NO DEFINIDO'))))

# Conversión monetaria segura a Double
def parse_currency(col_name):
    return F.coalesce(
        F.regexp_replace(F.col(col_name), '[^0-9.]', '').cast(DoubleType()),
        F.lit(0.0)
    )

# Sanitización de fechas: evita errores de SparkUpgradeException en años previos a 1582 (ej. 0001)
def parse_clean_date(col_name):
    d = F.to_date(F.col(col_name))
    return F.when(F.year(d).between(1990, 2040), d).otherwise(F.lit(None))

# Dataset base con tipos estandarizados
df_base = df_raw.select(
    # Identificadores de negocio
    clean_str('id_contrato').alias('id_contrato'),
    clean_str('proceso_de_compra').alias('proceso_de_compra'),
    clean_str('referencia_del_contrato').alias('referencia_contrato'),
    clean_str('estado_contrato').alias('estado_contrato'),
    clean_str('tipo_de_contrato').alias('tipo_contrato'),
    clean_str('modalidad_de_contratacion').alias('modalidad_contratacion'),
    clean_str('justificacion_modalidad_de').alias('justificacion_modalidad'),
    
    # Entidades estatales
    clean_str('nit_entidad').alias('nit_entidad'),
    clean_str('nombre_entidad').alias('nombre_entidad'),
    clean_str('orden').alias('orden_entidad'),
    clean_str('sector').alias('sector_entidad'),
    clean_str('rama').alias('rama_entidad'),
    clean_str('entidad_centralizada').alias('entidad_centralizada'),
    
    # Proveedores / Contratistas (Nombres exactos de SECOP II)
    clean_str('tipodocproveedor').alias('tipo_doc_proveedor'),
    clean_str('documento_proveedor').alias('nit_cc_proveedor'),
    clean_str('proveedor_adjudicado').alias('nombre_proveedor'),
    clean_str('nombre_representante_legal').alias('nombre_representante'),
    clean_str('identificaci_n_representante_legal').alias('nit_cc_representante'),
    clean_str('g_nero_representante_legal').alias('genero_representante'),
    
    # Ubicación geográfica
    clean_str('departamento').alias('departamento'),
    clean_str('ciudad').alias('ciudad'),
    clean_str('localizaci_n').alias('localizacion'),
    
    # Fechas parseadas y protegidas contra fechas anómalas de SECOP II
    parse_clean_date('fecha_de_firma').alias('fecha_firma'),
    parse_clean_date('fecha_de_inicio_del_contrato').alias('fecha_inicio'),
    parse_clean_date('fecha_de_fin_del_contrato').alias('fecha_fin'),
    
    # Métricas monetarias
    parse_currency('valor_del_contrato').alias('valor_contrato'),
    parse_currency('valor_pagado').alias('valor_pagado'),
    parse_currency('valor_facturado').alias('valor_facturado'),
    parse_currency('valor_pendiente_de_pago').alias('valor_pendiente_pago'),
    parse_currency('valor_de_pago_adelantado').alias('valor_anticipo')
)

print('✅ Limpieza base completada.')


# CELL ********************

# =====================================================================
# 🏛️ 3. DIMENSIÓN ENTIDADES PÚBLICAS (dim_entidades)
# =====================================================================
print('Construyendo dim_entidades con Surrogate Key numérica (BIGINT)...')

df_entidades = (
    df_base.select(
        'nit_entidad',
        'nombre_entidad',
        'orden_entidad',
        'sector_entidad',
        'rama_entidad',
        'entidad_centralizada'
    )
    .dropDuplicates(['nit_entidad', 'nombre_entidad'])
    .withColumn(
        'id_entidad_sk',
        F.xxhash64(F.col('nit_entidad'), F.col('nombre_entidad'))
    )
)

df_entidades.write.format('delta').mode('overwrite').saveAsTable(DIM_ENTIDADES_TABLE)
count_entidades = spark.table(DIM_ENTIDADES_TABLE).count()
print(f'✅ dim_entidades persistida con éxito. Total entidades únicas: {count_entidades:,}')


# CELL ********************

# =====================================================================
# 🏢 4. DIMENSIÓN PROVEEDORES Y CONTRATISTAS (dim_proveedores)
# =====================================================================
print('Construyendo dim_proveedores con Surrogate Key numérica (BIGINT)...')

df_proveedores = (
    df_base.select(
        'tipo_doc_proveedor',
        'nit_cc_proveedor',
        'nombre_proveedor',
        'nombre_representante',
        'nit_cc_representante',
        'genero_representante'
    )
    .dropDuplicates(['tipo_doc_proveedor', 'nit_cc_proveedor'])
    .withColumn(
        'id_proveedor_sk',
        F.xxhash64(F.col('tipo_doc_proveedor'), F.col('nit_cc_proveedor'))
    )
)

df_proveedores.write.format('delta').mode('overwrite').saveAsTable(DIM_PROVEEDORES_TABLE)
count_proveedores = spark.table(DIM_PROVEEDORES_TABLE).count()
print(f'✅ dim_proveedores persistida con éxito. Total proveedores únicos: {count_proveedores:,}')


# CELL ********************

# =====================================================================
# 📍 5. DIMENSIÓN GEOGRAFÍA DE COLOMBIA (dim_geografia)
# =====================================================================
print('Construyendo dim_geografia con Surrogate Key numérica (BIGINT)...')

# Normalización de tildes para municipios y departamentos
def remove_accents(c):
    return F.translate(c, 'ÁÉÍÓÚáéíóúÑñÜü', 'AEIOUAEIOUNNUU')

# Mapeo oficial de las 5 Regiones Naturales de Colombia
def get_region(dpto):
    return (
        F.when(dpto.isin('ATLANTICO', 'BOLIVAR', 'CESAR', 'CORDOBA', 'LA GUAJIRA', 'MAGDALENA', 'SUCRE', 'SAN ANDRES, PROVIDENCIA Y SANTA CATALINA'), F.lit('Región Caribe'))
        .when(dpto.isin('ANTIOQUIA', 'BOYACA', 'CALDAS', 'CUNDINAMARCA', 'DISTRITO CAPITAL DE BOGOTA', 'HUILA', 'NORTE DE SANTANDER', 'QUINDIO', 'RISARALDA', 'SANTANDER', 'TOLIMA'), F.lit('Región Andina'))
        .when(dpto.isin('CAUCA', 'CHOCO', 'NARINO', 'VALLE DEL CAUCA'), F.lit('Región Pacífica'))
        .when(dpto.isin('ARAUCA', 'CASANARE', 'META', 'VICHADA'), F.lit('Región Orinoquía'))
        .when(dpto.isin('AMAZONAS', 'CAQUETA', 'GUAINIA', 'GUAVIARE', 'PUTUMAYO', 'VAUPES'), F.lit('Región Amazonía'))
        .otherwise(F.lit('Otra / No Definida'))
    )

df_geografia = (
    df_base.select(
        remove_accents(F.col('departamento')).alias('departamento_norm'),
        remove_accents(F.col('ciudad')).alias('ciudad_norm'),
        'localizacion'
    )
    .dropDuplicates(['departamento_norm', 'ciudad_norm'])
    .withColumn(
        'id_geografia_sk',
        F.xxhash64(F.col('departamento_norm'), F.col('ciudad_norm'))
    )
    .withColumn('region_natural', get_region(F.col('departamento_norm')))
)

df_geografia.write.format('delta').mode('overwrite').saveAsTable(DIM_GEOGRAFIA_TABLE)
count_geografia = spark.table(DIM_GEOGRAFIA_TABLE).count()
print(f'✅ dim_geografia persistida con éxito. Total ubicaciones únicas: {count_geografia:,}')


# CELL ********************

# =====================================================================
# 📊 6. TABLA DE HECHOS: fact_contratos (CON SURROGATE KEYS NUMÉRICAS)
# =====================================================================
print('Construyendo fact_contratos con llaves foráneas numéricas BIGINT...')

# Configuración oficial de compatibilidad para Parquet DateTime en Spark 3.x
spark.conf.set('spark.sql.parquet.datetimeRebaseModeInWrite', 'CORRECTED')
spark.conf.set('spark.sql.parquet.int96RebaseModeInWrite', 'CORRECTED')
spark.conf.set('spark.sql.parquet.datetimeRebaseModeInRead', 'CORRECTED')

# Limpieza previa de metastore para asegurar creación desde cero
spark.sql(f'DROP TABLE IF EXISTS {FACT_TABLE}')

# Cálculo seguro del año para métricas
raw_year = F.year(F.col('fecha_firma'))

# Claves subrogadas numéricas de 64 bits (xxhash64) para máximo rendimiento VertiPaq
df_fact = (
    df_base
    .withColumn('id_entidad_sk', F.xxhash64(F.col('nit_entidad'), F.col('nombre_entidad')))
    .withColumn('id_proveedor_sk', F.xxhash64(F.col('tipo_doc_proveedor'), F.col('nit_cc_proveedor')))
    .withColumn('id_geografia_sk', F.xxhash64(remove_accents(F.col('departamento')), remove_accents(F.col('ciudad'))))
    
    # Regla de Negocio ADR-007: Bandera de cuantía cero o nula
    .withColumn('es_cuantia_cero', F.when(F.col('valor_contrato') <= 0, F.lit(True)).otherwise(F.lit(False)))
    
    # Duración del contrato en días
    .withColumn('duracion_dias', F.coalesce(F.datediff(F.col('fecha_fin'), F.col('fecha_inicio')), F.lit(0)))
    
    # Partición temporal de análisis (delimitada entre 2000 y 2030)
    .withColumn('anno_firma', F.when(raw_year.between(2000, 2030), raw_year).otherwise(F.lit(1900)))
    .withColumn('mes_firma', F.coalesce(F.month(F.col('fecha_firma')), F.lit(0)))
    
    # Clasificación por Rango de Cuantía oficial de contratación
    .withColumn(
        'rango_cuantia',
        F.when(F.col('es_cuantia_cero') == True, F.lit('0. Sin Cuantía / Indeterminada'))
        .when(F.col('valor_contrato') < 50000000, F.lit('1. Mínima Cuantía (< $50M)'))
        .when(F.col('valor_contrato') < 500000000, F.lit('2. Menor Cuantía ($50M - $500M)'))
        .when(F.col('valor_contrato') < 5000000000, F.lit('3. Mayor Cuantía ($500M - $5.000M)'))
        .otherwise(F.lit('4. Megacontratos (> $5.000M)'))
    )
    .withColumn('_silver_processed_at', F.current_timestamp())
    
    # Selección final optimizada para el Data Warehouse
    .select(
        'id_contrato',
        'proceso_de_compra',
        'referencia_contrato',
        'id_entidad_sk',
        'id_proveedor_sk',
        'id_geografia_sk',
        'estado_contrato',
        'tipo_contrato',
        'modalidad_contratacion',
        'fecha_firma',
        'fecha_inicio',
        'fecha_fin',
        'anno_firma',
        'mes_firma',
        'duracion_dias',
        'valor_contrato',
        'valor_pagado',
        'valor_facturado',
        'valor_pendiente_pago',
        'valor_anticipo',
        'es_cuantia_cero',
        'rango_cuantia',
        '_silver_processed_at'
    )
)

# Persistencia optimizada en Delta Lake con V-Order nativo de Microsoft Fabric
print('Persistiendo 6M de filas en fact_contratos (Delta Lake con V-Order)...')
(
    df_fact
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable(FACT_TABLE)
)

count_fact = spark.table(FACT_TABLE).count()
print(f'🎉 fact_contratos persistida con éxito. Total filas: {count_fact:,}')


# CELL ********************

# =====================================================================
# 🔍 7. AUDITORÍA Y MATRIZ DE INTEGRIDAD CAPA SILVER
# =====================================================================
print('================================================================')
print('🏛️ RESUMEN ANALÍTICO DEL MODELO ESTRELLA (CAPA SILVER)')
print('================================================================')
c_bronze = total_bronze
c_fact = spark.table(FACT_TABLE).count()
c_ent = spark.table(DIM_ENTIDADES_TABLE).count()
c_prov = spark.table(DIM_PROVEEDORES_TABLE).count()
c_geo = spark.table(DIM_GEOGRAFIA_TABLE).count()

print(f'1. Total Contratos en Bronze:     {c_bronze:,}')
print(f'2. Total Contratos en fact (100%): {c_fact:,}')
print(f'3. Entidades Públicas Únicas:     {c_ent:,}')
print(f'4. Proveedores / Contratistas:    {c_prov:,}')
print(f'5. Ubicaciones Geográficas:       {c_geo:,}')
print(f'6. Integridad de Filas:           {"✅ 100% Exacto" if c_bronze == c_fact else "⚠️ Discrepancia detectada"}')
print('================================================================')

# Distribución por Rango de Cuantía
display(
    spark.table(FACT_TABLE)
    .groupBy('rango_cuantia')
    .agg(
        F.count('*').alias('cantidad_contratos'),
        F.round(F.sum('valor_contrato'), 2).alias('valor_total_cop')
    )
    .orderBy('rango_cuantia')
)

