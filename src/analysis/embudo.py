"""Módulo 4: composición analítica del embudo de transferencia.

Reto del Grupo 5 — Conectividad Fluvial y Embudo de Transferencia
(Río Dulce y Livingston, Izabal).

Este módulo NO recalcula agregados: toma las tablas ya procesadas por el ETL
(`src.etl.transform`) y las compone para responder las preguntas de gestión
del reto. Sigue el mismo patrón que `src/analysis/feriados.py`.

Las tres preguntas que responde:

1. **¿Se puede medir el embudo?** -> `descomposicion_corredor()`
   En las fronteras marítimas de Izabal, visitantes y tránsito NUNCA coinciden
   en un mismo mes (0 meses de solape). El embudo marítimo no es medible con
   la base oficial; el terrestrial sí.

2. **¿Por dónde entra y hacia dónde va?** -> `grafo_conectividad()`,
   `cadena_flujo()`
   La cadena de conectividad del destino, medida como flujo frontera -> nodo
   del corredor (Río Dulce, Puerto Barrios, Livingston, ...).

3. **¿Qué hacer al respecto?** -> `recomendaciones_inguat()`
   Cada recomendación se construye a partir de los datos, no se redacta a mano:
   su texto cita la cifra que la respalda.
"""

from __future__ import annotations

import pandas as pd

# Nodos de agua del corredor: río (Río Dulce, Santo Tomás) y mar (Puerto Barrios,
# Livingston). El resto de nodos son terrestres.
NODOS_AGUA = ["Río Dulce", "Puerto Barrios", "Livingston"]

# Nodo raíz del corredor: es el puerto fluvial desde donde se reparte la carga.
NODO_RAIZ = "Puerto Barrios"

# Nombres de mes en español (el locale del sistema puede no ser es).
MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


# ---------------------------------------------------------------------------
# 1. ¿Se puede medir el embudo?
# ---------------------------------------------------------------------------
def descomposicion_corredor(perfil: pd.DataFrame) -> pd.DataFrame:
    """Clasifica cada frontera del corredor según la medida que sí admite.

    A partir de `maritime_flow_profile` (ETL) responde: ¿esta frontera tiene
    visitantes? ¿tiene tránsito? ¿coexisten? De ahí se deduce si su embudo
    es calculable o no.
    """
    d = perfil.copy()
    d["medida_disponible"] = d.apply(
        lambda r: (
            "Visitantes y tránsito simultáneos (embudo medible)"
            if r["meses_solape"] > 0
            else (
                "Visitantes y tránsito en periodos disjuntos (embudo NO medible)"
                if r["meses_visitantes"] > 0 and r["meses_transito"] > 0
                else ("Solo visitantes" if r["meses_visitantes"] > 0 else "Solo tránsito")
            )
        ),
        axis=1,
    )
    d["periodo"] = d.apply(
        lambda r: " / ".join(
            x for x in [r["rango_visitantes"], r["rango_transito"]] if isinstance(x, str) and x
        ),
        axis=1,
    )
    cols = [
        "Frontera",
        "es_destino_maritimo",
        "es_alimentadora",
        "medida_disponible",
        "meses_visitantes",
        "meses_transito",
        "meses_solape",
        "embudo_medible",
        "periodo",
    ]
    return d[cols].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. ¿Por dónde entra y hacia dónde va?
