# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "9f9b4f36-e70e-47a8-853a-e73e6d454649",
# META       "default_lakehouse_name": "lh_bronze_ingestion",
# META       "default_lakehouse_workspace_id": "ace87823-ba3c-4e0d-b5f8-3f051d09dca9",
# META       "known_lakehouses": [
# META         {
# META           "id": "9f9b4f36-e70e-47a8-853a-e73e6d454649"
# META         },
# META         {
# META           "id": "b26c63f3-de56-4c27-b4e1-1df78b2a5567"
# META         },
# META         {
# META           "id": "0b67fb06-f34c-445c-9e2a-fc7f2dac1d64"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Multi-Supplier Price Ingestion & Harmonization Framework
# ### Medallion Architecture: Bronze -> Silver -> Gold (Velykapet)
# This notebook dynamically reads heterogeneous price lists (PDF, Excel, CSV) from Bronze, maps each supplier's unique format into a **unified Canonical Schema** in Silver (`dim_supplier_prices`), and generates Gold pricing tables with calculated retail margins.

# CELL ********************

# 1. Install required dependencies
%pip install pypdf openpyxl


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import os
import re
from datetime import datetime
import pandas as pd
from pypdf import PdfReader
from pyspark.sql import functions as F

print('Loaded dependencies for Multi-Supplier Price Ingestion Framework.')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 2. Extensible Supplier Parser Registry Pattern
# Define custom parsers for each supplier format (PDF, Excel, CSV) without breaking the downstream pipeline.

# CELL ********************

