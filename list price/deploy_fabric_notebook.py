"""
Deploy Multi-Supplier Price Harmonization Framework Notebook to Microsoft Fabric.
"""

import os
import json
import base64
import subprocess
import urllib.request
import urllib.error


def main():
    # 1. Get Azure Access Token for Fabric API
    token_proc = subprocess.run(
        ["az.cmd", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com"],
        capture_output=True,
        text=True,
        check=True
    )
    token = json.loads(token_proc.stdout)["accessToken"]

    workspace_id = "ace87823-ba3c-4e0d-b5f8-3f051d09dca9"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. Check if notebook already exists
    list_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
    req = urllib.request.Request(list_url, headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        items = json.loads(resp.read().decode("utf-8")).get("value", [])

    item_id = None
    notebook_name = "nb_harmonize_supplier_prices"
    for it in items:
        if it.get("displayName") == notebook_name and it.get("type") == "Notebook":
            item_id = it["id"]
            break

    if not item_id:
        print(f"Creating item {notebook_name}...")
        create_body = {
            "displayName": notebook_name,
            "type": "Notebook"
        }
        req = urllib.request.Request(list_url, data=json.dumps(create_body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            item_id = res["id"]
            print(f"Created notebook item ID: {item_id}")
    else:
        print(f"Found existing notebook item ID: {item_id}")

    # 3. Construct Jupyter Notebook JSON structure
    notebook_json = {
        "nbformat": 4,
        "nbformat_minor": 2,
        "metadata": {
            "language_info": {"name": "python"},
            "dependencies": {
                "lakehouse": {
                    "default_lakehouse": "9f9b4f36-e70e-47a8-853a-e73e6d454649",
                    "default_lakehouse_name": "lh_bronze_ingestion",
                    "default_lakehouse_workspace_id": workspace_id,
                    "known_lakehouses": [
                        {"id": "9f9b4f36-e70e-47a8-853a-e73e6d454649"},
                        {"id": "b26c63f3-de56-4c27-b4e1-1df78b2a5567"},
                        {"id": "0b67fb06-f34c-445c-9e2a-fc7f2dac1d64"}
                    ]
                }
            }
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Multi-Supplier Price Ingestion & Harmonization Framework\n",
                    "### Medallion Architecture: Bronze -> Silver -> Gold (Velykapet)\n",
                    "This notebook dynamically reads heterogeneous price lists (PDF, Excel, CSV) from Bronze, maps each supplier's unique format into a **unified Canonical Schema** in Silver (`dim_supplier_prices`), and generates Gold pricing tables with calculated retail margins."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 1. Install required dependencies\n",
                    "%pip install pypdf openpyxl\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import os\n",
                    "import re\n",
                    "from datetime import datetime\n",
                    "import pandas as pd\n",
                    "from pypdf import PdfReader\n",
                    "from pyspark.sql import functions as F\n",
                    "\n",
                    "print('Loaded dependencies for Multi-Supplier Price Ingestion Framework.')\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Extensible Supplier Parser Registry Pattern\n",
                    "Define custom parsers for each supplier format (PDF, Excel, CSV) without breaking the downstream pipeline."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "class BaseSupplierParser:\n",
                    "    \"\"\"Abstract base class for all supplier price list parsers.\"\"\"\n",
                    "    def __init__(self, supplier_name: str):\n",
                    "        self.supplier_name = supplier_name\n",
                    "\n",
                    "    def parse(self, file_path: str) -> pd.DataFrame:\n",
                    "        raise NotImplementedError('Subclasses must implement parse()')\n",
                    "\n",
                    "\n",
                    "class ItalcolPDFParser(BaseSupplierParser):\n",
                    "    \"\"\"Parser for Italcol PDF price lists with 4 price columns and EAN/Internal code pairs.\"\"\"\n",
                    "    def __init__(self):\n",
                    "        super().__init__('Italcol')\n",
                    "\n",
                    "    def parse(self, file_path: str) -> pd.DataFrame:\n",
                    "        reader = PdfReader(file_path)\n",
                    "        records = []\n",
                    "        current_category = 'GENERAL'\n",
                    "        header_patterns = [\n",
                    "            'LISTA VIGENTE', 'ESTOS PRECIOS', 'PRECIOS SUJETOS', 'PLANTAS',\n",
                    "            'EAN 13', 'COD BARRAS', 'COD INTERNO', 'PRECIO BASE', 'PRECIO antes',\n",
                    "            'precio iva', 'descuento 3%', 'PAGINA'\n",
                    "        ]\n",
                    "        effective_date = '2026-05-01'\n",
                    "\n",
                    "        for page_idx, page in enumerate(reader.pages):\n",
                    "            raw_text = page.extract_text() or ''\n",
                    "            for raw_line in raw_text.split('\\n'):\n",
                    "                line = raw_line.strip()\n",
                    "                if not line or any(h.lower() in line.lower() for h in header_patterns):\n",
                    "                    continue\n",
                    "\n",
                    "                prices = re.findall(r'\\$\\s*[\\d\\.\\,]+', line)\n",
                    "                if not prices:\n",
                    "                    current_category = line\n",
                    "                    continue\n",
                    "\n",
                    "                if len(prices) >= 4:\n",
                    "                    p4_str, p3_str, p2_str, p1_str = prices[-1], prices[-2], prices[-3], prices[-4]\n",
                    "                    idx = line.rfind(prices[-4])\n",
                    "                    prefix = line[:idx].strip()\n",
                    "                    tokens = prefix.split()\n",
                    "\n",
                    "                    if len(tokens) >= 2:\n",
                    "                        if re.match(r'^\\d{8,}$', tokens[0]) or tokens[0].upper() == 'N/A':\n",
                    "                            barcode = tokens[0]\n",
                    "                            internal_code = tokens[1]\n",
                    "                            desc = ' '.join(tokens[2:])\n",
                    "                        else:\n",
                    "                            barcode = 'N/A'\n",
                    "                            internal_code = tokens[0]\n",
                    "                            desc = ' '.join(tokens[1:])\n",
                    "                    else:\n",
                    "                        barcode, internal_code, desc = 'N/A', 'N/A', prefix\n",
                    "\n",
                    "                    p_base = float(p1_str.replace('$', '').replace('.', '').replace(',', '.').strip())\n",
                    "                    p_antes_iva = float(p2_str.replace('$', '').replace('.', '').replace(',', '.').strip())\n",
                    "                    p_con_iva = float(p3_str.replace('$', '').replace('.', '').replace(',', '.').strip())\n",
                    "                    p_final_dto = float(p4_str.replace('$', '').replace('.', '').replace(',', '.').strip())\n",
                    "\n",
                    "                    tax_rate = round(((p_con_iva - p_antes_iva) / p_antes_iva * 100), 1) if p_antes_iva > 0 else 0.0\n",
                    "                    dto_pct = round(((p_con_iva - p_final_dto) / p_con_iva * 100), 1) if p_con_iva > 0 else 0.0\n",
                    "\n",
                    "                    records.append({\n",
                    "                        'supplier_name': self.supplier_name,\n",
                    "                        'supplier_sku': str(internal_code),\n",
                    "                        'barcode_ean': str(barcode),\n",
                    "                        'product_description': desc,\n",
                    "                        'category': current_category,\n",
                    "                        'base_cost': p_base,\n",
                    "                        'price_before_tax': p_antes_iva,\n",
                    "                        'tax_rate_pct': tax_rate,\n",
                    "                        'price_with_tax': p_con_iva,\n",
                    "                        'discount_pct': dto_pct,\n",
                    "                        'final_net_cost': p_final_dto,\n",
                    "                        'effective_date': effective_date,\n",
                    "                        'source_file': os.path.basename(file_path),\n",
                    "                        'ingestion_timestamp': datetime.now().isoformat()\n",
                    "                    })\n",
                    "        return pd.DataFrame(records)\n",
                    "\n",
                    "\n",
                    "class GenericExcelSupplierParser(BaseSupplierParser):\n",
                    "    \"\"\"Parser template for suppliers delivering standard Excel catalogues.\"\"\"\n",
                    "    def __init__(self, supplier_name: str):\n",
                    "        super().__init__(supplier_name)\n",
                    "\n",
                    "    def parse(self, file_path: str) -> pd.DataFrame:\n",
                    "        df_raw = pd.read_excel(file_path)\n",
                    "        records = []\n",
                    "        for _, row in df_raw.iterrows():\n",
                    "            records.append({\n",
                    "                'supplier_name': self.supplier_name,\n",
                    "                'supplier_sku': str(row.get('CODIGO', row.get('SKU', 'N/A'))),\n",
                    "                'barcode_ean': str(row.get('EAN', row.get('BARCODE', 'N/A'))),\n",
                    "                'product_description': str(row.get('DESCRIPCION', row.get('PRODUCTO', ''))),\n",
                    "                'category': str(row.get('CATEGORIA', 'GENERAL')),\n",
                    "                'base_cost': float(row.get('PRECIO_BASE', 0.0)),\n",
                    "                'price_before_tax': float(row.get('PRECIO_NETO', 0.0)),\n",
                    "                'tax_rate_pct': float(row.get('IVA_PCT', 19.0)),\n",
                    "                'price_with_tax': float(row.get('PRECIO_IVA', 0.0)),\n",
                    "                'discount_pct': float(row.get('DESCUENTO_PCT', 0.0)),\n",
                    "                'final_net_cost': float(row.get('PRECIO_FINAL', 0.0)),\n",
                    "                'effective_date': str(row.get('FECHA_VIGENCIA', datetime.now().strftime('%Y-%m-%d'))),\n",
                    "                'source_file': os.path.basename(file_path),\n",
                    "                'ingestion_timestamp': datetime.now().isoformat()\n",
                    "            })\n",
                    "        return pd.DataFrame(records)\n",
                    "\n",
                    "\n",
                    "class ParserRegistry:\n",
                    "    \"\"\"Factory registry for dynamic supplier parser discovery.\"\"\"\n",
                    "    _registry = {\n",
                    "        'italcol': ItalcolPDFParser(),\n",
                    "        'gabrica': GenericExcelSupplierParser('Gabrica'),\n",
                    "        'solla': GenericExcelSupplierParser('Solla'),\n",
                    "    }\n",
                    "\n",
                    "    @classmethod\n",
                    "    def get_parser(cls, supplier_key: str):\n",
                    "        return cls._registry.get(supplier_key.lower())\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Bronze -> Silver Pipeline Execution\n",
                    "Scans `/lakehouse/default/Files/raw/` subdirectories per supplier and transforms all files into the Silver Delta Table (`dim_supplier_prices`)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "bronze_base_path = '/lakehouse/default/Files/raw'\n",
                    "all_standardized_dfs = []\n",
                    "\n",
                    "if os.path.exists(bronze_base_path):\n",
                    "    for supplier_dir in os.listdir(bronze_base_path):\n",
                    "        supplier_path = os.path.join(bronze_base_path, supplier_dir)\n",
                    "        if os.path.isdir(supplier_path):\n",
                    "            parser = ParserRegistry.get_parser(supplier_dir)\n",
                    "            if not parser:\n",
                    "                print(f'[WARN] No parser registered for supplier folder: {supplier_dir}. Skipping.')\n",
                    "                continue\n",
                    "\n",
                    "            for file_name in os.listdir(supplier_path):\n",
                    "                file_path = os.path.join(supplier_path, file_name)\n",
                    "                if file_name.endswith(('.pdf', '.xlsx', '.csv')):\n",
                    "                    print(f'[PROCESSING] {supplier_dir} -> {file_name}...')\n",
                    "                    try:\n",
                    "                        df_parsed = parser.parse(file_path)\n",
                    "                        if not df_parsed.empty:\n",
                    "                            all_standardized_dfs.append(df_parsed)\n",
                    "                            print(f'[SUCCESS] Parsed {len(df_parsed)} rows from {file_name}')\n",
                    "                    except Exception as e:\n",
                    "                        print(f'[ERROR] Failed to parse {file_name}: {e}')\n",
                    "\n",
                    "if all_standardized_dfs:\n",
                    "    combined_pdf = pd.concat(all_standardized_dfs, ignore_index=True)\n",
                    "    spark_silver_df = spark.createDataFrame(combined_pdf)\n",
                    "    \n",
                    "    # Direct OneLake ABFSS path to Silver Lakehouse Tables\n",
                    "    silver_table_path = \"abfss://ws_velykapet_random@onelake.dfs.fabric.microsoft.com/lh_silver_transformation.Lakehouse/Tables/dim_supplier_prices\"\n",
                    "    \n",
                    "    spark_silver_df.write.format(\"delta\") \\\n",
                    "        .mode(\"overwrite\") \\\n",
                    "        .partitionBy(\"supplier_name\") \\\n",
                    "        .save(silver_table_path)\n",
                    "    print(f\"[DELTA] Successfully updated Silver table at {silver_table_path} with {spark_silver_df.count()} total records.\")\n",
                    "    display(spark_silver_df.limit(10))\n",
                    "else:\n",
                    "    print('[INFO] No files found to process.')\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 4. Silver -> Gold Serving Layer\n",
                    "Generates recommended retail prices (PVP) at 25%, 30%, and 35% margin targets."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "silver_table_path = 'abfss://ws_velykapet_random@onelake.dfs.fabric.microsoft.com/lh_silver_transformation.Lakehouse/Tables/dim_supplier_prices'\n",
                    "df_silver = spark.read.format('delta').load(silver_table_path)\n",
                    "\n",
                    "df_gold = df_silver.withColumn(\n",
                    "    'pvp_recommended_25_margin', F.round(F.col('final_net_cost') / (1 - 0.25), 0)\n",
                    ").withColumn(\n",
                    "    'pvp_recommended_30_margin', F.round(F.col('final_net_cost') / (1 - 0.30), 0)\n",
                    ").withColumn(\n",
                    "    'pvp_recommended_35_margin', F.round(F.col('final_net_cost') / (1 - 0.35), 0)\n",
                    ").withColumn(\n",
                    "    'calculated_at', F.current_timestamp()\n",
                    ")\n",
                    "\n",
                    "gold_table_path = 'abfss://ws_velykapet_random@onelake.dfs.fabric.microsoft.com/lh_gold_serving.Lakehouse/Tables/fact_product_pricing_master'\n",
                    "df_gold.write.format('delta').mode('overwrite').save(gold_table_path)\n",
                    "print(f'[GOLD] Successfully generated Gold table at {gold_table_path}')\n",
                    "display(df_gold.limit(10))\n"
                ]
            }
        ]
    }

    payload_b64 = base64.b64encode(json.dumps(notebook_json).encode("utf-8")).decode("utf-8")
    update_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{item_id}/updateDefinition"
    update_body = {
        "definition": {
            "format": "ipynb",
            "parts": [
                {
                    "path": "notebook-content.ipynb",
                    "payload": payload_b64,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }

    req = urllib.request.Request(update_url, data=json.dumps(update_body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print("Successfully updated Fabric notebook definition! Status:", resp.status)
    except urllib.error.HTTPError as e:
        print("Error updating notebook definition:", e.code, e.read().decode("utf-8"))


if __name__ == "__main__":
    main()
