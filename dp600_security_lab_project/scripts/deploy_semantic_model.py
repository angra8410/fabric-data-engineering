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

    model_dir = os.path.abspath("semantic_models/SecurityLab_Model.SemanticModel")
    
    parts = []
    for root, _, files in os.walk(model_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, model_dir).replace("\\", "/")
            with open(full_path, "rb") as fp:
                content = fp.read()
            parts.append({
                "path": rel_path,
                "payload": base64.b64encode(content).decode("utf-8"),
                "payloadType": "InlineBase64"
            })
            print(f"Added part: {rel_path} ({len(content)} bytes)")

    # Check if semantic model already exists
    items = client.get_items("SemanticModel")
    sm_item = next((i for i in items if i.get("displayName") == "SecurityLab_Model"), None)

    if not sm_item:
        print("[*] Creating SemanticModel 'SecurityLab_Model' with TMDL definition...")
        url = f"{client.FABRIC_API_BASE}/workspaces/{ws_id}/items"
        payload = {
            "displayName": "SecurityLab_Model",
            "type": "SemanticModel",
            "folderId": folder_id,
            "definition": {
                "parts": parts
            }
        }
        r = requests.post(url, headers=client.fabric_headers, json=payload)
        print("Create SemanticModel response:", r.status_code)
        if r.status_code == 202:
            loc = r.headers.get("Location")
            print(f"Operation location: {loc}")
            for i in range(15):
                time.sleep(3)
                r_op = requests.get(loc, headers=client.fabric_headers)
                status = r_op.json().get("status")
                print(f"Operation status: {status}")
                if status in ("Succeeded", "Failed"):
                    if status == "Failed":
                        print("Failed error details:", r_op.json())
                    break
        elif r.status_code in (200, 201):
            print("Direct creation succeeded:", r.json())
        else:
            print("Create error:", r.text)

        time.sleep(3)
        items = client.get_items("SemanticModel")
        sm_item = next((i for i in items if i.get("displayName") == "SecurityLab_Model"), None)
    else:
        print(f"[*] SemanticModel already exists: {sm_item['id']}")

    print(f"[*] SecurityLab_Model details: {sm_item}")
    return sm_item

if __name__ == "__main__":
    main()
