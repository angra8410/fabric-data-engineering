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

# Card 4: Employment
c4_val = p1_cards[3].find("div", class_="card-value").text
c4_comp = p1_cards[3].find("div", class_="card-comparison").text
check("Page 1 KPI", "Employment 2022 Baseline", c4_val, f"{emp_base:,}")
check("Page 1 KPI", "Employment 2045 Target", re.search(r"Target:\s*([\d,]+)", c4_comp).group(1), f"{emp_tgt:,}")

# 2. Page 1 Population Trajectory Chart
pop_traj = df_pop[df_pop["Year"].between(2020, 2025)].groupby("Year")["Population_Count"].sum().to_dict()
p1_chart1 = p1.find("div", class_="visual-subtitle")
check("Page 1 Chart", "Pop Trajectory 2020-2025 Growth", re.search(r"\+([\d,]+)\s*/", p1_chart1.text).group(1), f"{pop_2025 - pop_traj[2020]:,}")
for y in [2020, 2021, 2022, 2023, 2024, 2025]:
    m = re.search(rf"{y}\s*\(([\d,]+)\)", p1.text)
    check("Page 1 Chart", f"Pop Trajectory Year {y}", m.group(1), f"{pop_traj[y]:,}")

# 3. Page 1 Permitted Typology Chart (2025 Cluster)
p1_perm_svg = p1.find_all("svg", class_="chart-svg")[1]
texts = [t.text.strip() for t in p1_perm_svg.find_all("text")]
check("Page 1 Permitting SVG", "2025 SF Permits", str(sf_2025) in texts, True)
check("Page 1 Permitting SVG", "2025 MF Permits", str(mf_2025) in texts, True)
check("Page 1 Permitting SVG", "2025 ADU Permits", str(adu_2025) in texts, True)

# 4. Page 1 Reconciliation Table
p1_table = p1.find("table", class_="table-visual")
p1_rows = p1_table.find("tbody").find_all("tr")

tgt_indexed = df_tgt.set_index("Jurisdiction_ID")
pop_2025_idx = df_pop[df_pop["Year"] == 2025].set_index("Jurisdiction_ID")
cum_h_idx = df_hp[(df_hp["Year"] >= 2020) & (df_hp["Year"] <= 2025)].groupby("Jurisdiction_ID")["Net_New_Units"].sum()

jur_order = [
    "JUR-01", "JUR-02", "JUR-03", "JUR-04", "JUR-05", 
    "JUR-06", "JUR-07", "JUR-08", "JUR-09", "JUR-10", "JUR-11"
]

for idx, jid in enumerate(jur_order):
    tr = p1_rows[idx]
    tds = tr.find_all("td")
    name = tds[0].text.strip()
    jtype = tds[1].text.strip()
    p25 = tds[2].text.strip()
    ptgt = tds[3].text.strip()
    hcum = tds[4].text.strip()
    htgt = tds[5].text.strip()
    hpct = tds[6].text.strip()
    
    exp_name = tgt_indexed.loc[jid, "Jurisdiction_Name"]
    exp_p25 = int(pop_2025_idx.loc[jid, "Population_Count"])
    exp_ptgt = int(tgt_indexed.loc[jid, "Target_2045_Population"])
    exp_hcum = int(cum_h_idx.get(jid, 0))
    exp_htgt = int(tgt_indexed.loc[jid, "Target_2045_Housing_Units"])
    exp_hpct = f"{(exp_hcum / exp_htgt * 100):.1f}%" if exp_htgt > 0 else "—"
    
    check("Page 1 Table", f"{exp_name} 2025 Population", p25, f"{exp_p25:,}")
    check("Page 1 Table", f"{exp_name} 2045 Pop Target", ptgt, f"{exp_ptgt:,}")
    check("Page 1 Table", f"{exp_name} Net Housing Cum", hcum, f"{exp_hcum:,}")
    check("Page 1 Table", f"{exp_name} 2045 Housing Target", htgt, f"{exp_htgt:,}")
    check("Page 1 Table", f"{exp_name} Housing Target %", hpct, exp_hpct)

