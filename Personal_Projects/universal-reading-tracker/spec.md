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
- **RF-08: Calibración y Backfill de Racha Preexistente (164 Días)**
  - La aplicación garantiza la preservación de la racha previa activa acumulada (164 días hasta ayer 2026-09-27).
  - Se genera y auto-repara el backfill de resúmenes diarios históricos (`DailyReadingSummary`) en Room DB para los 164 días anteriores (incluyendo ayer), garantizando que el contador muestre 164 días de base y avance a 165 días inmediatamente al registrar la primera lectura de hoy.
- **RF-09: Condición de Mantenimiento de Racha**
  - La racha diaria se mantiene activa si el usuario registra **al menos 1 minuto** de lectura válida (en Audible, Kindle o cualquier formato) entre las 00:00:00 y las 23:59:59 del día local.
- **RF-10: Manejo de Sesiones a Medianoche (División Proporcional)**
  - Si una sesión de lectura cruza el cambio de día (ej. inicia a las 23:45 y finaliza a las 00:20):
    - El tramo antes de las 00:00 (15 min) se asigna al día que finaliza (manteniendo o consolidando su racha).
    - El tramo posterior a las 00:00 (20 min) se asigna al nuevo día (contribuyendo inmediatamente a la racha del día que comienza).
- **RF-12: Recordatorio Inteligente Preventivo de Racha (9:00 PM Hora Colombia)**
  - A las 21:00 horas (zona horaria `America/Bogota`), el sistema evalúa automáticamente si el usuario ya registró lectura en el día.
  - Si el usuario ya leyó (`totalMinutesRead >= 1`), la alerta se silencia para no interrumpir.
  - Si aún no ha leído, dispara una notificación de alta prioridad invitando al usuario a leer 15 minutos en Kindle o Audible para blindar su racha.
  - Los 7 indicadores de la cápsula de consistencia semanal (`L M M J V S D`) reflejan en tiempo real el cumplimiento de cada día (incluyendo el domingo).
- **RF-13: Ficha Interactiva de Métricas de Sesión en Historial Reciente**
  - Cada fila en "Historial Reciente" es interactiva al toque (`clickable`).
  - Al pulsar una sesión, se despliega una ficha modal con estética Obsidian Luxury (`SessionDetailDialog`) que muestra:
    - Título y autor completo de la obra leída.
    - Modalidad de lectura (`AUDIOLIBRO` o `KINDLE FÍSICO`) con insignias y gradientes curados.
    - Cuadrícula de 4 métricas clave: Tiempo neto (min y seg), Ventana horaria (`hh:mm a` inicio y fin), Ritmo de lectura (`págs/h` o inmersión) e Impacto en racha.
    - Rango de páginas alcanzadas (`Pág. X ➔ Y`).
    - Botón de acción rápida para reanudar o seleccionar ese libro como lectura activa.
- **RF-14: Temporizador Resiliente a Doze/Deep-Sleep y Auto-Sanación de Sesiones**
  - La duración de las sesiones en `KindleReadingTimerService` se calcula exclusivamente por diferencia de marcas temporales de reloj real (`endEpoch - startEpoch`).
  - El estado del temporizador se respalda en `SharedPreferences` para soportar reinicios o suspensión del sistema operativo.
  - La notificación de lectura en curso utiliza el cronómetro nativo del sistema operativo (`usesChronometer = true`).
  - Auto-sanación reactiva en segundo plano que detecta sesiones históricas o del día truncadas por reposo del procesador y las repara automáticamente, recalculando los resúmenes diarios correspondientes.
- **RF-15: Widget de Pantalla de Inicio (AppWidget) con 1 Toque y Racha en Vivo**
  - Widget nativo 4x2 redimensionable con sistema de diseño Obsidian Luxury (`ReadingAppWidgetProvider` + `RemoteViews`).
  - Muestra la racha activa (`🔥 164 Días`), el progreso de hoy (`HOY: X / 30 MIN`), y el libro en curso (`Pág. X / Y`).
  - Botón de acción táctil de 1 toque que conmuta `KindleReadingTimerService` con respuesta háptica instantánea sin tener que abrir la app.
  - Sincronización reactiva bidireccional inmediata con Room DB y el estado del temporizador.
