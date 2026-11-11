"""Pronóstico e imputación de series mensuales (PLAN §3).

Cuatro modelos comparados con backtest rolling-origin (expanding window):

    M1  logit_ets         ETS aditivo (tendencia + estacionalidad 12) sobre logit(y)
    M2  logit_ets_damped  igual, con tendencia amortiguada
    M3  factor_reparto    y_t = r_m * migración_t  (método literal de la guía)
    M4  naive_estacional  media del mismo mes en los últimos 2 años

Para series acotadas a [0, 1] (ocupación) se usa ``transform="logit"``: toda
predicción queda en (0, 1) por construcción. Para conteos no negativos
(encuesta) se usa ``transform="log"``; el plan no fija la transformación de la
encuesta, así que ésta es una decisión explícita y documentada.

Reglas: la ausencia de dato no es cero (los NaN nunca se rellenan con 0 ni se
evalúan); las estimaciones se rotulan siempre como ``tipo = "Estimación"``.
"""

from __future__ import annotations

import warnings
from typing import Callable

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src.utils.helpers import ilogit, logit, metricas_error

TIPO_ESTIMACION = "Estimación"
MIN_HISTORIA_ETS = 25  # ETS estacional exige >= 2 ciclos (+1 mes de margen)
MODELOS = ["logit_ets", "logit_ets_damped", "factor_reparto", "naive_estacional"]
ETIQUETAS = {
    "logit_ets": "Logit-ETS",
    "logit_ets_damped": "Logit-ETS damped",
    "factor_reparto": "Perfil estacional + factor de reparto",
    "naive_estacional": "Naive estacional (media 2 años)",
}
# Historia mínima por modelo (meses con dato observado en el entrenamiento)
MIN_TRAIN = {
    "logit_ets": MIN_HISTORIA_ETS,
    "logit_ets_damped": MIN_HISTORIA_ETS,
    "factor_reparto": 12,
    "naive_estacional": 12,
}


# ---------------------------------------------------------------------------
# Utilidades de serie
# ---------------------------------------------------------------------------
def como_serie(datos, columna: str | None = None, fecha: str = "fecha") -> pd.Series:
    """DataFrame (fecha + columna) o Series -> Series mensual ('MS') con índice completo.

    Los meses faltantes quedan como NaN (nunca 0).
    """
    if isinstance(datos, pd.DataFrame):
        if columna is None:
            columna = [c for c in datos.columns if c != fecha][0]
        s = pd.Series(datos[columna].to_numpy(dtype=float), index=pd.to_datetime(datos[fecha]))
    else:
        s = datos.astype(float).copy()
        s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    s.index = s.index.to_period("M").to_timestamp()
    s = s[~s.index.duplicated(keep="last")]
    full = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    s = s.reindex(full)
    s.index.name = "fecha"
    return s


def _a_transformada(y: np.ndarray, transform: str) -> np.ndarray:
    if transform == "logit":
        return logit(y)
    if transform == "log":
        return np.log1p(np.clip(y, 0, None))
    return np.asarray(y, dtype=float)


def _de_transformada(x: np.ndarray, transform: str) -> np.ndarray:
    if transform == "logit":
        return ilogit(x)
    if transform == "log":
        return np.expm1(x).clip(min=0)
    return np.asarray(x, dtype=float)


def _acotar(pred: np.ndarray, bounds: tuple[float, float] | None) -> np.ndarray:
    return pred if bounds is None else np.clip(pred, bounds[0], bounds[1])


