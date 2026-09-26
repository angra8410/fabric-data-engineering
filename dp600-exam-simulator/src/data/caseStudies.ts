import { CaseStudy } from '../types';

export const CASE_STUDIES: CaseStudy[] = [
  {
    id: 'cs-fabric-enterprise',
    title: 'Case Study: Contoso Enterprise Modernization',
    overview: 'Contoso is transitioning its legacy enterprise reporting solution from Azure Synapse Analytics and SQL Server Analysis Services (SSAS) to Microsoft Fabric on an F64 capacity.',
    currentEnvironment: [
      'Raw telemetry files arrive every 5 minutes in an external ADLS Gen2 storage account in JSON format.',
      'Sales and ERP financial data reside in an on-premises SQL Server database updated daily at midnight.',
      'Existing SSAS Tabular models contain over 40 calculated columns and use dynamic Row-Level Security (RLS) based on Windows usernames.',
      'Business analysts currently query historical data spanning 5 years (approx. 8 TB) using Power BI Desktop in Import mode with 8-hour refresh times.'
    ],
    businessRequirements: [
      'Provide near real-time dashboards for executive sales telemetry without exceeding Fabric capacity smoothing limits.',
      'Avoid data duplication between the external ADLS Gen2 data lake and Fabric.',
      'Maintain sub-second query latency on Power BI reports for the 8 TB sales dataset.',
      'Ensure strict data governance and row-level security without duplicating semantic models across business units.'
    ],
    technicalConstraints: [
      'Fabric capacity is strictly capped at F64; compute operations that cause burst throttling must be rescheduled or refactored.',
      'All semantic models for executive reporting must utilize Direct Lake mode whenever possible.',
      'Deployment of Fabric workspace items (Lakehouses, Warehouses, Semantic Models) must be automated via Azure DevOps Git integration.'
    ],
    identifiedIssues: [
      'Recent testing showed that when opening the new executive report, Power BI queries silently fell back from Direct Lake to DirectQuery mode.',
      'The on-premises SQL Server daily ingestion pipeline is taking 3 hours and locking production tables.',
      'Spark notebooks running on the bronze Lakehouse are creating thousands of tiny 50 KB Parquet files.'
    ]
  }
];
