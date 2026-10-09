# SCOG Annual Growth Monitoring Report — Power BI Prototype (2025 Baseline)

## 1. Project Overview & Context
This directory contains the complete **Microsoft Power BI Project (`.pbip`)** and analytical artifacts for the **Skagit Council of Governments (SCOG) Annual Growth Monitoring Report**.

* **Client:** Skagit Council of Governments (SCOG) — Regional Planning Organization in Skagit County, Washington.
* **Phase:** 2025 Prototype Baseline (Prior-Year Historical Calibration & Star Schema Implementation).
* **Delivery Scope:** Option 1 Base Scope (Power BI connected to standardized Excel Star Schema + GIS spatial mapping).
* **Format:** Git-friendly `.pbip` (Power BI Project), enabling full version control, automated CI/CD readiness, and human-readable semantic model / report definitions.

---

## 2. Directory Structure

```
powerbi/
├── SCOG_Growth_Monitoring_Report/
│   ├── SCOG_Growth_Monitoring_Report.pbip              # Root project file (open in Power BI Desktop)
│   ├── SCOG_Growth_Monitoring_Report.SemanticModel/    # Tabular semantic model definition
│   │   ├── definition.pbism                            # Model settings
│   │   └── model.bim                                   # Complete TMSL 1567 schema (tables, M queries, DAX, relations)
│   └── SCOG_Growth_Monitoring_Report.Report/           # Visual canvas layout
│       ├── definition.pbir                             # Report-to-model binding
│       ├── report.json                                 # 4-page 16:9 widescreen canvas definitions
│       └── StaticResources/SharedResources/BaseThemes/
│           └── CY24SU08.json                           # Custom SCOG civic theme
├── dax_measures.dax                                    # Standalone DAX formulas library (30+ measures with comments)
├── power_query_m_scripts.pq                            # Standalone Power Query M transformations
├── scog_theme.json                                     # SCOG branded color palette & visual styles
└── README.md                                           # This technical runbook
```

---

## 3. How to Open and Refresh the Prototype in Power BI Desktop

### Step 1: Open the Project
Double-click or open with Power BI Desktop:
```
powerbi/SCOG_Growth_Monitoring_Report/SCOG_Growth_Monitoring_Report.pbip
```
*(Requires Power BI Desktop June 2023 or newer with Power BI Project (.pbip) enabled).*

### Step 2: Validate Data Source Parameter
The semantic model includes a centralized parameter:
* **Parameter Name:** `SourceWorkbookPath`
* **Default Value:** `.../data/processed/SCOG_Star_Schema_Data_Model.xlsx`

To re-point to another location (e.g., SharePoint Online / OneDrive document library):
1. In Power BI Desktop, click **Home** > **Transform Data** > **Edit Parameters**.
2. Paste the local path or SharePoint web URL of `SCOG_Star_Schema_Data_Model.xlsx`.
3. Click **Apply Changes**.

### Step 3: Refresh the Data
Click **Home** > **Refresh**. All 8 tables will ingest and recalculate deterministically with zero schema drift.

---

## 4. Star Schema Architecture

The report is built on a relational Star Schema designed to ensure referential integrity across 56 historical and planning years (1990–2045):

### Conformed Dimensions (4 Tables)
1. **`Dim_Jurisdiction` (11 Entities):**
   * 8 Incorporated Cities/Towns: *Anacortes, Burlington, Concrete, Hamilton, La Conner, Lyman, Mount Vernon, Sedro-Woolley*.
   * 2 Urban Growth Areas (UGAs): *Bay View Ridge UGA, Swinomish UGA*.
   * 1 Rural Balance: *Unincorporated Skagit County* (officially designated as "Rural (outside of UGAs)" under Skagit County Ordinance O20250002).
   * Geographic Coordinates: `Latitude` and `Longitude` centroids derived from official **USGS Geographic Names Information System (GNIS)** and **US Census Bureau 2020** municipal and UGA boundary centers.
2. **`Dim_CalendarYear` (1990–2045):**
   * Multi-decade calendar dimension categorized by GMA planning horizons (`Early GMA Foundation 1990-1999`, `Prior Comprehensive Cycle 2000-2019`, `Active GMA 20-Year Horizon 2020-2045`).
   * Flags: `Is_Historical`, `Is_Prototype_Year_2025`, `Is_Production_Year_2026`, `Is_Target_Year_2045`.
3. **`Dim_GMA_2045_Target`:**
   * Countywide Planning Policies (Ordinance O20250002) growth targets for 2045.
   * Baseline 2022 Population & 2045 Target (29,566 new residents regional allocation).
   * 2045 Net Housing Unit Allocations (17,450 net new units countywide).
   * Baseline 2022 Employment & 2045 Target (80,100 total jobs countywide).
4. **`Dim_CAI_Employment_Benchmark` (1999–2022):**
   * Historical benchmark series documenting WA ESD QCEW covered jobs alongside Nonemployer Statistics (Census NES) and the empirical self-employment multiplier (`1.15458`).

