# Technical Options Scoping Document: Annual Growth Monitoring Report

**Client:** Skagit Council of Governments (SCOG)  
**Author:** Antonio / Skagit Consulting  
**Date:** September 16, 2026 (Revision 3)  
**Target Delivery:** Wednesday Delivery Review  
**Revision 3 Note:** This version presents Option 1 as the base contracted approach, estimated across six task areas — Discovery/Planning, the 2025 prototype, the 2026 Power BI Growth Monitoring Report, documentation, staff training, and contingency — for a 55–97 hour range (75-hour baseline). The 2025 prototype is treated as work in progress; see the assumption note in Section 2.5, which should be confirmed once the prototype's actual state is assessed under Task 1.

---

## 1. Executive Summary

The Skagit Council of Governments (SCOG) compiles and publishes an annual **Growth Monitoring Report** to track regional land use, population, housing, and employment trends under Washington State's Growth Management Act (GMA). Historically, SCOG staff has manually gathered disparate spreadsheets from municipal and county jurisdictions, cleaned and merged them in Microsoft Excel, and manually produced charts and tables for inclusion in board-adopted reports.

This project evaluates the transition of SCOG's annual growth monitoring reporting into **Microsoft Power BI**. The primary objective is to deliver an interactive, maintainable, and visually compelling reporting system that streamlines annual updates while preserving the official, archivable format required for Board adoption.

This scoping document provides an objective, side-by-side technical evaluation of two delivery pathways:
* **Option 1 — Base Scope (Power BI from SCOG-Prepared Excel/GIS Files):** Implementation is scoped bottom-up across six task areas — discovery, a 2025 prototype (in progress) built on prior-year data, the 2026 production report, documentation, staff training, and contingency — for a **55–97 hour range (75-hour baseline)**. SCOG staff retains responsibility for cleaning and structuring annual Excel and GIS files, while Skagit Consulting constructs a clean, standardized Power BI data model, core interactive dashboards, and a streamlined annual refresh procedure.
* **Option 2 — Expanded Scope (Dataverse-Backed Reporting Architecture with Annual Ingestion Pipeline):** An expanded data-platform architecture (estimated at **110–150 hours**) that establishes Microsoft Dataverse as a structured reporting data layer, introducing automated file intake (via SharePoint and Power Query / Power Automate Dataflows), validation, historical auditing, and approval workflows.

---

## 2. Option 1 — Power BI Report Built from SCOG-Prepared Excel/GIS Files

### 2.1 Recommended Architecture
Under Option 1, data ingestion relies on standardized Excel workbooks curated by SCOG and hosted in a governed SharePoint Online / OneDrive document library.

```
[SCOG Standardized Excel Workbooks] + [GIS Reference GeoJSON/TopoJSON]
                              │
                              ▼ (Direct SharePoint Folder Connector)
            [Power Query (M) - Deterministic Types & Cleansing]
                              │
                              ▼
            [Power BI Star Schema Semantic Model]
           ┌──────────────────┴──────────────────┐
           ▼                                     ▼
 [Shared Dimensions]                      [Fact Tables]
 - Dim_Jurisdiction                       - Fact_HousingPermits
 - Dim_CalendarYear                       - Fact_PopulationEstimates
 - Dim_UGA_Reference                      - Fact_EmploymentBySector
```

* **Data Model Approach:** A classic, lightweight **Star Schema** — fact tables for annual numerical observations (`Fact_Housing_Units`, `Fact_Population_OFM`, `Fact_Employment_ESD`) against conformed dimensions (`Dim_Jurisdiction`, `Dim_Year`, `Dim_GrowthTarget`). A star schema is recommended over a single flat table because it supports cross-filtering across disparate sources (OFM population vs. local permit data) without many-to-many cardinality issues.
* **Prototype Build Integration:** Because Option 1 now includes building out a 2025 prototype as its own task rather than treating the model as a quick pass over already-complete work, the architecture and star schema design happen as part of that prototype build — not as a separate up-front step.

