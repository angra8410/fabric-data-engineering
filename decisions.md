# Bitácora de Decisiones (Decisions Log) - Datos Abiertos Colombia

## [ADR-001] Adopción de Estrategia de Ingesta SODA (Opción A: Cliente/Extractor Resiliente)
- **Fecha:** 2026-09-02
- **Estado:** Aprobado
- **Contexto:** Para conectar con Datos Abiertos de Colombia (`datos.gov.co`), se evaluó si crear una API intermedia propia (wrapper/microservicio) o un motor de extracción directo hacia el Lakehouse. El usuario confirmó que se requiere un extractor robusto (Opción A) enfocado en consumir la API SODA pública evitando caídas.
- **Decisión Tomada:** Desarrollar un cliente extractor en Python/PySpark que interactúe directamente con los endpoints SODA de Socrata, permitiendo orquestación nativa dentro de Microsoft Fabric.
- **Alternativas Consideradas:** 
  - *Microservicio API intermedio (FastAPI/Express):* Descartado en esta etapa inicial por añadir complejidad y capas innecesarias de hosting cuando el destino final de los datos analíticos es el Lakehouse.
- **Consecuencias:** Menor sobrecarga de infraestructura, integración directa con el almacenamiento Lakehouse y facilidad de agendamiento nativo en Fabric.

---

## [ADR-002] Destino de Almacenamiento Independiente en Fabric (`ws-datos-abiertos-colombia` / `datos_abiertos_lh_dev`)
- **Fecha:** 2026-09-02
- **Estado:** Aprobado
- **Contexto:** El proyecto requiere almacenar un volumen significativo de registros de manera aislada de los entornos existentes de Velykapet o DANE. En el tenant de Microsoft Fabric se definió el workspace `ws-datos-abiertos-colombia` con el Lakehouse `datos_abiertos_lh_dev`.
- **Decisión Tomada:** Crear la estructura de artefactos correspondiente a `ws-datos-abiertos-colombia` en el repositorio, asegurando que las tablas aterrizadas sean formato Delta Lake con particionamiento y columnas de auditoría.
- **Alternativas Consideradas:**
  - Reutilizar lakehouses existentes (`ws-data-eng-dev`): Descartado para mantener gobernanza, límites de consumo y separación de dominios de negocio.
- **Consecuencias:** Claridad de gobernanza, independencia de costos y posibilidad de escalar a pipelines Silver y Gold dedicados en el futuro.

---

## [ADR-003] Paginación por Lotes y Control Anticaídas (Rate Limiting y Exponential Backoff)
- **Fecha:** 2026-09-02
- **Estado:** Aprobado
- **Contexto:** Socrata impone límites de velocidad y cuotas por IP/App-Token. Descargas masivas continuas provocan bloqueos HTTP 429 ("Too Many Requests") o abortos de socket por timeout.
- **Decisión Tomada:** Implementar paginación en lotes con `$limit` (10,000 registros por defecto) y `$offset`, acompañada de pausas deliberadas (*throttling*) entre llamadas y un decorador/manejador de reintentos con *Exponential Backoff*.
- **Alternativas Consideradas:**
  - Descargas de archivos completos CSV/JSON planos: No viable para datasets masivos o actualizaciones diarias incrementales.
- **Consecuencias:** Ingesta predecible, resiliente y continua, apta para ejecutarse desatendida en schedules diarios.

---

## [ADR-004] Flexibilidad Multi-Dataset mediante Identificador SODA de 4x4
- **Fecha:** 2026-09-02
- **Estado:** Aprobado
- **Contexto:** El usuario indicó que aún no tiene un dataset específico fijado, por lo que el sistema no debe quedar acoplado a una sola estructura o esquema rígido.
- **Decisión Tomada:** Diseñar el cliente SODA y el notebook para aceptar el `dataset_id` como parámetro, permitiendo extraer contratos SECOP, compras públicas, datos de salud o cualquier otro dataset público de `datos.gov.co` con la misma lógica subyacente.
- **Alternativas Consideradas:**
  - Hardcodear esquemas fijos: Descartado por limitar la escalabilidad del proyecto.
- **Consecuencias:** Máxima reutilización y extensibilidad del código dentro del ecosistema de Datos Abiertos.

---

## [ADR-005] Adopción de Modelo Dimensional Estrella con Surrogate Keys Numéricas (BIGINT / xxhash64)
- **Fecha:** 2026-09-03
- **Estado:** Aprobado
- **Contexto:** Transformar 6M de contratos crudos en una estructura analítica. Se evaluó el uso de Natural Keys vs Surrogate Keys de tipo texto (SHA-256) vs Surrogate Keys numéricas (BIGINT).
- **Decisión Tomada:** Implementar un Modelo Dimensional Estrella (`fact_contratos`, `dim_entidades`, `dim_proveedores`, `dim_geografia`) utilizando **Surrogate Keys numéricas de 64 bits (`BIGINT`) generadas determinísticamente mediante `F.xxhash64()`**.
- **Alternativas Consideradas:**
  - *Natural Keys directas:* Descartadas por inconsistencias en los datos origen (NITs nulos, consorcios sin identificación única, llaves compuestas de texto).
  - *Hashes String SHA-256 (64 caracteres):* Descartados para las relaciones porque ocupan excesiva memoria en el diccionario VertiPaq de Power BI / Direct Lake.
  - *IDs Autoincrementales centralizados:* Descartados por requerir bloqueos de secuencia en cargas incrementales distribuidas.
- **Consecuencias:** Máxima velocidad de compresión y filtrado en Power BI / Direct Lake (8 bytes por llave vs 64 bytes de texto), total independencia de secuencias y determinismo 100% en cargas diarias incrementales.


---

## [ADR-006] Creación de Lakehouse Silver Dedicado (`datos_abiertos_silver_lh_dev`)
- **Fecha:** 2026-09-03
- **Estado:** Aprobado
- **Contexto:** Definir la ubicación física de las tablas Silver.
- **Decisión Tomada:** Aprovisionar un nuevo Lakehouse en Microsoft Fabric (`datos_abiertos_silver_lh_dev`) para segregar estrictamente la capa Bronze (cruda) de la capa Silver (curada/dimensional).
- **Alternativas Consideradas:**
  - Almacenar todo en `datos_abiertos_lh_dev`: Descartado para mantener gobernanza limpia de la arquitectura Medallion.
- **Consecuencias:** Clara segregación de permisos, ciclo de vida independiente y mantenimiento limpio.

---

## [ADR-007] Tratamiento de Cuantías Cero y Columnas Enriquecidas de Negocio
- **Fecha:** 2026-09-03
- **Estado:** Aprobado
- **Contexto:** Manejo de contratos con valor <= 0 o nulo y enriquecimiento de métricas operativas.
- **Decisión Tomada:** Conservar todos los registros con bandera booleana `es_cuantia_cero = True`, calcular duración en días (`duracion_dias`), particiones temporales (`anno_firma`, `mes_firma`) y segmentación por `rango_cuantia` (Mínima, Menor, Mayor y Megacontratos).
- **Alternativas Consideradas:**
  - Eliminar contratos sin valor: Descartado porque distorsiona el conteo total de procesos estatales ejecutados.
- **Consecuencias:** Auditoría 100% fiel a los 6M de contratos con capacidad de excluir montos cero en medidas agregadas.

