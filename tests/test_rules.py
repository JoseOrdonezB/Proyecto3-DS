"""Pruebas de las reglas metodológicas estrictas del proyecto."""


def test_missing_not_zero(outputs):
    """El hueco 2017-2022 debe conservarse (sin datos), no rellenarse con cero."""
    dm = outputs["destination_monthly.parquet"]
    hueco = dm[(dm["fecha"] >= "2017-01-01") & (dm["fecha"] <= "2022-12-01")]
    assert hueco.empty, "El período sin cobertura no debe aparecer como cero."


def test_no_sum_subdestinos(outputs):
    """No debe existir una fila de total que sume subdestinos."""
    sub = outputs["survey_subdestino.parquet"]
    assert "Total" not in set(sub["subdestino"])


def test_weighted_not_mean(outputs):
    """La estadía media no es el promedio de 'noches', es ponderada."""
    stay = outputs["survey_stay_izabal.parquet"]
    valores = dict(zip(stay["indicador"], stay["valor"]))
    assert abs(
        valores["estadia_media_ponderada"]
        - valores["dias_persona"] / valores["visitantes_pernocta"]
    ) < 1e-6


def test_survey_is_sample_only(outputs):
    """La encuesta no debe usarse como total absoluto (sin factor de expansión)."""
    stay = outputs["survey_stay.parquet"]
    valores = dict(zip(stay["indicador"], stay["valor"]))
    # Los visitantes de la encuesta son una fracción de los absolutos
    assert valores["visitantes_pernocta"] < 1_000_000
