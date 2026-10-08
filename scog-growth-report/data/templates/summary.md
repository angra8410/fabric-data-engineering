# Template Rebuild Summary

All four requested templates — Population, Housing Permits, Housing AMI, and Employment Masters — have been rebuilt from the raw source files, with real control-total formulas, source-accurate rows, and Excel Tables. All formulas recalculate clean with zero errors (verified via LibreOffice recalc on each file).

**Two scope defaults I applied without an explicit answer from you** (flagged in my prior message, no reply received — proceeding on these, override if wrong):
1. **April-year reporting convention** used throughout (OFM's "Estimate Year" runs Apr 2–Apr 1), except Unincorporated county data for 2011–2019, which OFM's own readme says is calendar-year. The inference that the "2025" UGA permit file is really April 2024–March 2025 is unconfirmed by Skagit County — recommend confirming before this goes further.
2. **AMI tab**: since 2025 AMI datasheets aren't due until 10/20 and no local-adjusted data exists, I derived the tab from the WA Commerce "Exhibit 12" default methodology (documented in `HousingMethodologyTest.xlsx`) applied to the real 2025 permitted-unit counts, rather than leaving it blank. Every row is flagged `Default Allocation (WA Commerce Exhibit 12) — not a jurisdiction-verified split` so no one mistakes it for local data.

## Template_Population_Master.xlsx
- Replaced all 22 sample rows with real OFM April 1 population data (2025/2026) for the 8 cities + Unincorporated County, and real SAEP UGA estimates (data as of 17-Aug-26) for Bay View Ridge and Swinomish UGA — replacing the stale "Pending SAEP" placeholders.
- **Swinomish progress corrected**: was overstated ~16x in the original sample data (32.7% on an unverified 2026 figure); now computes to 2.0%/1.0% using real SAEP population and the existing `(F-J)/L` formula.
- **Fixed a formula bug**: jurisdictions with zero allocated 2045 growth (Hamilton, Lyman, Bay View Ridge — denominator L=0) now show `N/A` instead of a misleading `0%`.
- Baseline 2022 population and 2045 allocation targets (columns J/K) came from `Adopted_2045_GrowthProjections.xlsx` Table 1 and were already correct in the original template — unchanged.
- **Not attempted**: I could not reproduce the "corrected GMA progress" percentages quoted in the pasted review (e.g., Burlington 29.0%, Mount Vernon 6.7%) — I don't have enough information to verify what methodology produced those figures, and reverse-engineering a match without a verified source would mean fabricating a methodology. The rebuilt sheet instead uses the template's own documented formula with corrected inputs.

## Template_Housing_Permits_Master.xlsx
- City + Unincorporated County rows (2024 and 2025) now use real permitted/completed/demolished unit counts from `ofm_april1_postcensal_permits_1990-present.xlsx`.
- Bay View Ridge UGA (2025) and Swinomish UGA (2025) rows computed directly from the deduplicated `UGA_Dev_Permits_2025.csv`: **12 single-family permits, $4,343,012.17 total valuation** for Bay View Ridge (confirms the pasted review's $4.34M exactly) — the original template's ADU=1/$6.2M figures didn't match anything in the source data. Swinomish UGA shows 0 new units — all 5 of its permits are additions/alterations to existing structures, not new construction.
- **Gap, not filled**: no 2024 UGA-level source file was provided, so I did not add 2024 Bay View Ridge/Swinomish rows (the original template had fabricated placeholder values there) — left out rather than guessed.
- **Total_Valuation_USD is blank for all city/county rows**: the OFM permits source has no valuation column; only the UGA permit log does. I did not fabricate city-level valuation figures.
- Mobile_Home_Units = 0 throughout — not tracked in the only available source.

## Template_Housing_AMI_Master.xlsx
- Rebuilt for the 4 cities with permit data (Anacortes, Burlington, Mount Vernon, Sedro-Woolley), 2025, using the real permitted-unit counts from the rebuilt Housing Permits Master, allocated 100% to a single AMI tier per structure type, per WA Commerce Exhibit 12 methodology: 1-unit → 120%+, 2-unit & 3-4 unit → 101–120%, 5+ unit & ADU → 81–100%.
- This replaces the original sample rows, which spread units across multiple tiers in a way that contradicted the documented methodology and didn't reconcile to any real permit count.
- Every row's `Reconciliation_Status` states plainly this is the statewide default allocation, not a jurisdiction-verified split — real local data isn't due until 10/20.

## Template_Employment_Master.xlsx
- Rebuilt from `2025-QCEW-annual-averages-revisedSkagit_County.csv` (12 sector rows: Total, Agriculture, Crop Production, Animal Production, Construction, Manufacturing, Retail, Healthcare, Accommodation, and Federal/State/Local Government) plus a parallel set of 2026 Q1 preliminary rows from `2026Q1-QCEW-preliminary.csv`.
- **No "Public Administration" / NAICS 92 row** — the raw ESD data has no such row; replaced with the three real Government breakdown rows (Federal/State/Local), as the review found.
- **Fixed the Q2–Q4 and Annual_Average_Employment errors** the review flagged: every original sample row's Q2/Q3/Q4 and annual-average figures were wrong, including the TOTAL row (template had 54,510/54,220/53,740/53,850; correct quarterly averages of the raw monthly data are 54,910/55,213/53,539, annual average 54,148). All values here are computed directly from the monthly columns (Q = average of that quarter's 3 months), not copied from any prior draft.
- None of the 12 rows I included are ESD-suppressed (`*`); I did not need to build null-handling for this subset, though the raw files do have 21 (annual) and 18 (Q1) suppressed rows elsewhere if the sector list is ever expanded.
- `YoY_Employment_Change` is now a live `SUMIFS`-based lookup formula (matches prior calendar year by NAICS code), not a hardcoded 0. It correctly returns "No Prior-Year Data" for every row here, because no 2024 QCEW file was provided to this task — it is not silently showing a false zero.
- 2026 rows are explicitly partial: Annual_Average_Employment and Q2–Q4 are blank (not available), `Data_Release_Status` = "Preliminary — Q1 Only."

## Still unverifiable (per the pasted review, unchanged)
I don't have the star schema, ETL script, commit hash, or orphan-key results for how these templates feed into the actual Power BI/Fabric pipeline — only the templates and raw source files were provided here, so I can't confirm the pipeline consumes these rebuilt files correctly. The hours-workbook reconciliation mentioned in the pasted transcript was not part of this task and was not attempted.

## Recommended before these go further
1. Confirm the April-year vs. calendar-year reporting convention with Skagit County.
2. Confirm whether the Bay View Ridge/Swinomish UGA permit log (county-issued) should be combined with or kept separate from OFM's city/Unincorporated permit counts — I kept them as separate rows to avoid double-counting, consistent with the original template's design, but this wasn't explicitly confirmed.
3. Swap in real local AMI data once the 10/20 datasheets arrive — the current AMI tab is a defensible placeholder, not final data.
