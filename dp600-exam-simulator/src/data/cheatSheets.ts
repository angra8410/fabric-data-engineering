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
  }
];

