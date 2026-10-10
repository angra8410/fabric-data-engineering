"""
verify_v2_mockup.py
Automated verification script for alternative_design_v2_mockup.html.
Reads the processed CSVs and compares EVERY cell, card, chart figure, and table value
in the generated HTML mock-up against authoritative values.
Prints PASS/FAIL per cell.
"""

from pathlib import Path
import re
from bs4 import BeautifulSoup
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
HTML_FILE = BASE_DIR / "alternative_design_v2_mockup.html"

# Load source data
df_pop = pd.read_csv(DATA_DIR / "Fact_Population.csv")
df_hp = pd.read_csv(DATA_DIR / "Fact_HousingPermits.csv")
df_emp = pd.read_csv(DATA_DIR / "Fact_Employment.csv")
df_ami = pd.read_csv(DATA_DIR / "Fact_Housing_AMI.csv")
df_tgt = pd.read_csv(DATA_DIR / "Dim_GMA_2045_Target.csv")
df_jur = pd.read_csv(DATA_DIR / "Dim_Jurisdiction.csv")
df_cai = pd.read_csv(DATA_DIR / "Dim_CAI_Employment_Benchmark.csv")

# Parse HTML
with open(HTML_FILE, "r", encoding="utf-8") as f:
    html_text = f.read()

soup = BeautifulSoup(html_text, "html.parser")

results = []

def check(category, metric_name, rendered_val, expected_val):
    def normalize(val):
        if val is None:
            return ""
        s = str(val).strip().replace(",", "")
        s = s.replace("%", "").replace("+", "")
        try:
            return f"{float(s):.2f}"
        except ValueError:
            return str(val).strip()

    norm_rend = normalize(rendered_val)
    norm_exp = normalize(expected_val)
    status = "PASS" if norm_rend == norm_exp else "FAIL"
    results.append({
        "category": category,
        "metric": metric_name,
        "rendered": str(rendered_val).strip(),
        "expected": str(expected_val).strip(),
        "status": status
    })

# -------------------------------------------------------------------------
# PAGE 1 CHECKS
# -------------------------------------------------------------------------
p1 = soup.find("div", id="p1")

pop_2025 = int(df_pop[df_pop["Year"] == 2025]["Population_Count"].sum())
pop_tgt = int(df_tgt["Target_2045_Population"].sum())
pop_base = int(df_tgt["Baseline_2022_Population"].sum())
pop_growth_base = pop_2025 - pop_base

hp_cum = int(df_hp[(df_hp["Year"] >= 2020) & (df_hp["Year"] <= 2025)]["Net_New_Units"].sum())
hp_tgt = int(df_tgt["Target_2045_Housing_Units"].sum())
hp_pct = (hp_cum / hp_tgt) * 100

hp_2025 = df_hp[df_hp["Year"] == 2025]
sf_2025 = int(hp_2025["Single_Family_Units"].sum())
mf_2025 = int((hp_2025["Duplex_Units"] + hp_2025["MultiFamily_3_4_Units"] + hp_2025["MultiFamily_5_Plus_Units"]).sum())
adu_2025 = int(hp_2025["ADU_Units"].sum())
dem_2025 = int(hp_2025["Demolished_Units"].sum())
net_2025 = int(hp_2025["Net_New_Units"].sum())
gross_2025 = sf_2025 + mf_2025 + adu_2025

emp_base = int(df_tgt["Baseline_2022_Employment"].sum())
emp_tgt = int(df_tgt["Target_2045_Employment"].sum())
emp_2025_qcew = int(df_emp[(df_emp["Year"] == 2025) & (df_emp["Is_County_Total"] == 1)]["Annual_Average_Employment"].iloc[0])

p1_cards = p1.find_all("div", class_="card")
# Card 1: Population
c1_val = p1_cards[0].find("div", class_="card-value").text
c1_comp = p1_cards[0].find("div", class_="card-comparison").text
check("Page 1 KPI", "Total Population (2025)", c1_val, f"{pop_2025:,}")
check("Page 1 KPI", "Pop Adopted 2045 Target", re.search(r"Target:\s*([\d,]+)", c1_comp).group(1), f"{pop_tgt:,}")
check("Page 1 KPI", "Pop Baseline 2022", re.search(r"Baseline 2022:\s*([\d,]+)", c1_comp).group(1), f"{pop_base:,}")
check("Page 1 KPI", "Pop Growth from 2022", re.search(r"\(\+([\d,]+)\)", c1_comp).group(1), f"{pop_growth_base:,}")

