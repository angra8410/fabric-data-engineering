# Especificaciones de Aplicación: Datos Abiertos Colombia (`datos-abiertos-colombia`)

## 1. Resumen Ejecutivo y Objetivos
- **Problema de Negocio:** El portal de Datos Abiertos de Colombia (`datos.gov.co`) alberga millones de registros públicos cruciales para análisis gubernamental, económico y social. La descarga manual o masiva sin control genera cuellos de botella, bloqueos por tasa de peticiones (HTTP 429) y desconexiones.
- **Propuesta de Solución:** Desarrollar un motor de extracción e ingesta modular en Python/PySpark que consuma la API SODA (Socrata Open Data API), maneje paginación por lotes tolerante a fallos, respete los límites de velocidad del API para evitar caídas y sincronice automáticamente de forma diaria incremental hacia el Lakehouse dedicado `datos_abiertos_lh_dev` en el workspace `ws-datos-abiertos-colombia` de Microsoft Fabric.
- **Usuarios / Roles Involucrados:** Ingenieros de datos, analistas de políticas públicas y científicos de datos que requieren datos gubernamentales normalizados y actualizados diariamente.

---

## 2. Requerimientos Funcionales

### RF-01: Cliente Modular Socrata SODA API
- **Endpoint Principal Configurado:** `https://www.datos.gov.co/resource/jbjy-vk9h.json` (SECOP II - Contratos Electrónicos).
- Parámetros configurables: `dataset_id` (por defecto `jbjy-vk9h`, adaptable a cualquier dataset de 4x4 de `datos.gov.co`), `$limit`, `$offset`, `$where`, `$order`.
- Soporte opcional y seguro para `X-App-Token` (mediante variables de entorno o parámetros seguros) para maximizar la cuota de peticiones sin bloqueos.

### RF-02: Estrategia Anticaídas y Control de Tasa (Rate Limiting)
- Paginación automática en bloques de tamaño configurable (ej. lotes de 10,000 o 25,000 registros).
- Introducción de pausas (*throttling delays*) entre peticiones sucesivas para evitar saturación de la API de Socrata.
- Manejo de reintentos con *Exponential Backoff* ante respuestas HTTP 429 (Too Many Requests), 500 o fallos de red transitorios.

### RF-03: Sincronización Automática Diaria e Incremental
- Mecanismo de seguimiento de marca de agua (*watermark* o fecha de última actualización) para extraer solo los registros creados o modificados desde la última ejecución diaria.
- Opción de carga completa inicial (*Initial Full Load*) y cargas diarias incrementales (*Daily Delta Load*).

### RF-04: Aterrizaje en Lakehouse de Microsoft Fabric (`datos_abiertos_lh_dev`)
- Almacenamiento en capa Bronze / Raw del Lakehouse `datos_abiertos_lh_dev` en formato nativo **Delta Lake** o **Parquet**.
- Adición de columnas de auditoría y linaje:
  - `_ingestion_timestamp`: Marca temporal UTC de la ingesta.
  - `_source_dataset_id`: Identificador del dataset origen.
  - `_batch_id`: Identificador único de la corrida.

### RF-05: Empaquetado para Orquestación en Fabric
- Estructuración del código en un Fabric Notebook (`nb_bronze_ingest_secop.Notebook`) y script de utilidad reproducible, agendado en Microsoft Fabric.

---

## 3. Especificaciones de la Capa Silver (Modelo Dimensional Estrella)

### RF-06: Lakehouse Silver Dedicado en Fabric (`datos_abiertos_silver_lh_dev`)
- Creación y vinculación de un Lakehouse independiente en `ws-datos-abiertos-colombia` exclusivo para la capa curada Silver, manteniendo la separación física de capas Bronze y Silver.
- Lectura de origen desde `datos_abiertos_lh_dev.bronze_secop_contratos` (6,013,832 registros).

