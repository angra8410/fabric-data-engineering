# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "836d80d4-d5f4-45b2-9fe2-22051b2cf93a",
# META       "default_lakehouse_name": "datos_abiertos_gold_lh_dev",
# META       "default_lakehouse_workspace_id": "2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e",
# META       "known_lakehouses": [
# META         {
# META           "id": "836d80d4-d5f4-45b2-9fe2-22051b2cf93a"
# META         },
# META         {
# META           "id": "dee59c18-2af7-4f0f-9100-fd6655a63309"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # 🥇 Capa Gold: Data Marts Temáticos de Contratación Pública (SECOP II)
# ### Medallion Architecture: Silver (`datos_abiertos_silver_lh_dev`) ➔ Gold (`datos_abiertos_gold_lh_dev`)
# Este notebook construye los **Data Marts temáticos de alta gerencia** definidos en `spec.md` (RF-09, RF-10) y `decisions.md` (ADR-008):
# 1. **`mart_gasto_territorial`:** Inversión pública por Departamento, Municipio, Año y Mes para mapas en Power BI.
# 2. **`mart_transparencia_modalidades`:** Índice de contratación directa ("a dedo") vs. licitaciones por entidad estatal.
# 3. **`mart_concentracion_proveedores`:** Monitoreo de megacontratistas y concentración de presupuesto por sector.
# 4. **`mart_ejecucion_financiera`:** Análisis de pagos efectivos, anticipos, cartera pendiente y liquidez pública.
# 
# Todas las tablas son optimizadas automáticamente con el motor columnar **V-Order** para responder en milisegundos en **Power BI Direct Lake**.

# PARAMETERS CELL ********************

# =====================================================================
# ⚙️ CONFIGURACIÓN Y RUTAS CANÓNICAS ONELAKE
# =====================================================================
WORKSPACE_ID = '2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e'     # ws-datos-abiertos-colombia
SILVER_LH_ID = 'dee59c18-2af7-4f0f-9100-fd6655a63309'     # datos_abiertos_silver_lh_dev
GOLD_LH_ID   = '836d80d4-d5f4-45b2-9fe2-22051b2cf93a'     # datos_abiertos_gold_lh_dev

# Ruta canónica de lectura de las 4 tablas dimensionales en Silver
SILVER_BASE = f'abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{SILVER_LH_ID}/Tables'

FACT_CONTRATOS_PATH = f'{SILVER_BASE}/fact_contratos'
DIM_ENTIDADES_PATH  = f'{SILVER_BASE}/dim_entidades'
DIM_PROVEEDORES_PATH = f'{SILVER_BASE}/dim_proveedores'
DIM_GEOGRAFIA_PATH  = f'{SILVER_BASE}/dim_geografia'

# Nombres de los Data Marts destino en Gold
MART_TERRITORIAL     = 'mart_gasto_territorial'
MART_TRANSPARENCIA   = 'mart_transparencia_modalidades'
MART_CONTRATISTAS    = 'mart_concentracion_proveedores'
MART_FINANCIERO      = 'mart_ejecucion_financiera'

print(f'🚀 Origen Silver OneLake: {SILVER_BASE}')
print(f'🎯 Destino Gold Lakehouse: datos_abiertos_gold_lh_dev')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 📥 1. LECTURA DE LAS TABLAS DEL MODELO ESTRELLA SILVER
# =====================================================================
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Configuración oficial de compatibilidad para Parquet DateTime
spark.conf.set('spark.sql.parquet.datetimeRebaseModeInWrite', 'CORRECTED')
spark.conf.set('spark.sql.parquet.int96RebaseModeInWrite', 'CORRECTED')

print('Cargando tablas curadas desde Silver...')
df_fact = spark.read.format('delta').load(FACT_CONTRATOS_PATH)
df_entidades = spark.read.format('delta').load(DIM_ENTIDADES_PATH)
df_proveedores = spark.read.format('delta').load(DIM_PROVEEDORES_PATH)
df_geografia = spark.read.format('delta').load(DIM_GEOGRAFIA_PATH)

