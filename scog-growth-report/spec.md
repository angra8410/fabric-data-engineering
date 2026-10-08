# Especificaciones de Aplicación: SCOG Annual Growth Monitoring Report

## 1. Resumen Ejecutivo y Estado Contractual
- **Cliente:** Skagit Council of Governments (SCOG) — Regional Planning Organization en Skagit County, Washington.
- **Estado del Proyecto:** **APROBADO POR SCOG — EN FASE DE CONSTRUCCIÓN E IMPLEMENTACIÓN**
- **Opción Seleccionada:** **Opción 1 — Base Scope (Power BI desde SharePoint / Excel Estandarizado + GIS)**
- **Bolsa Contractual Aprobada:** **100 Horas Totales**
  - **Horas Ejecutadas (Scoping & Delivery Review):** 15 horas (completadas).
  - **Horas Restantes para Implementación:** 85 horas (activas).
- **Problema de Negocio:** El proceso actual del *Annual Growth Monitoring Report* depende de la preparación manual y fragmentada en Excel de múltiples agencias/jurisdicciones, ensamblando tablas y gráficos estáticos para la adopción formal por la junta directiva (Board).
- **Propuesta de Solución:** Modernizar y migrar el reporte a Microsoft Power BI para dotar a SCOG de un reporte interactivo, auditable y mantenible año a año, con lienzos optimizados para exportación formal a PDF/impresión de Junta.

---

## 2. Requerimientos Funcionales y Alcance (Opción 1)

### RF-01: Dominio de Datos y Métricas de Crecimiento Regional
- **Dominios Temáticos:**
  - **Vivienda (Housing):** Permisos emitidos, tipos de vivienda (single-family, multi-family, ADUs), densidad, metas de crecimiento del GMA (Growth Management Act / Countywide Planning Policies).
  - **Población (Population):** Estimaciones anuales (OFM - Office of Financial Management del estado de WA), tasas de crecimiento histórico, proyecciones.
  - **Empleo (Employment):** Puestos de trabajo cubiertos (ESD - Employment Security Department), tendencias por sector/industria.
- **Entidades Jurisdiccionales (Skagit County):**
  - Ciudades/Pueblos: Anacortes, Burlington, Mount Vernon, Sedro-Woolley, Concrete, Hamilton, La Conner, Lyman.
  - Áreas no incorporadas y UGAs (Urban Growth Areas).

### RF-02: Doble Modo de Consumo (Interactivo vs. Reporte Oficial Adoptado)
- **Modo Interactivo:** Dashboard de 4 páginas en Power BI Service para exploración analítica por año, jurisdicción y métrica:
  1. Executive Summary & Regional Dashboard
  2. Housing Deep-Dive
  3. Population & Employment Overview
  4. Jurisdictional Comparison & Spatial Mapping
- **Modo Board-Adopted / Export:** Lienzos bloqueados en relación 16:9 con diseño de alto contraste y pie de página con metadatos dinámicos para exportación limpia a PDF del paquete formal para la Junta.

### RF-03: Blindaje de Ingesta Excel (.xlsx) y Gobernanza Ligera
- Plantillas maestras pre-estructuradas en SharePoint Online / OneDrive.
- Fórmulas de validación nativas sin macros (TEXTJOIN para integridad de headers, SUMIFS para checksums históricos).
- Tipado estricto en Power Query (M) con Table.SelectColumns para detener la carga ante derivas de esquema.

---

## 3. Desglose de Horas y Control Presupuestario (85 Horas de Ejecución Restantes)

| Tarea de Implementación | Rango (Hrs) | Baseline (Hrs) | Horas Asignadas (Cap 85h) | Estado Actual |
| :--- | :---: | :---: | :---: | :--- |
| **0. Scoping Técnico & Delivery Review** | 15 | 15 | 15 | **COMPLETADO (15h devengadas)** |
| **1. Discovery & Planning** | 6 – 10 | 8 | 8 | **EN CURSO** |
| **2. Prototipo 2025 (in progress)** | 12 – 22 | 16 | 16 | Pendiente de auditoría T1 |
| **3. Reporte de Producción 2026** | 18 – 30 | 24 | 24 | Pendiente |
| **4. Documentación Técnica & Runbook** | 6 – 10 | 8 | 8 | Pendiente |
| **5. Capacitación & Handoff al Personal** | 5 – 9 | 7 | 7 | Pendiente |
| **6. Buffer de Contingencia & Ajustes** | 8 – 16 | 12 | 22 | Disponible (colchón de seguridad) |
| **TOTAL CONTRATO** | **55 – 97** | **75** | **100 (15h hechas + 85h rest.)** | **ACTIVO** |

---

## 4. Plan de Acción Inmediato: Tarea 1 (Discovery & Planning)
1. **Auditoría de Archivos Fuente SCOG:**
   - Inventariar las hojas de cálculo Excel históricas (Housing, OFM Population, ESD Employment).
   - Revisar el estado real del archivo .pbix del prototipo 2025 (conexiones existentes, medidas DAX, relaciones).
2. **Auditoría de Capas GIS:**
   - Inspeccionar límites municipales y capas UGA (Shapefile/GeoJSON) y compatibilidad con Azure Maps / ArcGIS Maps.
3. **Construcción de Plantillas Maestras Excel:**
   - Generar los layouts estándar con fórmulas de validación de encabezados y sumas de control.
4. **Validación del Modelo Star Schema:**
   - Confirmar tablas de dimensiones (Dim_Jurisdiction, Dim_CalendarYear, Dim_UGA_Reference) y tablas de hechos numéricas.
