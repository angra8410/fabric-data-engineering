# Technical Options Scoping Document: Annual Growth Monitoring Report

**Client:** Skagit Council of Governments (SCOG)  
**Author:** Antonio / Skagit Consulting  
**Date:** September 16, 2026 (Revision 2)  
**Target Delivery:** Wednesday Delivery Review  
**Revision 2 Note:** This version replaces the Option 1 task structure and hour estimate with the six-task breakdown confirmed by the client (Discovery, 2025 Prototype, 2026 Production Report, Documentation, Training, Contingency), targeting a 70–100 hour range instead of the earlier 15-hour figure — which the client has clarified was the fee for producing this scoping document, not the Option 1 implementation estimate. This revision reflects that the 2025 prototype is work in progress rather than complete. Figures for the prototype task in particular are provisional — see the assumption note in Section 2.5 — and should be confirmed once the prototype's actual state is assessed under Task 1.

---

## 1. Executive Summary

The Skagit Council of Governments (SCOG) compiles and publishes an annual **Growth Monitoring Report** to track regional land use, population, housing, and employment trends under Washington State's Growth Management Act (GMA). Historically, SCOG staff has manually gathered disparate spreadsheets from municipal and county jurisdictions, cleaned and merged them in Microsoft Excel, and manually produced charts and tables for inclusion in board-adopted reports.

This project evaluates the transition of SCOG's annual growth monitoring reporting into **Microsoft Power BI**. The primary objective is to deliver an interactive, maintainable, and visually compelling reporting system that streamlines annual updates while preserving the official, archivable format required for Board adoption.

This scoping document provides an objective, side-by-side technical evaluation of two delivery pathways:
- **Option 1 — Base Scope (Power BI from SCOG-Prepared Excel/GIS Files):** Implementation is scoped bottom-up across six task areas — discovery, a 2025 prototype (in progress) built on prior-year data, the 2026 production report, documentation, staff training, and contingency — targeting a **70–100 hour range** (baseline ~75 hours). SCOG staff retains responsibility for cleaning and structuring annual Excel and GIS files, while Skagit Consulting constructs a clean, standardized Power BI data model, core interactive dashboards, and a streamlined annual refresh procedure.
- **Option 2 — Expanded Scope (Dataverse-Backed Reporting Architecture with Annual Ingestion Pipeline):** An enterprise-grade architecture (estimated at **90–124 hours**) that establishes Microsoft Dataverse as a single source of truth, introducing automated file intake (via SharePoint and Power Query / Power Automate Dataflows), validation, historical auditing, and approval workflows.

> [!IMPORTANT]
> **Confirmed per Aaron's guidance:** The 15-hour figure referenced in an earlier version of this engagement is the Skagit Consulting ↔ The Flock fee for producing this scoping document — it is not, and should not be used as, SCOG's Option 1 implementation estimate. Option 1 is estimated separately below, bottom-up, against the six task areas defined by the SCOG contract scope.

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

* **Expected Excel Structure:** Rather than unstructured spreadsheets with merged cells or presentation formatting, data must be arranged in flat **Excel Tables (`ListObject`)**. Each theme (Housing, Population, Employment) will have a fixed schema with invariant column headers (e.g., `ReportingYear`, `JurisdictionID`, `MetricType`, `Value`, `Unit`).
* **Data Model Approach:** A classic, lightweight **Star Schema**. 
  - **Fact Tables:** Numerical observations at the annual grain (`Fact_Housing_Units`, `Fact_Population_OFM`, `Fact_Employment_ESD`).
  - **Dimension Tables:** Conformed dimensions (`Dim_Jurisdiction`, `Dim_Year`, `Dim_GrowthTarget`).
* **Star Schema vs. Flat Model:** A star schema is strongly recommended over a single wide flat table because it allows cross-filtering across disparate data sources (OFM population vs. local permit data) without many-to-many cardinality pitfalls.
* **Prototype Build Integration:** Because Option 1 now includes building out a 2025 prototype as its own task rather than treating the model as a quick pass over already-complete work, the architecture and star schema design happen as part of that prototype build — not as a separate up-front step.

### 2.2 Power BI Report Structure
The report is structured into four cohesive pages, built out first against 2025 prior-year data in the prototype and then extended to 2026 data in the production report:
1. **Executive Summary & Regional Dashboard:** County-level KPIs (Total County Population, Net New Housing Units, Total Covered Employment, YoY % Growth, Progress toward 20-Year GMA Allocations).
2. **Housing Deep-Dive (Primary Focus):** 
   - Annual residential building permits (Single-Family vs. Multi-Family vs. ADUs) by jurisdiction.
   - Cumulative net housing growth vs. Countywide Planning Policy (CPP) housing allocation targets.
   - County vs. Urban Growth Area (UGA) distribution.
