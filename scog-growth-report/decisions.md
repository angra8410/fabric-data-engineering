# Bitácora de Decisiones (Decisions Log): SCOG Growth Monitoring Report

## [ADR-001] Adopción de Estrategia Progresiva ("The Simplest Road First")
- **Fecha:** 2026-09-14
- **Estado:** Propuesto / En Evaluación
- **Contexto:** SCOG necesita un scoping técnico para decidir entre Opción 1 (Power BI con Excel/GIS preparados) y Opción 2 (Dataverse + Ingesta automatizada). La frecuencia de actualización es puramente anual y el volumen de datos regional es pequeño/moderado (~decenas de miles de filas acumuladas a lo largo de décadas).
- **Decisión Tomada:** Priorizar en la propuesta técnica una ruta base pragmática (Opción 1 robustecida con plantillas SharePoint) y posicionar la Opción 2 como una fase evolutiva modular (Add-on) en caso de que SCOG cuente con licencias M365 Business/Enterprise con Dataverse y desee gobernanza centralizada a largo plazo.
- **Alternativas Consideradas:**
  1. Forzar Opción 2 como requerimiento obligatorio inicial (Descartado: Riesgo de rechazo por costos de licencias Power Platform Premium y complejidad administrativa para un equipo de planificación pequeño).
  2. Opción 1 tradicional sin estandarización (Descartado: Riesgo alto de rotura de queries por cambio de nombres de columnas en Excel).
- **Consecuencias:** Se requiere diseñar la Opción 1 con modelos en estrella limpios y plantillas tabulares en Excel que puedan migrarse transparentemente a Dataverse en el futuro si SCOG lo aprueba.

---

## [ADR-002] Calibración de Alcance para Opción 1 con Presupuesto Fijo de 15 Horas
- **Fecha:** 2026-09-14
- **Estado:** Aprobado / Restricción Activa
- **Contexto:** El cliente / gerencia ha fijado un presupuesto estricto de **15 horas** para la Opción 1 (Base Scope). 15 horas es un presupuesto muy reducido que no permite retrabajo en limpieza de datos desestructurados, ni desarrollo de lógica compleja de transformación o pipelines ETL extensos.
- **Decisión Tomada:** 
  1. Diseñar el desglose de tareas de la Opción 1 con una suma exacta de 15 horas (con un rango de contingencia de 14-17 horas).
  2. Establecer como **supuesto contractual no negociable** que SCOG entrega archivos Excel 100% limpios, tabulares y normalizados según una plantilla predefinida. Cualquier necesidad de limpieza profunda de datos por parte del consultor consumirá horas fuera del presupuesto de 15 horas.
  3. Desglose estricto de las 15 horas:
     - Revisión de fuentes y alineación de esquema: **2 hrs**
     - Modelado de datos en Power BI & Power Query ligero: **3 hrs**
     - Desarrollo de Reporte & Visuales Clave (Housing, Population, Employment, Map): **6 hrs**
     - Pruebas de refresh, validación cruzada y ajuste de exportación PDF/impresión: **2 hrs**
     - Documentación de proceso de refresh anual (1-pager) y sesión de handoff: **2 hrs**
     - **Total: 15 horas**.
- **Consecuencias:** 
  - La propuesta para SCOG debe resaltar con total claridad qué incluye y qué NO incluye este paquete de 15 horas para evitar fricciones futuras de soporte y expectativas irreales.
  - La Opción 2 se presenta como el contraste natural donde la consultoría asume el trabajo pesado de ingeniería de datos y automatización (90-124 hrs).

---

## [ADR-003] Reconciliación de Rangos Horarios y Banderas de Riesgo de QA
- **Fecha:** 2026-09-14
- **Estado:** Aprobado
- **Contexto:** Revisión crítica del documento de scoping para entrega a la Junta Directiva de SCOG. Se detectaron discrepancias menores en los rangos citados para la Opción 2 (85-115 vs 90-124 hrs) y riesgos técnicos latentes en componentes de Power BI y licenciamiento.
- **Decisión Tomada:**
  1. **Reconciliación Unificada:** Fijar el rango de la Opción 2 en **90 – 124 horas** de forma consistente en todo el documento (MVP: 90 hrs, Completo: 124 hrs), respaldado por la sumatoria exacta de tareas.
  2. **Bandera de Riesgo en Visual de Mapas:** No dar por sentado el *Shape Map* (estado preview en Power BI) frente a *ArcGIS Maps for Power BI*. Exigir validación técnica previa antes de comprometer horas de desarrollo de mapas.
  3. **Bandera de Riesgo de Entrega (Opción 1):** Registrar explícitamente que la tarea de 6 horas para un reporte de 4 páginas (incluyendo mapa y deep-dive de vivienda) es la más vulnerable a sobrecostos si los datos de SCOG no están perfectamente limpios.
  4. **Costos de Licenciamiento:** Señalar los precios de Power Apps / Dataverse como aproximados y sujetos a confirmación con el administrador M365 de SCOG antes de presentar cifras firmes al Board.
