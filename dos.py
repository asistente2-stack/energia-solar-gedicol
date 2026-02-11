#!/usr/bin/env python3
"""
Dashboard Energia Solar GEDICOL - Streamlit
Tema claro con acentos rosa/magenta, KPIs ejecutivos.

Dependencias:
  pip install streamlit pandas numpy openpyxl matplotlib

Ejecucion:
  streamlit run dos.py
"""

import os, glob
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Dashboard Energia Solar - GEDICOL",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- PALETA CLARA (inspirada en la referencia) --
# Fondo: blanco / gris muy claro
# Acentos: rosa-magenta (#E91E8C), verde-teal (#00BFA5), azul (#2196F3)
# Textos: gris oscuro (#2D3436), gris medio (#636E72)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');

    /* === BASE === */
    .stApp {
        background: #F5F6FA !important;
        font-family: 'Poppins', sans-serif !important;
    }
    .block-container {
        padding: 1rem 2rem 2rem !important;
        max-width: 1440px !important;
    }
    #MainMenu, footer, header {visibility: hidden;}

    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B5E3B 0%, #2E7D52 50%, #43A36E 100%) !important;
        padding-top: 0.5rem;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
    }
    [data-testid="stSidebar"] label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.85;
    }
    [data-testid="stSidebar"] .stMultiSelect > div > div,
    [data-testid="stSidebar"] .stDateInput > div > div {
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        border-radius: 10px !important;
    }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background: rgba(255,255,255,0.3) !important;
        border-radius: 6px !important;
    }

    /* === METRIC OVERRIDES === */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E8ECF0 !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    [data-testid="stMetricLabel"] {
        color: #636E72 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #2D3436 !important;
        font-size: 20px !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 11px !important;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: #E8ECF0;
        padding: 4px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: #636E72;
        font-weight: 700;
        font-size: 13px;
        padding: 10px 24px;
        font-family: 'Poppins', sans-serif;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #E91E8C, #C2185B) !important;
        color: #fff !important;
        box-shadow: 0 4px 12px rgba(233,30,140,0.25);
    }

    /* === HERO HEADER === */
    .hero {
        background: linear-gradient(135deg, #1B5E3B 0%, #2E7D52 60%, #43A36E 100%);
        border-radius: 18px;
        padding: 24px 32px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(27,94,59,0.2);
    }
    .hero-left h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 26px;
        font-weight: 900;
        color: #FFFFFF;
        margin: 0;
    }
    .hero-left p {
        font-size: 12px;
        color: rgba(255,255,255,0.75);
        margin: 4px 0 0;
        font-weight: 500;
    }
    .hero-right {
        display: flex;
        gap: 24px;
        align-items: center;
    }
    .hero-stat {
        text-align: center;
    }
    .hero-stat .val {
        font-family: 'Poppins', sans-serif;
        font-size: 28px;
        font-weight: 900;
        color: #FFFFFF;
        line-height: 1;
    }
    .hero-stat .lbl {
        font-size: 10px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-top: 4px;
    }
    .hero-divider {
        width: 1px;
        height: 50px;
        background: rgba(255,255,255,0.25);
    }

    /* === KPI CARDS === */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 22px;
    }
    @media (max-width: 900px) {
        .kpi-row { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 20px 22px;
        border: 1px solid #E8ECF0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        display: flex;
        align-items: center;
        gap: 16px;
        transition: all 0.25s;
    }
    .kpi:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }
    .kpi-icon {
        width: 52px; height: 52px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        flex-shrink: 0;
    }
    .kpi-icon.pink   { background: #FDE8F3; color: #E91E8C; }
    .kpi-icon.green  { background: #E0F7EF; color: #00BFA5; }
    .kpi-icon.blue   { background: #E3F2FD; color: #2196F3; }
    .kpi-icon.amber  { background: #FFF8E1; color: #FF9800; }

    .kpi-body { flex: 1; }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        color: #95A5A6;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-val {
        font-size: 26px;
        font-weight: 900;
        color: #2D3436;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 11px;
        color: #95A5A6;
        font-weight: 500;
        margin-top: 2px;
    }
    .kpi-sub b { color: #636E72; }

    /* === SIDE METRICS (Metricas Adicionales) === */
    .side-title {
        font-family: 'Poppins', sans-serif;
        font-size: 18px;
        font-weight: 800;
        color: #E91E8C;
        font-style: italic;
        margin-bottom: 16px;
        text-align: center;
    }
    .side-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 18px 16px;
        border: 1px solid #E8ECF0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 14px;
        transition: all 0.2s;
    }
    .side-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        transform: translateX(3px);
    }
    .side-icon {
        width: 50px; height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
    }
    .side-icon.pink   { background: linear-gradient(135deg, #FDE8F3, #FCE4EC); color: #E91E8C; }
    .side-icon.teal   { background: linear-gradient(135deg, #E0F7EF, #E0F2F1); color: #00BFA5; }
    .side-icon.blue   { background: linear-gradient(135deg, #E3F2FD, #BBDEFB); color: #2196F3; }
    .side-icon.orange { background: linear-gradient(135deg, #FFF8E1, #FFE0B2); color: #FF9800; }

    .side-info { flex: 1; }
    .side-info .label {
        font-size: 11px;
        font-weight: 600;
        color: #95A5A6;
        margin-bottom: 2px;
    }
    .side-info .value {
        font-size: 24px;
        font-weight: 900;
        color: #2D3436;
        line-height: 1;
    }
    .side-info .sub {
        font-size: 10px;
        color: #B2BEC3;
        margin-top: 2px;
    }

    /* === SECTION HEADERS === */
    .sec-hdr {
        font-family: 'Poppins', sans-serif;
        font-size: 16px;
        font-weight: 800;
        color: #2D3436;
        margin: 20px 0 10px;
        padding-bottom: 8px;
        border-bottom: 3px solid #E8ECF0;
    }

    /* === TABLES === */
    .tbl-wrap {
        background: #FFFFFF;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #E8ECF0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }
    .tbl-hd {
        background: linear-gradient(135deg, #E91E8C, #C2185B);
        padding: 14px 22px;
    }
    .tbl-hd h3 {
        color: #fff;
        font-family: 'Poppins', sans-serif;
        font-size: 14px;
        font-weight: 700;
        margin: 0;
    }
    table.dt {width:100%; border-collapse:collapse; font-family:'Poppins',sans-serif;}
    table.dt thead th {
        background: #F8F9FA;
        color: #E91E8C;
        padding: 12px 16px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #F0E0EA;
        text-align: left;
    }
    table.dt tbody td {
        padding: 12px 16px;
        font-size: 13px;
        font-weight: 500;
        color: #2D3436;
        border-bottom: 1px solid #F5F6FA;
    }
    table.dt tbody tr:hover { background: #FFF5F9 !important; }

    .badge-c {
        background: linear-gradient(135deg, #2196F3, #1976D2);
        color: #fff; padding: 3px 10px; border-radius: 6px;
        font-size: 10px; font-weight: 700;
    }
    .badge-m {
        background: linear-gradient(135deg, #00BFA5, #00897B);
        color: #fff; padding: 3px 10px; border-radius: 6px;
        font-size: 10px; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# -- Helpers --
def fmt(x, d=0):
    try:
        v = float(x)
    except:
        return "0"
    s = f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.split(",")[0] if d == 0 else s

def fmoney(x):
    try:
        v = float(x)
    except:
        return "$0"
    return f"${v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

MESES_C = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
MESES_L = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
           "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
COSTOS = {"CAFE": 1033, "MERCADO": 1077}

def bdg(p):
    return '<span class="badge-c">CAFE</span>' if p == "CAFE" else '<span class="badge-m">MERCADO</span>'


# -- Carga datos --
@st.cache_data
def load():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    archivo = None
    for pat in ["Reporte_Energia_Solar_GEDICOL*.xlsx"]:
        hits = sorted(glob.glob(os.path.join(carpeta, pat)))
        if hits:
            archivo = hits[-1]
            break
    if not archivo:
        return None, None, None

    m = pd.read_excel(archivo, sheet_name="POR MES")
    d = pd.read_excel(archivo, sheet_name="POR DIA")
    h = pd.read_excel(archivo, sheet_name="POR HORA")
    for df in [m, d, h]:
        df.columns = [str(c).strip().lower() for c in df.columns]
        df["planta"] = df["planta"].str.strip().str.upper()
    d["fecha"] = pd.to_datetime(d["fecha"])
    h["fecha"] = pd.to_datetime(h["fecha"])
    h["hora_num"] = pd.to_datetime(h["hora"], format="%H:%M").dt.hour
    return m, d, h

mensual_df, diario_df, horario_df = load()
if mensual_df is None:
    st.error("No se encontro Reporte_Energia_Solar_GEDICOL.xlsx")
    st.stop()


# =============================================
# SIDEBAR
# =============================================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:8px 0 16px;'>
        <div style='font-size:32px; font-weight:900; color:#fff;'>GEDICOL</div>
        <div style='font-size:11px; color:rgba(255,255,255,0.6);
                    letter-spacing:2px; text-transform:uppercase;'>Energia Solar</div>
    </div>
    <hr style='border-color:rgba(255,255,255,0.15); margin:0 0 14px;'>
    """, unsafe_allow_html=True)

    pl_disp = sorted(mensual_df["planta"].unique().tolist())
    sel_pl = st.multiselect("Planta", options=pl_disp, default=pl_disp, key="fp")
    if not sel_pl: sel_pl = pl_disp

    yr_disp = sorted(mensual_df["anio"].unique().tolist())
    sel_yr = st.multiselect("Anio", options=yr_disp, default=yr_disp, key="fy")
    if not sel_yr: sel_yr = yr_disp

    ms_disp = sorted(mensual_df["mes"].unique().tolist())
    sel_ms = st.multiselect("Mes", options=ms_disp, default=ms_disp,
                            format_func=lambda m: MESES_C[m], key="fm")
    if not sel_ms: sel_ms = ms_disp

    st.markdown("<hr style='border-color:rgba(255,255,255,0.15);margin:14px 0;'>",
                unsafe_allow_html=True)

    min_f = diario_df["fecha"].min().date()
    max_f = diario_df["fecha"].max().date()
    st.markdown("<p style='font-size:10px;font-weight:700;letter-spacing:1.2px;"
                "text-transform:uppercase;opacity:0.7;'>Rango de Fechas</p>",
                unsafe_allow_html=True)
    f_ini = st.date_input("Desde", value=min_f, min_value=min_f, max_value=max_f, key="fd")
    f_fin = st.date_input("Hasta", value=max_f, min_value=min_f, max_value=max_f, key="fh")
    if f_ini > f_fin: f_ini, f_fin = f_fin, f_ini


# -- Filtros --
mf = mensual_df[(mensual_df["anio"].isin(sel_yr)) & (mensual_df["mes"].isin(sel_ms)) &
                (mensual_df["planta"].isin(sel_pl))].copy()
df = diario_df[(diario_df["fecha"].dt.date >= f_ini) & (diario_df["fecha"].dt.date <= f_fin) &
               (diario_df["planta"].isin(sel_pl)) & (diario_df["fecha"].dt.year.isin(sel_yr)) &
               (diario_df["fecha"].dt.month.isin(sel_ms))].copy()
hf = horario_df[(horario_df["fecha"].dt.date >= f_ini) & (horario_df["fecha"].dt.date <= f_fin) &
                (horario_df["planta"].isin(sel_pl)) & (horario_df["fecha"].dt.year.isin(sel_yr)) &
                (horario_df["fecha"].dt.month.isin(sel_ms))].copy()

# -- Metricas --
g_cafe = mf.loc[mf["planta"]=="CAFE","energia_kwh"].sum()
g_merc = mf.loc[mf["planta"]=="MERCADO","energia_kwh"].sum()
g_total = g_cafe + g_merc
a_cafe = g_cafe * COSTOS["CAFE"]
a_merc = g_merc * COSTOS["MERCADO"]
a_total = a_cafe + a_merc
dias = df["fecha"].nunique()
prom = g_total / dias if dias > 0 else 0
co2 = g_total * 0.126 / 1000


# =============================================
# HERO HEADER
# =============================================
st.markdown(f"""
<div class="hero">
    <div class="hero-left">
        <h1>Dashboard Energia Solar</h1>
        <p>Monitoreo Plantas CAFE & MERCADO &middot; Montesereno</p>
    </div>
    <div class="hero-right">
        <div class="hero-stat">
            <div class="val">{fmt(g_total,0)}</div>
            <div class="lbl">kWh Generados</div>
        </div>
        <div class="hero-divider"></div>
        <div class="hero-stat">
            <div class="val">{fmoney(a_total)}</div>
            <div class="lbl">Ahorro Total</div>
        </div>
        <div class="hero-divider"></div>
        <div class="hero-stat">
            <div class="val">{fmt(co2,2)}</div>
            <div class="lbl">Ton CO2 Evitadas</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================
# KPI CARDS
# =============================================
khtml = '<div class="kpi-row">'

khtml += f"""
<div class="kpi">
    <div class="kpi-icon pink">&#9889;</div>
    <div class="kpi-body">
        <div class="kpi-label">Generacion CAFE</div>
        <div class="kpi-val">{fmt(g_cafe,1)}</div>
        <div class="kpi-sub">kWh &middot; Ahorro <b>{fmoney(a_cafe)}</b></div>
    </div>
</div>"""

khtml += f"""
<div class="kpi">
    <div class="kpi-icon green">&#9889;</div>
    <div class="kpi-body">
        <div class="kpi-label">Generacion MERCADO</div>
        <div class="kpi-val">{fmt(g_merc,1)}</div>
        <div class="kpi-sub">kWh &middot; Ahorro <b>{fmoney(a_merc)}</b></div>
    </div>
</div>"""

khtml += f"""
<div class="kpi">
    <div class="kpi-icon blue">&#9733;</div>
    <div class="kpi-body">
        <div class="kpi-label">Promedio Diario</div>
        <div class="kpi-val">{fmt(prom,1)}</div>
        <div class="kpi-sub">kWh/dia &middot; <b>{dias}</b> dias</div>
    </div>
</div>"""

khtml += f"""
<div class="kpi">
    <div class="kpi-icon amber">&#127811;</div>
    <div class="kpi-body">
        <div class="kpi-label">CO2 Evitado</div>
        <div class="kpi-val">{fmt(co2,2)}</div>
        <div class="kpi-sub">toneladas &middot; Factor 0,126 kg/kWh</div>
    </div>
</div>"""

khtml += '</div>'
st.markdown(khtml, unsafe_allow_html=True)


# =============================================
# TABS
# =============================================
tab1, tab2, tab3 = st.tabs(["Mensual", "Diario", "Por Hora"])

# -- Chart style --
PINK = "#E91E8C"
TEAL = "#00BFA5"
PC = {"CAFE": "#E91E8C", "MERCADO": "#00BFA5"}

def light_ax(ax, fig):
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    for sp in ax.spines.values():
        sp.set_color('#E8ECF0')
        sp.set_linewidth(0.8)
    ax.tick_params(colors='#95A5A6', labelsize=9)
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='#DFE6E9')
    ax.xaxis.label.set_color('#636E72')
    ax.yaxis.label.set_color('#636E72')
    ax.title.set_color('#2D3436')


MESES_EN_ES = {
    "January":"Enero","February":"Febrero","March":"Marzo","April":"Abril",
    "May":"Mayo","June":"Junio","July":"Julio","August":"Agosto",
    "September":"Septiembre","October":"Octubre","November":"Noviembre","December":"Diciembre",
}

# -- TABLE STYLES (shared) --
TBL_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    body { background:transparent; font-family:'Poppins',sans-serif; }
    .tbl-wrap { background:#fff; border-radius:16px; overflow:hidden;
                border:1px solid #E8ECF0; box-shadow:0 2px 12px rgba(0,0,0,0.04); }
    .tbl-hd { background:linear-gradient(135deg,#E91E8C,#C2185B); padding:14px 22px; }
    .tbl-hd.green { background:linear-gradient(135deg,#00BFA5,#00897B); }
    .tbl-hd.purple { background:linear-gradient(135deg,#7C4DFF,#651FFF); }
    .tbl-hd h3 { color:#fff; font-size:14px; font-weight:700; margin:0; }
    table.dt { width:100%; border-collapse:collapse; }
    table.dt thead th { background:#F8F9FA; color:#E91E8C; padding:12px 16px;
                        font-size:10px; font-weight:700; text-transform:uppercase;
                        letter-spacing:0.8px; border-bottom:2px solid #FCE4EC; text-align:left; }
    table.dt.green thead th { color:#00BFA5; border-bottom-color:#E0F2F1; }
    table.dt.purple thead th { color:#7C4DFF; border-bottom-color:#EDE7F6; }
    table.dt tbody td { padding:12px 16px; font-size:13px; font-weight:500;
                        color:#2D3436; border-bottom:1px solid #F5F6FA; }
    table.dt tbody tr:hover { background:#FFF5F9 !important; }
    .badge-c { background:linear-gradient(135deg,#E91E8C,#C2185B); color:#fff;
               padding:3px 10px; border-radius:6px; font-size:10px; font-weight:700; }
    .badge-m { background:linear-gradient(135deg,#00BFA5,#00897B); color:#fff;
               padding:3px 10px; border-radius:6px; font-size:10px; font-weight:700; }
</style>
"""


# =============================================
# TAB 1 - MENSUAL
# =============================================
with tab1:
    if mf.empty:
        st.warning("Sin datos para los filtros seleccionados.")
    else:
        col_chart, col_side = st.columns([3, 1])

        with col_chart:
            pivot = (
                mf.pivot_table(index=["anio","mes"], columns="planta",
                               values="energia_kwh", aggfunc="sum", fill_value=0)
                .reset_index().sort_values(["anio","mes"])
            )
            pivot["label"] = pivot.apply(
                lambda r: f"{MESES_C[int(r['mes'])]}\n{int(r['anio'])}", axis=1)

            fig, ax = plt.subplots(figsize=(14, 5.5))
            light_ax(ax, fig)
            x = np.arange(len(pivot))
            w = 0.36

            for i, pl in enumerate(sel_pl):
                if pl in pivot.columns:
                    off = -w/2 if i == 0 else w/2
                    c = PC.get(pl, "#7C4DFF")
                    bars = ax.bar(x+off, pivot[pl], w, label=pl,
                                  color=c, edgecolor='white', linewidth=0.8,
                                  alpha=0.88, zorder=3)
                    for bar in bars:
                        h = bar.get_height()
                        if h > 0:
                            ax.text(bar.get_x()+bar.get_width()/2, h+g_total*0.006,
                                    fmt(h,0), ha='center', va='bottom',
                                    fontsize=8, fontweight='bold', color='#636E72',
                                    fontfamily='Poppins')

            ax.set_xticks(x)
            ax.set_xticklabels(pivot["label"], fontsize=9, fontweight='bold')
            ax.set_ylabel("Energia (kWh)", fontsize=11, fontweight='bold')
            ax.set_title("Generacion Solar Mensual por Planta",
                         fontsize=16, fontweight='black', pad=14, fontfamily='Poppins')
            ax.legend(fontsize=10, framealpha=0.9, edgecolor='#E8ECF0')
            fig.tight_layout()
            st.pyplot(fig, clear_figure=True)

        with col_side:
            st.markdown('<div class="side-title">Metricas Adicionales</div>',
                        unsafe_allow_html=True)

            if not mf.empty:
                best = mf.loc[mf["energia_kwh"].idxmax()]
                best_lbl = f"{MESES_L[int(best['mes'])]} {int(best['anio'])}"

                total_m = len(mf)
                avg_m = g_total / total_m if total_m > 0 else 0

                if not df.empty:
                    bd = df.loc[df["energia_kwh"].idxmax()]
                    bd_val = bd["energia_kwh"]
                    bd_date = pd.to_datetime(bd["fecha"]).strftime("%d/%m/%Y")
                else:
                    bd_val = 0; bd_date = "-"

                st.markdown(f"""
                <div class="side-card">
                    <div class="side-icon pink">&#9733;</div>
                    <div class="side-info">
                        <div class="label">Mejor Mes</div>
                        <div class="value">{fmt(best['energia_kwh'],0)}</div>
                        <div class="sub">{best_lbl} - {best['planta']}</div>
                    </div>
                </div>
                <div class="side-card">
                    <div class="side-icon teal">&#8801;</div>
                    <div class="side-info">
                        <div class="label">Promedio Mensual</div>
                        <div class="value">{fmt(avg_m,1)}</div>
                        <div class="sub">kWh por planta/mes</div>
                    </div>
                </div>
                <div class="side-card">
                    <div class="side-icon blue">&#9650;</div>
                    <div class="side-info">
                        <div class="label">Mejor Dia</div>
                        <div class="value">{fmt(bd_val,1)}</div>
                        <div class="sub">{bd_date}</div>
                    </div>
                </div>
                <div class="side-card">
                    <div class="side-icon orange">&#8986;</div>
                    <div class="side-info">
                        <div class="label">Dias Monitoreados</div>
                        <div class="value">{dias}</div>
                        <div class="sub">Total del periodo</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Tabla mensual
        st.markdown('<div class="sec-hdr">Detalle Mensual</div>', unsafe_allow_html=True)
        rows = ""
        for i, (_, r) in enumerate(mf.sort_values(["anio","mes"]).iterrows()):
            ah = r["energia_kwh"] * COSTOS.get(r["planta"], 0)
            bg = "#FFFFFF" if i%2==0 else "#FAFBFC"
            rows += (
                f"<tr style='background:{bg}'>"
                f"<td style='font-weight:700'>{MESES_L[int(r['mes'])]} {int(r['anio'])}</td>"
                f"<td>{bdg(r['planta'])}</td>"
                f"<td style='color:#E91E8C;font-weight:700'>{fmt(r['energia_kwh'],1)} kWh</td>"
                f"<td style='color:#00BFA5;font-weight:800'>{fmoney(ah)}</td>"
                f"</tr>")

        components.html(f"""{TBL_CSS}
        <div class="tbl-wrap">
            <div class="tbl-hd"><h3>Balance Mensual - Generacion y Ahorro</h3></div>
            <table class="dt">
                <thead><tr><th>Periodo</th><th>Planta</th><th>Generacion</th><th>Ahorro</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>""", height=min(500, 90+len(mf)*50), scrolling=True)


# =============================================
# TAB 2 - DIARIO
# =============================================
with tab2:
    if df.empty:
        st.warning("Sin datos para los filtros seleccionados.")
    else:
        mcols = st.columns(4)
        for idx, pl in enumerate(sel_pl):
            dp = df[df["planta"]==pl]
            if dp.empty: continue
            t=dp["energia_kwh"].sum(); p=dp["energia_kwh"].mean(); mx=dp["energia_kwh"].max()
            ah=t*COSTOS.get(pl,0)
            with mcols[idx]:
                st.metric(f"{pl} Total", f"{fmt(t,1)} kWh", f"Prom {fmt(p,1)} kWh/dia")
            with mcols[idx+2]:
                st.metric(f"{pl} Ahorro", fmoney(ah), f"Max {fmt(mx,1)} kWh/dia")

        fig, ax = plt.subplots(figsize=(16, 5.5))
        light_ax(ax, fig)
        for pl in sel_pl:
            dp = df[df["planta"]==pl].sort_values("fecha")
            if dp.empty: continue
            c = PC.get(pl, "#7C4DFF")
            ax.plot(dp["fecha"], dp["energia_kwh"], linewidth=2, label=pl, color=c, alpha=0.9)
            ax.fill_between(dp["fecha"], dp["energia_kwh"], alpha=0.12, color=c)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)
        ax.set_ylabel("Energia (kWh)", fontsize=11, fontweight='bold')
        ax.set_title("Evolucion Diaria de Generacion Solar",
                     fontsize=16, fontweight='black', pad=14, fontfamily='Poppins')
        ax.legend(fontsize=10, framealpha=0.9, edgecolor='#E8ECF0')
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

        st.markdown('<div class="sec-hdr">Detalle Diario</div>', unsafe_allow_html=True)
        sd = df.sort_values("fecha")
        rows=""
        for i,(_, r) in enumerate(sd.iterrows()):
            ah = r["energia_kwh"]*COSTOS.get(r["planta"],0)
            fd = pd.to_datetime(r["fecha"])
            fs = f"{fd.day:02d} {fd.strftime('%B')} {fd.year}"
            for en, es in MESES_EN_ES.items(): fs = fs.replace(en, es)
            bg = "#FFFFFF" if i%2==0 else "#FAFBFC"
            rows += (
                f"<tr style='background:{bg}'>"
                f"<td style='font-weight:700'>{fs}</td>"
                f"<td>{bdg(r['planta'])}</td>"
                f"<td style='color:#E91E8C;font-weight:700'>{fmt(r['energia_kwh'],1)} kWh</td>"
                f"<td style='color:#00BFA5;font-weight:800'>{fmoney(ah)}</td>"
                f"</tr>")

        components.html(f"""{TBL_CSS}
        <div class="tbl-wrap">
            <div class="tbl-hd green"><h3>Detalle Diario - Generacion y Ahorro</h3></div>
            <table class="dt green">
                <thead><tr><th>Fecha</th><th>Planta</th><th>Generacion</th><th>Ahorro</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>""", height=520, scrolling=True)


# =============================================
# TAB 3 - POR HORA
# =============================================
with tab3:
    if hf.empty:
        st.warning("Sin datos para los filtros seleccionados.")
    else:
        hs = hf.groupby("hora_num")["energia_kwh"].sum()
        hg = hs[hs>0]
        hp = hs.idxmax() if not hs.empty else 0
        hi = hg.index.min() if len(hg)>0 else 0
        he = hg.index.max() if len(hg)>0 else 0
        hpp = len(hg)
        pp = hf[hf["hora_num"]==hp]["energia_kwh"].mean() if hp else 0

        hcols = st.columns(3)
        with hcols[0]:
            st.metric("Hora Pico", f"{int(hp)}:00", f"{fmt(hs.get(hp,0),1)} kWh acum.")
        with hcols[1]:
            st.metric("Ventana Solar", f"{int(hi)}:00 - {int(he)}:00", f"{hpp} horas activas")
        with hcols[2]:
            st.metric("Promedio Hora Pico", f"{fmt(pp,2)} kWh", "Por registro")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        fig, ax = plt.subplots(figsize=(14, 5.5))
        light_ax(ax, fig)
        hprom = hf.groupby(["hora_num","planta"])["energia_kwh"].mean().reset_index()

        for pl in sel_pl:
            dp = hprom[hprom["planta"]==pl].sort_values("hora_num")
            if dp.empty: continue
            c = PC.get(pl, "#7C4DFF")
            ax.fill_between(dp["hora_num"], dp["energia_kwh"], alpha=0.15, color=c)
            ax.plot(dp["hora_num"], dp["energia_kwh"],
                    marker='o', markersize=6, linewidth=2.5, label=pl, color=c, zorder=4)
            ix = dp["energia_kwh"].idxmax()
            rm = dp.loc[ix]
            ax.annotate(
                f"{fmt(rm['energia_kwh'],2)} kWh",
                xy=(rm["hora_num"], rm["energia_kwh"]),
                xytext=(0,14), textcoords="offset points",
                ha="center", fontsize=9, fontweight="bold", color=c,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=c, alpha=0.9))

        ax.set_xticks(range(5,21))
        ax.set_xticklabels([f"{h}:00" for h in range(5,21)], fontsize=9, fontweight='bold')
        ax.set_xlim(4.5, 20.5)
        ax.set_ylabel("Energia Promedio (kWh)", fontsize=11, fontweight='bold')
        ax.set_xlabel("Hora del dia", fontsize=11, fontweight='bold')
        ax.set_title("Perfil Solar Promedio por Hora",
                     fontsize=16, fontweight='black', pad=14, fontfamily='Poppins')
        ax.legend(fontsize=10, framealpha=0.9, edgecolor='#E8ECF0')
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

        st.markdown('<div class="sec-hdr">Resumen por Hora</div>', unsafe_allow_html=True)
        res = (hf.groupby(["hora_num","planta"])["energia_kwh"]
               .agg(["mean","sum","count"]).reset_index()
               .sort_values(["planta","hora_num"]))
        res.columns = ["hora_num","planta","promedio","total","registros"]
        rows=""
        for i,(_, r) in enumerate(res.iterrows()):
            if r["total"]==0: continue
            ah = r["total"]*COSTOS.get(r["planta"],0)
            bg = "#FFFFFF" if i%2==0 else "#FAFBFC"
            rows += (
                f"<tr style='background:{bg}'>"
                f"<td style='font-weight:700'>{int(r['hora_num']):02d}:00</td>"
                f"<td>{bdg(r['planta'])}</td>"
                f"<td style='color:#E91E8C;font-weight:700'>{fmt(r['promedio'],2)} kWh</td>"
                f"<td style='font-weight:600'>{fmt(r['total'],1)} kWh</td>"
                f"<td style='color:#00BFA5;font-weight:800'>{fmoney(ah)}</td>"
                f"<td style='color:#95A5A6'>{int(r['registros'])}</td>"
                f"</tr>")

        components.html(f"""{TBL_CSS}
        <div class="tbl-wrap">
            <div class="tbl-hd purple"><h3>Generacion Promedio y Total por Hora</h3></div>
            <table class="dt purple">
                <thead><tr><th>Hora</th><th>Planta</th><th>Promedio</th>
                <th>Total</th><th>Ahorro</th><th>Registros</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>""", height=480, scrolling=True)


# -- Footer --
st.markdown("""
<div style='text-align:center; color:#B2BEC3; font-size:10px;
            padding:20px; margin-top:32px; border-top:2px solid #E8ECF0;
            letter-spacing:1px;'>
    Dashboard Energia Solar &middot; GEDICOL &middot; 2025
</div>
""", unsafe_allow_html=True)