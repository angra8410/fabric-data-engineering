/*
========================================================================================
SCOG ANNUAL GROWTH MONITORING REPORT — POWER QUERY (M) INGESTION SCRIPTS
Source Workbook: C:/SCOG_Data/SCOG_Star_Schema_Data_Model.xlsx
Schema: Star Schema (4 Dimensions, 4 Facts, 1 Parameter)
========================================================================================
*/

// PARAMETER: SourceWorkbookPath
let SourceWorkbookPath = "C:/SCOG_Data/SCOG_Star_Schema_Data_Model.xlsx" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true] in SourceWorkbookPath

// DIMENSION: Dim_Jurisdiction
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Dim_Jurisdiction",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Jurisdiction_ID", "Jurisdiction_Name", "Jurisdiction_Type", "Is_Incorporated", "Is_UGA", "Latitude", "Longitude", "County_Name", "State"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Jurisdiction_ID", type text}, {"Jurisdiction_Name", type text}, {"Jurisdiction_Type", type text},
        {"Is_Incorporated", Int64.Type}, {"Is_UGA", Int64.Type},
        {"Latitude", type number}, {"Longitude", type number},
        {"County_Name", type text}, {"State", type text}
    })
in
    Typed

// DIMENSION: Dim_CalendarYear
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Dim_CalendarYear",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Year", "Decade", "GMA_Planning_Cycle", "Is_Historical", "Is_Prototype_Year_2025", "Is_Production_Year_2026", "Is_Target_Year_2045"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Year", Int64.Type}, {"Decade", type text}, {"GMA_Planning_Cycle", type text},
        {"Is_Historical", Int64.Type}, {"Is_Prototype_Year_2025", Int64.Type},
        {"Is_Production_Year_2026", Int64.Type}, {"Is_Target_Year_2045", Int64.Type}
    })
in
    Typed

// DIMENSION: Dim_GMA_2045_Target
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Dim_GMA_2045_Target",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Jurisdiction_ID", "Jurisdiction_Name", "Jurisdiction_Type", "Baseline_2022_Population", "Target_2045_Population", "Projected_2045_Population_Growth", "Population_Growth_Share_Pct", "Target_2045_Housing_Units", "Baseline_2022_Employment", "Target_2045_Employment", "Projected_2045_Employment_Growth", "Employment_Growth_Share_Pct", "CAI_Self_Employment_Multiplier", "Data_Source"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Jurisdiction_ID", type text}, {"Jurisdiction_Name", type text}, {"Jurisdiction_Type", type text},
        {"Baseline_2022_Population", Int64.Type}, {"Target_2045_Population", Int64.Type},
        {"Projected_2045_Population_Growth", Int64.Type}, {"Population_Growth_Share_Pct", type number},
        {"Target_2045_Housing_Units", Int64.Type}, {"Baseline_2022_Employment", Int64.Type},
        {"Target_2045_Employment", Int64.Type}, {"Projected_2045_Employment_Growth", Int64.Type},
        {"Employment_Growth_Share_Pct", type number}, {"CAI_Self_Employment_Multiplier", type number},
        {"Data_Source", type text}
    })
in
    Typed

// DIMENSION: Dim_CAI_Employment_Benchmark
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Dim_CAI_Employment_Benchmark",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Benchmark_Key", "Year", "Covered_Employment_QCEW", "Self_Employment_NES", "Total_Employment_Combined", "Self_Employment_Ratio", "Ratio_Average_All_Years", "Ratio_Average_Last_10_Obs", "Is_Observed", "Data_Source"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Benchmark_Key", type text}, {"Year", Int64.Type},
        {"Covered_Employment_QCEW", Int64.Type}, {"Self_Employment_NES", Int64.Type},
        {"Total_Employment_Combined", Int64.Type}, {"Self_Employment_Ratio", type number},
        {"Ratio_Average_All_Years", type number}, {"Ratio_Average_Last_10_Obs", type number},
        {"Is_Observed", Int64.Type}, {"Data_Source", type text}
    })
in
    Typed

