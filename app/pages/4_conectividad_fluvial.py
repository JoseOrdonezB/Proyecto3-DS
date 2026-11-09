"""Módulo 4: Monitor Especializado del Destino.

Reto del Grupo 5: Conectividad Fluvial y Embudo de Transferencia.
Responsable: _por asignar_

Objetivo: analizar el corredor Río Dulce–Livingston como embudo de
transferencia entre las fronteras de entrada (terrestres y marítimas) y el
destino Izabal / Caribe.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.data import get
from app.components.kpis import advertencia, kpi, nota, titulo_modulo

st.set_page_config(page_title="M4 · Conectividad Fluvial", page_icon="🚢", layout="wide")

titulo_modulo(
    "🚢 Módulo 4 · Conectividad Fluvial y Embudo de Transferencia",
    "Reto especializado del Grupo 5: el corredor Río Dulce–Livingston como embudo.",
)

# ---------------------------------------------------------------------------
# Flujo de visitantes por frontera del corredor
# ---------------------------------------------------------------------------
st.subheader("Visitantes por frontera del corredor (2009–2016)")

corredor = get("corridor_monthly")
fig = px.line(
    corredor,
    x="fecha",
    y="viajeros",
    color="Frontera",
    markers=True,
)
fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Visitantes")
st.plotly_chart(fig, width="stretch")

advertencia(
    "Los visitantes por vía marítima solo están disponibles entre 2009 y 2016. "
    "La caída posterior corresponde a un cambio de cobertura, no a una caída real."
)

# ---------------------------------------------------------------------------
# Tránsito / trasbordo (Viajero) 2023+
# ---------------------------------------------------------------------------
st.subheader("Tránsito / trasbordo por frontera (2023–2026)")

transito = get("destination_transit_monthly")
fig = px.line(
    transito,
    x="fecha",
    y="viajeros",
    color="Frontera",
    markers=True,
)
fig.update_layout(height=350, xaxis_title="Mes", yaxis_title="Viajeros (tránsito)")
st.plotly_chart(fig, width="stretch")

nota(
    "'Viajero' cruza la frontera sin calificar como visitante (trabajo fronterizo, "
    "tránsito, carga, comercio de alta frecuencia). Es la medida del **embudo de "
    "transferencia**."
)

# ---------------------------------------------------------------------------
# Cruceros
# ---------------------------------------------------------------------------
st.subheader("Cruceristas (2009–2022)")

cruceros = get("destination_cruise_monthly")
if not cruceros.empty:
    fig = px.bar(
        cruceros,
        x="fecha",
        y="viajeros",
        color="Frontera",
    )
    fig.update_layout(height=300, xaxis_title="Mes", yaxis_title="Cruceristas")
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Sin datos de cruceros.")

# ---------------------------------------------------------------------------
# Embudo: frontera -> destino (encuesta)
# ---------------------------------------------------------------------------
st.subheader("Embudo de transferencia: frontera de entrada → destino")

embudo = get("survey_funnel")
# Enfocar en Izabal / Caribe
embudo_iz = embudo[embudo["nuevo_destino"].eq("Izabal/Caribe")]
embudo_iz = embudo_iz.sort_values("registros", ascending=False).head(12)
fig = px.bar(
    embudo_iz,
    x="registros",
    y="frontera_nombre",
    orientation="h",
    color_discrete_sequence=["#0E7C86"],
)
fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Transporte y subdestinos
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Medio de transporte (encuesta)")
    transporte = get("survey_transport")
    fig = px.pie(
        transporte,
        names="tipo_transporte",
        values="registros",
        color_discrete_sequence=px.colors.sequential.Teal,
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Subdestinos en Izabal / Caribe")
    subdestinos = get("survey_subdestino").head(8)
    fig = px.bar(
        subdestinos,
        x="registros",
        y="subdestino",
        orientation="h",
        color_discrete_sequence=["#5B8E7D"],
    )
    fig.update_layout(height=300, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

st.markdown(
    """
    **Pendiente:**
    - [ ] Cuantificar el embudo: entradas por frontera vs visitantes que llegan al destino.
    - [ ] Diferenciar flujo turístico (Livingston) vs flujo comercial/de transferencia (Puerto Barrios).
    - [ ] Conectividad fluvial: relación entre Puerto Barrios, Santo Tomás y Río Dulce.
    - [ ] Estacionalidad del corredor y cuellos de botella.
    - [ ] Recomendaciones para INGUAT.
    """
)
