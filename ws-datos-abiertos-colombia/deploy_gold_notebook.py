"""
Deploy Gold Marts Transformation Notebook for SECOP II (Datos Abiertos Colombia) directly to Microsoft Fabric.
Connects via Fabric REST API using Azure CLI credentials.
Workspace: ws-datos-abiertos-colombia (2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e)
Source Lakehouse (Silver): datos_abiertos_silver_lh_dev (dee59c18-2af7-4f0f-9100-fd6655a63309)
Target Lakehouse (Gold): datos_abiertos_gold_lh_dev (836d80d4-d5f4-45b2-9fe2-22051b2cf93a)
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
    silver_lh_id = "dee59c18-2af7-4f0f-9100-fd6655a63309"
    gold_lh_id = "836d80d4-d5f4-45b2-9fe2-22051b2cf93a"
    notebook_name = "nb_gold_build_marts"

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
            "description": "Capa Gold: Construcción de Data Marts temáticos (Gasto Territorial, Transparencia, Contratistas, Ejecución Financiera)",
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
                    "default_lakehouse": gold_lh_id,
                    "default_lakehouse_name": "datos_abiertos_gold_lh_dev",
                    "default_lakehouse_workspace_id": workspace_id,
                    "known_lakehouses": [
                        {"id": gold_lh_id},
                        {"id": silver_lh_id},
                    ],
                }
            },
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 🥇 Capa Gold: Data Marts Temáticos de Contratación Pública (SECOP II)\n",
                    "### Medallion Architecture: Silver (`datos_abiertos_silver_lh_dev`) ➔ Gold (`datos_abiertos_gold_lh_dev`)\n",
                    "Este notebook construye los **Data Marts temáticos de alta gerencia** definidos en `spec.md` (RF-09, RF-10) y `decisions.md` (ADR-008):\n",
                    "1. **`mart_gasto_territorial`:** Inversión pública por Departamento, Municipio, Año y Mes para mapas en Power BI.\n",
                    "2. **`mart_transparencia_modalidades`:** Índice de contratación directa (\"a dedo\") vs. licitaciones por entidad estatal.\n",
                    "3. **`mart_concentracion_proveedores`:** Monitoreo de megacontratistas y concentración de presupuesto por sector.\n",
                    "4. **`mart_ejecucion_financiera`:** Análisis de pagos efectivos, anticipos, cartera pendiente y liquidez pública.\n",
                    "\n",
                    "Todas las tablas son optimizadas automáticamente con el motor columnar **V-Order** para responder en milisegundos en **Power BI Direct Lake**."
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"tags": ["parameters"]},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# ⚙️ CONFIGURACIÓN Y RUTAS CANÓNICAS ONELAKE\n",
                    "# =====================================================================\n",
                    "WORKSPACE_ID = '2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e'     # ws-datos-abiertos-colombia\n",
                    "SILVER_LH_ID = 'dee59c18-2af7-4f0f-9100-fd6655a63309'     # datos_abiertos_silver_lh_dev\n",
                    "GOLD_LH_ID   = '836d80d4-d5f4-45b2-9fe2-22051b2cf93a'     # datos_abiertos_gold_lh_dev\n",
                    "\n",
                    "# Ruta canónica de lectura de las 4 tablas dimensionales en Silver\n",
                    "SILVER_BASE = f'abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{SILVER_LH_ID}/Tables'\n",
                    "\n",
                    "FACT_CONTRATOS_PATH = f'{SILVER_BASE}/fact_contratos'\n",
                    "DIM_ENTIDADES_PATH  = f'{SILVER_BASE}/dim_entidades'\n",
                    "DIM_PROVEEDORES_PATH = f'{SILVER_BASE}/dim_proveedores'\n",
                    "DIM_GEOGRAFIA_PATH  = f'{SILVER_BASE}/dim_geografia'\n",
                    "\n",
                    "# Nombres de los Data Marts destino en Gold\n",
                    "MART_TERRITORIAL     = 'mart_gasto_territorial'\n",
                    "MART_TRANSPARENCIA   = 'mart_transparencia_modalidades'\n",
                    "MART_CONTRATISTAS    = 'mart_concentracion_proveedores'\n",
                    "MART_FINANCIERO      = 'mart_ejecucion_financiera'\n",
                    "\n",
                    "print(f'🚀 Origen Silver OneLake: {SILVER_BASE}')\n",
                    "print(f'🎯 Destino Gold Lakehouse: datos_abiertos_gold_lh_dev')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 📥 1. LECTURA DE LAS TABLAS DEL MODELO ESTRELLA SILVER\n",
                    "# =====================================================================\n",
                    "from pyspark.sql import functions as F\n",
                    "from pyspark.sql.types import *\n",
                    "\n",
                    "# Configuración oficial de compatibilidad para Parquet DateTime\n",
                    "spark.conf.set('spark.sql.parquet.datetimeRebaseModeInWrite', 'CORRECTED')\n",
                    "spark.conf.set('spark.sql.parquet.int96RebaseModeInWrite', 'CORRECTED')\n",
                    "\n",
                    "print('Cargando tablas curadas desde Silver...')\n",
                    "df_fact = spark.read.format('delta').load(FACT_CONTRATOS_PATH)\n",
                    "df_entidades = spark.read.format('delta').load(DIM_ENTIDADES_PATH)\n",
                    "df_proveedores = spark.read.format('delta').load(DIM_PROVEEDORES_PATH)\n",
                    "df_geografia = spark.read.format('delta').load(DIM_GEOGRAFIA_PATH)\n",
                    "\n",
                    "print(f'✅ fact_contratos:   {df_fact.count():,} registros')\n",
                    "print(f'✅ dim_entidades:     {df_entidades.count():,} entidades')\n",
                    "print(f'✅ dim_proveedores:   {df_proveedores.count():,} contratistas')\n",
                    "print(f'✅ dim_geografia:     {df_geografia.count():,} municipios/deptos')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🗺️ 2. DATA MART: GASTO TERRITORIAL Y DEPARTAMENTAL\n",
                    "# =====================================================================\n",
                    "print(f'Construyendo {MART_TERRITORIAL}...')\n",
                    "# Mapeo oficial de las 5 Regiones Naturales de Colombia\n",
                    "def get_region(dpto):\n",
                    "    return (\n",
                    "        F.when(dpto.isin('ATLANTICO', 'BOLIVAR', 'CESAR', 'CORDOBA', 'LA GUAJIRA', 'MAGDALENA', 'SUCRE', 'SAN ANDRES, PROVIDENCIA Y SANTA CATALINA'), F.lit('Región Caribe'))\n",
                    "        .when(dpto.isin('ANTIOQUIA', 'BOYACA', 'CALDAS', 'CUNDINAMARCA', 'DISTRITO CAPITAL DE BOGOTA', 'HUILA', 'NORTE DE SANTANDER', 'QUINDIO', 'RISARALDA', 'SANTANDER', 'TOLIMA'), F.lit('Región Andina'))\n",
                    "        .when(dpto.isin('CAUCA', 'CHOCO', 'NARINO', 'VALLE DEL CAUCA'), F.lit('Región Pacífica'))\n",
                    "        .when(dpto.isin('ARAUCA', 'CASANARE', 'META', 'VICHADA'), F.lit('Región Orinoquía'))\n",
                    "        .when(dpto.isin('AMAZONAS', 'CAQUETA', 'GUAINIA', 'GUAVIARE', 'PUTUMAYO', 'VAUPES'), F.lit('Región Amazonía'))\n",
                    "        .otherwise(F.lit('Otra / No Definida'))\n",
                    "    )\n",
                    "\n",
                    "mart_territorial = (\n",
                    "    df_fact.filter(F.col('anno_firma') >= 2015)\n",
                    "    .join(df_geografia, on='id_geografia_sk', how='inner')\n",
                    "    .withColumn('region_natural', get_region(F.col('departamento_norm')))\n",
                    "    .groupBy(\n",
                    "        'region_natural',\n",
                    "        'departamento_norm',\n",
                    "        'ciudad_norm',\n",
                    "        'anno_firma',\n",
                    "        'mes_firma'\n",
                    "    )\n",
                    "    .agg(\n",
                    "        F.count('*').alias('total_contratos'),\n",
                    "        F.round(F.sum('valor_contrato'), 2).alias('inversion_total_cop'),\n",
                    "        F.round(F.avg('valor_contrato'), 2).alias('gasto_promedio_contrato'),\n",
                    "        F.round(F.sum('valor_pagado'), 2).alias('total_pagado_cop'),\n",
                    "        F.sum(F.when(F.col('rango_cuantia').like('%Megacontratos%'), 1).otherwise(0)).alias('contratos_megacuantia'),\n",
                    "        F.round(F.avg('duracion_dias'), 1).alias('duracion_promedio_dias')\n",
                    "    )\n",
                    "    .withColumn('_gold_processed_at', F.current_timestamp())\n",
                    ")\n",
                    "\n",
                    "spark.sql(f'DROP TABLE IF EXISTS {MART_TERRITORIAL}')\n",
                    "mart_territorial.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_TERRITORIAL)\n",
                    "print(f'✅ {MART_TERRITORIAL} persistido exitosamente con {spark.table(MART_TERRITORIAL).count():,} filas.')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# ⚖️ 3. DATA MART: TRANSPARENCIA Y MODALIDADES DE CONTRATACIÓN\n",
                    "# =====================================================================\n",
                    "print(f'Construyendo {MART_TRANSPARENCIA}...')\n",
                    "\n",
                    "mart_transparencia = (\n",
                    "    df_fact.filter(F.col('anno_firma') >= 2015)\n",
                    "    .join(df_entidades, on='id_entidad_sk', how='inner')\n",
                    "    .groupBy(\n",
                    "        'nit_entidad',\n",
                    "        'nombre_entidad',\n",
                    "        'orden_entidad',\n",
                    "        'sector_entidad',\n",
                    "        'modalidad_contratacion',\n",
                    "        'anno_firma'\n",
                    "    )\n",
                    "    .agg(\n",
                    "        F.count('*').alias('total_contratos'),\n",
                    "        F.round(F.sum('valor_contrato'), 2).alias('monto_total_cop'),\n",
                    "        F.round(F.sum('valor_pagado'), 2).alias('monto_pagado_cop'),\n",
                    "        F.sum(F.when(F.col('modalidad_contratacion').like('%DIRECTA%'), 1).otherwise(0)).alias('contratos_directos'),\n",
                    "        F.round(F.sum(F.when(F.col('modalidad_contratacion').like('%DIRECTA%'), F.col('valor_contrato')).otherwise(0.0)), 2).alias('monto_directo_cop')\n",
                    "    )\n",
                    "    .withColumn(\n",
                    "        'pct_contratacion_directa',\n",
                    "        F.round((F.col('monto_directo_cop') / F.when(F.col('monto_total_cop') > 0, F.col('monto_total_cop')).otherwise(1.0)) * 100, 2)\n",
                    "    )\n",
                    "    .withColumn('_gold_processed_at', F.current_timestamp())\n",
                    ")\n",
                    "\n",
                    "spark.sql(f'DROP TABLE IF EXISTS {MART_TRANSPARENCIA}')\n",
                    "mart_transparencia.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_TRANSPARENCIA)\n",
                    "print(f'✅ {MART_TRANSPARENCIA} persistido exitosamente con {spark.table(MART_TRANSPARENCIA).count():,} filas.')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🏢 4. DATA MART: CONCENTRACIÓN Y MEGACONTRATISTAS DEL ESTADO\n",
                    "# =====================================================================\n",
                    "print(f'Construyendo {MART_CONTRATISTAS}...')\n",
                    "\n",
                    "mart_contratistas = (\n",
                    "    df_fact.filter(F.col('anno_firma') >= 2015)\n",
                    "    .join(df_proveedores, on='id_proveedor_sk', how='inner')\n",
                    "    .join(df_entidades.select('id_entidad_sk', 'sector_entidad'), on='id_entidad_sk', how='inner')\n",
                    "    .groupBy(\n",
                    "        'tipo_doc_proveedor',\n",
                    "        'nit_cc_proveedor',\n",
                    "        'nombre_proveedor',\n",
                    "        'sector_entidad',\n",
                    "        'anno_firma'\n",
                    "    )\n",
                    "    .agg(\n",
                    "        F.count('*').alias('total_contratos_ganados'),\n",
                    "        F.round(F.sum('valor_contrato'), 2).alias('monto_total_adjudicado_cop'),\n",
                    "        F.countDistinct('id_entidad_sk').alias('entidades_distintas_cliente')\n",
                    "    )\n",
                    "    .withColumn(\n",
                    "        'es_megacontratista',\n",
                    "        F.when(F.col('monto_total_adjudicado_cop') >= 5000000000, F.lit(True)).otherwise(F.lit(False))\n",
                    "    )\n",
                    "    .withColumn('_gold_processed_at', F.current_timestamp())\n",
                    ")\n",
                    "\n",
                    "spark.sql(f'DROP TABLE IF EXISTS {MART_CONTRATISTAS}')\n",
                    "mart_contratistas.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_CONTRATISTAS)\n",
                    "print(f'✅ {MART_CONTRATISTAS} persistido exitosamente con {spark.table(MART_CONTRATISTAS).count():,} filas.')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 💰 5. DATA MART: EFICIENCIA Y EJECUCIÓN FINANCIERA\n",
                    "# =====================================================================\n",
                    "print(f'Construyendo {MART_FINANCIERO}...')\n",
                    "\n",
                    "mart_financiero = (\n",
                    "    df_fact.filter(F.col('anno_firma') >= 2015)\n",
                    "    .groupBy(\n",
                    "        'tipo_contrato',\n",
                    "        'estado_contrato',\n",
                    "        'rango_cuantia',\n",
                    "        'anno_firma'\n",
                    "    )\n",
                    "    .agg(\n",
                    "        F.count('*').alias('total_contratos'),\n",
                    "        F.round(F.sum('valor_contrato'), 2).alias('monto_contratado_cop'),\n",
                    "        F.round(F.sum('valor_pagado'), 2).alias('monto_pagado_cop'),\n",
                    "        F.round(F.sum('valor_facturado'), 2).alias('monto_facturado_cop'),\n",
                    "        F.round(F.sum('valor_pendiente_pago'), 2).alias('saldo_pendiente_pago_cop'),\n",
                    "        F.round(F.sum('valor_anticipo'), 2).alias('total_anticipos_cop')\n",
                    "    )\n",
                    "    .withColumn(\n",
                    "        'tasa_pago_efectivo_pct',\n",
                    "        F.round((F.col('monto_pagado_cop') / F.when(F.col('monto_contratado_cop') > 0, F.col('monto_contratado_cop')).otherwise(1.0)) * 100, 2)\n",
                    "    )\n",
                    "    .withColumn('_gold_processed_at', F.current_timestamp())\n",
                    ")\n",
                    "\n",
                    "spark.sql(f'DROP TABLE IF EXISTS {MART_FINANCIERO}')\n",
                    "mart_financiero.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(MART_FINANCIERO)\n",
                    "print(f'✅ {MART_FINANCIERO} persistido exitosamente con {spark.table(MART_FINANCIERO).count():,} filas.')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🏆 6. RESUMEN ANALÍTICO Y VERIFICACIÓN CAPA GOLD\n",
                    "# =====================================================================\n",
                    "print('================================================================')\n",
                    "print('🥇 RESUMEN DE DATA MARTS DISPONIBLES EN CAPA GOLD')\n",
                    "print('================================================================')\n",
                    "c_terr = spark.table(MART_TERRITORIAL).count()\n",
                    "c_trans = spark.table(MART_TRANSPARENCIA).count()\n",
                    "c_prov = spark.table(MART_CONTRATISTAS).count()\n",
                    "c_fin = spark.table(MART_FINANCIERO).count()\n",
                    "\n",
                    "print(f'1. {MART_TERRITORIAL}:     {c_terr:,} filas (Agrupación Depto/Municipio)')\n",
                    "print(f'2. {MART_TRANSPARENCIA}:   {c_trans:,} filas (Índice Contratación Directa)')\n",
                    "print(f'3. {MART_CONTRATISTAS}:    {c_prov:,} filas (Top Megacontratistas)')\n",
                    "print(f'4. {MART_FINANCIERO}:        {c_fin:,} filas (Flujo de Caja y Pagos)')\n",
                    "print('================================================================')\n",
                    "\n",
                    "# Muestra de Top Departamentos con mayor inversión en mart_gasto_territorial\n",
                    "display(\n",
                    "    spark.table(MART_TERRITORIAL)\n",
                    "    .groupBy('departamento_norm')\n",
                    "    .agg(\n",
                    "        F.sum('total_contratos').alias('total_contratos'),\n",
                    "        F.round(F.sum('inversion_total_cop'), 2).alias('inversion_acumulada_cop')\n",
                    "    )\n",
                    "    .orderBy(F.desc('inversion_acumulada_cop'))\n",
                    "    .limit(10)\n",
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
            print(f"📍 Lakehouse Gold enlazado: datos_abiertos_gold_lh_dev ({gold_lh_id})")
            print(f"📍 Estado HTTP de Fabric API: {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"❌ Error al actualizar definición del Notebook: HTTP {e.code}")
        print(e.read().decode("utf-8"))


if __name__ == "__main__":
    main()