### RF-07: Modelo Dimensional Estrella (Star Schema)
Estructuración en tablas Delta normalizadas y optimizadas para Power BI:
1. **`fact_contratos`:**
   - Granularidad: 1 fila por contrato público.
   - Claves foráneas: `id_entidad_sk`, `id_proveedor_sk`, `id_geografia_sk`.
   - Métricas: `valor_contrato`, `valor_pago_adelantado`, `valor_facturado`, `valor_pagado`, `valor_pendiente_pago`, `duracion_dias`.
   - Banderas: `es_cuantia_cero` (booleano para valores <= 0 o nulos).
   - Dimensiones degeneradas: `id_contrato`, `proceso_compra`, `estado_contrato`, `tipo_contrato`, `modalidad_contratacion`, `rango_cuantia`, `anno_firma`, `mes_firma`.

2. **`dim_entidades`:**
   - Granularidad: Entidad estatal única.
   - Clave primaria subrogada: `id_entidad_sk` (hash MD5/SHA de NIT o nombre).
   - Atributos: `nit_entidad`, `nombre_entidad`, `orden` (Nacional/Territorial), `sector`, `rama`, `entidad_centralizada`.

3. **`dim_proveedores`:**
   - Granularidad: Contratista o proveedor adjudicado único.
   - Clave primaria subrogada: `id_proveedor_sk` (hash de tipo y número de identificación).
   - Atributos: `tipo_documento_contratista`, `identificacion_contratista`, `razon_social_proveedor`, `representante_legal`, `genero_representante_legal`.

4. **`dim_geografia`:**
   - Granularidad: Municipio / Departamento de ejecución.
   - Clave primaria subrogada: `id_geografia_sk`.
   - Atributos: `departamento` (normalizado en mayúsculas sin tildes), `ciudad` (normalizado), `localizacion`.

### RF-08: Reglas de Transformación y Limpieza (Data Cleaning)
- **Valores Monetarios:** Casteo seguro a tipo numérico `Double`/`Decimal(18,2)`. Valores nulos o <= 0 se preservan con `es_cuantia_cero = True`.
- **Parseo de Fechas:** Conversión de cadenas ISO a tipo `Date`/`Timestamp` (`fecha_firma`, `fecha_inicio`, `fecha_fin`).
- **Columnas Calculadas de Negocio:**
  - `duracion_dias`: `datediff(fecha_fin_contrato, fecha_inicio_contrato)`.
  - `anno_firma`: `year(fecha_firma)`.
  - `mes_firma`: `month(fecha_firma)`.
  - `rango_cuantia`: Clasificación de montos:
    - *Mínima Cuantía:* < $50,000,000 COP
    - *Menor Cuantía:* $50,000,000 COP - $500,000,000 COP
    - *Mayor Cuantía:* $500,000,000 COP - $5,000,000,000 COP
# Especificaciones de Aplicación: Datos Abiertos Colombia (`datos-abiertos-colombia`)

## 1. Resumen Ejecutivo y Objetivos
- **Problema de Negocio:** El portal de Datos Abiertos de Colombia (`datos.gov.co`) alberga millones de registros públicos cruciales para análisis gubernamental, económico y social. La descarga manual o masiva sin control genera cuellos de botella, bloqueos por tasa de peticiones (HTTP 429) y desconexiones.
- **Propuesta de Solución:** Desarrollar un motor de extracción e ingesta modular en Python/PySpark que consuma la API SODA (Socrata Open Data API), maneje paginación por lotes tolerante a fallos, respete los límites de velocidad del API para evitar caídas y sincronice automáticamente de forma diaria incremental hacia el Lakehouse dedicado `datos_abiertos_lh_dev` en el workspace `ws-datos-abiertos-colombia` de Microsoft Fabric.
- **Usuarios / Roles Involucrados:** Ingenieros de datos, analistas de políticas públicas y científicos de datos que requieren datos gubernamentales normalizados y actualizados diariamente.

---

## 2. Requerimientos Funcionales

