"""Configuración central del Observatorio de Inteligencia Turística.

Agrupación 5: Río Dulce y Livingston, Izabal.
Reto especializado: Conectividad Fluvial y Embudo de Transferencia.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

MIGRATION_FILE = DATA_RAW / "Base_Migracion_2009-2026jun.xlsx"
OCCUPANCY_FILE = DATA_RAW / "indice_ocupacion_mensual_2023_2025_1.csv"
SURVEY_FILE = DATA_RAW / "BD_COMPLEMENTARIA"  # parquet sin extensión

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------
# Fronteras marítimas del destino (Izabal / Caribe)
IZABAL_BORDERS = [
    "05 Puerto Barrios",
    "06 Livingston",
    "04 Santo Tomás de Castilla",
]

# Corredor completo: destino + puntos de conexión del embudo de transferencia
CORRIDOR_BORDERS = IZABAL_BORDERS + [
    "03 Puerto Quetzal",
    "02 Mundo Maya",
]

# Tipos de viajero que SÍ son visitantes.
# Regla estricta: "Viajero" (tránsito/fronterizo) y "Cruceristas" no cuentan.
VISITOR_TYPES = ["Turista", "Excursionista"]
NON_VISITOR_TYPES = ["Viajero", "Cruceristas"]

# Cruzamientos de cruceros (fuente externa desde 2023)
CRUISE_BORDER = "Cruceros"

DESTINATION_DEPT = "Izabal"
DESTINATION_REGION = "Izabal/Caribe"  # etiqueta usada en la BD complementaria

# ---------------------------------------------------------------------------
# Columnas esperadas por fuente (validación de esquema)
# ---------------------------------------------------------------------------
MIGRATION_COLUMNS = [
    "Año",
    "Mes cod",
    "Mes",
    "Vía",
    "Frontera",
    "País",
    "Región",
    "Región dos",
    "Regiones OMT",
    "MCEO",
    "Agrupación Residencia",
    "Tipo de Viajero",
    "Viajero",
]

OCCUPANCY_COLUMNS = ["anio", "mes", "departamento", "indice_ocupacion"]

SURVEY_COLUMNS = [
    "fecha",
    "destino",
    "nuevo_destino",
    "estadia",
    "noches",
    "total_visitantes",
    "validacion",
    "frontera_nombre",
    "frontera_tipo",
    "residencia",
    "nacionalidad",
    "hospedaje",
    "tipo_transporte",
    "id_unico",
    "BD",
    "personas1",
]