# ---------------------------------------------------------------------------
def cadena_flujo(border_node_flow: pd.DataFrame) -> pd.DataFrame:
    """Nodo principal de cada frontera y su peso dentro del flujo de esa frontera.

    `border_node_flow` viene del ETL con una fila por (frontera, nodo, segmento).
    """
    d = border_node_flow.copy()
    g = (
        d.groupby(["frontera_nombre", "nodo"], as_index=False)
        .agg(registros=("registros", "sum"), visitantes=("visitantes", "sum"))
        .sort_values(["frontera_nombre", "registros", "nodo"], ascending=[True, False, True])
    )
    total = g.groupby("frontera_nombre")["registros"].transform("sum").replace(0, pd.NA)
    g["participacion_frontera"] = g["registros"] / total
    # Nodo principal: el de mayor peso. Los empates se resuelven por orden
    # alfabético para que el resultado sea determinista.
    principal = (
        g[g["registros"] == g.groupby("frontera_nombre")["registros"].transform("max")]
        .drop_duplicates("frontera_nombre", keep="first")
        .rename(columns={"nodo": "nodo_principal"})
    )
    principal["es_nodo_agua"] = principal["nodo_principal"].isin(NODOS_AGUA)
    return principal[
        [
            "frontera_nombre",
            "nodo_principal",
            "registros",
            "participacion_frontera",
            "es_nodo_agua",
        ]
    ].reset_index(drop=True)


def grafo_conectividad(
    border_node_flow: pd.DataFrame, min_registros: int = 10
) -> dict:
    """Nodos y aristas del corredor fluvial, para dibujar el grafo.

    Arista: frontera de entrada -> nodo del corredor, peso = registros
    (muestrales). Se descartan las aristas por debajo de `min_registros` para
    que el grafo muestre la estructura y no el ruido de la muestra.

    Returns:
        dict con "nodos" (DataFrame) y "aristas" (DataFrame).
    """
    d = border_node_flow.copy()
    e = (
        d.groupby(["frontera_nombre", "nodo"], as_index=False)
        .agg(registros=("registros", "sum"), visitantes=("visitantes", "sum"))
        .sort_values("registros", ascending=False)
    )
    e = e[e["registros"] >= min_registros].reset_index(drop=True)
    e = e.rename(columns={"frontera_nombre": "origen", "nodo": "destino"})

    nodos = pd.DataFrame(
        [
            {"nodo": n, "tipo": "frontera", "registros": int(e.loc[e["origen"].eq(n), "registros"].sum())}
            for n in sorted(e["origen"].unique())
        ]
        + [
            {
                "nodo": n,
                "tipo": "nodo_agua" if n in NODOS_AGUA else "nodo_tierra",
                "registros": int(e.loc[e["destino"].eq(n), "registros"].sum()),
            }
            for n in sorted(e["destino"].unique())
        ]
    ).reset_index(drop=True)
    nodos["es_raiz"] = nodos["nodo"].eq(NODO_RAIZ)
    return {"nodos": nodos, "aristas": e}


def participacion_nodos_agua(border_node_flow: pd.DataFrame) -> pd.DataFrame:
    """Peso relativo de cada nodo de agua dentro del flujo hacia Izabal.

    Regla 4: los nodos no se suman para obtener un total de visitantes únicos;
    aquí se reporta el peso RELATIVO de cada nodo dentro de la muestra, que sí
    es interpretable.
    """
    d = border_node_flow.copy()
    g = d.groupby("nodo", as_index=False).agg(registros=("registros", "sum"))
    g["participacion"] = g["registros"] / g["registros"].sum()
    g["es_nodo_agua"] = g["nodo"].isin(NODOS_AGUA)
    return g.sort_values("registros", ascending=False).reset_index(drop=True)


def modo_por_nodo(node_transport: pd.DataFrame, nodos: list[str]) -> pd.DataFrame:
    """Modo de transporte dominante de cada nodo, con su participación."""
    d = node_transport[node_transport["nodo"].isin(nodos)].copy()
    d = d.sort_values(["nodo", "registros"], ascending=[True, False])
    dom = d.groupby("nodo", as_index=False).head(1).copy()
    dom["participacion"] = dom["participacion_nodo"]
    return dom[["nodo", "tipo_transporte", "registros", "participacion", "es_nodo_agua"]].reset_index(
        drop=True
    )


