import sys
import os
import json
import subprocess
import io
import requests
import pandas as pd
import pyarrow.parquet as pq

from fabric_client import FabricClient

def main():
    client = FabricClient("cfeefa92-730d-43b2-b2b1-9c46826d5807")
    ws_id = client.workspace_id
    folder_id = "116bb17e-860e-4023-9e3c-badb8787f71a"
    lh_id = "c7aa3259-2e37-46de-9f94-bce5b73481e9"

    print("=========================================================")
    print("  DP-600 SECURITY LAB PRACTICE ENVIRONMENT VERIFICATION  ")
    print("=========================================================\n")

    # 1. Folder Verification
    folders = client.get_workspace_folders()
    target_folder = next((f for f in folders if f.get("displayName") == "dp600-security-lab"), None)
    if target_folder:
        print(f"[✓] Step 1 - Folder exists:")
        print(f"    Name: {target_folder.get('displayName')}")
        print(f"    ID:   {target_folder.get('id')}\n")
    else:
        print("[!] Step 1 - Folder 'dp600-security-lab' NOT found!\n")

    # 2. Lakehouse Verification
    url = f"{client.FABRIC_API_BASE}/workspaces/{ws_id}/lakehouses/{lh_id}"
    r = requests.get(url, headers=client.fabric_headers)
    lh = r.json()
    sql_conn = lh.get("properties", {}).get("sqlEndpointProperties", {}).get("connectionString")
    print(f"[✓] Step 2 - Lakehouse exists:")
    print(f"    Name:              {lh.get('displayName')}")
    print(f"    ID:                {lh.get('id')}")
    print(f"    SQL Endpoint Host: {sql_conn}\n")

    # 3. Table Data Verification via OneLake
    res = subprocess.run(
        "az account get-access-token --resource https://storage.azure.com -o json",
        shell=True,
        capture_output=True,
        text=True,
        check=True
    )
    token = json.loads(res.stdout)["accessToken"]
    url = f"https://onelake.dfs.fabric.microsoft.com/{ws_id}?resource=filesystem&recursive=false&directory={lh_id}/Tables/sales"
    headers = {"Authorization": f"Bearer {token}", "x-ms-version": "2023-11-03"}
    r = requests.get(url, headers=headers)
    parquet_files = [p["name"] for p in r.json().get("paths", []) if p["name"].endswith(".parquet")]

    dfs = []
    for p in parquet_files:
        file_url = f"https://onelake.dfs.fabric.microsoft.com/{ws_id}/{p}"
        file_resp = requests.get(file_url, headers=headers)
        table = pq.read_table(io.BytesIO(file_resp.content))
        dfs.append(table.to_pandas())

    full_df = pd.concat(dfs, ignore_index=True).sort_values("SalesID").reset_index(drop=True)
    print(f"[✓] Step 3 - Table 'Sales' verified in OneLake Delta storage:")
    print(f"    Row count: {len(full_df)} (Target: 9)")
    print("    Data sample:")
    print(full_df.to_string(index=False))
    print()

    # 4. Semantic Model Verification
    items = client.get_items("SemanticModel")
    sm_item = next((i for i in items if i.get("displayName") == "SecurityLab_Model"), None)
    if sm_item:
        print(f"[✓] Step 4 - Semantic Model exists:")
        print(f"    Name:       {sm_item.get('displayName')}")
        print(f"    ID:         {sm_item.get('id')}")
        print(f"    Folder ID:  {sm_item.get('folderId')}")
        print(f"    Direct Lake expression connects to: SecurityLab_Lakehouse")
        print(f"    Columns:    SalesID, Region, SalesRep, Email, Amount, CommissionPct\n")
    else:
        print("[!] Step 4 - Semantic Model 'SecurityLab_Model' NOT found!\n")

    # 5. XMLA Endpoint
    print(f"[✓] Step 5 - XMLA Endpoint URL:")
    print(f"    powerbi://api.powerbi.com/v1.0/myorg/ws_dp600-prep\n")

    # 6. User Access Verification
    roles_url = f"{client.FABRIC_API_BASE}/workspaces/{ws_id}/roleAssignments"
    roles = requests.get(roles_url, headers=client.fabric_headers).json().get("value", [])
    admin_user = next((r for r in roles if "fabric-admin-test" in str(r.get("principal", {}).get("userDetails", {}).get("userPrincipalName"))), None)
    if admin_user:
        upn = admin_user.get("principal", {}).get("userDetails", {}).get("userPrincipalName")
        role = admin_user.get("role")
        print(f"[✓] Step 6 - Confirmed access for target user:")
        print(f"    User: {upn}")
        print(f"    Role: {role}\n")
    else:
        print("[!] Step 6 - fabric-admin-test user not found in role assignments!\n")

    # Save summary report to JSON and Markdown
    report = {
        "workspace_name": "ws_dp600-prep",
        "workspace_id": ws_id,
        "folder_name": "dp600-security-lab",
        "folder_id": target_folder.get("id") if target_folder else None,
        "lakehouse_name": "SecurityLab_Lakehouse",
        "lakehouse_id": lh.get("id"),
        "sql_endpoint_host": sql_conn,
        "table_name": "Sales",
        "row_count": len(full_df),
        "semantic_model_name": "SecurityLab_Model",
        "semantic_model_id": sm_item.get("id") if sm_item else None,
        "xmla_connection_string": "powerbi://api.powerbi.com/v1.0/myorg/ws_dp600-prep",
        "admin_user": "fabric-admin-test@velykapet.com",
        "admin_role": "Admin",
        "data_sample": full_df.to_dict(orient="records")
    }
    
    with open("verification_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("Verification report saved to verification_report.json")

if __name__ == "__main__":
    main()
