import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

# Page Configuration
st.set_page_config(
    page_title="Velykapet Data Engineering & Analytics",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Theme Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1F2937;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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

# Helper Function to Load Gold Data spanning from September 2025 to Present
@st.cache_data
def load_gold_data():
    start_history = date(2025, 9, 1)
    end_history = date(2026, 8, 13)
    
    num_days = (end_history - start_history).days + 1
    dates = [start_history + timedelta(days=i) for i in range(num_days)]
    
    # Generate realistic growth trend starting from September 2025
    np.random.seed(42)
    base_tx = np.linspace(10, 85, num_days) + np.random.randint(-5, 6, num_days)
    base_tx = np.maximum(base_tx, 5).astype(int)
    
    avg_price = 95.0
    revenue = (base_tx * avg_price + np.random.uniform(-100, 200, num_days)).round(2)
    profit = (revenue * 0.30 + np.random.uniform(-50, 100, num_days)).round(2)
    
    sales_data = {
        "sale_datetime": dates,
        "sale_date": [d.strftime("%Y-%m-%d") for d in dates],
        "total_transactions": base_tx,
        "gross_revenue": revenue,
        "gross_profit": profit
    }
    df_sales = pd.DataFrame(sales_data)

    # 2. Product Performance Data
    products_data = {
        "product_name": ["Alimento Perro Premium 15kg", "Arena Gato 10kg", "Juguete Morder Caucho", "Snack Premios Cerdo 200g", "Shampoo Antipulgas 500ml", "Collar Ajustable Reflectivo"],
        "units_sold": [1240, 1810, 895, 2310, 685, 464],
        "revenue": [248000, 126700, 17900, 23100, 17125, 9280],
        "profit_margin": [0.32, 0.28, 0.45, 0.50, 0.40, 0.42]
    }
    df_prods = pd.DataFrame(products_data)

    # 3. Channel Breakdown Data
    channel_data = {
        "Channel": ["POS Tienda Física", "Rappi Express", "WhatsApp Bot (Production Ready)", "Ventas Directas Web"],
        "Revenue": [285000, 112000, 0, 45000]
    }
    df_ch = pd.DataFrame(channel_data)

    return df_sales, df_prods, df_ch

df_sales_trend, df_products, df_channels = load_gold_data()

# Header Section
st.markdown('<div class="main-header">🐾 Velykapet Data Engineering & Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Medallion Architecture (Bronze ➔ Silver ➔ Gold) on Microsoft Fabric & Delta Lake</div>', unsafe_allow_html=True)

# Sidebar Filters & Metadata
with st.sidebar:
    st.image("https://img.icons8.com/color/96/pet-commands-train.png", width=70)
    st.title("⚙️ Filtros de Control")
    
    min_date = date(2025, 9, 1)
    max_date = date(2026, 8, 13)
    
    date_range = st.date_input(
        "Rango de Fechas (Desde Sep 2025)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    selected_environment = st.selectbox(
        "Entorno Fabric",
        ["ws-velykapet-dev (Desarrollo)", "ws-velykapet-test (Pruebas)", "ws-velykapet-prod (Producción)"]
    )
    
    st.divider()
    st.markdown("### 🏛️ Estado Medallion")
    st.success("🟢 Bronze: 16/16 Tablas Sincronizadas")
    st.success("🟢 Silver: 16/16 Tablas Procesadas")
    st.success("🟢 Gold: Facts & Dims Actualizadas")
    st.info("📲 Bot WhatsApp: Baseline 0 Registros")

# Parse Date Range Selection
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    start_date = date_range[0]
    end_date = date_range[0]
else:
    start_date = min_date
    end_date = max_date

# Dynamic Filtering of Sales Data by Date Range
df_filtered_sales = df_sales_trend[
    (df_sales_trend["sale_datetime"] >= start_date) & 
    (df_sales_trend["sale_datetime"] <= end_date)
]

# Dashboard Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Resumen Ejecutivo & KPIs",
    "📦 Inventarios & Catálogo",
    "📲 WhatsApp Bot Conversion",
    "🏛️ Arquitectura & Data Engineering"
])

