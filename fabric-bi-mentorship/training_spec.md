# Especificaciones de Programa: Fabric & BI Engineering Mentorship Track

## 1. Resumen Ejecutivo y Objetivos
- **Problema de Negocio:** El mercado laboral para roles Senior de BI y Fabric (ej. DigX, BairesDev, CluePoints, Gorilla Logic, CuraLinc, Jane App) demanda profesionales integrales capaces de:
  1. Diseñar e implementar pipelines ETL/ELT confiables (PySpark / Delta Lake / Medallion en Fabric Lakehouse).
  2. Modelar datos analíticos de alta fidelidad bajo metodología dimensional Kimball (Star Schema).
  3. Formular lógica de negocio compleja y optimizada en DAX (comprensión profunda de contextos de evaluación y VertiPaq).
  4. Auditar, gobernar y optimizar modelos a escala empresarial utilizando **Tabular Editor 2** (Calculation Groups, BPA) y **DAX Studio** (Server Timings, Query Plans, Formula vs. Storage Engine).
  5. Consultar y validar calidad de datos mediante SQL avanzado y SARGable.
- **Propuesta Pedagógica:** Mentoría interactiva en formato "Role-Play" (Senior Lead Architect vs. Data Developer) basada en la skill `growme`. Progresión por capas: comenzando desde bases fundamentales en SQL y PySpark hasta escenarios complejos de nivel arquitectónico.
- **Entorno del Desarrollador:**
  - Local: Power BI Desktop, DAX Studio, Tabular Editor 2 instalados y operativos.
  - Cloud / Microsoft Fabric: Workspace `ws_dp600-prep` (`cfeefa92-730d-43b2-b2b1-9c46826d5807`), Carpeta `dp-600-smash-practice`.
  - Lakehouse Activo: `lh_practice_smash_interview` (`86204f05-6d46-4c76-a76d-9cb8a5fa5cb6`).
  - SQL Analytics Endpoint: `4kq2jhmt3otufjmisv75mkjoq4-sl5o5tynoozehmvrtrdie3kya4.datawarehouse.fabric.microsoft.com`.
  - Dominio y Modelo de Datos: **Credit Union / Financial Loan Portfolio Analytics**:
    - `dbo.dimbranch` (`BranchID`, `BranchName`, `Region`, `State`)
    - `dbo.dimdate` (`DateKey`, `FullDate`, `Year`, `Quarter`, `Month`, `MonthName`, `DayOfWeek`)
    - `dbo.dimloan` (`LoanKey`, `MemberKey`, `BranchID`, `LoanType`, `OriginalAmount`, `InterestRate`, `StartDate`)
    - `dbo.dimmember` (`MemberKey`, `MemberName`, `SSN`, `Email`, `CreditScore`, `DebtToIncomeRatio`)
    - `dbo.factdailyloanbalances` (`SnapshotKey`, `LoanKey`, `MemberKey`, `BranchID`, `DateKey`, `CurrentBalance`, `InterestAccrued`)
    - `dbo.factloantransactions` (`TransactionKey`, `LoanKey`, `MemberKey`, `BranchID`, `DateKey`, `TransactionType`, `TransactionAmount`)
    - `dbo.dimsecuritymapping` (`UserEmail`, `AssignedBranchID`, `RoleDescription`)

---

## 2. Matriz de Módulos y Competencias

