"""Módulo 1: Monitor de Demanda y Mercados Emisores (Diagnóstico Macro).

La historia que cuenta este módulo, en tres pasos:

    1. Cuántos llegan a Izabal y cuántos se quedan a dormir.
    2. De qué mercados vienen y qué perfil tiene cada uno.
    3. Por las fronteras que alimentan el destino, cuánta gente entra al país.

Visualización enlazada: el filtro de mercado (selector o clic en la barra del
ranking) actualiza KPIs, segmentación, estadía, perfil y serie de migración.

Fuentes: encuesta (muestral, sin factor de expansión) y base de migración
(absoluta). La encuesta solo se lee como proporción (regla 6).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.charts import colores_foco, estilo, marcar_hueco, pct_texto, titulo_grafico
from app.components.data import get
from app.components.kpis import advertencia, nota
from app.components.layout import (
    ALTURA,
    ALTURA_GRANDE,
    insight,
    kpis,
    modulo,
    seccion,
)
from app.components.theme import PALETA
from src.config import SURVEY_BORDER_MAP, SURVEY_NATIONALITY_MAP, VISITOR_TYPES

st.set_page_config(page_title="M1 · Demanda y Mercados", page_icon="📊", layout="wide")

cubo = get("survey_izabal_cube")
cubo["fecha"] = pd.to_datetime(cubo["fecha"])


@st.cache_data(show_spinner=False)
def migracion_alimentadoras() -> pd.DataFrame:
    """Visitantes (Turista+Excursionista) por mes y país en las fronteras mapeadas."""
    mm = get("migration_monthly")
    m = mm[mm["Frontera"].isin(SURVEY_BORDER_MAP.values()) & mm["Tipo de Viajero"].isin(VISITOR_TYPES)]
    return m.groupby(["fecha", "País"], as_index=False)["viajeros"].sum()


mig = migracion_alimentadoras()
paises_mig = set(mig["País"])
meses = pd.date_range(cubo["fecha"].min(), cubo["fecha"].max(), freq="MS")
etiquetas = [m.strftime("%Y-%m") for m in meses]
MIN_N = 30

# --- Cifras de cabecera -----------------------------------------------------
vis_total = cubo["visitantes"].sum()
vp_total = cubo["visitantes_pernocta"].sum()
dp_total = cubo["dias_persona"].sum()
prop_pernocta = vp_total / vis_total if vis_total else 0.0
estadia_media = dp_total / vp_total if vp_total else 0.0
mercado_top = (
    cubo[cubo["nacionalidad"].ne("Guatemala")]
    .groupby("nacionalidad")["visitantes"].sum().nlargest(1).index.tolist()
)
nombre_mercado = mercado_top[0] if mercado_top else "el mercado principal"

modulo(
    "📊 Módulo 1 · Monitor de Demanda y Mercados Emisores",
    "¿Cuántos visitantes recibe Izabal, cuánto se quedan y de dónde vienen?",
    f"**{prop_pernocta:.0%} de los visitantes que llegan a Izabal pernoctan** y se quedan "
    f"**{estadia_media:.1f} noches** en promedio; el mercado se concentra en "
    f"**{nombre_mercado}**.",
)

kpis(
    [
        ("Encuestas (n)", f"{int(cubo['registros'].sum()):,}", "grupos de viaje con destino Izabal"),
        ("Visitantes/mes (muestra)", f"{vis_total / max(cubo['fecha'].nunique(), 1):,.0f}",
         "tamaño de muestra, no demanda real", "info"),
        ("Pernoctan (turistas)", f"{prop_pernocta:.0%}", "visitantes que pasan > 24 h", "secundario"),
        ("Estadía media ponderada", f"{estadia_media:.1f} noches", "Σ días-persona / Σ visitantes",
         "acento"),
    ]
)

# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
f1, f2, f3, f4 = st.columns([2.2, 1.3, 1.2, 1.6])
with f1:
    ini_txt, fin_txt = st.select_slider(
        "Período (encuesta)", options=etiquetas, value=(etiquetas[0], etiquetas[-1]), key="m1_periodo"
    )
with f2:
    segmento = st.radio("Segmento", ["Todos", "Turista", "Excursionista"], horizontal=True,
                        key="m1_segmento", help="Turista: pernocta (> 24 h). Excursionista: < 24 h.")
with f3:
    lente = st.radio("Mercado por", ["Nacionalidad", "Residencia"], horizontal=True, key="m1_lente")
col_mercado = "nacionalidad" if lente == "Nacionalidad" else "residencia"

ini, fin = pd.Timestamp(ini_txt), pd.Timestamp(fin_txt)
en_periodo = cubo["fecha"].between(ini, fin)
en_segmento = cubo["segmento"].eq(segmento) if segmento != "Todos" else pd.Series(True, index=cubo.index)

ranking_base = cubo[en_periodo & en_segmento]
orden_mercados = (
    ranking_base.groupby(col_mercado)["visitantes"].sum().sort_values(ascending=False).index.tolist()
)
opciones = ["Todos"] + orden_mercados
if st.session_state.get("m1_mercado") not in opciones:
    st.session_state["m1_mercado"] = "Todos"
with f4:
    mercado = st.selectbox(f"Mercado ({lente.lower()})", opciones, key="m1_mercado")
foco = None if mercado == "Todos" else mercado
en_mercado = cubo[col_mercado].eq(foco) if foco else pd.Series(True, index=cubo.index)
f = cubo[en_periodo & en_segmento & en_mercado]


def _al_clic():
    """Clic en una barra del ranking -> fija el mercado (visualización enlazada)."""
    ev = st.session_state.get("m1_click")
    puntos = (ev or {}).get("selection", {}).get("points", []) if ev else []
    if puntos:
        valor = puntos[0].get("y") or puntos[0].get("label")
        st.session_state["m1_mercado"] = "Todos" if valor == st.session_state.get("m1_mercado") else valor


if foco:
    st.markdown(
        f"Filtrando por **{lente.lower()}: {foco}** · {ini_txt} → {fin_txt} · segmento: **{segmento}**. "
        "Vuelve a hacer clic en la barra o elige *Todos* para quitar el filtro."
    )

# ---------------------------------------------------------------------------
# 1 · Llegada y permanencia
# ---------------------------------------------------------------------------
seccion(
    f"{prop_pernocta:.0%} de los visitantes hacen noche en el destino",
    "Participación mensual de cada segmento en los visitantes encuestados. "
    "El hueco gris es un mes sin encuesta: ausencia de dato, no cero.",
    badge="Muestral",
)

n_reg = int(f["registros"].sum())
vis = f["visitantes"].sum()
vp = f["visitantes_pernocta"].sum()
dp = f["dias_persona"].sum()
if 0 < n_reg < MIN_N:
    advertencia(f"Solo hay **{n_reg} encuestas** con estos filtros: los porcentajes son poco estables.")
elif n_reg == 0:
    advertencia("No hay encuestas con esta combinación de filtros.")

col_a, col_b = st.columns([1.3, 1])
with col_a:
    s = cubo[en_periodo & en_mercado].groupby(["fecha", "segmento"])["visitantes"].sum().unstack()
    s = s.reindex(pd.date_range(ini, fin, freq="MS")).reindex(columns=["Turista", "Excursionista"])
    con_dato = s.notna().any(axis=1)
    s.loc[con_dato] = s.loc[con_dato].fillna(0)
    total = s.sum(axis=1, min_count=1)
    fig = go.Figure()
    colores_seg = {"Turista": PALETA["primario"], "Excursionista": PALETA["secundario"]}
    for seg in ["Turista", "Excursionista"]:
        color = colores_seg[seg] if segmento in ("Todos", seg) else "#D5D9DD"
        fig.add_bar(
            x=s.index, y=s[seg] / total, name=seg, marker_color=color,
            customdata=np.c_[s[seg].fillna(0), total.fillna(0)],
            hovertemplate="%{x|%b %Y}<br>" + seg + ": %{y:.1%}<br>%{customdata[0]:,.0f} de "
            "%{customdata[1]:,.0f} visitantes<extra></extra>",
        )
    fig.update_layout(barmode="stack")
    for m in s.index[~con_dato]:
        if not foco:
            marcar_hueco(fig, m)
    estilo(fig, ALTURA_GRANDE, y="% de visitantes", y_pct=True)
    titulo_grafico(fig, "El peso de quien pernocta se mantiene estable todo el año")
    st.plotly_chart(fig, width="stretch")

with col_b:
    e = f[f["segmento"].eq("Turista")].groupby("fecha")[["dias_persona", "visitantes_pernocta", "registros"]].sum()
    e = e.reindex(pd.date_range(ini, fin, freq="MS"))
    e["estadia"] = e["dias_persona"] / e["visitantes_pernocta"].replace(0, np.nan)
    pocas = e["registros"] < 10
    fig = go.Figure()
    fig.add_scatter(
        x=e.index, y=e["estadia"], mode="lines+markers", name="Estadía",
        line=dict(color=PALETA["primario"], width=2),
        marker=dict(size=8, color=np.where(pocas, "white", PALETA["primario"]),
                    line=dict(color=PALETA["primario"], width=2)),
        customdata=e["registros"].fillna(0),
        hovertemplate="%{x|%b %Y}<br>%{y:.1f} noches<br>n = %{customdata:.0f} encuestas<extra></extra>",
    )
    if vp:
        fig.add_hline(y=dp / vp, line_dash="dot", line_color=PALETA["neutro"],
                      annotation_text=f"Período: {dp / vp:.1f}", annotation_position="top left")
    estilo(fig, ALTURA_GRANDE, y="Noches", leyenda=False)
    titulo_grafico(fig, "La estadía media ponderada ronda las {} noches".format(
        f"{dp / vp:.1f}" if vp else "—"))
    st.plotly_chart(fig, width="stretch")
    st.caption("Marcador vacío = mes con menos de 10 encuestas.")

insight(
    f"La estadía media ponderada del período es de **{dp / vp:.1f} noches** "
    f"(Σ días-persona / Σ visitantes que pernoctan, nunca un promedio simple). "
    f"Un excursionista **no** entra en ese cálculo: una estancia de menos de 24 h no es permanencia."
    if vp else "Sin visitantes que pernocten en este filtro: no hay estadía que calcular."
)

# ---------------------------------------------------------------------------
# 2 · Mercados emisores
# ---------------------------------------------------------------------------
seccion(
    f"El mercado de Izabal se concentra en {nombre_mercado}",
    f"Top 10 mercados extranjeros por {lente.lower()} como porcentaje de la muestra. "
    "Clic en una barra para filtrar todo el módulo.",
    badge="Muestral",
)

rk = ranking_base.groupby(col_mercado)["visitantes"].sum()
tot_rk = rk.sum()
nacionales = rk.get("Guatemala", 0.0)
ext = rk.drop("Guatemala", errors="ignore").sort_values(ascending=False)
top = ext.head(10)

col_r, col_t = st.columns([1.15, 1])
with col_r:
    fig = go.Figure(go.Bar(
        x=(top / tot_rk).values[::-1], y=top.index[::-1], orientation="h",
        marker_color=colores_foco(top.index[::-1], foco),
        customdata=top.values[::-1],
        hovertemplate="%{y}: %{x:.1%} de la muestra<br>%{customdata:,.0f} visitantes encuestados<extra></extra>",
        texttemplate="%{x:.0%}", textposition="outside", textfont=dict(color=PALETA["texto"]),
    ))
    estilo(fig, ALTURA_GRANDE, x="% de visitantes de la muestra", leyenda=False)
    fig.update_xaxes(tickformat=".0%", range=[0, (top / tot_rk).max() * 1.2 if len(top) else 1])
    fig.update_layout(clickmode="event+select", dragmode=False)
    titulo_grafico(fig, "Tres mercados explican la mayor parte de los visitantes extranjeros")
    st.plotly_chart(fig, width="stretch", key="m1_click", on_select=_al_clic, selection_mode="points")
    st.caption(
        f"Nacionales (Guatemala) se reportan aparte: **{nacionales / tot_rk:.1%}** de la muestra."
        if tot_rk else "Sin datos en el período."
    )

with col_t:
    st.markdown(f"**Nacionalidad vs. residencia** (top 10 nacionalidades)")
    base = cubo[en_periodo & en_segmento]
    tot_b = base["visitantes"].sum()
    top_nac = base.groupby("nacionalidad")["visitantes"].sum().drop("Guatemala", errors="ignore").nlargest(10)
    filas = []
    for pais, v in top_nac.items():
        sub = base[base["nacionalidad"].eq(pais)]
        reside_otro = sub.loc[sub["residencia"].ne(pais), "visitantes"].sum()
        filas.append({
            "Nacionalidad": pais,
            "% nacionalidad": v / tot_b,
            "% residencia": base.loc[base["residencia"].eq(pais), "visitantes"].sum() / tot_b,
            "Residen fuera": reside_otro / v if v else np.nan,
        })
    st.dataframe(
        pd.DataFrame(filas), hide_index=True, width="stretch",
        column_config={
            "% nacionalidad": st.column_config.NumberColumn(format="percent"),
            "% residencia": st.column_config.NumberColumn(format="percent"),
            "Residen fuera": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.caption("*Residen fuera*: % de esa nacionalidad que vive en otro país. Una brecha alta "
               "indica diáspora o expatriados: el mercado emisor real es el país de residencia.")

# ---------------------------------------------------------------------------
# 3 · Perfil del visitante
# ---------------------------------------------------------------------------
_fr = cubo.groupby("frontera_nombre")["visitantes"].sum().sort_values(ascending=False)
_hos = cubo.groupby("hospedaje")["visitantes"].sum().sort_values(ascending=False)
_tr = cubo.groupby("tipo_transporte")["visitantes"].sum().sort_values(ascending=False)
cuota_frontera = float(_fr.iloc[0] / cubo["visitantes"].sum()) if len(_fr) else 0.0
cuota_hospedaje = float(_hos.iloc[0] / cubo["visitantes"].sum()) if len(_hos) else 0.0
cuota_bus = float(_tr.iloc[0] / cubo["visitantes"].sum()) if len(_tr) else 0.0

seccion(
    f"El {cuota_frontera:.0%} entra por {_fr.index[0]} y el {cuota_bus:.0%} llega en {_tr.index[0].lower()}",
    "Las tres gráficas responden al período, el segmento y el mercado seleccionados."
    + (f" Foco: **{foco}**." if foco else ""),
    badge="Muestral",
)


def barras_participacion(columna: str, titulo: str, top_n: int = 6):
    d = f.groupby(columna)["visitantes"].sum().sort_values(ascending=False)
    if d.empty:
        st.info("Sin datos con estos filtros.")
        return
    if len(d) > top_n:
        d = pd.concat([d.head(top_n), pd.Series({"Otros": d.iloc[top_n:].sum()})])
    p = d / d.sum()
    fig = go.Figure(go.Bar(
        x=p.values[::-1], y=p.index[::-1], orientation="h", marker_color=PALETA["primario"],
        text=pct_texto(p.values[::-1]), textposition="outside", textfont=dict(color=PALETA["texto"]),
        hovertemplate="%{y}: %{x:.1%}<extra></extra>",
    ))
    estilo(fig, ALTURA, leyenda=False)
    fig.update_xaxes(tickformat=".0%", range=[0, p.max() * 1.3], visible=False)
    fig.update_layout(title=dict(text=titulo, font=dict(size=13, color=PALETA["texto"])),
                      margin=dict(t=34, l=10, r=10, b=10))
    st.plotly_chart(fig, width="stretch")


p1, p2, p3 = st.columns(3)
with p1:
    barras_participacion("frontera_nombre", "Frontera de entrada")
with p2:
    barras_participacion("hospedaje", "Tipo de hospedaje")
with p3:
    barras_participacion("tipo_transporte", "Medio de transporte")

# ---------------------------------------------------------------------------
# 4 · Migración por las fronteras alimentadoras
# ---------------------------------------------------------------------------
seccion(
    "Por las fronteras que alimentan Izabal entra mucha más gente de la que visita el destino",
    "Turistas y excursionistas registrados por Migración en las fronteras por donde entra la "
    "muestra de Izabal. Mide la puerta de entrada al país, no los visitantes que llegan a Izabal.",
    badge="Observado",
)

pais_mig = None
if foco:
    candidato = SURVEY_NATIONALITY_MAP.get(foco, foco)
    pais_mig = candidato if candidato in paises_mig else None
etiqueta_mig = pais_mig if pais_mig else "todos los mercados"
if foco and not pais_mig:
    st.caption(f"'{foco}' no tiene serie propia en la base de migración desde 2023 "
               "(queda dentro de una agrupación): se muestra el total.")

serie = mig[mig["País"].eq(pais_mig)] if pais_mig else mig
serie = serie.groupby("fecha")["viajeros"].sum()
serie = serie.reindex(pd.date_range(serie.index.min(), serie.index.max(), freq="MS"))

fig = go.Figure()
fig.add_scatter(x=serie.index, y=serie.values, mode="lines", name="Visitantes",
                line=dict(color=PALETA["info"], width=2),
                hovertemplate="%{x|%b %Y}<br>%{y:,.0f} visitantes<extra></extra>")
fig.add_vrect(x0="2020-03-01", x1="2021-12-31", fillcolor=PALETA["neutro"], opacity=0.08, line_width=0,
              annotation_text="Pandemia", annotation_position="top left",
              annotation_font=dict(size=11, color=PALETA["neutro"]))
fig.add_vrect(x0=ini, x1=fin + pd.offsets.MonthEnd(0), fillcolor=PALETA["primario"], opacity=0.07,
              line_width=0, annotation_text="Período filtrado", annotation_position="top right",
              annotation_font=dict(size=11, color=PALETA["primario"]))
fig.add_vline(x=pd.Timestamp("2023-01-01").timestamp() * 1000, line_dash="dot", line_color=PALETA["neutro"],
              annotation_text="Quiebre metodológico", annotation_position="bottom right",
              annotation_font=dict(size=11, color=PALETA["neutro"]))
estilo(fig, ALTURA_GRANDE, y="Visitantes por mes", leyenda=False)
titulo_grafico(fig, f"Entran {serie.mean():,.0f} visitantes al mes por estas fronteras ({etiqueta_mig})")
st.plotly_chart(fig, width="stretch")

per = serie[(serie.index >= ini) & (serie.index <= fin)].dropna()
previo = serie.reindex(per.index - pd.DateOffset(years=1))
ok = previo.notna().to_numpy()
var = per[ok].sum() / previo[ok].sum() - 1 if ok.any() and previo[ok].sum() else np.nan
st.markdown(
    f'<div style="font-size:0.85rem;color:{PALETA["neutro"]};margin-top:-4px;">'
    f"**{per.mean():,.0f}** visitantes/mes en el período · "
    f"variación interanual **{'n/c' if np.isnan(var) else f'{var:+.1%}'}** · "
    f"**{len(per)}** meses con dato"
    "</div>",
    unsafe_allow_html=True,
)

with st.expander("📜 Serie histórica de visitantes por las fronteras marítimas de Izabal (2009–2016)",
                 expanded=False):
    dm = get("destination_monthly")
    h = dm.groupby("fecha")["viajeros"].sum()
    h = h.reindex(pd.date_range(h.index.min(), "2026-06-01", freq="MS"))
    fig = go.Figure(go.Scatter(x=h.index, y=h.values, mode="lines",
                               line=dict(color=PALETA["info"], width=2),
                               hovertemplate="%{x|%b %Y}<br>%{y:,.0f}<extra></extra>"))
    estilo(fig, ALTURA, y="Visitantes por mes", leyenda=False)
    st.plotly_chart(fig, width="stretch")
    advertencia(
        "Puerto Barrios, Livingston y Santo Tomás solo registran visitantes (turista/excursionista) "
        "entre 2009 y 2016; en 2022 no hay ninguna fila y desde 2023 solo se registra 'Viajero' "
        "(tránsito). El vacío posterior es falta de registro, no ausencia de visitantes."
    )
    nt = get("nationality_top")
    st.dataframe(nt.rename(columns={"viajeros": "visitantes 2009–2016"}), hide_index=True, width="stretch")

nota(
    "**Cómo leer este módulo.** La encuesta no tiene factor de expansión, así que nunca se multiplica "
    "por la migración para obtener visitantes de Izabal (regla 6). Las cifras absolutas vienen solo "
    "de Migración y miden entradas al país."
)
