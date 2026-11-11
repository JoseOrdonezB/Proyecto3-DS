"""Helpers de normalización y transformación de uso compartido."""

import unicodedata

import numpy as np
import pandas as pd

from src.config import SURVEY_BORDER_MAP

# ---------------------------------------------------------------------------
# Normalización de subdestinos dentro de Izabal / Caribe
# ---------------------------------------------------------------------------
# El campo 'destino' de la BD complementaria tiene múltiples variantes
# (typos, mayúsculas, nombres compuestos). Se mapean a nombres canónicos.
SUBDESTINO_KEYWORDS = [
    ("rio dulce", "Río Dulce"),
    ("río dulce", "Río Dulce"),
    ("puerto barrios", "Puerto Barrios"),
    ("livingston", "Livingston"),
    ("quirigua", "Quiriguá"),
    ("morales", "Morales"),
    ("entre rios", "Entre Ríos"),
    ("entre ríos", "Entre Ríos"),
    ("santo tomas", "Santo Tomás de Castilla"),
    ("santo tomás", "Santo Tomás de Castilla"),
    ("amates", "Los Amates"),
    ("el estor", "El Estor"),
    ("amatique", "Amatique"),
    ("castillo", "Castillo de San Felipe"),
    ("bananeras", "Bananeras"),
    ("mariscos", "Mariscos"),
    ("tenedores", "Tenedores"),
    ("machaca", "Machaca"),
    ("izabal", "Izabal (genérico)"),
]


def normalize_subdestino(value) -> str:
    """Mapea el valor libre de 'destino' a un subdestino canónico."""
    s = str(value).strip().lower()
    if not s or s in ("nan", "none", "no especificado"):
        return "No especificado"
    for keyword, canonical in SUBDESTINO_KEYWORDS:
        if keyword in s:
            return canonical
    return "Otro"


def safe_div(numerador, denominador, default=0.0):
    """División segura que evita errores con denominadores cero."""
    if denominador in (0, 0.0) or denominador is None:
        return default
    return numerador / denominador


# ---------------------------------------------------------------------------
# Transformación logit (series acotadas a [0, 1], p. ej. índice de ocupación)
# ---------------------------------------------------------------------------
EPS = 1e-4


def logit(p, eps: float = EPS):
    """logit(p) = ln(p / (1 - p)), con p recortado a [eps, 1 - eps]."""
    p = np.clip(np.asarray(p, dtype=float), eps, 1.0 - eps)
    return np.log(p / (1.0 - p))


def ilogit(x):
    """Inversa del logit (sigmoide). La salida siempre queda en (0, 1)."""
    x = np.clip(np.asarray(x, dtype=float), -50.0, 50.0)
    return 1.0 / (1.0 + np.exp(-x))


# ---------------------------------------------------------------------------
# Métricas de error de pronóstico
# ---------------------------------------------------------------------------
def metricas_error(y_true, y_pred) -> dict:
    """MAPE (%), RMSE y MAE entre observado y pronosticado.

    Los pares con NaN en cualquiera de los dos lados se descartan (la ausencia
    de dato no es cero). El MAPE se calcula solo sobre observados distintos de 0.
    Devuelve también ``n`` (pares usados).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ok = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true, y_pred = y_true[ok], y_pred[ok]
    if y_true.size == 0:
        return {"n": 0, "mape": np.nan, "rmse": np.nan, "mae": np.nan}
    err = y_true - y_pred
    nz = y_true != 0
    mape = float(np.mean(np.abs(err[nz] / y_true[nz])) * 100) if nz.any() else np.nan
    return {
        "n": int(y_true.size),
        "mape": mape,
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mae": float(np.mean(np.abs(err))),
    }


# ---------------------------------------------------------------------------
# Mapeo de fronteras encuesta -> migración
# ---------------------------------------------------------------------------
def _norm(texto) -> str:
    s = unicodedata.normalize("NFKD", str(texto).strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


_BORDER_LOOKUP = {_norm(k): v for k, v in SURVEY_BORDER_MAP.items()}


def mapa_frontera(valor):
    """Nombre de frontera de la encuesta -> nombre en la base de migración.

    Acepta un escalar o una ``pd.Series``. Ignora mayúsculas y tildes.
    Devuelve ``None`` (o NaN en una Serie) si la frontera no tiene equivalente.
    """
    if isinstance(valor, pd.Series):
        return valor.map(lambda v: _BORDER_LOOKUP.get(_norm(v), np.nan))
    return _BORDER_LOOKUP.get(_norm(valor))