3. **Population & Employment Overview (Lighter Supporting Views):**
   - Washington Office of Financial Management (OFM) historical population estimates and annual growth rates.
   - Employment Security Department (ESD) covered employment trends by sector/industry.
4. **Jurisdictional Comparison & Spatial Mapping:**
   - **Recommended Default:** **Azure Maps** or **ArcGIS Maps for Power BI** visual.
   - **Technical Rationale on Mapping Visuals (Standardizing on Azure Maps / ArcGIS Maps):** Standardized on Azure Maps or ArcGIS Maps for Power BI (GA-grade, board-suitable) rather than the preview-only Shape Map visual, ensuring long-term stability and eliminating risks of rendering inconsistencies in Board-adopted PDF exports.
   - Jurisdictional comparative benchmark cards (e.g., Mount Vernon, Burlington, Anacortes, Sedro-Woolley, Concrete, Hamilton, La Conner, Lyman, and Unincorporated areas).
5. **Board-Adopted Print / Export Considerations:**
   - Report canvases locked to standard **16:9 widescreen** with high-contrast, publication-grade styling.
   - Visual headers and slicers formatted to cleanly export to PDF for the formal Board package, accompanied by a dynamic metadata footer ("Data Source: SCOG Annual Monitoring | Adopted: [Date]").

### 2.3 Annual Update Process
* **Staff Pre-Refresh Steps:** 
  1. SCOG staff collects annual data from OFM, ESD, and municipal permit offices.
  2. Staff inputs new annual rows into pre-formatted Excel Master Tables stored in SharePoint.
  3. **Formula-Based Template Integrity Verification (Standard `.xlsx`, No Macros Required):**
     - **Header String Comparison (Schema Protection):** To prevent broken Power Query refreshes caused by accidental column renames or deletions, the master Excel template (`.xlsx`) includes a prominent formula-based status cell. A standard formula (`TEXTJOIN` / array comparison) checks the table's header row against the expected schema string. If any header is modified, deleted, or reordered, the status cell immediately flags: `⚠️ SCHEMA ERROR: Column headers altered. Do not trigger Power BI refresh.` Because this uses native formulas, the files remain standard `.xlsx` (fully compatible with Excel Online, SharePoint co-authoring, and requiring zero VBA/macros).
     - **Historical Baseline Reconciliation Total:** A formula-based control cell computes a verification sum (`SUMIFS`) across prior board-adopted years (e.g., 2010–2025). This gives staff an immediate visual check that historical baseline numbers were not inadvertently altered or shifted while typing in the new annual row.
     - **In-Cell Dropdown Constraints:** Native Excel Data Validation enforces closed dropdown lists for official jurisdiction IDs and restricts permit, population, and employment counts to positive numbers.
* **Refresh & Validation in Power BI:**
  1. Open Power BI Desktop (or trigger scheduled cloud refresh in Power BI Service).
  2. **Power Query Refresh:** Power Query ingests the verified SharePoint files; native type enforcement validates schema integrity during load.
  3. Review the "Data Audit / QA Visual" (a dedicated validation visual checking row counts and total permits against raw inputs).
  4. Publish to the SCOG Power BI Workspace and export the official PDF for Board review.

### 2.4 Pros and Cons

| Pros (Advantages) | Cons (Limitations & Risks) |
| :--- | :--- |
| **No Added Software Licensing:** Requires only standard M365 and existing Power BI Pro licenses. | **Fragility (Excel Entropy):** Column alterations break refresh (mitigated but not eliminated by formula-based checks). |
| **Low Learning Curve:** SCOG staff is already comfortable manipulating Excel. | **Manual Staff Burden:** All cleaning and formatting remains manual on SCOG staff annually. |
| **Simple Governance:** No complex Power Platform environment to administer. | **Weak Audit Trail:** No native database log of which user altered numbers prior to publication. |
| **Direct Delivery:** Implements a clean, working Power BI solution without infrastructure overhead. | **Limited Concurrency:** Multi-staff editing risks sync locks and template formula corruption. |

### 2.5 Estimated Implementation Hours (Revised: 70–100 Hour Target Range)

Hours are estimated bottom-up across six task areas rather than back-solved to a fixed total. The 2025 prototype is treated as work in progress — partially built, not started from scratch — which is why its allocation sits below what a full from-zero build would require. The exact reduction is an assumption pending a firsthand assessment of what already exists; Task 1 (Discovery) includes confirming that state before the prototype work is finalized.

