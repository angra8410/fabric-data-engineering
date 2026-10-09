# Architecture Decision Records (ADRs): SCOG Growth Monitoring Report

## [ADR-001] Adoption of Progressive Technical Strategy (Option 1 vs Option 2)
- **Date:** 2026-09-14
- **Status:** Approved
- **Context:** SCOG required technical evaluation between Option 1 (Power BI fueled by structured SharePoint/Excel templates + GIS layers) and Option 2 (Power Apps/Dataverse with automated cloud intake). Ingestion frequency is strictly annual and regional data volume is moderate (~tens of thousands of rows spanning decades).
- **Decision Taken:** Prioritize a robust, low-friction base implementation (Option 1 with standardized SharePoint Excel workbooks and Power Query M ingestion) while structuring the semantic model and data schema so that an automated Dataverse platform (Option 2) can be introduced modularly in future phases if SCOG establishes tenant capacity and administrative consensus.
- **Alternatives Considered:**
  1. Mandate Option 2 (Dataverse) as the sole initial architecture: Rejected due to recurring premium licensing requirements and administrative overhead for a small regional planning team.
  2. Option 1 without standardized intake templates: Rejected due to severe vulnerability to Excel schema drift and broken annual refreshes.
- **Consequences:** Requires designing strict dimensional Star Schemas, fortified Excel templates with formula-based validation, and resilient Power Query M ingestion assertions (`MissingField.Error`).

---

## [ADR-002] Spatial Mapping Visuals: Standardization on GA Native Maps and WGS84 Coordinates
- **Date:** 2026-09-14
- **Status:** Approved
- **Context:** Spatial representation of Skagit County jurisdictions and Urban Growth Areas (UGAs) is required on executive canvases. Power BI Shape Map remains in perpetual preview without General Availability (GA) enterprise SLA, risking rendering failures during automated Power BI Service PDF exports.
- **Decision Taken:** 
  1. Standardize on native GA Power BI Map and Azure Maps visuals using official WGS84 geographic coordinates (`Latitude`, `Longitude`).
  2. Jurisdiction centroids are derived from official USGS Geographic Names Information System (GNIS) and US Census Bureau 2020 municipal centers and UGA geographic centroids.
  3. "Unincorporated Skagit County" is explicitly represented as the official "Rural (outside of UGAs)" balance defined under Skagit County Ordinance O20250002.
- **Consequences:** Guarantees stable rendering in Power BI Desktop, Power BI Service, and board-adopted PDF exports without preview feature dependencies.

---

## [ADR-003] Formula-Based Schema Integrity Validation in Master Excel Templates
- **Date:** 2026-09-15
- **Status:** Approved
- **Context:** The primary vulnerability of spreadsheet-driven reporting is user error: unintentional column renaming, deleted headers, or accidental overwrites of historical rows previously adopted by the SCOG Board. The solution must protect data integrity without requiring VBA/macro-enabled workbooks (`.xlsm`), maintaining full compatibility with Excel Online and SharePoint.
- **Decision Taken:** Implement native Excel formula validation within `.xlsx` templates:
  1. Dynamic header assertion using `TEXTJOIN` compared against the canonical schema string, rendering a clear visual error banner if headers are altered.
  2. Historical checksum controls using `SUMIFS` / `SUM` formulas to detect unintended edits to adopted prior-year rows.
  3. Data validation dropdowns restricting jurisdiction entry to official Skagit entities.
- **Consequences:** Establishes lightweight, auditable data governance directly inside SharePoint Online without macro security warnings.

---

## [ADR-004] Master Excel Intake Templates Design
- **Date:** 2026-10-08
- **Status:** Approved / Implemented
- **Context:** Annual intake across four planning domains requires uniform structure for municipal reporting and state agency feeds.
- **Decision Taken:** Deploy four master intake workbooks in `data/templates/`:
  1. `Template_Housing_Permits_Master.xlsx`: Annual residential permits by structure type, demolitions, and net unit changes.
  2. `Template_Population_Master.xlsx`: OFM April 1 official estimates and SAEP UGA allocations vs GMA 2045 targets.
  3. `Template_Employment_Master.xlsx`: Annual covered employment and establishments by 2-digit and 3-digit NAICS sectors.
  4. `Template_Housing_AMI_Master.xlsx`: Housing production categorized by Area Median Income (AMI) tiers.
- **Consequences:** Eliminates ad-hoc data formatting and provides documented SOPs for regional staff.

---

