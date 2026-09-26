import { Question } from '../types';

export const STARTER_QUESTIONS: Question[] = [
  // ================= DOMAIN 1: Plan, implement, and manage an analytics solution (10-15%) =================
  {
    id: 'dp600-d1-001',
    domain: 'domain1',
    topic: 'Capacity & Workspace Admin',
    difficulty: 'Medium',
    text: 'You manage a Fabric F64 capacity. You notice that during peak business hours, background job requests are rejected with throttling errors. You review the Microsoft Fabric Capacity Metrics app and notice high background utilization over a 24-hour window. Which mechanism in Microsoft Fabric is responsible for smoothing background job usage over 24 hours, and what action should you take first?',
    options: [
      { id: 'A', text: 'Fabric interactive smoothing smoothes background jobs over 10 minutes; you should convert all background pipelines to interactive queries.' },
      { id: 'B', text: 'Fabric background operations are smoothed over a 24-hour rolling window; you should identify high-CU operations and schedule non-critical notebooks to off-peak hours.' },
      { id: 'C', text: 'Fabric rejects jobs because autoscale is disabled; you must attach an Azure Synapse dedicated SQL pool to absorb the excess capacity.' },
      { id: 'D', text: 'Fabric only throttles interactive operations; background operations never consume capacity units (CUs).' }
    ],
    correctOptionId: 'B',
    explanation: 'In Microsoft Fabric, operations are split into Interactive (smoothed over 5-10 minutes) and Background (smoothed over 24 hours). If total CU consumption across the 24-hour window exceeds the capacity allowance, background throttling occurs. The immediate best practice is to check the Fabric Capacity Metrics app to identify top CU-consuming operations and stagger heavy workloads (like batch ETL or Spark notebooks) to off-peak periods.',
    distractorExplanations: {
      'A': 'Interactive operations are smoothed over short periods (minutes), whereas background jobs are smoothed over a 24-hour window.',
      'C': 'Azure Synapse dedicated SQL pools cannot be attached as autoscale engines for Fabric capacities.',
      'D': 'Background operations (e.g. data pipelines, scheduled notebooks, semantic model refreshes) definitely consume CUs and can cause capacity throttling.'
    },
    msLearnTitle: 'Microsoft Fabric Capacity Metrics - Smoothing and Throttling',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/enterprise/throttling'
  },
  {
    id: 'dp600-d1-002',
    domain: 'domain1',
    topic: 'Deployment Pipelines & Git',
    difficulty: 'Hard',
    text: 'You are implementing CI/CD for a Fabric solution using Azure DevOps Git integration and Fabric Deployment Pipelines across Dev, Test, and Prod workspaces. You need to ensure that when a Lakehouse and its associated semantic model are deployed from Dev to Test, the semantic model automatically connects to the Test Lakehouse rather than the Dev Lakehouse. What should you configure?',
    options: [
      { id: 'A', text: 'Manually edit the model.bim file in Git before each release and commit to the main branch.' },
      { id: 'B', text: 'Configure Deployment Rules on the semantic model within the Test stage of the Fabric Deployment Pipeline.' },
      { id: 'C', text: 'Create an Azure Data Factory pipeline to copy the schema across workspaces.' },
      { id: 'D', text: 'Use Power BI Desktop to republish the semantic model manually with updated credentials.' }
    ],
    correctOptionId: 'B',
    explanation: 'Fabric Deployment Pipelines support "Deployment Rules" (Data source rules and Parameter rules). Configuring a deployment rule on the target stage (Test or Prod) allows Fabric to automatically redirect the semantic model connection from the source Lakehouse/Warehouse to the corresponding target Lakehouse/Warehouse upon deployment.',
    distractorExplanations: {
      'A': 'Manually editing JSON/BIM files directly violates automated CI/CD practices and introduces human error.',
      'C': 'ADF pipelines do not manage Fabric deployment pipeline binding rules.',
      'D': 'Manual republishing breaks the automated lifecycle and overrides Git-synced metadata.'
    },
    msLearnTitle: 'Create deployment rules in Fabric deployment pipelines',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/create-rules'
  },
  {
    id: 'dp600-d1-003',
    domain: 'domain1',
    topic: 'OneLake Security & Governance',
    difficulty: 'Medium',
    text: 'Your enterprise has implemented a Medallion architecture in Microsoft Fabric. You need to grant external business auditors read-only access to specific tables in the Gold layer of a Fabric Lakehouse, without allowing them to view the underlying raw files in the OneLake bronze directory or edit any items. Which permission configuration achieves this with the principle of least privilege?',
    options: [
      { id: 'A', text: 'Add the auditors as Contributors to the Fabric workspace.' },
      { id: 'B', text: 'Grant auditors Workspace Viewer role and assign OneLake data access security roles (or SQL Analytics Endpoint object-level SELECT permissions) on the Gold tables.' },
      { id: 'C', text: 'Assign the auditors the Workspace Admin role with read-only flags in Azure Active Directory (Entra ID).' },
      { id: 'D', text: 'Create a shared SAS token for the OneLake storage account root.' }
    ],
    correctOptionId: 'B',
    explanation: 'Workspace Viewer role grants read access to workspace items without edit capabilities. To restrict access to specific tables (and prevent access to raw bronze files), use SQL Analytics Endpoint granular permissions (GRANT SELECT ON specific tables) or OneLake data access security roles. Workspace Contributor or Admin would allow viewing raw files and modifying items.',
    distractorExplanations: {
      'A': 'Contributor role grants edit, delete, and full workspace file access.',
      'C': 'Admin role grants full control, including deleting the workspace and modifying permissions.',
      'D': 'SAS tokens at the root compromise the entire OneLake storage security boundary.'
    },
    msLearnTitle: 'Fabric Workspace roles and OneLake security',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/get-started/roles-workspaces'
  },

  // ================= DOMAIN 2: Prepare and connect to data (40-45%) =================
  {
    id: 'dp600-d2-001',
    domain: 'domain2',
    topic: 'OneLake Shortcuts',
    difficulty: 'Easy',
    text: 'You have 15 TB of existing customer demographic data stored in an Azure Data Lake Storage (ADLS) Gen2 container in Delta format. You need to make this data accessible in a Fabric Lakehouse for analysis without duplicating or copying the files over the network. Which Fabric feature should you implement?',
    options: [
      { id: 'A', text: 'Create an external OneLake shortcut pointing to the ADLS Gen2 container.' },
      { id: 'B', text: 'Run a Data Factory Copy activity in a nightly pipeline.' },
      { id: 'C', text: 'Import the data using Dataflows Gen2 with fast-copy enabled.' },
      { id: 'D', text: 'Mount the ADLS Gen2 path in a PySpark notebook and write to a new Delta table.' }
    ],
    correctOptionId: 'A',
    explanation: 'OneLake shortcuts allow you to unify data across domains and clouds without copying. An external shortcut in the Lakehouse Tables or Files directory points directly to the external ADLS Gen2 location, exposing the existing Delta tables instantly to Fabric engines (Spark, SQL, and Direct Lake) with zero data movement.',
    distractorExplanations: {
      'B': 'Copy activity moves and duplicates 15 TB of data, incurring storage and networking costs.',
      'C': 'Dataflows Gen2 also ingests and duplicates data into Fabric.',
      'D': 'Writing to a new Delta table duplicates the 15 TB dataset.'
    },
    msLearnTitle: 'OneLake shortcuts overview',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts'
  },
  {
    id: 'dp600-d2-002',
    domain: 'domain2',
    topic: 'Delta Lake (V-Order, OPTIMIZE, VACUUM)',
    difficulty: 'Medium',
    text: 'You maintain a high-volume Lakehouse table that receives append-only streaming sensor data throughout the day. Queries are degrading in performance because thousands of small files have accumulated. Furthermore, queries typically filter on DeviceID and DateKey. Which PySpark or SQL command should you execute to compact small files and organize data for optimal scan performance?',
    codeSnippet: {
      language: 'sql',
      code: '-- Option command structure to optimize telemetry table\nOPTIMIZE TelemetryReading ...'
    },
    options: [
      { id: 'A', text: 'VACUUM TelemetryReading RETAIN 0 HOURS' },
      { id: 'B', text: 'OPTIMIZE TelemetryReading ZORDER BY (DeviceID, DateKey)' },
      { id: 'C', text: 'ALTER TABLE TelemetryReading SET TBLPROPERTIES (\'delta.autoOptimize.optimizeWrite\' = false)' },
      { id: 'D', text: 'DBCC CHECKDB(TelemetryReading) WITH COMPACT' }
    ],
    correctOptionId: 'B',
    explanation: 'The `OPTIMIZE` command compacts small files into larger ~1 GB Parquet files. Adding `ZORDER BY (DeviceID, DateKey)` colocates related column data along a multidimensional space-filling curve, dramatically improving file-skipping for queries filtering on those columns. In Fabric, Delta writes also apply V-Order by default.',
    distractorExplanations: {
      'A': 'VACUUM only removes files that have already been compacted or soft-deleted beyond the retention period; it does not compact small active files.',
      'C': 'Disabling optimizeWrite will worsen small file generation.',
      'D': 'DBCC CHECKDB is an on-prem SQL Server command not applicable to Delta Lake tables.'
    },
    msLearnTitle: 'Delta Lake table optimization and V-Order in Fabric',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-optimize'
  },
  {
    id: 'dp600-d2-003',
    domain: 'domain2',
    topic: 'Lakehouse vs Warehouse',
    difficulty: 'Hard',
    text: 'You are designing the enterprise data platform. The engineering team consists primarily of SQL developers who require full multi-table ACID transactions, cross-database queries using three-part naming (`Database.Schema.Table`), primary key / foreign key constraints (with informational metadata), and native T-SQL DDL/DML. Data will be consumed by semantic models. Which Fabric artifact should you choose?',
    options: [
      { id: 'A', text: 'Fabric Lakehouse' },
      { id: 'B', text: 'Fabric Warehouse' },
      { id: 'C', text: 'KQL Database' },
      { id: 'D', text: 'Dataflow Gen2 Staging Lakehouse' }
    ],
    correctOptionId: 'B',
    explanation: 'Fabric Warehouse provides a complete, modern T-SQL data warehousing engine with full DML/DDL (CREATE TABLE, INSERT, UPDATE, DELETE), multi-table transactions within a session, cross-warehouse queries with three-part naming, and SQL-native security (RLS, CLS). A Lakehouse is file/folder centric and driven primarily by Spark/Python, with a read-only SQL endpoint.',
    distractorExplanations: {
      'A': 'A Lakehouse provides a read-only SQL Analytics Endpoint; you cannot run native T-SQL DDL (CREATE TABLE) or multi-table ACID DML transactions against it.',
      'C': 'KQL Database is designed for real-time telemetry streaming using Kusto Query Language, not relational enterprise warehousing.',
      'D': 'Staging Lakehouse is an internal engine artifact for Dataflows Gen2, not a user-facing modeling destination.'
    },
    msLearnTitle: 'Fabric Warehouse vs Lakehouse comparison',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/data-warehouse/lakehouse-vs-warehouse'
  },
  {
    id: 'dp600-d2-004',
    domain: 'domain2',
    topic: 'PySpark Transformations',
    difficulty: 'Medium',
    text: 'You are writing a PySpark transformation in a Fabric Notebook to ingest customer orders. You need to deduplicate records based on `OrderID`, keeping only the most recently updated record determined by `LastModifiedTimestamp`. Which code snippet achieves this efficiently in PySpark?',
    codeSnippet: {
      language: 'python',
      code: 'from pyspark.sql.window import Window\nimport pyspark.sql.functions as F\n\n# Deduplication logic to implement'
    },
    options: [
      {
        id: 'A',
        text: 'windowSpec = Window.partitionBy("OrderID").orderBy(F.col("LastModifiedTimestamp").desc())\ndf_dedup = df.withColumn("rn", F.row_number().over(windowSpec)).filter("rn == 1").drop("rn")'
      },
      {
        id: 'B',
        text: 'df_dedup = df.groupBy("OrderID").max("LastModifiedTimestamp")'
      },
      {
        id: 'C',
        text: 'df_dedup = df.dropDuplicates(["LastModifiedTimestamp"])'
      },
      {
        id: 'D',
        text: 'df_dedup = df.distinct()'
      }
    ],
    correctOptionId: 'A',
    explanation: 'Using `Window.partitionBy("OrderID").orderBy(col("LastModifiedTimestamp").desc())` combined with `row_number() == 1` is the standard, reliable PySpark pattern to deduplicate by key while preserving all columns from the latest record.',
    distractorExplanations: {
      'B': 'groupBy().max() loses all other columns in the DataFrame besides the grouping key and max date.',
      'C': 'dropDuplicates(["LastModifiedTimestamp"]) drops records with duplicate timestamps regardless of OrderID.',
      'D': 'distinct() only removes rows where EVERY single column value is completely identical.'
    },
    msLearnTitle: 'Data transformations with Apache Spark in Fabric',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/data-engineering/pyspark-window-functions'
  },
  {
    id: 'dp600-d2-005',
    domain: 'domain2',
    topic: 'Delta Lake (V-Order, OPTIMIZE, VACUUM)',
    difficulty: 'Medium',
    text: 'What is the primary benefit of Microsoft Fabric V-Order write optimization when writing Delta tables in a Lakehouse or Warehouse?',
    options: [
      { id: 'A', text: 'It encrypts the Parquet files using customer-managed Azure Key Vault keys.' },
      { id: 'B', text: 'It applies special in-memory sorting, row group distribution, and dictionary encoding to Parquet files, enabling lightning-fast read operations for Power BI Direct Lake and VertiPaq engine.' },
      { id: 'C', text: 'It automatically converts Delta tables into CSV files for legacy Excel export.' },
      { id: 'D', text: 'It forces data to be written across all Azure geographic regions simultaneously.' }
    ],
    correctOptionId: 'B',
    explanation: 'V-Order is a Microsoft-proprietary write-time optimization for the open Parquet standard. It organizes data in Parquet files with sorting and compression techniques optimized specifically for the Power BI VertiPaq engine and Direct Lake mode, leading to 2x-10x faster scan times without breaking standard Parquet reader compatibility.',
    distractorExplanations: {
      'A': 'V-Order is a performance read-optimization format, not an encryption mechanism.',
      'C': 'V-Order maintains Parquet format, not CSV.',
      'D': 'V-Order is local file layout optimization, not cross-region geo-replication.'
    },
    msLearnTitle: 'Delta Lake table optimization and V-Order',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-optimize#what-is-v-order'
  },

  // ================= DOMAIN 3: Model and explore data (40-45%) =================
  {
    id: 'dp600-d3-001',
    domain: 'domain3',
    topic: 'Direct Lake Requirements & Fallback',
    difficulty: 'Hard',
    text: 'You have configured a Power BI semantic model using Direct Lake mode connected to a Fabric Lakehouse Delta table. However, during user queries, users experience slow report performance. You inspect the query logs and discover that queries are falling back to DirectQuery mode. Which of the following conditions is a known trigger that forces a Direct Lake model to fall back to DirectQuery?',
    options: [
      { id: 'A', text: 'The underlying Delta table is compressed with Snappy.' },
      { id: 'B', text: 'The semantic model contains a DAX Calculated Table or Calculated Column, or Row-Level Security (RLS) is defined directly in the Lakehouse SQL Analytics Endpoint rather than in the semantic model.' },
      { id: 'C', text: 'The workspace is hosted on an F64 capacity.' },
      { id: 'D', text: 'The semantic model has relationships defined using Integer surrogate keys.' }
    ],
    correctOptionId: 'B',
    explanation: 'Direct Lake mode reads Parquet Delta files directly into the VertiPaq memory. Key fallback triggers include: adding calculated columns or calculated tables in the model (which cannot be read from OneLake Parquet directly), exceeding capacity memory limits, views instead of tables, or using SQL Endpoint RLS (which blocks Direct Lake and forces DirectQuery). Note: Fabric now supports RLS defined inside the Direct Lake semantic model itself, but SQL endpoint RLS causes fallback.',
    distractorExplanations: {
      'A': 'Snappy compression is the default and fully supported in Parquet and Direct Lake.',
      'C': 'F64 capacity has ample memory and fully supports Direct Lake.',
      'D': 'Integer surrogate key relationships are standard and optimal in Direct Lake models.'
    },
    msLearnTitle: 'Learn about Direct Lake in Power BI and Microsoft Fabric',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/get-started/direct-lake-overview'
  },
  {
    id: 'dp600-d3-002',
    domain: 'domain3',
    topic: 'Calculation Groups & Field Parameters',
    difficulty: 'Medium',
    text: 'You have 25 base financial measures (e.g. Total Sales, Total Cost, Gross Margin, Units Sold). The finance department requires 6 time-intelligence variations for every single measure: MTD, QTD, YTD, YoY Growth, YoY Growth %, and Prior Year. Creating separate DAX measures would require authoring 150 individual measures. Which modeling technique should you implement using Tabular Editor?',
    options: [
      { id: 'A', text: 'Create 150 calculated columns in the underlying Delta table.' },
      { id: 'B', text: 'Implement a Calculation Group with Calculation Items that utilize `SELECTEDMEASURE()`.' },
      { id: 'C', text: 'Create a Field Parameter table with static measure references.' },
      { id: 'D', text: 'Use a Quick Measure template repeated across all report visuals.' }
    ],
    correctOptionId: 'B',
    explanation: 'Calculation Groups drastically reduce measure proliferation. By authoring a single Calculation Group (e.g. "Time Intelligence") with calculation items (YTD, QTD, YoY) referencing `SELECTEDMEASURE()`, all 25 base measures instantly inherit all 6 time-intelligence calculations without writing 150 individual measures.',
    distractorExplanations: {
      'A': 'Calculated columns consume memory and do not support dynamic measure aggregation or context transition.',
      'C': 'Field Parameters allow users to dynamically switch which measure is displayed on an axis, but do not apply time-intelligence transformations across arbitrary measures.',
      'D': 'Quick Measures still create 150 discrete measures in the model.'
    },
    msLearnTitle: 'Calculation groups in Analysis Services and Power BI',
    msLearnUrl: 'https://learn.microsoft.com/en-us/analysis-services/tabular-models/calculation-groups'
  },
  {
    id: 'dp600-d3-003',
    domain: 'domain3',
    topic: 'Tabular Modeling & DAX',
    difficulty: 'Hard',
    text: 'You are authoring a DAX measure in a large sales model. You need to calculate the sales amount for customers located in the "Europe" region while preserving any existing report visual filters on other columns of the Customer table, such as Customer Segment or Age Group. Which DAX expression follows best practices?',
    options: [
      {
        id: 'A',
        text: 'CALCULATE([Total Sales], Customer[Region] = "Europe")'
      },
      {
        id: 'B',
        text: 'CALCULATE([Total Sales], FILTER(ALL(Customer), Customer[Region] = "Europe"))'
      },
      {
        id: 'C',
        text: 'CALCULATE([Total Sales], KEEPFILTERS(Customer[Region] = "Europe"))'
      },
      {
        id: 'D',
        text: 'FILTER([Total Sales], Customer[Region] == "Europe")'
      }
    ],
    correctOptionId: 'A',
    explanation: '`CALCULATE([Total Sales], Customer[Region] = "Europe")` translates under the hood to `FILTER(ALL(Customer[Region]), Customer[Region] = "Europe")`. This replaces any existing filter on `Customer[Region]` while preserving all existing filters on other columns of the Customer table (such as Segment or Age Group). Option B (`ALL(Customer)`) would overwrite and wipe out ALL filters on the entire Customer table.',
    distractorExplanations: {
      'B': 'Using FILTER(ALL(Customer), ...) strips away filters from every other column in the Customer table.',
      'C': 'KEEPFILTERS intersects filters, so if a visual is filtered by "North America", KEEPFILTERS would return blank rather than forcing "Europe".',
      'D': 'FILTER returns a table, not a scalar measure value.'
    },
    msLearnTitle: 'Filter context and CALCULATE in DAX',
    msLearnUrl: 'https://learn.microsoft.com/en-us/dax/calculate-function-dax'
  },
  {
    id: 'dp600-d3-004',
    domain: 'domain3',
    topic: 'DAX Studio & Performance Tuning',
    difficulty: 'Hard',
    text: 'You are using DAX Studio to troubleshoot a slow Power BI report connected to a Fabric Warehouse. You examine the Server Timings trace and discover that the Storage Engine (SE) query duration is 25 ms, while the Formula Engine (FE) query duration is 4,800 ms. The query metric shows a high count of row-by-row callback iterations (`CallbackDataID`). What does this indicate, and how should you resolve it?',
    options: [
      { id: 'A', text: 'The VertiPaq Storage Engine is overloaded; you need to scale up your Fabric capacity SKU.' },
      { id: 'B', text: 'The DAX formula contains operations that cannot be evaluated inside the multi-threaded Storage Engine, forcing the single-threaded Formula Engine to evaluate rows sequentially. You should refactor DAX to eliminate conditional row-level iterations.' },
      { id: 'C', text: 'The network connection between DAX Studio and Fabric is throttling the query.' },
      { id: 'D', text: 'The Warehouse needs an index rebuild on the fact table.' }
    ],
    correctOptionId: 'B',
    explanation: 'In DAX architecture, the Storage Engine (SE) is multi-threaded and extremely fast, whereas the Formula Engine (FE) is single-threaded. High FE time coupled with `CallbackDataID` indicates that the Formula Engine had to repeatedly step into the Storage Engine on a row-by-row basis to evaluate complex logic (such as nested IFs or unsupported functions). Refactoring the DAX measure to allow pure SE vector evaluation resolves the bottleneck.',
    distractorExplanations: {
      'A': 'The SE duration is only 25 ms, proving the Storage Engine is not the bottleneck.',
      'C': 'Network latency does not manifest as Formula Engine internal processing time in Server Timings.',
      'D': 'Fabric Warehouse Delta tables do not have traditional SQL Server index rebuilds.'
    },
    msLearnTitle: 'Optimize DAX and use DAX Studio Server Timings',
    msLearnUrl: 'https://learn.microsoft.com/en-us/power-bi/guidance/dax-performance'
  },
  {
    id: 'dp600-d3-005',
    domain: 'domain3',
    topic: 'Real-Time Intelligence (KQL)',
    difficulty: 'Medium',
    text: 'You are streaming IoT sensor events into a Microsoft Fabric KQL Database. You need to write a KQL query that calculates the average temperature per machine for the last 15 minutes, aggregated into 1-minute time buckets. Which KQL query is correct?',
    codeSnippet: {
      language: 'kql',
      code: '// SensorReadings table schema: Timestamp (datetime), MachineID (string), Temperature (real)'
    },
    options: [
      {
        id: 'A',
        text: 'SensorReadings\n| where Timestamp > ago(15m)\n| summarize AvgTemp = avg(Temperature) by MachineID, bin(Timestamp, 1m)'
      },
      {
        id: 'B',
        text: 'SELECT MachineID, AVG(Temperature) FROM SensorReadings WHERE Timestamp > NOW() - 15 GROUP BY MachineID'
      },
      {
        id: 'C',
        text: 'SensorReadings\n| filter Timestamp between (1m, 15m)\n| group by MachineID\n| calculate avg(Temperature)'
      },
      {
        id: 'D',
        text: 'SensorReadings\n| window(1m)\n| aggregate Temperature.mean() over MachineID'
      }
    ],
    correctOptionId: 'A',
    explanation: 'In Kusto Query Language (KQL), filtering by relative time is done using `where Timestamp > ago(15m)`, and time bucketing is accomplished using `summarize avg(col) by GroupCol, bin(Timestamp, 1m)`.',
    distractorExplanations: {
      'B': 'This is pseudo-SQL syntax, not valid KQL.',
      'C': 'KQL uses `where` rather than `filter` and `summarize` rather than `group by`.',
      'D': 'This is pandas/streaming syntax, not KQL.'
    },
    msLearnTitle: 'Kusto Query Language (KQL) overview and summarize operator',
    msLearnUrl: 'https://learn.microsoft.com/en-us/kusto/query/summarizeoperator'
  },

  // ================= CASE STUDY QUESTIONS (Contoso Enterprise) =================
  {
    id: 'dp600-cs-001',
    caseStudyId: 'cs-fabric-enterprise',
    domain: 'domain2',
    topic: 'OneLake Shortcuts',
    difficulty: 'Hard',
    text: '[Case Study: Contoso] Contoso receives telemetry JSON files every 5 minutes in an external ADLS Gen2 container. Which solution satisfies the business requirement to avoid data duplication between the external ADLS Gen2 data lake and Fabric while supporting downstream PySpark Bronze processing?',
    options: [
      { id: 'A', text: 'Create an ADLS Gen2 shortcut in the "Files" section of the Bronze Lakehouse.' },
      { id: 'B', text: 'Create an ADLS Gen2 shortcut in the "Tables" section of the Gold Warehouse.' },
      { id: 'C', text: 'Set up an Azure Data Factory Copy pipeline with tumbling window triggers.' },
      { id: 'D', text: 'Use Dataflows Gen2 to ingest and staging-save to OneLake.' }
    ],
    correctOptionId: 'A',
    explanation: 'Creating a shortcut under the "Files" section of the Bronze Lakehouse directly exposes the raw JSON files stored in ADLS Gen2 without copying any data. Spark notebooks can read this shortcut path directly to parse and write clean Delta tables into the Silver layer.',
    distractorExplanations: {
      'B': 'The "Tables" section expects structured Delta tables, not raw semi-structured JSON files.',
      'C': 'Copy pipeline duplicates data and incurs network/storage overhead, violating the zero-duplication requirement.',
      'D': 'Dataflows Gen2 also stages and duplicates the data.'
    },
    msLearnTitle: 'Create an ADLS Gen2 shortcut in Microsoft Fabric',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/onelake/create-adls-gen2-shortcut'
  },
  {
    id: 'dp600-cs-002',
    caseStudyId: 'cs-fabric-enterprise',
    domain: 'domain3',
    topic: 'Direct Lake Requirements & Fallback',
    difficulty: 'Hard',
    text: '[Case Study: Contoso] Contoso reported that the new executive sales report silently fell back from Direct Lake to DirectQuery mode during business testing. Based on Contoso’s existing architecture and requirements, what is the most likely cause of this fallback?',
    options: [
      { id: 'A', text: 'The semantic model utilizes integer primary keys.' },
      { id: 'B', text: 'The existing SSAS model’s calculated columns were migrated directly into the Power BI semantic model.' },
      { id: 'C', text: 'The Lakehouse tables were formatted using Delta Lake with V-Order enabled.' },
      { id: 'D', text: 'The report was accessed by multiple executive users simultaneously.' }
    ],
    correctOptionId: 'B',
    explanation: 'Direct Lake models cannot materialize DAX calculated columns or calculated tables because Direct Lake reads data directly from Parquet Delta files in OneLake without intermediate processing. Introducing DAX calculated columns immediately forces the semantic model to fall back to DirectQuery mode. Calculations must be pushed upstream into the Lakehouse/Warehouse Delta tables.',
    distractorExplanations: {
      'A': 'Integer keys are completely standard in star schemas and Direct Lake.',
      'C': 'V-Order is specifically designed for Direct Lake and will never cause fallback.',
      'D': 'Concurrent users do not cause fallback unless capacity memory limits are exceeded.'
    },
    msLearnTitle: 'Direct Lake fallback triggers and limitations',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/get-started/direct-lake-overview#fallback'
  },
  {
    id: 'dp600-cs-003',
    caseStudyId: 'cs-fabric-enterprise',
    domain: 'domain2',
    topic: 'Delta Lake (V-Order, OPTIMIZE, VACUUM)',
    difficulty: 'Medium',
    text: '[Case Study: Contoso] Contoso identified that Spark notebooks running on the bronze Lakehouse are creating thousands of tiny 50 KB Parquet files, slowing downstream read performance. What two configurations should you implement to resolve this issue?',
    options: [
      { id: 'A', text: 'Enable V-Order on writes and run `OPTIMIZE` on the Delta tables periodically.' },
      { id: 'B', text: 'Switch the Spark notebook language to Scala and disable Delta Lake.' },
      { id: 'C', text: 'Increase the Fabric capacity to F512.' },
      { id: 'D', text: 'Export all tables to CSV files.' }
    ],
    correctOptionId: 'A',
    explanation: 'Running `OPTIMIZE` consolidates the small 50 KB files into uniform ~1 GB Parquet files, reducing metadata overhead and maximizing scan throughput. Enabling V-Order write optimization ensures that files are sorted and compressed for fast analytical querying.',
    distractorExplanations: {
      'B': 'Disabling Delta Lake loses ACID transactions, time travel, and Direct Lake compatibility.',
      'C': 'Scaling capacity does not resolve small file proliferation.',
      'D': 'CSV files are not supported in Direct Lake and lack columnar performance.'
    },
    msLearnTitle: 'Optimize Delta tables in Fabric Lakehouse',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-optimize'
  },
  {
    id: 'dp600-cs-004',
    caseStudyId: 'cs-fabric-enterprise',
    domain: 'domain1',
    topic: 'Deployment Pipelines & Git',
    difficulty: 'Hard',
    text: '[Case Study: Contoso] Contoso requires automated deployment of Lakehouses, Warehouses, and Semantic Models via Azure DevOps. What format should Power BI developer artifacts be saved in to support granular Git branching, merging, and pull request reviews?',
    options: [
      { id: 'A', text: 'Power BI Desktop Single Binary (.pbix)' },
      { id: 'B', text: 'Power BI Project format (.pbip) using PBIR format for reports and TMDL for semantic models' },
      { id: 'C', text: 'Excel Workbook (.xlsx)' },
      { id: 'D', text: 'SQL Server Data Tools (.ssdtproj)' }
    ],
    correctOptionId: 'B',
    explanation: 'Power BI Project files (.pbip) decompose reports and datasets into text-based files. Using PBIR (Power BI Report format) and TMDL (Tabular Model Definition Language) represents reports and semantic models as clean, human-readable JSON/text files, making Git version control, branching, diffs, and pull requests seamless.',
    distractorExplanations: {
      'A': '.pbix is a binary zip format that cannot be diffed, merged, or reviewed effectively in Git.',
      'C': 'Excel workbooks are not Fabric developer artifacts.',
      'D': 'SSDT projects are for legacy SSAS/SSIS and not the native Fabric Git format.'
    },
    msLearnTitle: 'Fabric Git integration and Power BI Project (.pbip)',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration'
  },

  // ================= DRAG AND DROP / STEP ORDERING QUESTIONS =================
  {
    id: 'dp600-ord-001',
    type: 'drag_and_drop',
    domain: 'domain1',
    topic: 'Git Integration & CI/CD',
    difficulty: 'Hard',
    text: 'You need to establish a collaborative CI/CD development workflow for a Fabric workspace using Azure DevOps Git integration. Which four actions should you perform in sequence?',
    options: [
      { id: 'A', text: 'Step 1: Connect workspace to Azure DevOps Git repository and main branch' },
      { id: 'B', text: 'Step 2: Create a personal development branch from main' },
      { id: 'C', text: 'Step 3: Modify workspace artifacts and commit changes to your branch' },
      { id: 'D', text: 'Step 4: Create a pull request (PR) in Azure DevOps to merge into main' }
    ],
    correctOptionId: 'A',
    orderingSteps: [
      { id: 's1', text: 'Connect the Fabric workspace to the Azure DevOps Git repository and main branch.' },
      { id: 's2', text: 'From the workspace or Git repo, create a personal development branch from main.' },
      { id: 's3', text: 'Make changes to workspace artifacts and commit your updates to the feature branch.' },
      { id: 's4', text: 'Create a pull request (PR) in Azure DevOps to review and merge changes into main.' }
    ],
    correctOrder: ['s1', 's2', 's3', 's4'],
    explanation: 'In Microsoft Fabric Git integration: 1) First link the workspace to the Azure DevOps repository and main branch. 2) Branch off main into an isolated feature/dev branch. 3) Author and commit changes to the feature branch. 4) Open a Pull Request (PR) in Azure DevOps for peer code review and merging into the release branch.',
    msLearnTitle: 'Implement version control and Git integration in Fabric',
    msLearnUrl: 'https://learn.microsoft.com/en-us/training/modules/implement-cicd-in-fabric/3-implement-version-control-and-git-integration'
  },
  {
    id: 'dp600-ord-002',
    type: 'drag_and_drop',
    domain: 'domain2',
    topic: 'Delta Lake (V-Order, OPTIMIZE, VACUUM)',
    difficulty: 'Hard',
    text: 'You are implementing an end-to-end Medallion pipeline in a Fabric Lakehouse to process high-volume sensor telemetry data and maximize Power BI Direct Lake performance. Which four steps should you perform in sequence?',
    options: [
      { id: 'A', text: 'Step 1: Ingest raw telemetry files into the Lakehouse Files directory' },
      { id: 'B', text: 'Step 2: Transform raw files into Silver Delta tables with schema enforcement' },
      { id: 'C', text: 'Step 3: Execute OPTIMIZE ZORDER BY on filter columns with V-Order enabled' },
      { id: 'D', text: 'Step 4: Run VACUUM to purge expired historical transaction files' }
    ],
    correctOptionId: 'A',
    orderingSteps: [
      { id: 'step-bronze', text: 'Ingest raw telemetry JSON files into the Bronze Files directory of the Lakehouse.' },
      { id: 'step-silver', text: 'Execute a PySpark notebook to validate schemas and append clean rows to Silver Delta tables.' },
      { id: 'step-optimize', text: 'Execute OPTIMIZE SilverTable ZORDER BY (DeviceID, DateKey) with V-Order enabled.' },
      { id: 'step-vacuum', text: 'Run VACUUM SilverTable RETAIN 168 HOURS to remove obsolete compacted files.' }
    ],
    correctOrder: ['step-bronze', 'step-silver', 'step-optimize', 'step-vacuum'],
    explanation: 'The standard Medallion workflow: 1) Ingest raw files to Bronze. 2) Cleanse and enforce schema into Silver Delta format. 3) Compact small files and sort columns using OPTIMIZE with ZORDER and V-Order for fast VertiPaq scans. 4) Periodically run VACUUM with appropriate retention (default 7 days / 168 hours) to clean up soft-deleted files.',
    msLearnTitle: 'Delta Lake table optimization in Microsoft Fabric',
    msLearnUrl: 'https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-optimize'
  },
  {
    id: 'dp600-ord-003',
    type: 'drag_and_drop',
    domain: 'domain3',
    topic: 'Calculation Groups & Field Parameters',
    difficulty: 'Hard',
    text: 'You need to build a Direct Lake semantic model with dynamic time-intelligence Calculation Groups (YTD, QTD, Prior Year) for 30 base financial measures. Which four steps should you perform in sequence?',
    options: [
      { id: 'A', text: 'Step 1: Create a Direct Lake semantic model from Lakehouse Delta tables' },
      { id: 'B', text: 'Step 2: Connect Tabular Editor to the workspace XMLA read/write endpoint' },
      { id: 'C', text: 'Step 3: Create a Calculation Group with calculation items using SELECTEDMEASURE()' },
      { id: 'D', text: 'Step 4: Save model metadata changes and publish Power BI reports using the group' }
    ],
    correctOptionId: 'A',
    orderingSteps: [
      { id: 'cg-1', text: 'Create a Power BI semantic model using Direct Lake mode connected to Lakehouse Gold Delta tables.' },
      { id: 'cg-2', text: 'Connect Tabular Editor 2 or 3 to the Fabric workspace XMLA endpoint.' },
      { id: 'cg-3', text: 'Author a Calculation Group (e.g. "Time Intelligence") with Calculation Items referencing SELECTEDMEASURE().' },
      { id: 'cg-4', text: 'Save changes back to the workspace and use the calculation group in report slicers or matrix columns.' }
    ],
    correctOrder: ['cg-1', 'cg-2', 'cg-3', 'cg-4'],
    explanation: 'Direct Lake models with Calculation Groups are configured by: 1) Establishing the Direct Lake semantic model on Parquet Delta tables. 2) Opening the model in Tabular Editor via the XMLA endpoint. 3) Defining the Calculation Group and items using SELECTEDMEASURE() to apply time intelligence dynamically across all base measures. 4) Saving model metadata back to Fabric and consuming in visuals.',
    msLearnTitle: 'Calculation groups in Tabular models and Power BI',
    msLearnUrl: 'https://learn.microsoft.com/en-us/analysis-services/tabular-models/calculation-groups'
  }
];
