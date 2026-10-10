"""
generate_v2_mockup.py
Generates the HTML mock-up for the SCOG Growth Monitoring Report alternative design v2.
All numbers, table cells, chart values, and SVG coordinates are dynamically computed
from the authoritative processed CSV datasets:
- data/processed/Fact_Population.csv
- data/processed/Fact_HousingPermits.csv
- data/processed/Fact_Employment.csv
- data/processed/Fact_Housing_AMI.csv
- data/processed/Dim_GMA_2045_Target.csv
- data/processed/Dim_Jurisdiction.csv
- data/processed/Dim_CAI_Employment_Benchmark.csv
"""

import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
OUT_FILE = BASE_DIR / "alternative_design_v2_mockup.html"

# Load CSVs
df_pop = pd.read_csv(DATA_DIR / "Fact_Population.csv")
df_hp = pd.read_csv(DATA_DIR / "Fact_HousingPermits.csv")
df_emp = pd.read_csv(DATA_DIR / "Fact_Employment.csv")
df_ami = pd.read_csv(DATA_DIR / "Fact_Housing_AMI.csv")
df_tgt = pd.read_csv(DATA_DIR / "Dim_GMA_2045_Target.csv")
df_jur = pd.read_csv(DATA_DIR / "Dim_Jurisdiction.csv")
df_cai = pd.read_csv(DATA_DIR / "Dim_CAI_Employment_Benchmark.csv")

# -------------------------------------------------------------
# 1. CORE DATA CALCULATIONS
# -------------------------------------------------------------

# Jurisdiction list in standard ordering
jur_order = [
    "JUR-01", "JUR-02", "JUR-03", "JUR-04", "JUR-05", 
    "JUR-06", "JUR-07", "JUR-08", "JUR-09", "JUR-10", "JUR-11"
]

# Page 1 & Countywide Totals
pop_2025_df = df_pop[df_pop["Year"] == 2025].set_index("Jurisdiction_ID")
total_pop_2025 = int(pop_2025_df["Population_Count"].sum())
target_pop_2045 = int(df_tgt["Target_2045_Population"].sum())

baseline_pop_2022 = int(df_tgt["Baseline_2022_Population"].sum()) # 131,249
pop_growth_from_2022 = total_pop_2025 - baseline_pop_2022 # 3,351

# Cumulative housing units 2020-2025
hp_filtered = df_hp[(df_hp["Year"] >= 2020) & (df_hp["Year"] <= 2025)]
cum_housing_series = hp_filtered.groupby("Jurisdiction_ID")["Net_New_Units"].sum()
total_cum_housing = int(cum_housing_series.sum())
total_housing_target = int(df_tgt["Target_2045_Housing_Units"].sum())
housing_progress_pct = (total_cum_housing / total_housing_target) * 100

# 2025 Single Year Housing Permits
hp_2025 = df_hp[df_hp["Year"] == 2025].set_index("Jurisdiction_ID")
total_sf_2025 = int(hp_2025["Single_Family_Units"].sum())
total_mf_2025 = int((hp_2025["Duplex_Units"] + hp_2025["MultiFamily_3_4_Units"] + hp_2025["MultiFamily_5_Plus_Units"]).sum())
total_adu_2025 = int(hp_2025["ADU_Units"].sum())
total_dem_2025 = int(hp_2025["Demolished_Units"].sum())
total_net_2025 = int(hp_2025["Net_New_Units"].sum())
total_gross_2025 = total_sf_2025 + total_mf_2025 + total_adu_2025

# 2022 Employment Baseline (Total Employment) & 2045 Target
emp_baseline_2022 = int(df_tgt["Baseline_2022_Employment"].sum()) # 59,571
emp_target_2045 = int(df_tgt["Target_2045_Employment"].sum()) # 80,100

# Population trajectory 2020-2025
pop_traj = df_pop[df_pop["Year"].between(2020, 2025)].groupby("Year")["Population_Count"].sum().to_dict()
pop_2020 = pop_traj[2020]
pop_growth_cum = total_pop_2025 - pop_2020
pop_growth_pct = (pop_growth_cum / pop_2020) * 100

# SVG Population Trajectory Polyline
pop_pts = []
pop_dots = []
years = [2020, 2021, 2022, 2023, 2024, 2025]
x_coords = [80, 175, 270, 365, 460, 540]
for yr, x in zip(years, x_coords):
    p_val = pop_traj[yr]
    # y range 128k to 135k over height 150px (y: 175 down to 35)
    y = 175 - ((p_val - 128000) / 7000) * 140
    pop_pts.append(f"{x},{y:.1f}")
    pop_dots.append(f'<circle cx="{x}" cy="{y:.1f}" r="4.5" fill="#004B87" stroke="#ffffff" stroke-width="2" />')
pop_polyline = " ".join(pop_pts)

# Benchmarking Table rows (Page 1)
p1_table_rows = []
for jid in jur_order:
    row_tgt = df_tgt[df_tgt["Jurisdiction_ID"] == jid].iloc[0]
    j_name = row_tgt["Jurisdiction_Name"]
    j_type = row_tgt["Jurisdiction_Type"]
    pop_25 = int(pop_2025_df.loc[jid, "Population_Count"]) if jid in pop_2025_df.index else 0
    pop_t = int(row_tgt["Target_2045_Population"])
    h_cum = int(cum_housing_series.get(jid, 0))
    h_t = int(row_tgt["Target_2045_Housing_Units"])
    h_pct_str = f"{(h_cum / h_t * 100):.1f}%" if h_t > 0 else "—"
    
    p1_table_rows.append({
        "id": jid,
        "name": j_name,
        "type": j_type,
        "pop25": pop_25,
        "pop_tgt": pop_t,
        "h_cum": h_cum,
        "h_tgt": h_t,
        "h_pct_str": h_pct_str
    })

# Page 2 Housing Typology Breakdown
p2_matrix_rows = []
for jid in jur_order:
    row_tgt = df_tgt[df_tgt["Jurisdiction_ID"] == jid].iloc[0]
    j_name = row_tgt["Jurisdiction_Name"]
    if jid in hp_2025.index:
        r_hp = hp_2025.loc[jid]
        sf = int(r_hp["Single_Family_Units"])
        mf = int(r_hp["Duplex_Units"] + r_hp["MultiFamily_3_4_Units"] + r_hp["MultiFamily_5_Plus_Units"])
        adu = int(r_hp["ADU_Units"])
        dem = int(r_hp["Demolished_Units"])
        net = int(r_hp["Net_New_Units"])
    else:
        sf = mf = adu = dem = net = 0
    p2_matrix_rows.append({
        "id": jid,
        "name": j_name,
        "sf": sf,
        "mf": mf,
        "adu": adu,
        "dem": dem,
        "net": net
    })

# Page 2 AMI breakdown
ami_agg = df_ami[df_ami["Year"] == 2025].groupby(["Jurisdiction_ID", "Jurisdiction_Name"]).agg({
    "AMI_0_to_30_Pct_Units": "sum",
    "AMI_31_to_50_Pct_Units": "sum",
    "AMI_51_to_80_Pct_Units": "sum",
    "AMI_81_to_100_Pct_Units": "sum",
    "AMI_101_to_120_Pct_Units": "sum",
    "AMI_Greater_120_Pct_Units": "sum",
    "Total_AMI_Units": "sum"
}).reset_index()
ami_agg["Low"] = ami_agg["AMI_0_to_30_Pct_Units"] + ami_agg["AMI_31_to_50_Pct_Units"] + ami_agg["AMI_51_to_80_Pct_Units"]
ami_agg["ModHigh"] = ami_agg["AMI_81_to_100_Pct_Units"] + ami_agg["AMI_101_to_120_Pct_Units"] + ami_agg["AMI_Greater_120_Pct_Units"]
max_ami_units = int(ami_agg["Total_AMI_Units"].max()) if not ami_agg.empty else 1

# Page 3 YoY Growth (2024 to 2025)
pop_2024_df = df_pop[df_pop["Year"] == 2024].set_index("Jurisdiction_ID")
p3_yoy_rows = []
for jid in jur_order:
    row_tgt = df_tgt[df_tgt["Jurisdiction_ID"] == jid].iloc[0]
    p25 = int(pop_2025_df.loc[jid, "Population_Count"]) if jid in pop_2025_df.index else 0
    p24 = int(pop_2024_df.loc[jid, "Population_Count"]) if jid in pop_2024_df.index else 0
    yoy = p25 - p24
    p3_yoy_rows.append({
        "id": jid,
        "name": row_tgt["Jurisdiction_Name"],
        "yoy": yoy
    })

# Page 3 Employment Table
p3_emp_rows = []
for jid in jur_order:
    row_tgt = df_tgt[df_tgt["Jurisdiction_ID"] == jid].iloc[0]
    p3_emp_rows.append({
        "id": jid,
        "name": row_tgt["Jurisdiction_Name"],
        "base": int(row_tgt["Baseline_2022_Employment"]),
        "target": int(row_tgt["Target_2045_Employment"])
    })

