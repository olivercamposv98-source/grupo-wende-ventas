# ============================================================
#  GRUPO WENDE — DASHBOARD DE VENTAS
#  Menú lateral: General · Venta por Marca · Venta por Tienda · Últimos 7 días
#  Estilo: fondo negro, tarjetas oscuras, acentos amarillos
# ============================================================

import calendar
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# 1) CONFIGURACIÓN
# ------------------------------------------------------------
st.set_page_config(page_title="Grupo Wende · Ventas", layout="wide", initial_sidebar_state="expanded")

C_BG, C_PANEL, C_CARD, C_BORDER = "#0A0A0C", "#111114", "#1A1A1F", "#2A2A32"
C_YELLOW, C_TEXT, C_MUTED = "#FFD400", "#F4F1E6", "#98969F"
C_GREEN, C_RED, C_GRAY = "#3DDC84", "#FF5C5C", "#3A3A42"

BRAND_COLORS = {"El Chico Fresa": "#FF3B4E", "MrBeast Burger": "#FFD400",
                "La Happy Hour": "#F2A900", "Santo Domingo": "#F5A3C7"}
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
            "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

SHEET_ID = "1pKund1DmfQzY0SGBFrk7VIKeXrqiJzl_QVmJ7roSyek"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
LOCAL_CSV = Path(__file__).parent / "data" / "ventas_diarias_raw.csv"

MENU = ["General", "Venta por Marca", "Venta por Tienda", "Últimos 7 días"]

# ------------------------------------------------------------
# 2) ESTILOS
# ------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;800&family=IBM+Plex+Sans:wght@400;600&display=swap');
html, body, [data-testid="stAppViewContainer"] {{ background:{C_BG}; color:{C_TEXT}; font-family:'IBM Plex Sans',sans-serif; }}
[data-testid="stSidebar"] {{ background:#000000; border-right:1px solid {C_BORDER}; }}
h1,h2,h3,h4 {{ font-family:'Archivo',sans-serif; }}

/* --- Menú lateral (radio disfrazado de menú) --- */
[data-testid="stSidebar"] div[role="radiogroup"] > label {{
    display:flex; align-items:center; width:100%;
    padding:11px 14px; margin:2px 0; border-radius:9px;
    border-left:3px solid transparent; cursor:pointer;
    font-weight:600; color:{C_MUTED}; transition:background .15s;
}}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{ background:{C_CARD}; }}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
    background:{C_CARD}; border-left:3px solid {C_YELLOW}; color:{C_YELLOW};
}}
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child,
[data-testid="stSidebar"] div[role="radiogroup"] > label > span:first-child,
[data-testid="stSidebar"] div[role="radiogroup"] > label input {{ display:none !important; }}
[data-testid="stSidebar"] div[role="radiogroup"] > label p {{ font-size:0.95rem; }}

/* --- Tarjetas KPI --- */
.kpi {{ background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:12px;
       padding:16px 18px 10px 18px; height:100%; }}
.kpi .lbl {{ font-size:.7rem; text-transform:uppercase; letter-spacing:.12em; color:{C_MUTED}; }}
.kpi .val {{ font-family:'Archivo'; font-size:1.9rem; font-weight:800; margin-top:2px; }}
.kpi .pos {{ color:{C_GREEN}; font-weight:600; font-size:.82rem; }}
.kpi .neg {{ color:{C_RED}; font-weight:600; font-size:.82rem; }}
.kpi .sub {{ color:{C_MUTED}; font-size:.75rem; }}

.box {{ background:{C_CARD}; border:1px solid {C_BORDER}; border-left:4px solid {C_YELLOW};
       border-radius:10px; padding:13px 16px; margin-bottom:10px; }}
.rankcard {{ background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:10px;
            padding:12px 14px; margin-bottom:8px; display:flex;
            justify-content:space-between; align-items:center; }}