| Task Breakdown | Low (hrs) | Baseline (hrs) | High (hrs) | Task Description |
| :--- | :---: | :---: | :---: | :--- |
| **1. Discovery & Planning** | 6 | **8** | 10 | Review existing prototype state, source files, GIS reference data; confirm schema and template approach. |
| **2. 2025 Prototype (prior-year data, in progress)** | 12 | **16** | 22 | Complete the in-progress prototype: star schema, DAX measures, and first working report pages against 2025 data. Hours reflect partial completion — confirm actual state before finalizing. |
| **3. 2026 Production Report** | 18 | **24** | 30 | Apply current-year (2026) data and any updated methodology to the model built in the prototype; refine visuals to board/print quality. |
| **4. Power BI Documentation** | 6 | **8** | 10 | Technical documentation plus an annual refresh runbook. |
| **5. Staff Training / Walkthrough** | 5 | **7** | 9 | Live walkthrough session plus a follow-up session. |
| **6. Contingency** | 8 | **12** | 16 | Buffer for source-data cleanup, schema drift, or mapping/GIS rework beyond the assumptions below. |
| **Total Option 1 Hours** | **55** | **75** | **97** | **Baseline sits within the 70–100 hour target range; low end depends on the prototype being closer to complete than assumed.** |

> [!IMPORTANT]
> **Key Assumptions for Option 1:**
> 1. The 2025 prototype exists in some working form (data connections and/or partial model) but is not yet validated or extended to a full report — to be confirmed during Discovery.
> 2. The 2025 prototype and 2026 production report share one data model and report structure. If SCOG wants them kept as fully separate artifacts, add roughly 10–15 hours.
> 3. SCOG delivers Excel data in flat, tabular (`ListObject`) format with uniform headers across reporting years.
> 4. GIS boundaries are provided in a directly usable format (GeoJSON, Shapefile, or TopoJSON) without custom reprojection.
> 5. Scope excludes custom ETL data scrubbing, paginated report (.rdl) development, or historical data forensic reconciliation.

> [!TIP]
> **Recommendation for the Client Conversation:** Present the 75-hour baseline as the working estimate, with 55 hours as a best case that depends on the prototype being further along than currently assumed and on clean source files. If the client needs the number closer to the low end of the 70–100 range, the honest lever is narrowing scope (e.g., fewer report pages, lighter documentation) rather than trimming the prototype or contingency lines.

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

1. **Dataverse Storage Capacity:** Microsoft Power Platform tenants receive pooled default database capacity upon acquiring qualifying administrator licenses (supplemented by monthly per-user accruals). Because SCOG's cumulative annual growth monitoring records across decades comprise only a few megabytes, the reporting dataset is negligible in size and is expected to reside comfortably within standard tenant pooled capacity, incurring **$0 in incremental database storage add-on fees**. However, because Microsoft regularly updates tenant capacity entitlement models and consumption rules, available tenant storage and exact quota balances must be validated directly with SCOG's M365 tenant administrator via the Power Platform Admin Center prior to procurement.
2. **Power Platform Ingestion Licensing:** 
   - Connecting Power Automate flows and Power Query Dataflows into Dataverse requires **Power Apps Premium** (currently **$20/user/month list price**; note that the legacy $5/user/app plan was retired for new customers in early 2026, with Pay-As-You-Go via Azure available at ~$10/active user/app/month).
   - *Operational Impact:* Only the 1 or 2 SCOG staff members responsible for administering and triggering annual ingestion pipelines require this license. Report-only consumers in Power BI do **not** require Power Apps licenses.
3. **Power BI Licensing:** Current list pricing for **Power BI Pro is $14/user/month** (effective post-April 2025 price adjustment, up from historical $10/mo), with **Premium Per User (PPU) at $24/user/month** (up from $20/mo). Power BI Pro remains required for report authors and internal consumers unless SCOG holds M365 E5 or Fabric capacity. Specific governmental/GCC pricing should be confirmed against SCOG's Microsoft contract.

### 3.6 Pros and Cons

| Pros (Advantages) | Cons (Limitations & Risks) |
| :--- | :--- |
| **True Automation:** Eliminates a large share of annual staff manual formatting and data prep. | **Comparable Implementation Investment:** Implementation hours (90–124 hrs) roughly comparable to or exceeding a fully-scoped Option 1 (70–100 hrs). |
| **Bulletproof Data Governance:** Role-based security, historical data freezing, and audit logs. | **Licensing Complexity:** Potential added recurring cost for Power Apps / Dataverse capacity. |
| **Zero Refresh Maintenance:** Model never breaks from renamed spreadsheet columns. | **Higher Skill Floor:** Requires basic Power Platform administration knowledge for long-term ownership. |
| **Scalable Foundation:** Ready for multi-agency inputs and future regional planning tools. | **Overkill for Small Datasets:** Significant architectural overhead for an annual update cadence. |

