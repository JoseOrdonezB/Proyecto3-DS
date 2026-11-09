"""Carga de datos procesados con caché de Streamlit."""

import pandas as pd
import streamlit as st

from src.data import load


@st.cache_data(show_spinner="Cargando datos procesados…")
def get(nombre: str) -> pd.DataFrame:
    """Carga un conjunto procesado y lo cachea por nombre."""
    return load(nombre)
