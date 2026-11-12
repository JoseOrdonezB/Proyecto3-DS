# Plan de Implementación — Observatorio de Inteligencia Turística
## Grupo 5 · Río Dulce y Livingston, Izabal

**Curso:** CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II 2026
**Reto especializado del grupo:** Conectividad Fluvial y Embudo de Transferencia
**Documento:** plan maestro compartido por los 4 integrantes del grupo
**Estado:** listo para ejecutar por fases

---

## 📌 Cómo usar este documento

Este plan es la **fuente única de verdad** del proyecto. Fue construido a partir de
análisis reales sobre las tres fuentes de datos, no de supuestos.

**Para los compañeros:** cada uno toma un módulo (ver §8) y puede handing-off a su
propio agente de IA usando la sección correspondiente de este documento como
instrucción directa. Cada sección indica qué archivos crear, qué funciones
implementar y con qué criterio de aceptación.

**Para los agentes:** las fases están ordenadas por dependencia. El **Módulo 2
(pronóstico) es el camino crítico** y debe arrancar primero. Los módulos 1, 3 y 4
son independientes entre sí y pueden developerse en paralelo.

> ⚠️ **No modificar los datos.** La carpeta `data/` es institucional y está en
> `.gitignore`. Ningún agente debe subir microdatos, cambiar `.gitignore` para
> incluirlos, ni publicar el repositorio.

> 📐 **Reglas metodológicas estrictas** (de la guía oficial, aplican a todos):
> 1. La ausencia de dato **no** es cero.
> 2. Prohibido promediar la permanencia → usar `suma(días-persona) / suma(visitantes)`.
> 3. No sumar la base diaria para obtener el mes.
> 4. No sumar subdestinos para obtener el total.
> 5. No mezclar aeronaves con personas.
> 6. No extrapolar encuestas a totales absolutos (la encuesta es muestral).

---

## 1. Estado actual verificado

| Pieza | Estado | Nota |
|---|---|---|
| ETL (`load→clean→transform→pipeline`) | ✅ Funciona | 3 fuentes → 19 tablas en `data/processed/` |
| Tests | ✅ 13 pasan | `pytest -q` → 13 passed |
| 4 páginas Streamlit | ⚠️ Esqueleto | gráficos básicos + checklists "Pendiente" |
| `src/models/forecast.py` | ❌ Stub | `raise NotImplementedError("Fase 3")` |
| `docs/` | ❌ No existe | el README referencia `asignacion_modulos.md` y `memoria_tecnica.md` |
| `notebooks/` | ⚠️ Vacío | solo `.gitkeep` |
| Docker / Makefile / requirements | ✅ OK | `docker compose up --build` funciona |

**Conclusión:** el andamiaje de ingeniería está bien. Falta el ~60% del contenido
analítico y documental que exige la guía.

---

## 2. Hallazgos de datos (medidos — definen el diseño)

### 2.1 La capacidad instalada de alojamiento NO EXISTE en las fuentes

`indice_ocupacion_mensual_2023_2025_1.csv` contiene solo 4 columnas: `anio, mes,
departamento, indice_ocupacion` (792 filas = 22 dept × 36 meses, 2023-01→2025-12,
completo).

El Módulo 3 de la guía pide *"Evolución anual (2022–2025) de establecimientos,
habitaciones y plazas cama departamentales"*. **Es materialmente imposible con lo
entregado.**

**Decisión:** documentar el gap de forma explícita y visible (dashboard + memoria
técnica) y convertirlo en **recomendación de datos a incorporar a futuro** (la guía
lo pide en "propuesta de nuevos datos"). No inventar proxies ni estimar inventarios.

### 2.2 La discontinuidad marítima de Izabal

| Frontera | Visitantes (`Turista`+`Excursionista`) | Otros tipos |
|---|---|---|
| `05 Puerto Barrios` | 2009–2016 (55,231) | `Cruceristas` hasta 2022; `Viajero` 2023-2026 |
| `06 Livingston` | 2009–2016 (38,191) | ídem |
| `04 Santo Tomás de Castilla` | 2009–2016 (931) | ídem |
| **2022** | **0 filas para las 3 fronteras** | — |

La serie oficial de visitantes de Izabal **no es continua**. Por eso la encuesta es
la pieza central del observatorio.

> Dato de contexto de la hoja `Notas` de la base oficial: *"Vía Marítima pierde
> detalle desde 2017 (cambio de registro)"* y *"los niveles no son perfectamente
> comparables con 2022 hacia atrás"* por el quiebre metodológico 2022→2023.

### 2.3 La encuesta es la única serie continua de Izabal

`BD_COMPLEMENTARIA` → `nuevo_destino == 'Izabal/Caribe'`: **2,153 registros,
2022-04 → 2026-08**.

Es **muestral** (sin factor de expansión) → solo porcentajes, nunca totales
absolutos (regla 6).

**Hueco real:** `2025-01` es el **único mes sin una sola fila** (2024-12 → 2025-02).

### 2.4 La llave del reto (Módulo 4): los borders de la encuesta mapean 1:1 con migración

Quitando el prefijo numérico `"NN "` de la columna `Frontera` de la base oficial:

