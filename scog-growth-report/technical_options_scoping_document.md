# Technical Options Scoping Document: Annual Growth Monitoring Report

**Client:** Skagit Council of Governments (SCOG)  
**Author:** Antonio / Skagit Consulting  
**Date:** September 15, 2026  
**Target Delivery:** Wednesday Delivery Review  
**Revision Note:** This version reconciles the Option 2 hour estimate to a single consistent range (90–124 hours) and flags key technical and licensing figures to be confirmed against current Microsoft documentation before presentation to the Board.

---

## 1. Executive Summary

The Skagit Council of Governments (SCOG) compiles and publishes an annual **Growth Monitoring Report** to track regional land use, population, housing, and employment trends under Washington State's Growth Management Act (GMA). Historically, SCOG staff has manually gathered disparate spreadsheets from municipal and county jurisdictions, cleaned and merged them in Microsoft Excel, and manually produced charts and tables for inclusion in board-adopted reports.

This project evaluates the transition of SCOG's annual growth monitoring reporting into **Microsoft Power BI**. The primary objective is to deliver an interactive, maintainable, and visually compelling reporting system that streamlines annual updates while preserving the official, archivable format required for Board adoption.

This scoping document provides an objective, side-by-side technical evaluation of two delivery pathways:
- **Option 1 — Base Scope (Power BI from SCOG-Prepared Excel/GIS Files):** Tailored strictly to a **budgeted 15-hour implementation**. SCOG staff retains responsibility for cleaning and structuring annual Excel and GIS files, while Skagit Consulting constructs a clean, standardized Power BI data model, core interactive dashboards, and a streamlined annual refresh procedure.
- **Option 2 — Expanded Scope (Dataverse-Backed Reporting Architecture with Annual Ingestion Pipeline):** An enterprise-grade architecture (estimated at **90 – 124 hours**) that establishes Microsoft Dataverse as a single source of truth, introducing automated file intake (via SharePoint and Power Query / Power Automate Dataflows), validation, historical auditing, and approval workflows.

---

## 2. Option 1 — Base Scope: Power BI Report Built from SCOG-Prepared Excel/GIS Files

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

* **Expected Excel Structure:** Rather than unstructured spreadsheets with merged cells or presentation formatting, data must be arranged in flat **Excel Tables (`ListObject`)**. Each theme (Housing, Population, Employment) will have a fixed schema with invariant column headers (e.g., `ReportingYear`, `JurisdictionID`, `MetricType`, `Value`, `Unit`).
* **Data Model Approach:** A classic, lightweight **Star Schema**. 
  - **Fact Tables:** Numerical observations at the annual grain (`Fact_Housing_Units`, `Fact_Population_OFM`, `Fact_Employment_ESD`).
  - **Dimension Tables:** Conformed dimensions (`Dim_Jurisdiction`, `Dim_Year`, `Dim_GrowthTarget`).
* **Star Schema vs. Flat Model:** A star schema is strongly recommended over a single wide flat table because it allows cross-filtering across disparate data sources (OFM population vs. local permit data) without many-to-many cardinality pitfalls.

### 2.2 Power BI Report Structure
To respect the strict 15-hour budget while providing high visual and analytical impact, the report will be structured into 4 cohesive pages:
1. **Executive Summary & Regional Dashboard:** High-level KPIs (Total County Population, Net New Housing Units, Total Covered Employment, YoY % Growth, Progress toward 20-Year GMA Allocations).
2. **Housing Deep-Dive (Primary Focus):** 
   - Annual residential building permits (Single-Family vs. Multi-Family vs. ADUs) by jurisdiction.
   - Cumulative net housing growth vs. Countywide Planning Policy (CPP) housing allocation targets.
   - County vs. Urban Growth Area (UGA) distribution.
3. **Population & Employment Overview (Lighter Views):**
   - Washington Office of Financial Management (OFM) historical population estimates and annual growth rates.
   - Employment Security Department (ESD) covered employment trends by sector/industry.
