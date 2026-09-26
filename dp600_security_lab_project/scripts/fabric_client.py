"""
Fabric API Client helper with IPv4 resolution and az cli token acquisition.
"""
import os
import sys
import json
import time
import socket
import subprocess
import requests

# Fix Windows DNS IPv6 resolution issue for Microsoft Fabric endpoints
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4


class FabricClient:
    FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
    POWERBI_API_BASE = "https://api.powerbi.com/v1.0/myorg"

    def __init__(self, workspace_id: str = "cfeefa92-730d-43b2-b2b1-9c46826d5807"):
        self.workspace_id = workspace_id
        self._fabric_token = None
        self._powerbi_token = None
        self._token_expiry = 0

    def get_fabric_token(self) -> str:
        res = subprocess.run(
            "az account get-access-token --resource https://api.fabric.microsoft.com -o json",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        self._fabric_token = data["accessToken"]
        return self._fabric_token

    def get_powerbi_token(self) -> str:
        res = subprocess.run(
            "az account get-access-token --resource https://analysis.windows.net/powerbi/api -o json",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        self._powerbi_token = data["accessToken"]
        return self._powerbi_token

    @property
    def fabric_headers(self) -> dict:
        token = self.get_fabric_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    @property
    def powerbi_headers(self) -> dict:
        token = self.get_powerbi_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_workspace_folders(self) -> list:
        url = f"{self.FABRIC_API_BASE}/workspaces/{self.workspace_id}/folders"
        r = requests.get(url, headers=self.fabric_headers)
        r.raise_for_status()
        return r.json().get("value", [])

    def create_folder(self, display_name: str) -> dict:
        # Check if already exists
        folders = self.get_workspace_folders()
        for f in folders:
            if f.get("displayName") == display_name:
                print(f"[+] Folder '{display_name}' already exists with ID: {f.get('id')}")
                return f

        url = f"{self.FABRIC_API_BASE}/workspaces/{self.workspace_id}/folders"
        r = requests.post(url, headers=self.fabric_headers, json={"displayName": display_name})
        r.raise_for_status()
        folder = r.json()
        print(f"[+] Created folder '{display_name}' with ID: {folder.get('id')}")
        return folder

    def get_lakehouses(self) -> list:
        url = f"{self.FABRIC_API_BASE}/workspaces/{self.workspace_id}/lakehouses"
        r = requests.get(url, headers=self.fabric_headers)
        r.raise_for_status()
        return r.json().get("value", [])

    def create_lakehouse(self, display_name: str, folder_id: str = None) -> dict:
        lakehouses = self.get_lakehouses()
        for lh in lakehouses:
            if lh.get("displayName") == display_name:
                print(f"[+] Lakehouse '{display_name}' already exists with ID: {lh.get('id')}")
                if folder_id and lh.get("folderId") != folder_id:
                    self.move_item_to_folder(lh["id"], folder_id)
                return lh

        url = f"{self.FABRIC_API_BASE}/workspaces/{self.workspace_id}/lakehouses"
        payload = {"displayName": display_name}
        if folder_id:
            payload["folderId"] = folder_id

        r = requests.post(url, headers=self.fabric_headers, json=payload)
        r.raise_for_status()
        lh = r.json()
        print(f"[+] Created Lakehouse '{display_name}' with ID: {lh.get('id')}")
        
        # If folder_id was specified and not in folder, move it
        if folder_id and lh.get("folderId") != folder_id:
            time.sleep(2)
            self.move_item_to_folder(lh["id"], folder_id)
        return lh

    def move_item_to_folder(self, item_id: str, folder_id: str):
        url = f"{self.FABRIC_API_BASE}/workspaces/{self.workspace_id}/items/{item_id}/move"
        payload = {"targetFolderId": folder_id}
        try:
            r = requests.post(url, headers=self.fabric_headers, json=payload)
            if r.status_code in (200, 204):
                print(f"[+] Moved item {item_id} into folder {folder_id}")
            else:
                print(f"[-] Move item response: {r.status_code} {r.text}")
        except Exception as e:
            print(f"[-] Move item exception: {e}")

    def get_items(self, item_type: str = None) -> list:
        url = f"{self.FABRIC_API_BASE}/workspaces/{self.workspace_id}/items"
        params = {}
        if item_type:
            params["type"] = item_type
        r = requests.get(url, headers=self.fabric_headers, params=params)
        r.raise_for_status()
        return r.json().get("value", [])

    def get_lakehouse_tables(self, lakehouse_id: str) -> list:
        url = f"{self.FABRIC_API_BASE}/workspaces/{self.workspace_id}/lakehouses/{lakehouse_id}/tables"
        r = requests.get(url, headers=self.fabric_headers)
        r.raise_for_status()
        return r.json().get("data", [])
