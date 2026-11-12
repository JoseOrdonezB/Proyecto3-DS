"""Reglas metodológicas ampliadas (Fase 2).

Cubren las transformaciones nuevas: días-persona, segmentación, patrón semanal
normalizado, lift de feriados, cruce encuesta-migración, tasa de transferencia,
matriz del corredor, ventana coincidente y calidad de datos.
"""

import numpy as np
import pandas as pd

from src.config import IZABAL_BORDERS, SURVEY_BORDER_MAP, VENTANA_COINCIDENTE

HUECO_ENCUESTA = pd.Timestamp("2025-01-01")


# ---------------------------------------------------------------------------
# Regla 1 · La ausencia de dato no es cero
# ---------------------------------------------------------------------------
def test_hueco_2025_01_es_nan_en_segmentacion(outputs):
    seg = outputs["survey_segment.parquet"]
    hueco = seg[seg["fecha"].eq(HUECO_ENCUESTA)]
    assert len(hueco) == 2, "El mes sin encuesta debe existir como fila (para cortar la serie)."
    assert hueco[["registros", "visitantes"]].isna().all().all()


def test_hueco_2025_01_es_nan_en_dias_persona(outputs):
    dp = outputs["survey_days_person_monthly.parquet"]
    fila = dp[dp["fecha"].eq(HUECO_ENCUESTA)]
    assert len(fila) == 1
    assert fila[["registros", "dias_persona", "estadia_ponderada"]].isna().all().all()


def test_hueco_2025_01_es_nan_en_ventana(outputs):
    ova = outputs["occupancy_vs_affluence.parquet"]
    fila = ova[ova["fecha"].eq(HUECO_ENCUESTA)].iloc[0]
    assert np.isnan(fila["registros_encuesta"])
    assert not np.isnan(fila["ocupacion"]), "La ocupación sí existe en 2025-01."


def test_matriz_corredor_conserva_hueco_maritimo(outputs):
    m = outputs["corridor_funnel_matrix.parquet"]
    vis = m[m["Frontera"].isin(IZABAL_BORDERS) & m["tipo_flujo"].eq("Visitantes")]
    hueco = vis[vis["fecha"].dt.year.between(2017, 2022)]
    assert not hueco.empty
    assert hueco["viajeros"].isna().all(), "2017-2022 sin registro no puede aparecer como 0."


# ---------------------------------------------------------------------------
# Regla 2 · Estadía = suma(días-persona) / suma(visitantes), nunca promedio
# ---------------------------------------------------------------------------
def test_estadia_mensual_ponderada(outputs):
    dp = outputs["survey_days_person_monthly.parquet"].dropna(subset=["estadia_ponderada"])
    esperado = dp["dias_persona"] / dp["visitantes_pernocta"]
    assert np.allclose(dp["estadia_ponderada"], esperado)


def test_cubo_reproduce_estadia_global(outputs):
    """El cubo debe permitir recalcular la estadía global de Izabal sin promediar."""
    cubo = outputs["survey_izabal_cube.parquet"]
    stay = dict(zip(outputs["survey_stay_izabal.parquet"]["indicador"],
                    outputs["survey_stay_izabal.parquet"]["valor"]))
    estadia_cubo = cubo["dias_persona"].sum() / cubo["visitantes_pernocta"].sum()
    assert abs(estadia_cubo - stay["estadia_media_ponderada"]) < 1e-6


def test_cubo_suma_registros_izabal(outputs):
    cubo = outputs["survey_izabal_cube.parquet"]
    seg = outputs["survey_segment.parquet"]
    assert cubo["registros"].sum() == seg["registros"].sum()


# ---------------------------------------------------------------------------
# Regla 3 · No sumar la base diaria para el mes / patrón semanal normalizado
# ---------------------------------------------------------------------------
def test_patron_semanal_normalizado(outputs):
    w = outputs["survey_weekly_pattern.parquet"]
    assert len(w) == 7
    assert (w["n_dias"] > 0).all()
    # Es un promedio por día: el índice ponderado por n_dias vale 1
    ponderado = (w["indice_registros"] * w["n_dias"]).sum() / w["n_dias"].sum()
    assert abs(ponderado - 1) < 1e-9
    # No es una suma bruta: el promedio diario es mucho menor que el total mensual
    assert w["registros_promedio"].max() < 20


