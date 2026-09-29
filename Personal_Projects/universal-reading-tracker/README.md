# Universal Reading Tracker (Android) 📖🎧✨

Aplicación Android nativa para registrar y unificar de forma integral los hábitos de lectura a través de múltiples modalidades:
- 🎧 **Audiolibros:** Detección automática en **Audible** (extensible a Spotify, Storytel, etc.) vía `MediaSession` y control de pausas interactivo.
- 📱 **Kindle Físico & E-Readers:** Temporizador inteligente con Quick Action / Tile para registrar sesiones de lectura con cálculo de páginas leídas y ritmo (págs/hora).
- 📚 **Libros Impresos / Físicos:** Registro flexible de tiempo y páginas.
- 🔄 **Lectura Híbrida:** Soporte para títulos consumidos tanto en audio como en texto.

---

## 📋 Documentación de Arquitectura y Especificaciones (SDD)

- 📄 **[spec.md](spec.md)**: Especificación funcional completa, requerimientos de negocio (RF-01 a RF-14), modelo de entidades de dominio y flujos operativos.
- 🤖 **[AGENTS.md](AGENTS.md)**: Guía operativa, comandos de build, reglas de scope y lineamientos para agentes de IA (conforme al estándar open source AGENTS.md).
- 🏛️ **[decisions.md](decisions.md)**: Registro de decisiones de arquitectura (ADRs):
  - **ADR-001:** Detección híbrida vía `NotificationListenerService` / `MediaSessionManager` en Android.
  - **ADR-002:** Criterio de tiempo de reloj real dedicado (wall-clock time neto).
  - **ADR-003:** Arquitectura de adaptadores desacoplada (`ReadingProviderAdapter`).
  - **ADR-004:** Control de pausas con notificación interactiva y botones rápidos.
  - **ADR-005:** Stack nativo: Kotlin + Jetpack Compose + Room DB + Clean Architecture.
  - **ADR-006:** Modelo local-first y privacidad total de datos.
  - **ADR-007:** Soporte multimodal unificado (Audiolibros + Kindle Físico + Papel).
  - **ADR-008:** Mecanismo de registro para dispositivo físico Kindle (Temporizador Inteligente / Quick Action).
  - **ADR-009:** Calibración y sembrado de historial de racha (Backfill integral en Room DB para 163 días).
  - **ADR-010:** Manejo de sesiones a medianoche con división proporcional temporal.

---

## 🛠️ Stack Tecnológico
- **Lenguaje:** Kotlin
- **UI:** Jetpack Compose con Material Design 3
- **Arquitectura:** Clean Architecture (Domain, Data, Presentation) + MVI/MVVM
- **Base de Datos:** Room (SQLite) con soporte 100% offline
- **Concurrencia:** Kotlin Coroutines & Flow
- **Servicios del Sistema:** Android `NotificationListenerService`, `ForegroundService`, `QuickSettingsTile`