- **RF-16: Mapa de Calor Anual (Heatmap) y Analítica Visual de Hábitos**
  - **Matriz de Consistencia Anual (Estilo GitHub / Obsidian):** Renderizado horizontal de cuadrícula de semanas con 5 niveles de intensidad en esmeralda Obsidian. Refleja fielmente los 164+ días acumulados e interactividad al toque para inspeccionar la fecha y minutos discriminados por modalidad.
  - **Tendencia Semanal de Modalidad (Audible vs. Kindle):** Gráfica de barras apiladas de los 7 días de la semana en curso (Cian vs. Ámbar) con porcentajes de distribución y formato predominante.
  - **Ritmo de Lectura y Franja Horaria:** Cálculo en tiempo real de velocidad promedio (`págs/hora`), proyección estimada de finalización para el libro activo e identificación del patrón horario de lectura (Matutino, Vespertino, Nocturno, Madrugada).
- **RF-17: Navegación por Pestañas Inferiores (Bottom Dock) y Gestión de Biblioteca Integral**
  - **Arquitectura de Navegación Desacoplada (Bottom Navigation Dock):** Sustituye la sobrecarga vertical de una sola pantalla continua por 3 pestañas especializadas accesibles con 1 pulgar:
    1. **Inicio (`HOME`):** Dashboard focalizado en el objetivo del día, cronómetro de Kindle físico, libro activo, desglose diario y sesiones recientes.
    2. **Analítica (`ANALYTICS`):** Tablero visual dedicado para el Heatmap anual de consistencia (164+ días), gráfica semanal de tendencias (Audible vs. Kindle) y métricas de ritmo y franjas horarias.
    3. **Biblioteca (`LIBRARY`):** Gestión integral del catálogo de libros local con buscador en tiempo real por título y autor.
  - **Secciones de Biblioteca por Estado de Lectura:**
    - **Leyendo:** Libros en curso con barra de progreso porcentual, botón para activar lectura instantánea ("Leer Ahora") y diálogo de avance de página.
    - **Por Leer:** Lista de espera con contador de libros y acción de inicio directo.
    - **Completados:** Libros concluidos al 100% con insignia de estado terminada.
  - **Estética Obsidian Luxury:** Dock flotante con soporte para gestos, bordes redondeados (`RoundedCornerShape(32.dp)`), píldoras activas iluminadas y transiciones fluidas con `AnimatedContent`.
- **RF-18: Historial Reciente Compacto con Expansión Dinámica y Gestión de Obras Concluidas**
  - **Historial Reciente Compacto:**
    - Muestra de forma predeterminada las **3 sesiones más recientes** en la pantalla de inicio, reduciendo drásticamente la saturación visual.
    - Cabecera con contador contextual (`3 de X sesiones`) y botón interactivo `Ver todo (X) ▾` / `Mostrar menos ▴`.
    - Expansor táctil inferior tipo píldora de cristal Obsidian con chevron animado que revela u oculta el historial completo.
  - **Marcado Directo de Libros Leídos:**
    - Botón `[✓ Marcar Leído]` en tarjetas de biblioteca para libros en lectura o lista de espera.
    - Mueve la obra instantáneamente a `Completados` fijando su progreso en `totalUnits` (100%).
    - En `Completados`, muestra insignia de finalización y botón `[Reabrir]` para reiniciar si el usuario desea releer.
  - **Registro de Libros Leídos en Racha Histórica (+100 Días):**
    - Toggle en `AddBookDialog` para ingresar libros ya terminados anteriormente sin activarlos forzosamente como lectura en curso.
    - Botón `[Marcar 100% Terminado]` en el diálogo de avance (`UpdatePositionDialog`).