### 2.2 Power BI Report Structure
The report is structured into four cohesive pages, built out first against 2025 prior-year data in the prototype and then extended to 2026 data in the production report:
1. **Executive Summary & Regional Dashboard:** County-level KPIs (population, net new housing units, covered employment, YoY growth, progress toward 20-year GMA allocations).
2. **Housing Deep-Dive:** Permits by type and jurisdiction, cumulative growth vs. Countywide Planning Policy targets, County vs. Urban Growth Area distribution.
3. **Population & Employment Overview:** OFM population estimates and ESD covered employment trends, presented as lighter supporting views.
4. **Jurisdictional Comparison & Spatial Mapping:** Standardized on **Azure Maps** or **ArcGIS Maps for Power BI** (GA-grade, board-suitable) rather than the preview-only Shape Map visual.
5. **Board-Adopted Print / Export Considerations:** Canvases locked to standard **16:9 widescreen**, high-contrast styling, and a dynamic metadata footer for the formal PDF package.

### 2.3 Annual Update Process
* **Staff Pre-Refresh Steps:** SCOG staff collects annual data from OFM, ESD, and municipal permit offices, and enters it into pre-formatted Excel master tables in SharePoint. Formula-based schema and baseline-reconciliation checks (header string comparison, historical `SUMIFS` control totals, in-cell dropdown constraints) flag broken templates before a refresh is attempted — delivered as standard `.xlsx` with no macros required.
* **Refresh and Validation in Power BI:** Power Query ingests the verified SharePoint files with native type enforcement; a dedicated Data Audit/QA visual checks row counts and totals against raw inputs before publishing to the SCOG workspace and exporting the Board PDF.

### 2.4 Pros and Cons

| Pros (Advantages) | Cons (Limitations & Risks) |
| :--- | :--- |
| **No Added Software Licensing:** Beyond standard M365 and Power BI Pro. | **Fragility to Column/Header Changes:** Mitigated but not eliminated by formula-based checks. |
| **Low Learning Curve:** For staff already comfortable in Excel. | **Manual Staff Burden:** Annual data preparation remains a manual staff task. |
| **Simple Governance:** No Power Platform environment to administer. | **Weak Audit Trail:** Limited native auditing of prior spreadsheet alterations. |
| **Direct Implementation:** Focuses directly on report deliverables. | **Limited Concurrency:** Multi-staff editing risks sync conflicts and formula overwrites. |

### 2.5 Estimated Implementation Hours (55–97 Hour Range, 75-Hour Baseline)

Hours are estimated bottom-up across six task areas rather than back-solved to a fixed total. The 2025 prototype is treated as work in progress — partially built, not started from scratch — which is why its allocation sits below what a full from-zero build would require. The exact reduction is an assumption pending a firsthand assessment of what already exists; Task 1 (Discovery) includes confirming that state before the prototype work is finalized.

| Task Breakdown | Low (hrs) | Baseline (hrs) | High (hrs) | Description |
| :--- | :---: | :---: | :---: | :--- |
| **1. Discovery & Planning** | 6 | **8** | 10 | Review existing prototype state, source files, GIS reference data; confirm schema and template approach. |
| **2. 2025 Prototype (prior-year data, in progress)** | 12 | **16** | 22 | Complete the in-progress prototype: star schema, DAX measures, and first working report pages against 2025 data. Hours reflect partial completion — confirm actual state before finalizing. |
| **3. 2026 Production Report** | 18 | **24** | 30 | Apply current-year (2026) data and any updated methodology to the model built in the prototype; refine visuals to board/print quality. |
| **4. Power BI Documentation** | 6 | **8** | 10 | Technical documentation plus an annual refresh runbook. |
| **5. Staff Training / Walkthrough** | 5 | **7** | 9 | Live walkthrough session plus a follow-up session. |
| **6. Contingency** | 8 | **12** | 16 | Buffer for source-data cleanup, schema drift, or mapping/GIS rework beyond the assumptions below. |
| **Total Option 1 Hours** | **55** | **75** | **97** | **75-hour baseline; low end depends on the prototype being closer to complete than assumed, high end on source-data or mapping complexity.** |