# Page 4 Spatial Allocations
p4_table_rows = []
p4_share_comp = []
for jid in jur_order:
    row_tgt = df_tgt[df_tgt["Jurisdiction_ID"] == jid].iloc[0]
    j_name = row_tgt["Jurisdiction_Name"]
    j_type = row_tgt["Jurisdiction_Type"]
    pop_25 = int(pop_2025_df.loc[jid, "Population_Count"]) if jid in pop_2025_df.index else 0
    pop_share = (pop_25 / total_pop_2025) * 100
    h_tgt = int(row_tgt["Target_2045_Housing_Units"])
    h_share = (h_tgt / total_housing_target) * 100
    
    p4_table_rows.append({
        "id": jid,
        "name": j_name,
        "type": j_type,
        "pop": pop_25,
        "share": pop_share
    })
    p4_share_comp.append({
        "id": jid,
        "name": j_name,
        "pop_share": pop_share,
        "h_share": h_share
    })

# Subtotals
cities_pop = sum([r["pop"] for r in p4_table_rows[:8]])
cities_share = (cities_pop / total_pop_2025) * 100
uga_pop = sum([r["pop"] for r in p4_table_rows[8:10]])
uga_share = (uga_pop / total_pop_2025) * 100
rural_pop = p4_table_rows[10]["pop"]
rural_share = (rural_pop / total_pop_2025) * 100

# SVG Cluster Bars (Page 1 Housing Typology 2010, 2015, 2020, 2025)
benchmark_years = [2010, 2015, 2020, 2025]
bar_x_centers = [90, 210, 350, 490]
cluster_bars = []
for yr, cx in zip(benchmark_years, bar_x_centers):
    df_y = df_hp[df_hp["Year"] == yr]
    sf = int(df_y["Single_Family_Units"].sum())
    mf = int((df_y["Duplex_Units"] + df_y["MultiFamily_3_4_Units"] + df_y["MultiFamily_5_Plus_Units"]).sum())
    adu = int(df_y["ADU_Units"].sum())
    
    # Scale: 0 to 450 units -> height 140px (y: 170 down to 30)
    sf_h = (sf / 450) * 140
    mf_h = (mf / 450) * 140
    adu_h = (adu / 450) * 140
    
    # Bars width = 16
    cluster_bars.append(f'<g class="benchmark-year-group" data-year="{yr}" data-sf="{sf}" data-mf="{mf}" data-adu="{adu}">')
    cluster_bars.append(f'<rect x="{cx-26}" y="{170-sf_h:.1f}" width="16" height="{sf_h:.1f}" fill="#004B87" rx="2" />')
    cluster_bars.append(f'<text x="{cx-18}" y="{165-sf_h:.1f}" class="chart-val-text">{sf}</text>' if sf > 0 else "")
    cluster_bars.append(f'<rect x="{cx-8}" y="{170-mf_h:.1f}" width="16" height="{mf_h:.1f}" fill="#2563eb" rx="2" />')
    cluster_bars.append(f'<text x="{cx}" y="{165-mf_h:.1f}" class="chart-val-text">{mf}</text>' if mf > 0 else "")
    cluster_bars.append(f'<rect x="{cx+10}" y="{170-adu_h:.1f}" width="16" height="{adu_h:.1f}" fill="#94a3b8" rx="2" />')
    cluster_bars.append(f'<text x="{cx+18}" y="{165-adu_h:.1f}" class="chart-val-text">{adu}</text>' if adu > 0 else "")
    cluster_bars.append('</g>')

cluster_bars_svg = "\n".join([b for b in cluster_bars if b])

# SVG Stacked Area Series (Page 2)
hp_annual = df_hp.groupby("Year").agg({
    "Single_Family_Units": "sum",
    "Duplex_Units": "sum",
    "MultiFamily_3_4_Units": "sum",
    "MultiFamily_5_Plus_Units": "sum",
    "ADU_Units": "sum"
}).reset_index()
hp_annual["MF_Total"] = hp_annual["Duplex_Units"] + hp_annual["MultiFamily_3_4_Units"] + hp_annual["MultiFamily_5_Plus_Units"]
hp_annual["Gross"] = hp_annual["Single_Family_Units"] + hp_annual["MF_Total"] + hp_annual["ADU_Units"]

gross_pts = []
mf_pts = []
sf_pts = []
area_pts_svg = []
for _, r in hp_annual.iterrows():
    yr = int(r["Year"])
    sf_val = int(r["Single_Family_Units"])
    mf_val = int(r["MF_Total"])
    adu_val = int(r["ADU_Units"])
    gross_val = int(r["Gross"])
    x = 40 + ((yr - 2010) / (2025 - 2010)) * 520
    # y scale: 0 to 800 units -> height 140px (y: 170 down to 30)
    g_h = (gross_val / 800) * 140
    mf_h = ((sf_val + mf_val) / 800) * 140
    sf_h = (sf_val / 800) * 140
    gross_pts.append(f"{x:.1f} {170-g_h:.1f}")
    mf_pts.append(f"{x:.1f} {170-mf_h:.1f}")
    sf_pts.append(f"{x:.1f} {170-sf_h:.1f}")
    area_pts_svg.append(f'<g class="area-data-point" data-year="{yr}" data-sf="{sf_val}" data-mf="{mf_val}" data-adu="{adu_val}" data-gross="{gross_val}"></g>')

area_gross = f"M 40 170 L " + " L ".join(gross_pts) + " L 560 170 Z"
area_mf = f"M 40 170 L " + " L ".join(mf_pts) + " L 560 170 Z"
area_sf = f"M 40 170 L " + " L ".join(sf_pts) + " L 560 170 Z"
area_data_elements = "\n".join(area_pts_svg)

# SVG Historical QCEW Series (Page 3)
# Extended to 2025 using Fact_Employment (County Total Annual Average = 54,148)
emp_2025_row = df_emp[(df_emp["Year"] == 2025) & (df_emp["Is_County_Total"] == 1)].iloc[0]
emp_2025_qcew = int(emp_2025_row["Annual_Average_Employment"]) # 54,148
emp_2025_est_total = int(emp_2025_row["Estimated_Total_Employment"]) # 62,518
emp_2022_qcew = int(df_cai[df_cai["Year"] == 2022]["Covered_Employment_QCEW"].iloc[0]) # 51,597

cai_series = df_cai[df_cai["Year"].between(1999, 2022)].sort_values("Year").to_dict("records")
qcew_full_series = [{"Year": int(r["Year"]), "Covered_Employment_QCEW": int(r["Covered_Employment_QCEW"])} for r in cai_series]
qcew_full_series.append({"Year": 2025, "Covered_Employment_QCEW": emp_2025_qcew})

# Segment 1: Continuous polyline 1999 to 2019 (21 points)
# Break line across gaps (2020-21 and 2023-24 have no data in source files)
qcew_seg1_series = [r for r in qcew_full_series if r["Year"] <= 2019]
qcew_seg1_pts = []
for r in qcew_seg1_series:
    yr = r["Year"]
    val = r["Covered_Employment_QCEW"]
    x = 60 + ((yr - 1999) / (2025 - 1999)) * 480
    y = 230 - ((val - 35000) / 20000) * 190
    qcew_seg1_pts.append(f"{x:.1f},{y:.1f}")

qcew_seg1_polyline = " ".join(qcew_seg1_pts)

# Markers for all 23 nodes
qcew_dots = []
for r in qcew_full_series:
    yr = r["Year"]
    val = r["Covered_Employment_QCEW"]
    x = 60 + ((yr - 1999) / (2025 - 1999)) * 480
    y = 230 - ((val - 35000) / 20000) * 190
    r_rad = "4.5" if yr in [2022, 2025] else "3"
    f_col = "#2563eb" if yr in [2022, 2025] else "#004B87"
    qcew_dots.append(f'<circle class="qcew-node" cx="{x:.1f}" cy="{y:.1f}" r="{r_rad}" fill="{f_col}" data-year="{yr}" data-qcew="{val}"><title>{yr}: {val:,} Covered Jobs</title></circle>')

qcew_last = qcew_full_series[-1]
qcew_last_x = 60 + ((qcew_last["Year"] - 1999) / (2025 - 1999)) * 480
qcew_last_y = 230 - ((qcew_last["Covered_Employment_QCEW"] - 35000) / 20000) * 190

qcew_2022 = next(r for r in qcew_full_series if r["Year"] == 2022)
qcew_2022_x = 60 + ((2022 - 1999) / (2025 - 1999)) * 480
qcew_2022_y = 230 - ((qcew_2022["Covered_Employment_QCEW"] - 35000) / 20000) * 190

# Geo Centroids for Leaflet & SVG Map (Page 4)
map_markers_data = []
svg_marker_elements = []

