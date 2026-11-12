"""Módulo 3: Oferta Hotelera y Desagregación Territorial.

Preguntas de gestión que responde:
    1. ¿Qué tan llenos están los hoteles de Izabal y cómo se compara con otros departamentos?
    2. ¿La afluencia de visitantes acompaña a la ocupación? (ventana coincidente)
    3. ¿A qué subdestinos van y cómo se comporta cada uno?

Visualizaciones enlazadas:
    - El selector de medida de afluencia actualiza las series, la dispersión y la tabla.
    - El subdestino (selector o clic en la barra) actualiza KPIs, hospedaje y tendencia.

Limitación: ninguna fuente trae capacidad instalada (establecimientos,
habitaciones, plazas cama); se documenta y no se estima.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from scipy import stats

from app.components.charts import colores_foco, encabezado, estilo, marcar_hueco
from app.components.data import get
from app.components.kpis import advertencia, kpi, nota, titulo_modulo
from app.components.theme import PALETA, PATRONES_LINEA
from src.config import DESTINATION_DEPT, VENTANA_COINCIDENTE

st.set_page_config(page_title="M3 · Oferta Hotelera", page_icon="🏨", layout="wide")

titulo_modulo(
    "🏨 Módulo 3 · Oferta Hotelera y Desagregación Territorial",
    "Ocupación hotelera de Izabal, su relación con la afluencia de visitantes y el peso de cada subdestino.",
)

dep = get("occupancy_departments")
dep["fecha"] = pd.to_datetime(dep["fecha"])
ova = get("occupancy_vs_affluence")
ova["fecha"] = pd.to_datetime(ova["fecha"])
cubo = get("survey_izabal_cube")
cubo["fecha"] = pd.to_datetime(cubo["fecha"])

V_INI, V_FIN = (pd.Timestamp(x) for x in VENTANA_COINCIDENTE)
HUECO_ENCUESTA = ova.loc[ova["registros_encuesta"].isna(), "fecha"].tolist()
MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# ---------------------------------------------------------------------------
# Aviso de brecha de datos (capacidad instalada)
# ---------------------------------------------------------------------------
st.warning(
    "**Capacidad instalada no disponible.** Ninguna de las tres fuentes trae número de establecimientos, "
    "habitaciones ni plazas cama para 2022–2025, por lo que este módulo **no** estima la oferta. "
    "Solo se dispone del índice de ocupación departamental (2023–2025). Se recomienda a INGUAT incorporar "
    "el registro de establecimientos para medir capacidad y presión sobre la oferta en Río Dulce y Livingston.",
    icon="🧱",
)

# ---------------------------------------------------------------------------
# Filtros (una fila)
# ---------------------------------------------------------------------------
meses_occ = sorted(dep["fecha"].unique())
etq = [pd.Timestamp(m).strftime("%Y-%m") for m in meses_occ]
otros_deptos = sorted(d for d in dep["departamento"].unique() if d != DESTINATION_DEPT)

f1, f2, f3 = st.columns([2, 2.2, 1])
with f1:
    a_txt, b_txt = st.select_slider("Período (ocupación)", options=etq, value=(etq[0], etq[-1]), key="m3_periodo")
with f2:
    comparar = st.multiselect("Comparar Izabal con", otros_deptos, default=["Petén", "Sacatepéquez"],
                              max_selections=4, key="m3_deptos")
with f3:
    ver_prom = st.toggle("Promedio deptos.", value=True, key="m3_prom")
A, B = pd.Timestamp(a_txt), pd.Timestamp(b_txt)
dep_p = dep[dep["fecha"].between(A, B)]
iz = dep_p[dep_p["departamento"].eq(DESTINATION_DEPT)].set_index("fecha")["indice_ocupacion"]
prom = dep_p.groupby("fecha")["indice_ocupacion"].mean()

# ---------------------------------------------------------------------------
# 1. Ocupación
# ---------------------------------------------------------------------------
encabezado("¿Qué tan llenos están los hoteles de Izabal?", "Observado",
           "Índice de ocupación hotelera mensual del departamento (0–100 %).")

medias = dep_p.groupby("departamento")["indice_ocupacion"].mean().sort_values(ascending=False)
rank = list(medias.index).index(DESTINATION_DEPT) + 1
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi("Ocupación promedio", f"{iz.mean():.1%}", help="Promedio de los índices mensuales del período.")
with c2:
    kpi("vs. promedio deptos.", f"{(iz.mean() - prom.mean()) * 100:+.1f} pp",
        help="Diferencia en puntos porcentuales frente al promedio simple de los 22 departamentos.")
with c3:
    kpi("Mes más alto", f"{iz.max():.0%}", help=f"{iz.idxmax():%b %Y}")
    st.caption(f"{MESES_ES[iz.idxmax().month - 1]} {iz.idxmax().year}")
with c4:
    kpi("Mes más bajo", f"{iz.min():.0%}")
    st.caption(f"{MESES_ES[iz.idxmin().month - 1]} {iz.idxmin().year}")
with c5:
    kpi("Posición nacional", f"#{rank} de {len(medias)}", help="Ranking por ocupación promedio del período.")

col_l, col_r = st.columns([1.6, 1])
with col_l:
    fig = go.Figure()
    if ver_prom:
        fig.add_scatter(x=prom.index, y=prom.values, name="Promedio departamental", mode="lines",
                        line=dict(color=PALETA["neutro"], width=2, dash="dot"),
                        hovertemplate="%{x|%b %Y}: %{y:.0%}<extra>Promedio</extra>")
    paleta_comp = [PALETA["secundario"], PALETA["info"], PALETA["alerta"], PALETA["acento"]]
    for i, d in enumerate(comparar):
        s = dep_p[dep_p["departamento"].eq(d)].set_index("fecha")["indice_ocupacion"]
        fig.add_scatter(x=s.index, y=s.values, name=d, mode="lines",
                        line=dict(color=paleta_comp[i], width=1.5, dash=PATRONES_LINEA[i + 1]),
                        opacity=0.8, hovertemplate="%{x|%b %Y}: %{y:.0%}<extra>" + d + "</extra>")
    fig.add_scatter(x=iz.index, y=iz.values, name="Izabal", mode="lines+markers",
                    line=dict(color=PALETA["primario"], width=3), marker=dict(size=8),
                    hovertemplate="%{x|%b %Y}: %{y:.0%}<extra>Izabal</extra>")
    estilo(fig, 380, y="Índice de ocupación", y_pct=True)
    fig.update_yaxes(range=[0, 1])
    st.plotly_chart(fig, width="stretch")

with col_r:
    fig = go.Figure(go.Bar(
        x=medias.values[::-1], y=medias.index[::-1], orientation="h",
        marker_color=colores_foco(medias.index[::-1], DESTINATION_DEPT),
        hovertemplate="%{y}: %{x:.1%}<extra></extra>",
    ))
    estilo(fig, 440, x="Ocupación promedio del período", leyenda=False)
    fig.update_xaxes(tickformat=".0%")
    fig.update_yaxes(tickfont=dict(size=10), tickmode="array", tickvals=list(medias.index), automargin=True)
    fig.update_layout(bargap=0.15)
    fig.update_layout(title=dict(text="Ranking de los 22 departamentos", font=dict(size=14)))
    st.plotly_chart(fig, width="stretch")

with st.expander("🗓️ Estacionalidad: ocupación de Izabal por año y mes", expanded=True):
    hm = dep[dep["departamento"].eq(DESTINATION_DEPT)].copy()
    hm["anio"], hm["mes"] = hm["fecha"].dt.year, hm["fecha"].dt.month
    piv = hm.pivot(index="anio", columns="mes", values="indice_ocupacion").reindex(columns=range(1, 13))
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=MESES_ES, y=[str(a) for a in piv.index],
        colorscale=[[0, "#F1F7F8"], [1, PALETA["primario"]]], zmin=0.3, zmax=1,
        text=np.vectorize(lambda v: f"{v:.0%}" if not np.isnan(v) else "")(piv.values),
        texttemplate="%{text}", textfont=dict(size=12),
        hovertemplate="%{x} %{y}: %{z:.0%}<extra></extra>", colorbar=dict(tickformat=".0%", title=None),
        xgap=2, ygap=2,
    ))
    estilo(fig, 230, leyenda=False)
    st.plotly_chart(fig, width="stretch")
    perfil = piv.mean()
    st.caption(
        f"En promedio 2023–2025 el mes más alto es **{MESES_ES[perfil.idxmax() - 1]}** ({perfil.max():.0%}) "
        f"y el más bajo **{MESES_ES[perfil.idxmin() - 1]}** ({perfil.min():.0%})."
    )

# ---------------------------------------------------------------------------
# 2. Ventana coincidente: afluencia vs ocupación
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿La afluencia de visitantes acompaña a la ocupación hotelera?",
    None,
    "Cruce de la ocupación con una medida de afluencia en los meses en que ambas fuentes existen "
    "(2023–2025). La ventana coincidente Sep–Dic 2025 se resalta en todas las vistas.",
)

MEDIDAS = {
    "Participación de Izabal en la encuesta": ("participacion_izabal_encuesta", "Muestral", True),
    "Encuestas con destino Izabal (n)": ("registros_encuesta", "Muestral", False),
    "Visitantes en la muestra": ("visitantes_encuesta", "Muestral", False),
    "% de visitantes que pernocta": ("proporcion_pernocta", "Muestral", True),
    "Estadía media ponderada (noches)": ("estadia_ponderada", "Muestral", False),
    "Visitantes por fronteras alimentadoras (Migración)": ("migracion_alimentadoras", "Observado", False),
    "Tránsito marítimo en Izabal ('Viajero', Migración)": ("transito_izabal", "Observado", False),
}
g1, g2 = st.columns([2, 1.4])
with g1:
    medida = st.selectbox("Medida de afluencia", list(MEDIDAS), key="m3_medida",
                          help="La participación de Izabal en la encuesta corrige por el tamaño variable de la muestra.")
with g2:
    muestra = st.radio("Calcular correlación con", ["Todos los meses coincidentes", "Solo ventana Sep–Dic 2025"],
                       horizontal=False, key="m3_muestra")
col, tipo_dato, es_pct = MEDIDAS[medida]
st.markdown(f"Tipo de dato de la medida: **{tipo_dato}**  ·  ocupación: **Observado**")

v = ova[ova["fecha"].between(A, B)].copy()
fmt_med = ".1%" if es_pct else ",.1f"

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                    subplot_titles=("Ocupación hotelera de Izabal", medida))
fig.add_scatter(x=v["fecha"], y=v["ocupacion"], mode="lines+markers", name="Ocupación",
                line=dict(color=PALETA["primario"], width=2), marker=dict(size=7),
                hovertemplate="%{x|%b %Y}: %{y:.0%}<extra></extra>", row=1, col=1)
fig.add_bar(x=v["fecha"], y=v[col], name=medida,
            marker_color=np.where(v["en_ventana"], PALETA["info"], "#AEB6BE"),
            hovertemplate="%{x|%b %Y}: %{y:" + fmt_med + "}<extra></extra>", row=2, col=1)
for r in (1, 2):
    fig.add_vrect(x0=V_INI - pd.Timedelta(days=15), x1=V_FIN + pd.Timedelta(days=15),
                  fillcolor=PALETA["primario"], opacity=0.08, line_width=0, row=r, col=1)
if tipo_dato == "Muestral":
    for h in HUECO_ENCUESTA:
        if A <= h <= B:
            marcar_hueco(fig, h, fila=2, col=1)
estilo(fig, 470, leyenda=False)
fig.update_yaxes(tickformat=".0%", range=[0, 1], row=1, col=1)
if es_pct:
    fig.update_yaxes(tickformat=".0%", row=2, col=1)
fig.update_annotations(font=dict(size=13, color=PALETA["texto"]))
st.plotly_chart(fig, width="stretch")
st.caption("Dos paneles con su propia escala (no se usa doble eje). Franja turquesa = ventana Sep–Dic 2025; "
           "barras azules = meses de la ventana.")

# Dispersión + correlación
pares = ova.dropna(subset=["ocupacion", col])
if muestra.startswith("Solo"):
    pares_corr = pares[pares["en_ventana"]]
else:
    pares_corr = pares[pares["fecha"].between(A, B)]
n = len(pares_corr)

col_s, col_t = st.columns([1.3, 1])
with col_s:
    fig = go.Figure()
    fuera = pares_corr[~pares_corr["en_ventana"]]
    dentro = pares_corr[pares_corr["en_ventana"]]
    fig.add_scatter(x=fuera[col], y=fuera["ocupacion"], mode="markers", name="Otros meses",
                    marker=dict(size=9, color="#AEB6BE", line=dict(color="white", width=2)),
                    customdata=fuera["fecha"].dt.strftime("%b %Y"),
                    hovertemplate="%{customdata}<br>Afluencia: %{x:" + fmt_med + "}<br>Ocupación: %{y:.0%}<extra></extra>")
    fig.add_scatter(x=dentro[col], y=dentro["ocupacion"], mode="markers+text", name="Ventana Sep–Dic 2025",
                    marker=dict(size=12, color=PALETA["primario"], line=dict(color="white", width=2)),
                    text=[MESES_ES[m - 1] for m in dentro["fecha"].dt.month], textposition="top center",
                    textfont=dict(color=PALETA["texto"], size=11),
                    customdata=dentro["fecha"].dt.strftime("%b %Y"),
                    hovertemplate="%{customdata}<br>Afluencia: %{x:" + fmt_med + "}<br>Ocupación: %{y:.0%}<extra></extra>")
    if n >= 3 and pares_corr[col].nunique() > 1:
        b1, b0 = np.polyfit(pares_corr[col], pares_corr["ocupacion"], 1)
        xs = np.linspace(pares_corr[col].min(), pares_corr[col].max(), 50)
        fig.add_scatter(x=xs, y=b0 + b1 * xs, mode="lines", name="Tendencia lineal",
                        line=dict(color=PALETA["neutro"], dash="dash", width=1.5), hoverinfo="skip")
    estilo(fig, 380, x=medida, y="Ocupación")
    fig.update_yaxes(tickformat=".0%")
    if es_pct:
        fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")

with col_t:
    if n >= 3 and pares_corr[col].nunique() > 1:
        r, p = stats.pearsonr(pares_corr[col], pares_corr["ocupacion"])
        rho, p_s = stats.spearmanr(pares_corr[col], pares_corr["ocupacion"])
        fuerza = "débil" if abs(r) < 0.3 else "moderada" if abs(r) < 0.6 else "fuerte"
        sentido = "positiva" if r > 0 else "negativa"
        k1, k2 = st.columns(2)
        with k1:
            kpi("Pearson r", f"{r:+.2f}", help=f"p = {p:.3f}")
        with k2:
            kpi("Spearman ρ", f"{rho:+.2f}", help=f"p = {p_s:.3f}")
        kpi("Meses en el cálculo (n)", f"{n}")
        signif = "estadísticamente significativa (p < 0,05)" if p < 0.05 else "no significativa (p ≥ 0,05)"
        st.markdown(f"Relación **{fuerza} {sentido}**, {signif}.")
        if n < 8:
            advertencia(f"Con n = {n} meses la correlación es solo descriptiva: no permite concluir una relación.")
        elif abs(r) < 0.3:
            st.caption("La afluencia medida no explica bien la ocupación: el índice responde a otros factores "
                       "(mercado nacional, eventos, capacidad), por eso el pronóstico se basa en la propia serie de ocupación.")
    else:
        st.info("No hay suficientes meses con ambas fuentes para calcular la correlación.")

# Tabla de la ventana coincidente
st.markdown("**Ventana coincidente Sep–Dic 2025 frente al mismo mes de 2024**")
ventana = ova[ova["en_ventana"]].copy()
previo = ova.set_index("fecha")
ventana["Ocupación 2024"] = [previo["ocupacion"].get(f - pd.DateOffset(years=1), np.nan) for f in ventana["fecha"]]
ventana["Medida 2024"] = [previo[col].get(f - pd.DateOffset(years=1), np.nan) for f in ventana["fecha"]]
tabla = pd.DataFrame({
    "Mes": [f"{MESES_ES[f.month - 1]} {f.year}" for f in ventana["fecha"]],
    "Ocupación": ventana["ocupacion"].values,
    "Δ ocupación vs 2024 (pp)": ((ventana["ocupacion"] - ventana["Ocupación 2024"]) * 100).values,
    medida: ventana[col].values,
    "Δ medida vs 2024": ((ventana[col] / ventana["Medida 2024"] - 1) * 100).values,
})
st.dataframe(
    tabla, hide_index=True, width="stretch",
    column_config={
        "Ocupación": st.column_config.NumberColumn(format="percent"),
        "Δ ocupación vs 2024 (pp)": st.column_config.NumberColumn(format="%+.0f pp"),
        medida: st.column_config.NumberColumn(format="percent" if es_pct else "localized"),
        "Δ medida vs 2024": st.column_config.NumberColumn(format="%+.0f %%"),
    },
)

# ---------------------------------------------------------------------------
# 3. Subdestinos
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿A qué subdestinos de Izabal van los visitantes?",
    "Muestral",
    "Cada encuesta registra un destino principal. Los porcentajes comparan el peso relativo de cada "
    "subdestino y nunca se suman para obtener visitantes del departamento (regla 4). "
    "Haz clic en una barra para ver el perfil del subdestino.",
)

meses_enc = pd.date_range(cubo["fecha"].min(), cubo["fecha"].max(), freq="MS")
etq_enc = [m.strftime("%Y-%m") for m in meses_enc]
s1, s2 = st.columns([2.2, 1.3])
with s1:
    sa, sb = st.select_slider("Período (encuesta)", options=etq_enc, value=(etq_enc[0], etq_enc[-1]), key="m3_sub_periodo")
with s2:
    seg = st.radio("Segmento", ["Todos", "Turista", "Excursionista"], horizontal=True, key="m3_sub_seg")
SA, SB = pd.Timestamp(sa), pd.Timestamp(sb)
base = cubo[cubo["fecha"].between(SA, SB)]
if seg != "Todos":
    base = base[base["segmento"].eq(seg)]

GENERICOS = {"Izabal (genérico)", "Otro", "No especificado"}
por_sub = base.groupby("subdestino")["registros"].sum()
total_sub = por_sub.sum()
especificos = por_sub.drop(list(GENERICOS), errors="ignore").sort_values(ascending=False)
sin_especificar = por_sub.reindex(list(GENERICOS)).sum()
mostrar = especificos.head(10)

opciones_sub = ["Todos"] + mostrar.index.tolist()
if st.session_state.get("m3_sub") not in opciones_sub:
    st.session_state["m3_sub"] = "Todos"


def _clic_sub():
    ev = st.session_state.get("m3_sub_click")
    puntos = (ev or {}).get("selection", {}).get("points", []) if ev else []
    if puntos:
        valor = puntos[0].get("y") or puntos[0].get("label")
        st.session_state["m3_sub"] = "Todos" if valor == st.session_state.get("m3_sub") else valor


col_b, col_p = st.columns([1.1, 1])
with col_b:
    sub = st.selectbox("Subdestino", opciones_sub, key="m3_sub")
    foco = None if sub == "Todos" else sub
    fig = go.Figure(go.Bar(
        x=(mostrar / total_sub).values[::-1], y=mostrar.index[::-1], orientation="h",
        marker_color=colores_foco(mostrar.index[::-1], foco),
        customdata=mostrar.values[::-1],
        texttemplate="%{x:.1%}", textposition="outside", textfont=dict(color=PALETA["texto"]),
        hovertemplate="%{y}: %{x:.1%} de las encuestas<br>n = %{customdata}<extra></extra>",
    ))
    estilo(fig, 380, x="% de encuestas con destino Izabal", leyenda=False)
    fig.update_xaxes(tickformat=".0%", range=[0, (mostrar / total_sub).max() * 1.2 if total_sub else 1])
    fig.update_layout(clickmode="event+select", dragmode=False)
    st.plotly_chart(fig, width="stretch", key="m3_sub_click", on_select=_clic_sub, selection_mode="points")
    if total_sub:
        st.caption(f"Sin subdestino específico (solo 'Izabal' u otro texto): **{sin_especificar / total_sub:.1%}** "
                   f"de {int(total_sub):,} encuestas.")

with col_p:
    sel = base[base["subdestino"].eq(foco)] if foco else base
    st.markdown(f"**Perfil: {foco or 'todo Izabal'}**")
    vp, dp_ = sel["visitantes_pernocta"].sum(), sel["dias_persona"].sum()
    q1, q2, q3 = st.columns(3)
    with q1:
        kpi("Encuestas (n)", f"{int(sel['registros'].sum()):,}")
    with q2:
        kpi("Pernoctan", f"{vp / sel['visitantes'].sum():.0%}" if sel["visitantes"].sum() else "Sin dato")
    with q3:
        kpi("Estadía (noches)", f"{dp_ / vp:.1f}" if vp else "Sin dato",
            help="Estadía media ponderada: Σ días-persona / Σ visitantes que pernoctan.")
    if foco and sel["registros"].sum() < 30:
        advertencia("Menos de 30 encuestas: interpretar con cautela.")

    # Hospedaje: subdestino vs Izabal completo (dos series, un eje)
    h_sel = sel.groupby("hospedaje")["visitantes"].sum()
    h_tot = base.groupby("hospedaje")["visitantes"].sum()
    orden = h_tot.sort_values(ascending=False).index
    fig = go.Figure()
    fig.add_bar(y=orden[::-1], x=(h_tot / h_tot.sum()).reindex(orden)[::-1], orientation="h",
                name="Todo Izabal", marker_color="#AEB6BE" if foco else PALETA["primario"], hovertemplate="%{y}: %{x:.0%}<extra>Izabal</extra>")
    if foco:
        fig.add_bar(y=orden[::-1], x=(h_sel / h_sel.sum()).reindex(orden).fillna(0)[::-1], orientation="h",
                    name=foco, marker_color=PALETA["primario"],
                    hovertemplate="%{y}: %{x:.0%}<extra>" + foco + "</extra>")
    fig.update_layout(barmode="group", title=dict(text="Tipo de hospedaje (% de visitantes)", font=dict(size=14)))
    estilo(fig, 320, leyenda=bool(foco))
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0))
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")

# Tendencia trimestral del peso del subdestino
if foco:
    t = base.assign(trim=base["fecha"].dt.to_period("Q").dt.to_timestamp())
    tot_q = t.groupby("trim")["registros"].sum()
    sub_q = t[t["subdestino"].eq(foco)].groupby("trim")["registros"].sum().reindex(tot_q.index, fill_value=0)
    share = sub_q / tot_q
    pocos = tot_q < 20
    fig = go.Figure(go.Scatter(
        x=share.index, y=share.values, mode="lines+markers", line=dict(color=PALETA["primario"], width=2),
        marker=dict(size=9, color=np.where(pocos, "white", PALETA["primario"]),
                    line=dict(color=PALETA["primario"], width=2)),
        customdata=np.c_[sub_q.values, tot_q.values],
        hovertemplate="%{x|%Y T%q}<br>%{y:.0%} (%{customdata[0]} de %{customdata[1]} encuestas)<extra></extra>",
    ))
    estilo(fig, 280, y=f"% de encuestas a {foco}", y_pct=True, leyenda=False)
    fig.update_layout(title=dict(text=f"Peso trimestral de {foco} dentro de Izabal "
                                      "(marcador vacío = trimestre con < 20 encuestas)", font=dict(size=14)))
    st.plotly_chart(fig, width="stretch")

nota(
    "**Fuentes y límites.** Ocupación: índice mensual departamental 2023–2025 (no distingue subdestinos). "
    "Afluencia y subdestinos: encuesta muestral sin factor de expansión (2022-04 a 2026-08, sin datos en 2025-01). "
    "Migración: entradas al país por frontera, no visitantes del destino."
)
