"""Transformaciones analíticas del observatorio.

Todas las funciones reciben DataFrames ya limpiados (src.etl.clean).
"""

import numpy as np
import pandas as pd

from src.config import (
    CORRIDOR_BORDERS,
    DESTINATION_DEPT,
    ISABAL_FEEDER_BORDERS,
    IZABAL_BORDERS,
    SURVEY_BORDER_MAP,
    VENTANA_COINCIDENTE,
    VISITOR_TYPES,
)
from src.utils.helpers import mapa_frontera, safe_div


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
    """Participación mensual de Izabal en el corredor (nunca se suman subdestinos).

    REGLA 1 (la ausencia de dato no es cero):
        Un mes en el que una frontera NO tiene registro es ausencia, no cero.
        Por eso no se rellena con 0: si ninguna frontera de Izabal tiene dato
        en el mes, ``viajeros_izabal`` queda en NaN, y ``participacion`` también
        (el denominador estaría incompleto y la razón sería sesgada).

        Consecuencia medida: Izabal tiene registro de VISITANTES solo entre
        2009-01 y 2016-12; de 2017 en adelante la frontera solo registra
        'Viajero' (tránsito), que no es visitante. Por eso 2017-2026 aparece
        como "Sin dato" y no como 0 % de participación.

    Columnas de contexto:
        n_fronteras_con_dato  cuántas fronteras del corredor tienen registro ese mes
        corredor_completo     si las 5 fronteras del corredor tienen dato ese mes
    """
    corredor = df[df["es_visita"] & df["Frontera"].isin(CORRIDOR_BORDERS)]
    pivot = corredor.pivot_table(
        index="fecha", columns="Frontera", values="Viajero", aggfunc="sum"
    )
    if pivot.empty:
        return pd.DataFrame(
            columns=[
                "fecha",
                "viajeros_izabal",
                "viajeros_corredor",
                "participacion",
                "n_fronteras_con_dato",
                "corredor_completo",
            ]
        )
    # min_count=1 -> NaN solo si NINGUNA frontera tiene dato (ausencia real)
    cols_frontera = list(pivot.columns)
    pivot["viajeros_corredor"] = pivot.sum(axis=1, min_count=1)
    # Izabal = suma de sus fronteras (es el destino completo, no subdestinos)
    izabal_cols = [c for c in cols_frontera if c in IZABAL_BORDERS]
    pivot["viajeros_izabal"] = (
        pivot[izabal_cols].sum(axis=1, min_count=1) if izabal_cols else pd.NA
    )
    # Conteo de cobertura sobre las columnas de frontera (antes de derivar columnas)
    pivot["n_fronteras_con_dato"] = pivot[cols_frontera].notna().sum(axis=1).astype(int)
    pivot["corredor_completo"] = pivot["n_fronteras_con_dato"].eq(len(CORRIDOR_BORDERS))
    # La participación solo es calculable si el corredor está completo: con una
    # frontera faltando, tanto el numerador como el denominador están sesgados.
    pivot["participacion"] = np.where(
        pivot["corredor_completo"], pivot["viajeros_izabal"] / pivot["viajeros_corredor"], np.nan
    )
    return pivot[
        [
            "viajeros_izabal",
            "viajeros_corredor",
            "participacion",
            "n_fronteras_con_dato",
            "corredor_completo",
        ]
    ].reset_index()


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




# ---------------------------------------------------------------------------
# Utilidades internas (Fase 2)
# ---------------------------------------------------------------------------
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
SEGMENTOS = ["Turista", "Excursionista"]


def _mes(fechas: pd.Series) -> pd.Series:
    """Fecha -> primer día del mes."""
    return pd.to_datetime(fechas).dt.to_period("M").dt.to_timestamp()


def _rango_mensual(inicio, fin) -> pd.DatetimeIndex:
    ini = pd.Timestamp(inicio).to_period("M").to_timestamp()
    fin = pd.Timestamp(fin).to_period("M").to_timestamp()
    return pd.date_range(ini, fin, freq="MS", name="fecha")


