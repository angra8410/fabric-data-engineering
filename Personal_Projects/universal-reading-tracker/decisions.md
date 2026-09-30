# Bitácora de Decisiones Arquitectónicas (Decisions Log)

## [ADR-001] Mecanismo de Ingesta y Detección de Audible
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  Audible (Amazon) no expone una API pública ni SDK para desarrolladores de terceros.
- **Decisión Tomada:**
  Adoptar un **enfoque híbrido**:
  1. Uso de `NotificationListenerService` / `MediaSessionManager` en Android para interceptar de forma pasiva y sin credenciales los eventos de reproducción del paquete `com.audible.application`.
  2. Confirmación y enriquecimiento manual por parte del usuario.
- **Consecuencias:**
  - Requiere solicitar al usuario el permiso de acceso a notificaciones en el Onboarding.
  - Funciona de forma 100% offline y con total privacidad de credenciales.

---

## [ADR-002] Criterio de Cuantificación del Tiempo de Lectura
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  En audiolibros y lectura visual, existía el dilema de cómo consolidar el progreso en una métrica coherente.
- **Decisión Tomada:**
  Computar el **tiempo de reloj real** (wall-clock time neto dedicado a la actividad de lectura). Si el usuario escucha 30 minutos a 1.75x en Audible y lee 20 minutos en su Kindle físico, su total diario es de 50 minutos de hábito lector.
- **Consecuencias:**
  - Se unifican todas las modalidades bajo la moneda común de "Minutos de concentración lectora dedicada".

---

## [ADR-003] Arquitectura Multi-Proveedor y Multi-Modalidad Desacoplada
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  El sistema debe soportar tanto reproductores de audio en el teléfono (Audible, Spotify, Storytel) como sesiones de lectura visual externas (Kindle físico, libros en papel).
- **Decisión Tomada:**
  Definir la abstracción de arquitectura `ReadingProviderAdapter`:
  - `AudioSessionProviderAdapter`: Especializado en interceptar `MediaSession` (Audible como implementación piloto).
  - `ManualSessionProviderAdapter`: Especializado en flujos de lectura externa con temporizador inteligente (Kindle físico, papel).
- **Consecuencias:**
  - Desacoplamiento total entre los disparadores de sesión (automáticos o por temporizador) y el motor de agregación de estadísticas de Room DB.

---

## [ADR-004] Gestión del Ciclo de Vida de Pausas y Notificación Interactiva
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  Evitar tiempos muertos en pausas de Audible y facilitar el cierre rápido de sesiones.
- **Decisión Tomada:**
  Notificación interactiva con acciones rápidas `[Terminar Sesión]` y `[Continuar]`.
- **Consecuencias:**
  - Control explícito y máxima precisión en el registro del tiempo sin frustraciones por sesiones infladas o truncadas.

---

## [ADR-005] Stack Tecnológico Nativo (Android Jetpack Compose + Clean Architecture)
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  Integración con servicios de segundo plano del sistema operativo (`NotificationListenerService`, `ForegroundService`, `QuickSettingsTile`).
- **Decisión Tomada:**
  Desarrollar la aplicación en **Android Nativo con Kotlin**:
  - **UI:** Jetpack Compose (Material Design 3).
  - **Arquitectura:** Clean Architecture (Domain, Data, Presentation) con MVI / MVVM.
  - **Persistencia:** Room Database con SQLite (100% Offline-first).
  - **Concurrencia:** Kotlin Coroutines & Flow.
- **Consecuencias:**
  - Alto rendimiento, soporte directo de APIs del sistema Android y experiencia visual premium.

---

## [ADR-006] Catálogo Local-First y Privacidad de Datos
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  Privacidad de los datos de lectura y funcionamiento sin internet.
- **Decisión Tomada:**
  Modelo **Local-First**: Todos los libros y sesiones se almacenan en SQLite (Room) localmente en el dispositivo. No se requiere cuenta ni login externo para la experiencia central.
- **Consecuencias:**
  - Cero latencia, funcionamiento offline y absoluta soberanía de los datos del usuario.

---

## [ADR-007] Soporte Multimodal Unificado (Audiolibros + Kindle Físico + Papel)
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  El usuario indicó expresamente: *"it's not only for audio-reading, because I am reading using my kindle ok"*. Los lectores actuales alternan entre audiolibros (Audible) y e-readers físicos (Kindle Paperwhite/Oasis/Scribe), incluso consumiendo el mismo libro en ambos formatos (lectura híbrida).
- **Decisión Tomada:**
  1. Extender el modelo de dominio con la enumeración `ReadingModality` (`AUDIOBOOK`, `EBOOK_KINDLE`, `PHYSICAL_BOOK`).
  2. Permitir que una entidad `Book` pueda tener formato `HYBRID`, acumulando tanto sesiones de audio (Audible) como sesiones de texto (Kindle).
  3. Proporcionar un tablero consolidado con desglose por modalidad y cálculo de racha unificada.