> [!IMPORTANT]
> **Key Assumptions for Option 1:**
> 1. The 2025 prototype exists in some working form (data connections and/or partial model) but is not yet validated or extended to a full report — to be confirmed during Discovery.
> 2. The 2025 prototype and 2026 production report share one data model and report structure. If SCOG wants them kept as fully separate artifacts, add roughly 10–15 hours.
> 3. SCOG delivers Excel data in flat, tabular (`ListObject`) format with uniform headers across reporting years.
> 4. GIS boundaries are provided in a directly usable format (GeoJSON, Shapefile, or TopoJSON) without custom reprojection.
> 5. Scope excludes custom ETL data scrubbing, paginated report (.rdl) development, or historical data forensic reconciliation.

> [!TIP]
> **Recommendation for the Client Conversation:** Present the 75-hour baseline as the working estimate, with 55 hours as a best case that depends on the prototype being further along than currently assumed and on clean source files. Reducing the estimate would require reducing scope, such as fewer report pages, lighter documentation, or reduced mapping/export work.

---

## 3. Option 2 — Expanded Scope: Dataverse-Backed Reporting Architecture with Annual Ingestion Pipeline

### 3.1 Recommended Architecture
Option 2 introduces a structured Dataverse-backed reporting data layer for SCOG's annual growth monitoring. Data is decoupled from end-user spreadsheets and centralized in **Microsoft Dataverse**, with core tables for jurisdictions, reporting periods, housing/population/employment metrics, import logs and errors, and a geography/GIS reference table. Power BI connects via the native Dataverse connector (TDS endpoint), supporting both Import and DirectQuery modes.

```
                       [Disparate Agency Raw Files]
                     (OFM, ESD, Municipal Excel/CSVs)
                                    │
                                    ▼ (Drop Zone)
                [SharePoint "Annual Intake" Document Library]
                                    │
                                    ▼ (Trigger / Scheduled)
      [Power Query Dataflows / Power Automate Ingestion Engine]
         ├── Schema Validation (Header & Data Type Checks)
         ├── Business Rule Validation (Non-Negative Permits, Valid Jurisdiction IDs)
         └── Exception Routing (Validation Errors Logged)
                                    │
                                    ▼ (Upsert / Merge)
                      [Microsoft Dataverse Tables]
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
[Core Dimension Tables]     [Fact / Metric Tables]          [System / Audit Tables]
- Jurisdictions             - Housing Metrics               - Import Logs
- Reporting Years           - Population Metrics            - Import Errors / Exceptions
- Geography / UGA Reference - Employment Metrics            - Report Approval Status
                                    │
                                    ▼ (DirectQuery / Native TDS Connector / Import)
                      [Power BI Semantic Model]
                                    │
                                    ▼
                [Interactive Board Report & Historical Trends]
```

#### Core Dataverse Table Entities:
1. `scog_jurisdiction`: Unique municipal entities, county unincorporated zones, GMA designation, baseline planning targets.
2. `scog_reporting_period`: Reporting years, calendar metadata, adoption cycle state (`Draft`, `Under Review`, `Board Adopted`).
3. `scog_housing_metric`: Permitted units, housing type (Single-Family, Multi-Family, ADUs), demolition counts, net unit gains.
4. `scog_population_metric`: Official OFM April 1 estimates, annual growth rate, cumulative decadal growth.
5. `scog_employment_metric`: ESD covered employment counts by NAICS sector classification.
6. `scog_import_log` & `scog_import_error`: Tracks timestamp, uploaded file name, processing user, row counts, and specific cell-level validation rejections.
7. `scog_geography_reference`: Boundary definitions, GIS centroids, and boundary change metadata.