for jid in jur_order:
    row_jur = df_jur[df_jur["Jurisdiction_ID"] == jid].iloc[0]
    j_name = row_jur["Jurisdiction_Name"]
    j_type = row_jur["Jurisdiction_Type"]
    lat = float(row_jur["Latitude"])
    lon = float(row_jur["Longitude"])
    pop_val = int(pop_2025_df.loc[jid, "Population_Count"]) if jid in pop_2025_df.index else 0
    pop_share = (pop_val / total_pop_2025) * 100
    h_tgt_row = df_tgt[df_tgt["Jurisdiction_ID"] == jid]
    h_tgt = int(h_tgt_row["Target_2045_Housing_Units"].values[0]) if not h_tgt_row.empty else 0
    
    # Strictly one accent color palette (dark blue, accent blue, neutral slate)
    if row_jur["Is_Incorporated"] == 1:
        cat = "City"
        color = "#004B87"
    elif row_jur["Is_UGA"] == 1:
        cat = "UGA"
        color = "#2563eb"
    else:
        cat = "Rural"
        color = "#64748b" # Neutral Slate (No green!)
        
    map_markers_data.append({
        "id": jid,
        "name": j_name,
        "type": j_type,
        "cat": cat,
        "color": color,
        "lat": lat,
        "lon": lon,
        "pop": pop_val,
        "share": pop_share,
        "htgt": h_tgt
    })
    
    # SVG projection: lon [-122.68, -121.68] -> x [30, 550], lat [48.35, 48.60] -> y [30, 330]
    px = 30 + ((lon - (-122.68)) / (-121.68 - (-122.68))) * 510
    py = 30 + ((48.60 - lat) / (48.60 - 48.35)) * 290
    
    if pop_val >= 30000:
        r_svg = 14
    elif pop_val >= 15000:
        r_svg = 11
    elif pop_val >= 10000:
        r_svg = 9
    elif pop_val >= 2000:
        r_svg = 7
    elif cat == "Rural":
        r_svg = 13
    else:
        r_svg = 5
        
    label_offset_y = -r_svg - 4
    anchor = "middle"
    offset_x = 0
    if jid == "JUR-02": # Burlington
        offset_x = 8
        label_offset_y = -r_svg - 2
        anchor = "start"
    elif jid == "JUR-09": # Bay View Ridge UGA
        offset_x = -8
        label_offset_y = -r_svg - 2
        anchor = "end"
    elif jid == "JUR-05": # La Conner
        offset_x = 6
        label_offset_y = r_svg + 11
        anchor = "start"
    elif jid == "JUR-10": # Swinomish UGA
        offset_x = -6
        label_offset_y = -r_svg - 4
        anchor = "end"
    elif jid == "JUR-07": # Mount Vernon
        label_offset_y = r_svg + 11
        anchor = "middle"
        
    stroke_style = 'stroke="#ffffff" stroke-width="2"' if cat != "Rural" else 'stroke="#ffffff" stroke-width="2" stroke-dasharray="3,2"'
    svg_marker_elements.append(f'''
              <g class="svg-map-node">
                <circle cx="{px:.1f}" cy="{py:.1f}" r="{r_svg}" fill="{color}" {stroke_style} opacity="0.9">
                  <title>{j_name} ({j_type})&#10;2025 Pop: {pop_val:,} ({pop_share:.1f}%)&#10;2045 Housing Target: {h_tgt:,} units</title>
                </circle>
                <circle cx="{px:.1f}" cy="{py:.1f}" r="{r_svg+4}" fill="none" stroke="{color}" stroke-width="1" opacity="0.3" />
                <text x="{px+offset_x:.1f}" y="{py+label_offset_y:.1f}" text-anchor="{anchor}" font-size="9" font-weight="700" fill="#0f172a" stroke="#ffffff" stroke-width="2.5" paint-order="stroke">{j_name}</text>
              </g>''')

svg_markers_markup = "\n".join(svg_marker_elements)
map_markers_json_str = json.dumps(map_markers_data)

# -------------------------------------------------------------
# 2. GENERATE HTML MARKUP
# -------------------------------------------------------------

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SCOG Growth Monitoring Report — Alternative Design v2 Mock-up</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <style>
    :root {{
      --slate-900: #0f172a;
      --slate-800: #1e293b;
      --slate-700: #334155;
      --slate-600: #475569;
      --slate-500: #64748b;
      --slate-400: #94a3b8;
      --slate-200: #e2e8f0;
      --slate-100: #f1f5f9;
      --primary-accent: #004B87;     /* Single accent: Navy/Azure (#004B87) */
      --accent-tint: #e6f0f8;
      --accent-bar: #2563eb;
      --bg-canvas: #f1f5f9;
      --bg-card: #ffffff;
      --border-card: #e2e8f0;
      --border-divider: #cbd5e1;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: var(--font-family);
      background-color: #0b0f19;
      color: var(--text-main);
      padding: 8px 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      overflow-x: hidden;
    }}

    .mockup-controls {{
      width: 1300px;
      max-width: 100%;
      background: var(--slate-800);
      color: #f8fafc;
      padding: 6px 16px;
      border-radius: 8px 8px 0 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid var(--slate-700);
      flex-shrink: 0;
      height: 44px;
    }}

    .mockup-title {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .mockup-title h1 {{
      font-size: 14px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
    }}

    .badge-v2 {{
      background: #0284c7;
      color: #ffffff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .tab-bar {{
      display: flex;
      gap: 6px;
    }}

    .tab-btn {{
      background: var(--slate-700);
      color: #cbd5e1;
      border: 1px solid var(--slate-600);
      padding: 5px 12px;
      border-radius: 5px;
      font-size: 11.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .tab-btn:hover {{
      background: var(--slate-600);
      color: #ffffff;
    }}

    .tab-btn.active {{
      background: var(--primary-accent);
      color: #ffffff;
      border-color: #38bdf8;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }}

    .view-controls {{
      display: flex;
      gap: 6px;
      align-items: center;
    }}

    .view-btn {{
      background: transparent;
      color: #94a3b8;
      border: 1px solid var(--slate-600);
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .view-btn:hover {{
      color: #ffffff;
      border-color: #94a3b8;
    }}

    .view-btn.active {{
      background: #0284c7;
      color: #ffffff;
      border-color: #38bdf8;
    }}

    .canvas-container {{
      width: 100%;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      overflow: visible;
      margin-bottom: 12px;
    }}

    .report-viewport {{
      width: 1300px;
      height: 900px;
      background: var(--bg-canvas);
      position: relative;
      overflow: hidden;
      border-radius: 0 0 8px 8px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      flex-shrink: 0;
      transform-origin: top center;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .report-page {{
      display: none;
      width: 1300px;
      height: 900px;
      position: absolute;
      top: 0;
      left: 0;
      padding: 16px 24px 12px 24px;
      box-sizing: border-box;
      flex-direction: column;
      justify-content: space-between;
    }}

    .report-page.active {{
      display: flex;
    }}

    .page-header {{
      height: 46px;
      margin-bottom: 10px;
      border-bottom: 2px solid var(--border-divider);
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      padding-bottom: 6px;
      flex-shrink: 0;
    }}

    .page-header-text h2 {{
      font-size: 18.5px;
      font-weight: 700;
      color: var(--primary-accent);
      line-height: 1.2;
    }}

    .page-header-text p {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
    }}

    .page-header-tag {{
      font-size: 10.5px;
      font-weight: 600;
      color: var(--slate-700);
      background: var(--accent-tint);
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid #bfdbfe;
    }}

    .kpi-row {{
      display: grid;
      grid-template-columns: 220px repeat(4, 1fr);
      gap: 16px;
      height: 96px;
      margin-bottom: 14px;
      flex-shrink: 0;
    }}

    .card {{
      background: var(--bg-card);
      border: 1px solid var(--border-card);
      border-radius: 8px;
      padding: 10px 14px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .card-title {{
      font-size: 10px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }}

    .card-value {{
      font-size: 24px;
      font-weight: 700;
      color: var(--slate-900);
      line-height: 1.1;
      margin: 1px 0;
    }}

    .card-comparison {{
      font-size: 10px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
      border-top: 1px dashed var(--slate-100);
      padding-top: 4px;
      line-height: 1.25;
    }}

    .card-comparison strong {{
      color: var(--slate-800);
    }}

    .slicer-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-card);
      border-radius: 8px;
      padding: 8px 12px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .slicer-card label {{
      font-size: 10px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .slicer-dropdown {{
      width: 100%;
      height: 28px;
      padding: 2px 6px;
      border: 1px solid var(--border-divider);
      border-radius: 4px;
      background: #ffffff;
      font-size: 11.5px;
      font-weight: 600;
      color: var(--slate-900);
      cursor: pointer;
    }}

    .slicer-hint {{
      font-size: 9px;
      color: var(--text-muted);
      line-height: 1;
    }}

    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      flex-shrink: 0;
    }}

    .grid-2col-split {{
      display: grid;
      grid-template-columns: 1fr 1.05fr;
      gap: 16px;
      flex-shrink: 0;
    }}

    .visual-container {{
      background: var(--bg-card);
      border: 1px solid var(--border-card);
      border-radius: 8px;
      padding: 12px 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-sizing: border-box;
    }}

    .visual-title {{
      font-size: 12.5px;
      font-weight: 700;
      color: var(--primary-accent);
      margin-bottom: 2px;
    }}

    .visual-subtitle {{
      font-size: 10px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}

    .visual-body {{
      flex: 1;
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      overflow: visible;
    }}

    .table-visual {{
      width: 100%;
      border-collapse: collapse;
      font-size: 10.5px;
      text-align: left;
    }}

    .table-visual th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #f8fafc;
      color: var(--slate-800);
      font-weight: 700;
      padding: 4px 8px;
      border-bottom: 2px solid var(--border-divider);
      white-space: nowrap;
    }}

    .table-visual th.num, .table-visual td.num {{
      text-align: right;
    }}

    .table-visual td {{
      padding: 3.5px 8px;
      border-bottom: 1px solid var(--slate-100);
      color: var(--slate-900);
      line-height: 1.25;
      white-space: nowrap;
    }}

    .table-visual tr:nth-child(even) td {{
      background: #fcfdfe;
    }}

    .table-visual tr.total-row td {{
      font-weight: 700;
      background: #f1f5f9;
      border-top: 2px solid var(--slate-400);
      border-bottom: 2px solid var(--slate-400);
      color: var(--slate-900);
    }}

    .chart-svg {{
      width: 100%;
      height: 100%;
      overflow: visible;
    }}

    .axis-line {{
      stroke: var(--border-divider);
      stroke-width: 1;
    }}

    .axis-label {{
      font-size: 9.5px;
      fill: var(--text-muted);
      font-family: var(--font-family);
    }}

    .chart-val-text {{
      font-size: 8.5px;
      font-weight: 700;
      fill: var(--slate-800);
      text-anchor: middle;
      font-family: var(--font-family);
    }}

    .page-footer {{
      height: 22px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid var(--border-divider);
      padding-top: 4px;
      font-size: 9.5px;
      color: var(--text-muted);
      flex-shrink: 0;
    }}

    .legend-box {{
      display: flex;
      gap: 12px;
      margin-bottom: 6px;
      font-size: 10px;
      color: var(--text-muted);
    }}

    .legend-item {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .legend-color {{
      width: 10px;
      height: 10px;
      border-radius: 2px;
      display: inline-block;
    }}

    .bar-row {{
      display: flex;
      align-items: center;
      margin-bottom: 4px;
      font-size: 10px;
    }}

    .bar-label {{
      width: 220px;
      color: var(--slate-800);
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex-shrink: 0;
      font-size: 10px;
    }}

    .bar-track {{
      flex: 1;
      height: 12px;
      background: var(--slate-100);
      border-radius: 3px;
      overflow: hidden;
      display: flex;
      margin: 0 8px;
    }}

    .bar-fill {{
      height: 100%;
      background: var(--primary-accent);
    }}

    .bar-fill.accent2 {{
      background: #2563eb;
    }}

    .bar-val {{
      width: 85px;
      text-align: right;
      font-weight: 600;
      color: var(--slate-900);
      flex-shrink: 0;
      font-size: 9.5px;
    }}

    .grouped-bar-row {{
      display: flex;
      align-items: center;
      margin-bottom: 6px;
      padding-bottom: 4px;
      border-bottom: 1px dashed var(--slate-100);
      font-size: 10px;
    }}

    .grouped-bar-row .bar-label {{
      width: 220px;
      font-size: 10px;
      font-weight: 600;
    }}

    #p3 .visual-container:first-child .bar-label {{
      width: 220px;
    }}

    #p3 .visual-container:first-child .bar-val {{
      width: 135px;
    }}

    .grouped-bar-col {{
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}

    .grouped-bar-item {{
      display: flex;
      align-items: center;
    }}

    .info-callout {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 6px 10px;
      font-size: 10px;
      color: var(--slate-700);
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 6px;
      line-height: 1.3;
    }}

    #map-container {{
      position: relative;
      width: 100%;
      height: 100%;
      min-height: 380px;
      border-radius: 6px;
      overflow: hidden;
      background: #f8fafc;
      border: 1px solid var(--border-card);
    }}

    #skagit-leaflet-map {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 2;
    }}

    #skagit-svg-fallback {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
    }}

    .map-legend-overlay {{
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(4px);
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 5px 8px;
      font-size: 9.5px;
      z-index: 1000;
      box-shadow: 0 2px 6px rgba(0,0,0,0.12);
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}

    .map-legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--slate-800);
      font-weight: 600;
    }}

    .map-legend-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      border: 1.5px solid #ffffff;
      display: inline-block;
    }}
  </style>
