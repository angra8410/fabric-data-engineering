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
hp_2020_2025 = df_hp[(df_hp["Year"] >= 2020) & (df_hp["Year"] <= 2025)]
cum_housing_by_jur = hp_2020_2025.groupby("Jurisdiction_ID")["Net_New_Units"].sum()
total_cum_housing = int(cum_housing_by_jur.sum()) # 3,465
total_housing_target = int(df_tgt["Target_2045_Housing_Units"].sum()) # 17,450
housing_progress_pct = (total_cum_housing / total_housing_target) * 100 # 19.8567% -> 19.9%

# 2025 Housing Permits
hp_2025 = df_hp[df_hp["Year"] == 2025].set_index("Jurisdiction_ID")
hp_2025["MF_Units"] = hp_2025["Duplex_Units"] + hp_2025["MultiFamily_3_4_Units"] + hp_2025["MultiFamily_5_Plus_Units"]

total_sf_2025 = int(hp_2025["Single_Family_Units"].sum()) # 202
total_mf_2025 = int(hp_2025["MF_Units"].sum()) # 259
total_adu_2025 = int(hp_2025["ADU_Units"].sum()) # 56
total_dem_2025 = int(hp_2025["Demolished_Units"].sum()) # 27
total_net_2025 = int(hp_2025["Net_New_Units"].sum()) # 490
total_gross_2025 = total_sf_2025 + total_mf_2025 + total_adu_2025 # 517

# Employment
emp_baseline_2022 = int(df_tgt["Baseline_2022_Employment"].sum()) # 59,571
emp_target_2045 = int(df_tgt["Target_2045_Employment"].sum()) # 80,100

# Annual Population Trajectory (2020-2025)
pop_traj = df_pop[df_pop["Year"].between(2020, 2025)].groupby("Year")["Population_Count"].sum().to_dict()

# Annual Permits Trajectory (2010-2025)
perm_traj = []
for y in range(2010, 2026):
    sub = df_hp[df_hp["Year"] == y]
    sf = int(sub["Single_Family_Units"].sum())
    mf = int((sub["Duplex_Units"] + sub["MultiFamily_3_4_Units"] + sub["MultiFamily_5_Plus_Units"]).sum())
    adu = int(sub["ADU_Units"].sum())
    perm_traj.append({"year": y, "sf": sf, "mf": mf, "adu": adu, "gross": sf + mf + adu})

# Target DataFrame indexed
tgt_df = df_tgt.set_index("Jurisdiction_ID")

# Build Table Data for Page 1
p1_table_rows = []
for jid in jur_order:
    name = tgt_df.loc[jid, "Jurisdiction_Name"]
    jtype = tgt_df.loc[jid, "Jurisdiction_Type"]
    pop25 = int(pop_2025_df.loc[jid, "Population_Count"])
    pop_tgt = int(tgt_df.loc[jid, "Target_2045_Population"])
    h_cum = int(cum_housing_by_jur.get(jid, 0))
    h_tgt = int(tgt_df.loc[jid, "Target_2045_Housing_Units"])
    h_pct_str = f"{(h_cum / h_tgt * 100):.1f}%" if h_tgt > 0 else "—"
    p1_table_rows.append({
        "jid": jid,
        "name": name,
        "type": jtype,
        "pop25": pop25,
        "pop_tgt": pop_tgt,
        "h_cum": h_cum,
        "h_tgt": h_tgt,
        "h_pct_str": h_pct_str
    })

# Page 2: Housing Permitting Matrix Rows (2025)
p2_matrix_rows = []
for jid in jur_order:
    name = tgt_df.loc[jid, "Jurisdiction_Name"]
    if jid in hp_2025.index:
        r = hp_2025.loc[jid]
        sf = int(r["Single_Family_Units"])
        mf = int(r["MF_Units"])
        adu = int(r["ADU_Units"])
        dem = int(r["Demolished_Units"])
        net = int(r["Net_New_Units"])
    else:
        sf = mf = adu = dem = net = 0
    p2_matrix_rows.append({
        "jid": jid, "name": name, "sf": sf, "mf": mf, "adu": adu, "dem": dem, "net": net
    })

# Page 2: AMI breakdown from Fact_Housing_AMI.csv
df_ami["Low"] = df_ami["AMI_0_to_30_Pct_Units"] + df_ami["AMI_31_to_50_Pct_Units"] + df_ami["AMI_51_to_80_Pct_Units"]
df_ami["ModHigh"] = df_ami["AMI_81_to_100_Pct_Units"] + df_ami["AMI_101_to_120_Pct_Units"] + df_ami["AMI_Greater_120_Pct_Units"]
ami_agg = df_ami.groupby(["Jurisdiction_ID", "Jurisdiction_Name"])[["Low", "ModHigh", "Total_AMI_Units"]].sum().reset_index()

