"""Paleta validada del observatorio y reglas de uso (PLAN §6).

Contraste verificado en OKLab bajo el peor caso de daltonismo; el núcleo
categórico de 5 colores tiene dE mínimo = 0.113 (umbral 0.10).
"""

# Roles semánticos
PALETA = {
    "primario": "#0E7C86",     # turquesa Caribe · serie principal · AA texto (4.95)
    "secundario": "#D97706",   # arena · relleno/gráfico (3.19, NO usar como texto)
    "acento": "#3FA8B8",       # turquesa claro · relleno/gráfico (2.80, NO texto)
    "alerta": "#C0392B",       # coral · AA texto (5.44)
    "info": "#1B4F8F",         # azul profundo · AA texto (8.20)
    "estimacion": "#7D3C98",   # violeta · EXCLUSIVO de estimaciones (7.07)
    "neutro": "#6C757D",       # gris · series sin foco (4.69)
    "texto": "#1F2933",        # texto general (14.76)
}

# Núcleo categórico: máximo 5 series simultáneas
CATEGORICA = [
    PALETA["primario"],
    PALETA["secundario"],
    PALETA["acento"],
    PALETA["alerta"],
    PALETA["info"],
]

# Encoding redundante (forma además de color): un patrón de línea por serie
PATRONES_LINEA = ["solid", "dash", "dot", "dashdot", "longdash"]

# Estimaciones: violeta + línea discontinua + marcador vacío + etiqueta
ESTIMACION = {
    "color": PALETA["estimacion"],
    "dash": "dash",
    "marker_symbol": "circle-open",
    "etiqueta": "Estimación",
}

# Series sin foco
OPACIDAD_SIN_FOCO = 0.35

# ---------------------------------------------------------------------------
# Ritmo de presentación (ver app/components/layout.py)
# ---------------------------------------------------------------------------
# Alturas estándar de gráfico. Mantenerlas iguales hace que dos gráficos
# quepan en un mismo plano de pantalla y que la página tenga ritmo.
ALTURA = 300
ALTURA_GRANDE = 380
ALTURA_ALTA = 440

# Máximo de tarjetas KPI visibles a la vez por módulo.
MAX_KPIS = 4

# Tipografía del bloque de texto destacado (conclusión de módulo, insight).
TAMANO_AFIRMACION = "1.02rem"
TAMANO_INSIGHT = "0.93rem"

# Fondos suaves para los bloques con barra de color.
FONDO_PRIMARIO = "rgba(14,124,134,0.07)"
FONDO_NEUTRO = "rgba(0,0,0,0.035)"
FONDO_ALERTA = "rgba(192,57,43,0.06)"

# Grid y ejes
GRID = "#E5E7EB"
FONDO_GRAFICO = "rgba(0,0,0,0)"

# Etiquetas de tipo de dato (badges)
TIPO_DATO = {
    "observado": "Observado",
    "muestral": "Muestral",
    "estimacion": "Estimación",
}

REGLAS = [
    "Separar por forma, no solo por tono: estimaciones = violeta + discontinua + marcador vacío + etiqueta.",
    "El violeta de estimación nunca comparte escala categórica con datos observados.",
    "Series múltiples: color + patrón de línea distinto (legible en B/N y daltonismo).",
    "Color categórico solo para la serie en foco; el resto en neutro con opacidad 0.35.",
    "Máximo 5 series simultáneas; si hay más, small multiples o selector.",
    "Contraste: texto >= 4.5:1, elementos gráficos >= 3:1 (WCAG 2.1).",
]
