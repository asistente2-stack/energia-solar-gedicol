# -*- coding: utf-8 -*-
import re, traceback
from io import StringIO
from datetime import datetime
import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ====================== CONFIG ======================
SOLAR_SHEET_ID = "1ceFwwFm6D1QRW4slPj67BlSDR9woGFFaOMLoN1FxVvs"
SOLAR_TAB_MES  = "POR MES"
SOLAR_TAB_DIA  = "POR DIA"
SOLAR_TAB_HORA = "POR HORA"
EPM_SHEET_ID   = "1ANEtNlryqo_4wq1n6V5OlutpcDFMP_EdxxWXgjEhQ3c"
EPM_GID_MES    = "2089036315"
COSTOS_EPM     = {"CAFE": 1033, "MERCADO": 1077}
COLOR_CAFE     = "#3b82f6"
COLOR_MERC     = "#10b981"
COLOR_TOTAL    = "#8b5cf6"
COLOR_AMBAR    = "#f59e0b"
BG             = "#f8fafc"
ML = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
      7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

st.set_page_config(page_title="Dashboard Energia Solar - GEDICOL",
                   layout="wide", initial_sidebar_state="collapsed")

# ====================== CSS ======================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif!important}}
.block-container{{padding-top:.6rem;padding-bottom:2rem;background:{BG}}}
#MainMenu,.stDeployButton{{visibility:hidden}}footer{{visibility:hidden}}header{{visibility:hidden}}
.main{{background:{BG}}}
.header-wrap{{text-align:center;padding:16px 0;background:linear-gradient(135deg,{BG},#fff);border-radius:14px;margin-bottom:12px;border:1px solid #e2e8f0;box-shadow:0 2px 12px rgba(0,0,0,.04)}}
.header-wrap h1{{font-size:28px;font-weight:900;margin:0;background:linear-gradient(135deg,{COLOR_CAFE},{COLOR_MERC},{COLOR_TOTAL});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header-wrap p{{margin:6px 0 0;font-size:12px;color:#64748b;font-weight:600;letter-spacing:1.5px;text-transform:uppercase}}
.left-card{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:16px;box-shadow:0 4px 14px rgba(0,0,0,.06)}}
.left-title{{font-size:15px;font-weight:900;margin:0 0 10px;color:#0f172a}}
.fsec{{font-size:11px;font-weight:800;color:{COLOR_CAFE};text-transform:uppercase;letter-spacing:1.5px;padding:10px 0 4px;margin-top:8px;border-top:1px solid #e2e8f0}}
.small-note{{font-size:10px;color:#94a3b8;font-weight:500;line-height:1.3;background:#f1f5f9;border-radius:8px;padding:8px;margin-top:6px}}
.kpi-row{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}}
.kpi-card{{flex:1;min-width:130px;background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px 16px;box-shadow:0 4px 14px rgba(0,0,0,.05);border-left:5px solid {COLOR_TOTAL};transition:transform .2s,box-shadow .2s}}
.kpi-card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.1)}}
.kpi-card.c1{{border-left-color:{COLOR_CAFE}}}.kpi-card.c2{{border-left-color:{COLOR_MERC}}}
.kpi-card.c3{{border-left-color:{COLOR_TOTAL}}}.kpi-card.c4{{border-left-color:{COLOR_AMBAR}}}
.kpi-card.c5{{border-left-color:#ef4444}}
.kl{{font-size:10px;font-weight:900;color:#64748b;text-transform:uppercase;letter-spacing:1px}}
.kv{{font-size:22px;font-weight:900;margin-top:4px;line-height:1}}
.ks{{font-size:11px;color:#64748b;font-weight:600;margin-top:6px}}
.panel{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:18px;box-shadow:0 4px 14px rgba(0,0,0,.06);margin-bottom:14px}}
.pt{{font-size:15px;font-weight:900;color:#0f172a;margin:0 0 2px}}
.ps{{font-size:11px;color:#64748b;font-weight:600;margin:0 0 10px}}
.sg{{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}}
.sc{{flex:1;min-width:120px;text-align:center;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:14px 10px}}
.sl{{font-size:10px;font-weight:800;color:#64748b;text-transform:uppercase;letter-spacing:1px}}
.sv{{font-size:22px;font-weight:900;margin:4px 0 2px}}
.se{{font-size:10px;color:#94a3b8;font-weight:600}}
.dash-footer{{text-align:center;color:#94a3b8;font-size:11px;padding:14px;background:#fff;border:1px solid #e2e8f0;border-radius:12px;margin-top:16px}}
div[data-baseweb="select"]>div{{border-radius:10px!important}}
</style>""", unsafe_allow_html=True)

# ====================== HELPERS ======================
PLT = dict(paper_bgcolor="rgba(255,255,255,0)", plot_bgcolor="rgba(255,255,255,0)",
           font=dict(family="Inter,sans-serif", color="#0f172a", size=12),
           margin=dict(l=50,r=30,t=50,b=50),
           legend=dict(bgcolor="rgba(255,255,255,.95)", bordercolor="#e2e8f0",
                       borderwidth=1, font=dict(size=11)))
def aplyt(fig, h=420):
    fig.update_layout(**PLT, height=h)
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    return fig

def sf(x):
    try:
        v=float(x); return 0.0 if np.isnan(v) or np.isinf(v) else v
    except: return 0.0
def fn(x,d=0):
    s=f"{sf(x):,.{d}f}".replace(",","X").replace(".",",").replace("X",".")
    return s.split(",")[0] if d==0 else s
def fc(x):
    return f"${sf(x):,.0f}".replace(",","X").replace(".",",").replace("X",".")
def mlbl(y,m): return f"{ML.get(int(m),str(m))} {int(y)}"
def dlbl(dt): return f"{dt.day} {ML.get(dt.month,str(dt.month))} {dt.year}"
def tis(val):
    try: return int(float(str(val).strip()))
    except: return 0
def parse_h(x):
    if pd.isna(x): return np.nan
    m=re.match(r"(\d+)",str(x).strip())
    return int(m.group(1)) if m else np.nan

# ====================== GOOGLE SHEETS ======================
def read_gid(sid,gid):
    r=requests.get(f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}",timeout=30)
    if r.status_code!=200: raise RuntimeError(f"Sheet gid={gid} status={r.status_code}")
    return pd.read_csv(StringIO(r.text))
def read_tab(sid,tab):
    r=requests.get(f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={requests.utils.quote(tab)}",timeout=30)
    if r.status_code!=200: raise RuntimeError(f"Sheet tab={tab} status={r.status_code}")
    return pd.read_csv(StringIO(r.text))
def cc(df):
    df.columns=[str(c).strip().lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u") for c in df.columns]
    return df

@st.cache_data(ttl=300)
def cargar():
    # --- SOLAR ---
    ms=cc(read_tab(SOLAR_SHEET_ID,SOLAR_TAB_MES))
    di=cc(read_tab(SOLAR_SHEET_ID,SOLAR_TAB_DIA))
    hr=cc(read_tab(SOLAR_SHEET_ID,SOLAR_TAB_HORA))
    for d in [ms,di,hr]:
        for old in ["año","ano"]:
            if old in d.columns and "anio" not in d.columns: d["anio"]=d[old]
    ms["planta"]=ms["planta"].astype(str).str.strip().str.upper()
    ms["anio"]=ms["anio"].apply(tis); ms["mes"]=ms["mes"].apply(tis)
    ms["energia_kwh"]=pd.to_numeric(ms["energia_kwh"],errors="coerce").fillna(0.0)
    di["planta"]=di["planta"].astype(str).str.strip().str.upper()
    di["energia_kwh"]=pd.to_numeric(di["energia_kwh"],errors="coerce").fillna(0.0)
    di["fecha"]=pd.to_datetime(di["fecha"],errors="coerce",dayfirst=True)
    hr["planta"]=hr["planta"].astype(str).str.strip().str.upper()
    hr["energia_kwh"]=pd.to_numeric(hr["energia_kwh"],errors="coerce").fillna(0.0)
    hr["fecha"]=pd.to_datetime(hr["fecha"],errors="coerce",dayfirst=True)
    hr["hora_num"]=hr["hora"].apply(parse_h)

    # --- EPM (BLINDADO) ---
    ep=cc(read_gid(EPM_SHEET_ID,EPM_GID_MES))
    for old in ["año","ano"]:
        if old in ep.columns and "anio" not in ep.columns: ep["anio"]=ep[old]
    if "planta" not in ep.columns and "sede" in ep.columns: ep["planta"]=ep["sede"]
    if "planta" in ep.columns:
        ep["planta"]=ep["planta"].astype(str).str.strip().str.upper()
    else:
        ep["planta"]="TOTAL"

    # ENCONTRAR COLUMNA kWh: intentar todas las variantes posibles
    kwh_col = None
    for c in ep.columns:
        cl = c.strip().lower()
        if cl in ["energia_kwh","energía_kwh","epm_kwh","consumo_kwh","epm (kwh)","kwh","consumo","valor"]:
            kwh_col = c; break
    if kwh_col is None:
        # Buscar cualquier columna numerica que no sea anio/mes/dia
        for c in ep.columns:
            if c not in ["anio","ano","año","mes","dia","planta","sede","tipo","fecha"]:
                test = pd.to_numeric(ep[c], errors="coerce")
                if test.sum() > 100:
                    kwh_col = c; break
    if kwh_col:
        ep["epm_kwh"] = pd.to_numeric(ep[kwh_col], errors="coerce").fillna(0.0)
    else:
        ep["epm_kwh"] = 0.0

    # Extraer metadata
    cx, ph = {}, {}
    epm_debug_info = f"EPM cols: {list(ep.columns)}, kwh_col: {kwh_col}, rows: {len(ep)}"
    if "tipo" in ep.columns:
        for _,r in ep.iterrows():
            t=str(r.get("tipo","")).lower().strip()
            p=str(r.get("planta","")).strip().upper()
            v=sf(r.get("epm_kwh",0))
            if p in ["CAFE","MERCADO"]:
                if "valor" in t or "costo" in t: cx[p]=v
                if "promedio" in t or "historico" in t: ph[p]=v
        ep=ep[ep["tipo"].astype(str).str.lower().str.contains("consumo",na=False)].copy()
    epm_debug_info += f", after_filter: {len(ep)}"

    # FORZAR tipos int
    ep["anio"]=ep["anio"].apply(tis)
    ep["mes"]=ep["mes"].apply(tis)
    ep["epm_kwh"]=pd.to_numeric(ep["epm_kwh"],errors="coerce").fillna(0.0)
    ep=ep[ep["mes"].between(1,12)].copy()
    epm_debug_info += f", final: {len(ep)}, sum: {ep['epm_kwh'].sum()}"

    return ms, di, hr, ep, cx, ph, epm_debug_info

# ====================== HEADER ======================
st.markdown("""
<div class="header-wrap">
  <h1>Dashboard Energia Solar - GEDICOL</h1>
  <p>Monitoreo en tiempo real &middot; Plantas CAFE &amp; MERCADO</p>
</div>""", unsafe_allow_html=True)

# ====================== LOAD ======================
try:
    ms_df, di_df, hr_df, ep_df, cx, ph, epm_debug = cargar()
    for k,v in cx.items():
        if v>0: COSTOS_EPM[k]=v
except Exception as e:
    st.error(f"Error leyendo Google Sheets.\n\n{e}\n\n{traceback.format_exc()}")
    st.stop()

di_df=di_df.dropna(subset=["fecha"])
hr_df=hr_df.dropna(subset=["fecha","hora_num"])

ya=sorted(set(ms_df["anio"].unique())|set(ep_df["anio"].unique()))
ma=sorted(set(ms_df["mes"].unique())|set(ep_df["mes"].unique()))
pa=sorted(set(ms_df["planta"].unique())|{"CAFE","MERCADO"})
min_f=di_df["fecha"].min().date() if not di_df.empty else datetime.today().date()
max_f=di_df["fecha"].max().date() if not di_df.empty else datetime.today().date()

# ====================== FILTROS ======================
col_f,col_m=st.columns([1.1,3.2],gap="large")

with col_f:
    st.markdown('<div class="left-card">',unsafe_allow_html=True)
    st.markdown('<div class="left-title">Filtros</div>',unsafe_allow_html=True)
    if st.button("Actualizar datos",use_container_width=True):
        st.cache_data.clear(); st.rerun()

    st.markdown('<div class="fsec">VISTA</div>',unsafe_allow_html=True)
    vista=st.selectbox("v",["Mensual (Solar vs EPM)","Diario (Solar)","Hora (Solar)"],label_visibility="collapsed")

    st.markdown('<div class="fsec">PLANTAS</div>',unsafe_allow_html=True)
    all_pl=st.checkbox("Seleccionar todas",value=True,key="all_pl")
    sel_pl=pa if all_pl else st.multiselect("p",pa,default=["CAFE","MERCADO"],label_visibility="collapsed")

    st.markdown('<div class="fsec">ANIOS</div>',unsafe_allow_html=True)
    all_yr=st.checkbox("Seleccionar todos",value=True,key="all_yr")
    sel_yr=ya if all_yr else st.multiselect("y",ya,default=ya,label_visibility="collapsed")

    st.markdown('<div class="fsec">MESES</div>',unsafe_allow_html=True)
    all_ms=st.checkbox("Seleccionar todos",value=True,key="all_ms")
    sel_ms=ma if all_ms else st.multiselect("m",ma,default=ma,format_func=lambda x:ML.get(x,str(x)),label_visibility="collapsed")

    st.markdown('<div class="fsec">RANGO FECHAS</div>',unsafe_allow_html=True)
    fr=st.date_input("f",value=(min_f,max_f),min_value=min_f,max_value=max_f,label_visibility="collapsed")

    st.markdown('<div class="fsec">RANGO HORARIO</div>',unsafe_allow_html=True)
    h_min,h_max=st.select_slider("h",options=list(range(24)),value=(0,23),
        format_func=lambda x:f"{x:02d}:00",label_visibility="collapsed")

    st.markdown('<div class="fsec">COSTOS kWh</div>',unsafe_allow_html=True)
    st.markdown(f"**CAFE:** ${COSTOS_EPM['CAFE']:,}/kWh  \n**MERCADO:** ${COSTOS_EPM['MERCADO']:,}/kWh".replace(",","."))
    if ph:
        st.markdown('<div class="fsec">PROM. HISTORICO EPM</div>',unsafe_allow_html=True)
        for p,v in ph.items(): st.markdown(f"**{p}:** {fn(v)} kWh/mes")

    st.markdown(f'<div class="small-note">Datos: Google Sheets<br>Carga: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>',unsafe_allow_html=True)

    # Debug EPM (colapsado)
    with st.expander("Info tecnica EPM"):
        st.caption(epm_debug)
        if not ep_df.empty:
            st.dataframe(ep_df[["anio","mes","planta","epm_kwh"]].head(20), hide_index=True, height=200)
        else:
            st.warning("EPM vacio despues de filtros")

    st.markdown("</div>",unsafe_allow_html=True)

if not sel_pl: sel_pl=["CAFE","MERCADO"]
if not sel_yr: sel_yr=ya
if not sel_ms: sel_ms=ma
fi,ff=(fr if isinstance(fr,tuple) and len(fr)==2 else (min_f,max_f))

# ====================== FILTRADO ======================
mf=ms_df[ms_df["planta"].isin(sel_pl)&ms_df["anio"].isin(sel_yr)&ms_df["mes"].isin(sel_ms)].copy()
dff=di_df[di_df["planta"].isin(sel_pl)&(di_df["fecha"].dt.date>=fi)&(di_df["fecha"].dt.date<=ff)].copy()
hf=hr_df[hr_df["planta"].isin(sel_pl)&(hr_df["fecha"].dt.date>=fi)&(hr_df["fecha"].dt.date<=ff)&(hr_df["hora_num"]>=h_min)&(hr_df["hora_num"]<=h_max)].copy()
ef=ep_df[ep_df["anio"].isin(sel_yr)&ep_df["mes"].isin(sel_ms)].copy()

# ====================== CONTENIDO ======================
with col_m:

    # =====================================================
    #  MENSUAL
    # =====================================================
    if vista.startswith("Mensual"):
        # KPIs MENSUALES
        gc=mf[mf["planta"]=="CAFE"]["energia_kwh"].sum()
        gm=mf[mf["planta"]=="MERCADO"]["energia_kwh"].sum()
        gt_=gc+gm
        et_=ef["epm_kwh"].sum()
        ec_=ef[ef["planta"]=="CAFE"]["epm_kwh"].sum()
        em_=ef[ef["planta"]=="MERCADO"]["epm_kwh"].sum()
        ac_=gc*COSTOS_EPM["CAFE"]; am_=gm*COSTOS_EPM["MERCADO"]; at_=ac_+am_
        cp_=(gt_/et_*100) if et_>0 else 0

        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi-card c3"><div class="kl">Solar Total</div>
            <div class="kv" style="color:{COLOR_TOTAL}">{fn(gt_,1)} kWh</div></div>
          <div class="kpi-card c5"><div class="kl">EPM Total</div>
            <div class="kv" style="color:#ef4444">{fn(et_)} kWh</div></div>
          <div class="kpi-card c4"><div class="kl">Ahorro Total</div>
            <div class="kv" style="color:{COLOR_AMBAR}">{fc(at_)}</div></div>
          <div class="kpi-card c1"><div class="kl">Cobertura</div>
            <div class="kv" style="color:{COLOR_CAFE}">{fn(cp_,1)}%</div>
            <div class="ks">Solar / EPM</div></div>
        </div>""",unsafe_allow_html=True)

        st.markdown("## Mensual: Solar vs EPM")

        # Solar pivot
        sp=mf.groupby(["anio","mes","planta"],as_index=False)["energia_kwh"].sum()
        sp=sp.pivot_table(index=["anio","mes"],columns="planta",values="energia_kwh",aggfunc="sum",fill_value=0).reset_index()
        for c in ["CAFE","MERCADO"]:
            if c not in sp.columns: sp[c]=0.0
        sp["SOL_T"]=sp["CAFE"]+sp["MERCADO"]

        # EPM pivot
        epp=ef.pivot_table(index=["anio","mes"],columns="planta",values="epm_kwh",aggfunc="sum",fill_value=0).reset_index()
        for c in ["CAFE","MERCADO"]:
            if c not in epp.columns: epp[c]=0.0
        epp["EPM_T"]=epp["CAFE"]+epp["MERCADO"]
        epp=epp.rename(columns={"CAFE":"EC","MERCADO":"EM"})

        # Merge OUTER
        b=pd.merge(sp,epp,on=["anio","mes"],how="outer")
        for c in ["CAFE","MERCADO","SOL_T","EC","EM","EPM_T"]:
            if c not in b.columns: b[c]=0.0
            b[c]=b[c].fillna(0.0)
        b["anio"]=b["anio"].apply(tis); b["mes"]=b["mes"].apply(tis)
        b=b.sort_values(["anio","mes"]).reset_index(drop=True)
        b["Mes"]=b.apply(lambda r:mlbl(r["anio"],r["mes"]),axis=1)
        b["Cob"]=b.apply(lambda r:(r["SOL_T"]/r["EPM_T"]*100) if r["EPM_T"]>0 else 0,axis=1)
        b["Ahorro"]=b["CAFE"]*COSTOS_EPM["CAFE"]+b["MERCADO"]*COSTOS_EPM["MERCADO"]

        # GRAFICO
        st.markdown('<div class="panel"><div class="pt">Generacion Solar vs Consumo EPM</div>',unsafe_allow_html=True)
        st.markdown('<div class="ps">Barras solidas: Solar | Barras con patron: EPM | Linea: % cobertura | Punteadas: promedios por planta</div>',unsafe_allow_html=True)
        fig=make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(go.Bar(name="Solar CAFE",x=b["Mes"],y=b["CAFE"],marker_color=COLOR_CAFE,offsetgroup="solar",
            text=b["CAFE"].apply(lambda v:fn(v) if v>0 else ""),textposition="inside",textfont=dict(size=10,color="white")))
        fig.add_trace(go.Bar(name="Solar MERCADO",x=b["Mes"],y=b["MERCADO"],marker_color=COLOR_MERC,offsetgroup="solar",
            text=b["MERCADO"].apply(lambda v:fn(v) if v>0 else ""),textposition="inside",textfont=dict(size=10,color="white")))
        fig.add_trace(go.Bar(name="EPM CAFE",x=b["Mes"],y=b["EC"],marker_color=COLOR_CAFE,
            marker_line=dict(width=2,color=COLOR_CAFE),marker_pattern_shape="/",opacity=.5,offsetgroup="epm",
            text=b["EC"].apply(lambda v:fn(v) if v>0 else ""),textposition="inside",textfont=dict(size=9,color="#1e293b")))
        fig.add_trace(go.Bar(name="EPM MERCADO",x=b["Mes"],y=b["EM"],marker_color=COLOR_MERC,
            marker_line=dict(width=2,color=COLOR_MERC),marker_pattern_shape="/",opacity=.5,offsetgroup="epm",
            text=b["EM"].apply(lambda v:fn(v) if v>0 else ""),textposition="inside",textfont=dict(size=9,color="#1e293b")))
        fig.add_trace(go.Scatter(name="% Cobertura",x=b["Mes"],y=b["Cob"],mode="lines+markers+text",
            line=dict(color=COLOR_AMBAR,width=3),marker=dict(size=10,color=COLOR_AMBAR,line=dict(width=2,color="white")),
            text=b["Cob"].apply(lambda v:f"{v:.0f}%"),textposition="top center",textfont=dict(size=11,color=COLOR_AMBAR)),secondary_y=True)
        # Promedios por planta
        sc=b[b["CAFE"]>0]; sm=b[b["MERCADO"]>0]
        avc=sf(sc["CAFE"].mean()) if not sc.empty else 0
        avm=sf(sm["MERCADO"].mean()) if not sm.empty else 0
        if avc>0:
            fig.add_hline(y=avc,line_dash="dot",line_color=COLOR_CAFE,line_width=2,
                annotation_text=f"Prom CAFE: {fn(avc)} kWh",annotation_position="top left",
                annotation_font=dict(size=10,color=COLOR_CAFE))
        if avm>0:
            fig.add_hline(y=avm,line_dash="dash",line_color=COLOR_MERC,line_width=2,
                annotation_text=f"Prom MERCADO: {fn(avm)} kWh",annotation_position="bottom right",
                annotation_font=dict(size=10,color=COLOR_MERC))
        mc=b["Cob"].max()
        fig.update_layout(barmode="stack",bargroupgap=.12,bargap=.25,
            yaxis_title="Energia (kWh)",yaxis2_title="Cobertura (%)",
            yaxis2=dict(range=[0,max(mc*1.3,100) if mc>0 else 100],showgrid=False))
        fig=aplyt(fig,500)
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('</div>',unsafe_allow_html=True)

        # Tortas + Ahorro
        c1,c2,c3=st.columns(3)
        with c1:
            st.markdown('<div class="panel"><div class="pt">Solar por Planta</div>',unsafe_allow_html=True)
            fp=go.Figure(go.Pie(labels=["CAFE","MERCADO"],values=[sf(gc),sf(gm)],hole=.55,
                marker=dict(colors=[COLOR_CAFE,COLOR_MERC],line=dict(color="white",width=3)),
                textinfo="label+percent",textfont=dict(size=11)))
            fp.add_annotation(text=f"<b>{fn(gt_)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                x=.5,y=.5,showarrow=False,font=dict(size=16,color="#0f172a"))
            fp.update_layout(paper_bgcolor="rgba(0,0,0,0)",showlegend=False,height=260,margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fp,use_container_width=True)
            st.markdown('</div>',unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel"><div class="pt">EPM por Planta</div>',unsafe_allow_html=True)
            fp2=go.Figure(go.Pie(labels=["CAFE","MERCADO"],values=[sf(ec_),sf(em_)],hole=.55,
                marker=dict(colors=[COLOR_CAFE,COLOR_MERC],line=dict(color="white",width=3)),
                textinfo="label+percent",textfont=dict(size=11)))
            fp2.add_annotation(text=f"<b>{fn(et_)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                x=.5,y=.5,showarrow=False,font=dict(size=16,color="#0f172a"))
            fp2.update_layout(paper_bgcolor="rgba(0,0,0,0)",showlegend=False,height=260,margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fp2,use_container_width=True)
            st.markdown('</div>',unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="panel"><div class="pt">Ahorro por Mes</div>',unsafe_allow_html=True)
            fa=go.Figure(go.Bar(x=b["Mes"],y=b["Ahorro"],marker_color=COLOR_AMBAR,
                text=b["Ahorro"].apply(lambda v:fc(v) if v>0 else ""),textposition="outside",textfont=dict(size=9,color=COLOR_AMBAR)))
            fa.update_layout(showlegend=False,yaxis_title="$COP")
            fa=aplyt(fa,260)
            st.plotly_chart(fa,use_container_width=True)
            st.markdown('</div>',unsafe_allow_html=True)

        # Tendencia
        st.markdown('<div class="panel"><div class="pt">Tendencia Mensual</div>',unsafe_allow_html=True)
        ft=go.Figure()
        ft.add_trace(go.Scatter(name="EPM Total",x=b["Mes"],y=b["EPM_T"],mode="lines+markers",
            line=dict(color="#ef4444",width=2.5),marker=dict(size=8,color="#ef4444",line=dict(width=2,color="white")),
            fill="tozeroy",fillcolor="rgba(239,68,68,.06)"))
        ft.add_trace(go.Scatter(name="Solar Total",x=b["Mes"],y=b["SOL_T"],mode="lines+markers",
            line=dict(color=COLOR_TOTAL,width=3),marker=dict(size=9,color=COLOR_TOTAL,line=dict(width=2,color="white")),
            fill="tozeroy",fillcolor="rgba(139,92,246,.08)"))
        ft.update_layout(yaxis_title="Energia (kWh)")
        ft=aplyt(ft,350)
        st.plotly_chart(ft,use_container_width=True)
        st.markdown('</div>',unsafe_allow_html=True)

        # TABLA
        st.markdown('<div class="panel"><div class="pt">Tabla Resumen Mensual</div>',unsafe_allow_html=True)
        tbl=pd.DataFrame({"Mes":b["Mes"],"Solar CAFE":b["CAFE"].round(1),"Solar MERCADO":b["MERCADO"].round(1),
            "Solar TOTAL":b["SOL_T"].round(1),"EPM CAFE":b["EC"].round(0).astype(int),
            "EPM MERCADO":b["EM"].round(0).astype(int),"EPM TOTAL":b["EPM_T"].round(0).astype(int),
            "Cobertura %":b["Cob"].round(1),"Ahorro COP":b["Ahorro"].round(0).astype(int)})
        st.dataframe(tbl,use_container_width=True,hide_index=True,
            column_config={
                "Solar CAFE":st.column_config.NumberColumn(format="%.1f kWh"),
                "Solar MERCADO":st.column_config.NumberColumn(format="%.1f kWh"),
                "Solar TOTAL":st.column_config.NumberColumn(format="%.1f kWh"),
                "EPM CAFE":st.column_config.NumberColumn(format="%d kWh"),
                "EPM MERCADO":st.column_config.NumberColumn(format="%d kWh"),
                "EPM TOTAL":st.column_config.NumberColumn(format="%d kWh"),
                "Cobertura %":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.1f%%"),
                "Ahorro COP":st.column_config.NumberColumn(format="$%d"),
            })
        st.markdown('</div>',unsafe_allow_html=True)


    # =====================================================
    #  DIARIO
    # =====================================================
    elif vista.startswith("Diario"):
        # KPIs DIARIOS
        da_=dff.groupby(["fecha","planta"],as_index=False)["energia_kwh"].sum()
        dt_=dff.groupby("fecha",as_index=False)["energia_kwh"].sum()
        pc_=da_[(da_["planta"]=="CAFE")&(da_["energia_kwh"]>0)]
        pm_=da_[(da_["planta"]=="MERCADO")&(da_["energia_kwh"]>0)]
        avc=sf(pc_["energia_kwh"].mean()) if not pc_.empty else 0
        avm=sf(pm_["energia_kwh"].mean()) if not pm_.empty else 0
        dt_pos=dt_[dt_["energia_kwh"]>0]
        avt=sf(dt_pos["energia_kwh"].mean()) if not dt_pos.empty else 0
        dias=len(dt_pos)
        gtd=dff["energia_kwh"].sum()
        ahd=da_[da_["planta"]=="CAFE"]["energia_kwh"].sum()*COSTOS_EPM["CAFE"]+da_[da_["planta"]=="MERCADO"]["energia_kwh"].sum()*COSTOS_EPM["MERCADO"]
        mx=dt_.loc[dt_["energia_kwh"].idxmax()] if not dt_.empty else None
        bv=fn(mx["energia_kwh"]) if mx is not None else "-"
        bd=dlbl(mx["fecha"]) if mx is not None else ""

        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi-card c1"><div class="kl">Prom CAFE/dia</div>
            <div class="kv" style="color:{COLOR_CAFE}">{fn(avc,1)} kWh</div></div>
          <div class="kpi-card c2"><div class="kl">Prom MERCADO/dia</div>
            <div class="kv" style="color:{COLOR_MERC}">{fn(avm,1)} kWh</div></div>
          <div class="kpi-card c3"><div class="kl">Total Periodo</div>
            <div class="kv" style="color:{COLOR_TOTAL}">{fn(gtd,1)} kWh</div>
            <div class="ks">{dias} dias activos</div></div>
          <div class="kpi-card c4"><div class="kl">Ahorro Periodo</div>
            <div class="kv" style="color:{COLOR_AMBAR}">{fc(ahd)}</div></div>
          <div class="kpi-card c5"><div class="kl">Mejor Dia</div>
            <div class="kv" style="color:#ef4444">{bv} kWh</div>
            <div class="ks">{bd}</div></div>
        </div>""",unsafe_allow_html=True)

        st.markdown("## Diario: Generacion Solar")
        if dff.empty:
            st.warning("No hay datos diarios.")
        else:
            st.markdown('<div class="panel"><div class="pt">Evolucion Diaria</div>',unsafe_allow_html=True)
            st.markdown('<div class="ps">Por planta | Punteadas: promedios individuales</div>',unsafe_allow_html=True)
            fd=go.Figure()
            for pl in sel_pl:
                d=da_[da_["planta"]==pl].sort_values("fecha")
                if d.empty: continue
                c=COLOR_CAFE if pl=="CAFE" else COLOR_MERC
                fd.add_trace(go.Scatter(name=pl,x=d["fecha"],y=d["energia_kwh"],mode="lines+markers",
                    line=dict(color=c,width=2),marker=dict(size=4,color=c),fill="tozeroy",
                    fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},.08)",
                    customdata=d["fecha"].apply(dlbl),hovertemplate="<b>%{customdata}</b><br>%{y:.1f} kWh<extra></extra>"))
            if avc>0 and "CAFE" in sel_pl:
                fd.add_hline(y=avc,line_dash="dot",line_color=COLOR_CAFE,line_width=2,
                    annotation_text=f"Prom CAFE: {fn(avc,1)} kWh/dia",annotation_position="top left",
                    annotation_font=dict(size=10,color=COLOR_CAFE))
            if avm>0 and "MERCADO" in sel_pl:
                fd.add_hline(y=avm,line_dash="dash",line_color=COLOR_MERC,line_width=2,
                    annotation_text=f"Prom MERCADO: {fn(avm,1)} kWh/dia",annotation_position="bottom right",
                    annotation_font=dict(size=10,color=COLOR_MERC))
            fd.update_layout(yaxis_title="Energia (kWh)",xaxis_title="Fecha")
            fd=aplyt(fd,460)
            st.plotly_chart(fd,use_container_width=True)
            st.markdown('</div>',unsafe_allow_html=True)

            c1,c2,c3=st.columns([1,1,1.5])
            with c1:
                st.markdown('<div class="panel"><div class="pt">Distribucion por Planta</div>',unsafe_allow_html=True)
                ddc=da_[da_["planta"]=="CAFE"]["energia_kwh"].sum()
                ddm=da_[da_["planta"]=="MERCADO"]["energia_kwh"].sum()
                fp=go.Figure(go.Pie(labels=["CAFE","MERCADO"],values=[sf(ddc),sf(ddm)],hole=.55,
                    marker=dict(colors=[COLOR_CAFE,COLOR_MERC],line=dict(color="white",width=3)),
                    textinfo="label+percent",textfont=dict(size=11)))
                fp.add_annotation(text=f"<b>{fn(ddc+ddm)}</b><br><span style='font-size:9px;color:#64748b'>kWh</span>",
                    x=.5,y=.5,showarrow=False,font=dict(size=16,color="#0f172a"))
                fp.update_layout(paper_bgcolor="rgba(0,0,0,0)",showlegend=False,height=300,margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fp,use_container_width=True)
                st.markdown('</div>',unsafe_allow_html=True)
            with c2:
                sd=sf(dt_pos["energia_kwh"].std()) if not dt_pos.empty else 0
                st.markdown(f"""
                <div class="panel"><div class="pt">Resumen Estadistico</div>
                <div class="sg" style="flex-direction:column">
                  <div class="sc"><div class="sl">Prom Total</div>
                    <div class="sv" style="color:{COLOR_TOTAL};font-size:20px">{fn(avt,1)} kWh/dia</div></div>
                  <div class="sc"><div class="sl">Desv. Estandar</div>
                    <div class="sv" style="color:#64748b;font-size:20px">{fn(sd,1)} kWh</div></div>
                  <div class="sc"><div class="sl">Dias Activos</div>
                    <div class="sv" style="color:{COLOR_AMBAR};font-size:20px">{dias}</div></div>
                </div></div>""",unsafe_allow_html=True)
            with c3:
                st.markdown('<div class="panel"><div class="pt">Promedio por Dia de Semana</div>',unsafe_allow_html=True)
                dw=dff.copy(); dw["dow"]=dw["fecha"].dt.dayofweek
                dn=["Lun","Mar","Mie","Jue","Vie","Sab","Dom"]
                dwa=dw.groupby(["dow","planta"],as_index=False)["energia_kwh"].mean()
                fdw=go.Figure()
                for pl in sel_pl:
                    d=dwa[dwa["planta"]==pl].sort_values("dow")
                    if d.empty: continue
                    c=COLOR_CAFE if pl=="CAFE" else COLOR_MERC
                    fdw.add_trace(go.Bar(name=pl,x=[dn[int(i)] for i in d["dow"]],y=d["energia_kwh"],
                        marker_color=c,text=d["energia_kwh"].apply(lambda v:fn(v,1)),textposition="outside",textfont=dict(size=9)))
                fdw.update_layout(barmode="group",yaxis_title="Prom kWh/dia")
                fdw=aplyt(fdw,300)
                st.plotly_chart(fdw,use_container_width=True)
                st.markdown('</div>',unsafe_allow_html=True)

            st.markdown('<div class="panel"><div class="pt">Tabla Resumen Diario</div>',unsafe_allow_html=True)
            pv=da_.pivot_table(index="fecha",columns="planta",values="energia_kwh",fill_value=0).reset_index()
            for c in ["CAFE","MERCADO"]:
                if c not in pv.columns: pv[c]=0.0
            pv["TOTAL"]=pv["CAFE"]+pv["MERCADO"]
            pv=pv.sort_values("fecha")
            pv["Fecha"]=pv["fecha"].apply(dlbl)
            pv["Ahorro"]=(pv["CAFE"]*COSTOS_EPM["CAFE"]+pv["MERCADO"]*COSTOS_EPM["MERCADO"]).round(0).astype(int)
            out=pv[["Fecha","CAFE","MERCADO","TOTAL","Ahorro"]].rename(columns={"CAFE":"Solar CAFE","MERCADO":"Solar MERCADO","TOTAL":"Solar TOTAL","Ahorro":"Ahorro COP"})
            out["Solar CAFE"]=out["Solar CAFE"].round(1); out["Solar MERCADO"]=out["Solar MERCADO"].round(1); out["Solar TOTAL"]=out["Solar TOTAL"].round(1)
            mxt=float(out["Solar TOTAL"].max()) if out["Solar TOTAL"].max()>0 else 100
            st.dataframe(out,use_container_width=True,hide_index=True,height=400,
                column_config={
                    "Solar CAFE":st.column_config.NumberColumn(format="%.1f kWh"),
                    "Solar MERCADO":st.column_config.NumberColumn(format="%.1f kWh"),
                    "Solar TOTAL":st.column_config.ProgressColumn(min_value=0,max_value=mxt*1.1,format="%.1f kWh"),
                    "Ahorro COP":st.column_config.NumberColumn(format="$%d"),
                })
            st.markdown('</div>',unsafe_allow_html=True)


    # =====================================================
    #  HORA
    # =====================================================
    else:
        # KPIs HORARIOS
        hp=hf.groupby(["hora_num","planta"],as_index=False)["energia_kwh"].mean()
        hp["hora_num"]=hp["hora_num"].astype(int)
        thp=hp.groupby("hora_num")["energia_kwh"].sum()
        pkh=int(thp.idxmax()) if not thp.empty else 0
        pkv=sf(thp.max())
        prod=hp[hp["energia_kwh"]>.5]["hora_num"].nunique()
        avhc=sf(hp[(hp["planta"]=="CAFE")&(hp["energia_kwh"]>.5)]["energia_kwh"].mean())
        avhm=sf(hp[(hp["planta"]=="MERCADO")&(hp["energia_kwh"]>.5)]["energia_kwh"].mean())
        ghf=hf["energia_kwh"].sum()

        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi-card c4"><div class="kl">Hora Pico</div>
            <div class="kv" style="color:{COLOR_AMBAR}">{pkh:02d}:00</div>
            <div class="ks">{fn(pkv,1)} kWh prom</div></div>
          <div class="kpi-card c2"><div class="kl">Horas Productivas</div>
            <div class="kv" style="color:{COLOR_MERC}">{prod}</div>
            <div class="ks">horas con +0.5 kWh</div></div>
          <div class="kpi-card c1"><div class="kl">Prom CAFE/hora</div>
            <div class="kv" style="color:{COLOR_CAFE}">{fn(avhc,2)} kWh</div></div>
          <div class="kpi-card c2"><div class="kl">Prom MERCADO/hora</div>
            <div class="kv" style="color:{COLOR_MERC}">{fn(avhm,2)} kWh</div></div>
          <div class="kpi-card c3"><div class="kl">Total Generado</div>
            <div class="kv" style="color:{COLOR_TOTAL}">{fn(ghf,1)} kWh</div></div>
        </div>""",unsafe_allow_html=True)

        st.markdown("## Hora: Generacion Solar")
        if hf.empty:
            st.warning("No hay datos horarios.")
        else:
            st.markdown('<div class="panel"><div class="pt">Patron de Generacion Solar por Hora</div>',unsafe_allow_html=True)
            st.markdown('<div class="ps">Curva promedio por planta | Punteadas: promedios por planta | Zona solar 6h-18h</div>',unsafe_allow_html=True)
            fh=go.Figure()
            for pl in sel_pl:
                d=hp[hp["planta"]==pl].sort_values("hora_num")
                if d.empty: continue
                c=COLOR_CAFE if pl=="CAFE" else COLOR_MERC
                fh.add_trace(go.Scatter(name=f"Solar {pl}",x=d["hora_num"],y=d["energia_kwh"],
                    mode="lines+markers+text",line=dict(color=c,width=3,shape="spline"),
                    marker=dict(size=8,color=c,line=dict(width=2,color="white")),fill="tozeroy",
                    fillcolor=f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},.1)",
                    text=d["energia_kwh"].apply(lambda v:f"{v:.1f}" if v>.5 else ""),
                    textposition="top center",textfont=dict(size=9,color="#0f172a")))
            fh.add_vrect(x0=6,x1=18,fillcolor="rgba(245,158,11,.04)",line_width=0,
                annotation_text="Horas solares",annotation_position="top left",
                annotation_font=dict(size=10,color=COLOR_AMBAR))
            for pl in sel_pl:
                hpg=hp[(hp["planta"]==pl)&(hp["energia_kwh"]>.5)]
                av=sf(hpg["energia_kwh"].mean()) if not hpg.empty else 0
                if av>0:
                    c=COLOR_CAFE if pl=="CAFE" else COLOR_MERC
                    ds="dot" if pl=="CAFE" else "dash"
                    ps="top left" if pl=="CAFE" else "bottom right"
                    fh.add_hline(y=av,line_dash=ds,line_color=c,line_width=2,
                        annotation_text=f"Prom {pl}: {av:.2f} kWh/h",annotation_position=ps,
                        annotation_font=dict(size=10,color=c))
            fh.update_layout(xaxis=dict(tickmode="array",tickvals=list(range(h_min,h_max+1)),
                ticktext=[f"{h:02d}:00" for h in range(h_min,h_max+1)],title="Hora"),yaxis_title="kWh promedio")
            fh=aplyt(fh,460)
            st.plotly_chart(fh,use_container_width=True)
            st.markdown('</div>',unsafe_allow_html=True)

            c1,c2=st.columns([1,1.5])
            with c1:
                st.markdown('<div class="panel"><div class="pt">Pico vs Fuera de Pico</div>',unsafe_allow_html=True)
                hpt=hp.groupby("hora_num")["energia_kwh"].sum().reset_index()
                pk=sf(hpt[(hpt["hora_num"]>=9)&(hpt["hora_num"]<=15)]["energia_kwh"].sum())
                np_=sf(hpt[~((hpt["hora_num"]>=9)&(hpt["hora_num"]<=15))]["energia_kwh"].sum())
                fpp=go.Figure(go.Pie(labels=["Pico (9-15h)","Fuera de pico"],values=[pk,np_],hole=.55,
                    marker=dict(colors=[COLOR_AMBAR,"#e2e8f0"],line=dict(color="white",width=3)),
                    textinfo="label+percent",textfont=dict(size=11)))
                fpp.update_layout(paper_bgcolor="rgba(0,0,0,0)",showlegend=False,height=280,margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fpp,use_container_width=True)
                st.markdown('</div>',unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="panel"><div class="pt">Heatmap: Generacion por Hora y Fecha</div>',unsafe_allow_html=True)
                hm=hf.groupby(["fecha","hora_num"],as_index=False)["energia_kwh"].sum()
                hm["fs"]=hm["fecha"].apply(dlbl)
                hmv=hm.pivot_table(index="hora_num",columns="fs",values="energia_kwh",fill_value=0).sort_index()
                if hmv.shape[1]>45: hmv=hmv.iloc[:,-45:]
                fhm=go.Figure(go.Heatmap(z=hmv.values,x=hmv.columns.tolist(),
                    y=[f"{int(h):02d}:00" for h in hmv.index],
                    colorscale=[[0,"#f8fafc"],[.15,"#dbeafe"],[.4,COLOR_CAFE],[.7,COLOR_MERC],[1,COLOR_AMBAR]],
                    hovertemplate="Fecha: %{x}<br>Hora: %{y}<br>kWh: %{z:.1f}<extra></extra>",
                    colorbar=dict(title=dict(text="kWh",font=dict(size=11)),tickfont=dict(size=10))))
                fhm.update_layout(xaxis_title="Fecha",yaxis_title="Hora",yaxis=dict(autorange="reversed"))
                fhm=aplyt(fhm,460)
                st.plotly_chart(fhm,use_container_width=True)
                st.markdown('</div>',unsafe_allow_html=True)

            st.markdown('<div class="panel"><div class="pt">Tabla Resumen por Hora</div>',unsafe_allow_html=True)
            pvh=hp.pivot_table(index="hora_num",columns="planta",values="energia_kwh",fill_value=0).reset_index()
            for c in ["CAFE","MERCADO"]:
                if c not in pvh.columns: pvh[c]=0.0
            pvh["TOTAL"]=pvh["CAFE"]+pvh["MERCADO"]
            pvh=pvh.sort_values("hora_num")
            pvh["Hora"]=pvh["hora_num"].apply(lambda h:f"{int(h):02d}:00")
            out_h=pvh[["Hora","CAFE","MERCADO","TOTAL"]].rename(columns={"CAFE":"Solar CAFE","MERCADO":"Solar MERCADO","TOTAL":"Solar TOTAL"}).round(2)
            mxh=float(out_h["Solar TOTAL"].max()) if out_h["Solar TOTAL"].max()>0 else 1
            st.dataframe(out_h,use_container_width=True,hide_index=True,height=500,
                column_config={
                    "Solar CAFE":st.column_config.NumberColumn(format="%.2f kWh"),
                    "Solar MERCADO":st.column_config.NumberColumn(format="%.2f kWh"),
                    "Solar TOTAL":st.column_config.ProgressColumn(min_value=0,max_value=mxh*1.1,format="%.2f kWh"),
                })
            st.markdown('</div>',unsafe_allow_html=True)

st.markdown(f"""
<div class="dash-footer">
  Dashboard Energia Solar - GEDICOL | &copy; {datetime.now().year} | Datos: Google Sheets |
  <span style="color:{COLOR_CAFE}">&#9632;</span> CAFE
  <span style="color:{COLOR_MERC}">&#9632;</span> MERCADO
  <span style="color:{COLOR_TOTAL}">&#9632;</span> Total
  <span style="color:{COLOR_AMBAR}">&#9632;</span> Ahorro
</div>""",unsafe_allow_html=True)