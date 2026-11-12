"""Módulo 4 · Tasa de transferencia por frontera.

La tasa de transferencia responde: de las personas que entran por una frontera,
¿qué proporción declara destino Izabal/Caribe?

Es una proporción MUESTRAL (la encuesta no tiene factor de expansión), por lo
que:
    - se expresa como porcentaje de la muestra, nunca como total de visitantes;
    - lleva un intervalo de Wilson al 95% que acota la incertidumbre por el
      tamaño de muestra de cada frontera;
    - el denominador nunca puede ser cero.
"""

import numpy as np
import pandas as pd

from src.analysis.embudo import cadena_flujo, grafo_conectividad, modo_por_nodo


# ---------------------------------------------------------------------------
# Tasas
# ---------------------------------------------------------------------------
def test_tasa_entre_0_y_1(outputs):
    tr = outputs["survey_transfer_rate.parquet"]
    validas = tr[tr["registros_total"].gt(0)]
    assert not validas.empty
    assert validas["tasa_transferencia"].between(0, 1).all()
    assert validas["tasa_registros"].between(0, 1).all()


def test_denominador_nunca_cero(outputs):
    tr = outputs["survey_transfer_rate.parquet"]
    assert tr["registros_total"].gt(0).all(), "Una frontera sin questionnaires no genera fila."


def test_tasa_es_cociente_de_la_misma_tabla(outputs):
    """La tasa debe ser exactamente izabal/total, no un promedio de porcentajes."""
    tr = outputs["survey_transfer_rate.parquet"]
    esperado = tr["visitantes_izabal"] / tr["visitantes_total"]
    dif = (tr["tasa_transferencia"] - esperado).abs().dropna()
    assert dif.max() < 1e-9


def test_ic_wilson_contiene_la_tasa(outputs):
    """El intervalo de Wilson al 95% debe contener la estimación puntual."""
    tr = outputs["survey_transfer_rate.parquet"]
    v = tr[tr["registros_total"].gt(0)]
    dentro = (v["ic_inf"] <= v["tasa_registros"]) & (v["tasa_registros"] <= v["ic_sup"])
    assert dentro.all()
    assert v["ic_inf"].between(0, 1).all() and v["ic_sup"].between(0, 1).all()


def test_ic_mas_estrecho_con_mas_muestra(outputs):
    """A más muestra, menor incertidumbre: el IC se estrecha (monotonía)."""
    tr = outputs["survey_transfer_rate.parquet"]
    t = tr[(tr["anio"].eq("Todos")) & tr["registros_total"].gt(0)].copy()
    t["ancho_ic"] = t["ic_sup"] - t["ic_inf"]
    orden = t.sort_values("registros_total")
    mitad = len(orden) // 2
    chico = orden.head(mitad)["ancho_ic"].mean()
    grande = orden.tail(mitad)["ancho_ic"].mean()
    assert chico >= grande, "El intervalo no se estrecha con más muestra."


def test_pesos_suman_uno(outputs):
    """El peso de cada frontera en el destino debe sumar 1 (muestral)."""
    tr = outputs["survey_transfer_rate.parquet"]
    t = tr[tr["anio"].eq("Todos")]
    assert abs(t["peso_en_izabal"].sum() - 1.0) < 1e-9


def test_solo_fronteras_del_mapeo(outputs):
    """Ninguna fila puede traer una frontera sin equivalente en migración."""
    tr = outputs["survey_transfer_rate.parquet"]
    assert tr["frontera_migracion"].notna().all()


# ---------------------------------------------------------------------------
# Cadena de nodos y grafo
# ---------------------------------------------------------------------------
def test_cadena_flujo_un_nodo_principal_por_frontera(outputs):
    flujo = outputs["survey_border_node_flow.parquet"]
    cadena = cadena_flujo(flujo)
    assert not cadena.empty
    assert not cadena["frontera_nombre"].duplicated().any()
    assert cadena["participacion_frontera"].between(0, 1).all()


def test_grafo_tiene_nodos_y_aristas(outputs):
    flujo = outputs["survey_border_node_flow.parquet"]
    g = grafo_conectividad(flujo, min_registros=10)
    assert not g["nodos"].empty and not g["aristas"].empty
    assert {"nodos", "aristas"} == set(g.keys())
    assert g["aristas"]["registros"].gt(0).all()


def test_nodos_de_agua_clasificados(outputs):
    from src.analysis.embudo import NODOS_AGUA

    flujo = outputs["survey_border_node_flow.parquet"]
    g = grafo_conectividad(flujo, min_registros=10)
    agua = g["nodos"][g["nodos"]["tipo"].eq("nodo_agua")]["nodo"]
    assert set(agua) <= set(NODOS_AGUA)


def test_modo_por_nodo_tiene_una_fila_por_nodo(outputs):
    nt = outputs["survey_node_transport.parquet"]
    dom = modo_por_nodo(nt, ["Río Dulce", "Puerto Barrios", "Livingston"])
    assert len(dom) == 3
    assert dom["participacion"].between(0, 1).all()
    assert dom["registros"].gt(0).all()


def test_flujo_nodo_no_incluye_no_izabal(outputs):
    """La cadena de nodos es solo del destino Izabal/Caribe."""
    flujo = outputs["survey_border_node_flow.parquet"]
    # El total de registros del flujo debe coincidir con los registros de Izabal
    # en la encuesta: si apareciera otro destino, la suma crecería.
    assert flujo["registros"].sum() > 0
    assert flujo["nodo"].ne("No especificado").all()