| Encuesta (`frontera_nombre`) | Migración (`Frontera`) |
|---|---|
| El Florido | `12 El Florido` |
| La Ermita (Nueva Anguiatú) | `10 La Ermita (Nueva Anguiatú)` |
| San Cristóbal | `09 San Cristóbal` |
| Melchor de Mencos | `20 Melchor de Mencos` |
| El Carmen | `15 El Carmen` |
| La Aurora | `01 La Aurora` |
| Valle Nuevo | `07 Valle Nuevo` |
| La Mesilla | `16 La Mesilla` |
| Pedro de Alvarado | `08 Pedro de Alvarado` |
| Agua Caliente | `11 Agua Caliente` |
| Tecún Umán | `14 Tecún Umán` |

**11/11 coinciden.** Esto permite cruzar *dónde entró el visitante* (encuesta,
muestral) con *cuántos entraron* (migración, absoluto) → **tasa de transferencia
por frontera**. Es el corazón del reto.

**Las 9 fronteras que alimentan el destino** (las que registran visitantes con
destino Izabal/Caribe en la encuesta) son:

`12 El Florido` · `10 La Ermita (Nueva Anguiatú)` · `09 San Cristóbal` ·
`20 Melchor de Mencos` · `15 El Carmen` · `01 La Aurora` · `07 Valle Nuevo` ·
`16 La Mesilla` · `08 Pedro de Alvarado`

Las 2 restantes del mapeo (`11 Agua Caliente`, `14 Tecún Umán`) aparecen en la
encuesta general pero **no** en el subconjunto Izabal/Caribe: no alimentan el
destino y por eso quedan fuera de `ISABAL_FEEDER_BORDERS` (constante en
`src/config.py`).

Las 9 tienen **serie de visitantes continua 2009-2026** → son el ancla temporal
del corredor y la única base donde el embudo es medible (§4.1).

### 2.5 La ocupación de Izabal está completa (36 meses) → el pronóstico es viable

`2023-01 → 2025-12`, sin huecos. Perfil estacional (índice relativo): mínimo en
**octubre (0.78)**, máximo en **abril (1.27)**.

---

## 3. Diseño del pronóstico (lo más pesado: 15% de la nota)

### 3.1 Restricciones descubiertas al probar

Estas no son criterios de estilo: son límites reales de los datos que se
descubrieron ejecutando los modelos. Cualquier agente que implemente el pronóstico
debe respetar las tres primeras.

| Restricción | Detalle | Mitigación |
|---|---|---|
| **El índice de ocupación está acotado a [0,1]** | ETS plano proyectó **103% y 123.6%** de ocupación (2026-01 y 2026-04) | Transformación **logit** + inverse-logit → rango garantizado (0,1) |
| **ETS estacional exige ≥2 ciclos** | `ExponentialSmoothing` lanza `ValueError: Cannot compute initial seasonals` con <24 meses | Regla de protocolo: **historia mínima ≥25 meses**; los folds que no la cumplen se excluyen y se reportan |
| **La encuesta es demasiado ruidosa para pronóstico mensual** | Backtest 2024-01→2025-12 (n=23): factor de reparto **80.7% MAPE**, seasonal naive **100.0%**, logit-ETS **51.6%** | Se reporta honestamente el error alto y se explica la causa (muestreo pequeño: 6–117 registros/mes) |
| **La relación ocupación ↔ migración es débil** | `R²(ocupación ~ migración) = 0.069`; correlación de índices estacionales **0.144** | La migración se usa como **perfil estacional de referencia y benchmark**, no como driver primario. Se documenta como hallazgo |

### 3.2 Arquitectura de modelos (4 modelos, todos con backtest comparativo)

| # | Modelo | Descripción | Rol |
|---|---|---|---|
| M1 | **Logit-ETS** | ETS aditivo sobre `logit(ocupación)`, `seasonal_periods=12` | **Candidato principal** (respeta [0,1]) |
| M2 | **Logit-ETS damped** | Igual, con `damped_trend=True` | Alternativa anti-extrapolación |
| M3 | **Perfil estacional + factor de reparto** *(método literal de la guía)* | `valor_m = r_m × migración_m`, con `r_m` del destino | **Obligatorio por rúbrica** — se implementa y se contrasta |
| M4 | **Naive estacional** | mismo mes del año previo (media 2 años) | Baseline / control |

**M3 en detalle** (es el método que la guía exige textualmente):

```
r_m         = VisitantesEncuesta_Izabal(m) / VisitantesMigración_alimentadoras(m)   # ventana de referencia
Estimación(m) = r_m × VisitantesMigración_alimentadoras(m)                            # mes objetivo
```

Donde `VisitantesMigración_alimentadoras` usa solo `Turista + Excursionista` de las 9
fronteras de la tabla 2.4, y `r_m` se estima sobre una ventana con ambas fuentes
observadas (2023–2024).

### 3.3 Protocolo de validación (rolling-origin)

- **Expanding window**: para cada mes objetivo `t`, se entrena **solo** con datos `< t`.
- Se evaluan **MAPE, RMSE, MAE** por modelo y por fold.
- Se reportan las métricas agregadas **y el nº de folds válidos** (regla de ≥25 meses).
- Se reporta el **modelo ganador** y su identidad de forma visible en el dashboard.

### 3.4 Resultados medidos (ocupación Izabal, backtest 2025)

| Modelo | MAPE | RMSE | MAE |
|---|---|---|---|
| **Logit-ETS** | **10.75%** | **0.1053** | 0.080 |
| Logit-ETS damped | 11.26% | 0.1019 | 0.085 |
| Perfil estacional + factor de reparto | 11.27% | 0.1145 | 0.087 |
| Naive estacional (media 2 años) | 13.84% | 0.1317 | 0.109 |

