"""
Deploy Ingestion Notebook for SECOP II (Datos Abiertos Colombia) directly to Microsoft Fabric.
Connects via Fabric REST API using Azure CLI credentials.
Workspace: ws-datos-abiertos-colombia (2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e)
Lakehouse: datos_abiertos_lh_dev (f95e26b3-c404-4e86-be37-c64906ebe3f9)
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

    workspace_id = "2ba52c07-88c2-43c6-9dc0-1ff1dfb52c6e"  # ws-datos-abiertos-colombia
    lakehouse_id = "f95e26b3-c404-4e86-be37-c64906ebe3f9"  # datos_abiertos_lh_dev
    notebook_name = "nb_bronze_ingest_secop"

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
            "description": "Ingesta masiva e incremental de SECOP II (datos.gov.co) hacia Lakehouse datos_abiertos_lh_dev",
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
                    "default_lakehouse": lakehouse_id,
                    "default_lakehouse_name": "datos_abiertos_lh_dev",
                    "default_lakehouse_workspace_id": workspace_id,
                    "known_lakehouses": [{"id": lakehouse_id}],
                }
            },
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 🇨🇴 Datos Abiertos Colombia - Ingesta Bronze SECOP II\n",
                    "### Medallion Architecture: SODA API -> Fabric Lakehouse (`datos_abiertos_lh_dev`)\n",
                    "Este notebook implementa el desarrollo guiado por especificaciones (**Spec-Driven Development**) definido en `spec.md` y `decisions.md`:\n",
                    "- **Fuente:** Portal oficial de Datos Abiertos Colombia (`datos.gov.co`) - SECOP II Contratos Electrónicos (`jbjy-vk9h`).\n",
                    "- **Estrategia Anticaídas:** Paginación por lotes ($limit, $offset), control de tasa (*throttling*) y reintentos con *Exponential Backoff* ante errores HTTP 429 / 5xx.\n",
                    "- **Sincronización Incremental:** Seguimiento automático de marca de agua (*watermark*) sobre `fecha_de_firma`.\n",
                    "- **Destino:** Tabla Delta Lake `bronze_secop_contratos` en `datos_abiertos_lh_dev` con linaje y auditoría."
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"tags": ["parameters"]},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# ⚙️ CELDA DE PARÁMETROS CONFIGURABLES\n",
                    "# =====================================================================\n",
                    "DATASET_ID = 'jbjy-vk9h'               # Identificador 4x4 SODA (SECOP II)\n",
                    "TARGET_TABLE = 'bronze_secop_contratos' # Tabla Delta en datos_abiertos_lh_dev\n",
                    "BATCH_SIZE = 10000                     # Tamaño de lote por llamada (máx 50,000 en Socrata)\n",
                    "MAX_RECORDS = None                     # None para sincronizar todo, o entero (ej. 50000) para pruebas\n",
                    "WATERMARK_COLUMN = 'fecha_de_firma'    # Columna temporal para filtrado incremental\n",
                    "RATE_LIMIT_DELAY_SEC = 0.5             # Pausa preventiva entre llamadas (segundos)\n",
                    "MAX_RETRIES = 5                        # Reintentos máximos con espera exponencial\n",
                    "APP_TOKEN = None                       # Socrata App Token (opcional para mayor cuota)\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🛡️ MOTOR DE EXTRACCIÓN SODA CON RESILIENCIA Y EXPONENTIAL BACKOFF\n",
                    "# =====================================================================\n",
                    "import json\n",
                    "import time\n",
                    "import urllib.parse\n",
                    "import urllib.request\n",
                    "from datetime import datetime, timezone\n",
                    "from pyspark.sql import functions as F\n",
                    "\n",
                    "class FabricSodaExtractor:\n",
                    "    BASE_URL = 'https://www.datos.gov.co/resource'\n",
                    "    \n",
                    "    def __init__(self, dataset_id, app_token=None, delay=0.5, retries=5):\n",
                    "        self.dataset_id = dataset_id\n",
                    "        self.app_token = app_token\n",
                    "        self.delay = delay\n",
                    "        self.retries = retries\n",
                    "        \n",
                    "    def execute_request(self, params):\n",
                    "        clean_params = {k: v for k, v in params.items() if v is not None}\n",
                    "        url = f'{self.BASE_URL}/{self.dataset_id}.json'\n",
                    "        if clean_params:\n",
                    "            url += f'?{urllib.parse.urlencode(clean_params)}'\n",
                    "            \n",
                    "        headers = {\n",
                    "            'Accept': 'application/json',\n",
                    "            'User-Agent': 'FabricDataEngineering/1.0 (DatosAbiertosColombia; PySpark)'\n",
                    "        }\n",
                    "        if self.app_token:\n",
                    "            headers['X-App-Token'] = self.app_token\n",
                    "            \n",
                    "        attempt = 0\n",
                    "        while attempt <= self.retries:\n",
                    "            try:\n",
                    "                req = urllib.request.Request(url, headers=headers)\n",
                    "                with urllib.request.urlopen(req, timeout=90) as resp:\n",
                    "                    return json.loads(resp.read().decode('utf-8'))\n",
                    "            except urllib.error.HTTPError as e:\n",
                    "                attempt += 1\n",
                    "                status = e.code\n",
                    "                if status in (429, 500, 502, 503, 504) and attempt <= self.retries:\n",
                    "                    wait = max(2.0 ** attempt, 5.0 if status == 429 else 2.0)\n",
                    "                    print(f'⚠️ HTTP {status}. Pausa preventiva de {wait:.1f}s antes de reintentar (intento {attempt}/{self.retries})...')\n",
                    "                    time.sleep(wait)\n",
                    "                else:\n",
                    "                    raise\n",
                    "            except Exception as e:\n",
                    "                attempt += 1\n",
                    "                if attempt <= self.retries:\n",
                    "                    wait = 2.0 ** attempt\n",
                    "                    print(f'⚠️ Error de conexión ({e}). Reintentando en {wait:.1f}s...')\n",
                    "                    time.sleep(wait)\n",
                    "                else:\n",
                    "                    raise\n",
                    "                    \n",
                    "    def get_count(self, where_clause=None):\n",
                    "        res = self.execute_request({'$select': 'count(*)', '$where': where_clause})\n",
                    "        if res and isinstance(res, list) and 'count' in res[0]:\n",
                    "            return int(res[0]['count'])\n",
                    "        return 0\n",
                    "\n",
                    "print('✅ Extractor SODA inicializado correctamente.')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 🔍 ANÁLISIS DE WATERMARK Y RECONOCIMIENTO DEL LAKEHOUSE\n",
                    "# =====================================================================\n",
                    "extractor = FabricSodaExtractor(DATASET_ID, app_token=APP_TOKEN, delay=RATE_LIMIT_DELAY_SEC, retries=MAX_RETRIES)\n",
                    "\n",
                    "watermark_filter = None\n",
                    "is_incremental = False\n",
                    "\n",
                    "try:\n",
                    "    existing_df = spark.table(TARGET_TABLE)\n",
                    "    max_val_row = existing_df.select(F.max(F.col(WATERMARK_COLUMN))).collect()\n",
                    "    max_watermark = max_val_row[0][0] if max_val_row and max_val_row[0][0] else None\n",
                    "    \n",
                    "    if max_watermark:\n",
                    "        watermark_filter = f\"{WATERMARK_COLUMN} > '{max_watermark}'\"\n",
                    "        is_incremental = True\n",
                    "        print(f'📌 Sincronización Incremental activada. Último watermark ({WATERMARK_COLUMN}): {max_watermark}')\n",
                    "    else:\n",
                    "        print('📌 Tabla vacía. Se realizará carga inicial.')\n",
                    "except Exception:\n",
                    "    print(f'📌 La tabla [{TARGET_TABLE}] no existe aún. Iniciando primera creación.')\n",
                    "\n",
                    "total_available = extractor.get_count(where_clause=watermark_filter)\n",
                    "print(f'📊 Registros identificados en datos.gov.co para extracción: {total_available:,}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 📥 DESCARGA POR LOTES, ENRIQUECIMIENTO Y PERSISTENCIA EN DELTA\n",
                    "# =====================================================================\n",
                    "if total_available == 0:\n",
                    "    print('✅ No hay registros nuevos por sincronizar. Proceso completado.')\n",
                    "else:\n",
                    "    offset = 0\n",
                    "    batch_num = 1\n",
                    "    total_written = 0\n",
                    "    batch_run_id = f'run_{int(time.time())}'\n",
                    "    \n",
                    "    while True:\n",
                    "        limit = BATCH_SIZE\n",
                    "        if MAX_RECORDS is not None:\n",
                    "            remaining = MAX_RECORDS - total_written\n",
                    "            if remaining <= 0:\n",
                    "                break\n",
                    "            limit = min(limit, remaining)\n",
                    "            \n",
                    "        print(f'📦 Descargando lote #{batch_num}: offset={offset:,}, limit={limit:,}...')\n",
                    "        batch_data = extractor.execute_request({\n",
                    "            '$limit': limit,\n",
                    "            '$offset': offset,\n",
                    "            '$where': watermark_filter,\n",
                    "            '$order': ':id'\n",
                    "        })\n",
                    "        \n",
                    "        if not batch_data:\n",
                    "            print('🏁 Fin de los datos retornados por el endpoint.')\n",
                    "            break\n",
                    "            \n",
                    "        # Convertir a Spark DataFrame\n",
                    "        batch_rdd = spark.sparkContext.parallelize([json.dumps(row) for row in batch_data])\n",
                    "        batch_df = spark.read.json(batch_rdd)\n",
                    "        \n",
                    "        # Enriquecer con metadatos de auditoría\n",
                    "        enriched_df = (\n",
                    "            batch_df\n",
                    "            .withColumn('_ingestion_timestamp', F.current_timestamp())\n",
                    "            .withColumn('_source_dataset_id', F.lit(DATASET_ID))\n",
                    "            .withColumn('_batch_id', F.lit(f'{batch_run_id}_{batch_num}'))\n",
                    "        )\n",
                    "        \n",
                    "        # Persistir en tabla Delta del Lakehouse\n",
                    "        enriched_df.write.format('delta').mode('append').saveAsTable(TARGET_TABLE)\n",
                    "        \n",
                    "        total_written += len(batch_data)\n",
                    "        offset += len(batch_data)\n",
                    "        batch_num += 1\n",
                    "        print(f'  💾 Guardados {len(batch_data):,} registros en [{TARGET_TABLE}]. Total acumulado: {total_written:,}/{total_available:,}')\n",
                    "        \n",
                    "        if len(batch_data) < limit:\n",
                    "            break\n",
                    "            \n",
                    "        # Pausa preventiva entre lotes (throttling)\n",
                    "        if RATE_LIMIT_DELAY_SEC > 0:\n",
                    "            time.sleep(RATE_LIMIT_DELAY_SEC)\n",
                    "\n",
                    "    print(f'\\n🎉 Ingesta Bronze completada. Total registros persistidos: {total_written:,}')\n"
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =====================================================================\n",
                    "# 📊 RESUMEN Y MUESTRA DE DATOS ATERRIZADOS EN LAKEHOUSE\n",
                    "# =====================================================================\n",
                    "result_df = spark.table(TARGET_TABLE)\n",
                    "count_final = result_df.count()\n",
                    "print(f'🏛️ Total de filas en la tabla Delta [{TARGET_TABLE}]: {count_final:,}')\n",
                    "\n",
                    "display(result_df.select(\n",
                    "    'nombre_entidad',\n",
                    "    'valor_del_contrato',\n",
                    "    'departamento',\n",
                    "    'ciudad',\n",
                    "    'fecha_de_firma',\n",
                    "    '_ingestion_timestamp'\n",
                    ").limit(10))\n"
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

    print(f"🚀 Desplegando definición completa del Notebook en Microsoft Fabric...")
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
            print(f"📍 Lakehouse enlazado: datos_abiertos_lh_dev ({lakehouse_id})")
            print(f"📍 Estado HTTP de Fabric API: {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"❌ Error al actualizar definición del Notebook: HTTP {e.code}")
        print(e.read().decode("utf-8"))


if __name__ == "__main__":
    main()