- **Consecuencias:**
  - Convierte la aplicación en una solución universal de hábitos de lectura en lugar de un reproductor o tracker aislado de audio.

---

## [ADR-008] Mecanismo de Registro para Dispositivo Físico Kindle
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  A diferencia de las aplicaciones instaladas en el propio teléfono Android, un dispositivo físico Kindle externo no emite eventos de software directamente al sistema operativo del teléfono.
- **Decisión Tomada:**
  Implementar un **Temporizador Inteligente / Quick Action**:
  - Acceso directo mediante botón en la app, Quick Settings Tile de Android o Widget de inicio ("Leer en Kindle").
  - Al activarse, inicia un `ForegroundService` ligero que cronometra el tiempo de lectura mientras la pantalla del teléfono permanece apagada.
  - Al presionar "Finalizar", ofrece un diálogo opcional para registrar página final leída o porcentaje, calculando automáticamente la velocidad de lectura (páginas/hora).
- **Consecuencias:**
  - Fricción mínima (un toque para empezar y un toque para terminar) sin necesidad de sincronización por cables ni ingeniería inversa de Amazon Cloud.

---

## [ADR-009] Calibración y Sembrado de Historial de Racha (Backfill Integral en Room DB)
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  El usuario ya cuenta con una racha activa consolidada de 163 días consecutivos al día de hoy (2026-09-26). Comenzar la aplicación en día 0 o día 1 penalizaría el esfuerzo previo. Se evaluó si convenía un "offset artificial" (un simple entero `+ 163`) o un backfill estructurado en base de datos.
- **Decisión Tomada:**
  Implementar una rutina de **Backfill de Historial en Room DB**:
  - Al configurar o inicializar la app, se generan los 163 registros diarios en `DailyReadingSummary` (con marca `isHistoricalBackfill = true`).
  - Todas las queries SQL analíticas de racha, calendarios de actividad (estilo GitHub contribution graph) y gráficas de consistencia operan sobre datos homogéneos sin condiciones mágicas de `+ 163`.
- **Alternativas Consideradas:**
  - *Offset numérico en SharedPreferences:* Frágil, causa discrepancias visuales al pintar calendarios mensuales históricos donde los días aparecerían vacíos.
- **Consecuencias:**
  - Consistencia analítica total y fidelidad visual en el historial.

---

## [ADR-010] Manejo de Sesiones Trans-Medianoche (División Proporcional Temporal)
- **Fecha:** 2026-09-26
- **Estado:** Aprobado
- **Contexto:**
  Es habitual leer en la cama entre las 23:30 y las 00:30. Si una sesión se atribuye únicamente al día de inicio o al día de fin, puede dejar desprotegida la racha de uno de los dos días o falsear el tiempo diario.
- **Decisión Tomada:**
  Aplicar **División Proporcional a Medianoche** (`Midnight Splitting`):
  - La capa de persistencia fragmenta automáticamente cualquier sesión que cruce las 00:00:00 locales en dos segmentos contiguos vinculados a sus respectivas fechas de calendario.
  - Ejemplo: Sesión de 40 min (23:45 a 00:25) -> 15 min al día previo (salva la racha si faltaba lectura) + 25 min al nuevo día (inicia la nueva racha).
- **Consecuencias:**
  - Máxima justicia y precisión en el conteo de tiempo diario y preservación natural de rachas.

---

## [ADR-011] Disparador Inteligente NFC para Kindle Físico (Tap-to-Track)
- **Fecha:** 2026-09-27
- **Estado:** Aprobado
- **Contexto:**
  El usuario lee exclusivamente en un dispositivo físico Kindle. Para eliminar la necesidad de desbloquear el teléfono o buscar botones en la pantalla, se busca un mecanismo de interacción física instantánea con el dispositivo de lectura.
- **Decisión Tomada:**
  Integrar soporte para **Stickers NFC (NTAG213 / NTAG215 / NTAG216)**:
  1. Uso del URI scheme estándar `readingtracker://kindle`.
  2. Implementación de una `NfcKindleActivity` transparente que actúa como conmutador (toggle): inicia la sesión si está inactiva y la finaliza si está activa, con respuesta háptica y notificación silenciosa.
  3. Módulo de escritura NDEF integrado en la app para programar cualquier sticker virgen directamente desde los ajustes.
- **Alternativas Consideradas:**
  - *Beacons Bluetooth:* Descartados por requerir hardware activo con batería propia y mayor costo.
  - *Integración exclusiva por botón/widget:* Válida pero requiere interactuar visualmente con la pantalla del teléfono.
- **Consecuencias:**
  - Interacción táctil sin fricción (apoyar el teléfono sobre el Kindle para iniciar/parar lectura) manteniendo la pantalla del teléfono apagada durante la lectura.