# ---------------------------------------------------------------------------
# 3. ¿Qué hacer al respecto?
# ---------------------------------------------------------------------------
def recomendaciones_inguat(datos: dict) -> list[dict]:
    """Recomendaciones para INGUAT construidas a partir de los datos.

    Cada recomendación incluye la cifra que la respalda, de modo que el texto
    y su evidencia no puedan divergir. `datos` es un dict con las tablas
    procesadas del ETL.
    """
    perfil = datos["perfil"]
    flujo = datos["flujo"]
    transporte = datos["transporte"]
    tr = datos.get("transito")
    perfil = perfil.set_index("Frontera")

    recs: list[dict] = []

    # 1) El corredor marítimo no es medible: hay que instrumentarlo.
    maritimas = perfil[perfil["es_destino_maritimo"]]
    if not maritimas.empty:
        solape = int(maritimas["meses_solape"].sum())
        meses_vis = int(maritimas["meses_visitantes"].sum())
        meses_tra = int(maritimas["meses_transito"].sum())
        recs.append(
            {
                "titulo": "Instrumentar el corredor fluvial con una serie única de visitantes",
                "hallazgo": (
                    f"En las {len(maritimas)} fronteras marítimas de Izabal hay "
                    f"{meses_vis:,} meses con visitantes y {meses_tra:,} con tránsito, "
                    f"pero {solape} meses en que ambos coexisten. El embudo del "
                    f"corredor marítimo no es calculable con la base actual."
                ),
                "recomendacion": (
                    "Pedir a INGUAT una serie que registre, para una misma frontera y "
                    "mes, tanto el visitante (con pernocta o sin ella) como el tránsito, "
                    "de modo que exista una tasa de transferencia oficial del corredor."
                ),
                "prioridad": "Alta",
            }
        )

    # 2) Concentración del flujo terrestre: dos fronteras sostienen el destino.
    if not flujo.empty:
        top = flujo.sort_values("registros", ascending=False).head(2)
        total = flujo["registros"].sum()
        cuota = top["registros"].sum() / total if total else float("nan")
        nombres = " y ".join(top["frontera_nombre"].tolist())
        recs.append(
            {
                "titulo": "El acceso terrestre a Izabal depende de un cuello de botella de dos fronteras",
                "hallazgo": (
                    f"{nombres} concentran el {cuota:.0%} de los registros de la muestra "
                    f"de visitantes con destino Izabal/Caribe."
                ),
                "recomendacion": (
                    "Priorizar en esas dos fronteras la señalización hacia el corredor "
                    "fluvial y el transporte oficial, porque cualquier interceptor en "
                    "ellas afecta de forma desproporcionada a todo el destino."
                ),
                "prioridad": "Alta",
            }
        )

    # 3) Asimetría de modos entre el nodo turístico y el nodo comercial.
    if not transporte.empty:
        rio = transporte[transporte["nodo"].eq("Río Dulce")]
        pb = transporte[transporte["nodo"].eq("Puerto Barrios")]
        if not rio.empty and not pb.empty:
            r_modo = rio.iloc[0]
            p_modo = pb.iloc[0]
            recs.append(
                {
                    "titulo": "Río Dulce y Puerto Barrios son dos corredores con demanda distinta",
                    "hallazgo": (
                        f"Río Dulce se alcanza sobre todo en {r_modo['tipo_transporte']} "
                        f"({r_modo['participacion_nodo']:.0%} de sus registros), mientras "
                        f"Puerto Barrios llega en {p_modo['tipo_transporte']} "
                        f"({p_modo['participacion_nodo']:.0%})."
                    ),
                    "recomendacion": (
                        "No tratar el corredor como una sola oferta: Río Dulce necesita "
                        "gestión de buses turísticos y cupos; Puerto Barrios, despacho de "
                        "carga particular y trailer."
                    ),
                    "prioridad": "Media",
                }
            )

    # 4) Estacionalidad del tránsito: si es plana, el cuello es estructural.
    if tr is not None and not tr.empty:
        # Acepta tanto la tabla procesada ('viajeros') como la migración cruda
        # ('Viajero' + 'Frontera'), para no atar la función a un solo llamador.
        col = "viajeros" if "viajeros" in tr.columns else "Viajero"
        # Total mensual del corredor (sumar fronteras antes de medir dispersión:
        # la variación entre fronteras no es estacionalidad).
        serie = tr.groupby("fecha")[col].sum().sort_index()
        media = float(serie.mean())
        cv = float(serie.std() / media) if media else float("nan")
        mes_min = MESES_ES[int(serie.idxmin().month) - 1] if len(serie) else "?"
        mes_max = MESES_ES[int(serie.idxmax().month) - 1] if len(serie) else "?"
        amplitud = (float(serie.max()) - float(serie.min())) / media if media else float("nan")
        recs.append(
            {
                "titulo": "El tránsito del corredor es estructural, no estacional",
                "hallazgo": (
                    f"El tránsito mensual de las fronteras marítimas de Izabal tiene un "
                    f"coeficiente de variación de {cv:.2f} y una amplitud de {amplitud:.0%} "
                    f"respecto a su media: va de {mes_min} (mínimo) a {mes_max} (máximo) "
                    f"sin llegar a la concentración estacional de la demanda turística."
                ),
                "recomendacion": (
                    "Planificar la capacidad de traslado de forma permanente (infraestructura, "
                    "turnos y señalización) y no por temporadas, porque el movimiento de "
                    "personas y carga no se concentra en fechas picos como sí ocurre con "
                    "el visitante con pernocta."
                ),
                "prioridad": "Media",
            }
        )

    # 5) Datos a incorporar a futuro.
    if "itinerarios" in datos:
        it = datos["itinerarios"]
        multi = it[it["es_multi_parada"]] if "es_multi_parada" in it.columns else it.iloc[0:0]
        n_multi = int(multi["registros"].sum()) if not multi.empty else 0
        n_total = int(it["registros"].sum()) if not it.empty else 0
        recs.append(
            {
                "titulo": "Solicitar el diccionario de códigos de destino y el inventario hotelero",
                "hallazgo": (
                    f"La encuesta registra {n_multi:,} registros con itinerarios de dos o más "
                    f"paradas en el campo 'otros_destinos' (sobre {n_total:,} con el campo "
                    f"informado), pero los códigos no traen diccionario, así que las rutas "
                    f"no pueden nombrarse ni validarse."
                ),
                "recomendacion": (
                    "Pedir a INGUAT el catálogo de códigos de destino por base (V10/V11/V12) "
                    "y, en paralelo, el inventario de establecimientos, habitaciones y plazas "
                    "cama por departamento, que hoy impide medir la capacidad instalada."
                ),
                "prioridad": "Alta",
            }
        )

    return recs


