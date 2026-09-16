# Especificaciones de Aplicación: SCOG Annual Growth Monitoring Report

## 1. Resumen Ejecutivo y Objetivos
- **Cliente:** Skagit Council of Governments (SCOG) — Regional Planning Organization en Skagit County, Washington.
- **Problema de Negocio:** El proceso actual del *Annual Growth Monitoring Report* depende de la preparación manual y fragmentada en Excel de múltiples agencias/jurisdicciones, ensamblando tablas y gráficos estáticos para la adopción formal por la junta directiva (Board).
- **Propuesta de Solución:** Modernizar y migrar el reporte a Microsoft Power BI para dotar a SCOG de un reporte interactivo, auditable y mantenible año a año.
- **Entregable Inicial:** Documento Técnico de Opciones (*Technical Options Scoping Document*, Revisión 3) comparando la Opción 1 (Power BI con archivos Excel/GIS preparados por SCOG - Base Scope) frente a la Opción 2 (Arquitectura respaldada por Dataverse con proceso de ingesta anual - Expanded Scope).
- **Enfoque Primario:** *Decision Support Neutral & Balanced* — Presentar objetivamente ambas opciones técnicas según prioridades y restricciones de SCOG: Opción 1 como alcance base contratado plenamente autosuficiente, y Opción 2 como modernización de datos ampliada con gobernanza institucional.

---

## 2. Requerimientos Funcionales y Alcance

### RF-01: Dominio de Datos y Métricas de Crecimiento Regional
- **Dominios Temáticos:**
  - **Vivienda (Housing):** Permisos emitidos, tipos de vivienda (single-family, multi-family, ADUs), densidad, metas de crecimiento del GMA (Growth Management Act / Countywide Planning Policies).
  - **Población (Population):** Estimaciones anuales (OFM - Office of Financial Management del estado de WA), tasas de crecimiento histórico, proyecciones.
  - **Empleo (Employment):** Puestos de trabajo cubiertos (ESD - Employment Security Department), tendencias por sector/industria.
- **Entidades Jurisdiccionales (Skagit County):**
  - Ciudades/Pueblos: Anacortes, Burlington, Mount Vernon, Sedro-Woolley, Concrete, Hamilton, La Conner, Lyman.
  - Áreas no incorporadas y UGAs (Urban Growth Areas).

### RF-02: Doble Modo de Consumo (Interactivo vs. Reporte Oficial Adoptado)
- **Modo Interactivo:** Dashboard de 4 páginas en Power BI Service para exploración analítica por año, jurisdicción y métrica.
- **Modo Board-Adopted / Export:** Lienzos bloqueados en relación 16:9 con diseño de alto contraste y pie de página con metadatos dinámicos para exportación limpia a PDF del paquete formal para la Junta.

---

## 3. Comparativa de Enfoques (Opciones de Arquitectura - Revisión 3)

### Opción 1: Base Scope (Power BI desde SharePoint / Excel Estandarizado + GIS) — [55 – 97 Horas / Baseline 75 hrs]
- **Enfoque Base Contratado:** Estimado bottom-up a través de seis tareas:
  1. Discovery & Planning (6 / 8 / 10 hrs) — revisión del prototipo existente, archivos fuente y confirmación de esquema.
  2. Prototipo 2025 en curso (12 / 16 / 22 hrs) — finalización de modelo en estrella y vistas analíticas sobre datos de 2025 (work in progress; estado real a confirmar en Tarea 1).
  3. Reporte de Producción 2026 (18 / 24 / 30 hrs) — aplicación de datos 2026 y refinamiento visual para calidad Board/impresión.
  4. Documentación Técnica y Runbook de Actualización Anual (6 / 8 / 10 hrs).
  5. Capacitación y Handoff al Personal (5 / 7 / 9 hrs).
  6. Buffer de Contingencia (8 / 12 / 16 hrs) para derivas de esquema o ajustes de capas GIS.
- **Supuesto Arquitectónico Clave:** El prototipo 2025 y el reporte de producción 2026 comparten un modelo semántico y estructura de reporte unificados. Si SCOG requiere mantenerlos en archivos `.pbix` totalmente separados, se añadirán 10–15 horas.
- **Ingesta:** Plantillas Excel pre-estructuradas depositadas en SharePoint Online / OneDrive con verificación de integridad por fórmulas nativas (`TEXTJOIN`, `SUMIFS`, dropdowns) sin requerir macros.
- **Transformación:** Power Query (M) con tipado fuerte y detección estricta de inconsistencias de columnas.
- **Modelo:** Modelo en estrella formal (Star Schema) con dimensiones compartidas (`Dim_Jurisdiction`, `Dim_CalendarYear`, `Dim_UGA_Reference`) y tablas de hechos numéricas.
- **GIS:** Mapa nativo GA (**Azure Maps** o **ArcGIS Maps for Power BI**) descartando el preview inestable de Shape Map.

### Opción 2: Expanded Scope (Dataverse + Ingesta Automatizada Power Platform) — [110 – 150 Horas]
- **Enfoque:** Plataforma de datos ampliada con capa estructurada en Dataverse, ingesta automatizada de archivos vía SharePoint y flujos Power Query Dataflows / Power Automate, validación determinista de esquemas, staging y flujo de aprobación (`Draft` a `Board Adopted`). (MVP: 110 hrs / Completo: 150 hrs).
- **Desglose de Ocho Tareas (Revisión 3):**
  1. Discovery & Source File Schema Audit: 10 / 16 hrs
  2. Dataverse Environment & Entity Modeling: 16 / 20 hrs
  3. Annual Intake & SharePoint Ingestion Architecture: 18 / 22 hrs
  4. Dataflows / Power Automate ETL Implementation: 22 / 28 hrs
  5. Data Validation & Error Handling Pipelines: 12 / 18 hrs
  6. Power BI Semantic Model & Report Development: 18 / 22 hrs
  7. User Acceptance Testing & Historical Migration (10–15 años): 8 / 14 hrs
  8. Governance, Documentation & Admin Training: 6 / 10 hrs
- **Comparativa Operativa y ROI:** Reduce el mantenimiento manual anual de 20–40 hrs/año a 2–4 hrs/año de revisión por excepción, sentando bases para iniciativas regionales más amplias (modelos de transporte, inventarios de suelo edificable).

---

## 4. Criterios de Aceptación del Entregable
- [x] Documento de opciones técnicas con estimación horaria realista por tarea (Revisión 3).
- [x] Tabla comparativa detallada (complejidad, mantenimiento, horas, licencias, riesgos).
- [x] Recomendación estratégica neutral y balanceada que respalda la toma de decisiones sin sesgo ni sobreventa.