---

## [ADR-012] Sistema de Diseño Obsidian Luxury y Micro-animaciones Fluidas
- **Fecha:** 2026-09-27
- **Estado:** Aprobado
- **Contexto:**
  La interfaz estándar basada en tarjetas planas de Material Design resultaba genérica y no reflejaba el valor emocional de una racha de más de 160 días de lectura ininterrumpida ni la experiencia premium esperada por el usuario.
- **Decisión Tomada:**
  Adoptar un **Sistema de Diseño Obsidian Luxury** con estética Glassmorphic y micro-animaciones fluidas:
  1. **Tarjeta Trofeo de Racha (Hero Card):** Fondo titanio oscuro con halo radial cálido de brasa (`Brush.radialGradient`), borde de cristal con reflejo ámbar y llama 3D animada con doble anillo de respiración áurea continua (*breathing halo pulse*).
  2. **Cuadrícula de Hardware Simétrica:** Altura unificada (172 dp) para Audible y Kindle Físico. Audible integra un ecualizador de 4 bandas armónicas animadas en tiempo real. Kindle Físico integra conmutación de estado háptica a botón carmesí con badge pulsante `EN CURSO`.
  3. **Píldora NFC Inteligente:** Diseño de bordes neón violeta con acción de vinculación directa y modal instructivo oscuro paso a paso.
  4. **Metas con Física Elástica (*Spring Animations*):** Barra de progreso dual con degradé suave y micro-desglose por modalidad.
- **Consecuencias:**
  - Experiencia visual y táctil del más alto estándar de diseño moderno (estilo Apple Fitness / Linear / Opal), potenciando la retención del hábito de lectura diaria.

---

## [ADR-013] Meta Diaria Reactiva, Aislamiento de Backfill Histórico e Iconografía Adaptativa
- **Fecha:** 2026-09-27
- **Estado:** Aprobado
- **Contexto:**
  1. El backfill de 163 días sembraba erróneamente un resumen completado de 30 minutos para la fecha de "hoy", mostrando "¡Meta Cumplida!" de forma fija antes de leer.
  2. La aplicación carecía de un icono distintivo nativo (usaba el recurso de sistema genérico `ic_menu_agenda`) y de transiciones suaves al iniciar.
- **Decisión Tomada:**
  1. **Aislamiento de Backfill:** El proceso de backfill histórico se restringe estrictamente a los 163 días previos (`ayer` hacia atrás), purgando cualquier dato simulado de hoy para que la meta diaria inicie en `0 de 30 min` (`Por comenzar 📖`).
  2. **Observación Reactiva en Room:** Se implementa `observeSummaryForDate` como un `Flow` continuo para actualizar la barra elástica y desglose Audible/Kindle en tiempo real según transcurre la lectura.
  3. **Icono Adaptativo Vectorial:** Se crea `ic_launcher` en formato adaptativo para Android (libro abierto en cian eléctrico y llama ascendente en degradé fuego).
  4. **Transición de Entrada Fluida:** Animación de apertura `fadeIn + slideInVertically` con física de resorte y `overrideActivityTransition`.
- **Consecuencias:**
  - Precisión absoluta en el cálculo del progreso diario, preservando la racha de 163 días de forma transparente y proporcionando una identidad visual premium.

---

## [ADR-014] Selector de Libros Físicos Kindle, Unidades Duales (Pág/Loc) y Exportación JSON
- **Fecha:** 2026-09-27
- **Estado:** Aprobado
- **Contexto:**
  El usuario lee en Kindle libros con diferente sistema de progreso (páginas impresas fijas vs. ubicaciones digitales "Loc") y requiere cambiar el libro activo directamente desde el tablero, además de respaldar toda su base de datos.
- **Decisión Tomada:**
  1. Catálogo enriquecido con búsqueda difusa (fuzzy search) insensible a acentos/tildes y carga desde assets/JSON.
  2. Selector modal interactivo y soporte de unidades `ProgressUnit.PAGES` y `ProgressUnit.LOCATIONS`.
  3. Utilidad de exportación completa a archivo JSON en almacenamiento externo/descargas.
- **Consecuencias:**
  - Control granular de lecturas activas y soberanía de datos del usuario.

---

## [ADR-015] Calibración de Racha a 164 Días (Hasta Ayer) y Auto-Sanación de Continuidad
- **Fecha:** 2026-09-28
- **Estado:** Aprobado
- **Contexto:**
  El usuario acumulaba 164 días continuos de lectura hasta el día de ayer (2026-09-27). Al implementar la purga de "hoy" en ADR-013, la fecha de ayer quedó desprovista de registro o excluida por el tope de 163 días previo, causando que al leer hoy (2026-09-28) la racha se reiniciara visualmente a 1 en vez de avanzar a 165 días.