### Módulo 1: SQL & Query Engineering (Desde Fundamentos hasta Avanzado)
- **Fase 1.1 (Fundamentos):** Proyecciones, alias explícitos, joins relacionales (`INNER`, `LEFT`, `CROSS`, `FULL OUTER`), filtrado SARGable (`WHERE` vs `HAVING`), manejo de valores `NULL` (`COALESCE`, `NULLIF`).
- **Fase 1.2 (Agregación & Agrupación):** `GROUP BY`, `HAVING`, funciones de agregación condicionales (`COUNT(CASE WHEN...)`), métricas clave.
- **Fase 1.3 (Expresiones de Tabla Común & Jerarquías):** CTEs legibles vs subconsultas, Self-Joins para jerarquías organizacionales (Empleado -> Manager).
- **Fase 1.4 (Window Functions & Analítica Estadística / Percentiles):**
  - Ranking & Offset: `ROW_NUMBER()`, `DENSE_RANK()`, `LEAD()`, `LAG()`, ventanas deslizantes `ROWS BETWEEN`.
  - **Distribución y Percentiles Multi-Motor:** Cálculo de medianas, cuartiles y percentiles continuos vs discretos (`PERCENTILE_CONT`, `PERCENTILE_DISC`, `NTILE`). Comparativa de implementación y limitaciones entre motores: SQL Server / T-SQL, SQLite (aproximaciones / window workarounds) vs PySpark / Fabric (`percentile_approx`, `expr('percentile_approx(...)')`).
- **Fase 1.5 (Performance Tuning, Índices & Execution Plans en Entorno Bancario):**
  - **Mecanismos de Almacenamiento & B-Trees:** Por qué los índices aceleran búsquedas (desmitificación: no es por el tipo de dato `INT` vs `VARCHAR`, sino por la estructura de salto del índice).
  - **Clustered vs. Non-Clustered Indexes:** Organización física de datos vs apuntadores de búsqueda secundaria.
  - **Lectura de Planes de Ejecución (SSMS & Spark Catalyst):** Identificación visual de cuellos de botella: *Index Seek* (salto directo) vs *Table Scan / Clustered Index Scan* (revisión exhaustiva fila por fila).
  - **SARGabilidad:** Anti-patrones que destruyen el uso de índices (funciones envolventes en columnas dentro de `WHERE`, conversiones de tipo implícitas, `LIKE '%...'`).
  - **Indexación en Joins & Estadísticas:** Impacto de missing indexes en columnas de unión y necesidad de mantenimiento de estadísticas (`UPDATE STATISTICS`).
- **Fase 1.6 (Seguridad, Gobernanza y Administración en Base de Datos Bancaria):**
  - **Jerarquía de Seguridad:** Logins (nivel instancia/servidor) vs. Users (nivel base de datos) vs. Service Principals / AAD en Fabric.
  - **Control de Acceso Basado en Roles (RBAC):** Roles predefinidos (`db_datareader`, `db_datawriter`, `db_owner`) vs roles de negocio personalizados.
  - **Permisos Granulares:** Sintaxis y efectos de `GRANT`, `REVOKE` y `DENY` a nivel de servidor, esquema, tabla y columna.
  - **Seguridad a Nivel de Fila (Row-Level Security - RLS):** Implementación de funciones predicado de seguridad y Security Policies en T-SQL / SQL Analytics Endpoint para segregar carteras de clientes según la sucursal del usuario autenticado.

### Módulo 2: Fabric Lakehouse & PySpark Engineering (Desde Fundamentos hasta Avanzado)
- **Fase 2.1 (Fundamentos PySpark):** DataFrames, proyecciones (`select`, `withColumn`), filtrado, transformaciones y esquemas (`StructType`).
- **Fase 2.2 (Arquitectura Medallion en Fabric):**
  - **Bronze:** Ingesta Raw sin pérdida, metadatos de auditoría (`_ingestion_timestamp`, `_source_file`).
  - **Silver:** Limpieza, deduplicación, validación de calidad de datos, tipado estricto, generación de llaves subrogadas (`xxhash64`).
  - **Gold:** Construcción de Data Marts dimensionales listos para consumo en Power BI.
- **Fase 2.3 (Delta Lake Avanzado, Hashing para CDC & SCD):**
  - Transacciones ACID y optimización Delta en Fabric (V-Order, Liquid Clustering / Optimize).
  - Concepto de **Hash Diff / Row Hash**: detección eficiente de cambios en tablas amplias evitando comparaciones columna por columna.
  - Hashing determinístico con `HASHBYTES('SHA2_256', ...)` en SQL y `F.sha2(F.concat_ws(...))` / `F.xxhash64()` en PySpark.
  - Manejo seguro de valores `NULL` y separadores para prevenir colisiones de hash.
  - Implementación de `MERGE INTO` para Upserts, SCD Tipo 1 y SCD Tipo 2 (Nuevos registros $\rightarrow$ Insert, Modificados $\rightarrow$ Update/Expire, Idénticos $\rightarrow$ No-Op).

