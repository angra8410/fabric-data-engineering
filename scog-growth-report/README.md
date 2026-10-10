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
