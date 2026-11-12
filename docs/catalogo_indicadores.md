# Catálogo formal de indicadores y métricas

## Observatorio de Inteligencia Turística — Grupo 5 (Río Dulce y Livingston, Izabal)

**Curso:** CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II 2026
**Alcance:** ficha técnica (8 campos, según la guía oficial) de cada indicador visualizado
en el dashboard, agrupadas por módulo.

> Formato de cada ficha: **1. Nombre** (encabezado) · **2. Definición de negocio** ·
> **3. Fórmula matemática formal** · **4. Implementación en código** · **5. Nivel de
> agregación y granularidad** · **6. Unidad de medida** · **7. Fuentes de datos de
> origen** · **8. Reglas de negocio y exclusiones**.

---

## Índice

- [Módulo 1 — Monitor de Demanda y Mercados Emisores](#módulo-1--monitor-de-demanda-y-mercados-emisores)
- [Módulo 2 — Dinámica Temporal, Eventos y Pronóstico](#módulo-2--dinámica-temporal-eventos-y-pronóstico)
- [Módulo 3 — Oferta Hotelera y Desagregación Territorial](#módulo-3--oferta-hotelera-y-desagregación-territorial)
- [Módulo 4 — Conectividad Fluvial y Embudo de Transferencia](#módulo-4--conectividad-fluvial-y-embudo-de-transferencia)

---

## Módulo 1 — Monitor de Demanda y Mercados Emisores

### 1. Visitantes totales de la muestra (por mes)

- **Definición de negocio:** cuántas personas registra la encuesta con destino
  Izabal/Caribe cada mes; mide el volumen de demanda muestral que llega al destino.
- **Fórmula matemática formal:** `Visitantes(mes) = Σ total_visitantes` (filas con
  `nuevo_destino = 'Izabal/Caribe'` y `fecha ∈ mes`).
- **Implementación en código:** `cubo.groupby("fecha")["visitantes"].sum()`
  (`src/etl/transform.py::survey_izabal_cube`, consumida en `app/pages/1_monitor_demanda.py`).
- **Nivel de agregación y granularidad:** registro de encuesta (grupo de viaje) → destino-mes.
- **Unidad de medida:** personas (muestra, sin factor de expansión).
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA` (parquet), columnas `fecha`,
  `nuevo_destino`, `total_visitantes`, `validacion`.
- **Reglas de negocio y exclusiones:** solo registros con `validacion` no nula; es una
  cifra muestral y **nunca** se multiplica por un factor de expansión (regla 6).

### 2. Proporción de pernocta (Turista vs. Excursionista)

- **Definición de negocio:** qué parte de los visitantes se queda a dormir (Turista)
  frente a quienes solo pasan por el destino (Excursionista); diagnostica si la demanda
  es de paso o de estadía.
- **Fórmula matemática formal:**
  `Proporción_pernocta = Σ visitantes_pernocta / (Σ visitantes_pernocta + Σ visitantes_excursionistas)`.
- **Implementación en código:** `g["proporcion_pernocta"] = g["visitantes_pernocta"] / (g["visitantes_pernocta"] + g["visitantes_excursionistas"])`
  (`src/etl/transform.py::survey_days_person_monthly`).
- **Nivel de agregación y granularidad:** registro de encuesta → destino-mes (o
  agregado al período filtrado en el dashboard).
- **Unidad de medida:** proporción (0–1) / porcentaje.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA`, columnas `estadia`, `noches`,
  `total_visitantes` (bandera `es_pernocta` calculada en `src/etl/clean.py`).
- **Reglas de negocio y exclusiones:** Turista = pernocta > 1 día; Excursionista (< 24 h)
  tiene permanencia 1 por definición y no debe distorsionar la pernocta.

### 3. Estadía media ponderada

- **Definición de negocio:** cuántas noches se queda, en promedio, un visitante que
  pernocta en Izabal; es el indicador de referencia de la guía para medir permanencia
  sin sesgo.
- **Fórmula matemática formal:**
  `Estadía_media_ponderada = Σ días-persona / Σ visitantes`, calculada **exclusivamente**
  sobre el segmento con pernocta > 1 día.
- **Implementación en código:**
  `dias_persona = (pernocta["noches_validadas"] * pernocta["total_visitantes"]).sum(); safe_div(dias_persona, visitantes)`
  (`src/etl/transform.py::_survey_stay_segment`, usada por `survey_stay_izabal`).
- **Nivel de agregación y granularidad:** registro de encuesta → destino-mes → agregado
  del período.
- **Unidad de medida:** días (noches) por visitante.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA`, columnas `estadia`, `noches`,
  `total_visitantes`.
- **Reglas de negocio y exclusiones:** se excluyen los excursionistas (< 24 h); **nunca**
  se promedia la columna de permanencia directamente (regla 2) — se pondera por
  días-persona sobre visitantes.

### 4. Días-persona mensuales

- **Definición de negocio:** la "carga" real de pernoctaciones que recibe el destino
  cada mes (no cuántas personas llegan, sino cuántas noches-persona generan).
- **Fórmula matemática formal:** `Días-persona(mes) = Σ (noches_validadas × total_visitantes)`,
  solo sobre el segmento con pernocta.
- **Implementación en código:** `dias_persona=("dias_persona", "sum")`
  (`src/etl/transform.py::survey_days_person_monthly`).
- **Nivel de agregación y granularidad:** registro de encuesta (día) → destino-mes.
- **Unidad de medida:** días-persona.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA`, columnas `fecha`, `noches`,
  `total_visitantes`.
- **Reglas de negocio y exclusiones:** no se suma la base diaria directamente para
  obtener el mes sin pasar por este agregado (regla 3); solo segmento con pernocta.

### 5. Top 10 mercados emisores (nacionales y extranjeros por separado)

- **Definición de negocio:** de qué países (o departamentos de residencia) vienen los
  visitantes de Izabal, para priorizar promoción por mercado.
- **Fórmula matemática formal:** `Ranking(país) = Σ visitantes`, ordenado descendente,
  con los 10 primeros de cada grupo (`Nacional` / `Extranjero`).
- **Implementación en código:**
  `grupo.groupby(["País","es_nacional"]).agg(viajeros=("Viajero","sum")); grupo[grupo["rank"] <= 10]`
  (`src/etl/transform.py::nationality_top`); en el dashboard, el ranking muestral
  equivalente usa `cubo.groupby(["nacionalidad","residencia"])["visitantes"].sum()`.
- **Nivel de agregación y granularidad:** migración: país-mes → top 10 del período
  2009–2026; encuesta: nacionalidad/residencia → top 10 del período filtrado.
- **Unidad de medida:** personas (migración, absoluto) / % de la muestra (encuesta).
- **Fuentes de datos de origen:** `Base_Migracion_2009-2026jun.xlsx` (`País`,
  `Tipo de Viajero`, `Viajero`); `BD_COMPLEMENTARIA` (`nacionalidad`, `residencia`).
- **Reglas de negocio y exclusiones:** los nacionales (Guatemala) se reportan **aparte**
  porque incorporan un factor de expansión distinto al de los extranjeros; no se mezclan
  en el mismo ranking.

### 6. Visitantes de migración por las fronteras alimentadoras (contexto absoluto)

- **Definición de negocio:** cuánta gente entra al país por las 11 fronteras que la
  encuesta mapea 1:1 a Izabal, como contexto absoluto frente a la muestra.
- **Fórmula matemática formal:** `Visitantes(frontera, mes) = Σ Viajero`, con
  `Tipo de Viajero ∈ {Turista, Excursionista}` y `Frontera ∈ SURVEY_BORDER_MAP`.
- **Implementación en código:**
  `mm[mm["Frontera"].isin(SURVEY_BORDER_MAP.values()) & mm["Tipo de Viajero"].isin(VISITOR_TYPES)].groupby(["fecha","País"])["viajeros"].sum()`
  (`app/pages/1_monitor_demanda.py::migracion_alimentadoras`).
- **Nivel de agregación y granularidad:** frontera-mes → agregado por país o total.
- **Unidad de medida:** personas (absoluto).
- **Fuentes de datos de origen:** `Base_Migracion_2009-2026jun.xlsx` (`Frontera`,
  `Tipo de Viajero`, `País`, `Viajero`).
- **Reglas de negocio y exclusiones:** mide entradas al país por esas fronteras, **no**
  visitantes de Izabal; nunca se multiplica por la encuesta ni se usa para inflar la
  muestra (regla 6).

---

## Módulo 2 — Dinámica Temporal, Eventos y Pronóstico

### 7. Serie diaria de visitantes (encuesta, Izabal/Caribe)

- **Definición de negocio:** la única serie continua día a día del destino; permite ver
  tendencia y estacionalidad fina que la migración (mensual) no muestra.
- **Fórmula matemática formal:** `Visitantes(día) = Σ total_visitantes`
  (`nuevo_destino = 'Izabal/Caribe'`, agrupado por día).
- **Implementación en código:**
  `izabal.groupby("fecha", as_index=False).agg(registros=("id_unico","count"), visitantes=("total_visitantes","sum"))`
  (`src/etl/transform.py::survey_izabal_daily`).
- **Nivel de agregación y granularidad:** registro de encuesta → día.
- **Unidad de medida:** personas (muestra).
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA`, columnas `fecha`, `nuevo_destino`,
  `total_visitantes`.
- **Reglas de negocio y exclusiones:** no se suma la serie diaria para obtener el mes sin
  pasar por el agregado mensual (regla 3); los días sin encuesta no aparecen como fila
  (ausencia, no cero).

### 8. Patrón semanal normalizado

- **Definición de negocio:** qué día de la semana concentra más presión turística, para
  planificar personal, transporte y capacidad.
- **Fórmula matemática formal:**
  `Índice(día_semana) = promedio(visitantes | día_semana) / promedio(visitantes | todos los días activos)`.
- **Implementación en código:**
  `g["indice_visitantes"] = g["visitantes_promedio"] / media_vis`
  (`src/etl/transform.py::survey_weekly_pattern`).
- **Nivel de agregación y granularidad:** día (fecha) → día de la semana (agregado sobre
  todo el período con operativo).
- **Unidad de medida:** índice adimensional (1.00 = día típico).
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA`, columnas `fecha`, `total_visitantes`.
- **Reglas de negocio y exclusiones:** se normaliza por **promedio**, no por suma bruta,
  para que un mes con más sábados no infle el índice de ese día.

### 9. Lift de festividades

- **Definición de negocio:** cuánto sube (o baja) la demanda diaria en una festividad
  frente a un día regular, para anticipar presión en fechas críticas.
- **Fórmula matemática formal:**
  `Lift_%(evento) = (promedio(visitantes | evento) / promedio(visitantes | día regular del mismo período) − 1) × 100`.
- **Implementación en código:** `(prom_v / base_v - 1) * 100`
  (`src/etl/transform.py::survey_holiday_lift`).
- **Nivel de agregación y granularidad:** día → festividad (feriado o evento), por año y
  para el período completo (`anio = "Todos"`).
- **Unidad de medida:** porcentaje de variación.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA` (`fecha`, `total_visitantes`) +
  calendario de feriados de Guatemala (`src/analysis/feriados.py::calendario`).
- **Reglas de negocio y exclusiones:** "día regular" excluye feriados y eventos, y se
  compara contra los días regulares **del mismo período** (no un promedio histórico
  genérico), para no mezclar volúmenes de muestra distintos entre años.

### 10. Pronóstico de ocupación de Izabal (ene–feb 2026)

- **Definición de negocio:** estimación formal de la ocupación hotelera de Izabal en los
  dos meses de 2026 que la fuente no cubre (deliverable obligatorio de la guía).
- **Fórmula matemática formal:** modelo ganador por backtest; los dos candidatos
  principales son `ŷ = ilogit(ETS(logit(y)))` (Logit-ETS, con o sin tendencia amortiguada)
  y `ŷ_m = r_m × migración_m`, con `r_m = Σy / Σmigración` del mismo mes calendario
  (factor de reparto, método literal de la guía).
- **Implementación en código:**
  `fc.predecir(modelo, train, h, transform="logit", bounds=(0.0, 1.0), migracion=...)`
  (`src/models/forecast.py::predecir`, `pronostico`, `generar_salidas`).
- **Nivel de agregación y granularidad:** Izabal-mes.
- **Unidad de medida:** índice de ocupación, acotado a [0, 1].
- **Fuentes de datos de origen:** `indice_ocupacion_mensual_2023_2025_1.csv`
  (`indice_ocupacion`) + `Base_Migracion_2009-2026jun.xlsx` (fronteras alimentadoras,
  solo para el modelo de factor de reparto).
- **Reglas de negocio y exclusiones:** toda cifra se rotula **"Estimación"** (violeta,
  línea discontinua, marcador vacío); el modelo se elige por error medido en backtest,
  nunca por preferencia visual; ninguna predicción puede salir de [0, 1] (transformada
  logit).

### 11. Métricas de error del pronóstico (MAPE / RMSE / MAE)

- **Definición de negocio:** qué tanto se equivoca cada modelo candidato al predecir un
  mes por delante; sustenta cuál modelo se usa para el pronóstico oficial.
- **Fórmula matemática formal:**
  `MAPE = mean(|y − ŷ| / |y|)`, `RMSE = sqrt(mean((y − ŷ)²))`, `MAE = mean(|y − ŷ|)`,
  calculadas sobre los folds válidos del backtest rolling-origin (expanding window,
  horizonte de 1 mes).
- **Implementación en código:** `metricas_error(y_true, y_pred)`
  (`src/utils/helpers.py`), agregada por modelo en
  `src/models/forecast.py::metricas_backtest`.
- **Nivel de agregación y granularidad:** fold (fecha × modelo) → modelo × objetivo
  (ocupación / encuesta).
- **Unidad de medida:** MAPE en %; RMSE y MAE en unidades del índice de ocupación (o de
  visitantes, para la encuesta).
- **Fuentes de datos de origen:** resultado del backtest (`src/models/forecast.py::backtest`),
  no un archivo crudo.
- **Reglas de negocio y exclusiones:** un fold es inválido si no cumple la historia
  mínima (25 meses para los modelos ETS, 12 para los demás) o si el ajuste no converge;
  se reporta como excluido, nunca se fuerza a 0 ni se descarta en silencio.

---

## Módulo 3 — Oferta Hotelera y Desagregación Territorial

### 12. Índice de ocupación departamental (Izabal)

- **Definición de negocio:** qué tan llenos están los hoteles de Izabal mes a mes, según
  el índice oficial.
- **Fórmula matemática formal:** valor reportado por la fuente, reindexado a una serie
  mensual completa (`2023-01` → `2025-12`).
- **Implementación en código:** `izabal.reindex(indice_completo)`
  (`src/etl/transform.py::occupancy_series`).
- **Nivel de agregación y granularidad:** departamento-mes.
- **Unidad de medida:** índice de ocupación [0, 1] (%).
- **Fuentes de datos de origen:** `indice_ocupacion_mensual_2023_2025_1.csv`
  (`anio`, `mes`, `departamento`, `indice_ocupacion`).
- **Reglas de negocio y exclusiones:** los meses sin registro quedan en `NaN`, nunca en 0
  (regla 1).

### 13. Comparación interdepartamental de ocupación

- **Definición de negocio:** en qué posición queda Izabal frente a los demás
  departamentos, para contextualizar si su ocupación es alta o baja en términos
  relativos.
- **Fórmula matemática formal:**
  `Posición(depto) = rank(promedio(indice_ocupacion) de ese depto, descendente)`.
- **Implementación en código:**
  `dep.groupby("departamento")["indice_ocupacion"].mean().sort_values(ascending=False)`
  (`app/pages/3_oferta_hotelera.py`).
- **Nivel de agregación y granularidad:** departamento (agregado 2023–2025).
- **Unidad de medida:** índice [0, 1] y posición ordinal (#).
- **Fuentes de datos de origen:** igual que el indicador 12, todos los departamentos.
- **Reglas de negocio y exclusiones:** ninguna (la serie de ocupación está completa para
  los 22 departamentos en el rango 2023–2025).

### 14. Cruce ocupación–afluencia en la ventana coincidente (correlación)

- **Definición de negocio:** si la afluencia medida (por la encuesta o por migración)
  explica la ocupación hotelera, para decidir si conviene usarla como variable
  predictiva.
- **Fórmula matemática formal:** coeficientes de Pearson `r` y Spearman `ρ` entre
  `indice_ocupacion` y la medida de afluencia elegida, sobre los meses en que **ambas**
  series tienen dato (ventana coincidente Sep–Dic 2025, u otra ventana ampliada).
- **Implementación en código:**
  `stats.pearsonr(pares_corr[col], pares_corr["ocupacion"])` y
  `stats.spearmanr(...)` (`app/pages/3_oferta_hotelera.py`, sobre la tabla
  `src/etl/transform.py::occupancy_vs_affluence`).
- **Nivel de agregación y granularidad:** Izabal-mes, restringido a los meses con ambas
  fuentes observadas.
- **Unidad de medida:** coeficiente de correlación (−1 a 1); la medida de afluencia
  puede ser proporción (%) o conteo, según la variable elegida.
- **Fuentes de datos de origen:** `indice_ocupacion_mensual...csv` + `BD_COMPLEMENTARIA`
  + `Base_Migracion...xlsx` (fronteras alimentadoras), cruzadas por mes.
- **Reglas de negocio y exclusiones:** el cruce se limita estrictamente a los meses con
  ambas series observadas; la encuesta (muestral) nunca se multiplica por la migración
  (regla 6) para construir la medida de afluencia.

### 15. Participación de subdestinos (sin sumar)

- **Definición de negocio:** a qué puntos dentro de Izabal va la gente (Río Dulce,
  Livingston, Puerto Barrios, Quiriguá, etc.), para priorizar inversión por subdestino.
- **Fórmula matemática formal:** `Participación(subdestino) = registros(subdestino) / Σ registros(período)`.
- **Implementación en código:** `por_sub = base.groupby("subdestino")["registros"].sum(); mostrar / total_sub`
  (`src/etl/transform.py::survey_subdestino`, consumida en `app/pages/3_oferta_hotelera.py`).
- **Nivel de agregación y granularidad:** registro de encuesta → subdestino, agregado
  por el período y segmento elegidos.
- **Unidad de medida:** % de la muestra.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA`, columna `destino` normalizada a
  `subdestino`.
- **Reglas de negocio y exclusiones:** los subdestinos **nunca** se suman entre sí para
  obtener el total de Izabal, porque un mismo visitante puede recorrer varios (regla 4).

> **Nota — capacidad instalada de alojamiento.** La guía pide la evolución anual
> 2022–2025 de establecimientos, habitaciones y plazas cama departamentales. Ninguna de
> las tres fuentes la contiene (`indice_ocupacion_mensual...csv` solo trae `anio`, `mes`,
> `departamento`, `indice_ocupacion`): no se documenta como ficha porque no existe un
> indicador que calcular. Se trata como limitación (§5 de `memoria_tecnica.md`) y como
> recomendación de datos a incorporar (§6).

---

## Módulo 4 — Conectividad Fluvial y Embudo de Transferencia

### 16. Meses de solape (embudo medible)

- **Definición de negocio:** en cuántos meses una frontera registra visitantes y
  tránsito a la vez; determina si esa frontera admite una tasa de transferencia
  calculable.
- **Fórmula matemática formal:** `Meses_solape(frontera) = |{meses con visitantes} ∩ {meses con tránsito}|`.
- **Implementación en código:** `src/etl/transform.py::maritime_flow_profile`.
- **Nivel de agregación y granularidad:** frontera (agregado sobre todo el histórico
  2009–2026).
- **Unidad de medida:** meses (conteo).
- **Fuentes de datos de origen:** `Base_Migracion_2009-2026jun.xlsx` (`Frontera`,
  `Tipo de Viajero`, `fecha`).
- **Reglas de negocio y exclusiones:** solo `Turista`/`Excursionista` cuentan como
  visitantes; solo `Viajero` cuenta como tránsito; no se mezclan con `Cruceristas`.

### 17. Tasa de transferencia por frontera

- **Definición de negocio:** de las personas que entran por una frontera terrestre y que
  la encuesta registra, qué proporción declara destino Izabal/Caribe; identifica qué
  fronteras vale la pena promocionar hacia el destino.
- **Fórmula matemática formal:**
  `Tasa(frontera) = Σ visitantes_con_destino_Izabal / Σ visitantes_totales_de_esa_frontera ∈ [0, 1]`.
- **Implementación en código:**
  `out["tasa_transferencia"] = out["visitantes_izabal"] / out["visitantes_total"]`
  (`src/etl/transform.py::survey_transfer_rate`).
- **Nivel de agregación y granularidad:** frontera × mes → agregado por frontera (total
  o por año).
- **Unidad de medida:** proporción (0–1) / porcentaje.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA` (`frontera_nombre`,
  `total_visitantes`, `nuevo_destino`), mapeada 1:1 a `Base_Migracion...xlsx`
  (`SURVEY_BORDER_MAP`).
- **Reglas de negocio y exclusiones:** es una proporción **dentro de la misma fuente**
  (muestral); la migración del mismo período se adjunta como contexto absoluto pero
  **nunca** se usa como denominador (regla 6).

### 18. Intervalo de Wilson al 95 % (de la tasa de transferencia)

- **Definición de negocio:** cuánta confianza merece la tasa de transferencia de cada
  frontera, dado que el tamaño de muestra varía mucho entre ellas.
- **Fórmula matemática formal:** intervalo de Wilson para una proporción binomial,
  `k` éxitos sobre `n` ensayos, `z = 1.96` (95 %).
- **Implementación en código:** `out["ic_inf"], out["ic_sup"] = _wilson(out["registros_izabal"], out["registros_total"])`
  (`src/etl/transform.py::survey_transfer_rate`).
- **Nivel de agregación y granularidad:** frontera (mismo nivel que el indicador 17).
- **Unidad de medida:** proporción (0–1), límite inferior y superior.
- **Fuentes de datos de origen:** igual que el indicador 17.
- **Reglas de negocio y exclusiones:** `k` = encuestas con destino Izabal; el caso `k = 0`
  se trata explícitamente para que el límite inferior sea 0 exacto, no ~1e-18.

### 19. Peso de cada frontera en el destino

- **Definición de negocio:** qué cuota de la muestra total de Izabal entra por cada
  frontera; distingue "mucha gente entra por aquí" de "mucha de la que entra aquí va a
  Izabal" (indicador 17).
- **Fórmula matemática formal:** `Peso(frontera) = registros_izabal(frontera) / Σ registros_izabal(todas las fronteras)`.
- **Implementación en código:** `src/etl/transform.py::survey_transfer_rate`
  (columna `peso_en_izabal`).
- **Nivel de agregación y granularidad:** frontera, por periodo.
- **Unidad de medida:** proporción (0–1); suma 1 dentro de cada periodo.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA` (`frontera_nombre`, `nuevo_destino`).
- **Reglas de negocio y exclusiones:** solo fronteras con equivalencia 1:1 a migración
  (`SURVEY_BORDER_MAP`); es muestral, no se extrapola a visitantes absolutos.

### 20. Nodo principal del corredor (por frontera)

- **Definición de negocio:** a qué nodo del corredor (Río Dulce, Puerto Barrios,
  Livingston, Izabal genérico) llega la mayoría de quienes entran por cada frontera.
- **Fórmula matemática formal:** `Nodo_principal(frontera) = argmax_nodo(registros(frontera, nodo))`.
- **Implementación en código:** `src/etl/transform.py::survey_border_node_flow`.
- **Nivel de agregación y granularidad:** frontera × nodo → nodo con más registros por
  frontera.
- **Unidad de medida:** categoría (nombre del nodo) + % de participación dentro de esa
  frontera.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA` (`frontera_nombre`, `subdestino`
  normalizado a nodo).
- **Reglas de negocio y exclusiones:** empates se resuelven por orden alfabético; los
  nodos no se suman entre sí (regla 4).

### 21. Modo de transporte dominante por nodo

- **Definición de negocio:** cómo llega la gente a cada nodo del corredor, para
  planificar transporte oficial y cupos.
- **Fórmula matemática formal:** `Modo_dominante(nodo) = argmax_modo(registros(nodo, tipo_transporte))`.
- **Implementación en código:** `src/etl/transform.py::survey_node_transport`.
- **Nivel de agregación y granularidad:** nodo × tipo de transporte → modo con más
  registros por nodo.
- **Unidad de medida:** categoría (modo de transporte) + % de participación.
- **Fuentes de datos de origen:** `BD_COMPLEMENTARIA` (`tipo_transporte`, subdestino
  normalizado a nodo).
- **Reglas de negocio y exclusiones:** la taxonomía de transporte no tiene categoría
  acuática (11 categorías, ninguna de lancha o barco); la conectividad fluvial se mide
  como cadena de nodos, no como modo de transporte.

### 22. Coeficiente de variación del tránsito del corredor

- **Definición de negocio:** si la demanda de traslado por el corredor marítimo se
  concentra en temporada o es permanente, para decidir si la capacidad se planifica por
  estación o todo el año.
- **Fórmula matemática formal:** `CV = σ(tránsito_mensual) / μ(tránsito_mensual)`.
- **Implementación en código:** `cv_tr = float(serie_tr.std() / serie_tr.mean())`
  (`app/pages/4_conectividad_fluvial.py`, sobre `destination_transit_monthly`).
- **Nivel de agregación y granularidad:** corredor (suma mensual de las 3 fronteras
  marítimas) → agregado 2023–jun 2026.
- **Unidad de medida:** adimensional (razón).
- **Fuentes de datos de origen:** `Base_Migracion_2009-2026jun.xlsx`, `Tipo de Viajero = 'Viajero'`.
- **Reglas de negocio y exclusiones:** se agrega por mes antes de medir (regla 3); no se
  mezcla con el visitante (`Turista`/`Excursionista`).

### 23. Participación de Izabal en el corredor completo

- **Definición de negocio:** qué cuota de los visitantes del corredor completo
  (Izabal + puntos de conexión) corresponde a Izabal, en la única ventana donde las 5
  fronteras del corredor son comparables.
- **Fórmula matemática formal:** `Participación(mes) = viajeros_Izabal(mes) / viajeros_corredor(mes)`.
- **Implementación en código:** `src/etl/transform.py::corridor_share`.
- **Nivel de agregación y granularidad:** corredor-mes.
- **Unidad de medida:** proporción (0–1).
- **Fuentes de datos de origen:** `Base_Migracion_2009-2026jun.xlsx`, fronteras de
  `CORRIDOR_BORDERS` (`src/config.py`).
- **Reglas de negocio y exclusiones:** si falta el dato de alguna frontera del corredor
  en ese mes, el resultado es `NaN`, nunca 0 (regla 1; corrección aplicada el
  2026-11-11 — ver `docs/PLAN.md` §9).

---

*Catálogo generado a partir del código vigente en `src/etl/transform.py`,
`src/models/forecast.py` y las páginas de `app/pages/`. Si una fórmula o un fragmento de
código no coincide con la implementación real, hay que corregir este documento antes de
entregarlo (ver nota de cierre de `docs/memoria_tecnica.md`).*
