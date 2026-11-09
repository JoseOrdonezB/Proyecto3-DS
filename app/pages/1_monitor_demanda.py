"""Módulo 1: Monitor de Demanda y Mercados Emisores (Diagnóstico Macro).

Responsable: _por asignar_
Objetivo: KPIs principales, segmentación turista vs excursionista y
mercados emisores (top 10 nacionalidades, nacionales y extranjeros por separado).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.data import get
from app.components.kpis import advertencia, kpi, nota, titulo_modulo

st.set_page_config(page_title="M1 · Demanda y Mercados", page_icon="📊", layout="wide")

titulo_modulo(
    "📊 Módulo 1 · Monitor de Demanda y Mercados Emisores",
    "Diagnóstico macro del destino: visitantes, segmentación y mercados emisores.",
)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
destino = get("destination_monthly")
stay_izabal = get("survey_stay_izabal")
nacionalidades = get("nationality_top")

total_visitantes = destino["viajeros"].sum()
meses = destino["fecha"].nunique()
promedio_mensual = total_visitantes / meses if meses else 0.0

stay_dict = dict(zip(stay_izabal["indicador"], stay_izabal["valor"]))
prop_pernocta = stay_dict.get("proporcion_pernocta", 0.0)
estadia_media = stay_dict.get("estadia_media_ponderada", 0.0)

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Visitantes totales (2009–2016)", f"{total_visitantes:,.0f}")
with c2:
    kpi("Promedio mensual", f"{promedio_mensual:,.0f}")
with c3:
    kpi("Proporción pernocta (encuesta)", f"{prop_pernocta:.1%}")
with c4:
    kpi("Estadía media ponderada", f"{estadia_media:.2f} días")

nota(
    "La estadía media ponderada y la proporción de pernocta provienen de la "
    "**encuesta** (muestral, sin factor de expansión). Los visitantes absolutos "
    "provienen de la base oficial de migración."
)

# ---------------------------------------------------------------------------
# Top nacionalidades
# ---------------------------------------------------------------------------
st.subheader("Top 10 mercados emisores")

col_ext, col_nac = st.columns(2)
with col_ext:
    extranjeros = nacionalidades[nacionalidades["tipo"].eq("Extranjero")]
    fig = px.bar(
        extranjeros,
        x="viajeros",
        y="País",
        orientation="h",
        color_discrete_sequence=["#0E7C86"],
        title="Extranjeros",
    )
    fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

with col_nac:
    nacionales = nacionalidades[nacionalidades["tipo"].eq("Nacional")]
    fig = px.bar(
        nacionales,
        x="viajeros",
        y="País",
        orientation="h",
        color_discrete_sequence=["#F4A259"],
        title="Nacionales",
    )
    fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

advertencia(
    "Los nacionales incorporan factor de expansión, por lo que se reportan por "
    "separado (regla del proyecto)."
)

# ---------------------------------------------------------------------------
# Serie histórica de visitantes
# ---------------------------------------------------------------------------
st.subheader("Serie mensual de visitantes del destino")

serie = destino.groupby("fecha", as_index=False)["viajeros"].sum()
fig = px.line(
    serie,
    x="fecha",
    y="viajeros",
    markers=True,
    color_discrete_sequence=["#0E7C86"],
)
fig.update_layout(height=350, xaxis_title="Mes", yaxis_title="Visitantes")
st.plotly_chart(fig, width="stretch")

advertencia(
    "La serie de visitantes absolutos cubre **2009–2016**. De 2017 a 2022 no hay "
    "registros para las fronteras marítimas de Izabal y desde 2023 solo se registra "
    "'Viajero' (tránsito). No se muestran como cero: son períodos sin dato."
)

# ---------------------------------------------------------------------------
# Pendiente
# ---------------------------------------------------------------------------
st.subheader("📝 Pendiente para este módulo")
st.markdown(
    """
    - [ ] Días-persona totales (migración + encuesta).
    - [ ] Segmentación turista vs excursionista con absolutos y relativos.
    - [ ] Top 10 nacionalidades con nacionalidad vs residencia.
    - [ ] Comparación con la encuesta para 2022–2026 (caracterización).
    - [ ] Visualización adicional que el grupo considere relevante.
    """
)
