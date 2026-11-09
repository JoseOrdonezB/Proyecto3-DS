"""Pronóstico de ocupación de Izabal para 2026 (Fase 3).

En construcción: el modelo definitivo se implementará en la Fase 3.
"""

import pandas as pd


def pronostico_ocupacion(serie: pd.DataFrame, meses: int = 12) -> pd.DataFrame:
    """Placeholder del modelo de pronóstico.

    Args:
        serie: serie mensual de ocupación de Izabal (índice fecha).
        meses: cantidad de meses a proyectar.

    Returns:
        DataFrame con columnas: fecha, estimacion, tipo ('Estimación').
    """
    raise NotImplementedError("El modelo de pronóstico se implementa en la Fase 3.")