# Page 3: YoY Population Change (2024 to 2025)
pop_2025_all = df_pop[df_pop["Year"] == 2025].set_index("Jurisdiction_ID")
p3_yoy_rows = []
for jid in jur_order:
    r = pop_2025_all.loc[jid]
    p3_yoy_rows.append({
        "jid": jid,
        "name": r["Jurisdiction_Name"],
        "pop24": int(r["Prior_Year_Population"]),
        "pop25": int(r["Population_Count"]),
        "yoy": int(r["YoY_Population_Change"])
    })

# Page 3: Employment Benchmark & Target Table
p3_emp_rows = []
for jid in jur_order:
    name = tgt_df.loc[jid, "Jurisdiction_Name"]
    base = int(tgt_df.loc[jid, "Baseline_2022_Employment"])
    target = int(tgt_df.loc[jid, "Target_2045_Employment"])
    p3_emp_rows.append({"jid": jid, "name": name, "base": base, "target": target})

# Page 3: Historical QCEW Series (Dim_CAI_Employment_Benchmark)
cai_series = df_cai.sort_values("Year")[["Year", "Covered_Employment_QCEW"]].to_dict(orient="records")

# Page 4: Classification Rollup
cities_pop = int(pop_2025_df.loc[[f"JUR-0{i}" for i in range(1, 9)], "Population_Count"].sum())
uga_pop = int(pop_2025_df.loc[["JUR-09", "JUR-10"], "Population_Count"].sum())
rural_pop = int(pop_2025_df.loc["JUR-11", "Population_Count"])

cities_share = (cities_pop / total_pop_2025) * 100
uga_share = (uga_pop / total_pop_2025) * 100
rural_share = (rural_pop / total_pop_2025) * 100

p4_table_rows = []
for jid in jur_order:
    name = tgt_df.loc[jid, "Jurisdiction_Name"]
    jtype = tgt_df.loc[jid, "Jurisdiction_Type"]
    pop = int(pop_2025_df.loc[jid, "Population_Count"])
    share = (pop / total_pop_2025) * 100
    p4_table_rows.append({"jid": jid, "name": name, "type": jtype, "pop": pop, "share": share})

p4_share_comp = []
for jid in jur_order:
    name = tgt_df.loc[jid, "Jurisdiction_Name"]
    pop = int(pop_2025_df.loc[jid, "Population_Count"])
    h_tgt = int(tgt_df.loc[jid, "Target_2045_Housing_Units"])
    pop_share = (pop / total_pop_2025) * 100
    h_share = (h_tgt / total_housing_target) * 100
    p4_share_comp.append({
        "jid": jid, "name": name, "pop_share": pop_share, "h_share": h_share
    })

# SVG Population Trajectory (Page 1)
pop_years = [2020, 2021, 2022, 2023, 2024, 2025]
pop_pts = []
pop_dots = []
for i, y in enumerate(pop_years):
    x = 80 + i * (460 / 5)
    val = pop_traj[y]
    y_pos = 180 - ((val - 128000) / (135000 - 128000)) * 140
    pop_pts.append(f"{x:.1f},{y_pos:.1f}")
    if y == 2025:
        pop_dots.append(f'<circle cx="{x:.1f}" cy="{y_pos:.1f}" r="5" fill="#2563eb" stroke="#ffffff" stroke-width="2" />')
        pop_dots.append(f'<text x="{x:.1f}" y="{y_pos-14:.1f}" class="axis-label" font-weight="700" fill="#0f172a" text-anchor="middle">{val:,}</text>')
    else:
        pop_dots.append(f'<circle cx="{x:.1f}" cy="{y_pos:.1f}" r="4" fill="#004B87" />')
pop_polyline = " ".join(pop_pts)

# SVG Permit Cluster Bars (Page 1)
cluster_years = [2010, 2015, 2020, 2025]
cluster_bars_svg = ""
for yr, cx in zip(cluster_years, [90, 210, 350, 490]):
    sub = [p for p in perm_traj if p["year"] == yr][0]
    sf_h = (sub["sf"] / 450) * 140
    mf_h = (sub["mf"] / 450) * 140
    adu_h = (sub["adu"] / 450) * 140
    is_2025 = (yr == 2025)
    op = "1.0" if is_2025 else "0.5"
    cluster_bars_svg += f"""
              <rect x="{cx-24}" y="{170-sf_h:.1f}" width="16" height="{sf_h:.1f}" fill="#004B87" opacity="{op}" rx="2" />
              <text x="{cx-16}" y="{170-sf_h-4:.1f}" class="axis-label" text-anchor="middle" font-weight="{'700' if is_2025 else '400'}">{sub['sf']}</text>
              <rect x="{cx-4}" y="{170-mf_h:.1f}" width="16" height="{mf_h:.1f}" fill="#2563eb" opacity="{op}" rx="2" />
              <text x="{cx+4}" y="{170-mf_h-4:.1f}" class="axis-label" text-anchor="middle" font-weight="{'700' if is_2025 else '400'}">{sub['mf']}</text>
              <rect x="{cx+16}" y="{170-adu_h:.1f}" width="16" height="{max(adu_h, 1):.1f}" fill="#94a3b8" opacity="{op}" rx="2" />
              <text x="{cx+24}" y="{170-adu_h-4:.1f}" class="axis-label" text-anchor="middle" font-weight="{'700' if is_2025 else '400'}">{sub['adu']}</text>"""

