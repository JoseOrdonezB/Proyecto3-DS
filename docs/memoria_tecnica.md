# Memoria Técnica y Recomendaciones
## Observatorio de Inteligencia Turística — Grupo 5
### Río Dulce y Livingston, Izabal · Reto: Conectividad Fluvial y Embudo de Transferencia

**Curso:** CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II 2026
**Versión:** 0.3 — 2026-11-12
**Estado:** redacción completa de las 8 secciones exigidas por la guía. Verificado
contra una corrida real de `python -m src.etl.pipeline` y `pytest -q` (107 passed) el
2026-11-12; `docker compose up --build` también probado y funcional.

> **Uso:** cada integrante del grupo redacta la sección de su módulo y el
> responsable de cada bloque la completa. Las cifras de esta memoria **deben**
> salir de `data/processed/` y ser reproducibles con el código del repositorio.

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura y modelo de datos](#2-arquitectura-y-modelo-de-datos)
3. [Catálogo formal de indicadores y métricas](#3-catálogo-formal-de-indicadores-y-métricas)
4. [Desarrollo y resolución del reto analítico específico](#4-desarrollo-y-resolución-del-reto-analítico-específico)
5. [Supuestos, limitaciones y calidad de las fuentes](#5-supuestos-limitaciones-y-calidad-de-las-fuentes)
6. [Recomendaciones estratégicas y hoja de ruta para INGUAT](#6-recomendaciones-estratégicas-y-hoja-de-ruta-para-inguat)
7. [Anexos técnicos y repositorio](#7-anexos-técnicos-y-repositorio)
8. [Investigación: qué es un Observatorio de Turismo Sostenible](#8-investigación-qué-es-un-observatorio-de-turismo-sostenible)

---

## 1. Resumen ejecutivo

El Grupo 5 construyó un observatorio de inteligencia turística para Río Dulce y
Livingston (Izabal), cruzando tres fuentes institucionales de naturaleza distinta
—migración oficial (absoluta), ocupación hotelera (absoluta) y una encuesta de turismo
(muestral, sin factor de expansión)— para resolver el reto asignado: **Conectividad
Fluvial y Embudo de Transferencia**.

El hallazgo que encuadra todo el análisis es que el corredor marítimo de Izabal **no
tiene un embudo medible**: en sus tres fronteras, los visitantes (2009–2016) y el
tránsito (2023–2026) nunca coinciden en un mismo mes. El embudo sí se mide en las 9
fronteras terrestres que alimentan el destino, y ahí dos de ellas concentran la mayor
parte del flujo. La demanda de traslado por el corredor, además, resultó ser
**estructural y no estacional**: no se concentra en temporada alta, así que la
capacidad de transporte debe planificarse todo el año.

En paralelo, se resolvió el pronóstico obligatorio de ocupación hotelera de Izabal para
enero–febrero de 2026 con cuatro modelos comparados por backtest rolling-origin: el
ganador (Logit-ETS, transformada logit para garantizar el rango [0,1]) reporta un
**MAPE de 10.75 %**, por debajo del método que la guía exige textualmente (perfil
estacional + factor de reparto de la migración, MAPE 11.27 %) y del baseline naive
(13.84 %). La encuesta —muestral y mucho más ruidosa— se pronostica aparte, con un error
más alto (MAPE ≈ 56 %) que se explica por el tamaño de muestra mensual, no por un fallo
del método.

**Los 3–4 hallazgos cuantitativos de mayor impacto para el INGUAT:**

1. El corredor marítimo no admite una tasa de transferencia calculable con la fuente
   actual (0 meses de solape visitante-tránsito en sus 3 fronteras); el dato que haría
   falta no existe hoy.
2. Dos fronteras terrestres (El Florido y La Ermita) concentran el **80 %** de la
   muestra con destino Izabal/Caribe: son el punto de mayor apalancamiento para
   cualquier intervención de promoción o señalización.
3. El tránsito del corredor tiene un coeficiente de variación de solo **0.22**: es una
   demanda permanente, no estacional, y debe planificarse como tal.
4. El pronóstico de ocupación 2026 queda acotado por construcción a [0,1] y reporta
   error formal (MAPE 10.75 %), cumpliendo la exigencia de rigor analítico de la guía.

Las limitaciones de mayor peso —ausencia de inventario hotelero, discontinuidad de la
vía marítima desde 2017, y la naturaleza muestral de la encuesta— se documentan en
detalle en §5, junto con las recomendaciones accionables para INGUAT en §6.

Hallazgos cuantitativos que respaldan este resumen (ver §4):

| # | Hallazgo | Cifra |
|---|---|---|
| 1 | El corredor marítimo de Izabal **no tiene embudo medible**: visitantes y tránsito nunca coexisten | **0 meses de solape** en las 3 fronteras marítimas |
| 2 | El acceso terrestre al destino depende de **dos fronteras** | **80%** de la muestra (El Florido + La Ermita) |
| 3 | Río Dulce concentra el flujo turístico del corredor | **51.4%** de los registros de la muestra |
| 4 | El tránsito del corredor es **estructural, no estacional** | CV **0.22**, mínimo en octubre |
| 5 | Pronóstico de ocupación 2026 con error formal reportado | MAPE **10.75%** (Logit-ETS, backtest rolling-origin) |

---

## 2. Arquitectura y modelo de datos

### 2.1 Fuentes de origen

| # | Fuente | Archivo | Formato | Cobertura | Naturaleza |
|---|---|---|---|---|---|
| 1 | Migración oficial | `data/raw/Base_Migracion_2009-2026jun.xlsx` (hoja `Datos`) | XLSX | ene 2009 – jun 2026 | **Absoluta** (conteos) |
| 2 | Índice de ocupación hotelera | `data/raw/indice_ocupacion_mensual_2023_2025_1.csv` | CSV | 2023 – 2025 | **Absoluta** (índice 0–1) |
| 3 | BD complementaria (encuesta) | `data/raw/BD_COMPLEMENTARIA` | Parquet | oct 2021 – ago 2026 | **Muestral** (sin factor de expansión) |

> ⚠️ **Confidencialidad.** Las tres fuentes son registros institucionales de uso
> exclusivamente académico. `data/` está en `.gitignore`, el repositorio es
> **privado** y no se habilitan descargas masivas de microdatos en el dashboard.

### 2.2 Modelo de datos

```
MIGRACIÓN (absoluta)                      ENCUESTA (muestral)
───────────────────────                   ─────────────────────
161,036 filas                             227,347 filas
  fecha (mes)                                fecha (día)
  Frontera (22 + Cruceros)                  frontera_nombre (11)
  Vía (aérea/marítima/terrestre)            frontera_tipo (terrestre/aérea)
  Tipo de Viajero (4)                       destino / otros_destinos (códigos)
  País / agrupación (27 desde 2023)        subdestino (normalizado)
  Viajero (medida)                          estadia, noches, hospedaje
                                            tipo_transporte, residencia
        │                                          │
        │  mapeo 1:1 por nombre de frontera        │
        └──────────────►┬──────────────────────────┘
                       ▼
              CORREDOR DE TRANSFERENCIA
    (tasa de transferencia, cadena de nodos,
     perfil de flujo, cuellos de botella)
```

**Cardinalidades verificadas:**
- Encuesta → Migración: **11 fronteras** con equivalencia 1:1; de ellas, **9**
  registran visitantes con destino Izabal/Caribe.
- Visitantes y tránsito marítimos: **0 meses de solape** (§4.1).
- Encuesta → subdestinos: 17 categorías normalizadas a 11 nodos del corredor.

### 2.3 Estructura de carpetas del tablero

```
Proyecto3-DS/
├── data/
│   ├── raw/                  # fuentes originales (ignoradas por git)
│   └── processed/            # salida del ETL: 33 tablas parquet + csv
├── src/
│   ├── config.py             # rutas, constantes de negocio, paleta
│   ├── data.py               # carga de datos procesados
│   ├── etl/
│   │   ├── load.py  clean.py  transform.py  pipeline.py
│   ├── models/forecast.py    # 4 modelos + backtest rolling-origin
│   ├── analysis/             # feriados.py, embudo.py
│   └── utils/helpers.py
├── app/
│   ├── app.py                # página principal
│   ├── pages/                # 4 módulos
│   ├── components/           # theme.py, charts.py, kpis.py, data.py
│   └── assets/style.css
├── notebooks/                # 01 calidad, 02 pronóstico, 03 embudo
├── docs/                     # PLAN.md, memoria, catálogo, paleta
└── tests/                    # 107 pruebas
```

### 2.4 Pipeline ETL

```
load → clean → transform → forecast → save
```

- **Load**: valida el esquema de las 3 fuentes (columnas obligatorias).
- **Clean**: normaliza texto y fechas, aplica banderas de negocio
  (`es_visita`, `es_nacional`, `es_izabal`, `es_pernocta`), marca como nulos
  las permanencias > 365 días y excluye registros con `validacion` nula.
- **Transform**: 28 agregaciones analíticas.
- **Forecast**: 4 modelos comparados con backtest rolling-origin.
- **Save**: parquet (uso del dashboard) + csv (inspección).

---

## 3. Catálogo formal de indicadores y métricas

El catálogo completo vive en [`docs/catalogo_indicadores.md`](catalogo_indicadores.md):
23 fichas técnicas (los 8 campos exigidos por la guía — nombre, definición de negocio,
fórmula formal, implementación en código, nivel de agregación, unidad de medida,
fuentes de origen y reglas de exclusión), agrupadas por módulo:

| Módulo | Indicadores documentados |
|---|---|
| M1 — Demanda y Mercados Emisores | 6: visitantes totales, proporción de pernocta, estadía media ponderada, días-persona, top 10 mercados emisores, migración de fronteras alimentadoras |
| M2 — Dinámica Temporal y Pronóstico | 5: serie diaria, patrón semanal normalizado, lift de festividades, pronóstico de ocupación, métricas de error (MAPE/RMSE/MAE) |
| M3 — Oferta Hotelera | 4: índice de ocupación, comparación interdepartamental, cruce ocupación-afluencia (correlación), participación de subdestinos |
| M4 — Conectividad Fluvial (el reto) | 8: meses de solape, tasa de transferencia, IC de Wilson, peso por frontera, nodo principal, modo de transporte, CV del tránsito, participación del corredor |

Las fichas del Módulo 4, redactadas primero por ser el reto del grupo, también se
presentan en prosa (con la evidencia que las sustenta) en la §4.7 de este documento.

---

## 4. Desarrollo y resolución del reto analítico específico

### 4.1 El reto y el hallazgo que lo reencuadra

El reto asignado al Grupo 5 es el **Embudo de Transferencia**: analizar cómo
entra el flujo hacia Río Dulce y Livingston y qué se queda en el destino.

El primer paso fue determinar **si el embudo es medible**. La respuesta es
**parcialmente**, y el resultado es el hallazgo más importante del módulo.

**Los dos flujos del corredor marítimo son disjuntos en el tiempo.** En las tres
fronteras marítimas de Izabal:

| Frontera | Visitantes (`Turista`+`Excursionista`) | Tránsito (`Viajero`) | Meses de solape |
|---|---|---|---|
| `05 Puerto Barrios` | 2009-01 → 2016-12 (96 meses) | 2023-01 → 2026-06 (42 meses) | **0** |
| `06 Livingston` | 2009-01 → 2016-12 (96 meses) | 2023-01 → 2026-06 (42 meses) | **0** |
| `04 Santo Tomás de Castilla` | 2009-01 → 2016-12 (95 meses) | 2023-01 → 2026-06 (41 meses) | **0** |

Además, **2022 no tiene ninguna fila** para estas tres fronteras, y entre 2017 y
2021 solo hay registros de `Cruceristas`.

**Consecuencia metodológica:** para el corredor marítimo **no existe una tasa de
transferencia calculable**. Cualquier ratio entre "visitantes que entraron por
Livingston" y "visitantes que llegaron a Río Dulce" mezclaría dos periodos
disjuntos y dos poblaciones distintas, y daría un número tentador pero falso. La
decisión metodológica del módulo es **no calcularlo** y **explicitar por qué**,
en lugar de producir una cifra sin respaldo.

La observación se apoya en la hoja `Notas` de la base oficial: *"Vía Marítima
pierde detalle desde 2017 (cambio de registro)"*.

**Dónde sí el embudo es medible:** el corredor **terrestre alimentador**. Las 9
fronteras que registran visitantes con destino Izabal/Caribe en la encuesta tienen
serie de visitantes continua 2009–2026 y coexisten con el tránsito en 176–204
meses cada una. Sobre ellas se construye el embudo.

### 4.2 La tasa de transferencia (fórmula y por qué es esta)

**Definición de negocio:** de las personas que ingresan al país por una frontera
`b` y que la encuesta registra, ¿qué proporción declara a Izabal/Caribe como
destino? Sirve al gestor para saber qué fronteras de entrada valen la pena
promocionar y cuáles son solo tráfico de paso.

**Fórmula matemática formal:**

```
                    Σ  visitantes con destino Izabal/Caribe
Tasa(b)  =  ───────────────────────────────────────────────────────
                    Σ  visitantes totales de esa frontera
```

Es decir, **de las personas que entran por la frontera `b` y que la encuesta
registra, ¿qué proporción declara destino Izabal/Caribe?**

**Implementación en código** (`src/etl/transform.py`, función
`survey_transfer_rate`):

```python
out["tasa_transferencia"] = out["visitantes_izabal"] / out["visitantes_total"]
out["ic_inf"], out["ic_sup"] = _wilson(out["registros_izabal"], out["registros_total"])
```

**Nivel de agregación:** frontera × mes → agregado por frontera (total o por año).
**Unidad:** proporción (0–1) y porcentaje.
**Fuentes:** `BD_COMPLEMENTARIA` (hoja única), columnas `frontera_nombre`,
`total_visitantes`, `nuevo_destino`, `id_unico`.
**Reglas y exclusiones:**
- Solo registros con `validacion` no nula (encuesta válida).
- La migración del mismo período se **adjunta como contexto absoluto**
  (`migracion_visitantes`, `migracion_transito`) en los meses en que la encuesta
  operó en esa frontera; **nunca se divide por ella** (regla 6: sin factor de
  expansión no se convierte una proporción en un total).
- Se reporta el **intervalo de Wilson al 95%** porque el tamaño de muestra varía
  mucho entre fronteras (de 1 a 1,841 questionnaires).

> **Nota sobre una fórmula descartada.** Una primera versión de este documento
> proponía `Tasa(b) = VisitantesEncuesta_Izabal(b) / VisitantesMigración(b)`.
> Se descartó por inválida: divide una **muestra** entre un **conteo absoluto**,
> así que el resultado depende del factor de muestreo de cada frontera y no está
> acotado a [0,1]. La implementación adoptada es una proporción dentro de la
> misma fuente.

### 4.3 La cadena de conectividad fluvial

El destino no se recibe de una sola puerta: se reparte en una **cadena de
nodos**. La tabla `survey_border_node_flow` cruza la frontera de entrada con el
nodo del corredor de destino:

| Frontera de entrada | Nodo principal | Peso dentro de esa frontera | Nodo de agua |
|---|---|---|---|
| El Florido | **Río Dulce** | 72.6% | Sí |
| La Ermita (Nueva Anguiatú) | Izabal (genérico) | 52.7% | No |
| Melchor de Mencos | **Río Dulce** | 54.5% | Sí |
| El Carmen | **Puerto Barrios** | 69.5% | Sí |
| San Cristóbal | **Puerto Barrios** | 39.7% | Sí |
| La Mesilla | **Puerto Barrios** | 54.5% | Sí |
| Valle Nuevo | **Río Dulce** | 36.4% | Sí |

Se lee una estructura territorial clara: **las fronteras del nororiente
(El Florido, La Ermita, Melchor de Mencos) alimentan Río Dulce**, mientras que
**las del sur (El Carmen, San Cristóbal, La Mesilla) alimentan Puerto Barrios**.
Río Dulce concentra el **51.4%** de los registros de la muestra del destino,
seguido de Izabal genérico (19.3%) y Puerto Barrios (18.7%).

**Las fronteras de Puerto Barrios son también las que más cargaier brings de
Río Dulce y Livingston**: El Florido → Puerto Barrios 104 registros y → Livingston
31; Melchor de Mencos → Puerto Barrios 70. Es la evidencia de que el puerto
fluvial de Puerto Barrios funciona como **nodo de redistribución**, no solo como
destino.

### 4.4 Cómo se llega a cada nodo, y el límite de lo medible

| Nodo | Modo dominante | Participación | Evidencia de la asimetría |
|---|---|---|---|
| Río Dulce | Bus Turístico | 57% | Flujo turístico organizado |
| Puerto Barrios | Vehículo | 58% | Vehículo particular, bus regional (18%) y trailer (12%) |
| Livingston | Bus Turístico | 60% | Flujo turístico, mayormente aéreo (12%) y bus (20%) |

**Limitación estructural declarada:** la taxonomía de transporte de la encuesta
tiene **11 categorías y ninguna es acuática** (verificado sobre las 227,347
filas: `Vehículo`, `Bus Regional`, `Bus Turístico`, `Taxi`, `Avión`, `A Pie`,
`Moto`, `Trailer`, `Moto Taxi`, `Otro`, `Otros`). Por tanto **la conectividad
fluvial no puede medirse como modo de transporte**, sino como **cadena espacial
de nodos**. El tramo de río y de mar del corredor se infiere de la estructura
nodo-frontera, no de un medio de transporte declarado.

### 4.5 Cuellos de botella del corredor

**El tránsito es estructural, no estacional.** El tránsito mensual agregado de
las tres fronteras marítimas (2023-01 → 2026-06, 20,766 viajeros, media 494/mes)
tiene un **coeficiente de variación de 0.22**, con mínimo en **octubre** (índice
estacional 0.58) y máximo en **abril** (1.26). No es el patrón de concentración
estival del visitante con pernocta: es una demanda de traslado y carga
permanente.

**La participación de Izabal en el corredor solo es calculable en 2009–2016**,
cuando las cinco fronteras del corredor registraban visitantes. En 2017–2026 solo
Mundo Maya tiene registro, por lo que la participación queda **vacía** y no en
cero (regla 1). El corredor completo se reporta en 95 de 96 meses de esa ventana:
en 2010-04 falta Santo Tomás.

### 4.6 Itinerarios multi-parada: un supuesto, no un hallazgo

El campo `otros_destinos` registra itinerarios de dos o más paradas con códigos
numéricos: `320` (903 registros), `320+340` (411), `222+320+340` (162),
`320+340+484` (26), etc. — **24,583 registros con dos o más paradas**.

Los códigos pertenecen a un catálogo por base (`BD` = V10, V11, V12) que **no
viene con diccionario**. La estructura de co-ocurrencia es consistente entre las
tres bases (el código `320` acompaña a destinos Izabal, Río Dulce y Puerto Barrios
en proporciones similares en V10, V11 y V12), lo que sugiere que `320` es un
código agrupador del departamento y `340` el de un nodo específico. **Pero la
inferencia no es concluyente**: varias lecturas son consistentes con los datos,
y `340` y `320` podrían ser Río Dulce y Livingston en cualquier orden.

**Decisión metodológica:** se reporta la **estructura de co-ocurrencia** (que es
un hecho) y **no se asignan nombres a los códigos** (que sería inventar). Pedir
el catálogo a INGUAT es una de las recomendaciones (§6).

### 4.7 Fichas técnicas de los indicadores del Módulo 4

| # | Indicador | Definición | Fórmula | Nivel | Unidad | Fuentes | Reglas |
|---|---|---|---|---|---|---|---|
| 1 | **Meses de solape** | Meses en que una frontera registra visitantes y tránsito simultáneamente | `card({meses_vis} ∩ {meses_tra})` | Frontera | Meses | Migración | Solo `Turista`/`Excursionista` vs `Viajero` |
| 2 | **Tasa de transferencia** | Proporción de visitantes que eligen Izabal/Caribe como destino en esa frontera | `Σ Izabal / Σ total` | Frontera × año | Proporción | Encuesta | Muestral; nunca × migración |
| 3 | **IC de Wilson 95%** | Intervalo de la tasa por tamaño de muestra | Wilson(k, n, 1.96) | Frontera | Proporción | Encuesta | `k` = questionnaires con destino Izabal |
| 4 | **Peso en el destino** | Cuota de la muestra de Izabal que entra por cada frontera | `registros_izabal / Σ` | Frontera | Proporción | Encuesta | Suma 1 por periodo |
| 5 | **Nodo principal** | Nodo del corredor con más registros de esa frontera | `argmax registros` | Frontera | Categoría | Encuesta | Empates resueltos por orden alfabético |
| 6 | **Modo dominante del nodo** | Medio de transporte con más registros hacia el nodo | `argmax registros` | Nodo | Categoría + % | Encuesta | Sin categoría acuática |
| 7 | **CV del tránsito** | Dispersión relativa del tránsito mensual | `σ / μ` | Corredor | Adimensional | Migración | Suma mensual antes de medir |
| 8 | **Participación del corredor** | Cuota de Izabal en el total de visitantes del corredor | `viajeros_izabal / viajeros_corredor` | Mes | Proporción | Migración | `NaN` si el corredor está incompleto |

---

## 5. Supuestos, limitaciones y calidad de las fuentes

### 5.1 Discontinuidades de cobertura (medidas)

| # | Limitación | Evidencia | Tratamiento |
|---|---|---|---|
| L1 | Los visitantes marítimos de Izabal se apagan en 2016 | 0 meses de solape entre visitantes y tránsito | Se documenta; no se calcula tasa de transferencia marítima |
| L2 | 2022 sin filas en las fronteras marítimas | 0 registros | Período sin dato, no con cero |
| L3 | Quiebre metodológico 2022→2023 en la base oficial | "los niveles no son perfectamente comparables" (hoja `Notas`) | Se analyses por tramos; las comparaciones interanuales 2025→2026 se marcan |
| L4 | Cambio de granularidad en `País` desde 2023 (226 países → 27 agrupaciones) | Hoja `Notas` | Los mercados principales siguen comparables; los pequeños quedan agrupados |
| L5 | `Viajero` contiene decimales: son estimaciones expandidas de encuesta, no conteos exactos | Hoja `Notas` | Se reportan como estimaciones |
| L6 | La encuesta no tiene factor de expansión | — | Solo proporciones y promedios ponderados (regla 6) |
| L7 | La encuesta no cubre fronteras marítimas | `frontera_nombre` solo con fronteras terrestres | Puerto Barrios y Livingston se analizan solo con la base oficial |
| L8 | La encuesta no tiene categoría de transporte acuático | 11 categorías, ninguna acuática | La conectividad fluvial se mide como cadena de nodos |
| L9 | La ocupación hotelera solo cubre 2023–2025 y no tiene inventario de establecimientos/habitaciones/plazas cama | 4 columnas en el CSV | **Gap de la capacidad instalada**: se documenta y se recomienda a INGUAT |
| L10 | Los códigos de `otros_destinos` no traen diccionario | 24,583 itinerarios multi-parada sin código legible | Se reporta co-ocurrencia, no se nombran |
| L11 | El mes 2025-01 no tiene ninguna encuesta de Izabal | 0 filas | Se imputa con el modelo ganador y se rotula "Estimación" |
| L12 | Los márgenes de error de la encuesta muestral son grandes | IC de Wilson por frontera | Se publican siempre junto a la tasa |
| L13 | Los nacionales (Guatemala) incorporan un factor de expansión distinto al de los extranjeros en la base de migración | Hoja `Notas` de la base oficial | Se reportan siempre en un ranking aparte (Módulo 1), nunca mezclados con el top de mercados extranjeros |
| L14 | **Diferencia de universos: hotelería formal vs. plataformas digitales.** El índice de ocupación de INGUAT cubre establecimientos formales registrados; no hay evidencia de que incluya oferta de plataformas como Airbnb | Las 4 columnas del CSV no distinguen tipo de establecimiento | No se estima la oferta informal; se documenta como universo no cubierto y se recomienda a INGUAT precisarlo |
| L15 | La guía advierte, para otras fuentes del curso, que los datos de 2026 pueden ser parciales (solo Q1) y repetir el valor del año anterior en parte de las combinaciones | **Verificado 2026-11-12** contra el archivo real: `indice_ocupacion_mensual_2023_2025_1.csv` tiene exactamente 792 filas (22 deptos × 36 meses) y **0 filas de 2026**. La advertencia de la guía no aplica a esta fuente para este grupo | El objetivo de imputación del Módulo 2 (ene-feb 2026) es un hueco real, no parcial; no requiere ajuste |

### 5.2 Tratamiento del problema de la capacidad instalada

El Módulo 3 de la guía requiere *"evolución anual (2022–2025) de establecimientos,
habitaciones y plazas cama departamentales"*. **La fuente disponible no contiene
esa información**: `indice_ocupacion_mensual_2023_2025_1.csv` tiene únicamente
`anio`, `mes`, `departamento` e `indice_ocupacion` (792 filas = 22 departamentos ×
36 meses).

**Decisión:** no se construye un proxy ni se estima un inventario. El gap se
documenta de forma visible en el dashboard y se convierte en la recomendación
explícita de **datos nuevos a incorporar** (§6).

---

## 6. Recomendaciones estratégicas y hoja de ruta para INGUAT

> Las cinco recomendaciones del Módulo 4 se **generan desde los datos**
> (`src/analysis/embudo.py`, función `recomendaciones_inguat`): el texto y su
> evidencia no pueden divergir.

| # | Prioridad | Recomendación | Evidencia |
|---|---|---|---|
| R1 | **Alta** | **Instrumentar el corredor fluvial con una serie única de visitantes.** Pedir una fuente que registre, para la misma frontera y el mismo mes, tanto el visitante (con o sin pernocta) como el tránsito, de modo que exista una tasa de transferencia oficial del corredor. | 287 meses con visitantes y 125 con tránsito en las 3 fronteras marítimas, pero **0 meses de solape**. |
| R2 | **Alta** | **Priorizar en El Florido y La Ermita** la señalización hacia el corredor fluvial y el transporte oficial: cualquier interceptor ahí afecta de forma desproporcionada a todo el destino. | Concentran el **80%** de la muestra de visitantes con destino Izabal/Caribe. |
| R3 | **Media** | **Tratar el corredor como dos ofertas distintas:** Río Dulce (gestión de buses turísticos y cupos) y Puerto Barrios (despacho de carga particular y trailer). | Río Dulce se alcanza en **Bus Turístico (57%)**; Puerto Barrios en **Vehículo (58%)**. |
| R4 | **Media** | **Planificar la capacidad de traslado de forma permanente**, no por temporadas. | El tránsito tiene **CV 0.22**, con mínimo en octubre: es demanda estructural, no estacional. |
| R5 | **Alta** | **Solicitar dos fuentes que hoy faltan:** (a) el catálogo de códigos de destino por base (V10/V11/V12) y (b) el inventario de establecimientos, habitaciones y plazas cama por departamento. | 24,583 itinerarios sin código legible; la capacidad instalada no es medible con la fuente actual. |

### Hoja de ruta sugerida

| Horizonte | Acción | Indicador de seguimiento |
|---|---|---|
| Inmediato | Solicitar a INGUAT el inventario hotelero y el catálogo de códigos | Datasets recibidos |
| 3 meses | Señalización y transporte oficial en El Florido y La Ermita | Tasa de transferencia de esas fronteras |
| 6 meses | Evaluar una serie instrumentada de visitantes + tránsito en el corredor | Meses de solape > 0 |
| 12 meses | Rediseñar la planificación de capacidad de traslado con base estacional | CV del tránsito |

---

## 7. Anexos técnicos y repositorio

### 7.1 Estructura del repositorio

Ver §2.3 de esta memoria y `README.md`.

### 7.2 Dependencias

`requirements.txt` — pandas ≥3.0, numpy ≥2.5, openpyxl, pyarrow, streamlit ≥1.40,
plotly ≥5.24, statsmodels ≥0.14, scipy, pytest ≥8.0.

### 7.3 Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.etl.pipeline        # genera data/processed/
streamlit run app/app.py
# o bien:
docker compose up --build         # dashboard en http://localhost:8501
```

Los datos **no se copian a la imagen**: se montan por volumen (`./data:/app/data`).

### 7.4 Fragmentos reproducibles

**Imputación del mes sin encuesta (2025-01):**

```python
from src.models import forecast as fc
enc = fc.serie_mensual_encuesta(encuesta_diaria)
estimado = fc.imputar_mes(enc, "2025-01-01", "logit_ets",
                          transform="log", bounds=(0, np.inf), migracion=mig_feeders)
```

**Tasa de transferencia por frontera:**

```python
from src.etl.transform import survey_transfer_rate
tr = survey_transfer_rate(encuesta_limpia, migracion_limpia)
```

**Verificación del hallazgo central:**

```python
from src.etl.transform import maritime_flow_profile
perfil = maritime_flow_profile(migracion_limpia)
assert perfil.loc[perfil["es_destino_maritimo"], "meses_solape"].sum() == 0
```

### 7.5 Pruebas

```bash
pytest -q     # 107 pruebas
```

Cubren: esquema de las fuentes, definición de visitante, fórmula de estadía
ponderada, las 6 reglas metodológicas, límites del pronóstico ([0,1]), métricas
de error, mapeo de fronteras, tasa de transferencia, huecos del corredor y una
**prueba de humo del dashboard** que ejecuta cada página y sus selectores.

---

## 8. Investigación: qué es un Observatorio de Turismo Sostenible

### 8.1 Definición

Un Observatorio de Turismo (o Sistema de Inteligencia Turística) es una herramienta de
**gobernanza y conocimiento continuo**: recolecta, procesa, modela y visualiza datos
heterogéneos de un destino para que gestores públicos y privados decidan con evidencia,
no con intuición. No es un reporte estático ni un tablero corporativo de ventas — la
diferencia es el ciclo: un observatorio se actualiza y se vuelve a consultar, mes tras
mes, mientras que un reporte se entrega una vez y queda fijo.

### 8.2 Marcos de referencia

**INSTO** (*International Network of Sustainable Tourism Observatories*), la red de
observatorios de turismo sostenible de ONU Turismo (antigua OMT), fue creada en 2004
para apoyar el monitoreo sistemático, oportuno y regular del desempeño y el impacto del
turismo a nivel de destino. Sus miembros se comprometen a medir el impacto del turismo
en **11 áreas obligatorias** que cubren las dimensiones económica, ambiental y
socioeconómica — exactamente el espíritu detrás de las "seis dimensiones" que esta guía
retoma (demanda, oferta, movilidad, sostenibilidad, experiencia, capacidad predictiva).

**SEGITTUR** (Sociedad Mercantil Estatal para la Gestión de la Innovación y las
Tecnologías Turísticas, España) impulsa el modelo de **Destinos Turísticos Inteligentes
(DTI)** por encargo de la Secretaría de Estado de Turismo española. El modelo DTI se
basa en una metodología de **97 requisitos y 261 indicadores** distribuidos en cinco
ejes — gobernanza, innovación, tecnología, sostenibilidad y accesibilidad — pensada para
diagnosticar el estado de un destino y priorizar un plan de acción. El principio que
este proyecto adopta de SEGITTUR no es el volumen de indicadores (fuera de alcance para
un curso), sino la idea de **ficha técnica estandarizada por indicador** (ver
`docs/catalogo_indicadores.md`): cada métrica debe ser trazable a una fuente, una
fórmula y una regla de negocio, no a un número suelto en un gráfico.

### 8.3 Las seis dimensiones del observatorio y los cuatro módulos del proyecto

| Dimensión (INSTO / guía del curso) | Cómo la cubre este proyecto |
|---|---|
| 1. Demanda turística y mercados emisores | **Módulo 1**: visitantes, estadía ponderada, segmentación turista/excursionista, top 10 mercados |
| 2. Capacidad hotelera y oferta de alojamiento | **Módulo 3**: índice de ocupación, ventana coincidente con afluencia, subdestinos; se documenta como gap el inventario de establecimientos que ninguna fuente trae |
| 3. Movilidad y presión sobre el territorio en fechas críticas | **Módulo 2**: patrón semanal, lift de festividades, pronóstico de ocupación para 2026; **Módulo 4**: conectividad fluvial y cuellos de botella del corredor |
| 4. Sostenibilidad y percepción ciudadana comunitaria | Fuera del alcance de las 3 fuentes disponibles (ninguna mide percepción ciudadana ni huella ambiental); se señala como recomendación de datos a incorporar (§6) |
| 5. Experiencia y calidad de los servicios | Parcialmente cubierta por el hospedaje y el modo de transporte declarados en la encuesta (Módulos 1 y 4); no hay medición directa de satisfacción |
| 6. Capacidad analítica predictiva | **Módulo 2**: 4 modelos de pronóstico con backtest rolling-origin y métricas de error formales (MAPE/RMSE/MAE) |

Las dimensiones 4 y 5 quedan parcialmente abiertas porque ninguna de las tres fuentes
institucionales mide percepción, satisfacción o impacto ambiental directamente — es la
misma limitación de origen que obliga a documentar el gap de capacidad instalada en el
Módulo 3 (§5.2): el observatorio reporta lo que las fuentes permiten medir, y señala
explícitamente lo que no.

### 8.4 Referencias consultables

- UN Tourism (ONU Turismo). *International Network of Sustainable Tourism Observatories
  (INSTO)*.
  <http://www.unwto.org/sustainable-development/unwto-international-network-of-sustainable-tourism-observatories>
  (consultado 2026-11-12).
- UN Tourism. *INSTO — sitio de la red*. <http://insto.unwto.org/> (consultado 2026-11-12).
- SEGITTUR. *Los Sistemas de Inteligencia Turística en el ámbito de la Red de Destinos
  Turísticos Inteligentes*.
  <https://www.segittur.es/wp-content/uploads/2024/03/Informe-SIT-en-Red-DTI.pdf>
  (consultado 2026-11-12).

---

*Documento generado a partir del análisis directo de `data/raw/`. Si una cifra no
se reproduce con los comandos del §7, hay que corregir este documento antes de
entregarlo.*
