"""
Extract and convert Italcol Price List from PDF to structured formats (CSV, JSON, Parquet).
"""

import os
import re
import json
import pandas as pd
from pypdf import PdfReader


def parse_italcol_pdf(pdf_path: str) -> pd.DataFrame:
    reader = PdfReader(pdf_path)
    records = []
    current_category = "GENERAL"

    header_patterns = [
        "LISTA VIGENTE", "ESTOS PRECIOS", "PRECIOS SUJETOS", "PLANTAS",
        "EAN 13", "COD BARRAS", "COD INTERNO", "PRECIO BASE", "PRECIO antes",
        "precio iva", "descuento 3%", "PAGINA"
    ]

    for page_idx, page in enumerate(reader.pages):
        raw_text = page.extract_text()
        for raw_line in raw_text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            if any(h.lower() in line.lower() for h in header_patterns):
                continue

            prices = re.findall(r"\$\s*[\d\.\,]+", line)
            if not prices:
                current_category = line
                continue

            if len(prices) >= 4:
                p4_str = prices[-1]
                p3_str = prices[-2]
                p2_str = prices[-3]
                p1_str = prices[-4]

                idx = line.rfind(prices[-4])
                prefix = line[:idx].strip()

                tokens = prefix.split()
                if len(tokens) >= 2:
                    if re.match(r"^\d{8,}$", tokens[0]) or tokens[0].upper() == "N/A":
                        barcode = tokens[0]
                        internal_code = tokens[1]
                        desc = " ".join(tokens[2:])
                    elif re.match(r"^\d{4,7}$", tokens[0]):
                        barcode = "N/A"
                        internal_code = tokens[0]
                        desc = " ".join(tokens[1:])
                    else:
                        barcode = "N/A"
                        internal_code = tokens[0]
                        desc = " ".join(tokens[1:])
                else:
                    barcode = "N/A"
                    internal_code = "N/A"
                    desc = prefix

                records.append({
                    "categoria": current_category,
                    "codigo_barras": barcode,
                    "codigo_interno": internal_code,
                    "descripcion": desc,
                    "precio_base": float(p1_str.replace("$", "").replace(".", "").replace(",", ".").strip()),
                    "precio_antes_iva": float(p2_str.replace("$", "").replace(".", "").replace(",", ".").strip()),
                    "precio_iva_incluido": float(p3_str.replace("$", "").replace(".", "").replace(",", ".").strip()),
                    "precio_descuento_3_pct": float(p4_str.replace("$", "").replace(".", "").replace(",", ".").strip()),
                    "pagina": page_idx + 1,
                })

    df = pd.DataFrame(records)
    return df


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(base_dir, "LISTA DE PRECIOS ITALCOL 2026 3..pdf")

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return

    print(f"Parsing {pdf_path}...")
    df = parse_italcol_pdf(pdf_path)
    print(f"Extracted {len(df)} products.")

    # Export CSV
    csv_path = os.path.join(base_dir, "lista_precios_italcol.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved CSV to {csv_path}")

    # Export JSON
    json_path = os.path.join(base_dir, "lista_precios_italcol.json")
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)
    print(f"Saved JSON to {json_path}")

    # Export Parquet
    parquet_path = os.path.join(base_dir, "lista_precios_italcol.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"Saved Parquet to {parquet_path}")


if __name__ == "__main__":
    main()