### 3.7 Estimated Implementation Hours (Expanded Scope: 90–124 Hours)

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
| **Total Option 2 Hours** | **90 hrs** | **124 hrs** | **Proposal baseline: 90–124 hours.** |

---

## 4. Side-by-Side Comparison Matrix

| Evaluation Category | Option 1: Power BI from SCOG-Prepared Excel/GIS | Option 2: Dataverse + Automated Intake Pipeline |
| :--- | :--- | :--- |
| **Initial Implementation Complexity** | **Moderate:** Bottom-up build across six task areas, including a prototype build-out. | **High:** Multi-component Power Platform architecture. |
| **Annual Maintenance Effort** | **Moderate / High (Estimated 20–40 hours annually across staff):** Indicative operational planning range reflecting cumulative staff time spent coordinating file submissions from multiple jurisdictions, reformatting disparate spreadsheets, and performing visual QA. To be calibrated against SCOG's actual internal tracking after the Year 1 cycle. | **Low (Estimated 2–4 hours annually):** Indicative operational scenario reflecting automated file intake, scheduled dataflow processing, and staff time limited to reviewing validation exceptions and approving final adoption states. |
| **Staff Skill Required** | Intermediate Excel skills + basic Power BI desktop literacy. | Basic SharePoint drop skills for annual use; Power Platform admin skills for maintenance. |
| **Repeatability & Reliability** | **Fragile:** Vulnerable to human error, altered headers, or accidental file overwrites (mitigated by formula-based checks). | **Resilient:** Deterministic schema enforcement, validation gates, and rejection logging. |
| **Data Quality Controls** | Manual spot-checking in Excel and visual inspection in Power BI. | Automated validation rules, error logs, and approval gate (`Draft` vs `Adopted`). |
| **Licensing / Cost Impact** | **$0 Added Cost:** Operates within current standard M365 and Power BI Pro licenses. | **Potential Added Cost:** Requires Dataverse capacity and potentially Power Apps/Automate licenses — confirm with M365 admin. |
| **Long-Term Scalability** | Limited to annual growth monitoring reporting. | Highly extensible to transportation, buildable lands, and regional data hubs. |
| **Estimated Implementation Hours** | **70–100 hours (Baseline ~75 hrs; 55–97 hr range)** | **90–124 hours** |
| **Main Risks** | Refresh breaks in later years; data inconsistencies; ongoing manual staff labor; prototype scope larger than currently assumed. | Budget rejection; licensing surprises; over-engineering a simple annual task. |
| **Best Fit If...** | SCOG needs a working Power BI transition without new Power Platform licensing or admin overhead. | SCOG seeks a long-term data modernization initiative to eliminate manual spreadsheet workflows. |

---

## 5. Summary of Estimated Hours by Option

```
Option 1: Base Scope (Power BI + Excel) — six task areas, 55–97 hr range, 75-hr baseline (target 70–100):
├── Discovery & Planning:              6 /  8 / 10 hrs
├── 2025 Prototype (in progress):     12 / 16 / 22 hrs
├── 2026 Production Report:           18 / 24 / 30 hrs
├── Power BI Documentation:            6 /  8 / 10 hrs
├── Staff Training / Walkthrough:      5 /  7 /  9 hrs
└── Contingency Buffer:                8 / 12 / 16 hrs
TOTAL: 55 / 75 / 97 Hours (Baseline: 75.0 hrs; Target Range: 70–100 hrs)

Option 2: Expanded Scope (Dataverse + Ingestion) — MVP / Complete, 90–124 hours:
├── Discovery & Schema Audit:          8 / 12 hrs
├── Dataverse Entity Modeling:        12 / 16 hrs
├── Intake & Pipeline Design:         14 / 18 hrs
├── Dataflows / Automate ETL:         18 / 24 hrs
├── Validation & Error Handling:      10 / 14 hrs
├── Power BI Integration:             14 / 18 hrs
├── Historical Migration & QA:         8 / 12 hrs
└── Admin Runbook & Training:          6 / 10 hrs
TOTAL: 90 hrs (MVP) – 124 hrs (Complete)
```

> [!NOTE]
> **Reconciliation Note:** This summary block matches Section 2.5 and Section 3.7 exactly. All instances across the document (Executive Summary, Section 2.5, Section 4 Comparison Matrix, and Section 5 Summary) are aligned to the same Option 1 range (70–100 hours, 75-hour baseline). Option 2 is carried over unchanged from the prior revision (90–124 hours) since no new information about Option 2 prompted a change.

