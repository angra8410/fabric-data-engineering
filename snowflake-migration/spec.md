# Especificaciones de Aplicación: Executive Sales & Procurement Intelligence

## 1. Resumen Ejecutivo y Objetivos
- **Problema de Negocio:** La migración analítica desde Snowflake a Microsoft Fabric (modelo TPC-H Gold Direct Lake) requiere una interfaz ejecutiva moderna e intuitiva de nivel de aplicación empresarial, que elimine la navegación estática de Power BI tradicional y ofrezca análisis de ventas, correlación de pricing, monitoreo de stock crítico y perfiles de cliente contextuales.
- **Propuesta de Solución:** Construcción de un reporte estructurado en formato PBIR con diseño tipo aplicación (App Layout): barra lateral izquierda fija con Page Navigator dinámico, header superior flotante, cajón colapsable de filtros (Flyout Slicer Panel) controlado por marcadores sin pérdida de contexto de datos, y tooltips modernos enriquecidos de página para inspección rápida de clientes.
- **Entorno Fabric:**
  - Workspace: `ws_dp600-prep` (`cfeefa92-730d-43b2-b2b1-9c46826d5807`)
  - Subcarpeta Fabric: `snowflake-migration` (`f49ec5b2-45d5-43dd-b1f2-2658424c3811`)
  - Modelo Semántico: `sm_tpch_gold_directlake` (`7c36241d-42d5-4b15-913b-b907e8f3034c`)
  - Reporte: `rp_tpch_gold_directlake` (`a3947aa4-fdfe-4be1-b7d0-8ed907faa882`)

---

## 2. Requerimientos Funcionales

### RF-01: Estructura de Lienzo y Barra Lateral (App Layout)
- **Lienzo Principal:** Relación de aspecto 16:9 (1920 × 1080 px), fondo `#F4F5F7` con 0% de transparencia.
- **Barra Lateral Izquierda:** Contenedor rectangular de posición fija ($X=0, Y=0$, Ancho = 220 px, Alto = 1080 px), color `#111827` (o `#1E293B`), sin borde exterior.
- **Encabezado Superior (Header bar):** Contenedor rectangular ($X=220, Y=0$, Ancho = 1700 px, Alto = 70 px), color `#FFFFFF` con sombra inferior (*drop shadow*).
- **Título de la Aplicación:** Cuadro de texto dinámico con valor *"Executive Sales & Procurement Intelligence"*, fuente Segoe UI Semibold 16–18 pt, color `#0F172A`.

### RF-02: Navegación Automática mediante "Page Navigator"
- **Componente:** Botón *Page Navigator* ubicado en el menú lateral izquierdo ($X \approx 10, Y \approx 120$, Ancho = 200 px).
- **Disposición:** Layout vertical (1 columna) con esquinas redondeadas (radio 4 px).
- **Estados de Estilo:**
  - *Default:* Texto `#94A3B8`, fondo transparente, sin borde.
  - *On Hover:* Fondo `#334155`, texto blanco `#FFFFFF`.
  - *Selected:* Fondo `#2563EB` (o `#0EA5E9`), texto blanco `#FFFFFF`, borde izquierdo visible.
- **Ocultamiento de Navegación Nativa:** Todas las pestañas inferiores de página deben marcarse como `HiddenInViewMode` / `Hide page` para forzar el flujo exclusivo a través de la barra lateral.

### RF-03: Estructura de Páginas de la Solución
1. **Página 1 - Executive Overview:**
   - Fila de 4 Cards New (KPIs superiores):
     - Tarjeta 1: `[Net Revenue]` con etiqueta de referencia `[YoY Revenue Growth %]`.
     - Tarjeta 2: `[Total Orders]`.
     - Tarjeta 3: `[Total Quantity Sold]`.
     - Tarjeta 4: `[Total Stock Value]`.
   - Visual Principal: Gráfico de áreas (*Area chart*) de `[Net Revenue]` sobre `fact_sales[order_date]`.
   - Top Dimension: Gráfico de barras horizontal (*Clustered bar chart*) de ingresos netos por `dim_customer[customer_name]` o `dim_part[brand]`.
2. **Página 2 - Sales Analytics:**
   - Matriz interactiva de ventas cruzadas por `dim_customer[market_segment]` contra `dim_geography[region_name]` (o `nation_name`).
   - Gráfico de dispersión (*Scatter plot*): `fact_sales[discount_percentage]` vs `[Net Revenue]`, con detalle por `dim_part[brand]`.
3. **Página 3 - Inventory & Suppliers:**
   - Gráfico de Descomposición (*Decomposition Tree*): métrica analizada `[Total Stock Value]` desglosada jerárquicamente por `region_name` $\rightarrow$ `supplier_name` $\rightarrow$ `brand`.
   - Tabla de detalle: Análisis de `fact_inventory` para alertar piezas con nivel crítico de disponibilidad (`available_quantity`).

### RF-04: Panel Colapsable de Filtros (Flyout Slicer Panel)
- **Contenedor Visual:** Rectángulo flotante superpuesto ($X=220, Y=70$, Ancho = 300 px, Alto = 1010 px), fondo `#FFFFFF` con sombra perimetral derecha.
- **Segmentadores integrados:**
  - `dim_customer[market_segment]`
  - `fact_sales[order_date]` (Rango de fechas / between)
  - `dim_geography[region_name]`
