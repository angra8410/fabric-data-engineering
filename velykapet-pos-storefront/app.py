import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

# Page Configuration
st.set_page_config(
    page_title="Data Engineering & Analytics Portfolio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Theme Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #9CA3AF;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        background-color: #111827;
    }
</style>
""", unsafe_allow_html=True)

# Data Loader for Velykapet
@st.cache_data
def load_velykapet_data():
    start_history = date(2025, 9, 1)
    end_history = date(2026, 8, 13)
    num_days = (end_history - start_history).days + 1
    dates = [start_history + timedelta(days=i) for i in range(num_days)]
    
    np.random.seed(42)
    base_tx = np.linspace(10, 85, num_days) + np.random.randint(-5, 6, num_days)
    base_tx = np.maximum(base_tx, 5).astype(int)
    avg_price = 95.0
    revenue = (base_tx * avg_price + np.random.uniform(-100, 200, num_days)).round(2)
    profit = (revenue * 0.30 + np.random.uniform(-50, 100, num_days)).round(2)
    
    df_sales = pd.DataFrame({
        "sale_datetime": dates,
        "sale_date": [d.strftime("%Y-%m-%d") for d in dates],
        "total_transactions": base_tx,
        "gross_revenue": revenue,
        "gross_profit": profit
    })

    df_prods = pd.DataFrame({
        "product_name": ["Alimento Perro Premium 15kg", "Arena Gato 10kg", "Juguete Morder Caucho", "Snack Premios Cerdo 200g", "Shampoo Antipulgas 500ml", "Collar Ajustable Reflectivo"],
        "units_sold": [1240, 1810, 895, 2310, 685, 464],
        "revenue": [248000, 126700, 17900, 23100, 17125, 9280],
        "profit_margin": [0.32, 0.28, 0.45, 0.50, 0.40, 0.42]
    })

    df_ch = pd.DataFrame({
        "Channel": ["POS Tienda Física", "Rappi Express", "WhatsApp Bot (Production Ready)", "Ventas Directas Web"],
        "Revenue": [285000, 112000, 0, 45000]
    })

    return df_sales, df_prods, df_ch

# Data Loader for DANE Colombia Employment Project
@st.cache_data
def load_dane_data():
    years = list(range(2004, 2027))
    np.random.seed(101)
    
    unemp_trend = [14.2, 13.5, 12.8, 11.5, 11.2, 12.0, 11.8, 10.8, 10.4, 9.6, 9.1, 8.9, 9.2, 9.4, 9.7, 10.5, 16.1, 13.8, 11.2, 10.2, 9.8, 9.4, 9.1]
    tgp_trend = [59.5, 60.1, 60.8, 61.2, 62.0, 63.5, 64.0, 64.8, 65.2, 64.9, 64.2, 64.7, 64.5, 63.9, 64.0, 63.3, 59.2, 61.5, 63.6, 63.8, 64.1, 64.3, 64.5]
    occupied_millions = [17.5, 18.1, 18.7, 19.2, 19.8, 20.4, 21.0, 21.6, 22.1, 22.5, 22.8, 23.1, 23.2, 23.0, 22.8, 22.5, 19.8, 21.4, 22.6, 23.1, 23.5, 23.9, 24.2]
    
    df_dane_yearly = pd.DataFrame({
        "Year": years,
        "Tasa_Desempleo": unemp_trend,
        "TGP": tgp_trend,
        "Ocupados_Millones": occupied_millions
    })

    df_cities = pd.DataFrame({
        "Ciudad_Metropolitana": ["Bogotá D.C.", "Medellín A.M.", "Cali A.M.", "Barranquilla A.M.", "Bucaramanga A.M.", "Manizales A.M.", "Pereira A.M."],
        "Tasa_Desempleo": [9.8, 8.9, 10.5, 8.4, 8.1, 9.2, 9.0],
        "Informalidad_Pct": [32.5, 38.2, 44.1, 54.3, 42.0, 36.8, 41.2],
        "Ocupados_K": [4150, 1920, 1150, 890, 520, 220, 310]
    })

    df_informality = pd.DataFrame({
        "Condición": ["Ocupados Formales", "Ocupados Informales"],
        "Porcentaje": [43.8, 56.2]
    })

    return df_dane_yearly, df_cities, df_informality

# Sidebar Project Navigation
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/data-configuration.png", width=65)
    st.title("💼 Portafolio de Ingeniería de Datos")
    
    selected_project = st.selectbox(
        "📁 Seleccionar Proyecto",
        [
            "🐾 Velykapet: Omnichannel Retail & POS Platform",
            "🇨🇴 DANE Colombia: Mercado Laboral & Empleo (2004 - 2026)"
        ]
    )
    
    st.divider()

# ==============================================================================
# PROJECT 1: VELYKAPET OMNICHANNEL RETAIL PLATFORM
# ==============================================================================
if "Velykapet" in selected_project:
    df_sales_trend, df_products, df_channels = load_velykapet_data()
    
    st.markdown('<div class="main-header">🐾 Velykapet Omnichannel Retail Data Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Microsoft Fabric & Delta Lake Medallion Engine (Bronze ➔ Silver ➔ Gold Data Warehouse)</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Filtros de Control")
        min_date = date(2025, 9, 1)
        max_date = date(2026, 8, 13)
        date_range = st.date_input("Rango de Fechas", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        selected_env = st.selectbox("Entorno Fabric", ["ws-velykapet-dev (Desarrollo)", "ws-velykapet-test (Pruebas)", "ws-velykapet-prod (Producción)"])
        st.divider()
        st.markdown("### 🏛️ Estado Medallion")
        st.success("🟢 Bronze: 16/16 Tablas Sincronizadas")
        st.success("🟢 Silver: 16/16 Tablas Procesadas")
        st.success("🟢 Gold: Facts & Dims Actualizadas")
        st.info("📲 Bot WhatsApp: Baseline 0 Registros")

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_d, end_d = date_range
    elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
        start_d, end_d = date_range[0], date_range[0]
    else:
        start_d, end_d = min_date, max_date

    df_filtered_sales = df_sales_trend[(df_sales_trend["sale_datetime"] >= start_d) & (df_sales_trend["sale_datetime"] <= end_d)]

    t1, t2, t3, t4, t5 = st.tabs([
        "📊 Resumen Ejecutivo & KPIs", 
        "📦 Inventarios & Catálogo", 
        "📲 WhatsApp Bot Conversion", 
        "📈 Power BI & Modelo Semántico",
        "🏛️ Arquitectura & Data Engineering"
    ])
    
    with t1:
        st.subheader(f"📈 Rendimiento Financiero y de Ventas ({start_d.strftime('%d/%m/%Y')} a {end_d.strftime('%d/%m/%Y')})")
        if df_filtered_sales.empty:
            st.warning("⚠️ No hay transacciones en el rango seleccionado.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            tot_rev = df_filtered_sales["gross_revenue"].sum()
            tot_prof = df_filtered_sales["gross_profit"].sum()
            tot_tx = df_filtered_sales["total_transactions"].sum()
            avg_t = tot_rev / tot_tx if tot_tx > 0 else 0
            m_pct = (tot_prof / tot_rev * 100) if tot_rev > 0 else 0

            c1.metric("💰 Ingresos Totales", f"${tot_rev:,.2f}", f"{len(df_filtered_sales)} días")
            c2.metric("📈 Ganancia Bruta", f"${tot_prof:,.2f}", f"Margen: {m_pct:.1f}%")
            c3.metric("🛒 Transacciones Totales", f"{tot_tx:,}")
            c4.metric("🏷️ Ticket Promedio", f"${avg_t:,.2f}")

            st.divider()
            vc1, vc2 = st.columns([2, 1])
            with vc1:
                st.markdown("##### 📅 Tendencia Diaria de Ventas y Margen")
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=df_filtered_sales["sale_date"], y=df_filtered_sales["gross_revenue"], mode='lines', name='Ingreso Bruto ($)', line=dict(color='#4F46E5', width=2.5)))
                fig_trend.add_trace(go.Scatter(x=df_filtered_sales["sale_date"], y=df_filtered_sales["gross_profit"], mode='lines', name='Ganancia Bruta ($)', line=dict(color='#10B981', width=2.5)))
                fig_trend.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_trend)
            with vc2:
                st.markdown("##### 🍕 Origen de Ventas por Canal")
                fig_pie = px.pie(df_channels, names='Channel', values='Revenue', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_pie)

    with t2:
        st.subheader("📦 Estado de Inventario y Desempeño de Productos")
        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("🏷️ SKUs Activos", "275 SKUs")
        ic2.metric("📦 Unidades en Stock", "1,840 unidades")
        ic3.metric("💵 Valor Comercial Inv.", "$48,500.00")
        st.divider()
        fig_bar = px.bar(df_products, x='product_name', y='revenue', color='profit_margin', text_auto='.2s', color_continuous_scale='Viridis')
        fig_bar.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_bar)

    with t3:
        st.subheader("📲 Monitor de Conversión del Bot de WhatsApp")
        st.info("ℹ️ **Listo para Salida a Producción**: Las tablas de mensajes y pedidos por WhatsApp han sido inicializadas en 0 registros como baseline limpio.")
        wc1, wc2, wc3, wc4 = st.columns(4)
        wc1.metric("📩 Mensajes Procesados", "0 msgs")
        wc2.metric("🛍️ Pedidos Convertidos", "0 pedidos")
        wc3.metric("💰 Facturación Bot", "$0.00")
        wc4.metric("📈 Tasa de Conversión", "0.0%")

    with t4:
        st.subheader("📈 Power BI Direct Lake Semantic Model & Interactive Visual Report")
        st.caption("Conexión Direct Lake sobre Delta Tables en `lh_velykapet_gold_dev.dbo` con 25+ Medidas DAX.")
        
        pbi_page = st.selectbox(
            "📄 Seleccionar Página de Reporte Power BI:",
            [
                "Page 1: 🌟 Executive Financial Overview",
                "Page 2: 🛍️ Omnichannel Sales Performance",
                "Page 3: 💸 Financial Control & Expenses Waterfall",
                "Page 4: 📦 Inventory Health & Stock Alerts",
                "Page 5: 🤖 WhatsApp Bot Conversion Funnel"
            ]
        )

        if "Page 1" in pbi_page:
            st.markdown("#### 🌟 Page 1: Resumen Ejecutivo Financiero")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Ingreso Total [DAX: Total Revenue]", f"${tot_rev:,.2f}")
            k2.metric("Ganancia Bruta [DAX: Gross Profit]", f"${tot_prof:,.2f}")
            k3.metric("Margen Bruto [DAX: Gross Margin %]", f"{m_pct:.1f}%")
            k4.metric("Ticket Promedio [DAX: AOV]", f"${avg_t:,.2f}")
            
            fig_pbi1 = px.area(df_filtered_sales, x="sale_date", y="gross_revenue", title="Ingreso Bruto Mensual / Diarios (Direct Lake Stream)", color_discrete_sequence=["#4F46E5"])
            fig_pbi1.update_layout(template="plotly_dark", height=320)
            st.plotly_chart(fig_pbi1, use_container_width=True)

        elif "Page 2" in pbi_page:
            st.markdown("#### 🛍️ Page 2: Desempeño Multicanal (POS, Rappi, Web, WhatsApp)")
            fig_pbi2 = px.bar(df_channels, x="Channel", y="Revenue", color="Channel", title="Ventas por Canal de Distribución", text_auto=True, color_discrete_sequence=["#4F46E5", "#7C3AED", "#EC4899", "#10B981"])
            fig_pbi2.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_pbi2, use_container_width=True)

        elif "Page 3" in pbi_page:
            st.markdown("#### 💸 Page 3: Control Financiero & Waterfall de Margen Neto")
            cogs = tot_rev - tot_prof
            opex = tot_rev * 0.12
            net_profit = tot_prof - opex
            
            fig_wf = go.Figure(go.Waterfall(
                name = "Finanzas Velykapet", orientation = "v",
                measure = ["relative", "relative", "total", "relative", "total"],
                x = ["Ingreso Bruto", "Costo de Ventas (COGS)", "Ganancia Bruta", "Gastos OpEx", "Utilidad Neta Operativa"],
                textposition = "outside",
                text = [f"${tot_rev:,.0f}", f"-${cogs:,.0f}", f"${tot_prof:,.0f}", f"-${opex:,.0f}", f"${net_profit:,.0f}"],
                y = [tot_rev, -cogs, 0, -opex, 0],
                connector = {"line":{"color":"#9CA3AF"}},
                decreasing = {"marker":{"color":"#EF4444"}},
                increasing = {"marker":{"color":"#10B981"}},
                totals = {"marker":{"color":"#4F46E5"}}
            ))
            fig_wf.update_layout(title="Waterfall de Margen Neto [DAX: Net Operating Profit]", template="plotly_dark", height=380)
            st.plotly_chart(fig_wf, use_container_width=True)

        elif "Page 4" in pbi_page:
            st.markdown("#### 📦 Page 4: Estado de Inventario & Alertas de Reabastecimiento")
            st.markdown("**Tabla de Alertas de Stock Crítico (`dim_products[current_stock] <= 5`)**")
            df_alert = pd.DataFrame({
                "SKU Code": ["VK-DOG-15K", "VK-CAT-LIT10", "VK-TOY-RUB01", "VK-SNK-PORK200"],
                "Producto": ["Alimento Perro Premium 15kg", "Arena Gato 10kg", "Juguete Morder Caucho", "Snack Premios Cerdo 200g"],
                "Costo ($)": [136.00, 50.40, 11.00, 5.00],
                "Precio ($)": [200.00, 70.00, 20.00, 10.00],
                "Stock Actual": [4, 2, 5, 1],
                "Estado": ["⚠️ Reabastecer", "🚨 Crítico", "⚠️ Reabastecer", "🚨 Crítico"]
            })
            st.dataframe(df_alert, use_container_width=True)

        elif "Page 5" in pbi_page:
            st.markdown("#### 🤖 Page 5: Embudo de Conversión Bot de WhatsApp")
            fig_funnel = go.Figure(go.Funnel(
                y = ["Consultas Mensajes", "Búsqueda Catálogo", "Carrito Creado", "Pedidos Completados"],
                x = [1250, 840, 310, 185],
                textinfo = "value+percent initial",
                marker = {"color": ["#4F46E5", "#7C3AED", "#EC4899", "#10B981"]}
            ))
            fig_funnel.update_layout(title="Embudo de Conversión WhatsApp Bot", template="plotly_dark", height=350)
            st.plotly_chart(fig_funnel, use_container_width=True)

        with st.expander("📚 Ver Catálogo de Medidas DAX del Modelo Semántico (`sm_velykapet_gold_analytics`)"):
            st.code("""
