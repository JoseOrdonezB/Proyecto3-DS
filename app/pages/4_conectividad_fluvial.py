"""Módulo 4: Monitor Especializado del Destino — Conectividad Fluvial y Embudo de
Transferencia.

Reto del Grupo 5: Río Dulce y Livingston, Izabal.

Preguntas de gestión que responde:
    1. ¿Se puede medir el embudo de transferencia con los datos oficiales?
    2. Por las fronteras que sí se pueden medir, ¿qué porcentaje del flujo
       continúa hacia Izabal?
    3. ¿Por dónde entra el visitante y hacia qué nodo del corredor se dirige?
    4. ¿Cómo se llega a cada nodo y qué cuellos de botella tiene el corredor?
    5. ¿Qué se le puede recomendar a INGUAT?

Visualización enlazada: el selector de frontera de entrada (o un clic en la barra
del embudo) filtra las secciones 2, 3 y 4 del módulo.

Bases de datos:
    - Migración (ABSOLUTA): entradas al país por frontera y tipo de viajero.
    - Encuesta (MUESTRAL, sin factor de expansión): destino, subdestino, medio de
      transporte y frontera de entrada. Solo se lee como proporción (regla 6).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.charts import colores_foco, encabezado, estilo, pct_texto
from app.components.data import get
from app.components.kpis import advertencia, kpi, nota, titulo_modulo
from app.components.theme import PALETA
from src.analysis import embudo as E
from src.config import IZABAL_BORDERS

st.set_page_config(page_title="M4 · Conectividad Fluvial", page_icon="🚢", layout="wide")

titulo_modulo(
    "🚢 Módulo 4 · Conectividad Fluvial y Embudo de Transferencia",
    "¿Por dónde entra el flujo hacia Río Dulce y Livingston, hacia dónde se dirige y "
    "qué se le puede recomendar a INGUAT? Elige una frontera de entrada para filtrar el módulo.",
)


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
perfil = get("maritime_flow_profile")
transferencia = get("survey_transfer_rate")
flujo_nodo = get("survey_border_node_flow")
nodo_transporte = get("survey_node_transport")
transito = get("destination_transit_monthly")
corredor = get("corridor_share")
itinerarios = get("survey_itinerarios")
mig = get("migration_monthly")

# 'anio' mezcla el agregado 'Todos' con los años: se trabaja como texto.
transferencia["anio"] = transferencia["anio"].astype(str)
transito["fecha"] = pd.to_datetime(transito["fecha"])
corredor["fecha"] = pd.to_datetime(corredor["fecha"])
mig["fecha"] = pd.to_datetime(mig["fecha"])

maritimas = perfil[perfil["es_destino_maritimo"]]
alimentadoras = perfil[perfil["es_alimentadora"]]

# --- Selector enlazado (frontera de entrada) --------------------------------
fronteras_op = ["Todas"] + sorted(flujo_nodo["frontera_nombre"].dropna().unique())
if st.session_state.get("m4_frontera") not in fronteras_op:
    st.session_state["m4_frontera"] = "Todas"

f1, f2, f3 = st.columns([2, 1.4, 2.2])
with f1:
    frontera_sel = st.selectbox(
        "Frontera de entrada (encuesta)", fronteras_op, key="m4_frontera",
        help="Filtra el embudo, la cadena de nodos y el modo de transporte.",
    )
with f2:
    anios_tr = ["Todos"] + sorted(
        a for a in transferencia["anio"].unique() if a != "Todos"
    )
    anio_sel = st.selectbox(
        "Periodo del embudo", anios_tr, key="m4_anio",
        help="'Todos' agrupa toda la ventana de la encuesta.",
    )
with f3:
    foco = None if frontera_sel == "Todas" else frontera_sel
    st.markdown(
        f"**Frontera activa:** {frontera_sel} · **Periodo:** {anio_sel}"
        + ("" if foco else " · mostrándose el agregado de todas las fronteras")
    )


# ---------------------------------------------------------------------------
# 1. ¿Se puede medir el embudo? — el hallazgo de fondo
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿Se puede medir el embudo de transferencia con los datos oficiales?",
    "Observado",
    "Meses en que cada frontera registra visitantes (turista/excursionista) y tránsito "
    "('Viajero') en la base oficial de Migración.",
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Meses de solape (marítimo)", f"{int(maritimas['meses_solape'].sum())}",
        help="Meses en que una frontera marítima registra visitantes Y tránsito a la vez. "
             "0 = la tasa de transferencia del corredor marítimo no es calculable.")
with c2:
    kpi("Meses con visitantes", f"{int(maritimas['meses_visitantes'].sum()):,}",
        help="Suma de meses con registro de visitante en las 3 fronteras marítimas de Izabal.")
with c3:
    kpi("Meses con tránsito", f"{int(maritimas['meses_transito'].sum()):,}",
        help="Suma de meses con registro de 'Viajero' en las mismas 3 fronteras.")
with c4:
    kpi("Fronteras medibles", f"{int(perfil['embudo_medible'].sum())} de {len(perfil)}",
        help="Fronteras donde visitantes y tránsito coexisten en al menos un mes.")

advertencia(
    "**El corredor marítimo no tiene embudo medible.** Puerto Barrios, Livingston y Santo "
    "Tomás registran visitantes entre 2009 y 2016 y tránsito entre 2023 y 2026, pero "
    "**nunca en el mismo mes**. Calcular una 'tasa de transferencia' para ellas sería "
    "inventar un número: no hay ningún mes donde ambos flujos coexistan. Lo que sí es "
    "medible es el corredor **terrestre** alimentador, que es lo que se analiza abajo."
)

# Las dos series desfasadas, para ver el hueco
col_g, col_t = st.columns([1.5, 1])
with col_g:
    fig = go.Figure()
    for i, f in enumerate(maritimas["Frontera"]):
        s = mig[(mig["Frontera"].eq(f)) & mig["Tipo de Viajero"].isin(["Turista", "Excursionista"])]
        v = s.groupby("fecha")["viajeros"].sum()
        color = [PALETA["primario"], PALETA["secundario"], PALETA["acento"]][i % 3]
        fig.add_scatter(x=v.index, y=v.values, mode="lines", name=f, line=dict(color=color, width=2),
                        hovertemplate=f"{f}<br>%{{x|%b %Y}}<br>%{{y:,.0f}} visitantes<extra></extra>")
        t = mig[(mig["Frontera"].eq(f)) & mig["Tipo de Viajero"].eq("Viajero")]
        tv = t.groupby("fecha")["viajeros"].sum()
        fig.add_scatter(x=tv.index, y=tv.values, mode="lines", name=f"{f} · tránsito",
                        line=dict(color=color, width=2, dash="dot"),
                        hovertemplate=f"{f} (tránsito)<br>%{{x|%b %Y}}<br>%{{y:,.0f}} viajeros<extra></extra>")
    fig.add_vrect(x0="2023-01-01", x1="2026-06-30", fillcolor=PALETA["estimacion"], opacity=0.06,
                  line_width=0, annotation_text="Solo tránsito", annotation_position="top left",
                  annotation_font=dict(size=11, color=PALETA["estimacion"]))
    fig.add_vrect(x0="2009-01-01", x1="2016-12-31", fillcolor=PALETA["primario"], opacity=0.06,
                  line_width=0, annotation_text="Solo visitantes", annotation_position="top right",
                  annotation_font=dict(size=11, color=PALETA["primario"]))
    fig.add_vrect(x0="2017-01-01", x1="2022-12-31", fillcolor=PALETA["neutro"], opacity=0.10,
                  line_width=0, annotation_text="Sin registro", annotation_position="top left",
                  annotation_font=dict(size=11, color=PALETA["neutro"]))
    estilo(fig, 360, y="Por mes", leyenda=True)
    st.plotly_chart(fig, width="stretch")
    st.caption("Línea sólida = visitantes (turista + excursionista). Línea punteada = tránsito ('Viajero').")

with col_t:
    encabezado("Qué medir en cada frontera", "Observado",
               "Cobertura de cada tipo de flujo y si ambos coexisten.")
    d = E.descomposicion_corredor(perfil)
    st.dataframe(
        d[["Frontera", "medida_disponible", "meses_visitantes", "meses_transito", "meses_solape"]]
        .rename(columns={
            "Frontera": "Frontera", "medida_disponible": "Medida disponible",
            "meses_visitantes": "Meses visitantes", "meses_transito": "Meses tránsito",
            "meses_solape": "Solape",
        }),
        hide_index=True, width="stretch", height=380,
    )
    st.caption("'Solape' = meses con visitantes y tránsito a la vez. Cero = embudo no calculable.")


# ---------------------------------------------------------------------------
# 2. El embudo que sí se puede medir (tasa de transferencia)
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿Qué porcentaje del flujo que entra por cada frontera continúa hacia Izabal?",
    "Muestral",
    "Sobre los visitantes **encuestados** en cada frontera: qué proporción declara "
    "destino Izabal/Caribe. Es una proporción de la muestra, no un total del destino.",
)

tr_sel = transferencia[transferencia["anio"].eq(anio_sel)].copy()
if foco:
    tr_sel = tr_sel[tr_sel["frontera_nombre"].eq(foco)]


def _al_clic_embudo():
    """Clic en una barra del embudo -> fija la frontera (visualización enlazada)."""
    ev = st.session_state.get("m4_click")
    puntos = (ev or {}).get("selection", {}).get("points", []) if ev else []
    if puntos:
        valor = puntos[0].get("y") or puntos[0].get("label")
        st.session_state["m4_frontera"] = (
            "Todas" if valor == st.session_state.get("m4_frontera") else valor
        )


if tr_sel.empty:
    st.info("No hay registros de encuesta para esta combinación de filtros.")
else:
    tr_sel = tr_sel.sort_values("tasa_transferencia", ascending=True)
    fig = go.Figure()
    fig.add_bar(
        x=tr_sel["tasa_transferencia"], y=tr_sel["frontera_nombre"], orientation="h",
        marker_color=colores_foco(tr_sel["frontera_nombre"], foco),
        error_x=dict(
            type="data",
            symmetric=False,
            array=(tr_sel["ic_sup"] - tr_sel["tasa_transferencia"]).clip(lower=0),
            arrayminus=(tr_sel["tasa_transferencia"] - tr_sel["ic_inf"]).clip(lower=0),
        ),
        customdata=tr_sel[["registros_total", "registros_izabal", "migracion_visitantes",
                           "migracion_transito", "meses_encuesta"]].to_numpy(),
        hovertemplate=(
            "%{y}<br>Tasa hacia Izabal: %{x:.1%}"
            "<br>%{customdata[1]:,.0f} de %{customdata[0]:,.0f} encuestados"
            "<br>Migración en el mismo período: %{customdata[2]:,.0f} visitantes / "
            "%{customdata[3]:,.0f} tránsito<extra></extra>"
        ),
        text=[f"{v:.0%}" for v in tr_sel["tasa_transferencia"]],
        textposition="outside", textfont=dict(color=PALETA["texto"]),
    )
    estilo(fig, 380, x="% que declara destino Izabal", leyenda=False)
    fig.update_xaxes(tickformat=".0%", range=[0, min(1.0, tr_sel["tasa_transferencia"].max() * 1.35)])
    fig.update_layout(clickmode="event+select", dragmode=False)
    st.plotly_chart(fig, width="stretch", key="m4_click", on_select=_al_clic_embudo,
                    selection_mode="points")
    st.caption(
        "Barras con **intervalo de Wilson al 95%**: el ancho indica cuánta confianza "
        "merece cada proporción según el tamaño de muestra. Haz clic en una barra para filtrar."
    )

    col_t2, col_t3 = st.columns([1.2, 1])
    with col_t2:
        encabezado("El contexto absoluto", "Observado",
                   "Migración registrada en esa frontera durante los mismos meses que la encuesta operó.")
        if not tr_sel.empty:
            st.dataframe(
                tr_sel[["frontera_nombre", "meses_encuesta", "registros_total", "registros_izabal",
                        "migracion_visitantes", "migracion_transito"]]
                .rename(columns={
                    "frontera_nombre": "Frontera", "meses_encuesta": "Meses con encuesta",
                    "registros_total": "Encuestados", "registros_izabal": "Con destino Izabal",
                    "migracion_visitantes": "Migración visitantes", "migracion_transito": "Migración tránsito",
                }),
                hide_index=True, width="stretch",
                column_config={
                    "Migración visitantes": st.column_config.NumberColumn(format="%,d"),
                    "Migración tránsito": st.column_config.NumberColumn(format="%,d"),
                },
            )
            st.caption(
                "La migración y la encuesta **no se multiplican**: la encuesta no tiene factor "
                "de expansión, así que su tasa no se convierte en un total de visitantes."
            )
    with col_t3:
        encabezado("El peso de cada frontera en el destino", "Muestral",
                   "Cuánto de la muestra de Izabal/Caribe entra por cada frontera.")
        p = tr_sel.sort_values("peso_en_izabal", ascending=True)
        if not p.empty:
            fig = go.Figure(go.Bar(
                x=p["peso_en_izabal"], y=p["frontera_nombre"], orientation="h",
                marker_color=colores_foco(p["frontera_nombre"], foco),
                text=pct_texto(p["peso_en_izabal"]), textposition="outside",
                textfont=dict(color=PALETA["texto"]),
                hovertemplate="%{y}: %{x:.1%} de la muestra de Izabal<extra></extra>",
            ))
            estilo(fig, 300, x="% de la muestra", leyenda=False)
            fig.update_xaxes(tickformat=".0%", range=[0, p["peso_en_izabal"].max() * 1.3], visible=False)
            st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# 3. La cadena de conectividad fluvial
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿Por dónde entra el visitante y hacia qué nodo del corredor se dirige?",
    "Muestral",
    "Flujo desde la frontera de entrada hacia el nodo del corredor (Río Dulce, Puerto Barrios, "
    "Livingston y los nodos terrestres). El ancho de la arista es el peso muestral.",
)

flujo_filtrado = flujo_nodo if not foco else flujo_nodo[flujo_nodo["frontera_nombre"].eq(foco)]
grafo = E.grafo_conectividad(flujo_nodo, min_registros=10)

col_gr, col_hm = st.columns([1.15, 1])
with col_gr:
    nodos = grafo["nodos"]
    aristas = grafo["aristas"]
    if foco:
        aristas = aristas[
            aristas["origen"].eq(foco) | aristas["destino"].isin(
                flujo_nodo.loc[flujo_nodo["frontera_nombre"].eq(foco), "nodo"].unique()
            )
        ]
    if aristas.empty:
        st.info("Sin aristas con peso suficiente para este filtro.")
    else:
        fig = go.Figure()
        xs_f = {n: 0.0 for n in sorted(aristas["origen"].unique())}
        ys_f = {n: i for i, n in enumerate(sorted(aristas["origen"].unique()))}
        nodos_destino = sorted(aristas["destino"].unique())
        xs_n = {n: 1.0 for n in nodos_destino}
        ys_n = {n: i for i, n in enumerate(nodos_destino)}
        max_reg = aristas["registros"].max()
        for r in aristas.itertuples():
            fig.add_annotation(
                x=0.5, y=(ys_f[r.origen] + ys_n[r.destino]) / 2, ax=0, ay=0,
                xref="x", yref="y", axref="x", ayref="y", showarrow=False, text="",
            )
            fig.add_trace(go.Scatter(
                x=[xs_f[r.origen], xs_n[r.destino]], y=[ys_f[r.origen], ys_n[r.destino]],
                mode="lines", line=dict(color=PALETA["acento"], width=1 + 7 * r.registros / max_reg),
                opacity=0.75, hoverinfo="skip", showlegend=False,
            ))
        tam = {n: 8 + 34 * nodos.loc[nodos["nodo"].eq(n), "registros"].iloc[0] / max_reg
               for n in nodos_destino}
        color_nodo = [PALETA["primario"] if n in E.NODOS_AGUA else PALETA["neutro"] for n in nodos_destino]
        fig.add_trace(go.Scatter(
            x=[xs_n[n] for n in nodos_destino], y=[ys_n[n] for n in nodos_destino],
            mode="markers+text", marker=dict(
                size=[tam[n] for n in nodos_destino], color=color_nodo, line=dict(color="white", width=2)),
            text=nodos_destino, textposition="middle right",
            textfont=dict(color=PALETA["texto"], size=12),
            customdata=[[n, nodos.loc[nodos["nodo"].eq(n), "registros"].iloc[0]] for n in nodos_destino],
            hovertemplate="%{customdata[0]}<br>%{customdata[1]:,.0f} registros<extra></extra>",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[xs_f[n] for n in xs_f], y=[ys_f[n] for n in xs_f],
            mode="markers+text", marker=dict(size=11, color=PALETA["secundario"], symbol="square"),
            text=list(xs_f.keys()), textposition="middle left",
            textfont=dict(color=PALETA["texto"], size=11),
            hoverinfo="skip", showlegend=False,
        ))
        fig.update_xaxes(range=[-0.45, 1.75], showgrid=False, showticklabels=False, zeroline=False)
        fig.update_yaxes(range=[-1, max(len(xs_f), len(nodos_destino))], showgrid=False,
                         showticklabels=False, zeroline=False)
        estilo(fig, 420, leyenda=False)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("■ frontera de entrada · ● nodo del corredor (verde azulado = nodo de agua)")

with col_hm:
    encabezado("Frontera × nodo", "Muestral",
               "Registros de la encuesta. Los nodos no se suman: un visitante puede recorrer varios.")
    piv = (
        flujo_filtrado.pivot_table(index="frontera_nombre", columns="nodo", values="registros",
                                   aggfunc="sum", fill_value=0)
    )
    if piv.empty:
        st.info("Sin datos para esta frontera.")
    else:
        fig = go.Figure(go.Heatmap(
            z=piv.to_numpy(), x=list(piv.columns), y=list(piv.index),
            colorscale=[[0, "#F2F5F6"], [0.5, PALETA["acento"]], [1, PALETA["primario"]]],
            hovertemplate="%{y} → %{x}<br>%{z:,.0f} registros<extra></extra>",
            colorbar=dict(title="reg.", thickness=12, outlinewidth=0),
        ))
        estilo(fig, 420, leyenda=False)
        fig.update_xaxes(tickangle=-35, showgrid=False)
        fig.update_yaxes(showgrid=False, autorange="reversed")
        st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# 4. Cómo se llega a cada nodo
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿Con qué se llega a cada nodo del corredor?",
    "Muestral",
    "Medio de transporte declarado por los visitantes con destino Izabal/Caribe.",
)

nota(
    "**Limitación estructural:** la encuesta no tiene una categoría de transporte acuático "
    "(lancha, barco, lanchaje). Por eso la conectividad fluvial **no se mide como modo de "
    "transporte**, sino como cadena de nodos. Lo que sí es observable es el medio tierra "
    "o aire con el que se llega al nodo."
)

nt = nodo_transporte if not foco else nodo_transporte[
    nodo_transporte["nodo"].isin(
        flujo_nodo.loc[flujo_nodo["frontera_nombre"].eq(foco), "nodo"].unique()
    )
]
if nt.empty:
    st.info("Sin datos de transporte para esta frontera.")
else:
    top = nt.groupby("nodo", as_index=False).agg(registros=("registros", "sum")).nlargest(4, "registros")
    nodos_grafico = top["nodo"].tolist()
    cols = st.columns(len(nodos_grafico))
    for col, nodo in zip(cols, nodos_grafico):
        with col:
            sub = nt[nt["nodo"].eq(nodo)].head(6)
            tot = sub["registros"].sum()
            fig = go.Figure(go.Bar(
                x=sub["participacion_nodo"], y=sub["tipo_transporte"], orientation="h",
                marker_color=PALETA["primario"] if nodo in E.NODOS_AGUA else PALETA["acento"],
                text=pct_texto(sub["participacion_nodo"]), textposition="outside",
                textfont=dict(color=PALETA["texto"]),
                customdata=sub["registros"],
                hovertemplate="%{y}: %{x:.1%}<br>%{customdata:,.0f} registros<extra></extra>",
            ))
            estilo(fig, 300, leyenda=False)
            fig.update_xaxes(tickformat=".0%", range=[0, sub["participacion_nodo"].max() * 1.35], visible=False)
            fig.update_layout(title=dict(text=nodo, font=dict(size=13, color=PALETA["texto"])),
                              margin=dict(t=34))
            st.plotly_chart(fig, width="stretch")
            st.caption(f"{tot:,.0f} registros en la muestra")


# ---------------------------------------------------------------------------
# 5. El corredor y sus cuellos de botella
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿El corredor tiene cuellos de botella?",
    "Observado",
    "Tránsito registrado en las fronteras marítimas de Izabal (2023–jun 2026) y participación "
    "de Izabal en el corredor de visitantes (2009–2016, única ventana con datos comparables).",
)

col_tb, col_sh = st.columns([1.4, 1])
with col_tb:
    tr = transito.copy()
    serie = tr.groupby("fecha")["viajeros"].sum().sort_index()
    total = serie.sum()
    cv = serie.std() / serie.mean() if serie.mean() else np.nan
    idx = (serie / serie.mean()) if serie.mean() else serie

    encabezado("Tránsito del corredor marítimo", "Observado",
               f"Total {total:,.0f} viajeros · {len(serie)} meses · CV {cv:.2f}")
    fig = go.Figure()
    fig.add_bar(x=serie.index, y=serie.values, marker_color=PALETA["secundario"],
                customdata=idx.values,
                hovertemplate="%{x|%b %Y}<br>%{y:,.0f} viajeros<br>Índice estacional: %{customdata:.2f}<extra></extra>")
    fig.add_hline(y=serie.mean(), line_dash="dot", line_color=PALETA["primario"],
                  annotation_text=f"Media {serie.mean():,.0f}", annotation_position="top left")
    estilo(fig, 340, y="Viajeros (tránsito) por mes", leyenda=False)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"El tránsito tiene un coeficiente de variación de **{cv:.2f}**: la columna de "
        "altura es el índice estacional (1 = media del período). Un valle en "
        f"**{serie.idxmin().strftime('%B')}** y un pico en **{serie.idxmax().strftime('%B')}** "
        "indican presión de temporada, no un cuello estructural."
    )

with col_sh:
    encabezado("Participación de Izabal en el corredor", "Observado",
               "Ventana 2009–2016: la única en que las 5 fronteras del corredor registran "
               "visitantes. El vacío posterior es falta de registro, no cero de visitantes.")
    c = corredor.copy()
    fig = go.Figure()
    fig.add_scatter(x=c["fecha"], y=c["participacion"], mode="lines+markers",
                    line=dict(color=PALETA["primario"], width=2),
                    marker=dict(size=6),
                    customdata=c[["n_fronteras_con_dato", "corredor_completo"]].to_numpy(),
                    hovertemplate=(
                        "%{x|%b %Y}<br>Participación de Izabal: %{y:.1%}"
                        "<br>Fronteras del corredor con dato: %{customdata[0]}<extra></extra>"
                    ))
    incompleto = c[~c["corredor_completo"]]
    if not incompleto.empty:
        fig.add_vrect(
            x0=incompleto["fecha"].min(), x1=incompleto["fecha"].max(),
            fillcolor=PALETA["neutro"], opacity=0.12, line_width=0,
            annotation_text="Corredor incompleto: sin dato de visitantes de Izabal",
            annotation_position="top left", annotation_font=dict(size=11, color=PALETA["neutro"]),
        )
    estilo(fig, 340, y="Participación de Izabal", y_pct=True, leyenda=False)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Donde no hay registro de visitantes de Izabal, la participación queda **vacía** "
        "(regla 1: la ausencia de dato no es cero)."
    )


# ---------------------------------------------------------------------------
# 6. Recomendaciones para INGUAT
# ---------------------------------------------------------------------------
st.divider()
encabezado(
    "¿Qué debería hacer INGUAT con este corredor?",
    "Observado",
    "Cada recomendación se construye a partir de los datos de este módulo: el texto y su "
    "evidencia no pueden divergir.",
)

recs = E.recomendaciones_inguat({
    "perfil": perfil,
    "flujo": E.cadena_flujo(flujo_nodo),
    "transporte": nodo_transporte,
    "transito": transito,
    "itinerarios": itinerarios,
})
if not recs:
    st.info("No hay datos suficientes para generar recomendaciones.")
else:
    for r in recs:
        color = {"Alta": PALETA["alerta"], "Media": PALETA["secundario"]}.get(r["prioridad"], PALETA["neutro"])
        with st.container(border=True):
            c1, c2 = st.columns([0.9, 6])
            with c1:
                st.markdown(
                    f"<div style='text-align:center'><span style='border:1.5px solid {color};"
                    f"color:{PALETA['texto']};border-radius:10px;padding:2px 10px;"
                    f"font-size:0.75rem;font-weight:600'>"
                    f"<span style='color:{color}'>●</span> {r['prioridad']}</span></div>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f"**{r['titulo']}**")
                st.markdown(f"🧭 *Hallazgo* — {r['hallazgo']}")
                st.markdown(f"✅ *Acción* — {r['recomendacion']}")

nota(
    "**Cómo leer este módulo.** La migración es la única fuente absoluta y mide entradas al "
    "país, no visitantes de Izabal. La encuesta es muestral y sin factor de expansión: sus "
    "cifras son proporciones. En ningún punto se multiplica una por la otra (regla 6). "
    "Los subdestinos y los nodos del corredor **no se suman** para obtener un total "
    "(regla 4), porque un mismo visitante puede recorrer varios."
)
