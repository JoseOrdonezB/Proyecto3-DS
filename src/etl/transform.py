"""Transformaciones analíticas del observatorio.

Todas las funciones reciben DataFrames ya limpiados (src.etl.clean).
"""

import pandas as pd

from src.config import CORRIDOR_BORDERS, DESTINATION_DEPT, IZABAL_BORDERS
from src.utils.helpers import safe_div


# ---------------------------------------------------------------------------
# Migración oficial (conteos absolutos)
# ---------------------------------------------------------------------------
def migration_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Serie mensual por frontera, vía, tipo de viajero y país."""
    return (
        df.groupby(["fecha", "Frontera", "Vía", "Tipo de Viajero", "País"], as_index=False)
        .agg(viajeros=("Viajero", "sum"))
        .sort_values(["fecha", "Frontera"])
    )


def destination_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Visitantes del destino (Izabal) por mes, frontera y tipo de viajero."""
    visitas = df[df["es_visita"] & df["es_izabal"]]
    return (
        visitas.groupby(["fecha", "Frontera", "Tipo de Viajero"], as_index=False)
        .agg(viajeros=("Viajero", "sum"))
        .sort_values(["fecha", "Frontera"])
    )


def nationality_top(df: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Top de nacionalidades del destino, separando nacionales y extranjeros.

    Regla: los nacionales incorporan factor de expansión, por lo que se
    reportan por separado.
    """
    visitas = df[df["es_visita"] & df["es_izabal"]]
    grupo = (
        visitas.groupby(["País", "es_nacional"], as_index=False)
        .agg(viajeros=("Viajero", "sum"))
    )
    grupo["tipo"] = grupo["es_nacional"].map({True: "Nacional", False: "Extranjero"})
    grupo = grupo.sort_values(["tipo", "viajeros"], ascending=[True, False])
    grupo["rank"] = grupo.groupby("tipo").cumcount() + 1
    grupo = grupo[grupo["rank"] <= top]
    return grupo[["tipo", "rank", "País", "viajeros"]].reset_index(drop=True)


def corridor_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Visitantes mensuales del corredor completo (destino + puntos de conexión)."""
    corredor = df[df["es_visita"] & df["Frontera"].isin(CORRIDOR_BORDERS)]
    return (
        corredor.groupby(["fecha", "Frontera"], as_index=False)
        .agg(viajeros=("Viajero", "sum"))
        .sort_values(["fecha", "Frontera"])
    )


def destination_transit_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Viajeros (tránsito / trasbordo) del destino por mes y frontera.

    Regla estricta: 'Viajero' NO es visitante, pero sí es parte del
    flujo de transferencia del reto de conectividad fluvial.
    """
    transito = df[df["Tipo de Viajero"].eq("Viajero") & df["es_izabal"]]
    return (
        transito.groupby(["fecha", "Frontera"], as_index=False)
        .agg(viajeros=("Viajero", "sum"))
        .sort_values(["fecha", "Frontera"])
    )


def destination_cruise_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Cruceristas por mes y frontera (solo 2009-2022)."""
    cruceros = df[df["Tipo de Viajero"].eq("Cruceristas")]
    return (
        cruceros.groupby(["fecha", "Frontera"], as_index=False)
        .agg(viajeros=("Viajero", "sum"))
        .sort_values(["fecha", "Frontera"])
    )


def corridor_transit_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Viajeros (tránsito) del corredor por mes y frontera."""
    transito = df[df["Tipo de Viajero"].eq("Viajero") & df["Frontera"].isin(CORRIDOR_BORDERS)]
    return (
        transito.groupby(["fecha", "Frontera"], as_index=False)
        .agg(viajeros=("Viajero", "sum"))
        .sort_values(["fecha", "Frontera"])
    )


def corridor_share(df: pd.DataFrame) -> pd.DataFrame:
    """Participación mensual de Izabal en el corredor (nunca se suman subdestinos)."""
    corredor = df[df["es_visita"] & df["Frontera"].isin(CORRIDOR_BORDERS)]
    pivot = corredor.pivot_table(
        index="fecha", columns="Frontera", values="Viajero", aggfunc="sum", fill_value=0
    )
    if pivot.empty:
        return pd.DataFrame(columns=["fecha", "viajeros_izabal", "viajeros_corredor", "participacion"])
    pivot["viajeros_corredor"] = pivot.sum(axis=1)
    # Izabal = suma de sus fronteras (es el destino completo, no subdestinos)
    izabal_cols = [c for c in pivot.columns if c in IZABAL_BORDERS]
    pivot["viajeros_izabal"] = pivot[izabal_cols].sum(axis=1) if izabal_cols else 0
    pivot["participacion"] = pivot["viajeros_izabal"] / pivot["viajeros_corredor"].replace(0, pd.NA)
    return pivot[["viajeros_izabal", "viajeros_corredor", "participacion"]].reset_index()


# ---------------------------------------------------------------------------
# Ocupación hotelera
# ---------------------------------------------------------------------------
def occupancy_series(df: pd.DataFrame) -> pd.DataFrame:
    """Serie mensual de ocupación de Izabal con índice completo.

    Los meses sin registro se conservan como NaN (nunca como cero).
    """
    izabal = df[df["departamento"].eq(DESTINATION_DEPT)].copy()
    izabal = izabal.set_index("fecha").sort_index()
    indice_completo = pd.date_range(izabal.index.min(), izabal.index.max(), freq="MS")
    serie = izabal.reindex(indice_completo)
    serie.index.name = "fecha"
    return serie.reset_index()


# ---------------------------------------------------------------------------
# Encuesta de turismo (BD complementaria) - muestral, sin factor de expansión
# ---------------------------------------------------------------------------
def survey_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Serie diaria de la encuesta por destino asignado."""
    return (
        df.groupby(["fecha", "nuevo_destino"], as_index=False)
        .agg(registros=("id_unico", "count"), visitantes=("total_visitantes", "sum"))
        .sort_values(["fecha", "nuevo_destino"])
    )


def survey_izabal_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Serie diaria de la encuesta para Izabal / Caribe."""
    izabal = df[df["es_izabal"]]
    return (
        izabal.groupby("fecha", as_index=False)
        .agg(registros=("id_unico", "count"), visitantes=("total_visitantes", "sum"))
        .sort_values("fecha")
    )


def survey_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """Embudo de transferencia: frontera de entrada -> destino asignado."""
    return (
        df.groupby(["frontera_nombre", "nuevo_destino"], as_index=False)
        .agg(registros=("id_unico", "count"), visitantes=("total_visitantes", "sum"))
        .sort_values(["frontera_nombre", "registros"], ascending=[True, False])
    )


def survey_subdestino(df: pd.DataFrame) -> pd.DataFrame:
    """Subdestinos dentro de Izabal / Caribe (regla: no se suman entre sí)."""
    izabal = df[df["es_izabal"]]
    return (
        izabal.groupby("subdestino", as_index=False)
        .agg(
            registros=("id_unico", "count"),
            pernocta=("es_pernocta", "sum"),
            noches_totales=("noches_validadas", "sum"),
            visitantes=("total_visitantes", "sum"),
        )
        .sort_values("registros", ascending=False)
    )


def _survey_stay_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Estadía media ponderada: suma(días-persona) / suma(visitantes).

    Se calcula exclusivamente sobre el segmento 'mayor a 1 día'.
    Los excursionistas (<24 hrs) tienen permanencia 1 por definición.
    """
    pernocta = df[df["es_pernocta"]]
    dias_persona = (pernocta["noches_validadas"] * pernocta["total_visitantes"]).sum()
    visitantes = pernocta["total_visitantes"].sum()

    excursionistas = df[~df["es_pernocta"]]
    visitantes_excursion = excursionistas["total_visitantes"].sum()

    return pd.DataFrame(
        {
            "indicador": [
                "estadia_media_ponderada",
                "dias_persona",
                "visitantes_pernocta",
                "visitantes_excursionistas",
                "proporcion_pernocta",
            ],
            "valor": [
                safe_div(dias_persona, visitantes),
                dias_persona,
                visitantes,
                visitantes_excursion,
                safe_div(visitantes, visitantes + visitantes_excursion),
            ],
        }
    )


def survey_stay(df: pd.DataFrame) -> pd.DataFrame:
    """Estadía media ponderada para toda la encuesta."""
    return _survey_stay_segment(df)


def survey_stay_izabal(df: pd.DataFrame) -> pd.DataFrame:
    """Estadía media ponderada para Izabal / Caribe."""
    return _survey_stay_segment(df[df["es_izabal"]])


def survey_lodging(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución de hospedaje en Izabal / Caribe (porcentajes muestrales)."""
    izabal = df[df["es_izabal"]]
    total = izabal["id_unico"].count()
    tabla = (
        izabal.groupby("hospedaje", as_index=False)
        .agg(registros=("id_unico", "count"))
        .sort_values("registros", ascending=False)
    )
    tabla["participacion"] = tabla["registros"] / total if total else 0.0
    return tabla


def survey_transport(df: pd.DataFrame) -> pd.DataFrame:
    """Medio de transporte en Izabal / Caribe (porcentajes muestrales)."""
    izabal = df[df["es_izabal"]]
    total = izabal["id_unico"].count()
    tabla = (
        izabal.groupby("tipo_transporte", as_index=False)
        .agg(registros=("id_unico", "count"))
        .sort_values("registros", ascending=False)
    )
    tabla["participacion"] = tabla["registros"] / total if total else 0.0
    return tabla


def survey_residence(df: pd.DataFrame) -> pd.DataFrame:
    """Residencia de los visitantes de Izabal / Caribe (porcentajes muestrales)."""
    izabal = df[df["es_izabal"]]
    total = izabal["id_unico"].count()
    tabla = (
        izabal.groupby("residencia", as_index=False)
        .agg(registros=("id_unico", "count"))
        .sort_values("registros", ascending=False)
    )
    tabla["participacion"] = tabla["registros"] / total if total else 0.0
    return tabla


def data_quality(mig: pd.DataFrame, sur: pd.DataFrame) -> pd.DataFrame:
    """Resumen de cobertura y huecos para documentar limitaciones.

    Documenta el hallazgo crítico: los datos marítimos de visitantes
    (Turista/Excursionista) solo cubren 2009-2016; desde 2023 solo
    existen registros de 'Viajero' (tránsito) en las fronteras de Izabal.
    """
    filas = []

    for frontera in sorted(mig["Frontera"].unique()):
        s = mig[mig["Frontera"].eq(frontera)]
        filas.append(
            {
                "fuente": "migracion",
                "segmento": frontera,
                "fecha_min": s["fecha"].min().date(),
                "fecha_max": s["fecha"].max().date(),
                "meses_con_datos": s["fecha"].nunique(),
                "meses_con_visitantes": s.loc[s["es_visita"], "fecha"].nunique(),
                "meses_con_transito": s.loc[s["Tipo de Viajero"].eq("Viajero"), "fecha"].nunique(),
                "meses_con_cruceros": s.loc[s["Tipo de Viajero"].eq("Cruceristas"), "fecha"].nunique(),
            }
        )

    for destino in sorted(sur["nuevo_destino"].unique()):
        s = sur[sur["nuevo_destino"].eq(destino)]
        filas.append(
            {
                "fuente": "encuesta",
                "segmento": destino,
                "fecha_min": s["fecha"].min().date(),
                "fecha_max": s["fecha"].max().date(),
                "meses_con_datos": s["fecha"].nunique(),
                "meses_con_visitantes": s["fecha"].nunique(),
                "meses_con_transito": 0,
                "meses_con_cruceros": 0,
            }
        )

    return pd.DataFrame(filas)
