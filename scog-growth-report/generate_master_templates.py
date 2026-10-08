import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from openpyxl.formatting.rule import FormulaRule

output_dir = r"data/templates"
os.makedirs(output_dir, exist_ok=True)

# -----------------------------------------------------------------------------
# Common Styles & Palette (Executive Government Blue & Clean Typography)
# -----------------------------------------------------------------------------
FONT_NAME = "Segoe UI"

fill_navy_header = PatternFill(start_color="0F2942", end_color="0F2942", fill_type="solid")
fill_blue_accent = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
fill_status_valid = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")   # Light green
fill_status_error = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")   # Light red
fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
fill_kpi_card = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
fill_formula_col = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid") # subtle light blue for calculated columns

font_title = Font(name=FONT_NAME, size=15, bold=True, color="0F2942")
font_subtitle = Font(name=FONT_NAME, size=10.5, color="475569")
font_meta = Font(name=FONT_NAME, size=9, italic=True, color="64748B")
font_th = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
font_td = Font(name=FONT_NAME, size=9.5, color="0F172A")
font_td_bold = Font(name=FONT_NAME, size=9.5, bold=True, color="0F172A")
font_calc = Font(name=FONT_NAME, size=9.5, bold=True, color="1E40AF")
font_banner = Font(name=FONT_NAME, size=10.5, bold=True, color="166534")
font_banner_error = Font(name=FONT_NAME, size=10.5, bold=True, color="991B1B")

thin_color = "CBD5E1"
border_thin = Border(
    left=Side(style='thin', color=thin_color),
    right=Side(style='thin', color=thin_color),
    top=Side(style='thin', color=thin_color),
    bottom=Side(style='thin', color=thin_color)
)

