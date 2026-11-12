"""Pruebas de las transformaciones del ETL."""


def test_visitor_definition(outputs):
    """El destino solo debe contener Turista y Excursionista."""
    dm = outputs["destination_monthly.parquet"]
    assert set(dm["Tipo de Viajero"].unique()).issubset({"Turista", "Excursionista"})


# Columnas que por definición pueden ser negativas (variación % frente a una base)
COLUMNAS_CON_SIGNO = {"lift_registros_pct", "lift_visitantes_pct"}


def test_no_negative_values(outputs):
    for nombre, df in outputs.items():
        numericos = df.select_dtypes("number").drop(columns=list(COLUMNAS_CON_SIGNO), errors="ignore")
        assert (numericos.fillna(0) >= 0).all().all(), nombre


def test_occupancy_range(outputs):
    occ = outputs["occupancy_monthly.parquet"]
    assert occ["indice_ocupacion"].dropna().between(0, 1).all()


def test_weighted_stay_formula(outputs):
    """La estadía media ponderada = días-persona / visitantes pernocta."""
    stay = outputs["survey_stay_izabal.parquet"]
    valores = dict(zip(stay["indicador"], stay["valor"]))
    assert valores["estadia_media_ponderada"] > 0
    esperado = valores["dias_persona"] / valores["visitantes_pernocta"]
    assert abs(valores["estadia_media_ponderada"] - esperado) < 1e-6


def test_corridor_share_range(outputs):
    cs = outputs["corridor_share.parquet"]
    assert cs["participacion"].dropna().between(0, 1).all()


def test_data_quality_present(outputs):
    dq = outputs["data_quality.parquet"]
    assert "05 Puerto Barrios" in set(dq["segmento"])
    assert "Izabal/Caribe" in set(dq["segmento"])
