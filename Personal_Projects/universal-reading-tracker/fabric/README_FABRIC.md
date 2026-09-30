# 🚀 Guía de Ingesta y Reportería en Microsoft Fabric con PySpark

Esta guía documenta cómo llevar tus datos de **Universal Reading Tracker** a un **Lakehouse de Microsoft Fabric** para crear reportes analíticos avanzados en **Power BI (Direct Lake)** o análisis exploratorio en Notebooks.

---

## 📥 Paso 1: Exportar los datos desde la App
1. En la app móvil, pulsa el botón **`📥 JSON`** en la esquina superior derecha del Dashboard.
2. Selecciona **Guardar en Google Drive**, **OneDrive**, o envíatelo por correo / Teams.
3. El archivo generado tendrá un nombre como:
   `universal_reading_tracker_export_2026-09-30.json`

---

## ☁️ Paso 2: Subir el JSON a tu Lakehouse en Microsoft Fabric
1. Abre tu espacio de trabajo en [Microsoft Fabric](https://app.fabric.microsoft.com/).
2. Entra a tu **Lakehouse** (o crea uno nuevo, ej: `lh_reading_analytics`).
3. En la sección **Files**, crea una carpeta llamada `reading_tracker`.
4. Sube tu archivo JSON a esa carpeta:
   `Files/reading_tracker/universal_reading_tracker_export_2026-09-30.json`

---

## ⚡ Paso 3: Ejecutar el Notebook PySpark
1. En tu Lakehouse de Fabric, haz clic en **New notebook** (o abre uno existente).
2. Pega el código de [`fabric_reading_lakehouse.py`](fabric_reading_lakehouse.py).
3. Haz clic en **Run all** (`Ctrl + Enter`).

### ¿Qué hace este script automáticamente?
- **Lectura Multilínea:** Lee el archivo `.json` jerárquico directamente desde OneLake.
- **Normalización (Arquitectura Medallion):**
  - Crea la tabla Delta `silver_reading_sessions` (con todas las sesiones históricas, duraciones, páginas leídas, velocidad en págs/h y citas/notas).
  - Crea la tabla Delta `silver_daily_reading_summaries` (con todos tus 164+ días, minutos de Kindle, minutos de Audible y estado de racha).
  - Crea la tabla Delta `silver_books_catalog` (con el catálogo, formato de libro y porcentaje de avance).
  - Crea la tabla Delta `silver_milestones` (con las insignias conquistadas).
- **Vistas Gold para BI:**
  - `gold_reading_kpis`: KPIs ejecutivos globales (minutos totales, horas acumuladas, % Audible vs % Kindle, días bimodales).
  - `gold_book_reading_velocity`: Velocidad media de lectura (págs/h), sesiones por libro y horas dedicadas.
  - `gold_monthly_reading_trend`: Evolución de minutos y días activos mes a mes.

---

## 📊 Paso 4: Crear tu Reporte en Power BI (Direct Lake)
1. En tu Lakehouse de Fabric, ve a **SQL analytics endpoint** o a **New Power BI semantic model**.
2. Selecciona las tablas `silver_reading_sessions`, `silver_daily_reading_summaries` y las vistas `gold_*`.
3. Haz clic en **New Report**.
4. ¡Listo! Ya puedes armar un dashboard con gráficos de barras, tarjetas de KPIs y matrices de consistencia directamente enlazadas a tu hábito de lectura diario.