### RF-01: Cliente Modular Socrata SODA API
- **Endpoint Principal Configurado:** `https://www.datos.gov.co/resource/jbjy-vk9h.json` (SECOP II - Contratos Electrónicos).
- Parámetros configurables: `dataset_id` (por defecto `jbjy-vk9h`, adaptable a cualquier dataset de 4x4 de `datos.gov.co`), `$limit`, `$offset`, `$where`, `$order`.
- Soporte opcional y seguro para `X-App-Token` (mediante variables de entorno o parámetros seguros) para maximizar la cuota de peticiones sin bloqueos.

### RF-02: Estrategia Anticaídas y Control de Tasa (Rate Limiting)
- Paginación automática en bloques de tamaño configurable (ej. lotes de 10,000 o 25,000 registros).
- Introducción de pausas (*throttling delays*) entre peticiones sucesivas para evitar saturación de la API de Socrata.
- Manejo de reintentos con *Exponential Backoff* ante respuestas HTTP 429 (Too Many Requests), 500 o fallos de red transitorios.

### RF-03: Sincronización Automática Diaria e Incremental
- Mecanismo de seguimiento de marca de agua (*watermark* o fecha de última actualización) para extraer solo los registros creados o modificados desde la última ejecución diaria.
- Opción de carga completa inicial (*Initial Full Load*) y cargas diarias incrementales (*Daily Delta Load*).

### RF-04: Aterrizaje en Lakehouse de Microsoft Fabric (`datos_abiertos_lh_dev`)
- Almacenamiento en capa Bronze / Raw del Lakehouse `datos_abiertos_lh_dev` en formato nativo **Delta Lake** o **Parquet**.
- Adición de columnas de auditoría y linaje:
  - `_ingestion_timestamp`: Marca temporal UTC de la ingesta.
  - `_source_dataset_id`: Identificador del dataset origen.
  - `_batch_id`: Identificador único de la corrida.

### RF-05: Empaquetado para Orquestación en Fabric
- Estructuración del código en un Fabric Notebook (`nb_bronze_ingest_secop.Notebook`) y script de utilidad reproducible, agendado en Microsoft Fabric.

---

## 3. Especificaciones de la Capa Silver (Modelo Dimensional Estrella)

### RF-06: Lakehouse Silver Dedicado en Fabric (`datos_abiertos_silver_lh_dev`)
- Creación y vinculación de un Lakehouse independiente en `ws-datos-abiertos-colombia` exclusivo para la capa curada Silver, manteniendo la separación física de capas Bronze y Silver.
- Lectura de origen desde `datos_abiertos_lh_dev.bronze_secop_contratos` (6,013,832 registros).

### RF-07: Modelo Dimensional Estrella (Star Schema)
Estructuración en tablas Delta normalizadas y optimizadas para Power BI:
1. **`fact_contratos`:**
   - Granularidad: 1 fila por contrato público.
   - Claves foráneas: `id_entidad_sk`, `id_proveedor_sk`, `id_geografia_sk`.
   - Métricas: `valor_contrato`, `valor_pago_adelantado`, `valor_facturado`, `valor_pagado`, `valor_pendiente_pago`, `duracion_dias`.
   - Banderas: `es_cuantia_cero` (booleano para valores <= 0 o nulos).
   - Dimensiones degeneradas: `id_contrato`, `proceso_compra`, `estado_contrato`, `tipo_contrato`, `modalidad_contratacion`, `rango_cuantia`, `anno_firma`, `mes_firma`.

2. **`dim_entidades`:**
   - Granularidad: Entidad estatal única.
   - Clave primaria subrogada: `id_entidad_sk` (hash MD5/SHA de NIT o nombre).
   - Atributos: `nit_entidad`, `nombre_entidad`, `orden` (Nacional/Territorial), `sector`, `rama`, `entidad_centralizada`.