### 3.2 Annual File Intake and Ingestion Process
SCOG staff drops raw annual spreadsheets into a year-structured SharePoint intake folder (`/Intake/2026/`). Power Query Dataflows combined with a lightweight Power Automate flow handle column-mapping, transformation, and loading into Dataverse. The pipeline validates jurisdiction names against master IDs, checks numeric thresholds, and routes failed rows to an import-error table with automated staff notification. Imported data defaults to `Draft` status until an administrator promotes it to `Board Adopted`.

### 3.3 Data Governance and Maintainability
* **Reduces the need for annual model changes:** Adding a new year typically requires no changes to measures, relationships, or visuals, though changes to source format, methodology, or reporting requirements could still require updates.
* **Historical preservation:** Row-level security / table permissions freeze historical records once a year is marked `Board Adopted`.
* **Improved source-file lineage:** Imported records link directly back to their originating import log entry, ensuring defensible audit trails for GMA compliance.

### 3.4 Power BI Reporting Impact
Supports scheduled/cloud refresh and reduces desktop-file dependency; supports rolling averages, CAGR measures, and target-vs-actual variance analysis; lays groundwork for future SCOG initiatives (transportation models, buildable lands inventories, public data portals).

### 3.5 Licensing, Hosting, and Added Costs
As part of Option 2, Skagit Consulting can help SCOG identify and validate licensing, tenant, and capacity implications with SCOG's Microsoft 365 administrator. The figures below are approximate list-price references only:
* **Dataverse storage:** SCOG's dataset is expected to fit within standard pooled tenant capacity at **$0 incremental cost** — confirm with SCOG's M365 administrator.
* **Power Apps Premium:** List price ~$20/user/month required only for the 1–2 staff administering the ingestion pipeline; report-only consumers do not need it.
* **Power BI Pro:** List price ~$14/user/month required for report authors/internal consumers unless SCOG holds M365 E5 or Fabric capacity; confirm government/GCC pricing separately.

### 3.6 Pros and Cons

| Pros (Advantages) | Cons (Limitations & Risks) |
| :--- | :--- |
| **Eliminates Manual Formatting:** Eliminates most manual annual formatting and spreadsheet stitching. | **Implementation Hours:** Implementation hours (110–150 hrs) exceed Option 1 (55–97 hrs). |
| **Enterprise Governance:** Role-based governance, historical freezing, and automated audit logs. | **Potential Added Licensing:** Potential added licensing cost for Power Apps / Dataverse capacity. |
| **Resilient Architecture:** Reduces refresh risk from renamed columns through deterministic schema validation. | **Higher Skill Floor:** Higher skill floor for long-term administration and pipeline troubleshooting. |
| **Extensible Platform:** Scalable to multi-agency inputs and future regional planning tools. | **Architectural Overhead:** Overhead that may be more than a small annual dataset strictly needs. |

### 3.7 Estimated Implementation Hours (Expanded Scope: 110–150 Hours)

This range is deliberately wider than Option 1's, reflecting the larger scope: Option 2 adds Dataverse environment setup, an automated intake/ETL pipeline, and validation/error-handling work that Option 1 does not require.

| Task Breakdown | MVP (hrs) | Complete (hrs) | Description |
| :--- | :---: | :---: | :--- |
| **1. Discovery & Source File Schema Audit** | 10 | 16 | Audit of municipal/state data schemas, mapping rules, cross-agency taxonomy. |
| **2. Dataverse Environment & Entity Modeling** | 16 | 20 | Provisioning Dataverse solution, custom tables, option sets, relationships, keys, security roles. |
| **3. Annual Intake & SharePoint Ingestion Architecture** | 18 | 22 | SharePoint library architecture, folder structure, intake triggers, metadata capture. |
| **4. Dataflows / Power Automate ETL Implementation** | 22 | 28 | Power Query dataflows, schema standardization, automated upsert logic into Dataverse. |
| **5. Data Validation & Error Handling Pipelines** | 12 | 18 | Pre-load validation rules, error logging tables, automated staff alert notifications. |
| **6. Power BI Semantic Model & Report Development** | 18 | 22 | Direct Dataverse connection, multi-year DAX measures, comprehensive 5-page report and mapping. |
| **7. User Acceptance Testing & Historical Migration** | 8 | 14 | Migrating 10–15 years of historical Excel records, reconciliation, edge-case testing. |
| **8. Governance, Documentation & Admin Training** | 6 | 10 | Technical architecture document, administrator runbook, staff training sessions. |
| **Total Option 2 Hours** | **110 hrs** | **150 hrs** | **Proposal baseline: 110–150 hours.** |

