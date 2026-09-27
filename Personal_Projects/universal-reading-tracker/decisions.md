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