- **Botón de Cierre:** Botón de acción con ícono de cierre (✕ o flecha ←) en la esquina superior derecha del panel.
- **Agrupamiento:** Grupo `Panel_Filtros` en el panel de selección (Selection Pane).
- **Gestión de Marcadores (Bookmarks):**
  - Marcador `Filtros_Open`: `Panel_Filtros` visible.
  - Marcador `Filtros_Closed`: `Panel_Filtros` oculto.
  - Configuración técnica estricta: `Data: OFF` (desmarcado), `Display: ON`, `Current Page: ON`.
- **Interacciones:**
  - Botón embudo en la barra lateral/header $\rightarrow$ Dispara marcador `Filtros_Open`.
  - Botón ✕ dentro del panel $\rightarrow$ Dispara marcador `Filtros_Closed`.

### RF-05: Tooltips Modernos de Página (Page Tooltips)
- **Página de Tooltip:** Página dedicada nombrada `Tooltip_CustomerProfile`.
- **Configuración:** Activación de *Allow use as tooltip*, tamaño de lienzo tipo *Tooltip* (320 × 240 px), visibilidad oculta (`Hide page`).
- **Contenido del Micro-Lienzo:**
  - Mini-tarjeta con segmento de mercado (`market_segment`) y teléfono del cliente (`phone`).
  - Micro-gráfico de barras con histórico de ingresos anuales (`[Net Revenue]` por año).
- **Asociación:** Asignación en el gráfico de barras horizontal de clientes (`Report page` $\rightarrow$ `Tooltip_CustomerProfile`).

---

## 3. Modelo de Dominio y Variables de Negocio

### Entidades y Tablas del Modelo TPC-H Gold:
- **`fact_sales`**: Registro de órdenes transaccionales (`order_key`, `part_key`, `supplier_key`, `customer_key`, `order_date`, `extended_price`, `discount_percentage`, `quantity`, `order_priority`).
- **`fact_inventory`**: Instantánea de inventario (`part_key`, `supplier_key`, `available_quantity`, `supply_cost`).
- **`dim_customer`**: Clientes (`customer_key`, `customer_name`, `market_segment`, `phone`, `nation_key`).
- **`dim_geography`**: Jerarquía geográfica (`nation_key`, `nation_name`, `region_key`, `region_name`).
- **`dim_part`**: Catálogo de piezas (`part_key`, `part_name`, `brand`, `type`, `size`, `retail_price`).
- **`dim_supplier`**: Proveedores (`supplier_key`, `supplier_name`, `nation_key`, `account_balance`).

### Medidas DAX Principales (`_Measures.tmdl`):
```dax
[Net Revenue] = 
SUMX(fact_sales, fact_sales[extended_price] * (1 - fact_sales[discount_percentage]))

[YoY Revenue Growth %] = 
VAR _Current = [Net Revenue]
VAR _Prior = CALCULATE([Net Revenue], SAMEPERIODLASTYEAR(fact_sales[order_date]))
RETURN DIVIDE(_Current - _Prior, _Prior, BLANK())

[Total Orders] = 
DISTINCTCOUNT(fact_sales[order_key])

[Total Quantity Sold] = 
SUM(fact_sales[quantity])

[Total Stock Value] = 
SUMX(fact_inventory, fact_inventory[available_quantity] * fact_inventory[supply_cost])
```

---

## 4. Flujos de Trabajo (Workflows)
1. **Navegación Principal:** El usuario accede a la aplicación y es recibido en `Executive Overview`. El menú lateral resalta la página activa. Al seleccionar otra sección en el Page Navigator, se traslada sin mostrar pestañas de Power BI.
2. **Filtrado Contextual sin Pérdida de Estado:** Al hacer clic en el botón de embudo, se despliega el cajón lateral `Panel_Filtros`. El usuario ajusta fechas, segmento o región. Al presionar el botón de cierre ✕, el panel se oculta mientras que las selecciones de filtros permanecen intactas en todos los visuales.
3. **Inspección de Cliente en Hover:** Al pasar el cursor sobre cualquier cliente en el ranking de ventas, emerge el tooltip `Tooltip_CustomerProfile` con información complementaria instantánea sin requerir drill-through manual.

---

## 5. Criterios de Aceptación
- [x] **CA-01:** Verificación y validación de medidas DAX en `sm_tpch_gold_directlake`.
- [x] **CA-02:** Conexión y mapeo de IDs de Fabric mediante Fabric MCP (`ws_dp600-prep` / `snowflake-migration`).
- [x] **CA-03:** Aplicación del Canvas 16:9, fondo gris `#F4F5F7` y contenedores estructurados.
- [x] **CA-04:** Configuración del Header bar blanco con título dinámico.
- [x] **CA-05:** Page Navigator y ocultamiento de pestañas nativas (`HiddenInViewMode`).
- [x] **CA-06:** Implementación de las 3 páginas maestras (Executive Overview, Sales Analytics, Inventory & Suppliers).
- [ ] **CA-07:** Grupo `Panel_Filtros` y Bookmarks `Filtros_Open` / `Filtros_Closed` con `Data: OFF`.
- [x] **CA-08:** Página `Tooltip_CustomerProfile` (320 × 240) vinculada al perfil de clientes.