.panel-title {{ font-family:'Archivo'; font-weight:800; font-size:1.05rem; margin:6px 0 10px 0; }}
div[data-testid="stDataFrame"] {{ border:1px solid {C_BORDER}; border-radius:10px; }}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# 3) DATOS
# ------------------------------------------------------------
def asignar_marca(s: str) -> str:
    s = s.upper()
    if s.startswith("CF"):
        return "El Chico Fresa"
    if "BEAST" in s:
        return "MrBeast Burger"
    if "HAPPY" in s:
        return "La Happy Hour"
    if "SANTO DOMINGO" in s:
        return "Santo Domingo"
    return "Otras"

@st.cache_data(ttl=900, show_spinner="Cargando ventas…")
def cargar_datos() -> pd.DataFrame:
    try:
        df = pd.read_csv(SHEET_URL)
        fuente = "Google Sheets (en vivo)"
    except Exception:
        df = pd.read_csv(LOCAL_CSV)
        fuente = "CSV local (respaldo)"
    df.columns = [c.strip().upper() for c in df.columns]
    df["SUCURSAL"] = df["SUCURSAL"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["VENTA"] = pd.to_numeric(df["VENTA REAL"].astype(str)
                                .str.replace("Bs", "", regex=False)
                                .str.replace(",", "", regex=False), errors="coerce")
    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["VENTA", "FECHA"])
    df["MES"] = df["FECHA"].dt.to_period("M")
    df["DIA"] = df["FECHA"].dt.day
    df["MARCA"] = df["SUCURSAL"].apply(asignar_marca)
    df.attrs["fuente"] = fuente
    return df

# --- Actualización de datos ---
# a) Al abrir o recargar la pestaña (sesión nueva): siempre datos frescos
if "_datos_frescos" not in st.session_state:
    st.cache_data.clear()
    st.session_state["_datos_frescos"] = True

df = cargar_datos()
st.session_state["_ultima_carga"] = st.session_state.get("_ultima_carga") or time.time()
fmt = lambda v: f"Bs {v:,.0f}"

# b) Mientras la pestaña esté abierta: recarga completa cada 15 minutos
@st.fragment(run_every=900)
def _auto_refresh():
    if time.time() - st.session_state.get("_ultima_carga", 0) >= 895:
        st.cache_data.clear()
        st.session_state["_ultima_carga"] = time.time()
        st.rerun(scope="app")

_auto_refresh()

def sparkline(vals, color=C_YELLOW, w=110, h=26):
    """Mini-gráfico SVG para incrustar dentro de una tarjeta KPI."""
    vals = [v for v in vals if not pd.isna(v)]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i*w/(len(vals)-1):.1f},{h-2-((v-lo)/rng)*(h-6):.1f}"
                   for i, v in enumerate(vals))
    return (f"<svg width='{w}' height='{h}'><polyline points='{pts}' fill='none' "
            f"stroke='{color}' stroke-width='2' stroke-linecap='round'/></svg>")

def kpi(col, label, value, delta=None, sub=None, spark=""):
    d = ""
    if delta is not None and not pd.isna(delta):
        cls = "pos" if delta >= 0 else "neg"
        d = f"<span class='{cls}'>{'↗' if delta >= 0 else '↘'} {delta:+.1%}</span> "
    s = f"<span class='sub'>{sub}</span>" if sub else ""
    col.markdown(f"<div class='kpi'><div class='lbl'>{label}</div>"
                 f"<div class='val'>{value}</div><div>{d}{s}</div>{spark}</div>",
                 unsafe_allow_html=True)

def plotly_base(fig, height=330, title=""):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=36 if title else 12, b=10),
                      **({"title": dict(text=title, font=dict(size=14))} if title else {}),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=C_TEXT),
                      xaxis=dict(gridcolor=C_BORDER), yaxis=dict(gridcolor=C_BORDER, tickformat=",.0f"))
    return fig