class BaseSupplierParser:
    """Abstract base class for all supplier price list parsers."""
    def __init__(self, supplier_name: str):
        self.supplier_name = supplier_name

    def parse(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError('Subclasses must implement parse()')


class ItalcolPDFParser(BaseSupplierParser):
    """Parser for Italcol PDF price lists with 4 price columns and EAN/Internal code pairs."""
    def __init__(self):
        super().__init__('Italcol')

    def parse(self, file_path: str) -> pd.DataFrame:
        reader = PdfReader(file_path)
        records = []
        current_category = 'GENERAL'
        header_patterns = [
            'LISTA VIGENTE', 'ESTOS PRECIOS', 'PRECIOS SUJETOS', 'PLANTAS',
            'EAN 13', 'COD BARRAS', 'COD INTERNO', 'PRECIO BASE', 'PRECIO antes',
            'precio iva', 'descuento 3%', 'PAGINA'
        ]
        effective_date = '2026-05-01'

        for page_idx, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ''
            for raw_line in raw_text.split('\n'):
                line = raw_line.strip()
                if not line or any(h.lower() in line.lower() for h in header_patterns):
                    continue

                prices = re.findall(r'\$\s*[\d\.\,]+', line)
                if not prices:
                    current_category = line
                    continue

                if len(prices) >= 4:
                    p4_str, p3_str, p2_str, p1_str = prices[-1], prices[-2], prices[-3], prices[-4]
                    idx = line.rfind(prices[-4])
                    prefix = line[:idx].strip()
                    tokens = prefix.split()

                    if len(tokens) >= 2:
                        if re.match(r'^\d{8,}$', tokens[0]) or tokens[0].upper() == 'N/A':
                            barcode = tokens[0]
                            internal_code = tokens[1]
                            desc = ' '.join(tokens[2:])
                        else:
                            barcode = 'N/A'
                            internal_code = tokens[0]
                            desc = ' '.join(tokens[1:])
                    else:
                        barcode, internal_code, desc = 'N/A', 'N/A', prefix

                    p_base = float(p1_str.replace('$', '').replace('.', '').replace(',', '.').strip())
                    p_antes_iva = float(p2_str.replace('$', '').replace('.', '').replace(',', '.').strip())
                    p_con_iva = float(p3_str.replace('$', '').replace('.', '').replace(',', '.').strip())
                    p_final_dto = float(p4_str.replace('$', '').replace('.', '').replace(',', '.').strip())

                    tax_rate = round(((p_con_iva - p_antes_iva) / p_antes_iva * 100), 1) if p_antes_iva > 0 else 0.0
                    dto_pct = round(((p_con_iva - p_final_dto) / p_con_iva * 100), 1) if p_con_iva > 0 else 0.0

                    records.append({
                        'supplier_name': self.supplier_name,
                        'supplier_sku': str(internal_code),
                        'barcode_ean': str(barcode),
                        'product_description': desc,
                        'category': current_category,
                        'base_cost': p_base,
                        'price_before_tax': p_antes_iva,
                        'tax_rate_pct': tax_rate,
                        'price_with_tax': p_con_iva,
                        'discount_pct': dto_pct,
                        'final_net_cost': p_final_dto,
                        'effective_date': effective_date,
                        'source_file': os.path.basename(file_path),
                        'ingestion_timestamp': datetime.now().isoformat()
                    })
        return pd.DataFrame(records)


class GenericExcelSupplierParser(BaseSupplierParser):
    """Parser template for suppliers delivering standard Excel catalogues."""
    def __init__(self, supplier_name: str):
        super().__init__(supplier_name)

    def parse(self, file_path: str) -> pd.DataFrame:
        df_raw = pd.read_excel(file_path)
        records = []
        for _, row in df_raw.iterrows():
            records.append({
                'supplier_name': self.supplier_name,
                'supplier_sku': str(row.get('CODIGO', row.get('SKU', 'N/A'))),
                'barcode_ean': str(row.get('EAN', row.get('BARCODE', 'N/A'))),
                'product_description': str(row.get('DESCRIPCION', row.get('PRODUCTO', ''))),
                'category': str(row.get('CATEGORIA', 'GENERAL')),
                'base_cost': float(row.get('PRECIO_BASE', 0.0)),
                'price_before_tax': float(row.get('PRECIO_NETO', 0.0)),
                'tax_rate_pct': float(row.get('IVA_PCT', 19.0)),
                'price_with_tax': float(row.get('PRECIO_IVA', 0.0)),
                'discount_pct': float(row.get('DESCUENTO_PCT', 0.0)),
                'final_net_cost': float(row.get('PRECIO_FINAL', 0.0)),
                'effective_date': str(row.get('FECHA_VIGENCIA', datetime.now().strftime('%Y-%m-%d'))),
                'source_file': os.path.basename(file_path),
                'ingestion_timestamp': datetime.now().isoformat()
            })
        return pd.DataFrame(records)


class ParserRegistry:
    """Factory registry for dynamic supplier parser discovery."""
    _registry = {
        'italcol': ItalcolPDFParser(),
        'gabrica': GenericExcelSupplierParser('Gabrica'),
        'solla': GenericExcelSupplierParser('Solla'),
    }

    @classmethod
    def get_parser(cls, supplier_key: str):
        return cls._registry.get(supplier_key.lower())


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 3. Bronze -> Silver Pipeline Execution
# Scans `/lakehouse/default/Files/raw/` subdirectories per supplier and transforms all files into the Silver Delta Table (`dim_supplier_prices`).

# CELL ********************

class BaseSupplierParser:
    """Abstract base class for all supplier price list parsers."""
    def __init__(self, supplier_name: str):
        self.supplier_name = supplier_name

    def parse(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement parse()")


class ItalcolPDFParser(BaseSupplierParser):
    """Parser for Italcol PDF price lists with 4 price columns and EAN/Internal code pairs."""
    def __init__(self):
        super().__init__("Italcol")

    def parse(self, file_path: str) -> pd.DataFrame:
        reader = PdfReader(file_path)
        records = []
        current_category = "GENERAL"
        header_patterns = [
            "LISTA VIGENTE", "ESTOS PRECIOS", "PRECIOS SUJETOS", "PLANTAS",
            "EAN 13", "COD BARRAS", "COD INTERNO", "PRECIO BASE", "PRECIO antes",
            "precio iva", "descuento 3%", "PAGINA"
        ]
        effective_date = "2026-05-01"

        for page_idx, page in enumerate(reader.pages):
            raw_text = page.extract_text() or ""
            for raw_line in raw_text.split("\n"):
                line = raw_line.strip()
                if not line or any(h.lower() in line.lower() for h in header_patterns):
                    continue

                prices = re.findall(r"\$\s*[\d\.\,]+", line)
                if not prices:
                    current_category = line
                    continue

                if len(prices) >= 4:
                    p4_str, p3_str, p2_str, p1_str = prices[-1], prices[-2], prices[-3], prices[-4]
                    idx = line.rfind(prices[-4])
                    prefix = line[:idx].strip()
                    tokens = prefix.split()

                    if len(tokens) >= 2:
                        if re.match(r"^\d{8,}$", tokens[0]) or tokens[0].upper() == "N/A":
                            barcode = tokens[0]
                            internal_code = tokens[1]
                            desc = " ".join(tokens[2:])
                        else:
                            barcode = "N/A"
                            internal_code = tokens[0]
                            desc = " ".join(tokens[1:])
                    else:
                        barcode = "N/A"
                        internal_code = "N/A"
                        desc = prefix

                    p_base = float(p1_str.replace("$", "").replace(".", "").replace(",", ".").strip())
                    p_antes_iva = float(p2_str.replace("$", "").replace(".", "").replace(",", ".").strip())
                    p_con_iva = float(p3_str.replace("$", "").replace(".", "").replace(",", ".").strip())
                    p_final_dto = float(p4_str.replace("$", "").replace(".", "").replace(",", ".").strip())

                    tax_rate = round(((p_con_iva - p_antes_iva) / p_antes_iva * 100), 1) if p_antes_iva > 0 else 0.0
                    dto_pct = round(((p_con_iva - p_final_dto) / p_con_iva * 100), 1) if p_con_iva > 0 else 0.0

                    records.append({
                        "supplier_name": self.supplier_name,
                        "supplier_sku": str(internal_code),
                        "barcode_ean": str(barcode),
                        "product_description": desc,
                        "category": current_category,
                        "base_cost": p_base,
                        "price_before_tax": p_antes_iva,
                        "tax_rate_pct": tax_rate,
                        "price_with_tax": p_con_iva,
                        "discount_pct": dto_pct,
                        "final_net_cost": p_final_dto,
                        "effective_date": effective_date,
                        "source_file": os.path.basename(file_path),
                        "ingestion_timestamp": datetime.now().isoformat()
                    })
        return pd.DataFrame(records)


class GenericExcelSupplierParser(BaseSupplierParser):
    """Parser template for suppliers delivering standard Excel catalogues."""
    def __init__(self, supplier_name: str):
        super().__init__(supplier_name)

    def parse(self, file_path: str) -> pd.DataFrame:
        df_raw = pd.read_excel(file_path)
        records = []
        for _, row in df_raw.iterrows():
            records.append({
                "supplier_name": self.supplier_name,
                "supplier_sku": str(row.get("CODIGO", row.get("SKU", "N/A"))),
                "barcode_ean": str(row.get("EAN", row.get("BARCODE", "N/A"))),
                "product_description": str(row.get("DESCRIPCION", row.get("PRODUCTO", ""))),
                "category": str(row.get("CATEGORIA", "GENERAL")),
                "base_cost": float(row.get("PRECIO_BASE", 0.0)),
                "price_before_tax": float(row.get("PRECIO_NETO", 0.0)),
                "tax_rate_pct": float(row.get("IVA_PCT", 19.0)),
                "price_with_tax": float(row.get("PRECIO_IVA", 0.0)),
                "discount_pct": float(row.get("DESCUENTO_PCT", 0.0)),
                "final_net_cost": float(row.get("PRECIO_FINAL", 0.0)),
                "effective_date": str(row.get("FECHA_VIGENCIA", datetime.now().strftime("%Y-%m-%d"))),
                "source_file": os.path.basename(file_path),
                "ingestion_timestamp": datetime.now().isoformat()
            })
        return pd.DataFrame(records)


class ParserRegistry:
    """Factory registry for dynamic supplier parser discovery."""
    _registry = {
        "italcol": ItalcolPDFParser(),
        "gabrica": GenericExcelSupplierParser("Gabrica"),
        "solla": GenericExcelSupplierParser("Solla"),
    }

    @classmethod
    def get_parser(cls, supplier_key: str):
        return cls._registry.get(supplier_key.lower())


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 4. Silver -> Gold Serving Layer
# Generates recommended retail prices (PVP) at 25%, 30%, and 35% margin targets.

# CELL ********************

bronze_base_path = "/lakehouse/default/Files/raw"
all_standardized_dfs = []

if os.path.exists(bronze_base_path):
    for supplier_dir in os.listdir(bronze_base_path):
        supplier_path = os.path.join(bronze_base_path, supplier_dir)
        if os.path.isdir(supplier_path):
            parser = ParserRegistry.get_parser(supplier_dir)
            if not parser:
                print(f"[WARN] No parser registered for supplier folder: {supplier_dir}. Skipping.")
                continue

            for file_name in os.listdir(supplier_path):
                file_path = os.path.join(supplier_path, file_name)
                if file_name.endswith((".pdf", ".xlsx", ".csv")):
                    print(f"[PROCESSING] {supplier_dir} -> {file_name}...")
                    try:
                        df_parsed = parser.parse(file_path)
                        if not df_parsed.empty:
                            all_standardized_dfs.append(df_parsed)
                            print(f"[SUCCESS] Parsed {len(df_parsed)} rows from {file_name}")
                    except Exception as e:
                        print(f"[ERROR] Failed to parse {file_name}: {e}")

if all_standardized_dfs:
    combined_pdf = pd.concat(all_standardized_dfs, ignore_index=True)
    spark_silver_df = spark.createDataFrame(combined_pdf)
    
    # Direct OneLake ABFSS path to Silver Lakehouse Tables
    silver_table_path = "abfss://ws_velykapet_random@onelake.dfs.fabric.microsoft.com/lh_silver_transformation.Lakehouse/Tables/dim_supplier_prices"
    
    spark_silver_df.write.format("delta") \
        .mode("overwrite") \
        .partitionBy("supplier_name") \
        .save(silver_table_path)
        
    print(f"[DELTA] Successfully updated Silver table at {silver_table_path} with {spark_silver_df.count()} total records.")
    display(spark_silver_df.limit(10))
else:
    print("[INFO] No files found to process.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# 1. Read from Silver OneLake Path
silver_table_path = "abfss://ws_velykapet_random@onelake.dfs.fabric.microsoft.com/lh_silver_transformation.Lakehouse/Tables/dim_supplier_prices"
df_silver = spark.read.format("delta").load(silver_table_path)

# 2. Calculate Gold serving metrics (Recommended PVP at 25%, 30%, 35% margins)
df_gold = df_silver.withColumn(
    "pvp_recommended_25_margin", F.round(F.col("final_net_cost") / (1 - 0.25), 0)
).withColumn(
    "pvp_recommended_30_margin", F.round(F.col("final_net_cost") / (1 - 0.30), 0)
).withColumn(
    "pvp_recommended_35_margin", F.round(F.col("final_net_cost") / (1 - 0.35), 0)
).withColumn(
    "calculated_at", F.current_timestamp()
)

# 3. Save to Gold Lakehouse
gold_table_path = "abfss://ws_velykapet_random@onelake.dfs.fabric.microsoft.com/lh_gold_serving.Lakehouse/Tables/fact_product_pricing_master"
df_gold.write.format("delta").mode("overwrite").save(gold_table_path)

print(f"[GOLD] Successfully generated Gold table at {gold_table_path}")
display(df_gold.limit(10))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
