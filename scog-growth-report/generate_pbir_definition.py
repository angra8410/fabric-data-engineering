import json
import os
import shutil
from pathlib import Path

# Paths
BASE_DIR = Path(r"c:\Users\antoi\Downloads\All_Files\projects\proyectos-data-engineering\scog-growth-report")
REPORT_DIR = BASE_DIR / "powerbi" / "SCOG_Growth_Monitoring_Report" / "SCOG_Growth_Monitoring_Report.Report"
DEF_DIR = REPORT_DIR / "definition"
PAGES_DIR = DEF_DIR / "pages"
STATIC_RES_DIR = REPORT_DIR / "StaticResources" / "SharedResources" / "BaseThemes"

SCHEMA_VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_PAGES_META = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"
SCHEMA_REPORT = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json"
SCHEMA_VERSION = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json"
SCHEMA_DEF_PROPS = "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json"

def make_measure_proj(entity, prop):
    return {
        "field": {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": prop
            }
        },
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop
    }

def make_col_proj(entity, prop):
    return {
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": prop
            }
        },
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop
    }

def make_agg_proj(entity, prop, func=0, func_name="Sum"):
    return {
        "field": {
            "Aggregation": {
                "Expression": {
                    "Column": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": prop
                    }
                },
                "Function": func
            }
        },
        "queryRef": f"{func_name}({entity}.{prop})",
        "nativeQueryRef": f"{func_name} of {prop}"
    }

def make_title_vco(text):
    return {
        "title": [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{text}'"}}}
            }
        }]
    }

import uuid

def make_year_range_filter(min_year, max_year):
    f_id = f"F_{uuid.uuid4().hex[:16]}"
    return {
        "name": f_id,
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": "Dim_CalendarYear"}},
                "Property": "Year"
            }
        },
        "type": "Advanced",
        "filter": {
            "Version": 2,
            "From": [{"Name": "d", "Entity": "Dim_CalendarYear", "Type": 0}],
            "Where": [{
                "Condition": {
                    "Between": {
                        "Expression": {
                            "Column": {
                                "Expression": {"SourceRef": {"Source": "d"}},
                                "Property": "Year"
                            }
                        },
                        "LowerBound": {"Literal": {"Value": f"{min_year}L"}},
                        "UpperBound": {"Literal": {"Value": f"{max_year}L"}}
                    }
                }
            }]
        },
        "howCreated": "User"
    }

def make_textbox(name, x, y, w, h, z, title, subtitle=None):
    runs = [{
        "value": title,
        "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "15pt", "color": "#004B87"}
    }]
    if subtitle:
        runs.append({
            "value": f"\n{subtitle}",
            "textStyle": {"fontFamily": "Segoe UI", "fontSize": "9pt", "color": "#475569"}
        })
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": runs,
                            "horizontalTextAlignment": "left"
                        }]
                    }
                }]
            }
        }
    }

def make_footer(name, x, y, w, h, z, text):
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": [{
                                "value": text,
                                "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8pt", "color": "#64748B"}
                            }],
                            "horizontalTextAlignment": "left"
                        }]
                    }
                }]
            }
        }
    }

def make_card(name, x, y, w, h, z, entity, measure_name):
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "cardVisual",
            "query": {
                "queryState": {
                    "Data": {
                        "projections": [make_measure_proj(entity, measure_name)]
                    }
                }
            }
        }
    }

def make_slicer(name, x, y, w, h, z, entity, col_name, header_text, default_val=None):
    vis = {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [make_col_proj(entity, col_name)]
                    }
                }
            },
            "objects": {
                "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
                "header": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": f"'{header_text}'"}}}}}]
            }
        }
    }
    if default_val is not None:
        lit_val = f"{default_val}L" if isinstance(default_val, int) else f"'{default_val}'"
        vis["visual"]["objects"]["general"] = [{
            "properties": {
                "filter": {
                    "filter": {
                        "Version": 2,
                        "From": [{"Name": "d", "Entity": entity, "Type": 0}],
                        "Where": [{
                            "Condition": {
                                "In": {
                                    "Expressions": [{
                                        "Column": {
                                            "Expression": {"SourceRef": {"Source": "d"}},
                                            "Property": col_name
                                        }
                                    }],
                                    "Values": [[{"Literal": {"Value": lit_val}}]]
                                }
                            }
                        }]
                    }
                }
            }
        }]
    return vis