> ⚠️ **Corrección 2026-11-11.** Esta tabla inicialmente predecía el pronóstico
> 2026 con `logit_ets_damped`. La implementación real **elige el modelo por
> backtest**, y ese procedimiento elige `logit_ets` (MAPE 10.75% frente a
> 11.26%): los números de abajo son los de la implementación, no al revés.
>
> | Mes | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 |
> |---|---|---|---|---|---|---|---|---|---|---|---|---|
> | **2026 (estimado)** | 0.939 | 0.940 | 0.915 | 0.984 | 0.968 | 0.932 | 0.939 | 0.955 | 0.951 | 0.890 | 0.903 | 0.961 |
> | 2025 (observado) | 0.780 | 0.740 | 0.640 | 0.820 | 0.830 | 0.730 | 0.740 | 0.810 | 0.820 | 0.560 | 0.750 | 0.920 |
>
> Rango 0.890–0.984: dentro de [0,1] por construcción (transformada logit).

Para la encuesta (muestral, muy ruidosa) el ganador es `logit_ets_damped` con
**MAPE 56.4%** (27 folds válidos) — el error alto es real y está explicado por el
tamaño de muestra (6–117 registros por mes), no por un fallo del modelo.

### 3.5 Los tres objetivos de imputación / pronóstico

| Objetivo | Qué falta | Método | Validación |
|---|---|---|---|
| **A. Ocupación ene-feb 2026** | la ocupación termina en 2025-12 → **exactamente los "dos meses" de la guía** | Logit-ETS + factor de reparto | Backtest 2025 (MAPE 10.75%) |
| **B. Encuesta 2025-01** | único mes sin filas | 4 modelos comparados | Backtest 2024-01→2025-12 (n=23) |
| **C. Ene-feb 2026 de la encuesta** | la encuesta **sí** los tiene observados | *pseudo-out-of-sample*: se enmascaran, se imputan y se comparan contra el real | Formal, satisface la letra de la rúbrica |

Toda cifra estimada: **violeta + línea discontinua + marcador vacío + etiqueta "Estimación"**.

---

## 4. Reto del Grupo 5 — Conectividad Fluvial y Embudo de Transferencia (Módulo 4)

### 4.1 El embudo cuantificado (métrica central del reto)

> ⚠️ **Corrección 2026-11-11 — la fórmula de este apartado cambió.**
> La versión original de este plan proponía:
>
> ```
> Tasa de Transferencia(b) = VisitantesEncuesta_Izabal(b) / VisitantesMigración(b)
> ```
>
> **Esa fórmula es inválida** y no debe implementarse: divide una **muestra**
> (encuesta, sin factor de expansión) entre un **conteo absoluto** (migración).
> El resultado no es una tasa sino un número cuyo valor depende del factor de
> muestreo de cada frontera y de cada año, y además no está acotado a [0,1].
> Usarlo violaría la regla 6.
>
> La fórmula correcta, ya implementada en `survey_transfer_rate`
> (`src/etl/transform.py`), es una **proporción dentro de la misma fuente**:
>
> ```
> Tasa de Transferencia(b) = VisitantesEncuesta_con_destino_Izabal(b)
>                            / VisitantesEncuesta_totales(b)        ∈ [0, 1]
> ```
>
> Es decir: **de las personas que entran por la frontera `b` y que la encuesta
> registra, ¿qué proporción declara destino Izabal/Caribe?** Lleva un
> **intervalo de Wilson al 95%** que acota la incertidumbre por tamaño de
> muestra, y el peso de cada frontera en el destino (`peso_en_izabal`).
>
> La migración del mismo período (visitantes y tránsito, en los meses en que la
> encuesta operó en esa frontera) se **adjunta como contexto absoluto** en la
> misma tabla, sin dividirse por ella. Ambas magnitudes se leen una al lado de
> la otra, nunca combinadas en un cociente.

**El hallazgo que encuadra todo el módulo:** el embudo **marítimo no es
medible**. En las tres fronteras marítimas de Izabal, los visitantes
(2009-01 → 2016-12) y el tránsito (2023-01 → 2026-06) **nunca coinciden en un
mismo mes**: 0 meses de solape. El embudo medible es el **terrestre**, sobre las
9 fronteras alimentadoras (176–204 meses de solape cada una). La métrica
`meses_solape` de `maritime_flow_profile` lo documenta.

### 4.2 Ejes de análisis del reto

| Eje | Fuentes | Hallazgo a producir |
|---|---|---|
| **Flujo turístico vs. comercial** | `Livingston` (turístico) vs `Puerto Barrios` (transferencia/carga) | Perfil `Viajero` vs `Turista` por frontera → evidencia de que Livingston es destino turístico y Puerto Barrios nodo de transferencia |
| **Conectividad fluvial** | `05 Puerto Barrios` → `04 Santo Tomás` → `Río Dulce` → `06 Livingston` | Grafo de conectividad + cadena de valor del corredor |
| **Estacionalidad del corredor** | migración 2009-2026 | Identificación de cuellos de botella por mes (el perfil de tránsito es plano todo el año → cuello **estructural**, no estacional) |
| **Tasa de transferencia por frontera** | encuesta (proporción + IC Wilson) | La migración se adjunta como contexto absoluto, sin dividirse por ella | Ranking de fronteras que más convierten a destino Izabal |
| **Subdestinos sin sumar** | encuesta `destino` normalizado | Peso relativo de Río Dulce / Livingston / Puerto Barrios / Quiriguá (nunca sumar) |
| **Itinerarios multi-parada** | encuesta `otros_destinos` | Co-ocurrencia de códigos de destino (320, 340, 222, 484) — **sin diccionario, no se nombran** |

