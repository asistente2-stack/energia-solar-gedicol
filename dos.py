# -*- coding: utf-8 -*-
import re, os, traceback
from io import StringIO, BytesIO
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# ======================
# CONFIG
# ======================
SOLAR_SHEET_ID = "1ceFwwFm6D1QRW4slPj67BlSDR9woGFFaOMLoN1FxVvs"
SOLAR_TAB_MES  = "POR MES"
SOLAR_TAB_DIA  = "POR DIA"
SOLAR_TAB_HORA = "POR HORA"

EPM_SHEET_ID   = "1ANEtNlryqo_4wq1n6V5OlutpcDFMP_EdxxWXgjEhQ3c"
EPM_GID_MES    = "2089036315"

# costos base por kWh
COSTOS_EPM = {"CAFE": 1033, "MERCADO": 1077}

# paleta mejorada - EPM más visible
COLOR_CAFE       = "#3b82f6"  # azul
COLOR_MERC       = "#10b981"  # verde
COLOR_TOTAL      = "#8b5cf6"  # morado
COLOR_AMBAR      = "#f59e0b"  # dorado
COLOR_EPM_CAFE   = "#1e40af"  # azul oscuro (EPM)
COLOR_EPM_MERC   = "#047857"  # verde oscuro (EPM)
BG = "#f8fafc"

ML = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