## [ADR-005] Relational Star Schema Architecture and Deterministic ETL Pipeline
- **Date:** 2026-10-08
- **Status:** Approved / Implemented
- **Context:** Raw multi-year datasets (1990–2026) must be transformed into a high-performance dimensional model suitable for Power BI Desktop and Power BI Service.
- **Decision Taken:** Implement an automated, deterministic Python ETL pipeline generating conformed dimensions and typed fact tables:
  1. **Conformed Dimensions:** `Dim_Jurisdiction` (11 entities with WGS84 coordinates), `Dim_CalendarYear` (56 years, 1990–2045), `Dim_GMA_2045_Target` (Baseline 2022 and 2045 targets).
  2. **Fact Tables:** `Fact_Population` (97 observations), `Fact_HousingPermits` (314 observations), `Fact_Employment` (131 observations), `Fact_Housing_AMI` (20 observations).
  3. **Integrity Assertions:** 0 orphaned foreign keys; strict 1-to-many relationship cardinality. Output generated to both clean CSVs and unified `SCOG_Star_Schema_Data_Model.xlsx`.
- **Consequences:** Decouples reporting presentation from raw file structures and enables one-click annual data refresh.

---

## [ADR-006] Employment Domain Methodology: QCEW Covered Employment vs CAI Total Employment Benchmark
- **Date:** 2026-10-09
- **Status:** Approved (With Methodology Caveats)
- **Context:** SCOG provided a draft calculation template from Community Attributes Inc. (CAI) that estimates total employment (including sole proprietors and non-employers) by applying a 1.15458 multiplier to QCEW covered employment. Direction from project leadership instructed not to present or finalize total employment figures on municipal progress comparisons until the methodology basis is officially confirmed with SCOG.
- **Decision Taken:**
  1. **Official State Series:** All primary executive cards and visual charts default strictly to Washington State Employment Security Department (ESD) QCEW covered employment.
  2. **Quarantine of Total Multiplier:** The CAI total employment calculation is isolated strictly to the countywide aggregate level and tagged with prominent disclaimer text ("Pending methodology confirmation with SCOG").
  3. **Exclusion from Municipal Matrix:** The Page 1 11-jurisdiction GMA 2045 progress matrix strictly displays Population and Housing progress only. Employment target progress is omitted by jurisdiction because sub-county annual employment data is suppressed by state confidentiality rules.
- **Consequences:** Adheres strictly to management guidance, prevents premature publication of unratified metrics, and maintains statistical defensibility.

---

## [ADR-007] Power BI Project (PBIP) Architecture and TMSL 1567 Semantic Model
- **Date:** 2026-10-09
- **Status:** Approved / Implemented
- **Context:** To ensure long-term auditability, team collaboration, and CI/CD integration, the reporting artifact must be version-controllable in Git rather than stored as an opaque binary `.pbix` file.
- **Decision Taken:** Deliver the 2025 prototype using the Microsoft Power BI Project (`.pbip`) format:
  1. `SCOG_Growth_Monitoring_Report.pbip`: Project entry point.
  2. `SCOG_Growth_Monitoring_Report.SemanticModel/`: TMSL 1567 tabular model (`model.bim`) with 8 tables, 30+ production DAX measures, typed schema partitions, and dynamic `SourceWorkbookPath` parameter.
  3. `SCOG_Growth_Monitoring_Report.Report/`: 4-page 16:9 widescreen canvas (1280 × 720 px) in `report.json` with high-contrast civic theme (`scog_theme.json`).
- **Consequences:** Enables granular Git tracking of visual changes, DAX measures, and data model modifications without binary merge conflicts.

---

## [ADR-008] Governance Safeguards: Strict Power Query Schema Assertions and AMI Preliminary Labeling
- **Date:** 2026-10-09
- **Status:** Approved / Implemented
- **Context:** Auditor review required verification that schema assertions fail safely against unexpected changes and that unverified preliminary data is properly tagged.
- **Decision Taken:**
  1. **Strict Power Query Assertions:** Power Query M queries enforce `Table.SelectColumns(Headers, {...}, MissingField.Error)`. If any required column is renamed or absent, the refresh halts immediately with an explicit error rather than silently loading corrupt data.
  2. **AMI Data Staging:** The Area Median Income (AMI) visual on Page 2 is prominently labeled as preliminary ("PRELIMINARY: Statewide default allocation — certified local jurisdiction datasheets due October 20").
  3. **GIS Centroid Footnote:** Page 4 explicitly documents the USGS GNIS / US Census Bureau 2020 coordinate sources and defines the "Unincorporated Skagit County" rural balance outside UGAs.
- **Consequences:** Ensures full compliance with audit guidelines and prevents misleading representation of unratified regional datasets.
