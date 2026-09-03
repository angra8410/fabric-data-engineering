"""
Fixed Multi-Year Schema & Delimiter Profiler for DANE dataset
"""
import subprocess
import json
import re
import os

ACCOUNT_NAME = "trustedworkspacestorage"
CONTAINER_NAME = "raw-data"

def run_az_command(args):
    cmd = ["az"] + args
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        return None
    return res.stdout

def main():
    print("Listing all blobs in raw-data...")
    raw_output = run_az_command([
        "storage", "blob", "list",
        "--account-name", ACCOUNT_NAME,
        "--container-name", CONTAINER_NAME,
        "--auth-mode", "login",
        "--query", "[].name",
        "-o", "json"
    ])
    
    if not raw_output:
        print("Failed to list blobs.")
        return

    blobs = json.loads(raw_output)
    print(f"Total blobs found: {len(blobs)}")

    by_year = {}
    for b in blobs:
        match = re.search(r"year=(\d{4})", b)
        if match:
            y = match.group(1)
            by_year.setdefault(y, []).append(b)

    sorted_years = sorted(by_year.keys())
    year_profiles = {}

    for y in sorted_years:
        year_files = by_year[y]
        
        # Pick 2-3 specific files: ocupados, desocupados, caracteristicas
        sample_candidates = []
        for kw in ["ocupados", "desocupados", "caracter", "fuerza"]:
            matches = [f for f in year_files if kw in f.lower()]
            if matches:
                for m in matches[:2]:
                    if m not in sample_candidates:
                        sample_candidates.append(m)
            if len(sample_candidates) >= 3:
                break
        if not sample_candidates and year_files:
            sample_candidates = year_files[:3]

        print(f"\n--- Profiling Year {y} ({len(year_files)} files) ---")
        year_profiles[y] = []

        for sample_path in sample_candidates:
            temp_file = f"temp_sample_{y}.txt"
            
            # Download file using az cli
            dl_cmd = [
                "storage", "blob", "download",
                "--account-name", ACCOUNT_NAME,
                "--container-name", CONTAINER_NAME,
                "--name", sample_path,
                "--file", temp_file,
                "--auth-mode", "login"
            ]
            run_az_command(dl_cmd)

            if not os.path.exists(temp_file):
                print(f"  Failed to download {sample_path}")
                continue

            try:
                content = None
                for enc in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        with open(temp_file, "r", encoding=enc) as f:
                            lines = [f.readline() for _ in range(4)]
                            if lines and lines[0].strip():
                                content = lines
                                break
                    except:
                        continue

                if content and content[0].strip():
                    # Check first row for headers
                    header = content[0].strip()
                    first_row = content[1].strip() if len(content) > 1 else ""
                    
                    # Detect delimiter
                    delim = "UNKNOWN"
                    if "\t" in header:
                        delim = "\\t (TAB)"
                        cols = header.split("\t")
                    elif ";" in header:
                        delim = "; (SEMICOLON)"
                        cols = header.split(";")
                    elif "," in header:
                        delim = ", (COMMA)"
                        cols = header.split(",")
                    elif "|" in header:
                        delim = "| (PIPE)"
                        cols = header.split("|")
                    else:
                        delim = "WHITESPACE"
                        cols = header.split()

                    cols = [c.strip().replace('"', '') for c in cols]
                    
                    # Key columns
                    weight_cols = [c for c in cols if any(w in c.upper() for w in ["FEX", "PESO", "FACTOR", "WGT", "POND"])]
                    geo_cols = [c for c in cols if any(g in c.upper() for g in ["DPTO", "DEP", "MPIO", "CIUDAD", "AREA", "CLASE", "REG"])]
                    id_cols = [c for c in cols if any(i in c.upper() for i in ["DIRECTORIO", "SECUENCIA", "ORDEN", "HOGAR", "LLAVE"])]

                    fname = sample_path.split("/")[-1]
                    info = {
                        "file": fname,
                        "path": sample_path,
                        "delim": delim,
                        "total_cols": len(cols),
                        "weights": weight_cols,
                        "geo": geo_cols,
                        "ids": id_cols,
                        "sample_cols_preview": cols[:10]
                    }
                    year_profiles[y].append(info)
                    print(f"  [{fname[:40]}...]")
                    print(f"    Delimiter: {delim} | Cols: {len(cols)}")
                    print(f"    Weights: {weight_cols}")
                    print(f"    Geo: {geo_cols}")
            except Exception as e:
                print(f"  Error reading {sample_path}: {e}")
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    with open("schema_profile_report.json", "w", encoding="utf-8") as f:
        json.dump(year_profiles, f, indent=2)
    print("\nSaved full report to schema_profile_report.json")

if __name__ == "__main__":
    main()
