"""Módulo 4: Monitor Especializado del Destino — Conectividad Fluvial y Embudo de
Transferencia.

Reto del Grupo 5: Río Dulce y Livingston, Izabal.

La historia que cuenta este módulo, en cuatro pasos:

    1. El corredor marítimo **no tiene embudo medible**: en Puerto Barrios,
       Livingston y Santo Tomás los visitantes y el tránsito nunca coinciden en
       un mismo mes.
    2. El embudo **sí** se mide en las fronteras terrestres, y dos de ellas
       concentran la mayor parte del flujo hacia Izabal.
    3. Ese flujo se reparte en una **cadena de nodos**: cada frontera alimenta
       un nodo del corredor y cada nodo se alcanza con un modo distinto.
    4. El tránsito del corredor es **estructural, no estacional**: hay que
       planificarlo todos los días del año.

Bases de datos:
    - Migración (ABSOLUTA): entradas al país por frontera y tipo de viajero.
    - Encuesta (MUESTRAL, sin factor de expansión): destino, subdestino, medio
      de transporte y frontera de entrada. Solo se lee como proporción (regla 6).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.charts import colores_foco, estilo, pct_texto, titulo_grafico
from app.components.data import get
from app.components.kpis import advertencia, nota
from app.components.layout import (
    ALTURA,
    ALTURA_GRANDE,
    bloque,
    caveat,
    insight,
    kpis,
    modulo,
    seccion,
)
from app.components.theme import PALETA
from src.analysis import embudo as E

st.set_page_config(page_title="M4 · Conectividad Fluvial", page_icon="🚢", layout="wide")

perfil = get("maritime_flow_profile")
transferencia = get("survey_transfer_rate")
flujo_nodo = get("survey_border_node_flow")
nodo_transporte = get("survey_node_transport")
transito = get("destination_transit_monthly")
corredor = get("corridor_share")
itinerarios = get("survey_itinerarios")
mig = get("migration_monthly")

transferencia["anio"] = transferencia["anio"].astype(str)
transito["fecha"] = pd.to_datetime(transito["fecha"])
corredor["fecha"] = pd.to_datetime(corredor["fecha"])
mig["fecha"] = pd.to_datetime(mig["fecha"])

maritimas = perfil[perfil["es_destino_maritimo"]]
MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# --- Cifras que sostienen los titulares -------------------------------------
solape_mar = int(maritimas["meses_solape"].sum())
meses_vis = int(maritimas["meses_visitantes"].sum())
meses_tra = int(maritimas["meses_transito"].sum())
tr_todos = transferencia[transferencia["anio"].eq("Todos")]
top2 = tr_todos.nlargest(2, "peso_en_izabal")
cuota_top2 = float(top2["peso_en_izabal"].sum())
nombre_top2 = " y ".join(top2["frontera_nombre"].tolist())
peso_nodos = flujo_nodo.groupby("nodo")["registros"].sum()
peso_rio = float(peso_nodos.get("Río Dulce", 0) / peso_nodos.sum())
peso_iz = float(peso_nodos.get("Izabal (genérico)", 0) / peso_nodos.sum())
peso_pb = float(peso_nodos.get("Puerto Barrios", 0) / peso_nodos.sum())
puente_pb = ", ".join(
    n for n in ["El Florido", "Melchor de Mencos", "San Cristóbal", "El Carmen"]
    if (flujo_nodo["frontera_nombre"].eq(n) & flujo_nodo["nodo"].eq("Puerto Barrios")).any()
)
serie_tr = transito.groupby("fecha")["viajeros"].sum().sort_index()
cv_tr = float(serie_tr.std() / serie_tr.mean())
mes_min_tr = MESES_ES[int(serie_tr.idxmin().month) - 1]
mes_max_tr = MESES_ES[int(serie_tr.idxmax().month) - 1]

modulo(
    "🚢 Módulo 4 · Conectividad Fluvial y Embudo de Transferencia",
    "¿Por dónde entra el flujo hacia Río Dulce y Livingston, hacia dónde se dirige y "
    "qué debería hacer INGUAT?",
    f"El corredor marítimo **no tiene embudo medible**: en sus tres fronteras los visitantes "
    f"y el tránsito nunca coinciden en un mismo mes. El embudo se mide en las fronteras "
    f"terrestres, donde **dos de ellas concentran el {cuota_top2:.0%}** del flujo hacia el destino.",
)

kpis(
    [
        ("Meses de solape marítimo", f"{solape_mar}", "no hay embudo medible", "alerta"),
        ("Meses con visitantes", f"{meses_vis:,}", "en las 3 fronteras marítimas", "info"),
        ("Meses con tránsito", f"{meses_tra:,}", "en las mismas 3 fronteras", "info"),
        ("Fronteras medibles", f"{int(perfil['embudo_medible'].sum())} de {len(perfil)}",
         "con visitantes y tránsito a la vez", "primario"),
    ]
)

# ---------------------------------------------------------------------------
# Filtro enlazado
# ---------------------------------------------------------------------------
fronteras_op = ["Todas"] + sorted(flujo_nodo["frontera_nombre"].dropna().unique())
if st.session_state.get("m4_frontera") not in fronteras_op:
    st.session_state["m4_frontera"] = "Todas"

f1, f2, f3 = st.columns([2.1, 1.4, 2.2])
with f1:
    frontera_sel = st.selectbox(
        "Frontera de entrada (encuesta)", fronteras_op, key="m4_frontera",
        help="Filtra el embudo, la cadena de nodos y el modo de transporte.",
    )
with f2:
    anios_tr = ["Todos"] + sorted(a for a in transferencia["anio"].unique() if a != "Todos")
    anio_sel = st.selectbox("Periodo del embudo", anios_tr, key="m4_anio")
with f3:
    foco = None if frontera_sel == "Todas" else frontera_sel
    st.markdown(
        f"**Frontera activa:** {frontera_sel} · **Periodo:** {anio_sel}"
        + ("" if foco else " · se muestra el agregado de todas las fronteras")
    )


# ---------------------------------------------------------------------------
# 1 · El hallazgo de fondo
# ---------------------------------------------------------------------------
seccion(
    f"En el corredor marítimo los visitantes y el tránsito nunca coinciden en el mismo mes "
    f"({solape_mar} meses de solape)",
    "Línea sólida: visitantes (turista + excursionista). Línea punteada: tránsito ('Viajero'). "
    "La base oficial dejó de medir visitantes en la vía marítima en 2016.",
    badge="Observado",
)

fig = go.Figure()
for i, f in enumerate(maritimas["Frontera"]):
    color = [PALETA["primario"], PALETA["secundario"], PALETA["acento"]][i % 3]
    s = mig[(mig["Frontera"].eq(f)) & mig["Tipo de Viajero"].isin(["Turista", "Excursionista"])]
    v = s.groupby("fecha")["viajeros"].sum()
    fig.add_scatter(x=v.index, y=v.values, mode="lines", name=f, line=dict(color=color, width=2),
                    hovertemplate=f"{f}<br>%{{x|%b %Y}}<br>%{{y:,.0f}} visitantes<extra></extra>")
    t = mig[(mig["Frontera"].eq(f)) & mig["Tipo de Viajero"].eq("Viajero")]
    tv = t.groupby("fecha")["viajeros"].sum()
    fig.add_scatter(x=tv.index, y=tv.values, mode="lines", name=f"{f} · tránsito",
                    line=dict(color=color, width=2, dash="dot"),
                    hovertemplate=f"{f} (tránsito)<br>%{{x|%b %Y}}<br>%{{y:,.0f}} viajeros<extra></extra>")
fig.add_vrect(x0="2009-01-01", x1="2016-12-31", fillcolor=PALETA["primario"], opacity=0.06,
              line_width=0, annotation_text="Solo visitantes", annotation_position="top left",
              annotation_font=dict(size=11, color=PALETA["primario"]))
fig.add_vrect(x0="2017-01-01", x1="2022-12-31", fillcolor=PALETA["neutro"], opacity=0.10,
              line_width=0, annotation_text="Sin registro", annotation_position="top left",
              annotation_font=dict(size=11, color=PALETA["neutro"]))
fig.add_vrect(x0="2023-01-01", x1="2026-06-30", fillcolor=PALETA["estimacion"], opacity=0.07,
              line_width=0, annotation_text="Solo tránsito", annotation_position="top right",
              annotation_font=dict(size=11, color=PALETA["estimacion"]))
estilo(fig, ALTURA_GRANDE, y="Viajeros por mes")
titulo_grafico(fig, "El hueco de 2017 a 2022 no es una caída de visitantes: es un cambio de cobertura")
st.plotly_chart(fig, width="stretch")

insight(
    f"Las tres fronteras marítimas registran {meses_vis:,} meses con visitantes y {meses_tra:,} "
    f"con tránsito, pero **ninguno de esos dos flujos ocurre en el mismo mes**. Por eso no se "
    f"calcula una tasa de transferencia para el corredor marítimo: sería mezclar dos periodos "
    f"disjuntos. El embudo sí es medible en las fronteras terrestres."
)

with st.expander("📋 Qué medir en cada frontera (cobertura por tipo de flujo)", expanded=False):
    d = E.descomposicion_corredor(perfil)
    st.dataframe(
        d[["Frontera", "medida_disponible", "meses_visitantes", "meses_transito", "meses_solape",
           "periodo"]]
        .rename(columns={
            "Frontera": "Frontera", "medida_disponible": "Medida disponible",
            "meses_visitantes": "Meses visitantes", "meses_transito": "Meses tránsito",
            "meses_solape": "Solape", "periodo": "Periodo con dato",
        }),
        hide_index=True, width="stretch",
    )
    st.caption(
        "'Solape' = meses con visitantes y tránsito a la vez. Cero significa que esa frontera "
        "**no admite una tasa de transferencia** calculable con esta base."
    )


# ---------------------------------------------------------------------------
# 2 · El embudo medible
# ---------------------------------------------------------------------------
seccion(
    f"{nombre_top2} concentran el {cuota_top2:.0%} del flujo de visitantes hacia Izabal",
    "De las personas que la encuesta registra en cada frontera, qué proporción declara destino "
    "Izabal/Caribe. Es una proporción de la muestra, con su intervalo de confianza al 95 %.",
    badge="Muestral",
)

tr_sel = tr_todos if anio_sel == "Todos" else transferencia[transferencia["anio"].eq(anio_sel)]
if foco:
    tr_sel = tr_sel[tr_sel["frontera_nombre"].eq(foco)]


def _al_clic_embudo():
    ev = st.session_state.get("m4_click")
    puntos = (ev or {}).get("selection", {}).get("points", []) if ev else []
    if puntos:
        valor = puntos[0].get("y") or puntos[0].get("label")
        st.session_state["m4_frontera"] = (
            "Todas" if valor == st.session_state.get("m4_frontera") else valor
        )


col_t2, col_t3 = st.columns([1.45, 1])
with col_t2:
    if tr_sel.empty:
        st.info("No hay registros de encuesta para esta combinación de filtros.")
    else:
        t_ord = tr_sel.sort_values("tasa_transferencia", ascending=True)
        fig = go.Figure()
        fig.add_bar(
            x=t_ord["tasa_transferencia"], y=t_ord["frontera_nombre"], orientation="h",
            marker_color=colores_foco(t_ord["frontera_nombre"], foco),
            error_x=dict(
                type="data", symmetric=False,
                array=(t_ord["ic_sup"] - t_ord["tasa_transferencia"]).clip(lower=0),
                arrayminus=(t_ord["tasa_transferencia"] - t_ord["ic_inf"]).clip(lower=0),
            ),
            customdata=t_ord[["registros_total", "registros_izabal"]].to_numpy(),
            hovertemplate=(
                "%{y}<br>Tasa hacia Izabal: %{x:.1%}"
                "<br>%{customdata[1]:,.0f} de %{customdata[0]:,.0f}.Unsafe"
                "<extra></extra>"
            ),
            text=[f"{v:.0%}" for v in t_ord["tasa_transferencia"]],
            textposition="outside", textfont=dict(color=PALETA["texto"]),
        )
        estilo(fig, ALTURA_GRANDE, x="% que declara destino Izabal", leyenda=False)
        fig.update_xaxes(tickformat=".0%", range=[0, max(0.02, t_ord["tasa_transferencia"].max() * 1.4)])
        fig.update_layout(clickmode="event+select", dragmode=False)
        titulo_grafico(fig, "Poco del flujo que entra por tierra continúa hacia Izabal")
        st.plotly_chart(fig, width="stretch", key="m4_click", on_select=_al_clic_embudo,
                        selection_mode="points")
        st.caption("Barras con **intervalo de Wilson al 95 %**: el ancho indica cuánta confianza "
                   "merece cada proporción. Clic en una barra para filtrar el módulo.")

with col_t3:
    p = tr_sel.sort_values("peso_en_izabal", ascending=True)
    if p.empty:
        st.info("Sin datos.")
    else:
        fig = go.Figure(go.Bar(
            x=p["peso_en_izabal"], y=p["frontera_nombre"], orientation="h",
            marker_color=colores_foco(p["frontera_nombre"], foco),
            text=pct_texto(p["peso_en_izabal"]), textposition="outside",
            textfont=dict(color=PALETA["texto"]),
            hovertemplate="%{y}: %{x:.1%} de la muestra de Izabal<extra></extra>",
        ))
        estilo(fig, ALTURA_GRANDE, x="% de la muestra", leyenda=False)
        fig.update_xaxes(tickformat=".0%", range=[0, p["peso_en_izabal"].max() * 1.35], visible=False)
        titulo_grafico(fig, "El peso de cada frontera dentro del destino")
        st.plotly_chart(fig, width="stretch")

insight(
    f"De cada 100 personas que la encuesta registra en {nombre_top2}, "
    f"**{cuota_top2:.0f} terminan con destino Izabal/Caribe**. En el resto de fronteras la tasa "
    f"es marginal: la mayoría del flujo que entra por tierra pasa de largo. Cualquier "
    f"interrupción en esas dos fronteras se lleva por delante una parte desproporcionada "
    f"del destino."
)

with st.expander("📊 El contexto absoluto: cuánta gente entra por cada frontera", expanded=False):
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
        "La migración y la encuesta **no se multiplican**: la encuesta no tiene factor de expansión, "
        "así que su tasa no se convierte en un total de visitantes (regla 6)."
    )


# ---------------------------------------------------------------------------
# 3 · La cadena de conectividad
# ---------------------------------------------------------------------------
seccion(
    f"Río Dulce concentra el {peso_rio:.0%} de los visitantes del destino",
    "Cada frontera de entrada alimenta un nodo del corredor. El ancho de la arista es el peso "
    "de la muestra; el tamaño del nodo, su papel en el conjunto.",
    badge="Muestral",
)

grafo = E.grafo_conectividad(flujo_nodo, min_registros=10)
nodos, aristas = grafo["nodos"], grafo["aristas"]
if foco:
    aristas = aristas[
        aristas["origen"].eq(foco)
        | aristas["destino"].isin(
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
        fig.add_trace(go.Scatter(
            x=[xs_f[r.origen], xs_n[r.destino]], y=[ys_f[r.origen], ys_n[r.destino]],
            mode="lines", line=dict(color=PALETA["acento"], width=1 + 7 * r.registros / max_reg),
            opacity=0.75, hoverinfo="skip", showlegend=False,
        ))
    tam = {n: 9 + 34 * nodos.loc[nodos["nodo"].eq(n), "registros"].iloc[0] / max_reg
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
    fig.update_xaxes(range=[-0.5, 1.85], showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(range=[-1, max(len(xs_f), len(nodos_destino))], showgrid=False,
                     showticklabels=False, zeroline=False)
    estilo(fig, ALTURA_GRANDE, leyenda=False)
    fig.update_layout(margin=dict(l=10, r=10, t=64, b=10))
    titulo_grafico(
        fig,
        "Las fronteras del nororiente alimentan Río Dulce; las del sur, Puerto Barrios",
        "■ frontera de entrada · ● nodo del corredor (turquesa = nodo de agua)",
    )
    st.plotly_chart(fig, width="stretch")

insight(
    f"El destino no se recibe por una sola puerta: **Río Dulce ({peso_rio:.0%})**, Izabal genérico "
    f"({peso_iz:.0%}) y Puerto Barrios ({peso_pb:.0%}) reparten la muestra, y cada frontera entra por "
    f"un nodo distinto. Puerto Barrios aparece además como **nodo intermedio**: {puente_pb} "
    f"llegan por tierra y continúan hacia él."
)

with st.expander("🗺️ La cadena completa: frontera × nodo y modo de transporte", expanded=False):
    flujo_filtrado = flujo_nodo if not foco else flujo_nodo[flujo_nodo["frontera_nombre"].eq(foco)]
    piv = (
        flujo_filtrado.pivot_table(index="frontera_nombre", columns="nodo", values="registros",
                                   aggfunc="sum", fill_value=0)
    )
    if not piv.empty:
        fig = go.Figure(go.Heatmap(
            z=piv.to_numpy(), x=list(piv.columns), y=list(piv.index),
            colorscale=[[0, "#F2F5F6"], [0.5, PALETA["acento"]], [1, PALETA["primario"]]],
            hovertemplate="%{y} → %{x}<br>%{z:,.0f} registros<extra></extra>",
            colorbar=dict(title="reg.", thickness=12, outlinewidth=0),
        ))
        estilo(fig, ALTURA_GRANDE, leyenda=False)
        fig.update_xaxes(tickangle=-30, showgrid=False)
        fig.update_yaxes(showgrid=False, autorange="reversed")
        titulo_grafico(fig, "De dónde viene cada nodo")
        st.plotly_chart(fig, width="stretch")
        st.caption("Los nodos **no se suman**: un mismo visitante puede recorrer varios (regla 4).")

    nt = nodo_transporte if not foco else nodo_transporte[
        nodo_transporte["nodo"].isin(
            flujo_nodo.loc[flujo_nodo["frontera_nombre"].eq(foco), "nodo"].unique()
        )
    ]
    if not nt.empty:
        st.markdown("**Medio de transporte por nodo**")
        top_nodos = nt.groupby("nodo", as_index=False)["registros"].sum().nlargest(4, "registros")
        cols = st.columns(len(top_nodos))
        for col, nodo in zip(cols, top_nodos["nodo"]):
            with col:
                sub = nt[nt["nodo"].eq(nodo)].head(6)
                fig = go.Figure(go.Bar(
                    x=sub["participacion_nodo"], y=sub["tipo_transporte"], orientation="h",
                    marker_color=PALETA["primario"] if nodo in E.NODOS_AGUA else PALETA["acento"],
                    text=pct_texto(sub["participacion_nodo"]), textposition="outside",
                    textfont=dict(color=PALETA["texto"]),
                    customdata=sub["registros"],
                    hovertemplate="%{y}: %{x:.1%}<br>%{customdata:,.0f} registros<extra></extra>",
                ))
                estilo(fig, ALTURA, leyenda=False)
                fig.update_xaxes(tickformat=".0%", range=[0, sub["participacion_nodo"].max() * 1.4],
                                 visible=False)
                fig.update_layout(margin=dict(l=10, r=10, t=34, b=10))
                fig.update_layout(title=dict(text=nodo, font=dict(size=13, color=PALETA["texto"])))
                st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# 4 · Los cuellos de botella
# ---------------------------------------------------------------------------
seccion(
    f"El tránsito del corredor se mueve poco a lo largo del año (CV {cv_tr:.2f}): es estructural, "
    f"no estacional",
    f"Tránsito de las fronteras marítimas, 2023–jun 2026. Mínimo en {mes_min_tr}, máximo en "
    f"{mes_max_tr}. La barra turquesa marca la participación de Izabal en el corredor de visitantes "
    f"(2009–2016, la única ventana con las 5 fronteras comparables).",
    badge="Observado",
)

col_tb, col_sh = st.columns([1.35, 1])
with col_tb:
    idx = serie_tr / serie_tr.mean()
    fig = go.Figure()
    fig.add_bar(x=serie_tr.index, y=serie_tr.values, marker_color=PALETA["secundario"],
                customdata=idx.values,
                hovertemplate="%{x|%b %Y}<br>%{y:,.0f} viajeros<br>Índice estacional: %{customdata:.2f}<extra></extra>")
    fig.add_hline(y=serie_tr.mean(), line_dash="dot", line_color=PALETA["primario"],
                  annotation_text=f"Media {serie_tr.mean():,.0f}", annotation_position="top left")
    estilo(fig, ALTURA_GRANDE, y="Viajeros (tránsito) por mes", leyenda=False)
    titulo_grafico(fig, "La demanda de traslado no se concentra en temporada")
    st.plotly_chart(fig, width="stretch")

with col_sh:
    fig = go.Figure()
    fig.add_scatter(x=corredor["fecha"], y=corredor["participacion"], mode="lines+markers",
                    line=dict(color=PALETA["primario"], width=2), marker=dict(size=6),
                    customdata=corredor[["n_fronteras_con_dato"]].to_numpy(),
                    hovertemplate=(
                        "%{x|%b %Y}<br>Participación de Izabal: %{y:.1%}"
                        "<br>Fronteras del corredor con dato: %{customdata[0]}<extra></extra>"
                    ))
    incompleto = corredor[~corredor["corredor_completo"]]
    if not incompleto.empty:
        fig.add_vrect(
            x0=incompleto["fecha"].min(), x1=incompleto["fecha"].max(),
            fillcolor=PALETA["neutro"], opacity=0.12, line_width=0,
            annotation_text="Corredor incompleto: sin dato de visitantes de Izabal",
            annotation_position="top left", annotation_font=dict(size=11, color=PALETA["neutro"]),
        )
    estilo(fig, ALTURA_GRANDE, y="Participación de Izabal", y_pct=True, leyenda=False)
    titulo_grafico(fig, "Izabal alrededor del 70 % del corredor, mientras hubo dato")
    st.plotly_chart(fig, width="stretch")

insight(
    f"El tránsito tiene un coeficiente de variación de **{cv_tr:.2f}**: baja a {mes_min_tr} y sube a "
    f"{mes_max_tr}, sin la concentración estacional de la demanda turística. La carga del corredor es "
    f"permanente, así que **la capacidad hay que ensured todo el año** y no por temporadas."
)

with st.expander("🧭 Itinerarios multi-parada: qué se puede y qué no se puede concluir", expanded=False):
    it = itinerarios.copy()
    multi = it[it["es_multi_parada"]] if "es_multi_parada" in it.columns else it.iloc[0:0]
    st.dataframe(
        it.head(12)[["combo", "registros", "participacion", "n_paradas"]]
        .rename(columns={"combo": "Combinación de códigos", "registros": "Registros",
                          "participacion": "% del campo informado", "n_paradas": "Paradas"}),
        hide_index=True, width="stretch",
        column_config={"% del campo informado": st.column_config.NumberColumn(format="percent")},
    )
    caveat(
        f"**Supuesto documentado.** La encuesta registra {int(multi['registros'].sum()):,} itinerarios "
        f"de dos o más paradas, pero los códigos (`320`, `340`, `222`, `484`) pertenecen a un "
        f"catálogo por base (V10/V11/V12) **que no viene con diccionario**. Se reporta la estructura "
        f"de co-ocurrencia, que es un hecho, pero **no se les asigna nombre**: varias lecturas son "
        f"consistentes con los datos y nombrarlos sería inventar. Pedir el catálogo a INGUAT es una "
        f"de las recomendaciones."
    )


# ---------------------------------------------------------------------------
# 5 · Recomendaciones
# ---------------------------------------------------------------------------
seccion(
    "Cinco recomendaciones para INGUAT, cada una con el dato que la respalda",
    "Las genera el código a partir de las tablas de este módulo, así que el texto y su evidencia "
    "no pueden divergir.",
)

recs = E.recomendaciones_inguat({
    "perfil": perfil,
    "flujo": E.cadena_flujo(flujo_nodo),
    "transporte": nodo_transporte,
    "transito": transito,
    "itinerarios": itinerarios,
    "transferencia": tr_todos,
})
if not recs:
    st.info("No hay datos suficientes para generar recomendaciones.")
else:
    for r in recs:
        color = {"Alta": PALETA["alerta"], "Media": PALETA["secundario"]}.get(r["prioridad"], PALETA["neutro"])
        with st.container(border=True):
            c1, c2 = st.columns([0.8, 6])
            with c1:
                st.markdown(
                    f'<div style="text-align:center"><span style="border:1.5px solid {color};'
                    f'color:{PALETA["texto"]};border-radius:10px;padding:2px 10px;'
                    f'font-size:0.72rem;font-weight:600;">'
                    f'<span style="color:{color}">●</span> {r["prioridad"]}</span></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f"**{r['titulo']}**")
                st.markdown(f"<span style='color:{PALETA['neutro']}'>🧭 {r['hallazgo']}</span>",
                            unsafe_allow_html=True)
                st.markdown(f"✅ {r['recomendacion']}")

nota(
    "**Cómo leer este módulo.** La migración es la única fuente absoluta y mide entradas al país, "
    "no visitantes de Izabal. La encuesta es muestral y sin factor de expansión: sus cifras son "
    "proporciones. En ningún punto se multiplica una por la otra (regla 6). Los nodos y "
    "subdestinos del corredor **no se suman** para obtener un total (regla 4), porque un mismo "
    "visitante puede recorrer varios."
)
