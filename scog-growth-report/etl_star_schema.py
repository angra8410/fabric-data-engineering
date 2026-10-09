import os
import re
import csv
import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# JURISDICTION NORMALIZATION MAP
# -----------------------------------------------------------------------------
JURISDICTION_MASTER = [
    {"Jurisdiction_ID": "JUR-01", "Jurisdiction_Name": "Anacortes", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-02", "Jurisdiction_Name": "Burlington", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-03", "Jurisdiction_Name": "Concrete", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-04", "Jurisdiction_Name": "Hamilton", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-05", "Jurisdiction_Name": "La Conner", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-06", "Jurisdiction_Name": "Lyman", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-07", "Jurisdiction_Name": "Mount Vernon", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-08", "Jurisdiction_Name": "Sedro-Woolley", "Jurisdiction_Type": "Incorporated City/Town", "Is_Incorporated": 1, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-09", "Jurisdiction_Name": "Bay View Ridge UGA", "Jurisdiction_Type": "Urban Growth Area (UGA)", "Is_Incorporated": 0, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-10", "Jurisdiction_Name": "Swinomish UGA", "Jurisdiction_Type": "Urban Growth Area (UGA)", "Is_Incorporated": 0, "Is_UGA": 1},
    {"Jurisdiction_ID": "JUR-11", "Jurisdiction_Name": "Unincorporated Skagit County", "Jurisdiction_Type": "Unincorporated Rural Area", "Is_Incorporated": 0, "Is_UGA": 0},
]

NAME_NORM_MAP = {
    "anacortes": "Anacortes",
    "burlington": "Burlington",
    "concrete": "Concrete",
    "hamilton": "Hamilton",
    "la conner": "La Conner",
    "laconner": "La Conner",
    "lyman": "Lyman",
    "mount vernon": "Mount Vernon",
    "mount\nvernon": "Mount Vernon",
    "mt vernon": "Mount Vernon",
    "sedro-woolley": "Sedro-Woolley",
    "sedro woolley": "Sedro-Woolley",
    "sedrowoolley": "Sedro-Woolley",
    "sedro-\nwoolley": "Sedro-Woolley",
    "sedro- woolley": "Sedro-Woolley",
    "bay view ridge": "Bay View Ridge UGA",
    "bayview ridge": "Bay View Ridge UGA",
    "bayview\nridge": "Bay View Ridge UGA",
    "bay view ridge uga": "Bay View Ridge UGA",
    "swinomish": "Swinomish UGA",
    "swinomish non-trust lands": "Swinomish UGA",
    "swinomish uga": "Swinomish UGA",
    "unincorporated": "Unincorporated Skagit County",
    "unincorporated skagit county": "Unincorporated Skagit County",
    "rural (outside ugas)": "Unincorporated Skagit County",
    "rural (outside of ugas)": "Unincorporated Skagit County",
    "rural (outside of uga's)": "Unincorporated Skagit County",
    "rural (outside of\nuga's)": "Unincorporated Skagit County",
    "rural (outside of\nugas)": "Unincorporated Skagit County",
    "rural (outside of uga’s)": "Unincorporated Skagit County",
    "rural (outside of\nuga’s)": "Unincorporated Skagit County",
}

def normalize_name(raw_name):
    if not raw_name:
        return None
    cleaned = str(raw_name).strip().lower().replace("  ", " ").replace("’", "'")
    if cleaned in NAME_NORM_MAP:
        return NAME_NORM_MAP[cleaned]
    cleaned_flat = cleaned.replace("\n", " ").replace("- ", "-").replace("  ", " ")
    return NAME_NORM_MAP.get(cleaned_flat, str(raw_name).strip())

def clean_num(val):
    if val is None or val == "" or str(val).strip() in ["*", "-", "N/A", "None"]:
        return 0
    s = str(val).replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        return float(s) if "." in s else int(s)
    except:
        return 0

# -----------------------------------------------------------------------------
# 1. BUILD DIM_JURISDICTION
# -----------------------------------------------------------------------------
def build_dim_jurisdiction():
    print("-> Building Dim_Jurisdiction...")
    df = pd.DataFrame(JURISDICTION_MASTER)
    df["County_Name"] = "Skagit"
    df["State"] = "WA"
    return df

# -----------------------------------------------------------------------------
# 2. BUILD DIM_CALENDARYEAR
# -----------------------------------------------------------------------------
def build_dim_calendaryear():
    print("-> Building Dim_CalendarYear...")
    years = list(range(1990, 2046))
    records = []
    for y in years:
        decade = f"{(y // 10) * 10}s"
        if y < 2000:
            cycle = "Early GMA Foundation (1990-1999)"
        elif y < 2020:
            cycle = "Prior Comprehensive Cycle (2000-2019)"
        else:
            cycle = "Active GMA 20-Year Horizon (2020-2045)"
            
        records.append({
            "Year": y,
            "Decade": decade,
            "GMA_Planning_Cycle": cycle,
            "Is_Historical": 1 if y <= 2026 else 0,
            "Is_Prototype_Year_2025": 1 if y == 2025 else 0,
            "Is_Production_Year_2026": 1 if y == 2026 else 0,
            "Is_Target_Year_2045": 1 if y == 2045 else 0
        })
    return pd.DataFrame(records)

# -----------------------------------------------------------------------------
# 3. BUILD DIM_GMA_2045_TARGET
# -----------------------------------------------------------------------------
def build_dim_gma_2045_target(dim_jur):
    print("-> Building Dim_GMA_2045_Target...")
    path = os.path.join(RAW_DIR, "2045-Adopted-SkagitCounty-GrowthProjectionsAndAllocationsTables.xlsx")
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb['Table 1']
    
    # Table 1: Population Allocations (rows 5 to 14, 16)
    pop_dict = {}
    for r in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]:
        name = normalize_name(ws.cell(r, 1).value)
        p22 = clean_num(ws.cell(r, 6).value)
        p45 = clean_num(ws.cell(r, 8).value)
        pgrowth = clean_num(ws.cell(r, 11).value)
        pshare = clean_num(ws.cell(r, 13).value)
        pop_dict[name] = (p22, p45, pgrowth, pshare)

    # Table 2: Housing Allocations - Net New Housing Needed 2020-2045 (rows 22 to 31, 33)
    hsg_dict = {}
    for r in [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 33]:
        name = normalize_name(ws.cell(r, 1).value)
        tot_hsg = clean_num(ws.cell(r, 16).value)
        hsg_dict[name] = tot_hsg

    # Table 3: Employment Allocations (rows 40 to 49, 51)
    emp_dict = {}
    for r in [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 51]:
        name = normalize_name(ws.cell(r, 1).value)
        e22 = clean_num(ws.cell(r, 6).value)
        e45 = clean_num(ws.cell(r, 9).value)
        egrowth = clean_num(ws.cell(r, 11).value)
        eshare = clean_num(ws.cell(r, 13).value)
        emp_dict[name] = (e22, e45, egrowth, eshare)

    wb.close()
    
    records = []
    for _, j in dim_jur.iterrows():
        jname = j["Jurisdiction_Name"]
        p22, p45, pgrowth, pshare = pop_dict.get(jname, (0, 0, 0, 0))
        h45 = hsg_dict.get(jname, 0)
        e22, e45, egrowth, eshare = emp_dict.get(jname, (0, 0, 0, 0))
        records.append({
            "Jurisdiction_ID": j["Jurisdiction_ID"],
            "Jurisdiction_Name": jname,
            "Jurisdiction_Type": j["Jurisdiction_Type"],
            "Baseline_2022_Population": p22,
            "Target_2045_Population": p45,
            "Projected_2045_Population_Growth": pgrowth,
            "Population_Growth_Share_Pct": round(float(pshare), 4) if pshare else 0.0,
            "Target_2045_Housing_Units": h45,
            "Baseline_2022_Employment": e22,
            "Target_2045_Employment": e45,
            "Projected_2045_Employment_Growth": egrowth,
            "Employment_Growth_Share_Pct": round(float(eshare), 4) if eshare else 0.0,
            "CAI_Self_Employment_Multiplier": 1.15458,
            "Data_Source": "Appendix A. Skagit County 2045 Growth Projections & Allocations (O20250002)"
        })
        
    return pd.DataFrame(records)