# Card 2: Net Housing Built
c2_val = p1_cards[1].find("div", class_="card-value").text
c2_comp = p1_cards[1].find("div", class_="card-comparison").text
check("Page 1 KPI", "Net Housing Built (2020-Pres)", c2_val, f"{hp_cum:,}")
check("Page 1 KPI", "Housing Target Progress %", re.search(r"([\d\.]+)%", c2_comp).group(1), f"{hp_pct:.1f}")
check("Page 1 KPI", "Housing Target in Comp", re.search(r"of\s*([\d,]+)\s*target", c2_comp).group(1), f"{hp_tgt:,}")

# Card 3: 2025 Net Permitted
c3_val = p1_cards[2].find("div", class_="card-value").text
c3_comp = p1_cards[2].find("div", class_="card-comparison").text
check("Page 1 KPI", "2025 Net Permitted Units", c3_val, f"{net_2025:,}")
check("Page 1 KPI", "2025 Gross Units", re.search(r"Gross:\s*([\d,]+)", c3_comp).group(1), f"{gross_2025:,}")
check("Page 1 KPI", "2025 Demolished Units", re.search(r"Demolished:\s*([\d,]+)", c3_comp).group(1), f"{dem_2025:,}")

# Card 4: Employment (Covered Jobs 2025 QCEW)
c4_val = p1_cards[3].find("div", class_="card-value").text
c4_comp = p1_cards[3].find("div", class_="card-comparison").text
check("Page 1 KPI", "Covered Jobs 2025 (QCEW)", c4_val, f"{emp_2025_qcew:,}")
check("Page 1 KPI", "Employment 2022 Total Baseline", re.search(r"2022 Total Baseline:\s*([\d,]+)", c4_comp).group(1), f"{emp_base:,}")
check("Page 1 KPI", "Employment 2045 Total Target", re.search(r"Target:\s*([\d,]+)", c4_comp).group(1), f"{emp_tgt:,}")

# 2. Page 1 Population Trajectory Chart
pop_traj = df_pop[df_pop["Year"].between(2020, 2025)].groupby("Year")["Population_Count"].sum().to_dict()
p1_chart1 = p1.find("div", class_="visual-subtitle")
check("Page 1 Chart", "Pop Trajectory 2020-2025 Growth", re.search(r"\+([\d,]+)\s*/", p1_chart1.text).group(1), f"{pop_2025 - pop_traj[2020]:,}")
p1_chart1_svg = p1.find_all("svg", class_="chart-svg")[0]
for y in [2020, 2021, 2022, 2023, 2024, 2025]:
    m = re.search(rf"{y}[\s\S]*?\(([\d,]+)\)", p1_chart1_svg.text)
    check("Page 1 Chart", f"Pop Trajectory Year {y}", m.group(1), f"{pop_traj[y]:,}")

# 3. Page 1 Benchmark Typology Bars (every benchmark year: 2010, 2015, 2020, 2025)
p1_perm_svg = p1.find_all("svg", class_="chart-svg")[1]
b_groups = p1_perm_svg.find_all("g", class_="benchmark-year-group")
for grp in b_groups:
    byr = int(grp["data-year"])
    b_sf = grp["data-sf"]
    b_mf = grp["data-mf"]
    b_adu = grp["data-adu"]
    df_by = df_hp[df_hp["Year"] == byr]
    exp_b_sf = int(df_by["Single_Family_Units"].sum())
    exp_b_mf = int((df_by["Duplex_Units"] + df_by["MultiFamily_3_4_Units"] + df_by["MultiFamily_5_Plus_Units"]).sum())
    exp_b_adu = int(df_by["ADU_Units"].sum())
    check("Page 1 Benchmark Bars", f"{byr} SF Permits", b_sf, str(exp_b_sf))
    check("Page 1 Benchmark Bars", f"{byr} MF Permits", b_mf, str(exp_b_mf))
    check("Page 1 Benchmark Bars", f"{byr} ADU Permits", b_adu, str(exp_b_adu))

