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





