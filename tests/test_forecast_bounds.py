"""Ninguna predicción de ocupación puede salir de [0, 1] (PLAN §3.1, §10)."""

import numpy as np
import pandas as pd
import pytest

from src.models import forecast as fc
from src.utils.helpers import ilogit, logit


def _ocupacion(extrema: bool = False, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", "2025-12-01", freq="MS")
    estacional = np.array([0, .1, .2, .5, .4, .1, 0, .2, .1, -.6, -.2, .5])[idx.month - 1]
    base = 3.5 if extrema else 0.8  # extrema: índice pegado a 1 (donde ETS plano pasa de 100%)
    z = base + estacional + 0.05 * np.arange(len(idx)) + rng.normal(0, .15, len(idx))
    return pd.Series(ilogit(z), index=idx)


def test_logit_roundtrip_and_range():
    p = np.array([0.0, 0.01, 0.5, 0.99, 1.0])
    out = ilogit(logit(p))
    assert ((out > 0) & (out < 1)).all()
    assert np.allclose(ilogit(logit([0.2, 0.5, 0.8])), [0.2, 0.5, 0.8])


@pytest.mark.parametrize("modelo", fc.MODELOS)
@pytest.mark.parametrize("extrema", [False, True])
def test_pronostico_dentro_de_0_1(modelo, extrema):
    serie = _ocupacion(extrema)
    mig = pd.Series(1000.0, index=pd.date_range("2023-01-01", "2027-01-01", freq="MS"))
    p = fc.pronostico(serie, 12, modelo, migracion=mig).dropna(subset=["estimacion"])
    assert len(p) > 0
    assert p["estimacion"].between(0, 1).all()
    assert (p["tipo"] == fc.TIPO_ESTIMACION).all()


def test_backtest_dentro_de_0_1():
    bt = fc.backtest(_ocupacion(True))
    assert bt["y_pred"].dropna().between(0, 1).all()


def test_pronostico_ocupacion_wrapper():
    df = _ocupacion().rename("indice_ocupacion").rename_axis("fecha").reset_index()
    p = fc.pronostico_ocupacion(df, 12)
    assert list(p.columns) == ["fecha", "modelo", "estimacion", "tipo"]
    assert len(p) == 12 and p["fecha"].iloc[0] == pd.Timestamp("2026-01-01")
    assert p["estimacion"].between(0, 1).all()