- **Consecuencias:** Mayor solidez técnica y credibilidad comercial ante la gerencia y el cliente, eliminando inconsistencias numéricas y protegiendo el margen del proyecto.

---

## [ADR-004] Descarte de Shape Map y Actualización de Precios Power BI ($14/mo)
- **Fecha:** 2026-09-14
- **Estado:** Aprobado
- **Contexto:** 
  1. *Shape Map:* Reportes técnicos confirmaron que Shape Map continúa en estado "preview" y presenta un bug activo en Power BI Service donde el visual desaparece del panel de visualizaciones post-publicación. Como el flujo de SCOG depende de publicar en el Service y exportar el PDF oficial para el Board, este riesgo es inaceptable.
  2. *Precios de Power BI Pro:* Las listas de precios de Microsoft sufrieron un incremento efectivo en abril de 2025, elevando Power BI Pro de $10 a $14/usuario/mes y Premium Per User (PPU) de $20 a $24/usuario/mes.
- **Decisión Tomada:**
  1. Descartar definitivamente Shape Map de la arquitectura y adoptar **Azure Maps o ArcGIS Maps for Power BI** como el estándar por defecto para mapas de límites jurisdiccionales.
  2. Actualizar las referencias de precios en la Sección 3.5 a **$14/usuario/mes (Pro)** y **$24/usuario/mes (PPU)**, instruyendo validar descuentos gubernamentales (GCC/State agreement) con el administrador M365 de SCOG.
- **Consecuencias:** Se elimina un riesgo técnico severo de renderizado en la nube y se garantiza que el documento refleje datos financieros vigentes ante la Junta Directiva.

---

## [ADR-005] Verificación de Entitlements de Dataverse, Power Apps y Enfoque de Sensibilidad de Alcance
- **Fecha:** 2026-09-14
- **Estado:** Aprobado
- **Contexto:** Validación final antes de la presentación ante la Junta Directiva sobre las capacidades reales de almacenamiento de Dataverse, costos de Power Apps Premium y redacción de límites contractuales de alcance.
- **Decisión Tomada:**
  1. **Capacidad Base de Dataverse (20 GB):** Documentar formalmente que Microsoft otorga una asignación base a nivel de tenant de **20 GB de base de datos** al adquirir licencias Power Apps Premium. Para el volumen anual de SCOG (pocos MBs), el costo incremental por almacenamiento adicional de Dataverse ($40/GB/mes) es exactamente **$0**.
  2. **Licenciamiento Power Apps Premium ($20/mo):** Clarificar que solo los 1 o 2 administradores encargados de ejecutar y supervisar los flujos de ingesta en SharePoint/Dataverse requieren licencias de Power Apps Premium ($20/usuario/mes lista). Los consumidores y directores de SCOG que solo consultan el reporte en Power BI no requieren licencias de Power Apps.
  3. **Refactorización de Nota de Riesgo a Sensibilidad de Alcance:** En lugar de una advertencia informal interna que sugiera dudas de estimación, refactorizar la nota en la Sección 2.5 a una cláusula formal de "Sensibilidad de Alcance y Entrega", estableciendo que el reporte de 4 páginas se ceñirá estrictamente a plantillas visuales estándar para garantizar el cumplimiento dentro de las 15 horas presupuestadas.
  4. **Atribución de Estimaciones de Mantenimiento:** Etiquetar las estimaciones anuales (20-40 hrs vs 2-4 hrs) como métricas de referencia de consultoría (*benchmarks*) basadas en organismos de planificación regional homólogos, sujetas a calibración post-Año 1.
- **Consecuencias:** Coherencia total con la documentación oficial vigente de Microsoft, protección comercial de Skagit Consulting y presentación impecable ante la Junta Directiva de SCOG.