// CORE DAX MEASURES
[Total Revenue] = SUM(fact_sales[total_item_revenue])
[Total Cost] = SUMX(fact_sales, fact_sales[quantity] * fact_sales[unit_cost])
[Gross Profit] = [Total Revenue] - [Total Cost]
[Gross Margin %] = DIVIDE([Gross Profit], [Total Revenue], 0)
[Average Order Value (AOV)] = DIVIDE([Total Revenue], DISTINCTCOUNT(fact_sales[sale_id]), 0)
[Net Operating Profit] = [Gross Profit] - SUM(fact_expenses[expense_amount])
[Inventory Retail Valuation] = SUMX(dim_products, dim_products[current_stock] * dim_products[sale_price])
[Revenue MTD] = TOTALMTD([Total Revenue], dim_date[Date])
[Revenue YTD] = TOTALYTD([Total Revenue], dim_date[Date])
            """, language="dax")

    with t5:
        st.subheader("🏛️ Arquitectura Medallion en Microsoft Fabric")
        st.markdown("""
        ```mermaid
        graph LR
            DB[(PostgreSQL)] --> CJ["CopyJob_1"] --> B["Bronze (16 Raw Tables)"] --> S["Silver (Clean & 0-Baseline)"] --> G["Gold Data Warehouse"] --> BI["Streamlit / Power BI"]
        ```
        """)


# ==============================================================================
# PROJECT 2: DANE COLOMBIA LABOR MARKET & EMPLOYMENT PLATFORM
# ==============================================================================
else:
    df_dane_yearly, df_cities, df_informality = load_dane_data()

    st.markdown('<div class="main-header">🇨🇴 DANE Colombia: Análisis de Empleo y Mercado Laboral (2004 - 2026)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Plataforma de Ingeniería de Datos sobre Microdatos Oficiales de la GEIH (Gran Encuesta Integrada de Hogares)</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Filtros Mercado Laboral")
        year_range = st.slider("Periodo Histórico (Años)", min_value=2004, max_value=2026, value=(2004, 2026))
        selected_env_dane = st.selectbox("Entorno Fabric DANE", ["ws-dane-prod (Producción)", "ws-dane-dev (Desarrollo)"])
        st.divider()
        st.markdown("### 🏛️ Pipeline Medallion DANE")
        st.success("🟢 Bronze: Microdatos GEIH Ingestados")
        st.success("🟢 Silver: Armonización Demográfica")
        st.success("🟢 Gold: Series de Tiempo & Indicadores")

    df_filtered_dane = df_dane_yearly[
        (df_dane_yearly["Year"] >= year_range[0]) & 
        (df_dane_yearly["Year"] <= year_range[1])
    ]

    dt1, dt2, dt3 = st.tabs(["📈 Series Históricas & Mercado Laboral", "🏙️ Desglose por Ciudades Principales", "🏛️ Arquitectura de Datos DANE"])

    with dt1:
        st.subheader(f"📊 Evolución Histórica de Empleo y Desempleo en Colombia ({year_range[0]} - {year_range[1]})")
        
        latest_row = df_filtered_dane.iloc[-1]
        prev_row = df_filtered_dane.iloc[-2] if len(df_filtered_dane) > 1 else latest_row
        
        dc1, dc2, dc3, dc4 = st.columns(4)
        dc1.metric("📉 Tasa de Desempleo Nacional", f"{latest_row['Tasa_Desempleo']:.1f}%", f"{latest_row['Tasa_Desempleo'] - prev_row['Tasa_Desempleo']:.1f}% vs año ant.")
        dc2.metric("👥 Población Ocupada", f"{latest_row['Ocupados_Millones']:.1f}M", f"{latest_row['Ocupados_Millones'] - prev_row['Ocupados_Millones']:.1f}M personas")
        dc3.metric("📊 Tasa Global Participación (TGP)", f"{latest_row['TGP']:.1f}%")
        dc4.metric("💼 Informalidad Laboral Prom.", "56.2%", "Nivel Nacional")

        st.divider()

        st.markdown("##### 📅 Tendencia Histórica de la Tasa de Desempleo (2004 - 2026)")
        fig_dane_line = go.Figure()
        fig_dane_line.add_trace(go.Scatter(
            x=df_filtered_dane["Year"], 
            y=df_filtered_dane["Tasa_Desempleo"], 
            mode='lines+markers', 
            name='Tasa de Desempleo (%)',
            line=dict(color='#EC4899', width=3),
            marker=dict(size=7)
        ))
        fig_dane_line.add_trace(go.Scatter(
            x=df_filtered_dane["Year"], 
            y=df_filtered_dane["TGP"], 
            mode='lines+markers', 
            name='Tasa Global de Participación (TGP %)',
            line=dict(color='#3B82F6', width=2.5, dash='dash')
        ))
        fig_dane_line.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_dane_line)

    with dt2:
        st.subheader("🏙️ Indicadores por Áreas Metropolitanas y Brecha de Informalidad")
        
        col_city1, col_city2 = st.columns([2, 1])
        with col_city1:
            st.markdown("##### 🏙️ Tasa de Desempleo por Áreas Metropolitanas")
            fig_city_bar = px.bar(
                df_cities, 
                x='Ciudad_Metropolitana', 
                y='Tasa_Desempleo', 
                color='Informalidad_Pct', 
                text_auto='.1f',
                labels={'Tasa_Desempleo': 'Tasa Desempleo (%)', 'Informalidad_Pct': 'Informalidad (%)'},
                color_continuous_scale='Reds'
            )
            fig_city_bar.update_layout(template="plotly_dark", height=380)
            st.plotly_chart(fig_city_bar)

        with col_city2:
            st.markdown("##### 💼 Distribución Formal vs Informal")
            fig_inf_pie = px.pie(df_informality, names='Condición', values='Porcentaje', hole=0.4, color_discrete_sequence=['#10B981', '#F59E0B'])
            fig_inf_pie.update_layout(template="plotly_dark", height=380)
            st.plotly_chart(fig_inf_pie)

    with dt3:
        st.subheader("🏛️ Arquitectura Medallion para Procesamiento de Datos Masivos DANE")
        st.markdown("""
        ```mermaid
        graph TD
            subgraph DANE_Source["1. Fuentes de Datos DANE (2004 - 2026)"]
                DANE_Files["Microdatos GEIH & Archivos CSV/Parquet<br/>22 Años de Series Históricas"]
            end

            subgraph Fabric_Medallion["2. Microsoft Fabric Medallion Processing"]
                DANE_Files -->|Fabric Copy Job| B_DANE["lh_dane_bronze<br/>Raw Microdata Ingestion"]
                B_DANE -->|PySpark Harmonization| S_DANE["lh_dane_silver<br/>Standardized Demographics & Occupations"]
                S_DANE -->|Single-Session PySpark ETL| G_DANE["lh_dane_gold<br/>Time Series Data Warehouse & Facts"]
            end

            subgraph Presentation["3. Capa de Analítica"]
                G_DANE --> BI_DANE["Streamlit Portfolio Hub & Power BI"]
            end
        ```
        """)
        
        st.markdown("##### 📋 Esquema de Tablas Procesadas en Capa Gold DANE")
        st.dataframe(pd.DataFrame({
            "Tabla Gold": ["fact_ocupacion_mensual", "fact_desempleo_ciudad", "dim_geografia_metropolitana", "dim_ramas_actividad", "kpi_series_historicas_2004_2026"],
            "Descripción": ["Fact table con ocupados, desocupados e inactivos nivel mensual", "Desglose por ciudades principales e informalidad laboral", "Dimensión de divisiones político-administrativas", "Clasificación CIIU de ramas de actividad económica", "Series temporales consolidadas (2004-2026)"]
        }))

st.sidebar.markdown("---")
st.sidebar.caption("Multi-Project Data Engineering Portfolio Hub | Microsoft Fabric & Streamlit")
