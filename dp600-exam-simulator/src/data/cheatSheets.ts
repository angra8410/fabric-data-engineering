import { CheatSheet } from '../types';

export interface ExtendedCheatSheet extends CheatSheet {
  tag?: string;
}

export const FABRIC_CHEAT_SHEETS: ExtendedCheatSheet[] = [
  {
    id: 'direct-lake-guide',
    title: 'Direct Lake vs. Import vs. DirectQuery',
    badge: 'Model and Explore Data',
    tag: 'model-direct-lake-storage',
    domain: 'domain3',
    summary: 'Direct Lake delivers the blazing speed of Import mode without scheduled refresh delays or data duplication, by loading Delta Parquet files directly from OneLake into the VertiPaq memory engine.',
    comparisonTable: {
      headers: ['Feature', 'Direct Lake', 'Import Mode', 'DirectQuery'],
      rows: [
        { label: 'Data Latency', values: ['Near real-time (framed upon Delta commit)', 'Scheduled refresh latency', 'Real-time (live query time)'] },
        { label: 'VertiPaq Memory', values: ['Paged directly from OneLake on demand', 'Entire dataset loaded in RAM', 'None (processed at source engine)'] },
        { label: 'Calculated Columns', values: ['NOT supported (forces fallback to DQ)', 'Supported in DAX', 'Supported (translated to SQL)'] },
        { label: 'Max Data Size', values: ['Subject to capacity memory SKU limits', 'Limited by model size limit (e.g. 10 GB)', 'Virtually unlimited (source dependent)'] },
        { label: 'Fallback Behavior', values: ['Falls back silently or strictly to DirectQuery', 'No fallback', 'Native SQL pushdown'] }
      ]
    },
    keyRules: [
      'Direct Lake only reads Delta Parquet tables with V-Order. Lakehouse/Warehouse views cannot be queried via Direct Lake.',
      'Never add DAX calculated tables or calculated columns to a Direct Lake model—it triggers immediate DirectQuery fallback.',
      'If capacity memory is exceeded or unsupported DAX features are called, query falls back to DirectQuery unless set to DirectLakeOnly.',
      'Define Row-Level Security (RLS) within the Power BI semantic model, not on the SQL endpoint, to prevent DQ fallback.'
    ],
    commonTrap: 'Exam scenario: "You need calculated business metrics in a Direct Lake model and want to avoid DirectQuery fallback." Trap answer: Add DAX calculated columns. Correct answer: Calculate the column upstream in the PySpark notebook or Warehouse T-SQL table.',
    msLearnRef: {
      title: 'Learn about Direct Lake in Microsoft Fabric',
      url: 'https://learn.microsoft.com/en-us/fabric/get-started/direct-lake-overview'
    }
  },
  {
    id: 'lakehouse-vs-warehouse',
    title: 'Fabric Lakehouse vs. Fabric Warehouse',
    badge: 'Prepare and Connect to Data',
    tag: 'prep-lakehouse-vs-warehouse',
    domain: 'domain2',
    summary: 'Both store data in open Delta Lake Parquet format in OneLake, but their primary engines, authoring experiences, and SQL transaction capabilities differ significantly.',
    comparisonTable: {
      headers: ['Capability', 'Fabric Lakehouse', 'Fabric Warehouse'],
      rows: [
        { label: 'Primary Persona', values: ['Data Engineers, Data Scientists (Spark/Python)', 'SQL Developers, BI Engineers (T-SQL)'] },
        { label: 'Primary Engine', values: ['Apache Spark (read-only SQL Endpoint)', 'Distributed T-SQL Engine (full read/write)'] },
        { label: 'T-SQL DDL / DML', values: ['Read-only (SELECT) via SQL endpoint', 'Full T-SQL (CREATE, ALTER, INSERT, UPDATE, DELETE)'] },
        { label: 'Multi-Table Transactions', values: ['Not supported in SQL endpoint', 'Fully supported ACID multi-table transactions'] },
        { label: 'Data Types & Files', values: ['Structured Delta tables + unstructured files/folders', 'Structured relational Delta tables only'] },
        { label: 'Cross-Database Queries', values: ['Supported via 3-part naming in SQL endpoint', 'Supported via 3-part naming (DB.Schema.Table)'] }
      ]
    },
    keyRules: [
      'Choose Lakehouse if: Team writes PySpark/Scala/R, requires raw unstructured files, or wants automated schema evolution on streaming logs.',
      'Choose Warehouse if: Team writes complex T-SQL stored procedures, needs multi-table atomic ACID transactions, or requires native T-SQL row/column security.',
      'Lakehouse SQL endpoint is read-only; table creation and modifications must be performed through Spark or Pipelines.',
      'Warehouse Delta tables automatically apply V-Order optimization on all writes for VertiPaq query acceleration.'
    ],
    commonTrap: 'Exam scenario: "SQL developers need to create tables and execute UPDATE statements using T-SQL." Trap answer: Lakehouse SQL endpoint. Correct answer: Fabric Warehouse.',
    msLearnRef: {
      title: 'Fabric Warehouse vs Lakehouse decision guide',
      url: 'https://learn.microsoft.com/en-us/fabric/data-warehouse/lakehouse-vs-warehouse'
    }
  },
  {
    id: 'delta-optimization-guide',
    title: 'Delta Optimization: OPTIMIZE, VACUUM & V-Order',
    badge: 'Prepare and Connect to Data',
    tag: 'prep-delta-maintenance',
    domain: 'domain2',
    summary: 'Delta tables in OneLake accumulate small files and old versions over time. Knowing the exact purpose and syntax of OPTIMIZE, Z-ORDER, VACUUM, and V-Order is essential for DP-600.',
    comparisonTable: {
      headers: ['Command / Feature', 'What It Does', 'When To Use It', 'Key Constraint / Setting'],
      rows: [
        { label: 'OPTIMIZE', values: ['Compacts small files into ~1 GB Parquet files', 'After frequent small appends or streaming batches', 'Does not delete historical files by itself'] },
        { label: 'Z-ORDER BY (col1, col2)', values: ['Colocates column data using space-filling curves', 'Columns frequently used in WHERE filters', 'Only run on 1 to 4 high-cardinality filter columns'] },
        { label: 'VACUUM', values: ['Permanently deletes unreferenced files older than retention', 'Scheduled cleanup to reclaim OneLake storage', 'Default retention is 7 days; 0 hours requires override'] },
        { label: 'V-Order', values: ['Fabric-optimized write sort for VertiPaq read acceleration', 'Applied automatically on all Fabric Delta writes', 'Standard Parquet compliant; 2x-10x read boost'] }
      ]
    },
    keyRules: [
      'OPTIMIZE compacts small files into larger files (~1 GB) to eliminate the small file problem; it does NOT remove old files.',
      'VACUUM permanently deletes files that are no longer referenced by the Delta transaction log and are older than the retention threshold.',
      'Running VACUUM with retention < 7 days may corrupt concurrent queries or time travel; requires setting vacuum parallel delete or retention check override.',
      'Z-ORDER should only be applied to 1-4 high-cardinality filter columns; applying Z-Order on too many columns dilutes effectiveness.'
    ],
    commonTrap: 'Trap: Believing OPTIMIZE deletes historical files. Reality: OPTIMIZE creates new compacted files; VACUUM is required to remove the old unreferenced ones.',
    msLearnRef: {
      title: 'Delta Lake table optimization in Microsoft Fabric',
      url: 'https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-optimize'
    }
  },
  {
    id: 'capacity-smoothing-throttling',
    title: 'Fabric Capacity Units (CUs), Smoothing & Throttling',
    badge: 'Plan, Implement, and Manage',
    tag: 'plan-capacity-throttling',
    domain: 'domain1',
    summary: 'Microsoft Fabric capacities (F2 through F2048) smooth compute consumption over time to prevent temporary spikes from causing immediate service outages.',
    comparisonTable: {
      headers: ['Operation Type', 'Smoothing Window', 'Throttling Impact', 'Examples'],
      rows: [
        { label: 'Interactive Operations', values: ['Smoothed over 5 to 10 minutes', 'Slows interactive queries if capacity burndown limit is breached', 'Power BI visual renders, DAX queries, SQL endpoint reads'] },
        { label: 'Background Operations', values: ['Smoothed over a 24-hour rolling window', 'Rejects new background jobs if 24h consumption exceeds limit', 'Spark notebooks, Data pipelines, Dataflow Gen2 refreshes'] }
      ]
    },
    keyRules: [
      'Capacity Units (CUs) measure aggregate compute across all Fabric workloads; smoothing averages consumption over rolling time windows.',
      'Interactive operations are smoothed over 5-10 minutes; background batch operations are smoothed over a 24-hour rolling window.',
      'Burndown mechanism allows temporary bursting above capacity limits, repaid during subsequent low-activity periods.',
      'If background throttling occurs, non-essential batch workloads must be staggered or scheduled outside business hours.'
    ],
    commonTrap: 'Trap: Assuming interactive and background jobs smooth over the same duration. Remember: Interactive = minutes; Background = 24 hours.',
    msLearnRef: {
      title: 'Fabric Capacity Throttling and Smoothing',
      url: 'https://learn.microsoft.com/en-us/fabric/enterprise/throttling'
    }
  },
  {
    id: 'shortcuts-vs-pipelines',
    title: 'OneLake Shortcuts vs. Data Pipelines vs. Mirroring',
    badge: 'Prepare and Connect to Data',
    tag: 'prep-onelake-shortcuts',
    domain: 'domain2',
    summary: 'OneLake Shortcuts provide zero-copy virtualization into ADLS Gen2, AWS S3, Google Cloud Storage, or Dataverse without moving or replicating data.',
    comparisonTable: {
      headers: ['Ingestion Pattern', 'Data Movement', 'Storage Cost', 'Best Used For'],
      rows: [
        { label: 'OneLake Shortcut', values: ['Zero data copy (virtual pointer)', 'No extra Fabric storage cost', 'Instant federated access to S3, ADLS Gen2, Dataverse'] },
        { label: 'Data Pipeline (Copy)', values: ['Full physical data transfer', 'Standard OneLake storage cost', 'Heavy ETL/ELT transformations, on-prem gateways'] },
        { label: 'Fabric Mirroring', values: ['Continuous automated replication', 'Includes free mirroring storage limit', 'Real-time sync from Azure SQL DB, Cosmos DB, Snowflake'] }
      ]
    },
    keyRules: [
      'Shortcuts are virtual references pointing to internal OneLake locations or external cloud stores (ADLS Gen2, S3, GCS, Dataverse).',
      'Creating a shortcut does NOT copy or duplicate data; changes in the source are immediately visible to downstream queries.',
      'Shortcuts to Delta tables in ADLS Gen2 or S3 can be queried directly via Spark, SQL Analytics endpoint, and Direct Lake.',
      'Use Shortcuts when data must remain in place for regulatory or cost reasons; use Pipelines when complex transformations are required.'
    ],
    commonTrap: 'Trap: Choosing a Copy Data pipeline when the exam specifies "minimize data movement and eliminate ETL maintenance." Always choose OneLake Shortcuts.',
    msLearnRef: {
      title: 'OneLake shortcuts overview',
      url: 'https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts'
    }
  },
  {
    id: 'workspace-roles-security',
    title: 'Workspace Roles, Granular Permissions & Item Sharing',
    badge: 'Plan, Implement, and Manage',
    tag: 'plan-workspace-roles',
    domain: 'domain1',
    summary: 'Fabric enforces security at multiple layers: Microsoft Entra ID tenant settings, capacity allocation, workspace roles, item permissions, and native T-SQL/DAX security.',
    comparisonTable: {
      headers: ['Role', 'Create/Edit Items', 'Publish/Manage Apps', 'Assign Roles', 'View Only'],
      rows: [
        { label: 'Admin', values: ['Yes', 'Yes', 'Yes', 'Full control including delete workspace'] },
        { label: 'Member', values: ['Yes', 'Yes', 'Can add Members/Contributors (if enabled)', 'Full edit'] },
        { label: 'Contributor', values: ['Yes', 'No', 'No', 'Build & edit content'] },
        { label: 'Viewer', values: ['No', 'No', 'No', 'Read-only access to reports/endpoints'] }
      ]
    },
    keyRules: [
      'Admin and Member can manage workspace access and publish Power BI apps; Contributors can create and edit content but cannot publish apps by default.',
      'Viewer role grants read-only access to reports and items; viewers cannot execute Spark notebooks or modify warehouse tables.',
      'To restrict access to specific warehouse objects (tables/views), use T-SQL GRANT/REVOKE permissions rather than workspace roles.',
      'Item-level sharing allows sharing a single report or lakehouse without granting access to the entire workspace.'
    ],
    commonTrap: 'Exam question: "You need to allow a developer to create and run notebooks but prevent them from modifying workspace permissions or adding users." Correct answer: Contributor role.',
    msLearnRef: {
      title: 'Roles in Microsoft Fabric workspaces',
      url: 'https://learn.microsoft.com/en-us/fabric/get-started/roles-workspaces'
    }
  },
  {
    id: 'star-schema-dax-traps',
    title: 'Star Schema Design, DAX Relationships & RLS',
    badge: 'Model and Explore Data',
    tag: 'model-star-schema-dax',
    domain: 'domain3',
    summary: 'High-performance Fabric semantic models require pure star schemas with 1-to-many single-direction relationships, avoiding bidirectional filters and snowflaking.',
    comparisonTable: {
      headers: ['Concept', 'Recommended Pattern', 'Anti-Pattern', 'Impact on Performance'],
      rows: [
        { label: 'Schema Architecture', values: ['Star Schema (central fact + dimensional tables)', 'Snowflake / Flat single wide table', 'VertiPaq column compression optimized; faster DAX'] },
        { label: 'Relationship Direction', values: ['Single direction (1-to-Many)', 'Bi-directional filtering (Both)', 'Prevents ambiguous filter paths and severe slowdowns'] },
        { label: 'Security Enforcement', values: ['Row-Level Security (RLS) via USERPRINCIPALNAME()', 'Hardcoded visual filters', 'Consistent server-side row security across all reports'] },
        { label: 'Measures vs Columns', values: ['Explicit DAX measures (CALCULATE, SUM)', 'Implicit column sums or calculated columns', 'Re-usable, dynamic context evaluation, smaller file size'] }
      ]
    },
    keyRules: [
      'Always design star schemas where dimension tables filter central fact tables through 1-to-many single-direction relationships.',
      'Avoid bi-directional relationships and many-to-many relationships; resolve many-to-many using intermediate bridge tables.',
      'In Direct Lake mode, implement Row-Level Security (RLS) in the Power BI semantic model to prevent fallback to DirectQuery.',
      'Use USERPRINCIPALNAME() inside dynamic RLS role filters to dynamically match the logged-in user with their authorized security rows.'
    ],
    commonTrap: 'Trap: Enabling bi-directional cross-filtering between dimension and fact tables to solve a measure calculation. Correct approach: Use USERELATIONSHIP() or CROSSFILTER() inside DAX CALCULATE().',
    msLearnRef: {
      title: 'Understand star schema and the importance for Power BI',
      url: 'https://learn.microsoft.com/en-us/power-bi/guidance/star-schema'
    }
  },
  {
    id: 'dp700-table-maintenance',
    title: 'Delta Lake Table Maintenance & Streaming Compaction',
    badge: 'Monitor and Optimize',
    examId: 'dp700',
    domain: 'domain3',
    summary: 'Manage Delta Lake file fragmentation, streaming micro-batches, and query acceleration using V-Order, OPTIMIZE, and auto-compaction table properties.',
    comparisonTable: {
      headers: ['Feature / Property', 'Purpose & Scope', 'Trigger / Execution', 'Impact on Writes & Reads'],
      rows: [
        { label: 'delta.autoOptimize.optimizeWrite', values: ['Writes larger 128 MB files directly during streaming / batch', 'Table property (set to true)', 'Slight write overhead, avoids small file creation'] },
        { label: 'delta.autoOptimize.autoCompact', values: ['Automatically compacts newly written small files into larger files', 'Table property (set to true)', 'Runs immediately after write commit'] },
        { label: 'OPTIMIZE [table]', values: ['Explicit bin-packing command to consolidate files into 1 GB files', 'Manual SQL / PySpark run', 'Drastically speeds up scan performance'] },
        { label: 'V-Order (delta.parquet.vorder.enabled)', values: ['Optimizes Parquet sorting, dictionary encoding, and compression', 'Default on in Fabric Spark & Warehouse', 'VertiPaq query acceleration, faster scan times'] },
        { label: 'VACUUM [table] RETAIN n HOURS', values: ['Removes stale/dead files outside time-travel retention window', 'Manual maintenance', 'Reclaims OneLake storage; does NOT compact files'] }
      ]
    },
    keyRules: [
      'To prevent small-file overhead in Spark structured streaming jobs without changing frequency, set delta.autoOptimize.optimizeWrite and delta.autoOptimize.autoCompact to true.',
      'OPTIMIZE consolidates small files, but does NOT delete old versions; VACUUM deletes unreferenced files older than the retention threshold.',
      'V-Order applies Microsoft VertiPaq-style sorting and encoding to Parquet files, improving Direct Lake and T-SQL read performance.',
      'VACUUM with RETAIN 0 HOURS cannot be run in production without overriding safety checks (spark.databricks.delta.vacuum.parallelDelete.enabled) and breaks time-travel.'
    ],
    commonTrap: 'Exam scenario: "Spark streaming writes files every minute; SQL endpoint query latency is increasing. You must configure persistent table properties to automatically produce larger files." Trap: Run VACUUM after each micro-batch. Correct: Set delta.autoOptimize.optimizeWrite and delta.autoOptimize.autoCompact to true.',
    msLearnRef: {
      title: 'Delta Lake table maintenance in Microsoft Fabric',
      url: 'https://learn.microsoft.com/en-us/fabric/fundamentals/table-maintenance-optimization'
    }
  },
  {
    id: 'dp700-eventstreams-kql',
    title: 'Real-Time Intelligence: Eventstreams, KQL & Windowing',
    badge: 'Ingest and Transform Data',
    examId: 'dp700',
    domain: 'domain2',
    summary: 'Ingest and transform high-throughput streaming events using no-code Eventstreams and query dynamic telemetry in KQL databases.',
    comparisonTable: {
      headers: ['Component / Operator', 'Functionality', 'Supported Pattern', 'Exam Key Detail'],
      rows: [
        { label: 'Fabric Eventstreams', values: ['Ingest from Azure Event Hub, IoT Hub, Kafka, CDC', 'No-code event processing', 'Enhanced capabilities enable no-code transformations'] },
        { label: 'Event Processor', values: ['Filter, group by, expand, and aggregate streaming rows', 'In-stream before destination', 'Routes clean data to Lakehouse, KQL DB, or Activator'] },
        { label: 'KQL extend & project', values: ['Extract dynamic JSON (toint(col.field), tostring())', 'Scalar transformations', 'Project before extend loses dynamic columns!'] },
        { label: 'KQL ago(5m) & between', values: ['Time filtering for telemetry data', 'where TimeGenerated > ago(5m)', 'Fast time-index partition pruning'] },
        { label: 'Named Window() wrapper', values: ['Assigns non-null label: Window("1 min", TumblingWindow(minute, 1))', 'Stream Analytics query', 'System.Window().Id outputs the window name'] }
      ]
    },
    keyRules: [
      'In KQL, when extracting fields from dynamic JSON columns (e.g. AdditionalContext), use extend Level = toint(AdditionalContext.Level) BEFORE project.',
      'To aggregate multiple time windows (e.g. 1m, 15m, 30m, 60m) in a single stream query and identify the window, wrap each window with Window("Label", ...) and select System.Window().Id.',
      'For no-code streaming ingestion and transformation from IoT devices or Event Hubs, choose Microsoft Fabric Eventstreams with enhanced capabilities.',
      'For real-time environmental IoT telemetry requiring near real-time querying in Lakehouses, Spark Structured Streaming writes directly to Delta tables.'
    ],
    commonTrap: 'Exam scenario: "Identify which window produced each row in a multi-window streaming query." Trap: Unnamed Windows(...) with System.Timestamp(). Correct: Name windows with Window("label", TumblingWindow/HoppingWindow) and reference System.Window().Id.',
    msLearnRef: {
      title: 'Overview of Microsoft Fabric Eventstreams',
      url: 'https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview'
    }
  },
  {
    id: 'dp700-data-mesh-governance',
    title: 'Fabric Data Mesh: Domains, Delegated Admin & Workspaces',
    badge: 'Implement and Manage',
    examId: 'dp700',
    domain: 'domain1',
    summary: 'Implement decentralized domain-driven data mesh architectures in Microsoft Fabric by delegating tenant settings, assigning domain admins, and grouping workspaces.',
    comparisonTable: {
      headers: ['Concept', 'Responsibility', 'Configuration Level', 'Best Practice'],
      rows: [
        { label: 'Domains', values: ['Logical grouping of workspaces representing business units', 'Tenant Admin creates domains', 'Align with business domains (Sales, Finance, HR)'] },
        { label: 'Domain Admins', values: ['Manage domain-level configurations, rules, and restrictions', 'Assigned per domain', 'Business unit IT leads manage their own boundaries'] },
        { label: 'Delegated Tenant Settings', values: ['Allows domain admins to override tenant settings for their domain', 'Tenant setting delegation enabled', 'Enables autonomous governance per business unit'] },
        { label: 'Workspace Assignment', values: ['A workspace belongs to exactly ONE domain', 'Workspace settings', 'Workspaces cannot be assigned to multiple domains'] }
      ]
    },
    keyRules: [
      'To enable independent management of rules and restrictions by business units in a data mesh, delegate tenant-level settings to domains.',
      'Three core actions to delegate governance to business units: (1) Assign workspaces to domains, (2) Delegate tenant settings to domains, (3) Specify domain administrators.',
      'A workspace can only be assigned to a single domain; assigning a workspace to multiple domains is not supported.',
      'Domain sensitivity labels classify data but do not grant administrative autonomy to business units.'
    ],
    commonTrap: 'Exam trap: Attempting to assign workspaces to multiple domains or relying solely on row-level security for data mesh governance. Real data mesh requires domain assignment + delegated tenant settings + domain admins.',
    msLearnRef: {
      title: 'Domains in Microsoft Fabric',
      url: 'https://learn.microsoft.com/en-us/fabric/governance/domains'
    }
  },
  {
    id: 'dp700-spark-pools-optimization',
    title: 'Fabric Spark Pools, Autoscaling & Concurrency',
    badge: 'Monitor and Optimize',
    examId: 'dp700',
    domain: 'domain3',
    summary: 'Configure custom Apache Spark pools, dynamic executor allocation, session timeouts, and high concurrency modes for maximum performance.',
    comparisonTable: {
      headers: ['Setting / Feature', 'Functionality', 'Where Configured', 'Key Tradeoff / Advantage'],
      rows: [
        { label: 'Starter Pool', values: ['Pre-warmed Spark instances for fast start (< 10s)', 'Default in Fabric workspace', 'Fixed node size; cannot handle custom peak sizing'] },
        { label: 'Custom Spark Pool', values: ['Define custom node sizes (Small, Medium, Large) and node counts', 'Workspace > Spark Settings', 'Handles heavy compute requirements for large pipelines'] },
        { label: 'Autoscaling (min/max)', values: ['Dynamically scales node count based on submitted stages', 'Spark Pool configuration', 'Set maximum nodes to peak load to avoid resource delays'] },
        { label: 'Dynamic Allocation', values: ['Dynamically adjusts number of executors per job within pool', 'Workspace Spark settings', 'Optimizes memory usage without increasing session start times'] },
        { label: 'High Concurrency Mode', values: ['Shares active Spark sessions across multiple concurrent notebooks/users', 'Data Engineering/Science > Spark Settings', 'Eliminates cold starts, maximizes cluster utilization'] },
        { label: 'Session Timeout', values: ['Prevents "Your session timed out after inactivity" errors', 'Workspace settings', 'Extend workspace session timeout to minimize admin effort'] }
      ]
    },
    keyRules: [
      'When shared starter pools experience delays under heavy workloads, create a custom Spark pool with autoscaling enabled and set max nodes based on peak load.',
      'To handle larger jobs without slow session start times, combine custom pools with autoscaling AND enable dynamic allocation of executors.',
      'To enable notebook session sharing across concurrent users, turn on High Concurrency mode under Workspace Settings > Data Engineering/Science > Spark Settings.',
      'If native execution engine fails or degrades on User-Defined Functions (UDFs), adjust Spark configuration to run the traditional Spark execution engine.'
    ],
    commonTrap: 'Exam trap: Selecting "static allocation of executors" or "fixed number of nodes" to improve execution times. Static allocation leads to resource starvation or idle waste under fluctuating workloads.',
    msLearnRef: {
      title: 'Configure Apache Spark pools in Microsoft Fabric',
      url: 'https://learn.microsoft.com/en-us/fabric/data-engineering/spark-workspace-settings'
    }
  },
  {
    id: 'dp700-deployment-pipelines',
    title: 'Deployment Pipelines & Git ALM Recovery',
    badge: 'Implement and Manage',
    examId: 'dp700',
    domain: 'domain1',
    summary: 'Manage development, testing, and production stage transitions, selective deployments, stage assignment, and Git source control rollback.',
    comparisonTable: {
      headers: ['Action / Mechanism', 'Behavior', 'Required Permission', 'Impact on Target'],
      rows: [
        { label: 'Stage Linking', values: ['Assigning a workspace to Dev, Test, or Prod stage', 'Workspace Admin', 'NO changes occur to artifacts until an explicit deploy action'] },
        { label: 'Selective Deployment', values: ['Promotes ONLY specific selected items (e.g. verified notebooks)', 'Pipeline Admin / Stage User', 'Leaves unselected items unchanged in target stage'] },
        { label: 'Pipeline Admin Role', values: ['Controls who can edit pipeline settings, stages, and rules', 'Pipeline Admin', 'Restricts deployment configuration changes to authorized leads'] },
        { label: 'Git Sync & Revert', values: ['Connect workspace to Git repo; commit and sync changes', 'Git access + Workspace Contributor', 'Use git revert / reset in Git repo, then sync workspace to restore previous version'] }
      ]
    },
    keyRules: [
      'Assigning a workspace to a deployment stage (like Test) links the workspace, but does NOT copy or deploy any items until you trigger a deployment.',
      'To ensure only verified changes reach production from Test, use Selective Deployment rather than full stage deployment.',
      'To restrict who can modify deployment pipeline settings, assign users the Pipeline Admin role.',
      'To restore workspace items after a broken commit, run git revert or git reset in the Azure DevOps/GitHub repository, then sync the Fabric workspace from source control.'
    ],
    commonTrap: 'Exam question: "You assign Workspace2 to the test stage of pipeline1. What will occur?" Trap answer: Artifacts are copied to Workspace2. Correct answer: No changes will occur.',
    msLearnRef: {
      title: 'Get started with Fabric deployment pipelines',
      url: 'https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/get-started-with-deployment-pipelines'
    }
  },
  {
    id: 'dp700-security-rls-cls-ddm',
    title: 'Fabric Data Warehouse Security: RLS, CLS & DDM',
    badge: 'Implement and Manage',
    examId: 'dp700',
    domain: 'domain1',
    summary: 'Implement granular security controls in Fabric Warehouses using predicate-based Row-Level Security, Column-Level Security roles, Dynamic Data Masking, and T-SQL compute grants.',
    comparisonTable: {
      headers: ['Security Model', 'Implementation Mechanism', 'T-SQL Syntax / Function', 'Use Case'],
      rows: [
        { label: 'Row-Level Security (RLS)', values: ['Inline table-valued function + Security Policy with FILTER PREDICATE', 'CREATE SECURITY POLICY ... ADD FILTER PREDICATE fn(dept)', 'Departments only see their own rows based on USER_NAME()'] },
        { label: 'Column-Level Security (CLS)', values: ['Explicit GRANT / DENY SELECT on specific column lists to roles', 'GRANT SELECT ON tbl(Salary) TO HR_Role; DENY SELECT ON tbl(Salary) TO Other_Role;', 'Restrict sensitive columns (Salary, SSN) to authorized personnel'] },
        { label: 'Dynamic Data Masking (DDM)', values: ['Masks data on the fly for nonprivileged users', 'MASKED WITH (FUNCTION = "partial(1, XXXXX, 4)") / email()', 'Mask credit cards and emails while keeping tables queryable'] },
        { label: 'Granular SQL Compute Grants', values: ['Grant SELECT on individual table without workspace access', 'GRANT SELECT ON dbo.FactSales TO [Sales Analysts];', 'Users query only dbo.FactSales without seeing all workspace items'] }
      ]
    },
    keyRules: [
      'RLS requires two components in SQL: (1) A predicate function returning 1 based on USER_NAME(), and (2) A security policy binding the filter predicate to the table.',
      'To restrict access to sensitive columns (Salary, SSN) in a warehouse, create a specific role, grant SELECT on those columns to that role, and deny SELECT on those columns to other roles.',
      'Dynamic Data Masking obscures data for unauthorized users (e.g. email() for email, partial() for credit cards) without changing stored bytes.',
      'In a Fabric warehouse, users with Read permission still require T-SQL compute permissions (e.g. GRANT SELECT ON dbo.FactSales TO [group]) to query tables.'
    ],
    commonTrap: 'Exam trap: Creating a SQL VIEW or relying on workspace Viewer role for security. Views do not prevent direct table access if compute permissions exist, and workspace Viewer grants access to ALL items in the workspace.',
    msLearnRef: {
      title: 'Security for data warehousing in Microsoft Fabric',
      url: 'https://learn.microsoft.com/en-us/fabric/data-warehouse/security'
    }
  }
];