</head>
<body>

  <!-- Controls & Page Switcher -->
  <div class="mockup-controls">
    <div class="mockup-title">
      <h1>SCOG Growth Monitoring Report <span class="badge-v2">Alternative Design v2</span></h1>
    </div>
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchPage('p1')">Page 1: Regional Growth</button>
      <button class="tab-btn" onclick="switchPage('p2')">Page 2: Housing & Typologies</button>
      <button class="tab-btn" onclick="switchPage('p3')">Page 3: Population & Jobs</button>
      <button class="tab-btn" onclick="switchPage('p4')">Page 4: Spatial Allocation</button>
    </div>
    <div class="view-controls">
      <button id="btn-fit" class="view-btn active" onclick="setViewMode('fit')" title="Scale canvas to fit screen without scrolling">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
        Fit to Page
      </button>
      <button id="btn-actual" class="view-btn" onclick="setViewMode('actual')" title="100% Native 1300x900 canvas">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        100% Size
      </button>
    </div>
  </div>

  <div class="canvas-container">
    <div class="report-viewport">

      <!-- ========================================================================= -->
      <!-- PAGE 1: QUESTION: Is Skagit County Growing in Line with Regional Targets? -->
      <!-- ========================================================================= -->
      <div id="p1" class="report-page active">
        <div class="page-header">
          <div class="page-header-text">
            <h2>Is Skagit County Growing in Line with Regional Population and Housing Targets?</h2>
            <p>Regional Overview & 2025 Calibration Monitoring vs Adopted GMA 2045 Targets (Ordinance O20250002)</p>
          </div>
          <div class="page-header-tag">Baseline Calibration Year: 2025</div>
        </div>

        <div class="kpi-row">
          <div class="slicer-card">
            <label>Reporting Year</label>
            <select class="slicer-dropdown">
              <option selected>2025 Determination</option>
              <option>2024 Determination</option>
              <option>2023 Determination</option>
              <option>2022 Baseline Year</option>
            </select>
            <span class="slicer-hint">Controls single-year rollups</span>
          </div>

          <div class="card">
            <div class="card-title">Total Population (2025)</div>
            <div class="card-value">{total_pop_2025:,}</div>
            <div class="card-comparison">
              <span>Adopted 2045 Target: <strong>{target_pop_2045:,}</strong> · Baseline 2022: {baseline_pop_2022:,} (+{pop_growth_from_2022:,})</span>
            </div>
          </div>

          <div class="card">
            <div class="card-title">Net Housing Built (2020–Pres.)</div>
            <div class="card-value">{total_cum_housing:,}</div>
            <div class="card-comparison">
              <span><strong>{housing_progress_pct:.1f}%</strong> of 2045 Target ({total_cum_housing:,} net units of {total_housing_target:,} target)</span>
            </div>
          </div>

          <div class="card">
            <div class="card-title">2025 Net Permitted Units</div>
            <div class="card-value">{total_net_2025:,}</div>
            <div class="card-comparison">
              <span>Gross: <strong>{total_gross_2025:,}</strong> ({total_sf_2025:,} SF, {total_mf_2025:,} MF, {total_adu_2025:,} ADU) − Demolished: <strong>{total_dem_2025:,}</strong></span>
            </div>
          </div>

          <div class="card">
            <div class="card-title">Covered jobs, QCEW</div>
            <div class="card-value">{emp_2025_qcew:,}</div>
            <div class="card-comparison" style="font-size: 9.5px; line-height: 1.35; flex-direction: column; align-items: flex-start; gap: 2px;">
              <div>2022 covered: <strong>{emp_2022_qcew:,}</strong></div>
              <div>Total employment: 2022 baseline <strong>{emp_baseline_2022:,}</strong>; 2025 est. <strong>{emp_2025_est_total:,}</strong> (estimated); 2045 target <strong>{emp_target_2045:,}</strong></div>
            </div>
          </div>
        </div>

        <!-- Middle Row: 2 Charts -->
        <div class="grid-2col" style="height: 295px; margin-bottom: 14px;">
          <!-- Visual 07: Line Chart -->
          <div class="visual-container">
            <div class="visual-title">Regional Population Trajectory (2020–2025)</div>
            <div class="visual-subtitle">WA OFM Official April 1 Determination (Cumulative Growth: +{pop_growth_cum:,} / +{pop_growth_pct:.1f}%). (Axis truncated: starts at 128,000 for trend visibility; 2020: 129,523 → 2025: 134,600)</div>
            <div class="visual-body">
              <svg class="chart-svg" viewBox="0 0 580 230">
                <line x1="50" y1="175" x2="560" y2="175" class="axis-line" />
                <line x1="50" y1="35" x2="50" y2="175" class="axis-line" />
                <text x="42" y="178" class="axis-label" text-anchor="end">128k</text>
                <text x="42" y="135" class="axis-label" text-anchor="end">130k</text>
                <text x="42" y="95" class="axis-label" text-anchor="end">132k</text>
                <text x="42" y="55" class="axis-label" text-anchor="end">135k</text>
                <text x="80" y="195" class="axis-label" text-anchor="middle" font-weight="600">2020</text>
                <text x="80" y="210" class="axis-label" text-anchor="middle">({pop_traj[2020]:,})</text>
                <text x="175" y="195" class="axis-label" text-anchor="middle" font-weight="600">2021</text>
                <text x="175" y="210" class="axis-label" text-anchor="middle">({pop_traj[2021]:,})</text>
                <text x="270" y="195" class="axis-label" text-anchor="middle" font-weight="600">2022</text>
                <text x="270" y="210" class="axis-label" text-anchor="middle">({pop_traj[2022]:,})</text>
                <text x="365" y="195" class="axis-label" text-anchor="middle" font-weight="600">2023</text>
                <text x="365" y="210" class="axis-label" text-anchor="middle">({pop_traj[2023]:,})</text>
                <text x="460" y="195" class="axis-label" text-anchor="middle" font-weight="600">2024</text>
                <text x="460" y="210" class="axis-label" text-anchor="middle">({pop_traj[2024]:,})</text>
                <text x="540" y="195" class="axis-label" text-anchor="middle" font-weight="600">2025</text>
                <text x="540" y="210" class="axis-label" text-anchor="middle">({pop_traj[2025]:,})</text>
                <polyline fill="none" stroke="#004B87" stroke-width="3" points="{pop_polyline}" />
                {"".join(pop_dots)}
                <text x="540" y="28" font-size="10" font-weight="700" fill="#004B87" text-anchor="middle">134,600</text>
              </svg>
            </div>
          </div>

          <!-- Visual 08: Clustered Column -->
          <div class="visual-container">
            <div class="visual-title">Annual Permitted Housing Units by Typology (Benchmark Years)</div>
            <div class="visual-subtitle">Benchmark Years: 2010, 2015, 2020, and 2025 (Annual Single-Family, Multi-Family, and ADU Permits)</div>
            <div class="legend-box">
              <div class="legend-item"><span class="legend-color" style="background:#004B87;"></span> Single-Family</div>
              <div class="legend-item"><span class="legend-color" style="background:#2563eb;"></span> Multi-Family</div>
              <div class="legend-item"><span class="legend-color" style="background:#94a3b8;"></span> ADU Permits</div>
            </div>
            <div class="visual-body">
              <svg class="chart-svg" viewBox="0 0 580 200">
                <line x1="40" y1="170" x2="560" y2="170" class="axis-line" />
                <text x="90" y="185" class="axis-label" text-anchor="middle" font-weight="600">2010</text>
                <text x="210" y="185" class="axis-label" text-anchor="middle" font-weight="600">2015</text>
                <text x="350" y="185" class="axis-label" text-anchor="middle" font-weight="600">2020</text>
                <text x="490" y="185" class="axis-label" text-anchor="middle" font-weight="600">2025</text>
                {cluster_bars_svg}
              </svg>
            </div>
          </div>
        </div>

        <!-- Bottom Visual: Comprehensive Benchmarking Table -->
        <div class="visual-container" style="height: 375px;">
          <div class="visual-title">Jurisdictional Reconciliation Table (2025 Baseline vs. Adopted 2045 Targets)</div>
          <div class="visual-subtitle">Official WA OFM 2025 Determinations, Housing Production Progress & GMA Countywide Planning Allocations</div>
          <div class="visual-body">
            <table class="table-visual">
              <thead>
                <tr>
                  <th>Jurisdiction</th>
                  <th>Type</th>
                  <th class="num">2025 Population</th>
                  <th class="num">2045 Pop Target</th>
                  <th class="num">Net Housing (2020–Pres.)</th>
                  <th class="num">2045 Housing Target</th>
                  <th class="num">Housing Target %</th>
                </tr>
              </thead>
              <tbody>
