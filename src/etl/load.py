"""Carga de las tres fuentes de datos del observatorio.

Fuentes:
    1. Base_Migracion_2009-2026jun.xlsx  -> conteos oficiales por frontera (mensual)
    2. indice_ocupacion_mensual_2023_2025_1.csv -> ocupación hotelera (mensual)
    3. BD_COMPLEMENTARIA (parquet)        -> encuesta de turismo (diaria)
"""

import pandas as pd

from src.config import (
    MIGRATION_COLUMNS,
    MIGRATION_FILE,
    OCCUPANCY_COLUMNS,
    OCCUPANCY_FILE,
    SURVEY_COLUMNS,
    SURVEY_FILE,
)


def _validate_columns(df: pd.DataFrame, expected: list, source: str) -> None:
    """Verifica que la fuente contenga las columnas esperadas."""
    missing = sorted(set(expected) - set(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas en la fuente '{source}': {missing}")


def load_migration(path: str | None = None) -> pd.DataFrame:
    """Carga la base oficial de migración (hoja 'Datos')."""
    df = pd.read_excel(path or MIGRATION_FILE, sheet_name="Datos")
    _validate_columns(df, MIGRATION_COLUMNS, "migración")
    return df


def load_occupancy(path: str | None = None) -> pd.DataFrame:
    """Carga el índice de ocupación mensual por departamento."""
    df = pd.read_csv(path or OCCUPANCY_FILE)
    _validate_columns(df, OCCUPANCY_COLUMNS, "ocupación")
    return df


def load_survey(path: str | None = None) -> pd.DataFrame:
    """Carga la BD complementaria (encuesta de turismo en parquet)."""
    df = pd.read_parquet(path or SURVEY_FILE)
    _validate_columns(df, SURVEY_COLUMNS, "encuesta")
    return df


def load_all() -> dict:
    """Carga las tres fuentes y las devuelve en un diccionario."""
    return {
        "migration": load_migration(),
        "occupancy": load_occupancy(),
        "survey": load_survey(),
    }
