import sys
import os
import json
import time
import base64
import requests

from fabric_client import FabricClient

def main():
    client = FabricClient("cfeefa92-730d-43b2-b2b1-9c46826d5807")
    ws_id = client.workspace_id
    folder_id = "116bb17e-860e-4023-9e3c-badb8787f71a"
    lh_id = "c7aa3259-2e37-46de-9f94-bce5b73481e9"
    lh_name = "SecurityLab_Lakehouse"

    nb_content = f"""# Fabric notebook source

# METADATA ********************

# META {{
# META   "kernel_info": {{
# META     "name": "synapse_pyspark"
# META   }},
# META   "dependencies": {{
# META     "lakehouse": {{
# META       "default_lakehouse": "{lh_id}",
# META       "default_lakehouse_name": "{lh_name}",
# META       "default_lakehouse_workspace_id": "{ws_id}",
# META       "known_lakehouses": [
# META         {{
# META           "id": "{lh_id}"
# META         }}
# META       ]
# META     }}
# META   }}
# META }}

# MARKDOWN ********************
# # DP-600 Study Environment: Security & Governance Lab
# ## Step 3 — Load Messy Synthetic Sales Data

# CELL ********************

from pyspark.sql import Row

data = [
    Row(SalesID=1, Region="East",  SalesRep="Alice", Email="alice@contoso.com", Amount=1200.00, CommissionPct=0.05),
    Row(SalesID=2, Region="east",  SalesRep="alice", Email="alice@contoso.com", Amount=950.0,   CommissionPct=0.05),
    Row(SalesID=3, Region="West",  SalesRep="Bob",   Email="bob@contoso.com",   Amount=None,    CommissionPct=0.04),
    Row(SalesID=4, Region="WEST",  SalesRep="Bob",   Email=None,                Amount=700.0,   CommissionPct=0.04),
    Row(SalesID=5, Region=None,    SalesRep="Carol", Email="carol@contoso.com", Amount=1100.0,  CommissionPct=None),
    Row(SalesID=6, Region="North", SalesRep="Carol", Email="carol@contoso.com", Amount=640.0,   CommissionPct=0.03),
    Row(SalesID=7, Region="",      SalesRep="Dave",  Email="dave@contoso.com",  Amount=2200.0,  CommissionPct=0.06),
    Row(SalesID=8, Region="West",  SalesRep="Dave",  Email="DAVE@CONTOSO.COM",  Amount=300.0,   CommissionPct=0.06),
    Row(SalesID=7, Region="East",  SalesRep="Dave",  Email="dave@contoso.com",  Amount=2200.0,  CommissionPct=0.06),
]

df = spark.createDataFrame(data)
df.write.mode("overwrite").format("delta").saveAsTable("Sales")

# METADATA ********************

# CELL ********************

print("Sales table row count:")
display(spark.sql("SELECT COUNT(*) as row_count FROM Sales"))
display(spark.sql("SELECT * FROM Sales"))

# METADATA ********************
"""

    platform_content = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": "Notebook",
            "displayName": "nb_load_security_sales"
        },
        "config": {
            "version": "2.0",
            "logicalId": "00000000-0000-0000-0000-000000000000"
        }
    }

    parts = [
        {
            "path": "notebook-content.py",
            "payload": base64.b64encode(nb_content.encode("utf-8")).decode("utf-8"),
            "payloadType": "InlineBase64"
        },
        {
            "path": ".platform",
            "payload": base64.b64encode(json.dumps(platform_content).encode("utf-8")).decode("utf-8"),
            "payloadType": "InlineBase64"
        }
    ]

    items = client.get_items("Notebook")
    nb_item = next((i for i in items if i.get("displayName") == "nb_load_security_sales"), None)

    if not nb_item:
        url = f"{client.FABRIC_API_BASE}/workspaces/{ws_id}/items"
        payload = {
            "displayName": "nb_load_security_sales",
            "type": "Notebook",
            "folderId": folder_id,
            "definition": {
                "parts": parts
            }
        }
        r = requests.post(url, headers=client.fabric_headers, json=payload)
        print("Create notebook response:", r.status_code)
        if r.status_code in (200, 201, 202):
            time.sleep(3)
            items = client.get_items("Notebook")
            nb_item = next((i for i in items if i.get("displayName") == "nb_load_security_sales"), None)
    else:
        print("Notebook already exists:", nb_item["id"])
        # Ensure it is in the right folder
        if nb_item.get("folderId") != folder_id:
            client.move_item_to_folder(nb_item["id"], folder_id)

    print("Notebook ready:", nb_item["id"] if nb_item else "None")
    return nb_item

if __name__ == "__main__":
    main()
