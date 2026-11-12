"""Prueba de humo del dashboard: cada página debe renderizar sin errores.

Un error de runtime en una página de Streamlit no se ve hasta que alguien la
abre en el navegador, y en una entrega eso puede significar un módulo vacío.
Estas pruebas ejecutan cada página con el runner de Streamlit y fallan si
alguna lanza una excepción.

Además ejercitan los selectores, porque una página puede renderizar bien en su
estado inicial y romperse al filtrar (es el error más común al encadenar
gráficas).
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

# AppTest resuelve las rutas relativas contra el archivo de test, no contra la
# raíz del proyecto: hay que fijarlas de forma explícita.
ROOT = Path(__file__).resolve().parents[1]

PAGINAS = [
    "app/app.py",
    "app/pages/1_monitor_demanda.py",
    "app/pages/2_dinamica_temporal.py",
    "app/pages/3_oferta_hotelera.py",
    "app/pages/4_conectividad_fluvial.py",
]


def _cargar(ruta: str) -> AppTest:
    at = AppTest.from_file(str(ROOT / ruta), default_timeout=180)
    at.run()
    return at


@pytest.mark.parametrize("ruta", PAGINAS)
def test_pagina_renderiza_sin_errores(ruta):
    at = _cargar(ruta)
    assert not at.exception, f"{ruta} falló: {[str(e.value) for e in at.exception]}"


def test_modulo_4_filtra_por_frontera():
    """El selector enlazado del Módulo 4 debe re-renderizar sin romperse."""
    at = _cargar("app/pages/4_conectividad_fluvial.py")
    assert not at.exception
    selectores = [s for s in at.selectbox if s.label.startswith("Frontera de entrada")]
    assert selectores, "El Módulo 4 debe tener el selector de frontera."
    sb = selectores[0]
    for valor in [o for o in sb.options if o != "Todas"][:3]:
        sb.set_value(valor).run()
        assert not at.exception, f"Error al filtrar por '{valor}': {[str(e.value) for e in at.exception]}"


def test_modulo_4_filtra_por_periodo():
    at = _cargar("app/pages/4_conectividad_fluvial.py")
    assert not at.exception
    selectores = [s for s in at.selectbox if s.label.startswith("Periodo")]
    assert selectores, "El Módulo 4 debe tener el selector de periodo."
    sb = selectores[0]
    for valor in sb.options[:3]:
        sb.set_value(valor).run()
        assert not at.exception, f"Error al filtrar por '{valor}': {[str(e.value) for e in at.exception]}"


@pytest.mark.parametrize("ruta", ["app/pages/1_monitor_demanda.py", "app/pages/3_oferta_hotelera.py"])
def test_selectores_de_los_modulos_no_rompen_la_pagina(ruta):
    """Cada filtro debe dejar la página renderizable."""
    at = _cargar(ruta)
    assert not at.exception
    for sb in at.selectbox:
        if len(sb.options) < 2:
            continue
        sb.set_value(sb.options[1]).run()
        assert not at.exception, f"{ruta} con '{sb.label}': {[str(e.value) for e in at.exception]}"
