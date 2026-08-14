# 💼 Data Engineering & Analytics Portfolio Monorepo
### Enterprise Medallion Pipelines on Microsoft Fabric & Interactive Multi-Project Streamlit Hub

Bienvenido al monorepositorio principal de **Ingeniería de Datos & Analítica**. Este repositorio está estructurado bajo una arquitectura modular tipo *monorepo*, diseñada para escalar múltiples proyectos de datos independientes sobre la nube (**Microsoft Fabric**, **Delta Lake**, **PySpark**) junto con un portal web interactivo de portafolio en **Streamlit**.

---

## 🌟 Proyectos Destacados en el Monorepositorio

| Proyecto | Descripción | Stack Tecnológico | Estado ALM & Deployment |
| :--- | :--- | :--- | :--- |
| [**`velykapet_project`**](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/velykapet_project/README.md) | Plataforma de Datos E-Commerce & POS con Arquitectura Medallion en Microsoft Fabric (16 Tablas Bronze ➔ Silver ➔ Gold Data Warehouse & Bot de Sales por WhatsApp). | PySpark, Delta Lake, Fabric DataPipelines, Streamlit | 🟢 Desplegado en DEV, TEST y PROD via `pl_deployment_velykapet` |
| [**`dane_employment_project`**](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/dane_employment_project/README.md) | Plataforma de Análisis de Mercado Laboral y Empleo en Colombia (2004 - 2026) sobre microdatos oficiales de la GEIH del DANE. | PySpark, Delta Lake, Fabric Medallion, Plotly | 🟢 Desplegado en Fabric & Integrado en Portafolio Hub |
| [**`portfolio_app`**](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/portfolio_app/app.py) | **Multi-Project Data Engineering Portfolio Hub** (Permite alternar interactivamente entre proyectos). | Python, Streamlit, Plotly, Mermaid | 🌐 En Ejecución Live ([Streamlit Cloud Link](https://fabric-data-engineering-3xtvkaywnsgusarg5ssrtz.streamlit.app)) |

---

## 🏛️ Arquitectura General del Monorepositorio

```text
proyectos-data-engineering/
├── portfolio_app/                 <-- Multi-Project Streamlit Hub (Navegador de Proyectos)
│   ├── app.py                     <-- Código fuente del Hub con selector de proyectos
│   └── requirements.txt
├── velykapet_project/             <-- Proyecto 1: Velykapet Retail Data Engineering Platform
│   ├── config/
│   ├── notebooks/                 <-- PySpark (Bronze, Silver, Gold y Master)
│   ├── pipelines/
│   └── README.md
├── dane_employment_project/       <-- Proyecto 2: DANE Colombia Labor Market Analytics (2004-2026)
│   └── README.md
├── create_project.py             <-- CLI Scaffolding Tool para nuevos proyectos
└── README.md                     <-- Documentación Principal
```

---

## 🌐 Live Web Portal
- 🔗 **Streamlit Community Cloud Link**: [https://fabric-data-engineering-3xtvkaywnsgusarg5ssrtz.streamlit.app](https://fabric-data-engineering-3xtvkaywnsgusarg5ssrtz.streamlit.app)