- **Decisión Tomada:**
  1. **Actualización de Base Histórica:** Se calibra el sembrado histórico a **164 días** hacia atrás desde la fecha actual (cubriendo desde ayer `2026-09-27` hasta `2026-04-17`).
  2. **Auto-Sanación Reactiva (`hasCompletedBackfill`):** Se valida explícitamente que la fecha de ayer exista en Room como un día de racha válido (`isValidStreakDay = true`) y que el conteo total histórico sea `>= 164`. Si ayer falta o tiene minutos vacíos, el sistema lo repara automáticamente con estrategia `REPLACE`.
  3. **Comportamiento Esperado:** Antes de la primera lectura de hoy, la app muestra de forma estable 164 días; al registrar la lectura de hoy, asciende inmediatamente a **165 días**.
- **Consecuencias:**
  - Preservación íntegra e inviolable del hábito lector histórico del usuario sin reseteos accidentales ante cambios de día o limpiezas de caché.

---

## [ADR-016] Cápsula de Consistencia Semanal Dinámica y Recordatorio Inteligente a las 9:00 PM (Hora Colombia)
- **Fecha:** 2026-09-28
- **Estado:** Aprobado
- **Contexto:**
  1. En la tarjeta de racha (`LuxuryStreakCard`), los círculos de la semana (`L M M J V S D`) usaban una condición fija `index <= 5`, provocando que el domingo (`D`, índice 6) apareciera siempre desmarcado e incompleto a pesar de haber leído.
  2. El usuario requería una alerta preventiva a las 9:00 PM (hora Colombia / UTC-5) si aún no ha registrado lectura durante el día, protegiendo su racha antes de medianoche.
- **Decisión Tomada:**
  1. **Consistencia Semanal Anclada a la Semana en Curso:** Los 7 indicadores de `L M M J V S D` ahora computan estrictamente los días de la **semana calendario actual** (iniciando el lunes actual).
     - **Días futuros (`isFuture`):** Se muestran desactivados/pendientes (círculos oscuros translúcidos con borde sutil), sin checkmark.
     - **Día de hoy (`isToday`):** Si ya se leyó (como hoy lunes), se marca de inmediato con degradé de fuego y checkmark; si está pendiente, muestra un borde ámbar activo esperando la lectura.
     - **Días pasados de la semana (`isPast`):** Evalúan si hubo lectura en ese día específico de la semana en curso.
  2. **Recordatorio Programado a las 9:00 PM:**
     - Se implementa `ReadingReminderScheduler` y `ReadingReminderReceiver` vinculados a la zona horaria `America/Bogota` (21:00 COT).
     - **Inteligencia Condicional:** Al dispararse la alarma a las 21:00, la app consulta Room en segundo plano. Si el usuario ya leyó hoy (`totalMinutesRead >= 1`), la notificación se omite en silencio. Si aún no ha leído, despliega una notificación de alta prioridad alertando para proteger su racha de 165 días.
     - **Persistencia en Reinicio:** `BootReceiver` reprograma el recordatorio automáticamente tras el reinicio del teléfono.
- **Consecuencias:**
  - Fidelidad visual total en la consistencia semanal y protección activa del hábito lector sin spam innecesario.

---

## [ADR-017] Ficha Interactiva de Métricas de Sesión en Historial Reciente
- **Fecha:** 2026-09-28
- **Estado:** Aprobado
- **Contexto:**
  En la sección "Historial Reciente" del dashboard, cada sesión mostraba un resumen estático básico. El usuario requería que al pulsar una sesión (por ejemplo: "24 mins - *Your Past Lives* de Michael Talbot"), se abriera una vista detallada interactiva con métricas enriquecidas del libro, tiempo, ritmo de lectura e impacto en el hábito.
- **Decisión Tomada:**
  1. **Interactividad en `LuxurySessionRow`:** Se añade comportamiento táctil (`Modifier.clickable`), micro-feedback visual y un icono chevron indicador de navegación/expansión.
  2. **Diálogo de Métricas de Alta Fidelidad (`SessionDetailDialog`):**
     - **Encabezado y Metadatos:** Distintivo de modalidad (`🎧 AUDIOLIBRO` o `📖 KINDLE FÍSICO`), título completo sin truncar y autor.
     - **Cuadrícula de Métricas de 4 Ejes:**
       - *Tiempo Neto:* Minutos y segundos reales de inmersión.
       - *Ventana de Horario:* Rango horario exacto de la sesión (`hh:mm a` de inicio a fin).
       - *Ritmo de Lectura:* Páginas avanzadas y velocidad calculada en `págs/h` (o inmersión continua para audiolibros).
       - *Impacto en Racha:* Minutos aportados al hábito diario y conteo actual de racha.
     - **Progreso de Páginas:** Visualización clara de página inicial y final (`Pág. X ➔ Y`) para lecturas de texto.
     - **Acción Rápida de Continuación:** Botón primario *"Continuar leyendo este libro"* que activa el libro en el repositorio si no es el libro actual seleccionado, facilitando alternar entre lecturas en progreso.
