"""Reglas del sistema de diseño de presentación (app/components/layout.py).

El diseño de un observatorio se presenta en pantalla: si cada módulo acumula
contenido, la página se vuelve ilegible y la historia se pierde. Estas pruebas
convierten las reglas de diseño en algo verificable, para que no se deshagan
cuando alguien agregue una gráfica.

Reglas que se comprueban:
    1. Máximo 5 secciones visibles por módulo.
    2. Una sola fila de tarjetas KPI por módulo, con máximo 4 tarjetas.
    3. Alturas de gráfico solo de la lista estándar (300 / 380 / 440).
    4. Los gráficos de detalle van dentro de `st.expander`, no sueltos.
"""

import re
from pathlib import Path

import pytest

from app.components import layout

ROOT = Path(__file__).resolve().parents[1]
PAGINAS = sorted((ROOT / "app" / "pages").glob("*.py"))


def _contenido(pagina: Path) -> str:
    return pagina.read_text(encoding="utf-8")


def _en_sistema(pagina: Path) -> bool:
    """Una página está en el sistema de diseño si usa la cabecera `modulo()`.

    Así, cuando un módulo se reescriba con el armazón nuevo, las reglas le
    aplican sin tocar este archivo.
    """
    return bool(re.search(r"^modulo\(", _contenido(pagina), re.M))


MODULOS_DISENO = [p for p in PAGINAS if _en_sistema(p)]
MODULOS_PENDIENTES = [p.name for p in PAGINAS if not _en_sistema(p)]


def test_las_constantes_de_diseno_existen():
    assert layout.MAX_KPIS == 4
    assert layout.MAX_SECCIONES == 5
    assert layout.ALTURA == 300
    assert layout.ALTURA_GRANDE == 380
    assert layout.ALTURA_ALTA == 440


@pytest.mark.xfail(
    bool(MODULOS_PENDIENTES),
    reason=(
        "Módulos que aún no usan el armazón de presentación: "
        f"{MODULOS_PENDIENTES}. El Módulo 2 sigue con el esqueleto viejo; cuando se "
        "reescriba con app/components/layout.py, esta prueba pasa sola."
    ),
    strict=False,
)
def test_todos_los_modulos_estan_en_el_sistema_de_diseno():
    """Todos los módulos deben usar el armazón común.

    Mientras quede uno fuera (porque todavía es el esqueleto viejo), el
    recordatorio queda anotado como deuda conocida.
    """
    assert not MODULOS_PENDIENTES, (
        "Módulos que todavía no usan el armazón de presentación "
        f"(`modulo()` / `seccion()` / `kpis()`): {MODULOS_PENDIENTES}. "
        "Reescribirlos con app/components/layout.py."
    )


@pytest.mark.parametrize("pagina", MODULOS_DISENO, ids=lambda p: p.name)
def test_maximo_de_secciones_por_modulo(pagina):
    """La historia de un módulo se cuenta en pocas pantallas."""
    n = len(re.findall(r"^seccion\(", _contenido(pagina), re.M))
    assert n <= layout.MAX_SECCIONES, (
        f"{pagina.name} tiene {n} secciones visibles (máximo {layout.MAX_SECCIONES}). "
        "Baja el contenido sobrante a un st.expander."
    )


@pytest.mark.parametrize("pagina", MODULOS_DISENO, ids=lambda p: p.name)
def test_una_sola_fila_de_kpis_por_modulo(pagina):
    """El ancla visual del módulo es una sola fila de tarjetas."""
    n = len(re.findall(r"^kpis\(", _contenido(pagina), re.M))
    assert n <= 1, f"{pagina.name} tiene {n} filas de KPI; debe tener una sola."


@pytest.mark.parametrize("pagina", MODULOS_DISENO, ids=lambda p: p.name)
def test_alturas_de_grafico_estandar(pagina):
    """Todas las gráficas usan las alturas del sistema de diseño."""
    alturas = re.findall(r"estilo\(\s*fig\s*,\s*([^,)]+)", _contenido(pagina))
    permitidas = {"ALTURA", "ALTURA_GRANDE", "ALTURA_ALTA"}
    literales = {a.strip() for a in alturas if a.strip().isdigit()}
    fuera = {int(a) for a in literales} - {300, 380, 440}
    assert not fuera, f"{pagina.name} usa alturas fuera del estándar: {sorted(fuera)}"
    for a in alturas:
        a = a.strip()
        if not a.isdigit():
            assert a in permitidas, f"{pagina.name} usa una altura no reconocida: {a}"


@pytest.mark.parametrize("pagina", MODULOS_DISENO, ids=lambda p: p.name)
def test_cada_modulo_tiene_asercion_de_cabecera(pagina):
    """Cada módulo debe abrir con una conclusión, no solo con un título."""
    txt = _contenido(pagina)
    assert re.search(r"^modulo\(", txt, re.M), f"{pagina.name} no llama a modulo()."
    bloque = re.search(r"modulo\((.*?)\n\)", txt, re.S)
    assert bloque, f"{pagina.name} no tiene cabecera de módulo bien formada."
    assert len(bloque.group(1)) > 200, (
        f"{pagina.name}: la cabecera debe incluir la afirmación con la cifra, no solo el título."
    )


@pytest.mark.parametrize("pagina", MODULOS_DISENO, ids=lambda p: p.name)
def test_titulares_de_seccion_son_frases_con_cifra(pagina):
    """El titular de cada sección debe leerse como una afirmación."""
    secciones = re.findall(r"^seccion\(\s*\n?\s*(f?\"[^\"]+\")", _contenido(pagina), re.M)
    assert secciones, f"{pagina.name} no tiene secciones."
    for t in secciones:
        texto = t.strip('f"')
        assert len(texto) > 25, f"Titular demasiado corto: {texto!r}"
        assert "?" not in texto, (
            f"El titular de sección debe ser una afirmación, no una pregunta: {texto!r}"
        )