3. **`dim_proveedores`:**
   - Granularidad: Contratista o proveedor adjudicado único.
   - Clave primaria subrogada: `id_proveedor_sk` (hash de tipo y número de identificación).
   - Atributos: `tipo_documento_contratista`, `identificacion_contratista`, `razon_social_proveedor`, `representante_legal`, `genero_representante_legal`.

4. **`dim_geografia`:**
   - Granularidad: Municipio / Departamento de ejecución.
   - Clave primaria subrogada: `id_geografia_sk`.
   - Atributos: `departamento` (normalizado en mayúsculas sin tildes), `ciudad` (normalizado), `localizacion`.

### RF-08: Reglas de Transformación y Limpieza (Data Cleaning)
- **Valores Monetarios:** Casteo seguro a tipo numérico `Double`/`Decimal(18,2)`. Valores nulos o <= 0 se preservan con `es_cuantia_cero = True`.
- **Parseo de Fechas:** Conversión de cadenas ISO a tipo `Date`/`Timestamp` (`fecha_firma`, `fecha_inicio`, `fecha_fin`).
- **Columnas Calculadas de Negocio:**
  - `duracion_dias`: `datediff(fecha_fin_contrato, fecha_inicio_contrato)`.
  - `anno_firma`: `year(fecha_firma)`.
  - `mes_firma`: `month(fecha_firma)`.
  - `rango_cuantia`: Clasificación de montos:
    - *Mínima Cuantía:* < $50,000,000 COP
    - *Menor Cuantía:* $50,000,000 COP - $500,000,000 COP
    - *Mayor Cuantía:* $500,000,000 COP - $5,000,000,000 COP
    - *Megacontratos / Licitación Masiva:* > $5,000,000,000 COP
    - *Sin Cuantía Definida:* Si `es_cuantia_cero = True`
- **Cobertura de Estados:** Conservar el 100% de estados históricos (Borrador, En ejecución, Celebrado, Liquidado, etc.).

---

## 4. Criterios de Aceptación
- [x] Módulo/Cliente SODA implementado con soporte para paginación por lotes y SoQL (`datos_abiertos/soda_client.py`).
- [x] Implementado control de throttling y reintentos exponenciales contra bloqueos y caídas.
- [x] Estructurado el espacio de trabajo local correspondiente a `ws-datos-abiertos-colombia` con el Lakehouse `datos_abiertos_lh_dev`.
- [x] Creado el Notebook de ingesta Bronze compatible con Microsoft Fabric (`nb_bronze_ingest_secop.Notebook`).
- [x] Verificación de descarga y persistencia con el dataset `jbjy-vk9h` de `datos.gov.co`.
- [x] **Hito Bronze:** Ingesta del 100.00% del dataset SECOP II completada exitosamente en el Lakehouse (`6,013,832 / 6,013,832` registros).
- [x] **Hito Silver (Aprovisionamiento):** Creación y aprovisionamiento del nuevo Lakehouse Silver dedicado `datos_abiertos_silver_lh_dev` en Fabric.
- [x] **Hito Silver (Despliegue y Ejecución):** Implementación y ejecución del Notebook PySpark `nb_silver_transform_secop.Notebook` (13 de 13 Spark jobs exitosos en 5.9s).
- [x] **Hito Silver (Modelo Estrella Verificado):**
  - `fact_contratos`: **6,013,832 registros** (100.00% integridad exacta contra Bronze).
  - `dim_entidades`: **6,505 entidades públicas únicas** identificadas.
  - `dim_proveedores`: **1,226,613 proveedores y contratistas únicos** mapeados.
  - `dim_geografia`: **1,013 municipios y departamentos únicos** normalizados.
- [x] **Reglas de Calidad y Rendimiento Validadas:**
  - Surrogate Keys numéricas `BIGINT` generadas determinísticamente vía `F.xxhash64()`.
  - Clasificación por rangos de cuantía (`195,946` sin cuantía, `4,737,490` mínima cuantía, `914,096` menor, `139,695` mayor y `26,605` megacontratos).
  - Protección de fechas históricas y compatibilidad total con V-Order en Microsoft Fabric.

