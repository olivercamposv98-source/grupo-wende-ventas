# ============================================================
#  GRUPO WENDE — DASHBOARD EJECUTIVO DE VENTAS DIARIAS
#  Versión simplificada · 3 pestañas · Objetivo: superar el mes anterior
# ============================================================

import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# 1) CONFIGURACIÓN Y ESTILO
# ------------------------------------------------------------
st.set_page_config(
    page_title="Grupo Wende · Ventas",
    page_icon="🟡",
    layout="wide",
    initial_sidebar_state="expanded",
)

C_BG, C_PANEL, C_BORDER = "#0B0B0E", "#15151A", "#26262E"
C_YELLOW, C_TEXT, C_MUTED = "#FFD400", "#F4F1E6", "#9C9AA6"
C_GREEN, C_RED = "#3DDC84", "#FF5C5C"

BRAND_COLORS = {
    "El Chico Fresa": "#FF3B4E",
    "MrBeast Burger": "#FFD400",
    "La Happy Hour": "#F2A900",
    "Santo Domingo": "#F5A3C7",
}
BRAND_LOGOS = {
    "El Chico Fresa": "assets/chico_fresa.png",
    "MrBeast Burger": "assets/mrbeast.png",
    "La Happy Hour": "assets/la_happy_hour.jpg",
    "Santo Domingo": "assets/santo_domingo.jpg",
}
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
            "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