### 4.3 Salidas del módulo

- Gráfico de embudo: entradas por frontera → transferencia a destino (muestral).
- Tabla de tasa de transferencia con las 11 fronteras mapeadas.
- Grafo/mapa de conectividad fluvial.
- **3–5 recomendaciones accionables para INGUAT** respaldadas en los cuellos de
  botella medidos.

### 4.4 Limitación estructural que hay que declarar

La taxonomía de transporte de la encuesta tiene **11 categorías y ninguna es
acuática** (no hay lancha, barco ni lanchaje; verificado sobre las 227,347 filas).
Por eso **la conectividad fluvial no se mide como modo de transporte**, sino como
**cadena espacial de nodos**: frontera de entrada → nodo del corredor
(Río Dulce, Puerto Barrios, Livingston) → subdestino.

Esto es un hallazgo, no un fallo del análisis, y debe aparecer explícitamente en
la memoria técnica: es el tipo de limitación que la guía pide documentar.

### 4.5 Supuesto sobre los códigos de destino

`otros_destinos` guarda itinerarios multi-parada con códigos numéricos (320, 340,
222, 484, 998) que pertenecen a un catálogo por base (V10/V11/V12) **que no viene
con diccionario**. Se reporta la **estructura de co-ocurrencia** —que es un
hecho— pero **no se les asigna nombre**: varias lecturas son consistentes con los
datos (320 y 340 podrían ser Río Dulce y Livingston en cualquier orden), así que
nombrarlos sería inventar. **Pedir el catálogo a INGUAT es una de las
recomendaciones del módulo.**

---

## 5. Arquitectura de cambios (archivos)

### 5.1 Nuevos / modificados en `src/`

| Archivo | Cambios |
|---|---|
| `src/config.py` | + `SURVEY_BORDER_MAP` (mapeo 1:1), `ISABAL_FEEDER_BORDERS`, `PALETA`, `FERIADOS_GT` (2021-2026), `EVENTOS_DESTINO` |
| `src/etl/clean.py` | + fix de mojibake (`AsunciÃ³n Mita` → `Asunción Mita`), marca `es_alimentadora` |
| `src/etl/transform.py` | + ~10 funciones nuevas (ver 5.2) |
| `src/models/forecast.py` | **Reemplazar el stub** por la arquitectura de 4 modelos (§3) |
| `src/models/__init__.py` | exports públicos |
| `src/analysis/feriados.py` | **NUEVO** — calendario de feriados de Guatemala 2021-2026 + eventos del destino; `es_feriado`, `es_evento`, `nombre_evento` |
| `src/analysis/embudo.py` | **NUEVO** — composición analítica del Módulo 4: `descomposicion_corredor`, `cadena_flujo`, `grafo_conectividad`, `participacion_nodos_agua`, `modo_por_nodo`, `recomendaciones_inguat`, `perfil_itinerarios` |
| `src/utils/helpers.py` | + `logit`, `ilogit`, `metricas_error` (MAPE/RMSE/MAE), `mapa_frontera` |

### 5.2 Transformaciones nuevas (`src/etl/transform.py`)

| Función | Módulo | Propósito |
|---|---|---|
| `survey_segment_tourist_excursionist` | M1 | Segmentación turista vs excursionista (abs + %) |
| `survey_days_person_monthly` | M1 | Días-persona por mes (regla 2) |
| `survey_weekly_pattern` | M2 | Patrón semanal **normalizado** (promedio por día, no suma bruta) |
| `survey_holiday_lift` | M2 | Lift % de cada festividad vs día regular promedio |
| `survey_border_migration` | M4 | Cruce encuesta ↔ migración por frontera (mapeo 1:1) |
| `survey_transfer_rate` | M4 | Tasa de transferencia por frontera **con IC de Wilson** (proporción, §4.1) |
| `survey_border_node_flow` | M4 | Cadena frontera → nodo del corredor (la conectividad fluvial) |
| `survey_node_transport` | M4 | Modo de transporte por nodo del corredor |
| `maritime_flow_profile` | M4 | Cobertura y **meses de solape** por frontera (el hallazgo central) |
| `corridor_funnel_matrix` | M4 | Matriz corredor × mes × tipo de flujo |
| `survey_itinerarios` | M4 | Co-ocurrencia de códigos de `otros_destinos` (sin diccionario) |
| `occupancy_vs_affluence` | M3 | Cruce analítico de la ventana coincidente |
| `migration_seasonal_index` | M2/M4 | Perfil estacional de migración por frontera |
| `data_quality` (ampliar) | todos | + hueco 2022, + hueco 2025-01, + nota de decimales (encuestas expandidas) |

### 5.3 Dashboard

