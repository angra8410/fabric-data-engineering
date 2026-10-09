# Skagit Council of Governments (SCOG) — Growth Monitoring Report
## Technical Engineering & Delivery Summary

**Project:** Skagit Council of Governments — Annual Growth Monitoring Report (Option 1 Base Scope)  
**Deliverable:** 2025 Prototype Baseline & Dimensional Architecture  
**Format:** Power BI Project (`.pbip`) + Relational Star Schema + Master Excel Templates  

---

## 1. Executive Summary & Delivery Status

The data engineering and reporting foundation for the **SCOG Annual Growth Monitoring Report** has been established and verified. The solution transforms historical datasets (1990–2026) into an auditable relational Star Schema with conformed dimensions, accompanied by a 4-page 16:9 widescreen Power BI Project (`.pbip`) optimized for interactive analysis and Board-adopted PDF exports.

---

## 2. Technical Milestones Completed

### Milestone 1: Master Intake Templates & Formula Governance
- Standardized 4 master Excel templates (`.xlsx`) in [`data/templates/`](data/templates/):
  - `Template_Housing_Permits_Master.xlsx`: Annual permits by typology, demolitions, and net units.
  - `Template_Population_Master.xlsx`: WA OFM April 1 official estimates and SAEP UGA allocations.
  - `Template_Employment_Master.xlsx`: WA ESD QCEW covered jobs by NAICS industry sector.
  - `Template_Housing_AMI_Master.xlsx`: Housing production categorized by Area Median Income (AMI) tiers.
- **Lightweight Formula Governance:**
  - Header schema verification using `TEXTJOIN` formulas against canonical schemas.
  - Historical checksum controls using `SUMIFS` to prevent unintended alterations to adopted data.
  - Controlled data validation dropdowns for official Skagit County jurisdictions.

### Milestone 2: Automated ETL Pipeline & Dimensional Star Schema
- Automated ETL pipeline ([`etl_star_schema.py`](etl_star_schema.py)) transforms raw sources into a normalized dimensional model:
  - **Conformed Dimensions:** `Dim_Jurisdiction` (11 entities with WGS84 coordinates), `Dim_CalendarYear` (1990–2045), `Dim_GMA_2045_Target` (Baseline 2022 and 2045 adopted targets), `Dim_CAI_Employment_Benchmark` (1999–2022).
  - **Fact Tables:** `Fact_Population` (97 rows), `Fact_HousingPermits` (314 rows), `Fact_Employment` (131 rows), `Fact_Housing_AMI` (20 rows).
  - **Referential Integrity:** 0 orphaned foreign keys; strict 1-to-many relationship cardinality. Output generated to both clean CSVs and unified workbook `SCOG_Star_Schema_Data_Model.xlsx`.

### Milestone 3: Power BI Project (PBIP) Prototype Delivery
- Implemented complete `.pbip` structure in [`powerbi/SCOG_Growth_Monitoring_Report/`](powerbi/SCOG_Growth_Monitoring_Report/):
  - `SCOG_Growth_Monitoring_Report.pbip`: Root project entry point.
  - `SCOG_Growth_Monitoring_Report.SemanticModel/`: TMSL 1567 tabular model (`model.bim`) with 8 tables, 30+ production DAX measures, and dynamic `SourceWorkbookPath` parameter.
  - `SCOG_Growth_Monitoring_Report.Report/`: 4-page 16:9 widescreen canvas definitions (`report.json`) styled with high-contrast civic theme (`scog_theme.json`).
  - Standalone exports: [`dax_measures.dax`](powerbi/dax_measures.dax) and [`power_query_m_scripts.pq`](powerbi/power_query_m_scripts.pq).

---

## 3. Governance Safeguards & Audit Alignments

Following rigorous quality audit reviews, the prototype incorporates the following safeguards:

1. **Executive Summary Matrix (Page 1):**
   - Strictly covers **Population and Housing progress only**. Employment target progress is excluded at the municipal level because annual QCEW data is suppressed for sub-county jurisdictions due to state confidentiality rules, supporting only county-level aggregates.
2. **Employment Methodology Isolation (Page 3):**
   - Executive cards and charts default strictly to official **WA ESD QCEW covered employment**.
   - The CAI total employment calculation (self-employment multiplier) is quarantined to countywide totals and prominently labeled as **"Pending methodology confirmation with SCOG staff"** per project leadership direction.
3. **AMI Affordability Staging (Page 2):**
   - The Area Median Income distribution visual is explicitly flagged as **"PRELIMINARY: Statewide default allocation"** pending delivery of certified local jurisdiction datasheets due October 20.
4. **Spatial Centroid Attribution (Page 4):**
   - Jurisdiction centroids (`Latitude`, `Longitude`) are derived from official **USGS GNIS** and **US Census Bureau 2020** municipal centers and UGA boundary centroids.
   - "Unincorporated Skagit County" is explicitly defined as the official "Rural (outside of UGAs)" balance under Skagit County Ordinance O20250002.
5. **Strict Schema Protection (Power Query M):**
   - Ingestion queries enforce `Table.SelectColumns(Headers, {...}, MissingField.Error)`. Any renamed, deleted, or missing column halts the refresh with an explicit error rather than silently loading corrupt data.

---

## 4. Next Steps
1. Review prototype artifacts with SCOG planning staff.
2. Ingest certified local jurisdiction AMI datasheets following the October 20 submission deadline.
3. Confirm total employment methodology basis with SCOG before finalizing regional employment targets.
4. Transition 2025 baseline prototype into 2026 production report upon release of full-year 2026 datasets.
