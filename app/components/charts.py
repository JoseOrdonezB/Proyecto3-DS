"""Helpers de gráficos compartidos (Plotly) con la paleta del observatorio.

Reglas que aplican aquí (ver app/components/theme.py):
    - Un solo eje Y por gráfico (nunca doble eje).
    - Color categórico solo para la serie en foco; el resto en neutro.
    - Texto en tinta neutra, nunca en el color de la serie.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.theme import PALETA

GRID = "#E5E7EB"
FONDO = "rgba(0,0,0,0)"

BADGE_COLOR = {
    "Observado": PALETA["info"],
    "Muestral": PALETA["primario"],
    "Estimación": PALETA["estimacion"],
}


def estilo(fig: go.Figure, alto: int = 360, x: str | None = None, y: str | None = None,
           y_pct: bool = False, leyenda: bool = True) -> go.Figure:
    """Aplica el estilo base: fondo limpio, rejilla recesiva, hover unificado."""
    fig.update_layout(
        height=alto,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor=FONDO,
        plot_bgcolor=FONDO,
        font=dict(color=PALETA["texto"], size=13),
        hoverlabel=dict(bgcolor="white", font_size=13),
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
        bargap=0.25,
    )
    fig.update_xaxes(title=x, showgrid=False, linecolor=GRID)
    fig.update_yaxes(title=y, gridcolor=GRID, zeroline=False)
    if y_pct:
        fig.update_yaxes(tickformat=".0%")
    return fig


def badge(tipo: str) -> str:
    """Etiqueta HTML del tipo de dato: Observado / Muestral / Estimación."""
    color = BADGE_COLOR.get(tipo, PALETA["neutro"])
    return (
        f"<span style='border:1.5px solid {color};color:{PALETA['texto']};"
        f"border-radius:10px;padding:1px 8px;font-size:0.75rem;font-weight:600'>"
        f"<span style='color:{color}'>●</span> {tipo}</span>"
    )


def encabezado(pregunta: str, tipo: str | None = None, ayuda: str | None = None) -> None:
    """Subtítulo de sección redactado como pregunta de gestión, con badge del dato."""
    st.markdown(f"#### {pregunta}")
    partes = [badge(tipo)] if tipo else []
    if ayuda:
        partes.append(f"<span style='color:{PALETA['neutro']};font-size:0.875rem'>{ayuda}</span>")
    if partes:
        st.markdown(" &nbsp;".join(partes), unsafe_allow_html=True)


def marcar_hueco(fig: go.Figure, fecha, texto: str = "Sin encuesta", fila=None, col=None) -> None:
    """Sombrea un mes sin dato (la ausencia no es cero)."""
    f = pd.Timestamp(fecha)
    kw = dict(row=fila, col=col) if fila else {}
    fig.add_vrect(
        x0=f - pd.Timedelta(days=15), x1=f + pd.Timedelta(days=15),
        fillcolor=PALETA["neutro"], opacity=0.12, line_width=0,
        annotation_text=texto, annotation_position="top left",
        annotation_font=dict(size=11, color=PALETA["neutro"]), **kw,
    )


def pct_texto(valores) -> list[str]:
    """Etiquetas de porcentaje legibles: '<1%' para valores pequeños."""
    return [("<1%" if 0 < v < 0.01 else f"{v:.0%}") for v in valores]


def colores_foco(categorias, foco=None) -> list[str]:
    """Primario para la categoría en foco (o todas si no hay foco); neutro para el resto."""
    if not foco:
        return [PALETA["primario"]] * len(categorias)
    return [PALETA["primario"] if c == foco else "#C7CCD1" for c in categorias]