# ------------------------------------------------------------
# 4) SIDEBAR — MENÚ + FILTROS
# ------------------------------------------------------------
with st.sidebar:
    assets_dir = Path(__file__).parent / "assets"
    logo = None
    if assets_dir.exists():
        imgs = [p for p in assets_dir.iterdir()
                if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        marcas_conocidas = ("chico", "fresa", "beast", "happy", "santo", "chelato")
        preferidos = [p for p in imgs
                      if "wende" in p.name.lower() or "grupo" in p.name.lower()]
        otros = [p for p in imgs
                 if not any(m in p.name.lower() for m in marcas_conocidas)]
        if preferidos:
            logo = preferidos[0]
        elif otros:
            logo = otros[0]
    if logo:
        st.image(str(logo), width="stretch")
    st.markdown(f"<p style='color:{C_MUTED};font-size:.8rem;margin-top:-6px'>Sales Dashboard</p>",
                unsafe_allow_html=True)

    pagina = st.radio("Menú", MENU, label_visibility="collapsed")

    st.divider()
    meses = sorted(df["MES"].unique())
    n_tiendas = df["SUCURSAL"].nunique()
    cobertura = df.groupby("MES")["SUCURSAL"].nunique()
    candidatos = [m for m in meses if cobertura.get(m, 0) >= n_tiendas / 2]
    mes_default = candidatos[-1] if candidatos else meses[-1]
    etiqueta = lambda m: f"{MESES_ES[m.month]} {m.year}"

    mes_actual = st.selectbox("Mes", meses, index=meses.index(mes_default), format_func=etiqueta)
    mes_anterior = mes_actual - 1
    marcas_sel = st.multiselect("Marcas", sorted(df["MARCA"].unique()),
                                default=sorted(df["MARCA"].unique()))
    st.caption(f"Fuente: {df.attrs['fuente']}")
    st.caption(f"Último dato: {df['FECHA'].max():%d/%m/%Y}")

df_f = df[df["MARCA"].isin(marcas_sel)]
d_act = df_f[df_f["MES"] == mes_actual]
d_ant = df_f[df_f["MES"] == mes_anterior]
if d_act.empty:
    st.warning("No hay ventas para el mes y marcas seleccionadas.")
    st.stop()

# ------------------------------------------------------------
# 5) CÁLCULOS GLOBALES
# ------------------------------------------------------------
dias_mes = calendar.monthrange(mes_actual.year, mes_actual.month)[1]
dia_corte = int(d_act["DIA"].max())
dias_rest = dias_mes - dia_corte

venta_mtd = d_act["VENTA"].sum()
run_rate = venta_mtd / dia_corte * dias_mes
venta_ant = d_ant["VENTA"].sum()
venta_ant_mismo = d_ant[d_ant["DIA"] <= dia_corte]["VENTA"].sum()
prom_diario = venta_mtd / dia_corte
mom = (venta_mtd / venta_ant_mismo - 1) if venta_ant_mismo else np.nan
cumpl = (run_rate / venta_ant) if venta_ant else np.nan
ritmo_req = (venta_ant - venta_mtd) / dias_rest if dias_rest > 0 else 0

serie_diaria = d_act.groupby("DIA")["VENTA"].sum().sort_index()

# Ranking por tienda (usado en varias páginas)
g_act = d_act.groupby(["SUCURSAL", "MARCA"])["VENTA"].sum().rename("Este mes")
g_ant = d_ant.groupby("SUCURSAL")["VENTA"].sum().rename("Mes anterior")
g_ant_mismo = d_ant[d_ant["DIA"] <= dia_corte].groupby("SUCURSAL")["VENTA"].sum()
rank = g_act.reset_index().merge(g_ant.reset_index(), on="SUCURSAL", how="outer")
rank["MARCA"] = rank["MARCA"].fillna(rank["SUCURSAL"].apply(asignar_marca))
rank = rank.fillna({"Este mes": 0, "Mes anterior": 0})
rank["Proyección"] = rank["Este mes"] / dia_corte * dias_mes
rank["_mismo"] = rank["SUCURSAL"].map(g_ant_mismo).fillna(0)
rank["¿Cómo va?"] = np.where(rank["_mismo"] > 0, rank["Este mes"] / rank["_mismo"] - 1, np.nan)
rank["Estado"] = np.select(
    [rank["Mes anterior"] == 0, rank["Proyección"] >= rank["Mes anterior"]],
    ["Nueva", "Supera la meta"], default="Bajo la meta")
rank = rank.sort_values("Este mes", ascending=False).reset_index(drop=True)

def encabezado(titulo, subtitulo):
    st.markdown(f"<h1 style='margin-bottom:0'>{titulo}</h1>"
                f"<p style='color:{C_MUTED};margin-top:2px'>{subtitulo}</p>",
                unsafe_allow_html=True)

# ============================================================
# PÁGINA · GENERAL
# ============================================================
if pagina == MENU[0]:
    encabezado("Dashboard Principal",
               f"Resumen de {etiqueta(mes_actual)} · corte al día {dia_corte} · "
               f"{d_act['SUCURSAL'].nunique()} tiendas activas")

    k1, k2, k3 = st.columns(3)
    kpi(k1, "Ventas totales", fmt(venta_mtd), mom, "vs mes anterior",
        sparkline(serie_diaria.values))
    kpi(k2, "Proyección de cierre", fmt(run_rate),
        (cumpl - 1) if not pd.isna(cumpl) else None, "vs total mes anterior",
        sparkline(serie_diaria.cumsum().values))
    kpi(k3, "Venta promedio diaria", fmt(prom_diario), None,
        f"{dia_corte} días transcurridos",
        sparkline(serie_diaria.rolling(3, min_periods=1).mean().values, C_GREEN))

    st.markdown("<br>", unsafe_allow_html=True)
    if not pd.isna(cumpl):
        if cumpl >= 1:
            st.markdown(f"<div class='box' style='border-left-color:{C_GREEN}'>"
                        f"<b>Vamos bien:</b> proyección de cierre {fmt(run_rate)} "
                        f"(<b style='color:{C_GREEN}'>{cumpl-1:+.1%}</b> vs {MESES_ES[mes_anterior.month]}).</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='box' style='border-left-color:{C_RED}'>"
                        f"<b>Atención:</b> proyección {fmt(run_rate)} "
                        f"(<b style='color:{C_RED}'>{cumpl-1:+.1%}</b>). Para igualar a "
                        f"{MESES_ES[mes_anterior.month]} hay que vender <b>{fmt(max(ritmo_req,0))}/día</b> "
                        f"durante {dias_rest} días.</div>", unsafe_allow_html=True)

    c_izq, c_der = st.columns([0.63, 0.37])
    with c_izq:
        st.markdown("<div class='panel-title'>Ventas por Marca</div>", unsafe_allow_html=True)
        m_act = d_act.groupby("MARCA")["VENTA"].sum()
        m_ant = d_ant.groupby("MARCA")["VENTA"].sum()
        marcas = m_act.sort_values(ascending=False).index.tolist()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=marcas, y=[m_ant.get(m, 0) for m in marcas],
                             name="Mes anterior", marker_color=C_GRAY, width=0.62,
                             hovertemplate="%{x} · mes anterior: Bs %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Bar(x=marcas, y=[m_act.get(m, 0) for m in marcas],
                             name="Este mes", marker_color=C_YELLOW, width=0.4,
                             hovertemplate="%{x} · este mes: Bs %{y:,.0f}<extra></extra>"))
        fig.update_layout(barmode="overlay", legend=dict(orientation="h", y=1.12))
        st.plotly_chart(plotly_base(fig, 360), width="stretch")
        st.caption("Barra gris = total del mes anterior · Barra amarilla = acumulado de este mes.")
    with c_der:
        st.markdown("<div class='panel-title'>Tiendas con Mejor Rendimiento</div>",
                    unsafe_allow_html=True)
        for r in rank[rank["Este mes"] > 0].head(3).itertuples():
            va = getattr(r, "_6")  # ¿Cómo va?
            va_html = "" if pd.isna(va) else (
                f"<span style='color:{C_GREEN if va >= 0 else C_RED};font-size:.75rem'>"
                f"{'↗' if va >= 0 else '↘'} {va:+.0%}</span>")
            st.markdown(f"<div class='rankcard'><div><b>{r.SUCURSAL}</b><br>"
                        f"<span style='color:{C_MUTED};font-size:.78rem'>{r.MARCA}</span></div>"
                        f"<div style='text-align:right'><b style='color:{C_YELLOW}'>"
                        f"{fmt(getattr(r, '_4'))}</b><br>{va_html}</div></div>",
                        unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:14px'>Movimiento reciente</div>",
                    unsafe_allow_html=True)
        rec = (df_f.sort_values("FECHA", ascending=False).head(6)
               [["FECHA", "SUCURSAL", "VENTA"]])
        for r in rec.itertuples():
            st.markdown(f"<div class='rankcard' style='padding:8px 14px'>"
                        f"<div><b style='font-size:.85rem'>{r.SUCURSAL}</b><br>"
                        f"<span style='color:{C_MUTED};font-size:.72rem'>{r.FECHA:%d/%m/%Y}</span></div>"
                        f"<div><b>{fmt(r.VENTA)}</b></div></div>", unsafe_allow_html=True)

