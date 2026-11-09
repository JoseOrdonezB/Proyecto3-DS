"""Helpers de visualización del dashboard."""

import streamlit as st

# Paleta documentada del observatorio (tonos Caribe / Río Dulce)
PALETA = {
    "primario": "#0E7C86",    # turquesa Caribe
    "secundario": "#F4A259",  # arena cálida
    "acento": "#5B8E7D",      # verde río
    "alerta": "#C0392B",      # rojo coral
    "neutro": "#6C757D",      # gris
    "estimacion": "#9B59B6",  # morado para estimaciones
}


def kpi(label: str, value, delta=None, help: str | None = None) -> None:
    """Tarjeta KPI usando st.metric."""
    st.metric(label=label, value=value, delta=delta, help=help)


def nota(texto: str) -> None:
    """Nota informativa (azul)."""
    st.info(texto, icon="ℹ️")


def advertencia(texto: str) -> None:
    """Advertencia (ámbar)."""
    st.warning(texto, icon="⚠️")


def titulo_modulo(nombre: str, descripcion: str) -> None:
    """Encabezado estándar de módulo."""
    st.title(nombre)
    st.caption(descripcion)
