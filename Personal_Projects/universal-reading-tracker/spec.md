# Especificaciones de Aplicación: Universal Reading Tracker (Android)

## 1. Resumen Ejecutivo y Objetivos
- **Problema de Negocio:**
  Los lectores contemporáneos consumen literatura de forma multimodal: escuchan audiolibros (Audible, Spotify) durante traslados o actividades manuales, y leen texto visualmente en dispositivos dedicados como e-readers físicos (Amazon Kindle Paperwhite, Oasis, Scribe) o libros impresos. Actualmente, las estadísticas de lectura están fragmentadas:
  - Audible no habla con Kindle para consolidar el hábito de tiempo diario.
  - Los dispositivos físicos Kindle no tienen una forma local e inmediata de reportar tiempo de lectura a una app Android abierta.
  - El usuario pierde la continuidad de sus rachas, metas y tiempo de atención global dedicado a la lectura.
- **Propuesta de Solución:**
  Construir una aplicación nativa de Android (**Universal Reading Tracker**) que unifique en un solo tablero local-first el seguimiento de hábitos de lectura:
  1. **Modalidad Audio (Audible y futuros proveedores):** Detección pasiva y automática mediante `MediaSessionManager` / `NotificationListenerService` con control de pausas interactivo.
  2. **Modalidad E-Reader Físico (Kindle) y Libros Físicos:** Temporizador inteligente interactivo (Quick Settings Tile / Notificación flotante de control) con registro opcional de páginas o porcentaje para calcular ritmo de lectura y tiempo neto.
- **Usuarios / Roles Involucrados:**
  - **Lector Multimodal:** Usuario que combina audiolibros (Audible) y lectura visual en e-readers dedicados (Kindle físico), buscando consolidar sus hábitos diarios de lectura en minutos reales.

---

## 2. Requerimientos Funcionales

### A. Módulo Audio (Audible y Audio-providers)
- **RF-01: Detección Automática de Audible (MediaSession / Notification Listener)**
  - Detección pasiva en segundo plano cuando el paquete `com.audible.application` entra en estado `PLAYING`.
  - Extracción de metadatos: Título, autor y duración disponible.
- **RF-02: Gestión de Pausas y Notificación Interactiva para Audio**
  - Al pausarse Audible, detiene el cómputo de tiempo de inmediato.
  - Muestra notificación interactiva con botones: `[Terminar Sesión]` y `[Continuar]`.

### B. Módulo Kindle Físico y Lectura Visual
- **RF-03: Temporizador Inteligente de Lectura (Kindle / E-Reader)**
  - El usuario puede iniciar una sesión de lectura con 1 toque desde la app, un Widget de pantalla de inicio o un Quick Settings Tile de Android.
  - Permite seleccionar el libro activo o crear uno rápido ("Leyendo en Kindle: [Libro]").
  - Funciona con la pantalla apagada (el usuario está leyendo en su e-reader físico, no en el teléfono).
  - Incluye modo "Pomodoro" o alarma suave opcional para descansos visuales.
- **RF-04: Cierre de Sesión Kindle y Métricas de Progreso**
  - Al terminar de leer en el Kindle físico, el usuario presiona "Finalizar sesión" en la notificación de control o widget.
  - Diálogo rápido opcional:
    - ¿Página o % alcanzado? (ej. inició en pág 120, terminó en pág 145 -> +25 páginas en 40 minutos = 37.5 págs/hora).
    - Notas o reflexiones breves.
- **RF-11: Disparador Inteligente NFC (Tap-to-Track)**
  - La app responde al contacto NFC con stickers programados (`readingtracker://kindle`).
  - Al apoyar el teléfono sobre la funda del Kindle:
    - Si no hay sesión activa: Inicia la lectura de Kindle con vibración háptica de confirmación.
    - Si hay sesión activa: Detiene la sesión, guarda el tiempo acumulado y emite vibración de cierre.
  - La app incluye una herramienta interna para escribir/vincular cualquier sticker virgen (NTAG213/215/216) sin apps externas.