def _futuro(train: pd.Series, h: int) -> pd.DatetimeIndex:
    return pd.date_range(train.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")


# ---------------------------------------------------------------------------
# Modelos: cada uno recibe train (serie mensual con posibles NaN) y devuelve
# un array de h predicciones (NaN si no se puede estimar).
# ---------------------------------------------------------------------------
def _ets(train: pd.Series, h: int, transform: str, damped: bool) -> np.ndarray:
    obs = train.dropna()
    if len(obs) < MIN_HISTORIA_ETS:
        return np.full(h, np.nan)
    # Huecos internos: interpolación lineal SOLO como entrada del ajuste ETS.
    y = train.interpolate(limit_area="inside").dropna()
    z = _a_transformada(y.to_numpy(), transform)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            fit = ExponentialSmoothing(
                z,
                trend="add",
                damped_trend=damped,
                seasonal="add",
                seasonal_periods=12,
                initialization_method="estimated",
            ).fit()
            return _de_transformada(fit.forecast(h), transform)
        except Exception:  # noqa: BLE001  (ajuste no converge -> fold no válido)
            return np.full(h, np.nan)


def _naive_estacional(train: pd.Series, h: int, anios: int = 2) -> np.ndarray:
    obs = train.dropna()
    out = []
    for f in _futuro(train, h):
        previos = obs[obs.index.month == f.month].tail(anios)
        out.append(previos.mean() if len(previos) else np.nan)
    return np.asarray(out, dtype=float)


def _factor_reparto(
    train: pd.Series, h: int, migracion: pd.Series | None, ventana: int = 24
) -> np.ndarray:
    """y_m = r_m * migración_m; r_m = Σy / Σmigración del mismo mes calendario
    sobre la ventana de referencia (solo meses con ambas fuentes observadas)."""
    if migracion is None:
        return np.full(h, np.nan)
    mig = migracion.reindex(train.index.union(_futuro(train, h)))
    comun = pd.concat([train, mig.reindex(train.index)], axis=1, keys=["y", "m"]).dropna()
    comun = comun[comun["m"] > 0].tail(ventana)
    out = []
    for f in _futuro(train, h):
        c = comun[comun.index.month == f.month]
        m_f = mig.get(f, np.nan)
        if c.empty or np.isnan(m_f):
            out.append(np.nan)
        else:
            out.append(c["y"].sum() / c["m"].sum() * m_f)
    return np.asarray(out, dtype=float)


def predecir(
    modelo: str,
    train: pd.Series,
    h: int = 1,
    *,
    transform: str = "logit",
    bounds: tuple[float, float] | None = (0.0, 1.0),
    migracion: pd.Series | None = None,
) -> pd.Series:
    """Pronostica ``h`` meses con ``modelo`` entrenando solo con ``train``."""
    if modelo == "logit_ets":
        p = _ets(train, h, transform, damped=False)
    elif modelo == "logit_ets_damped":
        p = _ets(train, h, transform, damped=True)
    elif modelo == "factor_reparto":
        p = _factor_reparto(train, h, migracion)
    elif modelo == "naive_estacional":
        p = _naive_estacional(train, h)
    else:
        raise ValueError(f"Modelo desconocido: {modelo!r}. Opciones: {MODELOS}")
    return pd.Series(_acotar(p, bounds), index=_futuro(train, h), name=modelo)


# ---------------------------------------------------------------------------
# Backtest rolling-origin (expanding window, horizonte de 1 mes)
# ---------------------------------------------------------------------------
def backtest(
    serie: pd.Series,
    *,
    modelos: list[str] | None = None,
    desde: str | pd.Timestamp | None = None,
    hasta: str | pd.Timestamp | None = None,
    transform: str = "logit",
    bounds: tuple[float, float] | None = (0.0, 1.0),
    migracion: pd.Series | None = None,
) -> pd.DataFrame:
    """Para cada mes objetivo t observado se entrena SOLO con datos < t.

    Devuelve una fila por (fecha, modelo): y_true, y_pred, error, n_train, valido.
    Un fold es inválido si no cumple la historia mínima del modelo o el modelo
    no puede estimar (se reporta, no se descarta en silencio).
    """
    serie = como_serie(serie)
    modelos = modelos or MODELOS
    desde = pd.Timestamp(desde) if desde is not None else serie.index[0]
    hasta = pd.Timestamp(hasta) if hasta is not None else serie.index[-1]
    objetivos = [t for t in serie.index if desde <= t <= hasta and not np.isnan(serie[t])]

    filas = []
    for t in objetivos:
        train = serie[serie.index < t]
        n_train = int(train.notna().sum())
        for m in modelos:
            if n_train >= MIN_TRAIN[m]:
                pred = predecir(
                    m, train, 1, transform=transform, bounds=bounds, migracion=migracion
                )
                y_pred = float(pred.iloc[0]) if pred.index[0] == t else np.nan
            else:
                y_pred = np.nan
            filas.append(
                {
                    "fecha": t,
                    "modelo": m,
                    "y_true": float(serie[t]),
                    "y_pred": y_pred,
                    "error": float(serie[t]) - y_pred,
                    "n_train": n_train,
                    "valido": not np.isnan(y_pred),
                }
            )
    return pd.DataFrame(filas)


def metricas_backtest(folds: pd.DataFrame) -> pd.DataFrame:
    """MAPE/RMSE/MAE por modelo + nº de folds válidos y excluidos.

    ``*_comunes`` se calculan solo sobre los folds válidos para TODOS los modelos
    (comparación justa); ``ganador`` se decide por MAPE sobre folds comunes.
    """
    if folds.empty:
        return pd.DataFrame()
    modelos = list(folds["modelo"].unique())
    validos_por_modelo = {
        m: set(folds[(folds["modelo"] == m) & folds["valido"]]["fecha"]) for m in modelos
    }
    comunes = set.intersection(*validos_por_modelo.values()) if modelos else set()

    filas = []
    for m in modelos:
        f = folds[folds["modelo"] == m]
        v = f[f["valido"]]
        e = metricas_error(v["y_true"], v["y_pred"])
        c = v[v["fecha"].isin(comunes)]
        ec = metricas_error(c["y_true"], c["y_pred"])
        filas.append(
            {
                "modelo": m,
                "etiqueta": ETIQUETAS.get(m, m),
                "n_folds_validos": int(len(v)),
                "n_folds_excluidos": int(len(f) - len(v)),
                "mape": e["mape"],
                "rmse": e["rmse"],
                "mae": e["mae"],
                "n_folds_comunes": int(len(c)),
                "mape_comunes": ec["mape"],
                "rmse_comunes": ec["rmse"],
                "mae_comunes": ec["mae"],
            }
        )
    out = pd.DataFrame(filas)
    col = "mape_comunes" if out["mape_comunes"].notna().any() else "mape"
    out["ganador"] = out[col] == out[col].min()
    return out.sort_values(col).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Pronóstico hacia adelante e imputación de huecos
# ---------------------------------------------------------------------------
def pronostico(
    serie,
    meses: int = 12,
    modelo: str = "logit_ets_damped",
    *,
    transform: str = "logit",
    bounds: tuple[float, float] | None = (0.0, 1.0),
    migracion: pd.Series | None = None,
) -> pd.DataFrame:
    """Pronóstico a ``meses`` desde el último dato. Columnas: fecha, modelo, estimacion, tipo."""
    s = como_serie(serie)
    p = predecir(modelo, s, meses, transform=transform, bounds=bounds, migracion=migracion)
    return pd.DataFrame(
        {"fecha": p.index, "modelo": modelo, "estimacion": p.to_numpy(), "tipo": TIPO_ESTIMACION}
    )


def imputar_mes(
    serie,
    fecha,
    modelo: str = "logit_ets",
    *,
    transform: str = "logit",
    bounds: tuple[float, float] | None = (0.0, 1.0),
    migracion: pd.Series | None = None,
) -> float:
    """Estima un mes (hueco real o enmascarado) entrenando solo con datos < fecha."""
    s = como_serie(serie)
    f = pd.Timestamp(fecha).to_period("M").to_timestamp()
    train = s[s.index < f]
    p = predecir(modelo, train, 1, transform=transform, bounds=bounds, migracion=migracion)
    # Si hay un hueco entre el último dato de train y f, 'predecir' arranca tras train.
    meses_hasta = (f.year - train.index[-1].year) * 12 + f.month - train.index[-1].month
    if meses_hasta != 1:
        p = predecir(
            modelo, train, meses_hasta, transform=transform, bounds=bounds, migracion=migracion
        )
    return float(p.loc[f])


def pronostico_ocupacion(serie: pd.DataFrame, meses: int = 12, modelo: str = "logit_ets_damped"):
    """Pronóstico de ocupación de Izabal (índice en [0, 1]).

    Args:
        serie: serie mensual de ocupación (DataFrame ``fecha`` + ``indice_ocupacion``).
        meses: meses a proyectar.
        modelo: por defecto Logit-ETS damped (el usado en PLAN §3.4).

    Returns:
        DataFrame con columnas: fecha, modelo, estimacion, tipo ('Estimación').
    """
    return pronostico(
        como_serie(serie, "indice_ocupacion"), meses, modelo, transform="logit", bounds=(0.0, 1.0)
    )


# ---------------------------------------------------------------------------
# Salidas procesadas (forecast_*.parquet)
# ---------------------------------------------------------------------------
def serie_mensual_encuesta(survey_izabal_daily: pd.DataFrame, columna: str = "visitantes") -> pd.Series:
    """Suma mensual de la encuesta de Izabal; meses sin filas -> NaN (no 0)."""
    d = survey_izabal_daily.copy()
    d["fecha"] = pd.to_datetime(d["fecha"]).dt.to_period("M").dt.to_timestamp()
    m = d.groupby("fecha")[columna].sum()
    full = pd.date_range(m.index.min(), m.index.max(), freq="MS")
    return m.reindex(full).rename_axis("fecha")


def serie_mensual_migracion(
    migration_monthly: pd.DataFrame, fronteras: list[str], tipos: list[str]
) -> pd.Series:
    """Visitantes mensuales (migración) de las fronteras indicadas."""
    d = migration_monthly[
        migration_monthly["Frontera"].isin(fronteras) & migration_monthly["Tipo de Viajero"].isin(tipos)
    ]
    return d.groupby("fecha")["viajeros"].sum().rename_axis("fecha")


def generar_salidas(
    ocupacion: pd.DataFrame,
    encuesta_diaria: pd.DataFrame,
    migracion: pd.Series | None = None,
    horizonte: int = 12,
) -> dict[str, pd.DataFrame]:
    """Construye forecast_occupancy / forecast_survey / forecast_metrics.

    - forecast_occupancy: pronóstico de ocupación de cada modelo (hasta ``horizonte``
      meses tras el último dato). Todo en [0, 1].
    - forecast_survey: backtest (observado vs estimado) y estimación del mes sin filas.
    - forecast_metrics: MAPE/RMSE/MAE por modelo y objetivo, con folds válidos.
    """
    occ = como_serie(ocupacion, "indice_ocupacion")
    enc = serie_mensual_encuesta(encuesta_diaria)

    bt_occ = backtest(occ, transform="logit", bounds=(0.0, 1.0), migracion=migracion)
    bt_enc = backtest(enc, transform="log", bounds=(0.0, np.inf), migracion=migracion)

    filas_occ = []
    for m in MODELOS:
        p = pronostico(occ, horizonte, m, transform="logit", bounds=(0.0, 1.0), migracion=migracion)
        filas_occ.append(p)
    f_occ = pd.concat(filas_occ, ignore_index=True)
    f_occ = f_occ.dropna(subset=["estimacion"])

    # Encuesta: folds del backtest + imputación de los meses sin filas
    f_enc = bt_enc.rename(columns={"y_true": "observado", "y_pred": "estimacion"})[
        ["fecha", "modelo", "observado", "estimacion", "valido"]
    ].copy()
    f_enc["tipo"] = TIPO_ESTIMACION
    huecos = enc.index[enc.isna()]
    extra = []
    for h in huecos:
        for m in ["logit_ets", "logit_ets_damped", "factor_reparto", "naive_estacional"]:
            try:
                v = imputar_mes(enc, h, m, transform="log", bounds=(0.0, np.inf), migracion=migracion)
            except Exception:  # noqa: BLE001
                v = np.nan
            extra.append(
                {"fecha": h, "modelo": m, "observado": np.nan, "estimacion": v,
                 "valido": not np.isnan(v), "tipo": TIPO_ESTIMACION}
            )
    if extra:
        f_enc = pd.concat([f_enc, pd.DataFrame(extra)], ignore_index=True)

    metr = []
    for objetivo, bt in [("ocupacion", bt_occ), ("encuesta", bt_enc)]:
        mt = metricas_backtest(bt)
        mt.insert(0, "objetivo", objetivo)
        metr.append(mt)
    f_met = pd.concat(metr, ignore_index=True)

    return {
        "forecast_occupancy.parquet": f_occ.reset_index(drop=True),
        "forecast_survey.parquet": f_enc.reset_index(drop=True),
        "forecast_metrics.parquet": f_met,
    }
