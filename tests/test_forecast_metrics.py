"""Métricas MAPE/RMSE/MAE y nº de folds válidos del backtest."""

import numpy as np
import pandas as pd

from src.models import forecast as fc
from src.utils.helpers import metricas_error


def test_metricas_coinciden_con_calculo_manual():
    y = np.array([0.8, 0.5, 0.6, 0.9])
    yh = np.array([0.7, 0.6, 0.6, 1.0])
    m = metricas_error(y, yh)
    err = y - yh
    assert m["n"] == 4
    assert np.isclose(m["mae"], np.mean(np.abs(err)))
    assert np.isclose(m["rmse"], np.sqrt(np.mean(err**2)))
    assert np.isclose(m["mape"], np.mean(np.abs(err / y)) * 100)


def test_metricas_ignoran_nan():
    m = metricas_error([1.0, np.nan, 2.0], [1.0, 5.0, 3.0])
    assert m["n"] == 2 and np.isclose(m["mae"], 0.5)


def _serie(n=36, faltante=None):
    idx = pd.date_range("2023-01-01", periods=n, freq="MS")
    s = pd.Series(0.6 + 0.2 * np.sin(2 * np.pi * idx.month / 12), index=idx)
    if faltante is not None:
        s[faltante] = np.nan
    return s


def test_folds_validos_segun_historia_minima():
    """36 meses, historia mínima ETS = 25 -> 11 folds válidos (objetivos feb-dic 2025)."""
    bt = fc.backtest(_serie(36), modelos=["logit_ets", "naive_estacional"])
    ets = bt[bt["modelo"] == "logit_ets"]
    assert ets["valido"].sum() == 11
    assert ets[ets["valido"]]["fecha"].min() == pd.Timestamp("2025-02-01")
    assert (ets[ets["valido"]]["n_train"] >= fc.MIN_HISTORIA_ETS).all()


def test_expanding_window_sin_fuga_de_datos():
    """El entrenamiento de cada fold solo usa meses estrictamente anteriores."""
    s = _serie(36)
    bt = fc.backtest(s, modelos=["naive_estacional"])
    for _, f in bt[bt["valido"]].iterrows():
        assert f["n_train"] == (s.index < f["fecha"]).sum()


def test_metricas_backtest_reporta_folds_y_ganador():
    bt = fc.backtest(_serie(36), modelos=["logit_ets", "naive_estacional"])
    mt = fc.metricas_backtest(bt)
    ets = mt[mt["modelo"] == "logit_ets"].iloc[0]
    nai = mt[mt["modelo"] == "naive_estacional"].iloc[0]
    assert ets["n_folds_validos"] == 11 and ets["n_folds_excluidos"] == 25
    assert nai["n_folds_validos"] > ets["n_folds_validos"]
    assert ets["n_folds_comunes"] == nai["n_folds_comunes"] == 11
    assert mt["ganador"].sum() == 1
    # métricas del modelo = recálculo manual sobre sus folds válidos
    v = bt[(bt["modelo"] == "naive_estacional") & bt["valido"]]
    assert np.isclose(nai["mae"], np.mean(np.abs(v["y_true"] - v["y_pred"])))


def test_mes_sin_dato_no_se_evalua_ni_se_rellena_con_cero():
    s = _serie(36, faltante="2025-01-01")
    bt = fc.backtest(s, modelos=["naive_estacional"])
    assert pd.Timestamp("2025-01-01") not in set(bt["fecha"])
    assert not (bt["y_true"] == 0).any()
    assert np.isnan(fc.como_serie(s)["2025-01-01"])
