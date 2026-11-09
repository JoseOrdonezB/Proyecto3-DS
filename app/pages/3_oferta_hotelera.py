"""Módulo 3: Oferta Hotelera y Desagregación Territorial.

Responsable: _por asignar_
Objetivo: ocupación hotelera mensual, ventana coincidente Sep–Dic 2025,
desagregación por subdestinos y tipo de hospedaje.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.data import get
from app.components.kpis import advertencia, kpi, nota, titulo_modulo

st.set_page_config(page_title="M3 · Oferta Hotelera", page_icon="🏨", layout="wide")

titulo_modulo(
    "🏨 Módulo 3 · Oferta Hotelera y Desagregación Territorial",
    "Ocupación hotelera de Izabal, ventana coincidente y subdestinos.",
)

# ---------------------------------------------------------------------------
# Ocupación mensual
# ---------------------------------------------------------------------------
st.subheader("Tasa de ocupación departamental — Izabal (2023–2025)")

ocupacion = get("occupancy_monthly")
fig = px.line(
    ocupacion,
    x="fecha",
    y="indice_ocupacion",
    markers=True,
    color_discrete_sequence=["#0E7C86"],
)
fig.update_layout(
    height=350,
    xaxis_title="Mes",
    yaxis_title="Índice de ocupación",
    yaxis_tickformat=".0%",
)
st.plotly_chart(fig, width="stretch")

# KPIs de ocupacion
c1, c2, c3 = st.columns(3)
with c1:
    kpi("Ocupación promedio", f"{ocupacion['indice_ocupacion'].mean():.1%}")
with c2:
    kpi("Máximo", f"{ocupacion['indice_ocupacion'].max():.1%}")
with c3:
    kpi("Mínimo", f"{ocupacion['indice_ocupacion'].min():.1%}")

# ---------------------------------------------------------------------------
# Ventana coincidente Sep–Dic 2025
# ---------------------------------------------------------------------------
st.subheader("Ventana coincidente (Sep–Dic 2025)")

ventana = ocupacion[
    (ocupacion["fecha"] >= "2025-09-01") & (ocupacion["fecha"] <= "2025-12-01")
]
st.dataframe(ventana, width="stretch", hide_index=True)

nota(
    "La ventana Sep–Dic 2025 es el único período donde coinciden la afluencia y "
    "la ocupación hotelera. Es el cruce analítico obligatorio del módulo."
)

# ---------------------------------------------------------------------------
# Desagregación por subdestinos (encuesta)
# ---------------------------------------------------------------------------
st.subheader("Desagregación por subdestinos (encuesta, Izabal / Caribe)")

subdestinos = get("survey_subdestino")
fig = px.bar(
    subdestinos,
    x="registros",
    y="subdestino",
    orientation="h",
    color_discrete_sequence=["#5B8E7D"],
)
fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, width="stretch")

advertencia(
    "Regla estricta: **no se suman los subdestinos** para obtener el total, ya que "
    "un mismo visitante puede recorrer varios puntos del destino."
)

# ---------------------------------------------------------------------------
# Tipo de hospedaje
# ---------------------------------------------------------------------------
st.subheader("Tipo de hospedaje (encuesta)")

hospedaje = get("survey_lodging")
fig = px.pie(
    hospedaje,
    names="hospedaje",
    values="registros",
    color_discrete_sequence=px.colors.sequential.Teal,
)
fig.update_layout(height=350)
st.plotly_chart(fig, width="stretch")

st.markdown(
    """
    **Pendiente:**
    - [ ] Capacidad instalada (establecimientos, habitaciones, plazas cama) 2022–2025.
    - [ ] Cruzar afluencia vs ocupación en la ventana Sep–Dic 2025.
    - [ ] Comparativa de afluencia relativa entre subdestinos.
    - [ ] Visualización adicional relevante.
    """
)
