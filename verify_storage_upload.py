"""
Quick Verification & Exploration Script for Azure Blob Storage
Container: raw-data @ trustedworkspacestorage
"""
import subprocess
import json
import os
import sys

ACCOUNT_NAME = "trustedworkspacestorage"
CONTAINER_NAME = "raw-data"

def run_az_command(args):
    cmd = ["az"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        return None
    return result.stdout

def main():
    print(f"==================================================")
    print(f"Starting Storage Verification: {ACCOUNT_NAME}/{CONTAINER_NAME}")
    print(f"==================================================")

    # 1. Fetch all blobs metadata
    print("Fetching list of all uploaded blobs...")
    raw_output = run_az_command([
        "storage", "blob", "list",
        "--account-name", ACCOUNT_NAME,
        "--container-name", CONTAINER_NAME,
        "--auth-mode", "login",
        "--query", "[].{name:name, size:properties.contentLength}",
        "-o", "json"
    ])

    if not raw_output:
        print("Failed to list blobs.")
        return

    blobs = json.loads(raw_output)
    total_blobs = len(blobs)
    total_size_bytes = sum(b.get("size", 0) or 0 for b in blobs)
    total_size_gb = total_size_bytes / (1024 ** 3)
    total_size_mb = total_size_bytes / (1024 ** 2)

    print(f"\n[SUMMARY METRICS]")
    print(f"- Total Files/Blobs: {total_blobs:,}")
    print(f"- Total Volume: {total_size_gb:.2f} GB ({total_size_mb:,.2f} MB)")

    # 2. Partition & Dataset Analysis
    years = set()
    months_by_year = {}
    file_types = {}
    categories = set()
    ref_data = []

    for b in blobs:
        name = b["name"]
        parts = name.split("/")

        # Check reference files (e.g. DIVIPOLA / DAVIPOLA)
        if "codigos davipola" in name.lower() or "divipola" in name.lower():
            ref_data.append(name)
            continue

        # Check year/month partitions
        for part in parts:
            if part.startswith("year="):
                y = part.split("=")[1]
                years.add(y)
                if y not in months_by_year:
                    months_by_year[y] = set()
            elif part.startswith("month="):
                m = part.split("=")[1]
                # Associate with the most recent detected year
                if years:
                    current_y = [p.split("=")[1] for p in parts if p.startswith("year=")]
                    if current_y:
                        months_by_year[current_y[0]].add(m)

        # File classification
        filename = parts[-1]
        ext = os.path.splitext(filename)[1].lower()
        file_types[ext] = file_types.get(ext, 0) + 1
        
        # Categorize by module/survey topic
        main_topic = filename.split(" - ")[0] if " - " in filename else filename
        categories.add(main_topic)

    print(f"\n[PARTITIONS DETECTED]")
    sorted_years = sorted(list(years))
    if sorted_years:
        print(f"- Years available ({len(sorted_years)}): {sorted_years[0]} to {sorted_years[-1]}")
        for y in sorted_years:
            months = sorted(list(months_by_year.get(y, [])))
            print(f"  * Year {y}: {len(months)} months ({', '.join(months)})")
    else:
        print("- No standard year=YYYY partitions found.")

    print(f"\n[REFERENCE DATA]")
    for r in ref_data:
        print(f"- {r}")

    print(f"\n[FILE EXTENSIONS]")
    for ext, count in file_types.items():
        print(f"- {ext or '[no extension]'}: {count} files")

    # 3. Sample a small snippet from DIVIPOLA and one DANE file
    print(f"\n[SAMPLE PREVIEW (First 5 lines)]")
    
    # Preview DIVIPOLA
    if ref_data:
        target_ref = ref_data[0]
        print(f"\n--- Previewing Reference: {target_ref} ---")
        preview_ref = run_az_command([
            "storage", "blob", "download",
            "--account-name", ACCOUNT_NAME,
            "--container-name", CONTAINER_NAME,
            "--name", f'"{target_ref}"',
            "--auth-mode", "login",
            "--query", "content",
            "-o", "tsv"
        ])
        if preview_ref:
            lines = preview_ref.strip().split("\n")[:6]
            for l in lines:
                print(l)

    # Preview one DANE raw data file
    dane_files = [b["name"] for b in blobs if b["name"].endswith(".txt") or b["name"].endswith(".csv")]
    if dane_files:
        sample_file = dane_files[0]
        print(f"\n--- Previewing Raw Sample: {sample_file} ---")
        sample_out = run_az_command([
            "storage", "blob", "download",
            "--account-name", ACCOUNT_NAME,
            "--container-name", CONTAINER_NAME,
            "--name", f'"{sample_file}"',
            "--auth-mode", "login",
            "--query", "content",
            "-o", "tsv"
        ])
        if sample_out:
            lines = sample_out.strip().split("\n")[:6]
            for l in lines:
                print(l)

    print(f"\n==================================================")
    print("Verification Completed Successfully!")
    print(f"==================================================")

if __name__ == "__main__":
    main()