// FACT: Fact_Population
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Fact_Population",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Fact_Population_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Population_Count", "Prior_Year_Population", "YoY_Population_Change", "YoY_Growth_Rate_Pct", "Data_Source_Type"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Fact_Population_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},
        {"Jurisdiction_Name", type text}, {"Population_Count", Int64.Type},
        {"Prior_Year_Population", Int64.Type}, {"YoY_Population_Change", Int64.Type},
        {"YoY_Growth_Rate_Pct", type number}, {"Data_Source_Type", type text}
    })
in
    Typed

// FACT: Fact_HousingPermits
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Fact_HousingPermits",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Fact_Housing_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Single_Family_Units", "Duplex_Units", "MultiFamily_3_4_Units", "MultiFamily_5_Plus_Units", "ADU_Units", "Mobile_Home_Units", "Total_Permitted_Units", "Completed_Units", "Demolished_Units", "Net_New_Units", "Total_Valuation_USD", "Data_Source"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Fact_Housing_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},
        {"Jurisdiction_Name", type text}, {"Single_Family_Units", Int64.Type},
        {"Duplex_Units", Int64.Type}, {"MultiFamily_3_4_Units", Int64.Type},
        {"MultiFamily_5_Plus_Units", Int64.Type}, {"ADU_Units", Int64.Type},
        {"Mobile_Home_Units", Int64.Type}, {"Total_Permitted_Units", Int64.Type},
        {"Completed_Units", Int64.Type}, {"Demolished_Units", Int64.Type},
        {"Net_New_Units", Int64.Type}, {"Total_Valuation_USD", Int64.Type},
        {"Data_Source", type text}
    })
in
    Typed

// FACT: Fact_Employment
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Fact_Employment",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Fact_Employment_Key", "Year", "Period_Type", "Industry_Key", "Row_Level", "Parent_2Digit_Code", "NAICS_2Digit_Code", "NAICS_3Digit_Code", "Industry_Subsector_Title", "Title_As_Reported", "Is_County_Total", "Is_Suppressed", "Average_Establishments", "Annual_Average_Employment", "Q1_Average_Employment", "Estimated_Total_Employment", "Estimated_Total_Employment_Q1", "CAI_Self_Employment_Multiplier", "Average_Annual_Wage_USD", "Data_Status"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Fact_Employment_Key", type text}, {"Year", Int64.Type}, {"Period_Type", type text},
        {"Industry_Key", type text}, {"Row_Level", type text}, {"Parent_2Digit_Code", type text},
        {"NAICS_2Digit_Code", type text}, {"NAICS_3Digit_Code", type text},
        {"Industry_Subsector_Title", type text}, {"Title_As_Reported", type text},
        {"Is_County_Total", Int64.Type}, {"Is_Suppressed", Int64.Type},
        {"Average_Establishments", Int64.Type}, {"Annual_Average_Employment", Int64.Type},
        {"Q1_Average_Employment", Int64.Type}, {"Estimated_Total_Employment", Int64.Type},
        {"Estimated_Total_Employment_Q1", Int64.Type}, {"CAI_Self_Employment_Multiplier", type number},
        {"Average_Annual_Wage_USD", Int64.Type}, {"Data_Status", type text}
    })
in
    Typed

// FACT: Fact_Housing_AMI
let
    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),
    Sheet = Source{[Item="Fact_Housing_AMI",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    Selected = Table.SelectColumns(Headers, {"Fact_AMI_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Structure_Type", "AMI_0_to_30_Pct_Units", "AMI_31_to_50_Pct_Units", "AMI_51_to_80_Pct_Units", "AMI_81_to_100_Pct_Units", "AMI_101_to_120_Pct_Units", "AMI_Greater_120_Pct_Units", "Total_AMI_Units", "Reconciliation_Status"}, MissingField.Error),
    Typed = Table.TransformColumnTypes(Selected,{
        {"Fact_AMI_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},
        {"Jurisdiction_Name", type text}, {"Structure_Type", type text},
        {"AMI_0_to_30_Pct_Units", Int64.Type}, {"AMI_31_to_50_Pct_Units", Int64.Type},
        {"AMI_51_to_80_Pct_Units", Int64.Type}, {"AMI_81_to_100_Pct_Units", Int64.Type},
        {"AMI_101_to_120_Pct_Units", Int64.Type}, {"AMI_Greater_120_Pct_Units", Int64.Type},
        {"Total_AMI_Units", Int64.Type}, {"Reconciliation_Status", type text}
    })
in
    Typed