print(f'✅ fact_contratos:   {df_fact.count():,} registros')
print(f'✅ dim_entidades:     {df_entidades.count():,} entidades')
print(f'✅ dim_proveedores:   {df_proveedores.count():,} contratistas')
print(f'✅ dim_geografia:     {df_geografia.count():,} municipios/deptos')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 🗺️ 2. DATA MART: GASTO TERRITORIAL Y DEPARTAMENTAL
# =====================================================================
print(f'Construyendo {MART_TERRITORIAL}...')

mart_territorial = (
    df_fact.filter(F.col('anno_firma') >= 2015)
    .join(df_geografia, on='id_geografia_sk', how='inner')
    .groupBy(
        'departamento_norm',
        'ciudad_norm',
        'anno_firma',
        'mes_firma'
    )
    .agg(
        F.count('*').alias('total_contratos'),
        F.round(F.sum('valor_contrato'), 2).alias('inversion_total_cop'),
        F.round(F.avg('valor_contrato'), 2).alias('gasto_promedio_contrato'),
        F.round(F.sum('valor_pagado'), 2).alias('total_pagado_cop'),
        F.sum(F.when(F.col('rango_cuantia').like('%Megacontratos%'), 1).otherwise(0)).alias('contratos_megacuantia'),
        F.round(F.avg('duracion_dias'), 1).alias('duracion_promedio_dias')
    )
    .withColumn('_gold_processed_at', F.current_timestamp())
)

spark.sql(f'DROP TABLE IF EXISTS {MART_TERRITORIAL}')
mart_territorial.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_TERRITORIAL)
print(f'✅ {MART_TERRITORIAL} persistido exitosamente con {spark.table(MART_TERRITORIAL).count():,} filas.')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# ⚖️ 3. DATA MART: TRANSPARENCIA Y MODALIDADES DE CONTRATACIÓN
# =====================================================================
print(f'Construyendo {MART_TRANSPARENCIA}...')

mart_transparencia = (
    df_fact.filter(F.col('anno_firma') >= 2015)
    .join(df_entidades, on='id_entidad_sk', how='inner')
    .groupBy(
        'nit_entidad',
        'nombre_entidad',
        'orden_entidad',
        'sector_entidad',
        'modalidad_contratacion',
        'anno_firma'
    )
    .agg(
        F.count('*').alias('total_contratos'),
        F.round(F.sum('valor_contrato'), 2).alias('monto_total_cop'),
        F.round(F.sum('valor_pagado'), 2).alias('monto_pagado_cop'),
        F.sum(F.when(F.col('modalidad_contratacion').like('%DIRECTA%'), 1).otherwise(0)).alias('contratos_directos'),
        F.round(F.sum(F.when(F.col('modalidad_contratacion').like('%DIRECTA%'), F.col('valor_contrato')).otherwise(0.0)), 2).alias('monto_directo_cop')
    )
    .withColumn(
        'pct_contratacion_directa',
        F.round((F.col('monto_directo_cop') / F.when(F.col('monto_total_cop') > 0, F.col('monto_total_cop')).otherwise(1.0)) * 100, 2)
    )
    .withColumn('_gold_processed_at', F.current_timestamp())
)

spark.sql(f'DROP TABLE IF EXISTS {MART_TRANSPARENCIA}')
mart_transparencia.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_TRANSPARENCIA)
print(f'✅ {MART_TRANSPARENCIA} persistido exitosamente con {spark.table(MART_TRANSPARENCIA).count():,} filas.')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 🏢 4. DATA MART: CONCENTRACIÓN Y MEGACONTRATISTAS DEL ESTADO
# =====================================================================
print(f'Construyendo {MART_CONTRATISTAS}...')

