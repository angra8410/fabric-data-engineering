import re

with open('src/components/SevenDayPlan.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# DP-700 days definition
dp700_days_code = '''  const dp700Days: DayPlan[] = [
    {
      day: 1,
      tag: 'Security & Governance',
      domain: 'domain1',
      title: 'Domain 1: Security, RLS, CLS, DDM & Data Mesh',
      description: 'Master Row-Level Security predicates, Column-Level Security roles, Dynamic Data Masking, T-SQL compute permissions, and Data Mesh domain settings.',
      topics: ['Row-Level Security (RLS)', 'Column-Level Security (CLS)', 'Dynamic Data Masking (DDM)', 'Granular T-SQL Grants', 'Domain Tenant Delegation'],
      icon: <ShieldCheck className="w-5 h-5 text-amber-400" />
    },
    {
      day: 2,
      tag: 'CI/CD & Git ALM',
      domain: 'domain1',
      title: 'Domain 1: Git Integration, Rollback & Deployment Pipelines',
      description: 'Master Azure DevOps Git syncing, git revert/reset recovery, selective stage deployments, stage workspace linking, and pipeline admin roles.',
      topics: ['Git Integration & Version Control', 'Git Revert & Sync Recovery', 'Selective Deployment Promotion', 'Stage Linking Behaviors', 'Pipeline Admin Security'],
      icon: <Layers className="w-5 h-5 text-sky-400" />
    },
    {
      day: 3,
      tag: 'Pipelines & Orchestration',
      domain: 'domain1',
      title: 'Domain 1: Data Factory Orchestration, Parameters & Triggers',
      description: 'Master pipeline parameters, string interpolation, runtime dynamic expressions, notebook baseParameters, ForEach arrays, and schedule triggers.',
      topics: ['Pipeline Parameters & Dynamic Expressions', 'Notebook baseParameters Passing', 'ForEach Array Types & @json()', 'Schedule Triggers', 'Fail Activity Termination'],
      icon: <Code2 className="w-5 h-5 text-purple-400" />
    },
    {
      day: 4,
      tag: 'OneLake & Batch Loading',
      domain: 'domain2',
      title: 'Domain 2: Shortcuts, Mirrored DBs, COPY & CTAS',
      description: 'Master OneLake shortcuts without data duplication, near real-time Database Mirroring, high-throughput COPY with SAS, cross-database CTAS, and SCD Type 2.',
      topics: ['OneLake Shortcuts (Zero-Copy)', 'Mirrored Databases (Azure SQL)', 'T-SQL COPY with SAS Token', 'CTAS Cross-Database Tables', 'SCD Type 2 Dimension Tables'],
      icon: <Database className="w-5 h-5 text-emerald-400" />
    },
    {
      day: 5,
      tag: 'Eventstreams & KQL',
      domain: 'domain2',
      title: 'Domain 2: Real-Time Intelligence, Eventstreams & KQL',
      description: 'Master Eventstreams with Azure Event Hub, no-code Event Processors, KQL database queries on dynamic JSON, and Stream Analytics windowing functions.',
      topics: ['Eventstreams & Event Processor', 'KQL Dynamic JSON & extend/project', 'Stream Windowing (Tumbling & Hopping)', 'Spark Streaming to Delta', 'Diverse Storage Architecture'],
      icon: <Zap className="w-5 h-5 text-amber-400" />
    },
    {
      day: 6,
      tag: 'Monitoring & Optimization',
      domain: 'domain3',
      title: 'Domain 3: Monitor Hub, Activator & Delta Maintenance',
      description: 'Master Monitor hub activity filtering, Fabric Activator automated alerts, Delta table V-Order, OPTIMIZE, autoCompact/optimizeWrite, and custom Spark pool autoscaling.',
      topics: ['Monitor Hub Filtering & Alerts', 'Fabric Activator Event Thresholds', 'Delta Auto-Compaction & Optimize Write', 'Custom Spark Pools & Autoscaling', 'Spark Session Timeout & Concurrency'],
      icon: <Cpu className="w-5 h-5 text-rose-400" />
    },
    {
      day: 7,
      tag: 'Full DP-700 Mock Exam',
      domain: 'domain1',
      title: 'Comprehensive DP-700 Mock Exam (100 mins)',
      description: 'Full 50-question timed exam under Pearson VUE conditions covering all official Microsoft Data Engineering objectives.',
      topics: ['50 Timed Questions', '100 Minutes', 'Passing Score: 700 / 1000', 'Full Explanations & Study Drill'],
      icon: <Award className="w-5 h-5 text-amber-400" />,
      isExamDay: true
    }
  ];

  const dp600Days: DayPlan[] = [
    {
      day: 1,
      tag: 'Workspaces & CU Admin',
      domain: 'domain1',
      title: 'Domain 1: Plan, implement, and manage an analytics solution',
      description: 'Master Fabric capacities, smoothing, throttling, workspace roles, Git integration, and deployment pipelines.',
      topics: ['Capacity & Workspace Admin', 'Deployment Pipelines & Git', 'OneLake Security & Governance', 'Monitoring & Tenant Settings'],
      icon: <ShieldCheck className="w-5 h-5 text-teal-400" />
    },
    {
      day: 2,
      tag: 'OneLake Shortcuts',
      domain: 'domain2',
      topicKeyword: 'shortcut',
      title: 'Domain 2: OneLake Architecture & Shortcuts',
      description: 'Internal vs external shortcuts, ADLS Gen2, Amazon S3, OneLake security and folder paths.',
      topics: ['Internal Shortcuts', 'ADLS Gen2 Shortcuts', 'Amazon S3 Shortcuts', 'Tables vs Files Structure'],
      icon: <Layers className="w-5 h-5 text-sky-400" />
    },
    {
      day: 3,
      tag: 'Delta Lake & V-Order',
      domain: 'domain2',
      topicKeyword: 'delta',
      title: 'Domain 2: Delta Lake Optimization & Engine',
      description: 'Delta Parquet storage, V-Order encoding for VertiPaq, OPTIMIZE ZORDER BY, and VACUUM retention periods.',
      topics: ['V-Order Encoding', 'OPTIMIZE ZORDER BY', 'VACUUM Retention', 'Delta Log & Parquet'],
      icon: <Database className="w-5 h-5 text-emerald-400" />
    },
    {
      day: 4,
      tag: 'PySpark & Dataflows',
      domain: 'domain2',
      title: 'Domain 2: Lakehouse vs Warehouse & Data Transformation',
      description: 'When to choose Lakehouse vs Warehouse, cross-database T-SQL, PySpark DataFrames, and Dataflows Gen2.',
      topics: ['Lakehouse vs Warehouse', 'PySpark Transformations', 'T-SQL Joins & CTAS', 'Dataflows Gen2'],
      icon: <Code2 className="w-5 h-5 text-amber-400" />
    },
    {
      day: 5,
      tag: 'Direct Lake Modeling',
      domain: 'domain3',
      topicKeyword: 'direct lake',
      title: 'Domain 3: Direct Lake Semantic Models & Fallback',
      description: 'Direct Lake performance, Delta Parquet requirements, fallback conditions to DirectQuery, and memory framing.',
      topics: ['Direct Lake Requirements', 'VertiPaq Memory Limits', 'Fallback to DirectQuery', 'Framing & Auto-Sync'],
      icon: <Cpu className="w-5 h-5 text-purple-400" />
    },
    {
      day: 6,
      tag: 'DAX & Calc Groups',
      domain: 'domain3',
      title: 'Domain 3: DAX Calculations & Semantic Modeling',
      description: 'Star schema design, Calculation Groups with SELECTEDMEASURE(), Field Parameters, and DAX Studio tuning.',
      topics: ['Star Schema Fact & Dim', 'Calculation Groups', 'Field Parameters', 'DAX Studio Profiling'],
      icon: <BarChart3 className="w-5 h-5 text-rose-400" />
    },
    {
      day: 7,
      tag: 'Full 100m Mock Exam',
      domain: 'domain1',
      title: 'Comprehensive DP-600 Mock Exam (100 mins)',
      description: 'Full 40-question timed exam under Pearson VUE conditions with case studies, multi-select, and drag-and-drop sequencing.',
      topics: ['40 Timed Questions', '100 Minutes', 'Case Study Analysis', 'Official Pass Mark: 700 / 1000'],
      icon: <Award className="w-5 h-5 text-amber-400" />,
      isExamDay: true
    }
  ];

  const days = activeExam === 'dp700' ? dp700Days : dp600Days;'''

# Replace the single const days array
pattern = r'  const days: DayPlan\[\] = \[.*?  \];'
text = re.sub(pattern, dp700_days_code, text, flags=re.DOTALL)

# Replace titles referencing DP-600 in SevenDayPlan UI
text = text.replace('DP-600 Exam (100 mins)', '{activeExam === "dp700" ? "DP-700" : "DP-600"} Exam (100 mins)')
text = text.replace('Pass the DP-600', 'Pass the {activeExam === "dp700" ? "DP-700" : "DP-600"}')
text = text.replace('Master the DP-600', 'Master the {activeExam === "dp700" ? "DP-700" : "DP-600"}')

with open('src/components/SevenDayPlan.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated SevenDayPlan.tsx with DP-700 and DP-600 tailored schedules!')
