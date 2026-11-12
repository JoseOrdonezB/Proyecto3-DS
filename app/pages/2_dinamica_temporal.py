"""Módulo 2: Dinámica Temporal, Eventos y Pronóstico Predictivo.

La historia que cuenta este módulo, en tres pasos:

    1. La encuesta es la única serie diaria continua de Izabal: tiene un
       patrón semanal claro y las festividades la mueven, en ambos sentidos.
    2. La ocupación hotelera de Izabal termina en diciembre 2025: los dos
       meses de 2026 que exige la guía se estiman con el modelo ganador del
       backtest, nunca con el método obligatorio sin contraste.
    3. Ese modelo se valida formalmente contra los meses ya observados: se
       reporta el error (MAPE) y se compara contra los otros 3 candidatos,
       incluido el método literal de la guía (factor de reparto).

Bases de datos:
    - Encuesta (MUESTRAL, sin factor de expansión): serie diaria de Izabal,
      patrón semanal e impacto de festividades.
    - Ocupación hotelera de Izabal (ABSOLUTA, índice en [0, 1]): serie mensual
      2023-2025, pronosticada con 4 modelos y backtest rolling-origin.
    - Migración (ABSOLUTA): perfil estacional de las fronteras alimentadoras,
      insumo del modelo 'factor de reparto'.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.charts import colores_foco, estilo, titulo_grafico
from app.components.data import get
from app.components.kpis import nota
from app.components.layout import (
    ALTURA_GRANDE,
    caveat,
    insight,
    kpis,
    modulo,
    seccion,
)
from app.components.theme import PALETA
from src.analysis.feriados import calendario
from src.config import ISABAL_FEEDER_BORDERS, VISITOR_TYPES
from src.models import forecast as fc

st.set_page_config(page_title="M2 · Dinámica Temporal", page_icon="📈", layout="wide")

diaria = get("survey_izabal_daily")
diaria["fecha"] = pd.to_datetime(diaria["fecha"])
semanal = get("survey_weekly_pattern")
lift = get("survey_holiday_lift")
occ_m = get("occupancy_monthly")
occ_m["fecha"] = pd.to_datetime(occ_m["fecha"])
mig_m = get("migration_monthly")
mig_m["fecha"] = pd.to_datetime(mig_m["fecha"])
focc = get("forecast_occupancy")
focc["fecha"] = pd.to_datetime(focc["fecha"])
met = get("forecast_metrics")

MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# --- Modelo ganador (ocupación) ----------------------------------------------
met_occ = met[met["objetivo"].eq("ocupacion")].copy()
met_enc = met[met["objetivo"].eq("encuesta")].copy()
fila_gan = met_occ[met_occ["ganador"]].iloc[0]
modelo_gan = fila_gan["modelo"]
etiqueta_gan = fila_gan["etiqueta"]
col_mape = "mape_comunes" if pd.notna(fila_gan.get("mape_comunes")) else "mape"
mape_gan = float(fila_gan[col_mape])

focc_gan = focc[focc["modelo"].eq(modelo_gan)].sort_values("fecha")
obligatorio = focc_gan.head(2)
serie_obs = occ_m.set_index("fecha")["indice_ocupacion"].sort_index()

# --- Backtest del modelo ganador (recalculado en vivo para graficar folds) ---
migracion_feeders = fc.serie_mensual_migracion(mig_m, ISABAL_FEEDER_BORDERS, VISITOR_TYPES)
bt_occ = fc.backtest(
    occ_m[["fecha", "indice_ocupacion"]], modelos=[modelo_gan],
    transform="logit", bounds=(0.0, 1.0), migracion=migracion_feeders,
)
bt_valid = bt_occ[bt_occ["valido"]].sort_values("fecha")

# --- Lift de festividades (período completo) --------------------------------
lift_todos = lift[lift["anio"].eq("Todos")].copy()
fila_top = lift_todos.loc[lift_todos["lift_visitantes_pct"].idxmax()]
evento_top = fila_top["nombre"]
lift_top = float(fila_top["lift_visitantes_pct"])

# --- Patrón semanal -----------------------------------------------------------
fila_pico = semanal.loc[semanal["indice_visitantes"].idxmax()]
dia_pico = fila_pico["dia_semana"]
indice_pico = float(fila_pico["indice_visitantes"])

modulo(
    "📈 Módulo 2 · Dinámica Temporal, Eventos y Pronóstico",
    "¿Cómo se mueve la demanda día a día, qué festividades la mueven y qué ocupación "
    "tendrá Izabal en los dos meses de 2026 que todavía no se observan?",
    f"**{evento_top}** sube los registros un **{lift_top:+.0f}%** frente a un día regular, "
    f"y **{dia_pico}** concentra la mayor presión semanal. La ocupación de ene-feb 2026 se "
    f"estima con **{etiqueta_gan}** (MAPE **{mape_gan:.1%}** en backtest), el modelo que más "
    f"le acierta al mes siguiente entre los 4 candidatos comparados.",
)

kpis(
    [
        ("MAPE del pronóstico", f"{mape_gan:.1%}", f"modelo ganador: {etiqueta_gan}", "primario"),
        (
            "Ocupación estimada ene-feb 2026",
            " / ".join(f"{v:.0%}" for v in obligatorio["estimacion"]) if len(obligatorio) else "Sin dato",
            "Estimación — nunca cero, nunca observado",
            "estimacion",
        ),
        ("Festividad con más lift", evento_top, f"{lift_top:+.0f}% vs. día regular", "secundario"),
        ("Día con más presión", dia_pico, f"{indice_pico:.0%} del promedio diario", "info"),
    ]
)

# ---------------------------------------------------------------------------
# Filtro enlazado: selector de festividad
# ---------------------------------------------------------------------------
eventos_op = sorted(lift_todos["nombre"].unique())
if st.session_state.get("m2_evento") not in eventos_op:
    st.session_state["m2_evento"] = evento_top


def _al_clic_evento():
    ev = st.session_state.get("m2_click")
    puntos = (ev or {}).get("selection", {}).get("points", []) if ev else []
    if puntos:
        valor = puntos[0].get("y") or puntos[0].get("label")
        if valor in eventos_op:
            st.session_state["m2_evento"] = valor


f1, f2 = st.columns([2, 3])
with f1:
    evento_sel = st.selectbox(
        "Festividad / evento", eventos_op, key="m2_evento",
        help="Marca sus fechas en la serie diaria y calcula el lift frente al día regular.",
    )
with f2:
    fila_sel = lift_todos[lift_todos["nombre"].eq(evento_sel)].iloc[0]
    st.markdown(
        f"**{evento_sel}** ({fila_sel['tipo']}): **{fila_sel['lift_visitantes_pct']:+.0f}%** en "
        f"visitantes, **{fila_sel['lift_registros_pct']:+.0f}%** en registros, sobre "
        f"{int(fila_sel['n_dias'])} días con operativo."
    )


def _vrects_evento(fig: go.Figure, nombre: str, index_min, index_max) -> None:
    fechas = calendario().loc[calendario()["nombre"].eq(nombre), "fecha"].sort_values()
    fechas = fechas[(fechas >= index_min) & (fechas <= index_max)]
    if fechas.empty:
        return
    inicio = anterior = fechas.iloc[0]
    for x in fechas.iloc[1:]:
        if (x - anterior).days > 1:
            fig.add_vrect(x0=inicio - pd.Timedelta(days=1), x1=anterior + pd.Timedelta(days=1),
                          fillcolor=PALETA["secundario"], opacity=0.16, line_width=0)
            inicio = x
        anterior = x
    fig.add_vrect(x0=inicio - pd.Timedelta(days=1), x1=anterior + pd.Timedelta(days=1),
                  fillcolor=PALETA["secundario"], opacity=0.16, line_width=0)


# ---------------------------------------------------------------------------
# 1 · Serie diaria y efecto de las festividades
# ---------------------------------------------------------------------------
seccion(
    f"{evento_sel} mueve la demanda diaria un {fila_sel['lift_visitantes_pct']:+.0f}% frente a un día regular",
    "Serie diaria de la encuesta en Izabal/Caribe (muestral). Las franjas marcan las fechas de la "
    "festividad seleccionada en cada año.",
    badge="Muestral",
)

col_d1, col_d2 = st.columns([1.6, 1])
with col_d1:
    fig = go.Figure()
    fig.add_scatter(
        x=diaria["fecha"], y=diaria["visitantes"], mode="lines",
        line=dict(color=PALETA["primario"], width=1.3),
        hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} visitantes (muestra)<extra></extra>",
    )
    _vrects_evento(fig, evento_sel, diaria["fecha"].min(), diaria["fecha"].max())
    estilo(fig, ALTURA_GRANDE, y="Visitantes (muestra) por día")
    titulo_grafico(fig, "La serie diaria de la encuesta es la única continua de Izabal",
                   f"Franjas: fechas de {evento_sel}")
    st.plotly_chart(fig, width="stretch")

with col_d2:
    l_ord = lift_todos.sort_values("lift_visitantes_pct", ascending=True)
    fig = go.Figure(go.Bar(
        x=l_ord["lift_visitantes_pct"], y=l_ord["nombre"], orientation="h",
        marker_color=colores_foco(l_ord["nombre"], evento_sel),
        text=[f"{v:+.0f}%" for v in l_ord["lift_visitantes_pct"]], textposition="outside",
        textfont=dict(color=PALETA["texto"]),
        hovertemplate="%{y}: %{x:+.0f}%<extra></extra>",
    ))
    fig.add_vline(x=0, line_color=PALETA["neutro"], line_width=1)
    fig.update_layout(clickmode="event+select", dragmode=False)
    estilo(fig, ALTURA_GRANDE, x="Lift en visitantes vs. día regular", leyenda=False)
    titulo_grafico(fig, "El lift cambia de signo entre festividades")
    st.plotly_chart(fig, width="stretch", key="m2_click", on_select=_al_clic_evento,
                    selection_mode="points")
    st.caption("Clic en una barra para marcarla en la serie diaria.")

insight(
    f"**{evento_top}** es la festividad con mayor impacto positivo ({lift_top:+.0f}% en visitantes). "
    "El lift se calcula contra el promedio de los días regulares del mismo período (ni feriado ni "
    "evento), así que compara como con como, no un día cualquiera contra un promedio histórico."
)


# ---------------------------------------------------------------------------
# 2 · Patrón semanal
# ---------------------------------------------------------------------------
seccion(
    f"{dia_pico} concentra un {indice_pico:.0%} del promedio diario: el fin de semana presiona más",
    "Índice = promedio de visitantes de ese día de la semana / promedio de todos los días con "
    "operativo. 1.00 es un día típico.",
    badge="Muestral",
)

sem_ord = semanal.copy()
fines = {"Sábado", "Domingo"}
fig = go.Figure(go.Bar(
    x=sem_ord["dia_semana"], y=sem_ord["indice_visitantes"],
    marker_color=[PALETA["secundario"] if d in fines else PALETA["primario"] for d in sem_ord["dia_semana"]],
    text=[f"{v:.0%}" for v in sem_ord["indice_visitantes"]], textposition="outside",
    textfont=dict(color=PALETA["texto"]),
    hovertemplate="%{x}: %{y:.0%} del promedio diario<extra></extra>",
))
fig.add_hline(y=1.0, line_dash="dot", line_color=PALETA["neutro"], annotation_text="Día típico")
estilo(fig, ALTURA_GRANDE, y="Índice de visitantes")
titulo_grafico(fig, f"{dia_pico} es el día de mayor presión muestral de la semana")
st.plotly_chart(fig, width="stretch")

insight(
    f"El patrón se construye sobre el **promedio**, no la suma bruta de cada día de la semana "
    "(evita que un mes con más sábados infle el resultado). El fin de semana (naranja) está por "
    "encima del día típico; los días hábiles (turquesa), por debajo o cerca de él."
)


# ---------------------------------------------------------------------------
# 3 · Pronóstico de ocupación 2026
# ---------------------------------------------------------------------------
if len(obligatorio) >= 2:
    mes1 = MESES_ES[obligatorio["fecha"].iloc[0].month - 1]
    mes2 = MESES_ES[obligatorio["fecha"].iloc[1].month - 1]
    est1 = float(obligatorio["estimacion"].iloc[0])
    est2 = float(obligatorio["estimacion"].iloc[1])
else:
    mes1 = mes2 = "s/d"
    est1 = est2 = float("nan")

seccion(
    f"La ocupación de Izabal se estima en {est1:.0%} en {mes1} y {est2:.0%} en {mes2} de 2026",
    f"Serie observada de ocupación hotelera de Izabal (índice en [0,1]) y pronóstico del modelo "
    f"ganador ({etiqueta_gan}), con transformada logit: ninguna estimación puede salir de [0,1].",
)

fig = go.Figure()
fig.add_scatter(
    x=serie_obs.index, y=serie_obs.values, mode="lines+markers", name="Observado",
    line=dict(color=PALETA["primario"], width=2), marker=dict(size=5), connectgaps=False,
    hovertemplate="%{x|%b %Y}<br>Ocupación observada: %{y:.1%}<extra></extra>",
)
fig.add_scatter(
    x=focc_gan["fecha"], y=focc_gan["estimacion"], mode="lines+markers",
    name=f"Estimación ({etiqueta_gan})",
    line=dict(color=PALETA["estimacion"], width=2, dash="dash"),
    marker=dict(symbol="circle-open", size=7, color=PALETA["estimacion"]),
    hovertemplate="%{x|%b %Y}<br>Ocupación estimada: %{y:.1%}<extra></extra>",
)
if len(obligatorio) >= 1:
    fig.add_vrect(
        x0=obligatorio["fecha"].min() - pd.Timedelta(days=15),
        x1=obligatorio["fecha"].max() + pd.Timedelta(days=15),
        fillcolor=PALETA["estimacion"], opacity=0.08, line_width=0,
        annotation_text="Ene-Feb 2026 (obligatorio)", annotation_position="top left",
        annotation_font=dict(size=11, color=PALETA["estimacion"]),
    )
estilo(fig, ALTURA_GRANDE, y="Índice de ocupación", y_pct=True)
titulo_grafico(fig, "La estimación 2026 queda dentro del rango histórico, nunca fuera de [0,1]")
st.plotly_chart(fig, width="stretch")

insight(
    "La línea violeta discontinua con marcador vacío es siempre una **estimación**, nunca un dato "
    "observado (regla 1): los meses sin cobertura se muestran así, no como cero ni fusionados con "
    "la serie real."
)

with st.expander("📋 Pronóstico completo de los 4 modelos (12 meses)", expanded=False):
    piv = focc.pivot_table(index="fecha", columns="modelo", values="estimacion")
    st.dataframe(
        piv.rename(columns=fc.ETIQUETAS).style.format("{:.1%}"),
        width="stretch",
    )
    st.caption(
        "Cada columna es un modelo candidato; el ganador se decide por MAPE en el backtest "
        "(sección siguiente), no por cuál 'se ve mejor' en el gráfico."
    )


# ---------------------------------------------------------------------------
# 4 · Validación formal del modelo
# ---------------------------------------------------------------------------
if modelo_gan == "factor_reparto":
    comparacion_metodo = (
        "coincide con el método que exige la guía textualmente (perfil estacional + factor de "
        "reparto de la migración)"
    )
else:
    fila_factor = met_occ[met_occ["modelo"].eq("factor_reparto")]
    if not fila_factor.empty:
        mape_factor = float(fila_factor.iloc[0][col_mape])
        comparacion_metodo = (
            f"le gana por {(mape_factor - mape_gan) * 100:.1f} puntos porcentuales de MAPE al método "
            "que exige la guía textualmente (perfil estacional + factor de reparto de la migración)"
        )
    else:
        comparacion_metodo = "se compara contra los otros 3 modelos candidatos"

seccion(
    f"{etiqueta_gan} {comparacion_metodo}",
    "Observado vs. estimado por el modelo ganador en cada mes del backtest rolling-origin "
    "(entrena solo con datos anteriores al mes evaluado) y comparación de error frente a los "
    "otros 3 modelos candidatos.",
    badge="Observado",
)

col_v1, col_v2 = st.columns([1.5, 1])
with col_v1:
    fig = go.Figure()
    fig.add_scatter(
        x=bt_valid["fecha"], y=bt_valid["y_true"], mode="lines+markers", name="Observado",
        line=dict(color=PALETA["primario"], width=2), marker=dict(size=5),
        hovertemplate="%{x|%b %Y}<br>Observado: %{y:.1%}<extra></extra>",
    )
    fig.add_scatter(
        x=bt_valid["fecha"], y=bt_valid["y_pred"], mode="lines+markers",
        name=f"Backtest ({etiqueta_gan})",
        line=dict(color=PALETA["estimacion"], width=2, dash="dash"),
        marker=dict(symbol="circle-open", size=6, color=PALETA["estimacion"]),
        hovertemplate="%{x|%b %Y}<br>Backtest: %{y:.1%}<extra></extra>",
    )
    estilo(fig, ALTURA_GRANDE, y="Índice de ocupación", y_pct=True)
    titulo_grafico(fig, f"El modelo ganador se equivoca {mape_gan:.1%} en promedio (MAPE) un mes adelante")
    st.plotly_chart(fig, width="stretch")

with col_v2:
    met_plot = met_occ.sort_values(col_mape, ascending=True)
    fig = go.Figure(go.Bar(
        x=met_plot[col_mape], y=met_plot["etiqueta"], orientation="h",
        marker_color=colores_foco(met_plot["etiqueta"], etiqueta_gan),
        text=[f"{v:.1%}" for v in met_plot[col_mape]], textposition="outside",
        textfont=dict(color=PALETA["texto"]),
    ))
    estilo(fig, ALTURA_GRANDE, x="MAPE (backtest)", leyenda=False)
    fig.update_xaxes(tickformat=".0%")
    titulo_grafico(fig, "Comparación de error entre los 4 modelos candidatos")
    st.plotly_chart(fig, width="stretch")

insight(
    f"**{etiqueta_gan}** gana porque entrena sobre la transformada logit de la ocupación (garantiza "
    f"[0,1]) y usa estacionalidad anual; el método obligatorio por rúbrica (factor de reparto) se "
    "implementa y se reporta siempre, pero no es el que decide el pronóstico final: decide el que "
    "mide menos error en el backtest."
)

with st.expander("📐 Métricas completas (ocupación y encuesta)", expanded=False):
    cols_m = ["etiqueta", "n_folds_validos", "n_folds_excluidos", "mape", "rmse", "mae",
              "mape_comunes", "ganador"]
    st.markdown("**Ocupación de Izabal**")
    st.dataframe(
        met_occ[cols_m].rename(columns={
            "etiqueta": "Modelo", "n_folds_validos": "Folds válidos",
            "n_folds_excluidos": "Folds excluidos", "mape": "MAPE", "rmse": "RMSE", "mae": "MAE",
            "mape_comunes": "MAPE (folds comunes)", "ganador": "Ganador",
        }),
        hide_index=True, width="stretch",
        column_config={"MAPE": st.column_config.NumberColumn(format="percent"),
                        "MAPE (folds comunes)": st.column_config.NumberColumn(format="percent")},
    )
    st.markdown("**Encuesta de Izabal (muestral)**")
    st.dataframe(
        met_enc[cols_m].rename(columns={
            "etiqueta": "Modelo", "n_folds_validos": "Folds válidos",
            "n_folds_excluidos": "Folds excluidos", "mape": "MAPE", "rmse": "RMSE", "mae": "MAE",
            "mape_comunes": "MAPE (folds comunes)", "ganador": "Ganador",
        }),
        hide_index=True, width="stretch",
        column_config={"MAPE": st.column_config.NumberColumn(format="percent"),
                        "MAPE (folds comunes)": st.column_config.NumberColumn(format="percent")},
    )
    registros_mes = fc.serie_mensual_encuesta(diaria, "visitantes")
    muestra_valida = registros_mes.dropna()
    if not muestra_valida.empty:
        caveat(
            f"**El error de la encuesta es real, no un fallo del modelo.** Su MAPE es mucho mayor "
            f"que el de ocupación porque la muestra mensual de Izabal va de "
            f"{muestra_valida.min():,.0f} a {muestra_valida.max():,.0f} visitantes registrados: con "
            "tan poca muestra, el ruido mes a mes es inherente al dato, no al método de pronóstico "
            "(regla 6: la encuesta no tiene factor de expansión)."
        )

nota(
    "**Cómo leer este módulo.** La ocupación es la única serie absoluta pronosticada (índice en "
    "[0,1], transformada logit). La encuesta es muestral: su patrón semanal y su lift de "
    "festividades se leen como tendencia relativa, nunca como visitantes totales (regla 6). Toda "
    "cifra violeta con línea discontinua y marcador vacío es una **Estimación**; los meses sin dato "
    "se muestran vacíos, nunca en cero (regla 1)."
)