mart_contratistas = (
    df_fact.filter(F.col('anno_firma') >= 2015)
    .join(df_proveedores, on='id_proveedor_sk', how='inner')
    .join(df_entidades.select('id_entidad_sk', 'sector_entidad'), on='id_entidad_sk', how='inner')
    .groupBy(
        'tipo_doc_proveedor',
        'nit_cc_proveedor',
        'nombre_proveedor',
        'sector_entidad',
        'anno_firma'
    )
    .agg(
        F.count('*').alias('total_contratos_ganados'),
        F.round(F.sum('valor_contrato'), 2).alias('monto_total_adjudicado_cop'),
        F.countDistinct('id_entidad_sk').alias('entidades_distintas_cliente')
    )
    .withColumn(
        'es_megacontratista',
        F.when(F.col('monto_total_adjudicado_cop') >= 5000000000, F.lit(True)).otherwise(F.lit(False))
    )
    .withColumn('_gold_processed_at', F.current_timestamp())
)

spark.sql(f'DROP TABLE IF EXISTS {MART_CONTRATISTAS}')
mart_contratistas.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_CONTRATISTAS)
print(f'✅ {MART_CONTRATISTAS} persistido exitosamente con {spark.table(MART_CONTRATISTAS).count():,} filas.')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 💰 5. DATA MART: EFICIENCIA Y EJECUCIÓN FINANCIERA
# =====================================================================
print(f'Construyendo {MART_FINANCIERO}...')

mart_financiero = (
    df_fact.filter(F.col('anno_firma') >= 2015)
    .groupBy(
        'tipo_contrato',
        'estado_contrato',
        'rango_cuantia',
        'anno_firma'
    )
    .agg(
        F.count('*').alias('total_contratos'),
        F.round(F.sum('valor_contrato'), 2).alias('monto_contratado_cop'),
        F.round(F.sum('valor_pagado'), 2).alias('monto_pagado_cop'),
        F.round(F.sum('valor_facturado'), 2).alias('monto_facturado_cop'),
        F.round(F.sum('valor_pendiente_pago'), 2).alias('saldo_pendiente_pago_cop'),
        F.round(F.sum('valor_anticipo'), 2).alias('total_anticipos_cop')
    )
    .withColumn(
        'tasa_pago_efectivo_pct',
        F.round((F.col('monto_pagado_cop') / F.when(F.col('monto_contratado_cop') > 0, F.col('monto_contratado_cop')).otherwise(1.0)) * 100, 2)
    )
    .withColumn('_gold_processed_at', F.current_timestamp())
)

spark.sql(f'DROP TABLE IF EXISTS {MART_FINANCIERO}')
mart_financiero.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_FINANCIERO)
print(f'✅ {MART_FINANCIERO} persistido exitosamente con {spark.table(MART_FINANCIERO).count():,} filas.')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================
# 🏆 6. RESUMEN ANALÍTICO Y VERIFICACIÓN CAPA GOLD
# =====================================================================
print('================================================================')
print('🥇 RESUMEN DE DATA MARTS DISPONIBLES EN CAPA GOLD')
print('================================================================')
c_terr = spark.table(MART_TERRITORIAL).count()
c_trans = spark.table(MART_TRANSPARENCIA).count()
c_prov = spark.table(MART_CONTRATISTAS).count()
c_fin = spark.table(MART_FINANCIERO).count()

print(f'1. {MART_TERRITORIAL}:     {c_terr:,} filas (Agrupación Depto/Municipio)')
print(f'2. {MART_TRANSPARENCIA}:   {c_trans:,} filas (Índice Contratación Directa)')
print(f'3. {MART_CONTRATISTAS}:    {c_prov:,} filas (Top Megacontratistas)')
print(f'4. {MART_FINANCIERO}:        {c_fin:,} filas (Flujo de Caja y Pagos)')
print('================================================================')

# Muestra de Top Departamentos con mayor inversión en mart_gasto_territorial
display(
    spark.table(MART_TERRITORIAL)
    .groupBy('departamento_norm')
    .agg(
        F.sum('total_contratos').alias('total_contratos'),
        F.round(F.sum('inversion_total_cop'), 2).alias('inversion_acumulada_cop')
    )
    .orderBy(F.desc('inversion_acumulada_cop'))
    .limit(10)
)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
