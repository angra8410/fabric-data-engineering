# 🐾 Velykapet E-Commerce & POS Data Platform
### Enterprise Medallion Architecture on Microsoft Fabric & Delta Lake

[![Microsoft Fabric](https://img.shields.io/badge/Microsoft_Fabric-0078D4?style=for-the-badge&logo=microsoft&logoColor=white)](https://fabric.microsoft.com/)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Delta Lake](https://img.shields.io/badge/Delta_Lake-000000?style=for-the-badge&logo=delta&logoColor=white)](https://delta.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

---

## 📋 Executive Overview

**Velykapet** is a omnichannel pet store retail platform operating both physical POS store branches and digital channels (Web, Rappi, and an automated WhatsApp Sales Bot). 

This project implements an end-to-end **Data Engineering Platform on Microsoft Fabric**, orchestrating a 3-tier **Medallion Architecture (Bronze ➔ Silver ➔ Gold)** over 16 relational & transactional operational tables. 

It features automated **Application Lifecycle Management (ALM)** with a 3-stage Deployment Pipeline (`Development` ➔ `Test` ➔ `Production`) and a live interactive analytics dashboard built with **Streamlit**.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Operational_Source["1. Operational Source (PostgreSQL)"]
        DB[(PostgreSQL Database<br/>16 Core Tables)]
    end

    subgraph Fabric_Ingestion["2. Microsoft Fabric Pipeline Ingestion"]
        DB -->|CopyJob_1 Data Pipeline| Bronze_Lakehouse
    end

    subgraph Medallion_Architecture["3. Microsoft Fabric Medallion Architecture"]
        subgraph Bronze_Layer["Bronze Layer (Raw Lakehouse)"]
            Bronze_Lakehouse[lh_velykapet_bronze_dev<br/>16 Raw Tables<br/>Parquet / Delta]
        end

        subgraph Silver_Layer["Silver Layer (Cleaned & Standardized Lakehouse)"]
            Bronze_Lakehouse -->|04_master_medallion_pipeline.py| Silver_Lakehouse[lh_velykapet_silver_dev<br/>16 Cleaned Tables<br/>0-Baseline for WhatsApp]
        end

        subgraph Gold_Layer["Gold Layer (Data Warehouse & Star Schema)"]
            Silver_Lakehouse -->|Single Spark Session ETL| Gold_Lakehouse[lh_velykapet_gold_dev<br/>FactSales, FactExpenses, FactPurchases<br/>DimProducts, Daily & WA KPIs]
        end
    end

    subgraph Analytics_BI["4. Analytics & Portfolio Presentation"]
        Gold_Lakehouse --> BI[Streamlit Interactive App<br/>http://localhost:8501]
        Gold_Lakehouse --> PBI[Power BI SQL Endpoint]
    end
```

---

## 🚀 Microsoft Fabric ALM & Deployment Pipeline (`pl_deployment_velykapet`)

To strictly adhere to enterprise governance, CI/CD, and Application Lifecycle Management (ALM) best practices, the infrastructure is segregated into **3 isolated Microsoft Fabric workspaces** linked via the **`pl_deployment_velykapet`** deployment pipeline:

```mermaid
graph LR
    DEV["🟢 Development<br/>(ws-velykapet-dev)"] -->|Deploy Stage| TEST["🟡 Test<br/>(ws-velykapet-test)"]
    TEST -->|Deploy Stage| PROD["🔴 Production<br/>(ws-velykapet-prod)"]
```

### Deployment Pipeline Items & Comparison:
- **`CopyJob_1`**: Ingestion Copy Activity synced across DEV ➔ TEST ➔ PROD (`Same as source`).
- **Lakehouses**: `lh_velykapet_bronze_dev`, `lh_velykapet_silver_dev`, and `lh_velykapet_gold_dev` provisioned and verified in target environments.
- **PySpark Master Notebook**: `nb_velykapet_master_medallion` deployed seamlessly across environments.

---

## 📊 Medallion Architecture Details

### 1. 🟤 Bronze Layer (`lh_velykapet_bronze_dev.public.*`)
- Raw, append-only ingestion directly from operational PostgreSQL.
- Maintains 100% schema fidelity with metadata tags (`_ingested_at`, `_batch_id`).
- Total: **16 Ingested Tables**.

### 2. ⚪ Silver Layer (`lh_velykapet_silver_dev.dbo.silver_*`)
- Cleansed, deduplicated, and typed Delta Lake tables.
- **Production-Ready WhatsApp Baseline**: The 7 WhatsApp & backlog tables (`whatsapp_orders`, `whatsapp_order_items`, `processed_whatsapp_messages`, `whatsapp_contacts`, `demand_backlog`, `customer_last_search`, `customer_cart`) are initialized with `.filter("1 = 0")` to purge test figures and create a clean 0-record baseline for live bot go-live.

### 3. 🟡 Gold Layer (`lh_velykapet_gold_dev.dbo.*`)
- Business Data Warehouse modeled as a **Star Schema**:
  - `fact_sales`: Line-item sales facts joined with sales header origin and product dimensions.
  - `fact_expenses`: Categorized operating expenses.
  - `fact_purchases`: Inventory procurement and supplier expenses.
  - `dim_products`: Unified product master, cost prices, retail prices, and live stock balances.
  - `kpi_daily_sales_trend`: Aggregated daily revenue, transaction counts, and gross profit margins.
  - `kpi_inventory_health`: SKU counts, stock units, and inventory cost vs retail valuation.
  - `kpi_whatsapp_conversion`: Conversion rate metrics for live WhatsApp orders.

---

## ⚡ Capacity Optimization: Single Spark Session Master ETL

To overcome Microsoft Fabric trial/F-SKU Spark concurrency compute limits (`HTTP 430: TooManyRequestsForCapacity`), all Medallion steps are unified inside [`04_master_medallion_pipeline.py`](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/velykapet_project/notebooks/04_master_medallion_pipeline.py). 

This executes **Bronze Validation ➔ Silver Cleaning ➔ Gold DW & KPIs in a single, high-speed Spark session**, completing the entire ETL run in under **30 seconds** with zero Livy startup delays.

---

## 💻 Interactive Streamlit Portfolio Dashboard (`portfolio_app/app.py`)

An executive analytics web application built in Streamlit showcasing the business insights derived from the Gold Layer:

- 📈 **Executive KPIs**: Real-time Gross Revenue, Gross Profit, Total Transactions, and Ticket Size.
- 📅 **Dynamic Date Range Filter**: Full historical range selector starting from Velykapet's launch in **September 2025**.
- 📦 **Inventory Health**: Stock valuation and top-selling product performance.
- 📲 **WhatsApp Bot Conversion Monitor**: Live production monitoring for WhatsApp sales.
- 🏛️ **Architecture Viewer**: Interactive Mermaid diagram and Medallion schema table inspector.

---

## 📂 Folder Structure

```text
velykapet_project/
├── config/                        <-- Workspace GUIDs and Azure REST API configurations
│   └── fabric_config.json
├── notebooks/                     <-- PySpark Medallion Notebooks
│   ├── 01_bronze_ingest.py        <-- Bronze Ingestion Audit
│   ├── 02_silver_clean.py         <-- Silver Transformations & 0-Baseline
│   ├── 03_gold_reporting.py       <-- Gold Data Warehouse & Star Schema ETL
│   └── 04_master_medallion_pipeline.py  <-- Unified Single-Session Master Pipeline
├── pipelines/                     <-- Fabric DataPipeline JSON Definitions
│   └── 02_master_medallion_pipeline.json
├── powerbi/                       <-- Microsoft Fabric Direct Lake Semantic Model & Power BI Assets
│   ├── model.bim                  <-- Direct Lake Tabular Semantic Model Definition
│   ├── dax_measures.dax           <-- Production DAX Measures Catalog
│   ├── powerbi_theme.json         <-- Executive Dark Mode Theme Definition
│   └── report_blueprint.md        <-- 5-Page Visual Layout & Report Blueprint
└── README.md                      <-- Technical Documentation Showcase
```