### Módulo 3: Modelado Dimensional Kimball (Star Schema)
- **Fase 3.1:** Definición de granularidad atómica vs agrupada.
- **Fase 3.2:** Hechos (`fact_`) transaccionales, periódicos y sin hechos (*factless*).
- **Fase 3.3:** Dimensiones conformadas, dimensiones degeneradas, dimensiones de rol múltiple (*role-playing* como calendario) y manejo de relaciones muchos a muchos.
- **Fase 3.4:** Reglas de oro en Power BI: evitar relaciones bidireccionales y modelos copo de nieve (*snowflake*) innecesarios.

### Módulo 4: DAX & Capa Semántica (Desde Conceptos Core hasta Avanzado)
- **Fase 4.1:** Medidas implícitas vs explícitas, reglas de sintaxis estándar.
- **Fase 4.2:** Contexto de Fila (*Row Context*) vs Contexto de Filtro (*Filter Context*).
- **Fase 4.3:** Transición de Contexto (*Context Transition*) en calculadas y `CALCULATE`.
- **Fase 4.4:** Modificadores de `CALCULATE` (`REMOVEFILTERS`, `ALL`, `ALLEXCEPT`, `KEEPFILTERS`, `USERELATIONSHIP`).
- **Fase 4.5:** Time Intelligence personalizado y estándar (YTD, YoY, Moving Averages).
- **Fase 4.6:** Métricas semi-aditivas (Headcount/Inventario a fin de período).

### Módulo 5: Tabular Editor 2 (Gobernanza, Automatización y Conexión API / XMLA)
- **Fase 5.1:** Conexión remota a Microsoft Fabric / Power BI Premium vía **XMLA Endpoint** (`powerbi://api.powerbi.com/v1.0/myorg/WorkspaceName`) para administración directa del modelo semántico.
- **Fase 5.2 (Automatización con C# Scripting & TOM - Tabular Object Model):**
  - Automatización por script: creación masiva de medidas, formateo numérico y asignación de carpetas de despliegue (*Display Folders*).
  - Scripting avanzado para generar Grupos de Cálculo (*Calculation Groups*) automáticos (YTD, MTD, YoY, % YoY).
  - Manipulación directa del metadata BIM/TMSL y uso de Tabular Editor CLI en flujos de integración continua (CI/CD) y Fabric REST APIs.
- **Fase 5.3 (Gobernanza & Calidad):** Reglas de auditoría con Best Practice Analyzer (BPA) para detectar columnas no utilizadas, cardinalidades críticas, bidireccionalidad y malas prácticas DAX.

### Módulo 6: DAX Studio (Afinamiento y Rendimiento de Modelos)
- **Fase 6.1:** Conexión a modelos locales y remotos.
- **Fase 6.2:** Lectura de Server Timings: desglose de tiempos entre Formula Engine (FE - monohilo) y Storage Engine (SE - VertiPaq multihilo).
- **Fase 6.3:** Análisis de consultas xmSQL y reducción de materializaciones innecesarias.
- **Fase 6.4:** Optimización de medidas lentas para tiempos de respuesta sub-segundo.

---

## 3. Dinámica Operativa (Reglas de Interacción)
1. **Un reto a la vez:** El mentor plantea el problema de negocio, el esquema y los criterios de aceptación.
2. **Entrega de código:** El desarrollador escribe y comparte la solución en código real (SQL / PySpark / DAX).
3. **Senior PR Review:** El mentor realiza una revisión exhaustiva destacando aciertos, malas prácticas y estándares de la industria antes de avanzar.
