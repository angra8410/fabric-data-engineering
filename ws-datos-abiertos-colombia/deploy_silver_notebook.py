"""
Deploy Silver Transformation Notebook for SECOP II (Datos Abiertos Colombia) directly to Microsoft Fabric.
Connects via Fabric REST API using Azure CLI credentials.
Workspace: ws-datos-abiertos-colombia (2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e)
Source Lakehouse (Bronze): datos_abiertos_lh_dev (f95e26b3-c404-4e86-be37-c64906ebe3f9)
Target Lakehouse (Silver): datos_abiertos_silver_lh_dev (dee59c18-2af7-4f0f-9100-fd6655a63309)
"""

import base64
import json
import subprocess
import urllib.error
import urllib.request


def get_fabric_token() -> str:
    proc = subprocess.run(
        ["az.cmd", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)["accessToken"]


def main():
    print("🔑 Obteniendo token de autenticación de Azure para Microsoft Fabric...")
    token = get_fabric_token()

    workspace_id = "2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e"
    bronze_lh_id = "f95e26b3-c404-4e86-be37-c64906ebe3f9"
    silver_lh_id = "dee59c18-2af7-4f0f-9100-fd6655a63309"
    notebook_name = "nb_silver_transform_secop"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 1. Verificar si el Notebook ya existe en el Workspace
    list_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
    req = urllib.request.Request(list_url, headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        items = json.loads(resp.read().decode("utf-8")).get("value", [])

    item_id = None
    for it in items:
        if it.get("displayName") == notebook_name and it.get("type") == "Notebook":
            item_id = it["id"]
            break

    if not item_id:
        print(f"📦 Creando nuevo Notebook '{notebook_name}' en workspace {workspace_id}...")
        create_body = {
            "displayName": notebook_name,
            "type": "Notebook",
            "description": "Transformación Medallion Silver: Modelo Estrella (fact_contratos, dim_entidades, dim_proveedores, dim_geografia)",
        }
        req = urllib.request.Request(
            list_url,
            data=json.dumps(create_body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            item_id = res["id"]
            print(f"✅ Notebook creado con ID: {item_id}")
    else:
        print(f"🔍 Notebook '{notebook_name}' encontrado con ID: {item_id}")

    # 2. Construir la estructura completa del Jupyter Notebook (.ipynb)
    notebook_json = {
        "nbformat": 4,
        "nbformat_minor": 2,
        "metadata": {
            "language_info": {"name": "python"},
            "dependencies": {
                "lakehouse": {
                    "default_lakehouse": silver_lh_id,
                    "default_lakehouse_name": "datos_abiertos_silver_lh_dev",
                    "default_lakehouse_workspace_id": workspace_id,
                    "known_lakehouses": [
                        {"id": silver_lh_id},
                        {"id": bronze_lh_id},
                    ],
                }
            },
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 🇨🇴 Capa Silver: Transformación y Modelo Estrella SECOP II\n",
                    "### Medallion Architecture: Bronze (`datos_abiertos_lh_dev`) ➔ Silver (`datos_abiertos_silver_lh_dev`)\n",
                    "Este notebook implementa el desarrollo guiado por especificaciones (**Spec-Driven Development**) definido en `spec.md` (RF-06, RF-07, RF-08) y `decisions.md` (ADR-005, ADR-006, ADR-007):\n",
                    "- **Origen:** 6,013,832 contratos crudos en `bronze_secop_contratos`.\n",
                    "- **Destino:** Lakehouse dedicado `datos_abiertos_silver_lh_dev`.\n",
                    "- **Modelo Dimensional Estrella:**\n",
                    "  1. `fact_contratos`: Métricas monetarias, duraciones, rangos de cuantía y claves foráneas.\n",
                    "  2. `dim_entidades`: Catálogo maestro de entidades estatales (Nacional/Territorial, Sectores).\n",
                    "  3. `dim_proveedores`: Directorio deduplicado de contratistas adjudicados y representantes legales.\n",
                    "  4. `dim_geografia`: Normalización geográfica de departamentos y municipios de Colombia.\n",
                    "- **Reglas de Calidad:** Preservación del 100% histórico con bandera `es_cuantia_cero = True` para contratos <= $0 o nulos."
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"tags": ["parameters"]},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# ⚙️ CELDA DE PARÁMETROS Y CONFIGURACIÓN MEDALLION\n",
                    "# =====================================================================\n",
                    "# Identificadores canónicos de Microsoft Fabric\n",
                    "WORKSPACE_ID = '2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e'     # ws-datos-abiertos-colombia\n",
                    "BRONZE_LH_ID = 'f95e26b3-c404-4e86-be37-c64906ebe3f9'     # datos_abiertos_lh_dev\n",
                    "BRONZE_TABLE = 'bronze_secop_contratos'\n",
                    "\n",
                    "# Tablas destino en Silver (se persisten en el default lakehouse: datos_abiertos_silver_lh_dev)\n",
                    "FACT_TABLE = 'fact_contratos'\n",
                    "DIM_ENTIDADES_TABLE = 'dim_entidades'\n",
                    "DIM_PROVEEDORES_TABLE = 'dim_proveedores'\n",
                    "DIM_GEOGRAFIA_TABLE = 'dim_geografia'\n",
                    "\n",
                    "# Ruta canónica OneLake ABFSS inter-lakehouse (con esquema dbo habilitado)\n",
                    "BRONZE_PATH = f'abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{BRONZE_LH_ID}/Tables/dbo/{BRONZE_TABLE}'\n",
                    "\n",
                    "print(f'🚀 Origen canónico Bronze OneLake: {BRONZE_PATH}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 📥 1. LECTURA Y PERFILAMIENTO INICIAL DE LA CAPA BRONZE\n",
                    "# =====================================================================\n",
                    "from pyspark.sql import functions as F\n",
                    "from pyspark.sql.types import *\n",
                    "\n",
                    "print(f'Cargando 6 millones de registros desde Bronze OneLake: {BRONZE_PATH}...')\n",
                    "df_raw = spark.read.format('delta').load(BRONZE_PATH)\n",
                    "\n",
                    "total_bronze = df_raw.count()\n",
                    "print(f'✅ Total registros cargados desde Bronze: {total_bronze:,}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🧹 2. LIMPIEZA, NORMALIZACIÓN Y ENRIQUECIMIENTO BASE\n",
                    "# =====================================================================\n",
                    "# Función de limpieza textual: mayúsculas, sin espacios redundantes\n",
                    "def clean_str(col_name):\n",
                    "    return F.upper(F.trim(F.coalesce(F.col(col_name), F.lit('NO DEFINIDO'))))\n",
                    "\n",
                    "# Conversión monetaria segura a Double\n",
                    "def parse_currency(col_name):\n",
                    "    return F.coalesce(\n",
                    "        F.regexp_replace(F.col(col_name), '[^0-9.]', '').cast(DoubleType()),\n",
                    "        F.lit(0.0)\n",
                    "    )\n",
                    "\n",
                    "# Dataset base con tipos estandarizados\n",
                    "df_base = df_raw.select(\n",
                    "    # Identificadores de negocio\n",
                    "    clean_str('id_contrato').alias('id_contrato'),\n",
                    "    clean_str('proceso_de_compra').alias('proceso_de_compra'),\n",
                    "    clean_str('referencia_del_contrato').alias('referencia_contrato'),\n",
                    "    clean_str('estado_contrato').alias('estado_contrato'),\n",
                    "    clean_str('tipo_de_contrato').alias('tipo_contrato'),\n",
                    "    clean_str('modalidad_de_contratacion').alias('modalidad_contratacion'),\n",
                    "    clean_str('justificacion_modalidad_de').alias('justificacion_modalidad'),\n",
                    "    \n",
                    "    # Entidades estatales\n",
                    "    clean_str('nit_entidad').alias('nit_entidad'),\n",
                    "    clean_str('nombre_entidad').alias('nombre_entidad'),\n",
                    "    clean_str('orden').alias('orden_entidad'),\n",
                    "    clean_str('sector').alias('sector_entidad'),\n",
                    "    clean_str('rama').alias('rama_entidad'),\n",
                    "    clean_str('entidad_centralizada').alias('entidad_centralizada'),\n",
                    "    \n",
                    "    # Proveedores / Contratistas (Nombres exactos de SECOP II)\n",
                    "    clean_str('tipodocproveedor').alias('tipo_doc_proveedor'),\n",
                    "    clean_str('documento_proveedor').alias('nit_cc_proveedor'),\n",
                    "    clean_str('proveedor_adjudicado').alias('nombre_proveedor'),\n",
                    "    clean_str('nombre_representante_legal').alias('nombre_representante'),\n",
                    "    clean_str('identificaci_n_representante_legal').alias('nit_cc_representante'),\n",
                    "    clean_str('g_nero_representante_legal').alias('genero_representante'),\n",
                    "    \n",
                    "    # Ubicación geográfica\n",
                    "    clean_str('departamento').alias('departamento'),\n",
                    "    clean_str('ciudad').alias('ciudad'),\n",
                    "    clean_str('localizaci_n').alias('localizacion'),\n",
                    "    \n",
                    "    # Fechas parseadas a DateType\n",
                    "    F.to_date(F.col('fecha_de_firma')).alias('fecha_firma'),\n",
                    "    F.to_date(F.col('fecha_de_inicio_del_contrato')).alias('fecha_inicio'),\n",
                    "    F.to_date(F.col('fecha_de_fin_del_contrato')).alias('fecha_fin'),\n",
                    "    \n",
                    "    # Métricas monetarias\n",
                    "    parse_currency('valor_del_contrato').alias('valor_contrato'),\n",
                    "    parse_currency('valor_pagado').alias('valor_pagado'),\n",
                    "    parse_currency('valor_facturado').alias('valor_facturado'),\n",
                    "    parse_currency('valor_pendiente_de_pago').alias('valor_pendiente_pago'),\n",
                    "    parse_currency('valor_de_pago_adelantado').alias('valor_anticipo')\n",
                    ")\n",
                    "\n",
                    "print('✅ Limpieza base completada.')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🏛️ 3. DIMENSIÓN ENTIDADES PÚBLICAS (dim_entidades)\n",
                    "# =====================================================================\n",
                    "print('Construyendo dim_entidades con Surrogate Key numérica (BIGINT)...')\n",
                    "\n",
                    "df_entidades = (\n",
                    "    df_base.select(\n",
                    "        'nit_entidad',\n",
                    "        'nombre_entidad',\n",
                    "        'orden_entidad',\n",
                    "        'sector_entidad',\n",
                    "        'rama_entidad',\n",
                    "        'entidad_centralizada'\n",
                    "    )\n",
                    "    .dropDuplicates(['nit_entidad', 'nombre_entidad'])\n",
                    "    .withColumn(\n",
                    "        'id_entidad_sk',\n",
                    "        F.xxhash64(F.col('nit_entidad'), F.col('nombre_entidad'))\n",
                    "    )\n",
                    ")\n",
                    "\n",
                    "df_entidades.write.format('delta').mode('overwrite').saveAsTable(DIM_ENTIDADES_TABLE)\n",
                    "count_entidades = spark.table(DIM_ENTIDADES_TABLE).count()\n",
                    "print(f'✅ dim_entidades persistida con éxito. Total entidades únicas: {count_entidades:,}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🏢 4. DIMENSIÓN PROVEEDORES Y CONTRATISTAS (dim_proveedores)\n",
                    "# =====================================================================\n",
                    "print('Construyendo dim_proveedores con Surrogate Key numérica (BIGINT)...')\n",
                    "\n",
                    "df_proveedores = (\n",
                    "    df_base.select(\n",
                    "        'tipo_doc_proveedor',\n",
                    "        'nit_cc_proveedor',\n",
                    "        'nombre_proveedor',\n",
                    "        'nombre_representante',\n",
                    "        'nit_cc_representante',\n",
                    "        'genero_representante'\n",
                    "    )\n",
                    "    .dropDuplicates(['tipo_doc_proveedor', 'nit_cc_proveedor'])\n",
                    "    .withColumn(\n",
                    "        'id_proveedor_sk',\n",
                    "        F.xxhash64(F.col('tipo_doc_proveedor'), F.col('nit_cc_proveedor'))\n",
                    "    )\n",
                    ")\n",
                    "\n",
                    "df_proveedores.write.format('delta').mode('overwrite').saveAsTable(DIM_PROVEEDORES_TABLE)\n",
                    "count_proveedores = spark.table(DIM_PROVEEDORES_TABLE).count()\n",
                    "print(f'✅ dim_proveedores persistida con éxito. Total proveedores únicos: {count_proveedores:,}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 📍 5. DIMENSIÓN GEOGRAFÍA DE COLOMBIA (dim_geografia)\n",
                    "# =====================================================================\n",
                    "print('Construyendo dim_geografia con Surrogate Key numérica (BIGINT)...')\n",
                    "\n",
                    "# Normalización de tildes para municipios y departamentos\n",
                    "def remove_accents(c):\n",
                    "    return F.translate(c, 'ÁÉÍÓÚáéíóúÑñÜü', 'AEIOUAEIOUNNUU')\n",
                    "\n",
                    "df_geografia = (\n",
                    "    df_base.select(\n",
                    "        remove_accents(F.col('departamento')).alias('departamento_norm'),\n",
                    "        remove_accents(F.col('ciudad')).alias('ciudad_norm'),\n",
                    "        'localizacion'\n",
                    "    )\n",
                    "    .dropDuplicates(['departamento_norm', 'ciudad_norm'])\n",
                    "    .withColumn(\n",
                    "        'id_geografia_sk',\n",
                    "        F.xxhash64(F.col('departamento_norm'), F.col('ciudad_norm'))\n",
                    "    )\n",
                    ")\n",
                    "\n",
                    "df_geografia.write.format('delta').mode('overwrite').saveAsTable(DIM_GEOGRAFIA_TABLE)\n",
                    "count_geografia = spark.table(DIM_GEOGRAFIA_TABLE).count()\n",
                    "print(f'✅ dim_geografia persistida con éxito. Total ubicaciones únicas: {count_geografia:,}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 📊 6. TABLA DE HECHOS: fact_contratos (CON SURROGATE KEYS NUMÉRICAS)\n",
                    "# =====================================================================\n",
                    "print('Construyendo fact_contratos con llaves foráneas numéricas BIGINT...')\n",
                    "\n",
                    "# Claves subrogadas numéricas de 64 bits (xxhash64) para máximo rendimiento VertiPaq\n",
                    "df_fact = (\n",
                    "    df_base\n",
                    "    .withColumn('id_entidad_sk', F.xxhash64(F.col('nit_entidad'), F.col('nombre_entidad')))\n",
                    "    .withColumn('id_proveedor_sk', F.xxhash64(F.col('tipo_doc_proveedor'), F.col('nit_cc_proveedor')))\n",
                    "    .withColumn('id_geografia_sk', F.xxhash64(remove_accents(F.col('departamento')), remove_accents(F.col('ciudad'))))\n",
                    "    \n",
                    "    # Regla de Negocio ADR-007: Bandera de cuantía cero o nula\n",
                    "    .withColumn('es_cuantia_cero', F.when(F.col('valor_contrato') <= 0, F.lit(True)).otherwise(F.lit(False)))\n",
                    "    \n",
                    "    # Duración del contrato en días\n",
                    "    .withColumn('duracion_dias', F.coalesce(F.datediff(F.col('fecha_fin'), F.col('fecha_inicio')), F.lit(0)))\n",
                    "    \n",
                    "    # Partición temporal de análisis\n",
                    "    .withColumn('anno_firma', F.coalesce(F.year(F.col('fecha_firma')), F.lit(1900)))\n",
                    "    .withColumn('mes_firma', F.coalesce(F.month(F.col('fecha_firma')), F.lit(0)))\n",
                    "    \n",
                    "    # Clasificación por Rango de Cuantía oficial de contratación\n",
                    "    .withColumn(\n",
                    "        'rango_cuantia',\n",
                    "        F.when(F.col('es_cuantia_cero') == True, F.lit('0. Sin Cuantía / Indeterminada'))\n",
                    "        .when(F.col('valor_contrato') < 50000000, F.lit('1. Mínima Cuantía (< $50M)'))\n",
                    "        .when(F.col('valor_contrato') < 500000000, F.lit('2. Menor Cuantía ($50M - $500M)'))\n",
                    "        .when(F.col('valor_contrato') < 5000000000, F.lit('3. Mayor Cuantía ($500M - $5.000M)'))\n",
                    "        .otherwise(F.lit('4. Megacontratos (> $5.000M)'))\n",
                    "    )\n",
                    "    .withColumn('_silver_processed_at', F.current_timestamp())\n",
                    "    \n",
                    "    # Selección final optimizada para el Data Warehouse\n",
                    "    .select(\n",
                    "        'id_contrato',\n",
                    "        'proceso_de_compra',\n",
                    "        'referencia_contrato',\n",
                    "        'id_entidad_sk',\n",
                    "        'id_proveedor_sk',\n",
                    "        'id_geografia_sk',\n",
                    "        'estado_contrato',\n",
                    "        'tipo_contrato',\n",
                    "        'modalidad_contratacion',\n",
                    "        'fecha_firma',\n",
                    "        'fecha_inicio',\n",
                    "        'fecha_fin',\n",
                    "        'anno_firma',\n",
                    "        'mes_firma',\n",
                    "        'duracion_dias',\n",
                    "        'valor_contrato',\n",
                    "        'valor_pagado',\n",
                    "        'valor_facturado',\n",
                    "        'valor_pendiente_pago',\n",
                    "        'valor_anticipo',\n",
                    "        'es_cuantia_cero',\n",
                    "        'rango_cuantia',\n",
                    "        '_silver_processed_at'\n",
                    "    )\n",
                    ")\n",
                    "\n",
                    "# Persistencia particionada por año de firma para máxima velocidad de consulta en Power BI\n",
                    "print('Persistiendo fact_contratos particionada por anno_firma...')\n",
                    "(\n",
                    "    df_fact.write\n",
                    "    .format('delta')\n",
                    "    .mode('overwrite')\n",
                    "    .partitionBy('anno_firma')\n",
                    "    .saveAsTable(FACT_TABLE)\n",
                    ")\n",
                    "\n",
                    "count_fact = spark.table(FACT_TABLE).count()\n",
                    "print(f'🎉 fact_contratos persistida con éxito. Total filas: {count_fact:,}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🔍 7. AUDITORÍA Y MATRIZ DE INTEGRIDAD CAPA SILVER\n",
                    "# =====================================================================\n",
                    "print('================================================================')\n",
                    "print('🏛️ RESUMEN ANALÍTICO DEL MODELO ESTRELLA (CAPA SILVER)')\n",
                    "print('================================================================')\n",
                    "c_bronze = total_bronze\n",
                    "c_fact = spark.table(FACT_TABLE).count()\n",
                    "c_ent = spark.table(DIM_ENTIDADES_TABLE).count()\n",
                    "c_prov = spark.table(DIM_PROVEEDORES_TABLE).count()\n",
                    "c_geo = spark.table(DIM_GEOGRAFIA_TABLE).count()\n",
                    "\n",
                    "print(f'1. Total Contratos en Bronze:     {c_bronze:,}')\n",
                    "print(f'2. Total Contratos en fact (100%): {c_fact:,}')\n",
                    "print(f'3. Entidades Públicas Únicas:     {c_ent:,}')\n",
                    "print(f'4. Proveedores / Contratistas:    {c_prov:,}')\n",
                    "print(f'5. Ubicaciones Geográficas:       {c_geo:,}')\n",
                    "print(f'6. Integridad de Filas:           {\"✅ 100% Exacto\" if c_bronze == c_fact else \"⚠️ Discrepancia detectada\"}')\n",
                    "print('================================================================')\n",
                    "\n",
                    "# Distribución por Rango de Cuantía\n",
                    "display(\n",
                    "    spark.table(FACT_TABLE)\n",
                    "    .groupBy('rango_cuantia')\n",
                    "    .agg(\n",
                    "        F.count('*').alias('cantidad_contratos'),\n",
                    "        F.round(F.sum('valor_contrato'), 2).alias('valor_total_cop')\n",
                    "    )\n",
                    "    .orderBy('rango_cuantia')\n",
                    ")\n"
                ],
            },
        ],
    }

    # 3. Serializar y codificar en Base64
    payload_b64 = base64.b64encode(json.dumps(notebook_json).encode("utf-8")).decode("utf-8")

    # 4. Enviar actualización de definición a la API de Microsoft Fabric
    update_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{item_id}/updateDefinition"
    update_body = {
        "definition": {
            "format": "ipynb",
            "parts": [
                {
                    "path": "notebook-content.ipynb",
                    "payload": payload_b64,
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }

    print(f"🚀 Desplegando definición completa de '{notebook_name}' en Microsoft Fabric...")
    req = urllib.request.Request(
        update_url,
        data=json.dumps(update_body).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"🎉 ¡Éxito! Notebook '{notebook_name}' desplegado y configurado en Microsoft Fabric.")
            print(f"📍 Workspace: ws-datos-abiertos-colombia ({workspace_id})")
            print(f"📍 Lakehouse Silver enlazado: datos_abiertos_silver_lh_dev ({silver_lh_id})")
            print(f"📍 Estado HTTP de Fabric API: {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"❌ Error al actualizar definición del Notebook: HTTP {e.code}")
        print(e.read().decode("utf-8"))


if __name__ == "__main__":
    main()