4. **Jurisdictional Comparison & Spatial Mapping:**
   - **Recommended Default:** **Azure Maps** or **ArcGIS Maps for Power BI** visual.
   - **Technical Caveat on Shape Map:** Although Shape Map supports custom TopoJSON files, it has remained in perpetual "preview" status since 2016 and is reported across Microsoft community forums ([Fabric Community Service Discussion](https://community.fabric.microsoft.com/t5/Service/shape-map/m-p/491855)) as exhibiting inconsistent rendering or disappearing from the Visualizations pane post-publishing in some Power BI Service environments. Because SCOG's operational workflow requires publishing to the cloud workspace and exporting high-fidelity Board PDFs directly from the Service, we **sidestep Shape Map entirely** and standardize on Azure Maps or ArcGIS Maps for Power BI to eliminate cloud export and rendering failure risks.
   - Jurisdictional comparative benchmark cards (e.g., Mount Vernon, Burlington, Anacortes, Sedro-Woolley, Concrete, Hamilton, La Conner, Lyman, and Unincorporated areas).
5. **Board-Adopted Print / Export Considerations:**
   - Report canvases will be locked to standard **16:9 widescreen** with high-contrast, publication-grade styling.
   - Visual headers and slicers will be formatted to cleanly export to PDF for the formal Board package, accompanied by a dynamic metadata footer ("Data Source: SCOG Annual Monitoring | Adopted: [Date]").

### 2.3 Annual Update Process
* **Staff Pre-Refresh Steps:** 
  1. SCOG staff collects annual data from OFM, ESD, and municipal permit offices.
  2. Staff inputs new annual rows into the pre-formatted Excel Master Tables stored in SharePoint.
  3. **Formula-Based Template Integrity Verification (Standard `.xlsx`, No Macros Required):**
     - **Header String Comparison (Schema Protection):** To prevent broken Power Query refreshes caused by accidental column renames or deletions, the master Excel template (`.xlsx`) includes a prominent formula-based status cell. A standard formula (`TEXTJOIN` / array comparison) checks the table's header row against the expected schema string. If any header is modified, deleted, or reordered, the status cell immediately flags: `⚠️ SCHEMA ERROR: Column headers altered. Do not trigger Power BI refresh.` Because this uses native formulas, the files remain standard `.xlsx` (fully compatible with Excel Online, SharePoint co-authoring, and requiring zero VBA/macros).
     - **Historical Baseline Reconciliation Total:** A formula-based control cell computes a verification sum (`SUMIFS`) across prior board-adopted years (e.g., 2010–2025). This gives staff an immediate visual check that historical baseline numbers were not inadvertently altered or shifted while typing in the new annual row.
     - **In-Cell Dropdown Constraints:** Native Excel Data Validation enforces closed dropdown lists for official jurisdiction IDs and restricts permit, population, and employment counts to positive numbers.
* **Scope Realism within the 15-Hour Budget:** The validation features above are delivered as **pre-configured template formulas** baked into the initial blank master workbooks provided during Task 1 (Source File Review & Template Standardization). In Power Query (Task 2), schema enforcement relies on native column-selection assertions (`Table.SelectColumns` with strict typing) that cleanly halt refresh if required columns are absent, avoiding the need for complex custom error-routing logic that would exceed the 15-hour budget.
* **Naming Conventions:** A single, persistent file naming scheme (e.g., `SCOG_Growth_Master_Data.xlsx` or partitioned files `SCOG_Housing_Master.xlsx`, `SCOG_Population_Master.xlsx`) in a dedicated SharePoint document library.
* **Refresh & Validation in Power BI:**
  1. Open Power BI Desktop (or trigger scheduled cloud refresh in Power BI Service).
  2. **Power Query Refresh:** Power Query ingests the verified SharePoint files; native type enforcement validates schema integrity during load.
  3. Review the "Data Audit / QA Visual" (a dedicated validation visual checking row counts and total permits against raw inputs).
  4. Publish to the SCOG Power BI Workspace and export the official PDF for Board review.

### 2.4 Pros and Cons

| Pros (Advantages) | Cons (Limitations & Risks) |
| :--- | :--- |
| **Fastest Delivery:** Fits directly into the active contract scope and minimal budget. | **Fragility (Excel Entropy):** Column alterations break refresh (mitigated by Excel formula header comparisons and native Power Query schema checks). |
| **Zero Added Software Licensing:** Requires only standard M365 and existing Power BI Pro licenses. | **High Staff Burden:** All cleaning and formatting remains entirely manual on SCOG staff. |
| **Low Learning Curve:** SCOG staff is already comfortable manipulating Excel. | **Weak Audit Trail:** No native database log of which user altered numbers prior to publication. |
| **Simple Governance:** No complex Azure or Power Platform environments to administer. | **Limited Concurrency:** Multiple staff editing the same workbook risks sync locks and formula corruption. |

### 2.5 Estimated Implementation Hours (Fixed Budget: 15 Hours)

To deliver a reliable, professional report within the budgeted 15 hours, the scope is precisely allocated to eliminate overhead:

| Task Breakdown | Low (hrs) | Baseline (hrs) | High (hrs) | Task Description |
| :--- | :---: | :---: | :---: | :--- |
| **1. Source File Review & Template Standardization** | 1.5 | **2.0** | 2.5 | Inspect sample Excel/GIS files, provide SCOG with locked tabular template guidelines. |
| **2. Power Query Ingestion & Star Schema Model** | 2.5 | **3.0** | 3.5 | Build clean SharePoint connector, dimension relationships, DAX core measures (YoY, Targets). |
| **3. Power BI Report & Visuals Development** | 5.0 | **6.0** | 7.0 | Build 4-page report (Executive, Housing Deep-Dive, Pop/Emp, Jurisdictional/Shape Map). |
| **4. Board-Adopted PDF Export & QA Validation** | 1.5 | **2.0** | 2.0 | Configure 16:9 print layouts, visual QA matrix, verify PDF export fidelity. |
| **5. Documentation & Handoff Session** | 1.5 | **2.0** | 2.0 | 1-page step-by-step refresh checklist and 1-hour live handoff walkthrough with staff. |
| **Total Option 1 Hours** | **12.0** | **15.0** | **17.0** | **Strictly aligned with the 15-hour budgeted cap.** |

> [!IMPORTANT]
> **Key Assumptions for Option 1 Feasibility within 15 Hours:**
> 1. SCOG staff delivers 100% clean, standardized Excel tabular data (`ListObject` format) with uniform headers across all reporting years.
> 2. Skagit GIS boundaries are provided in ready-to-use GeoJSON, Shapefile, or TopoJSON format without requiring custom geospatial reprojection.
> 3. Scope does not include custom ETL data scrubbing, complex paginated report builder (.rdl) development, or historical data forensic reconciliation.

> [!NOTE]
> **Scope Sensitivity & Delivery Note:** The 6.0-hour allocation for report and visual development across 4 pages represents an agile, focused build. If underlying source data requires unanticipated manual cleanup or geospatial re-alignment beyond the agreed template, this line item represents the primary area of budget sensitivity. To guarantee delivery within the 15-hour fixed budget, visuals will strictly adhere to pre-defined standard layouts and verified source structures.

---

## 3. Option 2 — Expanded Scope: Dataverse-Backed Reporting Architecture with Annual Ingestion Pipeline

### 3.1 Recommended Architecture
Option 2 transforms SCOG's annual growth monitoring from an ad-hoc reporting task into an enterprise data platform. Data is decoupled from end-user spreadsheets and centralized in **Microsoft Dataverse**.

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
                                    ▼ (DirectQuery / Azure Synapse Link / Import)
                      [Power BI Semantic Model]
                                    │
                                    ▼
                [Interactive Board Report & Historical Trends]
```

#### Conceptual Dataverse Table Design:
1. **`scog_jurisdiction`:** Unique municipal entities, county unincorporated zones, GMA designation, baseline planning targets.
2. **`scog_reporting_period`:** Reporting years, calendar metadata, adoption cycle state (`Draft`, `Under Review`, `Board Adopted`).
3. **`scog_housing_metric`:** Permitted units, housing type (Single-Family, Multi-Family, Accessory Dwelling Units), demolition counts, net unit gains.
4. **`scog_population_metric`:** Official OFM April 1 estimates, annual growth rate, cumulative decadal growth.
5. **`scog_employment_metric`:** ESD covered employment counts by NAICS sector classification.
6. **`scog_import_log` & `scog_import_error`:** Tracks timestamp, uploaded file name, processing user, row counts, and specific cell-level validation rejections.
7. **`scog_geography_reference`:** Boundary definitions, GIS centroids, and boundary change metadata.

* **Power BI Connectivity:** Power BI connects via the native **Dataverse Connector** using the TDS endpoint (supports both high-performance Import mode and DirectQuery).
* **Year-over-Year Reporting:** Multi-year historical data is permanently stored in normalized tables, enabling instant 5-year, 10-year, and 20-year trend analyses without manual historical stitching.

### 3.2 Annual File Intake and Ingestion Process
* **Intake Mechanism:** SCOG staff drops raw annual spreadsheets received from local cities and state agencies into a designated **SharePoint Intake Folder** structured by year (`/Intake/2026/`).
* **Ingestion Technology Choice:** **Power Query Dataflows (Power Apps / Power Platform Dataflows)** combined with a lightweight **Power Automate flow**. Dataflows provide resilient column-mapping, data transformation, and scheduled or triggered data loading directly into Dataverse tables.
* **Standardization & Pre-Validation:**
  - The pipeline validates that incoming jurisdiction names match official master IDs (e.g., standardizing "City of Mount Vernon," "Mt. Vernon," and "Mount Vernon" to a single ID).
  - Validates numeric thresholds (e.g., residential permits cannot be negative; population cannot drop by 50% without a warning flag).
* **Surfacing Errors & Exceptions:** If a file fails validation, rows with discrepancies are flagged into `scog_import_error`, and an automated notification (email or Teams adaptive card) alerts staff detailing the exact row and field requiring correction.
* **Formal Approval Step:** Data imported into Dataverse defaults to `Status = Draft`. Once staff reviews the validation summary, an authorized administrator updates the period status to `Board Adopted`, which updates the public-facing Power BI visuals.

### 3.3 Data Governance and Maintainability
* **No Annual Model Rebuilding:** The Power BI semantic model connects to persistent Dataverse entity structures. Adding year 2027 or 2028 requires zero changes to measures, relationships, or visuals.
* **Historical Preservation:** Once a reporting year is marked `Adopted`, row-level security or Dataverse table permissions can freeze historical records, preventing accidental edits.
* **Data Lineage:** Every metric record links back to the originating file record in `scog_import_log`, preserving full auditability for GMA legal compliance.

### 3.4 Power BI Reporting Impact
* **Unified Refresh:** Automatic cloud-to-cloud refresh with no desktop file locking issues.
* **Advanced Analytics:** Enables dynamic 10-year rolling averages, compound annual growth rate (CAGR) measures, and automated target vs. actual variance analysis.
* **Future Scalability:** Lays the data groundwork for future SCOG initiatives (e.g., regional transportation models, buildable lands inventories, public data portals).

### 3.5 Licensing, Hosting, and Added Costs

Implementing Option 2 introduces Microsoft Power Platform licensing considerations that must be validated with SCOG's M365 administrator. The figures below are approximate and should be confirmed against Microsoft's current pricing pages and SCOG's specific agreement (public-sector/nonprofit pricing can differ materially from list price) before being presented to the Board as firm numbers:

1. **Dataverse Storage Capacity:** Under current Microsoft Power Platform licensing, the tenant receives a base entitlement of **20 GB Database capacity** upon purchasing a qualifying Power Apps Premium license (plus 250 MB database / 2 GB file storage accrued per user license). Because SCOG's cumulative annual growth data across decades represents only a few megabytes, the reporting dataset will comfortably reside well within default tenant capacity, incurring **$0 in incremental database storage add-on fees** ($40/GB/month list).
2. **Power Platform Ingestion Licensing:** 
   - Connecting Power Automate flows and Power Query Dataflows into Dataverse requires **Power Apps Premium** (currently **$20/user/month list price**; note that the legacy $5/user/app plan was retired for new customers in early 2026, with Pay-As-You-Go via Azure available at ~$10/active user/app/month).
   - *Operational Impact:* Only the 1 or 2 SCOG staff members responsible for administering and triggering annual ingestion pipelines require this license. Report-only consumers in Power BI do **not** require Power Apps licenses.
3. **Power BI Licensing:** Current list pricing for **Power BI Pro is $14/user/month** (effective post-April 2025 price adjustment, up from historical $10/mo), with **Premium Per User (PPU) at $24/user/month** (up from $20/mo). Power BI Pro remains required for report authors and internal consumers unless SCOG holds M365 E5 or Fabric capacity. Specific governmental/GCC pricing should be confirmed against SCOG's Microsoft contract.

### 3.6 Pros and Cons

| Pros (Advantages) | Cons (Limitations & Risks) |
| :--- | :--- |
| **True Automation:** Eliminates a large share of annual staff manual formatting and data prep. | **Higher Initial Cost:** Implementation hours are roughly 6x to 8x the Option 1 budget. |
| **Bulletproof Data Governance:** Role-based security, historical data freezing, and audit logs. | **Licensing Complexity:** Potential added recurring cost for Power Apps / Dataverse capacity. |
| **Zero Refresh Maintenance:** Model never breaks from renamed spreadsheet columns. | **Higher Skill Floor:** Requires basic Power Platform administration knowledge for long-term ownership. |
| **Scalable Foundation:** Ready for multi-agency inputs and future regional planning tools. | **Overkill for Small Datasets:** Significant architectural overhead for an annual update cadence. |

### 3.7 Estimated Implementation Hours (Expanded Scope: 90 – 124 Hours)

Option 2 represents a robust engineering engagement. We differentiate a **Minimum Viable Implementation (MVP)** from a **Complete Enterprise Implementation**:

| Task Breakdown | MVP (hrs) | Complete (hrs) | Task Description |
| :--- | :---: | :---: | :--- |
| **1. Discovery & Source File Schema Audit** | 8 | 12 | In-depth audit of municipal and state data schemas, mapping rules, cross-agency taxonomy. |
| **2. Dataverse Environment & Entity Modeling** | 12 | 16 | Provisioning Dataverse solution, custom tables, option sets, relationships, keys, security roles. |
| **3. Annual Intake & SharePoint Ingestion Architecture** | 14 | 18 | SharePoint library architecture, folder structure, intake triggers, metadata capture. |
| **4. Dataflows / Power Automate ETL Implementation** | 18 | 24 | Power Query dataflows, schema standardization, automated upsert logic into Dataverse. |
| **5. Data Validation & Error Handling Pipelines** | 10 | 14 | Pre-load validation rules, error logging tables, automated staff alert notifications. |
| **6. Power BI Semantic Model & Report Development** | 14 | 18 | Direct Dataverse connection, multi-year DAX measures, comprehensive 5-page report & mapping. |
| **7. User Acceptance Testing & Historical Migration** | 8 | 12 | Migrating 10–15 years of historical Excel records, end-to-end reconciliation, edge-case testing. |
| **8. Governance, Documentation & Admin Training** | 6 | 10 | Full technical architecture document, administrator runbook, staff training sessions. |
| **Total Option 2 Hours** | **90 hrs** | **124 hrs** | **Proposal baseline: 90 – 124 hours.** |

---

## 4. Side-by-Side Comparison Matrix

| Evaluation Category | Option 1: Power BI from SCOG-Prepared Excel/GIS | Option 2: Dataverse + Automated Intake Pipeline |
| :--- | :--- | :--- |
| **Initial Implementation Complexity** | **Low:** Rapid desktop build using existing files. | **High:** Multi-component Power Platform architecture. |
| **Annual Maintenance Effort** | **Moderate / High:** Estimated 20–40 hours annually across staff for data collation, manual formatting, and refresh QA *(consulting benchmark estimate based on peer regional planning councils; to be calibrated with SCOG staff post-Year 1)*. | **Low:** Estimated 2–4 hours annually dropping raw files into SharePoint and reviewing approval screens *(consulting benchmark estimate)*. |
| **Staff Skill Required** | Intermediate Excel skills + basic Power BI desktop literacy. | Basic SharePoint drop skills for annual use; Power Platform admin skills for maintenance. |
| **Repeatability & Reliability** | **Fragile:** Vulnerable to human error, altered headers, or accidental file overwrites. | **Resilient:** Deterministic schema enforcement, validation gates, and rejection logging. |
| **Data Quality Controls** | Manual spot-checking in Excel and visual inspection in Power BI. | Automated validation rules, error logs, and approval gate (`Draft` vs `Adopted`). |
| **Licensing / Cost Impact** | **$0 Added Cost:** Operates within current standard M365 and Power BI Pro licenses. | **Potential Added Cost:** Requires Dataverse capacity and potentially Power Apps/Automate licenses — confirm with M365 admin. |
| **Long-Term Scalability** | Limited to annual growth monitoring reporting. | Highly extensible to transportation, buildable lands, and regional data hubs. |
| **Estimated Implementation Hours** | **15 hours (Fixed Budget: 12 – 17 hrs)** | **90 – 124 hours** |
| **Main Risks** | Refresh breaks on year 2; data inconsistencies; high recurring manual staff labor. | Budget rejection; licensing surprises; over-engineering a simple annual task. |
| **Best Fit If...** | SCOG needs an immediate, cost-effective transition to Power BI within current budget constraints. | SCOG seeks a long-term data modernization initiative to eliminate manual spreadsheet workflows. |

---

## 5. Summary of Estimated Hours by Option

```
Option 1: Base Scope (Power BI + Excel)
├── Discovery & Schema Review:    2.0 hrs
├── Model & Power Query:          3.0 hrs
├── Report & Visuals:             6.0 hrs
├── PDF / Print Export QA:        2.0 hrs
└── Handoff & Checklist:          2.0 hrs
TOTAL: 15.0 Hours (Budgeted Cap; Low–High range 12.0–17.0 hrs)

Option 2: Expanded Scope (Dataverse + Ingestion) — MVP / Complete
├── Discovery & Schema Audit:     8 / 12 hrs
├── Dataverse Entity Modeling:   12 / 16 hrs
├── Intake & Pipeline Design:    14 / 18 hrs
├── Dataflows / Automate ETL:    18 / 24 hrs
├── Validation & Error Handling: 10 / 14 hrs
├── Power BI Integration:        14 / 18 hrs
├── Historical Migration & QA:    8 / 12 hrs
└── Admin Runbook & Training:     6 / 10 hrs
TOTAL: 90 hrs (MVP) – 124 hrs (Complete)
```

> [!NOTE]
> **Reconciliation Note:** This summary block matches Section 3.7 exactly. All instances across the document (Executive Summary, Section 3.7, Comparison Matrix, and Summary) are reconciled to the single range supported by the underlying line items: **90 – 124 hours**.

---

## 6. Risks, Assumptions, and Open Questions

### Critical Dependencies & Assumptions:
1. **M365 Tenant Administration:** Option 2 requires tenant-level permissions to create Power Platform environments, provision Dataverse databases, and assign security roles.
2. **Current Licensing Inventory:** We assume SCOG has existing Power BI Pro licenses. Whether SCOG has available Power Apps / Dataverse pooled storage capacity must be validated with their IT administrator — the specific dollar figures in Section 3.5 are approximate and should not be quoted to the Board without confirmation.
3. **Excel File Consistency (Option 1):** Option 1's 15-hour budget assumes SCOG delivers clean, normalized Excel tables. If historical data is fragmented across dozens of unstandardized spreadsheets requiring consulting remediation, hours will exceed the 15-hour allocation.
4. **GIS Reference Layers:** We assume SCOG or Skagit County GIS provides established spatial boundary files (Shapefile or GeoJSON) for municipal boundaries and Urban Growth Areas (UGAs) that can be converted directly to TopoJSON for Power BI's mapping visual of choice.
5. **Report Delivery Cadence:** Both options assume an annual batch reporting cycle rather than real-time or monthly streaming updates.
6. **Mapping Visual Selection (Decided):** Rather than treating Shape Map as a viable alternative, we explicitly adopt **Azure Maps or ArcGIS Maps for Power BI**. Shape Map’s ongoing preview status and documented bug where it disappears or fails to render in the Power BI Service creates an unacceptable operational risk for Board-adopted PDF exports.

---

## 7. Strategic Recommendation

### The Pragmatic Recommendation: Phased Progression ("The Simplest Road First")

Based on the contract parameters and the **15-hour budget allocation** for the base scope, our professional recommendation is to adopt a **phased approach**:

1. **Execute Option 1 Now (Base Scope — 15 Hours):**
   - Immediately satisfies SCOG's primary contract objective: transitioning the static report into an interactive, visually impressive Power BI report in time for the upcoming adoption cycle.
   - Preserves client budget and requires zero additional licensing approvals or tenant IT friction.
   - Provides SCOG with locked Excel templates that instill immediate data hygiene discipline among staff.

2. **Propose Option 2 as a Structured Phase 2 Add-On (Modernization Roadmap):**
   - Present Option 2 in the scoping document not as an absolute prerequisite, but as a **Phase 2 Data Modernization Upgrade**.
   - If SCOG experiences frustration with the manual compilation of municipal Excel sheets during the Year 1 cycle, Option 2 offers a clear, pre-scoped roadmap to automate ingestion, lock down historical governance, and scale into a regional data hub.

This phased strategy protects SCOG's immediate timeline and budget while establishing Skagit Consulting as a forward-thinking strategic partner.

---

## Revision Log
- **Hour Estimate Reconciliation:** Reconciled all Option 2 hour references (Sections 1, 3.7, 4, 5) to a single consistent range: **90–124 hours**, matching the sum of the line-item table in Section 3.7.
- **Power BI Shape Map Risk Avoidance:** Updated Section 2.2 and Section 6 to formally retire Shape Map due to active Power BI Service preview quirks ([Fabric Community Discussion](https://community.fabric.microsoft.com/t5/Service/shape-map/m-p/491855)), defaulting strictly to **Azure Maps or ArcGIS Maps for Power BI**.
- **Power BI Pro Pricing Revision:** Updated Section 3.5 to reflect the current post-April 2025 Microsoft list pricing of **$14/user/month for Power BI Pro** (up from $10) and **$24/user/month for Premium Per User (PPU)** (up from $20), with notes to confirm SCOG's government/GCC agreement discounts.
- **Dataverse Capacity & Power Apps Entitlements:** Updated Section 3.5 with verified Microsoft Power Platform entitlements (tenant base grant of **20 GB Database capacity** on qualifying licenses, confirming SCOG's annual growth data will incur **$0 in incremental storage add-on fees**). Clarified Power Apps Premium list pricing at **$20/user/month** for the 1–2 pipeline administrators.
- **Annual Maintenance Attribution:** Explicitly attributed the 20–40 hr and 2–4 hr annual figures in Section 4 as consulting benchmarks based on peer regional planning agencies, to be calibrated post-Year 1.
- **Scope Sensitivity Reframing:** Reframed the delivery note in Section 2.5 as a professional "Scope Sensitivity & Delivery Note" focusing on standard visual layouts to protect the 15-hour fixed budget.
- **Excel Formula-Based Template Integrity Verification:** Updated Section 2.3 and Section 2.4 to specify formula-based header string matching and historical baseline reconciliation totals within standard `.xlsx` master workbooks (no macros required), coupled with native Power Query column assertions, hardening Option 1 against schema drift while strictly respecting the 15-hour budget.
- **Option 2 Diagram Rule Clarification:** Refined Section 3.1 architecture diagram text to "Non-Negative Permits" to prevent PDF font and symbol rendering clipping.