# -----------------------------------------------------------------------------
# 4. BUILD FACT_POPULATION
# -----------------------------------------------------------------------------
def build_fact_population(dim_jur):
    print("-> Building Fact_Population...")
    records = []
    
    # 4.1 OFM April 1 Population Final (Cities & County)
    ofm_path = os.path.join(RAW_DIR, "ofm_april1_population_final(Population).csv")
    with open(ofm_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for _ in range(4): # skip first 4 lines
            next(reader, None)
        header = next(reader)
        # Year columns in line 5
        year_cols = []
        for idx, col in enumerate(header):
            m = re.search(r'(20\d\d)', col)
            if m:
                year_cols.append((idx, int(m.group(1))))
                
        for row in reader:
            if len(row) > 3 and row[2].strip() == "Skagit":
                raw_jur = row[3].strip()
                if raw_jur in ["Skagit County", "Incorporated Skagit County"]:
                    continue # keep granular jurisdictions; rollups happen in Power BI
                norm_jur = normalize_name(raw_jur)
                
                for col_idx, yr in year_cols:
                    if col_idx < len(row):
                        pop_val = clean_num(row[col_idx])
                        if pop_val > 0:
                            records.append({
                                "Jurisdiction_Name": norm_jur,
                                "Year": yr,
                                "Population_Count": pop_val,
                                "Data_Source_Type": "OFM_April1_Official_Determination"
                            })

    # 4.2 SAEP UGA Population (UGAs historical 2010 to 2026)
    saep_path = os.path.join(RAW_DIR, "saep_uga20p(Total Population).csv")
    with open(saep_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for _ in range(11):
            next(reader, None)
        header = next(reader)
        uga_year_cols = []
        for idx, col in enumerate(header):
            m = re.search(r'(20\d\d)', col)
            if m:
                uga_year_cols.append((idx, int(m.group(1))))
                
        for row in reader:
            if len(row) > 2 and row[0].strip().lower() == "skagit":
                raw_uga = row[2].strip()
                norm_uga = normalize_name(raw_uga)
                # Only take unincorporated UGAs not covered by OFM city records (Bay View Ridge & Swinomish)
                if norm_uga in ["Bay View Ridge UGA", "Swinomish UGA"]:
                    for col_idx, yr in uga_year_cols:
                        if col_idx < len(row):
                            pop_val = clean_num(row[col_idx])
                            if pop_val > 0:
                                records.append({
                                    "Jurisdiction_Name": norm_uga,
                                    "Year": yr,
                                    "Population_Count": pop_val,
                                    "Data_Source_Type": "OFM_SAEP_UGA_Estimate"
                                })

    df = pd.DataFrame(records)
    # Deduplicate if any overlap
    df = df.drop_duplicates(subset=["Jurisdiction_Name", "Year"])
    
    # Merge Jurisdiction_ID
    df = pd.merge(df, dim_jur[["Jurisdiction_ID", "Jurisdiction_Name"]], on="Jurisdiction_Name", how="inner")
    
    # Calculate Prior Year & YoY Changes
    df = df.sort_values(by=["Jurisdiction_ID", "Year"]).reset_index(drop=True)
    df["Prior_Year_Population"] = df.groupby("Jurisdiction_ID")["Population_Count"].shift(1)
    df["YoY_Population_Change"] = df["Population_Count"] - df["Prior_Year_Population"]
    df["YoY_Growth_Rate_Pct"] = (df["YoY_Population_Change"] / df["Prior_Year_Population"]).round(4)
    
    df["Fact_Population_Key"] = [f"FPOP-{i+1:05d}" for i in range(len(df))]
    
    cols_order = [
        "Fact_Population_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name",
        "Population_Count", "Prior_Year_Population", "YoY_Population_Change", "YoY_Growth_Rate_Pct",
        "Data_Source_Type"
    ]
    return df[cols_order]

# -----------------------------------------------------------------------------
# 5. BUILD FACT_HOUSINGPERMITS
# -----------------------------------------------------------------------------
def build_fact_housing_permits(dim_jur):
    print("-> Building Fact_HousingPermits...")
    records = []
    
    # 5.1 Historical Permits from OFM (1990 - 2026)
    ofm_perm_path = os.path.join(RAW_DIR, "ofm_april1_postcensal_permits_1990-present.xlsx")
    wb = openpyxl.load_workbook(ofm_perm_path, data_only=True)
    ws = wb['PermitCompletionDemolition']
    
    for r in ws.iter_rows(min_row=2, values_only=True):
        county = str(r[0]).strip().lower() if r[0] else ""
        if county == "skagit":
            raw_city = str(r[1]).strip()
            norm_jur = normalize_name(raw_city)
            year = int(r[2])
            
            sf_perm = clean_num(r[3])
            sf_comp = clean_num(r[4])
            sf_demo = clean_num(r[5])
            
            dup_perm = clean_num(r[6])
            dup_comp = clean_num(r[7])
            dup_demo = clean_num(r[8])
            
            mf34_perm = clean_num(r[9])
            mf34_comp = clean_num(r[10])
            mf34_demo = clean_num(r[11])
            
            mf5_perm = clean_num(r[12])
            mf5_comp = clean_num(r[13])
            mf5_demo = clean_num(r[14])
            
            adu_perm = clean_num(r[15])
            adu_comp = clean_num(r[16])
            adu_demo = clean_num(r[17])
            
            mob_perm = 0
            mob_comp = 0
            mob_demo = 0
            
            tot_perm = sf_perm + dup_perm + mf34_perm + mf5_perm + adu_perm
            tot_comp = sf_comp + dup_comp + mf34_comp + mf5_comp + adu_comp
            tot_demo = sf_demo + dup_demo + mf34_demo + mf5_demo + adu_demo
            net_new = tot_perm - tot_demo
            
            records.append({
                "Jurisdiction_Name": norm_jur,
                "Year": year,
                "Single_Family_Units": sf_perm,
                "Duplex_Units": dup_perm,
                "MultiFamily_3_4_Units": mf34_perm,
                "MultiFamily_5_Plus_Units": mf5_perm,
                "ADU_Units": adu_perm,
                "Mobile_Home_Units": mob_perm,
                "Total_Permitted_Units": tot_perm,
                "Completed_Units": tot_comp,
                "Demolished_Units": tot_demo,
                "Net_New_Units": net_new,
                "Total_Valuation_USD": 0.0,
                "Data_Source": "OFM Postcensal Housing Permits (1990-present)"
            })
    wb.close()
    
    # 5.2 2025 UGA Permits File (Add Bay View Ridge and Swinomish specifically for 2025)
    uga_perm_path = os.path.join(RAW_DIR, "UGA_Dev_Permits_2025.csv")
    with open(uga_perm_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        uga_agg = {}
        for row in reader:
            raw_uga = row.get("Select the Urban Growth Area of the parcel", "").strip()
            if not raw_uga:
                continue
            norm_uga = normalize_name(raw_uga)
            wclass = row.get("Permit Work Class", "").strip().lower()
            val = clean_num(row.get("Permit Valuation", 0))
            
            if norm_uga not in uga_agg:
                uga_agg[norm_uga] = {"sf": 0, "adu": 0, "add": 0, "tot": 0, "val": 0.0}
            
            if "single family" in wclass:
                uga_agg[norm_uga]["sf"] += 1
                uga_agg[norm_uga]["tot"] += 1
            elif "accessory dwelling" in wclass or "adu" in wclass:
                uga_agg[norm_uga]["adu"] += 1
                uga_agg[norm_uga]["tot"] += 1
            else:
                uga_agg[norm_uga]["add"] += 1
            uga_agg[norm_uga]["val"] += val
            
        for u_name, data in uga_agg.items():
            if u_name in ["Bay View Ridge UGA", "Swinomish UGA"]:
                records.append({
                    "Jurisdiction_Name": u_name,
                    "Year": 2025,
                    "Single_Family_Units": data["sf"],
                    "Duplex_Units": 0,
                    "MultiFamily_3_4_Units": 0,
                    "MultiFamily_5_Plus_Units": 0,
                    "ADU_Units": data["adu"],
                    "Mobile_Home_Units": 0,
                    "Total_Permitted_Units": data["tot"],
                    "Completed_Units": data["tot"],
                    "Demolished_Units": 0,
                    "Net_New_Units": data["tot"],
                    "Total_Valuation_USD": round(float(data["val"]), 2),
                    "Data_Source": "Skagit County UGA Building Permits Log (2025)"
                })

    df = pd.DataFrame(records)
    df = pd.merge(df, dim_jur[["Jurisdiction_ID", "Jurisdiction_Name"]], on="Jurisdiction_Name", how="inner")
    df = df.sort_values(by=["Jurisdiction_ID", "Year"]).reset_index(drop=True)
    df["Fact_Housing_Key"] = [f"FHSG-{i+1:05d}" for i in range(len(df))]
    
    cols_order = [
        "Fact_Housing_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name",
        "Single_Family_Units", "Duplex_Units", "MultiFamily_3_4_Units", "MultiFamily_5_Plus_Units",
        "ADU_Units", "Mobile_Home_Units", "Total_Permitted_Units", "Completed_Units",
        "Demolished_Units", "Net_New_Units", "Total_Valuation_USD", "Data_Source"
    ]
    return df[cols_order]

# -----------------------------------------------------------------------------
# 6. BUILD DIM_CAI_EMPLOYMENT_BENCHMARK
# -----------------------------------------------------------------------------
def build_dim_cai_employment_benchmark():
    print("-> Building Dim_CAI_Employment_Benchmark...")
    cai_path = os.path.join(RAW_DIR, "CAI.Total Employment Calc Template DRAFT.2024 0206.xlsx")
    wb = openpyxl.load_workbook(cai_path, data_only=True)
    ws = wb['Total Employment Calculation']
    
    records = []
    # Historical columns D to X (cols 4 to 24) covering 1999 to 2019
    for c in range(4, 25):
        yr = ws.cell(20, c).value
        if yr is not None and isinstance(yr, (int, float)):
            yr = int(yr)
            self_emp = clean_num(ws.cell(21, c).value)
            tot_emp = clean_num(ws.cell(26, c).value)
            cov_emp = (tot_emp - self_emp) if (tot_emp and self_emp) else 0
            ratio = float(ws.cell(31, c).value) if ws.cell(31, c).value else 0.0
            
            records.append({
                "Year": yr,
                "Covered_Employment_QCEW": int(cov_emp),
                "Self_Employment_NES": int(self_emp),
                "Total_Employment_Combined": int(tot_emp),
                "Self_Employment_Ratio": round(ratio, 5),
                "Benchmark_10Yr_Average_Ratio": 1.15458,
                "Data_Source": "CAI Total Employment Calc Template / BLS QCEW & Census NES"
            })
    wb.close()
    
    # Add 2022 baseline row from CAI cells D15, D16, D41
    records.append({
        "Year": 2022,
        "Covered_Employment_QCEW": 51597,
        "Self_Employment_NES": 7976, # 59,573 total - 51,597 covered
        "Total_Employment_Combined": 59573,
        "Self_Employment_Ratio": 1.15458,
        "Benchmark_10Yr_Average_Ratio": 1.15458,
        "Data_Source": "CAI Total Employment Calc Template / 2022 Adopted Baseline"
    })
    
    df = pd.DataFrame(records).sort_values("Year").reset_index(drop=True)
    df["Benchmark_Key"] = [f"CAI-EMP-{r['Year']}" for _, r in df.iterrows()]
    cols_order = [
        "Benchmark_Key", "Year", "Covered_Employment_QCEW", "Self_Employment_NES",
        "Total_Employment_Combined", "Self_Employment_Ratio", "Benchmark_10Yr_Average_Ratio",
        "Data_Source"
    ]
    return df[cols_order]

# -----------------------------------------------------------------------------
# 7. BUILD FACT_EMPLOYMENT
# -----------------------------------------------------------------------------
def build_fact_employment():
    print("-> Building Fact_Employment...")
    records = []
    
    # 7.1 2025 QCEW Revised
    qcew_path = os.path.join(RAW_DIR, "2025-QCEW-annual-averages-revised(Skagit County) (1).csv")
    with open(qcew_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for _ in range(4):
            next(reader, None)
        h1 = next(reader) # line 5
        h2 = next(reader) # line 6
        
        for row in reader:
            if not row or len(row) < 3:
                continue
            n2 = row[0].strip()
            n3 = row[1].strip()
            title = row[2].strip()
            if not title or title.lower().startswith("source"):
                continue
            firms = clean_num(row[3]) if len(row) > 3 else 0
            
            # Jan to Dec
            monthly = []
            for m_idx in range(4, 16):
                monthly.append(clean_num(row[m_idx]) if m_idx < len(row) else 0)
                
            # Annual Average
            avg_emp = clean_num(row[17]) if len(row) > 17 else (sum(monthly)/12 if monthly else 0)
            avg_wage = clean_num(row[18]) if len(row) > 18 else 0
            est_tot_emp = int(round(avg_emp * 1.15458)) if avg_emp > 0 else 0
            
            records.append({
                "Year": 2025,
                "NAICS_2Digit_Code": n2,
                "NAICS_3Digit_Code": n3,
                "Industry_Subsector_Title": title,
                "Average_Establishments": firms,
                "Annual_Average_Employment": int(avg_emp),
                "Estimated_Total_Employment": est_tot_emp,
                "CAI_Self_Employment_Multiplier": 1.15458,
                "Average_Annual_Wage_USD": int(avg_wage),
                "Jan_Employment": int(monthly[0]),
                "Feb_Employment": int(monthly[1]),
                "Mar_Employment": int(monthly[2]),
                "Apr_Employment": int(monthly[3]),
                "May_Employment": int(monthly[4]),
                "Jun_Employment": int(monthly[5]),
                "Jul_Employment": int(monthly[6]),
                "Aug_Employment": int(monthly[7]),
                "Sep_Employment": int(monthly[8]),
                "Oct_Employment": int(monthly[9]),
                "Nov_Employment": int(monthly[10]),
                "Dec_Employment": int(monthly[11]),
                "Data_Status": "2025 Official Revised Averages"
            })
            
    # 7.2 2026 Q1 QCEW Preliminary
    q1_path = os.path.join(RAW_DIR, "2026Q1-QCEW-preliminary(Skagit County).csv")
    if os.path.exists(q1_path):
        with open(q1_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for _ in range(5):
                next(reader, None)
            for row in reader:
                if not row or len(row) < 3:
                    continue
                n2 = row[0].strip()
                n3 = row[1].strip()
                title = row[2].strip()
                if not title or title.lower().startswith("source"):
                    continue
                firms = clean_num(row[3]) if len(row) > 3 else 0
                jan = clean_num(row[4]) if len(row) > 4 else 0
                feb = clean_num(row[5]) if len(row) > 5 else 0
                mar = clean_num(row[6]) if len(row) > 6 else 0
                avg_emp = clean_num(row[8]) if len(row) > 8 else 0
                avg_qtr_wage = clean_num(row[9]) if len(row) > 9 else 0
                annualized_wage = int(avg_qtr_wage * 4)
                est_tot_emp = int(round(avg_emp * 1.15458)) if avg_emp > 0 else 0
                
                records.append({
                    "Year": 2026,
                    "NAICS_2Digit_Code": n2,
                    "NAICS_3Digit_Code": n3,
                    "Industry_Subsector_Title": title,
                    "Average_Establishments": firms,
                    "Annual_Average_Employment": int(avg_emp),
                    "Estimated_Total_Employment": est_tot_emp,
                    "CAI_Self_Employment_Multiplier": 1.15458,
                    "Average_Annual_Wage_USD": annualized_wage,
                    "Jan_Employment": int(jan),
                    "Feb_Employment": int(feb),
                    "Mar_Employment": int(mar),
                    "Apr_Employment": 0,
                    "May_Employment": 0,
                    "Jun_Employment": 0,
                    "Jul_Employment": 0,
                    "Aug_Employment": 0,
                    "Sep_Employment": 0,
                    "Oct_Employment": 0,
                    "Nov_Employment": 0,
                    "Dec_Employment": 0,
                    "Data_Status": "2026 Q1 Preliminary"
                })

    df = pd.DataFrame(records)
    df["Fact_Employment_Key"] = [f"FEMP-{i+1:04d}" for i in range(len(df))]
    cols_order = [
        "Fact_Employment_Key", "Year", "NAICS_2Digit_Code", "NAICS_3Digit_Code", "Industry_Subsector_Title",
        "Average_Establishments", "Annual_Average_Employment", "Estimated_Total_Employment",
        "CAI_Self_Employment_Multiplier", "Average_Annual_Wage_USD",
        "Jan_Employment", "Feb_Employment", "Mar_Employment", "Apr_Employment",
        "May_Employment", "Jun_Employment", "Jul_Employment", "Aug_Employment",
        "Sep_Employment", "Oct_Employment", "Nov_Employment", "Dec_Employment",
        "Data_Status"
    ]
    return df[cols_order]

# -----------------------------------------------------------------------------
# 8. BUILD FACT_HOUSING_AMI
# -----------------------------------------------------------------------------
def build_fact_housing_ami(dim_jur):
    print("-> Building Fact_Housing_AMI...")
    path = os.path.join("data/templates", "Template_Housing_AMI_Master.xlsx")
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb['Housing_AMI_Master']
    
    records = []
    for r in ws.iter_rows(min_row=9, max_row=28, values_only=True):
        if not r or not r[1]:
            continue
        rec_id = r[1]
        yr = r[2]
        jur = r[3]
        stype = r[4]
        ami_0_30 = clean_num(r[5])
        ami_31_50 = clean_num(r[6])
        ami_51_80 = clean_num(r[7])
        ami_81_100 = clean_num(r[8])
        ami_101_120 = clean_num(r[9])
        ami_120_plus = clean_num(r[10])
        tot_units = clean_num(r[11])
        status = r[12]
        
        records.append({
            "Fact_AMI_Key": rec_id,
            "Year": yr,
            "Jurisdiction_Name": jur,
            "Structure_Type": stype,
            "AMI_0_to_30_Pct_Units": ami_0_30,
            "AMI_31_to_50_Pct_Units": ami_31_50,
            "AMI_51_to_80_Pct_Units": ami_51_80,
            "AMI_81_to_100_Pct_Units": ami_81_100,
            "AMI_101_to_120_Pct_Units": ami_101_120,
            "AMI_Greater_120_Pct_Units": ami_120_plus,
            "Total_AMI_Units": tot_units,
            "Reconciliation_Status": status
        })
    wb.close()
    
    df = pd.DataFrame(records)
    df = pd.merge(df, dim_jur[["Jurisdiction_ID", "Jurisdiction_Name"]], on="Jurisdiction_Name", how="inner")
    cols_order = [
        "Fact_AMI_Key", "Jurisdiction_ID", "Year", "Jurisdiction_Name", "Structure_Type",
        "AMI_0_to_30_Pct_Units", "AMI_31_to_50_Pct_Units", "AMI_51_to_80_Pct_Units",
        "AMI_81_to_100_Pct_Units", "AMI_101_to_120_Pct_Units", "AMI_Greater_120_Pct_Units",
        "Total_AMI_Units", "Reconciliation_Status"
    ]
    return df[cols_order]

# -----------------------------------------------------------------------------
# MAIN ETL EXECUTION
# -----------------------------------------------------------------------------
def run_etl():
    print("="*70)
    print("EXECUTING ETL PIPELINE: SCOG ANNUAL GROWTH MONITORING STAR SCHEMA")
    print("="*70)
    
    # 1. Dimensions
    dim_jur = build_dim_jurisdiction()
    dim_cal = build_dim_calendaryear()
    dim_gma = build_dim_gma_2045_target(dim_jur)
    dim_cai = build_dim_cai_employment_benchmark()
    
    # 2. Facts
    fact_pop = build_fact_population(dim_jur)
    fact_hsg = build_fact_housing_permits(dim_jur)
    fact_emp = build_fact_employment()
    fact_ami = build_fact_housing_ami(dim_jur)
    
    # Save CSVs
    tables = {
        "Dim_Jurisdiction": dim_jur,
        "Dim_CalendarYear": dim_cal,
        "Dim_GMA_2045_Target": dim_gma,
        "Dim_CAI_Employment_Benchmark": dim_cai,
        "Fact_Population": fact_pop,
        "Fact_HousingPermits": fact_hsg,
        "Fact_Employment": fact_emp,
        "Fact_Housing_AMI": fact_ami
    }
    
    print("\n-> Saving Processed CSV Tables:")
    for name, df in tables.items():
        csv_path = os.path.join(PROCESSED_DIR, f"{name}.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"   [CSV] {name:30} | Rows: {len(df):6d} | Cols: {len(df.columns):2d} -> {csv_path}")

    # Save to Multi-tab Master Excel Model for Power BI
    excel_path = os.path.join(PROCESSED_DIR, "SCOG_Star_Schema_Data_Model.xlsx")
    print(f"\n-> Building Master Excel Workbook for Power BI Desktop: {excel_path}...")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name, index=False)
            
    # Format openpyxl workbook with tables
    wb = openpyxl.load_workbook(excel_path)
    for name in tables.keys():
        ws = wb[name]
        ws.views.sheetView[0].showGridLines = True
        # auto-fit width
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(c.value or '')) for c in col)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
    wb.save(excel_path)
    print("   [XLSX] Complete Multi-Tab Model Saved Successfully!")

    print("\n" + "="*70)
    print("ETL PIPELINE COMPLETE: STAR SCHEMA READY FOR POWER BI INGESTION")
    print("="*70)

if __name__ == "__main__":
    run_etl()