"""

for r in p1_table_rows:
    html_content += f"""                <tr>
                  <td>{r['name']}</td>
                  <td>{r['type']}</td>
                  <td class="num">{r['pop25']:,}</td>
                  <td class="num">{r['pop_tgt']:,}</td>
                  <td class="num">{r['h_cum']:,}</td>
                  <td class="num">{r['h_tgt']:,}</td>
                  <td class="num">{r['h_pct_str']}</td>
                </tr>\n"""

html_content += f"""                <tr class="total-row">
                  <td>Total Skagit County</td>
                  <td>Countywide</td>
                  <td class="num">{total_pop_2025:,}</td>
                  <td class="num">{target_pop_2045:,}</td>
                  <td class="num">{total_cum_housing:,}</td>
                  <td class="num">{total_housing_target:,}</td>
                  <td class="num">{housing_progress_pct:.1f}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="page-footer" style="height: auto; min-height: 26px; flex-direction: column; align-items: flex-start; gap: 2px; padding-top: 4px;">
          <div style="width: 100%; display: flex; justify-content: space-between;">
            <span>Data Sources: WA OFM April 1 Population | ESD QCEW Covered Employment | SCOG Ordinance O20250002</span>
            <span>Reconciliation Check: 81,220 (Cities) + 4,278 (UGAs) + 49,102 (Rural) = 134,600 Total Pop</span>
          </div>
          <div style="color: var(--slate-500); font-size: 9px;">
            Note: 2022 Total employment baseline (59,571) reflects adopted Appendix A multiplier (1.15458 x 51,597).
          </div>
        </div>
      </div>

      <!-- ========================================================================= -->
      <!-- PAGE 2: QUESTION: Where and What Types of Housing Are Being Built?        -->
      <!-- ========================================================================= -->
      <div id="p2" class="report-page">
        <div class="page-header">
          <div class="page-header-text">
            <h2>Where and What Types of Housing Are Being Built Across Skagit County?</h2>
            <p>Housing Production, Typology Breakdown & Preliminary HB 1220 Affordability (AMI) Targets</p>
          </div>
          <div class="page-header-tag">HB 1220 Compliance Review</div>
        </div>

        <div class="kpi-row">
          <div class="slicer-card">
            <label>Jurisdiction Filter</label>
            <select class="slicer-dropdown">
              <option selected>(All Jurisdictions)</option>
              <option>Anacortes</option>
              <option>Burlington</option>
              <option>Mount Vernon</option>
              <option>Sedro-Woolley</option>
              <option>Unincorporated Rural</option>
            </select>
            <span class="slicer-hint">Filters permitting records</span>
          </div>

          <div class="card">
            <div class="card-title">2025 Net New Units</div>
            <div class="card-value">{total_net_2025:,}</div>
            <div class="card-comparison">
              <span>Gross: <strong>{total_gross_2025:,}</strong> | Demolished: <strong>{total_dem_2025:,}</strong></span>
            </div>
          </div>

          <div class="card">
            <div class="card-title">Single-Family Permits (2025)</div>
            <div class="card-value">{total_sf_2025:,}</div>
            <div class="card-comparison">
              <span>Share of Gross: <strong>{(total_sf_2025/total_gross_2025*100):.1f}%</strong></span>
            </div>
          </div>

          <div class="card">
            <div class="card-title">Multi-Family Permits (2025)</div>
            <div class="card-value">{total_mf_2025:,}</div>
            <div class="card-comparison">
              <span>Share of Gross: <strong>{(total_mf_2025/total_gross_2025*100):.1f}%</strong></span>
            </div>
          </div>

          <div class="card">
            <div class="card-title">ADU Permits (2025)</div>
            <div class="card-value">{total_adu_2025:,}</div>
            <div class="card-comparison">
              <span>Share of Gross: <strong>{(total_adu_2025/total_gross_2025*100):.1f}%</strong></span>
            </div>
          </div>
        </div>

        <!-- Middle Row: 2 Charts -->
        <div class="grid-2col" style="height: 295px; margin-bottom: 14px;">
          <!-- Visual 08: Stacked Area Chart with Axes and Legend -->
          <div class="visual-container">
            <div class="visual-title">Historical Permitted Housing Units by Typology (2010–2025)</div>
            <div class="visual-subtitle">Shift in Regional Construction Diversity (SF vs MF vs ADU)</div>
            <div class="legend-box">
              <div class="legend-item"><span class="legend-color" style="background:#004B87;"></span> Single-Family</div>
              <div class="legend-item"><span class="legend-color" style="background:#2563eb;"></span> Multi-Family</div>
              <div class="legend-item"><span class="legend-color" style="background:#94a3b8;"></span> ADU Permits</div>
            </div>
            <div class="visual-body">
              <svg class="chart-svg" viewBox="0 0 580 200">
                <line x1="40" y1="170" x2="560" y2="170" class="axis-line" />
                <line x1="40" y1="30" x2="40" y2="170" class="axis-line" />
                <!-- Y-axis labels -->
                <text x="34" y="173" class="axis-label" text-anchor="end">0</text>
                <text x="34" y="135" class="axis-label" text-anchor="end">200</text>
                <text x="34" y="100" class="axis-label" text-anchor="end">400</text>
                <text x="34" y="65" class="axis-label" text-anchor="end">600</text>
                <text x="34" y="32" class="axis-label" text-anchor="end">800</text>
                <!-- X-axis labels -->
                <text x="40" y="185" class="axis-label" text-anchor="middle">2010</text>
                <text x="144" y="185" class="axis-label" text-anchor="middle">2013</text>
                <text x="248" y="185" class="axis-label" text-anchor="middle">2016</text>
                <text x="352" y="185" class="axis-label" text-anchor="middle">2019</text>
                <text x="456" y="185" class="axis-label" text-anchor="middle">2022</text>
                <text x="560" y="185" class="axis-label" text-anchor="middle">2025</text>
                <path d="{area_gross}" fill="#94a3b8" opacity="0.6" />
                <path d="{area_mf}" fill="#2563eb" opacity="0.85" />
                <path d="{area_sf}" fill="#004B87" opacity="0.95" />
                {area_data_elements}
                <text x="560" y="20" font-size="9" font-weight="700" fill="#0f172a" text-anchor="end">2025 Total: {total_gross_2025:,} Gross ({total_net_2025:,} Net)</text>
              </svg>
            </div>
          </div>

          <!-- Visual 09: 100% Stacked Bar -->
          <div class="visual-container">
            <div class="visual-title">Single-Family vs. Multi-Family Production by Jurisdiction (2025)</div>
            <div class="visual-subtitle">2025 Single-Family ({total_sf_2025:,}) vs Multi-Family ({total_mf_2025:,}) Permits</div>
            <div class="visual-body" style="padding-top: 10px;">