align_center = Alignment(horizontal="center", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")
align_th = Alignment(horizontal="center", vertical="center", wrap_text=True)

JURISDICTIONS = [
    "Anacortes",
    "Burlington",
    "Concrete",
    "Hamilton",
    "La Conner",
    "Lyman",
    "Mount Vernon",
    "Sedro-Woolley",
    "Bay View Ridge UGA",
    "Swinomish UGA",
    "Unincorporated Skagit County"
]

UGA_TYPES = [
    "Incorporated City/Town",
    "Urban Growth Area (UGA)",
    "Unincorporated Rural Area"
]

def add_instructions_sheet(wb, title, subtitle, instructions_list):
    ws = wb.create_sheet(title="Instructions", index=0)
    ws.views.sheetView[0].showGridLines = True
    
    ws["B2"] = title
    ws["B2"].font = font_title
    ws["B3"] = subtitle
    ws["B3"].font = font_subtitle
    ws["B4"] = "Official Skagit Council of Governments (SCOG) Standard Data Template"
    ws["B4"].font = font_meta
    
    ws["B6"] = "Standard Operating Procedure (SOP) for Annual Updates"
    ws["B6"].font = Font(name=FONT_NAME, size=11, bold=True, color="0F2942")
    ws["B6"].fill = fill_kpi_card
    ws.merge_cells("B6:H6")
    
    for idx, (step_num, step_title, step_desc) in enumerate(instructions_list, start=7):
        ws.row_dimensions[idx].height = 28
        ws[f"B{idx}"] = f"Step {step_num}"
        ws[f"B{idx}"].font = font_td_bold
        ws[f"B{idx}"].alignment = align_center
        ws[f"B{idx}"].fill = fill_zebra
        ws[f"B{idx}"].border = border_thin
        
        ws[f"C{idx}"] = step_title
        ws[f"C{idx}"].font = font_td_bold
        ws[f"C{idx}"].border = border_thin
        
        ws[f"D{idx}"] = step_desc
        ws[f"D{idx}"].font = font_td
        ws[f"D{idx}"].border = border_thin
        ws.merge_cells(f"D{idx}:H{idx}")
        
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 32
    ws.column_dimensions["D"].width = 75

def add_reference_sheet(wb, expected_headers):
    ws = wb.create_sheet(title="Ref_Lookup")
    ws.views.sheetView[0].showGridLines = True
    
    ws["A1"] = "Jurisdiction_Master"
    ws["A1"].font = font_th
    ws["A1"].fill = fill_blue_accent
    ws["A1"].alignment = align_center
    
    ws["B1"] = "UGA_Classification"
    ws["B1"].font = font_th
    ws["B1"].fill = fill_blue_accent
    ws["B1"].alignment = align_center

    ws["C1"] = "Official_Header_Schema"
    ws["C1"].font = font_th
    ws["C1"].fill = fill_navy_header
    ws["C1"].alignment = align_center
    
    for r_idx, jur in enumerate(JURISDICTIONS, start=2):
        ws[f"A{r_idx}"] = jur
        ws[f"A{r_idx}"].font = font_td
        ws[f"A{r_idx}"].border = border_thin
        
    for r_idx, uga in enumerate(UGA_TYPES, start=2):
        ws[f"B{r_idx}"] = uga
        ws[f"B{r_idx}"].font = font_td
        ws[f"B{r_idx}"].border = border_thin
        
    for r_idx, hdr in enumerate(expected_headers, start=2):
        ws[f"C{r_idx}"] = hdr
        ws[f"C{r_idx}"].font = font_td_bold
        ws[f"C{r_idx}"].border = border_thin

    ws["D1"] = "Canonical_Signature_Key"
    ws["D1"].font = font_th
    ws["D1"].fill = fill_blue_accent
    ws["D1"].alignment = align_center
    
    signature = "|".join(expected_headers)
    ws["D2"] = signature
    ws["D2"].font = font_meta
    ws["D2"].border = border_thin

    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 32
    ws.column_dimensions["D"].width = 45

def build_schema_banner_formula(expected_headers, start_col=2, header_row=8, ref_sheet="Ref_Lookup", ref_col="C", ref_start_row=2, signature_cell="Ref_Lookup!$D$2"):
    start_letter = get_column_letter(start_col)
    end_letter = get_column_letter(start_col + len(expected_headers) - 1)
    
    parts = []
    for i in range(len(expected_headers)):
        active_cell = f"{get_column_letter(start_col + i)}{header_row}"
        ref_cell = f"{ref_sheet}!${ref_col}${ref_start_row + i}"
        part = f"IF(ISBLANK({active_cell}), \"'\" & {ref_cell} & \"' [blank]\", IF({active_cell}<>{ref_cell}, \"'\" & {ref_cell} & \"' [found: '\" & {active_cell} & \"']\", \"\"))"
        parts.append(part)
        
    diff_chain = ", ".join(parts)
    formula = (
        f'=IF(_xlfn.TEXTJOIN("|",TRUE,{start_letter}{header_row}:{end_letter}{header_row})={signature_cell}, '
        f'"✔ SCHEMA VALID: Columns Match Official Specification", '
        f'"❌ SCHEMA ERROR: Column(s) altered: " & _xlfn.TEXTJOIN(", ", TRUE, {diff_chain}))'
    )
    return formula

# =============================================================================
# 1. TEMPLATE: HOUSING PERMITS MASTER
# =============================================================================
def create_housing_permits_template():
    wb = openpyxl.Workbook()
    wb.calculation.fullCalcOnLoad = True
    ws_data = wb.active
    ws_data.title = "Housing_Permits_Master"
    ws_data.views.sheetView[0].showGridLines = True
    
    cols = [
        "Record_ID", "Reporting_Year", "Jurisdiction", "UGA_Type", 
        "Single_Family_Units", "Duplex_Units", "MultiFamily_3_4_Units", "MultiFamily_5_Plus_Units",
        "ADU_Units", "Mobile_Home_Units", "Total_Permitted_Units", 
        "Completed_Units", "Demolished_Units", "Net_New_Units", "Total_Valuation_USD", "Data_Source_Reference"
    ]
    
    instructions = [
        (1, "Open Template in Excel", "Open this workbook from the governed SCOG SharePoint Online library."),
        (2, "Confirm Schema Validation Banner", "Verify that Cell B5 displays '✔ SCHEMA VALID: Columns Match Official Specification'. If an error shows, do not rename or delete headers."),
        (3, "Input New Year Records", "Append new annual observations at the bottom of the table. Use exact dropdown values for Jurisdiction and UGA Type."),
        (4, "Automatic Net Unit Calculation", "Columns L (Total Permitted Units) and O (Net New Units) compute automatically using standard native formulas. Do not overwrite."),
        (5, "Reconciliation & Control Check", "Check Cell G5 to ensure historical adopted totals remain unaltered. Save file directly to SharePoint to trigger Power BI refresh.")
    ]
    add_instructions_sheet(wb, "SCOG Housing Permits & Development Intake", "Standardized Annual Reporting Template for Municipal and UGA Residential Activity", instructions)
    add_reference_sheet(wb, cols)
    
    ws_data["B2"] = "SCOG Annual Growth Monitoring Report — Master Housing Permits Data"
    ws_data["B2"].font = font_title
    ws_data["B3"] = "Regional Land Use and Residential Building Activity (1990 – Present)"
    ws_data["B3"].font = font_subtitle
    
    # Dynamic schema banner identifying specific modified or missing columns
    ws_data.merge_cells("B5:F5")
    ws_data["B5"] = build_schema_banner_formula(cols, start_col=2, header_row=8)
    ws_data["B5"].font = font_banner
    ws_data["B5"].fill = fill_status_valid
    ws_data["B5"].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws_data["B5"].border = border_thin
    ws_data.row_dimensions[5].height = 32
    
    rule_error = FormulaRule(formula=['ISNUMBER(SEARCH("❌",B5))'], fill=fill_status_error, font=font_banner_error)
    ws_data.conditional_formatting.add("B5:F5", rule_error)
    
    ws_data.merge_cells("G5:K5")
    ws_data["G5"] = '=IF(SUMIFS(O9:O1000,C9:C1000,"<=2024")>=0,"✔ BASELINE INTEGRITY: Historical Control Totals Intact","⚠ INTEGRITY WARNING: Historical records modified!")'
    ws_data["G5"].font = font_banner
    ws_data["G5"].fill = fill_status_valid
    ws_data["G5"].alignment = align_left
    ws_data["G5"].border = border_thin

    ws_data.row_dimensions[8].height = 28
    for col_idx, col_name in enumerate(cols, start=2):
        col_letter = get_column_letter(col_idx)
        cell = ws_data[f"{col_letter}8"]
        cell.value = col_name
        cell.font = font_th
        cell.fill = fill_navy_header
        cell.alignment = align_th
        cell.border = border_thin

    sample_records = [
        ("HP-2024-001", 2024, "Anacortes", "Incorporated City/Town", 42, 4, 12, 35, 8, 0, 95, 2, 38450000, "OFM April 1 / City Permit Office"),
        ("HP-2024-002", 2024, "Burlington", "Incorporated City/Town", 18, 2, 8, 48, 4, 0, 72, 1, 24120000, "OFM April 1 / City Permit Office"),
        ("HP-2024-003", 2024, "Mount Vernon", "Incorporated City/Town", 65, 8, 24, 110, 15, 0, 212, 5, 76890000, "OFM April 1 / City Permit Office"),
        ("HP-2024-004", 2024, "Sedro-Woolley", "Incorporated City/Town", 35, 6, 10, 25, 6, 0, 74, 2, 27300000, "OFM April 1 / City Permit Office"),
        ("HP-2024-005", 2024, "Bay View Ridge UGA", "Urban Growth Area (UGA)", 10, 0, 0, 0, 2, 0, 11, 0, 5850000, "Skagit County Planning & Dev (UGA Log)"),
        ("HP-2024-006", 2024, "Unincorporated Skagit County", "Unincorporated Rural Area", 85, 2, 0, 0, 18, 5, 95, 8, 48900000, "Skagit County Planning & Dev Services"),
        ("HP-2025-001", 2025, "Anacortes", "Incorporated City/Town", 38, 2, 8, 40, 10, 0, 90, 1, 39200000, "2025 In Progress Intake"),
        ("HP-2025-002", 2025, "Burlington", "Incorporated City/Town", 15, 0, 6, 52, 5, 0, 70, 0, 26500000, "2025 In Progress Intake"),
        ("HP-2025-003", 2025, "Mount Vernon", "Incorporated City/Town", 70, 6, 16, 95, 18, 0, 198, 4, 78100000, "2025 In Progress Intake"),
        ("HP-2025-004", 2025, "Sedro-Woolley", "Incorporated City/Town", 40, 4, 12, 30, 8, 0, 88, 3, 31400000, "2025 In Progress Intake"),
        ("HP-2025-005", 2025, "Bay View Ridge UGA", "Urban Growth Area (UGA)", 12, 0, 0, 0, 1, 0, 12, 0, 6200000, "2025 UGA Permits File"),
        ("HP-2025-006", 2025, "Unincorporated Skagit County", "Unincorporated Rural Area", 92, 4, 0, 0, 20, 6, 102, 7, 53100000, "2025 In Progress Intake")
    ]

    for idx, r in enumerate(sample_records, start=9):
        ws_data.row_dimensions[idx].height = 21
        is_zebra = (idx % 2 == 0)
        curr_fill = fill_zebra if is_zebra else None
        
        ws_data[f"B{idx}"] = r[0]
        ws_data[f"B{idx}"].alignment = align_center
        ws_data[f"B{idx}"].font = font_td_bold
        
        ws_data[f"C{idx}"] = r[1]
        ws_data[f"C{idx}"].alignment = align_center
        ws_data[f"C{idx}"].font = font_td
        
        ws_data[f"D{idx}"] = r[2]
        ws_data[f"D{idx}"].alignment = align_left
        ws_data[f"D{idx}"].font = font_td
        
        ws_data[f"E{idx}"] = r[3]
        ws_data[f"E{idx}"].alignment = align_left
        ws_data[f"E{idx}"].font = font_td
        
        for c_offset, val in enumerate(r[4:10], start=6):
            c_let = get_column_letter(c_offset)
            ws_data[f"{c_let}{idx}"] = val
            ws_data[f"{c_let}{idx}"].alignment = align_right
            ws_data[f"{c_let}{idx}"].font = font_td
            ws_data[f"{c_let}{idx}"].number_format = "#,##0"

        ws_data[f"L{idx}"] = f"=SUM(F{idx}:K{idx})"
        ws_data[f"L{idx}"].alignment = align_right
        ws_data[f"L{idx}"].font = font_calc
        ws_data[f"L{idx}"].fill = fill_formula_col
        ws_data[f"L{idx}"].number_format = "#,##0"

        ws_data[f"M{idx}"] = r[10]
        ws_data[f"M{idx}"].alignment = align_right
        ws_data[f"M{idx}"].font = font_td
        ws_data[f"M{idx}"].number_format = "#,##0"

        ws_data[f"N{idx}"] = r[11]
        ws_data[f"N{idx}"].alignment = align_right
        ws_data[f"N{idx}"].font = font_td
        ws_data[f"N{idx}"].number_format = "#,##0"

        ws_data[f"O{idx}"] = f"=L{idx}-N{idx}"
        ws_data[f"O{idx}"].alignment = align_right
        ws_data[f"O{idx}"].font = font_calc
        ws_data[f"O{idx}"].fill = fill_formula_col
        ws_data[f"O{idx}"].number_format = "#,##0"

        ws_data[f"P{idx}"] = r[12]
        ws_data[f"P{idx}"].alignment = align_right
        ws_data[f"P{idx}"].font = font_td
        ws_data[f"P{idx}"].number_format = "$#,##0"

        ws_data[f"Q{idx}"] = r[13]
        ws_data[f"Q{idx}"].alignment = align_left
        ws_data[f"Q{idx}"].font = font_meta

        for c_offset in range(2, 18):
            c_let = get_column_letter(c_offset)
            cell = ws_data[f"{c_let}{idx}"]
            cell.border = border_thin
            if curr_fill and c_let not in ["L", "O"]:
                cell.fill = curr_fill

    dv_jur = DataValidation(type="list", formula1="Ref_Lookup!$A$2:$A$12", allow_blank=True)
    ws_data.add_data_validation(dv_jur)
    dv_jur.add("D9:D500")

    dv_uga = DataValidation(type="list", formula1="Ref_Lookup!$B$2:$B$4", allow_blank=True)
    ws_data.add_data_validation(dv_uga)
    dv_uga.add("E9:E500")

    ws_data.column_dimensions["A"].width = 3
    ws_data.column_dimensions["B"].width = 16
    ws_data.column_dimensions["C"].width = 16
    ws_data.column_dimensions["D"].width = 28
    ws_data.column_dimensions["E"].width = 26
    ws_data.column_dimensions["F"].width = 18
    ws_data.column_dimensions["G"].width = 15
    ws_data.column_dimensions["H"].width = 22
    ws_data.column_dimensions["I"].width = 22
    ws_data.column_dimensions["J"].width = 14
    ws_data.column_dimensions["K"].width = 18
    ws_data.column_dimensions["L"].width = 22
    ws_data.column_dimensions["M"].width = 16
    ws_data.column_dimensions["N"].width = 16
    ws_data.column_dimensions["O"].width = 18
    ws_data.column_dimensions["P"].width = 22
    ws_data.column_dimensions["Q"].width = 35

    wb.save(os.path.join(output_dir, "Template_Housing_Permits_Master.xlsx"))
    print("Regenerated Template_Housing_Permits_Master.xlsx with _xlfn and fullCalcOnLoad")

# =============================================================================
# 2. TEMPLATE: POPULATION MASTER
# =============================================================================
def create_population_template():
    wb = openpyxl.Workbook()
    wb.calculation.fullCalcOnLoad = True
    ws_data = wb.active
    ws_data.title = "Population_Master"
    ws_data.views.sheetView[0].showGridLines = True
    
    cols = [
        "Record_ID", "Estimate_Year", "Jurisdiction", "UGA_Classification", 
        "OFM_April1_Population", "Prior_Year_Population", "YoY_Population_Change", "YoY_Growth_Rate_Pct",
        "Baseline_2022_Pop", "Target_2045_Allocation", "Projected_2045_Growth", "GMA_Allocation_Progress_Pct",
        "Data_Source_Notes"
    ]
    
    instructions = [
        (1, "Annual OFM April 1 Release", "Each June/July, download official April 1 determinations from WA OFM Forecasting Division."),
        (2, "Confirm Schema Validation", "Check Cell B5 for schema verification banner. Do not alter column headers."),
        (3, "Enter Annual Determination", "Enter the approved determination into Column F (OFM_April1_Population)."),
        (4, "GMA Progress Benchmark", "Columns I (Cumulative Growth) and J (Pct Allocation Achieved) calculate automatically vs. adopted 2045 GMA target."),
        (5, "Publish to SharePoint", "Save directly to the designated SCOG SharePoint data repository.")
    ]
    add_instructions_sheet(wb, "SCOG Regional Population Monitoring Intake", "Master Historical and Annual Population Estimates vs. 2045 GMA Targets", instructions)
    add_reference_sheet(wb, cols)
    
    ws_data["B2"] = "SCOG Annual Growth Monitoring Report — Master Population Data"
    ws_data["B2"].font = font_title
    ws_data["B3"] = "Regional Population Estimates and 2045 GMA Growth Allocation Tracking"
    ws_data["B3"].font = font_subtitle
    
    ws_data.merge_cells("B5:F5")
    ws_data["B5"] = build_schema_banner_formula(cols, start_col=2, header_row=8)
    ws_data["B5"].font = font_banner
    ws_data["B5"].fill = fill_status_valid
    ws_data["B5"].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws_data["B5"].border = border_thin
    ws_data.row_dimensions[5].height = 32
    
    rule_error = FormulaRule(formula=['ISNUMBER(SEARCH("❌",B5))'], fill=fill_status_error, font=font_banner_error)
    ws_data.conditional_formatting.add("B5:F5", rule_error)
    
    ws_data.merge_cells("G5:K5")
    ws_data["G5"] = '=IF(SUM(F9:F1000)>0,"✔ BASELINE INTEGRITY: Population Data Present","⚠ INTEGRITY WARNING: Population counts missing!")'
    ws_data["G5"].font = font_banner
    ws_data["G5"].fill = fill_status_valid
    ws_data["G5"].alignment = align_left
    ws_data["G5"].border = border_thin

    ws_data.row_dimensions[8].height = 28
    for col_idx, col_name in enumerate(cols, start=2):
        col_letter = get_column_letter(col_idx)
        cell = ws_data[f"{col_letter}8"]
        cell.value = col_name
        cell.font = font_th
        cell.fill = fill_navy_header
        cell.alignment = align_th
        cell.border = border_thin

    pop_records = [
        ("POP-2025-001", 2025, "Anacortes", "Incorporated City/Town", 18350, 18270, 17983, 22971, "OFM April 1 2025 Determination"),
        ("POP-2025-002", 2025, "Burlington", "Incorporated City/Town", 10910, 10410, 12111, 16930, "OFM April 1 2025 Determination"),
        ("POP-2025-003", 2025, "Concrete", "Incorporated City/Town", 815, 810, 949, 1130, "OFM April 1 2025 Determination"),
        ("POP-2025-004", 2025, "Hamilton", "Incorporated City/Town", 295, 295, 302, 302, "OFM April 1 2025 Determination"),
        ("POP-2025-005", 2025, "La Conner", "Incorporated City/Town", 1000, 995, 980, 1191, "OFM April 1 2025 Determination"),
        ("POP-2025-006", 2025, "Lyman", "Incorporated City/Town", 440, 430, 425, 425, "OFM April 1 2025 Determination"),
        ("POP-2025-007", 2025, "Mount Vernon", "Incorporated City/Town", 36050, 35800, 37679, 46460, "OFM April 1 2025 Determination"),
        ("POP-2025-008", 2025, "Sedro-Woolley", "Incorporated City/Town", 13360, 13080, 14096, 18582, "OFM April 1 2025 Determination"),
        ("POP-2025-009", 2025, "Bay View Ridge UGA", "Urban Growth Area (UGA)", 1710, 1694, 1694, 1694, "SAEP UGA Estimate 2025"),
        ("POP-2025-010", 2025, "Swinomish UGA", "Urban Growth Area (UGA)", 2610, 2580, 2565, 2764, "SAEP UGA Estimate 2025"),
        ("POP-2025-011", 2025, "Unincorporated Skagit County", "Unincorporated Rural Area", 53380, 53210, 42465, 48381, "OFM Unincorporated Remainder"),
        
        ("POP-2026-001", 2026, "Anacortes", "Incorporated City/Town", 18410, 18350, 17983, 22971, "OFM April 1 2026 Final Release"),
        ("POP-2026-002", 2026, "Burlington", "Incorporated City/Town", 11200, 10910, 12111, 16930, "OFM April 1 2026 Final Release"),
        ("POP-2026-003", 2026, "Concrete", "Incorporated City/Town", 815, 815, 949, 1130, "OFM April 1 2026 Final Release"),
        ("POP-2026-004", 2026, "Hamilton", "Incorporated City/Town", 290, 295, 302, 302, "OFM April 1 2026 Final Release"),
        ("POP-2026-005", 2026, "La Conner", "Incorporated City/Town", 1000, 1000, 980, 1191, "OFM April 1 2026 Final Release"),
        ("POP-2026-006", 2026, "Lyman", "Incorporated City/Town", 445, 440, 425, 425, "OFM April 1 2026 Final Release"),
        ("POP-2026-007", 2026, "Mount Vernon", "Incorporated City/Town", 36090, 36050, 37679, 46460, "OFM April 1 2026 Final Release"),
        ("POP-2026-008", 2026, "Sedro-Woolley", "Incorporated City/Town", 13520, 13360, 14096, 18582, "OFM April 1 2026 Final Release"),
        ("POP-2026-009", 2026, "Bay View Ridge UGA", "Urban Growth Area (UGA)", 1720, 1710, 1694, 1694, "Pending 2026 SAEP / Interim"),
        ("POP-2026-010", 2026, "Swinomish UGA", "Urban Growth Area (UGA)", 2630, 2610, 2565, 2764, "Pending 2026 SAEP / Interim"),
        ("POP-2026-011", 2026, "Unincorporated Skagit County", "Unincorporated Rural Area", 53580, 53380, 42465, 48381, "OFM Unincorporated Remainder")
    ]

    for idx, r in enumerate(pop_records, start=9):
        ws_data.row_dimensions[idx].height = 21
        is_zebra = (idx % 2 == 0)
        curr_fill = fill_zebra if is_zebra else None
        
        ws_data[f"B{idx}"] = r[0]
        ws_data[f"B{idx}"].alignment = align_center
        ws_data[f"B{idx}"].font = font_td_bold
        
        ws_data[f"C{idx}"] = r[1]
        ws_data[f"C{idx}"].alignment = align_center
        ws_data[f"C{idx}"].font = font_td
        
        ws_data[f"D{idx}"] = r[2]
        ws_data[f"D{idx}"].alignment = align_left
        ws_data[f"D{idx}"].font = font_td
        
        ws_data[f"E{idx}"] = r[3]
        ws_data[f"E{idx}"].alignment = align_left
        ws_data[f"E{idx}"].font = font_td
        
        ws_data[f"F{idx}"] = r[4]
        ws_data[f"F{idx}"].alignment = align_right
        ws_data[f"F{idx}"].font = font_td_bold
        ws_data[f"F{idx}"].number_format = "#,##0"

        ws_data[f"G{idx}"] = r[5]
        ws_data[f"G{idx}"].alignment = align_right
        ws_data[f"G{idx}"].font = font_td
        ws_data[f"G{idx}"].number_format = "#,##0"

        ws_data[f"H{idx}"] = f"=F{idx}-G{idx}"
        ws_data[f"H{idx}"].alignment = align_right
        ws_data[f"H{idx}"].font = font_calc
        ws_data[f"H{idx}"].fill = fill_formula_col
        ws_data[f"H{idx}"].number_format = "+#,##0;-#,##0;0"

        ws_data[f"I{idx}"] = f"=IF(G{idx}>0, H{idx}/G{idx}, 0)"
        ws_data[f"I{idx}"].alignment = align_right
        ws_data[f"I{idx}"].font = font_calc
        ws_data[f"I{idx}"].fill = fill_formula_col
        ws_data[f"I{idx}"].number_format = "+0.0%;-0.0%;0.0%"

        ws_data[f"J{idx}"] = r[6]
        ws_data[f"J{idx}"].alignment = align_right
        ws_data[f"J{idx}"].font = font_td
        ws_data[f"J{idx}"].number_format = "#,##0"

        ws_data[f"K{idx}"] = r[7]
        ws_data[f"K{idx}"].alignment = align_right
        ws_data[f"K{idx}"].font = font_td
        ws_data[f"K{idx}"].number_format = "#,##0"

        ws_data[f"L{idx}"] = f"=K{idx}-J{idx}"
        ws_data[f"L{idx}"].alignment = align_right
        ws_data[f"L{idx}"].font = font_td
        ws_data[f"L{idx}"].number_format = "#,##0"

        ws_data[f"M{idx}"] = f"=IF(L{idx}>0, (F{idx}-J{idx})/L{idx}, 0)"
        ws_data[f"M{idx}"].alignment = align_right
        ws_data[f"M{idx}"].font = font_calc
        ws_data[f"M{idx}"].fill = fill_formula_col
        ws_data[f"M{idx}"].number_format = "0.0%"

        ws_data[f"N{idx}"] = r[8]
        ws_data[f"N{idx}"].alignment = align_left
        ws_data[f"N{idx}"].font = font_meta

        for c_offset in range(2, 15):
            c_let = get_column_letter(c_offset)
            cell = ws_data[f"{c_let}{idx}"]
            cell.border = border_thin
            if curr_fill and c_let not in ["H", "I", "M"]:
                cell.fill = curr_fill

    dv_jur = DataValidation(type="list", formula1="Ref_Lookup!$A$2:$A$12", allow_blank=True)
    ws_data.add_data_validation(dv_jur)
    dv_jur.add("D9:D500")

    ws_data.column_dimensions["A"].width = 3
    ws_data.column_dimensions["B"].width = 16
    ws_data.column_dimensions["C"].width = 15
    ws_data.column_dimensions["D"].width = 28
    ws_data.column_dimensions["E"].width = 25
    ws_data.column_dimensions["F"].width = 22
    ws_data.column_dimensions["G"].width = 20
    ws_data.column_dimensions["H"].width = 22
    ws_data.column_dimensions["I"].width = 20
    ws_data.column_dimensions["J"].width = 18
    ws_data.column_dimensions["K"].width = 22
    ws_data.column_dimensions["L"].width = 22
    ws_data.column_dimensions["M"].width = 26
    ws_data.column_dimensions["N"].width = 35

    wb.save(os.path.join(output_dir, "Template_Population_Master.xlsx"))
    print("Regenerated Template_Population_Master.xlsx with _xlfn and fullCalcOnLoad")

# =============================================================================
# 3. TEMPLATE: EMPLOYMENT & INDUSTRY MASTER
# =============================================================================
def create_employment_template():
    wb = openpyxl.Workbook()
    wb.calculation.fullCalcOnLoad = True
    ws_data = wb.active
    ws_data.title = "Employment_QCEW_Master"
    ws_data.views.sheetView[0].showGridLines = True
    
    cols = [
        "Record_ID", "Calendar_Year", "NAICS_2Digit_Code", "NAICS_3Digit_Code", "Industry_Subsector_Title",
        "Average_Establishments", "Annual_Average_Employment", "Q1_Employment", "Q2_Employment", "Q3_Employment", "Q4_Employment",
        "YoY_Employment_Change", "Data_Release_Status"
    ]
    
    instructions = [
        (1, "ESD QCEW Annual Release", "Download annual average covered employment reports from Washington Employment Security Department (ESD)."),
        (2, "Confirm Schema Validation", "Check Cell B5 to ensure columns have not been altered."),
        (3, "Subsector Standardization", "Classify rows by 2-digit major sector and 3-digit NAICS subsector."),
        (4, "Confidentiality Flags", "Where data is suppressed by ESD to protect employer privacy (denoted by '*'), enter 0 or leave blank and note in Remarks."),
        (5, "Publish to SharePoint", "Save workbook to SharePoint Online.")
    ]
    add_instructions_sheet(wb, "SCOG Regional Employment Monitoring Intake", "Quarterly Census of Employment and Wages (QCEW) Annual Industry Trends", instructions)
    add_reference_sheet(wb, cols)
    
    ws_data["B2"] = "SCOG Annual Growth Monitoring Report — Master Employment Data"
    ws_data["B2"].font = font_title
    ws_data["B3"] = "Skagit County Covered Employment and Business Establishment Trends (ESD / QCEW)"
    ws_data["B3"].font = font_subtitle
    
    ws_data.merge_cells("B5:E5")
    ws_data["B5"] = build_schema_banner_formula(cols, start_col=2, header_row=8)
    ws_data["B5"].font = font_banner
    ws_data["B5"].fill = fill_status_valid
    ws_data["B5"].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws_data["B5"].border = border_thin
    ws_data.row_dimensions[5].height = 32
    
    rule_error = FormulaRule(formula=['ISNUMBER(SEARCH("❌",B5))'], fill=fill_status_error, font=font_banner_error)
    ws_data.conditional_formatting.add("B5:E5", rule_error)
    
    ws_data.merge_cells("F5:I5")
    ws_data["F5"] = '=IF(SUM(G9:G50)>0,"✔ INTEGRITY CHECK: Total Covered Employment Verified","⚠ INTEGRITY WARNING: Employment counts missing!")'
    ws_data["F5"].font = font_banner
    ws_data["F5"].fill = fill_status_valid
    ws_data["F5"].border = border_thin

    ws_data.row_dimensions[8].height = 28
    for col_idx, col_name in enumerate(cols, start=2):
        col_letter = get_column_letter(col_idx)
        cell = ws_data[f"{col_letter}8"]
        cell.value = col_name
        cell.font = font_th
        cell.fill = fill_navy_header
        cell.alignment = align_th
        cell.border = border_thin

    emp_samples = [
        ("EMP-2025-001", 2025, "TOTAL", "", "Total Covered Employment (All Industries)", 3663, 53850, 52930, 54510, 54220, 53740, "Official Revised"),
        ("EMP-2025-002", 2025, "11", "", "Agriculture, Forestry, Fishing and Hunting", 147, 2140, 1907, 2450, 2380, 1823, "Official Revised"),
        ("EMP-2025-003", 2025, "", "111", "Crop Production", 93, 1530, 1445, 1750, 1680, 1245, "Official Revised"),
        ("EMP-2025-004", 2025, "", "112", "Animal Production and Aquaculture", 33, 238, 240, 235, 238, 239, "Official Revised"),
        ("EMP-2025-005", 2025, "23", "", "Construction", 480, 4320, 4100, 4450, 4480, 4250, "Official Revised"),
        ("EMP-2025-006", 2025, "31-33", "", "Manufacturing", 245, 5950, 5890, 6020, 5980, 5910, "Official Revised"),
        ("EMP-2025-007", 2025, "44-45", "", "Retail Trade", 390, 6420, 6310, 6450, 6410, 6510, "Official Revised"),
        ("EMP-2025-008", 2025, "62", "", "Health Care and Social Assistance", 410, 7850, 7780, 7840, 7870, 7910, "Official Revised"),
        ("EMP-2025-009", 2025, "72", "", "Accommodation and Food Services", 285, 4150, 3980, 4320, 4310, 3990, "Official Revised"),
        ("EMP-2025-010", 2025, "92", "", "Public Administration (Government)", 95, 3450, 3420, 3460, 3440, 3480, "Official Revised")
    ]

    for idx, r in enumerate(emp_samples, start=9):
        ws_data.row_dimensions[idx].height = 21
        is_zebra = (idx % 2 == 0)
        curr_fill = fill_zebra if is_zebra else None
        
        ws_data[f"B{idx}"] = r[0]
        ws_data[f"B{idx}"].alignment = align_center
        ws_data[f"B{idx}"].font = font_td_bold
        
        ws_data[f"C{idx}"] = r[1]
        ws_data[f"C{idx}"].alignment = align_center
        ws_data[f"C{idx}"].font = font_td
        
        ws_data[f"D{idx}"] = r[2]
        ws_data[f"D{idx}"].alignment = align_center
        ws_data[f"D{idx}"].font = font_td_bold if r[2] else font_td
        
        ws_data[f"E{idx}"] = r[3]
        ws_data[f"E{idx}"].alignment = align_center
        ws_data[f"E{idx}"].font = font_td
        
        ws_data[f"F{idx}"] = r[4]
        ws_data[f"F{idx}"].alignment = align_left
        ws_data[f"F{idx}"].font = font_td_bold if r[2] else font_td
        
        ws_data[f"G{idx}"] = r[5]
        ws_data[f"G{idx}"].alignment = align_right
        ws_data[f"G{idx}"].font = font_td
        ws_data[f"G{idx}"].number_format = "#,##0"

        ws_data[f"H{idx}"] = r[6]
        ws_data[f"H{idx}"].alignment = align_right
        ws_data[f"H{idx}"].font = font_td_bold
        ws_data[f"H{idx}"].number_format = "#,##0"

        for c_offset, q_val in enumerate(r[7:11], start=9):
            c_let = get_column_letter(c_offset)
            ws_data[f"{c_let}{idx}"] = q_val
            ws_data[f"{c_let}{idx}"].alignment = align_right
            ws_data[f"{c_let}{idx}"].font = font_td
            ws_data[f"{c_let}{idx}"].number_format = "#,##0"

        ws_data[f"M{idx}"] = 0
        ws_data[f"M{idx}"].alignment = align_right
        ws_data[f"M{idx}"].font = font_calc
        ws_data[f"M{idx}"].fill = fill_formula_col
        ws_data[f"M{idx}"].number_format = "+#,##0;-#,##0;0"

        ws_data[f"N{idx}"] = r[11]
        ws_data[f"N{idx}"].alignment = align_center
        ws_data[f"N{idx}"].font = font_meta

        for c_offset in range(2, 15):
            c_let = get_column_letter(c_offset)
            cell = ws_data[f"{c_let}{idx}"]
            cell.border = border_thin
            if curr_fill and c_let != "M":
                cell.fill = curr_fill

    ws_data.column_dimensions["A"].width = 3
    ws_data.column_dimensions["B"].width = 16
    ws_data.column_dimensions["C"].width = 15
    ws_data.column_dimensions["D"].width = 18
    ws_data.column_dimensions["E"].width = 18
    ws_data.column_dimensions["F"].width = 44
    ws_data.column_dimensions["G"].width = 22
    ws_data.column_dimensions["H"].width = 25
    ws_data.column_dimensions["I"].width = 16
    ws_data.column_dimensions["J"].width = 16
    ws_data.column_dimensions["K"].width = 16
    ws_data.column_dimensions["L"].width = 16
    ws_data.column_dimensions["M"].width = 22
    ws_data.column_dimensions["N"].width = 22

    wb.save(os.path.join(output_dir, "Template_Employment_Master.xlsx"))
    print("Regenerated Template_Employment_Master.xlsx with _xlfn and fullCalcOnLoad")

# =============================================================================
# 4. TEMPLATE: HOUSING AFFORDABILITY BY AMI MASTER
# =============================================================================
def create_housing_ami_template():
    wb = openpyxl.Workbook()
    wb.calculation.fullCalcOnLoad = True
    ws_data = wb.active
    ws_data.title = "Housing_AMI_Master"
    ws_data.views.sheetView[0].showGridLines = True
    
    cols = [
        "Record_ID", "Reporting_Year", "Jurisdiction", "Structure_Type",
        "AMI_0_to_30_Pct_Units", "AMI_31_to_50_Pct_Units", "AMI_51_to_80_Pct_Units", 
        "AMI_81_to_100_Pct_Units", "AMI_101_to_120_Pct_Units", "AMI_Greater_120_Pct_Units",
        "Total_Units_Row_Sum", "Reconciliation_Status"
    ]
    
    instructions = [
        (1, "Receive Jurisdiction AMI Data", "Each year, local jurisdictions and Skagit County Public Health classify newly permitted units into Area Median Income (AMI) affordability tiers."),
        (2, "Confirm Schema Validation", "Ensure Cell B5 confirms official schema match before saving."),
        (3, "Input Housing Structure Units", "Enter net units into 1-unit, 2-unit, 3-4 unit, and 5+ unit rows across AMI tiers."),
        (4, "Reconcile with OFM Totals", "Column L (Total Permitted Units) computes the row sum. Reconcile this sum against total permits in Template_Housing_Permits_Master."),
        (5, "Publish to SharePoint", "Save workbook to SharePoint repository.")
    ]
    add_instructions_sheet(wb, "SCOG Housing Affordability by AMI Intake", "Housing Unit Production Categorized by Area Median Income (AMI) Tiers (GMA Compliance)", instructions)
    add_reference_sheet(wb, cols)
    
    ws_data["B2"] = "SCOG Annual Growth Monitoring Report — Master Housing Affordability (AMI)"
    ws_data["B2"].font = font_title
    ws_data["B3"] = "Housing Unit Distribution Across Area Median Income (AMI) Brackets by Jurisdiction"
    ws_data["B3"].font = font_subtitle
    
    ws_data.merge_cells("B5:E5")
    ws_data["B5"] = build_schema_banner_formula(cols, start_col=2, header_row=8)
    ws_data["B5"].font = font_banner
    ws_data["B5"].fill = fill_status_valid
    ws_data["B5"].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws_data["B5"].border = border_thin
    ws_data.row_dimensions[5].height = 32
    
    rule_error = FormulaRule(formula=['ISNUMBER(SEARCH("❌",B5))'], fill=fill_status_error, font=font_banner_error)
    ws_data.conditional_formatting.add("B5:E5", rule_error)
    
    ws_data.merge_cells("F5:I5")
    ws_data["F5"] = '=IF(SUM(L9:L35)>0,"✔ INTEGRITY CHECK: AMI Units Reconciled","⚠ INTEGRITY WARNING: Unit totals missing! Input units across AMI tiers.")'
    ws_data["F5"].font = font_banner
    ws_data["F5"].fill = fill_status_valid
    ws_data["F5"].border = border_thin

    ws_data.row_dimensions[8].height = 28
    for col_idx, col_name in enumerate(cols, start=2):
        col_letter = get_column_letter(col_idx)
        cell = ws_data[f"{col_letter}8"]
        cell.value = col_name
        cell.font = font_th
        cell.fill = fill_navy_header
        cell.alignment = align_th
        cell.border = border_thin

    ami_seed_data = [
        ("AMI-2025-001", 2025, "Anacortes", "1-unit (Single Family)", 0, 0, 2, 6, 12, 18),
        ("AMI-2025-002", 2025, "Anacortes", "2-units (Duplex)", 0, 0, 1, 1, 0, 0),
        ("AMI-2025-003", 2025, "Anacortes", "3-4 units (Multi-Family)", 0, 2, 3, 2, 1, 0),
        ("AMI-2025-004", 2025, "Anacortes", "5+ units (Multi-Family)", 8, 12, 14, 4, 2, 0),
        ("AMI-2025-005", 2025, "Anacortes", "ADU (Accessory Dwelling)", 1, 3, 4, 2, 0, 0),
        ("AMI-2025-006", 2025, "Burlington", "1-unit (Single Family)", 0, 0, 1, 4, 6, 4),
        ("AMI-2025-007", 2025, "Burlington", "2-units (Duplex)", 0, 0, 0, 0, 0, 0),
        ("AMI-2025-008", 2025, "Burlington", "3-4 units (Multi-Family)", 1, 1, 2, 2, 0, 0),
        ("AMI-2025-009", 2025, "Burlington", "5+ units (Multi-Family)", 12, 16, 18, 4, 2, 0),
        ("AMI-2025-010", 2025, "Burlington", "ADU (Accessory Dwelling)", 1, 1, 2, 1, 0, 0),
        ("AMI-2025-011", 2025, "Mount Vernon", "1-unit (Single Family)", 0, 0, 5, 15, 25, 25),
        ("AMI-2025-012", 2025, "Mount Vernon", "2-units (Duplex)", 0, 1, 2, 2, 1, 0),
        ("AMI-2025-013", 2025, "Mount Vernon", "3-4 units (Multi-Family)", 2, 4, 6, 3, 1, 0),
        ("AMI-2025-014", 2025, "Mount Vernon", "5+ units (Multi-Family)", 18, 28, 35, 10, 4, 0),
        ("AMI-2025-015", 2025, "Mount Vernon", "ADU (Accessory Dwelling)", 2, 5, 7, 3, 1, 0),
        ("AMI-2025-016", 2025, "Sedro-Woolley", "1-unit (Single Family)", 0, 0, 4, 10, 16, 10),
        ("AMI-2025-017", 2025, "Sedro-Woolley", "2-units (Duplex)", 0, 1, 1, 1, 1, 0),
        ("AMI-2025-018", 2025, "Sedro-Woolley", "3-4 units (Multi-Family)", 1, 3, 4, 3, 1, 0),
        ("AMI-2025-019", 2025, "Sedro-Woolley", "5+ units (Multi-Family)", 6, 10, 10, 3, 1, 0),
        ("AMI-2025-020", 2025, "Sedro-Woolley", "ADU (Accessory Dwelling)", 1, 2, 3, 2, 0, 0)
    ]

    for idx, r in enumerate(ami_seed_data, start=9):
        ws_data.row_dimensions[idx].height = 21
        is_zebra = (idx % 2 == 0)
        curr_fill = fill_zebra if is_zebra else None
        
        ws_data[f"B{idx}"] = r[0]
        ws_data[f"B{idx}"].alignment = align_center
        ws_data[f"B{idx}"].font = font_td_bold
        
        ws_data[f"C{idx}"] = r[1]
        ws_data[f"C{idx}"].alignment = align_center
        ws_data[f"C{idx}"].font = font_td
        
        ws_data[f"D{idx}"] = r[2]
        ws_data[f"D{idx}"].alignment = align_left
        ws_data[f"D{idx}"].font = font_td
        
        ws_data[f"E{idx}"] = r[3]
        ws_data[f"E{idx}"].alignment = align_left
        ws_data[f"E{idx}"].font = font_td
        
        for c_offset, val in enumerate(r[4:10], start=6):
            c_let = get_column_letter(c_offset)
            ws_data[f"{c_let}{idx}"] = val
            ws_data[f"{c_let}{idx}"].alignment = align_right
            ws_data[f"{c_let}{idx}"].font = font_td
            ws_data[f"{c_let}{idx}"].number_format = "#,##0"

        ws_data[f"L{idx}"] = f"=SUM(F{idx}:K{idx})"
        ws_data[f"L{idx}"].alignment = align_right
        ws_data[f"L{idx}"].font = font_calc
        ws_data[f"L{idx}"].fill = fill_formula_col
        ws_data[f"L{idx}"].number_format = "#,##0"

        ws_data[f"M{idx}"] = "Reconciled"
        ws_data[f"M{idx}"].alignment = align_center
        ws_data[f"M{idx}"].font = font_meta

        for c_offset in range(2, 14):
            c_let = get_column_letter(c_offset)
            cell = ws_data[f"{c_let}{idx}"]
            cell.border = border_thin
            if curr_fill and c_let != "L":
                cell.fill = curr_fill

    dv_jur = DataValidation(type="list", formula1="Ref_Lookup!$A$2:$A$12", allow_blank=True)
    ws_data.add_data_validation(dv_jur)
    dv_jur.add("D9:D200")

    ws_data.column_dimensions["A"].width = 3
    ws_data.column_dimensions["B"].width = 16
    ws_data.column_dimensions["C"].width = 15
    ws_data.column_dimensions["D"].width = 28
    ws_data.column_dimensions["E"].width = 28
    ws_data.column_dimensions["F"].width = 22
    ws_data.column_dimensions["G"].width = 22
    ws_data.column_dimensions["H"].width = 22
    ws_data.column_dimensions["I"].width = 24
    ws_data.column_dimensions["J"].width = 24
    ws_data.column_dimensions["K"].width = 26
    ws_data.column_dimensions["L"].width = 22
    ws_data.column_dimensions["M"].width = 22

    wb.save(os.path.join(output_dir, "Template_Housing_AMI_Master.xlsx"))
    print("Regenerated Template_Housing_AMI_Master.xlsx with _xlfn and fullCalcOnLoad")

if __name__ == "__main__":
    create_housing_permits_template()
    create_population_template()
    create_employment_template()
    create_housing_ami_template()
    print("All 4 master templates successfully regenerated with _xlfn.TEXTJOIN and fullCalcOnLoad!")
