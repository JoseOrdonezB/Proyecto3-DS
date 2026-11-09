"""Helpers de normalización y transformación de uso compartido."""

# ---------------------------------------------------------------------------
# Normalización de subdestinos dentro de Izabal / Caribe
# ---------------------------------------------------------------------------
# El campo 'destino' de la BD complementaria tiene múltiples variantes
# (typos, mayúsculas, nombres compuestos). Se mapean a nombres canónicos.
SUBDESTINO_KEYWORDS = [
    ("rio dulce", "Río Dulce"),
    ("río dulce", "Río Dulce"),
    ("puerto barrios", "Puerto Barrios"),
    ("livingston", "Livingston"),
    ("quirigua", "Quiriguá"),
    ("morales", "Morales"),
    ("entre rios", "Entre Ríos"),
    ("entre ríos", "Entre Ríos"),
    ("santo tomas", "Santo Tomás de Castilla"),
    ("santo tomás", "Santo Tomás de Castilla"),
    ("amates", "Los Amates"),
    ("el estor", "El Estor"),
    ("amatique", "Amatique"),
    ("castillo", "Castillo de San Felipe"),
    ("bananeras", "Bananeras"),
    ("mariscos", "Mariscos"),
    ("tenedores", "Tenedores"),
    ("machaca", "Machaca"),
    ("izabal", "Izabal (genérico)"),
]


def normalize_subdestino(value) -> str:
    """Mapea el valor libre de 'destino' a un subdestino canónico."""
    s = str(value).strip().lower()
    if not s or s in ("nan", "none", "no especificado"):
        return "No especificado"
    for keyword, canonical in SUBDESTINO_KEYWORDS:
        if keyword in s:
            return canonical
    return "Otro"


def safe_div(numerador, denominador, default=0.0):
    """División segura que evita errores con denominadores cero."""
    if denominador in (0, 0.0) or denominador is None:
        return default
    return numerador / denominador