# ---------------------------------------------------------------------------
# 4. Itinerarios (supuesto documentado)
# ---------------------------------------------------------------------------
def perfil_itinerarios(survey: pd.DataFrame) -> pd.DataFrame:
    """Estructura de co-ocurrencia de los códigos de `otros_destinos`.

    SUPUESTO DOCUMENTADO: los códigos del campo `otros_destinos` (320, 340,
    222, 484, 998, 999) pertenecen a un catálogo por base (V10/V11/V12) que NO
    viene con diccionario. Se reporta la estructura de co-ocurrencia —que es
    un hecho— y no se asignan nombres a los códigos, porque varias lecturas
    son consistentes con los datos (p. ej. `320` y `340` podrían ser Río Dulce
    y Livingston en cualquier orden). Nombrarlos sin el catálogo sería
    inventar. La petición del diccionario es una de las recomendaciones.
    """
    d = survey.copy()
    d["od"] = d["otros_destinos"].fillna("").astype(str).str.strip()
    d = d[d["od"].ne("") & d["od"].ne("nan")]
    d["combo"] = d["od"].apply(lambda x: "+".join(sorted(x.split(","))))
    g = d.groupby("combo", as_index=False).agg(registros=("id_unico", "count"))
    g["participacion"] = g["registros"] / g["registros"].sum()
    g["n_paradas"] = g["combo"].str.count(r"\+") + 1
    g["es_multi_parada"] = g["n_paradas"] > 1
    return g.sort_values("registros", ascending=False).reset_index(drop=True)
