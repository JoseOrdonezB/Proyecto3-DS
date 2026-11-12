"""Armazón de presentación común a los 4 módulos del observatorio.

El dashboard se presenta en pantalla: cada módulo debe poder leerse en pocos
minutos y contar una historia. Este módulo fija el esqueleto para que los cuatro
módulos se vean iguales y no acumulen contenido.

Reglas de diseño que aplica:

    1. **Una afirmación por sección.** El título de cada sección ES la
       conclusión, con la cifra dentro. No es un tema ("Ocupación hotelera")
       sino un hallazgo ("Izabal se llena un 22% por encima del promedio
       departamental").
    2. **Máximo 4 KPI visibles por módulo**, siempre en la misma fila, arriba.
       El resto del detalle vive en un `st.expander`.
    3. **Máximo 2 gráficos visibles por sección.** Si hay más, se reparten en
       subsecciones o bajan a detalle.
    4. **Altura constante de gráfico** (300 / 380 px) para que la pantalla
       tenga ritmo y dos gráficos quepan en un mismo plano.
    5. **Scroll, no tabs.** La historia se lee de arriba abajo; el contenido
       secundario se colapsa en `st.expander`.
    6. **Cada gráfico va precedido de una línea de insight** con la lectura
       que se quiere que quede: el docente entiende la conclusión sin tener
       que interpretar la figura.
"""

from __future__ import annotations

import streamlit as st

from app.components.theme import PALETA

# Alturas estándar (px). Mantenerlas iguales da ritmo a la pantalla.
ALTURA = 300
ALTURA_GRANDE = 380
ALTURA_ALTA = 440

# Máximo de tarjetas KPI visibles a la vez.
MAX_KPIS = 4

# Máximo de secciones visibles por módulo (la historia se cuenta en pocas pantallas).
MAX_SECCIONES = 5

# Colores de acento disponibles para tarjetas KPI.
ACENTOS = ("primario", "secundario", "acento", "alerta", "info", "estimacion")