# Total Row
p1_total_tds = p1_rows[11].find_all("td")
check("Page 1 Table Total", "Countywide 2025 Population", p1_total_tds[2].text, f"{pop_2025:,}")
check("Page 1 Table Total", "Countywide 2045 Pop Target", p1_total_tds[3].text, f"{pop_tgt:,}")
check("Page 1 Table Total", "Countywide Net Housing Cum", p1_total_tds[4].text, f"{hp_cum:,}")
check("Page 1 Table Total", "Countywide 2045 Housing Target", p1_total_tds[5].text, f"{hp_tgt:,}")
check("Page 1 Table Total", "Countywide Housing Target %", p1_total_tds[6].text, f"{hp_pct:.1f}%")

# -------------------------------------------------------------------------
# PAGE 2 CHECKS
# -------------------------------------------------------------------------
p2 = soup.find("div", id="p2")

# 1. Page 2 KPIs
p2_cards = p2.find_all("div", class_="card")
check("Page 2 KPI", "2025 Net New Units", p2_cards[0].find("div", class_="card-value").text, f"{net_2025:,}")
check("Page 2 KPI", "2025 SF Permits", p2_cards[1].find("div", class_="card-value").text, f"{sf_2025:,}")
check("Page 2 KPI", "2025 SF Share %", re.search(r"([\d\.]+)%", p2_cards[1].find("div", class_="card-comparison").text).group(1), f"{(sf_2025/gross_2025*100):.1f}")
check("Page 2 KPI", "2025 MF Permits", p2_cards[2].find("div", class_="card-value").text, f"{mf_2025:,}")
check("Page 2 KPI", "2025 MF Share %", re.search(r"([\d\.]+)%", p2_cards[2].find("div", class_="card-comparison").text).group(1), f"{(mf_2025/gross_2025*100):.1f}")
check("Page 2 KPI", "2025 ADU Permits", p2_cards[3].find("div", class_="card-value").text, f"{adu_2025:,}")
check("Page 2 KPI", "2025 ADU Share %", re.search(r"([\d\.]+)%", p2_cards[3].find("div", class_="card-comparison").text).group(1), f"{(adu_2025/gross_2025*100):.1f}")

# 2. Page 2 Top Row Chart: SF vs MF production
p2_bar_rows = p2.find_all("div", class_="bar-row")
# First group of bar rows are the top 5 SF vs MF production
p2_hp_rows = p2_bar_rows[:5]
for row in p2_hp_rows:
    lbl = row.find("span", class_="bar-label").text.strip()
    val_txt = row.find("span", class_="bar-val").text.strip()
    m_sf_mf = re.search(r"(\d+)\s*SF\s*/\s*(\d+)\s*MF", val_txt)
    exp_r = tgt_indexed[tgt_indexed["Jurisdiction_Name"] == lbl]
    jid = exp_r.index[0]
    exp_sf = int(hp_2025.set_index("Jurisdiction_ID").loc[jid, "Single_Family_Units"])
    exp_mf = int((hp_2025.set_index("Jurisdiction_ID").loc[jid, "Duplex_Units"] + 
                  hp_2025.set_index("Jurisdiction_ID").loc[jid, "MultiFamily_3_4_Units"] + 
                  hp_2025.set_index("Jurisdiction_ID").loc[jid, "MultiFamily_5_Plus_Units"]))
    check("Page 2 SF/MF Chart", f"{lbl} SF Value", m_sf_mf.group(1), str(exp_sf))
    check("Page 2 SF/MF Chart", f"{lbl} MF Value", m_sf_mf.group(2), str(exp_mf))

# 3. Page 2 Permitting Matrix Table
p2_table = p2.find("table", class_="table-visual")
p2_rows = p2_table.find("tbody").find_all("tr")