# SVG Historical Permits Stacked Area (Page 2)
gross_pts = []
mf_pts = []
sf_pts = []
for i, p in enumerate(perm_traj):
    x = 40 + i * (520 / 15)
    g_h = (p["gross"] / 750) * 120
    sf_h = (p["sf"] / 750) * 120
    mf_h = ((p["sf"] + p["mf"]) / 750) * 120
    gross_pts.append(f"{x:.1f} {150-g_h:.1f}")
    mf_pts.append(f"{x:.1f} {150-mf_h:.1f}")
    sf_pts.append(f"{x:.1f} {150-sf_h:.1f}")

area_gross = f"M 40 150 L " + " L ".join(gross_pts) + " L 560 150 Z"
area_mf = f"M 40 150 L " + " L ".join(mf_pts) + " L 560 150 Z"
area_sf = f"M 40 150 L " + " L ".join(sf_pts) + " L 560 150 Z"

# SVG Historical QCEW Series (Page 3)
qcew_pts = []
for r in cai_series:
    yr = r["Year"]
    val = r["Covered_Employment_QCEW"]
    x = 70 + ((yr - 1999) / (2022 - 1999)) * 440
    y = 240 - ((val - 40000) / 15000) * 200
    qcew_pts.append(f"{x:.1f},{y:.1f}")