def make_cartesian(name, vtype, x, y, w, h, z, cat_proj, y_projs, title, filters=None):
    vis = {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": vtype,
            "query": {
                "queryState": {
                    "Category": {"projections": [cat_proj]},
                    "Y": {"projections": y_projs}
                }
            },
            "visualContainerObjects": make_title_vco(title)
        }
    }
    if filters:
        vis["filterConfig"] = {"filters": filters}
    return vis

def make_table(name, x, y, w, h, z, projs, title):
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "tableEx",
            "query": {
                "queryState": {
                    "Values": {"projections": projs}
                }
            },
            "visualContainerObjects": make_title_vco(title)
        }
    }

def make_matrix(name, x, y, w, h, z, row_projs, val_projs, title):
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "matrix",
            "query": {
                "queryState": {
                    "Rows": {"projections": row_projs},
                    "Values": {"projections": val_projs}
                }
            },
            "visualContainerObjects": make_title_vco(title)
        }
    }

def make_azure_map(name, x, y, w, h, z, cat_proj, lat_proj, lon_proj, size_proj, title):
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "azureMap",
            "query": {
                "queryState": {
                    "Category": {"projections": [cat_proj]},
                    "Y": {"projections": [lat_proj]},
                    "X": {"projections": [lon_proj]},
                    "Size": {"projections": [size_proj]}
                }
            },
            "visualContainerObjects": make_title_vco(title)
        }
    }

print("Setting up report directory...")
REPORT_DIR.mkdir(parents=True, exist_ok=True)
DEF_DIR.mkdir(parents=True, exist_ok=True)

# Completely clean existing pages directory to remove long path names
if PAGES_DIR.exists():
    shutil.rmtree(PAGES_DIR)
PAGES_DIR.mkdir(parents=True, exist_ok=True)

STATIC_RES_DIR.mkdir(parents=True, exist_ok=True)

# Copy base theme from scratch sample if exists
scratch_theme = Path(r"C:\Users\antoi\.gemini\antigravity-ide\brain\455c9708-5535-4649-a57d-85898ca28d65\scratch\sample_report\Sample.Report\StaticResources\SharedResources\BaseThemes\Fluent2-CY26SU10.json")
if scratch_theme.exists():
    shutil.copy2(scratch_theme, STATIC_RES_DIR / "Fluent2-CY26SU10.json")
else:
    with open(STATIC_RES_DIR / "Fluent2-CY26SU10.json", "w", encoding="utf-8") as f:
        json.dump({"name": "Fluent2-CY26SU10", "dataColors": ["#004B87", "#008080", "#2E7D32", "#C0392B", "#D97706", "#6B21A8", "#1E293B", "#0891B2"]}, f, indent=2)

# 1. definition.pbir
with open(REPORT_DIR / "definition.pbir", "w", encoding="utf-8") as f:
    json.dump({
        "$schema": SCHEMA_DEF_PROPS,
        "version": "4.0",
        "datasetReference": {
            "byPath": {
                "path": "../SCOG_Growth_Monitoring_Report.SemanticModel"
            }
        }
    }, f, indent=2)

# 2. version.json
with open(DEF_DIR / "version.json", "w", encoding="utf-8") as f:
    json.dump({
        "$schema": SCHEMA_VERSION,
        "version": "2.0.0"
    }, f, indent=2)

# 3. report.json
with open(DEF_DIR / "report.json", "w", encoding="utf-8") as f:
    json.dump({
        "$schema": SCHEMA_REPORT,
        "themeCollection": {
            "baseTheme": {
                "name": "Fluent2-CY26SU10",
                "reportVersionAtImport": {
                    "visual": "2.11.0",
                    "report": "3.4.0",
                    "page": "2.3.1"
                },
                "type": "SharedResources"
            }
        },
        "resourcePackages": [
            {
                "name": "SharedResources",
                "type": "SharedResources",
                "items": [
                    {
                        "name": "Fluent2-CY26SU10",
                        "path": "BaseThemes/Fluent2-CY26SU10.json",
                        "type": "BaseTheme"
                    }
                ]
            }
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True
        }
    }, f, indent=2)