def _con_segmento(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega 'segmento' (Turista = pernocta > 24 h; Excursionista = < 24 h) y 'mes'."""
    out = df.copy()
    out["segmento"] = np.where(out["es_pernocta"], "Turista", "Excursionista")
    out["mes"] = _mes(out["fecha"])
    # Días-persona solo con noches válidas (regla 2: nunca se promedia la permanencia)
    valido = out["es_pernocta"] & out["noches_validadas"].notna()
    out["visitantes_pernocta"] = out["total_visitantes"].where(valido, 0.0)
    out["dias_persona"] = (out["noches_validadas"] * out["total_visitantes"]).where(valido, 0.0)
    return out


def _rangos_texto(meses) -> str:
    """Comprime una lista de meses en rangos legibles: '2017-01→2022-12, 2025-01'."""
    meses = sorted(pd.to_datetime(list(meses)))
    if not meses:
        return ""
    tramos, ini, prev = [], meses[0], meses[0]
    for m in meses[1:]:
        if m == prev + pd.offsets.MonthBegin(1):
            prev = m
            continue
        tramos.append((ini, prev))
        ini = prev = m
    tramos.append((ini, prev))
    return ", ".join(
        a.strftime("%Y-%m") if a == b else f"{a:%Y-%m}→{b:%Y-%m}" for a, b in tramos
    )


def _izabal_diaria_activa(df: pd.DataFrame) -> pd.DataFrame:
    """Serie diaria de Izabal sobre los días en que la encuesta operó.

    Un día con operativo de encuesta (cualquier destino) pero sin registros de
    Izabal es un cero observado. Un día sin operativo no existe en la serie
    (regla 1: la ausencia de dato no es cero).
    """
    activos = pd.DatetimeIndex(pd.to_datetime(df["fecha"]).dt.normalize().unique()).sort_values()
    iz = df[df["es_izabal"]]
    diaria = (
        iz.groupby(pd.to_datetime(iz["fecha"]).dt.normalize())
        .agg(registros=("id_unico", "count"), visitantes=("total_visitantes", "sum"))
        .reindex(activos, fill_value=0)
    )
    diaria.index.name = "fecha"
    diaria = diaria.reset_index()
    # Solo dentro del período en que Izabal tiene cobertura
    if not iz.empty:
        ini, fin = iz["fecha"].min(), iz["fecha"].max()
        diaria = diaria[diaria["fecha"].between(ini, fin)]
    return diaria.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Módulo 1 · Demanda y mercados emisores
# ---------------------------------------------------------------------------
def survey_segment_tourist_excursionist(df: pd.DataFrame) -> pd.DataFrame:
    """Segmentación mensual turista vs excursionista en Izabal (absolutos muestrales y %).

    Meses sin ninguna fila de encuesta (p. ej. 2025-01) quedan en NaN; un mes con
    encuestas pero sin excursionistas es un 0 observado.
    """
    iz = _con_segmento(df[df["es_izabal"]])
    if iz.empty:
        return pd.DataFrame(columns=["fecha", "segmento", "registros", "visitantes",
                                     "participacion_registros", "participacion_visitantes"])
    g = iz.groupby(["mes", "segmento"]).agg(
        registros=("id_unico", "count"), visitantes=("total_visitantes", "sum")
    )
    rango = _rango_mensual(iz["mes"].min(), iz["mes"].max())
    idx = pd.MultiIndex.from_product([rango, SEGMENTOS], names=["fecha", "segmento"])
    g.index.names = ["fecha", "segmento"]
    g = g.reindex(idx)
    con_dato = set(iz["mes"])
    observado = g.index.get_level_values("fecha").isin(list(con_dato))
    g.loc[observado] = g.loc[observado].fillna(0)
    g = g.reset_index()
    tot = g.groupby("fecha")[["registros", "visitantes"]].transform(lambda x: x.sum(min_count=1))
    g["participacion_registros"] = g["registros"] / tot["registros"].replace(0, np.nan)
    g["participacion_visitantes"] = g["visitantes"] / tot["visitantes"].replace(0, np.nan)
    return g


def survey_days_person_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Días-persona y estadía media ponderada por mes (Izabal, muestral).

    estadia_ponderada = suma(días-persona) / suma(visitantes pernocta)  (regla 2).
    Meses sin encuesta -> NaN.
    """
    iz = _con_segmento(df[df["es_izabal"]])
    cols = ["fecha", "registros", "visitantes", "visitantes_pernocta",
            "visitantes_excursionistas", "dias_persona", "estadia_ponderada",
            "proporcion_pernocta"]
    if iz.empty:
        return pd.DataFrame(columns=cols)
    iz["visitantes_excursion"] = iz["total_visitantes"].where(~iz["es_pernocta"], 0.0)
    g = iz.groupby("mes").agg(
        registros=("id_unico", "count"),
        visitantes=("total_visitantes", "sum"),
        visitantes_pernocta=("visitantes_pernocta", "sum"),
        visitantes_excursionistas=("visitantes_excursion", "sum"),
        dias_persona=("dias_persona", "sum"),
    )
    g = g.reindex(_rango_mensual(iz["mes"].min(), iz["mes"].max()))
    g["estadia_ponderada"] = g["dias_persona"] / g["visitantes_pernocta"].replace(0, np.nan)
    g["proporcion_pernocta"] = g["visitantes_pernocta"] / (
        g["visitantes_pernocta"] + g["visitantes_excursionistas"]
    ).replace(0, np.nan)
    g.index.name = "fecha"
    return g.reset_index()[cols]


def survey_izabal_cube(df: pd.DataFrame) -> pd.DataFrame:
    """Cubo muestral de Izabal para filtros enlazados del dashboard.

    Una fila por combinación (mes, segmento, nacionalidad, residencia, frontera,
    hospedaje, transporte, subdestino) con medidas aditivas: registros,
    visitantes, visitantes_pernocta y días-persona. Las razones (%, estadía) se
    recalculan en el dashboard sobre el subconjunto filtrado, nunca se promedian.
    """
    iz = _con_segmento(df[df["es_izabal"]])
    dims = ["mes", "segmento", "nacionalidad", "residencia", "frontera_nombre",
            "hospedaje", "tipo_transporte", "subdestino"]
    g = (
        iz.groupby(dims, as_index=False)
        .agg(
            registros=("id_unico", "count"),
            visitantes=("total_visitantes", "sum"),
            visitantes_pernocta=("visitantes_pernocta", "sum"),
            dias_persona=("dias_persona", "sum"),
        )
        .rename(columns={"mes": "fecha"})
    )
    g["frontera_migracion"] = mapa_frontera(g["frontera_nombre"])
    return g.sort_values(["fecha", "registros"], ascending=[True, False]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Módulo 2 · Patrón semanal y efecto de feriados
# ---------------------------------------------------------------------------
def survey_weekly_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Patrón semanal NORMALIZADO de Izabal (promedio por día, no suma bruta).

    indice = promedio del día de la semana / promedio de todos los días activos.
    Un índice de 1.20 significa 20 % más registros que un día típico.
    """
    d = _izabal_diaria_activa(df)
    d["dia_num"] = d["fecha"].dt.dayofweek
    media_reg, media_vis = d["registros"].mean(), d["visitantes"].mean()
    g = d.groupby("dia_num").agg(
        n_dias=("fecha", "count"),
        registros_promedio=("registros", "mean"),
        visitantes_promedio=("visitantes", "mean"),
    ).reindex(range(7))
    g["dia_semana"] = DIAS_SEMANA
    g["indice_registros"] = g["registros_promedio"] / media_reg if media_reg else np.nan
    g["indice_visitantes"] = g["visitantes_promedio"] / media_vis if media_vis else np.nan
    return g.reset_index()[["dia_num", "dia_semana", "n_dias", "registros_promedio",
                            "visitantes_promedio", "indice_registros", "indice_visitantes"]]


def survey_holiday_lift(df: pd.DataFrame) -> pd.DataFrame:
    """Lift % de cada feriado/evento frente al día regular promedio (Izabal).

    Base: días con operativo de encuesta. Día regular = ni feriado ni evento.
    lift_pct = (promedio en el evento / promedio en día regular - 1) * 100.
    Se reporta para el período completo (anio = 'Todos') y por año, comparando
    contra los días regulares del mismo año (el volumen muestral cambia por año).
    """
    from src.analysis.feriados import calendario

    d = _izabal_diaria_activa(df)
    cal = calendario()
    especiales = set(cal["fecha"])
    d["regular"] = ~d["fecha"].isin(especiales)

    eventos = cal.merge(d, on="fecha", how="inner")
    # Navidad-Año Nuevo: el 1 de enero pertenece a la temporada del año anterior
    eventos["anio"] = eventos["fecha"].dt.year - (
        eventos["nombre"].eq("Navidad y Año Nuevo") & eventos["fecha"].dt.month.eq(1)
    ).astype(int)
    d["anio"] = d["fecha"].dt.year

    filas = []
    for periodo in ["Todos"] + sorted(eventos["anio"].unique().tolist()):
        if periodo == "Todos":
            ev, reg = eventos, d[d["regular"]]
        else:
            ev = eventos[eventos["anio"].eq(periodo)]
            reg = d[d["regular"] & d["anio"].eq(periodo)]
        if reg.empty:
            continue
        base_r, base_v = reg["registros"].mean(), reg["visitantes"].mean()
        for (nombre, tipo), e in ev.groupby(["nombre", "tipo"]):
            prom_r, prom_v = e["registros"].mean(), e["visitantes"].mean()
            filas.append(
                {
                    "anio": str(periodo),
                    "nombre": nombre,
                    "tipo": tipo,
                    "n_dias": int(len(e)),
                    "n_dias_regulares": int(len(reg)),
                    "registros_promedio": prom_r,
                    "visitantes_promedio": prom_v,
                    "regular_registros_promedio": base_r,
                    "regular_visitantes_promedio": base_v,
                    "lift_registros_pct": (prom_r / base_r - 1) * 100 if base_r else np.nan,
                    "lift_visitantes_pct": (prom_v / base_v - 1) * 100 if base_v else np.nan,
                }
            )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Módulo 4 · Cruce encuesta ↔ migración por frontera
# ---------------------------------------------------------------------------
def _migracion_por_frontera_mes(mig: pd.DataFrame) -> pd.DataFrame:
    m = mig.assign(
        visitantes=mig["Viajero"].where(mig["Tipo de Viajero"].isin(VISITOR_TYPES), 0.0),
        transito=mig["Viajero"].where(mig["Tipo de Viajero"].eq("Viajero"), 0.0),
    )
    return (
        m.groupby(["fecha", "Frontera"], as_index=False)
        .agg(migracion_visitantes=("visitantes", "sum"), migracion_transito=("transito", "sum"))
    )


def survey_border_migration(sur: pd.DataFrame, mig: pd.DataFrame) -> pd.DataFrame:
    """Cruce mensual por frontera: encuesta (muestral) + migración (absoluto).

    Solo fronteras con equivalencia 1:1 (SURVEY_BORDER_MAP). Meses en que la
    encuesta no operó en esa frontera no aparecen (no son cero).
    """
    s = sur.assign(mes=_mes(sur["fecha"]))
    s["frontera_migracion"] = mapa_frontera(s["frontera_nombre"])
    s = s[s["frontera_migracion"].notna()]
    s["vis_iz"] = s["total_visitantes"].where(s["es_izabal"], 0.0)
    enc = s.groupby(["mes", "frontera_nombre", "frontera_migracion"], as_index=False).agg(
        registros_total=("id_unico", "count"),
        registros_izabal=("es_izabal", "sum"),
        visitantes_total=("total_visitantes", "sum"),
        visitantes_izabal=("vis_iz", "sum"),
    )
    enc = enc.rename(columns={"mes": "fecha"})
    mm = _migracion_por_frontera_mes(mig).rename(columns={"Frontera": "frontera_migracion"})
    out = enc.merge(mm, on=["fecha", "frontera_migracion"], how="left")
    out["registros_izabal"] = out["registros_izabal"].astype(int)
    return out.sort_values(["fecha", "frontera_nombre"]).reset_index(drop=True)


def _wilson(k, n, z: float = 1.96):
    """Intervalo de Wilson al 95% para una proporción.

    Con k = 0 el límite inferior es exactamente 0 (en aritmética de punto
    flotante quedaba en ~1e-18, lo que hacía que el intervalo "no contuviera"
    la estimación puntual).
    """
    k, n = np.asarray(k, dtype=float), np.asarray(n, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = k / n
        den = 1 + z**2 / n
        centro = (p + z**2 / (2 * n)) / den
        margen = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    inferior = np.where(k <= 0, 0.0, centro - margen)
    superior = np.where(k >= n, 1.0, centro + margen)
    return np.clip(inferior, 0, 1), np.clip(superior, 0, 1)


def survey_transfer_rate(sur: pd.DataFrame, mig: pd.DataFrame) -> pd.DataFrame:
    """Tasa de transferencia por frontera de entrada hacia Izabal/Caribe.

    tasa_transferencia = visitantes encuestados con destino Izabal en la frontera b
                         / visitantes encuestados en la frontera b      (∈ [0, 1])

    Es una proporción MUESTRAL (regla 6: no se multiplica por la migración para
    obtener totales). La migración del mismo período (solo meses en que la
    encuesta operó en b) se adjunta como contexto absoluto, en dos versiones:
    visitantes (Turista+Excursionista) y tránsito (Viajero).
    Incluye IC 95 % de Wilson sobre registros. anio = 'Todos' o el año.
    """
    bm = survey_border_migration(sur, mig)
    bm["anio"] = bm["fecha"].dt.year
    filas = []
    for periodo in ["Todos"] + sorted(bm["anio"].unique().tolist()):
        sub = bm if periodo == "Todos" else bm[bm["anio"].eq(periodo)]
        g = sub.groupby(["frontera_nombre", "frontera_migracion"], as_index=False).agg(
            meses_encuesta=("fecha", "nunique"),
            registros_total=("registros_total", "sum"),
            registros_izabal=("registros_izabal", "sum"),
            visitantes_total=("visitantes_total", "sum"),
            visitantes_izabal=("visitantes_izabal", "sum"),
            migracion_visitantes=("migracion_visitantes", "sum"),
            migracion_transito=("migracion_transito", "sum"),
        )
        g = g[g["registros_total"] > 0]
        g.insert(0, "anio", str(periodo))
        filas.append(g)
    out = pd.concat(filas, ignore_index=True)
    out["tasa_transferencia"] = out["visitantes_izabal"] / out["visitantes_total"]
    out["tasa_registros"] = out["registros_izabal"] / out["registros_total"]
    out["ic_inf"], out["ic_sup"] = _wilson(out["registros_izabal"], out["registros_total"])
    tot_iz = out.groupby("anio")["registros_izabal"].transform("sum").replace(0, np.nan)
    out["peso_en_izabal"] = out["registros_izabal"] / tot_iz
    return out.sort_values(["anio", "tasa_transferencia"], ascending=[True, False]).reset_index(drop=True)


def corridor_funnel_matrix(mig: pd.DataFrame) -> pd.DataFrame:
    """Matriz corredor × mes × tipo de flujo (formato largo).

    tipo_flujo ∈ {Visitantes, Tránsito, Cruceristas}. Las celdas sin registro
    quedan en NaN (no cero): permite ver la discontinuidad marítima 2017-2022.
    """
    rango = _rango_mensual(mig["fecha"].min(), mig["fecha"].max())
    c = mig[mig["Frontera"].isin(CORRIDOR_BORDERS)].copy()
    c["tipo_flujo"] = np.select(
        [c["Tipo de Viajero"].isin(VISITOR_TYPES), c["Tipo de Viajero"].eq("Viajero"),
         c["Tipo de Viajero"].eq("Cruceristas")],
        ["Visitantes", "Tránsito", "Cruceristas"],
        default="Otro",
    )
    g = c.groupby(["fecha", "Frontera", "tipo_flujo"])["Viajero"].sum()
    idx = pd.MultiIndex.from_product(
        [rango, CORRIDOR_BORDERS, ["Visitantes", "Tránsito", "Cruceristas"]],
        names=["fecha", "Frontera", "tipo_flujo"],
    )
    out = g.reindex(idx).rename("viajeros").reset_index()
    out["es_izabal"] = out["Frontera"].isin(IZABAL_BORDERS)
    return out


def migration_seasonal_index(mig: pd.DataFrame, desde: int = 2023, hasta: int = 2025) -> pd.DataFrame:
    """Perfil estacional por frontera: índice del mes = valor / promedio mensual del año.

    Se promedia el índice entre años COMPLETOS (12 meses con dato) del rango
    [desde, hasta]; por defecto 2023-2025 (posterior al quiebre 2022→2023).
    Incluye el agregado 'Alimentadoras de Izabal' (las 9 fronteras que
    efectivamente alimentan el destino; ver ISABAL_FEEDER_BORDERS).
    """
    mm = _migracion_por_frontera_mes(mig)
    alim = (
        mm[mm["Frontera"].isin(ISABAL_FEEDER_BORDERS)]
        .groupby("fecha", as_index=False)[["migracion_visitantes", "migracion_transito"]].sum()
        .assign(Frontera="Alimentadoras de Izabal")
    )
    mm = pd.concat([mm, alim], ignore_index=True)
    mm = mm[mm["fecha"].dt.year.between(desde, hasta)]
    filas = []
    for tipo, col in [("Visitantes", "migracion_visitantes"), ("Tránsito", "migracion_transito")]:
        x = mm[["fecha", "Frontera", col]].rename(columns={col: "valor"})
        x = x[x["valor"] > 0]
        x["anio"], x["mes"] = x["fecha"].dt.year, x["fecha"].dt.month
        completos = x.groupby(["Frontera", "anio"])["mes"].transform("nunique").eq(12)
        x = x[completos]
        if x.empty:
            continue
        x["indice"] = x["valor"] / x.groupby(["Frontera", "anio"])["valor"].transform("mean")
        g = x.groupby(["Frontera", "mes"], as_index=False).agg(
            indice=("indice", "mean"), n_anios=("anio", "nunique")
        )
        g.insert(1, "tipo_flujo", tipo)
        filas.append(g)
    return pd.concat(filas, ignore_index=True) if filas else pd.DataFrame(
        columns=["Frontera", "tipo_flujo", "mes", "indice", "n_anios"])


# ---------------------------------------------------------------------------
# Módulo 4 · Conectividad fluvial y embudo de transferencia
# ---------------------------------------------------------------------------
# Nodos del corredor fluvial de Izabal. 'Río Dulce', 'Puerto Barrios' y
# 'Livingston' son los tres nodos de agua (río y mar); el resto son nodos
# terrestres del interior del departamento.
NODOS_CORREDOR = [
    "Río Dulce",
    "Puerto Barrios",
    "Livingston",
    "Santo Tomás de Castilla",
    "Quiriguá",
    "El Estor",
    "Entre Ríos",
    "Morales",
    "Los Amates",
    "Izabal (genérico)",
]
NODOS_AGUA = ["Río Dulce", "Puerto Barrios", "Livingston"]


def survey_border_node_flow(df: pd.DataFrame) -> pd.DataFrame:
    """Flujo frontera de entrada -> nodo del corredor fluvial (Módulo 4).

    Es la tabla que reconstruye la cadena de conectividad del destino:
    de dónde entra cada visitante (frontera) y hacia qué nodo se dirige.

    Base: encuesta (MUESTRAL, sin factor de expansión -> solo proporciones).
    Regla 4: los nodos NO se suman entre sí para obtener el total, porque un
    mismo visitante puede recorrer varios; por eso cada fila se reporta con su
    participación dentro de la frontera, nunca como total del destino.
    """
    d = _con_segmento(df[df["es_izabal"]])
    d = d.assign(nodo=d["subdestino"].where(d["subdestino"].isin(NODOS_CORREDOR), "Otro"))
    g = (
        d.groupby(["frontera_nombre", "nodo", "segmento"], as_index=False)
        .agg(
            registros=("id_unico", "count"),
            visitantes=("total_visitantes", "sum"),
            dias_persona=("dias_persona", "sum"),
        )
        .sort_values(["frontera_nombre", "registros"], ascending=[True, False])
    )
    # Participación dentro de cada frontera (no del destino)
    tot = g.groupby("frontera_nombre")["registros"].transform("sum").replace(0, np.nan)
    g["participacion_frontera"] = g["registros"] / tot
    # Rango de fechas en que la frontera operó (para el contexto)
    ventana = (
        d.groupby("frontera_nombre")["fecha"]
        .agg(fecha_min="min", fecha_max="max")
        .reset_index()
    )
    g = g.merge(ventana, on="frontera_nombre", how="left")
    g["es_nodo_agua"] = g["nodo"].isin(NODOS_AGUA)
    return g.reset_index(drop=True)


def survey_node_transport(df: pd.DataFrame) -> pd.DataFrame:
    """Modo de transporte por nodo del corredor (Módulo 4).

    LIMITACIÓN DOCUMENTADA: la taxonomía de la encuesta (11 categorías) NO
    incluye transporte acuático (lancha, barco, lanchaje). Por eso la
    conectividad fluvial NO se mide como modo de transporte, sino como cadena
    espacial de nodos. Esta tabla muestra el modo tierra/aire con el que se
    llega a cada nodo, que es lo que sí es observable.
    """
    d = df[df["es_izabal"]].copy()
    d["nodo"] = d["subdestino"].where(d["subdestino"].isin(NODOS_CORREDOR), "Otro")
    g = (
        d.groupby(["nodo", "tipo_transporte"], as_index=False)
        .agg(registros=("id_unico", "count"), visitantes=("total_visitantes", "sum"))
        .sort_values(["nodo", "registros"], ascending=[True, False])
    )
    total = g.groupby("nodo")["registros"].transform("sum").replace(0, np.nan)
    g["participacion_nodo"] = g["registros"] / total
    g["es_nodo_agua"] = g["nodo"].isin(NODOS_AGUA)
    return g.reset_index(drop=True)


def maritime_flow_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Perfil de cobertura por frontera: qué tipos de flujo existen y si se solapan.

    HALLAZGO CENTRAL DEL MÓDULO 4: en las fronteras marítimas de Izabal
    (Puerto Barrios, Livingston, Santo Tomás) los registros de VISITANTES
    (Turista/Excursionista) y de TRÁNSITO ('Viajero') nunca coinciden en un
    mismo mes: los visitantes se apagan en 2016 y el tránsito solo aparece
    desde 2023. Por eso el embudo marítimo NO es medible con la base oficial
    y su tasa de transferencia no debe calcularse.

    `meses_solape` es la métrica que lo demuestra: 0 para toda frontera
    marítima, >0 para las terrestres alimentadoras.
    """
    fronteras = list(dict.fromkeys([*CORRIDOR_BORDERS, *ISABAL_FEEDER_BORDERS]))
    filas = []
    for f in fronteras:
        s = df[df["Frontera"].eq(f)]
        if s.empty:
            continue
        meses_vis = set(_mes(s.loc[s["es_visita"], "fecha"]))
        meses_tra = set(_mes(s.loc[s["Tipo de Viajero"].eq("Viajero"), "fecha"]))
        meses_cru = set(_mes(s.loc[s["Tipo de Viajero"].eq("Cruceristas"), "fecha"]))
        solape = sorted(meses_vis & meses_tra)
        filas.append(
            {
                "Frontera": f,
                "es_destino_maritimo": f in IZABAL_BORDERS,
                "es_alimentadora": f in ISABAL_FEEDER_BORDERS,
                "meses_visitantes": len(meses_vis),
                "meses_transito": len(meses_tra),
                "meses_cruceros": len(meses_cru),
                "meses_solape": len(solape),
                "embudo_medible": len(solape) > 0,
                "rango_visitantes": _rangos_texto(meses_vis),
                "rango_transito": _rangos_texto(meses_tra),
                "rango_cruceros": _rangos_texto(meses_cru),
            }
        )
    return pd.DataFrame(filas).sort_values(
        ["es_alimentadora", "meses_solape"], ascending=[False, False]
    ).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Módulo 3 · Ventana coincidente afluencia ↔ ocupación
# ---------------------------------------------------------------------------
def occupancy_vs_affluence(occ: pd.DataFrame, sur: pd.DataFrame, mig: pd.DataFrame) -> pd.DataFrame:
    """Cruce mensual de ocupación hotelera de Izabal con medidas de afluencia.

    Rango: meses de la serie de ocupación (2023-2025). Columnas de afluencia:
      - registros/visitantes de la encuesta en Izabal (muestral)
      - participacion_izabal_encuesta: % de los registros del mes que van a Izabal
        (controla el tamaño variable de la muestra)
      - proporcion_pernocta y estadia_ponderada (muestral)
      - migracion_alimentadoras: visitantes absolutos por las 11 fronteras mapeadas
      - transito_izabal: 'Viajero' en las fronteras marítimas de Izabal
    en_ventana marca la ventana coincidente (VENTANA_COINCIDENTE).
    """
    o = occ.copy()
    o["fecha"] = _mes(o["fecha"])
    iz = o[o["departamento"].eq(DESTINATION_DEPT)].set_index("fecha")["indice_ocupacion"]
    nac = o.groupby("fecha")["indice_ocupacion"].mean()
    rango = _rango_mensual(o["fecha"].min(), o["fecha"].max())

    dp = survey_days_person_monthly(sur).set_index("fecha")
    s = sur.assign(mes=_mes(sur["fecha"]))
    total_mes = s.groupby("mes")["id_unico"].count()

    mm = _migracion_por_frontera_mes(mig)
    alim = mm[mm["Frontera"].isin(SURVEY_BORDER_MAP.values())].groupby("fecha")["migracion_visitantes"].sum()
    trans = mm[mm["Frontera"].isin(IZABAL_BORDERS)].groupby("fecha")["migracion_transito"].sum()
    # Meses sin registro de tránsito en Izabal -> NaN (no cero)
    trans = trans[trans > 0]

    out = pd.DataFrame(index=rango)
    out["ocupacion"] = iz.reindex(rango)
    out["ocupacion_promedio_departamental"] = nac.reindex(rango)
    out["registros_encuesta"] = dp["registros"].reindex(rango)
    out["visitantes_encuesta"] = dp["visitantes"].reindex(rango)
    out["participacion_izabal_encuesta"] = (dp["registros"] / total_mes).reindex(rango)
    out["proporcion_pernocta"] = dp["proporcion_pernocta"].reindex(rango)
    out["estadia_ponderada"] = dp["estadia_ponderada"].reindex(rango)
    out["migracion_alimentadoras"] = alim.reindex(rango)
    out["transito_izabal"] = trans.reindex(rango)
    ini, fin = pd.Timestamp(VENTANA_COINCIDENTE[0]), pd.Timestamp(VENTANA_COINCIDENTE[1])
    out["en_ventana"] = (out.index >= ini) & (out.index <= fin)
    out.index.name = "fecha"
    return out.reset_index()


# ---------------------------------------------------------------------------
# Calidad de datos
# ---------------------------------------------------------------------------
def data_quality(mig: pd.DataFrame, sur: pd.DataFrame) -> pd.DataFrame:
    """Resumen de cobertura, huecos y notas para documentar limitaciones.

    Además del resumen por frontera / destino, agrega filas explícitas
    (fuente = 'hueco' o 'nota') con:
      - el hueco 2022 de visitantes en las fronteras marítimas de Izabal,
      - el hueco 2025-01 de la encuesta de Izabal/Caribe,
      - decimales en 'Viajero' (estimaciones expandidas, no conteos exactos),
      - cobertura parcial de 2026 y el quiebre metodológico 2022→2023.
    'huecos_visitantes' lista los meses sin visitantes dentro del rango de cada segmento.
    """
    filas = []

    for frontera in sorted(mig["Frontera"].unique()):
        s = mig[mig["Frontera"].eq(frontera)]
        rango = _rango_mensual(s["fecha"].min(), s["fecha"].max())
        con_vis = set(s.loc[s["es_visita"], "fecha"])
        faltan = [m for m in rango if m not in con_vis]
        filas.append(
            {
                "fuente": "migracion",
                "segmento": frontera,
                "fecha_min": s["fecha"].min().date(),
                "fecha_max": s["fecha"].max().date(),
                "meses_con_datos": s["fecha"].nunique(),
                "meses_con_visitantes": len(con_vis),
                "meses_con_transito": s.loc[s["Tipo de Viajero"].eq("Viajero"), "fecha"].nunique(),
                "meses_con_cruceros": s.loc[s["Tipo de Viajero"].eq("Cruceristas"), "fecha"].nunique(),
                "huecos_visitantes": _rangos_texto(faltan),
                "detalle": "",
            }
        )

    s_mes = sur.assign(mes=_mes(sur["fecha"]))
    for destino in sorted(s_mes["nuevo_destino"].unique()):
        s = s_mes[s_mes["nuevo_destino"].eq(destino)]
        rango = _rango_mensual(s["mes"].min(), s["mes"].max())
        con = set(s["mes"])
        faltan = [m for m in rango if m not in con]
        filas.append(
            {
                "fuente": "encuesta",
                "segmento": destino,
                "fecha_min": s["fecha"].min().date(),
                "fecha_max": s["fecha"].max().date(),
                "meses_con_datos": len(con),
                "meses_con_visitantes": len(con),
                "meses_con_transito": 0,
                "meses_con_cruceros": 0,
                "huecos_visitantes": _rangos_texto(faltan),
                "detalle": f"{s['fecha'].nunique()} días con registros",
            }
        )

    extra = []
    # Hueco 2022: fronteras marítimas de Izabal sin ninguna fila
    m22 = mig[mig["Frontera"].isin(IZABAL_BORDERS) & mig["fecha"].dt.year.eq(2022)]
    if m22.empty:
        extra.append({
            "fuente": "hueco", "segmento": "Fronteras marítimas de Izabal (visitantes)",
            "fecha_min": pd.Timestamp("2022-01-01").date(), "fecha_max": pd.Timestamp("2022-12-01").date(),
            "huecos_visitantes": "2022-01→2022-12",
            "detalle": "0 filas en 2022 para " + ", ".join(IZABAL_BORDERS)
            + ". Los visitantes (Turista+Excursionista) solo existen 2009-2016; desde 2023 solo 'Viajero'.",
        })
    # Hueco 2025-01 (y cualquier otro) en la encuesta de Izabal/Caribe
    iz = s_mes[s_mes["es_izabal"]]
    if not iz.empty:
        rango = _rango_mensual(iz["mes"].min(), iz["mes"].max())
        faltan = [m for m in rango if m not in set(iz["mes"])]
        for m in faltan:
            extra.append({
                "fuente": "hueco", "segmento": "Encuesta Izabal/Caribe",
                "fecha_min": m.date(), "fecha_max": (m + pd.offsets.MonthEnd(0)).date(),
                "huecos_visitantes": m.strftime("%Y-%m"),
                "detalle": "Mes sin ninguna fila de encuesta para Izabal/Caribe: se trata como "
                "sin dato (NaN), nunca como cero; se estima en el Módulo 2.",
            })
    # Decimales en 'Viajero'
    dec = mig[(mig["Viajero"] % 1) != 0]
    if not dec.empty:
        extra.append({
            "fuente": "nota", "segmento": "Decimales en 'Viajero'",
            "fecha_min": dec["fecha"].min().date(), "fecha_max": dec["fecha"].max().date(),
            "detalle": f"{len(dec):,} filas con decimales: son estimaciones expandidas de encuesta, "
            "no conteos exactos. Se redondea solo al mostrar.",
        })
    extra.append({
        "fuente": "nota", "segmento": "Cobertura parcial 2026 (migración)",
        "fecha_min": pd.Timestamp("2026-01-01").date(), "fecha_max": mig["fecha"].max().date(),
        "detalle": "2026 cubre solo enero-junio: no comparar totales anuales de 2026.",
    })
    extra.append({
        "fuente": "nota", "segmento": "Quiebre metodológico 2022→2023 (migración)",
        "fecha_min": pd.Timestamp("2023-01-01").date(), "fecha_max": mig["fecha"].max().date(),
        "detalle": "Desde 2023 el sistema depurado excluye compradores fronterizos frecuentes; "
        "los niveles no son perfectamente comparables con 2022 hacia atrás.",
    })
    extra.append({
        "fuente": "nota", "segmento": "Capacidad instalada de alojamiento",
        "detalle": "Ninguna fuente trae establecimientos, habitaciones ni plazas cama: "
        "no se estiman (se recomienda incorporarlas).",
    })
    out = pd.concat([pd.DataFrame(filas), pd.DataFrame(extra)], ignore_index=True)
    out[["huecos_visitantes", "detalle"]] = out[["huecos_visitantes", "detalle"]].fillna("")
    return out
