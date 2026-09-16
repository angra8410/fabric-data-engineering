# Especificaciones de Aplicación: SCOG Annual Growth Monitoring Report

## 1. Resumen Ejecutivo y Objetivos
- **Cliente:** Skagit Council of Governments (SCOG) — Regional Planning Organization en Skagit County, Washington.
- **Problema de Negocio:** El proceso actual del *Annual Growth Monitoring Report* depende de la preparación manual y fragmentada en Excel de múltiples agencias/jurisdicciones, ensamblando tablas y gráficos estáticos para la adopción formal por la junta directiva (Board).
- **Propuesta de Solución:** Modernizar y migrar el reporte a Microsoft Power BI para dotar a SCOG de un reporte interactivo, auditable y mantenible año a año.
- **Entregable Inicial:** Documento Técnico de Opciones (*Technical Options Scoping Document*) comparando la Opción 1 (Power BI con archivos Excel/GIS preparados por SCOG - Base Scope) frente a la Opción 2 (Arquitectura respaldada por Dataverse con proceso de ingesta anual - Expanded Scope).
- **Enfoque Primario:** *The Simplest Road* — Priorizar simplicidad operativa, bajo costo de licenciamiento y máxima autonomía del equipo de SCOG sin sobreingeniería innecesaria.

---

## 2. Requerimientos Funcionales y Alcance

### RF-01: Dominio de Datos y Métricas de Crecimiento Regional
- **Dominios Temáticos:**
  - **Vivienda (Housing):** Permisos emitidos, tipos de vivienda (single-family, multi-family), densidad, metas de crecimiento del GMA (Growth Management Act).
  - **Población (Population):** Estimaciones anuales (OFM - Office of Financial Management del estado de WA), tasas de crecimiento histórico, proyecciones.
  - **Empleo (Employment):** Puestos de trabajo (ESD - Employment Security Department), tendencias por sector/industria.
- **Entidades Jurisdiccionales (Skagit County):**
  - Ciudades/Pueblos: Anacortes, Burlington, Mount Vernon, Sedro-Woolley, Concrete, Hamilton, La Conner, Lyman.
  - Áreas no incorporadas y UGAs (Urban Growth Areas).

### RF-02: Doble Modo de Consumo (Interactivo vs. Reporte Oficial Adoptado)
- **Modo Interactivo:** Dashboard en Power BI Service para exploración analítica por año, jurisdicción y métrica.
- **Modo Board-Adopted / Export:** Vistas o reportes paginados (Power BI Report Builder / vistas 16:9 aptas para PDF/impresión) que permitan congelar el reporte oficial anual adoptado por la junta.

---

## 3. Comparativa de Enfoques (Opciones de Arquitectura)

### Opción 1: Base Scope (Power BI desde SharePoint / Excel Estandarizado + GIS) — [Rango Reconciliado: 70 – 100 Horas / Baseline 75 hrs]
- **Clarificación Presupuestaria Confirmada (Guía de Aaron):** La cifra previa de **15 horas** correspondía exclusivamente a la tarifa contractual Skagit Consulting ↔ The Flock para la elaboración de este documento técnico de scoping, y no al presupuesto de construcción e implementación de la Opción 1 para SCOG. En la Revisión 2, la Opción 1 se estima bottom-up en un rango de **70 – 100 horas** (55 hrs low / 75 hrs baseline / 97 hrs high) distribuido en seis tareas formales.
- **Estructura de Seis Tareas:**
  1. Discovery & Planning (6 / 8 / 10 hrs)
  2. Prototipo 2025 en curso (12 / 16 / 22 hrs) — finalización de modelo en estrella y vistas analíticas sobre datos históricos.
  3. Reporte de Producción 2026 (18 / 24 / 30 hrs) — ingesta de año en curso y refinamiento visual para adopción de la Junta.
  4. Documentación Técnica y Runbook de Actualización (6 / 8 / 10 hrs).
  5. Capacitación y Handoff al Personal (5 / 7 / 9 hrs).
  6. Buffer de Contingencia (8 / 12 / 16 hrs) para derivas de esquema o ajustes GIS.
- **Supuesto Arquitectónico Clave:** El prototipo 2025 y el reporte de producción 2026 comparten un modelo semántico unificado. Si SCOG requiere mantenerlos en archivos `.pbix` separados e independientes, se añaden 10–15 horas.
- **Ingesta:** Plantillas Excel pre-estructuradas depositadas en SharePoint Online / OneDrive con verificación de integridad por fórmulas nativas (`TEXTJOIN`, `SUMIFS`).
- **Transformación:** Power Query (M) con tipado fuerte y detención limpia ante discrepancias de esquema.
- **Modelo:** Modelo en estrella formal (Star Schema) con dimensiones compartidas (`Dim_Jurisdiction`, `Dim_CalendarYear`, `Dim_UGA_Reference`) y hechos temáticos.
- **GIS:** Mapa nativo GA (**Azure Maps** o **ArcGIS Maps for Power BI**) descartando el preview de Shape Map.

### Opción 2: Expanded Scope (Dataverse + Ingesta Automatizada Power Platform) — [Rango Reconciliado: 90 – 124 Horas]
- **Enfoque:** Arquitectura empresarial completa con ingesta automatizada, validación de esquemas, staging y base de datos relacional (Dataverse) para eliminar la dependencia del trabajo manual de SCOG a largo plazo. (MVP: 90 hrs / Completo: 124 hrs).
- **Proximidad Relativa de Esfuerzo:** Con el nuevo baseline de la Opción 1 en 75 hrs, la Opción 2 MVP (90 hrs) representa una inversión inicial de solo ~20% adicional (15 hrs más), eliminando 20–40 hrs/año de esfuerzo manual recurrente.

---

## 4. Criterios de Aceptación del Entregable
- [ ] Documento de opciones técnicas con estimación horaria realista por tarea.
- [ ] Tabla comparativa detallada (complejidad, mantenimiento, horas, licencias, riesgos).
- [ ] Recomendación fundamentada y balanceada (sin sobreventa de la Opción 2).