st.set_page_config(
    page_title="Energía solar - Café y Mercado · Monte Sereno",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================
# CSS
# ======================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif!important}}
.block-container{{padding-top:.6rem;padding-bottom:2rem;background:{BG}}}
#MainMenu,.stDeployButton{{visibility:hidden}}
footer{{visibility:hidden}}
header{{visibility:hidden}}
.main{{background:{BG}}}

.left-card{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:16px;box-shadow:0 4px 14px rgba(0,0,0,.06)}}
.left-title{{font-size:15px;font-weight:900;margin:0 0 10px;color:#0f172a}}
.fsec{{font-size:11px;font-weight:800;color:{COLOR_CAFE};text-transform:uppercase;letter-spacing:1.5px;padding:10px 0 4px;margin-top:8px;border-top:1px solid #e2e8f0}}
.small-note{{font-size:10px;color:#94a3b8;font-weight:500;line-height:1.3;background:#f1f5f9;border-radius:8px;padding:8px;margin-top:6px}}

.kpi-row{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}}
.kpi-card{{flex:1;min-width:160px;background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px 16px;box-shadow:0 4px 14px rgba(0,0,0,.05);border-left:5px solid {COLOR_TOTAL};transition:transform .2s,box-shadow .2s}}
.kpi-card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.1)}}
.kpi-card.c1{{border-left-color:{COLOR_CAFE}}}
.kpi-card.c2{{border-left-color:{COLOR_MERC}}}
.kpi-card.c3{{border-left-color:{COLOR_TOTAL}}}
.kpi-card.c4{{border-left-color:{COLOR_AMBAR}}}
.kpi-card.c5{{border-left-color:#ef4444}}
.kpi-card.c6{{border-left-color:{COLOR_EPM_CAFE}}}
.kpi-card.c7{{border-left-color:{COLOR_EPM_MERC}}}
.kl{{font-size:10px;font-weight:900;color:#64748b;text-transform:uppercase;letter-spacing:1px}}
.kv{{font-size:22px;font-weight:900;margin-top:4px;line-height:1}}
.ks{{font-size:11px;color:#64748b;font-weight:600;margin-top:6px}}

.panel{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:18px;box-shadow:0 4px 14px rgba(0,0,0,.06);margin-bottom:14px}}
.pt{{font-size:15px;font-weight:900;color:#0f172a;margin:0 0 2px}}
.ps{{font-size:11px;color:#64748b;font-weight:600;margin:0 0 10px}}

.dash-footer{{text-align:center;color:#94a3b8;font-size:11px;padding:14px;background:#fff;border:1px solid #e2e8f0;border-radius:12px;margin-top:16px}}
div[data-baseweb="select"]>div{{border-radius:10px!important}}
.epm-ok{{background:#dcfce7;border:1px solid #86efac;border-radius:8px;padding:6px 10px;font-size:11px;font-weight:700;color:#166534;margin-top:4px}}
</style>
""", unsafe_allow_html=True)

# ======================
# HELPERS
# ======================
PLT = dict(
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(255,255,255,0)",
    font=dict(family="Inter,sans-serif", color="#0f172a", size=12),
    margin=dict(l=50, r=30, t=50, b=50),
    legend=dict(bgcolor="rgba(255,255,255,.95)", bordercolor="#e2e8f0", borderwidth=1, font=dict(size=11))
)

def aplyt(fig, h=420):
    fig.update_layout(**PLT, height=h)
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    return fig

def sf(x):
    try:
        v = float(x)
        return 0.0 if np.isnan(v) or np.isinf(v) else v
    except:
        return 0.0

def fn(x, d=0):
    s = f"{sf(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.split(",")[0] if d == 0 else s

def fc(x, decimals=0):
    """Formato moneda COP con decimales opcionales"""
    if decimals > 0:
        s = f"{sf(x):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${s}"
    return f"${sf(x):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def mlbl(y, m):
    return f"{ML.get(int(m), str(m))} {int(y)}"

def dlbl(dt):
    return f"{dt.day} {ML.get(dt.month, str(dt.month))} {dt.year}"

def tis(val):
    try:
        if pd.isna(val): return 0
        if isinstance(val, (int, np.integer)): return int(val)
        if isinstance(val, (float, np.floating)):
            if np.isnan(val) or np.isinf(val): return 0
            return int(val)
        s = str(val).strip()
        if s == "": return 0
        return int(float(s))
    except:
        return 0

def parse_h(x):
    if pd.isna(x): return np.nan
    m = re.match(r"(\d+)", str(x).strip())
    return int(m.group(1)) if m else np.nan

def parse_mes_any(x):
    if pd.isna(x): return 0
    if isinstance(x, (int, np.integer)):
        m = int(x)
        return m if 1 <= m <= 12 else 0
    if isinstance(x, (float, np.floating)):
        if np.isnan(x) or np.isinf(x): return 0
        m = int(x)
        return m if 1 <= m <= 12 else 0
    s = str(x).strip().lower()
    if s.startswith("ene"): return 1
    if s.startswith("feb"): return 2
    if s.startswith("mar"): return 3
    if s.startswith("abr"): return 4
    if s.startswith("may"): return 5
    if s.startswith("jun"): return 6
    if s.startswith("jul"): return 7
    if s.startswith("ago"): return 8
    if s.startswith("sep"): return 9
    if s.startswith("oct"): return 10
    if s.startswith("nov"): return 11
    if s.startswith("dic"): return 12
    m = re.match(r"^\s*(\d{1,2})(?:\.0+)?\s*$", s)
    if m:
        mm = int(m.group(1))
        return mm if 1 <= mm <= 12 else 0
    return 0

def to_num_auto(v):
    """
    Convierte cualquier representación de número a float.
    Detecta correctamente separadores de miles vs decimales:
      "5,444"   → 5444   (coma = miles, Google Sheets format)
      "5.6"     → 5.6    (punto = decimal)
      "1,234.56"→ 1234.56 (anglosajón)
      "1.234,56"→ 1234.56 (europeo)
      "1,234,567"→ 1234567 (múltiples comas = miles)
    """
    try:
        if v is None: return 0.0
        if isinstance(v, (int, np.integer)): return float(v)
        if isinstance(v, (float, np.floating)):
            return 0.0 if (np.isnan(v) or np.isinf(v)) else float(v)
        s = str(v).strip()
        if s == "" or s.lower() in ["nan", "none", "null", "-"]: return 0.0
        # Quitar símbolos de moneda y espacios
        s = s.replace(" ", "").replace("$", "").replace("€", "").replace("£", "")
        has_comma = "," in s
        has_dot   = "." in s
        if has_comma and has_dot:
            # El último separador es el decimal
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")   # "1.234,56" → "1234.56"
            else:
                s = s.replace(",", "")                      # "1,234.56" → "1234.56"
        elif has_comma and not has_dot:
            parts = s.split(",")
            # N,NNN  → exactamente 3 dígitos tras la coma = separador de miles
            if len(parts) == 2 and re.fullmatch(r"\d{1,3}", parts[0]) and re.fullmatch(r"\d{3}", parts[1]):
                s = s.replace(",", "")   # "5,444" → "5444"
            elif len(parts) > 2:
                s = s.replace(",", "")   # "1,234,567" → "1234567"
            else:
                s = s.replace(",", ".")  # "5,6" → "5.6" decimal europeo
        # Solo punto: lo dejamos como está (decimal estándar)
        s = re.sub(r"[^0-9\.\-]", "", s)
        if s in ["", "-", ".", "-."]: return 0.0
        return float(s)
    except:
        return 0.0

def norm_planta(p):
    s = str(p or "").strip().upper()
    s = s.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
    s = re.sub(r"\s+", " ", s)
    if s in ["CAFE","CAFÉ","MONTESERENO CAFE","MONTESERENO CAFÉ","MONTE SERENO CAFE","MONTE SERENO CAFÉ"]:
        return "CAFE"
    if s in ["MERCADO","MONTESERENO MERCADO","MONTE SERENO MERCADO"]:
        return "MERCADO"
    if "CAFE" in s: return "CAFE"
    if "MERCADO" in s: return "MERCADO"
    return s if s else "TOTAL"

def st_btn(label):
    try:
        return st.button(label, width="stretch")
    except TypeError:
        return st.button(label, use_container_width=True)

def st_plot(fig):
    try:
        return st.plotly_chart(fig, width="stretch")
    except TypeError:
        return st.plotly_chart(fig, use_container_width=True)

def st_df(df, **kwargs):
    try:
        return st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        return st.dataframe(df, use_container_width=True, **kwargs)

def cc(df):
    df.columns = [
        str(c).strip().lower()
        .replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
        for c in df.columns
    ]
    return df

# ======================
# EPM PARSER
# ======================
def parse_epm_df(raw_df):
    ep = cc(raw_df.copy())
    cx, ph = {}, {}
    debug_msgs = []

    for old in ["año", "ano"]:
        if old in ep.columns and "anio" not in ep.columns:
            ep = ep.rename(columns={old: "anio"})

    if "planta" not in ep.columns and "sede" in ep.columns:
        ep = ep.rename(columns={"sede": "planta"})
    if "planta" in ep.columns:
        ep["planta"] = ep["planta"].astype(str).apply(norm_planta)
    else:
        ep["planta"] = "TOTAL"

    kwh_col = None
    KWHS_NAMES = {"energia_kwh","energía_kwh","energia kwh","energía kwh","epm_kwh","consumo_kwh","kwh","consumo","energia (kwh)","energía (kwh)","epm (kwh)","valor","energia","energía"}
    for c in ep.columns:
        if str(c).strip().lower() in KWHS_NAMES:
            kwh_col = c; break

    if kwh_col:
        ep["epm_kwh"] = ep[kwh_col].apply(to_num_auto)
        debug_msgs.append(f"kwh_col='{kwh_col}'")
    else:
        ep["epm_kwh"] = 0.0
        debug_msgs.append("⚠ No se encontró columna kWh")

    if "mes" in ep.columns:
        for _, row in ep.iterrows():
            mes_raw = str(row.get("mes", "")).strip().lower()
            planta  = str(row.get("planta", "")).strip().upper()
            valor   = sf(row.get("epm_kwh", 0))
            if planta not in ("CAFE", "MERCADO") or valor <= 0: continue
            if "costo" in mes_raw:
                cx[planta] = valor
                debug_msgs.append(f"Costo {planta}={valor}")
            elif "promedio" in mes_raw or mes_raw.startswith("prom"):
                ph[planta] = valor
                debug_msgs.append(f"Promedio {planta}={valor}")
        ep["mes"] = ep["mes"].apply(parse_mes_any)
    else:
        ep["mes"] = 0

    if "anio" in ep.columns:
        ep["anio"] = ep["anio"].apply(tis)
    else:
        ep["anio"] = 0

    ep = ep[ep["mes"].between(1, 12)].copy()
    ep = ep[ep["anio"] > 0].copy()
    debug_msgs.append(f"rows={len(ep)} | total={sf(ep['epm_kwh'].sum()):.0f} kWh")
    return ep, cx, ph, " | ".join(debug_msgs)

# ======================
# GOOGLE SHEETS
# ======================
def read_gid_csv(sid, gid):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Sheet gid={gid} status={r.status_code}")
    head = (r.text or "")[:2500].lower()
    if "<!doctype html" in head or "accounts.google.com" in head or "servicelogin" in head:
        raise RuntimeError("Google devolvió HTML de login. El Sheet de EPM NO está público.")
    return pd.read_csv(StringIO(r.text))

def read_tab_csv(sid, tab):
    url = (
        f"https://docs.google.com/spreadsheets/d/{sid}"
        f"/gviz/tq?tqx=out:csv&sheet={requests.utils.quote(tab)}"
    )
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Sheet tab='{tab}' status={r.status_code}")
    head = (r.text or "")[:2500].lower()
    if "<!doctype html" in head or "accounts.google.com" in head or "servicelogin" in head:
        raise RuntimeError(f"Google devolvió HTML de login. La pestaña '{tab}' NO está pública.")
    return pd.read_csv(StringIO(r.text))

# ======================
# EPM LOADER
# ======================
EPM_LOCAL_PATHS = [
    r"/mnt/data/Reporte_Energia_EPM_Solar_Completo.xlsx",
    r"Reporte_Energia_EPM_Solar_Completo.xlsx",
]

def load_epm(uploaded_file=None):
    debug_msgs = []
    raw = None

    if uploaded_file is not None:
        try:
            raw = pd.read_excel(BytesIO(uploaded_file.read()))
            debug_msgs.append(f"✅ EPM desde archivo subido")
        except Exception as e:
            debug_msgs.append(f"⚠ Error leyendo archivo subido: {e}")

    if raw is None:
        try:
            raw = read_gid_csv(EPM_SHEET_ID, EPM_GID_MES)
            debug_msgs.append("✅ EPM desde Google Sheets")
        except Exception as e:
            debug_msgs.append(f"❌ EPM Sheets: {e}")

    if raw is None:
        for path in EPM_LOCAL_PATHS:
            if os.path.exists(path):
                try:
                    raw = pd.read_excel(path)
                    debug_msgs.append(f"✅ EPM desde archivo local: {path}")
                    break
                except Exception as e:
                    debug_msgs.append(f"⚠ Error local ({path}): {e}")

    if raw is None or (hasattr(raw, "empty") and raw.empty):
        empty = pd.DataFrame(columns=["anio","mes","planta","epm_kwh"])
        return empty, {}, {}, " | ".join(debug_msgs) + " | ⛔ Sin datos EPM"

    ep, cx, ph, parse_info = parse_epm_df(raw)
    return ep, cx, ph, " | ".join(debug_msgs) + " | " + parse_info

# ======================
# SOLAR LOADER
# ======================
@st.cache_data(ttl=300)
def cargar_solar():
    ms = cc(read_tab_csv(SOLAR_SHEET_ID, SOLAR_TAB_MES))
    di = cc(read_tab_csv(SOLAR_SHEET_ID, SOLAR_TAB_DIA))
    hr = cc(read_tab_csv(SOLAR_SHEET_ID, SOLAR_TAB_HORA))

    for d in [ms, di, hr]:
        for old in ["año","ano"]:
            if old in d.columns and "anio" not in d.columns:
                d.rename(columns={old: "anio"}, inplace=True)

    ms["planta"]      = ms["planta"].astype(str).apply(norm_planta)
    ms["anio"]        = ms["anio"].apply(tis)
    ms["mes"]         = ms["mes"].apply(parse_mes_any)
    ms["energia_kwh"] = ms["energia_kwh"].apply(to_num_auto)

    di["planta"]      = di["planta"].astype(str).apply(norm_planta)
    di["energia_kwh"] = di["energia_kwh"].apply(to_num_auto)
    di["fecha"]       = pd.to_datetime(di["fecha"], errors="coerce", dayfirst=True)

    hr["planta"]      = hr["planta"].astype(str).apply(norm_planta)
    hr["energia_kwh"] = hr["energia_kwh"].apply(to_num_auto)
    hr["fecha"]       = pd.to_datetime(hr["fecha"], errors="coerce", dayfirst=True)
    hr["hora_num"]    = hr["hora"].apply(parse_h)

    return ms, di, hr

# ======================
# HEADER
# ======================
def render_header(logo_bytes=None):
    col_logo, col_title, col_right = st.columns([1.2, 5, 1.2])

    with col_logo:
        if logo_bytes:
            st.image(logo_bytes, use_container_width=True)

    with col_title:
        st.markdown(f"""
<div style="text-align:center;padding:10px 0">
  <div style="font-size:32px;font-weight:900;margin:0;line-height:1.1;
              background:linear-gradient(135deg,{COLOR_CAFE},{COLOR_MERC},{COLOR_TOTAL});
              -webkit-background-clip:text;-webkit-text-fill-color:transparent">
    Energía Solar · Café &amp; Mercado · Monte Sereno
  </div>
</div>
""", unsafe_allow_html=True)

    with col_right:
        pass

    st.markdown("<hr style='margin:8px 0 14px;border:none;border-top:1px solid #e2e8f0'>", unsafe_allow_html=True)

# ======================
# APP
# ======================
try:
    ms_df, di_df, hr_df = cargar_solar()
except Exception as e:
    st.error(f"Error leyendo Google Sheets (Solar).\n\n{e}\n\n{traceback.format_exc()}")
    st.stop()

di_df = di_df.dropna(subset=["fecha"])
hr_df = hr_df.dropna(subset=["fecha","hora_num"])

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("**Logo Axioma**")
    logo_file = st.file_uploader(
        "Sube el logo (.png/.jpg/.svg)",
        type=["png","jpg","jpeg","svg","webp"],
        key="logo_up",
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Archivo EPM Excel**")
    epm_file = st.file_uploader(
        "Excel EPM",
        type=["xlsx","xls","csv"],
        key="epm_up",
        label_visibility="collapsed"
    )

logo_bytes = None
if logo_file is not None:
    logo_bytes = logo_file.read()

render_header(logo_bytes)

# EPM
ep_df, cx, ph, epm_debug = load_epm(epm_file)
for k, v in cx.items():
    if v > 0:
        COSTOS_EPM[k] = v

ya = sorted(set(ms_df["anio"].unique()) | (set(ep_df["anio"].unique()) if not ep_df.empty else set()))
ma = sorted(set(ms_df["mes"].unique())  | (set(ep_df["mes"].unique())  if not ep_df.empty else set()))
pa = sorted(set(ms_df["planta"].unique()) | {"CAFE","MERCADO"})

min_f = di_df["fecha"].min().date() if not di_df.empty else datetime.today().date()
max_f = di_df["fecha"].max().date() if not di_df.empty else datetime.today().date()

# COLUMNAS
col_f, col_m = st.columns([1.1, 3.2], gap="large")

with col_f:
    st.markdown('<div class="left-card">', unsafe_allow_html=True)
    st.markdown('<div class="left-title">Filtros</div>', unsafe_allow_html=True)

    if st_btn("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="fsec">VISTA</div>', unsafe_allow_html=True)
    vista = st.selectbox("v", ["Mensual (Solar vs EPM)", "Diario (Solar)", "Hora (Solar)"], label_visibility="collapsed")

    st.markdown('<div class="fsec">PLANTAS</div>', unsafe_allow_html=True)
    all_pl = st.checkbox("Seleccionar todas", value=True, key="all_pl")
    sel_pl = pa if all_pl else st.multiselect("p", pa, default=["CAFE","MERCADO"], label_visibility="collapsed")

    st.markdown('<div class="fsec">AÑOS</div>', unsafe_allow_html=True)
    all_yr = st.checkbox("Seleccionar todos", value=True, key="all_yr")
    sel_yr = ya if all_yr else st.multiselect("y", ya, default=ya, label_visibility="collapsed")

    st.markdown('<div class="fsec">MESES</div>', unsafe_allow_html=True)
    all_ms = st.checkbox("Seleccionar todos", value=True, key="all_ms")
    sel_ms = ma if all_ms else st.multiselect("m", ma, default=ma, format_func=lambda x: ML.get(int(x), str(x)), label_visibility="collapsed")

    st.markdown('<div class="fsec">RANGO FECHAS</div>', unsafe_allow_html=True)
    fr = st.date_input("f", value=(min_f, max_f), min_value=min_f, max_value=max_f, label_visibility="collapsed")

    st.markdown('<div class="fsec">RANGO HORARIO</div>', unsafe_allow_html=True)
    h_min, h_max = st.select_slider(
        "h", options=list(range(24)), value=(0, 23),
        format_func=lambda x: f"{x:02d}:00", label_visibility="collapsed"
    )

    st.markdown('<div class="fsec">COSTOS kWh</div>', unsafe_allow_html=True)
    c_cafe = COSTOS_EPM["CAFE"]
    c_merc = COSTOS_EPM["MERCADO"]
    src_txt = "📄 desde Excel" if cx else "⚙️ config base"
    st.markdown(f"""
    <div style='font-size:12px;line-height:1.8'>
      <b>CAFE:</b> ${c_cafe:,}/kWh<br>
      <b>MERCADO:</b> ${c_merc:,}/kWh<br>
      <span style='color:#64748b;font-size:10px'>{src_txt}</span>
    </div>
    """.replace(",","."), unsafe_allow_html=True)

    if ph:
        st.markdown('<div class="fsec">PROM. HISTÓRICO EPM</div>', unsafe_allow_html=True)
        for plnt, val in ph.items():
            st.markdown(f"**{plnt}:** {fn(val)} kWh/mes")

    st.markdown('<div class="fsec">ESTADO EPM</div>', unsafe_allow_html=True)
    if not ep_df.empty:
        epm_rows = len(ep_df)
        epm_sum  = sf(ep_df["epm_kwh"].sum())
        st.markdown(
            f'<div class="epm-ok">✅ {epm_rows} registros · {fn(epm_sum)} kWh</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:8px;padding:6px 10px;font-size:11px;font-weight:700;color:#991b1b;margin-top:4px">⛔ Sin datos EPM</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div class="small-note">Última actualización: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

if not sel_pl: sel_pl = ["CAFE","MERCADO"]
if not sel_yr: sel_yr = ya
if not sel_ms: sel_ms = ma
fi, ff = (fr if isinstance(fr, (tuple, list)) and len(fr) == 2 else (min_f, max_f))

# FILTROS
mf = ms_df[
    ms_df["planta"].isin(sel_pl) &
    ms_df["anio"].isin(sel_yr) &
    ms_df["mes"].isin(sel_ms)
].copy()

dff = di_df[
    di_df["planta"].isin(sel_pl) &
    (di_df["fecha"].dt.date >= fi) &
    (di_df["fecha"].dt.date <= ff)
].copy()

hf = hr_df[
    hr_df["planta"].isin(sel_pl) &
    (hr_df["fecha"].dt.date >= fi) &
    (hr_df["fecha"].dt.date <= ff) &
    (hr_df["hora_num"] >= h_min) &
    (hr_df["hora_num"] <= h_max)
].copy()

ef = ep_df[
    ep_df["anio"].isin(sel_yr) &
    ep_df["mes"].isin(sel_ms)
].copy() if not ep_df.empty else pd.DataFrame(columns=["anio","mes","planta","epm_kwh"])

# ======================
# CONTENIDO
# ======================
with col_m:

    # =========================================================
    # MENSUAL
    # =========================================================
    if vista.startswith("Mensual"):

        gc  = mf[mf["planta"]=="CAFE"]["energia_kwh"].sum()
        gm  = mf[mf["planta"]=="MERCADO"]["energia_kwh"].sum()
        gt_ = gc + gm

        et_ = ef["epm_kwh"].sum() if not ef.empty else 0
        ec_ = ef[ef["planta"]=="CAFE"]["epm_kwh"].sum()    if not ef.empty else 0
        em_ = ef[ef["planta"]=="MERCADO"]["epm_kwh"].sum() if not ef.empty else 0

        ac_ = gc * COSTOS_EPM["CAFE"]
        am_ = gm * COSTOS_EPM["MERCADO"]
        at_ = ac_ + am_
        cp_ = (gt_ / et_ * 100) if et_ > 0 else 0

        # Promedios individuales
        sol_cafe_prom = mf[mf["planta"]=="CAFE"].groupby(["anio","mes"])["energia_kwh"].sum().mean() if len(mf[mf["planta"]=="CAFE"]) > 0 else 0
        sol_merc_prom = mf[mf["planta"]=="MERCADO"].groupby(["anio","mes"])["energia_kwh"].sum().mean() if len(mf[mf["planta"]=="MERCADO"]) > 0 else 0
        epm_cafe_prom = ef[ef["planta"]=="CAFE"].groupby(["anio","mes"])["epm_kwh"].sum().mean() if len(ef[ef["planta"]=="CAFE"]) > 0 else 0
        epm_merc_prom = ef[ef["planta"]=="MERCADO"].groupby(["anio","mes"])["epm_kwh"].sum().mean() if len(ef[ef["planta"]=="MERCADO"]) > 0 else 0

        # KPIs principales
        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi-card c3">
            <div class="kl">Solar Total</div>
            <div class="kv" style="color:{COLOR_TOTAL}">{fn(gt_,1)} kWh</div>
            <div class="ks">Generación fotovoltaica</div>
          </div>
          <div class="kpi-card c5">
            <div class="kl">EPM Total</div>
            <div class="kv" style="color:#ef4444">{fn(et_)} kWh</div>
            <div class="ks">Consumo eléctrico</div>
          </div>
          <div class="kpi-card c4">
            <div class="kl">Ahorro Total</div>
            <div class="kv" style="color:{COLOR_AMBAR}">{fc(at_, 2)}</div>
            <div class="ks">Ahorro económico</div>
          </div>
          <div class="kpi-card c1">
            <div class="kl">Cobertura</div>
            <div class="kv" style="color:{COLOR_CAFE}">{fn(cp_,1)}%</div>
            <div class="ks">Solar / EPM</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # KPIs por planta
        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi-card c1">
            <div class="kl">Solar CAFE</div>
            <div class="kv" style="color:{COLOR_CAFE}">{fn(gc,1)} kWh</div>
            <div class="ks">Prom: {fn(sol_cafe_prom,1)} kWh/mes</div>
          </div>
          <div class="kpi-card c2">
            <div class="kl">Solar MERCADO</div>
            <div class="kv" style="color:{COLOR_MERC}">{fn(gm,1)} kWh</div>
            <div class="ks">Prom: {fn(sol_merc_prom,1)} kWh/mes</div>
          </div>
          <div class="kpi-card c6">
            <div class="kl">EPM CAFE</div>
            <div class="kv" style="color:{COLOR_EPM_CAFE}">{fn(ec_)} kWh</div>
            <div class="ks">Prom: {fn(epm_cafe_prom,1)} kWh/mes</div>
          </div>
          <div class="kpi-card c7">
            <div class="kl">EPM MERCADO</div>
            <div class="kv" style="color:{COLOR_EPM_MERC}">{fn(em_)} kWh</div>
            <div class="ks">Prom: {fn(epm_merc_prom,1)} kWh/mes</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Pivots
        sp = mf.groupby(["anio","mes","planta"], as_index=False)["energia_kwh"].sum()
        sp = sp.pivot_table(
            index=["anio","mes"], columns="planta",
            values="energia_kwh", aggfunc="sum", fill_value=0
        ).reset_index()
        for c in ["CAFE","MERCADO"]:
            if c not in sp.columns: sp[c] = 0.0
        sp["SOL_T"] = sp["CAFE"] + sp["MERCADO"]

        if ef.empty or et_ == 0:
            epp = pd.DataFrame(columns=["anio","mes","EC","EM","EPM_T"])
        else:
            epp = ef.pivot_table(
                index=["anio","mes"], columns="planta",
                values="epm_kwh", aggfunc="sum", fill_value=0
            ).reset_index()
            for c in ["CAFE","MERCADO"]:
                if c not in epp.columns: epp[c] = 0.0
            epp["EPM_T"] = epp["CAFE"] + epp["MERCADO"]
            if "TOTAL" in epp.columns:
                epp["EPM_T"] = np.where(epp["EPM_T"] > 0, epp["EPM_T"], epp["TOTAL"])
            epp = epp.rename(columns={"CAFE":"EC","MERCADO":"EM"})

        if epp.empty:
            b = sp.copy()
            b["EC"]    = 0.0
            b["EM"]    = 0.0
            b["EPM_T"] = 0.0
        else:
            b = pd.merge(sp, epp[["anio","mes","EC","EM","EPM_T"]], on=["anio","mes"], how="outer")
            for c in ["CAFE","MERCADO","SOL_T","EC","EM","EPM_T"]:
                if c not in b.columns: b[c] = 0.0
                b[c] = b[c].fillna(0.0)

        b["anio"] = b["anio"].apply(tis)
        b["mes"]  = b["mes"].apply(parse_mes_any)
        b = b[b["mes"].between(1,12)].sort_values(["anio","mes"]).reset_index(drop=True)
        b["Mes"]    = b.apply(lambda r: mlbl(r["anio"], r["mes"]), axis=1)
        b["Cob"]    = b.apply(lambda r: (r["SOL_T"] / r["EPM_T"] * 100) if r["EPM_T"] > 0 else 0, axis=1)
        b["Ahorro"] = b["CAFE"] * COSTOS_EPM["CAFE"] + b["MERCADO"] * COSTOS_EPM["MERCADO"]

        # ──── GRÁFICO 1: Comparativo 4 barras agrupadas con promedios ────
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="pt">Comparativo: Solar vs EPM por Planta</div>', unsafe_allow_html=True)
        st.markdown('<div class="ps">4 series agrupadas con líneas de promedio por planta</div>', unsafe_allow_html=True)

        fig1 = go.Figure()

        # Solar CAFE
        fig1.add_trace(go.Bar(
            name="Solar CAFE",
            x=b["Mes"],
            y=b["CAFE"],
            marker_color=COLOR_CAFE,
            text=b["CAFE"].apply(lambda v: fn(v,1) if v > 0 else ""),
            textposition="outside",
            textfont=dict(size=9),
            offsetgroup="1"
        ))

        # Solar MERCADO
        fig1.add_trace(go.Bar(
            name="Solar MERCADO",
            x=b["Mes"],
            y=b["MERCADO"],
            marker_color=COLOR_MERC,
            text=b["MERCADO"].apply(lambda v: fn(v,1) if v > 0 else ""),
            textposition="outside",
            textfont=dict(size=9),
            offsetgroup="2"
        ))

        # EPM CAFE (color oscuro sólido)
        fig1.add_trace(go.Bar(
            name="EPM CAFE",
            x=b["Mes"],
            y=b["EC"],
            marker_color=COLOR_EPM_CAFE,
            text=b["EC"].apply(lambda v: fn(v) if v > 0 else ""),
            textposition="outside",
            textfont=dict(size=9),
            offsetgroup="3"
        ))

        # EPM MERCADO (color oscuro sólido)
        fig1.add_trace(go.Bar(
            name="EPM MERCADO",
            x=b["Mes"],
            y=b["EM"],
            marker_color=COLOR_EPM_MERC,
            text=b["EM"].apply(lambda v: fn(v) if v > 0 else ""),
            textposition="outside",
            textfont=dict(size=9),
            offsetgroup="4"
        ))

        # Promedios como líneas horizontales
        if sol_cafe_prom > 0:
            fig1.add_hline(
                y=sol_cafe_prom,
                line_dash="dot",
                line_color=COLOR_CAFE,
                line_width=2,
                annotation_text=f"Prom Solar CAFE: {fn(sol_cafe_prom,1)}",
                annotation_position="top left",
                annotation_font=dict(size=9, color=COLOR_CAFE)
            )
        if sol_merc_prom > 0:
            fig1.add_hline(
                y=sol_merc_prom,
                line_dash="dash",
                line_color=COLOR_MERC,
                line_width=2,
                annotation_text=f"Prom Solar MERCADO: {fn(sol_merc_prom,1)}",
                annotation_position="bottom right",
                annotation_font=dict(size=9, color=COLOR_MERC)
            )
        if epm_cafe_prom > 0:
            fig1.add_hline(
                y=epm_cafe_prom,
                line_dash="dot",
                line_color=COLOR_EPM_CAFE,
                line_width=2,
                annotation_text=f"Prom EPM CAFE: {fn(epm_cafe_prom,1)}",
                annotation_position="top right",
                annotation_font=dict(size=9, color=COLOR_EPM_CAFE)
            )
        if epm_merc_prom > 0:
            fig1.add_hline(
                y=epm_merc_prom,
                line_dash="dashdot",
                line_color=COLOR_EPM_MERC,
                line_width=2,
                annotation_text=f"Prom EPM MERCADO: {fn(epm_merc_prom,1)}",
                annotation_position="bottom left",
                annotation_font=dict(size=9, color=COLOR_EPM_MERC)
            )

        fig1.update_layout(
            barmode="group",
            yaxis_title="Energía (kWh)",
            bargap=0.15,
            bargroupgap=0.1
        )
        fig1 = aplyt(fig1, 500)
        st_plot(fig1)
        st.markdown("</div>", unsafe_allow_html=True)

        # ──── GRÁFICO 2: Barras apiladas EPM vs Solar ────
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="pt">Comparativo Apilado: Consumo EPM + Generación Solar</div>', unsafe_allow_html=True)
        st.markdown('<div class="ps">Barras apiladas mostrando distribución por planta</div>', unsafe_allow_html=True)

        fig2 = go.Figure()

        # EPM base (arriba)
        fig2.add_trace(go.Bar(
            name="EPM CAFE",
            x=b["Mes"],
            y=b["EC"],
            marker_color=COLOR_EPM_CAFE,
            text=b["EC"].apply(lambda v: fn(v) if v > 0 else ""),
            textposition="inside",
            textfont=dict(size=9, color="white")
        ))
        fig2.add_trace(go.Bar(
            name="EPM MERCADO",
            x=b["Mes"],
            y=b["EM"],
            marker_color=COLOR_EPM_MERC,
            text=b["EM"].apply(lambda v: fn(v) if v > 0 else ""),
            textposition="inside",
            textfont=dict(size=9, color="white")
        ))

        # Solar encima
        fig2.add_trace(go.Bar(
            name="Solar CAFE",
            x=b["Mes"],
            y=b["CAFE"],
            marker_color=COLOR_CAFE,
            text=b["CAFE"].apply(lambda v: fn(v,1) if v > 0 else ""),
            textposition="inside",
            textfont=dict(size=9, color="white")
        ))
        fig2.add_trace(go.Bar(
            name="Solar MERCADO",
            x=b["Mes"],
            y=b["MERCADO"],
            marker_color=COLOR_MERC,
            text=b["MERCADO"].apply(lambda v: fn(v,1) if v > 0 else ""),
            textposition="inside",
            textfont=dict(size=9, color="white")
        ))

        # Promedios totales por planta (Solar + EPM)
        prom_cafe_total = sol_cafe_prom + epm_cafe_prom
        prom_merc_total = sol_merc_prom + epm_merc_prom
        
        if prom_cafe_total > 0:
            fig2.add_hline(
                y=prom_cafe_total,
                line_dash="dot",
                line_color=COLOR_CAFE,
                line_width=2,
                annotation_text=f"Prom CAFE (Solar+EPM): {fn(prom_cafe_total,1)}",
                annotation_position="top left",
                annotation_font=dict(size=8, color=COLOR_CAFE)
            )
        if prom_merc_total > 0:
            fig2.add_hline(
                y=prom_merc_total,
                line_dash="dash",
                line_color=COLOR_MERC,
                line_width=2,
                annotation_text=f"Prom MERCADO (Solar+EPM): {fn(prom_merc_total,1)}",
                annotation_position="bottom right",
                annotation_font=dict(size=8, color=COLOR_MERC)
            )

        fig2.update_layout(
            barmode="stack",
            yaxis_title="Energía (kWh)"
        )
        fig2 = aplyt(fig2, 480)
        st_plot(fig2)
        st.markdown("</div>", unsafe_allow_html=True)

        # Tarjetas resumen
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown('<div class="panel"><div class="pt">Solar por Planta</div>', unsafe_allow_html=True)
            fp = go.Figure(go.Pie(
                labels=["CAFE","MERCADO"], values=[sf(gc), sf(gm)],
                hole=.55,
                marker=dict(colors=[COLOR_CAFE, COLOR_MERC], line=dict(color="white", width=3)),
                textinfo="label+percent", textfont=dict(size=11)
            ))
            fp.add_annotation(
                text=f"<b>{fn(gt_,1)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                x=.5, y=.5, showarrow=False, font=dict(size=16, color="#0f172a")
            )
            fp.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                             height=260, margin=dict(l=10,r=10,t=10,b=10))
            st_plot(fp)
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="panel"><div class="pt">EPM por Planta</div>', unsafe_allow_html=True)
            if (ec_ + em_) > 0:
                fp2 = go.Figure(go.Pie(
                    labels=["CAFE","MERCADO"], values=[sf(ec_), sf(em_)],
                    hole=.55,
                    marker=dict(colors=[COLOR_EPM_CAFE, COLOR_EPM_MERC], line=dict(color="white", width=3)),
                    textinfo="label+percent", textfont=dict(size=11)
                ))
            elif et_ > 0:
                fp2 = go.Figure(go.Pie(
                    labels=["TOTAL"], values=[sf(et_)],
                    hole=.55,
                    marker=dict(colors=["#ef4444"], line=dict(color="white", width=3)),
                    textinfo="label+percent", textfont=dict(size=11)
                ))
            else:
                fp2 = go.Figure()
                fp2.add_annotation(
                    text="Sin datos EPM",
                    x=.5, y=.5, showarrow=False,
                    font=dict(size=14, color="#94a3b8"), xref="paper", yref="paper"
                )
            fp2.add_annotation(
                text=f"<b>{fn(et_)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                x=.5, y=.5, showarrow=False, font=dict(size=16, color="#0f172a")
            )
            fp2.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                              height=260, margin=dict(l=10,r=10,t=10,b=10))
            st_plot(fp2)
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="panel"><div class="pt">Ahorro Mensual</div>', unsafe_allow_html=True)
            fa = go.Figure(go.Bar(
                x=b["Mes"], y=b["Ahorro"],
                marker_color=COLOR_AMBAR,
                text=b["Ahorro"].apply(lambda v: fc(v, 2) if v > 0 else ""),
                textposition="outside", textfont=dict(size=9, color=COLOR_AMBAR)
            ))
            fa.update_layout(showlegend=False, yaxis_title="$COP")
            fa = aplyt(fa, 260)
            st_plot(fa)
            st.markdown("</div>", unsafe_allow_html=True)

        # Tendencia
        st.markdown('<div class="panel"><div class="pt">Tendencia Mensual</div>', unsafe_allow_html=True)
        ft = go.Figure()
        if b["EPM_T"].sum() > 0:
            ft.add_trace(go.Scatter(
                name="EPM Total", x=b["Mes"], y=b["EPM_T"],
                mode="lines+markers",
                line=dict(color="#ef4444", width=2.5),
                marker=dict(size=8, color="#ef4444", line=dict(width=2, color="white")),
                fill="tozeroy", fillcolor="rgba(239,68,68,.06)"
            ))
        ft.add_trace(go.Scatter(
            name="Solar Total", x=b["Mes"], y=b["SOL_T"],
            mode="lines+markers",
            line=dict(color=COLOR_TOTAL, width=3),
            marker=dict(size=9, color=COLOR_TOTAL, line=dict(width=2, color="white")),
            fill="tozeroy", fillcolor="rgba(139,92,246,.08)"
        ))
        ft.update_layout(yaxis_title="Energía (kWh)")
        ft = aplyt(ft, 350)
        st_plot(ft)
        st.markdown("</div>", unsafe_allow_html=True)

        # Tabla resumen mejorada
        st.markdown('<div class="panel"><div class="pt">Tabla Resumen Mensual</div>', unsafe_allow_html=True)
        tbl = pd.DataFrame({
            "Periodo": b["Mes"],
            "Solar CAFE (kWh)": b["CAFE"].round(1),
            "Solar MERCADO (kWh)": b["MERCADO"].round(1),
            "Solar TOTAL (kWh)": b["SOL_T"].round(1),
            "EPM CAFE (kWh)": b["EC"].round(0).fillna(0).astype(int),
            "EPM MERCADO (kWh)": b["EM"].round(0).fillna(0).astype(int),
            "EPM TOTAL (kWh)": b["EPM_T"].round(0).fillna(0).astype(int),
            "Cobertura (%)": b["Cob"].round(1),
            "Ahorro (COP)": b["Ahorro"].round(2),
        })
        st_df(tbl, hide_index=True, column_config={
            "Solar CAFE (kWh)": st.column_config.NumberColumn(format="%.1f"),
            "Solar MERCADO (kWh)": st.column_config.NumberColumn(format="%.1f"),
            "Solar TOTAL (kWh)": st.column_config.NumberColumn(format="%.1f"),
            "EPM CAFE (kWh)": st.column_config.NumberColumn(format="%d"),
            "EPM MERCADO (kWh)": st.column_config.NumberColumn(format="%d"),
            "EPM TOTAL (kWh)": st.column_config.NumberColumn(format="%d"),
            "Cobertura (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
            "Ahorro (COP)": st.column_config.NumberColumn(format="$%.2f"),
        })
        st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================
    # VISTA DIARIA
    # =========================================================
    elif vista.startswith("Diario"):
        st.markdown("## Vista Diaria: Generación Solar")

        if dff.empty:
            st.info("Sin datos para el rango seleccionado.")
        else:
            dd = dff.groupby(["fecha","planta"], as_index=False)["energia_kwh"].sum()
            dd["lbl"] = dd["fecha"].apply(dlbl)

            # KPIs diarios
            dc = dd[dd["planta"]=="CAFE"]["energia_kwh"].sum()
            dm = dd[dd["planta"]=="MERCADO"]["energia_kwh"].sum()
            dt = dc + dm
            dias_totales = dd["fecha"].nunique()
            prom_diario = dt / dias_totales if dias_totales > 0 else 0
            ahorro_diario = dc * COSTOS_EPM["CAFE"] + dm * COSTOS_EPM["MERCADO"]

            st.markdown(f"""
            <div class="kpi-row">
              <div class="kpi-card c3">
                <div class="kl">Total Generado</div>
                <div class="kv" style="color:{COLOR_TOTAL}">{fn(dt,1)} kWh</div>
                <div class="ks">{dias_totales} días</div>
              </div>
              <div class="kpi-card c1">
                <div class="kl">CAFE</div>
                <div class="kv" style="color:{COLOR_CAFE}">{fn(dc,1)} kWh</div>
              </div>
              <div class="kpi-card c2">
                <div class="kl">MERCADO</div>
                <div class="kv" style="color:{COLOR_MERC}">{fn(dm,1)} kWh</div>
              </div>
              <div class="kpi-card c4">
                <div class="kl">Ahorro Total</div>
                <div class="kv" style="color:{COLOR_AMBAR}">{fc(ahorro_diario, 2)}</div>
              </div>
              <div class="kpi-card c3">
                <div class="kl">Promedio Diario</div>
                <div class="kv" style="color:{COLOR_TOTAL}">{fn(prom_diario,1)} kWh/día</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Gráfico de barras apiladas (más visible que área)
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="pt">Generación Diaria (Flujo)</div>', unsafe_allow_html=True)

            dd_pivot = dd.pivot_table(index="fecha", columns="planta", values="energia_kwh", fill_value=0).reset_index()
            if "CAFE" not in dd_pivot.columns: dd_pivot["CAFE"] = 0
            if "MERCADO" not in dd_pivot.columns: dd_pivot["MERCADO"] = 0
            dd_pivot["lbl"] = dd_pivot["fecha"].apply(dlbl)

            fig_d = go.Figure()
            fig_d.add_trace(go.Bar(
                name="CAFE",
                x=dd_pivot["lbl"],
                y=dd_pivot["CAFE"],
                marker_color=COLOR_CAFE,
                text=dd_pivot["CAFE"].apply(lambda v: fn(v,1) if v > 10 else ""),
                textposition="inside",
                textfont=dict(size=8, color="white")
            ))
            fig_d.add_trace(go.Bar(
                name="MERCADO",
                x=dd_pivot["lbl"],
                y=dd_pivot["MERCADO"],
                marker_color=COLOR_MERC,
                text=dd_pivot["MERCADO"].apply(lambda v: fn(v,1) if v > 10 else ""),
                textposition="inside",
                textfont=dict(size=8, color="white")
            ))
            fig_d.update_layout(
                barmode="stack",
                yaxis_title="kWh",
                hovermode="x unified",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_d = aplyt(fig_d, 400)
            st_plot(fig_d)
            st.markdown("</div>", unsafe_allow_html=True)

            # Tabla diaria con ahorro
            st.markdown('<div class="panel"><div class="pt">Tabla Diaria</div>', unsafe_allow_html=True)
            tbl_d = dd.pivot_table(index="lbl", columns="planta", values="energia_kwh", fill_value=0).reset_index()
            tbl_d.columns.name = None
            if "CAFE" not in tbl_d.columns: tbl_d["CAFE"] = 0
            if "MERCADO" not in tbl_d.columns: tbl_d["MERCADO"] = 0
            tbl_d["TOTAL (kWh)"] = tbl_d.get("CAFE", 0) + tbl_d.get("MERCADO", 0)
            tbl_d["Ahorro (COP)"] = tbl_d.get("CAFE", 0) * COSTOS_EPM["CAFE"] + tbl_d.get("MERCADO", 0) * COSTOS_EPM["MERCADO"]
            tbl_d = tbl_d.rename(columns={"lbl": "Fecha", "CAFE": "CAFE (kWh)", "MERCADO": "MERCADO (kWh)"})
            st_df(tbl_d, hide_index=True, column_config={
                "CAFE (kWh)": st.column_config.NumberColumn(format="%.1f"),
                "MERCADO (kWh)": st.column_config.NumberColumn(format="%.1f"),
                "TOTAL (kWh)": st.column_config.NumberColumn(format="%.1f"),
                "Ahorro (COP)": st.column_config.NumberColumn(format="$%.2f"),
            })
            st.markdown("</div>", unsafe_allow_html=True)

            # Mapa de calor
            st.markdown('<div class="panel"><div class="pt">Mapa de Calor: Generación por Día</div>', unsafe_allow_html=True)
            dff_hm = dff.copy()
            dff_hm["dia"] = dff_hm["fecha"].dt.day
            dff_hm["mes_nombre"] = dff_hm["fecha"].dt.month.apply(lambda m: ML.get(m, str(m)))
            hm_pivot = dff_hm.groupby(["mes_nombre","dia"])["energia_kwh"].sum().reset_index()
            hm_matrix = hm_pivot.pivot_table(index="mes_nombre", columns="dia", values="energia_kwh", fill_value=0)

            fig_hm = go.Figure(go.Heatmap(
                z=hm_matrix.values,
                x=hm_matrix.columns,
                y=hm_matrix.index,
                colorscale="YlOrRd",
                text=np.round(hm_matrix.values, 1),
                texttemplate="%{text}",
                textfont={"size": 9},
                hovertemplate="Mes: %{y}<br>Día: %{x}<br>kWh: %{z:.1f}<extra></extra>"
            ))
            fig_hm.update_layout(
                xaxis_title="Día del mes",
                yaxis_title="Mes",
                height=300,
                margin=dict(l=50,r=30,t=30,b=50)
            )
            st_plot(fig_hm)
            st.markdown("</div>", unsafe_allow_html=True)

            # Tabla resumen diaria
            st.markdown('<div class="panel"><div class="pt">Resumen Diario</div>', unsafe_allow_html=True)
            resumen_diario = dff.groupby("planta")["energia_kwh"].agg(["sum","mean","max","min"]).reset_index()
            resumen_diario.columns = ["Planta", "Total (kWh)", "Promedio (kWh)", "Máximo (kWh)", "Mínimo (kWh)"]
            st_df(resumen_diario, hide_index=True, column_config={
                "Total (kWh)": st.column_config.NumberColumn(format="%.1f"),
                "Promedio (kWh)": st.column_config.NumberColumn(format="%.1f"),
                "Máximo (kWh)": st.column_config.NumberColumn(format="%.1f"),
                "Mínimo (kWh)": st.column_config.NumberColumn(format="%.1f"),
            })
            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================
    # VISTA HORARIA
    # =========================================================
    else:
        st.markdown("## Vista Horaria: Generación Solar")

        if hf.empty:
            st.info("Sin datos para el rango y horario seleccionados.")
        else:
            hh = hf.groupby(["hora_num","planta"], as_index=False)["energia_kwh"].mean()

            # KPIs horarios
            hc = hf[hf["planta"]=="CAFE"]["energia_kwh"].sum()
            hm = hf[hf["planta"]=="MERCADO"]["energia_kwh"].sum()
            ht = hc + hm
            hora_pico_c = hh[hh["planta"]=="CAFE"].nlargest(1, "energia_kwh")["hora_num"].values[0] if len(hh[hh["planta"]=="CAFE"]) > 0 else 0
            hora_pico_m = hh[hh["planta"]=="MERCADO"].nlargest(1, "energia_kwh")["hora_num"].values[0] if len(hh[hh["planta"]=="MERCADO"]) > 0 else 0

            st.markdown(f"""
            <div class="kpi-row">
              <div class="kpi-card c3">
                <div class="kl">Total Generado</div>
                <div class="kv" style="color:{COLOR_TOTAL}">{fn(ht,1)} kWh</div>
              </div>
              <div class="kpi-card c1">
                <div class="kl">CAFE</div>
                <div class="kv" style="color:{COLOR_CAFE}">{fn(hc,1)} kWh</div>
                <div class="ks">Pico: {int(hora_pico_c):02d}:00</div>
              </div>
              <div class="kpi-card c2">
                <div class="kl">MERCADO</div>
                <div class="kv" style="color:{COLOR_MERC}">{fn(hm,1)} kWh</div>
                <div class="ks">Pico: {int(hora_pico_m):02d}:00</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="pt">Generación Promedio por Hora</div>', unsafe_allow_html=True)

            fig_h = go.Figure()
            for pl, col in [("CAFE", COLOR_CAFE), ("MERCADO", COLOR_MERC)]:
                sub = hh[hh["planta"]==pl].sort_values("hora_num")
                if not sub.empty:
                    fig_h.add_trace(go.Scatter(
                        name=f"{pl}",
                        x=sub["hora_num"],
                        y=sub["energia_kwh"],
                        mode="lines+markers",
                        line=dict(color=col, width=3),
                        marker=dict(size=8, color=col, line=dict(width=2, color="white")),
                        fill="tozeroy",
                        fillcolor=col.replace("#","rgba(").rstrip(")") + ",.12)"
                        if False else f"rgba({'59,130,246' if pl=='CAFE' else '16,185,129'},.12)"
                    ))
            fig_h.update_layout(
                xaxis=dict(title="Hora del día", tickmode="linear", dtick=1,
                           ticktext=[f"{h:02d}:00" for h in range(24)],
                           tickvals=list(range(24))),
                yaxis_title="kWh promedio",
                hovermode="x unified"
            )
            fig_h = aplyt(fig_h, 460)
            st_plot(fig_h)
            st.markdown("</div>", unsafe_allow_html=True)

            # Tabla resumen horaria
            st.markdown('<div class="panel"><div class="pt">Resumen por Hora</div>', unsafe_allow_html=True)
            
            # Pivot para tener formato tabular
            hh_pivot = hh.pivot_table(index="hora_num", columns="planta", values="energia_kwh", fill_value=0).reset_index()
            hh_pivot.columns.name = None
            if "CAFE" not in hh_pivot.columns: hh_pivot["CAFE"] = 0
            if "MERCADO" not in hh_pivot.columns: hh_pivot["MERCADO"] = 0
            hh_pivot["TOTAL"] = hh_pivot["CAFE"] + hh_pivot["MERCADO"]
            hh_pivot["Hora"] = hh_pivot["hora_num"].apply(lambda h: f"{int(h):02d}:00")
            hh_pivot = hh_pivot.rename(columns={"CAFE": "CAFE Promedio (kWh)", "MERCADO": "MERCADO Promedio (kWh)", "TOTAL": "TOTAL Promedio (kWh)"})
            hh_pivot = hh_pivot[["Hora", "CAFE Promedio (kWh)", "MERCADO Promedio (kWh)", "TOTAL Promedio (kWh)"]]
            
            st_df(hh_pivot, hide_index=True, column_config={
                "CAFE Promedio (kWh)": st.column_config.NumberColumn(format="%.2f"),
                "MERCADO Promedio (kWh)": st.column_config.NumberColumn(format="%.2f"),
                "TOTAL Promedio (kWh)": st.column_config.NumberColumn(format="%.2f"),
            })
            st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div class="dash-footer">
  Dashboard Energía Solar · GEDICOL &nbsp;|&nbsp; &copy; {datetime.now().year} &nbsp;|&nbsp;
  <span style="color:{COLOR_CAFE}">&#9632;</span> CAFE &nbsp;
  <span style="color:{COLOR_MERC}">&#9632;</span> MERCADO &nbsp;
  <span style="color:{COLOR_TOTAL}">&#9632;</span> Total &nbsp;
  <span style="color:{COLOR_AMBAR}">&#9632;</span> Ahorro
</div>
""", unsafe_allow_html=True)