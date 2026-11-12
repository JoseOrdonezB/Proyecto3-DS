"""Página principal del Observatorio de Inteligencia Turística.

Portada e índice: en una presentación esto es la primera pantalla, así que tiene que
contestar de inmediato tres preguntas:

    1. ¿Qué es este observatorio y qué pregunta responde?
    2. ¿Qué encontraron? (cuatro cifras, una por módulo)
    3. ¿Por dónde se navega?

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
from app.components.layout import ALTURA, bloque, caveat, insight, kpis, modulo
from app.components.theme import PALETA

st.set_page_config(
    page_title="Observatorio de Inteligencia Turística",
    page_icon="🧭",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Cifras de cabecera (una por módulo)
# ---------------------------------------------------------------------------
cubo = get("survey_izabal_cube")
stay = get("survey_stay_izabal")
occ = get("occupancy_monthly")
perfil = get("maritime_flow_profile")
métricas = get("forecast_metrics")

valores = dict(zip(stay["indicador"], stay["valor"]))
prop_pernocta = float(valores.get("proporcion_pernocta", 0.0))
estadia = float(valores.get("estadia_media_ponderada", 0.0))
ocupacion = float(occ["indice_ocupacion"].mean())

_m = métricas[métricas["objetivo"].eq("ocupacion")]
_mape = float(_m.loc[_m["ganador"], "mape_comunes"].iloc[0]) if len(_m) else float("nan")
_modelo = str(_m.loc[_m["ganador"], "modelo"].iloc[0]) if len(_m) else "—"

maritimas = perfil[perfil["es_destino_maritimo"]]
solape = int(maritimas["meses_solape"].sum())

tr = get("survey_transfer_rate")
tr_todos = tr[tr["anio"].astype(str).eq("Todos")]
top2 = tr_todos.nlargest(2, "peso_en_izabal")
cuota_top2 = float(top2["peso_en_izabal"].sum())

_mercado = (
    cubo[cubo["nacionalidad"].ne("Guatemala")]
    .groupby("nacionalidad")["visitantes"].sum().nlargest(1)
)
_nombre_mercado = str(_mercado.index[0]) if len(_mercado) else "el mercado principal"

modulo(
    "🧭 Observatorio de Inteligencia Turística · Río Dulce y Livingston",
    "¿Cuánta gente recibe Izabal, cuánto se queda, por dónde entra y qué debería hacer el INGUAT?",
    f"**{prop_pernocta:.0%}** de los visitantes pernoctan **{estadia:.1f} noches**, la ocupación "
    f"hotelera de Izabal promedia **{ocupacion:.0%}**, el acceso terrestre se concentra en "
    f"**dos fronteras ({cuota_top2:.0%} del flujo)** y el corredor marítimo **no tiene embudo "
    f"medible**: {solape} meses de solape entre visitantes y tránsito.",
)

kpis(
    [
        ("Pernoctan (turistas)", f"{prop_pernocta:.0%}", "de los visitantes de la muestra", "primario"),
        ("Estadía media ponderada", f"{estadia:.1f} noches", "Σ días-persona / Σ visitantes", "acento"),
        ("Ocupación hotelera", f"{ocupacion:.0%}", "Índice departamental 2023–2025", "secundario"),
        ("Error del pronóstico 2026", f"{_mape:.1%} MAPE", f"backtest de {_modelo}", "info"),
    ]
)

# ---------------------------------------------------------------------------
# Los cuatro módulos
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f'<div style="font-size:1.16rem;font-weight:700;color:{PALETA["texto"]};margin:4px 0 2px 0;">'
    "Los cuatro módulos del observatorio</div>",
    unsafe_allow_html=True,
)
st.markdown(
    f'<div style="color:{PALETA["neutro"]};font-size:0.87rem;margin:0 0 12px 0;">'
    "Cada módulo responde una pregunta de gestión y se apoya en las tres fuentes. "
    "Usá el menú lateral para navegar.</div>",
    unsafe_allow_html=True,
)

MODULOS = [
    {
        "icono": "📊",
        "nombre": "Módulo 1 · Demanda y Mercados Emisores",
        "pregunta": "¿Cuántos llegan, cuánto se quedan y de qué mercados vienen?",
        "hallazgo": f"{prop_pernocta:.0%} pernoctan y el mercado principal es {_nombre_mercado}.",
        "color": PALETA["primario"],
    },
    {
        "icono": "📈",
        "nombre": "Módulo 2 · Dinámica Temporal, Eventos y Pronóstico",
        "pregunta": "¿Cómo se mueve la demanda y qué se espera para 2026?",
        "hallazgo": f"Pronóstico de ocupación 2026 con backtest rolling-origin: MAPE {_mape:.1%}.",
        "color": PALETA["info"],
    },
    {
        "icono": "🏨",
        "nombre": "Módulo 3 · Oferta Hotelera y Desagregación Territorial",
        "pregunta": "¿Qué tan llenos están los hoteles y a qué subdestinos va la gente?",
        "hallazgo": f"Ocupación promedio de {ocupacion:.0%}; la afluencia medida no explica la ocupación.",
        "color": PALETA["secundario"],
    },
    {
        "icono": "🚢",
        "nombre": "Módulo 4 · Conectividad Fluvial y Embudo de Transferencia",
        "pregunta": "¿Por dónde entra el flujo y hacia dónde se dirige?",
        "hallazgo": f"Dos fronteras concentran el {cuota_top2:.0%}; el corredor marítimo no tiene embudo medible.",
        "color": PALETA["alerta"],
    },
]

cols = st.columns(2)
for col, m in zip(cols, MODULOS):
    with col:
        with st.container(border=True):
            st.markdown(
                f'<div style="font-size:0.98rem;font-weight:700;color:{m["color"]};">'
                f'{m["icono"]} {m["nombre"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="color:{PALETA["texto"]};font-size:0.88rem;margin-top:4px;">'
                f'{m["pregunta"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="color:{PALETA["neutro"]};font-size:0.85rem;margin-top:6px;">'
                f"▸ {m['hallazgo']}</div>",
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# Documentos y fuentes
# ---------------------------------------------------------------------------
st.markdown("---")
c1, c2 = st.columns([1.1, 1])

with c1:
    st.markdown("**📄 Documentación del proyecto**")
    st.markdown(
        "| Documento | Qué contiene |\n|---|---|\n"
        "| [`docs/PLAN.md`](docs/PLAN.md) | Plan maestro, hallazgos de datos y estado de avance |\n"
        "| [`docs/memoria_tecnica.md`](docs/memoria_tecnica.md) | Memoria técnica y recomendaciones (entrega formal) |\n"
        "| [`docs/asignacion_modulos.md`](docs/asignacion_modulos.md) | Reparto de los 4 integrantes por módulo |\n"
        "| `notebooks/` | Análisis exploratorio: calidad de datos, pronóstico y embudo |"
    )

with c2:
    st.markdown("**🗄️ Fuentes de datos**")
    st.markdown(
        "| Fuente | Cobertura | Naturaleza |\n|---|---|---|\n"
        "| `Base_Migracion_2009-2026jun.xlsx` | ene 2009 – jun 2026 | **Absoluta** (conteos) |\n"
        "| `indice_ocupacion_mensual_2023_2025_1.csv` | 2023 – 2025 | **Absoluta** (índice) |\n"
        "| `BD_COMPLEMENTARIA` (parquet) | oct 2021 – ago 2026 | **Muestral** (sin factor de expansión) |"
    )

# ---------------------------------------------------------------------------
# Limitaciones
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{PALETA["texto"]};margin:4px 0 6px 0;">'
    "Lo que este observatorio no puede afirmar</div>",
    unsafe_allow_html=True,
)

caveat(
    "**El corredor marítimo de Izabal no tiene embudo medible.** En Puerto Barrios, Livingston y "
    "Santo Tomás los visitantes (2009–2016) y el tránsito (2023–2026) nunca coinciden en un mismo "
    f"mes: **{solape} meses de solape**. Por eso el Módulo 4 no calcula una tasa de transferencia "
    "para esas fronteras."
)
bloque(
    "**La encuesta no tiene factor de expansión.** Sus cifras son proporciones muestrales: nunca "
    "se multiplican por la migración para obtener visitantes de Izabal (regla 6).",
    color=PALETA["secundario"], size="0.9rem", fondo="rgba(217,119,6,0.06)",
)
bloque(
    "**Falta el inventario hotelero.** Ninguna fuente trae establecimientos, habitaciones ni plazas "
    "cama, así que la capacidad instalada no se estima: se documenta y se recomienda a INGUAT "
    "incorporarla.",
    color=PALETA["info"], size="0.9rem", fondo="rgba(30,79,143,0.06)",
)
bloque(
    "**Los datos son institucionales y de uso académico.** La carpeta `data/` no se versiona, el "
    "repositorio es privado y el dashboard no habilita descargas de microdatos.",
    color=PALETA["neutro"], size="0.9rem",
)

with st.expander("📊 Cobertura y calidad de los datos (resumen)", expanded=False):
    calidad = get("data_quality")
    st.dataframe(calidad, hide_index=True, width="stretch")
    st.caption(
        "La tabla completa documenta, frontera por frontera, en qué meses hay registro de "
        "visitantes, de tránsito y de cruceros. Los períodos sin cobertura se conservan vacíos: "
        "la ausencia de dato no se rellena con cero (regla 1)."
    )
