/**
 * Dynamic Multi-Report & Project Metadata Configuration
 * Supports DEV and PROD environment switching and multi-report hosting per project.
 */
const PORTFOLIO_DATA = {
  currentEnv: "prod", // 'prod' | 'dev'

  environments: {
    prod: {
      name: "Production (ws-prod)",
      badgeClass: "badge-prod",
      description: "Recruiter-facing production environment connected to Microsoft Fabric Production Workspace."
    },
    dev: {
      name: "Development (ws-dev)",
      badgeClass: "badge-dev",
      description: "Staging environment for testing new Lakehouse schemas, PySpark transforms, and Power BI embeds."
    }
  },

  projects: [
    {
      id: "velykapet",
      title: "Velykapet Retail & WhatsApp Medallion Platform",
      category: "E-Commerce & POS Data Platform",
      badge: "Microsoft Fabric Medallion",
      icon: "🐾",
      summary: "End-to-end Data Engineering Platform on Microsoft Fabric orchestrating a 3-tier Medallion Architecture (Bronze ➔ Silver ➔ Gold Data Warehouse) across 16 PostgreSQL operational tables, integrated with WhatsApp Bot sales analytics and 3-stage ALM deployment pipeline.",
      tags: ["Microsoft Fabric", "PySpark", "Delta Lake", "DataPipelines", "Power BI", "PostgreSQL", "WhatsApp API"],
      reports: {
        prod: [
          {
            id: "v_sales_pos_prod",
            title: "📊 Velykapet Executive Revenue & Sales POS",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=2712136d-9fc9-4fda-b800-ce21d8ab0c80&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Omnichannel sales analytics, transaction volume, gross profit margins, and top product ranking across physical POS and Web.",
            metrics: [
              { label: "Total Revenue", value: "$23.55M" },
              { label: "Transactions", value: "412" },
              { label: "Net Profit", value: "$3.03M" },
              { label: "Total Purchases", value: "$21.29M" }
            ]
          },
          {
            id: "v_whatsapp_bot_prod",
            title: "💬 WhatsApp Bot Sales & Demand Funnel",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=2712136d-9fc9-4fda-b800-ce21d8ab0c80&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Production WhatsApp sales bot conversion funnel, abandoned cart recovery, and product search demand backlog.",
            metrics: [
              { label: "WhatsApp Orders", value: "0" },
              { label: "Processed Msgs", value: "0" },
              { label: "Funnel State", value: "Live 0-Baseline" },
              { label: "Architecture", value: "Delta Lake Ready" }
            ]
          },
          {
            id: "v_inventory_prod",
            title: "📦 Inventory Health & Procurement Expenses",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=2712136d-9fc9-4fda-b800-ce21d8ab0c80&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Inventory valuation (Cost vs Retail), low-stock alert monitoring, supplier purchases, and operating expense breakdown.",
            metrics: [
              { label: "Active SKUs", value: "275" },
              { label: "Stock-Out Alerts", value: "263 SKUs" },
              { label: "Total Expenses", value: "$1.00M" },
              { label: "Expense Ratio", value: "4.3%" }
            ]
          }
        ],
        dev: [
          {
            id: "v_sales_pos_dev",
            title: "🟡 [DEV] Velykapet POS Staging & Testing",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=2712136d-9fc9-4fda-b800-ce21d8ab0c80&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Staging dashboard connected to 'lh_velykapet_gold_dev' lakehouse for testing new margin KPI aggregations.",
            metrics: [
              { label: "Dev Records", value: "1,846 Units" },
              { label: "Spark Execution", value: "4m 44s" },
              { label: "Direct Lake Mode", value: "Active" }
            ]
          },
          {
            id: "v_whatsapp_bot_dev",
            title: "🟡 [DEV] WhatsApp Message Parsing Lab",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=dev-whatsapp-parsing-placeholder",
            description: "Testing regex message parsers and automated order placement payloads prior to PROD release.",
            metrics: [
              { label: "Parsed JSONs", value: "482" },
              { label: "Error Rate", value: "0.0%" }
            ]
          }
        ]
      },
      medallion: {
        bronze: {
          name: "lh_velykapet_bronze_dev",
          type: "Raw Ingestion (Parquet / Delta)",
          description: "100% operational fidelity raw tables ingested from PostgreSQL using Fabric Copy Activity (`CopyJob_1`). Includes audit metadata tags `_ingested_at` and `_batch_id`.",
          tableCount: 16,
          tables: ["sales", "sale_items", "products", "master_catalog", "purchases", "expenses", "devolutions", "devolution_items", "v_product_stock", "whatsapp_orders", "whatsapp_order_items", "processed_whatsapp_messages", "whatsapp_contacts", "demand_backlog", "customer_last_search", "customer_cart"]
        },
        silver: {
          name: "lh_velykapet_silver_dev",
          type: "Cleaned & Standardized Delta Tables",
          description: "Type casting, timestamp normalization, null imputation, and 0-record baseline initialization for 7 WhatsApp tables (`.filter('1 = 0')`) to prepare clean production state.",
          tableCount: 16,
          tables: ["silver_sales", "silver_sale_items", "silver_products", "silver_master_catalog", "silver_purchases", "silver_expenses", "silver_devolutions", "silver_devolution_items", "silver_stock", "silver_whatsapp_orders", "silver_whatsapp_order_items", "silver_processed_whatsapp_messages", "silver_whatsapp_contacts", "silver_demand_backlog", "silver_customer_last_search", "silver_customer_cart"]
        },
        gold: {
          name: "lh_velykapet_gold_dev",
          type: "Data Warehouse Star Schema",
          description: "Business Data Warehouse built with single PySpark session. Fact tables (`fact_sales`, `fact_expenses`, `fact_purchases`) joined with Dimension (`dim_products`) and pre-computed KPI aggregations.",
          tableCount: 7,
          tables: ["fact_sales", "fact_expenses", "fact_purchases", "dim_products", "kpi_daily_sales_trend", "kpi_inventory_health", "kpi_whatsapp_conversion"]
        }
      },
      alm: {
        pipeline: "pl_deployment_velykapet",
        stages: [
          { name: "🟢 Development", workspace: "ws-velykapet-dev", lakehouses: "lh_velykapet_*_dev" },
          { name: "🟡 Test", workspace: "ws-velykapet-test", lakehouses: "lh_velykapet_*_test" },
          { name: "🔴 Production", workspace: "ws-velykapet-prod", lakehouses: "lh_velykapet_*_prod" }
        ],
        optimization: "Single Spark Session Master ETL (`nb_velykapet_master_medallion`) executes Bronze Validation ➔ Silver Transformation ➔ Gold DW in under 30 seconds, eliminating Fabric F-SKU concurrency limits (HTTP 430)."
      },
      codeSnippets: [
        {
          id: "master_medallion",
          title: "nb_velykapet_master_medallion.Notebook",
          language: "python",
          description: "Single Spark session executor unifying Bronze validation, Silver cleansing, and Gold Star Schema creation.",
          code: `# Fabric Notebook Source: Master Medallion Pipeline (<30s Single Spark Session)
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, count as _count, current_timestamp, to_date, lit

spark = SparkSession.builder \\
    .appName("Velykapet_Master_Medallion_Pipeline") \\
    .getOrCreate()

# 1️⃣ BRONZE AUDIT STAGE
tables = ["sales", "sale_items", "products", "whatsapp_orders", "whatsapp_order_items", "expenses"]
for t in tables:
    cnt = spark.read.table(f"lh_velykapet_bronze_dev.public.{t}").count()
    print(f"  ├── 📋 Bronze Table '{t}': {cnt} records.")

# 2️⃣ SILVER CLEANING & WHATSAPP 0-BASELINE SETUP
df_sales = spark.read.table("lh_velykapet_bronze_dev.public.sales")
df_items = spark.read.table("lh_velykapet_bronze_dev.public.sale_items")

# Purge test figures for production baseline
df_wa_orders = spark.read.table("lh_velykapet_bronze_dev.public.whatsapp_orders").filter("1 = 0")
df_wa_orders.write.format("delta").mode("overwrite").saveAsTable("lh_velykapet_silver_dev.dbo.silver_whatsapp_orders")

# 3️⃣ GOLD DATA WAREHOUSE FACT & DIM GENERATION
df_joined = df_items.alias("i") \\
    .join(df_sales.alias("s"), col("i.sale_id") == col("s.id"), "inner")

df_fact_sales = df_joined.select(
    col("i.id").alias("item_id"),
    col("s.id").alias("sale_id"),
    col("s.origin").alias("sale_origin"),
    to_date(col("s.created_at")).alias("sale_date"),
    col("i.quantity"),
    col("i.total_price").alias("total_item_revenue")
).withColumn("_updated_at", current_timestamp())

df_fact_sales.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \\
    .saveAsTable("lh_velykapet_gold_dev.dbo.fact_sales")
print("✅ Gold 'fact_sales' built successfully!")`
        },
        {
          id: "gold_transformation",
          title: "nb_velykapet_transformation_gold.Notebook",
          language: "python",
          description: "Star Schema fact_sales, fact_expenses, dim_products and WhatsApp KPI transformation script.",
          code: `# Gold Layer Star Schema Construction Script
SILVER_SCHEMA = "lh_velykapet_silver_dev.dbo"
GOLD_SCHEMA = "lh_velykapet_gold_dev.dbo"

def build_fact_expenses():
    df_exp = spark.read.table(f"{SILVER_SCHEMA}.silver_expenses")
    df_fact = df_exp.select(
        col("id").alias("expense_id"),
        col("expense_date"),
        col("category"),
        col("amount"),
        col("description")
    ).withColumn("_updated_at", current_timestamp())
    
    df_fact.write.format("delta").mode("overwrite").saveAsTable(f"{GOLD_SCHEMA}.fact_expenses")

def build_kpi_whatsapp_conversion():
    df_orders = spark.read.table(f"{SILVER_SCHEMA}.silver_whatsapp_orders")
    df_msgs = spark.read.table(f"{SILVER_SCHEMA}.silver_processed_whatsapp_messages")
    
    # Conversion rate aggregation
    total_msgs = df_msgs.count()
    completed_orders = df_orders.filter(col("status") == "COMPLETED").count()
    conv_rate = (completed_orders / total_msgs * 100.0) if total_msgs > 0 else 0.0
    print(f"📊 WhatsApp Bot Conversion Rate: {conv_rate:.2f}%")`
        }
      ],
      dashboardData: {
        filterOptions: {
          slicer1: { label: "Year:", id: "filter-year", options: [
            { value: "ALL", label: "All Years" },
            { value: "2026", label: "2026" },
            { value: "2025", label: "2025" }
          ]},
          slicer2: { label: "Origin:", id: "filter-channel", options: [
            { value: "ALL", label: "All Channels" },
            { value: "Tienda", label: "Tienda POS" },
            { value: "Whatsapp", label: "WhatsApp Bot" },
            { value: "Rappi", label: "Rappi" }
          ]}
        },
        monthly: [
          { month: "2025-09", year: "2025", rev: 0.09, profit: 0.02, margin: 25.0, tx: 3 },
          { month: "2025-10", year: "2025", rev: 0.50, profit: 0.07, margin: 13.7, tx: 12 },
          { month: "2025-11", year: "2025", rev: 0.73, profit: 0.15, margin: 20.1, tx: 18 },
          { month: "2025-12", year: "2025", rev: 1.49, profit: 0.44, margin: 29.3, tx: 32 },
          { month: "2026-01", year: "2026", rev: 1.44, profit: 0.18, margin: 12.8, tx: 28 },
          { month: "2026-02", year: "2026", rev: 2.16, profit: 0.29, margin: 13.5, tx: 41 },
          { month: "2026-03", year: "2026", rev: 1.38, profit: 0.19, margin: 13.7, tx: 25 },
          { month: "2026-04", year: "2026", rev: 2.42, profit: 0.43, margin: 17.7, tx: 46 },
          { month: "2026-05", year: "2026", rev: 3.03, profit: 0.55, margin: 18.0, tx: 58 },
          { month: "2026-06", year: "2026", rev: 3.69, profit: 0.63, margin: 17.2, tx: 69 },
          { month: "2026-07", year: "2026", rev: 4.53, profit: 0.78, margin: 17.2, tx: 84 },
          { month: "2026-08", year: "2026", rev: 2.45, profit: 0.44, margin: 17.8, tx: 47 }
        ],
        channels: [
          { name: "Tienda POS", rev: 21.64, pct: 91.63, color: "#0d9488" },
          { name: "WhatsApp Bot", rev: 1.91, pct: 8.07, color: "#38bdf8" },
          { name: "Rappi Delivery", rev: 0.07, pct: 0.29, color: "#f43f5e" }
        ],
        topProducts: [
          { name: "ARENA MAIZ CAT 10 KG", rev: 1.74 },
          { name: "PRO PLAN VETE DIETS", rev: 1.60 },
          { name: "AGILITY ADULTO GATO 3KG", rev: 1.23 },
          { name: "AGILITY GOLD GATITOS 1.5KG", rev: 1.11 },
          { name: "C MAX PERRO JARABE", rev: 0.54 },
          { name: "FORTIFLORA PERRO SOBRE", rev: 0.45 },
          { name: "NEXGARD SPECTRA 15-30KG", rev: 0.43 },
          { name: "PRO PLAN EXIGENT", rev: 0.41 },
          { name: "NUSKÉ CABALLO", rev: 0.40 },
          { name: "INABA GATO CHURU", rev: 0.39 }
        ],
        stockouts: [
          { name: "ROYAL CANIN GASTROINTESTINAL FIBRE", supplier: "PharmaVet Logistics", stock: 0, price: "$253,750" },
          { name: "ROYAL CANIN KITTEN STERILISED 400 GR", supplier: "PharmaVet Logistics", stock: 0, price: "$44,950" },
          { name: "ROYAL CANIN KITTEN STERILISED 2 KG", supplier: "NutriPet Wholesale", stock: 0, price: "$200,100" },
          { name: "ROYAL CANIN PUPPY MINI INDOOR 1.5KG", supplier: "NutriPet Wholesale", stock: 0, price: "$128,150" },
          { name: "PRO PLAN VETE DIETS EN PERRO 379GR", supplier: "NutriPet Wholesale", stock: 0, price: "$36,250" },
          { name: "DR CLAUDERS GATO BANDEJA CAMARONES", supplier: "Global Pet Logistics", stock: 0, price: "$15,370" },
          { name: "NEXGARD COMBO GATO 2.5 - 7.5 KG", supplier: "NutriPet Wholesale", stock: 0, price: "$82,650" },
          { name: "CALMING COLLAR FOR DOGS", supplier: "E-Commerce Partner", stock: 0, price: "$29,055" },
          { name: "HILLS SD SMALL MINI ADULTO 1.5KG", supplier: "OmniPet Direct", stock: 0, price: "$138,050" }
        ],
        profitability: [
          { name: "BAÑO SECO IKIPETS PERROS 200 ML", supplier: "Retail Vendor Network", rev: "$17,400", margin: "-33.3%", status: "loss" },
          { name: "ARENA ULTRA CAT TOFU CAFÉ X2.5KG", supplier: "Regional Pet Partner", rev: "$68,700", margin: "-13.7%", status: "loss" },
          { name: "ALIMENTO HÚMEDO GATITOS ATÚN WHISKAS", supplier: "AgroPet Supply Co.", rev: "$4,205", margin: "0.0%", status: "warn" },
          { name: "ALIMENTO HÚMEDO GATOS POUCH ATÚN", supplier: "Regional Pet Partner", rev: "$3,680", margin: "0.0%", status: "warn" },
          { name: "ARENA PARA GATO CALABAZA ROSA X4.5KG", supplier: "Pet Essentials Hub", rev: "$15,857", margin: "0.0%", status: "warn" },
          { name: "ARNES D2 MORADO", supplier: "Prime Pet Wholesaler", rev: "$23,345", margin: "0.0%", status: "warn" },
          { name: "ARNES NYLON D1", supplier: "Prime Pet Wholesaler", rev: "$36,260", margin: "0.0%", status: "warn" },
          { name: "BEEFS DRY BATH 200 ML", supplier: "NutriPet Wholesale", rev: "$39,875", margin: "0.0%", status: "warn" },
          { name: "CHUNKY ADULTO CORDERO ARROZ X 1.5KG", supplier: "NutriPet Wholesale", rev: "$34,220", margin: "16.0%", status: "healthy" }
        ],
        opex: [
          { category: "Transporte & Logística", amount: 340740, pct: 34.1, color: "#0d9488" },
          { category: "Documentación Legal & Notarial", amount: 178210, pct: 17.8, color: "#334155" },
          { category: "Trade & Marketing POS", amount: 165450, pct: 16.5, color: "#f43f5e" },
          { category: "Eventos & Ferias Pet", amount: 101500, pct: 10.2, color: "#eab308" },
          { category: "Operativo & Mantenimiento", amount: 67640, pct: 6.8, color: "#64748b" },
          { category: "Donaciones & Rescate Animal", amount: 58000, pct: 5.8, color: "#38bdf8" },
          { category: "Equipos & Tecnología", amount: 48720, pct: 4.9, color: "#f97316" },
          { category: "Papelería & Suministros", amount: 36760, pct: 3.7, color: "#a855f7" }
        ],
        procurement: [
          { supplier: "NutriPet Wholesale", spend: "$7,315,135.97", orders: 187, share: "33.2%" },
          { supplier: "Global Pet Logistics", spend: "$4,642,058.22", orders: 230, share: "21.0%" },
          { supplier: "Regional Pet Partner", spend: "$3,025,439.81", orders: 119, share: "13.7%" },
          { supplier: "AgroVets Distribution", spend: "$1,954,165.00", orders: 27, share: "8.9%" },
          { supplier: "AgroPet Supply Co.", spend: "$1,564,695.00", orders: 29, share: "7.1%" },
          { supplier: "OmniPet Direct", spend: "$833,683.30", orders: 17, share: "3.8%" },
          { supplier: "Kanine Care Supply", spend: "$771,650.00", orders: 16, share: "3.5%" },
          { supplier: "Prime Pet Wholesaler", spend: "$649,745.00", orders: 67, share: "2.9%" },
          { supplier: "Pet Essentials Hub", spend: "$523,328.94", orders: 12, share: "2.4%" },
          { supplier: "PharmaVet Logistics", spend: "$332,630.00", orders: 3, share: "1.5%" },
          { supplier: "BioPet Nutrition", spend: "$265,654.50", orders: 7, share: "1.2%" },
          { supplier: "E-Commerce Partner", spend: "$120,832.85", orders: 2, share: "0.5%" },
          { supplier: "Retail Vendor Network", spend: "$62,219.50", orders: 8, share: "0.3%" }
        ]
      }
    },
    {
      id: "colombian_labor",
      title: "Colombia Labor Market & Macroeconomics (2004-2026)",
      category: "Macroeconomic Big Data Platform",
      badge: "DANE GEIH Big Data & Direct Lake",
      icon: "🇨🇴",
      summary: "Comprehensive Macroeconomic Labor Intelligence Platform on Microsoft Fabric processing 22+ years (2004–2026) of DANE GEIH national surveys (8.8M+ microdata records) across 6 presidential administrations and 33 departments with sub-second Direct Lake Power BI cross-filtering.",
      tags: ["Microsoft Fabric", "DANE GEIH", "PySpark", "Delta Lake", "Direct Lake", "Star Schema", "Power BI Desktop"],
      reports: {
        prod: [
          {
            id: "labor_market_prod",
            title: "🇨🇴 Colombian Labor Market Figures (2004–2026)",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=194e03e4-600b-47b9-8291-e7ef04133e25&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Direct Lake Power BI Executive Report featuring monthly labor trends, 12M moving average, presidential term comparisons, and departmental unemployment rankings.",
            metrics: [
              { label: "Historical Span", value: "2004–2026 (22 Yrs)" },
              { label: "Average Unemployment", value: "10.88%" },
              { label: "Monthly Labor Force", value: "~24M" },
              { label: "Microdata Records", value: "8.8M+" }
            ]
          }
        ],
        dev: [
          {
            id: "labor_market_dev",
            title: "🟡 [DEV] Colombian Labor Market Direct Lake",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=c32cf431-7788-468e-9080-33767cb29fa8&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Staging direct lake model connected to ws-data-eng-dev for testing time intelligence DAX and presidential cross-filter cascading.",
            metrics: [
              { label: "Dev Records", value: "8.8M Rows" },
              { label: "Direct Lake Mode", value: "Active" },
              { label: "Query Latency", value: "< 250ms" }
            ]
          }
        ]
      },
      medallion: {
        bronze: {
          name: "dane_bronze_lh",
          type: "Raw Ingestion (OneLake Shortcuts)",
          description: "OneLake ADLS Gen2 shortcut storage containing raw monthly DANE GEIH survey microdata files partitioned by year (2004–2026) in CSV/TXT formats (Tab, Comma, Semicolon delimited).",
          tableCount: 1,
          tables: ["Files/raw/dane (1,318 survey files)"]
        },
        silver: {
          name: "dane_silver_lh",
          type: "Harmonized Survey Microdata",
          description: "Vectorized PySpark pipeline unifying 22+ years of changing DANE survey schemas, auto-detecting delimiters (\\t, ;, ,), standardizing expansion factor weights (FEX_C, FEX_C_2011, FEX_C18), department codes, and open unemployment (DSI=1).",
          tableCount: 1,
          tables: ["silver_dane_labor_market (8,828,567 rows)"]
        },
        gold: {
          name: "dane_gold_lh",
          type: "Direct Lake Star Schema & Dimensions",
          description: "Production Data Warehouse Star Schema optimized for Direct Lake querying: `dim_date` (with presidential bridge `id_periodo`), `dim_presidentes` (6 administrations), `dim_departamentos` (33 regions), `fact_monthly_labor`, and `gold_dane_labor_indicators`.",
          tableCount: 6,
          tables: ["dim_date", "dim_presidentes", "dim_departamentos", "fact_monthly_labor", "fact_labor_by_president", "gold_dane_labor_indicators"]
        }
      },
      alm: {
        pipeline: "Deployment Pipeline (ws-data-eng)",
        stages: [
          { name: "🟢 Development", workspace: "ws-data-eng-dev", lakehouses: "dane_*_lh (Dev)" },
          { name: "🟡 Test", workspace: "ws-data-eng-test", lakehouses: "dane_*_lh (Test)" },
          { name: "🔴 Production", workspace: "ws-data-eng-prod", lakehouses: "dane_*_lh (Prod)" }
        ],
        optimization: "Cascading Star Schema (dim_presidentes ➔ dim_date ➔ fact_monthly_labor / gold_dane_labor_indicators) enables sub-second Direct Lake Power BI cross-filtering across 22 years of data without circular deadlocks."
      },
      codeSnippets: [
        {
          id: "silver_transformation",
          title: "nb_silver_transform_labor.Notebook",
          language: "python",
          description: "Vectorized PySpark batch ingestion parsing 1,300+ DANE GEIH files across changing survey delimiters and expansion factor schemas.",
          code: `# Vectorized PySpark Silver Pipeline (2004 - 2026 DANE GEIH)
import notebookutils
from pyspark.sql import functions as F

bronze_root = "abfss://ws-data-eng@onelake.dfs.fabric.microsoft.com/dane_bronze_lh/Files/raw/dane"
all_files = get_files_recursive(bronze_root)

dfs_by_year = []
for yr in range(2004, 2027):
    yr_paths = [p for p in valid_paths if f"year={yr}" in p]
    delims = ["\\t", ";", ","] if yr <= 2015 else ([",", ";"] if yr == 2021 else [";", ","])
    
    for delim in delims:
        df_raw = spark.read.format("csv").option("header", "true").option("delimiter", delim).load(yr_paths)
        # Dynamic FEX, DPTO, and DSI extraction...
        df_clean = df_raw.select(
            F.lit(yr).alias("year"),
            F.regexp_extract("SOURCE_FILE", r"month=(\\d+)", 1).alias("month"),
            F.lpad("DPTO", 2, "0").alias("codigo_departamento"),
            F.when(col("FN_LOW").rlike("(?i)desocu|no_ocu"), "desocupado").otherwise("ocupado").alias("status"),
            F.col("FEX").cast("double").alias("total_weight")
        )
        dfs_by_year.append(df_clean)

df_silver = dfs_by_year[0]
for d in dfs_by_year[1:]: df_silver = df_silver.unionByName(d)
df_silver.write.format("delta").mode("overwrite").saveAsTable("silver_dane_labor_market")`
        },
        {
          id: "gold_dw_builder",
          title: "nb_gold_build_labor.Notebook",
          language: "python",
          description: "Gold Data Warehouse Star Schema builder creating dim_date bridge, dim_presidentes, fact_monthly_labor, and departmental indicators.",
          code: `# Gold Lakehouse DW Star Schema Builder
from pyspark.sql import functions as F

# 1. DIM_DATE with Presidential Term Bridge (id_periodo)
df_dim_date = spark.sql("SELECT explode(sequence(to_date('2004-01-01'), to_date('2026-12-31'), interval 1 day)) as date") \\
    .withColumn("id_periodo",
        F.when(F.col("date") < "2006-08-07", 1)
         .when((F.col("date") >= "2006-08-07") & (F.col("date") < "2010-08-07"), 2)
         .when((F.col("date") >= "2010-08-07") & (F.col("date") < "2014-08-07"), 3)
         .when((F.col("date") >= "2014-08-07") & (F.col("date") < "2018-08-07"), 4)
         .when((F.col("date") >= "2018-08-07") & (F.col("date") < "2022-08-07"), 5)
         .otherwise(6)
    )
df_dim_date.write.format("delta").mode("overwrite").saveAsTable("dim_date")

# 2. FACT_MONTHLY_LABOR
df_monthly = df_silver.groupBy("year", "month").agg(
    F.sum(F.when(F.col("status") == "ocupado", F.col("total_weight"))).alias("ocupados"),
    F.sum(F.when(F.col("status") == "desocupado", F.col("total_weight"))).alias("desocupados")
).withColumn("fuerza_laboral", F.col("ocupados") + F.col("desocupados")) \\
 .withColumn("tasa_desempleo_pct", (F.col("desocupados") / F.col("fuerza_laboral")) * 100)

df_monthly.write.format("delta").mode("overwrite").saveAsTable("fact_monthly_labor")`
        }
      ],
      dashboardData: {
        filterOptions: {
          slicer1: { label: "President:", id: "filter-president", options: [
            { value: "ALL", label: "All Presidential Terms" },
            { value: "1", label: "2002-2006 (Álvaro Uribe Vélez)" },
            { value: "2", label: "2006-2010 (Álvaro Uribe Vélez)" },
            { value: "3", label: "2010-2014 (Juan Manuel Santos)" },
            { value: "4", label: "2014-2018 (Juan Manuel Santos)" },
            { value: "5", label: "2018-2022 (Iván Duque Márquez)" },
            { value: "6", label: "2022-2026 (Gustavo Petro Urrego)" }
          ]},
          slicer2: { label: "Year Filter:", id: "filter-labor-year", options: [
            { value: "ALL", label: "All Years (2004–2026)" },
            { value: "2026", label: "2026 (En Curso)" },
            { value: "2025", label: "2025" },
            { value: "2024", label: "2024" },
            { value: "2023", label: "2023" },
            { value: "2022", label: "2022" },
            { value: "2021", label: "2021" },
            { value: "2020", label: "2020 (Pandemia)" },
            { value: "2019", label: "2019" },
            { value: "2018", label: "2018" },
            { value: "2016", label: "2016" },
            { value: "2015", label: "2015" },
            { value: "2014", label: "2014" },
            { value: "2013", label: "2013" },
            { value: "2012", label: "2012" },
            { value: "2011", label: "2011" },
            { value: "2010", label: "2010" },
            { value: "2009", label: "2009" },
            { value: "2008", label: "2008" },
            { value: "2007", label: "2007" },
            { value: "2006", label: "2006" },
            { value: "2005", label: "2005" },
            { value: "2004", label: "2004" }
          ]}
        },
        kpiTotals: {
          unemployment: "10.88%",
          ocupados: "22.9M",
          fuerzaLaboral: "25.7M",
          desocupados: "2.8M",
          records: "8.8M Microdatos"
        },
        presidents: [
          { id: 1, name: "Álvaro Uribe Vélez (2002-2006)", period: "2002 - 2006", rate: 12.88, color: "#38bdf8", avgOcup: "18.2M", avgDesoc: "2.7M", status: "Primer Mandato" },
          { id: 2, name: "Álvaro Uribe Vélez (2006-2010)", period: "2006 - 2010", rate: 11.75, color: "#0284c7", avgOcup: "19.5M", avgDesoc: "2.6M", status: "Segundo Mandato" },
          { id: 3, name: "Juan Manuel Santos (2010-2014)", period: "2010 - 2014", rate: 10.41, color: "#0d9488", avgOcup: "21.1M", avgDesoc: "2.4M", status: "Primer Mandato" },
          { id: 4, name: "Juan Manuel Santos (2014-2018)", period: "2014 - 2018", rate: 8.51, color: "#14b8a6", avgOcup: "22.4M", avgDesoc: "2.1M", status: "Segundo Mandato" },
          { id: 5, name: "Iván Duque Márquez (2018-2022)", period: "2018 - 2022", rate: 14.61, color: "#ec4899", avgOcup: "21.8M", avgDesoc: "3.7M", status: "Único Mandato (COVID)" },
          { id: 6, name: "Gustavo Petro Urrego (2022-2026)", period: "2022 - 2026", rate: 9.52, color: "#eab308", avgOcup: "23.4M", avgDesoc: "2.4M", status: "Mandato en Curso" }
        ],
        annualSeries: [
          { year: "2004", rate: 13.79, ocupados: "201.8M", desocupados: "32.3M", presId: 1 },
          { year: "2005", rate: 12.20, ocupados: "206.6M", desocupados: "28.7M", presId: 1 },
          { year: "2006", rate: 12.43, ocupados: "105.5M", desocupados: "15.0M", presId: 1 },
          { year: "2007", rate: 11.48, ocupados: "162.8M", desocupados: "21.1M", presId: 2 },
          { year: "2008", rate: 11.38, ocupados: "223.4M", desocupados: "28.7M", presId: 2 },
          { year: "2009", rate: 11.94, ocupados: "229.4M", desocupados: "31.1M", presId: 2 },
          { year: "2010", rate: 11.61, ocupados: "237.6M", desocupados: "31.2M", presId: 2 },
          { year: "2011", rate: 10.92, ocupados: "244.8M", desocupados: "30.0M", presId: 3 },
          { year: "2012", rate: 10.22, ocupados: "252.3M", desocupados: "28.7M", presId: 3 },
          { year: "2013", rate: 9.71, ocupados: "255.9M", desocupados: "27.5M", presId: 3 },
          { year: "2014", rate: 9.10, ocupados: "257.9M", desocupados: "25.8M", presId: 3 },
          { year: "2015", rate: 8.92, ocupados: "264.2M", desocupados: "25.9M", presId: 4 },
          { year: "2016", rate: 9.21, ocupados: "178.0M", desocupados: "18.1M", presId: 4 },
          { year: "2018", rate: 9.83, ocupados: "366.8M", desocupados: "40.0M", presId: 5 },
          { year: "2019", rate: 10.73, ocupados: "396.9M", desocupados: "47.7M", presId: 5 },
          { year: "2020", rate: 20.58, ocupados: "229.2M", desocupados: "59.4M", presId: 5 },
          { year: "2021", rate: 13.70, ocupados: "252.5M", desocupados: "40.0M", presId: 5 },
          { year: "2022", rate: 10.90, ocupados: "243.7M", desocupados: "29.8M", presId: 6 },
          { year: "2023", rate: 10.16, ocupados: "273.5M", desocupados: "30.9M", presId: 6 },
          { year: "2024", rate: 9.31, ocupados: "276.4M", desocupados: "28.4M", presId: 6 },
          { year: "2025", rate: 8.89, ocupados: "285.9M", desocupados: "27.9M", presId: 6 },
          { year: "2026", rate: 9.62, ocupados: "71.7M", desocupados: "7.6M", presId: 6 }
        ],
        departments: [
          { name: "Quindío", rate: "15.76%", unempCount: "42,800", region: "Andina" },
          { name: "Norte de Santander", rate: "15.12%", unempCount: "108,500", region: "Andina" },
          { name: "Caldas", rate: "14.23%", unempCount: "68,200", region: "Andina" },
          { name: "Tolima", rate: "13.45%", unempCount: "94,100", region: "Andina" },
          { name: "Risaralda", rate: "12.89%", unempCount: "64,300", region: "Andina" },
          { name: "Antioquia", rate: "11.55%", unempCount: "382,400", region: "Andina" },
          { name: "Valle del Cauca", rate: "11.48%", unempCount: "258,900", region: "Pacífica" },
          { name: "Bogotá, D.C.", rate: "10.84%", unempCount: "472,100", region: "Andina" },
          { name: "Meta", rate: "10.49%", unempCount: "52,600", region: "Orinoquía" },
          { name: "Santander", rate: "10.39%", unempCount: "115,200", region: "Andina" },
          { name: "Boyacá", rate: "9.84%", unempCount: "61,200", region: "Andina" },
          { name: "Cundinamarca", rate: "9.52%", unempCount: "134,800", region: "Andina" },
          { name: "Atlántico", rate: "8.89%", unempCount: "112,400", region: "Caribe" },
          { name: "Bolívar", rate: "8.29%", unempCount: "86,300", region: "Caribe" },
          { name: "Nariño", rate: "8.28%", unempCount: "71,500", region: "Pacífica" },
          { name: "Huila", rate: "7.82%", unempCount: "44,700", region: "Andina" }
        ]
      }
    },
    {
      id: "secop_colombia",
      title: "Observatorio Nacional de Contratación Pública (SECOP II)",
      category: "Public Sector Big Data & Direct Lake",
      badge: "Fabric Direct Lake & Medallion",
      icon: "🏛️",
      summary: "Plataforma integral de analítica e ingeniería de datos en Microsoft Fabric procesando más de 6 millones de contratos públicos de Colombia (SECOP II / Portal de Datos Abiertos) mediante arquitectura Medallion Delta Lake, Star Schema dimensional con Surrogate Keys xxhash64, 4 Data Marts de alta velocidad y modelo semántico Direct Lake con mapa coroplético TopoJSON departamental y conformed dimensions.",
      tags: ["Microsoft Fabric", "SECOP II", "PySpark", "Delta Lake", "Direct Lake", "Star Schema", "Power BI Desktop", "TopoJSON"],
      reports: {
        prod: [
          {
            id: "secop_observatorio_prod",
            title: "🏛️ Observatorio de Contratación Estatal SECOP II (Direct Lake)",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=c43734a7-897c-4860-84c1-42e01dfdbbbf&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Direct Lake Power BI Executive Report con análisis de $90.84 Billones en inversión pública saneada, distribución territorial por 5 regiones naturales y 32 departamentos, índice de contratación directa y concentración de contratistas.",
            metrics: [
              { label: "Contratos Procesados", value: "6.01M" },
              { label: "Inversión Saneada", value: "$90.84B COP" },
              { label: "Departamentos Cobertura", value: "32 + D.C." },
              { label: "Direct Lake Latency", value: "< 350ms" }
            ]
          }
        ],
        dev: [
          {
            id: "secop_observatorio_dev",
            title: "🟡 [DEV] SECOP II Gold Data Marts Staging",
            embedUrl: "https://app.fabric.microsoft.com/reportEmbed?reportId=c43734a7-897c-4860-84c1-42e01dfdbbbf&autoAuth=true&ctid=9da4a1e2-db93-42a7-a588-957fd6292e87",
            description: "Ambiente de desarrollo y pruebas Direct Lake conectado al Lakehouse 'datos_abiertos_gold_lh_dev' para validación de medidas DAX saneadas y cross-filtering territorial.",
            metrics: [
              { label: "Filas Fact Silver", value: "6,013,832" },
              { label: "Data Marts", value: "4 Tablas" },
              { label: "V-Order Parquet", value: "Optimizado" }
            ]
          }
        ]
      },
      medallion: {
        bronze: {
          name: "datos_abiertos_lh_dev",
          type: "Raw Ingestion (SODA API / REST Extractor)",
          description: "Ingesta masiva particionada por chunks de 50,000 registros desde el API SODA de Datos Abiertos Colombia (Portal SECOP II) con token de autenticación, control de reintentos con backoff exponencial y aterrizaje en formato Delta Lake crudo.",
          tableCount: 1,
          tables: ["bronze_secop_contratos (6,013,832 registros)"]
        },
        silver: {
          name: "datos_abiertos_silver_lh_dev",
          type: "Star Schema Dimensional Delta Tables",
          description: "Modelo estrella con 64-bit BigInt Surrogate Keys computadas vía xxhash64 (sk_entidad, sk_proveedor, sk_geografia), normalización de fechas (fecha_firma_date), saneamiento de texto con trim/upper y optimización columnar V-Order.",
          tableCount: 4,
          tables: ["fact_contratos (6,013,832 filas)", "dim_entidades (6,505 entidades)", "dim_proveedores (1,226,613 proveedores)", "dim_geografia (1,013 municipios)"]
        },
        gold: {
          name: "datos_abiertos_gold_lh_dev",
          type: "Domain Data Marts & Direct Lake Aggregations",
          description: "4 Data Marts de alta performance con enriquecimiento de las 5 Regiones Naturales de Colombia (Andina, Caribe, Pacífica, Orinoquía, Amazonía) y pre-cálculos de transparencia, concentración y gasto territorial.",
          tableCount: 4,
          tables: ["mart_gasto_territorial (37,913 filas)", "mart_transparencia_modalidades (73,021 filas)", "mart_concentracion_proveedores (3,765,363 filas)", "mart_ejecucion_financiera (3,854 filas)"]
        }
      },
      alm: {
        pipeline: "pl_deployment_secop_observatorio",
        stages: [
          { name: "🟢 Development", workspace: "ws-datos-abiertos-colombia", lakehouses: "datos_abiertos_*_lh_dev" },
          { name: "🟡 Test / Staging", workspace: "ws-datos-abiertos-test", lakehouses: "datos_abiertos_*_lh_test" },
          { name: "🔴 Production", workspace: "ws-datos-abiertos-prod", lakehouses: "datos_abiertos_*_lh_prod" }
        ],
        optimization: "Modelo de Constelación con dimensiones conformadas (Dim_Anno, Dim_Region) y Direct Lake nativo sobre Delta Lake Parquet con V-Order, evitando consumo de memoria de importación y garantizando consultas de 6M filas en sub-segundos."
      },
      codeSnippets: [
        {
          id: "silver_star_schema",
          title: "nb_silver_transform_secop.Notebook",
          language: "python",
          description: "Transformación dimensional PySpark con Surrogate Keys xxhash64 (BigInt) y preservación de 6,013,832 contratos crudos.",
          code: `# PySpark Silver Star Schema Transformation (SECOP II)
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

# 1. Limpieza base y casteo seguro de fechas y montos
df_base = df_raw.select(
    F.upper(F.trim(F.coalesce(F.col("id_contrato"), F.lit("NO DEFINIDO")))).alias("id_contrato"),
    F.to_date(F.col("fecha_de_firma")).alias("fecha_firma"),
    F.coalesce(F.regexp_replace(F.col("valor_del_contrato"), "[^0-9.]", "").cast(DoubleType()), F.lit(0.0)).alias("valor_contrato"),
    F.upper(F.trim(F.col("departamento"))).alias("departamento"),
    F.upper(F.trim(F.col("ciudad"))).alias("ciudad"),
    F.upper(F.trim(F.col("nit_entidad"))).alias("nit_entidad"),
    F.upper(F.trim(F.col("documento_proveedor"))).alias("nit_cc_proveedor")
)

# 2. Generación de Surrogate Keys BigInt con xxhash64
df_entidades = df_base.select("nit_entidad", "nombre_entidad").dropDuplicates() \\
    .withColumn("id_entidad_sk", F.xxhash64("nit_entidad", "nombre_entidad"))
df_entidades.write.format("delta").mode("overwrite").saveAsTable("dim_entidades")

df_proveedores = df_base.select("nit_cc_proveedor", "nombre_proveedor").dropDuplicates() \\
    .withColumn("id_proveedor_sk", F.xxhash64("nit_cc_proveedor"))
df_proveedores.write.format("delta").mode("overwrite").saveAsTable("dim_proveedores")

df_geografia = df_base.select("departamento", "ciudad").dropDuplicates() \\
    .withColumn("id_geografia_sk", F.xxhash64("departamento", "ciudad"))
df_geografia.write.format("delta").mode("overwrite").saveAsTable("dim_geografia")

# 3. Fact Table con SKs vinculadas
df_fact = df_base \\
    .withColumn("id_entidad_sk", F.xxhash64("nit_entidad", "nombre_entidad")) \\
    .withColumn("id_proveedor_sk", F.xxhash64("nit_cc_proveedor")) \\
    .withColumn("id_geografia_sk", F.xxhash64("departamento", "ciudad"))
df_fact.write.format("delta").mode("overwrite").saveAsTable("fact_contratos")`
        },
        {
          id: "gold_data_marts",
          title: "nb_gold_build_marts.Notebook",
          language: "python",
          description: "Generación de 4 Data Marts de alta performance con mapeo oficial de las 5 Regiones Naturales de Colombia.",
          code: `# PySpark Gold Data Marts Builder (4 Specialized Marts)
from pyspark.sql import functions as F

def get_region(dpto):
    return (
        F.when(dpto.isin('ATLANTICO', 'BOLIVAR', 'CESAR', 'CORDOBA', 'LA GUAJIRA', 'MAGDALENA', 'SUCRE'), F.lit('Región Caribe'))
        .when(dpto.isin('ANTIOQUIA', 'BOYACA', 'CALDAS', 'CUNDINAMARCA', 'DISTRITO CAPITAL DE BOGOTA', 'HUILA', 'NORTE DE SANTANDER', 'QUINDIO', 'RISARALDA', 'SANTANDER', 'TOLIMA'), F.lit('Región Andina'))
        .when(dpto.isin('CAUCA', 'CHOCO', 'NARINO', 'VALLE DEL CAUCA'), F.lit('Región Pacífica'))
        .when(dpto.isin('ARAUCA', 'CASANARE', 'META', 'VICHADA'), F.lit('Región Orinoquía'))
        .when(dpto.isin('AMAZONAS', 'CAQUETA', 'GUAINIA', 'GUAVIARE', 'PUTUMAYO', 'VAUPES'), F.lit('Región Amazonía'))
        .otherwise(F.lit('Otra / No Definida'))
    )

# 1. Mart Gasto Territorial
mart_territorial = df_fact.filter(F.col("anno_firma") >= 2015) \\
    .join(df_geografia, on="id_geografia_sk") \\
    .withColumn("region_natural", get_region(F.col("departamento"))) \\
    .groupBy("region_natural", "departamento", "ciudad", "anno_firma", "mes_firma") \\
    .agg(
        F.count("*").alias("total_contratos"),
        F.round(F.sum("valor_contrato"), 2).alias("inversion_total_cop"),
        F.round(F.avg("valor_contrato"), 2).alias("gasto_promedio_contrato")
    )
mart_territorial.write.format("delta").mode("overwrite").saveAsTable("mart_gasto_territorial")`
        },
        {
          id: "dax_sane_measures",
          title: "Direct Lake DAX Business Logic",
          language: "sql",
          description: "Medidas DAX saneadas para mitigar errores humanos de digitación en SECOP II y conformed filtering.",
          code: `-- Medida DAX: Inversión Saneada (Excluye anomalías tipográficas > 50 Billones COP)
Inversion_Saneada_Billones = 
DIVIDE ( 
    CALCULATE (
        SUM ( mart_gasto_territorial[inversion_total_cop] ),
        mart_gasto_territorial[inversion_total_cop] < 50000000000000 -- Umbral de saneamiento (50 Billones)
    ),
    1000000000000, 
    0 
)

-- Medida DAX: Contratos Adjudicados por Proveedor
Contratos_Por_Proveedor = 
CALCULATE (
    SUM ( mart_concentracion_proveedores[total_contratos] )
)`
        }
      ],
      dashboardData: {
        filterOptions: {
          slicer1: {
            label: "Región Natural:",
            id: "filter-secop-region",
            options: [
              { value: "ALL", label: "Todas las Regiones (5)" },
              { value: "Andina", label: "Región Andina" },
              { value: "Caribe", label: "Región Caribe" },
              { value: "Pacífica", label: "Región Pacífica" },
              { value: "Orinoquía", label: "Región Orinoquía" },
              { value: "Amazonía", label: "Región Amazonía" }
            ]
          },
          slicer2: {
            label: "Año de Firma:",
            id: "filter-secop-year",
            options: [
              { value: "ALL", label: "Todos los Años (2015–2026)" },
              { value: "2026", label: "2026 (En Curso)" },
              { value: "2025", label: "2025" },
              { value: "2024", label: "2024" },
              { value: "2023", label: "2023" },
              { value: "2022", label: "2022" },
              { value: "2021", label: "2021" },
              { value: "2020", label: "2020" },
              { value: "2019", label: "2019" },
              { value: "2018", label: "2018" },
              { value: "2017", label: "2017" },
              { value: "2016", label: "2016" },
              { value: "2015", label: "2015 (Inicio SECOP II)" }
            ]
          }
        },
        kpiTotals: {
          inversionSaneada: "$90.84 Billones",
          totalContratos: "6,013,832",
          proveedores: "1.23M",
          entidades: "6,505",
          directaPct: "92.4%"
        },
        regions: [
          { name: "Región Andina", regionKey: "Andina", inv: 58.42, contracts: 4152000, pct: 64.3, color: "#38bdf8" },
          { name: "Región Caribe", regionKey: "Caribe", inv: 14.18, contracts: 1064000, pct: 15.6, color: "#0d9488" },
          { name: "Región Pacífica", regionKey: "Pacífica", inv: 11.82, contracts: 991000, pct: 13.0, color: "#a855f7" },
          { name: "Región Orinoquía", regionKey: "Orinoquía", inv: 4.28, contracts: 372000, pct: 4.7, color: "#f59e0b" },
          { name: "Región Amazonía", regionKey: "Amazonía", inv: 2.14, contracts: 138000, pct: 2.4, color: "#10b981" }
        ],
        annualSeries: [
          { year: "2015", inv: 0.85, contracts: 42000, directRate: 89.5 },
          { year: "2016", inv: 1.92, contracts: 115000, directRate: 90.2 },
          { year: "2017", inv: 3.45, contracts: 248000, directRate: 90.8 },
          { year: "2018", inv: 5.60, contracts: 435000, directRate: 91.2 },
          { year: "2019", inv: 8.10, contracts: 642000, directRate: 91.5 },
          { year: "2020", inv: 11.20, contracts: 785000, directRate: 91.8 },
          { year: "2021", inv: 13.50, contracts: 894000, directRate: 92.1 },
          { year: "2022", inv: 14.80, contracts: 982000, directRate: 92.5 },
          { year: "2023", inv: 15.20, contracts: 1025000, directRate: 92.7 },
          { year: "2024", inv: 12.40, contracts: 684000, directRate: 93.0 },
          { year: "2025", inv: 3.12, contracts: 148000, directRate: 92.4 },
          { year: "2026", inv: 0.70, contracts: 13832, directRate: 92.1 }
        ],
        departments: [
          { name: "Bogotá, D.C.", contracts: "1,842,500", inv: "$38.20 B", region: "Andina", share: "42.0%" },
          { name: "Valle del Cauca", contracts: "574,300", inv: "$8.92 B", region: "Pacífica", share: "9.8%" },
          { name: "Antioquia", contracts: "530,100", inv: "$8.41 B", region: "Andina", share: "9.3%" },
          { name: "Cundinamarca", contracts: "312,400", inv: "$4.62 B", region: "Andina", share: "5.1%" },
          { name: "Santander", contracts: "285,600", inv: "$3.91 B", region: "Andina", share: "4.3%" },
          { name: "Atlántico", contracts: "241,800", inv: "$3.54 B", region: "Caribe", share: "3.9%" },
          { name: "Bolívar", contracts: "198,200", inv: "$2.81 B", region: "Caribe", share: "3.1%" },
          { name: "Boyacá", contracts: "176,500", inv: "$2.43 B", region: "Andina", share: "2.7%" },
          { name: "Nariño", contracts: "154,200", inv: "$2.12 B", region: "Pacífica", share: "2.3%" },
          { name: "Tolima", contracts: "142,000", inv: "$1.95 B", region: "Andina", share: "2.1%" },
          { name: "Córdoba", contracts: "128,400", inv: "$1.62 B", region: "Caribe", share: "1.8%" },
          { name: "Meta", contracts: "119,300", inv: "$1.51 B", region: "Orinoquía", share: "1.7%" },
          { name: "Cauca", contracts: "104,800", inv: "$1.34 B", region: "Pacífica", share: "1.5%" },
          { name: "Magdalena", contracts: "96,200", inv: "$1.21 B", region: "Caribe", share: "1.3%" },
          { name: "Huila", contracts: "88,700", inv: "$1.12 B", region: "Andina", share: "1.2%" },
          { name: "Caldas", contracts: "84,100", inv: "$1.05 B", region: "Andina", share: "1.1%" }
        ],
        modalidades: [
          { name: "Contratación Directa", count: "5,556,781", pct: 92.4, inv: "$58.12 B", type: "Régimen Directo", color: "#f43f5e" },
          { name: "Selección Abreviada", count: "252,580", pct: 4.2, inv: "$14.65 B", type: "Convocatoria Rápida", color: "#38bdf8" },
          { name: "Régimen Especial", count: "126,290", pct: 2.1, inv: "$8.91 B", type: "Entidades Exentas", color: "#a855f7" },
          { name: "Licitación Pública", count: "54,124", pct: 0.9, inv: "$7.21 B", type: "Concurso Abierto", color: "#10b981" },
          { name: "Mínima Cuantía", count: "24,057", pct: 0.4, inv: "$1.95 B", type: "Adquisición Menor", color: "#f59e0b" }
        ],
        suppliers: [
          { name: "CONSORCIO VIAL NACIONAL", region: "Región Andina", contracts: 34, amount: "$4.21 B COP", share: "4.6%" },
          { name: "ALIANZA ENERGETICA DE COLOMBIA SAS", region: "Región Caribe", contracts: 18, amount: "$3.12 B COP", share: "3.4%" },
          { name: "UNION TEMPORAL BOGOTA DIGITAL", region: "Región Andina", contracts: 12, amount: "$2.84 B COP", share: "3.1%" },
          { name: "LOGISTICA HOSPITALARIA INTEGRAL", region: "Región Pacífica", contracts: 45, amount: "$2.15 B COP", share: "2.3%" },
          { name: "INFRAESTRUCTURA & CONCRETOS DE COLOMBIA", region: "Región Andina", contracts: 29, amount: "$1.92 B COP", share: "2.1%" },
          { name: "COMPAÑIA NACIONAL DE ALIMENTOS PAE SAS", region: "Región Andina", contracts: 82, amount: "$1.64 B COP", share: "1.8%" },
          { name: "SERVICIOS INTEGRALES DE SALUD IPS", region: "Región Caribe", contracts: 64, amount: "$1.41 B COP", share: "1.5%" },
          { name: "CONSTRUCTORA PACIFICO SUR SA", region: "Región Pacífica", contracts: 22, amount: "$1.23 B COP", share: "1.3%" },
          { name: "SUMINISTROS Y DOTACIONES NACIONALES SAS", region: "Región Andina", contracts: 115, amount: "$0.98 B COP", share: "1.1%" },
          { name: "ENLACE TECNOLOGICO ESTATAL SAS", region: "Región Andina", contracts: 38, amount: "$0.85 B COP", share: "0.9%" }
        ]
      }
    }
  ]
};

if (typeof window !== "undefined") {
  window.PORTFOLIO_DATA = PORTFOLIO_DATA;
}