# Use SHORT IDs: p1, p2, p3, p4 and v01..v11 to guarantee path lengths < 210 chars on Windows!
pages_data = [
    {
        "id": "p1",
        "displayName": "1. Executive Summary & Regional Dashboard",
        "visuals": [
            make_textbox(
                "v01", 20, 15, 1240, 60, 10,
                "REGIONAL EXECUTIVE SUMMARY & GMA 2045 TARGET TRAJECTORY",
                "Baseline Calibration Year: 2025 | WA OFM April 1 Population, ESD QCEW Employment & GMA Ordinance O20250002"
            ),
            make_slicer("v02", 20, 85, 180, 80, 20, "Dim_CalendarYear", "Year", "Reporting Year", default_val=2025),
            make_card("v03", 210, 85, 240, 80, 20, "_Measures", "Total Population"),
            make_card("v04", 460, 85, 240, 80, 20, "_Measures", "Net New Housing Units"),
            make_card("v05", 710, 85, 260, 80, 20, "_Measures", "Covered Employment QCEW"),
            make_card("v06", 980, 85, 280, 80, 20, "_Measures", "Housing Target Progress %"),
            make_cartesian(
                "v07", "lineChart", 20, 175, 615, 265, 20,
                make_col_proj("Dim_CalendarYear", "Year"),
                [make_measure_proj("_Measures", "Total Population")],
                "Regional Population Trajectory (2020-2025)",
                filters=[make_year_range_filter(2020, 2025)]
            ),
            make_cartesian(
                "v08", "clusteredColumnChart", 645, 175, 615, 265, 20,
                make_col_proj("Dim_CalendarYear", "Year"),
                [
                    make_measure_proj("_Measures", "Single-Family Permits"),
                    make_measure_proj("_Measures", "Multi-Family Permits"),
                    make_measure_proj("_Measures", "ADU Permits")
                ],
                "Annual Residential Units Permitted by Typology (2010-2025)",
                filters=[make_year_range_filter(2010, 2025)]
            ),
            make_table(
                "v09", 20, 450, 1240, 215, 20,
                [
                    make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                    make_col_proj("Dim_Jurisdiction", "Jurisdiction_Type"),
                    make_measure_proj("_Measures", "Total Population"),
                    make_measure_proj("_Measures", "2045 Population Target"),
                    make_measure_proj("_Measures", "Cumulative Net Housing Units (2020-Present)"),
                    make_measure_proj("_Measures", "2045 Housing Target Units"),
                    make_measure_proj("_Measures", "Housing Target Progress %")
                ],
                "Jurisdictional Summary Table (2025 Baseline Calibration vs. Adopted GMA 2045 Targets)"
            ),
            make_footer(
                "v10", 20, 675, 1240, 35, 10,
                "Data Sources: WA OFM April 1 Population (2020-2025) | ESD QCEW Covered Employment | Ordinance O20250002 | SCOG Annual Growth Monitoring Report"
            )
        ]
    },
    {
        "id": "p2",
        "displayName": "2. Housing Deep-Dive",
        "visuals": [
            make_textbox(
                "v01", 20, 15, 1240, 60, 10,
                "HOUSING PRODUCTION, TYPOLOGY & AFFORDABILITY (AMI) DEEP-DIVE",
                "Residential Construction Trends, Housing Stock Diversity & Affordable Housing Allocations (HB 1220 / GMA Targets) — PRELIMINARY: Local Jurisdiction Housing Needs Assessments due Oct 20, 2025"
            ),
            make_slicer("v02", 20, 85, 260, 80, 20, "Dim_Jurisdiction", "Jurisdiction_Name", "Jurisdiction Filter"),
            make_card("v03", 290, 85, 220, 80, 20, "_Measures", "Net New Housing Units"),
            make_card("v04", 520, 85, 220, 80, 20, "_Measures", "Single-Family Permits"),
            make_card("v05", 750, 85, 220, 80, 20, "_Measures", "Multi-Family Permits"),
            make_card("v06", 980, 85, 280, 80, 20, "_Measures", "ADU Permits"),
            make_cartesian(
                "v07", "stackedAreaChart", 20, 175, 780, 235, 20,
                make_col_proj("Dim_CalendarYear", "Year"),
                [
                    make_measure_proj("_Measures", "Single-Family Permits"),
                    make_measure_proj("_Measures", "Multi-Family Permits"),
                    make_measure_proj("_Measures", "ADU Permits")
                ],
                "Historical Permitted Housing Units by Typology (2010-2025)",
                filters=[make_year_range_filter(2010, 2025)]
            ),
            make_cartesian(
                "v08", "clusteredBarChart", 810, 175, 450, 235, 20,
                make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                [
                    make_measure_proj("_Measures", "Single-Family Permits"),
                    make_measure_proj("_Measures", "Multi-Family Permits")
                ],
                "Single-Family vs. Multi-Family Permits by Jurisdiction"
            ),
            make_cartesian(
                "v09", "clusteredBarChart", 20, 420, 620, 245, 20,
                make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                [
                    make_measure_proj("_Measures", "Low Income AMI Units (<80% AMI)"),
                    make_measure_proj("_Measures", "Moderate to High Income AMI Units (>80% AMI)")
                ],
                "Allocated Housing Units by Area Median Income (AMI) Income Band [HB 1220 Target Allocations]"
            ),
            make_matrix(
                "v10", 650, 420, 610, 245, 20,
                [make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name")],
                [
                    make_measure_proj("_Measures", "Single-Family Permits"),
                    make_measure_proj("_Measures", "Multi-Family Permits"),
                    make_measure_proj("_Measures", "ADU Permits"),
                    make_measure_proj("_Measures", "Demolished Units"),
                    make_measure_proj("_Measures", "Net New Housing Units"),
                    make_measure_proj("_Measures", "Total Permit Valuation")
                ],
                "Jurisdictional Housing Permitting Reconciliation Matrix"
            ),
            make_footer(
                "v11", 20, 675, 1240, 35, 10,
                "Data Sources: Local Building Department Annual Submissions | OFM Housing Estimates. Note: AMI income band allocations are preliminary statewide default shares pending local jurisdiction housing needs assessments due October 20, 2025."
            )
        ]
    },
    {
        "id": "p3",
        "displayName": "3. Population & Employment Overview",
        "visuals": [
            make_textbox(
                "v01", 20, 15, 1240, 60, 10,
                "POPULATION GROWTH & EMPLOYMENT BENCHMARKS",
                "Regional Demographic Change, Jurisdictional Target Progress & CAI Covered Employment Benchmark"
            ),
            make_cartesian(
                "v02", "clusteredBarChart", 20, 85, 615, 275, 20,
                make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                [
                    make_measure_proj("_Measures", "Total Population"),
                    make_measure_proj("_Measures", "2045 Population Target")
                ],
                "Population Progress toward 2045 GMA Target by Jurisdiction"
            ),
            make_cartesian(
                "v03", "clusteredBarChart", 645, 85, 615, 275, 20,
                make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                [make_measure_proj("_Measures", "YoY Population Change")],
                "Net Annual Population Change (OFM 2024-2025 Calibration)"
            ),
            make_cartesian(
                "v04", "lineChart", 20, 370, 700, 295, 20,
                make_col_proj("Dim_CAI_Employment_Benchmark", "Year"),
                [make_agg_proj("Dim_CAI_Employment_Benchmark", "Covered_Employment_QCEW")],
                "Official ESD Covered Employment Benchmark Series (1999-2022) [Total Multiplier Pending SCOG Confirmation]"
            ),
            make_table(
                "v05", 730, 370, 530, 295, 20,
                [
                    make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                    make_measure_proj("_Measures", "2022 Employment Baseline"),
                    make_measure_proj("_Measures", "2045 Employment Target")
                ],
                "Adopted GMA 2045 Employment Targets by Jurisdiction (Planning Allocations Only - No Annual Actuals)"
            ),
            make_footer(
                "v06", 20, 675, 1240, 35, 10,
                "Sources: WA OFM April 1 Population | ESD QCEW Covered Employment | Ordinance O20250002. Note: Total Employment multiplier is preliminary and withheld pending formal confirmation with SCOG staff."
            )
        ]
    },
    {
        "id": "p4",
        "displayName": "4. Jurisdictional Comparison & Spatial Mapping",
        "visuals": [
            make_textbox(
                "v01", 20, 15, 1240, 60, 10,
                "JURISDICTIONAL COMPARISON & SPATIAL DISTRIBUTION",
                "Incorporated Cities vs. UGAs vs. Rural Areas — Countywide Spatial Map and Planning Shares"
            ),
            make_azure_map(
                "v02", 20, 85, 640, 580, 20,
                make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                make_agg_proj("Dim_Jurisdiction", "Latitude", func=1, func_name="Avg"),
                make_agg_proj("Dim_Jurisdiction", "Longitude", func=1, func_name="Avg"),
                make_measure_proj("_Measures", "Total Population"),
                "Regional Jurisdictions & UGAs (Official USGS/Census 2020 Centroids)"
            ),
            make_matrix(
                "v03", 670, 85, 590, 325, 20,
                [
                    make_col_proj("Dim_Jurisdiction", "Jurisdiction_Type"),
                    make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name")
                ],
                [
                    make_measure_proj("_Measures", "Total Population"),
                    make_measure_proj("_Measures", "Jurisdiction Share of Regional Population %"),
                    make_measure_proj("_Measures", "Cumulative Net Housing Units (2020-Present)"),
                    make_measure_proj("_Measures", "Housing Target Progress %")
                ],
                "Growth & Allocation Metrics by Jurisdiction Classification"
            ),
            make_cartesian(
                "v04", "clusteredBarChart", 670, 420, 590, 245, 20,
                make_col_proj("Dim_Jurisdiction", "Jurisdiction_Name"),
                [
                    make_measure_proj("_Measures", "Jurisdiction Share of Regional Population %"),
                    make_measure_proj("_Measures", "Jurisdiction Share of Regional Housing %")
                ],
                "Jurisdictional Shares of Regional Population vs. Housing Allocations"
            ),
            make_footer(
                "v05", 20, 675, 1240, 35, 10,
                "Centroid Coordinates: Official USGS GNIS / US Census Bureau 2020 Municipal Centers & UGA Centroids. 'Unincorporated Skagit County' represents rural balance outside designated UGAs per Ordinance O20250002."
            )
        ]
    }
]

# Write pages.json
pages_meta = {
    "$schema": SCHEMA_PAGES_META,
    "pageOrder": [p["id"] for p in pages_data],
    "activePageName": pages_data[0]["id"]
}
with open(PAGES_DIR / "pages.json", "w", encoding="utf-8") as f:
    json.dump(pages_meta, f, indent=2)

# Write each page and its visuals
max_path_len = 0
longest_path = ""
for p in pages_data:
    pid = p["id"]
    p_dir = PAGES_DIR / pid
    p_dir.mkdir(parents=True, exist_ok=True)
    
    # page.json
    page_json = {
        "$schema": SCHEMA_PAGE,
        "name": pid,
        "displayName": p["displayName"],
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280
    }
    with open(p_dir / "page.json", "w", encoding="utf-8") as f:
        json.dump(page_json, f, indent=2)
    
    # visuals
    v_dir = p_dir / "visuals"
    v_dir.mkdir(parents=True, exist_ok=True)
    for v in p["visuals"]:
        v_name = v["name"]
        item_v_dir = v_dir / v_name
        item_v_dir.mkdir(parents=True, exist_ok=True)
        v_file = item_v_dir / "visual.json"
        with open(v_file, "w", encoding="utf-8") as f:
            json.dump(v, f, indent=2)
        cur_len = len(str(v_file.resolve()))
        if cur_len > max_path_len:
            max_path_len = cur_len
            longest_path = str(v_file.resolve())

# Remove legacy root report.json if present
legacy_report_json = REPORT_DIR / "report.json"
if legacy_report_json.exists():
    legacy_report_json.unlink()

print(f"Rebuild completed with short IDs! Created {len(pages_data)} pages.")
print(f"Longest path: {max_path_len} chars (< 260 MAX_PATH!):")
print(f"  {longest_path}")
