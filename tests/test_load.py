"""Pruebas de carga de las tres fuentes de datos."""

from src.etl.load import load_migration, load_occupancy, load_survey


def test_migration_schema():
    df = load_migration()
    assert len(df) > 100_000
    assert "Viajero" in df.columns
    assert (df["Viajero"] >= 0).all()


def test_occupancy_schema():
    df = load_occupancy()
    assert {"anio", "mes", "departamento", "indice_ocupacion"}.issubset(df.columns)
    assert df["indice_ocupacion"].between(0, 1).all()


def test_survey_schema():
    df = load_survey()
    assert len(df) > 100_000
    assert "nuevo_destino" in df.columns
    assert "fecha" in df.columns
