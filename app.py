# ============================================================
#  GRUPO WENDE — DASHBOARD EJECUTIVO DE VENTAS DIARIAS
#  13 tiendas · 5 marcas · Objetivo: igualar o superar el mes anterior
#  Streamlit + Plotly · Fondo oscuro · Detalles amarillos
# ============================================================

import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# 1) CONFIGURACIÓN GENERAL
# ------------------------------------------------------------
st.set_page_config(
    page_title="Grupo Wende · Dashboard Ejecutivo",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta corporativa (fondo oscuro + amarillo Grupo Wende)
C_BG      = "#0B0B0E"
C_PANEL   = "#15151A"
C_BORDER  = "#26262E"
C_YELLOW  = "#FFD400"
C_AMBER   = "#F2A900"
C_TEXT    = "#F4F1E6"
C_MUTED   = "#9C9AA6"
C_GREEN   = "#3DDC84"
C_RED     = "#FF5C5C"

BRAND_COLORS = {
    "El Chico Fresa":   "#FF3B4E",
    "MrBeast Burger":   "#FFD400",
    "La Happy Hour":    "#F2A900",
    "Santo Domingo":    "#F5A3C7",
}
BRAND_LOGOS = {
    "El Chico Fresa":   "assets/chico_fresa.png",
    "MrBeast Burger":   "assets/mrbeast.png",
    "La Happy Hour":    "assets/la_happy_hour.jpg",
    "Santo Domingo":    "assets/santo_domingo.jpg",
}
DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
            "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Fuente de datos: Google Sheets (export CSV) con respaldo local
SHEET_ID  = "1pKund1DmfQzY0SGBFrk7VIKeXrqiJzl_QVmJ7roSyek"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
LOCAL_CSV = Path(__file__).parent / "data" / "ventas_diarias_raw.csv"

# ------------------------------------------------------------
# 2) ESTILOS (CSS)
# ------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {C_BG};
        color: {C_TEXT};
        font-family: 'IBM Plex Sans', sans-serif;
    }}
    [data-testid="stSidebar"] {{
        background-color: {C_PANEL};
        border-right: 1px solid {C_BORDER};
    }}
    h1, h2, h3 {{ font-family: 'Archivo', sans-serif; letter-spacing: -0.01em; }}

    .kpi-card {{
        background: {C_PANEL};
        border: 1px solid {C_BORDER};
        border-top: 3px solid {C_YELLOW};
        border-radius: 12px;
        padding: 16px 18px 14px 18px;
        height: 100%;
    }}
    .kpi-label {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: .12em; color: {C_MUTED}; }}
    .kpi-value {{ font-family:'Archivo'; font-size: 1.65rem; font-weight: 800; color: {C_TEXT}; margin-top: 4px; }}
    .kpi-delta-pos {{ color: {C_GREEN}; font-size: 0.85rem; font-weight: 600; }}
    .kpi-delta-neg {{ color: {C_RED}; font-size: 0.85rem; font-weight: 600; }}
    .kpi-sub {{ color: {C_MUTED}; font-size: 0.78rem; margin-top: 2px; }}

    .insight-box {{
        background: {C_PANEL};
        border: 1px solid {C_BORDER};
        border-left: 4px solid {C_YELLOW};
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }}
    .section-title {{
        font-family: 'Archivo'; font-weight: 800; font-size: 1.15rem;
        color: {C_YELLOW}; text-transform: uppercase; letter-spacing: .08em;
        border-bottom: 1px solid {C_BORDER}; padding-bottom: 6px; margin: 8px 0 14px 0;
    }}
    div[data-testid="stDataFrame"] {{ border: 1px solid {C_BORDER}; border-radius: 10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 3) CARGA Y LIMPIEZA DE DATOS
# ------------------------------------------------------------
def asignar_marca(sucursal: str) -> str:
    s = sucursal.upper()
    if s.startswith("CF"):
        return "El Chico Fresa"
    if "BEAST" in s:
        return "MrBeast Burger"
    if "HAPPY" in s:
        return "La Happy Hour"
    if "SANTO DOMINGO" in s:
        return "Santo Domingo"
    return "Otras"

@st.cache_data(ttl=600, show_spinner="Cargando ventas desde Google Sheets…")
def cargar_datos() -> pd.DataFrame:
    try:
        df = pd.read_csv(SHEET_URL)
        fuente = "Google Sheets (en vivo)"
    except Exception:
        df = pd.read_csv(LOCAL_CSV)
        fuente = "CSV local (respaldo)"

    df.columns = [c.strip().upper() for c in df.columns]
    df["SUCURSAL"] = df["SUCURSAL"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["VENTA"] = (
        df["VENTA REAL"].astype(str)
        .str.replace("Bs", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["VENTA"] = pd.to_numeric(df["VENTA"], errors="coerce")
    df = df.dropna(subset=["VENTA"])
    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["FECHA"])
    df["MES"] = df["FECHA"].dt.to_period("M")
    df["DIA"] = df["FECHA"].dt.day
    df["DIA_SEMANA"] = df["FECHA"].dt.dayofweek  # 0 = lunes
    df["MARCA"] = df["SUCURSAL"].apply(asignar_marca)
    df.attrs["fuente"] = fuente
    return df

df = cargar_datos()

# ------------------------------------------------------------
# 4) SIDEBAR — FILTROS
# ------------------------------------------------------------
with st.sidebar:
    logo_gw = Path(__file__).parent / "assets" / "grupo_wende.jpeg"
    if logo_gw.exists():
        st.image(str(logo_gw), width="stretch")
    st.markdown("### Filtros del reporte")

    meses = sorted(df["MES"].unique())
    # Por defecto: el mes más reciente con cobertura de al menos la mitad de las tiendas
    n_tiendas = df["SUCURSAL"].nunique()
    cobertura = df.groupby("MES")["SUCURSAL"].nunique()
    candidatos = [m for m in meses if cobertura.get(m, 0) >= n_tiendas / 2]
    mes_default = candidatos[-1] if candidatos else meses[-1]

    etiqueta = lambda m: f"{MESES_ES[m.month]} {m.year}"
    mes_actual = st.selectbox(
        "Mes a analizar", meses, index=meses.index(mes_default), format_func=etiqueta
    )
    mes_anterior = mes_actual - 1

    marcas_disp = sorted(df["MARCA"].unique())
    marcas_sel = st.multiselect("Marcas", marcas_disp, default=marcas_disp)

    st.caption(f"Fuente: {df.attrs.get('fuente','—')}")
    st.caption(f"Última venta registrada: {df['FECHA'].max():%d/%m/%Y}")

df_f = df[df["MARCA"].isin(marcas_sel)]
d_act = df_f[df_f["MES"] == mes_actual]
d_ant = df_f[df_f["MES"] == mes_anterior]

if d_act.empty:
    st.warning("No hay ventas registradas para el mes y las marcas seleccionadas.")
    st.stop()

# ------------------------------------------------------------
# 5) CÁLCULOS CENTRALES (las "fórmulas" del dashboard)
# ------------------------------------------------------------
dias_mes        = calendar.monthrange(mes_actual.year, mes_actual.month)[1]
dia_corte       = int(d_act["DIA"].max())              # último día con datos
dias_restantes  = dias_mes - dia_corte
mes_cerrado     = dia_corte >= dias_mes

venta_mtd       = d_act["VENTA"].sum()                                  # Ventas MTD
run_rate        = venta_mtd / dia_corte * dias_mes                      # Run Rate
venta_ant_total = d_ant["VENTA"].sum()                                  # Total mes anterior
venta_ant_mismo = d_ant[d_ant["DIA"] <= dia_corte]["VENTA"].sum()       # Mismo período mes ant.
prom_diario     = venta_mtd / dia_corte                                 # Venta promedio diaria

mom_mismo   = (venta_mtd / venta_ant_mismo - 1) if venta_ant_mismo else np.nan
mom_proj    = (run_rate / venta_ant_total - 1) if venta_ant_total else np.nan
cumpl_proj  = (run_rate / venta_ant_total) if venta_ant_total else np.nan
gap         = venta_ant_total - venta_mtd
ritmo_req   = gap / dias_restantes if dias_restantes > 0 else 0.0

fmt  = lambda v: f"Bs {v:,.0f}"
fpct = lambda v: "—" if pd.isna(v) else f"{v:+.1%}"

# ------------------------------------------------------------
# 6) ENCABEZADO
# ------------------------------------------------------------
c1, c2 = st.columns([0.75, 0.25])
with c1:
    st.markdown(
        f"<h1 style='margin-bottom:0'>Dashboard Ejecutivo de Ventas</h1>"
        f"<p style='color:{C_MUTED};margin-top:2px'>Grupo Wende · {len(d_act['SUCURSAL'].unique())} tiendas activas · "
        f"{etiqueta(mes_actual)} (corte al día {dia_corte})</p>",
        unsafe_allow_html=True,
    )
with c2:
    objetivo_txt = "✅ Objetivo proyectado: SE SUPERA" if cumpl_proj >= 1 else "⚠️ Objetivo proyectado: EN RIESGO"
    color_obj = C_GREEN if cumpl_proj >= 1 else C_RED
    st.markdown(
        f"<div class='insight-box' style='border-left-color:{color_obj}'>"
        f"<b>Objetivo:</b> igualar o superar {etiqueta(mes_anterior)}<br>"
        f"<span style='color:{color_obj};font-weight:700'>{objetivo_txt}</span>"
        f"<br><span style='color:{C_MUTED};font-size:.8rem'>Proyección = {cumpl_proj:.0%} del mes anterior</span></div>",
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# 7) SECCIÓN 1 — RESUMEN EJECUTIVO (KPIs)
# ------------------------------------------------------------
st.markdown("<div class='section-title'>1 · Resumen ejecutivo</div>", unsafe_allow_html=True)

def kpi(col, label, value, delta=None, sub=None):
    delta_html = ""
    if delta is not None and not pd.isna(delta):
        cls = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f"<div class='{cls}'>{arrow} {abs(delta):.1%}</div>"
    sub_html = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    col.markdown(
        f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>{delta_html}{sub_html}</div>",
        unsafe_allow_html=True,
    )

k1, k2, k3, k4, k5 = st.columns(5)
kpi(k1, f"Ventas {etiqueta(mes_actual)} (MTD)", fmt(venta_mtd), mom_mismo, f"vs mismo período de {MESES_ES[mes_anterior.month]}")
kpi(k2, "Run Rate (proyección de cierre)", fmt(run_rate), mom_proj, f"vs total {MESES_ES[mes_anterior.month]}")
kpi(k3, f"Ventas {etiqueta(mes_anterior)}", fmt(venta_ant_total), None, "Mes anterior completo")
kpi(k4, "Crecimiento MoM proyectado", fpct(mom_proj), None, "Run Rate ÷ mes anterior − 1")
kpi(k5, "Venta promedio diaria", fmt(prom_diario), None, f"{dia_corte} días transcurridos")

# Barra de avance hacia el objetivo
st.markdown("<br>", unsafe_allow_html=True)
fig_gauge = go.Figure()
fig_gauge.add_trace(go.Bar(
    x=[venta_ant_total], y=["Objetivo"], orientation="h",
    marker=dict(color=C_BORDER), hovertemplate="Objetivo (mes anterior): %{x:,.0f} Bs<extra></extra>",
))
fig_gauge.add_trace(go.Bar(
    x=[venta_mtd], y=["Objetivo"], orientation="h",
    marker=dict(color=C_YELLOW), hovertemplate="Acumulado MTD: %{x:,.0f} Bs<extra></extra>",
))
fig_gauge.add_vline(x=run_rate, line_dash="dash", line_color=C_GREEN if run_rate >= venta_ant_total else C_RED,
                    annotation_text=f"Proyección {fmt(run_rate)}", annotation_font_color=C_TEXT)
fig_gauge.update_layout(
    barmode="overlay", height=110, margin=dict(l=10, r=10, t=26, b=8),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C_TEXT), showlegend=False,
    title=dict(text=f"Avance hacia el objetivo ({fmt(venta_ant_total)})", font=dict(size=13, color=C_MUTED)),
    xaxis=dict(showgrid=False, tickformat=",.0f"), yaxis=dict(showticklabels=False),
)
st.plotly_chart(fig_gauge, width="stretch")

if not mes_cerrado and dias_restantes > 0:
    msg = (f"Para igualar {etiqueta(mes_anterior)} faltan <b>{fmt(max(gap,0))}</b> en "
           f"<b>{dias_restantes} días</b> → ritmo requerido de <b>{fmt(max(ritmo_req,0))}/día</b> "
           f"(hoy el ritmo es {fmt(prom_diario)}/día).") if gap > 0 else \
          (f"🎉 El objetivo ya se alcanzó: el acumulado supera al total de {etiqueta(mes_anterior)} "
           f"por <b>{fmt(-gap)}</b>.")
    st.markdown(f"<div class='insight-box'>{msg}</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# 8) SECCIÓN 2 — DESGLOSE POR TIENDA Y MARCA
# ------------------------------------------------------------
st.markdown("<div class='section-title'>2 · Desglose por tienda y marca</div>", unsafe_allow_html=True)

g_act = d_act.groupby(["SUCURSAL", "MARCA"])["VENTA"].sum().rename("Ventas Mes Actual (MTD)")
g_ant = d_ant.groupby("SUCURSAL")["VENTA"].sum().rename("Ventas Mes Anterior")
g_ant_mismo = d_ant[d_ant["DIA"] <= dia_corte].groupby("SUCURSAL")["VENTA"].sum()

tabla = g_act.reset_index().merge(g_ant.reset_index(), on="SUCURSAL", how="outer")
tabla["MARCA"] = tabla["MARCA"].fillna(tabla["SUCURSAL"].apply(asignar_marca))
tabla = tabla.fillna({"Ventas Mes Actual (MTD)": 0, "Ventas Mes Anterior": 0})
tabla["Run Rate"] = tabla["Ventas Mes Actual (MTD)"] / dia_corte * dias_mes
tabla["_ant_mismo"] = tabla["SUCURSAL"].map(g_ant_mismo).fillna(0)
tabla["Variación %"] = np.where(
    tabla["_ant_mismo"] > 0,
    tabla["Ventas Mes Actual (MTD)"] / tabla["_ant_mismo"] - 1,
    np.nan,
)
tabla["% Proyección vs Objetivo"] = np.where(
    tabla["Ventas Mes Anterior"] > 0,
    tabla["Run Rate"] / tabla["Ventas Mes Anterior"],
    np.nan,
)
tabla = tabla.sort_values("Ventas Mes Actual (MTD)", ascending=False).reset_index(drop=True)

t_izq, t_der = st.columns([0.62, 0.38])
with t_izq:
    mostrar = tabla[["SUCURSAL", "MARCA", "Ventas Mes Anterior",
                     "Ventas Mes Actual (MTD)", "Variación %", "Run Rate",
                     "% Proyección vs Objetivo"]]
    styler = (
        mostrar.style
        .format({"Ventas Mes Anterior": "Bs {:,.0f}",
                 "Ventas Mes Actual (MTD)": "Bs {:,.0f}",
                 "Run Rate": "Bs {:,.0f}",
                 "Variación %": lambda v: "Nueva" if pd.isna(v) else f"{v:+.1%}",
                 "% Proyección vs Objetivo": lambda v: "—" if pd.isna(v) else f"{v:.0%}"})
        .map(lambda v: f"color:{C_GREEN}" if isinstance(v, float) and v >= 0 else
                       (f"color:{C_RED}" if isinstance(v, float) and v < 0 else ""),
             subset=["Variación %"])
        .background_gradient(cmap="YlOrBr_r", subset=["Ventas Mes Actual (MTD)"])
    )
    st.dataframe(styler, width="stretch", height=520, hide_index=True)

with t_der:
    activos = tabla[tabla["Ventas Mes Actual (MTD)"] > 0]
    top3 = activos.head(3)
    bottom3 = activos.tail(3).iloc[::-1]

    st.markdown("**🏆 Top 3 tiendas (MTD)**")
    for i, r in enumerate(top3.itertuples(), 1):
        st.markdown(
            f"<div class='insight-box' style='border-left-color:{C_GREEN}'>"
            f"<b>{i}. {r.SUCURSAL}</b><br>{fmt(r._4)} "
            f"<span style='color:{C_MUTED}'>· {r.MARCA}</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown("**🔻 Bottom 3 tiendas (MTD)**")
    for i, r in enumerate(bottom3.itertuples(), 1):
        st.markdown(
            f"<div class='insight-box' style='border-left-color:{C_RED}'>"
            f"<b>{i}. {r.SUCURSAL}</b><br>{fmt(r._4)} "
            f"<span style='color:{C_MUTED}'>· {r.MARCA}</span></div>",
            unsafe_allow_html=True,
        )

# --- Mix de ventas por marca ---
st.markdown("#### Mix de ventas por marca")
mix = d_act.groupby("MARCA")["VENTA"].sum().sort_values(ascending=False)
m_izq, m_der = st.columns([0.45, 0.55])
with m_izq:
    fig_mix = go.Figure(go.Pie(
        labels=mix.index, values=mix.values, hole=0.58,
        marker=dict(colors=[BRAND_COLORS.get(m, C_MUTED) for m in mix.index],
                    line=dict(color=C_BG, width=2)),
        textinfo="percent", textfont=dict(color=C_BG, size=13),
        hovertemplate="%{label}: Bs %{value:,.0f} (%{percent})<extra></extra>",
    ))
    fig_mix.update_layout(
        height=330, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color=C_TEXT),
        legend=dict(orientation="h", y=-0.1),
        annotations=[dict(text=f"<b>{fmt(mix.sum())}</b><br>total", showarrow=False,
                          font=dict(color=C_TEXT, size=14))],
    )
    st.plotly_chart(fig_mix, width="stretch")
with m_der:
    for marca, monto in mix.items():
        share = monto / mix.sum()
        lg = Path(__file__).parent / BRAND_LOGOS.get(marca, "")
        cA, cB = st.columns([0.14, 0.86])
        if lg.exists():
            cA.image(str(lg), width=52)
        cB.markdown(
            f"<b>{marca}</b> — {fmt(monto)} · <span style='color:{C_YELLOW}'>{share:.1%}</span> del total"
            f"<div style='background:{C_BORDER};border-radius:6px;height:8px;margin:4px 0 10px 0'>"
            f"<div style='background:{BRAND_COLORS.get(marca, C_YELLOW)};width:{share*100:.1f}%;"
            f"height:8px;border-radius:6px'></div></div>",
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# 9) SECCIÓN 3 — ANÁLISIS DE TENDENCIA DIARIA
# ------------------------------------------------------------
st.markdown("<div class='section-title'>3 · Análisis de tendencia diaria</div>", unsafe_allow_html=True)

serie_act = d_act.groupby("DIA")["VENTA"].sum()
serie_ant = d_ant.groupby("DIA")["VENTA"].sum()

fig_t = go.Figure()
if not serie_ant.empty:
    fig_t.add_trace(go.Scatter(
        x=serie_ant.index, y=serie_ant.values, name=etiqueta(mes_anterior),
        mode="lines", line=dict(color=C_MUTED, width=1.5, dash="dot"),
    ))
fig_t.add_trace(go.Scatter(
    x=serie_act.index, y=serie_act.values, name=etiqueta(mes_actual),
    mode="lines+markers", line=dict(color=C_YELLOW, width=3),
    marker=dict(size=6), fill="tozeroy", fillcolor="rgba(255,212,0,0.08)",
))
fig_t.update_layout(
    height=340, margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C_TEXT), title=dict(text="Venta diaria total (Bs)", font=dict(size=14)),
    xaxis=dict(title="Día del mes", gridcolor=C_BORDER),
    yaxis=dict(gridcolor=C_BORDER, tickformat=",.0f"),
    legend=dict(orientation="h", y=1.12),
    hovermode="x unified",
)
st.plotly_chart(fig_t, width="stretch")

# Mejor y peor día de la semana (promedio de venta total por día calendario)
base_dow = df_f[df_f["MES"].isin([mes_anterior, mes_actual])]
diaria = base_dow.groupby(["FECHA", "DIA_SEMANA"])["VENTA"].sum().reset_index()
dow = diaria.groupby("DIA_SEMANA")["VENTA"].mean().reindex(range(7))
mejor, peor = int(dow.idxmax()), int(dow.idxmin())

d1, d2 = st.columns([0.65, 0.35])
with d1:
    colores = [C_GREEN if i == mejor else (C_RED if i == peor else C_AMBER) for i in range(7)]
    fig_dow = go.Figure(go.Bar(
        x=DIAS_ES, y=dow.values, marker_color=colores,
        hovertemplate="%{x}: Bs %{y:,.0f} promedio<extra></extra>",
        text=[f"{v/1000:,.1f}k" for v in dow.values], textposition="outside",
        textfont=dict(color=C_TEXT),
    ))
    fig_dow.update_layout(
        height=340, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C_TEXT),
        title=dict(text="Venta promedio por día de la semana", font=dict(size=14)),
        yaxis=dict(gridcolor=C_BORDER, tickformat=",.0f"),
    )
    st.plotly_chart(fig_dow, width="stretch")
with d2:
    st.markdown(
        f"<div class='insight-box' style='border-left-color:{C_GREEN}'>"
        f"<b>Mejor día: {DIAS_ES[mejor]}</b><br>Promedio {fmt(dow[mejor])} "
        f"({dow[mejor]/dow[peor]-1:+.0%} vs el peor día)</div>"
        f"<div class='insight-box' style='border-left-color:{C_RED}'>"
        f"<b>Peor día: {DIAS_ES[peor]}</b><br>Promedio {fmt(dow[peor])}</div>",
        unsafe_allow_html=True,
    )
    fs = diaria[diaria["DIA_SEMANA"] >= 4]["VENTA"].sum()
    share_fs = fs / diaria["VENTA"].sum()
    st.markdown(
        f"<div class='insight-box'><b>Vie–Sáb–Dom</b> concentra el "
        f"<span style='color:{C_YELLOW};font-weight:700'>{share_fs:.0%}</span> de la venta.<br>"
        f"<span style='color:{C_MUTED};font-size:.8rem'>Priorizar personal, insumos y pauta en fin de semana.</span></div>",
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# 10) KPIs ADICIONALES DE ALTO VALOR
# ------------------------------------------------------------
st.markdown("<div class='section-title'>4 · KPIs adicionales</div>", unsafe_allow_html=True)

mejor_dia_hist = diaria.loc[diaria["VENTA"].idxmax()]
cv = (d_act.groupby(["SUCURSAL", "FECHA"])["VENTA"].sum()
      .groupby("SUCURSAL").agg(["mean", "std"]))
cv = cv[cv["mean"] > 0]
cv["cv"] = cv["std"] / cv["mean"]
consistente = cv["cv"].idxmin() if not cv.empty else "—"
mayor_salto = tabla.dropna(subset=["Variación %"]).sort_values("Variación %", ascending=False)

e1, e2, e3, e4 = st.columns(4)
kpi(e1, "Récord diario del período", fmt(mejor_dia_hist["VENTA"]),
    None, f"{mejor_dia_hist['FECHA']:%d/%m/%Y}")
kpi(e2, "Tienda más consistente", consistente, None,
    "Menor variabilidad diaria (CV)")
if not mayor_salto.empty:
    kpi(e3, "Mayor crecimiento vs mes ant.", mayor_salto.iloc[0]["SUCURSAL"],
        mayor_salto.iloc[0]["Variación %"], "Mismo período comparable")
    kpi(e4, "Mayor caída vs mes ant.", mayor_salto.iloc[-1]["SUCURSAL"],
        mayor_salto.iloc[-1]["Variación %"], "Mismo período comparable")

st.markdown(
    f"<p style='color:{C_MUTED};font-size:.75rem;margin-top:24px'>"
    f"Grupo Wende · Control Operativo & Business Intelligence · "
    f"Datos: hoja «REPORTE DE VENTAS DIARIAS». Los montos están en bolivianos (Bs).</p>",
    unsafe_allow_html=True,
)
