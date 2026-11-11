"""Calendario de feriados de Guatemala (2021-2026) y eventos del destino.

Base del Módulo 2 (lift de festividades). Las fechas móviles de Semana Santa se
calculan a partir de la Pascua; el resto son fechas fijas.

⚠️ Guatemala traslada algunos feriados por acuerdo gubernativo (p. ej. 30 jun
o 20 oct cuando caen entre semana). Aquí se usa la fecha oficial de calendario;
si la guía del curso o INGUAT fijan otra fecha para un año concreto, ajustar
``_FERIADOS_FIJOS`` o agregar el traslado en ``_TRASLADOS``.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import pandas as pd
from dateutil.easter import easter

ANIO_INICIO = 2021
ANIO_FIN = 2026

# (mes, día, nombre). El 15 ago es feriado solo en la Ciudad de Guatemala.
_FERIADOS_FIJOS = [
    (1, 1, "Año Nuevo"),
    (5, 1, "Día del Trabajo"),
    (6, 30, "Día del Ejército"),
    (8, 15, "Virgen de la Asunción (Ciudad de Guatemala)"),
    (9, 15, "Independencia"),
    (10, 20, "Día de la Revolución"),
    (11, 1, "Día de Todos los Santos"),
    (12, 24, "Nochebuena (medio día)"),
    (12, 25, "Navidad"),
    (12, 31, "Fin de año (medio día)"),
]

# Traslados puntuales {fecha_original: fecha_nueva}. Vacío por defecto.
_TRASLADOS: dict[date, date] = {}


def _feriados_anio(anio: int) -> list[tuple[date, str]]:
    pascua = easter(anio)
    filas = [(date(anio, m, d), n) for m, d, n in _FERIADOS_FIJOS]
    filas += [
        (pascua - timedelta(days=3), "Jueves Santo"),
        (pascua - timedelta(days=2), "Viernes Santo"),
        (pascua - timedelta(days=1), "Sábado Santo"),
    ]
    return [(_TRASLADOS.get(f, f), n) for f, n in filas]


def _eventos_anio(anio: int) -> list[tuple[date, date, str]]:
    """Ventanas (inicio, fin, nombre) de eventos con efecto sobre el destino."""
    pascua = easter(anio)
    return [
        (pascua - timedelta(days=6), pascua, "Semana Santa"),  # lunes a domingo
        (date(anio, 12, 24), date(anio + 1, 1, 1), "Navidad y Año Nuevo"),
    ]


@lru_cache(maxsize=1)
def calendario() -> pd.DataFrame:
    """Calendario diario: una fila por (fecha, tipo, nombre).

    Columnas: fecha (datetime64), nombre, tipo ('feriado' | 'evento').
    Sin duplicados por (fecha, tipo); fechas recortadas a 2021-2026.
    """
    ini, fin = pd.Timestamp(ANIO_INICIO, 1, 1), pd.Timestamp(ANIO_FIN, 12, 31)
    filas = []
    for anio in range(ANIO_INICIO, ANIO_FIN + 1):
        for f, nombre in _feriados_anio(anio):
            filas.append((pd.Timestamp(f), nombre, "feriado"))
    for anio in range(ANIO_INICIO - 1, ANIO_FIN + 1):
        for a, b, nombre in _eventos_anio(anio):
            for f in pd.date_range(a, b, freq="D"):
                filas.append((f, nombre, "evento"))
    df = pd.DataFrame(filas, columns=["fecha", "nombre", "tipo"])
    df = df[df["fecha"].between(ini, fin)]
    df = df.drop_duplicates(["fecha", "tipo"]).sort_values(["fecha", "tipo"])
    return df.reset_index(drop=True)


def _como_fechas(valor) -> pd.Series:
    if isinstance(valor, pd.Series):
        return pd.to_datetime(valor).dt.normalize()
    return pd.Series(pd.to_datetime(valor)).dt.normalize()


def _mapa(tipo: str) -> dict:
    c = calendario()
    c = c[c["tipo"].eq(tipo)]
    return dict(zip(c["fecha"], c["nombre"]))


def es_feriado(fecha):
    """True si la fecha es feriado. Escalar -> bool; Serie -> Serie bool."""
    f = _como_fechas(fecha)
    out = f.isin(_mapa("feriado").keys())
    return out if isinstance(fecha, pd.Series) else bool(out.iloc[0])


def es_evento(fecha):
    """True si la fecha cae dentro de un evento (Semana Santa, Navidad-Año Nuevo)."""
    f = _como_fechas(fecha)
    out = f.isin(_mapa("evento").keys())
    return out if isinstance(fecha, pd.Series) else bool(out.iloc[0])


def nombre_evento(fecha):
    """Nombre más específico: el feriado si lo hay; si no, el evento; si no, None."""
    fer, ev = _mapa("feriado"), _mapa("evento")
    f = _como_fechas(fecha)
    out = f.map(lambda d: fer.get(d, ev.get(d)))
    return out if isinstance(fecha, pd.Series) else out.iloc[0]
