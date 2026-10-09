# Application Specifications: SCOG Annual Growth Monitoring Report

## 1. Executive Summary & Project Context
- **Client:** Skagit Council of Governments (SCOG) — Regional Planning Organization in Skagit County, Washington.
- **Project Status:** Under Active Construction & Implementation (Option 1 Base Scope).
- **Architecture:** Standardized SharePoint/Excel Star Schema with Power BI Semantic Model and GIS Spatial Mapping.
- **Business Need:** Modernize the manual, fragmented spreadsheet compilation of annual growth monitoring data into an auditable, interactive Microsoft Power BI reporting suite with board-adopted print and export canvases.

---

## 2. Functional Requirements & Scope (Option 1)

### RF-01: Data Domains and Regional Growth Metrics
- **Thematic Domains:**
  - **Housing:** Annual building permits by structure type (Single-Family, Duplex, Multi-Family 3-4, Multi-Family 5+, ADUs), demolitions, net unit changes, construction valuations, and Growth Management Act (GMA) 2045 targets.
  - **Population:** Official Washington State Office of Financial Management (OFM) April 1 population estimates, historical growth trajectories, and 2045 allocations.
  - **Employment:** Washington State Employment Security Department (ESD) covered employment by NAICS industry sector.
- **Jurisdictional Entities (Skagit County):**
  - Incorporated Cities and Towns: Anacortes, Burlington, Concrete, Hamilton, La Conner, Lyman, Mount Vernon, Sedro-Woolley.
  - Designated Non-Municipal Urban Growth Areas (UGAs): Bay View Ridge UGA, Swinomish UGA.
  - Rural Balance: Unincorporated Skagit County (all rural and resource lands outside designated UGAs).

### RF-02: Consumption Modes (Interactive Dashboard vs. Board-Adopted PDF Export)
- **Interactive Service Dashboard:** 4-page analytical report:
  1. Executive Summary & Regional Dashboard
  2. Housing Deep-Dive & AMI Distribution
  3. Population & Employment Overview
  4. Jurisdictional Comparison & Spatial Mapping
- **Board-Adopted Print / Export Canvases:**
  - Standardized 16:9 widescreen canvas format (1280 × 720 px).
  - High-contrast civic styling with accessible color palette.
  - Dynamic metadata footer containing formal data source and adoption citations on every page.

### RF-03: Excel Intake Hardening & Lightweight Governance
- Structured master Excel intake templates in SharePoint Online / OneDrive.
- Formula-based schema validation (TEXTJOIN header string validation, SUMIFS historical control totals, dropdown constraints).
- Strict column selection (`Table.SelectColumns` with `MissingField.Error`) and strong data typing in Power Query (M) to prevent schema drift.

---

## 3. Technical Implementation Phases & Deliverables

| Implementation Phase | Key Deliverables & Scope | Technical Status |
| :--- | :--- | :--- |
| **Phase 1: Discovery & Source Data Structuring** | Source schema audits (OFM, ESD, GMA Allocations); master Excel intake templates; relational Star Schema design; GIS municipal/UGA centroid coordinate verification. | Completed |
| **Phase 2: 2025 Prototype (PBIP Baseline)** | Git-integrated Power BI Project (`.pbip`); TMSL 1567 semantic model; 30+ production DAX measures; 4-page 16:9 visual report layout; strict M query schema assertions. | Completed & Under Review |
| **Phase 3: 2026 Production Report** | Current-year (2026) data ingestion; refined Board-quality visual polish; PDF export formatting verification; publication to SCOG Power BI Service workspace. | Upcoming |
| **Phase 4: Technical Documentation & Runbook** | Data architecture runbook; step-by-step annual refresh operating guide; schema validation troubleshooting documentation. | Upcoming |
| **Phase 5: Staff Training & Knowledge Transfer** | Live staff walkthrough session; recording and handoff documentation. | Upcoming |
