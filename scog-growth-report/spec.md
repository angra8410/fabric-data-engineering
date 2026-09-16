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

### Opción 1: Base Scope (Power BI desde SharePoint / Excel Estandarizado + GIS) — [Presupuesto Fijo: ~15 Horas]
- **Restricción Presupuestaria Crítica:** Opción 1 cuenta con un presupuesto asignado estricto de **15 horas**.
- **Implicación Operativa:** Requiere que el 100% de la limpieza, consolidación y estructuración de los datos la realice el personal de SCOG antes de la entrega. El alcance de consultoría se limita estrictamente al modelado ágil en Power BI, creación de visuales clave y handoff básico.
- **Ingesta:** Plantillas Excel pre-estructuradas depositadas en SharePoint Online / OneDrive.
- **Transformación:** Power Query (M) ligero con reglas estándar de carga directa.
- **Modelo:** Modelo simplificado en estrella (Star Schema) rápido (Jurisdicción, Año, Vivienda, Población, Empleo).
- **GIS:** Mapa nativo (Shape Map o Azure Maps) utilizando capas geográficas existentes listas para consumo.
- **Entregables:** 1 archivo PBIX con páginas esenciales (Resumen Ejecutivo, Vivienda, Población/Empleo), checklist de actualización de 1 página y sesión de traspaso de 1 hora.

### Opción 2: Expanded Scope (Dataverse + Ingesta Automatizada Power Platform) — [Rango Reconciliado: 90 – 124 Horas]
- **Enfoque:** Arquitectura empresarial completa con ingesta automatizada, validación de esquemas, staging y base de datos relacional (Dataverse) para eliminar la dependencia del trabajo manual de SCOG a largo plazo. (MVP: 90 hrs / Completo: 124 hrs).

---

## 4. Criterios de Aceptación del Entregable
- [ ] Documento de opciones técnicas con estimación horaria realista por tarea.
- [ ] Tabla comparativa detallada (complejidad, mantenimiento, horas, licencias, riesgos).
- [ ] Recomendación fundamentada y balanceada (sin sobreventa de la Opción 2).