- **Consecuencias:**
  - Experiencia de usuario inmersiva, consulta transparente del historial y trazabilidad directa de qué libro y qué métricas se obtuvieron en cada bloque de lectura.

---

## [ADR-018] Temporizador de Lectura Físico Resiliente a Doze/Deep-Sleep y Auto-Sanación de Sesiones Truncadas
- **Fecha:** 2026-09-29
- **Estado:** Aprobado
- **Contexto:**
  El usuario inició su lectura en Kindle a las 7:47 AM y finalizó a las 8:10 AM (23 minutos de tiempo real transcurrido). Sin embargo, la aplicación registró únicamente 5 minutos. 
  La causa raíz identificada fue que `KindleReadingTimerService` computaba la duración mediante una corrutina con bucle `while(isActive) { delay(1000); elapsedSeconds++ }`. Al apagar la pantalla del teléfono para leer en el dispositivo Kindle físico, Android entra en suspensión profunda de CPU (Doze Mode / Deep Sleep). Esto congeló el bucle de la corrutina durante ~18 minutos, haciendo que al despertar solo hubiera acumulado ~300 segundos (5 minutos), descartando el tiempo de reloj real `endEpoch - startEpoch`.
- **Decisión Tomada:**
  1. **Cálculo Inviolable por Tiempo de Reloj Real (Wall-Clock Time):**
     - Se elimina la dependencia del contador de corrutina para la duración de la sesión.
     - La duración real se calcula estrictamente como `totalSeconds = maxOf(0L, (endEpoch - effectiveStartEpoch) / 1000L)`.
  2. **Persistencia de Estado Inmune a Destrucción de Proceso:**
     - Al invocar `ACTION_START`, `startEpoch`, título y autor se persisten de inmediato en `SharedPreferences`. Al detenerse (`ACTION_STOP`), se recupera el inicio persistido antes de limpiar el estado.
  3. **Cronómetro Nativo a Nivel de Sistema Operativo:**
     - La notificación en primer plano utiliza `.setUsesChronometer(true)` y `.setWhen(startEpoch)`, permitiendo a la barra de estado y pantalla de bloqueo de Android animar el cronómetro de forma fluida a nivel de hardware con 0% de consumo de batería y sin descalibración.
  4. **Atribución Automática del Libro Activo en NFC y Quick Settings:**
     - Al tocar la funda con el sticker NFC o usar el Tile de ajustes rápidos, la app consulta el libro en lectura actual en Room DB para asociar la sesión directamente a ese libro.
  5. **Auto-Sanación Reactiva de Sesiones Previas Truncadas (`autoRepairThrottledSessions`):**
     - En el arranque (`DashboardViewModel.init`), el repositorio examina las sesiones de Kindle donde `(endTime - startTime) / 1000L - realDurationSeconds >= 60`.
     - Repara automáticamente la sesión en Room con su tiempo real de pared (la sesión de hoy pasa de 5 min a 23 min) y recalcula la agregación de `DailyReadingSummary` del día en curso.
- **Consecuencias:**
  - Precisión absoluta e inviolable en el registro de lectura sin importar si el teléfono está bloqueado o en reposo por horas, y reparación automática retroactiva de la sesión afectada de hoy.

---

## [ADR-019] Widget de Pantalla de Inicio (AppWidget) para Lectura con 1 Toque y Racha en Vivo
- **Fecha:** 2026-09-29
- **Estado:** Aprobado
- **Contexto:**
  Para leer en el dispositivo físico Kindle o en un libro impreso, la fricción de desbloquear el teléfono, buscar la app en el cajón de aplicaciones y tocar el temporizador desincentiva el registro habitual de sesiones breves. Además, el usuario se beneficia de tener siempre visible en su escritorio la llama de su racha activa y su meta diaria.
- **Decisión Tomada:**
  1. **Arquitectura Nativa AppWidgetProvider:**
     - Se implementa `ReadingAppWidgetProvider` con diseño *Obsidian Luxury* en `res/layout/widget_reading_tracker.xml` utilizando `RemoteViews`.
     - Cero dependencias adicionales, soporte para redimensionamiento en cuadrícula (4x2 / 3x2) y compatibilidad total con cualquier launcher de Android.
  2. **Acción Rápida de 1-Toque Directa (`ACTION_TOGGLE_KINDLE_TIMER`):**
     - Botón táctil que envía un Broadcast a `ReadingAppWidgetProvider`, el cual consulta el libro activo y arranca o detiene `KindleReadingTimerService` en segundo plano con vibración háptica instantánea.
     - Si el temporizador está detenido: botón con degradado dorado `▶ Iniciar Lectura en Kindle`.
     - Si el temporizador está corriendo: botón rojo carmesí `⏹ Finalizar Lectura (Leyendo...)`.
  3. **Visualización y Sincronización Reactiva:**
     - Muestra la racha acumulada (`🔥 164 Días`), el progreso de hoy (`HOY: X / 30 MIN`) y el libro activo con sus páginas leídas y porcentaje.
     - El widget se actualiza automáticamente al iniciar o detener sesiones en `KindleReadingTimerService`, al volver a la aplicación en `MainActivity.onResume()` y ante cambios de selección de libro o avance de páginas.
