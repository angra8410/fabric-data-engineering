# 💼 Data Engineering & Analytics Portfolio Monorepo
### Enterprise Medallion Pipelines on Microsoft Fabric & Recruiter-Facing GitHub Pages Web Hub

Bienvenido al monorepositorio principal de **Ingeniería de Datos & Analítica**. Este repositorio está estructurado bajo una arquitectura modular tipo *monorepo*, diseñada para escalar múltiples proyectos de datos independientes sobre la nube (**Microsoft Fabric**, **Delta Lake**, **PySpark**, **Direct Lake BI**) junto con un portal web interactivo de portafolio alojado en **GitHub Pages** (carga instantánea sub-segundo, sin cold starts).

---

## 🌟 Proyectos Destacados en el Monorepositorio

| Proyecto | Descripción | Stack Tecnológico | Estado ALM & Deployment |
| :--- | :--- | :--- | :--- |
| [**`velykapet_project`**](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/velykapet_project/README.md) | Plataforma de Datos E-Commerce & POS con Arquitectura Medallion en Microsoft Fabric (16 Tablas Bronze ➔ Silver ➔ Gold Data Warehouse & Bot de Sales por WhatsApp). | PySpark, Delta Lake, Fabric DataPipelines, Power BI | 🟢 Desplegado en DEV, TEST y PROD via `pl_deployment_velykapet` |
| [**`dane_employment_project`**](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/dane_employment_project/README.md) | Plataforma de Análisis de Mercado Laboral y Empleo en Colombia (2004 - 2026) sobre microdatos oficiales de la GEIH del DANE. | PySpark, Delta Lake, Fabric Medallion, Plotly | 🟢 Desplegado en Fabric & Integrado en Portafolio Hub |
| [**`DP700-Contoso_Dev`**](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/DP700-Contoso_Dev) | Data Warehouse Enterprise con Data Pipelines y Semantic Models en modo Direct Lake para respuesta DAX de <50ms. | Microsoft Fabric, Direct Lake, OneLake, Data Factory | 🟢 Desplegado en Workspace Fabric |
| [**`portfolio_site`**](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/portfolio_site/index.html) | **Recruiter-Facing Static Web Portfolio Hub** (Soporta múltiples reportes Power BI, entornos DEV/PROD e inspector PySpark). | HTML5, CSS3, JavaScript, GitHub Pages | 🌐 En Ejecución Live ([GitHub Pages Link](https://angra8410.github.io/fabric-data-engineering/)) |

---

## 🌐 Live Portfolio & Entornos GitHub Pages

- 🟢 **PROD Environment**: [`https://angra8410.github.io/fabric-data-engineering/`](https://angra8410.github.io/fabric-data-engineering/) (Despliegue automático desde rama `main`)
- 🟡 **DEV Environment**: [`https://angra8410.github.io/fabric-data-engineering/dev/`](https://angra8410.github.io/fabric-data-engineering/) (Despliegue de staging desde rama `dev`)

### ⚡ Características Principales del Web Portfolio:
1. **Sub-second Load**: Carga instantánea desde CDN global de GitHub Pages sin esperas de 10-30s.
2. **Multi-Report Power BI Hub**: Selector dinámico para alojar **múltiples reportes** por proyecto desde [`portfolio_site/reports_config.js`](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/portfolio_site/reports_config.js).
3. **Inspector de Código PySpark**: Visualizador interactivo de notebooks reales de Fabric (`nb_velykapet_master_medallion`, etc.).
4. **Visualizador Medallion**: Inspección detallada de tablas Bronze (🟤), Silver (⚪) y Gold (🟡).
5. **Selector DEV / PROD**: Botón de alternancia en cabecera para previsualizar endpoints de desarrollo y producción.

---

## ⚙️ Configuración de Reportes Power BI (`reports_config.js`)

Para añadir o modificar reportes Power BI para cualquier proyecto:

```javascript
// Editar portfolio_site/reports_config.js
{
  id: "v_sales_pos_prod",
  title: "📊 Velykapet Executive Revenue & Sales POS",
  embedUrl: "https://app.powerbi.com/reportEmbed?reportId=TU_REPORT_ID...",
  description: "Descripción del reporte..."
}
```

---

## 🏛️ Estructura del Monorepositorio

```text
proyectos-data-engineering/
├── .github/workflows/
│   └── deploy-pages.yml           <-- CI/CD GitHub Actions para GitHub Pages (DEV & PROD)
├── portfolio_site/                <-- Recruiter-Facing Static Web Portfolio (GitHub Pages Target)
│   ├── index.html                 <-- Single Page Application (SPA)
│   ├── styles.css                 <-- Modern Dark Glassmorphic Design System
│   ├── app.js                     <-- Motor interactivo de selector de proyectos/reportes
│   └── reports_config.js          <-- Configuración modular de reportes Power BI & notebooks
├── velykapet-pos-storefront/      <-- Definiciones de ítems y Lakehouses de Fabric
├── velykapet_project/             <-- Proyecto 1: Velykapet Retail Data Engineering Platform
├── dane_employment_project/       <-- Proyecto 2: DANE Colombia Labor Market Analytics (2004-2026)
├── DP700-Contoso_Dev/             <-- Proyecto 3: Contoso Direct Lake Fabric Analytics
├── AdventureWorks/                <-- Workspace items de Microsoft Fabric
├── README.md                      <-- Documentación Principal
```

---

## 💻 Visualización Local

Para previsualizar la página web localmente antes de enviar a GitHub:

```bash
# Opción 1: Usando Python
python -m http.server 8080 --directory portfolio_site

# Opción 2: Usando Node npx
npx serve portfolio_site
```
Navega en tu navegador a `http://localhost:8080`.
