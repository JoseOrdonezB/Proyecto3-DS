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

# Mapeo 1:1 encuesta (frontera_nombre) -> migración (Frontera). Ver PLAN §2.4.
SURVEY_BORDER_MAP = {
    "El Florido": "12 El Florido",
    "La Ermita (Nueva Anguiatú)": "10 La Ermita (Nueva Anguiatú)",
    "San Cristóbal": "09 San Cristóbal",
    "Melchor de Mencos": "20 Melchor de Mencos",
    "El Carmen": "15 El Carmen",
    "La Aurora": "01 La Aurora",
    "Valle Nuevo": "07 Valle Nuevo",
    "La Mesilla": "16 La Mesilla",
    "Pedro de Alvarado": "08 Pedro de Alvarado",
    "Agua Caliente": "11 Agua Caliente",
    "Tecún Umán": "14 Tecún Umán",
}

# Las 9 fronteras "alimentadoras" de Izabal (PLAN §2.4 / §3.2, modelo M3).
# Son las fronteras que efectivamente registran visitantes con destino
# Izabal/Caribe en la BD complementaria (verificado sobre el subconjunto).
# Las 2 restantes del mapeo (Agua Caliente, Tecún Umán) aparecen en la encuesta
# general pero NO en el subconjunto Izabal/Caribe: no alimentan el destino.
# Todas tienen serie de visitantes continua 2009-2026 (a diferencia de las
# fronteras marítimas del destino, que se apagan en 2016).
ISABAL_FEEDER_BORDERS = [
    "12 El Florido",
    "10 La Ermita (Nueva Anguiatú)",
    "09 San Cristóbal",
    "20 Melchor de Mencos",
    "15 El Carmen",
    "01 La Aurora",
    "07 Valle Nuevo",
    "16 La Mesilla",
    "08 Pedro de Alvarado",
]

# Ventana coincidente del Módulo 3 (afluencia vs ocupación). Ver PLAN §8 (C).
VENTANA_COINCIDENTE = ("2025-09-01", "2025-12-01")

# Nacionalidad de la encuesta -> 'País' de la base de migración (para enlazar
# la selección de mercado entre ambas fuentes). Solo los que difieren de nombre;
# los demás se buscan tal cual.
SURVEY_NATIONALITY_MAP = {
    "EE. UU.": "Estados Unidos de América",
    "Reino Unido": "Reino Unido de Gran Bretaña e Irlanda del Norte",
    "Rusia": "Federación de Rusia",
}

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
