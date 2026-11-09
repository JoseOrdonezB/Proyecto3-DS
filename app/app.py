"""Página principal del Observatorio de Inteligencia Turística.

Ejecutar desde la raíz del proyecto:
    streamlit run app/app.py
"""

import sys
from pathlib import Path

# Asegura que la raíz del proyecto esté en el path (para importar src y app)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from app.components.data import get
from app.components.kpis import PALETA

st.set_page_config(
    page_title="Observatorio de Inteligencia Turística",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Observatorio de Inteligencia Turística")
st.caption(
    "**Grupo 5 · Río Dulce y Livingston, Izabal** — Conectividad Fluvial y Embudo de Transferencia  \n"
    "CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II 2026"
)

# ---------------------------------------------------------------------------
# Resumen de fuentes
# ---------------------------------------------------------------------------
st.subheader("Fuentes de datos")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        "**1. Base de migración oficial**  \n"
        "`Base_Migracion_2009-2026jun.xlsx`  \n"
        "Conteos por frontera, mes, vía y tipo de viajero.  \n"
        "Cobertura: ene 2009 – jun 2026."
    )
with col2:
    st.markdown(
        "**2. Índice de ocupación hotelera**  \n"
        "`indice_ocupacion_mensual_2023_2025_1.csv`  \n"
        "Ocupación mensual por departamento.  \n"
        "Cobertura: 2023 – 2025."
    )
with col3:
    st.markdown(
        "**3. BD complementaria (encuesta)**  \n"
        "`BD_COMPLEMENTARIA` (parquet)  \n"
        "Encuesta diaria de turismo, sin factor de expansión.  \n"
        "Cobertura: oct 2021 – ago 2026."
    )

# ---------------------------------------------------------------------------
# Calidad de datos (limitaciones documentadas)
# ---------------------------------------------------------------------------
st.subheader("Cobertura y limitaciones clave")

calidad = get("data_quality")
corredor = calidad[calidad["segmento"].str.contains(
    "Puerto Barrios|Livingston|Santo Tomás|Puerto Quetzal|Mundo Maya", case=False
)]
st.dataframe(corredor, width="stretch", hide_index=True)

st.warning(
    "Las fronteras marítimas de Izabal (Puerto Barrios y Livingston) solo tienen "
    "**visitantes (Turista/Excursionista) entre 2009 y 2016**. De 2023 en adelante "
    "únicamente registran **'Viajero'** (tránsito / trasbordo). Los cruceros están "
    "presentes hasta 2022. Esta discontinuidad se documenta en la memoria técnica.",
    icon="⚠️",
)

# ---------------------------------------------------------------------------
# Navegación
# ---------------------------------------------------------------------------
st.subheader("Módulos del observatorio")

st.markdown(
    """
    El dashboard está organizado en **4 módulos temáticos** (uno por integrante):

    | Módulo | Responsable | Contenido |
    |---|---|---|
    | **1. Monitor de Demanda y Mercados Emisores** | _por asignar_ | KPIs, turista vs excursionista, top nacionalidades |
    | **2. Dinámica Temporal, Eventos y Pronóstico** | _por asignar_ | Series, efecto feriados, pronóstico 2026 |
    | **3. Oferta Hotelera y Desagregación Territorial** | _por asignar_ | Ocupación, ventana Sep–Dic 2025, subdestinos |
    | **4. Conectividad Fluvial y Embudo de Transferencia** | _por asignar_ | Corredor, tránsito, cruceros, embudo |

    Usa el menú lateral para navegar entre módulos.
    """
)

# ---------------------------------------------------------------------------
# Resumen de datos procesados
# ---------------------------------------------------------------------------
with st.expander("📦 Resumen de los datos procesados"):
    from src.data import resumen

    st.dataframe(resumen(), width="stretch", hide_index=True)