| Archivo | Cambios |
|---|---|
| `app/components/kpis.py` | + `kpi_estimacion`, `estilo_estimacion`, `leyenda_paleta`, `badge_tipo_dato` (Observado / Muestral / Estimación) |
| `app/components/theme.py` | **NUEVO** — paleta documentada + reglas de uso + constantes de ritmo de presentación |
| `app/components/layout.py` | **NUEVO** — armazón de presentación común: `modulo()`, `kpis()`, `seccion()`, `insight()`, `caveat()`, `bloque()`, `detalle()` |
| `app/components/charts.py` | **NUEVO** — helpers de gráficos (patrón de línea por serie, formato %, tratamiento de estimación, `titulo_grafico()`) |
| `app/components/data.py` | + `get_optional` (no rompe si falta un dataset) |
| `app/app.py` | **Reescritura** — narrativa del observatorio, storyline, resumen de hallazgos, tarjetas de fuentes, enlace a docs |
| `app/pages/1_monitor_demanda.py` | **Reescritura** — KPIs (visitantes/mes, días-persona, estadía ponderada), segmentación, top nacionalidades, visualización enlazada |
| `app/pages/2_dinamica_temporal.py` | **Reescritura** — serie diaria, selector de eventos con Lift, patrón semanal, pronóstico con backtest y métricas |
| `app/pages/3_oferta_hotelera.py` | **Reescritura** — ocupación, ventana coincidente con cruce real, subdestinos, aviso de gap de capacidad |
| `app/pages/4_conectividad_fluvial.py` | **Reescritura** — embudo cuantificado, tasa por frontera, cadena fluvial (grafo + heatmap), modo por nodo, cuellos de botella, recomendaciones con evidencia |
| `app/pages/5_calidad_datos.py` | **NUEVO (opcional, recomendado)** — transparencia metodológica: cobertura, huecos, reglas aplicadas |
| `notebooks/03_embudo_transferencia.ipynb` | **NUEVO** — análisis exploratorio del reto (hallazgo de fondo, mapeo, tasa, cadena, cuellos, itinerarios) |

### 5.4 Documentación y notebooks

| Archivo | Contenido |
|---|---|
| `docs/asignacion_modulos.md` | Reparto de los 4 integrantes por módulo + alcance de cada uno |
| `docs/memoria_tecnica.md` | **Entregable formal.** Estructura exigida por la guía (ver §7) |
| `docs/catalogo_indicadores.md` | Fichas técnicas de cada indicador (campos 1–8 de la guía) |
| `docs/paleta_y_diseno.md` | Paleta + teoría del color + reglas de accesibilidad |
| `notebooks/01_calidad_datos.ipynb` | EDA, cobertura, huecos, decisiones de limpieza |
| `notebooks/02_pronostico_backtest.ipynb` | Modelos, backtest rolling-origin, métricas |
| `notebooks/03_embudo_transferencia.ipynb` | Cruce encuesta-migración, tasa de transferencia |
| `notebooks/04_ventana_coincidente.ipynb` | Cruce afluencia-ocupación |

### 5.5 Tests nuevos (`tests/`)

| Test | Qué valida |
|---|---|
| `test_forecast_bounds.py` | Ninguna predicción de ocupación fuera de [0,1] |
| `test_forecast_metrics.py` | MAPE/RMSE/MAE coinciden con cálculo manual; nº de folds válidos |
| `test_border_mapping.py` | Los 9 borders alimentadores mapean 1:1 a migración; 0 meses de solape en las marítimas |
| `test_transfer_rate.py` | Tasa ∈ [0,1], denominador ≠ 0, IC de Wilson contiene la estimación, pesos suman 1 |
| `test_corridor_share_gaps.py` | Los huecos del corredor son NaN y no 0 (regla 1) |
| `test_holidays.py` | Calendario sin solapes ni fechas inválidas; lift calculado sobre días válidos |
| `test_rules_extended.py` | Reglas 1–6 ampliadas (días-persona, patrón semanal normalizado, estimación no contada como observado) |
| `test_dashboard_smoke.py` | Cada página del dashboard renderiza sin errores y sus selectores no la rompen |
| `test_diseno.py` | Reglas de presentación: ≤ 5 secciones por módulo, una fila de KPI, alturas de gráfico estándar, titulares como afirmaciones |

---

## 6. Paleta de color y teoría del color (la nota de UI/UX vale 40%)

### 6.1 Problema medido en la paleta actual

Contraste perceptual (OKLab, bajo el **peor caso** de daltonismo) entre los colores
actuales de `app/components/kpis.py`:

| Par | dE | Veredicto |
|---|---|---|
| primario `#0E7C86` vs acento `#5B8E7D` | **0.052** | casi indistinguibles |
| primario vs alerta `#C0392B` | 0.045 | casi indistinguibles |
| primario vs estimación `#9B59B6` | 0.070 | límite |
| estimación vs info `#2E5EAA` | **0.019** | colapsan bajo deuteranopía |

Además `#F4A259` (arena) tiene contraste **2.07** contra blanco → **no cumple AA
para texto**.

### 6.2 Paleta final propuesta (validada)

| Rol | Hex | L (OKLab) | Contraste vs blanco | Uso |
|---|---|---|---|---|
| `primario` (turquesa Caribe) | `#0E7C86` | 0.536 | 4.95 | AA texto; serie principal |
| `secundario` (arena) | `#D97706` | 0.666 | 3.19 | relleno / gráfico |
| `acento` (turquesa claro) | `#3FA8B8` | 0.678 | 2.80 | relleno / gráfico |
| `alerta` (coral) | `#C0392B` | 0.543 | 5.44 | AA texto |
| `info` (azul profundo) | `#1B4F8F` | 0.429 | 8.20 | AA texto |
| `estimacion` (violeta) | `#7D3C98` | 0.481 | 7.07 | AA texto; **exclusivo de estimaciones** |
| `neutro` | `#6C757D` | 0.558 | 4.69 | gris / temático |
| `texto` | `#1F2933` | 0.276 | 14.76 | texto general |