- **Consecuencias:**
  - Fricción cero para registrar hábitos diarios de lectura. El usuario puede iniciar su sesión con un solo toque desde su pantalla de inicio en menos de 1 segundo.

---

## [ADR-020] Mapa de Calor Anual de Consistencia y Analítica Visual de Ritmo Lector
- **Fecha:** 2026-09-29
- **Estado:** Aprobado
- **Contexto:**
  Con 164+ días de lectura disciplinada acumulada, el usuario requería una forma visual integral y satisfactoria para contemplar su esfuerzo histórico distribuido a lo largo del año, contrastar cuánto tiempo dedicó a Audible vs. Kindle en cada día de la semana, y conocer sus métricas de velocidad (páginas/hora) y franjas horarias preferidas de lectura.
- **Decisión Tomada:**
  1. **Separación de Lógica y Modelo en Dominio:**
     - Se crearon los modelos `ReadingAnalytics`, `DayContribution`, `WeeklyModalityDistribution` y `ReadingRhythmInsights` en `domain.model`.
     - Se implementó el caso de uso `CalculateReadingAnalyticsUseCase` para procesar de forma desacoplada y eficiente los resúmenes diarios agregados y sesiones históricas.
  2. **Mapa de Calor de Consistencia Anual (GitHub / Obsidian Luxury):**
     - Cuadrícula matricial horizontal de semanas (`AnnualConsistencyHeatmapCard`) con 5 escalas de intensidad en verde esmeralda y acentos dorados (`#1E2230` a `#34D399`).
     - Desplazamiento horizontal fluido con auto-scroll a la fecha actual y toque interactivo para inspeccionar fecha exacta y minutos discriminados por formato.
  3. **Gráfica de Tendencia Semanal (Audible vs. Kindle):**
     - Barras apiladas proporcionales para los 7 días de la semana (`WeeklyModalityChartCard`) con desglose visual en Cian Eléctrico (`#00E5FF`) y Ámbar Kindle (`#FF9800`), reportando el porcentaje relativo y total de minutos leídos en cada formato.
  4. **Perfil de Ritmo y Franja Horaria:**
     - `ReadingRhythmCard` reporta la velocidad promedio en `págs/hora`, proyecta el tiempo restante para terminar el libro activo (`~X horas`) e identifica automáticamente el horario de mayor concentración lectora (Matutino, Vespertino, Nocturno o Madrugada).
  5. **Contenedor con Pestañas de Lujo:**
     - `ReadingAnalyticsSection` agrupa estas tres perspectivas con selectores de pestaña estilizados (`[🟩 Consistencia]`, `[📊 Audible vs Kindle]`, `[⚡ Ritmo & Horario]`) y transición suave de contenido (`AnimatedContent`).
- **Consecuencias:**
  - Alta motivación intrínseca para el usuario, total visibilidad del hábito lector acumulado y análisis profundo de patrones de lectura sin sobrecargar visualmente el tablero principal.

---

## [ADR-021] Arquitectura de Navegación Inferior (Bottom Navigation) y Pestaña de Biblioteca Integral
- **Fecha:** 2026-09-29
- **Estado:** Aprobado
- **Contexto:**
  Con la incorporación del mapa de calor de consistencia anual y las métricas de hábito, una sola pantalla continua de desplazamiento saturaba la experiencia de usuario (demasiados componentes verticales compitiendo por atención). Se requería una distribución modular en pestañas dedicadas para:
  1. Mantener la pantalla de inicio limpia, enfocada en la sesión diaria de lectura y la racha.
  2. Otorgar un espacio de inmersión total a la analítica anual y gráficos semanales.
  3. Proporcionar un gestor de biblioteca completo con búsqueda y segmentación (Leyendo, Por Leer, Completados).