### Fact Tables (4 Tables)
1. **`Fact_Population`:** Official WA OFM April 1 population estimates (2010–2026).
2. **`Fact_HousingPermits`:** Historical building permit records (1990–2026) by structure type (Single-Family, Duplex, Multi-Family 3-4, 5+, ADUs), demolitions, net units, and construction valuation.
3. **`Fact_Employment`:** ESD QCEW covered jobs by NAICS sector (2025 Annual Revised & 2026 Q1 Preliminary), plus county total estimated employment.
4. **`Fact_Housing_AMI`:** 2025 residential unit production classified across Area Median Income (AMI) tiers (0-30%, 31-50%, 51-80%, 81-100%, >100% AMI).

---

## 5. Report Pages Structure (RF-02 4-Page Layout)

All canvas pages are locked to **16:9 widescreen (1280 x 720 px)** with high-contrast styling and dynamic metadata footers optimized for Board-Adopted PDF exports:

### Page 1: Executive Summary & Regional Dashboard
* **KPI Cards:** Regional Population (OFM), Net New Housing Units, ESD Covered Jobs (Official QCEW), and Housing Target Progress % (replaces unratified multiplier metrics).
* **Trajectory Chart:** 2010–2025 Population growth curve.
* **Typology Production Chart:** Single-Family vs. Multi-Family vs. ADU units.
* **Executive Summary Matrix:** All 11 jurisdictions compared against adopted GMA 2045 allocations for **Population and Housing only**. *(Employment target progress is deliberately omitted by jurisdiction because state QCEW confidentiality suppresses sub-county employment counts, supporting only county-level aggregates).*
* **Audit Footer:** Official attribution to OFM, ESD, and Skagit County Ordinance O20250002.

### Page 2: Housing Deep-Dive & AMI Analysis
* **Typology Slicers & KPIs:** Net New Units, Single-Family, Multi-Family, ADUs.
* **Long-Term Area Chart:** 1990–2025 residential permitting cycles.
* **Production Mix Donut Chart:** Housing breakdown proportions.
* **AMI Affordability Breakdown:** Production in low-income tiers (<80% AMI) vs. moderate/high income (>80% AMI). Prominently tagged as **"PRELIMINARY: Statewide default allocation"** pending delivery of certified local jurisdiction datasheets due October 20.
* **Target Progress Matrix:** Cumulative net units since 2020 vs. 2045 allocations.

### Page 3: Population & Employment Overview
* **Municipal Population Bar Chart:** Current population rank by jurisdiction.
* **Employment by Sector Bar Chart:** ESD covered employment across 2-digit NAICS industries.
* **Official ESD Covered Employment Line Chart:** Long-term historical trend (1999–2025) of official ESD covered employment. Total employment CAI multipliers are withheld and disclaimed as **"Pending methodology confirmation with SCOG staff"** per leadership instruction.
* **GMA Adopted Employment Target Table:** Ordinance O20250002 Table 3 baseline (2022) and adopted 2045 target allocations.

### Page 4: Jurisdictional Comparison & Spatial Mapping
* **Azure / Native Bubble Map:** Precise plotting of all 11 entities using centroid coordinates (`Latitude`, `Longitude`) from USGS GNIS and Census Bureau 2020.
* **Governance Comparison Matrix:** Incorporated Cities vs. UGAs vs. Unincorporated Rural Area ("Rural outside of UGAs" per Ordinance O20250002).
* **Growth Share Bar Chart:** Population share % vs. Housing production share % across Skagit County.

---

## 6. Schema Protection & Power Query Safeguards (RF-03)

To ensure that the reporting model never loads corrupted or drifted data, Power Query M expressions enforce strict column assertion:
```powerquery
Selected = Table.SelectColumns(Headers, {"Col1", "Col2", ...}, MissingField.Error)
```
* **Impact of `MissingField.Error`:** If any source column is misspelled, renamed, or omitted in incoming spreadsheets, Power BI halts the refresh immediately with an explicit error rather than silently populating nulls or breaking relationships.
* **Future Column Additions:** If new columns (such as `Methodology_Status`) are introduced to source sheets, they must be registered in the `Table.SelectColumns` definition in `generate_powerbi_prototype.py` and `power_query_m_scripts.pq`.

---

## 7. DAX Measure Library Overview

Measures are isolated in the dedicated `_Measures` table across five display folders:
* `01. Executive & Governance`: Dynamic titles, year slicer fallbacks, Board adoption banners, audit citations.
* `02. Population Growth & Targets`: YoY change, growth rates, GMA 2045 target progress %, remaining allocation capacity.
* `03. Housing Production & AMI`: Net units, typology sums, 2020-present cumulative production, % progress to 17,450 county target, AMI low-income splits.
* `04. Employment & CAI Methodology`: Covered employment, preliminary total jobs via CAI multiplier (quarantined to county total with disclaimers), wage averages.
* `05. Regional & Spatial Analysis`: Regional percentage shares for population and housing.

See [dax_measures.dax](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering\scog-growth-report\powerbi\dax_measures.dax) for full DAX expressions.