# ============================================================
# PÁGINA · VENTA POR MARCA
# ============================================================
elif pagina == MENU[1]:
    encabezado("Venta por Marca",
               f"{etiqueta(mes_actual)} vs {etiqueta(mes_anterior)} · participación y proyección")

    m_act = d_act.groupby("MARCA")["VENTA"].sum().sort_values(ascending=False)
    m_ant = d_ant.groupby("MARCA")["VENTA"].sum()
    total = m_act.sum()

    cols = st.columns(min(len(m_act), 4))
    for col, (marca, monto) in zip(cols, m_act.items()):
        ant_mismo = d_ant[(d_ant["MARCA"] == marca) & (d_ant["DIA"] <= dia_corte)]["VENTA"].sum()
        delta = (monto / ant_mismo - 1) if ant_mismo else np.nan
        kpi(col, marca, fmt(monto), delta, f"{monto/total:.0%} del total")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([0.55, 0.45])
    with c1:
        st.markdown("<div class='panel-title'>Este mes vs mes anterior</div>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=m_act.index, x=[m_ant.get(m, 0) for m in m_act.index],
                             orientation="h", name="Mes anterior", marker_color=C_GRAY, width=0.62,
                             hovertemplate="%{y}: Bs %{x:,.0f}<extra>Mes anterior</extra>"))
        fig.add_trace(go.Bar(y=m_act.index, x=m_act.values, orientation="h",
                             name="Este mes", width=0.4,
                             marker_color=[BRAND_COLORS.get(m, C_YELLOW) for m in m_act.index],
                             hovertemplate="%{y}: Bs %{x:,.0f}<extra>Este mes</extra>"))
        fig.update_layout(barmode="overlay", legend=dict(orientation="h", y=1.12),
                          yaxis=dict(autorange="reversed"))
        fig.update_xaxes(tickformat=",.0f")
        st.plotly_chart(plotly_base(fig, 360), width="stretch")
    with c2:
        st.markdown("<div class='panel-title'>Participación (mix)</div>", unsafe_allow_html=True)
        fig_p = go.Figure(go.Pie(labels=m_act.index, values=m_act.values, hole=0.6,
                                 marker=dict(colors=[BRAND_COLORS.get(m, C_MUTED) for m in m_act.index],
                                             line=dict(color=C_BG, width=2)),
                                 textinfo="percent", textfont=dict(color=C_BG, size=13),
                                 hovertemplate="%{label}: Bs %{value:,.0f} (%{percent})<extra></extra>"))
        fig_p.update_layout(height=360, margin=dict(l=0, r=0, t=12, b=0),
                            paper_bgcolor="rgba(0,0,0,0)", font=dict(color=C_TEXT),
                            legend=dict(orientation="h", y=-0.08),
                            annotations=[dict(text=f"<b>{fmt(total)}</b>", showarrow=False,
                                              font=dict(color=C_TEXT, size=15))])
        st.plotly_chart(fig_p, width="stretch")

    st.markdown("<div class='panel-title'>Resumen por marca</div>", unsafe_allow_html=True)
    tm = pd.DataFrame({"Este mes": m_act,
                       "Mes anterior": m_ant.reindex(m_act.index).fillna(0)})
    tm["Proyección"] = tm["Este mes"] / dia_corte * dias_mes
    tm["Participación"] = tm["Este mes"] / total
    tm["Estado"] = np.where(tm["Mes anterior"] == 0, "Nueva",
                            np.where(tm["Proyección"] >= tm["Mes anterior"],
                                     "Supera la meta", "Bajo la meta"))
    st.dataframe(tm.reset_index().rename(columns={"MARCA": "Marca"}).style
                 .format({"Este mes": "Bs {:,.0f}", "Mes anterior": "Bs {:,.0f}",
                          "Proyección": "Bs {:,.0f}", "Participación": "{:.1%}"}),
                 width="stretch", hide_index=True)