- **Decisión Tomada:**
  1. **Dock de Navegación Flotante (`LuxuryBottomNavigation`):**
     - Barra de navegación inferior flotante con estética Obsidian Luxury (`#111422` con borde `#2D323F` y radio de 26dp) que conmuta entre 3 destinos principales:
       - 🏠 **Inicio (`AppTab.HOME`):** Racha activa, libro activo, controles Audible/Kindle, NFC, progreso dual y sesiones recientes.
       - 📊 **Analítica (`AppTab.ANALYTICS`):** Mapa de calor anual (Heatmap 36-52 semanas), gráfica semanal apilada Audible vs. Kindle, y ritmo lector (págs/h y horario clave).
       - 📚 **Biblioteca (`AppTab.LIBRARY`):** Vista integral de catálogo con subpestañas `Leyendo`, `Por Leer` y `Completados`, barra de búsqueda en tiempo real, botón para agregar libros y acciones de 1 toque para avanzar progreso o leer ahora.
  2. **Transición Fluida de Contenido (`AnimatedContent`):**
     - Conmutación suave entre pestañas con fundido de entrada y salida (`fadeIn` / `fadeOut`).
  3. **Preservación Total de Datos y Cero Migraciones:**
     - La clasificación en subpestañas de biblioteca se deriva dinámicamente de las entidades existentes sin requerir cambios destructivos en Room DB ni alterar los 164+ días de racha acumulada.
- **Consecuencias:**
  - Arquitectura limpia, experiencia de usuario pulida y sin fricción, orden visual absoluto y mayor facilidad para gestionar libros y explorar analítica.

---

## [ADR-022] Historial Reciente Compacto (Capped a 3 Sesiones) y Marcado de Libros Leídos en Racha Histórica
- **Fecha:** 2026-09-29
- **Estado:** Aprobado
- **Contexto:**
  1. Conforme avanza la racha (+164 días), el listado continuo de sesiones en el Inicio crecía desmedidamente, alargando la pantalla principal y degradando la ergonomía táctil.
  2. En su trayectoria histórica de más de 100 días continuos de lectura, el usuario ya ha concluido varios títulos físicos y en Kindle; requería una forma inmediata de marcar libros como leídos sin fricción, tanto desde la biblioteca como al añadir libros terminados anteriormente.
- **Decisión Tomada:**
  1. **Historial Reciente Compacto con Expansión Dinámica:**
     - La sección "Historial Reciente" en la pestaña Inicio muestra por defecto las **3 sesiones más recientes**.
     - Cabecera con contador contextual (`3 de X sesiones`) y botón interactivo `Ver todo (X) ▾` / `Mostrar menos ▴`.
     - Botón inferior tipo píldora Obsidian para expandir y colapsar el historial completo con 1 toque.
  2. **Acción Directa de Marcado "Marcar como Leído" en Biblioteca:**
     - En `LibraryScreen`, cada tarjeta de libro en progreso (`Leyendo` o `Por Leer`) cuenta con un botón de acción rápida `[✓ Marcar Leído]`.
     - Al pulsarlo, el progreso se actualiza a `totalUnits` (100%), moviéndose automáticamente a la pestaña `Completados`.
     - En la pestaña `Completados`, los libros lucen su insignia esmeralda `[✓ Completado]` y una acción `[Reabrir]` para reiniciar y releer si se desea.
  3. **Registro de Libros Ya Leídos en Racha Histórica:**
     - En `AddBookDialog`, se añade un switch/toggle Obsidian: *"¿Libro ya leído en tu racha histórica (+100 días)?"*.
     - Al activarlo, el libro se guarda directamente al 100% sin convertirlo en lectura activa en curso, registrándolo de inmediato en `Completados`.
  4. **Atajo de Finalización en Diálogo de Progreso:**
     - En `UpdatePositionDialog`, se incorpora el botón `[✓ Marcar 100% Terminado]` para culminar la obra con 1 toque.
- **Consecuencias:**
  - El Inicio se mantiene compacto, minimalista y libre de desorden vertical.
  - La biblioteca refleja fidedignamente la trayectoria de lecturas culminadas del usuario a lo largo de su hábito.

---

## [ADR-023] Cuaderno de Citas, Ideas y Reflexiones (Highlights & Notes) con Exportación Obsidian/Notion y Corrección de Alineación en Gráfica Semanal
- **Fecha:** 2026-09-29
- **Estado:** Aprobado
- **Contexto:**
  1. **Recorte de Etiquetas de Días en Gráfica Semanal:** En `WeeklyModalityChart` (pestaña Analítica), cuando las barras de domingo (S) y lunes (M) acumulaban minutos altos (ej. 24m y 93m), la fila tenía altura fija `height(110.dp)` y los textos de minutos desplazaban las etiquetas de los días fuera del marco visible inferior.
  2. **Captura de Citas y Reflexiones (Highlights & Notes):** Los lectores de Kindle y audiolibros capturan ideas clave, citas memorables o reflexiones al cerrar una sesión o al repasar un libro. Se requería poder registrarlas, explorarlas en la biblioteca y exportarlas a Obsidian o Notion en formato Markdown limpio con 1 toque.
