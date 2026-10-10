# Skagit Council of Governments (SCOG) — Annual Growth Monitoring ETL & Star Schema

This subproject implements the automated ELT/ETL data pipeline and relational star schema model for SCOG's Annual Growth Monitoring Report (Option 1).

## Prerequisites & Data Setup

Raw source datasets are located in `data/raw/`.

> [!NOTE]
> Due to external data distribution policies, the draft employment benchmark model:
> `data/raw/CAI.Total Employment Calc Template DRAFT.2024 0206.xlsx`
> must be placed manually in `data/raw/` prior to running `etl_star_schema.py`.

## Pipeline Execution

To run the end-to-end pipeline and regenerate all processed tables and the master Excel workbook:

```bash
cd scog-growth-report
python etl_star_schema.py
```

### Outputs Generated in `data/processed/`:
1. `Dim_Jurisdiction.csv`
2. `Dim_CalendarYear.csv`
3. `Dim_GMA_2045_Target.csv`
4. `Dim_CAI_Employment_Benchmark.csv`
5. `Fact_Population.csv`
6. `Fact_HousingPermits.csv`
7. `Fact_Employment.csv`
8. `Fact_Housing_AMI.csv`
9. `SCOG_Star_Schema_Data_Model.xlsx` (Multi-tab master workbook formatted for Power BI Desktop ingestion)

## Population Accounting & UGA Methodology
- **OFM Unincorporated Accounting:** Washington State OFM's official unincorporated population estimate includes the Bay View Ridge and Swinomish Urban Growth Areas (UGAs).
- **Derived Rural Population:** The report presents "Unincorporated Rural (outside UGAs)" as a derived value (OFM unincorporated minus the two SAEP UGA population estimates, per year), pending formal SCOG confirmation.
- **ETL Additivity Assertions:** The ETL pipeline systematically asserts that for every year 2020–2026, incorporated cities + UGAs + derived rural population exactly equals the OFM official county total.

## Design v2 Internal Notes & Methodological Rules

The following notes are documented internally for the development team and excluded from client-visible UI elements:

1. **Employment Progress-to-Target Restriction:**
   - Washington State ESD QCEW data reflects covered wage and salary employment (59,571 jobs in 2022 baseline).
   - GMA 2045 employment targets (80,100 countywide jobs) represent long-range comprehensive planning allocations under SCOG Ordinance O20250002.
   - Because covered employment does not track comprehensive self-employed/uncovered sectors and annual actuals are not calibrated to GMA target categories, **no employment progress-to-target percentage or ratio (`employment ÷ target`) may be computed or displayed**. Baseline and target are presented as independent facts.

2. **Progress Tracking Methodology:**
   - **Housing Progress:** Measured as cumulative net permitted units from the start of the planning horizon (2020–2025) divided by the adopted 2045 housing target: $3,465 \div 17,450 = 19.9\%$.
   - **Population Progress:** Population growth is benchmarked against the 2022 baseline ($131,249 \to 134,600$, $+3,351$ net growth). Ratio-of-levels ($134,600 \div 160,830 = 83.7\%$) is avoided to prevent misleading comparison with the cumulative housing measure.

3. **Color Palette & Visual Tokens:**
   - Single primary accent color: `#004B87` (civic blue/slate).
   - All CSS color variables use neutral naming (`--slate-900`, `--slate-800`, etc., avoiding `--navy-*`).
   - `#004B87` serves as the primary visual accent token pending formal SCOG brand guideline delivery.

4. **HB 1220 Affordability (AMI) Reporting:**
   - Data in `Fact_Housing_AMI.csv` reflects preliminary reporting from Washington Department of Commerce datasheets (327 allocated units across reporting jurisdictions).
   - Client-visible text retains the explicit `[PRELIMINARY: Local Jurisdiction Housing Needs Assessments due Oct 20, 2026]` advisory notice.