- **RF-19: Cuaderno de Citas, Ideas y Reflexiones (Highlights & Notes) y Exportación Obsidian/Notion**
  - **Captura de Pensamientos y Citas en Sesión:**
    - En `SessionDetailDialog` (y al concluir una lectura), campo para escribir o dictar por voz reflexiones, ideas clave o citas memorables asociadas a la sesión y obra.
    - Actualización reactiva persistida en Room DB sin migraciones destructivas (`updateSessionNotes`).
  - **Subpestaña "Citas & Notas" en Biblioteca:**
    - Nueva sección `Citas & Notas` en la pestaña de Biblioteca (`LibraryScreen`) con buscador en tiempo real por texto, título y autor.
    - Tarjeta Obsidian para cada nota con cita destacada, libro, autor, fecha, y botón `Copiar MD` con 1 toque.
    - Exportación al portapapeles en formato Markdown limpio compatible con Obsidian / Notion:
      ```markdown
      > "Cita o reflexión..."
      
      *— Título por Autor (Fecha, Pág. X)*
      ```
  - **Alineación Garantizada en Gráfica Semanal (`WeeklyModalityChart`):**
    - Ajuste de línea base y caja de minutos fija (16dp) para evitar que barras llenas (ej. S y M) desplacen o recorten las etiquetas de días de la semana.
- **RF-20: Metas Configurables Anuales/Mensuales y Sistema de Logros Obsidian (Gamificación Elegante)**
  - **Metas Configurables:**
    - Meta de libros leídos al año (por defecto 12 libros en 2026).
    - Meta de minutos de lectura al mes (por defecto 1,000 minutos/mes).
    - Diálogo de configuración rápida (`ConfigureGoalsDialog`) persistido en `SharedPreferences`.
  - **Insignias y Milestones Obsidian:**
    - 👑 **Centenario de Lectura:** 100+ días de racha continua de lectura activa.
    - ⚡ **Lector Bimodal:** Combinar Audible y Kindle en el mismo día.
    - 🌙 **Lector Nocturno:** Completar sesiones de lectura después de las 21:00 horas.
    - ☕ **Maratón de Fin de Semana:** Más de 60 minutos de lectura en sábado o domingo.
    - Modal detallado de hito (`MilestoneDetailDialog`) con trofeo radial, nivel de prestigio y métricas de avance.

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
- [x] Recordatorio preventivo diario a las 9:00 PM (hora Colombia) para proteger racha con reprogramación automática en reinicio (`ReadingReminderScheduler`, `ReadingReminderReceiver`, `BootReceiver`).
- [x] Ficha interactiva de métricas de sesión al tocar cualquier elemento del historial reciente (`LuxurySessionRow` -> `SessionDetailDialog`).
- [x] Temporizador de lectura físico basado en marcas de tiempo reales inmune a suspensión de CPU / Doze mode, con persistencia en SharedPreferences y auto-sanación reactiva de sesiones truncadas (`KindleReadingTimerService`, `autoRepairThrottledSessions`).
- [x] Widget de pantalla de inicio nativo para Android (AppWidget) con estética Obsidian Luxury, racha en vivo y botón 1-toque para Kindle físico (`ReadingAppWidgetProvider`, `widget_reading_tracker.xml`).
- [x] Mapa de calor anual de consistencia (Heatmap estilo GitHub/Obsidian), gráfica semanal comparativa Audible vs. Kindle y cálculo de ritmo lector con horario preferido (`CalculateReadingAnalyticsUseCase`, `ReadingAnalyticsSection`).
- [x] Navegación por pestañas inferiores (Inicio, Analítica, Biblioteca) con estética Obsidian Luxury, y gestión dedicada de biblioteca particionada por estado (Leyendo, Por leer, Completados), buscador en vivo y edición directa de progreso (ADR-021).
- [x] Historial reciente inteligente con vista compacta de 3 sesiones y expansor bajo demanda, y marcado de libros leídos tanto en biblioteca como en alta histórica (+100 días) (ADR-022).
- [x] Cuaderno de Citas, Ideas y Reflexiones (Highlights & Notes) con tarjetas Obsidian, exportación instantánea en Markdown para Obsidian/Notion, edición en diálogo de sesión y corrección de recorte de etiquetas en la gráfica semanal (ADR-023).
- [x] Metas configurables anuales (libros) y mensuales (minutos) con barras de progreso Obsidian y sistema de 4 insignias/milestones de prestigio (Centenario, Bimodal, Nocturno, Maratón Finde) con diálogos de detalle e interactividad de alta gama (ADR-024).