---

## 6. Risks, Assumptions, and Open Questions

### Critical Dependencies & Assumptions:
1. **2025 Prototype State (Option 1):** Treated as work in progress rather than complete or not-started. The exact completion level is not yet confirmed and materially affects the Prototype task's hours — to be validated during Discovery before the estimate is finalized.
2. **Original 15-Hour Figure:** Confirmed as the Skagit Consulting ↔ The Flock fee for producing this document, not the Option 1 implementation estimate. This has been clarified directly by the client and should not be read as a budget overrun against the 70–100 hour Option 1 estimate.
3. **M365 Tenant Administration:** Option 2 requires tenant-level permissions to create Power Platform environments, provision Dataverse databases, and assign security roles.
4. **Current Licensing Inventory:** We assume SCOG has existing Power BI Pro licenses. Whether SCOG has available Power Apps / Dataverse pooled storage capacity must be validated with their IT administrator — the specific dollar figures in Section 3.5 are approximate and should not be quoted to the Board without confirmation.
5. **Excel File Consistency (Option 1):** Option 1 assumes SCOG delivers clean, normalized Excel tables. If historical data is fragmented across unstandardized spreadsheets requiring consulting remediation, hours will push toward or beyond the high end of the range.
6. **GIS Reference Layers:** We assume SCOG or Skagit County GIS provides established spatial boundary files (Shapefile or GeoJSON) for municipal boundaries and Urban Growth Areas (UGAs) that can be converted directly for Power BI's mapping visual of choice.
7. **Mapping Visual Selection (Decided):** Standardized on **Azure Maps or ArcGIS Maps for Power BI** (GA-grade) rather than the preview-only Shape Map visual, ensuring long-term Board PDF export stability and eliminating preview-feature risks.

---

## 7. Strategic Recommendation

With Option 1 now scoped bottom-up at **70–100 hours** (75-hour baseline) rather than a fixed 15-hour cap, the phased-adoption logic still holds, but the budget conversation with SCOG needs to happen up front rather than being assumed:

1. **Confirm Prototype State First:** Confirm the 2025 prototype's actual state with SCOG (or internally) before finalizing the Prototype task hours — this is the single largest swing factor in the Option 1 estimate.
2. **Clarify the 15-Hour Document Production Distinction:** Present the 75-hour baseline as the realistic Option 1 estimate, distinct from the 15-hour figure the client has confirmed was quoted for producing this scoping document — not for the Option 1 implementation.
3. **Position Option 2 as a Phase 2 Modernization Roadmap:** Continue to position Option 2 (90–124 hours) as a Phase 2 modernization roadmap rather than a Year 1 prerequisite, to be revisited if SCOG finds the manual Excel compilation burdensome after the first annual cycle.
4. **Negotiation Lever:** If the client needs the Option 1 number closer to the low end of the 70–100 range, the honest lever is narrowing scope (e.g., fewer report pages, lighter documentation) rather than trimming the prototype or contingency lines.

---

## Revision Log
* **Revision 2 (September 16, 2026):**
  - **Option 1 Task Structure & Hour Recalibration:** Replaced the 15-hour fixed budget structure with a realistic six-task bottom-up breakdown (Discovery, 2025 Prototype, 2026 Production Report, Documentation, Staff Training, Contingency) targeting a **70–100 hour range** with a **75-hour baseline** (55 hrs low / 97 hrs high).
  - **Scoping vs. Implementation Disambiguation:** Clarified that the original 15-hour figure described the contract scope for producing this scoping document itself, not the Option 1 Power BI build budget.
  - **In-Progress 2025 Prototype Integration:** Explicitly treated the 2025 prototype as work in progress and documented the assumption that prototype and production share a unified semantic model (+10–15 hrs if separated).
  - **Comparison Matrix & Narrative Harmonization:** Updated initial implementation complexity of Option 1 to "Moderate", updated Option 2 cost comparison in Section 3.6 to "roughly comparable to or exceeding Option 1", aligned Section 4 and Section 5 summaries, and updated the strategic recommendation with explicit client negotiation levers.
* **Revision 1 (September 15, 2026):**
  - Reconciled Option 2 hour estimate to 90–124 hours.
  - Standardized mapping visual on GA-grade Azure Maps / ArcGIS Maps.
  - Updated Power BI Pro pricing ($14/mo) and Dataverse pooled capacity guidance.
  - Added formula-based template integrity verification (.xlsx) and operational maintenance ranges (20–40 hrs vs 2–4 hrs).