def test_lift_sobre_dias_validos(outputs):
    lift = outputs["survey_holiday_lift.parquet"]
    assert (lift["n_dias"] > 0).all()
    assert (lift["regular_registros_promedio"] > 0).all()
    esperado = (lift["registros_promedio"] / lift["regular_registros_promedio"] - 1) * 100
    assert np.allclose(lift["lift_registros_pct"], esperado)
    assert (lift["lift_registros_pct"] >= -100).all()
    assert "Semana Santa" in set(lift.loc[lift["anio"].eq("Todos"), "nombre"])


# ---------------------------------------------------------------------------
# Regla 4 · No sumar subdestinos
# ---------------------------------------------------------------------------
def test_cubo_no_trae_total_de_subdestinos(outputs):
    cubo = outputs["survey_izabal_cube.parquet"]
    assert not cubo["subdestino"].str.lower().isin({"total", "todos"}).any()


# ---------------------------------------------------------------------------
# Regla 5 · No mezclar unidades / Regla 6 · encuesta solo como %
# ---------------------------------------------------------------------------
def test_segmentacion_proporciones(outputs):
    seg = outputs["survey_segment.parquet"].dropna(subset=["registros"])
    suma = seg.groupby("fecha")["participacion_registros"].sum()
    assert np.allclose(suma, 1.0)


def test_tasa_transferencia_en_rango(outputs):
    tr = outputs["survey_transfer_rate.parquet"]
    assert (tr["registros_total"] > 0).all(), "El denominador nunca puede ser 0."
    assert tr["tasa_transferencia"].between(0, 1).all()
    assert (tr["ic_inf"] <= tr["tasa_registros"] + 1e-12).all()
    assert (tr["tasa_registros"] <= tr["ic_sup"] + 1e-12).all()


def test_tasa_no_extrapola_a_absolutos(outputs):
    """La tasa es muestral: no existe ninguna columna de visitantes 'estimados' absolutos."""
    tr = outputs["survey_transfer_rate.parquet"]
    assert not any("estimad" in c for c in tr.columns)


def test_peso_en_izabal_suma_uno(outputs):
    tr = outputs["survey_transfer_rate.parquet"]
    suma = tr.groupby("anio")["peso_en_izabal"].sum(min_count=1)
    assert np.allclose(suma.dropna(), 1.0)


# ---------------------------------------------------------------------------
# Mapeo encuesta <-> migración
# ---------------------------------------------------------------------------
def test_mapeo_fronteras_1a1(outputs):
    mig = outputs["migration_monthly.parquet"]
    assert len(SURVEY_BORDER_MAP) == 11
    assert len(set(SURVEY_BORDER_MAP.values())) == 11
    assert set(SURVEY_BORDER_MAP.values()).issubset(set(mig["Frontera"]))


def test_cruce_frontera_usa_solo_fronteras_mapeadas(outputs):
    bm = outputs["survey_border_migration.parquet"]
    assert set(bm["frontera_migracion"]).issubset(set(SURVEY_BORDER_MAP.values()))
    assert (bm["registros_izabal"] <= bm["registros_total"]).all()


# ---------------------------------------------------------------------------
# Ventana coincidente y perfil estacional
# ---------------------------------------------------------------------------
def test_ventana_coincidente(outputs):
    ova = outputs["occupancy_vs_affluence.parquet"]
    ventana = ova[ova["en_ventana"]]
    assert len(ventana) == 4
    assert ventana["fecha"].min() == pd.Timestamp(VENTANA_COINCIDENTE[0])
    assert ventana["ocupacion"].between(0, 1).all()
    assert ventana["registros_encuesta"].notna().all()


def test_indice_estacional_promedia_uno(outputs):
    si = outputs["migration_seasonal_index.parquet"]
    completos = si.groupby(["Frontera", "tipo_flujo"]).filter(lambda g: len(g) == 12)
    medias = completos.groupby(["Frontera", "tipo_flujo"])["indice"].mean()
    assert np.allclose(medias, 1.0, atol=0.05)


# ---------------------------------------------------------------------------
# Calidad de datos
# ---------------------------------------------------------------------------
def test_calidad_documenta_huecos(outputs):
    dq = outputs["data_quality.parquet"]
    huecos = dq[dq["fuente"].eq("hueco")]
    assert huecos["huecos_visitantes"].str.contains("2025-01").any()
    assert huecos["huecos_visitantes"].str.contains("2022").any()
    assert dq["segmento"].str.contains("Capacidad instalada").any()


def test_calidad_encuesta_en_meses(outputs):
    """meses_con_datos de la encuesta debe contar meses, no días."""
    dq = outputs["data_quality.parquet"]
    iz = dq[dq["fuente"].eq("encuesta") & dq["segmento"].eq("Izabal/Caribe")].iloc[0]
    assert iz["meses_con_datos"] <= 12 * 6