# 4. Page 1 Reconciliation Table
p1_table = p1.find("table", class_="table-visual")
p1_rows = p1_table.find("tbody").find_all("tr")

tgt_indexed = df_tgt.set_index("Jurisdiction_ID")
pop_2025_idx = df_pop[df_pop["Year"] == 2025].set_index("Jurisdiction_ID")
hp_cum_idx = df_hp[(df_hp["Year"] >= 2020) & (df_hp["Year"] <= 2025)].groupby("Jurisdiction_ID")["Net_New_Units"].sum()

jur_order = [
    "JUR-01", "JUR-02", "JUR-03", "JUR-04", "JUR-05", 
    "JUR-06", "JUR-07", "JUR-08", "JUR-09", "JUR-10", "JUR-11"
]

for idx, jid in enumerate(jur_order):
    tr = p1_rows[idx]
    tds = tr.find_all("td")
    name = tds[0].text.strip()
    j_type = tds[1].text.strip()
    pop_cell = tds[2].text.strip()
    pop_tgt_cell = tds[3].text.strip()
    net_h_cell = tds[4].text.strip()
    tgt_h_cell = tds[5].text.strip()
    pct_cell = tds[6].text.strip()

    exp_name = tgt_indexed.loc[jid, "Jurisdiction_Name"]
    exp_pop = int(pop_2025_idx.loc[jid, "Population_Count"])
    exp_pop_tgt = int(tgt_indexed.loc[jid, "Target_2045_Population"])
    exp_h_cum = int(hp_cum_idx.get(jid, 0))
    exp_h_tgt = int(tgt_indexed.loc[jid, "Target_2045_Housing_Units"])
    exp_pct = f"{(exp_h_cum / exp_h_tgt * 100):.1f}%" if exp_h_tgt > 0 else "—"

    check("Page 1 Table", f"{exp_name} 2025 Pop", pop_cell, f"{exp_pop:,}")
    check("Page 1 Table", f"{exp_name} 2045 Pop Target", pop_tgt_cell, f"{exp_pop_tgt:,}")
    check("Page 1 Table", f"{exp_name} Net Housing", net_h_cell, f"{exp_h_cum:,}")
    check("Page 1 Table", f"{exp_name} 2045 Housing Target", tgt_h_cell, f"{exp_h_tgt:,}")
    check("Page 1 Table", f"{exp_name} Target %", pct_cell, exp_pct)

# Page 1 Table Total Row
total_tds = p1_rows[11].find_all("td")
check("Page 1 Total", "Total Pop 2025", total_tds[2].text, f"{pop_2025:,}")
check("Page 1 Total", "Total Pop Target 2045", total_tds[3].text, f"{pop_tgt:,}")
check("Page 1 Total", "Total Net Housing Cum", total_tds[4].text, f"{hp_cum:,}")
check("Page 1 Total", "Total Housing Target", total_tds[5].text, f"{hp_tgt:,}")
check("Page 1 Total", "Total Progress %", total_tds[6].text, f"{hp_pct:.1f}%")

# -------------------------------------------------------------------------
# PAGE 2 CHECKS
# -------------------------------------------------------------------------
p2 = soup.find("div", id="p2")
p2_cards = p2.find_all("div", class_="card")

# KPI Cards
check("Page 2 KPI", "2025 Net New Units", p2_cards[0].find("div", class_="card-value").text, f"{net_2025:,}")
check("Page 2 KPI", "2025 Single-Family Units", p2_cards[1].find("div", class_="card-value").text, f"{sf_2025:,}")
check("Page 2 KPI", "2025 Multi-Family Units", p2_cards[2].find("div", class_="card-value").text, f"{mf_2025:,}")
check("Page 2 KPI", "2025 ADU Units", p2_cards[3].find("div", class_="card-value").text, f"{adu_2025:,}")

# Card Shares
c1_sh = p2_cards[1].find("div", class_="card-comparison").text
c2_sh = p2_cards[2].find("div", class_="card-comparison").text
c3_sh = p2_cards[3].find("div", class_="card-comparison").text
check("Page 2 KPI", "SF Share %", re.search(r"([\d\.]+)%", c1_sh).group(1), f"{(sf_2025/gross_2025*100):.1f}")
check("Page 2 KPI", "MF Share %", re.search(r"([\d\.]+)%", c2_sh).group(1), f"{(mf_2025/gross_2025*100):.1f}")
check("Page 2 KPI", "ADU Share %", re.search(r"([\d\.]+)%", c3_sh).group(1), f"{(adu_2025/gross_2025*100):.1f}")