qcew_polyline = " ".join(qcew_pts)
qcew_last = cai_series[-1]
qcew_last_x = 70 + ((qcew_last["Year"] - 1999) / (2022 - 1999)) * 440
qcew_last_y = 240 - ((qcew_last["Covered_Employment_QCEW"] - 40000) / 15000) * 200

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
      --primary-accent: #004B87;     /* Single accent: accent blue (#004B87) */
      --accent-tint: #e6f0f8;
      --accent-bar: #2563eb;
      --bg-canvas: #f1f5f9;
      --bg-card: #ffffff;
      --border-card: #e2e8f0;
      --border-divider: #cbd5e1;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --success-green: #059669;      /* Minimal green reserved strictly for progress/good */
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
      padding: 24px;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
    }}

    .mockup-controls {{
      width: 1300px;
      background: var(--slate-800);
      color: #f8fafc;
      padding: 16px 24px;
      border-radius: 12px 12px 0 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid var(--slate-700);
    }}

    .mockup-title h1 {{
      font-size: 18px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .mockup-title p {{
      font-size: 12px;
      color: var(--slate-400);
      margin-top: 4px;
    }}

    .badge-v2 {{
      background: #0284c7;
      color: #ffffff;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .tab-bar {{
      display: flex;
      gap: 8px;
    }}

    .tab-btn {{
      background: var(--slate-700);
      color: #cbd5e1;
      border: 1px solid var(--slate-600);
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 13px;
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
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
    }}

    .report-viewport {{
      width: 1300px;
      height: 900px;
      background: var(--bg-canvas);
      position: relative;
      overflow: hidden;
      border-radius: 0 0 12px 12px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
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
      height: 48px;
      margin-bottom: 10px;
      border-bottom: 2px solid var(--border-divider);
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      padding-bottom: 6px;
      flex-shrink: 0;
    }}

    .page-header-text h2 {{
      font-size: 19px;
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
      height: 82px;
      margin-bottom: 10px;
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
      font-size: 10.5px;
      font-weight: 600;
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
      font-size: 10.5px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
      border-top: 1px dashed var(--slate-100);
      padding-top: 3px;
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
      justify-content: flex-start;
      gap: 3px;
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
      margin-top: 1px;
    }}

    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      height: 250px;
      margin-bottom: 10px;
      flex-shrink: 0;
    }}

    .grid-2col-split {{
      display: grid;
      grid-template-columns: 1fr 1.05fr;
      gap: 16px;
      height: 310px;
      margin-bottom: 10px;
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
      padding: 3px 8px;
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
      background: #e2e8f0;
      border-top: 2px solid var(--slate-700);
      border-bottom: 2px solid var(--slate-700);
      color: var(--slate-900);
    }}

    svg.chart-svg {{
      width: 100%;
      height: 100%;
      overflow: visible;
    }}

    .axis-line {{
      stroke: var(--border-divider);
      stroke-width: 1;
    }}

    .grid-line {{
      stroke: var(--slate-100);
      stroke-width: 1;
    }}

    .axis-label {{
      font-size: 10px;
      fill: var(--slate-500);
      font-family: var(--font-family);
    }}

    .page-footer {{
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid var(--border-divider);
      padding-top: 4px;
      font-size: 10px;
      color: var(--text-muted);
      flex-shrink: 0;
    }}

    .legend-box {{
      display: flex;
      gap: 12px;
      align-items: center;
      font-size: 10px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}

    .legend-item {{
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .legend-color {{
      width: 10px;
      height: 10px;
      border-radius: 2px;
    }}

    .bar-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 5px;
      font-size: 11px;
    }}
    .bar-label {{
      width: 230px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      color: var(--slate-900);
    }}
    .bar-track {{
      flex: 1;
      height: 14px;
      background: var(--slate-100);
      border-radius: 3px;
      overflow: hidden;
      display: flex;
    }}
    .bar-fill {{
      height: 100%;
      background: var(--primary-accent);
    }}
    .bar-fill.accent2 {{
      background: #2563eb;
    }}
    .bar-fill.accent3 {{
      background: var(--slate-400);
    }}
    .bar-val {{
      width: 75px;
      text-align: right;
      font-weight: 600;
      color: var(--slate-900);
    }}

    .info-callout {{
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 11px;
      color: #166534;
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 8px;
    }}
  </style>
</head>
<body>

  <!-- Controls & Page Switcher -->
  <div class="mockup-controls">
    <div class="mockup-title">
      <h1>SCOG Growth Monitoring Report <span class="badge-v2">Alternative Design v2</span></h1>
      <p>Question-based headers · Single accent color (#004B87) · Contextual comparison KPIs · Consistent 1300x900 grid</p>
    </div>
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchPage('p1')">Page 1: Regional Growth</button>
      <button class="tab-btn" onclick="switchPage('p2')">Page 2: Housing & Typologies</button>
      <button class="tab-btn" onclick="switchPage('p3')">Page 3: Population & Jobs</button>
      <button class="tab-btn" onclick="switchPage('p4')">Page 4: Spatial Allocation</button>
    </div>
  </div>

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
            <option>2025 Determination</option>
            <option>2024</option>
            <option>2023</option>
            <option>2022</option>
          </select>
          <span style="font-size: 9px; color: var(--text-muted); margin-top: 4px;">Controls single-year rollups</span>
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
            <span>{housing_progress_pct:.1f}% of 2045 Target ({total_cum_housing:,} net units of {total_housing_target:,} target)</span>
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
          <div class="card-title">Covered Employment (2022 Baseline)</div>
          <div class="card-value">{emp_baseline_2022:,}</div>
          <div class="card-comparison">
            <span>2022 ESD QCEW Baseline · Adopted 2045 Target: <strong>{emp_target_2045:,}</strong></span>
          </div>
        </div>
      </div>

      <div class="grid-2col">
        <!-- Visual 07: Line Chart -->
        <div class="visual-container">
          <div class="visual-title">Regional Population Trajectory (2020–2025)</div>
          <div class="visual-subtitle">WA OFM Official April 1 Determination (Cumulative Growth: +{total_pop_2025 - pop_traj[2020]:,} / +{((total_pop_2025 - pop_traj[2020])/pop_traj[2020]*100):.1f}%)</div>
          <div class="visual-body">
            <svg class="chart-svg" viewBox="0 0 580 220">
              <line x1="50" y1="180" x2="560" y2="180" class="axis-line" />
              <line x1="50" y1="30" x2="50" y2="180" class="axis-line" />
              <line x1="50" y1="140" x2="560" y2="140" class="grid-line" />
              <line x1="50" y1="90" x2="560" y2="90" class="grid-line" />
              <line x1="50" y1="40" x2="560" y2="40" class="grid-line" />
              <text x="42" y="184" class="axis-label" text-anchor="end">128k</text>
              <text x="42" y="144" class="axis-label" text-anchor="end">130k</text>
              <text x="42" y="94" class="axis-label" text-anchor="end">132k</text>
              <text x="42" y="44" class="axis-label" text-anchor="end">135k</text>
              <text x="80" y="200" class="axis-label" text-anchor="middle">2020 ({pop_traj[2020]:,})</text>
              <text x="175" y="200" class="axis-label" text-anchor="middle">2021 ({pop_traj[2021]:,})</text>
              <text x="270" y="200" class="axis-label" text-anchor="middle">2022 ({pop_traj[2022]:,})</text>
              <text x="365" y="200" class="axis-label" text-anchor="middle">2023 ({pop_traj[2023]:,})</text>
              <text x="460" y="200" class="axis-label" text-anchor="middle">2024 ({pop_traj[2024]:,})</text>
              <text x="540" y="200" class="axis-label" text-anchor="middle">2025 ({pop_traj[2025]:,})</text>
              <polyline fill="none" stroke="#004B87" stroke-width="3" points="{pop_polyline}" />
              {"".join(pop_dots)}
            </svg>
          </div>
        </div>

        <!-- Visual 08: Clustered Column -->
        <div class="visual-container">
          <div class="visual-title">Annual Permitted Housing Units by Typology (2010–2025)</div>
          <div class="visual-subtitle">Single-Family ({total_sf_2025:,}) vs Multi-Family ({total_mf_2025:,}) vs ADU ({total_adu_2025:,}) in 2025</div>
          <div class="legend-box">
            <div class="legend-item"><span class="legend-color" style="background:#004B87;"></span> Single-Family</div>
            <div class="legend-item"><span class="legend-color" style="background:#2563eb;"></span> Multi-Family</div>
            <div class="legend-item"><span class="legend-color" style="background:#94a3b8;"></span> ADU Permits</div>
          </div>
          <div class="visual-body">
            <svg class="chart-svg" viewBox="0 0 580 200">
              <line x1="40" y1="170" x2="560" y2="170" class="axis-line" />
              <text x="90" y="185" class="axis-label" text-anchor="middle">2010</text>
              <text x="210" y="185" class="axis-label" text-anchor="middle">2015</text>
              <text x="350" y="185" class="axis-label" text-anchor="middle">2020</text>
              <text x="490" y="185" class="axis-label" text-anchor="middle">2025</text>
              <!-- Dynamically generated cluster bars (SF, MF, ADU) -->
              {cluster_bars_svg}
            </svg>
          </div>
        </div>
      </div>

      <!-- Bottom Visual: Comprehensive Benchmarking Table -->
      <div class="visual-container" style="height: 380px;">
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
    html_content += f"""              <tr>
                <td>{r['name']}</td>
                <td>{r['type']}</td>
                <td class="num">{r['pop25']:,}</td>
                <td class="num">{r['pop_tgt']:,}</td>
                <td class="num">{r['h_cum']:,}</td>
                <td class="num">{r['h_tgt']:,}</td>
                <td class="num">{r['h_pct_str']}</td>
              </tr>\n"""

html_content += f"""              <tr class="total-row">
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

      <div class="page-footer">
        <span>Data Sources: WA OFM April 1 Population (2020-2025 Determination) | ESD QCEW Covered Employment | SCOG Ordinance O20250002</span>
        <span>Reconciliation Check: {cities_pop:,} (Cities) + {uga_pop:,} (UGAs) + {rural_pop:,} (Rural) = {total_pop_2025:,} Total Population</span>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- PAGE 2: QUESTION: What Types of Housing Are Being Built and For Whom?     -->
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
            <option>(All Jurisdictions)</option>
            <option>Anacortes</option>
            <option>Burlington</option>
            <option>Mount Vernon</option>
            <option>Sedro-Woolley</option>
          </select>
          <span style="font-size: 9px; color: var(--text-muted); margin-top: 4px;">Filters permitting records</span>
        </div>

        <div class="card">
          <div class="card-title">2025 Net New Units</div>
          <div class="card-value">{total_net_2025:,}</div>
          <div class="card-comparison"><span>Gross: <strong>{total_gross_2025:,}</strong> | Demolished: <strong>{total_dem_2025:,}</strong></span></div>
        </div>

        <div class="card">
          <div class="card-title">Single-Family Permits (2025)</div>
          <div class="card-value">{total_sf_2025:,}</div>
          <div class="card-comparison"><span>Share of Gross: <strong>{(total_sf_2025/total_gross_2025*100):.1f}%</strong></span></div>
        </div>

        <div class="card">
          <div class="card-title">Multi-Family Permits (2025)</div>
          <div class="card-value">{total_mf_2025:,}</div>
          <div class="card-comparison"><span>Share of Gross: <strong>{(total_mf_2025/total_gross_2025*100):.1f}%</strong></span></div>
        </div>

        <div class="card">
          <div class="card-title">ADU Permits (2025)</div>
          <div class="card-value">{total_adu_2025:,}</div>
          <div class="card-comparison"><span>Share of Gross: <strong>{(total_adu_2025/total_gross_2025*100):.1f}%</strong></span></div>
        </div>
      </div>

      <!-- Top Row Charts -->
      <div class="grid-2col" style="height: 275px; margin-bottom: 16px;">
        <div class="visual-container">
          <div class="visual-title">Historical Permitted Housing Units by Typology (2010–2025)</div>
          <div class="visual-subtitle">Shift in Regional Construction Diversity (SF vs MF vs ADU)</div>
          <div class="visual-body">
            <svg class="chart-svg" viewBox="0 0 580 180">
              <path d="{area_gross}" fill="#94a3b8" opacity="0.6" />
              <path d="{area_mf}" fill="#2563eb" opacity="0.7" />
              <path d="{area_sf}" fill="#004B87" opacity="0.85" />
              <text x="560" y="32" class="axis-label" text-anchor="end" font-weight="700">2025 Total: {total_gross_2025} Gross ({total_net_2025} Net)</text>
            </svg>
          </div>
        </div>

        <div class="visual-container">
          <div class="visual-title">Single-Family vs. Multi-Family Production by Jurisdiction (2025)</div>
          <div class="visual-subtitle">2025 Single-Family ({total_sf_2025:,}) vs Multi-Family ({total_mf_2025:,}) Permits</div>
          <div class="visual-body" style="padding-top: 5px;">
"""

# Sort by gross permits for the bar chart
top_p2_jur = sorted([r for r in p2_matrix_rows if (r['sf'] + r['mf']) > 0], key=lambda x: (x['sf'] + x['mf']), reverse=True)[:5]
max_p2_val = max([r['sf'] + r['mf'] for r in top_p2_jur]) if top_p2_jur else 1

for r in top_p2_jur:
    tot = r['sf'] + r['mf']
    sf_w = (r['sf'] / tot * 100) * (tot / max_p2_val)
    mf_w = (r['mf'] / tot * 100) * (tot / max_p2_val)
    html_content += f"""            <div class="bar-row"><span class="bar-label">{r['name']}</span><div class="bar-track"><div class="bar-fill" style="width:{sf_w:.1f}%;"></div><div class="bar-fill accent2" style="width:{mf_w:.1f}%;"></div></div><span class="bar-val">{r['sf']} SF / {r['mf']} MF</span></div>\n"""

html_content += f"""          </div>
        </div>
      </div>

      <!-- Bottom Row: AMI Targets & Permitting Matrix -->
      <div class="grid-2col-split" style="height: 390px;">
        <div class="visual-container">
          <div class="visual-title">Allocated Housing Units by Area Median Income (AMI) Income Band</div>
          <div class="visual-subtitle">[PRELIMINARY: Local Jurisdiction Housing Needs Assessments due Oct 20, 2026]</div>
          <div class="legend-box">
            <div class="legend-item"><span class="legend-color" style="background:#004B87;"></span> &lt;80% AMI (Low Income)</div>
            <div class="legend-item"><span class="legend-color" style="background:#2563eb;"></span> &gt;80% AMI (Moderate/High)</div>
          </div>
          <div class="visual-body" style="padding-top: 5px;">
"""

for _, r in ami_agg.iterrows():
    tot = int(r["Total_AMI_Units"])
    low = int(r["Low"])
    mod = int(r["ModHigh"])
    html_content += f"""            <div class="bar-row"><span class="bar-label">{r['Jurisdiction_Name']}</span><div class="bar-track"><div class="bar-fill" style="width:{(low/tot*100):.1f}%;"></div><div class="bar-fill accent2" style="width:{(mod/tot*100):.1f}%;"></div></div><span class="bar-val">{tot:,} units</span></div>\n"""

html_content += f"""            <div class="info-callout">
              <strong>Notice:</strong> [PRELIMINARY: Local Jurisdiction Housing Needs Assessments due Oct 20, 2026]. Data reflects current preliminary Commerce reporting ({int(ami_agg['Total_AMI_Units'].sum()):,} total units across reporting jurisdictions).
            </div>
          </div>
        </div>

        <div class="visual-container">
          <div class="visual-title">Housing Permitting Reconciliation Matrix (2025)</div>
          <div class="visual-subtitle">Single-Family, Multi-Family, ADU, Demolitions & Net Production</div>
          <div class="visual-body" style="overflow-y: auto;">
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
    html_content += f"""                <tr>
                  <td>{r['name']}</td>
                  <td class="num">{r['sf']}</td>
                  <td class="num">{r['mf']}</td>
                  <td class="num">{r['adu']}</td>
                  <td class="num">{r['dem']}</td>
                  <td class="num" style="font-weight:600;">{r['net']}</td>
                </tr>\n"""

html_content += f"""                <tr class="total-row">
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
        <span>Local Building Department Annual Submissions | Preliminary Commerce HB 1220 Datasheets</span>
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

      <div class="grid-2col" style="height: 350px; margin-bottom: 16px;">
        <div class="visual-container">
          <div class="visual-title">Population Progress Toward 2045 GMA Target by Jurisdiction</div>
          <div class="visual-subtitle">2025 Current Population vs Adopted 2045 Target Allocations</div>
          <div class="legend-box">
            <div class="legend-item"><span class="legend-color" style="background:#004B87;"></span> 2025 Current Population</div>
            <div class="legend-item"><span class="legend-color" style="background:#94a3b8;"></span> 2045 Target Allocation</div>
          </div>
          <div class="visual-body">
"""

# Sort by 2025 population top 5
top_p3_pop = sorted(p1_table_rows, key=lambda x: x["pop25"], reverse=True)[:5]
max_p3_pop = max([x["pop_tgt"] for x in top_p3_pop])

for r in top_p3_pop:
    fill_w = (r["pop25"] / max_p3_pop) * 100
    html_content += f"""            <div class="bar-row"><span class="bar-label">{r['name']}</span><div class="bar-track"><div class="bar-fill" style="width:{fill_w:.1f}%;"></div></div><span class="bar-val">{r['pop25']:,} / {r['pop_tgt']:,}</span></div>\n"""

html_content += f"""          </div>
        </div>

        <div class="visual-container">
          <div class="visual-title">Net Annual Population Change (OFM 2024–2025 Calibration)</div>
          <div class="visual-subtitle">Single-Year Growth Dynamics by Jurisdiction (Total Countywide Change: +{total_pop_2025 - pop_traj[2024]:,})</div>
          <div class="visual-body">
"""

# Sort by YoY change top jurisdictions
top_yoy = sorted(p3_yoy_rows, key=lambda x: x["yoy"], reverse=True)[:6]
max_yoy = max([x["yoy"] for x in top_yoy])

for r in top_yoy:
    w = (r["yoy"] / max_yoy) * 100 if max_yoy > 0 else 0
    sign = "+" if r["yoy"] > 0 else ""
    html_content += f"""            <div class="bar-row"><span class="bar-label">{r['name']}</span><div class="bar-track"><div class="bar-fill" style="width:{w:.1f}%; background:#2563eb;"></div></div><span class="bar-val">{sign}{r['yoy']:,}</span></div>\n"""

html_content += f"""          </div>
        </div>
      </div>

      <!-- Bottom Row: Employment Benchmark & Targets Table -->
      <div class="grid-2col-split" style="height: 420px;">
        <div class="visual-container">
          <div class="visual-title">Covered Employment (ESD QCEW Benchmark, 1999–2022)</div>
          <div class="visual-subtitle">Historical Covered Wage & Salary Employment (Dim_CAI_Employment_Benchmark 1999–2022; Fact_Employment records through 2026)</div>
          <div class="visual-body">
            <svg class="chart-svg" viewBox="0 0 580 280">
              <line x1="50" y1="240" x2="560" y2="240" class="axis-line" />
              <line x1="50" y1="40" x2="50" y2="240" class="axis-line" />
              <text x="42" y="244" class="axis-label" text-anchor="end">40k</text>
              <text x="42" y="174" class="axis-label" text-anchor="end">50k</text>
              <text x="42" y="104" class="axis-label" text-anchor="end">60k</text>
              <text x="70" y="260" class="axis-label" text-anchor="middle">1999</text>
              <text x="210" y="260" class="axis-label" text-anchor="middle">2007</text>
              <text x="350" y="260" class="axis-label" text-anchor="middle">2015</text>
              <text x="510" y="260" class="axis-label" text-anchor="middle">2022</text>
              <polyline fill="none" stroke="#004B87" stroke-width="3" points="{qcew_polyline}" />
              <circle cx="{qcew_last_x:.1f}" cy="{qcew_last_y:.1f}" r="5" fill="#2563eb" stroke="#ffffff" stroke-width="2" />
              <text x="{qcew_last_x:.1f}" y="{qcew_last_y-12:.1f}" class="axis-label" font-weight="700" fill="#0f172a" text-anchor="middle">2022 QCEW: {qcew_last['Covered_Employment_QCEW']:,}</text>
            </svg>
          </div>
        </div>

        <div class="visual-container">
          <div class="visual-title">Adopted GMA 2045 Employment Targets by Jurisdiction</div>
          <div class="visual-subtitle">Planning Allocations Only (No Annual Actuals or Target Tracking)</div>
          <div class="visual-body" style="overflow-y: auto;">
            <table class="table-visual" style="font-size: 11px;">
              <thead>
                <tr>
                  <th>Jurisdiction</th>
                  <th class="num">2022 Baseline</th>
                  <th class="num">2045 Target</th>
                </tr>
              </thead>
              <tbody>
"""

for r in p3_emp_rows:
    html_content += f"""                <tr>
                  <td>{r['name']}</td>
                  <td class="num">{r['base']:,}</td>
                  <td class="num">{r['target']:,}</td>
                </tr>\n"""

html_content += f"""                <tr class="total-row">
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
        <span>Employment Benchmarks: ESD QCEW 1999-2022 Covered Jobs ({emp_baseline_2022:,} Baseline). Adopted 2045 GMA Planning Target: {emp_target_2045:,}</span>
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

      <div class="grid-2col-split" style="height: 440px; margin-bottom: 16px;">
        <div class="visual-container">
          <div class="visual-title">Regional Jurisdictions & UGA Centroids (USGS/Census 2020)</div>
          <div class="visual-subtitle">Native Azure Map Visual (Latitude/Longitude Centroid Anchors)</div>
          <div class="visual-body" style="background:#e0f2fe; border-radius:6px; display:flex; align-items:center; justify-content:center;">
            <div style="text-align:center; color:#0369a1;">
              <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" style="margin-bottom:8px;">
                <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
                <line x1="8" y1="2" x2="8" y2="18"></line>
                <line x1="16" y1="6" x2="16" y2="22"></line>
              </svg>
              <div style="font-weight:700; font-size:13px;">Native Azure Map Visual</div>
              <div style="font-size:11px; color:#075985;">Centroids: 8 Municipalities + 2 UGAs + Rural Centroid</div>
            </div>
          </div>
        </div>

        <div class="visual-container" style="height: 455px;">
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
    html_content += f"""                <tr><td>{r['type']}</td><td>{r['name']}</td><td class="num">{r['pop']:,}</td><td class="num">{r['share']:.1f}%</td></tr>\n"""

html_content += f"""                <tr style="background:#f1f5f9; font-weight:700;"><td colspan="2">Urban Growth Areas (UGAs)</td><td class="num">{uga_pop:,}</td><td class="num">{uga_share:.1f}%</td></tr>
"""

for r in p4_table_rows[8:10]:
    html_content += f"""                <tr><td>{r['type']}</td><td>{r['name']}</td><td class="num">{r['pop']:,}</td><td class="num">{r['share']:.1f}%</td></tr>\n"""

html_content += f"""                <tr style="background:#f1f5f9; font-weight:700;"><td colspan="2">Unincorporated Rural (outside UGAs)</td><td class="num">{rural_pop:,}</td><td class="num">{rural_share:.1f}%</td></tr>
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

      <!-- Bottom Visual: Comparison Clustered Bar -->
      <div class="visual-container" style="height: 330px;">
        <div class="visual-title">Jurisdictional Shares of Regional Population vs. Housing Allocations</div>
        <div class="visual-subtitle">Alignment of Current Population Footprint vs. Adopted 2045 Housing Target Shares</div>
        <div class="legend-box">
          <div class="legend-item"><span class="legend-color" style="background:#004B87;"></span> Share of Regional Population %</div>
          <div class="legend-item"><span class="legend-color" style="background:#2563eb;"></span> Share of Regional Housing %</div>
        </div>
        <div class="visual-body">
"""

# Top 5 by population share
top_p4_comp = sorted(p4_share_comp, key=lambda x: x["pop_share"], reverse=True)[:5]

for r in top_p4_comp:
    html_content += f"""          <div class="bar-row"><span class="bar-label">{r['name']}</span><div class="bar-track"><div class="bar-fill" style="width:{r['pop_share']:.1f}%;"></div><div class="bar-fill accent2" style="width:{r['h_share']:.1f}%;"></div></div><span class="bar-val">{r['pop_share']:.1f}% / {r['h_share']:.1f}%</span></div>\n"""

html_content += f"""        </div>
      </div>

      <div class="page-footer">
        <span>Tripartite Reconciliation: Cities ({cities_pop:,} / {cities_share:.1f}%) + UGAs ({uga_pop:,} / {uga_share:.1f}%) + Rural ({rural_pop:,} / {rural_share:.1f}%) = {total_pop_2025:,} Total (100.0%)</span>
        <span>Centroid Coordinates: Official USGS GNIS / US Census Bureau 2020 Municipal Centers & UGA Centroids</span>
      </div>
    </div>

  </div>

  <script>
    function switchPage(pageId) {{
      document.querySelectorAll('.report-page').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(pageId).classList.add('active');
      event.currentTarget.classList.add('active');
    }}
  </script>
</body>
</html>
"""

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully generated {OUT_FILE} with data sourced from processed CSVs!")