SHEET_ID = "1pKund1DmfQzY0SGBFrk7VIKeXrqiJzl_QVmJ7roSyek"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
LOCAL_CSV = Path(__file__).parent / "data" / "ventas_diarias_raw.csv"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;800&family=IBM+Plex+Sans:wght@400;600&display=swap');
    html, body, [data-testid="stAppViewContainer"] {{ background:{C_BG}; color:{C_TEXT}; font-family:'IBM Plex Sans',sans-serif; }}
    [data-testid="stSidebar"] {{ background:{C_PANEL}; border-right:1px solid {C_BORDER}; }}
    h1,h2,h3 {{ font-family:'Archivo',sans-serif; }}
    .stTabs [data-baseweb="tab"] {{ font-size:1rem; font-weight:600; }}
    .stTabs [aria-selected="true"] {{ color:{C_YELLOW} !important; }}

    .kpi {{ background:{C_PANEL}; border:1px solid {C_BORDER}; border-top:3px solid {C_YELLOW};
           border-radius:12px; padding:16px 18px; height:100%; }}
    .kpi .lbl {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.1em; color:{C_MUTED}; }}
    .kpi .val {{ font-family:'Archivo'; font-size:1.7rem; font-weight:800; margin-top:4px; }}
    .kpi .pos {{ color:{C_GREEN}; font-weight:600; font-size:.85rem; }}
    .kpi .neg {{ color:{C_RED}; font-weight:600; font-size:.85rem; }}
    .kpi .sub {{ color:{C_MUTED}; font-size:.76rem; margin-top:2px; }}

    .box {{ background:{C_PANEL}; border:1px solid {C_BORDER}; border-left:4px solid {C_YELLOW};
           border-radius:10px; padding:13px 16px; margin-bottom:10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 2) DATOS
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

@st.cache_data(ttl=600, show_spinner="Cargando ventas…")
def cargar_datos() -> pd.DataFrame:
    try:
        df = pd.read_csv(SHEET_URL)
        fuente = "Google Sheets (en vivo)"
    except Exception:
        df = pd.read_csv(LOCAL_CSV)
        fuente = "CSV local (respaldo)"
    df.columns = [c.strip().upper() for c in df.columns]
    df["SUCURSAL"] = df["SUCURSAL"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["VENTA"] = pd.to_numeric(
        df["VENTA REAL"].astype(str).str.replace("Bs", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce",
    )
    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["VENTA", "FECHA"])
    df["MES"] = df["FECHA"].dt.to_period("M")
    df["DIA"] = df["FECHA"].dt.day
    df["DOW"] = df["FECHA"].dt.dayofweek
    df["MARCA"] = df["SUCURSAL"].apply(asignar_marca)
    df.attrs["fuente"] = fuente
    return df

df = cargar_datos()
fmt = lambda v: f"Bs {v:,.0f}"

# ------------------------------------------------------------
# 3) SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    logo = Path(__file__).parent / "assets" / "grupo_wende.jpeg"
    if logo.exists():
        st.image(str(logo), width="stretch")
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
# 4) CÁLCULOS
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
gap = venta_ant - venta_mtd
ritmo_req = gap / dias_rest if dias_rest > 0 else 0

# ------------------------------------------------------------
# 5) ENCABEZADO + PESTAÑAS
# ------------------------------------------------------------
st.markdown(
    f"<h1 style='margin-bottom:0'>Ventas Grupo Wende</h1>"
    f"<p style='color:{C_MUTED};margin-top:2px'>{etiqueta(mes_actual)} · corte al día {dia_corte} · "
    f"{d_act['SUCURSAL'].nunique()} tiendas activas</p>",
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["📊  Resumen", "🏪  Tiendas y marcas", "📅  Últimos 5 días"])

def kpi(col, label, value, delta=None, sub=None):
    d = ""
    if delta is not None and not pd.isna(delta):
        cls = "pos" if delta >= 0 else "neg"
        d = f"<div class='{cls}'>{'▲' if delta >= 0 else '▼'} {abs(delta):.1%}</div>"
    s = f"<div class='sub'>{sub}</div>" if sub else ""
    col.markdown(f"<div class='kpi'><div class='lbl'>{label}</div>"
                 f"<div class='val'>{value}</div>{d}{s}</div>", unsafe_allow_html=True)

# ============================================================
# PESTAÑA 1 · RESUMEN
# ============================================================
with tab1:
    k1, k2, k3, k4 = st.columns(4)
    kpi(k1, "Venta del mes (acumulada)", fmt(venta_mtd), mom,
        f"vs mismos días de {MESES_ES[mes_anterior.month]}")
    kpi(k2, "Proyección de cierre", fmt(run_rate), None,
        f"Ritmo actual × {dias_mes} días")
    kpi(k3, f"Total {MESES_ES[mes_anterior.month]}", fmt(venta_ant), None,
        "La meta a superar")
    kpi(k4, "Venta promedio por día", fmt(prom_diario), None,
        f"{dia_corte} días transcurridos")

    # Semáforo del objetivo — el mensaje más importante en una sola frase
    st.markdown("<br>", unsafe_allow_html=True)
    if pd.isna(cumpl):
        st.markdown(f"<div class='box'>Sin mes anterior para comparar (tiendas nuevas).</div>",
                    unsafe_allow_html=True)
    elif cumpl >= 1:
        st.markdown(
            f"<div class='box' style='border-left-color:{C_GREEN}'>"
            f"✅ <b>Vamos bien:</b> al ritmo actual el mes cierra en <b>{fmt(run_rate)}</b>, "
            f"un <b style='color:{C_GREEN}'>{cumpl-1:+.1%}</b> sobre {MESES_ES[mes_anterior.month]}.</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='box' style='border-left-color:{C_RED}'>"
            f"⚠️ <b>Atención:</b> al ritmo actual el mes cierra en <b>{fmt(run_rate)}</b> "
            f"(<b style='color:{C_RED}'>{cumpl-1:+.1%}</b> vs {MESES_ES[mes_anterior.month]}). "
            f"Para igualarlo se necesita vender <b>{fmt(max(ritmo_req,0))}/día</b> "
            f"los próximos {dias_rest} días (hoy: {fmt(prom_diario)}/día).</div>",
            unsafe_allow_html=True)

    # Barra de avance
    fig_g = go.Figure()
    fig_g.add_trace(go.Bar(x=[venta_ant], y=[""], orientation="h", marker_color=C_BORDER,
                           hovertemplate="Meta: %{x:,.0f} Bs<extra></extra>"))
    fig_g.add_trace(go.Bar(x=[venta_mtd], y=[""], orientation="h", marker_color=C_YELLOW,
                           hovertemplate="Acumulado: %{x:,.0f} Bs<extra></extra>"))
    fig_g.add_vline(x=run_rate, line_dash="dash",
                    line_color=C_GREEN if run_rate >= venta_ant else C_RED,
                    annotation_text="Proyección", annotation_font_color=C_TEXT)
    fig_g.update_layout(barmode="overlay", height=90, showlegend=False,
                        margin=dict(l=10, r=10, t=24, b=6),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color=C_TEXT),
                        title=dict(text="Avance del mes vs meta", font=dict(size=13, color=C_MUTED)),
                        xaxis=dict(showgrid=False, tickformat=",.0f"),
                        yaxis=dict(showticklabels=False))
    st.plotly_chart(fig_g, width="stretch")

    # Tendencia diaria + día de la semana
    c_izq, c_der = st.columns([0.6, 0.4])
    with c_izq:
        s_act = d_act.groupby("DIA")["VENTA"].sum()
        s_ant = d_ant.groupby("DIA")["VENTA"].sum()
        fig_t = go.Figure()
        if not s_ant.empty:
            fig_t.add_trace(go.Scatter(x=s_ant.index, y=s_ant.values,
                                       name=MESES_ES[mes_anterior.month], mode="lines",
                                       line=dict(color=C_MUTED, width=1.5, dash="dot")))
        fig_t.add_trace(go.Scatter(x=s_act.index, y=s_act.values,
                                   name=MESES_ES[mes_actual.month], mode="lines+markers",
                                   line=dict(color=C_YELLOW, width=3),
                                   fill="tozeroy", fillcolor="rgba(255,212,0,0.08)"))
        fig_t.update_layout(height=320, margin=dict(l=10, r=10, t=34, b=10),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color=C_TEXT), hovermode="x unified",
                            title=dict(text="Venta por día del mes", font=dict(size=14)),
                            xaxis=dict(title="Día", gridcolor=C_BORDER),
                            yaxis=dict(gridcolor=C_BORDER, tickformat=",.0f"),
                            legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_t, width="stretch")
    with c_der:
        base = df_f[df_f["MES"].isin([mes_anterior, mes_actual])]
        diaria = base.groupby(["FECHA", "DOW"])["VENTA"].sum().reset_index()
        dow = diaria.groupby("DOW")["VENTA"].mean().reindex(range(7))
        mejor, peor = int(dow.idxmax()), int(dow.idxmin())
        colores = [C_GREEN if i == mejor else (C_RED if i == peor else "#5a5340") for i in range(7)]
        fig_d = go.Figure(go.Bar(x=DIAS_ES, y=dow.values, marker_color=colores,
                                 hovertemplate="%{x}: Bs %{y:,.0f}<extra></extra>"))
        fig_d.update_layout(height=320, margin=dict(l=10, r=10, t=34, b=10),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color=C_TEXT),
                            title=dict(text=f"Mejor día: {DIAS_ES[mejor]} · Peor día: {DIAS_ES[peor]}",
                                       font=dict(size=14)),
                            yaxis=dict(gridcolor=C_BORDER, tickformat=",.0f"))
        st.plotly_chart(fig_d, width="stretch")

