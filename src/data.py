"""Carga de datos procesados para el dashboard.

Si los archivos procesados no existen, ejecuta automáticamente el pipeline.
"""

from pathlib import Path

import pandas as pd

from src.config import DATA_PROCESSED


def ensure_processed() -> Path:
    """Garantiza que existan los datos procesados y devuelve la ruta."""
    marca = DATA_PROCESSED / "destination_monthly.parquet"
    if not marca.exists():
        from src.etl.pipeline import run

        run()
    return DATA_PROCESSED


def load(nombre: str) -> pd.DataFrame:
    """Carga un conjunto procesado por nombre (con o sin extensión)."""
    ruta = ensure_processed()
    nombre = nombre if nombre.endswith(".parquet") else f"{nombre}.parquet"
    return pd.read_parquet(ruta / nombre)


def resumen() -> pd.DataFrame:
    """Resumen de los conjuntos procesados (filas, columnas, archivo)."""
    ruta = ensure_processed()
    filas = []
    for archivo in sorted(ruta.glob("*.parquet")):
        df = pd.read_parquet(archivo)
        filas.append(
            {
                "archivo": archivo.name,
                "filas": len(df),
                "columnas": df.shape[1],
                "tamano_kb": round(archivo.stat().st_size / 1024, 1),
            }
        )
    return pd.DataFrame(filas)
