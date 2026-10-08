# Validation: Rebuilt Templates vs. Star Schema Audit Files

Checked all four rebuilt templates (`Template_Population_Master.xlsx`, `Template_Housing_Permits_Master.xlsx`,
`Template_Housing_AMI_Master.xlsx`, `Template_Employment_Master.xlsx`) cell-by-cell against the matching
`Fact_*.csv` files from the star-schema package (`Dim_CalendarYear`, `Dim_GMA_2045_Target`, `Dim_Jurisdiction`,
`Fact_Employment`, `Fact_Housing_AMI`, `Fact_HousingPermits`, `Fact_Population`, and
`SCOG_Star_Schema_Data_Model.xlsx`).

## Result Summary

- **Population:** ✅ Exact match across all 22 rows (11 jurisdictions × 2025/2026).
- **Housing AMI:** ✅ Exact match across all 20 rows (4 cities × 5 structure types, 2025).
- **Employment:** ✅ Exact match across all 11 sector rows (establishments, annual average, and recomputed quarterly averages). The all-industries aggregate `TOTAL` row is a design choice present in the intake template and rolled up dynamically in Power BI.
- **Housing Permits:** ⚠️ Identified ADU vs Mobile Home labeling swap in the historical ETL script `etl_star_schema.py`. Resolved in branch `fix/star-schema-adu-mobile-home`.

### Detail of Housing Permits Resolution
- Raw OFM source (`ofm_april1_postcensal_permits_1990-present.xlsx`) column 16 represents `Permitted Accessory Dwelling units` (ADU), not Mobile Home.
- `etl_star_schema.py` was updated to map column 16 directly to `ADU_Units`, with `Mobile_Home_Units` set to 0.
- UGA valuation precision was refined from integer rounding to exact 2-decimal cents ($4,343,012.17 for Bay View Ridge and $32,637.35 for Swinomish UGA).