# ============================================================
# PESTAÑA 2 · TIENDAS Y MARCAS
# ============================================================
with tab2:
    g_act = d_act.groupby(["SUCURSAL", "MARCA"])["VENTA"].sum().rename("Este mes")
    g_ant = d_ant.groupby("SUCURSAL")["VENTA"].sum().rename("Mes anterior")
    g_ant_mismo = d_ant[d_ant["DIA"] <= dia_corte].groupby("SUCURSAL")["VENTA"].sum()

    t = g_act.reset_index().merge(g_ant.reset_index(), on="SUCURSAL", how="outer")
    t["MARCA"] = t["MARCA"].fillna(t["SUCURSAL"].apply(asignar_marca))
    t = t.fillna({"Este mes": 0, "Mes anterior": 0})
    t["Proyección"] = t["Este mes"] / dia_corte * dias_mes
    t["_mismo"] = t["SUCURSAL"].map(g_ant_mismo).fillna(0)
    t["¿Cómo va?"] = np.where(t["_mismo"] > 0, t["Este mes"] / t["_mismo"] - 1, np.nan)
    t["Estado"] = np.select(
        [t["Mes anterior"] == 0, t["Proyección"] >= t["Mes anterior"]],
        ["🆕 Nueva", "✅ Supera la meta"], default="⚠️ Bajo la meta")
    t = t.sort_values("Este mes", ascending=False).reset_index(drop=True)

    st.markdown("#### Ranking de tiendas")
    styler = (
        t[["SUCURSAL", "MARCA", "Mes anterior", "Este mes", "¿Cómo va?", "Proyección", "Estado"]]
        .style
        .format({"Mes anterior": "Bs {:,.0f}", "Este mes": "Bs {:,.0f}",
                 "Proyección": "Bs {:,.0f}",
                 "¿Cómo va?": lambda v: "—" if pd.isna(v) else f"{v:+.0%}"})
        .map(lambda v: f"color:{C_GREEN}" if isinstance(v, float) and v >= 0 else
                       (f"color:{C_RED}" if isinstance(v, float) and v < 0 else ""),
             subset=["¿Cómo va?"])
    )
    st.dataframe(styler, width="stretch", height=500, hide_index=True)
    st.caption("«¿Cómo va?» compara contra los mismos días del mes anterior. "
               "«Proyección» estima el cierre manteniendo el ritmo actual.")

    activos = t[t["Este mes"] > 0]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🏆 Top 3 del mes**")
        for i, r in enumerate(activos.head(3).itertuples(), 1):
            st.markdown(f"<div class='box' style='border-left-color:{C_GREEN}'>"
                        f"<b>{i}. {r.SUCURSAL}</b> — {fmt(getattr(r, '_4'))}</div>",
                        unsafe_allow_html=True)
    with c2:
        st.markdown("**🔻 Bottom 3 del mes**")
        for i, r in enumerate(activos.tail(3).iloc[::-1].itertuples(), 1):
            st.markdown(f"<div class='box' style='border-left-color:{C_RED}'>"
                        f"<b>{i}. {r.SUCURSAL}</b> — {fmt(getattr(r, '_4'))}</div>",
                        unsafe_allow_html=True)

    st.markdown("#### ¿De dónde viene la venta? (mix por marca)")
    mix = d_act.groupby("MARCA")["VENTA"].sum().sort_values(ascending=False)
    for marca, monto in mix.items():
        share = monto / mix.sum()
        lg = Path(__file__).parent / BRAND_LOGOS.get(marca, "")
        cA, cB = st.columns([0.08, 0.92])
        if lg.exists():
            cA.image(str(lg), width=48)
        cB.markdown(
            f"<b>{marca}</b> — {fmt(monto)} · "
            f"<span style='color:{C_YELLOW};font-weight:700'>{share:.0%}</span> del total"
            f"<div style='background:{C_BORDER};border-radius:6px;height:10px;margin:4px 0 12px 0'>"
            f"<div style='background:{BRAND_COLORS.get(marca, C_YELLOW)};width:{share*100:.1f}%;"
            f"height:10px;border-radius:6px'></div></div>",
            unsafe_allow_html=True)