# Page 2 Permitting Matrix
p2_table = p2.find("table", class_="table-visual")
p2_rows = p2_table.find("tbody").find_all("tr")

hp_2025_idx = df_hp[df_hp["Year"] == 2025].set_index("Jurisdiction_ID")
for idx, jid in enumerate(jur_order):
    tr = p2_rows[idx]
    tds = tr.find_all("td")
    name = tds[0].text.strip()
    sf_cell = tds[1].text.strip()
    mf_cell = tds[2].text.strip()
    adu_cell = tds[3].text.strip()
    dem_cell = tds[4].text.strip()
    net_cell = tds[5].text.strip()

    exp_name = tgt_indexed.loc[jid, "Jurisdiction_Name"]
    if jid in hp_2025_idx.index:
        r_hp = hp_2025_idx.loc[jid]
        exp_sf = int(r_hp["Single_Family_Units"])
        exp_mf = int(r_hp["Duplex_Units"] + r_hp["MultiFamily_3_4_Units"] + r_hp["MultiFamily_5_Plus_Units"])
        exp_adu = int(r_hp["ADU_Units"])
        exp_dem = int(r_hp["Demolished_Units"])
        exp_net = int(r_hp["Net_New_Units"])
    else:
        exp_sf = exp_mf = exp_adu = exp_dem = exp_net = 0

    check("Page 2 Matrix", f"{exp_name} SF", sf_cell, str(exp_sf))
    check("Page 2 Matrix", f"{exp_name} MF", mf_cell, str(exp_mf))
    check("Page 2 Matrix", f"{exp_name} ADU", adu_cell, str(exp_adu))
    check("Page 2 Matrix", f"{exp_name} Demolished", dem_cell, str(exp_dem))
    check("Page 2 Matrix", f"{exp_name} Net New", net_cell, str(exp_net))

# Total Row
p2_total_tds = p2_rows[11].find_all("td")
check("Page 2 Matrix Total", "Total SF", p2_total_tds[1].text, f"{sf_2025:,}")
check("Page 2 Matrix Total", "Total MF", p2_total_tds[2].text, f"{mf_2025:,}")
check("Page 2 Matrix Total", "Total ADU", p2_total_tds[3].text, f"{adu_2025:,}")
check("Page 2 Matrix Total", "Total Demolished", p2_total_tds[4].text, f"{dem_2025:,}")
check("Page 2 Matrix Total", "Total Net New", p2_total_tds[5].text, f"{net_2025:,}")

# Page 2 Stacked-Area Series (every year 2010-2025: SF, MF, ADU, Gross)
area_pts = p2.find_all("g", class_="area-data-point")
for pt in area_pts:
    ayr = int(pt["data-year"])
    a_sf = pt["data-sf"]
    a_mf = pt["data-mf"]
    a_adu = pt["data-adu"]
    a_gross = pt["data-gross"]
    
    df_ay = df_hp[df_hp["Year"] == ayr]
    exp_a_sf = int(df_ay["Single_Family_Units"].sum())
    exp_a_mf = int((df_ay["Duplex_Units"] + df_ay["MultiFamily_3_4_Units"] + df_ay["MultiFamily_5_Plus_Units"]).sum())
    exp_a_adu = int(df_ay["ADU_Units"].sum())
    exp_a_gross = exp_a_sf + exp_a_mf + exp_a_adu
    
    check("Page 2 Stacked Area", f"{ayr} SF Units", a_sf, str(exp_a_sf))
    check("Page 2 Stacked Area", f"{ayr} MF Units", a_mf, str(exp_a_mf))
    check("Page 2 Stacked Area", f"{ayr} ADU Units", a_adu, str(exp_a_adu))
    check("Page 2 Stacked Area", f"{ayr} Gross Units", a_gross, str(exp_a_gross))

