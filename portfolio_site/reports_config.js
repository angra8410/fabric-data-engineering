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
    }
  ]
};

if (typeof window !== "undefined") {
  window.PORTFOLIO_DATA = PORTFOLIO_DATA;
}