# ---------------------------------------------------------------------------
# Tarjetas KPI
# ---------------------------------------------------------------------------
def kpi_card(label: str, value, pie: str | None = None, acento: str = "primario",
             help: str | None = None) -> None:
    """Tarjeta KPI con estilo propio (no `st.metric`).

    `st.metric` no permite controlar tipografía ni color de acento, y con once
    tarjetas en una página el resultado se ve como una tabla de números. Esta
    tarjeta lleva un borde de acento, la etiqueta en versalitas y el valor en
    grande: se lee como un indicador de observatorio.
    """
    color = PALETA.get(acento, PALETA["primario"])
    titulo = f' title="{help}"' if help else ""
    html = (
        f'<div{titulo} style="border:1px solid #E2E6E9;border-top:3px solid {color};'
        f'border-radius:8px;padding:12px 14px 13px 14px;height:100%;'
        f'background:#FFFFFF;box-sizing:border-box;">'
        f'<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.6px;'
        f'text-transform:uppercase;color:{PALETA["neutro"]};margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:1.65rem;font-weight:700;color:{color};'
        f'line-height:1.15;letter-spacing:-0.4px;">{value}</div>'
    )
    if pie:
        html += (
            f'<div style="font-size:0.75rem;color:{PALETA["neutro"]};margin-top:5px;">{pie}</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def kpis(items: list, columnas: int = MAX_KPIS) -> None:
    """Fila de tarjetas KPI.

    `items` es una lista de tuplas `(label, value)` o
    `(label, value, pie)` o `(label, value, pie, acento)`.

    Si se pasan más de `MAX_KPIS`, se muestran solo los primeros y se avisa:
    la fila de KPI es el ancla visual del módulo, no un tablero de números.
    """
    items = list(items)
    if len(items) > MAX_KPIS:
        st.warning(
            f"Se passaram {len(items)} tarjetas KPI; se muestran solo las {MAX_KPIS} primeras. "
            "El resto debe ir al detalle o a la sección que corresponde.",
            icon="⚠️",
        )
        items = items[:MAX_KPIS]
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value = item[0], item[1]
        pie = item[2] if len(item) > 2 else None
        acento = item[3] if len(item) > 3 else "primario"
        with col:
            kpi_card(label, value, pie=pie, acento=acento)


# ---------------------------------------------------------------------------
# Encabezados
# ---------------------------------------------------------------------------
def modulo(titulo: str, pregunta: str, afirmacion: str = "") -> None:
    """Cabecera estándar de módulo: título, pregunta de gestión y conclusión.

    `afirmacion` es la frase que el presentador dice del módulo. Si no se pasa,
    se usa `pregunta` como titular.
    """
    # Cada página empieza su propio conteo de secciones.
    st.session_state["_layout_secciones"] = 0
    st.title(titulo)
    st.markdown(
        f'<div style="color:{PALETA["neutro"]};font-size:0.95rem;margin:-6px 0 14px 0;">'
        f"{pregunta}</div>",
        unsafe_allow_html=True,
    )
    if afirmacion:
        bloque(
            afirmacion,
            color=PALETA["primario"],
            size="1.02rem",
            fondo="rgba(14,124,134,0.07)",
        )


def seccion(afirmacion: str, subtitulo: str | None = None, badge: str | None = None) -> None:
    """Separador de sección con el titular como afirmación.

    `badge` opcional ("Observado" / "Muestral" / "Estimación") para dejar
    explícito de qué tipo de dato viene la sección.
    """
    n = int(st.session_state.get("_layout_secciones", 0)) + 1
    st.session_state["_layout_secciones"] = n
    if n > MAX_SECCIONES:
        st.warning(
            f"Este módulo ya tiene {n} secciones visibles (el máximo del diseño es "
            f"{MAX_SECCIONES}). Para la presentación, lo que sobra debe bajar a un "
            "`st.expander` de detalle.",
            icon="⚠️",
        )
    st.divider()
    etiq = ""
    if badge:
        etiq = (
            f'<span style="display:inline-block;border:1.5px solid {PALETA["neutro"]};'
            f'color:{PALETA["neutro"]};border-radius:10px;padding:1px 8px;'
            f'font-size:0.7rem;font-weight:600;vertical-align:middle;'
            f'margin-left:10px;">{badge}</span>'
        )
    st.markdown(
        f'<div style="font-size:1.16rem;font-weight:700;color:{PALETA["texto"]};'
        f'margin:2px 0 2px 0;line-height:1.3;">{afirmacion}{etiq}</div>',
        unsafe_allow_html=True,
    )
    if subtitulo:
        st.markdown(
            f'<div style="color:{PALETA["neutro"]};font-size:0.87rem;margin:0 0 12px 0;">'
            f"{subtitulo}</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Bloques de texto
# ---------------------------------------------------------------------------
def bloque(texto: str, color: str | None = None, size: str = "0.95rem",
           fondo: str | None = None) -> None:
    """Bloque destacado con barra de color a la izquierda.

    Sirve para la conclusión de un módulo, una línea de insight o una advertencia
    de método, siempre con la misma forma para que el ojo aprenda a leerlo.
    """
    color = color or PALETA["primario"]
    fondo = fondo or "rgba(0,0,0,0.035)"
    st.markdown(
        f'<div style="border-left:4px solid {color};padding:9px 15px;background:{fondo};'
        f'border-radius:0 6px 6px 0;margin:8px 0;">'
        f'<span style="font-size:{size};color:{PALETA["texto"]};line-height:1.45;">{texto}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


def insight(texto: str) -> None:
    """Línea de lectura de un gráfico: lo que hay que retener.

    Es el recurso que más ayuda en una presentación: la página se entiende sin
    interpretar las figuras.
    """
    bloque(texto, color=PALETA["primario"], size="0.93rem", fondo="rgba(14,124,134,0.06)")


def caveat(texto: str) -> None:
    """Advertencia de método, en el color de la paleta reservado a alertas."""
    bloque(texto, color=PALETA["alerta"], size="0.9rem", fondo="rgba(192,57,43,0.06)")


# ---------------------------------------------------------------------------
# Detalle
# ---------------------------------------------------------------------------
def detalle(etiqueta: str, abierto: bool = False) -> None:
    """Abre un panel de detalle colapsado (contenido secundario del módulo)."""
    return st.expander(etiqueta, expanded=abierto)