# Page 2 AMI breakdown
ami_container = p2.find_all("div", class_="visual-container")[2]
ami_agg = df_ami[df_ami["Year"] == 2025].groupby("Jurisdiction_ID").agg({"Total_AMI_Units": "sum"}).reset_index().set_index("Jurisdiction_ID")
for jid in ami_agg.index:
    j_name = tgt_indexed.loc[jid, "Jurisdiction_Name"]
    exp_ami = int(ami_agg.loc[jid, "Total_AMI_Units"])
    m_ami = re.search(rf"{j_name}[\s\S]*?([\d,]+)\s*units", ami_container.text)
    check("Page 2 AMI", f"{j_name} AMI Units", m_ami.group(1), f"{exp_ami:,}")

tot_ami = int(df_ami[df_ami["Year"] == 2025]["Total_AMI_Units"].sum())
m_ami_tot = re.search(r"=\s*([\d,]+)\s*total units", ami_container.text)
check("Page 2 AMI", "Total Preliminary AMI Units", m_ami_tot.group(1), f"{tot_ami:,}")

# Page 2 AMI Bar Widths & Proportional Scaling Check
max_ami_val = ami_agg["Total_AMI_Units"].max()
ami_tracks = ami_container.find_all("div", class_="bar-track")
for track in ami_tracks:
    j_name = track["data-jurisdiction"]
    w_rend = track["data-width"]
    u_rend = int(track["data-units"])
    exp_w = f"{(u_rend / max_ami_val * 100):.1f}"
    check("Page 2 AMI Bar Width", f"{j_name} Bar Width %", w_rend, exp_w)

# Page 2 AMI Wording Compliance Check
check("Page 2 AMI Wording", "No reporting jurisdictions wording", "reporting jurisdictions with available local datasheets" in ami_container.text, False)
check("Page 2 AMI Wording", "Preliminary Commerce Notice", "Commerce default allocation (Exhibit 12)" in ami_container.text, True)

# -------------------------------------------------------------------------
# PAGE 3 CHECKS
# -------------------------------------------------------------------------
p3 = soup.find("div", id="p3")

# 1. Page 3 Population Progress Top Chart (All 11 Jurisdictions)
p3_containers = p3.find_all("div", class_="visual-container")
p3_prog_rows = p3_containers[0].find_all("div", class_="bar-row")

for row in p3_prog_rows:
    lbl = row.find("span", class_="bar-label").text.strip()
    val_txt = row.find("span", class_="bar-val").text.strip()
    m_prog = re.search(r"([\d,]+)\s*/\s*([\d,]+)", val_txt)
    exp_r = tgt_indexed[tgt_indexed["Jurisdiction_Name"] == lbl]
    jid = exp_r.index[0]
    exp_p = int(pop_2025_idx.loc[jid, "Population_Count"])
    exp_tgt = int(tgt_indexed.loc[jid, "Target_2045_Population"])
    check("Page 3 Pop Progress", f"{lbl} Pop Level", m_prog.group(1), f"{exp_p:,}")
    check("Page 3 Pop Progress", f"{lbl} Target Level", m_prog.group(2), f"{exp_tgt:,}")

# 2. Page 3 YoY Population Change
yoy_sub = re.search(r"Countywide Change:\s*\+([\d,]+)", p3.text)
check("Page 3 Chart", "YoY Countywide Pop Change", yoy_sub.group(1), f"{pop_2025 - pop_traj[2024]:,}")

p3_yoy_bars = p3_containers[1].find_all("div", class_="bar-row")
pop_2025_full = df_pop[df_pop["Year"] == 2025].set_index("Jurisdiction_ID")
for row in p3_yoy_bars:
    lbl = row.find("span", class_="bar-label").text.strip()
    val_txt = row.find("span", class_="bar-val").text.strip()
    exp_r = tgt_indexed[tgt_indexed["Jurisdiction_Name"] == lbl]
    jid = exp_r.index[0]
    exp_yoy = int(pop_2025_full.loc[jid, "YoY_Population_Change"])
    exp_yoy_str = f"+{exp_yoy:,}" if exp_yoy > 0 else f"{exp_yoy:,}"
    check("Page 3 YoY", f"{lbl} YoY Pop Change", val_txt, exp_yoy_str)

# 3. Page 3 Employment Table
p3_table = p3.find("table", class_="table-visual")
p3_rows = p3_table.find("tbody").find_all("tr")