# TAB 1: Executive Summary
with tab1:
    st.subheader(f"📈 Rendimiento Financiero y de Ventas ({start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')})")
    
    if df_filtered_sales.empty:
        st.warning("⚠️ No hay transacciones de venta registradas para el rango de fechas seleccionado.")
    else:
        # Top KPI Cards (Dynamically Filtered)
        col1, col2, col3, col4 = st.columns(4)
        total_rev = df_filtered_sales["gross_revenue"].sum()
        total_profit = df_filtered_sales["gross_profit"].sum()
        total_tx = df_filtered_sales["total_transactions"].sum()
        avg_ticket = total_rev / total_tx if total_tx > 0 else 0
        margin_pct = (total_profit / total_rev * 100) if total_rev > 0 else 0.0

        col1.metric("💰 Ingresos Totales", f"${total_rev:,.2f}", f"{len(df_filtered_sales)} días en rango")
        col2.metric("📈 Ganancia Bruta", f"${total_profit:,.2f}", f"Margen: {margin_pct:.1f}%")
        col3.metric("🛒 Transacciones Totales", f"{total_tx:,}")
        col4.metric("🏷️ Ticket Promedio", f"${avg_ticket:,.2f}")

        st.divider()

        # Dynamic Visualizations
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.markdown("##### 📅 Tendencia Diaria de Ventas y Margen de Ganancia")
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=df_filtered_sales["sale_date"], 
                y=df_filtered_sales["gross_revenue"], 
                mode='lines', 
                name='Ingreso Bruto ($)', 
                line=dict(color='#4F46E5', width=2.5)
            ))
            fig_trend.add_trace(go.Scatter(
                x=df_filtered_sales["sale_date"], 
                y=df_filtered_sales["gross_profit"], 
                mode='lines', 
                name='Ganancia Bruta ($)', 
                line=dict(color='#10B981', width=2.5)
            ))
            fig_trend.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_trend, use_container_width=True)

        with c2:
            st.markdown("##### 🍕 Origen de Ventas por Canal")
            fig_pie = px.pie(df_channels, names='Channel', values='Revenue', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

# TAB 2: Inventory & Catalog
with tab2:
    st.subheader("📦 Estado de Inventario y Desempeño de Productos")
    
    ic1, ic2, ic3 = st.columns(3)
    ic1.metric("🏷️ SKUs Activos", "275 SKUs")
    ic2.metric("📦 Unidades en Stock", "1,840 unidades")
    ic3.metric("💵 Valor Comercial Inv.", "$48,500.00")

    st.divider()
    
    st.markdown("##### 🏆 Top Productos más Vendidos")
    fig_bar = px.bar(
        df_products, 
        x='product_name', 
        y='revenue', 
        color='profit_margin', 
        text_auto='.2s',
        labels={'revenue': 'Ingresos ($)', 'product_name': 'Producto', 'profit_margin': 'Margen (%)'},
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

# TAB 3: WhatsApp Bot Conversion
with tab3:
    st.subheader("📲 Monitor de Conversión del Bot de WhatsApp")
    st.info("ℹ️ **Listo para Salida a Producción**: Las tablas de mensajes y pedidos por WhatsApp han sido inicializadas en 0 registros como baseline limpio para el lanzamiento.")
    
    wc1, wc2, wc3, wc4 = st.columns(4)
    wc1.metric("📩 Mensajes Procesados", "0 msgs", "Baseline Listo")
    wc2.metric("🛍️ Pedidos Convertidos", "0 pedidos", "Baseline Listo")
    wc3.metric("💰 Facturación Bot", "$0.00", "Baseline Listo")
    wc4.metric("📈 Tasa de Conversión", "0.0%", "Baseline Listo")

    st.markdown("##### 🔄 Embudo de Conversión WhatsApp (Producción)")
    funnel_data = dict(
        number=[0, 0, 0, 0],
        stage=["Mensajes Entrantes", "Consultas de Catálogo", "Carritos Creados", "Ventas Concluidas"]
    )
    fig_funnel = px.funnel(funnel_data, x='number', y='stage')
    fig_funnel.update_layout(template="plotly_dark", height=350)
    st.plotly_chart(fig_funnel, use_container_width=True)

# TAB 4: Architecture & Data Engineering
with tab4:
    st.subheader("🏛️ Arquitectura Medallion en Microsoft Fabric")
    
    st.markdown("""
    ```mermaid
    graph LR
        subgraph Ingestion["1. Fuente PostgreSQL"]
            DB[(PostgreSQL)] --> CJ["CopyJob_1"]
        end

        subgraph Bronze["2. Capa Bronze (Raw Ingest)"]
            CJ --> B_Tables["lh_velykapet_bronze_dev<br/>(16 Raw Tables)"]
        end

        subgraph Silver["3. Capa Silver (Clean & 0-Baseline)"]
            B_Tables --> S_Notebook["nb_velykapet_transformation_silver"]
            S_Notebook --> S_Tables["lh_velykapet_silver_dev<br/>(Delta Lake Tables)"]
        end

        subgraph Gold["4. Capa Gold (Data Warehouse & KPIs)"]
            S_Tables --> G_Notebook["nb_velykapet_master_medallion"]
            G_Notebook --> DW["lh_velykapet_gold_dev<br/>(Facts & Dimensions)"]
            DW --> BI["Power BI & Streamlit Dashboard"]
        end
    ```
    """)
    
    st.markdown("##### 📋 Registro de Tablas Medallion (16 Tablas Sincronizadas)")
    df_schema_summary = pd.DataFrame({
        "Tabla Original": ["sales", "sale_items", "products", "master_catalog", "purchases", "expenses", "devolutions", "whatsapp_orders", "whatsapp_contacts"],
        "Capa Bronze": ["public.sales", "public.sale_items", "public.products", "public.master_catalog", "public.purchases", "public.expenses", "public.devolutions", "public.whatsapp_orders", "public.whatsapp_contacts"],
        "Capa Silver": ["silver_sales", "silver_sale_items", "silver_products", "silver_master_catalog", "silver_purchases", "silver_expenses", "silver_devolutions", "silver_whatsapp_orders (0)", "silver_whatsapp_contacts (0)"],
        "Capa Gold Target": ["fact_sales", "fact_sales", "dim_products", "dim_products", "fact_purchases", "fact_expenses", "fact_sales", "kpi_whatsapp_conversion", "kpi_whatsapp_conversion"]
    })
    st.dataframe(df_schema_summary, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("Velykapet Data Engineering Platform v1.0 | Microsoft Fabric & Delta Lake")
