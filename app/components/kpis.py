"""Helpers de visualización del dashboard."""

import streamlit as st

# Paleta validada: ver app/components/theme.py (re-exportada por compatibilidad)
from app.components.theme import PALETA  # noqa: F401


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
