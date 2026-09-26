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
    nb_id = "812d6fe8-8f2e-4597-8968-d493fabe0e68"
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

# META {{
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }}

# CELL ********************

display(spark.sql("SELECT * FROM Sales"))

# METADATA ********************

# META {{
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }}
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

    print("[*] Updating notebook definition...")
    url = f"{client.FABRIC_API_BASE}/workspaces/{ws_id}/items/{nb_id}/updateDefinition"
    payload = {"definition": {"parts": parts}}
    r = requests.post(url, headers=client.fabric_headers, json=payload)
    print(f"Update definition response: {r.status_code}")
    if r.status_code == 202:
        loc = r.headers.get("Location")
        print(f"Operation location: {loc}")
        for _ in range(10):
            time.sleep(2)
            r_op = requests.get(loc, headers=client.fabric_headers)
            status = r_op.json().get("status")
            print(f"Definition update status: {status}")
            if status in ("Succeeded", "Failed"):
                if status == "Failed":
                    print("Error:", r_op.json())
                    return False
                break

    # Now trigger notebook run job
    print("[*] Triggering notebook job...")
    job_url = f"{client.FABRIC_API_BASE}/workspaces/{ws_id}/items/{nb_id}/jobs/instances?jobType=RunNotebook"
    r_job = requests.post(job_url, headers=client.fabric_headers)
    print(f"Trigger job response: {r_job.status_code}")

    loc = r_job.headers.get("Location")
    if loc:
        print(f"Job instance location: {loc}")
        # Poll job status
        for i in range(40):
            time.sleep(5)
            r_stat = requests.get(loc, headers=client.fabric_headers)
            job_data = r_stat.json()
            status = job_data.get("status")
            print(f"[{i*5}s] Job execution status: {status}")
            if status in ("Completed", "Failed", "Cancelled", "Deduped"):
                print(f"Final job result: {job_data}")
                return status == "Completed"
    return False

if __name__ == "__main__":
    main()