**Núcleo categórico de 5** (uso simultáneo en un mismo gráfico): `#0E7C86`,
`#D97706`, `#3FA8B8`, `#C0392B`, `#1B4F8F` → **dE mínimo = 0.113** bajo el peor
caso de daltonismo (protanopía / deuteranopía / tritanopía). Cumple el umbral 0.10.

### 6.3 Reglas de diseño (teoría del color aplicada)

1. **Separación por forma, no solo por tono:** las estimaciones se distinguen por
   **violeta + línea discontinua + marcador vacío + etiqueta**, nunca solo por color.
2. **El violeta de estimación nunca comparte escala categórica** con datos observados.
3. **Encoding redundante** en series múltiples: cada serie lleva además un patrón de
   línea distinto (`solid`, `dash`, `dot`, `dashdot`) → legible en impresión B/N y
   para daltonismo.
4. **Jerarquía de luminosidad:** el color categórico se reserva para la serie en foco;
   el resto baja a `#6C757D` con 0.35 de opacidad.
5. **Límite de 5 series simultáneas.** Si hay más categorías: small multiples o
   filtrado por selector.
6. **Contraste:** texto ≥ 4.5:1, elementos gráficos ≥ 3:1 (WCAG 2.1).

---

### 6.4 Sistema de presentación (armazón común a los 4 módulos)

Un observatorio se presenta en pantalla. El contenido acumulado hace que la
página se vuelva ilegible y la historia se pierda, así que el diseño se
normaliza en `app/components/layout.py` y **las reglas se verifican con tests**
(`tests/test_diseno.py`).

**Reglas duras:**

| Regla | Límite |
|---|---|
| Secciones visibles por módulo | **≤ 5** |
| Filas de tarjetas KPI por módulo | **1** (máx. 4 tarjetas) |
| Alturas de gráfico | solo **300 / 380 / 440 px** (`ALTURA`, `ALTURA_GRANDE`, `ALTURA_ALTA`) |
| Gráficos por sección | ≤ 2 visibles; el resto en `st.expander` de detalle |
| Título de sección | es una **afirmación con la cifra dentro**, nunca una pregunta |
| Título de gráfico | es la **conclusión** de lo que se ve |

**Piezas del armazón:**

| Función | Qué hace |
|---|---|
| `modulo(titulo, pregunta, afirmacion)` | Cabecera: título + pregunta de gestión + la conclusión del módulo en negrita |
| `kpis(items)` | Fila de tarjetas KPI con borde de acento (estilo propio, no `st.metric`) |
| `seccion(afirmacion, subtitulo, badge)` | Separador con el titular como afirmación y badge del tipo de dato |
| `insight(texto)` | Línea de lectura del gráfico: lo que hay que retener (barra de color a la izquierda) |
| `caveat(texto)` | Advertencia de método, en el color de alerta |
| `titulo_grafico(fig, afirmacion, subtitulo)` | Título del gráfico como afirmación |

**Scroll, no tabs:** la historia se lee de arriba abajo y el contenido
secundario se colapsa en `st.expander`. Es lo que permite que un módulo se
recorra en 3–4 pantallas.

---

## 7. Memoria técnica (entregable formal, 15%)Estructura exigida por la guía, mapeada a los archivos del repo:

| Sección de la guía | Dónde vive |
|---|---|
| 1. Resumen ejecutivo (3-4 hallazgos cuantitativos + resumen de pronósticos) | `docs/memoria_tecnica.md` |
| 2. Arquitectura y modelo de datos (estructura, relaciones, carpetas) | `docs/memoria_tecnica.md` + `README.md` |
| 3. Catálogo formal de indicadores (fichas 1–8) | `docs/catalogo_indicadores.md` |
| 4. Desarrollo y resolución del reto específico | `docs/memoria_tecnica.md` |
| 5. Supuestos, limitaciones y calidad de las fuentes | `docs/memoria_tecnica.md` (sección larga: las 5 limitaciones medidas) |
| 6. Recomendaciones a INGUAT (3-5) + datos nuevos a futuro | `docs/memoria_tecnica.md` |
| 7. Anexos: repo, requirements, fragmentos reproducibles, despliegue | `docs/memoria_tecnica.md` + `README.md` |
| Adicional: investigación sobre Observatorio de Turismo Sostenible (red INSTO / SEGITTUR) | `docs/memoria_tecnica.md`, con fuentes consultables |

---

## 8. Reparto propuesto (4 personas / 4 módulos)

| Persona | Módulo | Responsabilidad principal | Entregables clave |
|---|---|---|---|
| **A** | **M1** — Monitor de Demanda y Mercados Emisores | KPIs (visitantes/mes, días-persona, estadía ponderada), segmentación turista/excursionista, top 10 nacionalidades | `survey_segment_tourist_excursionist`, `survey_days_person_monthly`, página 1 reescrita |
| **B** | **M2** — Dinámica Temporal, Eventos y Pronóstico | Calendario de feriados con **Lift**, patrón semanal normalizado, **todo el sistema de pronóstico + backtest + métricas** | `src/models/forecast.py` completo, `src/analysis/feriados.py`, página 2 reescrita |
| **C** | **M3** — Oferta Hotelera y Desagregación Territorial | Ocupación 2023-2025, ventana coincidente Sep-Dic 2025 con cruce analítico real, subdestinos, **documentación del gap de capacidad instalada** | `occupancy_vs_affluence`, página 3 reescrita, sección de limitaciones |
| **D** | **M4** — Conectividad Fluvial y Embudo de Transferencia | **Tasa de transferencia por frontera**, flujo turístico vs comercial, conectividad fluvial, estacionalidad del corredor, **recomendaciones INGUAT** | `src/analysis/embudo.py`, `survey_transfer_rate`, página 4 reescrita |
| **Transversal** | — | `docs/asignacion_modulos.md`, paleta + teoría del color, `docs/memoria_tecnica.md` (redacción conjunta), notebooks | Documentos del repo |

