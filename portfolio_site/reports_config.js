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
      ]
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
      ]
    }
  ]
};

if (typeof window !== "undefined") {
  window.PORTFOLIO_DATA = PORTFOLIO_DATA;
}