for idx, jid in enumerate(jur_order):
    tr = p3_rows[idx]
    tds = tr.find_all("td")
    name = tds[0].text.strip()
    base = tds[1].text.strip()
    tgt = tds[2].text.strip()
    
    exp_name = tgt_indexed.loc[jid, "Jurisdiction_Name"]
    exp_base = int(tgt_indexed.loc[jid, "Baseline_2022_Employment"])
    exp_tgt = int(tgt_indexed.loc[jid, "Target_2045_Employment"])
    
    check("Page 3 Employment Table", f"{exp_name} 2022 Base", base, f"{exp_base:,}")
    check("Page 3 Employment Table", f"{exp_name} 2045 Target", tgt, f"{exp_tgt:,}")

# Total Row
p3_total_tds = p3_rows[11].find_all("td")
check("Page 3 Employment Total", "Countywide 2022 Baseline", p3_total_tds[1].text, f"{emp_base:,}")
check("Page 3 Employment Total", "Countywide 2045 Target", p3_total_tds[2].text, f"{emp_tgt:,}")

# 4. Page 3 Historical QCEW Benchmark Series (every point 1999-2025)
qcew_nodes = p3.find_all("circle", class_="qcew-node")
cai_dict = df_cai.set_index("Year")["Covered_Employment_QCEW"].to_dict()
for node in qcew_nodes:
    nyr = int(node["data-year"])
    nqcew = int(node["data-qcew"])
    if nyr == 2025:
        exp_q = emp_2025_qcew
    else:
        exp_q = int(cai_dict[nyr])
    check("Page 3 QCEW Series", f"{nyr} Covered Employment", str(nqcew), str(exp_q))

m_qcew_endpoint = re.search(r"2025 QCEW:\s*([\d,]+)", p3.text)
check("Page 3 QCEW", "2025 QCEW Endpoint Label", m_qcew_endpoint.group(1), f"{emp_2025_qcew:,}")

# -------------------------------------------------------------------------
# PAGE 4 CHECKS
# -------------------------------------------------------------------------
p4 = soup.find("div", id="p4")

cities_pop = int(pop_2025_idx.loc[[f"JUR-0{i}" for i in range(1, 9)], "Population_Count"].sum())
uga_pop = int(pop_2025_idx.loc[["JUR-09", "JUR-10"], "Population_Count"].sum())
rural_pop = int(pop_2025_idx.loc["JUR-11", "Population_Count"])

cities_share = (cities_pop / pop_2025) * 100
uga_share = (uga_pop / pop_2025) * 100
rural_share = (rural_pop / pop_2025) * 100

p4_tbody_rows = p4.find("table", class_="table-visual").find("tbody").find_all("tr")

# Row 0: Incorporated Cities Subtotal
r0_tds = [td.text.strip() for td in p4_tbody_rows[0].find_all("td")]
check("Page 4 Table", "Cities Subtotal Population", r0_tds[1], f"{cities_pop:,}")
check("Page 4 Table", "Cities Subtotal Share %", r0_tds[2], f"{cities_share:.1f}%")

# Rows 1 to 8: 8 cities
for idx in range(1, 9):
    tds = [td.text.strip() for td in p4_tbody_rows[idx].find_all("td")]
    c_type, c_name, c_pop, c_share = tds
    jid = jur_order[idx - 1]
    exp_pop = int(pop_2025_idx.loc[jid, "Population_Count"])
    exp_sh = (exp_pop / pop_2025) * 100
    check("Page 4 Table", f"{c_name} Population", c_pop, f"{exp_pop:,}")
    check("Page 4 Table", f"{c_name} Share %", c_share, f"{exp_sh:.1f}%")

# Row 9: UGAs Subtotal
r9_tds = [td.text.strip() for td in p4_tbody_rows[9].find_all("td")]
check("Page 4 Table", "UGAs Subtotal Population", r9_tds[1], f"{uga_pop:,}")
check("Page 4 Table", "UGAs Subtotal Share %", r9_tds[2], f"{uga_share:.1f}%")

