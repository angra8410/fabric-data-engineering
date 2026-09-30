# MEMORY.md — Universal Reading Tracker
> **Documento de Memoria y Continuidad de Proyecto**  
> *Lectura obligatoria para cualquier Agente de IA o desarrollador al iniciar una nueva sesión para no reiniciar contexto desde cero.*  
> **Última actualización:** 2026-09-29T20:55:00-05:00 | **Rama:** `main` | **Build:** `PASS (0 errores)`

---

## 🧭 Resumen Ejecutivo
**Universal Reading Tracker** es una aplicación Android nativa (Kotlin + Jetpack Compose) de alta gama con estética **Obsidian Luxury**. Unifica en un solo lugar la lectura pasiva de audiolibros (Audible/Spotify), lectura en Kindle físico (temporizador inteligente en segundo plano inmune a suspensión de CPU), y libros impresos, consolidando una racha única y unificando el progreso del lector.

- **Directorio de trabajo:** `Personal_Projects/universal-reading-tracker/`
- **Racha Activa del Usuario:** **164+ días consecutivos** preservados intactos mediante backfill estructurado en Room DB (ADR-009).
- **Compilación & Test:** `.\gradlew.bat test assembleDebug` (¡siempre debe pasar en verde!).

---

## 🏛️ Mapa de Arquitectura y Archivos Clave

```
Personal_Projects/universal-reading-tracker/
├── app/src/main/java/com/universalreadingtracker/
│   ├── domain/
│   │   ├── model/
│   │   │   ├── Book.kt                      # Entidad Libro (Páginas, Locaciones, Formato HYBRID/EBOOK)
│   │   │   ├── ReadingSession.kt            # Sesión individual (wall-clock time, notes de reflexión)
│   │   │   ├── DailyReadingSummary.kt       # Resumen por fecha (minutos Audible, Kindle, físico)
│   │   │   ├── ReadingAnalytics.kt          # Heatmap semanal/anual, ritmo págs/h, franjas horarias
│   │   │   ├── ReadingMilestone.kt          # Hitos Obsidian y Metas (anuales/mensuales)
│   │   │   └── ReadingModality.kt           # AUDIOBOOK, EBOOK_KINDLE, PHYSICAL_BOOK
│   │   └── usecase/
│   │       ├── BackfillHistoricalStreakUseCase.kt      # Calibración y preservación de 164+ días
│   │       ├── SplitMidnightSessionUseCase.kt          # División proporcional a las 00:00
│   │       ├── CalculateReadingAnalyticsUseCase.kt     # Heatmap anual, distribución y ritmo
│   │       └── CalculateMilestonesAndGoalsUseCase.kt   # Metas y cálculo de 4 insignias Obsidian
│   ├── data/
│   │   ├── local/
│   │   │   ├── AppDatabase.kt               # Room Database (entities: Book, ReadingSession, DailySummary)
│   │   │   └── dao/                         # BookDao, ReadingSessionDao, DailyReadingSummaryDao
│   │   └── repository/                      # Implementaciones de repositorios
│   ├── service/
│   │   ├── AudibleNotificationListenerService.kt  # Detección pasiva automática de Audible
│   │   ├── KindleReadingTimerService.kt           # Cronómetro de lectura en segundo plano
│   │   └── ReadingReminderScheduler.kt            # Recordatorio preventivo diario 9:00 PM
│   ├── widget/
│   │   └── ReadingAppWidgetProvider.kt      # Widget nativo de pantalla de inicio 4x2
│   └── presentation/
│       ├── MainActivity.kt                  # Punto de entrada, NFC y cableado de eventos
│       ├── dashboard/
│       │   ├── DashboardViewModel.kt        # StateFlow central, sincronización y Room observers
│       │   ├── DashboardState.kt            # UI State completo (streak, analytics, goals, milestones)
│       │   ├── DashboardScreen.kt           # Pantalla principal con dock de 3 pestañas y diálogos
│       │   └── analytics/
│       │       ├── AnalyticsScreen.kt             # Tab 2: Metas, Milestones, Heatmap y Ritmo
│       │       ├── GoalsAndMilestonesCards.kt     # Metas anual/mensual + 4 Insignias Obsidian
│       │       ├── AnnualConsistencyHeatmapCard.kt# Heatmap matriz anual estilo GitHub
│       │       ├── WeeklyModalityChart.kt         # Gráfica semanal Audible vs. Kindle
│       │       └── ReadingRhythmCard.kt           # Ritmo págs/h y franjas horarias
│       └── library/
│           └── LibraryScreen.kt             # Tab 3: Leyendo, Por Leer, Completados, Citas & Notas
├── spec.md                                  # Especificación funcional viva (RF-01 a RF-20)
├── decisions.md                             # Bitácora de arquitectura (ADR-001 a ADR-024)
└── AGENTS.md                                # Reglas operativas para Agentes de IA
```