> Los nombres de los 4 integrantes se completan en `docs/asignacion_modulos.md` cuando
> el grupo lo defina.
>
> **Orden de arranque sugerido:** **B arranca primero** (es el módulo más pesado y
> bloquea la página 2). **D va en paralelo** (es el que más distingue al grupo).

---

## 9. Fases de ejecución (orden recomendado)

### 📍 Estado de avance (actualizado 2026-11-11)

| Fase | Estado | Entregables |
|---|---|---|
| 0 · Fundaciones | ✅ | `asignacion_modulos.md`, `feriados.py`, helpers, `theme.py`, notebook 01 |
| 1 · Pronóstico | ✅ | `forecast.py` (4 modelos + backtest), 3 salidas, tests, notebook 02 |
| 2 · ETL transversal | ✅ | 12 transformaciones nuevas, `data_quality` ampliado, tests de reglas |
| 3 · Módulos 1 y 3 | ✅ | páginas 1 y 3 reescritas con visualización enlazada |
| **4 · Módulo 4 (reto)** | ✅ | `embudo.py`, 3 transformaciones, página 4 reescrita, notebook 03, 3 tests |
| **5 · Módulo 2 en el dashboard** | ✅ | página 2 reescrita: serie diaria + selector de festividad con lift dinámico, patrón semanal, pronóstico de ocupación ene-feb 2026 (modelo ganador) y validación formal (MAPE + comparación de los 4 modelos, incluido el factor de reparto obligatorio por rúbrica) |
| 6 · Pulido transversal | ✅ | `app.py`, `docs/catalogo_indicadores.md`, `docs/paleta_y_diseno.md`, `memoria_tecnica.md` (8 secciones completas), `notebooks/04_ventana_coincidente.ipynb`, `README.md` y nombres reales en `asignacion_modulos.md`. **Verificación final completa (2026-11-12):** `pytest -q` → 107 passed; `docker compose up --build` → levanta y responde HTTP 200; las 6 reglas metodológicas quedan cubiertas por tests |

**Correcciones aplicadas el 2026-11-11** (Fase 4):

1. **Regla 1 en `corridor_share`** — la participación del corredor se calculaba
   rellenando con 0 los meses sin registro, produciendo 107 filas que se leían
   como "0 % de participación" cuando no había dato. Ahora es `NaN` + las
   columnas `n_fronteras_con_dato` y `corredor_completo`.
2. **`ISABAL_FEEDER_BORDERS`** — estaba en `None` con un comentario que decía
   que el plan no enumeraba las fronteras alimentadoras. **Sí las enumeraba**
   (§2.4): son 9, no 11. Ahora están las 9 y el comentário es correcto.
   Impacto medido: el MAPE del modelo `factor_reparto` pasa de 11.43% a 11.27%
   y la imputación de 2025-01 de 75.4 a 77.7. **El modelo ganador no cambia**
   (`logit_ets` no usa migración).
3. **Wilson con k=0** — el límite inferior del intervalo daba ~1e-18 en vez de
   0, de modo que el IC no contenía la estimación puntual.
4. **Fórmula de la tasa de transferencia** (§4.1) — se corrigió el plan, no el
   código: la implementación ya era la correcta.
5. **`docs/PLAN.md` §3.4 y §4** — actualizados con las métricas reales.

**Tests: 50 → 85.**

### Fase 0 — Fundaciones (común) ✅
1. `docs/asignacion_modulos.md` con los nombres.
2. `src/analysis/feriados.py` con el calendario GT 2021-2026 (base para M2).
3. `src/utils/helpers.py`: `logit`/`ilogit`, `metricas_error`, `mapa_frontera`.
4. `app/components/theme.py` con la paleta validada.
5. `notebooks/01_calidad_datos.ipynb` → deja fijados los hallazgos de §2.

### Fase 1 — Pronóstico (B) · desbloquea M2
6. `src/models/forecast.py`: los 4 modelos + rolling-origin backtest + métricas.
7. Tests: `test_forecast_bounds.py`, `test_forecast_metrics.py`.
8. Salida procesada: `forecast_occupancy.parquet`, `forecast_survey.parquet`, `forecast_metrics.parquet`.
9. `notebooks/02_pronostico_backtest.ipynb`.

### Fase 2 — ETL transversal (todos)
10. Las ~10 transformaciones nuevas en `src/etl/transform.py`.
11. Ampliar `data_quality` con los huecos 2022 y 2025-01.
12. Tests de reglas ampliadas.

### Fase 3 — Módulos 1 y 3 (A y C) en paralelo
13. Página 1 (A): KPIs, segmentación, nacionalidades, visualización enlazada.
14. Página 3 (C): ocupación, ventana coincidente (con gráfico de dispersión y correlación), subdestinos, aviso de gap.

