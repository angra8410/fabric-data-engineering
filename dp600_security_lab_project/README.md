# DP-600 "Secure & Govern" Practice Environment

## Environment Overview
Isolated practice environment for the Microsoft Fabric DP-600 exam ("Secure & Govern" domain) in workspace **`ws_dp600-prep`** (Tenant: `velykapet.com`).

Per practice requirements, this environment sets up the **data and modeling layer only**, leaving all security (RLS, OLS, OneLake roles) completely unconfigured for hands-on exercises.

---

## Workspace & Asset Reference

| Item | Name | ID / Details |
| :--- | :--- | :--- |
| **Workspace** | `ws_dp600-prep` | `cfeefa92-730d-43b2-b2b1-9c46826d5807` |
| **Folder** | `dp600-security-lab` | `116bb17e-860e-4023-9e3c-badb8787f71a` |
| **Lakehouse** | `SecurityLab_Lakehouse` | `c7aa3259-2e37-46de-9f94-bce5b73481e9` |
| **SQL Analytics Host**| `SecurityLab_Lakehouse` | `4kq2jhmt3otufjmisv75mkjoq4-sl5o5tynoozehmvrtrdie3kya4.datawarehouse.fabric.microsoft.com` |
| **Table** | `Sales` (Delta) | 9 rows, deliberate casing & null anomalies |
| **Semantic Model** | `SecurityLab_Model` | `f3c62cd4-8d24-4f08-be88-49cd5c8e27c7` (Direct Lake) |
| **XMLA Connection** | XMLA Endpoint | `powerbi://api.powerbi.com/v1.0/myorg/ws_dp600-prep` |
| **Admin Account** | `fabric-admin-test@velykapet.com` | Role: `Admin` |

---

## Project Structure
```
dp600_security_lab_project/
├── config/
├── notebooks/
│   └── Setup_SecurityLab_Data.py      # PySpark script creating messy Sales table
├── pipelines/
├── scripts/
│   ├── fabric_client.py               # Fabric REST API client with IPv4 fix
│   ├── deploy_notebook.py             # Notebook deployer
│   ├── update_and_run_notebook.py     # Executes PySpark job on Fabric
│   ├── deploy_semantic_model.py       # Deploys Direct Lake TMDL model
│   └── verify_environment.py          # End-to-end environment validation
├── semantic_models/
│   └── SecurityLab_Model.SemanticModel/ # Direct Lake TMDL model definition
├── verification_report.json           # Machine-readable validation payload
└── README.md
```

---

## Verifying the Environment
To re-run the verification test suite at any time:
```bash
python scripts/verify_environment.py
```
