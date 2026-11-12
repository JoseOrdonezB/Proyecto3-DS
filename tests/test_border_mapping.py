"""Módulo 4 · Mapeo de fronteras entre la encuesta y la base de migración.

El cruce encuesta ↔ migración es el que permite medir el embudo de transferencia
del destino (PLAN §2.4 y §4). Si el mapeo 1:1 se rompe, el embudo deja de ser
calculable, así que estas pruebas fijan el contrato.
"""

import pandas as pd
import pytest

from src.config import ISABAL_FEEDER_BORDERS, SURVEY_BORDER_MAP
from src.etl.load import load_migration, load_survey
from src.utils.helpers import mapa_frontera


def test_fronteras_alimentadoras_son_9_y_estan_en_el_mapeo():
    """Las alimentadoras de Izabal son 9 y todas tienen equivalente en migración."""
    assert len(ISABAL_FEEDER_BORDERS) == 9
    assert set(ISABAL_FEEDER_BORDERS) <= set(SURVEY_BORDER_MAP.values())


def test_mapeo_1_a_1_contra_la_base_oficial():
    """Cada nombre del mapeo existe en la base oficial, con prefijo numérico."""
    migracion = load_migration()
    fronteras_oficiales = set(migracion["Frontera"].unique())
    for encuesta, oficial in SURVEY_BORDER_MAP.items():
        assert oficial in fronteras_oficiales, f"'{oficial}' no existe en la base de migración."
        assert oficial.split(" ", 1)[1] == encuesta, (
            f"El prefijo numérico de '{oficial}' no corresponde a '{encuesta}'."
        )


def test_mapeo_de_la_encuesta_real_es_total():
    """Ninguna frontera de la encuesta con destino Izabal queda sin equivalente."""
    survey = load_survey()
    izabal = survey[survey["nuevo_destino"].eq("Izabal/Caribe")]
    fronteras = set(izabal["frontera_nombre"].dropna().unique())
    sin_mapeo = [f for f in fronteras if mapa_frontera(f) is None]
    assert not sin_mapeo, f"Fronteras de Izabal sin equivalente en migración: {sin_mapeo}"


def test_mapeo_ignora_tildes_y_mayusculas():
    assert mapa_frontera("el florido") == "12 El Florido"
    assert mapa_frontera("LA ERMITA (NUEVA ANGUIATÚ)") == "10 La Ermita (Nueva Anguiatú)"
    assert mapa_frontera("San Cristobal") == "09 San Cristóbal"


def test_mapeo_devuelve_none_si_no_existe():
    assert mapa_frontera("Frontera Inventada") is None


def test_cruce_encuesta_migracion_cubre_las_9_alimentadoras(outputs):
    """El cruce debe incluir las 9 fronteras alimentadoras con registros."""
    cruce = outputs["survey_border_migration.parquet"]
    presentes = set(cruce["frontera_migracion"].dropna().unique())
    assert set(ISABAL_FEEDER_BORDERS) <= presentes


def test_meses_solape_cero_en_fronteras_maritimes(outputs):
    """El hallazgo central del Módulo 4: el embudo marítimo no es medible.

    Visitantes y tránsito nunca coexisten en un mismo mes en Puerto Barrios,
    Livingston ni Santo Tomás. Si algún día lo hacen, esta prueba falla y
    avisa de que el Módulo 4 debe actualizarse.
    """
    perfil = outputs["maritime_flow_profile.parquet"]
    maritimas = perfil[perfil["es_destino_maritimo"]]
    assert len(maritimas) == 3
    assert (maritimas["meses_solape"] == 0).all(), (
        "Las fronteras marítimas Han pasado a tener visitantes y tránsito en el mismo mes: "
        "el embudo marítimo ya sería calculable y el Módulo 4 debe actualizarse."
    )
    assert not maritimas["embudo_medible"].any()


def test_fronteras_alimentadoras_si_tienen_solape(outputs):
    """Contraste: las terrestres alimentadoras sí son medibles."""
    perfil = outputs["maritime_flow_profile.parquet"]
    alimentadoras = perfil[perfil["es_alimentadora"]]
    assert len(alimentadoras) == 9
    assert alimentadoras["meses_solape"].gt(0).all()
    assert alimentadoras["embudo_medible"].all()
