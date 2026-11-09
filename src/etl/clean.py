"""Limpieza y normalización de las fuentes.

Reglas estrictas del proyecto que se aplican aquí:
    - La ausencia de dato NO es cero: se conservan como NaN.
    - 'Viajero' y 'Cruceristas' no son visitantes.
    - No se promedian permanencias: se trabaja con noches y visitantes.
"""

import pandas as pd

from src.config import DESTINATION_REGION, IZABAL_BORDERS, VISITOR_TYPES
from src.utils.helpers import normalize_subdestino

# Columnas de texto que se normalizan (trim)
_MIGRATION_TEXT = [
    "Vía",
    "Frontera",
    "País",
    "Región",
    "Región dos",
    "Regiones OMT",
    "MCEO",
    "Agrupación Residencia",
    "Tipo de Viajero",
]

_SURVEY_TEXT = [
    "destino",
    "nuevo_destino",
    "frontera_nombre",
    "frontera_tipo",
    "residencia",
    "nacionalidad",
    "hospedaje",
    "tipo_transporte",
    "estadia",
    "BD",
]


def clean_migration(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la base oficial de migración."""
    df = df.copy()

    for col in _MIGRATION_TEXT:
        df[col] = df[col].astype(str).str.strip()

    # Fecha mensual (día 1)
    df["fecha"] = pd.to_datetime(
        dict(year=df["Año"], month=df["Mes cod"], day=1), errors="raise"
    )

    # Banderas de negocio
    df["es_visita"] = df["Tipo de Viajero"].isin(VISITOR_TYPES)
    df["es_nacional"] = df["Agrupación Residencia"].eq("Guatemala")
    df["es_izabal"] = df["Frontera"].isin(IZABAL_BORDERS)

    # Validaciones
    if (df["Viajero"] < 0).any():
        raise ValueError("La base de migración contiene valores negativos en 'Viajero'.")
    if df["fecha"].isna().any():
        raise ValueError("La base de migración contiene fechas inválidas.")

    return df


def clean_occupancy(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza el índice de ocupación mensual."""
    df = df.copy()
    df["departamento"] = df["departamento"].astype(str).str.strip()
    df["fecha"] = pd.to_datetime(
        dict(year=df["anio"], month=df["mes"], day=1), errors="raise"
    )

    if not df["indice_ocupacion"].between(0, 1).all():
        raise ValueError("El índice de ocupación debe estar en el rango [0, 1].")

    return df


def clean_survey(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la BD complementaria (encuesta de turismo).

    - Excluye registros inválidos (validacion nula).
    - Normaliza el subdestino.
    - Marca outliers de 'noches' (> 365) como nulos para no distorsionar
      la estadía media ponderada.
    """
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="raise")

    # Excluir registros inválidos (mismo criterio: validacion nula)
    df = df[df["validacion"].notna()].copy()

    for col in _SURVEY_TEXT:
        df[col] = df[col].astype(str).str.strip()

    df["subdestino"] = df["destino"].apply(normalize_subdestino)
    df["es_izabal"] = df["nuevo_destino"].eq(DESTINATION_REGION)
    df["es_pernocta"] = df["estadia"].eq("Mas de 24 Hrs")

    # Outliers de noches: se anulan para el cálculo de estadía (nunca se promedian)
    df["noches_validadas"] = df["noches"].where(df["noches"].le(365))

    return df
