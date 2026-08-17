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
            embedUrl: "https://app.powerbi.com/view?r=YOUR_PUBLIC_POWERBI_EMBED_ID",
            description: "Omnichannel sales analytics, transaction volume, gross profit margins, and top product ranking across physical POS and Web.",
            metrics: [
              { label: "Total Revenue", value: "$442.0K" },
              { label: "Transactions", value: "4,620" },
              { label: "Avg Margin", value: "34.8%" },
              { label: "POS vs Web", value: "64% / 36%" }
            ]
          },
          {
            id: "v_whatsapp_bot_prod",
            title: "💬 WhatsApp Bot Sales & Demand Funnel",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=whatsapp-bot-prod-embed-placeholder",
            description: "Production WhatsApp sales bot conversion funnel, abandoned cart recovery, and product search demand backlog.",
            metrics: [
              { label: "Active Contacts", value: "1,240" },
              { label: "Orders Processed", value: "318" },
              { label: "Conversion Rate", value: "25.6%" },
              { label: "Baseline State", value: "Clean 0-Record Baseline" }
            ]
          },
          {
            id: "v_inventory_prod",
            title: "📦 Inventory Health & Procurement Expenses",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=inventory-health-prod-embed-placeholder",
            description: "Inventory valuation (Cost vs Retail), low-stock alert monitoring, supplier purchases, and operating expense breakdown.",
            metrics: [
              { label: "Total SKU Count", value: "186" },
              { label: "Inventory Value", value: "$128.5K" },
              { label: "Reorder Alerts", value: "12 SKUs" },
              { label: "Operating Cost", value: "$42.1K" }
            ]
          }
        ],
        dev: [
          {
            id: "v_sales_pos_dev",
            title: "🟡 [DEV] Velykapet POS Staging & Testing",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=dev-sales-staging-placeholder",
            description: "Staging dashboard connected to 'lh_velykapet_gold_dev' lakehouse for testing new margin KPI aggregations.",
            metrics: [
              { label: "Dev Records", value: "14,250" },
              { label: "Spark Execution", value: "28.4s" },
              { label: "Status", value: "Staging Verified" }
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
      id: "dane_employment",
      title: "DANE Colombia Labor Market Analytics (2004 - 2026)",
      category: "Macroeconomic & Labor Market Data Platform",
      badge: "GEIH Microdata Analysis",
      icon: "🇨🇴",
      summary: "22-year longitudinal labor market data pipeline processing Gran Encuesta Integrada de Hogares (GEIH) microdata from DANE Colombia on Microsoft Fabric. Analyzes Global Participation Rate (TGP), Unemployment, and Metropolitan Informal Employment.",
      tags: ["Microsoft Fabric", "PySpark", "Delta Lake", "Data Analysis", "Plotly", "Macroeconomics"],
      reports: {
        prod: [
          {
            id: "dane_macro_prod",
            title: "🇨🇴 DANE National Labor Market & GEIH (2004 - 2026)",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=dane-labor-prod-embed-placeholder",
            description: "Longitudinal analysis of national unemployment rate (TGP), employed population, and formal vs informal labor market metrics.",
            metrics: [
              { label: "Years Analyzed", value: "2004 - 2026 (22 Yrs)" },
              { label: "Employed Pop.", value: "24.2 Million" },
              { label: "Unemployment Rate", value: "9.1%" },
              { label: "TGP Participation", value: "64.5%" }
            ]
          },
          {
            id: "dane_metropolitan_prod",
            title: "🏙️ 13 Cities Metropolitan Area & Informal Labor",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=dane-metropolitan-prod-placeholder",
            description: "Metropolitan area breakdown comparing Bogotá D.C., Medellín A.M., Cali, Barranquilla, and Bucaramanga informal employment rates.",
            metrics: [
              { label: "Top Metropolitan", value: "Bogotá D.C. (9.8%)" },
              { label: "Lowest Unemp.", value: "Bucaramanga (8.1%)" },
              { label: "Avg Informal Rate", value: "41.3%" },
              { label: "Data Source", value: "DANE GEIH Microdata" }
            ]
          }
        ],
        dev: [
          {
            id: "dane_macro_dev",
            title: "🟡 [DEV] GEIH 2026 Quarterly Microdata Ingestion",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=dane-macro-dev-placeholder",
            description: "Staging pipeline testing monthly batch ingestion of DANE raw GEIH microdata files into Fabric Bronze Lakehouse.",
            metrics: [
              { label: "Batch Files", value: "264 Months" },
              { label: "Spark Partition", value: "Year / Month" }
            ]
          }
        ]
      },
      medallion: {
        bronze: {
          name: "lh_dane_employment_bronze",
          type: "GEIH Raw Ingestion",
          description: "Raw DANE GEIH CSV and Parquet files covering 2004 through 2026 labor surveys.",
          tableCount: 4,
          tables: ["raw_geih_ocupados", "raw_geih_desocupados", "raw_geih_inactivos", "raw_geih_caracteristicas_generales"]
        },
        silver: {
          name: "lh_dane_employment_silver",
          type: "Cleansed Microdata Delta Tables",
          description: "Harmonized weights (`fexpr`), standardized expansion factors, and unified regional codes across 22 survey years.",
          tableCount: 3,
          tables: ["silver_geih_person_level", "silver_geih_household_level", "silver_city_dictionary"]
        },
        gold: {
          name: "lh_dane_employment_gold",
          type: "Labor Market Aggregates",
          description: "Monthly and annual time-series aggregates for TGP, Unemployment, and Informal Labor.",
          tableCount: 4,
          tables: ["kpi_national_employment_monthly", "kpi_city_employment_annual", "fact_labor_survey", "dim_time_geih"]
        }
      },
      alm: {
        pipeline: "pl_dane_labor_pipeline",
        stages: [
          { name: "🟢 Development", workspace: "ws-dane-dev", lakehouses: "lh_dane_dev" },
          { name: "🔴 Production", workspace: "ws-dane-prod", lakehouses: "lh_dane_prod" }
        ],
        optimization: "PySpark vectorized UDFs for expansion factor calculations over 50M+ microdata rows."
      },
      codeSnippets: [
        {
          id: "dane_spark_etl",
          title: "dane_geih_transformation.py",
          language: "python",
          description: "PySpark ETL calculating TGP and Unemployment Rate across GEIH microdata.",
          code: `# DANE GEIH Microdata Transformation Engine
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, round as _round, lit

spark = SparkSession.builder.appName("DANE_GEIH_Analytics").getOrCreate()

# Calculate Unemployment Rate (TD) & Global Participation Rate (TGP)
df_geih = spark.read.table("lh_dane_employment_silver.dbo.silver_geih_person_level")

df_kpi = df_geih.groupBy("year", "city_name").agg(
    _sum(col("fexpr") * col("is_occupied")).alias("total_occupied"),
    _sum(col("fexpr") * col("is_unemployed")).alias("total_unemployed"),
    _sum(col("fexpr") * col("is_in_labor_force")).alias("total_labor_force"),
    _sum(col("fexpr") * col("working_age_population")).alias("total_wap")
).withColumn(
    "tasa_desempleo", _round((col("total_unemployed") / col("total_labor_force")) * 100.0, 2)
).withColumn(
    "tgp", _round((col("total_labor_force") / col("total_wap")) * 100.0, 2)
)

df_kpi.write.format("delta").mode("overwrite").saveAsTable("lh_dane_employment_gold.dbo.kpi_city_employment_annual")
print("✅ DANE Labor Market KPIs updated!")`
        }
      ]
    },
    {
      id: "contoso",
      title: "DP-700 Enterprise Contoso Direct Lake Analytics",
      category: "Enterprise BI & Data Warehousing",
      badge: "Microsoft Fabric Direct Lake",
      icon: "🏬",
      summary: "Enterprise Data Engineering project implementing Microsoft Fabric Data Pipelines (`Carga_Contoso_To_Onelake_PL`), OneLake Delta tables, and Direct Lake Semantic Modeling for high-performance Power BI reporting.",
      tags: ["Microsoft Fabric", "Direct Lake", "Data Pipelines", "Power BI", "Data Factory", "DAX"],
      reports: {
        prod: [
          {
            id: "contoso_directlake_prod",
            title: "🏬 Contoso Enterprise Sales & Direct Lake Analytics",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=contoso-directlake-prod-placeholder",
            description: "Direct Lake Power BI report querying multi-million row Contoso OneLake dataset with sub-second DAX response times.",
            metrics: [
              { label: "Storage Engine", value: "Direct Lake Mode" },
              { label: "Source", value: "OneLake Delta Tables" },
              { label: "Data Pipeline", value: "Carga_Masiva_Contoso_PL" },
              { label: "DAX Latency", value: "< 50 ms" }
            ]
          }
        ],
        dev: [
          {
            id: "contoso_directlake_dev",
            title: "🟡 [DEV] Contoso Direct Lake Performance Test",
            embedUrl: "https://app.powerbi.com/reportEmbed?reportId=contoso-dev-placeholder",
            description: "Testing Direct Lake fallbacks to DirectQuery under high query concurrency.",
            metrics: [
              { label: "Fallback Rate", value: "0.0%" },
              { label: "Memory Usage", value: "Optimal" }
            ]
          }
        ]
      },
      medallion: {
        bronze: {
          name: "Contoso_Fabric_LH (Bronze)",
          type: "Data Factory Ingestion",
          description: "Automated Data Factory pipelines copying transactional Contoso DB tables to OneLake.",
          tableCount: 8,
          tables: ["FactSales", "FactInventory", "DimCustomer", "DimProduct", "DimStore", "DimChannel", "DimPromotion", "DimDate"]
        },
        silver: {
          name: "Contoso_Fabric_LH (Silver)",
          type: "OneLake Delta Tables",
          description: "V-Ordered Delta tables optimized for Direct Lake semantic model caching.",
          tableCount: 8,
          tables: ["silver_FactSales", "silver_DimCustomer", "silver_DimProduct", "silver_DimStore", "silver_DimChannel"]
        },
        gold: {
          name: "Contoso_SemanticModel",
          type: "Direct Lake Star Schema",
          description: "Unified Semantic Model serving Direct Lake Power BI reports directly from Delta parquet files without import refresh.",
          tableCount: 6,
          tables: ["FactSales", "DimCustomer", "DimProduct", "DimStore", "DimDate", "DimChannel"]
        }
      },
      alm: {
        pipeline: "Carga_Contoso_To_Onelake_PL",
        stages: [
          { name: "🟢 Dev Workspace", workspace: "DP700-Contoso_Dev", lakehouses: "Contoso_Fabric_LH" }
        ],
        optimization: "Fabric V-Order compression enabled on all OneLake Delta tables for maximum Direct Lake memory caching efficiency."
      },
      codeSnippets: [
        {
          id: "contoso_pipeline",
          title: "Carga_Contoso_To_Onelake_PL.DataPipeline",
          language: "json",
          description: "Data Factory Copy Activity JSON configuration for automated ingestion into OneLake.",
          code: `{
  "name": "Carga_Contoso_To_Onelake_PL",
  "properties": {
    "activities": [
      {
        "name": "Copy_Contoso_Tables",
        "type": "Copy",
        "typeProperties": {
          "source": { "type": "SqlSource" },
          "sink": {
            "type": "LakehouseTableSink",
            "tableActionOption": "Overwrite",
            "partitionOption": "None"
          }
        }
      }
    ]
  }
}`
        }
      ]
    }
  ]
};

if (typeof window !== "undefined") {
  window.PORTFOLIO_DATA = PORTFOLIO_DATA;
}