### C. Módulo Unificado de Consolidación y Métricas
- **RF-05: Cómputo de Tiempo en Minutos Reales Unificados**
  - El tiempo de hábito diario consolida minutos de Audible + minutos de Kindle en una sola métrica común: **Tiempo Total de Lectura Dedicado**.
  - Visualización discriminada por formato (ej. Hoy: 55 min totales -> 30 min Audible + 25 min Kindle).
- **RF-06: Catálogo Local-First Unificado y Formatos Híbridos**
  - Permite marcar un libro con formato `AUDIOBOOK`, `EBOOK_KINDLE` o `HYBRID` (cuando el usuario lee el mismo título alternando entre Kindle y Audible).
  - Almacenamiento 100% offline en Room DB con edición local completa de metadatos.
- **RF-07: Arquitectura Desacoplada Multi-Proveedor y Multi-Modalidad**
  - Abstracción de proveedores (`ReadingProviderAdapter`) que soporta tanto proveedores de audio pasivos como perfiles de dispositivos físicos/manuales.

### D. Módulo de Rachas (Streaks) y Calibración Histórica
- **RF-08: Calibración y Backfill de Racha Preexistente (163 Días)**
  - La aplicación incluye un asistente de incorporación (Onboarding / Settings) que permite al usuario registrar su racha previa activa (163 días al 2026-09-26).
  - Se genera un backfill de resúmenes diarios históricos (`DailyReadingSummary`) en Room DB para los 163 días anteriores, garantizando que el calendario de calor (heatmap) y el contador comiencen exactamente en 163 días y avancen a 164 en el próximo día con lectura.
- **RF-09: Condición de Mantenimiento de Racha**
  - La racha diaria se mantiene activa si el usuario registra **al menos 1 minuto** de lectura válida (en Audible, Kindle o cualquier formato) entre las 00:00:00 y las 23:59:59 del día local.
- **RF-10: Manejo de Sesiones a Medianoche (División Proporcional)**
  - Si una sesión de lectura cruza el cambio de día (ej. inicia a las 23:45 y finaliza a las 00:20):
    - El tramo antes de las 00:00 (15 min) se asigna al día que finaliza (manteniendo o consolidando su racha).
    - El tramo posterior a las 00:00 (20 min) se asigna al nuevo día (contribuyendo inmediatamente a la racha del día que comienza).

---

## 3. Modelo de Dominio y Variables de Negocio

### Entidades Principales

#### 1. `ReadingModality` (Enum)
- `AUDIOBOOK`: Escucha mediante reproductor de audio.
- `EBOOK_KINDLE`: Lectura en dispositivo físico Amazon Kindle.
- `PHYSICAL_BOOK`: Lectura en libro impreso en papel.
- `OTHER_EBOOK`: Otros lectores digitales.

#### 2. `Book`
- `id`: Long (PK Autogenerado)
- `title`: String
- `author`: String
- `format`: Enum (`AUDIOBOOK`, `EBOOK`, `PHYSICAL`, `HYBRID`)
- `primaryProviderId`: String (ej. `"audible"`, `"kindle"`, `"manual"`)
- `coverUri`: String?
- `totalPages`: Int? (para libros de texto/Kindle)
- `totalDurationSeconds`: Long? (para audiolibros)
- `currentPage`: Int?
- `currentDurationSeconds`: Long?
- `createdAt`: Long
- `updatedAt`: Long

#### 3. `ReadingSession`
- `id`: Long (PK Autogenerado)
- `bookId`: Long (FK -> Book)
- `modality`: ReadingModality
- `providerId`: String (ej. `"audible"`, `"kindle_physical"`)
- `startTime`: Long (Epoch timestamp)
- `endTime`: Long (Epoch timestamp)
- `realDurationSeconds`: Long (Tiempo neto activo en segundos)
- `startPage`: Int?
- `endPage`: Int?
- `pagesRead`: Int? (endPage - startPage)
- `status`: Enum (`RECORDING`, `PAUSED`, `CONFIRMED`, `DISCARDED`)
- `notes`: String?