### Fase 4 — Módulo 4 (D) · el reto ✅
15. `src/analysis/embudo.py`: composición analítica del reto.
16. Página 4 reescrita: embudo, tasa por frontera, cadena fluvial, modo por nodo, cuellos, recomendaciones.
17. `notebooks/03_embudo_transferencia.ipynb`.

### Fase 5 — M2 en el dashboard (B) ❌ **pendiente**
18. Página 2: serie diaria, selector de eventos con Lift, patrón semanal, pronóstico con backtest y métricas visibles.
    _Los datasets ya existen: `forecast_occupancy`, `forecast_survey`, `forecast_metrics`, `survey_holiday_lift`, `survey_weekly_pattern`._

### Fase 6 — Pulido transversal (todos)
19. `app/app.py` reescrito con narrativa y storyline.
20. **Visualizaciones vinculadas (3+):** selector de frontera que filtra varias gráficas del mismo módulo.
21. `docs/catalogo_indicadores.md` (fichas 1–8 de cada indicador).
22. `docs/paleta_y_diseno.md`.
23. `docs/memoria_tecnica.md` (redacción conjunta).
24. `notebooks/04_ventana_coincidente.ipynb`.
25. `README.md` actualizado con el estado real.
26. Verificación final: `pytest -q`, `docker compose up --build`, revisión de las 6 reglas metodológicas.

---

## 10. Criterios de aceptación (checklist de entrega)

- [x] Los 4 módulos del dashboard tienen contenido completo, sin checklists "Pendiente".
- [x] Existe un pronóstico con **MAPE/RMSE/MAE reportados** y backtest rolling-origin visible en la página 2.
      Verificado 2026-11-12 con datos reales: modelo ganador `logit_ets`, MAPE 10.75%,
      estimación ene/feb 2026 = 93.9% / 94.0% (coincide exacto con §3.4).
- [x] Todas las cifras estimadas están **rotuladas y diferenciadas** (violeta + discontinuo + etiqueta).
- [x] Ninguna predicción de ocupación sale de [0,1] (acotado en código por `_acotar` + transformada logit;
      cubierto por `tests/test_forecast_bounds.py`, verificado 2026-11-12: pasa).
- [x] Los 3 gráficos enlazados mínimo funcionan con un selector compartido (Módulos 1, 3 y 4).
- [x] La paleta está documentada en `docs/paleta_y_diseno.md` con teoría del color y reglas de accesibilidad.
- [x] `docs/memoria_tecnica.md` tiene las 8 secciones de la guía, con las fichas de indicadores
      (en `docs/catalogo_indicadores.md`).
- [x] El gap de capacidad instalada está documentado como limitación + recomendación.
- [x] Las 6 reglas metodológicas están citadas y respetadas (con tests que las cubren:
      `test_rules.py`, `test_rules_extended.py`).
- [x] `pytest -q` pasa (**107 passed, 1 warning** — verificado 2026-11-12 con datos reales
      y dependencias instaladas; el warning es un `Pandas4Warning` por `dt.dayofweek`
      deprecado en `transform.py`, no afecta el resultado).
- [x] `docker compose up --build` levanta el dashboard con los datos montados por volumen.
      Verificado 2026-11-12: build exitoso, contenedor responde HTTP 200 en `:8501`, sin
      errores en logs; se bajó con `docker compose down` tras la prueba.
- [x] El repo es privado y `data/` sigue en `.gitignore` (confirmado por el usuario
      2026-11-12; `.gitignore` también verificado en código).

---

## 11. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Los 4 integrantes no pueden coordinar entregas simultáneas | Bloqueo del dashboard | El módulo 2 (B) es el único con dependencia fuerte; A, C y D son independientes entre sí |
| La encuesta tiene error alto y un docente cuestiona el pronóstico | Crítico en 15% | Se reporta el error real con su causa; el pronóstico principal es el de ocupación (MAPE 10.75%), que es sólido |
| Los datos de ocupación 2026 no llegan | Afecta el objetivo A | Se documenta que la imputación es una estimación con error publicado, no un dato |
| No hay datos de capacidad instalada | Incumple un bullet del Módulo 3 | Documentado explícitamente como limitación + recomendado a INGUAT (la guía lo pide) |
| Se confunde muestra con absoluto | Regla metodológica violada | Badge `Observado / Muestral / Estimación` en todas las gráficas + tests |
| El puerto 8501 ocupado / Docker falla en el aula | No se puede calificar | Verificar `docker compose up --build` con tiempo de sobra antes de la entrega |

---

## Anexo — Cómo reproducir los hallazgos de este plan

```bash
# Instalar y correr el ETL
pip install -r requirements.txt
python -m src.etl.pipeline

# Verificar cobertura y huecos
python - <<'PY'
import pandas as pd
s = pd.read_parquet('data/raw/BD_COMPLEMENTARIA')
s['fecha'] = pd.to_datetime(s['fecha'])
iz = s[s['nuevo_destino'].eq('Izabal/Caribe')]
m = iz.groupby(iz['fecha'].dt.to_period('M')).size()
full = pd.period_range(m.index.min(), m.index.max(), freq='M')
print("Meses sin filas:", [str(p) for p in full if p not in m.index])   # -> ['2025-01']
PY

# Tests
pytest -q
```

---

*Documento generado a partir del análisis directo de `data/raw/`. Si un número de
este plan no se reproduce con los comandos de arriba, hay que actualizar el plan
antes de implementarlo.*