---

## 4. Side-by-Side Comparison Matrix

| Category | Option 1: Power BI from Excel/GIS | Option 2: Dataverse + Automated Intake |
| :--- | :--- | :--- |
| **Initial implementation complexity** | **Moderate:** bottom-up build across six task areas, including a prototype build-out. | **High:** multi-component Power Platform architecture. |
| **Annual maintenance effort** | **Moderate/high** (indicative 20–40 hrs/year of staff coordination and cleanup) — to be calibrated after Year 1. | **Low** (indicative 2–4 hrs/year) — automated intake with exception review only. |
| **Staff skill required** | Intermediate Excel + basic Power BI desktop literacy. | Basic SharePoint drop skills for annual use; Power Platform admin skills for maintenance. |
| **Repeatability & reliability** | **Fragile** — vulnerable to human error and altered headers, mitigated by formula-based checks. | **Resilient** — deterministic schema enforcement, validation gates, rejection logging. |
| **Data quality controls** | Manual spot-checking and visual inspection. | Automated validation rules, error logs, Draft/Adopted approval gate. |
| **Licensing / cost impact** | **$0 added cost** within current M365 / Power BI Pro licensing. | **Potential added cost** — Dataverse capacity and possibly Power Apps/Automate licensing; to be validated with SCOG's M365 admin as part of Option 2 planning. |
| **Long-term scalability** | Limited to annual growth monitoring reporting. | Extensible to transportation, buildable lands, and regional data hub initiatives. |
| **Estimated implementation hours** | **55–97 hours (75-hour baseline)** | **110–150 hours** |
| **Main risks** | Refresh breaks in later years; data inconsistencies; ongoing manual staff labor; prototype scope larger than currently assumed. | Budget/approval risk; licensing surprises; over-engineering a small annual dataset. |
| **Best fit if…** | SCOG needs a working Power BI transition without new Power Platform licensing or admin overhead. | SCOG wants a long-term data modernization initiative and is ready to take on the added cost and governance. |

---

## 5. Summary of Estimated Hours by Option

```
Option 1: Base Scope (Power BI + Excel) — six task areas, 55–97 hour range, 75-hour baseline:
├── Discovery & Planning:              6 /  8 / 10 hrs
├── 2025 Prototype (in progress):     12 / 16 / 22 hrs
├── 2026 Production Report:           18 / 24 / 30 hrs
├── Power BI Documentation:            6 /  8 / 10 hrs
├── Staff Training / Walkthrough:      5 /  7 /  9 hrs
└── Contingency Buffer:                8 / 12 / 16 hrs
TOTAL: 55 / 75 / 97 Hours (75-Hour Baseline)

Option 2: Expanded Scope (Dataverse + Ingestion) — MVP / Complete, 110–150 hours:
├── Discovery & Schema Audit:         10 / 16 hrs
├── Dataverse Entity Modeling:        16 / 20 hrs
├── Intake & Pipeline Design:         18 / 22 hrs
├── Dataflows / Automate ETL:         22 / 28 hrs
├── Validation & Error Handling:      12 / 18 hrs
├── Power BI Integration:             18 / 22 hrs
├── Historical Migration & QA:         8 / 14 hrs
└── Admin Runbook & Training:          6 / 10 hrs
TOTAL: 110 hrs (MVP) – 150 hrs (Complete)
```

