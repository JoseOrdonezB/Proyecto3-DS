"""Fixtures compartidas de las pruebas."""

import pytest

from src.etl.pipeline import run


@pytest.fixture(scope="session")
def outputs():
    """Ejecuta el pipeline una sola vez para todas las pruebas."""
    return run(save=False)