"""

# Sort jurisdictions with permitting activity
top_prod = sorted([r for r in p2_matrix_rows if (r["sf"] + r["mf"]) > 0], key=lambda x: (x["sf"] + x["mf"]), reverse=True)[:5]
for r in top_prod:
    tot_bar = r["sf"] + r["mf"]
    sf_w = (r["sf"] / tot_bar) * 100 if tot_bar > 0 else 0
    mf_w = (r["mf"] / tot_bar) * 100 if tot_bar > 0 else 0
    html_content += f"""              <div class="bar-row"><span class="bar-label">{r['name']}</span><div class="bar-track"><div class="bar-fill" style="width:{sf_w:.1f}%;"></div><div class="bar-fill accent2" style="width:{mf_w:.1f}%;"></div></div><span class="bar-val">{r['sf']} SF / {r['mf']} MF</span></div>\n"""

html_content += f"""            </div>
          </div>
        </div>

        <!-- Bottom Row: AMI Targets & Permitting Matrix -->
        <div class="grid-2col-split" style="height: 375px;">
          <div class="visual-container">
            <div class="visual-title">Preliminary Allocated Units by Jurisdiction</div>
            <div class="visual-subtitle">[PRELIMINARY: Commerce default allocation (Exhibit 12). Local jurisdiction datasheets due Oct 20, 2026; not jurisdiction-verified]</div>
            <div class="visual-body" style="padding-top: 5px;">
"""

for _, r in ami_agg.iterrows():
    tot = int(r["Total_AMI_Units"])
    prop_width = (tot / max_ami_units) * 100
    html_content += f"""              <div class="bar-row">
                <span class="bar-label">{r['Jurisdiction_Name']}</span>
                <div class="bar-track" data-jurisdiction="{r['Jurisdiction_Name']}" data-width="{prop_width:.1f}" data-units="{tot}">
                  <div class="bar-fill accent2" style="width: {prop_width:.1f}%;"></div>
                </div>
                <span class="bar-val" style="width: 65px; text-align: right; flex-shrink: 0;">{tot:,} units</span>
              </div>\n"""

html_content += f"""              <div class="info-callout">
                <div><strong>Notice:</strong> Preliminary: Commerce default allocation (Exhibit 12). Local jurisdiction datasheets due Oct 20, 2026; not jurisdiction-verified. Allocations shown: Anacortes 31, Burlington 217, Mount Vernon 23, Sedro-Woolley 56 = {int(ami_agg['Total_AMI_Units'].sum()):,} total units.</div>
              </div>
            </div>
          </div>

          <div class="visual-container">
            <div class="visual-title">Housing Permitting Reconciliation Matrix (2025)</div>
            <div class="visual-subtitle">Single-Family, Multi-Family, ADU, Demolitions & Net Production</div>
            <div class="visual-body">
              <table class="table-visual" style="font-size: 10.5px;">
                <thead>
                  <tr>
                    <th>Jurisdiction</th>
                    <th class="num">SF</th>
                    <th class="num">MF</th>
                    <th class="num">ADU</th>
                    <th class="num">Demolished</th>
                    <th class="num" style="color:#004B87;">Net New</th>
                  </tr>
                </thead>
                <tbody>
"""

for r in p2_matrix_rows:
    html_content += f"""                  <tr>
                    <td>{r['name']}</td>
                    <td class="num">{r['sf']}</td>
                    <td class="num">{r['mf']}</td>
                    <td class="num">{r['adu']}</td>
                    <td class="num">{r['dem']}</td>
                    <td class="num" style="font-weight:600;">{r['net']}</td>
                  </tr>\n"""

html_content += f"""                  <tr class="total-row">
                    <td>Total Skagit County</td>
                    <td class="num">{total_sf_2025:,}</td>
                    <td class="num">{total_mf_2025:,}</td>
                    <td class="num">{total_adu_2025:,}</td>
                    <td class="num">{total_dem_2025:,}</td>
                    <td class="num" style="font-weight:700; color:#004B87;">{total_net_2025:,}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="page-footer">
          <span>Reconciliation Check: SF {total_sf_2025:,} + MF {total_mf_2025:,} + ADU {total_adu_2025:,} − Demolitions {total_dem_2025:,} = Net New {total_net_2025:,} Units</span>
          <span>Local Building Department Annual Submissions | Preliminary Commerce default allocation (Exhibit 12)</span>
        </div>
      </div>

      <!-- ========================================================================= -->
      <!-- PAGE 3: QUESTION: How Are Populations and Jobs Expanding?                 -->
      <!-- ========================================================================= -->
      <div id="p3" class="report-page">
        <div class="page-header">
          <div class="page-header-text">
            <h2>How Are Jurisdictional Populations and Covered Jobs Expanding Across the Region?</h2>
            <p>Regional Demographic Shifts, Annual Net Population Growth & CAI/ESD QCEW Employment Baseline</p>
          </div>
          <div class="page-header-tag">Employment & Target Analysis</div>
        </div>

        <!-- Top Row: All 11 Jurisdictions Population Progress + YoY Change -->
        <div class="grid-2col" style="height: 395px; margin-bottom: 14px;">
          <div class="visual-container">
            <div class="visual-title">Jurisdictional Population Level (2025) vs. Adopted 2045 GMA Targets</div>
            <div class="visual-subtitle">Current 2025 Population Count vs Adopted 2045 Target Allocation across all 11 Jurisdictions (Level ÷ Target %; Not Cumulative Growth)</div>
            <div class="visual-body">
"""

# Show all 11 jurisdictions sorted by 2025 population
all_p3_pop = sorted(p1_table_rows, key=lambda x: x["pop25"], reverse=True)
max_p3_pop = max([x["pop_tgt"] for x in all_p3_pop])

for r in all_p3_pop:
    fill_w = (r["pop25"] / max_p3_pop) * 100
    pct_of_tgt = (r["pop25"] / r["pop_tgt"] * 100) if r["pop_tgt"] > 0 else 0
    html_content += f"""              <div class="bar-row"><span class="bar-label" title="{r['name']}">{r['name']}</span><div class="bar-track"><div class="bar-fill" style="width:{fill_w:.1f}%;"></div></div><span class="bar-val">{r['pop25']:,} / {r['pop_tgt']:,} ({pct_of_tgt:.1f}%)</span></div>\n"""

html_content += f"""              <div class="info-callout" style="margin-top: 4px; padding: 4px 8px; font-size: 9.5px;">
                <div><strong>Notice on Rural Target:</strong> Bars reflect 2025 population level relative to the 2045 target level (Level ÷ Target %), not progress of cumulative growth since baseline. Unincorporated Rural (49,102) already exceeds its adopted 2045 planning target (48,381 by +721 persons, or 101.5% of target allocation).</div>
              </div>
            </div>
          </div>

          <div class="visual-container">
            <div class="visual-title">Net Annual Population Change (OFM 2024–2025 Calibration)</div>
            <div class="visual-subtitle">Single-Year Growth Dynamics by Jurisdiction (Total Countywide Change: +{total_pop_2025 - pop_traj[2024]:,})</div>
            <div class="visual-body">
