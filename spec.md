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
- Estructuración del código en un Fabric Notebook (`nb_bronze_ingest_socrata.Notebook`) y/o script de utilidad reproducible, listo para ser agendado (*Schedule*) o encadenado en un Data Pipeline de Fabric en `ws-datos-abiertos-colombia`.

---

## 3. Modelo de Dominio y Variables de Negocio

- **Configuración de Dataset:**
  - `dataset_id`: Identificador de 4x4 (alfanumérico con guion).
  - `batch_size`: Registros por petición (por defecto 10,000; configurable hasta el límite de SODA de 50,000).
  - `rate_limit_delay_sec`: Tiempo de espera prudencial entre peticiones (ej. 0.5s - 1.0s).
  - `watermark_column`: Columna temporal del dataset para filtrado incremental (ej. `fecha_creacion`, `fecha_firma`).
- **Estados de Ejecución:** `IN_PROGRESS`, `SUCCESS`, `THROTTLED_RETRY`, `FAILED`.

---

## 4. Flujos de Trabajo (Workflows)

### 1. Flujo de Ingesta Diaria (Happy Path)
1. El pipeline/notebook se ejecuta automáticamente según el cron diario en Fabric.
2. Consulta el último *watermark* persistido en la tabla de control/delta del Lakehouse.
3. Solicita a `https://www.datos.gov.co/resource/{dataset_id}.json` el conteo o primer bloque mediante `$limit` y `$where [watermark_col] > 'última_marca'`.
4. Itera extrayendo lotes con pausas controladas hasta que la respuesta retorne un lote vacío (`[]`).
5. Transforma los registros a DataFrame Spark y realiza un `append` o `upsert` en la tabla Delta de `datos_abiertos_lh_dev`.
6. Actualiza el log de ejecución y finaliza exitosamente.

### 2. Manejo de Errores y Excepciones
- **HTTP 429 / Rate Limit Exceeded:** El cliente entra en espera exponencial (espera 2s, 4s, 8s...) antes de reintentar el lote actual sin abortar el proceso.
- **Conexión Interrumpida:** Reintento automático hasta 3 veces por lote antes de registrar error crítico y notificar.
- **Dataset no encontrado (HTTP 404):** Validación previa de metadatos de Socrata.

---

## 5. Criterios de Aceptación
- [x] Módulo/Cliente SODA implementado con soporte para paginación por lotes y SoQL (`datos_abiertos/soda_client.py`).
- [x] Implementado control de throttling y reintentos exponenciales contra bloqueos y caídas.
- [x] Estructurado el espacio de trabajo local correspondiente a `ws-datos-abiertos-colombia` con el Lakehouse `datos_abiertos_lh_dev`.
- [x] Creado el Notebook de ingesta Bronze compatible con Microsoft Fabric (`nb_bronze_ingest_secop.Notebook`).
- [x] Verificación de descarga y persistencia con el dataset `jbjy-vk9h` de `datos.gov.co`.
- [x] **Hito Histórico Alcanzado:** Ingesta del 100.00% del dataset SECOP II completada exitosamente en el Lakehouse (`6,013,832 / 6,013,832` registros, 0 faltantes). Sincronización incremental diaria lista para ejecución desatendida.
