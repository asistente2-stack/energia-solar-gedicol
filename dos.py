import os
import glob
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Dashboard Energía Solar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS ULTRA PROFESIONAL
st.markdown("""
<style>
    .block-container {padding-top: 0.5rem; padding-bottom: 2rem; background-color: #f8fafc;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .main {background-color: #f8fafc;}
    
    /* Filtros superiores */
    .filter-container {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(30, 64, 175, 0.3);
    }
    
    /* KPIs Dinámicos */
    .kpi-dynamic {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        border-left: 4px solid;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-dynamic.cafe {border-left-color: #3b82f6;}
    .kpi-dynamic.mercado {border-left-color: #10b981;}
    .kpi-dynamic.total {border-left-color: #8b5cf6;}
    .kpi-dynamic.ahorro {border-left-color: #f59e0b;}
    
    .kpi-dynamic:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    }
    
    .kpi-label-dyn {
        color: #64748b;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 10px;
    }
    
    .kpi-value-dyn {
        font-size: 36px;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 8px;
    }
    
    .kpi-value-dyn.cafe {color: #3b82f6;}
    .kpi-value-dyn.mercado {color: #10b981;}
    .kpi-value-dyn.total {color: #8b5cf6;}
    .kpi-value-dyn.ahorro {color: #f59e0b;}
    
    .kpi-subtitle-dyn {
        color: #64748b;
        font-size: 12px;
        font-weight: 600;
        line-height: 1.5;
    }
    
    /* Tablas mejoradas */
    .energy-table {
        background: #ffffff;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 2px solid #e2e8f0;
        margin-top: 20px;
    }
    
    .table-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 18px 24px;
        border-bottom: 3px solid #1e40af;
    }
    
    .table-title {
        color: #ffffff;
        font-size: 17px;
        font-weight: 800;
        margin: 0;
        letter-spacing: 0.5px;
    }
    
    table.data-table {
        width: 100%;
        border-collapse: collapse;
        background: #ffffff;
    }
    
    table.data-table thead th {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        color: #1e293b;
        padding: 14px 16px;
        text-align: left;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-bottom: 2px solid #cbd5e1;
    }
    
    table.data-table tbody td {
        padding: 16px;
        color: #1e293b;
        font-size: 13px;
        font-weight: 500;
        border-bottom: 1px solid #e2e8f0;
    }
    
    table.data-table tbody tr:nth-child(even) {
        background: #f8fafc;
    }
    
    table.data-table tbody tr:hover {
        background: #e0f2fe !important;
        cursor: pointer;
    }
    
    .badge-cafe {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
        color: white;
        padding: 5px 11px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 800;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    
    .badge-mercado {
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        color: white;
        padding: 5px 11px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 800;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    
    /* Pestañas mejoradas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px;
        color: #64748b;
        font-weight: 700;
        padding: 10px 18px;
        font-size: 13px;
        border: 2px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: 2px solid #1e40af;
    }
    
    /* Métricas de hora */
    .hour-metric {
        background: linear-gradient(135deg, #f1f5f9 0%, #ffffff 100%);
        padding: 16px;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .hour-metric:hover {
        transform: scale(1.05);
        border-color: #3b82f6;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
    }
    
    .hour-value {
        font-size: 26px;
        font-weight: 900;
        color: #3b82f6;
        margin: 6px 0;
    }
    
    .hour-label {
        font-size: 10px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# FUNCIONES AUXILIARES
def fmt_num(x, decimals=0):
    try:
        v = float(x)
    except:
        return "0"
    s = f"{v:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    if decimals == 0:
        s = s.split(",")[0]
    return s

def fmt_currency(x):
    try:
        v = float(x)
    except:
        return "$0"
    s = f"${v:,.0f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def month_label_es(y, m):
    months = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    return f"{months[int(m)-1]} {int(y)}"

def month_label_short(y, m):
    base = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    return f"{base[int(m)-1]}\n{int(y)}"

# COSTOS EPM (en pesos por kWh)
COSTOS_EPM = {
    'CAFE': 1033,
    'MERCADO': 1077
}

# CARGA DE DATOS
@st.cache_data
def cargar_datos():
    """Carga todos los datos del archivo consolidado"""
    try:
        # Buscar archivo
        carpeta = os.path.dirname(os.path.abspath(__file__))
        archivo = None
        for nombre in ["Reporte_Energia_Solar_GEDICOL*.xlsx", "Reporte_Energia_Solar_GEDICOL*.xls"]:
            hits = sorted(glob.glob(os.path.join(carpeta, nombre)))
            if hits:
                archivo = hits[0]
                break
        
        if not archivo or not os.path.exists(archivo):
            return None, None, None
        
        # Cargar hojas
        mensual = pd.read_excel(archivo, sheet_name='POR MES')
        diario = pd.read_excel(archivo, sheet_name='POR DIA')
        horario = pd.read_excel(archivo, sheet_name='POR HORA')
        
        # Procesar mensual
        mensual.columns = [str(c).strip().lower() for c in mensual.columns]
        mensual['planta'] = mensual['planta'].str.strip().str.upper()
        
        # Procesar diario
        diario.columns = [str(c).strip().lower() for c in diario.columns]
        diario['fecha'] = pd.to_datetime(diario['fecha'])
        diario['planta'] = diario['planta'].str.strip().str.upper()
        
        # Procesar horario
        horario.columns = [str(c).strip().lower() for c in horario.columns]
        horario['fecha'] = pd.to_datetime(horario['fecha'])
        horario['planta'] = horario['planta'].str.strip().str.upper()
        horario['hora_num'] = pd.to_datetime(horario['hora'], format='%H:%M').dt.hour
        
        return mensual, diario, horario
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None, None, None

# CARGAR DATOS
mensual_df, diario_df, horario_df = cargar_datos()

if mensual_df is None:
    st.error("No se pudo cargar el archivo. Asegúrate de que 'Reporte_Energia_Solar_GEDICOL.xlsx' esté en la misma carpeta.")
    st.stop()

# HEADER
st.markdown("""
<div style='text-align: center; padding: 16px 0; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border-radius: 12px; margin-bottom: 16px;'>
    <h1 style='font-size: 36px; font-weight: 900; background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 4px; letter-spacing: -0.5px;'>
        Dashboard Energía Solar
    </h1>
    <p style='font-size: 14px; color: #64748b; font-weight: 600; letter-spacing: 0.5px;'>
        Sistema de Monitoreo Avanzado | Plantas CAFE & MERCADO
    </p>
</div>
""", unsafe_allow_html=True)

# FILTROS GLOBALES
st.markdown('<div class="filter-container">', unsafe_allow_html=True)
st.markdown("### FILTROS GLOBALES")

filter_cols = st.columns([2, 2, 3, 2])

# Filtro de Año
years_disponibles = sorted(mensual_df['anio'].unique().tolist())
with filter_cols[0]:
    selected_years = st.multiselect(
        "Año",
        options=years_disponibles,
        default=years_disponibles,
        key="year_filter"
    )

# Filtro de Mes
meses_disponibles = sorted(mensual_df['mes'].unique().tolist())
month_names = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 
               7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
with filter_cols[1]:
    selected_months = st.multiselect(
        "Mes",
        options=meses_disponibles,
        default=meses_disponibles,
        format_func=lambda x: month_names.get(x, str(x)),
        key="month_filter"
    )

# Filtro de Fechas (para diario y horario)
with filter_cols[2]:
    min_fecha = diario_df['fecha'].min().date()
    max_fecha = diario_df['fecha'].max().date()
    fecha_range = st.date_input(
        "Rango de Fechas",
        value=(min_fecha, max_fecha),
        min_value=min_fecha,
        max_value=max_fecha,
        key="date_filter"
    )

# Filtro de Planta
with filter_cols[3]:
    plantas_disponibles = sorted(mensual_df['planta'].unique().tolist())
    selected_plantas = st.multiselect(
        "Planta",
        options=plantas_disponibles,
        default=plantas_disponibles,
        key="planta_filter"
    )

st.markdown('</div>', unsafe_allow_html=True)

# APLICAR FILTROS
if not selected_years:
    selected_years = years_disponibles
if not selected_months:
    selected_months = meses_disponibles
if not selected_plantas:
    selected_plantas = plantas_disponibles

# Filtrar datos
mensual_filtrado = mensual_df[
    (mensual_df['anio'].isin(selected_years)) &
    (mensual_df['mes'].isin(selected_months)) &
    (mensual_df['planta'].isin(selected_plantas))
].copy()

if isinstance(fecha_range, tuple) and len(fecha_range) == 2:
    fecha_inicio, fecha_fin = fecha_range
else:
    fecha_inicio = min_fecha
    fecha_fin = max_fecha

diario_filtrado = diario_df[
    (diario_df['fecha'].dt.date >= fecha_inicio) &
    (diario_df['fecha'].dt.date <= fecha_fin) &
    (diario_df['planta'].isin(selected_plantas))
].copy()

horario_filtrado = horario_df[
    (horario_df['fecha'].dt.date >= fecha_inicio) &
    (horario_df['fecha'].dt.date <= fecha_fin) &
    (horario_df['planta'].isin(selected_plantas))
].copy()

# KPIS DINÁMICOS
st.markdown("### RESUMEN EJECUTIVO")
kpi_cols = st.columns(4)

# Calcular métricas globales
total_generacion = mensual_filtrado['energia_kwh'].sum()
generacion_cafe = mensual_filtrado[mensual_filtrado['planta']=='CAFE']['energia_kwh'].sum()
generacion_mercado = mensual_filtrado[mensual_filtrado['planta']=='MERCADO']['energia_kwh'].sum()

ahorro_cafe = generacion_cafe * COSTOS_EPM['CAFE']
ahorro_mercado = generacion_mercado * COSTOS_EPM['MERCADO']
ahorro_total = ahorro_cafe + ahorro_mercado

# Promedio diario
dias_activos = len(diario_filtrado['fecha'].unique())
prom_diario = total_generacion / dias_activos if dias_activos > 0 else 0

with kpi_cols[0]:
    st.markdown(f"""
    <div class="kpi-dynamic cafe">
        <div class="kpi-label-dyn">Planta CAFE</div>
        <div class="kpi-value-dyn cafe">{fmt_num(generacion_cafe, 1)}</div>
        <div class="kpi-subtitle-dyn">
            kWh generados<br>
            Ahorro: {fmt_currency(ahorro_cafe)}
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown(f"""
    <div class="kpi-dynamic mercado">
        <div class="kpi-label-dyn">Planta MERCADO</div>
        <div class="kpi-value-dyn mercado">{fmt_num(generacion_mercado, 1)}</div>
        <div class="kpi-subtitle-dyn">
            kWh generados<br>
            Ahorro: {fmt_currency(ahorro_mercado)}
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown(f"""
    <div class="kpi-dynamic total">
        <div class="kpi-label-dyn">Total Generado</div>
        <div class="kpi-value-dyn total">{fmt_num(total_generacion, 1)}</div>
        <div class="kpi-subtitle-dyn">
            kWh totales<br>
            Promedio: {fmt_num(prom_diario, 1)} kWh/día
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown(f"""
    <div class="kpi-dynamic ahorro">
        <div class="kpi-label-dyn">Ahorro Total</div>
        <div class="kpi-value-dyn ahorro">{fmt_currency(ahorro_total)}</div>
        <div class="kpi-subtitle-dyn">
            Pesos colombianos<br>
            {dias_activos} días analizados
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# PESTAÑAS
tab1, tab2, tab3, tab4 = st.tabs(["Análisis Mensual", "Análisis Diario", "Análisis por Hora", "Comparativas"])

# ============================================================================
# TAB 1: ANÁLISIS MENSUAL
# ============================================================================
with tab1:
    if mensual_filtrado.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados.")
    else:
        # Gráfico de barras apiladas
        fig, ax = plt.subplots(figsize=(16, 7))
        ax.set_facecolor('#ffffff')
        fig.patch.set_facecolor('#f8fafc')
        
        # Preparar datos para gráfico
        pivot_data = mensual_filtrado.pivot_table(
            index=['anio', 'mes'],
            columns='planta',
            values='energia_kwh',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        pivot_data['mes_label'] = pivot_data.apply(lambda r: month_label_short(r['anio'], r['mes']), axis=1)
        
        x = np.arange(len(pivot_data))
        width = 0.4
        
        if 'CAFE' in pivot_data.columns:
            bars1 = ax.bar(x - width/2, pivot_data['CAFE'], width, label='CAFE', 
                          color='#3b82f6', edgecolor='white', linewidth=1.5, alpha=0.9)
        
        if 'MERCADO' in pivot_data.columns:
            bars2 = ax.bar(x + width/2, pivot_data['MERCADO'], width, label='MERCADO',
                          color='#10b981', edgecolor='white', linewidth=1.5, alpha=0.9)
        
        ax.set_xlabel('Período', fontsize=14, fontweight='bold', color='#475569')
        ax.set_ylabel('Energía (kWh)', fontsize=14, fontweight='bold', color='#475569')
        ax.set_title('Generación Solar Mensual por Planta', fontsize=18, fontweight='black', pad=20, color='#1e293b')
        ax.set_xticks(x)
        ax.set_xticklabels(pivot_data['mes_label'], fontsize=10, fontweight='bold')
        ax.legend(loc='upper left', fontsize=12, framealpha=0.95)
        ax.grid(axis='y', linestyle='--', alpha=0.3, color='#cbd5e1')
        
        for spine in ax.spines.values():
            spine.set_color('#cbd5e1')
            spine.set_linewidth(1.5)
        
        st.pyplot(fig, clear_figure=True)
        
        # Tabla con ahorro
        st.markdown("### Detalle Mensual")
        
        table_data = []
        for _, row in mensual_filtrado.iterrows():
            ahorro = row['energia_kwh'] * COSTOS_EPM.get(row['planta'], 0)
            table_data.append({
                'Mes': month_label_es(row['anio'], row['mes']),
                'Planta': row['planta'],
                'Generación (kWh)': fmt_num(row['energia_kwh'], 1),
                'Ahorro ($)': fmt_currency(ahorro)
            })
        
        table_df = pd.DataFrame(table_data)
        
        # HTML table
        rows_html = []
        for idx, r in table_df.iterrows():
            pl = r['Planta']
            badge = f'<div class="badge-cafe">CAFE</div>' if pl == 'CAFE' else f'<div class="badge-mercado">MERCADO</div>'
            bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            
            rows_html.append(f"""
            <tr style="background: {bg};">
                <td style="padding: 16px;"><strong>{r['Mes']}</strong></td>
                <td style="padding: 16px;">{badge}</td>
                <td style="padding: 16px; color: #3b82f6; font-weight: 700;">{r['Generación (kWh)']} kWh</td>
                <td style="padding: 16px; color: #10b981; font-weight: 800;">{r['Ahorro ($)']}</td>
            </tr>
            """)
        
        html = f"""
        <div style="display: flex; justify-content: center;">
            <div class="energy-table" style="max-width: 900px; width: 55%;">
                <div class="table-header">
                    <h3 class="table-title">Balance Mensual con Ahorro Económico</h3>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>MES</th>
                            <th>PLANTA</th>
                            <th>GENERACIÓN</th>
                            <th>AHORRO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        components.html(html, height=500, scrolling=True)

# ============================================================================
# TAB 2: ANÁLISIS DIARIO
# ============================================================================
with tab2:
    if diario_filtrado.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados.")
    else:
        # Estadísticas rápidas
        st.markdown("### Métricas del Período")
        metric_cols = st.columns(4)
        
        for idx, planta in enumerate(selected_plantas):
            data_planta = diario_filtrado[diario_filtrado['planta']==planta]
            if not data_planta.empty:
                total = data_planta['energia_kwh'].sum()
                promedio = data_planta['energia_kwh'].mean()
                maximo = data_planta['energia_kwh'].max()
                dias = len(data_planta)
                
                with metric_cols[idx]:
                    st.metric(
                        label=f"{planta} - Total",
                        value=f"{fmt_num(total, 1)} kWh",
                        delta=f"Prom: {fmt_num(promedio, 1)} kWh/día"
                    )
                
                with metric_cols[idx+2]:
                    ahorro_planta = total * COSTOS_EPM.get(planta, 0)
                    st.metric(
                        label=f"{planta} - Ahorro",
                        value=fmt_currency(ahorro_planta),
                        delta=f"{dias} días"
                    )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráfico de línea temporal
        fig, ax = plt.subplots(figsize=(18, 7))
        ax.set_facecolor('#ffffff')
        fig.patch.set_facecolor('#f8fafc')
        
        for planta in selected_plantas:
            data_planta = diario_filtrado[diario_filtrado['planta']==planta].sort_values('fecha')
            if not data_planta.empty:
                color = '#3b82f6' if planta == 'CAFE' else '#10b981'
                ax.plot(data_planta['fecha'], data_planta['energia_kwh'], 
                       marker='o', linewidth=2.5, markersize=5, label=planta, 
                       color=color, alpha=0.8)
                ax.fill_between(data_planta['fecha'], data_planta['energia_kwh'], 
                               alpha=0.2, color=color)
        
        ax.set_xlabel('Fecha', fontsize=14, fontweight='bold', color='#475569')
        ax.set_ylabel('Energía (kWh)', fontsize=14, fontweight='bold', color='#475569')
        ax.set_title('Evolución Diaria de Generación Solar', fontsize=18, fontweight='black', pad=20, color='#1e293b')
        ax.legend(loc='upper left', fontsize=12, framealpha=0.95)
        ax.grid(axis='both', linestyle='--', alpha=0.3, color='#cbd5e1')
        plt.xticks(rotation=45, ha='right')
        
        for spine in ax.spines.values():
            spine.set_color('#cbd5e1')
            spine.set_linewidth(1.5)
        
        st.pyplot(fig, clear_figure=True)
        
        # Tabla diaria con ahorro
        st.markdown("### Detalle Diario")
        
        table_data = []
        for _, row in diario_filtrado.sort_values('fecha').iterrows():
            ahorro = row['energia_kwh'] * COSTOS_EPM.get(row['planta'], 0)
            fecha_obj = pd.to_datetime(row['fecha'])
            fecha_str = f"{fecha_obj.day:02d} {fecha_obj.strftime('%B')}, {fecha_obj.year}"
            
            meses_es = {
                'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
                'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
                'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
            }
            for eng, esp in meses_es.items():
                fecha_str = fecha_str.replace(eng, esp)
            
            table_data.append({
                'Fecha': fecha_str,
                'Planta': row['planta'],
                'Generación (kWh)': fmt_num(row['energia_kwh'], 1),
                'Ahorro ($)': fmt_currency(ahorro)
            })
        
        table_df = pd.DataFrame(table_data)
        
        rows_html = []
        for idx, r in table_df.iterrows():
            pl = r['Planta']
            badge = f'<div class="badge-cafe">CAFE</div>' if pl == 'CAFE' else f'<div class="badge-mercado">MERCADO</div>'
            bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            
            rows_html.append(f"""
            <tr style="background: {bg};">
                <td style="padding: 16px;"><strong>{r['Fecha']}</strong></td>
                <td style="padding: 16px;">{badge}</td>
                <td style="padding: 16px; color: #3b82f6; font-weight: 700;">{r['Generación (kWh)']} kWh</td>
                <td style="padding: 16px; color: #10b981; font-weight: 800;">{r['Ahorro ($)']}</td>
            </tr>
            """)
        
        html = f"""
        <div style="display: flex; justify-content: center;">
            <div class="energy-table" style="max-width: 800px; width: 50%;">
                <div class="table-header">
                    <h3 class="table-title">Detalle Diario con Ahorro Económico</h3>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>FECHA</th>
                            <th>PLANTA</th>
                            <th>GENERACIÓN</th>
                            <th>AHORRO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        components.html(html, height=500, scrolling=True)

# ============================================================================
# TAB 3: ANÁLISIS POR HORA
# ============================================================================
with tab3:
    if horario_filtrado.empty:
        st.warning("No hay datos disponibles con los filtros seleccionados.")
    else:
        st.markdown("### Análisis de Generación por Hora")
        
        # Métricas por hora
        hora_metrics = st.columns(3)
        
        # Hora de mayor generación
        hora_max = horario_filtrado.groupby('hora_num')['energia_kwh'].sum().idxmax()
        energia_max = horario_filtrado.groupby('hora_num')['energia_kwh'].sum().max()
        
        # Hora de inicio (primera hora con generación > 0)
        horas_con_gen = horario_filtrado[horario_filtrado['energia_kwh'] > 0].groupby('hora_num')['energia_kwh'].sum()
        hora_inicio = horas_con_gen.index.min() if len(horas_con_gen) > 0 else 0
        
        # Total horas productivas
        horas_productivas = len(horas_con_gen)
        
        with hora_metrics[0]:
            st.markdown(f"""
            <div class="hour-metric">
                <div class="hour-label">Hora Pico</div>
                <div class="hour-value">{int(hora_max)}:00</div>
                <div class="hour-label">{fmt_num(energia_max, 1)} kWh</div>
            </div>
            """, unsafe_allow_html=True)
        
        with hora_metrics[1]:
            st.markdown(f"""
            <div class="hour-metric">
                <div class="hour-label">Inicio Generación</div>
                <div class="hour-value">{int(hora_inicio)}:00</div>
                <div class="hour-label">Primera hora activa</div>
            </div>
            """, unsafe_allow_html=True)
        
        with hora_metrics[2]:
            st.markdown(f"""
            <div class="hour-metric">
                <div class="hour-label">Horas Productivas</div>
                <div class="hour-value">{horas_productivas}</div>
                <div class="hour-label">Por día (promedio)</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráfico de generación por hora (promedio)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12))
        fig.patch.set_facecolor('#f8fafc')
        
        # Gráfico 1: Promedio por hora
        ax1.set_facecolor('#ffffff')
        hora_promedio = horario_filtrado.groupby(['hora_num', 'planta'])['energia_kwh'].mean().reset_index()
        
        for planta in selected_plantas:
            data_planta = hora_promedio[hora_promedio['planta']==planta].sort_values('hora_num')
            if not data_planta.empty:
                color = '#3b82f6' if planta == 'CAFE' else '#10b981'
                ax1.plot(data_planta['hora_num'], data_planta['energia_kwh'], 
                        marker='o', linewidth=3, markersize=8, label=planta, 
                        color=color, alpha=0.8)
                ax1.fill_between(data_planta['hora_num'], data_planta['energia_kwh'], 
                                alpha=0.2, color=color)
        
        ax1.set_xlabel('Hora del Día', fontsize=13, fontweight='bold', color='#475569')
        ax1.set_ylabel('Energía Promedio (kWh)', fontsize=13, fontweight='bold', color='#475569')
        ax1.set_title('Patrón de Generación Solar por Hora (Promedio)', 
                     fontsize=17, fontweight='black', pad=15, color='#1e293b')
        ax1.legend(loc='upper left', fontsize=11, framealpha=0.95)
        ax1.grid(axis='both', linestyle='--', alpha=0.3, color='#cbd5e1')
        ax1.set_xticks(range(0, 24, 2))
        ax1.set_xticklabels([f"{h}:00" for h in range(0, 24, 2)])
        
        for spine in ax1.spines.values():
            spine.set_color('#cbd5e1')
            spine.set_linewidth(1.5)
        
        # Gráfico 2: Heatmap
        ax2.set_facecolor('#ffffff')
        
        # Preparar datos para heatmap
        horario_filtrado['dia_nombre'] = horario_filtrado['fecha'].dt.strftime('%d-%b')
        pivot_heatmap = horario_filtrado.pivot_table(
            index='dia_nombre',
            columns='hora_num',
            values='energia_kwh',
            aggfunc='sum',
            fill_value=0
        )
        
        # Limitar a últimos 30 días si hay muchos
        if len(pivot_heatmap) > 30:
            pivot_heatmap = pivot_heatmap.tail(30)
        
        im = ax2.imshow(pivot_heatmap.values, cmap='YlOrRd', aspect='auto', interpolation='nearest')
        
        ax2.set_xlabel('Hora del Día', fontsize=13, fontweight='bold', color='#475569')
        ax2.set_ylabel('Fecha', fontsize=13, fontweight='bold', color='#475569')
        ax2.set_title('Mapa de Calor: Generación por Hora y Día', 
                     fontsize=17, fontweight='black', pad=15, color='#1e293b')
        
        ax2.set_xticks(range(0, 24, 2))
        ax2.set_xticklabels([f"{h}:00" for h in range(0, 24, 2)])
        ax2.set_yticks(range(len(pivot_heatmap)))
        ax2.set_yticklabels(pivot_heatmap.index, fontsize=8)
        
        plt.colorbar(im, ax=ax2, label='kWh')
        
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)
        
        # Tabla por hora con ahorro
        st.markdown("### Detalle por Hora")
        
        # Agrupar por fecha, hora y planta
        hora_agrupado = horario_filtrado.groupby(['fecha', 'hora_num', 'planta'])['energia_kwh'].sum().reset_index()
        hora_agrupado = hora_agrupado.sort_values(['fecha', 'hora_num'])
        
        table_data = []
        for _, row in hora_agrupado.head(100).iterrows():  # Limitar a 100 filas
            ahorro = row['energia_kwh'] * COSTOS_EPM.get(row['planta'], 0)
            fecha_str = row['fecha'].strftime('%d/%m/%Y')
            hora_str = f"{int(row['hora_num']):02d}:00"
            
            table_data.append({
                'Fecha': fecha_str,
                'Hora': hora_str,
                'Planta': row['planta'],
                'Generación (kWh)': fmt_num(row['energia_kwh'], 2),
                'Ahorro ($)': fmt_currency(ahorro)
            })
        
        table_df = pd.DataFrame(table_data)
        
        rows_html = []
        for idx, r in table_df.iterrows():
            pl = r['Planta']
            badge = f'<div class="badge-cafe">CAFE</div>' if pl == 'CAFE' else f'<div class="badge-mercado">MERCADO</div>'
            bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            
            rows_html.append(f"""
            <tr style="background: {bg};">
                <td style="padding: 14px;"><strong>{r['Fecha']}</strong></td>
                <td style="padding: 14px;"><strong>{r['Hora']}</strong></td>
                <td style="padding: 14px;">{badge}</td>
                <td style="padding: 14px; color: #3b82f6; font-weight: 700;">{r['Generación (kWh)']} kWh</td>
                <td style="padding: 14px; color: #10b981; font-weight: 800;">{r['Ahorro ($)']}</td>
            </tr>
            """)
        
        html = f"""
        <div style="display: flex; justify-content: center;">
            <div class="energy-table" style="max-width: 950px; width: 60%;">
                <div class="table-header">
                    <h3 class="table-title">Detalle por Hora con Ahorro (Primeros 100 registros)</h3>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>FECHA</th>
                            <th>HORA</th>
                            <th>PLANTA</th>
                            <th>GENERACIÓN</th>
                            <th>AHORRO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        components.html(html, height=500, scrolling=True)

# ============================================================================
# TAB 4: COMPARATIVAS
# ============================================================================
with tab4:
    st.markdown("### Análisis Comparativo entre Plantas")
    
    if len(selected_plantas) < 2:
        st.info("Selecciona ambas plantas en los filtros para ver las comparativas.")
    else:
        # Comparativa de distribución
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de torta - Generación
            fig, ax = plt.subplots(figsize=(7, 7))
            fig.patch.set_facecolor('#ffffff')
            
            totales_planta = mensual_filtrado.groupby('planta')['energia_kwh'].sum()
            
            colors = ['#3b82f6', '#10b981']
            wedges, texts, autotexts = ax.pie(
                totales_planta.values,
                labels=totales_planta.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 13, 'fontweight': 'bold', 'color': 'white'}
            )
            
            for text in texts:
                text.set_fontsize(14)
                text.set_fontweight('black')
                text.set_color('#1e293b')
            
            ax.set_title('Distribución de Generación por Planta', 
                        fontsize=16, fontweight='black', color='#1e293b', pad=20)
            
            st.pyplot(fig, clear_figure=True)
        
        with col2:
            # Gráfico de torta - Ahorro
            fig, ax = plt.subplots(figsize=(7, 7))
            fig.patch.set_facecolor('#ffffff')
            
            ahorros = []
            labels = []
            for planta in totales_planta.index:
                ahorro = totales_planta[planta] * COSTOS_EPM.get(planta, 0)
                ahorros.append(ahorro)
                labels.append(planta)
            
            wedges, texts, autotexts = ax.pie(
                ahorros,
                labels=labels,
                autopct=lambda pct: fmt_currency(pct * sum(ahorros) / 100),
                colors=colors,
                startangle=90,
                textprops={'fontsize': 11, 'fontweight': 'bold', 'color': 'white'}
            )
            
            for text in texts:
                text.set_fontsize(14)
                text.set_fontweight('black')
                text.set_color('#1e293b')
            
            ax.set_title('Distribución de Ahorro por Planta', 
                        fontsize=16, fontweight='black', color='#1e293b', pad=20)
            
            # Agregar total en el centro
            total_text = f"Total:\n{fmt_currency(sum(ahorros))}"
            ax.text(0, 0, total_text, ha='center', va='center',
                   fontsize=16, fontweight='black', color='#1e293b',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                            edgecolor='#e2e8f0', linewidth=2))
            
            st.pyplot(fig, clear_figure=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabla comparativa
        st.markdown("### Tabla Comparativa")
        
        comparativa = []
        for planta in selected_plantas:
            data_planta_mensual = mensual_filtrado[mensual_filtrado['planta']==planta]
            data_planta_diario = diario_filtrado[diario_filtrado['planta']==planta]
            
            total_gen = data_planta_mensual['energia_kwh'].sum()
            prom_diario = data_planta_diario['energia_kwh'].mean() if not data_planta_diario.empty else 0
            max_diario = data_planta_diario['energia_kwh'].max() if not data_planta_diario.empty else 0
            ahorro = total_gen * COSTOS_EPM.get(planta, 0)
            
            comparativa.append({
                'Planta': planta,
                'Total Generado (kWh)': fmt_num(total_gen, 1),
                'Promedio Diario (kWh)': fmt_num(prom_diario, 1),
                'Máximo Diario (kWh)': fmt_num(max_diario, 1),
                'Ahorro Total ($)': fmt_currency(ahorro)
            })
        
        comp_df = pd.DataFrame(comparativa)
        
        rows_html = []
        for idx, r in comp_df.iterrows():
            pl = r['Planta']
            badge = f'<div class="badge-cafe">CAFE</div>' if pl == 'CAFE' else f'<div class="badge-mercado">MERCADO</div>'
            bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            
            rows_html.append(f"""
            <tr style="background: {bg};">
                <td style="padding: 18px;">{badge}</td>
                <td style="padding: 18px; color: #3b82f6; font-weight: 700;">{r['Total Generado (kWh)']} kWh</td>
                <td style="padding: 18px; font-weight: 600;">{r['Promedio Diario (kWh)']} kWh</td>
                <td style="padding: 18px; font-weight: 600;">{r['Máximo Diario (kWh)']} kWh</td>
                <td style="padding: 18px; color: #10b981; font-weight: 800; font-size: 15px;">{r['Ahorro Total ($)']}</td>
            </tr>
            """)
        
        html = f"""
        <div style="display: flex; justify-content: center;">
            <div class="energy-table" style="max-width: 1100px; width: 70%;">
                <div class="table-header">
                    <h3 class="table-title">Comparativa de Rendimiento y Ahorro</h3>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>PLANTA</th>
                            <th>TOTAL GENERADO</th>
                            <th>PROMEDIO DIARIO</th>
                            <th>MÁXIMO DIARIO</th>
                            <th>AHORRO TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        components.html(html, height=300, scrolling=False)

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #94a3b8; font-size: 11px; padding: 16px; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0;'>
    Dashboard Energía Solar | Sistema de Monitoreo Avanzado de Plantas Fotovoltaicas | © 2025
</div>
""", unsafe_allow_html=True)