# ============================================================
# PESTAÑA 3 · ÚLTIMOS 5 DÍAS
# ============================================================
with tab3:
    fechas5 = sorted(df_f["FECHA"].unique())[-5:]
    d5 = df_f[df_f["FECHA"].isin(fechas5)]

    tot5 = d5.groupby("FECHA")["VENTA"].sum().reindex(fechas5).fillna(0)
    var_dia = tot5.pct_change().iloc[-1] if len(tot5) > 1 else np.nan

    a, b, c = st.columns(3)
    kpi(a, "Venta últimos 5 días", fmt(tot5.sum()), None,
        f"{pd.Timestamp(fechas5[0]):%d/%m} al {pd.Timestamp(fechas5[-1]):%d/%m}")
    kpi(b, f"Último día ({pd.Timestamp(fechas5[-1]):%d/%m})", fmt(tot5.iloc[-1]),
        var_dia, "vs día previo")
    kpi(c, "Promedio diario (5 días)", fmt(tot5.mean()), None,
        "Todas las tiendas seleccionadas")

    st.markdown("<br>", unsafe_allow_html=True)
    etiqueta_dia = lambda f: f"{DIAS_ES[pd.Timestamp(f).dayofweek]} {pd.Timestamp(f):%d/%m}"
    fig5 = go.Figure(go.Bar(
        x=[etiqueta_dia(f) for f in fechas5], y=tot5.values, marker_color=C_YELLOW,
        text=[f"{v/1000:,.0f}k" for v in tot5.values], textposition="outside",
        textfont=dict(color=C_TEXT),
        hovertemplate="%{x}: Bs %{y:,.0f}<extra></extra>"))
    fig5.update_layout(height=280, margin=dict(l=10, r=10, t=34, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font=dict(color=C_TEXT),
                       title=dict(text="Venta total por día", font=dict(size=14)),
                       yaxis=dict(gridcolor=C_BORDER, tickformat=",.0f"))
    st.plotly_chart(fig5, width="stretch")

    st.markdown("#### Detalle por tienda")
    piv = d5.pivot_table(index="SUCURSAL", columns="FECHA", values="VENTA",
                         aggfunc="sum").reindex(columns=fechas5)
    piv["TOTAL 5 DÍAS"] = piv.sum(axis=1)
    piv = piv.sort_values("TOTAL 5 DÍAS", ascending=False)
    piv.loc["TOTAL GRUPO"] = piv.sum()
    piv.columns = [etiqueta_dia(c) if not isinstance(c, str) else c for c in piv.columns]

    styler5 = (piv.style
               .format(lambda v: "—" if pd.isna(v) else f"Bs {v:,.0f}")
               .background_gradient(cmap="YlOrBr_r", axis=None,
                                    subset=pd.IndexSlice[piv.index[:-1], piv.columns[:-1]]))
    st.dataframe(styler5, width="stretch", height=520)
    st.caption("«—» = sin venta registrada ese día. La última fila suma todo el grupo.")

st.markdown(
    f"<p style='color:{C_MUTED};font-size:.75rem;margin-top:24px'>Grupo Wende · "
    f"Control Operativo & BI · Datos: hoja «REPORTE DE VENTAS DIARIAS» · Montos en Bs.</p>",
    unsafe_allow_html=True,
)
