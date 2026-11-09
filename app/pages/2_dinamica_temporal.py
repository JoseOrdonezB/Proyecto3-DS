"""Módulo 2: Dinámica Temporal, Eventos y Pronóstico Predictivo.

Responsable: _por asignar_
Objetivo: serie temporal, efecto feriados, patrón semanal, pronóstico de
ocupación de Izabal para 2026 y validación con métricas de error.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.data import get
from app.components.kpis import advertencia, nota, titulo_modulo

st.set_page_config(page_title="M2 · Dinámica Temporal", page_icon="📈", layout="wide")

titulo_modulo(
    "📈 Módulo 2 · Dinámica Temporal, Eventos y Pronóstico",
    "Serie temporal, patrón semanal, efecto feriados y pronóstico de ocupación 2026.",
)

# ---------------------------------------------------------------------------
# Serie mensual de visitantes (migración)
# ---------------------------------------------------------------------------
st.subheader("Serie mensual de visitantes (base oficial)")

destino = get("destination_monthly")
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

# ---------------------------------------------------------------------------
# Serie diaria (encuesta)
# ---------------------------------------------------------------------------
st.subheader("Serie diaria de la encuesta — Izabal / Caribe")

diaria = get("survey_izabal_daily")
fig = px.line(
    diaria,
    x="fecha",
    y="registros",
    color_discrete_sequence=["#5B8E7D"],
)
fig.update_layout(height=350, xaxis_title="Día", yaxis_title="Registros")
st.plotly_chart(fig, width="stretch")

nota(
    "La encuesta es **muestral** (sin factor de expansión): la serie diaria se "
    "interpreta como tendencia relativa, no como totales absolutos."
)

# ---------------------------------------------------------------------------
# Patrón semanal
# ---------------------------------------------------------------------------
st.subheader("Patrón semanal (día de la semana)")

# Se reconstruye el día de la semana desde la serie diaria
diaria = diaria.copy()
diaria["dia"] = pd.to_datetime(diaria["fecha"]).dt.day_name()
orden = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
semanal = (
    diaria.groupby("dia", as_index=False)["registros"].sum()
    .set_index("dia")
    .reindex(orden)
    .reset_index()
)
fig = px.bar(
    semanal,
    x="dia",
    y="registros",
    color_discrete_sequence=["#F4A259"],
)
fig.update_layout(height=300, xaxis_title="Día de la semana", yaxis_title="Registros")
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Pronóstico (pendiente Fase 3)
# ---------------------------------------------------------------------------
st.subheader("Pronóstico de ocupación de Izabal para 2026")

advertencia(
    "El pronóstico se implementa en la **Fase 3**: perfil estacional de la "
    "migración + modelo de ocupación, con validación formal (MAPE / RMSE / MAE) "
    "sobre 2024–2025. Las cifras estimadas se mostrarán en estilo diferenciado y "
    "rotuladas como **'Estimación'**."
)

st.markdown(
    """
    **Pendiente:**
    - [ ] Perfil estacional mensual desde la base de migración.
    - [ ] Modelo de ocupación (STL / ETS / Prophet) para Izabal.
    - [ ] Backtest 2024–2025 y métricas de error (MAPE, RMSE, MAE).
    - [ ] Imputación de ene–feb 2026 (y proyección del resto del año).
    - [ ] Efecto feriados: lift porcentual frente al día regular promedio.
    """
)