# ============================================================
# PÁGINA · VENTA POR TIENDA
# ============================================================
elif pagina == MENU[2]:
    encabezado("Venta por Tienda",
               f"Ranking de {etiqueta(mes_actual)} · corte al día {dia_corte}")

    fig = go.Figure()
    fig.add_trace(go.Bar(y=rank["SUCURSAL"], x=rank["Mes anterior"], orientation="h",
                         name="Mes anterior", marker_color=C_GRAY, width=0.66,
                         hovertemplate="%{y}: Bs %{x:,.0f}<extra>Mes anterior</extra>"))
    fig.add_trace(go.Bar(y=rank["SUCURSAL"], x=rank["Este mes"], orientation="h",
                         name="Este mes", marker_color=C_YELLOW, width=0.42,
                         hovertemplate="%{y}: Bs %{x:,.0f}<extra>Este mes</extra>"))
    fig.update_layout(barmode="overlay", legend=dict(orientation="h", y=1.06),
                      yaxis=dict(autorange="reversed"))
    fig.update_xaxes(tickformat=",.0f")
    st.plotly_chart(plotly_base(fig, 480), width="stretch")

    st.markdown("<div class='panel-title'>Detalle por tienda</div>", unsafe_allow_html=True)
    styler = (rank[["SUCURSAL", "MARCA", "Mes anterior", "Este mes",
                    "¿Cómo va?", "Proyección", "Estado"]]
              .style
              .format({"Mes anterior": "Bs {:,.0f}", "Este mes": "Bs {:,.0f}",
                       "Proyección": "Bs {:,.0f}",
                       "¿Cómo va?": lambda v: "—" if pd.isna(v) else f"{v:+.0%}"})
              .map(lambda v: f"color:{C_GREEN}" if isinstance(v, float) and v >= 0 else
                             (f"color:{C_RED}" if isinstance(v, float) and v < 0 else ""),
                   subset=["¿Cómo va?"]))
    st.dataframe(styler, width="stretch", height=500, hide_index=True)
    st.caption("«¿Cómo va?» compara contra los mismos días del mes anterior · "
               "«Proyección» estima el cierre al ritmo actual.")

    activos = rank[rank["Este mes"] > 0]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 3 del mes**")
        for i, r in enumerate(activos.head(3).itertuples(), 1):
            st.markdown(f"<div class='box' style='border-left-color:{C_GREEN}'>"
                        f"<b>{i}. {r.SUCURSAL}</b> — {fmt(getattr(r, '_4'))}</div>",
                        unsafe_allow_html=True)
    with c2:
        st.markdown("**Bottom 3 del mes**")
        for i, r in enumerate(activos.tail(3).iloc[::-1].itertuples(), 1):
            st.markdown(f"<div class='box' style='border-left-color:{C_RED}'>"
                        f"<b>{i}. {r.SUCURSAL}</b> — {fmt(getattr(r, '_4'))}</div>",
                        unsafe_allow_html=True)

