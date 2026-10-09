"""
Generator script for SCOG Annual Growth Monitoring Report Power BI Project (PBIP).
Creates the complete .pbip artifact, semantic model (model.bim), report layout (report.json),
theme (scog_theme.json), standalone DAX formulas, and Power Query M scripts.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POWERBI_DIR = os.path.join(BASE_DIR, "powerbi")
REPORT_NAME = "SCOG_Growth_Monitoring_Report"
PBIP_ROOT = os.path.join(POWERBI_DIR, REPORT_NAME)
SEMANTIC_DIR = os.path.join(PBIP_ROOT, f"{REPORT_NAME}.SemanticModel")
REPORT_DIR = os.path.join(PBIP_ROOT, f"{REPORT_NAME}.Report")

DATA_WORKBOOK_PATH = "C:/SCOG_Data/SCOG_Star_Schema_Data_Model.xlsx"


def build_pbip():
    os.makedirs(POWERBI_DIR, exist_ok=True)
    os.makedirs(PBIP_ROOT, exist_ok=True)
    os.makedirs(SEMANTIC_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    # 1. Root .pbip file
    pbip_def = {
        "version": "1.0",
        "artifacts": [
            {
                "report": {
                    "path": f"{REPORT_NAME}.Report"
                }
            }
        ],
        "settings": {}
    }
    with open(os.path.join(PBIP_ROOT, f"{REPORT_NAME}.pbip"), "w", encoding="utf-8") as f:
        json.dump(pbip_def, f, indent=2)

    # 2. SemanticModel definition.pbism
    pbism_def = {
        "version": "1.0",
        "settings": {}
    }
    with open(os.path.join(SEMANTIC_DIR, "definition.pbism"), "w", encoding="utf-8") as f:
        json.dump(pbism_def, f, indent=2)

    # 3. Report definition.pbir
    pbir_def = {
        "version": "1.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{REPORT_NAME}.SemanticModel"
            }
        }
    }
    with open(os.path.join(REPORT_DIR, "definition.pbir"), "w", encoding="utf-8") as f:
        json.dump(pbir_def, f, indent=2)

    # 4. Custom SCOG Theme JSON
    scog_theme = {
        "name": "SCOG Civic High-Contrast Theme",
        "dataColors": [
            "#004B87",  # SCOG Primary Deep Blue
            "#008080",  # Puget Sound Teal
            "#2E7D32",  # Evergreen Forest Green
            "#C0392B",  # High-Contrast Target Crimson
            "#D97706",  # GMA Planning Amber
            "#6B21A8",  # Royal Violet
            "#1E293B",  # Dark Slate
            "#0891B2"   # Electric Sky
        ],
        "background": "#FFFFFF",
        "foreground": "#1E293B",
        "tableAccent": "#004B87",
        "visualStyles": {
            "*": {
                "*": {
                    "fontFamily": [{"family": "Segoe UI Semibold"}],
                    "fontSize": [{"val": 10}],
                    "title": [{
                        "show": True,
                        "fontColor": {"solid": {"color": "#0F172A"}},
                        "fontSize": 12,
                        "fontFamily": "Segoe UI",
                        "bold": True
                    }],
                    "background": [{
                        "show": True,
                        "color": {"solid": {"color": "#FFFFFF"}},
                        "transparency": 0
                    }],
                    "border": [{
                        "show": True,
                        "color": {"solid": {"color": "#E2E8F0"}},
                        "radius": 4
                    }]
                }
            },
            "card": {
                "*": {
                    "labels": [{
                        "color": {"solid": {"color": "#004B87"}},
                        "fontSize": 26,
                        "fontFamily": "Segoe UI Bold"
                    }],
                    "categoryLabels": [{
                        "show": True,
                        "color": {"solid": {"color": "#475569"}},
                        "fontSize": 9
                    }]
                }
            }
        }
    }
    with open(os.path.join(POWERBI_DIR, "scog_theme.json"), "w", encoding="utf-8") as f:
        json.dump(scog_theme, f, indent=2)

    # 5. Semantic Model (model.bim)
    model_bim = build_model_bim(DATA_WORKBOOK_PATH)
    with open(os.path.join(SEMANTIC_DIR, "model.bim"), "w", encoding="utf-8") as f:
        json.dump(model_bim, f, indent=2)

    # 6. Report Layout (report.json)
    report_json = build_report_json()
    with open(os.path.join(REPORT_DIR, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    # 7. Standalone DAX measures file
    build_dax_file()

    # 8. Standalone Power Query M file
    build_power_query_file(DATA_WORKBOOK_PATH)

    print("All Power BI artifacts generated successfully!")


def build_model_bim(workbook_path):
    escaped_path = workbook_path.replace('"', '""')

    measures = [
        # Executive & Governance
        {
            "name": "Selected Reporting Year",
            "expression": "COALESCE(SELECTEDVALUE(Dim_CalendarYear[Year]), 2025)",
            "formatString": "0",
            "displayFolder": "01. Executive & Governance",
            "description": "Currently filtered calendar year, defaulting to prototype baseline 2025."
        },
        {
            "name": "Selected Jurisdiction",
            "expression": 'SELECTEDVALUE(Dim_Jurisdiction[Jurisdiction_Name], "All Skagit County Jurisdictions")',
            "displayFolder": "01. Executive & Governance",
            "description": "Selected jurisdiction name or countywide indicator."
        },
        {
            "name": "Report Adoption Status Banner",
            "expression": 'VAR CurrentYr = [Selected Reporting Year]\nRETURN\nIF(CurrentYr <= 2024, "BOARD ADOPTED (Official Legal Record)", IF(CurrentYr = 2025, "PROTOTYPE 2025 (Prior-Year Historical Calibration)", "PRELIMINARY 2026 (Under Review / Draft)"))',
            "displayFolder": "01. Executive & Governance",
            "description": "Dynamic governance status indicator for Board adoption review."
        },
        {
            "name": "Metadata Footer Notice",
            "expression": '"Data Sources: WA Office of Financial Management (OFM) | Employment Security Department (ESD QCEW) | Skagit County GMA Allocations (Ordinance O20250002) | SCOG Annual Growth Monitoring Report"',
            "displayFolder": "01. Executive & Governance",
            "description": "Standardized audit attribution footer text required for Board PDF exports."
        },

        # Population
        {
            "name": "Total Population",
            "expression": "SUM(Fact_Population[Population_Count])",
            "formatString": "#,##0",
            "displayFolder": "02. Population Growth & Targets",
            "description": "Total official population estimate from OFM April 1."
        },
        {
            "name": "Prior Year Population",
            "expression": "CALCULATE([Total Population], SAMEPERIODLASTYEAR(Dim_CalendarYear[Year]))",
            "formatString": "#,##0",
            "displayFolder": "02. Population Growth & Targets",
            "description": "Population count in the prior calendar year."
        },
        {
            "name": "YoY Population Change",
            "expression": "SUM(Fact_Population[YoY_Population_Change])",
            "formatString": "+#,##0;-#,##0;0",
            "displayFolder": "02. Population Growth & Targets",
            "description": "Net annual population change relative to prior year."
        },
        {
            "name": "YoY Population Growth %",
            "expression": "DIVIDE([YoY Population Change], [Prior Year Population], 0)",
            "formatString": "0.00%",
            "displayFolder": "02. Population Growth & Targets",
            "description": "Annual percentage growth rate of population."
        },
        {
            "name": "2022 Population Baseline",
            "expression": "SUM(Dim_GMA_2045_Target[Baseline_2022_Population])",
            "formatString": "#,##0",
            "displayFolder": "02. Population Growth & Targets",
            "description": "GMA adopted 2022 baseline population from Ordinance O20250002."
        },
        {
            "name": "2045 Population Target",
            "expression": "SUM(Dim_GMA_2045_Target[Target_2045_Population])",
            "formatString": "#,##0",
            "displayFolder": "02. Population Growth & Targets",
            "description": "GMA 2045 adopted population growth target allocation."
        },
        {
            "name": "Projected 2045 Population Growth",
            "expression": "SUM(Dim_GMA_2045_Target[Projected_2045_Population_Growth])",
            "formatString": "#,##0",
            "displayFolder": "02. Population Growth & Targets",
            "description": "Total growth allocation from 2022 to 2045."
        },
        {
            "name": "Population Growth Toward 2045 Target %",
            "expression": "VAR CurrentPop = [Total Population]\nVAR BasePop = [2022 Population Baseline]\nVAR TargetGain = [Projected 2045 Population Growth]\nRETURN\nIF(TargetGain > 0, DIVIDE(CurrentPop - BasePop, TargetGain, 0), BLANK())",
            "formatString": "0.0%",
            "displayFolder": "02. Population Growth & Targets",
            "description": "Percentage progress toward achieving the 2045 GMA population allocation."
        },
        {
            "name": "Remaining Population Capacity to 2045",
            "expression": "[2045 Population Target] - [Total Population]",
            "formatString": "#,##0",
            "displayFolder": "02. Population Growth & Targets",
            "description": "Remaining population growth allocation until 2045 target."
        },

        # Housing
        {
            "name": "Total Housing Permits",
            "expression": "SUM(Fact_HousingPermits[Total_Permitted_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Total residential units permitted in reporting period."
        },
        {
            "name": "Single-Family Permits",
            "expression": "SUM(Fact_HousingPermits[Single_Family_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Detached single-family residential permitted units."
        },
        {
            "name": "Multi-Family Permits",
            "expression": "SUM(Fact_HousingPermits[Duplex_Units]) + SUM(Fact_HousingPermits[MultiFamily_3_4_Units]) + SUM(Fact_HousingPermits[MultiFamily_5_Plus_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Total multi-family permitted units (Duplex + 3-4 units + 5+ units)."
        },
        {
            "name": "ADU Permits",
            "expression": "SUM(Fact_HousingPermits[ADU_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Permitted Accessory Dwelling Units."
        },
        {
            "name": "Demolished Units",
            "expression": "SUM(Fact_HousingPermits[Demolished_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Residential units demolished during reporting period."
        },
        {
            "name": "Net New Housing Units",
            "expression": "SUM(Fact_HousingPermits[Net_New_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Net new residential units (Total Permitted minus Demolitions)."
        },
        {
            "name": "Total Permit Valuation",
            "expression": "SUM(Fact_HousingPermits[Total_Valuation_USD])",
            "formatString": "$#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Permit construction valuation in US Dollars."
        },
        {
            "name": "2045 Housing Target Units",
            "expression": "SUM(Dim_GMA_2045_Target[Target_2045_Housing_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "GMA adopted net housing unit allocation 2020-2045 (17,450 countywide)."
        },
        {
            "name": "Cumulative Net Housing Units (2020-Present)",
            "expression": "CALCULATE([Net New Housing Units], FILTER(ALL(Dim_CalendarYear), Dim_CalendarYear[Year] >= 2020 && Dim_CalendarYear[Year] <= MAX(Dim_CalendarYear[Year])))",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Cumulative net new housing units added since GMA planning baseline 2020."
        },
        {
            "name": "Housing Target Progress %",
            "expression": "DIVIDE([Cumulative Net Housing Units (2020-Present)], [2045 Housing Target Units], 0)",
            "formatString": "0.0%",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Percentage progress of cumulative housing production against 2045 GMA target."
        },
        {
            "name": "Low Income AMI Units (<80% AMI)",
            "expression": "SUM(Fact_Housing_AMI[AMI_0_to_30_Pct_Units]) + SUM(Fact_Housing_AMI[AMI_31_to_50_Pct_Units]) + SUM(Fact_Housing_AMI[AMI_51_to_80_Pct_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Housing units serving households below 80% of Area Median Income."
        },
        {
            "name": "Moderate to High Income AMI Units (>80% AMI)",
            "expression": "SUM(Fact_Housing_AMI[AMI_81_to_100_Pct_Units]) + SUM(Fact_Housing_AMI[AMI_101_to_120_Pct_Units]) + SUM(Fact_Housing_AMI[AMI_Greater_120_Pct_Units])",
            "formatString": "#,##0",
            "displayFolder": "03. Housing Production & AMI",
            "description": "Housing units serving households at or above 80% Area Median Income."
        },

        # Employment
        {
            "name": "Covered Employment QCEW",
            "expression": "CALCULATE(SUM(Fact_Employment[Annual_Average_Employment]), Fact_Employment[Is_County_Total] = 1)",
            "formatString": "#,##0",
            "displayFolder": "04. Employment & CAI Methodology",
            "description": "Annual average covered employment from ESD QCEW (County Total)."
        },
        {
            "name": "Estimated Total Employment (CAI Multiplier)",
            "expression": "CALCULATE(SUM(Fact_Employment[Estimated_Total_Employment]), Fact_Employment[Is_County_Total] = 1)",
            "formatString": "#,##0",
            "displayFolder": "04. Employment & CAI Methodology",
            "description": "Estimated total employment including non-employer proprietors (CAI multiplier 1.15458)."
        },
        {
            "name": "2022 Employment Baseline",
            "expression": "SUM(Dim_GMA_2045_Target[Baseline_2022_Employment])",
            "formatString": "#,##0",
            "displayFolder": "04. Employment & CAI Methodology",
            "description": "GMA adopted 2022 employment baseline (59,571 jobs countywide)."
        },
        {
            "name": "2045 Employment Target",
            "expression": "SUM(Dim_GMA_2045_Target[Target_2045_Employment])",
            "formatString": "#,##0",
            "displayFolder": "04. Employment & CAI Methodology",
            "description": "GMA adopted 2045 total employment target (80,100 jobs countywide)."
        },
        {
            "name": "Total Establishments",
            "expression": "CALCULATE(SUM(Fact_Employment[Average_Establishments]), Fact_Employment[Is_County_Total] = 1)",
            "formatString": "#,##0",
            "displayFolder": "04. Employment & CAI Methodology",
            "description": "Total employer establishments active in Skagit County."
        },
        {
            "name": "Average Annual Wage USD",
            "expression": "CALCULATE(AVERAGE(Fact_Employment[Average_Annual_Wage_USD]), Fact_Employment[Is_County_Total] = 1)",
            "formatString": "$#,##0",
            "displayFolder": "04. Employment & CAI Methodology",
            "description": "Average annual covered wage per worker in US Dollars."
        },

        # Regional & Spatial
        {
            "name": "Jurisdiction Share of Regional Population %",
            "expression": "VAR RegionalPop = CALCULATE([Total Population], ALL(Dim_Jurisdiction))\nRETURN\nDIVIDE([Total Population], RegionalPop, 0)",
            "formatString": "0.0%",
            "displayFolder": "05. Regional & Spatial Analysis",
            "description": "Jurisdiction percentage share of total Skagit County population."
        },
        {
            "name": "Jurisdiction Share of Regional Housing %",
            "expression": "VAR RegionalHousing = CALCULATE([Net New Housing Units], ALL(Dim_Jurisdiction))\nRETURN\nDIVIDE([Net New Housing Units], RegionalHousing, 0)",
            "formatString": "0.0%",
            "displayFolder": "05. Regional & Spatial Analysis",
            "description": "Jurisdiction percentage share of total net residential units built."
        }
    ]

    model = {
        "name": "SCOG_Growth_Monitoring_Report",
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True
            },
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "expressions": [
                {
                    "name": "SourceWorkbookPath",
                    "kind": "m",
                    "expression": f'"{escaped_path}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
                    "description": "File path to the master processed star schema Excel workbook."
                }
            ],
            "tables": [
                {
                    "name": "_Measures",
                    "description": "Central repository for calculated DAX business logic and KPI metrics.",
                    "columns": [
                        {
                            "name": "Measure_Group",
                            "dataType": "string",
                            "isHidden": True,
                            "sourceColumn": "Measure_Group"
                        }
                    ],
                    "partitions": [
                        {
                            "name": "_Measures",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = #table({"Measure_Group"}, {{"SCOG Growth Metrics"}})\nin\n    Source'
                            }
                        }
                    ],
                    "measures": measures
                },
                {
                    "name": "Dim_Jurisdiction",
                    "description": "Official municipal, UGA, and rural entities within Skagit County.",
                    "columns": [
                        {"name": "Jurisdiction_ID", "dataType": "string", "sourceColumn": "Jurisdiction_ID", "isKey": True},
                        {"name": "Jurisdiction_Name", "dataType": "string", "sourceColumn": "Jurisdiction_Name", "dataCategory": "City"},
                        {"name": "Jurisdiction_Type", "dataType": "string", "sourceColumn": "Jurisdiction_Type"},
                        {"name": "Is_Incorporated", "dataType": "int64", "sourceColumn": "Is_Incorporated"},
                        {"name": "Is_UGA", "dataType": "int64", "sourceColumn": "Is_UGA"},
                        {"name": "Latitude", "dataType": "double", "sourceColumn": "Latitude", "dataCategory": "Latitude"},
                        {"name": "Longitude", "dataType": "double", "sourceColumn": "Longitude", "dataCategory": "Longitude"},
                        {"name": "County_Name", "dataType": "string", "sourceColumn": "County_Name", "dataCategory": "County"},
                        {"name": "State", "dataType": "string", "sourceColumn": "State", "dataCategory": "StateOrProvince"}
                    ],
                    "partitions": [
                        {
                            "name": "Dim_Jurisdiction",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Dim_Jurisdiction",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Jurisdiction_ID", "Jurisdiction_Name", "Jurisdiction_Type", "Is_Incorporated", "Is_UGA", "Latitude", "Longitude", "County_Name", "State"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Jurisdiction_ID", type text}, {"Jurisdiction_Name", type text}, {"Jurisdiction_Type", type text},\n        {"Is_Incorporated", Int64.Type}, {"Is_UGA", Int64.Type},\n        {"Latitude", type number}, {"Longitude", type number},\n        {"County_Name", type text}, {"State", type text}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                },
                {
                    "name": "Dim_CalendarYear",
                    "description": "Standardized calendar dimension spanning 1990 to 2045 GMA planning horizon.",
                    "columns": [
                        {"name": "Year", "dataType": "int64", "sourceColumn": "Year", "isKey": True},
                        {"name": "Decade", "dataType": "string", "sourceColumn": "Decade"},
                        {"name": "GMA_Planning_Cycle", "dataType": "string", "sourceColumn": "GMA_Planning_Cycle"},
                        {"name": "Is_Historical", "dataType": "int64", "sourceColumn": "Is_Historical"},
                        {"name": "Is_Prototype_Year_2025", "dataType": "int64", "sourceColumn": "Is_Prototype_Year_2025"},
                        {"name": "Is_Production_Year_2026", "dataType": "int64", "sourceColumn": "Is_Production_Year_2026"},
                        {"name": "Is_Target_Year_2045", "dataType": "int64", "sourceColumn": "Is_Target_Year_2045"}
                    ],
                    "partitions": [
                        {
                            "name": "Dim_CalendarYear",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Dim_CalendarYear",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Year", "Decade", "GMA_Planning_Cycle", "Is_Historical", "Is_Prototype_Year_2025", "Is_Production_Year_2026", "Is_Target_Year_2045"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Year", Int64.Type}, {"Decade", type text}, {"GMA_Planning_Cycle", type text},\n        {"Is_Historical", Int64.Type}, {"Is_Prototype_Year_2025", Int64.Type},\n        {"Is_Production_Year_2026", Int64.Type}, {"Is_Target_Year_2045", Int64.Type}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                },
                {
                    "name": "Dim_GMA_2045_Target",
                    "description": "Formally adopted Countywide Planning Policies growth targets (Ordinance O20250002).",
                    "columns": [
                        {"name": "Jurisdiction_ID", "dataType": "string", "sourceColumn": "Jurisdiction_ID"},
                        {"name": "Jurisdiction_Name", "dataType": "string", "sourceColumn": "Jurisdiction_Name"},
                        {"name": "Jurisdiction_Type", "dataType": "string", "sourceColumn": "Jurisdiction_Type"},
                        {"name": "Baseline_2022_Population", "dataType": "int64", "sourceColumn": "Baseline_2022_Population"},
                        {"name": "Target_2045_Population", "dataType": "int64", "sourceColumn": "Target_2045_Population"},
                        {"name": "Projected_2045_Population_Growth", "dataType": "int64", "sourceColumn": "Projected_2045_Population_Growth"},
                        {"name": "Population_Growth_Share_Pct", "dataType": "double", "sourceColumn": "Population_Growth_Share_Pct"},
                        {"name": "Target_2045_Housing_Units", "dataType": "int64", "sourceColumn": "Target_2045_Housing_Units"},
                        {"name": "Baseline_2022_Employment", "dataType": "int64", "sourceColumn": "Baseline_2022_Employment"},
                        {"name": "Target_2045_Employment", "dataType": "int64", "sourceColumn": "Target_2045_Employment"},
                        {"name": "Projected_2045_Employment_Growth", "dataType": "int64", "sourceColumn": "Projected_2045_Employment_Growth"},
                        {"name": "Employment_Growth_Share_Pct", "dataType": "double", "sourceColumn": "Employment_Growth_Share_Pct"},
                        {"name": "CAI_Self_Employment_Multiplier", "dataType": "double", "sourceColumn": "CAI_Self_Employment_Multiplier"},
                        {"name": "Data_Source", "dataType": "string", "sourceColumn": "Data_Source"}
                    ],
                    "partitions": [
                        {
                            "name": "Dim_GMA_2045_Target",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Dim_GMA_2045_Target",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Jurisdiction_ID", "Jurisdiction_Name", "Jurisdiction_Type", "Baseline_2022_Population", "Target_2045_Population", "Projected_2045_Population_Growth", "Population_Growth_Share_Pct", "Target_2045_Housing_Units", "Baseline_2022_Employment", "Target_2045_Employment", "Projected_2045_Employment_Growth", "Employment_Growth_Share_Pct", "CAI_Self_Employment_Multiplier", "Data_Source"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Jurisdiction_ID", type text}, {"Jurisdiction_Name", type text}, {"Jurisdiction_Type", type text},\n        {"Baseline_2022_Population", Int64.Type}, {"Target_2045_Population", Int64.Type},\n        {"Projected_2045_Population_Growth", Int64.Type}, {"Population_Growth_Share_Pct", type number},\n        {"Target_2045_Housing_Units", Int64.Type}, {"Baseline_2022_Employment", Int64.Type},\n        {"Target_2045_Employment", Int64.Type}, {"Projected_2045_Employment_Growth", Int64.Type},\n        {"Employment_Growth_Share_Pct", type number}, {"CAI_Self_Employment_Multiplier", type number},\n        {"Data_Source", type text}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                },
                {
                    "name": "Dim_CAI_Employment_Benchmark",
                    "description": "CAI Total Employment Calculation historical series (1999-2022) with QCEW and NES.",
                    "columns": [
                        {"name": "Benchmark_Key", "dataType": "string", "sourceColumn": "Benchmark_Key", "isKey": True},
                        {"name": "Year", "dataType": "int64", "sourceColumn": "Year"},
                        {"name": "Covered_Employment_QCEW", "dataType": "int64", "sourceColumn": "Covered_Employment_QCEW"},
                        {"name": "Self_Employment_NES", "dataType": "int64", "sourceColumn": "Self_Employment_NES"},
                        {"name": "Total_Employment_Combined", "dataType": "int64", "sourceColumn": "Total_Employment_Combined"},
                        {"name": "Self_Employment_Ratio", "dataType": "double", "sourceColumn": "Self_Employment_Ratio"},
                        {"name": "Ratio_Average_All_Years", "dataType": "double", "sourceColumn": "Ratio_Average_All_Years"},
                        {"name": "Ratio_Average_Last_10_Obs", "dataType": "double", "sourceColumn": "Ratio_Average_Last_10_Obs"},
                        {"name": "Is_Observed", "dataType": "int64", "sourceColumn": "Is_Observed"},
                        {"name": "Data_Source", "dataType": "string", "sourceColumn": "Data_Source"}
                    ],
                    "partitions": [
                        {
                            "name": "Dim_CAI_Employment_Benchmark",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Dim_CAI_Employment_Benchmark",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Benchmark_Key", "Year", "Covered_Employment_QCEW", "Self_Employment_NES", "Total_Employment_Combined", "Self_Employment_Ratio", "Ratio_Average_All_Years", "Ratio_Average_Last_10_Obs", "Is_Observed", "Data_Source"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Benchmark_Key", type text}, {"Year", Int64.Type},\n        {"Covered_Employment_QCEW", Int64.Type}, {"Self_Employment_NES", Int64.Type},\n        {"Total_Employment_Combined", Int64.Type}, {"Self_Employment_Ratio", type number},\n        {"Ratio_Average_All_Years", type number}, {"Ratio_Average_Last_10_Obs", type number},\n        {"Is_Observed", Int64.Type}, {"Data_Source", type text}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                },
                {
                    "name": "Fact_Population",
                    "description": "Annual population determinations by jurisdiction from OFM April 1.",
                    "columns": [
                        {"name": "Fact_Population_Key", "dataType": "string", "sourceColumn": "Fact_Population_Key", "isKey": True},
                        {"name": "Jurisdiction_ID", "dataType": "string", "sourceColumn": "Jurisdiction_ID"},
                        {"name": "Year", "dataType": "int64", "sourceColumn": "Year"},
                        {"name": "Jurisdiction_Name", "dataType": "string", "sourceColumn": "Jurisdiction_Name"},
                        {"name": "Population_Count", "dataType": "int64", "sourceColumn": "Population_Count"},
                        {"name": "Prior_Year_Population", "dataType": "int64", "sourceColumn": "Prior_Year_Population"},
                        {"name": "YoY_Population_Change", "dataType": "int64", "sourceColumn": "YoY_Population_Change"},
                        {"name": "YoY_Growth_Rate_Pct", "dataType": "double", "sourceColumn": "YoY_Growth_Rate_Pct"},
                        {"name": "Data_Source_Type", "dataType": "string", "sourceColumn": "Data_Source_Type"}
                    ],
                    "partitions": [
                        {
                            "name": "Fact_Population",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Fact_Population",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Fact_Population_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Population_Count", "Prior_Year_Population", "YoY_Population_Change", "YoY_Growth_Rate_Pct", "Data_Source_Type"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Fact_Population_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},\n        {"Jurisdiction_Name", type text}, {"Population_Count", Int64.Type},\n        {"Prior_Year_Population", Int64.Type}, {"YoY_Population_Change", Int64.Type},\n        {"YoY_Growth_Rate_Pct", type number}, {"Data_Source_Type", type text}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                },
                {
                    "name": "Fact_HousingPermits",
                    "description": "Annual residential building permit issuance by typology and valuation.",
                    "columns": [
                        {"name": "Fact_Housing_Key", "dataType": "string", "sourceColumn": "Fact_Housing_Key", "isKey": True},
                        {"name": "Jurisdiction_ID", "dataType": "string", "sourceColumn": "Jurisdiction_ID"},
                        {"name": "Year", "dataType": "int64", "sourceColumn": "Year"},
                        {"name": "Jurisdiction_Name", "dataType": "string", "sourceColumn": "Jurisdiction_Name"},
                        {"name": "Single_Family_Units", "dataType": "int64", "sourceColumn": "Single_Family_Units"},
                        {"name": "Duplex_Units", "dataType": "int64", "sourceColumn": "Duplex_Units"},
                        {"name": "MultiFamily_3_4_Units", "dataType": "int64", "sourceColumn": "MultiFamily_3_4_Units"},
                        {"name": "MultiFamily_5_Plus_Units", "dataType": "int64", "sourceColumn": "MultiFamily_5_Plus_Units"},
                        {"name": "ADU_Units", "dataType": "int64", "sourceColumn": "ADU_Units"},
                        {"name": "Mobile_Home_Units", "dataType": "int64", "sourceColumn": "Mobile_Home_Units"},
                        {"name": "Total_Permitted_Units", "dataType": "int64", "sourceColumn": "Total_Permitted_Units"},
                        {"name": "Completed_Units", "dataType": "int64", "sourceColumn": "Completed_Units"},
                        {"name": "Demolished_Units", "dataType": "int64", "sourceColumn": "Demolished_Units"},
                        {"name": "Net_New_Units", "dataType": "int64", "sourceColumn": "Net_New_Units"},
                        {"name": "Total_Valuation_USD", "dataType": "int64", "sourceColumn": "Total_Valuation_USD"},
                        {"name": "Data_Source", "dataType": "string", "sourceColumn": "Data_Source"}
                    ],
                    "partitions": [
                        {
                            "name": "Fact_HousingPermits",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Fact_HousingPermits",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Fact_Housing_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Single_Family_Units", "Duplex_Units", "MultiFamily_3_4_Units", "MultiFamily_5_Plus_Units", "ADU_Units", "Mobile_Home_Units", "Total_Permitted_Units", "Completed_Units", "Demolished_Units", "Net_New_Units", "Total_Valuation_USD", "Data_Source"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Fact_Housing_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},\n        {"Jurisdiction_Name", type text}, {"Single_Family_Units", Int64.Type},\n        {"Duplex_Units", Int64.Type}, {"MultiFamily_3_4_Units", Int64.Type},\n        {"MultiFamily_5_Plus_Units", Int64.Type}, {"ADU_Units", Int64.Type},\n        {"Mobile_Home_Units", Int64.Type}, {"Total_Permitted_Units", Int64.Type},\n        {"Completed_Units", Int64.Type}, {"Demolished_Units", Int64.Type},\n        {"Net_New_Units", Int64.Type}, {"Total_Valuation_USD", Int64.Type},\n        {"Data_Source", type text}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                },
                {
                    "name": "Fact_Employment",
                    "description": "Employment Security Department (ESD QCEW) covered jobs by NAICS industry sector.",
                    "columns": [
                        {"name": "Fact_Employment_Key", "dataType": "string", "sourceColumn": "Fact_Employment_Key", "isKey": True},
                        {"name": "Year", "dataType": "int64", "sourceColumn": "Year"},
                        {"name": "Period_Type", "dataType": "string", "sourceColumn": "Period_Type"},
                        {"name": "Industry_Key", "dataType": "string", "sourceColumn": "Industry_Key"},
                        {"name": "Row_Level", "dataType": "string", "sourceColumn": "Row_Level"},
                        {"name": "Parent_2Digit_Code", "dataType": "string", "sourceColumn": "Parent_2Digit_Code"},
                        {"name": "NAICS_2Digit_Code", "dataType": "string", "sourceColumn": "NAICS_2Digit_Code"},
                        {"name": "NAICS_3Digit_Code", "dataType": "string", "sourceColumn": "NAICS_3Digit_Code"},
                        {"name": "Industry_Subsector_Title", "dataType": "string", "sourceColumn": "Industry_Subsector_Title"},
                        {"name": "Title_As_Reported", "dataType": "string", "sourceColumn": "Title_As_Reported"},
                        {"name": "Is_County_Total", "dataType": "int64", "sourceColumn": "Is_County_Total"},
                        {"name": "Is_Suppressed", "dataType": "int64", "sourceColumn": "Is_Suppressed"},
                        {"name": "Average_Establishments", "dataType": "int64", "sourceColumn": "Average_Establishments"},
                        {"name": "Annual_Average_Employment", "dataType": "int64", "sourceColumn": "Annual_Average_Employment"},
                        {"name": "Q1_Average_Employment", "dataType": "int64", "sourceColumn": "Q1_Average_Employment"},
                        {"name": "Estimated_Total_Employment", "dataType": "int64", "sourceColumn": "Estimated_Total_Employment"},
                        {"name": "Estimated_Total_Employment_Q1", "dataType": "int64", "sourceColumn": "Estimated_Total_Employment_Q1"},
                        {"name": "CAI_Self_Employment_Multiplier", "dataType": "double", "sourceColumn": "CAI_Self_Employment_Multiplier"},
                        {"name": "Average_Annual_Wage_USD", "dataType": "int64", "sourceColumn": "Average_Annual_Wage_USD"},
                        {"name": "Data_Status", "dataType": "string", "sourceColumn": "Data_Status"}
                    ],
                    "partitions": [
                        {
                            "name": "Fact_Employment",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Fact_Employment",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Fact_Employment_Key", "Year", "Period_Type", "Industry_Key", "Row_Level", "Parent_2Digit_Code", "NAICS_2Digit_Code", "NAICS_3Digit_Code", "Industry_Subsector_Title", "Title_As_Reported", "Is_County_Total", "Is_Suppressed", "Average_Establishments", "Annual_Average_Employment", "Q1_Average_Employment", "Estimated_Total_Employment", "Estimated_Total_Employment_Q1", "CAI_Self_Employment_Multiplier", "Average_Annual_Wage_USD", "Data_Status"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Fact_Employment_Key", type text}, {"Year", Int64.Type}, {"Period_Type", type text},\n        {"Industry_Key", type text}, {"Row_Level", type text}, {"Parent_2Digit_Code", type text},\n        {"NAICS_2Digit_Code", type text}, {"NAICS_3Digit_Code", type text},\n        {"Industry_Subsector_Title", type text}, {"Title_As_Reported", type text},\n        {"Is_County_Total", Int64.Type}, {"Is_Suppressed", Int64.Type},\n        {"Average_Establishments", Int64.Type}, {"Annual_Average_Employment", Int64.Type},\n        {"Q1_Average_Employment", Int64.Type}, {"Estimated_Total_Employment", Int64.Type},\n        {"Estimated_Total_Employment_Q1", Int64.Type}, {"CAI_Self_Employment_Multiplier", type number},\n        {"Average_Annual_Wage_USD", Int64.Type}, {"Data_Status", type text}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                },
                {
                    "name": "Fact_Housing_AMI",
                    "description": "Affordable housing unit production classified by Area Median Income (AMI) tiers.",
                    "columns": [
                        {"name": "Fact_AMI_Key", "dataType": "string", "sourceColumn": "Fact_AMI_Key", "isKey": True},
                        {"name": "Jurisdiction_ID", "dataType": "string", "sourceColumn": "Jurisdiction_ID"},
                        {"name": "Year", "dataType": "int64", "sourceColumn": "Year"},
                        {"name": "Jurisdiction_Name", "dataType": "string", "sourceColumn": "Jurisdiction_Name"},
                        {"name": "Structure_Type", "dataType": "string", "sourceColumn": "Structure_Type"},
                        {"name": "AMI_0_to_30_Pct_Units", "dataType": "int64", "sourceColumn": "AMI_0_to_30_Pct_Units"},
                        {"name": "AMI_31_to_50_Pct_Units", "dataType": "int64", "sourceColumn": "AMI_31_to_50_Pct_Units"},
                        {"name": "AMI_51_to_80_Pct_Units", "dataType": "int64", "sourceColumn": "AMI_51_to_80_Pct_Units"},
                        {"name": "AMI_81_to_100_Pct_Units", "dataType": "int64", "sourceColumn": "AMI_81_to_100_Pct_Units"},
                        {"name": "AMI_101_to_120_Pct_Units", "dataType": "int64", "sourceColumn": "AMI_101_to_120_Pct_Units"},
                        {"name": "AMI_Greater_120_Pct_Units", "dataType": "int64", "sourceColumn": "AMI_Greater_120_Pct_Units"},
                        {"name": "Total_AMI_Units", "dataType": "int64", "sourceColumn": "Total_AMI_Units"},
                        {"name": "Reconciliation_Status", "dataType": "string", "sourceColumn": "Reconciliation_Status"}
                    ],
                    "partitions": [
                        {
                            "name": "Fact_Housing_AMI",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": 'let\n    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),\n    Sheet = Source{[Item="Fact_Housing_AMI",Kind="Sheet"]}[Data],\n    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),\n    Selected = Table.SelectColumns(Headers, {"Fact_AMI_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Structure_Type", "AMI_0_to_30_Pct_Units", "AMI_31_to_50_Pct_Units", "AMI_51_to_80_Pct_Units", "AMI_81_to_100_Pct_Units", "AMI_101_to_120_Pct_Units", "AMI_Greater_120_Pct_Units", "Total_AMI_Units", "Reconciliation_Status"}, MissingField.Error),\n    Typed = Table.TransformColumnTypes(Selected,{\n        {"Fact_AMI_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},\n        {"Jurisdiction_Name", type text}, {"Structure_Type", type text},\n        {"AMI_0_to_30_Pct_Units", Int64.Type}, {"AMI_31_to_50_Pct_Units", Int64.Type},\n        {"AMI_51_to_80_Pct_Units", Int64.Type}, {"AMI_81_to_100_Pct_Units", Int64.Type},\n        {"AMI_101_to_120_Pct_Units", Int64.Type}, {"AMI_Greater_120_Pct_Units", Int64.Type},\n        {"Total_AMI_Units", Int64.Type}, {"Reconciliation_Status", type text}\n    })\nin\n    Typed'
                            }
                        }
                    ]
                }
            ],
            "relationships": [
                {
                    "name": "Rel_Jurisdiction_FactPopulation",
                    "fromTable": "Fact_Population",
                    "fromColumn": "Jurisdiction_ID",
                    "toTable": "Dim_Jurisdiction",
                    "toColumn": "Jurisdiction_ID"
                },
                {
                    "name": "Rel_CalendarYear_FactPopulation",
                    "fromTable": "Fact_Population",
                    "fromColumn": "Year",
                    "toTable": "Dim_CalendarYear",
                    "toColumn": "Year"
                },
                {
                    "name": "Rel_Jurisdiction_FactHousingPermits",
                    "fromTable": "Fact_HousingPermits",
                    "fromColumn": "Jurisdiction_ID",
                    "toTable": "Dim_Jurisdiction",
                    "toColumn": "Jurisdiction_ID"
                },
                {
                    "name": "Rel_CalendarYear_FactHousingPermits",
                    "fromTable": "Fact_HousingPermits",
                    "fromColumn": "Year",
                    "toTable": "Dim_CalendarYear",
                    "toColumn": "Year"
                },
                {
                    "name": "Rel_CalendarYear_FactEmployment",
                    "fromTable": "Fact_Employment",
                    "fromColumn": "Year",
                    "toTable": "Dim_CalendarYear",
                    "toColumn": "Year"
                },
                {
                    "name": "Rel_Jurisdiction_FactHousingAMI",
                    "fromTable": "Fact_Housing_AMI",
                    "fromColumn": "Jurisdiction_ID",
                    "toTable": "Dim_Jurisdiction",
                    "toColumn": "Jurisdiction_ID"
                },
                {
                    "name": "Rel_CalendarYear_FactHousingAMI",
                    "fromTable": "Fact_Housing_AMI",
                    "fromColumn": "Year",
                    "toTable": "Dim_CalendarYear",
                    "toColumn": "Year"
                },
                {
                    "name": "Rel_Jurisdiction_DimGMATarget",
                    "fromTable": "Dim_GMA_2045_Target",
                    "fromColumn": "Jurisdiction_ID",
                    "toTable": "Dim_Jurisdiction",
                    "toColumn": "Jurisdiction_ID"
                },
                {
                    "name": "Rel_CalendarYear_DimCAIBenchmark",
                    "fromTable": "Dim_CAI_Employment_Benchmark",
                    "fromColumn": "Year",
                    "toTable": "Dim_CalendarYear",
                    "toColumn": "Year"
                }
            ]
        }
    }
    return model


def build_textbox_vc(name, x, y, width, height, title_text, subtitle_text):
    config = {
        "name": name,
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": title_text,
                                            "textStyle": {
                                                "fontSize": "15pt",
                                                "fontFamily": "Segoe UI Bold",
                                                "color": "#004B87"
                                            }
                                        },
                                        {
                                            "value": subtitle_text,
                                            "textStyle": {
                                                "fontSize": "9pt",
                                                "fontFamily": "Segoe UI",
                                                "color": "#475569"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
    return {
        "x": x, "y": y, "z": 1000, "width": width, "height": height,
        "config": json.dumps(config)
    }


def build_footer_vc(name, x, y, width, height, text):
    config = {
        "name": name,
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": text,
                                            "textStyle": {
                                                "fontSize": "8pt",
                                                "fontFamily": "Segoe UI",
                                                "color": "#64748B"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
    return {
        "x": x, "y": y, "z": 9000, "width": width, "height": height,
        "config": json.dumps(config)
    }


def build_card_vc(name, x, y, width, height, measure_name):
    config = {
        "name": name,
        "singleVisual": {
            "visualType": "card",
            "projections": {
                "Values": [{"queryRef": f"_Measures.{measure_name}"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "m", "Entity": "_Measures", "Type": 0}],
                "Select": [
                    {
                        "Measure": {
                            "Expression": {"SourceRef": {"Source": "m"}},
                            "Property": measure_name
                        },
                        "Name": f"_Measures.{measure_name}"
                    }
                ]
            }
        }
    }
    return {
        "x": x, "y": y, "z": 3000, "width": width, "height": height,
        "config": json.dumps(config)
    }


def build_report_json():
    # 4-page Power BI Report JSON layout (1280 x 720 widescreen 16:9)
    report = {
        "config": json.dumps({
            "version": "5.50",
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU08",
                    "version": "5.50",
                    "type": 2
                }
            },
            "activeSectionIndex": 0,
            "defaultDrillFilterOtherVisuals": True
        }),
        "layoutOptimization": 0,
        "sections": [
            # Page 1: Executive Summary & Regional Dashboard
            {
                "name": "Section_ExecutiveSummary",
                "displayName": "1. Executive Summary & Regional Dashboard",
                "width": 1280,
                "height": 720,
                "displayOption": 1,
                "visualContainers": [
                    build_textbox_vc(
                        "HeaderBanner_P1", 20, 15, 1240, 60,
                        "SKAGIT COUNCIL OF GOVERNMENTS — ANNUAL GROWTH MONITORING REPORT\n",
                        "Regional Executive Summary & GMA 2045 Target Trajectory | Baseline Calibration Year: 2025"
                    ),
                    # Slicer: Year
                    {
                        "x": 20, "y": 80, "z": 2000, "width": 180, "height": 75,
                        "config": json.dumps({
                            "name": "Slicer_Year_P1",
                            "singleVisual": {
                                "visualType": "slicer",
                                "projections": {"Values": [{"queryRef": "Dim_CalendarYear.Year"}]},
                                "prototypeQuery": {
                                    "Version": 2,
                                    "From": [{"Name": "d", "Entity": "Dim_CalendarYear", "Type": 0}],
                                    "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": "Year"}, "Name": "Dim_CalendarYear.Year"}]
                                }
                            }
                        })
                    },
                    build_card_vc("Card_TotalPopulation", 210, 80, 240, 95, "Total Population"),
                    build_card_vc("Card_NetHousingUnits", 460, 80, 240, 95, "Net New Housing Units"),
                    build_card_vc("Card_CoveredEmployment", 710, 80, 260, 95, "Covered Employment QCEW"),
                    build_card_vc("Card_HousingProgress", 980, 80, 280, 95, "Housing Target Progress %"),
                    # Chart: Historical Population Growth Trajectory
                    {
                        "x": 20, "y": 185, "z": 4000, "width": 615, "height": 260,
                        "config": json.dumps({
                            "name": "LineChart_PopulationTrend",
                            "singleVisual": {
                                "visualType": "lineChart",
                                "projections": {
                                    "Category": [{"queryRef": "Dim_CalendarYear.Year"}],
                                    "Y": [{"queryRef": "_Measures.Total Population"}]
                                }
                            }
                        })
                    },
                    # Chart: Housing Permits & Net Units by Typology
                    {
                        "x": 645, "y": 185, "z": 4001, "width": 615, "height": 260,
                        "config": json.dumps({
                            "name": "ColumnChart_HousingUnits",
                            "singleVisual": {
                                "visualType": "clusteredColumnChart",
                                "projections": {
                                    "Category": [{"queryRef": "Dim_CalendarYear.Year"}],
                                    "Y": [
                                        {"queryRef": "_Measures.Single-Family Permits"},
                                        {"queryRef": "_Measures.Multi-Family Permits"},
                                        {"queryRef": "_Measures.ADU Permits"}
                                    ]
                                }
                            }
                        })
                    },
                    # Summary Table: Jurisdictions vs GMA 2045 Targets (Population & Housing Only)
                    {
                        "x": 20, "y": 455, "z": 5000, "width": 1240, "height": 210,
                        "config": json.dumps({
                            "name": "Table_ExecutiveSummaryJurisdictions",
                            "singleVisual": {
                                "visualType": "tableEx",
                                "projections": {
                                    "Values": [
                                        {"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"},
                                        {"queryRef": "Dim_Jurisdiction.Jurisdiction_Type"},
                                        {"queryRef": "_Measures.Total Population"},
                                        {"queryRef": "_Measures.2045 Population Target"},
                                        {"queryRef": "_Measures.Net New Housing Units"},
                                        {"queryRef": "_Measures.2045 Housing Target Units"},
                                        {"queryRef": "_Measures.Housing Target Progress %"}
                                    ]
                                },
                                "objects": {
                                    "title": [{
                                        "properties": {
                                            "show": {"expr": {"Literal": {"Value": "true"}}},
                                            "text": {"expr": {"Literal": {"Value": "'11-Jurisdiction GMA 2045 Progress Matrix (Population & Housing Only)'"}}}
                                        }
                                    }]
                                }
                            }
                        })
                    },
                    build_footer_vc(
                        "FooterNotice_P1", 20, 675, 1240, 35,
                        "Source: Skagit Council of Governments (SCOG) | WA OFM April 1 Population | ESD Covered Employment | Skagit County Ordinance O20250002. Note: Jurisdiction matrix displays Population & Housing only; Employment allocations are tracked at County aggregate."
                    )
                ]
            },

            # Page 2: Housing Deep-Dive
            {
                "name": "Section_HousingDeepDive",
                "displayName": "2. Housing Deep-Dive",
                "width": 1280,
                "height": 720,
                "displayOption": 1,
                "visualContainers": [
                    build_textbox_vc(
                        "HeaderBanner_P2", 20, 15, 1240, 55,
                        "HOUSING PRODUCTION DEEP-DIVE & AFFORDABILITY (AMI) ANALYSIS\n",
                        "Permits by Typology, Net Production vs. GMA 2045 Allocations, and AMI Affordability (PRELIMINARY: local AMI datasheets due Oct 20)"
                    ),
                    # Slicer: Jurisdiction
                    {
                        "x": 20, "y": 75, "z": 2000, "width": 260, "height": 85,
                        "config": json.dumps({
                            "name": "Slicer_Jurisdiction_P2",
                            "singleVisual": {
                                "visualType": "slicer",
                                "projections": {"Values": [{"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"}]}
                            }
                        })
                    },
                    build_card_vc("Card_NetUnits_P2", 290, 75, 220, 85, "Net New Housing Units"),
                    build_card_vc("Card_SingleFamily_P2", 520, 75, 220, 85, "Single-Family Permits"),
                    build_card_vc("Card_MultiFamily_P2", 750, 75, 220, 85, "Multi-Family Permits"),
                    build_card_vc("Card_ADUs_P2", 980, 75, 280, 85, "ADU Permits"),
                    # Historical Permits Area Chart
                    {
                        "x": 20, "y": 170, "z": 3000, "width": 780, "height": 240,
                        "config": json.dumps({
                            "name": "AreaChart_HousingHistory",
                            "singleVisual": {
                                "visualType": "stackedAreaChart",
                                "projections": {
                                    "Category": [{"queryRef": "Dim_CalendarYear.Year"}],
                                    "Y": [
                                        {"queryRef": "_Measures.Single-Family Permits"},
                                        {"queryRef": "_Measures.Multi-Family Permits"},
                                        {"queryRef": "_Measures.ADU Permits"}
                                    ]
                                }
                            }
                        })
                    },
                    # Typology Donut
                    {
                        "x": 810, "y": 170, "z": 3001, "width": 450, "height": 240,
                        "config": json.dumps({
                            "name": "Donut_HousingMix",
                            "singleVisual": {
                                "visualType": "donutChart",
                                "projections": {
                                    "Y": [
                                        {"queryRef": "_Measures.Single-Family Permits"},
                                        {"queryRef": "_Measures.Multi-Family Permits"},
                                        {"queryRef": "_Measures.ADU Permits"}
                                    ]
                                }
                            }
                        })
                    },
                    # AMI Bar Chart with prominent Preliminary label
                    {
                        "x": 20, "y": 420, "z": 4000, "width": 620, "height": 245,
                        "config": json.dumps({
                            "name": "Bar_AMI_Distribution",
                            "singleVisual": {
                                "visualType": "clusteredBarChart",
                                "projections": {
                                    "Category": [{"queryRef": "Fact_Housing_AMI.Structure_Type"}],
                                    "Y": [
                                        {"queryRef": "_Measures.Low Income AMI Units (<80% AMI)"},
                                        {"queryRef": "_Measures.Moderate to High Income AMI Units (>80% AMI)"}
                                    ]
                                },
                                "objects": {
                                    "title": [{
                                        "properties": {
                                            "show": {"expr": {"Literal": {"Value": "true"}}},
                                            "text": {"expr": {"Literal": {"Value": "'Housing by AMI Tier (PRELIMINARY: Statewide Default Allocation — Local Datasheets Due Oct 20)'"}}}
                                        }
                                    }]
                                }
                            }
                        })
                    },
                    # Target Progress Matrix
                    {
                        "x": 650, "y": 420, "z": 4001, "width": 610, "height": 245,
                        "config": json.dumps({
                            "name": "Matrix_HousingTargets",
                            "singleVisual": {
                                "visualType": "pivotTable",
                                "projections": {
                                    "Rows": [{"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"}],
                                    "Values": [
                                        {"queryRef": "_Measures.Cumulative Net Housing Units (2020-Present)"},
                                        {"queryRef": "_Measures.2045 Housing Target Units"},
                                        {"queryRef": "_Measures.Housing Target Progress %"}
                                    ]
                                }
                            }
                        })
                    },
                    build_footer_vc(
                        "FooterNotice_P2", 20, 675, 1240, 35,
                        "Sources: OFM Postcensal Housing Permits (1990-2026) | WA Commerce AMI Allocation Guidance (PRELIMINARY: Local Certified Datasheets Due Oct 20) | Ordinance O20250002"
                    )
                ]
            },

            # Page 3: Population & Employment Overview
            {
                "name": "Section_PopulationEmployment",
                "displayName": "3. Population & Employment Overview",
                "width": 1280,
                "height": 720,
                "displayOption": 1,
                "visualContainers": [
                    build_textbox_vc(
                        "HeaderBanner_P3", 20, 15, 1240, 55,
                        "REGIONAL POPULATION & EMPLOYMENT DYNAMICS\n",
                        "OFM April 1 Population Trends and Official ESD Covered Employment by Sector (Official State Series)"
                    ),
                    # Population Bar Chart
                    {
                        "x": 20, "y": 80, "z": 2000, "width": 615, "height": 280,
                        "config": json.dumps({
                            "name": "Bar_PopByJurisdiction",
                            "singleVisual": {
                                "visualType": "clusteredBarChart",
                                "projections": {
                                    "Category": [{"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"}],
                                    "Y": [{"queryRef": "_Measures.Total Population"}]
                                }
                            }
                        })
                    },
                    # Industry Bar Chart
                    {
                        "x": 645, "y": 80, "z": 2001, "width": 615, "height": 280,
                        "config": json.dumps({
                            "name": "Bar_EmploymentByIndustry",
                            "singleVisual": {
                                "visualType": "clusteredBarChart",
                                "projections": {
                                    "Category": [{"queryRef": "Fact_Employment.Industry_Subsector_Title"}],
                                    "Y": [{"queryRef": "_Measures.Covered Employment QCEW"}]
                                }
                            }
                        })
                    },
                    # ESD Covered Employment Historical Trend (Official State Series)
                    {
                        "x": 20, "y": 370, "z": 3000, "width": 780, "height": 295,
                        "config": json.dumps({
                            "name": "Line_CoveredEmploymentOfficialSeries",
                            "singleVisual": {
                                "visualType": "lineChart",
                                "projections": {
                                    "Category": [{"queryRef": "Dim_CAI_Employment_Benchmark.Year"}],
                                    "Y": [
                                        {"queryRef": "Dim_CAI_Employment_Benchmark.Covered_Employment_QCEW"}
                                    ]
                                },
                                "objects": {
                                    "title": [{
                                        "properties": {
                                            "show": {"expr": {"Literal": {"Value": "true"}}},
                                            "text": {"expr": {"Literal": {"Value": "'Official ESD Covered Employment Benchmark Series (1999-2022) [Total Multiplier Pending SCOG Confirmation]'"}}}
                                        }
                                    }]
                                }
                            }
                        })
                    },
                    # Employment Matrix
                    {
                        "x": 810, "y": 370, "z": 3001, "width": 450, "height": 295,
                        "config": json.dumps({
                            "name": "Table_EmploymentOverviewDetails",
                            "singleVisual": {
                                "visualType": "tableEx",
                                "projections": {
                                    "Values": [
                                        {"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"},
                                        {"queryRef": "_Measures.2022 Employment Baseline"},
                                        {"queryRef": "_Measures.2045 Employment Target"}
                                    ]
                                },
                                "objects": {
                                    "title": [{
                                        "properties": {
                                            "show": {"expr": {"Literal": {"Value": "true"}}},
                                            "text": {"expr": {"Literal": {"Value": "'Adopted GMA 2045 Employment Targets by Jurisdiction (Planning Allocations Only - No Annual Actuals)'"}}}
                                        }
                                    }]
                                }
                            }
                        })
                    },
                    build_footer_vc(
                        "FooterNotice_P3", 20, 675, 1240, 35,
                        "Sources: WA OFM April 1 Population | ESD QCEW Covered Employment | Ordinance O20250002. Note: Total Employment multiplier is preliminary and withheld pending formal confirmation with SCOG staff."
                    )
                ]
            },

            # Page 4: Jurisdictional Comparison & Spatial Mapping
            {
                "name": "Section_JurisdictionSpatialMapping",
                "displayName": "4. Jurisdictional Comparison & Spatial Mapping",
                "width": 1280,
                "height": 720,
                "displayOption": 1,
                "visualContainers": [
                    build_textbox_vc(
                        "HeaderBanner_P4", 20, 15, 1240, 55,
                        "JURISDICTIONAL COMPARISON & SPATIAL DISTRIBUTION\n",
                        "Incorporated Cities vs. UGAs vs. Rural Areas — Countywide Spatial Map and Planning Shares"
                    ),
                    # Map Visual
                    {
                        "x": 20, "y": 80, "z": 2000, "width": 640, "height": 585,
                        "config": json.dumps({
                            "name": "Map_SkagitCountyJurisdictions",
                            "singleVisual": {
                                "visualType": "map",
                                "projections": {
                                    "Category": [{"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"}],
                                    "Latitude": [{"queryRef": "Dim_Jurisdiction.Latitude"}],
                                    "Longitude": [{"queryRef": "Dim_Jurisdiction.Longitude"}],
                                    "Size": [{"queryRef": "_Measures.Total Population"}]
                                },
                                "objects": {
                                    "title": [{
                                        "properties": {
                                            "show": {"expr": {"Literal": {"Value": "true"}}},
                                            "text": {"expr": {"Literal": {"Value": "'Regional Jurisdictions & UGAs (Official USGS/Census 2020 Centroids)'"}}}
                                        }
                                    }]
                                }
                            }
                        })
                    },
                    # Matrix: Comparison by Jurisdiction Type
                    {
                        "x": 670, "y": 80, "z": 3000, "width": 590, "height": 330,
                        "config": json.dumps({
                            "name": "Matrix_JurisdictionTypeComparison",
                            "singleVisual": {
                                "visualType": "pivotTable",
                                "projections": {
                                    "Rows": [
                                        {"queryRef": "Dim_Jurisdiction.Jurisdiction_Type"},
                                        {"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"}
                                    ],
                                    "Values": [
                                        {"queryRef": "_Measures.Total Population"},
                                        {"queryRef": "_Measures.Jurisdiction Share of Regional Population %"},
                                        {"queryRef": "_Measures.Net New Housing Units"},
                                        {"queryRef": "_Measures.Housing Target Progress %"}
                                    ]
                                }
                            }
                        })
                    },
                    # Growth Shares Bar Chart
                    {
                        "x": 670, "y": 420, "z": 4000, "width": 590, "height": 245,
                        "config": json.dumps({
                            "name": "Bar_GrowthShares",
                            "singleVisual": {
                                "visualType": "clusteredBarChart",
                                "projections": {
                                    "Category": [{"queryRef": "Dim_Jurisdiction.Jurisdiction_Name"}],
                                    "Y": [
                                        {"queryRef": "_Measures.Jurisdiction Share of Regional Population %"},
                                        {"queryRef": "_Measures.Jurisdiction Share of Regional Housing %"}
                                    ]
                                }
                            }
                        })
                    },
                    build_footer_vc(
                        "FooterNotice_P4", 20, 675, 1240, 35,
                        "Centroid Coordinates: Official USGS GNIS / US Census Bureau 2020 Municipal Centers & UGA Centroids. 'Unincorporated Skagit County' represents rural balance outside designated UGAs per Ordinance O20250002."
                    )
                ]
            }
        ]
    }
    return report


def build_dax_file():
    dax_content = '''/*
========================================================================================
SCOG ANNUAL GROWTH MONITORING REPORT — COMPLETE DAX MEASURES LIBRARY
Project: Skagit Council of Governments (SCOG) Growth Monitoring Report
Version: 2025 Prototype Baseline
Model Architecture: Star Schema (Conformed Dimensions: Jurisdiction, CalendarYear, GMA Target)
========================================================================================
*/

// =====================================================================================
// 01. EXECUTIVE & GOVERNANCE MEASURES
// =====================================================================================

[Selected Reporting Year] = 
COALESCE(SELECTEDVALUE(Dim_CalendarYear[Year]), 2025)
/* Description: Returns the actively filtered year in slicers, defaulting to 2025 prototype baseline. */

[Selected Jurisdiction] = 
SELECTEDVALUE(Dim_Jurisdiction[Jurisdiction_Name], "All Skagit County Jurisdictions")
/* Description: Returns the actively selected jurisdiction or an explicit countywide indicator. */

[Report Adoption Status Banner] = 
VAR CurrentYr = [Selected Reporting Year]
RETURN
IF(
    CurrentYr <= 2024,
    "BOARD ADOPTED (Official Legal Record)",
    IF(
        CurrentYr = 2025,
        "PROTOTYPE 2025 (Prior-Year Historical Calibration)",
        "PRELIMINARY 2026 (Under Review / Draft)"
    )
)
/* Description: Dynamic audit indicator for board review and PDF exports. */

[Metadata Footer Notice] = 
"Data Sources: WA Office of Financial Management (OFM) | Employment Security Department (ESD QCEW) | Skagit County GMA Allocations (Ordinance O20250002) | SCOG Annual Growth Monitoring Report"
/* Description: Mandatory data governance citation footer on all 16:9 canvas pages. */


// =====================================================================================
// 02. POPULATION GROWTH & TARGETS
// =====================================================================================

[Total Population] = 
SUM(Fact_Population[Population_Count])
// Format: #,##0
/* Description: Official April 1 population determination by OFM. */

[Prior Year Population] = 
CALCULATE(
    [Total Population],
    SAMEPERIODLASTYEAR(Dim_CalendarYear[Year])
)
// Format: #,##0

[YoY Population Change] = 
SUM(Fact_Population[YoY_Population_Change])
// Format: +#,##0;-#,##0;0

[YoY Population Growth %] = 
DIVIDE([YoY Population Change], [Prior Year Population], 0)
// Format: 0.00%

[2022 Population Baseline] = 
SUM(Dim_GMA_2045_Target[Baseline_2022_Population])
// Format: #,##0

[2045 Population Target] = 
SUM(Dim_GMA_2045_Target[Target_2045_Population])
// Format: #,##0

[Projected 2045 Population Growth] = 
SUM(Dim_GMA_2045_Target[Projected_2045_Population_Growth])
// Format: #,##0

[Population Growth Toward 2045 Target %] = 
VAR CurrentPop = [Total Population]
VAR BasePop = [2022 Population Baseline]
VAR TargetGain = [Projected 2045 Population Growth]
RETURN
IF(TargetGain > 0, DIVIDE(CurrentPop - BasePop, TargetGain, 0), BLANK())
// Format: 0.0%

[Remaining Population Capacity to 2045] = 
[2045 Population Target] - [Total Population]
// Format: #,##0


// =====================================================================================
// 03. HOUSING PRODUCTION & AMI
// =====================================================================================

[Total Housing Permits] = 
SUM(Fact_HousingPermits[Total_Permitted_Units])
// Format: #,##0

[Single-Family Permits] = 
SUM(Fact_HousingPermits[Single_Family_Units])
// Format: #,##0

[Multi-Family Permits] = 
SUM(Fact_HousingPermits[Duplex_Units]) + 
SUM(Fact_HousingPermits[MultiFamily_3_4_Units]) + 
SUM(Fact_HousingPermits[MultiFamily_5_Plus_Units])
// Format: #,##0

[ADU Permits] = 
SUM(Fact_HousingPermits[ADU_Units])
// Format: #,##0

[Demolished Units] = 
SUM(Fact_HousingPermits[Demolished_Units])
// Format: #,##0

[Net New Housing Units] = 
SUM(Fact_HousingPermits[Net_New_Units])
// Format: #,##0

[Total Permit Valuation] = 
SUM(Fact_HousingPermits[Total_Valuation_USD])
// Format: $#,##0

[2045 Housing Target Units] = 
SUM(Dim_GMA_2045_Target[Target_2045_Housing_Units])
// Format: #,##0

[Cumulative Net Housing Units (2020-Present)] = 
CALCULATE(
    [Net New Housing Units],
    FILTER(
        ALL(Dim_CalendarYear),
        Dim_CalendarYear[Year] >= 2020 && Dim_CalendarYear[Year] <= MAX(Dim_CalendarYear[Year])
    )
)
// Format: #,##0

[Housing Target Progress %] = 
DIVIDE([Cumulative Net Housing Units (2020-Present)], [2045 Housing Target Units], 0)
// Format: 0.0%

[Low Income AMI Units (<80% AMI)] = 
SUM(Fact_Housing_AMI[AMI_0_to_30_Pct_Units]) + 
SUM(Fact_Housing_AMI[AMI_31_to_50_Pct_Units]) + 
SUM(Fact_Housing_AMI[AMI_51_to_80_Pct_Units])
// Format: #,##0
/* Description: PRELIMINARY — Based on statewide default distribution (WA Commerce Exhibit 12). Official certified local jurisdiction datasheets are due October 20. */

[Moderate to High Income AMI Units (>80% AMI)] = 
SUM(Fact_Housing_AMI[AMI_81_to_100_Pct_Units]) + 
SUM(Fact_Housing_AMI[AMI_101_to_120_Pct_Units]) + 
SUM(Fact_Housing_AMI[AMI_Greater_120_Pct_Units])
// Format: #,##0
/* Description: PRELIMINARY — Based on statewide default distribution (WA Commerce Exhibit 12). Official certified local jurisdiction datasheets are due October 20. */


// =====================================================================================
// 04. EMPLOYMENT & CAI METHODOLOGY
// =====================================================================================

[Covered Employment QCEW] = 
CALCULATE(
    SUM(Fact_Employment[Annual_Average_Employment]),
    Fact_Employment[Is_County_Total] = 1
)
// Format: #,##0
/* Description: Official Employment Security Department (ESD QCEW) covered jobs for Skagit County Total. */

[Estimated Total Employment (CAI Multiplier)] = 
CALCULATE(
    SUM(Fact_Employment[Estimated_Total_Employment]),
    Fact_Employment[Is_County_Total] = 1
)
// Format: #,##0
/* Description: PRELIMINARY & WITHHELD FROM OFFICIAL REPORTING — Pending confirmation with SCOG staff on whether GMA 2045 employment targets are benchmarked against covered or total employment. Applies empirical CAI self-employment ratio (1.15458) to County Total row only. */

[2022 Employment Baseline] = 
SUM(Dim_GMA_2045_Target[Baseline_2022_Employment])
// Format: #,##0

[2045 Employment Target] = 
SUM(Dim_GMA_2045_Target[Target_2045_Employment])
// Format: #,##0

[Total Establishments] = 
CALCULATE(
    SUM(Fact_Employment[Average_Establishments]),
    Fact_Employment[Is_County_Total] = 1
)
// Format: #,##0

[Average Annual Wage USD] = 
CALCULATE(
    AVERAGE(Fact_Employment[Average_Annual_Wage_USD]),
    Fact_Employment[Is_County_Total] = 1
)
// Format: $#,##0


// =====================================================================================
// 05. REGIONAL & SPATIAL ANALYSIS
// =====================================================================================

[Jurisdiction Share of Regional Population %] = 
VAR RegionalPop = CALCULATE([Total Population], ALL(Dim_Jurisdiction))
RETURN
DIVIDE([Total Population], RegionalPop, 0)
// Format: 0.0%

[Jurisdiction Share of Regional Housing %] = 
VAR RegionalHousing = CALCULATE([Net New Housing Units], ALL(Dim_Jurisdiction))
RETURN
DIVIDE([Net New Housing Units], RegionalHousing, 0)
// Format: 0.0%
'''
    with open(os.path.join(POWERBI_DIR, "dax_measures.dax"), "w", encoding="utf-8") as f:
        f.write(dax_content)


def build_power_query_file(workbook_path):
    lines = [
        "/*",
        "========================================================================================",
        "SCOG ANNUAL GROWTH MONITORING REPORT — POWER QUERY (M) INGESTION SCRIPTS",
        f"Source Workbook: {workbook_path}",
        "Schema: Star Schema (4 Dimensions, 4 Facts, 1 Parameter)",
        "========================================================================================",
        "*/",
        "",
        "// PARAMETER: SourceWorkbookPath",
        f'let SourceWorkbookPath = "{workbook_path}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true] in SourceWorkbookPath',
        "",
        "// DIMENSION: Dim_Jurisdiction",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Dim_Jurisdiction",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Jurisdiction_ID", "Jurisdiction_Name", "Jurisdiction_Type", "Is_Incorporated", "Is_UGA", "Latitude", "Longitude", "County_Name", "State"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Jurisdiction_ID", type text}, {"Jurisdiction_Name", type text}, {"Jurisdiction_Type", type text},',
        '        {"Is_Incorporated", Int64.Type}, {"Is_UGA", Int64.Type},',
        '        {"Latitude", type number}, {"Longitude", type number},',
        '        {"County_Name", type text}, {"State", type text}',
        '    })',
        'in',
        '    Typed',
        "",
        "// DIMENSION: Dim_CalendarYear",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Dim_CalendarYear",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Year", "Decade", "GMA_Planning_Cycle", "Is_Historical", "Is_Prototype_Year_2025", "Is_Production_Year_2026", "Is_Target_Year_2045"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Year", Int64.Type}, {"Decade", type text}, {"GMA_Planning_Cycle", type text},',
        '        {"Is_Historical", Int64.Type}, {"Is_Prototype_Year_2025", Int64.Type},',
        '        {"Is_Production_Year_2026", Int64.Type}, {"Is_Target_Year_2045", Int64.Type}',
        '    })',
        'in',
        '    Typed',
        "",
        "// DIMENSION: Dim_GMA_2045_Target",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Dim_GMA_2045_Target",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Jurisdiction_ID", "Jurisdiction_Name", "Jurisdiction_Type", "Baseline_2022_Population", "Target_2045_Population", "Projected_2045_Population_Growth", "Population_Growth_Share_Pct", "Target_2045_Housing_Units", "Baseline_2022_Employment", "Target_2045_Employment", "Projected_2045_Employment_Growth", "Employment_Growth_Share_Pct", "CAI_Self_Employment_Multiplier", "Data_Source"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Jurisdiction_ID", type text}, {"Jurisdiction_Name", type text}, {"Jurisdiction_Type", type text},',
        '        {"Baseline_2022_Population", Int64.Type}, {"Target_2045_Population", Int64.Type},',
        '        {"Projected_2045_Population_Growth", Int64.Type}, {"Population_Growth_Share_Pct", type number},',
        '        {"Target_2045_Housing_Units", Int64.Type}, {"Baseline_2022_Employment", Int64.Type},',
        '        {"Target_2045_Employment", Int64.Type}, {"Projected_2045_Employment_Growth", Int64.Type},',
        '        {"Employment_Growth_Share_Pct", type number}, {"CAI_Self_Employment_Multiplier", type number},',
        '        {"Data_Source", type text}',
        '    })',
        'in',
        '    Typed',
        "",
        "// DIMENSION: Dim_CAI_Employment_Benchmark",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Dim_CAI_Employment_Benchmark",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Benchmark_Key", "Year", "Covered_Employment_QCEW", "Self_Employment_NES", "Total_Employment_Combined", "Self_Employment_Ratio", "Ratio_Average_All_Years", "Ratio_Average_Last_10_Obs", "Is_Observed", "Data_Source"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Benchmark_Key", type text}, {"Year", Int64.Type},',
        '        {"Covered_Employment_QCEW", Int64.Type}, {"Self_Employment_NES", Int64.Type},',
        '        {"Total_Employment_Combined", Int64.Type}, {"Self_Employment_Ratio", type number},',
        '        {"Ratio_Average_All_Years", type number}, {"Ratio_Average_Last_10_Obs", type number},',
        '        {"Is_Observed", Int64.Type}, {"Data_Source", type text}',
        '    })',
        'in',
        '    Typed',
        "",
        "// FACT: Fact_Population",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Fact_Population",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Fact_Population_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Population_Count", "Prior_Year_Population", "YoY_Population_Change", "YoY_Growth_Rate_Pct", "Data_Source_Type"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Fact_Population_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},',
        '        {"Jurisdiction_Name", type text}, {"Population_Count", Int64.Type},',
        '        {"Prior_Year_Population", Int64.Type}, {"YoY_Population_Change", Int64.Type},',
        '        {"YoY_Growth_Rate_Pct", type number}, {"Data_Source_Type", type text}',
        '    })',
        'in',
        '    Typed',
        "",
        "// FACT: Fact_HousingPermits",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Fact_HousingPermits",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Fact_Housing_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Single_Family_Units", "Duplex_Units", "MultiFamily_3_4_Units", "MultiFamily_5_Plus_Units", "ADU_Units", "Mobile_Home_Units", "Total_Permitted_Units", "Completed_Units", "Demolished_Units", "Net_New_Units", "Total_Valuation_USD", "Data_Source"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Fact_Housing_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},',
        '        {"Jurisdiction_Name", type text}, {"Single_Family_Units", Int64.Type},',
        '        {"Duplex_Units", Int64.Type}, {"MultiFamily_3_4_Units", Int64.Type},',
        '        {"MultiFamily_5_Plus_Units", Int64.Type}, {"ADU_Units", Int64.Type},',
        '        {"Mobile_Home_Units", Int64.Type}, {"Total_Permitted_Units", Int64.Type},',
        '        {"Completed_Units", Int64.Type}, {"Demolished_Units", Int64.Type},',
        '        {"Net_New_Units", Int64.Type}, {"Total_Valuation_USD", Int64.Type},',
        '        {"Data_Source", type text}',
        '    })',
        'in',
        '    Typed',
        "",
        "// FACT: Fact_Employment",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Fact_Employment",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Fact_Employment_Key", "Year", "Period_Type", "Industry_Key", "Row_Level", "Parent_2Digit_Code", "NAICS_2Digit_Code", "NAICS_3Digit_Code", "Industry_Subsector_Title", "Title_As_Reported", "Is_County_Total", "Is_Suppressed", "Average_Establishments", "Annual_Average_Employment", "Q1_Average_Employment", "Estimated_Total_Employment", "Estimated_Total_Employment_Q1", "CAI_Self_Employment_Multiplier", "Average_Annual_Wage_USD", "Data_Status"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Fact_Employment_Key", type text}, {"Year", Int64.Type}, {"Period_Type", type text},\n        {"Industry_Key", type text}, {"Row_Level", type text}, {"Parent_2Digit_Code", type text},\n        {"NAICS_2Digit_Code", type text}, {"NAICS_3Digit_Code", type text},\n        {"Industry_Subsector_Title", type text}, {"Title_As_Reported", type text},\n        {"Is_County_Total", Int64.Type}, {"Is_Suppressed", Int64.Type},\n        {"Average_Establishments", Int64.Type}, {"Annual_Average_Employment", Int64.Type},\n        {"Q1_Average_Employment", Int64.Type}, {"Estimated_Total_Employment", Int64.Type},\n        {"Estimated_Total_Employment_Q1", Int64.Type}, {"CAI_Self_Employment_Multiplier", type number},\n        {"Average_Annual_Wage_USD", Int64.Type}, {"Data_Status", type text}\n    })\nin\n    Typed',
        "",
        "// FACT: Fact_Housing_AMI",
        'let',
        '    Source = Excel.Workbook(File.Contents(SourceWorkbookPath), null, true),',
        '    Sheet = Source{[Item="Fact_Housing_AMI",Kind="Sheet"]}[Data],',
        '    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),',
        '    Selected = Table.SelectColumns(Headers, {"Fact_AMI_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Structure_Type", "AMI_0_to_30_Pct_Units", "AMI_31_to_50_Pct_Units", "AMI_51_to_80_Pct_Units", "AMI_81_to_100_Pct_Units", "AMI_101_to_120_Pct_Units", "AMI_Greater_120_Pct_Units", "Total_AMI_Units", "Reconciliation_Status"}, MissingField.Error),',
        '    Typed = Table.TransformColumnTypes(Selected,{',
        '        {"Fact_AMI_Key", type text}, {"Jurisdiction_ID", type text}, {"Year", Int64.Type},',
        '        {"Jurisdiction_Name", type text}, {"Structure_Type", type text},',
        '        {"AMI_0_to_30_Pct_Units", Int64.Type}, {"AMI_31_to_50_Pct_Units", Int64.Type},',
        '        {"AMI_51_to_80_Pct_Units", Int64.Type}, {"AMI_81_to_100_Pct_Units", Int64.Type},',
        '        {"AMI_101_to_120_Pct_Units", Int64.Type}, {"AMI_Greater_120_Pct_Units", Int64.Type},',
        '        {"Total_AMI_Units", Int64.Type}, {"Reconciliation_Status", type text}',
        '    })',
        'in',
        '    Typed'
    ]
    with open(os.path.join(POWERBI_DIR, "power_query_m_scripts.pq"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    build_pbip()