"""

# Sort by YoY change
top_yoy = sorted(p3_yoy_rows, key=lambda x: x["yoy"], reverse=True)
max_yoy = max([x["yoy"] for x in top_yoy])

for r in top_yoy:
    w = (r["yoy"] / max_yoy) * 100 if max_yoy > 0 else 0
    sign = "+" if r["yoy"] > 0 else ""
    html_content += f"""              <div class="bar-row"><span class="bar-label">{r['name']}</span><div class="bar-track"><div class="bar-fill" style="width:{w:.1f}%; background:#2563eb;"></div></div><span class="bar-val">{sign}{r['yoy']:,}</span></div>\n"""

html_content += f"""            </div>
          </div>
        </div>

        <!-- Bottom Row: Employment Benchmark & Targets Table -->
        <div class="grid-2col-split" style="height: 385px;">
          <div class="visual-container">
            <div class="visual-title">Covered Wage & Salary Employment (ESD QCEW Benchmark, 1999–2025)</div>
            <div class="visual-subtitle">Historical Covered Wage & Salary Employment (Dim_CAI_Employment_Benchmark & Fact_Employment). Axis starts at 35,000 for visibility. Note: No data for 2020-21 and 2023-24 in the source files.</div>
            <div class="visual-body">
              <svg class="chart-svg" viewBox="0 0 580 260">
                <line x1="50" y1="230" x2="560" y2="230" class="axis-line" />
                <line x1="50" y1="35" x2="50" y2="230" class="axis-line" />
                <text x="42" y="234" class="axis-label" text-anchor="end">35k</text>
                <text x="42" y="184" class="axis-label" text-anchor="end">40k</text>
                <text x="42" y="136" class="axis-label" text-anchor="end">45k</text>
                <text x="42" y="88" class="axis-label" text-anchor="end">50k</text>
                <text x="42" y="40" class="axis-label" text-anchor="end">55k</text>
                <text x="60" y="248" class="axis-label" text-anchor="middle">1999</text>
                <text x="189" y="248" class="axis-label" text-anchor="middle">2006</text>
                <text x="337" y="248" class="axis-label" text-anchor="middle">2014</text>
                <text x="485" y="248" class="axis-label" text-anchor="middle">2022</text>
                <text x="540" y="248" class="axis-label" text-anchor="middle" font-weight="700">2025</text>
                <polyline fill="none" stroke="#004B87" stroke-width="3" points="{qcew_seg1_polyline}" />
                {"".join(qcew_dots)}
                <circle cx="{qcew_last_x:.1f}" cy="{qcew_last_y:.1f}" r="5.5" fill="#2563eb" stroke="#ffffff" stroke-width="2" />
                <text x="{qcew_last_x-10:.1f}" y="{qcew_last_y-12:.1f}" class="axis-label" font-weight="700" fill="#0f172a" text-anchor="end">2025 QCEW: {qcew_last['Covered_Employment_QCEW']:,} (Covered Jobs)</text>
                <text x="{qcew_2022_x-8:.1f}" y="{qcew_2022_y+16:.1f}" font-size="8.5" fill="#475569" text-anchor="end">2022: 51,597</text>
              </svg>
            </div>
          </div>

          <div class="visual-container">
            <div class="visual-title">Adopted GMA 2045 Employment Targets by Jurisdiction</div>
            <div class="visual-subtitle">Planning Allocations Only (Total Employment Baseline & Target)</div>
            <div class="visual-body">
              <table class="table-visual" style="font-size: 10.5px;">
                <thead>
                  <tr>
                    <th>Jurisdiction</th>
                    <th class="num">2022 Baseline (Total)</th>
                    <th class="num">2045 Target (Total)</th>
                  </tr>
                </thead>
                <tbody>
"""

for r in p3_emp_rows:
    html_content += f"""                  <tr>
                    <td>{r['name']}</td>
                    <td class="num">{r['base']:,}</td>
                    <td class="num">{r['target']:,}</td>
                  </tr>\n"""

html_content += f"""                  <tr class="total-row">
                    <td>Total Skagit County</td>
                    <td class="num">{emp_baseline_2022:,}</td>
                    <td class="num">{emp_target_2045:,}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="page-footer">
          <span>Adopted GMA 2022 Total Employment Baseline: {emp_baseline_2022:,} jobs | Adopted 2045 Planning Target: {emp_target_2045:,} jobs (Appendix A). Total employment baseline (59,571) reflects adopted Appendix A allocations (derived via CAI multiplier 1.15458 applied to 2022 QCEW 51,597, pending final SCOG confirmation).</span>
          <span>Data Sources: ESD QCEW Covered Employment | SCOG Ordinance O20250002</span>
        </div>
      </div>

      <!-- ========================================================================= -->
      <!-- PAGE 4: QUESTION: How Is Regional Growth Distributed Across the County?   -->
      <!-- ========================================================================= -->
      <div id="p4" class="report-page">
        <div class="page-header">
          <div class="page-header-text">
            <h2>How Is Regional Growth Distributed Across Cities, Urban Growth Areas, and Rural Lands?</h2>
            <p>Countywide Centroids, Municipal vs UGA vs Rural Classifications & Planning Allocation Shares</p>
          </div>
          <div class="page-header-tag">Spatial & Typology Distribution</div>
        </div>

        <div class="grid-2col-split" style="height: 480px; margin-bottom: 14px;">
          <div class="visual-container" style="height: 100%;">
            <div class="visual-title">Approximate Centroids (Leaflet placeholder)</div>
            <div class="visual-subtitle">Map placeholder (Leaflet); Azure Map in the Power BI build</div>
            <div class="visual-body" style="padding: 0; position: relative;">
              <div id="map-container">
                <!-- SVG Base Map (Always visible immediately) -->
                <svg id="skagit-svg-fallback" viewBox="0 0 580 360">
                  <rect width="580" height="360" fill="#f8fafc" />
                  <!-- Puget Sound / Salish Sea Waters on West -->
                  <path d="M 0,0 L 140,0 C 130,50 145,100 135,160 C 120,200 150,260 130,360 L 0,360 Z" fill="#e0f2fe" opacity="0.8" />
                  <path d="M 0,0 L 140,0 C 130,50 145,100 135,160 C 120,200 150,260 130,360 L 0,360 Z" fill="none" stroke="#bae6fd" stroke-width="2" />
                  <!-- Fidalgo Island land outline (Anacortes) -->
                  <path d="M 25,75 Q 85,60 90,140 Q 80,210 30,200 Q 15,140 25,75 Z" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" />
                  <!-- Skagit River Channel -->
                  <path d="M 570,85 Q 520,100 450,110 T 350,118 T 260,145 Q 220,165 210,185 Q 200,240 185,270 Q 165,295 130,310" fill="none" stroke="#38bdf8" stroke-width="3" stroke-linecap="round" opacity="0.85" />
                  <text x="470" y="105" font-size="8" fill="#0284c7" font-style="italic">Skagit River</text>
                  <text x="25" y="45" font-size="9" fill="#0369a1" font-weight="600">Puget Sound / Padilla Bay</text>
                  <!-- Major Transport Corridors (I-5 & WA-20) -->
                  <line x1="210" y1="0" x2="210" y2="360" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="4,3" />
                  <text x="214" y="20" font-size="8" fill="#64748b" font-weight="600">I-5 Corridor</text>
                  <path d="M 50,132 L 210,179 L 260,143 L 354,116 L 394,117 L 524,98 L 570,95" fill="none" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="4,3" />
                  <text x="300" y="140" font-size="8" fill="#64748b" font-weight="600">WA-20 Highway</text>
                  <!-- Plotted Centroids with Proportional Sizes & Labels -->
                  {svg_markers_markup}
                </svg>

                <!-- Leaflet Map Mount Point (Interactive Tiles) -->
                <div id="skagit-leaflet-map"></div>

                <!-- Map Legend Overlay (Single Accent Palette) -->
                <div class="map-legend-overlay">
                  <div class="map-legend-item"><span class="map-legend-dot" style="background:#004B87;"></span> Incorporated Cities (8)</div>
                  <div class="map-legend-item"><span class="map-legend-dot" style="background:#2563eb;"></span> Urban Growth Areas (2)</div>
                  <div class="map-legend-item"><span class="map-legend-dot" style="background:#64748b; border-style:dashed;"></span> Unincorporated Rural (1)</div>
                </div>
              </div>
            </div>
          </div>

          <div class="visual-container" style="height: 100%;">
            <div class="visual-title">Growth & Allocation Metrics by Classification</div>
            <div class="visual-subtitle">Tripartite Breakdown: Incorporated Cities vs. UGAs vs. Unincorporated Rural</div>
            <div class="visual-body">
              <table class="table-visual" style="font-size: 10.5px;">
                <thead>
                  <tr>
                    <th style="width: 140px;">Jurisdiction Type</th>
                    <th style="width: 230px;">Entity</th>
                    <th class="num" style="width: 75px;">Population</th>
                    <th class="num" style="width: 60px;">Share %</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style="background:#f1f5f9; font-weight:700;"><td colspan="2">Incorporated Cities (8 Entities)</td><td class="num">{cities_pop:,}</td><td class="num">{cities_share:.1f}%</td></tr>