# ============================================================
# PÁGINA · ÚLTIMOS 7 DÍAS
# ============================================================
else:
    fechas7 = sorted(df_f["FECHA"].unique())[-7:]
    d7 = df_f[df_f["FECHA"].isin(fechas7)]
    encabezado("Últimos 7 días",
               f"Del {pd.Timestamp(fechas7[0]):%d/%m} al {pd.Timestamp(fechas7[-1]):%d/%m} · "
               f"venta por tienda y por día")

    tot7 = d7.groupby("FECHA")["VENTA"].sum().reindex(fechas7).fillna(0)
    var_dia = tot7.pct_change().iloc[-1] if len(tot7) > 1 else np.nan

    a, b, c = st.columns(3)
    kpi(a, "Venta de la semana", fmt(tot7.sum()), None, "Últimos 7 días con datos",
        sparkline(tot7.values))
    kpi(b, f"Último día ({pd.Timestamp(fechas7[-1]):%d/%m})", fmt(tot7.iloc[-1]),
        var_dia, "vs día previo")
    kpi(c, "Promedio diario", fmt(tot7.mean()), None, "Tiendas seleccionadas")

    st.markdown("<br>", unsafe_allow_html=True)
    et_dia = lambda f: f"{DIAS_ES[pd.Timestamp(f).dayofweek]} {pd.Timestamp(f):%d/%m}"
    fig7 = go.Figure(go.Bar(x=[et_dia(f) for f in fechas7], y=tot7.values,
                            marker_color=C_YELLOW,
                            text=[f"{v/1000:,.0f}k" for v in tot7.values],
                            textposition="outside", textfont=dict(color=C_TEXT),
                            hovertemplate="%{x}: Bs %{y:,.0f}<extra></extra>"))
    st.plotly_chart(plotly_base(fig7, 280, "Venta total por día"), width="stretch")

    st.markdown("<div class='panel-title'>Venta por tienda · día a día</div>",
                unsafe_allow_html=True)
    piv = d7.pivot_table(index="SUCURSAL", columns="FECHA", values="VENTA",
                         aggfunc="sum").reindex(columns=fechas7)
    piv["TOTAL 7 DÍAS"] = piv.sum(axis=1)
    piv = piv.sort_values("TOTAL 7 DÍAS", ascending=False)
    piv.loc["TOTAL GRUPO"] = piv.sum()
    piv.columns = [et_dia(c) if not isinstance(c, str) else c for c in piv.columns]
    styler7 = (piv.style
               .format(lambda v: "—" if pd.isna(v) else f"Bs {v:,.0f}")
               .background_gradient(cmap="YlOrBr_r", axis=None,
                                    subset=pd.IndexSlice[piv.index[:-1], piv.columns[:-1]]))
    st.dataframe(styler7, width="stretch", height=520)
    st.caption("«—» = sin venta registrada ese día · Celdas más claras = mayor venta · "
               "La última fila suma todo el grupo.")

st.markdown(f"<p style='color:{C_MUTED};font-size:.75rem;margin-top:24px'>Grupo Wende · "
            f"Control Operativo & BI · Hoja «REPORTE DE VENTAS DIARIAS» · Montos en Bs.</p>",
            unsafe_allow_html=True)