---

## 🌟 Funcionalidades Implementadas y Estado Actual

### 1. Dock Inferior Flotante de 3 Pestañas (`AppTab`)
- 🏠 **Inicio (`HOME`):**
  - Tarjeta trofeo con racha consolidada (**🔥 164 días**).
  - Libro activo en lectura con selector modal y ajuste de página/locación.
  - Controles de hardware (Temporizador Kindle físico + estado de Audible + NFC).
  - Medidor de meta diaria (30 min) y desglose de hoy.
  - **Historial Reciente Compacto:** Muestra las 3 sesiones más recientes por defecto con botón interactivo de expansión (`Ver todo` / `Mostrar menos`) para evitar saturación de pantalla (ADR-022).
- 📊 **Analítica (`ANALYTICS`):**
  - **Compromiso Lector (Metas):** Barras de progreso anual (ej. 12 libros en 2026) y mensual (1,000 min) con diálogo `Ajustar` (ADR-024).
  - **Insignias & Milestones Obsidian:** 4 hitos con diálogo interactivo al toque:
    1. 👑 **Centenario de Lectura:** 100+ días de racha (*Desbloqueado por los 164+ días*).
    2. ⚡ **Lector Bimodal:** Combinar Audible y Kindle en el mismo día.
    3. 🌙 **Lector Nocturno:** Sesiones de lectura profunda tras las 21:00 horas.
    4. ☕ **Maratón de Finde:** Más de 60 min leídos en sábado o domingo.
  - **Heatmap Anual:** Matriz de 52 semanas con 5 niveles de intensidad esmeralda Obsidian.
  - **Tendencia Semanal:** Gráfica de barras apiladas Audible vs. Kindle con alineación de días garantizada.
  - **Ritmo de Lectura:** Páginas/hora y franjas horarias (Matutino, Vespertino, Nocturno, Madrugada).
- 📚 **Biblioteca (`LIBRARY`):**
  - Subpestañas: `📖 Leyendo`, `⏳ Por Leer`, `✅ Completados`, `💡 Citas & Notas`.
  - Buscador en tiempo real por título o autor.
  - Acción rápida **`[✓ Marcar Leído]`** para mover libros concluidos a `Completados`.
  - Acción en alta de libro para registrar obras concluidas en la racha histórica (+100 días).
  - **Cuaderno de Citas & Notas:** Citas memorables de sesiones con botón **`Copiar MD`** para exportar a Obsidian / Notion con formato Markdown estándar (ADR-023).

---

## 🔒 Reglas Críticas Innegociables (Invariants)

1. **NO Destructive Migrations:**
   - La base de datos SQLite contiene 164+ días de historial del usuario. **NUNCA** ejecutar `fallbackToDestructiveMigration(true)` ni borrar la base de datos.
   - Cualquier nueva propiedad de configuración debe almacenarse en `SharedPreferences` o derivarse en tiempo de ejecución.
2. **Validación Automática de Build:**
   - Siempre ejecutar `.\gradlew.bat test assembleDebug` antes de considerar completada cualquier tarea.
3. **Estética Obsidian Luxury:**
   - Fondo oscuro profundo: `#0D0E11`
   - Superficies de tarjetas elevadas: `#111422` y bordes `#252C48`
   - Acentos: Oro Obsidian (`#FBBF24`), Azul Eléctrico (`#38BDF8`), Esmeralda (`#10B981`), Ámbar Audible (`#FF9900`).
4. **Sincronización Bidireccional de Documentación:**
   - Toda nueva decisión arquitectónica se documenta en [decisions.md](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/Personal_Projects/universal-reading-tracker/decisions.md) como ADR.
   - Todo nuevo requerimiento funcional se documenta en [spec.md](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/Personal_Projects/universal-reading-tracker/spec.md) como RF.

---

## 💡 Próximos Pasos Sugeridos / Backlog para Sesiones Futuras
- **Autocompletado de Portadas con OpenLibrary API:** Buscar carátulas y sinopsis oficiales al tipear el título de un libro.
- **Acciones NFC:** Permitir vincular stickers NFC físicos colocados detrás del Kindle para iniciar/parar el temporizador con solo acercar el móvil.
- **Respaldo & Exportación:** Exportar e importar base de datos completa en JSON comprimido para backup en Google Drive.
- **Widget Quick Settings Tile:** Acceso directo desde la barra de notificaciones de Android para conmutar el temporizador Kindle con pantalla bloqueada.