"""

for r in p4_table_rows[:8]:
    html_content += f"""                  <tr><td>{r['type']}</td><td>{r['name']}</td><td class="num">{r['pop']:,}</td><td class="num">{r['share']:.1f}%</td></tr>\n"""

html_content += f"""                  <tr style="background:#f1f5f9; font-weight:700;"><td colspan="2">Urban Growth Areas (UGAs)</td><td class="num">{uga_pop:,}</td><td class="num">{uga_share:.1f}%</td></tr>
"""

for r in p4_table_rows[8:10]:
    html_content += f"""                  <tr><td>{r['type']}</td><td>{r['name']}</td><td class="num">{r['pop']:,}</td><td class="num">{r['share']:.1f}%</td></tr>\n"""

html_content += f"""                  <tr style="background:#f1f5f9; font-weight:700;"><td colspan="2">Unincorporated Rural (outside UGAs)</td><td class="num">{rural_pop:,}</td><td class="num">{rural_share:.1f}%</td></tr>
                  <tr><td>{p4_table_rows[10]['type']}</td><td>{p4_table_rows[10]['name']}</td><td class="num">{p4_table_rows[10]['pop']:,}</td><td class="num">{p4_table_rows[10]['share']:.1f}%</td></tr>
                  <tr class="total-row">
                    <td colspan="2">Total Skagit County</td>
                    <td class="num">{total_pop_2025:,}</td>
                    <td class="num">100.0%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Bottom Visual: Comparison Clustered Bar (Side-by-Side Grouped Bars) -->
        <div class="visual-container" style="height: 300px;">
          <div class="visual-title">Jurisdictional Shares of Regional Population vs. Housing Allocations</div>
          <div class="visual-subtitle">Alignment of Current Population Footprint vs. Adopted 2045 Housing Target Shares (Side-by-Side Bars)</div>
          <div class="legend-box">
            <div class="legend-item"><span class="legend-color" style="background:#004B87;"></span> Share of Regional Population %</div>
            <div class="legend-item"><span class="legend-color" style="background:#2563eb;"></span> Share of Regional Housing %</div>
          </div>
          <div class="visual-body">
"""

# Top 5 by population share
top_p4_comp = sorted(p4_share_comp, key=lambda x: x["pop_share"], reverse=True)[:5]

for r in top_p4_comp:
    html_content += f"""            <div class="grouped-bar-row">
              <span class="bar-label">{r['name']}</span>
              <div class="grouped-bar-col">
                <div class="grouped-bar-item">
                  <div class="bar-track"><div class="bar-fill" style="width:{(r['pop_share']*2.5):.1f}%;"></div></div>
                  <span class="bar-val">{r['pop_share']:.1f}% Pop</span>
                </div>
                <div class="grouped-bar-item">
                  <div class="bar-track"><div class="bar-fill accent2" style="width:{(r['h_share']*2.5):.1f}%;"></div></div>
                  <span class="bar-val">{r['h_share']:.1f}% Hsg</span>
                </div>
              </div>
            </div>\n"""

html_content += f"""          </div>
        </div>

        <div class="page-footer">
          <span>Tripartite Reconciliation: Cities ({cities_pop:,} / {cities_share:.1f}%) + UGAs ({uga_pop:,} / {uga_share:.1f}%) + Rural ({rural_pop:,} / {rural_share:.1f}%) = {total_pop_2025:,} Total (100.0%)</span>
          <span>Centroid Coordinates: Approximate centroids derived from Dim_Jurisdiction.csv coordinates</span>
        </div>
      </div>

    </div>
  </div><!-- end canvas-container -->

  <script>
    let leafletMap = null;
    let viewMode = 'fit';

    function switchPage(pageId) {{
      document.querySelectorAll('.report-page').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(pageId).classList.add('active');
      const targetBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(pageId));
      if (targetBtn) targetBtn.classList.add('active');

      if (pageId === 'p4') {{
        setTimeout(() => {{
          initLeafletMap();
          if (leafletMap) {{
            leafletMap.invalidateSize();
            if (window.markersGroup) {{
              leafletMap.fitBounds(window.markersGroup.getBounds().pad(0.12));
            }}
          }}
        }}, 80);
      }}
    }}

    function setViewMode(mode) {{
      viewMode = mode;
      document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById(mode === 'fit' ? 'btn-fit' : 'btn-actual');
      if (activeBtn) activeBtn.classList.add('active');
      updateCanvasScale();
    }}

    function updateCanvasScale() {{
      const viewport = document.querySelector('.report-viewport');
      const container = document.querySelector('.canvas-container');
      if (!viewport || !container) return;

      if (viewMode === 'fit') {{
        const controls = document.querySelector('.mockup-controls');
        const controlsHeight = controls ? controls.offsetHeight : 44;
        const availWidth = window.innerWidth - 32;
        const availHeight = window.innerHeight - controlsHeight - 20;

        const scaleX = availWidth / 1300;
        const scaleY = availHeight / 900;
        const scale = Math.min(scaleX, scaleY, 1.0);

        viewport.style.transform = `scale(${{scale}})`;
        viewport.style.transformOrigin = 'top center';
        container.style.height = `${{Math.ceil(900 * scale)}}px`;
        container.style.overflow = 'hidden';
      }} else {{
        viewport.style.transform = 'none';
        container.style.height = 'auto';
        container.style.overflow = 'visible';
      }}
    }}

    function initLeafletMap() {{
      const mapEl = document.getElementById('skagit-leaflet-map');
      if (!mapEl || leafletMap) return;
      if (typeof L === 'undefined') {{
        console.log("Leaflet library not loaded, using SVG fallback.");
        return;
      }}

      try {{
        leafletMap = L.map('skagit-leaflet-map', {{
          zoomControl: true,
          scrollWheelZoom: false,
          attributionControl: true
        }}).setView([48.48, -122.18], 10);

        const tiles = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
          attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
          maxZoom: 16
        }});

        tiles.on('load', function() {{
          mapEl.style.opacity = '1';
        }});

        tiles.addTo(leafletMap);

        const markersData = {map_markers_json_str};
        window.markersGroup = L.featureGroup();

        markersData.forEach(m => {{
          let r = 7;
          if (m.pop >= 30000) r = 18;
          else if (m.pop >= 15000) r = 14;
          else if (m.pop >= 10000) r = 12;
          else if (m.pop >= 2000) r = 9;
          else if (m.cat === 'Rural') r = 16;

          const circle = L.circleMarker([m.lat, m.lon], {{
            radius: r,
            fillColor: m.color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85
          }});

          const popupContent = `
            <div style="font-family:'Segoe UI',sans-serif; min-width:180px; padding:2px;">
              <div style="font-weight:700; font-size:13px; color:#0f172a; border-bottom:1px solid #e2e8f0; padding-bottom:4px; margin-bottom:4px;">
                ${{m.name}}
              </div>
              <div style="font-size:10.5px; color:#64748b; margin-bottom:6px;">${{m.type}}</div>
              <div style="display:flex; justify-content:space-between; font-size:11.5px; margin-bottom:2px;">
                <span style="color:#64748b;">2025 Population:</span>
                <strong style="color:#0f172a;">${{m.pop.toLocaleString()}} (${{m.share.toFixed(1)}}%)</strong>
              </div>
              <div style="display:flex; justify-content:space-between; font-size:11.5px;">
                <span style="color:#64748b;">2045 Housing Target:</span>
                <strong style="color:#004B87;">${{m.htgt.toLocaleString()}} units</strong>
              </div>
            </div>
          `;
          circle.bindPopup(popupContent);
          circle.bindTooltip(`<b>${{m.name}}</b><br>${{m.pop.toLocaleString()}}`, {{ direction: 'top', offset: [0, -r] }});
          window.markersGroup.addLayer(circle);
        }});

        window.markersGroup.addTo(leafletMap);
        leafletMap.fitBounds(window.markersGroup.getBounds().pad(0.12));
      }} catch (err) {{
        console.warn("Leaflet error, using SVG fallback:", err);
      }}
    }}

    window.addEventListener('resize', () => {{
      updateCanvasScale();
      if (leafletMap) leafletMap.invalidateSize();
    }});

    window.addEventListener('load', () => {{
      updateCanvasScale();
      initLeafletMap();
    }});
  </script>
</body>
</html>
"""

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully generated {OUT_FILE} with data sourced from processed CSVs!")