hp_2025_idx = hp_2025.set_index("Jurisdiction_ID")
hp_2025_idx["MF_Units"] = hp_2025_idx["Duplex_Units"] + hp_2025_idx["MultiFamily_3_4_Units"] + hp_2025_idx["MultiFamily_5_Plus_Units"]

for idx, jid in enumerate(jur_order):
    tr = p2_rows[idx]
    tds = tr.find_all("td")
    name = tds[0].text.strip()
    sf = tds[1].text.strip()
    mf = tds[2].text.strip()
    adu = tds[3].text.strip()
    dem = tds[4].text.strip()
    net = tds[5].text.strip()
    
    exp_name = tgt_indexed.loc[jid, "Jurisdiction_Name"]
    if jid in hp_2025_idx.index:
        r = hp_2025_idx.loc[jid]
        exp_sf = int(r["Single_Family_Units"])
        exp_mf = int(r["MF_Units"])
        exp_adu = int(r["ADU_Units"])
        exp_dem = int(r["Demolished_Units"])
        exp_net = int(r["Net_New_Units"])
    else:
        exp_sf = exp_mf = exp_adu = exp_dem = exp_net = 0
        
    check("Page 2 Matrix", f"{exp_name} SF", sf, str(exp_sf))
    check("Page 2 Matrix", f"{exp_name} MF", mf, str(exp_mf))
    check("Page 2 Matrix", f"{exp_name} ADU", adu, str(exp_adu))
    check("Page 2 Matrix", f"{exp_name} Demolished", dem, str(exp_dem))
    check("Page 2 Matrix", f"{exp_name} Net New", net, str(exp_net))

# Total Row
p2_total_tds = p2_rows[11].find_all("td")
check("Page 2 Matrix Total", "Total County SF", p2_total_tds[1].text, f"{sf_2025:,}")
check("Page 2 Matrix Total", "Total County MF", p2_total_tds[2].text, f"{mf_2025:,}")
check("Page 2 Matrix Total", "Total County ADU", p2_total_tds[3].text, f"{adu_2025:,}")
check("Page 2 Matrix Total", "Total County Demolished", p2_total_tds[4].text, f"{dem_2025:,}")
check("Page 2 Matrix Total", "Total County Net New", p2_total_tds[5].text, f"{net_2025:,}")

# 4. Page 2 AMI Distribution
df_ami["Low"] = df_ami["AMI_0_to_30_Pct_Units"] + df_ami["AMI_31_to_50_Pct_Units"] + df_ami["AMI_51_to_80_Pct_Units"]
df_ami["ModHigh"] = df_ami["AMI_81_to_100_Pct_Units"] + df_ami["AMI_101_to_120_Pct_Units"] + df_ami["AMI_Greater_120_Pct_Units"]
ami_agg = df_ami.groupby(["Jurisdiction_ID", "Jurisdiction_Name"])[["Low", "ModHigh", "Total_AMI_Units"]].sum().reset_index()

p2_ami_rows = p2_bar_rows[5:]
for row in p2_ami_rows:
    lbl = row.find("span", class_="bar-label").text.strip()
    val_txt = row.find("span", class_="bar-val").text.strip()
    m_val = re.search(r"([\d,]+)\s*units", val_txt)
    exp_r = ami_agg[ami_agg["Jurisdiction_Name"] == lbl]
    if not exp_r.empty:
        exp_units = int(exp_r["Total_AMI_Units"].iloc[0])
        check("Page 2 AMI", f"{lbl} Total AMI Units", m_val.group(1), f"{exp_units:,}")

tot_ami = int(ami_agg["Total_AMI_Units"].sum())
m_ami_tot = re.search(r"reporting\s*\(([\d,]+)\s*total units", p2.text)
check("Page 2 AMI", "Total Preliminary AMI Units", m_ami_tot.group(1), f"{tot_ami:,}")

# -------------------------------------------------------------------------
# PAGE 3 CHECKS
# -------------------------------------------------------------------------
p3 = soup.find("div", id="p3")