- **Decisión Tomada:**
  1. **Corrección de Alineación en `WeeklyModalityChart`:**
     - Se eliminó el `height(110.dp)` restrictivo del contenedor horizontal y se asignó una caja de minutos fija `Box(height = 16.dp)` en la parte superior de cada columna de día.
     - La barra vertical se acota a `height(84.dp)` con alineación inferior `Alignment.BottomCenter`.
     - Todos los círculos de días (L, M, M, J, V, S, D) comparten ahora la misma línea base visual y no se desplazan ni se ocultan al llenarse la barra.
  2. **Persistencia Directa de Notas sin Migración Destructiva:**
     - La entidad `ReadingSessionEntity` en SQLite ya contenía el campo `notes: String? = null`.
     - Se añadió `updateSessionNotes(sessionId, notes)` en `ReadingSessionDao` y repositorio, garantizando 0 migraciones y 0 riesgo de pérdida de la racha de 164+ días.
  3. **Subpestaña "Citas & Notas" en Biblioteca:**
     - Nueva subpestaña `LibrarySubTab.NOTES("Citas & Notas", "💡")` en `LibraryScreen`.
     - Tarjetas Obsidian con comillas estilizadas, libro asociado, fecha, indicador de página/locación, y botón de 1 toque **"Copiar MD"** que copia la cita al portapapeles con formato Markdown estándar (`> Cita \n\n*— Libro por Autor*`) y muestra un Toast confirmatorio.
     - Buscador en tiempo real para filtrar notas por texto, libro o autor.
     - Botón `+ Nueva Cita` para agregar reflexiones directamente a cualquier libro del catálogo.
  4. **Edición y Captura de Reflexiones en `SessionDetailDialog`:**
     - Campo interactivo en el detalle de sesión para escribir o dictar por voz reflexiones al cerrar una lectura, guardarlas y exportarlas en Markdown.
- **Consecuencias:**
  - Gráfica semanal 100% visible y armónica en todas las resoluciones de pantalla.
  - Flujo de Second Brain (Obsidian / Notion) plenamente integrado al hábito diario de lectura.

---

## [ADR-024] Metas Anuales / Mensuales Configurables y Sistema de Logros Obsidian (Gamificación Elegante)
- **Fecha:** 2026-09-29
- **Estado:** Aprobado
- **Contexto:**
  Para fomentar el compromiso a largo plazo sin caer en interfaces ruidosas o infantiles, se requería un sistema de gamificación discreto, lujoso y adaptado a lectores profundos (Kindle y audiolibros), combinando objetivos temporales configurables con insignias de prestigio Obsidian.
- **Decisión Tomada:**
  1. **Metas Configurables y Proyecciones Dinámicas (`YearlyMonthlyGoalsCard`):**
     - **Meta Anual de Libros:** Seguimiento de libros concluidos en el año en curso vs. objetivo anual (por defecto 12 libros en 2026) con barra de progreso Obsidian Gold (`#FBBF24`).
     - **Meta Mensual de Minutos:** Conteo de minutos leídos en el mes en curso vs. objetivo mensual (por defecto 1,000 min/mes) con barra degradada cian-esmeralda (`#38BDF8` -> `#10B981`) y conversión a horas equivalentes.
     - **Modal de Ajuste Rápido (`ConfigureGoalsDialog`):** Diálogo minimalista para ajustar metas con selectores numéricos y botones rápidos (500m, 1000m, 1500m, 2000m), persistidos en `SharedPreferences` sin migraciones de base de datos.
  2. **Insignias y Milestones Obsidian (`ObsidianMilestonesCard`):**
     - Matriz 2x2 de hitos de lectura con estética de alta gama (tarjetas de cristal ahumado `#111422`, resplandor dorado y badge `DESBLOQUEADO ✨` / `EN CURSO`):
       - 👑 **Centenario de Lectura:** 100+ días de racha continua (conquistado automáticamente con los 164+ días del usuario).
       - ⚡ **Lector Bimodal:** Combinar Kindle y Audible en una misma jornada.
       - 🌙 **Lector Nocturno:** Sesiones de lectura profunda concluidas después de las 21:00 horas.
       - ☕ **Maratón de Fin de Semana:** Más de 60 minutos de lectura en una sola jornada de sábado o domingo.
     - **Modal de Detalle (`MilestoneDetailDialog`):** Al tocar cualquier insignia, despliega una vista ampliada con el trofeo radial, nivel de prestigio (*Obsidian Gold, Amber, Blue, Emerald*), criterio técnico de desbloqueo y progreso actual.
  3. **Cálculo Desacoplado y Cero Impacto en DB:**
     - El caso de uso `CalculateMilestonesAndGoalsUseCase` calcula todas las métricas de forma pura sobre los resúmenes y sesiones existentes, preservando el 100% de la base de datos Room y la racha histórica.
- **Consecuencias:**
  - Experiencia motivacional de lujo, refinada y visualmente alineada al sistema de diseño Obsidian Luxury de la app.