---

## 6. Risks, Assumptions, and Open Questions

### Critical dependencies and assumptions:
1. **2025 prototype state (Option 1):** Treated as work in progress rather than complete or not-started. The exact completion level is not yet confirmed and materially affects the Prototype task's hours — to be validated during Discovery before the estimate is finalized.
2. **M365 tenant administration:** Option 2 requires tenant-level permissions to create Power Platform environments and provision Dataverse.
3. **Licensing and tenant capacity:** Should be validated with SCOG's Microsoft 365 administrator as part of Option 2 planning.
4. **Excel file consistency (Option 1):** The estimate assumes SCOG delivers clean, normalized Excel tables; unstandardized historical data would push hours toward or beyond the high end of the range.
5. **GIS reference layers:** Assumes SCOG or Skagit County GIS provides usable boundary files (Shapefile or GeoJSON) convertible to the chosen mapping visual.
6. **Mapping visual:** Standardized on **Azure Maps or ArcGIS Maps for Power BI** (GA-grade) rather than the preview-only Shape Map visual, for long-term Board PDF export stability.

---

## 7. Strategic Recommendation

This document is intended to support SCOG's decision now, not to presuppose it. Both options are technically sound; the right choice depends on SCOG's priorities and constraints:

* **Choose Option 1** if the priority is delivering a working, interactive Power BI report within the current contract scope and board cycle, and SCOG staff can reliably prepare Excel/GIS source files each year.
* **Choose Option 2** if the priority is reducing annual manual data-compilation effort, establishing stronger data governance and an audit trail, and building a foundation for future regional reporting needs — and SCOG is prepared to validate the added licensing and administration requirements.
* **Confirm the 2025 prototype's actual state** before finalizing the Option 1 estimate, since it is the largest swing factor in that number.
* **If licensing or Power Platform tenant constraints** make Option 2 impractical for now, Option 1 stands on its own merits as a complete implementation path, not merely an interim step.

---

## Revision Log

* **Revision 3 (September 16, 2026):**
  - **Option 1 Base Contract Framing:** Established Option 1 explicitly as the base contracted approach with a 55–97 hour range (75-hour baseline) across six bottom-up task areas.
  - **Option 2 Scope & Hours Expansion:** Recalibrated Option 2 to **110–150 hours** (MVP: 110 hrs, Complete: 150 hrs) across expanded tasks for schema audit (10–16 hrs), Dataverse modeling (16–20 hrs), intake architecture (18–22 hrs), ETL dataflows (22–28 hrs), error handling (12–18 hrs), Power BI modeling (18–22 hrs), migration & QA (8–14 hrs), and governance/training (6–10 hrs).
  - **Objective Decision Support:** Updated the executive summary, comparison matrix, and strategic recommendations to neutrally present both options based on SCOG's priorities and capacity constraints, affirming that Option 1 stands on its own merits.
* **Revision 2 (September 16, 2026):**
  - Replaced the 15-hour fixed budget structure with a realistic six-task bottom-up breakdown (Discovery, 2025 Prototype, 2026 Production Report, Documentation, Staff Training, Contingency) targeting a 70–100 hour range with a 75-hour baseline (55 hrs low / 97 hrs high).
  - Clarified that the original 15-hour figure described the fee for producing the scoping document itself.
  - Treated the 2025 prototype as work in progress and documented the assumption that prototype and production share a unified semantic model.
* **Revision 1 (September 15, 2026):**
  - Reconciled Option 2 hour estimate to 90–124 hours.
  - Standardized mapping visual on GA-grade Azure Maps / ArcGIS Maps.
  - Updated Power BI Pro pricing ($14/mo) and Dataverse pooled capacity guidance.
  - Added formula-based template integrity verification (.xlsx) and operational maintenance ranges (20–40 hrs vs 2–4 hrs).