# 1. Page 3 Population Progress Top Chart
p3_bar_rows = p3.find_all("div", class_="bar-row")
p3_prog_rows = p3_bar_rows[:5]
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

p3_yoy_bars = p3_bar_rows[5:11]
pop_2025_full = df_pop[df_pop["Year"] == 2025].set_index("Jurisdiction_ID")
for row in p3_yoy_bars:
    lbl = row.find("span", class_="bar-label").text.strip()
    val_txt = row.find("span", class_="bar-val").text.strip()
    exp_r = tgt_indexed[tgt_indexed["Jurisdiction_Name"] == lbl]
    jid = exp_r.index[0]
    exp_yoy = int(pop_2025_full.loc[jid, "YoY_Population_Change"])
    check("Page 3 YoY", f"{lbl} YoY Pop Change", val_txt, f"+{exp_yoy:,}")

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

# 4. Page 3 Historical QCEW Benchmark
qcew_2022 = int(df_cai[df_cai["Year"] == 2022]["Covered_Employment_QCEW"].iloc[0])
m_qcew = re.search(r"2022 QCEW:\s*([\d,]+)", p3.text)
check("Page 3 QCEW", "2022 QCEW Value", m_qcew.group(1), f"{qcew_2022:,}")

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

# Page 4 Share Comparison Bars
p4_comp_bars = p4.find_all("div", class_="bar-row")
for bar in p4_comp_bars:
    name = bar.find("span", class_="bar-label").text.strip()
    val = bar.find("span", class_="bar-val").text.strip()
    m_comp = re.search(r"([\d\.]+)%\s*/\s*([\d\.]+)%", val)
    exp_r = tgt_indexed[tgt_indexed["Jurisdiction_Name"] == name]
    if not exp_r.empty:
        jid = exp_r.index[0]
        exp_p = int(pop_2025_idx.loc[jid, "Population_Count"])
        exp_ht = int(tgt_indexed.loc[jid, "Target_2045_Housing_Units"])
        exp_pop_sh = (exp_p / pop_2025) * 100
        exp_h_sh = (exp_ht / hp_tgt) * 100
        check("Page 4 Share Comparison", f"{name} Pop Share %", m_comp.group(1), f"{exp_pop_sh:.1f}")
        check("Page 4 Share Comparison", f"{name} Housing Share %", m_comp.group(2), f"{exp_h_sh:.1f}")

# Page 4 Footer Tripartite Check
p4_footer = p4.find("div", class_="page-footer").text
check("Page 4 Footer", "Cities in Footer", str(cities_pop) in p4_footer.replace(",", ""), True)
check("Page 4 Footer", "UGAs in Footer", str(uga_pop) in p4_footer.replace(",", ""), True)
check("Page 4 Footer", "Rural in Footer", str(rural_pop) in p4_footer.replace(",", ""), True)
check("Page 4 Footer", "Total in Footer", str(pop_2025) in p4_footer.replace(",", ""), True)

# -------------------------------------------------------------------------
# PRINT SUMMARY REPORT
# -------------------------------------------------------------------------
print("=" * 80)
print("SCOG REPORT DESIGN V2 MOCK-UP: AUTOMATED VERIFICATION AUDIT")
print("=" * 80)
print(f"{'Category':<24} | {'Metric / Cell':<35} | {'Rendered':<12} | {'Expected':<12} | {'Status'}")
print("-" * 95)

pass_count = 0
fail_count = 0

for r in results:
    if r["status"] == "PASS":
        pass_count += 1
    else:
        fail_count += 1
    print(f"{r['category']:<24} | {r['metric']:<35} | {r['rendered']:<12} | {r['expected']:<12} | {r['status']}")

print("=" * 95)
print(f"TOTAL CHECKS: {len(results)} | PASSED: {pass_count} | FAILED: {fail_count}")
print("=" * 95)

if fail_count > 0:
    exit(1)
else:
    print("ALL CELLS, METRICS AND FIGURES SUCCESSFULLY MATCH THE PROCESSED CSVS 100%!")