# Rows 10 to 11: 2 UGAs
for idx, jid in zip([10, 11], ["JUR-09", "JUR-10"]):
    tds = [td.text.strip() for td in p4_tbody_rows[idx].find_all("td")]
    u_type, u_name, u_pop, u_share = tds
    exp_pop = int(pop_2025_idx.loc[jid, "Population_Count"])
    exp_sh = (exp_pop / pop_2025) * 100
    check("Page 4 Table", f"{u_name} Population", u_pop, f"{exp_pop:,}")
    check("Page 4 Table", f"{u_name} Share %", u_share, f"{exp_sh:.1f}%")

# Row 12: Rural Subtotal
r12_tds = [td.text.strip() for td in p4_tbody_rows[12].find_all("td")]
check("Page 4 Table", "Rural Subtotal Population", r12_tds[1], f"{rural_pop:,}")
check("Page 4 Table", "Rural Subtotal Share %", r12_tds[2], f"{rural_share:.1f}%")

# Row 13: Rural Entity
r13_tds = [td.text.strip() for td in p4_tbody_rows[13].find_all("td")]
check("Page 4 Table", "Rural Entity Population", r13_tds[2], f"{rural_pop:,}")
check("Page 4 Table", "Rural Entity Share %", r13_tds[3], f"{rural_share:.1f}%")

# Row 14: Total Skagit County
r14_tds = [td.text.strip() for td in p4_tbody_rows[14].find_all("td")]
check("Page 4 Table", "Total County Population", r14_tds[1], f"{pop_2025:,}")
check("Page 4 Table", "Total County Share %", r14_tds[2], "100.0%")

p4_map_title = p4.find_all("div", class_="visual-title")[0].text.strip()
check("Page 4 Map", "Map Title Placeholder", p4_map_title, "Approximate Centroids (Leaflet placeholder)")

# Page 4 Share Comparison Bars (Grouped horizontal bars)
p4_comp_bars = p4.find_all("div", class_="grouped-bar-row")
for bar in p4_comp_bars:
    name = bar.find("span", class_="bar-label").text.strip()
    val_spans = bar.find_all("span", class_="bar-val")
    m_pop = re.search(r"([\d\.]+)%\s*Pop", val_spans[0].text)
    m_hsg = re.search(r"([\d\.]+)%\s*Hsg", val_spans[1].text)
    exp_r = tgt_indexed[tgt_indexed["Jurisdiction_Name"] == name]
    if not exp_r.empty:
        jid = exp_r.index[0]
        exp_p = int(pop_2025_idx.loc[jid, "Population_Count"])
        exp_ht = int(tgt_indexed.loc[jid, "Target_2045_Housing_Units"])
        exp_pop_sh = (exp_p / pop_2025) * 100
        exp_h_sh = (exp_ht / hp_tgt) * 100
        check("Page 4 Share Comparison", f"{name} Pop Share %", m_pop.group(1), f"{exp_pop_sh:.1f}")
        check("Page 4 Share Comparison", f"{name} Housing Share %", m_hsg.group(1), f"{exp_h_sh:.1f}")

# Page 4 Footer Tripartite Check
p4_footer = p4.find("div", class_="page-footer").text
check("Page 4 Footer", "Cities in Footer", str(cities_pop) in p4_footer.replace(",", ""), True)
check("Page 4 Footer", "UGAs in Footer", str(uga_pop) in p4_footer.replace(",", ""), True)
check("Page 4 Footer", "Rural in Footer", str(rural_pop) in p4_footer.replace(",", ""), True)
check("Page 4 Footer", "Total in Footer", str(pop_2025) in p4_footer.replace(",", ""), True)

if __name__ == "__main__":
    print("=" * 95)
    print("SCOG REPORT DESIGN V2 MOCK-UP: COMPREHENSIVE AUTOMATED VERIFICATION AUDIT")
    print("=" * 95)
    print(f"{'Category':<24} | {'Metric / Cell':<35} | {'Rendered':<12} | {'Expected':<12} | {'Status'}")
    print("-" * 95)
    for r in results:
        print(f"{r['category']:<24} | {r['metric']:<35} | {r['rendered']:<12} | {r['expected']:<12} | {r['status']}")
    print("=" * 95)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    print(f"TOTAL CHECKS: {len(results)} | PASSED: {pass_count} | FAILED: {fail_count}")
    print("=" * 95)
    if fail_count > 0:
        exit(1)
    else:
        print("ALL CELLS, METRICS AND FIGURES SUCCESSFULLY MATCH THE PROCESSED CSVS 100%!")
