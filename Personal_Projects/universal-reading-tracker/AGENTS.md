# AGENTS.md

> **Guía operativa y reglas del proyecto para Agentes de IA (Universal Reading Tracker)**  
> Compatible con Antigravity IDE, Cursor, Windsurf, Devin, GitHub Copilot, Jules y herramientas conformes al estándar `AGENTS.md`.

---

## 📌 Visión General del Proyecto

**Universal Reading Tracker** es una aplicación Android nativa diseñada para registrar y unificar de forma integral los hábitos de lectura multimodales (Audiolibros en Audible/Spotify, E-Readers/Kindle físico y Libros impresos) con un diseño Obsidian Luxury de alta fidelidad, cálculo de métricas en tiempo real y persistencia local-first.

- **Lenguaje:** Kotlin
- **UI:** Jetpack Compose + Material Design 3 (Obsidian Luxury theme)
- **Arquitectura:** Clean Architecture (Domain, Data, Presentation) + MVI/MVVM
- **Persistencia:** Room DB (SQLite) 100% offline
- **Concurrencia:** Kotlin Coroutines (`StateFlow`, `SharedFlow`, `Flow`)
- **Servicios:** Foreground Services (`ReadingTrackerService`), WorkManager (`DailyReadingReminderWorker`), BroadcastReceivers

---

## 🔒 Scope Lock (Regla Crítica)

- **Subdirectorio Activo:** Todo el trabajo debe ejecutarse y limitarse **estrictamente** dentro de:
  `Personal_Projects/universal-reading-tracker/`
- **Prohibido:** Modificar, eliminar o escanear archivos fuera de esta carpeta o en la raíz del repositorio multirepo a menos que el usuario lo pida explícitamente.

---

## 🛠️ Comandos de Desarrollo y Verificación

Todos los comandos deben ejecutarse desde el directorio raíz del proyecto (`Personal_Projects/universal-reading-tracker/`):

### Compilación y Verificación de Sintaxis (Rápido)
```powershell
.\gradlew.bat compileDebugKotlin
```

### Ejecutar Tests Unitarios
```powershell
.\gradlew.bat test
```

### Compilar APK Debug + Ejecutar Tests (Comprobación Completa)
```powershell
.\gradlew.bat test assembleDebug
```

> ⚠️ **Regla de Oro:** Siempre ejecutar y validar que `.\gradlew.bat test assembleDebug` pase en verde (cero errores) antes de finalizar una tarea o realizar un commit.

---

## 🏛️ Convenciones de Arquitectura y Código

### 1. Clean Architecture por Capas
- `domain/`: Modelos de negocio puros, interfaces de repositorios y UseCases. **Cero dependencias del framework Android** (excepto anotaciones mínimas).
- `data/`: Implementación de repositorios, Room Entities, DAOs, TypeConverters y adaptadores de servicios.
- `presentation/`: ViewModels, UI States (`*UiState`), composables de Jetpack Compose y temas.

### 2. Estilo y Patrones de UI (Obsidian Luxury)
- Respetar la paleta de colores Obsidian Luxury:
  - Fondo primario: `#0D0E11`
  - Superficies / Cards elevadas: `#16181D` / `#222630`
  - Bordes sutiles: `#2D323F` o blanco con alpha bajo (`0.08f`)
  - Acentos de lectura / Racha: Ámbar / Dorado (`#E5A93C`, `#D4AF37`) y Esmeralda (`#10B981`)
  - Textos: Blanco casi puro `#F3F4F6` (títulos) y Gris tenue `#9CA3AF` (metadatos)
- Usar iconos vectoriales de Material Icons (`Icons.Filled.*`, `Icons.Outlined.*`).
- Añadir micro-animaciones en tarjetas interactivas (`animateFloatAsState`, `animateColorAsState`, `AnimatedVisibility`).

### 3. Invariantes Críticas y Gotchas de Dominio

1. **Temporizador y Medición de Tiempo (ADR-002, ADR-018):**
   - **NUNCA** calcular la duración total de una sesión contando únicamente ticks de corrutinas (`delay(1000)`). El modo *Doze* de Android y la suspensión de CPU congelan los timers periódicos.
   - **SIEMPRE** calcular la duración real usando tiempo de reloj de pared (`System.currentTimeMillis() - startTimestampMs - pausedDurationMs`).
   - La base de datos y la sesión activa deben guardar `startTime` y `endTime` basados en timestamps UTC/epoch reales.
   
2. **Cálculo y Calibración de Racha (ADR-009, ADR-015, RF-06):**
   - La aplicación cuenta con una calibración histórica base (164 días sembrados) más los días de lectura activos calculados dinámicamente desde Room DB.
   - El widget semanal (`D`, `L`, `M`, `M`, `J`, `V`, `S`) debe reflejar con exactitud la semana actual o seleccionada, marcando los días leídos y desactivando visualmente los días futuros de la semana en curso.

3. **Notificación y Recordatorio Diario (ADR-016):**
   - Programado vía `WorkManager` (`PeriodicWorkRequestBuilder`) para ejecutarse diariamente a las 9:00 PM (hora local de Colombia, America/Bogota).
   - Comprueba si el usuario ya registró lectura en el día actual; si ya leyó, no emite alerta molesta.

---

## 📖 Gestión de Especificaciones (SDD) y Decisiones

Cualquier cambio de comportamiento, nuevo requerimiento o refactor estructural debe reflejarse en:
1. [spec.md](spec.md): Mantener actualizados los Requerimientos Funcionales (RF-01 a RF-14), modelos de dominio y flujos de usuario.
2. [decisions.md](decisions.md): Cada decisión arquitectónica o ajuste de lógica debe documentarse cronológicamente como un nuevo ADR (`ADR-019`, `ADR-020`, etc.), siguiendo la estructura:
   - Estado (Aceptado / Propuesto)
   - Contexto
   - Decisión
   - Consecuencias / Impacto

---

## 📝 Convención de Mensajes de Git / Commits

Formato estándar de Conventional Commits con referencia al ADR cuando aplique:

```
feat(<modulo>): <descripción breve en minúsculas> (ADR-xxx)
fix(<modulo>): <descripción del error corregido> (ADR-xxx)
docs(<modulo>): <actualización de documentación o especificación>
refactor(<modulo>): <mejora interna sin cambio funcional>
```

**Ejemplos reales del proyecto:**
- `feat(history): interactive session metrics detail card and book continuation (ADR-017)`
- `fix(timer): wall-clock duration resilient to Android doze and auto-repair throttled sessions (ADR-018)`
- `docs(agents): add AGENTS.md project specification for AI coding agents`
