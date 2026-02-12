# -*- coding: utf-8 -*-
import re
from io import StringIO
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# CONFIG (TUS SHEETS)
# =========================
SOLAR_SHEET_ID = "1ceFwwFm6D1QRW4slPj67BlSDR9woGFFaOMLoN1FxVvs"
SOLAR_TAB_MES  = "POR MES"
SOLAR_TAB_DIA  = "POR DIA"
SOLAR_TAB_HORA = "POR HORA"

EPM_SHEET_ID   = "1ANEtNlryqo_4wq1n6V5OlutpcDFMP_EdxxWXgjEhQ3c"
EPM_GID_MES    = "2089036315"

COSTOS_EPM = {"CAFE": 1033, "MERCADO": 1077}

# PALETA CORPORATIVA (NO CAMBIAR)
COLOR_CAFE  = "#3b82f6"
COLOR_MERC  = "#10b981"
COLOR_TOTAL = "#8b5cf6"
COLOR_AMBAR = "#f59e0b"
BG_APP      = "#f8fafc"

MES_NOMBRES_LARGO = {
    1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun",
    7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"
}

st.set_page_config(
    page_title="Dashboard Energia Solar - GEDICOL",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================
# CSS
# =========================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}
.block-container {{ padding-top: 0.6rem; padding-bottom: 2rem; background: {BG_APP}; }}
#MainMenu {{ visibility: hidden; }} footer {{ visibility: hidden; }} header {{ visibility: hidden; }}
.main {{ background-color: {BG_APP}; }}

.header-wrap {{
    text-align:center; padding:16px 0;
    background:linear-gradient(135deg,{BG_APP} 0%,#ffffff 100%);
    border-radius:14px; margin-bottom:12px; border:1px solid #e2e8f0;
    box-shadow:0 2px 12px rgba(0,0,0,.04);
}}
.header-wrap h1 {{
    font-size:28px; font-weight:900; margin:0;
    background:linear-gradient(135deg,{COLOR_CAFE} 0%,{COLOR_MERC} 50%,{COLOR_TOTAL} 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}}
.header-wrap p {{ margin:6px 0 0; font-size:12px; color:#64748b; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; }}

.left-card {{ background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:16px; box-shadow:0 4px 14px rgba(0,0,0,.06); }}
.left-title {{ font-size:15px; font-weight:900; margin:0 0 10px 0; color:#0f172a; }}
.filter-section {{ font-size:11px; font-weight:800; color:{COLOR_CAFE}; text-transform:uppercase; letter-spacing:1.5px; padding:10px 0 4px 0; margin-top:8px; border-top:1px solid #e2e8f0; }}
.small-note {{ font-size:10px; color:#94a3b8; font-weight:500; line-height:1.3; background:#f1f5f9; border-radius:8px; padding:8px; margin-top:6px; }}

.kpi-row {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px; }}
.kpi-card {{
    flex:1; min-width:140px; background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:14px 16px; box-shadow:0 4px 14px rgba(0,0,0,.05); border-left:5px solid {COLOR_TOTAL};
    transition:transform 0.2s ease, box-shadow 0.2s ease;
}}
.kpi-card:hover {{ transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,.1); }}
.kpi-card.cafe  {{ border-left-color:{COLOR_CAFE}; }}
.kpi-card.merc  {{ border-left-color:{COLOR_MERC}; }}
.kpi-card.total {{ border-left-color:{COLOR_TOTAL}; }}
.kpi-card.ahorro {{ border-left-color:{COLOR_AMBAR}; }}
.kpi-card.cob   {{ border-left-color:#ef4444; }}
.kpi-label {{ font-size:10px; font-weight:900; color:#64748b; text-transform:uppercase; letter-spacing:1px; }}
.kpi-value {{ font-size:24px; font-weight:900; margin-top:4px; line-height:1; }}
.kpi-sub   {{ font-size:11px; color:#64748b; font-weight:600; margin-top:6px; line-height:1.3; }}

.panel {{ background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:18px; box-shadow:0 4px 14px rgba(0,0,0,.06); margin-bottom:14px; }}
.panel-title {{ font-size:15px; font-weight:900; color:#0f172a; margin:0 0 2px 0; }}
.panel-sub {{ font-size:11px; color:#64748b; font-weight:600; margin:0 0 10px 0; }}

.stat-grid {{ display:flex; gap:10px; flex-wrap:wrap; margin:12px 0; }}
.stat-card {{
    flex:1; min-width:120px; text-align:center;
    background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:14px 10px;
}}
.stat-label {{ font-size:10px; font-weight:800; color:#64748b; text-transform:uppercase; letter-spacing:1px; }}
.stat-value {{ font-size:24px; font-weight:900; margin:4px 0 2px 0; }}
.stat-extra {{ font-size:10px; color:#94a3b8; font-weight:600; }}

.dash-footer {{
    text-align:center; color:#94a3b8; font-size:11px; padding:14px;
    background:#fff; border:1px solid #e2e8f0; border-radius:12px; margin-top:16px;
}}
div[data-baseweb="select"] > div {{ border-radius:10px !important; }}
</style>
""", unsafe_allow_html=True)

# =========================
# PLOTLY LIGHT THEME
# =========================
PLOTLY_LIGHT = dict(
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(255,255,255,0)",
    font=dict(family="Inter, sans-serif", color="#0f172a", size=12),
    margin=dict(l=50, r=30, t=50, b=50),
    legend=dict(bgcolor="rgba(255,255,255,0.95)", bordercolor="#e2e8f0", borderwidth=1, font=dict(size=11, color="#0f172a")),
)

def apply_light(fig, h=420):
    fig.update_layout(**PLOTLY_LIGHT, height=h)
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", gridwidth=1, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", gridwidth=1, zeroline=False)
    return fig

# =========================
# UTILS
# =========================
def _clean_cols(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def safe_float(x):
    try:
        v = float(x)
        return 0.0 if (np.isnan(v) or np.isinf(v)) else v
    except:
        return 0.0

def fmt_num(x, decimals=0):
    v = safe_float(x)
    s = f"{v:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    if decimals == 0:
        s = s.split(",")[0]
    return s

def fmt_currency(x):
    v = safe_float(x)
    s = f"${v:,.0f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def mes_anio_label(y, m):
    """Ej: 'Dic 2025'"""
    return f"{MES_NOMBRES_LARGO.get(int(m), str(m))} {int(y)}"

def fecha_label_dia(dt):
    """Ej: '22 Oct 2025'"""
    dia = dt.day
    mes_str = MES_NOMBRES_LARGO.get(dt.month, str(dt.month))
    return f"{dia} {mes_str} {dt.year}"

def parse_hora_to_hour(x):
    if pd.isna(x): return np.nan
    s = str(x).strip()
    if s == "": return np.nan
    if re.fullmatch(r"\d+(\.\d+)?", s):
        try: return int(float(s))
        except: return np.nan
    parts = s.split(":")
    if len(parts) >= 1 and re.fullmatch(r"\d+", parts[0]):
        try: return int(parts[0])
        except: return np.nan
    return np.nan

# =========================
# GOOGLE SHEETS READ
# =========================
def read_gsheet_csv_by_gid(sheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    r = requests.get(url, timeout=30)
    if r.status_code != 200 or len(r.text) < 10:
        raise RuntimeError("No pude leer Google Sheet por gid.")
    return pd.read_csv(StringIO(r.text))

def read_gsheet_csv_by_name(sheet_id, tab_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={requests.utils.quote(tab_name)}"
    r = requests.get(url, timeout=30)
    if r.status_code != 200 or len(r.text) < 10:
        raise RuntimeError("No pude leer Google Sheet por pestana.")
    return pd.read_csv(StringIO(r.text))

@st.cache_data(ttl=300)
def cargar_datos_nube():
    mensual = _clean_cols(read_gsheet_csv_by_name(SOLAR_SHEET_ID, SOLAR_TAB_MES))
    diario  = _clean_cols(read_gsheet_csv_by_name(SOLAR_SHEET_ID, SOLAR_TAB_DIA))
    horario = _clean_cols(read_gsheet_csv_by_name(SOLAR_SHEET_ID, SOLAR_TAB_HORA))

    if "año" in mensual.columns and "anio" not in mensual.columns:
        mensual["anio"] = mensual["año"]
    if "energía_kwh" in mensual.columns and "energia_kwh" not in mensual.columns:
        mensual["energia_kwh"] = mensual["energía_kwh"]

    mensual["planta"] = mensual["planta"].astype(str).str.strip().str.upper()
    mensual["anio"] = pd.to_numeric(mensual["anio"], errors="coerce").fillna(0).astype(int)
    mensual["mes"]  = pd.to_numeric(mensual["mes"], errors="coerce").fillna(0).astype(int)
    mensual["energia_kwh"] = pd.to_numeric(mensual["energia_kwh"], errors="coerce").fillna(0.0)

    diario["planta"] = diario["planta"].astype(str).str.strip().str.upper()
    diario["energia_kwh"] = pd.to_numeric(diario["energia_kwh"], errors="coerce").fillna(0.0)
    diario["fecha"] = pd.to_datetime(diario["fecha"], errors="coerce", dayfirst=True)

    horario["planta"] = horario["planta"].astype(str).str.strip().str.upper()
    horario["energia_kwh"] = pd.to_numeric(horario["energia_kwh"], errors="coerce").fillna(0.0)
    horario["fecha"] = pd.to_datetime(horario["fecha"], errors="coerce", dayfirst=True)
    horario["hora_num"] = horario["hora"].apply(parse_hora_to_hour)
    horario["hora_num"] = pd.to_numeric(horario["hora_num"], errors="coerce")

    # EPM
    epm_raw = _clean_cols(read_gsheet_csv_by_gid(EPM_SHEET_ID, EPM_GID_MES))
    if "año" in epm_raw.columns and "anio" not in epm_raw.columns:
        epm_raw["anio"] = epm_raw["año"]
    for src in ["consumo_kwh", "epm (kwh)", "energia_kwh"]:
        if src in epm_raw.columns and "epm_kwh" not in epm_raw.columns:
            epm_raw["epm_kwh"] = epm_raw[src]
    if "fecha" in epm_raw.columns and ("anio" not in epm_raw.columns or "mes" not in epm_raw.columns):
        fx = pd.to_datetime(epm_raw["fecha"], errors="coerce", dayfirst=True)
        epm_raw["anio"] = fx.dt.year; epm_raw["mes"] = fx.dt.month
    if "planta" in epm_raw.columns:
        epm_raw["planta"] = epm_raw["planta"].astype(str).str.strip().str.upper()
    elif "sede" in epm_raw.columns:
        epm_raw["planta"] = epm_raw["sede"].astype(str).str.strip().str.upper()
    else:
        epm_raw["planta"] = "TOTAL"

    costos_extra = {}
    promedios_hist = {}
    if "tipo" in epm_raw.columns:
        cost_rows = epm_raw[epm_raw["tipo"].astype(str).str.contains("Valor|Costo", case=False, na=False)]
        for _, cr in cost_rows.iterrows():
            pl = str(cr.get("planta","")).strip().upper()
            if pl in ["CAFE","MERCADO"]:
                costos_extra[pl] = safe_float(cr.get("epm_kwh", 0))
        hist_rows = epm_raw[epm_raw["tipo"].astype(str).str.contains("Promedio|Historico", case=False, na=False)]
        for _, hr in hist_rows.iterrows():
            pl = str(hr.get("planta","")).strip().upper()
            if pl in ["CAFE","MERCADO"]:
                promedios_hist[pl] = safe_float(hr.get("epm_kwh", 0))
        epm_raw = epm_raw[epm_raw["tipo"].astype(str).str.contains("Consumo", case=False, na=False)].copy()

    epm_raw["anio"] = pd.to_numeric(epm_raw["anio"], errors="coerce").fillna(0).astype(int)
    epm_raw["mes"]  = pd.to_numeric(epm_raw["mes"], errors="coerce").fillna(0).astype(int)
    epm_raw["epm_kwh"] = pd.to_numeric(epm_raw["epm_kwh"], errors="coerce").fillna(0.0)
    epm = epm_raw[epm_raw["mes"].between(1, 12)].copy()

    # EPM estimado por hora (perfil campana)
    epm_hora_list = []
    perfil_hora = {}
    for h in range(24):
        perfil_hora[h] = max(0, 1 - abs(h - 12) / 7) if 6 <= h <= 18 else 0.15
    total_perfil = sum(perfil_hora.values())
    for h in range(24):
        perfil_hora[h] /= total_perfil
    for _, row in epm.iterrows():
        for h in range(24):
            epm_hora_list.append({
                "anio": row["anio"], "mes": row["mes"], "planta": row["planta"],
                "hora_num": h, "epm_kwh_hora": row["epm_kwh"] * perfil_hora[h]
            })
    epm_hora_df = pd.DataFrame(epm_hora_list) if epm_hora_list else pd.DataFrame(
        columns=["anio","mes","planta","hora_num","epm_kwh_hora"])

    return mensual, diario, horario, epm, epm_hora_df, costos_extra, promedios_hist


# =========================
# HEADER
# =========================
st.markdown("""
<div class="header-wrap">
  <h1>Dashboard Energia Solar - GEDICOL</h1>
  <p>Monitoreo en tiempo real &middot; Plantas CAFE &amp; MERCADO</p>
</div>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
try:
    mensual_df, diario_df, horario_df, epm_mensual_df, epm_hora_df, costos_extra, promedios_hist = cargar_datos_nube()
    if costos_extra:
        for k, v in costos_extra.items():
            if v > 0:
                COSTOS_EPM[k] = v
except Exception as e:
    st.error(
        "No pude leer tus Google Sheets. "
        "Compartir > Cualquier persona con el enlace > Lector.\n\n"
        f"Detalle: {e}"
    )
    st.stop()

diario_df  = diario_df.dropna(subset=["fecha"])
horario_df = horario_df.dropna(subset=["fecha", "hora_num"])

# Disponibles
years_solar = set(mensual_df["anio"].unique().tolist())
years_epm   = set(epm_mensual_df["anio"].unique().tolist())
years_disponibles = sorted(list(years_solar | years_epm))

meses_solar = set(mensual_df["mes"].unique().tolist())
meses_epm   = set(epm_mensual_df["mes"].unique().tolist())
meses_disponibles = sorted(list(meses_solar | meses_epm))

plantas_disponibles = sorted(list(set(mensual_df["planta"].unique().tolist()) | {"CAFE","MERCADO"}))
min_fecha = diario_df["fecha"].min().date() if not diario_df.empty else datetime.today().date()
max_fecha = diario_df["fecha"].max().date() if not diario_df.empty else datetime.today().date()


# ==========================================
# LAYOUT: FILTROS IZQUIERDA + CONTENIDO DERECHA
# ==========================================
col_filt, col_main = st.columns([1.1, 3.2], gap="large")

with col_filt:
    st.markdown('<div class="left-card">', unsafe_allow_html=True)
    st.markdown('<div class="left-title">Filtros</div>', unsafe_allow_html=True)

    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="filter-section">VISTA</div>', unsafe_allow_html=True)
    vista = st.selectbox(
        "Vista",
        ["Mensual (Solar vs EPM)", "Diario (Solar)", "Hora (Solar)"],
        index=0, label_visibility="collapsed",
    )

    st.markdown('<div class="filter-section">PLANTAS</div>', unsafe_allow_html=True)
    selected_plantas = st.multiselect(
        "Plantas", options=plantas_disponibles, default=["CAFE","MERCADO"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="filter-section">AÑOS</div>', unsafe_allow_html=True)
    selected_years = st.multiselect(
        "Años", options=years_disponibles, default=years_disponibles,
        label_visibility="collapsed",
    )

    st.markdown('<div class="filter-section">MESES</div>', unsafe_allow_html=True)
    selected_months = st.multiselect(
        "Meses", options=meses_disponibles, default=meses_disponibles,
        format_func=lambda x: MES_NOMBRES_LARGO.get(x, str(x)),
        label_visibility="collapsed",
    )

    st.markdown('<div class="filter-section">RANGO DIARIO / HORA</div>', unsafe_allow_html=True)
    fecha_range = st.date_input(
        "Rango", value=(min_fecha, max_fecha),
        min_value=min_fecha, max_value=max_fecha,
        label_visibility="collapsed",
    )

    st.markdown('<div class="filter-section">COSTOS kWh</div>', unsafe_allow_html=True)
    costo_cafe_str = f"${COSTOS_EPM['CAFE']:,}/kWh".replace(",",".")
    costo_merc_str = f"${COSTOS_EPM['MERCADO']:,}/kWh".replace(",",".")
    st.markdown(
        f"**CAFE:** {costo_cafe_str}  \n**MERCADO:** {costo_merc_str}",
    )

    if promedios_hist:
        st.markdown('<div class="filter-section">PROM. HISTORICO EPM</div>', unsafe_allow_html=True)
        for pl, val in promedios_hist.items():
            st.markdown(f"**{pl}:** {fmt_num(val,0)} kWh/mes")

    st.markdown(
        f'<div class="small-note">Datos desde Google Sheets.<br>'
        f'Ultima carga: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# Defaults
if not selected_plantas: selected_plantas = ["CAFE","MERCADO"]
if not selected_years: selected_years = years_disponibles
if not selected_months: selected_months = meses_disponibles
if isinstance(fecha_range, tuple) and len(fecha_range) == 2:
    fecha_inicio, fecha_fin = fecha_range
else:
    fecha_inicio, fecha_fin = min_fecha, max_fecha


# =========================
# FILTRADO
# =========================
mensual_filtrado = mensual_df[
    mensual_df["planta"].isin(selected_plantas) &
    mensual_df["anio"].isin(selected_years) &
    mensual_df["mes"].isin(selected_months)
].copy()

diario_filtrado = diario_df[
    diario_df["planta"].isin(selected_plantas) &
    (diario_df["fecha"].dt.date >= fecha_inicio) &
    (diario_df["fecha"].dt.date <= fecha_fin)
].copy()

horario_filtrado = horario_df[
    horario_df["planta"].isin(selected_plantas) &
    (horario_df["fecha"].dt.date >= fecha_inicio) &
    (horario_df["fecha"].dt.date <= fecha_fin)
].copy()

epm_filtrado = epm_mensual_df[
    epm_mensual_df["anio"].isin(selected_years) &
    epm_mensual_df["mes"].isin(selected_months)
].copy()

epm_hora_filtrado = epm_hora_df[
    epm_hora_df["anio"].isin(selected_years) &
    epm_hora_df["mes"].isin(selected_months)
].copy()


# =========================
# KPIs GLOBALES
# =========================
gen_cafe  = mensual_filtrado[mensual_filtrado["planta"]=="CAFE"]["energia_kwh"].sum()
gen_merc  = mensual_filtrado[mensual_filtrado["planta"]=="MERCADO"]["energia_kwh"].sum()
gen_total = gen_cafe + gen_merc

epm_total_kwh = epm_filtrado["epm_kwh"].sum()
epm_cafe_kwh  = epm_filtrado[epm_filtrado["planta"]=="CAFE"]["epm_kwh"].sum()
epm_merc_kwh  = epm_filtrado[epm_filtrado["planta"]=="MERCADO"]["epm_kwh"].sum()

dias_activos = diario_filtrado["fecha"].dt.date.nunique()
prom_diario  = gen_total / dias_activos if dias_activos else 0

ahorro_cafe  = gen_cafe * COSTOS_EPM.get("CAFE", 0)
ahorro_merc  = gen_merc * COSTOS_EPM.get("MERCADO", 0)
ahorro_total = ahorro_cafe + ahorro_merc

cobertura_pct = (gen_total / epm_total_kwh * 100) if epm_total_kwh > 0 else 0
n_meses_solar = mensual_filtrado.groupby(["anio","mes"]).ngroups
prom_mensual  = gen_total / n_meses_solar if n_meses_solar > 0 else 0


# ==========================================
# CONTENIDO DERECHA
# ==========================================
with col_main:

    # ── KPIs ──
    cob_color = "#10b981" if cobertura_pct >= 20 else "#ef4444"
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card total">
        <div class="kpi-label">Solar Total</div>
        <div class="kpi-value" style="color:{COLOR_TOTAL};">{fmt_num(gen_total,1)} kWh</div>
        <div class="kpi-sub">Prom mensual: {fmt_num(prom_mensual,0)} kWh &middot; Prom diario: {fmt_num(prom_diario,1)} kWh</div>
      </div>
      <div class="kpi-card cafe">
        <div class="kpi-label">Solar CAFE</div>
        <div class="kpi-value" style="color:{COLOR_CAFE};">{fmt_num(gen_cafe,1)} kWh</div>
        <div class="kpi-sub">Ahorro: {fmt_currency(ahorro_cafe)}</div>
      </div>
      <div class="kpi-card merc">
        <div class="kpi-label">Solar MERCADO</div>
        <div class="kpi-value" style="color:{COLOR_MERC};">{fmt_num(gen_merc,1)} kWh</div>
        <div class="kpi-sub">Ahorro: {fmt_currency(ahorro_merc)}</div>
      </div>
      <div class="kpi-card ahorro">
        <div class="kpi-label">Ahorro Total</div>
        <div class="kpi-value" style="color:{COLOR_AMBAR};">{fmt_currency(ahorro_total)}</div>
        <div class="kpi-sub">{dias_activos} dias con generacion</div>
      </div>
      <div class="kpi-card cob">
        <div class="kpi-label">Cobertura Solar</div>
        <div class="kpi-value" style="color:{cob_color};">{fmt_num(cobertura_pct,1)}%</div>
        <div class="kpi-sub">EPM consumido: {fmt_num(epm_total_kwh,0)} kWh</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


    # ═══════════════════════════════════════
    # VISTA MENSUAL
    # ═══════════════════════════════════════
    if vista.startswith("Mensual"):
        st.markdown("## Mensual: Solar vs EPM")

        # Preparar datos: Solar pivotado
        sol = mensual_filtrado.groupby(["anio","mes","planta"], as_index=False)["energia_kwh"].sum()
        sol_p = sol.pivot_table(index=["anio","mes"], columns="planta", values="energia_kwh",
                                aggfunc="sum", fill_value=0).reset_index()
        for c in ["CAFE","MERCADO"]:
            if c not in sol_p.columns: sol_p[c] = 0.0
        sol_p["SOLAR_TOTAL"] = sol_p["CAFE"] + sol_p["MERCADO"]

        # EPM pivotado (FILTRAR solo por plantas seleccionadas)
        epm = epm_filtrado.copy()
        if "planta" in epm.columns:
            epm_sel = epm[epm["planta"].isin(selected_plantas)]
        else:
            epm_sel = epm
        if "planta" in epm_sel.columns and epm_sel["planta"].nunique() > 1:
            epm_p = epm_sel.pivot_table(index=["anio","mes"], columns="planta", values="epm_kwh",
                                         aggfunc="sum", fill_value=0).reset_index()
            for c in ["CAFE","MERCADO"]:
                if c not in epm_p.columns: epm_p[c] = 0.0
            epm_p["EPM_TOTAL"] = epm_p["CAFE"] + epm_p["MERCADO"]
            epm_p = epm_p.rename(columns={"CAFE":"EPM_CAFE","MERCADO":"EPM_MERCADO"})
        else:
            epm_sum = epm_sel.groupby(["anio","mes"], as_index=False)["epm_kwh"].sum()
            epm_p = epm_sum.copy()
            epm_p["EPM_CAFE"] = 0.0
            epm_p["EPM_MERCADO"] = 0.0
            epm_p["EPM_TOTAL"] = epm_p["epm_kwh"]
            epm_p = epm_p.drop(columns=["epm_kwh"])

        # MERGE OUTER para tener TODOS los meses (incluyendo EPM sin Solar)
        base = pd.merge(sol_p, epm_p, on=["anio","mes"], how="outer")
        for c in ["CAFE","MERCADO","SOLAR_TOTAL","EPM_CAFE","EPM_MERCADO","EPM_TOTAL"]:
            if c not in base.columns: base[c] = 0.0
            base[c] = base[c].fillna(0.0)
        base = base.sort_values(["anio","mes"]).reset_index(drop=True)
        base["Mes_label"] = base.apply(lambda r: mes_anio_label(r["anio"], r["mes"]), axis=1)
        base["Cobertura"] = base.apply(
            lambda r: (r["SOLAR_TOTAL"]/r["EPM_TOTAL"]*100) if r["EPM_TOTAL"]>0 else 0, axis=1)
        base["Ahorro"] = (base["CAFE"]*COSTOS_EPM["CAFE"]) + (base["MERCADO"]*COSTOS_EPM["MERCADO"])

        # ── GRAFICO PRINCIPAL ──
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Generacion Solar vs Consumo EPM</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-sub">Barras solidas: Solar | Barras rayadas: EPM (agrupadas) | '
            'Linea: % cobertura | Punteadas: promedios</div>',
            unsafe_allow_html=True,
        )

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(go.Bar(
            name="Solar CAFE", x=base["Mes_label"], y=base["CAFE"],
            marker_color=COLOR_CAFE, opacity=0.95,
            offsetgroup="solar",
            text=base["CAFE"].apply(lambda v: fmt_num(v,0) if v > 0 else ""),
            textposition="inside", textfont=dict(size=10, color="white"),
        ))
        fig.add_trace(go.Bar(
            name="Solar MERCADO", x=base["Mes_label"], y=base["MERCADO"],
            marker_color=COLOR_MERC, opacity=0.95,
            offsetgroup="solar",
            text=base["MERCADO"].apply(lambda v: fmt_num(v,0) if v > 0 else ""),
            textposition="inside", textfont=dict(size=10, color="white"),
        ))
        fig.add_trace(go.Bar(
            name="EPM CAFE", x=base["Mes_label"], y=base["EPM_CAFE"],
            marker_color=COLOR_CAFE, marker_line=dict(width=1.5, color=COLOR_CAFE),
            marker_pattern_shape="/", opacity=0.45,
            offsetgroup="epm",
            text=base["EPM_CAFE"].apply(lambda v: fmt_num(v,0) if v > 0 else ""),
            textposition="inside", textfont=dict(size=9, color="#0f172a"),
        ))
        fig.add_trace(go.Bar(
            name="EPM MERCADO", x=base["Mes_label"], y=base["EPM_MERCADO"],
            marker_color=COLOR_MERC, marker_line=dict(width=1.5, color=COLOR_MERC),
            marker_pattern_shape="/", opacity=0.45,
            offsetgroup="epm",
            text=base["EPM_MERCADO"].apply(lambda v: fmt_num(v,0) if v > 0 else ""),
            textposition="inside", textfont=dict(size=9, color="#0f172a"),
        ))
        fig.add_trace(go.Scatter(
            name="% Cobertura", x=base["Mes_label"], y=base["Cobertura"],
            mode="lines+markers+text",
            line=dict(color=COLOR_AMBAR, width=3),
            marker=dict(size=10, color=COLOR_AMBAR, line=dict(width=2, color="white")),
            text=base["Cobertura"].apply(lambda v: f"{v:.0f}%"),
            textposition="top center", textfont=dict(size=11, color=COLOR_AMBAR),
        ), secondary_y=True)

        # Promedios (solo meses CON datos solares para promedio solar)
        meses_con_solar = base[base["SOLAR_TOTAL"] > 0]
        avg_solar = safe_float(meses_con_solar["SOLAR_TOTAL"].mean()) if not meses_con_solar.empty else 0
        avg_epm = safe_float(base[base["EPM_TOTAL"] > 0]["EPM_TOTAL"].mean())

        if avg_solar > 0:
            fig.add_hline(y=avg_solar, line_dash="dot", line_color=COLOR_TOTAL, line_width=2,
                annotation_text=f"Prom Solar: {fmt_num(avg_solar,0)} kWh",
                annotation_position="top left",
                annotation_font=dict(size=11, color=COLOR_TOTAL))
        if avg_epm > 0:
            fig.add_hline(y=avg_epm, line_dash="dot", line_color="#ef4444", line_width=1.5,
                annotation_text=f"Prom EPM: {fmt_num(avg_epm,0)} kWh",
                annotation_position="bottom left",
                annotation_font=dict(size=11, color="#ef4444"))

        max_cob = base["Cobertura"].max()
        fig.update_layout(
            barmode="stack", bargroupgap=0.15, bargap=0.3,
            yaxis_title="Energia (kWh)",
            yaxis2_title="Cobertura (%)",
            yaxis2=dict(range=[0, max(max_cob * 1.3, 100) if max_cob > 0 else 100], showgrid=False),
        )
        fig = apply_light(fig, h=500)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── FILA: Tortas + Gauge + Ahorro ──
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown('<div class="panel"><div class="panel-title">Solar por Planta</div>', unsafe_allow_html=True)
            fig_ps = go.Figure(go.Pie(
                labels=["CAFE","MERCADO"], values=[safe_float(gen_cafe), safe_float(gen_merc)],
                hole=0.55, marker=dict(colors=[COLOR_CAFE, COLOR_MERC], line=dict(color="white", width=3)),
                textinfo="label+percent", textfont=dict(size=11, color="#0f172a"),
            ))
            fig_ps.add_annotation(
                text=f"<b>{fmt_num(gen_total,0)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#0f172a"))
            fig_ps.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                height=250, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig_ps, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="panel"><div class="panel-title">EPM por Planta</div>', unsafe_allow_html=True)
            fig_pe = go.Figure(go.Pie(
                labels=["CAFE","MERCADO"], values=[safe_float(epm_cafe_kwh), safe_float(epm_merc_kwh)],
                hole=0.55, marker=dict(colors=[COLOR_CAFE, COLOR_MERC], line=dict(color="white", width=3)),
                textinfo="label+percent", textfont=dict(size=11, color="#0f172a"),
            ))
            fig_pe.add_annotation(
                text=f"<b>{fmt_num(epm_total_kwh,0)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#0f172a"))
            fig_pe.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                height=250, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig_pe, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="panel"><div class="panel-title">Cobertura Solar</div>', unsafe_allow_html=True)
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=cobertura_pct,
                number=dict(suffix="%", font=dict(size=36, color="#0f172a")),
                gauge=dict(
                    axis=dict(range=[0,100], tickfont=dict(size=10)),
                    bar=dict(color=COLOR_MERC, thickness=0.3),
                    bgcolor="#f1f5f9", borderwidth=1, bordercolor="#e2e8f0",
                    steps=[
                        dict(range=[0,20], color="#fef2f2"),
                        dict(range=[20,50], color="#fffbeb"),
                        dict(range=[50,100], color="#ecfdf5"),
                    ],
                    threshold=dict(line=dict(color=COLOR_AMBAR, width=3), thickness=0.8, value=cobertura_pct),
                ),
            ))
            fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=250, margin=dict(l=30,r=30,t=30,b=10))
            st.plotly_chart(fig_g, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c4:
            st.markdown('<div class="panel"><div class="panel-title">Ahorro por Mes</div>', unsafe_allow_html=True)
            fig_a = go.Figure(go.Bar(
                x=base["Mes_label"], y=base["Ahorro"], marker_color=COLOR_AMBAR,
                text=base["Ahorro"].apply(lambda v: fmt_currency(v) if v > 0 else ""),
                textposition="outside", textfont=dict(size=9, color=COLOR_AMBAR),
            ))
            meses_con_ahorro = base[base["Ahorro"] > 0]
            avg_ah = safe_float(meses_con_ahorro["Ahorro"].mean()) if not meses_con_ahorro.empty else 0
            if avg_ah > 0:
                fig_a.add_hline(y=avg_ah, line_dash="dot", line_color=COLOR_TOTAL, line_width=2,
                    annotation_text=f"Prom: {fmt_currency(avg_ah)}",
                    annotation_font=dict(size=10, color=COLOR_TOTAL))
            fig_a.update_layout(showlegend=False, yaxis_title="$COP")
            fig_a = apply_light(fig_a, h=250)
            st.plotly_chart(fig_a, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Tendencia linea ──
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Tendencia Mensual - Solar vs EPM</div>', unsafe_allow_html=True)
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(
            name="EPM Total", x=base["Mes_label"], y=base["EPM_TOTAL"],
            mode="lines+markers",
            line=dict(color="#ef4444", width=2.5),
            marker=dict(size=8, color="#ef4444", line=dict(width=2, color="white")),
            fill="tozeroy", fillcolor="rgba(239,68,68,0.06)",
        ))
        fig_t.add_trace(go.Scatter(
            name="Solar Total", x=base["Mes_label"], y=base["SOLAR_TOTAL"],
            mode="lines+markers",
            line=dict(color=COLOR_TOTAL, width=3),
            marker=dict(size=9, color=COLOR_TOTAL, line=dict(width=2, color="white")),
            fill="tozeroy", fillcolor="rgba(139,92,246,0.08)",
        ))
        fig_t.update_layout(yaxis_title="Energia (kWh)")
        fig_t = apply_light(fig_t, h=350)
        st.plotly_chart(fig_t, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── TABLA RESUMEN MENSUAL ──
        st.markdown('<div class="panel"><div class="panel-title">Tabla Resumen Mensual</div>', unsafe_allow_html=True)
        resumen = pd.DataFrame({
            "Mes": base["Mes_label"],
            "Solar CAFE (kWh)": base["CAFE"].round(1),
            "Solar MERCADO (kWh)": base["MERCADO"].round(1),
            "Solar TOTAL (kWh)": base["SOLAR_TOTAL"].round(1),
            "EPM CAFE (kWh)": base["EPM_CAFE"].round(0).astype(int),
            "EPM MERCADO (kWh)": base["EPM_MERCADO"].round(0).astype(int),
            "EPM TOTAL (kWh)": base["EPM_TOTAL"].round(0).astype(int),
            "Cobertura": base["Cobertura"].round(1).astype(str) + "%",
            "Ahorro ($)": base["Ahorro"].apply(fmt_currency),
        })
        st.dataframe(resumen, use_container_width=True, hide_index=True)
        st.markdown(f"""
        <div class="stat-grid">
          <div class="stat-card"><div class="stat-label">Total Solar</div>
            <div class="stat-value" style="color:{COLOR_TOTAL};">{fmt_num(gen_total,0)}</div>
            <div class="stat-extra">kWh</div></div>
          <div class="stat-card"><div class="stat-label">Total EPM</div>
            <div class="stat-value" style="color:#ef4444;">{fmt_num(epm_total_kwh,0)}</div>
            <div class="stat-extra">kWh</div></div>
          <div class="stat-card"><div class="stat-label">Ahorro Total</div>
            <div class="stat-value" style="color:{COLOR_AMBAR};">{fmt_currency(ahorro_total)}</div>
            <div class="stat-extra">COP</div></div>
          <div class="stat-card"><div class="stat-label">Cobertura</div>
            <div class="stat-value" style="color:{COLOR_MERC};">{fmt_num(cobertura_pct,1)}%</div>
            <div class="stat-extra">promedio general</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


    # ═══════════════════════════════════════
    # VISTA DIARIO
    # ═══════════════════════════════════════
    elif vista.startswith("Diario"):
        st.markdown("## Diario: Generacion Solar")

        if diario_filtrado.empty:
            st.warning("No hay datos diarios con los filtros seleccionados.")
        else:
            daily_all = diario_filtrado.groupby(["fecha","planta"], as_index=False)["energia_kwh"].sum()
            daily_total = diario_filtrado.groupby("fecha", as_index=False)["energia_kwh"].sum()
            # Promedio: solo dias con generacion > 0
            dias_con_gen = daily_total[daily_total["energia_kwh"] > 0]
            avg_dia = safe_float(dias_con_gen["energia_kwh"].mean()) if not dias_con_gen.empty else 0

            # ── GRAFICO PRINCIPAL ──
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Evolucion Diaria de Generacion Solar</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-sub">Linea continua por planta | Linea punteada: promedio general (dias con generacion)</div>',
                unsafe_allow_html=True,
            )
            fig_d = go.Figure()
            for planta in selected_plantas:
                d = daily_all[daily_all["planta"]==planta].sort_values("fecha")
                if d.empty: continue
                color = COLOR_CAFE if planta == "CAFE" else COLOR_MERC
                d_labels = d["fecha"].apply(fecha_label_dia)
                fig_d.add_trace(go.Scatter(
                    name=planta, x=d["fecha"], y=d["energia_kwh"],
                    mode="lines+markers",
                    line=dict(color=color, width=2),
                    marker=dict(size=4, color=color),
                    fill="tozeroy",
                    fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
                    customdata=d_labels,
                    hovertemplate="<b>%{customdata}</b><br>%{y:.1f} kWh<extra></extra>",
                ))
            if avg_dia > 0:
                fig_d.add_hline(
                    y=avg_dia, line_dash="dot", line_color=COLOR_TOTAL, line_width=2,
                    annotation_text=f"Prom: {fmt_num(avg_dia,1)} kWh/dia",
                    annotation_font=dict(size=11, color=COLOR_TOTAL),
                )
            fig_d.update_layout(yaxis_title="Energia (kWh)", xaxis_title="Fecha")
            fig_d = apply_light(fig_d, h=460)
            st.plotly_chart(fig_d, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── FILA: Stats + Torta + Dia de semana ──
            c1, c2, c3 = st.columns([1, 1, 1.5])

            max_d = daily_total.loc[daily_total["energia_kwh"].idxmax()] if not daily_total.empty else None
            std_d = safe_float(dias_con_gen["energia_kwh"].std()) if not dias_con_gen.empty else 0

            with c1:
                best_val = fmt_num(max_d["energia_kwh"], 0) if max_d is not None else "—"
                best_date = fecha_label_dia(max_d["fecha"]) if max_d is not None else ""
                st.markdown(f"""
                <div class="panel"><div class="panel-title">Estadisticas Diarias</div>
                  <div class="stat-grid" style="flex-direction:column;">
                    <div class="stat-card">
                      <div class="stat-label">Promedio Diario</div>
                      <div class="stat-value" style="color:{COLOR_TOTAL};font-size:22px;">{fmt_num(avg_dia,1)} kWh</div>
                      <div class="stat-extra">dias con generacion: {len(dias_con_gen)}</div>
                    </div>
                    <div class="stat-card">
                      <div class="stat-label">Mejor Dia</div>
                      <div class="stat-value" style="color:{COLOR_MERC};font-size:22px;">{best_val} kWh</div>
                      <div class="stat-extra">{best_date}</div>
                    </div>
                    <div class="stat-card">
                      <div class="stat-label">Desviacion Estandar</div>
                      <div class="stat-value" style="color:{COLOR_AMBAR};font-size:22px;">{fmt_num(std_d,1)} kWh</div>
                      <div class="stat-extra">variabilidad diaria</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="panel"><div class="panel-title">Distribucion por Planta</div>', unsafe_allow_html=True)
                dcafe = daily_all[daily_all["planta"]=="CAFE"]["energia_kwh"].sum()
                dmerc = daily_all[daily_all["planta"]=="MERCADO"]["energia_kwh"].sum()
                fig_pd = go.Figure(go.Pie(
                    labels=["CAFE","MERCADO"], values=[safe_float(dcafe), safe_float(dmerc)],
                    hole=0.55, marker=dict(colors=[COLOR_CAFE, COLOR_MERC], line=dict(color="white", width=3)),
                    textinfo="label+percent", textfont=dict(size=11),
                ))
                fig_pd.add_annotation(
                    text=f"<b>{fmt_num(dcafe+dmerc,0)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                    x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#0f172a"))
                fig_pd.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                    height=300, margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_pd, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c3:
                st.markdown('<div class="panel"><div class="panel-title">Promedio por Dia de la Semana</div>', unsafe_allow_html=True)
                dow = diario_filtrado.copy()
                dow["dow"] = dow["fecha"].dt.dayofweek
                dow_names = ["Lun","Mar","Mie","Jue","Vie","Sab","Dom"]
                dow_agg = dow.groupby(["dow","planta"], as_index=False)["energia_kwh"].mean()
                fig_dw = go.Figure()
                for planta in selected_plantas:
                    d = dow_agg[dow_agg["planta"]==planta].sort_values("dow")
                    if d.empty: continue
                    color = COLOR_CAFE if planta == "CAFE" else COLOR_MERC
                    fig_dw.add_trace(go.Bar(
                        name=planta, x=[dow_names[int(i)] for i in d["dow"]],
                        y=d["energia_kwh"], marker_color=color,
                        text=d["energia_kwh"].apply(lambda v: fmt_num(v,1)),
                        textposition="outside", textfont=dict(size=9),
                    ))
                fig_dw.update_layout(barmode="group", yaxis_title="Prom kWh/dia")
                fig_dw = apply_light(fig_dw, h=300)
                st.plotly_chart(fig_dw, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ── TABLA RESUMEN DIARIO ──
            st.markdown('<div class="panel"><div class="panel-title">Tabla Resumen Diario</div>', unsafe_allow_html=True)
            piv = daily_all.pivot_table(index="fecha", columns="planta", values="energia_kwh", fill_value=0).reset_index()
            for c in ["CAFE","MERCADO"]:
                if c not in piv.columns: piv[c] = 0.0
            piv["TOTAL"] = piv["CAFE"] + piv["MERCADO"]
            piv = piv.sort_values("fecha")
            piv["Fecha"] = piv["fecha"].apply(fecha_label_dia)
            piv["Ahorro ($)"] = (piv["CAFE"]*COSTOS_EPM["CAFE"] + piv["MERCADO"]*COSTOS_EPM["MERCADO"]).apply(fmt_currency)
            out = piv[["Fecha","CAFE","MERCADO","TOTAL","Ahorro ($)"]].rename(columns={
                "CAFE":"Solar CAFE (kWh)", "MERCADO":"Solar MERCADO (kWh)", "TOTAL":"Solar TOTAL (kWh)"
            }).round(1)
            st.dataframe(out, use_container_width=True, hide_index=True, height=400)
            st.markdown('</div>', unsafe_allow_html=True)


    # ═══════════════════════════════════════
    # VISTA HORA
    # ═══════════════════════════════════════
    else:
        st.markdown("## Hora: Generacion Solar (promedio por hora)")

        if horario_filtrado.empty:
            st.warning("No hay datos por hora con los filtros seleccionados.")
        else:
            hp = horario_filtrado.groupby(["hora_num","planta"], as_index=False)["energia_kwh"].mean()
            hp["hora_num"] = hp["hora_num"].astype(int)

            epm_h_agg = pd.DataFrame(columns=["hora_num","planta","epm_kwh_hora"])
            if not epm_hora_filtrado.empty:
                epm_h_agg = epm_hora_filtrado.groupby(["hora_num","planta"], as_index=False)["epm_kwh_hora"].mean()
                epm_h_agg["hora_num"] = epm_h_agg["hora_num"].astype(int)

            # ── GRAFICO PRINCIPAL ──
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Patron de Generacion por Hora - Solar vs EPM (estimado)</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-sub">Curva solar promedio | EPM estimado por distribucion horaria | Zona solar: 6h-18h</div>',
                unsafe_allow_html=True,
            )
            fig_h = go.Figure()

            # EPM estimado
            if not epm_h_agg.empty:
                for planta in selected_plantas:
                    de = epm_h_agg[epm_h_agg["planta"]==planta].sort_values("hora_num")
                    if de.empty: continue
                    color = COLOR_CAFE if planta == "CAFE" else COLOR_MERC
                    fig_h.add_trace(go.Scatter(
                        name=f"EPM {planta} (est.)", x=de["hora_num"], y=de["epm_kwh_hora"],
                        mode="lines", line=dict(color=color, width=1.5, dash="dot"), opacity=0.35,
                        fill="tozeroy",
                        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.04)",
                    ))

            # Solar por hora
            for planta in selected_plantas:
                d = hp[hp["planta"]==planta].sort_values("hora_num")
                if d.empty: continue
                color = COLOR_CAFE if planta == "CAFE" else COLOR_MERC
                fig_h.add_trace(go.Scatter(
                    name=f"Solar {planta}", x=d["hora_num"], y=d["energia_kwh"],
                    mode="lines+markers+text",
                    line=dict(color=color, width=3, shape="spline"),
                    marker=dict(size=8, color=color, line=dict(width=2, color="white")),
                    fill="tozeroy",
                    fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)",
                    text=d["energia_kwh"].apply(lambda v: f"{v:.1f}" if v > 0.5 else ""),
                    textposition="top center", textfont=dict(size=9, color="#0f172a"),
                ))

            fig_h.add_vrect(
                x0=6, x1=18, fillcolor="rgba(245,158,11,0.04)", line_width=0,
                annotation_text="Horas solares", annotation_position="top left",
                annotation_font=dict(size=10, color=COLOR_AMBAR),
            )

            # Promedio horario (solo horas con generacion > 0)
            hp_con_gen = hp[hp["energia_kwh"] > 0]
            avg_hora = safe_float(hp_con_gen["energia_kwh"].mean()) if not hp_con_gen.empty else 0
            if avg_hora > 0:
                fig_h.add_hline(
                    y=avg_hora, line_dash="dot", line_color=COLOR_TOTAL, line_width=2,
                    annotation_text=f"Prom Solar: {avg_hora:.2f} kWh/h",
                    annotation_font=dict(size=11, color=COLOR_TOTAL),
                )

            fig_h.update_layout(
                xaxis=dict(
                    tickmode="array", tickvals=list(range(0,24)),
                    ticktext=[f"{h}:00" for h in range(0,24)],
                    title="Hora del dia",
                ),
                yaxis_title="kWh promedio",
            )
            fig_h = apply_light(fig_h, h=460)
            st.plotly_chart(fig_h, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── FILA: Stats + Torta + Heatmap ──
            c1, c2 = st.columns([1, 1.5])

            total_hp = hp.groupby("hora_num")["energia_kwh"].sum()
            peak_h = int(total_hp.idxmax()) if not total_hp.empty else 0
            peak_v = safe_float(total_hp.max())
            productive = hp[hp["energia_kwh"] > 0.5]["hora_num"].nunique()

            with c1:
                st.markdown(f"""
                <div class="panel"><div class="panel-title">Estadisticas Horarias</div>
                  <div class="stat-grid" style="flex-direction:column;">
                    <div class="stat-card">
                      <div class="stat-label">Hora Pico</div>
                      <div class="stat-value" style="color:{COLOR_AMBAR};font-size:26px;">{peak_h}:00</div>
                      <div class="stat-extra">{fmt_num(peak_v,1)} kWh promedio total</div>
                    </div>
                    <div class="stat-card">
                      <div class="stat-label">Horas Productivas</div>
                      <div class="stat-value" style="color:{COLOR_MERC};font-size:26px;">{productive}</div>
                      <div class="stat-extra">horas con mas de 0.5 kWh</div>
                    </div>
                    <div class="stat-card">
                      <div class="stat-label">Promedio por Hora</div>
                      <div class="stat-value" style="color:{COLOR_CAFE};font-size:26px;">{fmt_num(avg_hora,2)}</div>
                      <div class="stat-extra">kWh/hora (horas productivas)</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Torta pico vs no-pico
                st.markdown('<div class="panel"><div class="panel-title">Generacion Pico vs No-Pico</div>', unsafe_allow_html=True)
                hp_total = hp.groupby("hora_num")["energia_kwh"].sum().reset_index()
                pico_kwh = safe_float(hp_total[(hp_total["hora_num"]>=9) & (hp_total["hora_num"]<=15)]["energia_kwh"].sum())
                no_pico = safe_float(hp_total[~((hp_total["hora_num"]>=9) & (hp_total["hora_num"]<=15))]["energia_kwh"].sum())
                fig_pp = go.Figure(go.Pie(
                    labels=["Pico (9-15h)","Fuera de pico"],
                    values=[pico_kwh, no_pico],
                    hole=0.55,
                    marker=dict(colors=[COLOR_AMBAR, "#e2e8f0"], line=dict(color="white", width=3)),
                    textinfo="label+percent", textfont=dict(size=11),
                ))
                fig_pp.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                    height=220, margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_pp, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c2:
                # Heatmap
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">Heatmap: Generacion por Hora y Fecha</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-sub">Intensidad de generacion solar a lo largo del tiempo</div>', unsafe_allow_html=True)
                hm = horario_filtrado.groupby(["fecha","hora_num"], as_index=False)["energia_kwh"].sum()
                hm["fecha_str"] = hm["fecha"].apply(fecha_label_dia)
                hm_pivot = hm.pivot_table(index="hora_num", columns="fecha_str", values="energia_kwh", fill_value=0).sort_index()
                if hm_pivot.shape[1] > 45:
                    hm_pivot = hm_pivot.iloc[:, -45:]
                fig_hm = go.Figure(go.Heatmap(
                    z=hm_pivot.values,
                    x=hm_pivot.columns.tolist(),
                    y=[f"{int(h)}:00" for h in hm_pivot.index],
                    colorscale=[
                        [0, "#f8fafc"], [0.15, "#dbeafe"],
                        [0.4, COLOR_CAFE], [0.7, COLOR_MERC], [1.0, COLOR_AMBAR],
                    ],
                    hovertemplate="Fecha: %{x}<br>Hora: %{y}<br>kWh: %{z:.1f}<extra></extra>",
                    colorbar=dict(
                        title=dict(text="kWh", font=dict(size=11)),
                        tickfont=dict(size=10),
                    ),
                ))
                fig_hm.update_layout(
                    xaxis_title="Fecha", yaxis_title="Hora",
                    yaxis=dict(autorange="reversed"),
                )
                fig_hm = apply_light(fig_hm, h=460)
                st.plotly_chart(fig_hm, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ── TABLA POR HORA ──
            st.markdown('<div class="panel"><div class="panel-title">Tabla Resumen por Hora (Solar + EPM estimado)</div>', unsafe_allow_html=True)
            piv_h = hp.pivot_table(index="hora_num", columns="planta", values="energia_kwh", fill_value=0).reset_index()
            for c in ["CAFE","MERCADO"]:
                if c not in piv_h.columns: piv_h[c] = 0.0
            piv_h["TOTAL"] = piv_h["CAFE"] + piv_h["MERCADO"]

            if not epm_h_agg.empty:
                epm_h_piv = epm_h_agg.pivot_table(index="hora_num", columns="planta", values="epm_kwh_hora", fill_value=0).reset_index()
                epm_h_piv = epm_h_piv.rename(columns={"CAFE":"EPM_CAFE","MERCADO":"EPM_MERCADO"})
                for c in ["EPM_CAFE","EPM_MERCADO"]:
                    if c not in epm_h_piv.columns: epm_h_piv[c] = 0.0
                epm_h_piv["EPM_TOTAL"] = epm_h_piv.get("EPM_CAFE", 0) + epm_h_piv.get("EPM_MERCADO", 0)
                piv_h = pd.merge(piv_h, epm_h_piv[["hora_num","EPM_CAFE","EPM_MERCADO","EPM_TOTAL"]],
                                  on="hora_num", how="left")
                for c in ["EPM_CAFE","EPM_MERCADO","EPM_TOTAL"]:
                    piv_h[c] = piv_h[c].fillna(0.0)

            piv_h = piv_h.sort_values("hora_num")
            piv_h["Hora"] = piv_h["hora_num"].apply(lambda h: f"{int(h):02d}:00")

            cols_out = ["Hora","CAFE","MERCADO","TOTAL"]
            ren = {"CAFE":"Solar CAFE (kWh)", "MERCADO":"Solar MERCADO (kWh)", "TOTAL":"Solar TOTAL (kWh)"}
            if "EPM_TOTAL" in piv_h.columns:
                cols_out += ["EPM_CAFE","EPM_MERCADO","EPM_TOTAL"]
                ren.update({"EPM_CAFE":"EPM CAFE (est.)", "EPM_MERCADO":"EPM MERC (est.)", "EPM_TOTAL":"EPM TOTAL (est.)"})

            out_h = piv_h[cols_out].rename(columns=ren).round(2)
            st.dataframe(out_h, use_container_width=True, hide_index=True, height=500)
            st.markdown('</div>', unsafe_allow_html=True)


# =========================
# FOOTER
# =========================
st.markdown(f"""
<div class="dash-footer">
    Dashboard Energia Solar - GEDICOL | &copy; {datetime.now().year} |
    Datos: Google Sheets en tiempo real |
    <span style="color:{COLOR_CAFE};">&#9632;</span> CAFE
    <span style="color:{COLOR_MERC};">&#9632;</span> MERCADO
    <span style="color:{COLOR_TOTAL};">&#9632;</span> Total
    <span style="color:{COLOR_AMBAR};">&#9632;</span> Ahorro
</div>
""", unsafe_allow_html=True)