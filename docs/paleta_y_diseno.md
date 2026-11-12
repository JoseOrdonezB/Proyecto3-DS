# Paleta de color y teoría del color

## Observatorio de Inteligencia Turística — Grupo 5

Este documento sustenta la decisión de paleta exigida por la guía ("diseño profesional
siguiendo una paleta de color documentada y teniendo en cuenta la teoría del color
estudiada", 40 % de la nota). La paleta vive en código en
[`app/components/theme.py`](../app/components/theme.py) — este documento explica **por
qué** es esa y no otra.

---

## 1. Principios de teoría del color aplicados

Un dashboard de observatorio se lee en pantalla, a menudo proyectado, y por personas con
distintos tipos de percepción del color. Tres principios gobiernan la elección:

1. **Contraste perceptual, no solo visual.** Dos colores pueden verse "distintos" en una
   pantalla calibrada y colapsar bajo daltonismo o en una proyección de mal contraste. Se
   midió el contraste en **espacio OKLab** (perceptualmente uniforme, a diferencia de RGB
   o HSL) y bajo el **peor caso de daltonismo** (protanopía, deuteranopía, tritanopía
   simuladas), no solo en visión tricromática normal.
2. **Encoding redundante.** El color nunca es la única señal: una estimación se marca
   también con línea discontinua y marcador vacío; una serie en foco se distingue también
   por opacidad. Así la información sobrevive a una impresión en blanco y negro o a una
   proyección con mal contraste, además de a cualquier forma de daltonismo.
3. **Jerarquía, no decoración.** Los colores tienen **roles fijos** (primario, alerta,
   estimación, neutro…), no se eligen por gusto gráfico por gráfico. Un mismo rol
   significa lo mismo en los 4 módulos.

---

## 2. Problema medido en la paleta original

Antes de la paleta validada, `app/components/kpis.py` usaba estos colores. Se midió el
contraste perceptual (ΔE en OKLab) bajo el peor caso de daltonismo:

| Par de colores | ΔE (peor caso) | Veredicto |
|---|---|---|
| primario `#0E7C86` vs. acento `#5B8E7D` | **0.052** | casi indistinguibles |
| primario vs. alerta `#C0392B` | 0.045 | casi indistinguibles |
| primario vs. estimación `#9B59B6` | 0.070 | en el límite |
| estimación vs. info `#2E5EAA` | **0.019** | colapsan bajo deuteranopía |

Además, `#F4A259` (arena) tenía un contraste de **2.07** contra blanco: no cumple **AA**
(mínimo 4.5:1) para texto. El umbral de separación usado en este proyecto es **ΔE ≥ 0.10**
entre cualquier par de colores que puedan aparecer juntos en una misma vista.

---

## 3. Paleta final (validada)

| Rol | Hex | L (OKLab) | Contraste vs. blanco | Uso |
|---|---|---|---|---|
| `primario` (turquesa Caribe) | `#0E7C86` | 0.536 | 4.95 | AA texto; serie principal de cada módulo |
| `secundario` (arena/ámbar) | `#D97706` | 0.666 | 3.19 | relleno de gráfico (no usar como texto) |
| `acento` (turquesa claro) | `#3FA8B8` | 0.678 | 2.80 | relleno de gráfico (no usar como texto) |
| `alerta` (coral) | `#C0392B` | 0.543 | 5.44 | AA texto; advertencias de método |
| `info` (azul profundo) | `#1B4F8F` | 0.429 | 8.20 | AA texto; series "Observado" absolutas |
| `estimación` (violeta) | `#7D3C98` | 0.481 | 7.07 | AA texto; **exclusivo** de estimaciones |
| `neutro` | `#6C757D` | 0.558 | 4.69 | series sin foco, texto secundario |
| `texto` | `#1F2933` | 0.276 | 14.76 | texto general |

Definida en código en `app/components/theme.py::PALETA`.

### Núcleo categórico (máximo 5 series simultáneas)

`#0E7C86` · `#D97706` · `#3FA8B8` · `#C0392B` · `#1B4F8F` → **ΔE mínimo = 0.113** entre
cualquier par, bajo el peor caso de daltonismo (por encima del umbral 0.10).

### Encoding redundante

Para series múltiples, cada una lleva además un **patrón de línea** distinto, definido en
`PATRONES_LINEA = ["solid", "dash", "dot", "dashdot", "longdash"]`: la serie se reconoce
por forma además de por color.

---

## 4. Reglas de uso (aplicadas en código, no solo en este documento)

Las seis reglas de `app/components/theme.py::REGLAS`, con su razón de ser:

1. **Separar por forma, no solo por tono.** Toda estimación es violeta + línea
   discontinua + marcador vacío (`circle-open`) + etiqueta "Estimación"
   (`ESTIMACION` en `theme.py`). Nunca se confía solo en el color para distinguir un dato
   observado de uno estimado — la regla metodológica 1 ("la ausencia de dato no es
   cero") se vuelve ilegible si la estimación se ve igual que lo observado.
2. **El violeta de estimación nunca comparte escala categórica con datos observados.**
   Si una gráfica usa violeta para una categoría observada, un lector lo lee como
   "estimado" por reflejo. El rol es exclusivo.
3. **Encoding redundante en series múltiples:** color + patrón de línea distinto,
   legible en blanco y negro y bajo cualquier tipo de daltonismo.
4. **Jerarquía de luminosidad:** el color categórico se reserva para la serie en foco
   (p. ej. la frontera o el mercado seleccionado); el resto baja a `#6C757D` con opacidad
   0.35 (`OPACIDAD_SIN_FOCO`). Implementado en `app/components/charts.py::colores_foco`,
   usado en las 4 páginas para los selectores enlazados.
5. **Máximo 5 series simultáneas.** Si hay más categorías, se usan *small multiples*
   (ver el patrón de tarjetas por nodo en el Módulo 4) o un selector que filtra
   (Módulos 1, 3 y 4).
6. **Contraste:** texto ≥ 4.5:1 (WCAG 2.1 AA), elementos gráficos ≥ 3:1. Verificado en la
   tabla de la sección 3 para cada rol usado como texto.

---

## 5. Badges de tipo de dato

Cada sección y cada gráfico declara de qué naturaleza es el dato que muestra, con un
badge de color fijo (`app/components/charts.py::BADGE_COLOR`):

| Badge | Color | Significado |
|---|---|---|
| **Observado** | `info` (`#1B4F8F`) | conteo absoluto (migración, ocupación reportada) |
| **Muestral** | `primario` (`#0E7C86`) | encuesta sin factor de expansión; se lee como proporción |
| **Estimación** | `estimación` (`#7D3C98`) | imputación o pronóstico, nunca un dato observado |

Esto evita el error más fácil de cometer en un observatorio turístico: mezclar una cifra
muestral con una absoluta, o presentar una estimación como si fuera un hecho (regla
metodológica 6 y 1, respectivamente).

---

## 6. Ritmo de presentación (apoya la legibilidad, no solo el color)

La paleta se usa dentro de un armazón de presentación fijo (`app/components/layout.py`),
verificado con pruebas automáticas (`tests/test_diseno.py`):

- Máximo **5 secciones** visibles por módulo.
- Una sola fila de **hasta 4 tarjetas KPI**, con borde superior del color de su rol.
- Alturas de gráfico únicamente de **300 / 380 / 440 px** (`ALTURA`, `ALTURA_GRANDE`,
  `ALTURA_ALTA`), para que dos gráficos siempre quepan en el mismo plano de pantalla.
- El título de cada sección y de cada gráfico es una **afirmación con la cifra dentro**,
  nunca una pregunta ni solo un tema.

Esto no es teoría del color, pero es la razón por la que la paleta —bien elegida— sigue
siendo legible: un color correcto en una página saturada de contenido deja de leerse.

---

*Paleta y reglas verificadas en código: `app/components/theme.py` (definición),
`app/components/charts.py` (aplicación en gráficos) y `app/components/layout.py`
(armazón de presentación). Si el código cambia, este documento debe actualizarse para
seguir siendo la fuente de verdad del diseño.*