#### 4. `DailyReadingSummary` (Cálculo Agregado / Vista Room)
- `date`: String (YYYY-MM-DD)
- `totalMinutesRead`: Int
- `audioMinutes`: Int
- `kindleMinutes`: Int
- `physicalMinutes`: Int
- `goalReached`: Boolean
- `isHistoricalBackfill`: Boolean (True para los 163 días sembrados históricamente)

---

## 4. Flujos de Trabajo (Workflows)

### 1. Flujo Audible (Automático / Pasivo)
1. Usuario pulsa Play en Audible en su teléfono.
2. `NotificationListenerService` detecta paquete `com.audible.application`.
3. Inicia sesión activa de tipo `AUDIOBOOK`.
4. Al pausar Audible, se congela el tiempo y se lanza notificación interactiva `[Terminar Sesión]` / `[Continuar]`.

### 2. Flujo Kindle Físico (Temporizador Inteligente / Semi-automático)
1. El usuario se sienta a leer en su Kindle Paperwhite/Oasis.
2. En su teléfono Android, pulsa el botón del Widget / Quick Settings Tile: **"Leer en Kindle"**.
3. El servicio inicia un temporizador de lectura en segundo plano (`ForegroundService`) con notificación minimalista en pantalla de bloqueo.
4. El usuario apaga la pantalla del teléfono y lee en su Kindle físico.
5. Al terminar su lectura en el Kindle, toca **"Finalizar"** en la notificación del teléfono.
6. Se despliega un diálogo emergente:
   - Tiempo registrado: ej. 38 min.
   - "¿En qué página quedaste?" (opcional, pre-rellenado con la última página guardada).
   - Guarda la sesión en Room DB y actualiza la racha y meta diaria unificada.

### 3. Flujo de Inicialización y Calibración de Racha (163 Días)
1. En el primer inicio (Onboarding), la app detecta la calibración de racha inicial.
2. El usuario confirma sus 163 días de racha acumulada hasta el 2026-09-26.
3. Se ejecuta el backfill automático en Room DB, poblando los 163 registros diarios en `DailyReadingSummary`.
4. El tablero principal muestra la racha activa: **🔥 163 días**.

---

## 5. Criterios de Aceptación
- [x] Detección automática en segundo plano de audiolibros reproducidos en Audible con metadatos de título y autor (`AudibleNotificationListenerService`).
- [x] Widget / Quick Action para iniciar y detener sesiones de lectura con el Kindle físico sin fricción (`KindleReadingTimerService` y `KindleQuickSettingsTileService`).
- [x] Tablero unificado de hábitos que consolide minutos de Audible y minutos de Kindle en un solo total diario y racha (`DashboardScreen` + `DashboardViewModel`).
- [x] Soporte para libros híbridos (mismo libro leído en Kindle y escuchado en Audible) (`ReadingModality` y `BookFormat.HYBRID`).
- [x] Calibración y preservación intacta de la racha histórica de 163 días mediante backfill en Room DB (`BackfillHistoricalStreakUseCase` y `StreakRepositoryImpl`).
- [x] División automática proporcional a medianoche para sesiones que crucen las 00:00:00 (`SplitMidnightSessionUseCase` y `SplitMidnightSessionUseCaseTest`).
- [x] Almacenamiento local SQLite (Room) 100% offline con privacidad absoluta (`AppDatabase`, DAOs y Entities).
- [x] Arquitectura modular extensible para sumar nuevos servicios (`ReadingProviderAdapter`, `AudibleProviderAdapter`, `KindlePhysicalProviderAdapter`).
