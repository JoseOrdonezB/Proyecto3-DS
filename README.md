# 🧭 Observatorio de Inteligencia Turística — Grupo 5

**Destino:** Río Dulce y Livingston, Izabal
**Reto especializado:** Conectividad Fluvial y Embudo de Transferencia
**Curso:** CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II 2026

---

## 👥 Equipo y módulos

El dashboard tiene **4 módulos**, uno por integrante. Ver la asignación en
[`docs/asignacion_modulos.md`](docs/asignacion_modulos.md) y el plan maestro
completo en [`docs/PLAN.md`](docs/PLAN.md).

| Módulo | Responsable | Estado |
|---|---|---|
| 1. Monitor de Demanda y Mercados Emisores | Adrián Gonzales | ✅ En el dashboard |
| 2. Dinámica Temporal, Eventos y Pronóstico | José Anton | ✅ En el dashboard |
| 3. Oferta Hotelera y Desagregación Territorial | Gadiel Ocaña | ✅ En el dashboard |
| 4. Conectividad Fluvial y Embudo de Transferencia | José Ordoñez | ✅ En el dashboard |

> 📍 **Plan de trabajo y estado de avance:** [`docs/PLAN.md`](docs/PLAN.md)
> 📄 **Memoria técnica:** [`docs/memoria_tecnica.md`](docs/memoria_tecnica.md)
> 📇 **Catálogo de indicadores:** [`docs/catalogo_indicadores.md`](docs/catalogo_indicadores.md)
> 🎨 **Paleta y teoría del color:** [`docs/paleta_y_diseno.md`](docs/paleta_y_diseno.md)

---

## 📦 Fuentes de datos

| Fuente | Archivo | Contenido | Cobertura |
|---|---|---|---|
| Migración oficial | `data/raw/Base_Migracion_2009-2026jun.xlsx` | Conteos por frontera, mes, vía y tipo de viajero | ene 2009 – jun 2026 |
| Ocupación hotelera | `data/raw/indice_ocupacion_mensual_2023_2025_1.csv` | Índice de ocupación mensual por departamento | 2023 – 2025 |
| BD complementaria | `data/raw/BD_COMPLEMENTARIA` (parquet) | Encuesta diaria de turismo (sin factor de expansión) | oct 2021 – ago 2026 |

> 🔒 **Confidencialidad:** los datos son institucionales y se usan exclusivamente
> con fines académicos. La carpeta `data/` está ignorada por git (`.gitignore`).
> El repositorio debe ser **privado**.

### Limitaciones clave detectadas

- Las fronteras marítimas de Izabal (Puerto Barrios y Livingston) solo tienen
  **visitantes (Turista/Excursionista) entre 2009 y 2016**. De 2023 en adelante
  solo registran **"Viajero"** (tránsito / trasbordo). Los **cruceros** están
  presentes hasta 2022.
- La encuesta **no tiene factor de expansión**: se analiza únicamente como
  porcentajes muestrales (regla estricta del proyecto).
- La encuesta **no cubre fronteras marítimas**: Puerto Barrios y Livingston solo
  pueden analizarse con la base oficial de migración.

---

## 🗂️ Estructura del repositorio

```
Proyecto3-DS/
├── data/
│   ├── raw/                  # fuentes originales (ignoradas por git)
│   └── processed/            # salida del ETL (ignorada por git)
├── src/
│   ├── config.py             # rutas, constantes de negocio, paleta
│   ├── data.py               # carga de datos procesados
│   ├── etl/
│   │   ├── load.py           # carga por formato (xlsx, csv, parquet)
│   │   ├── clean.py          # limpieza y normalización
│   │   ├── transform.py      # transformaciones analíticas (28)
│   │   └── pipeline.py       # orquestador
│   ├── models/forecast.py    # 4 modelos + backtest rolling-origin
│   ├── analysis/
│   │   ├── feriados.py       # calendario de feriados de Guatemala
│   │   └── embudo.py         # composición analítica del Módulo 4
│   └── utils/helpers.py
├── app/
│   ├── app.py                # página principal
│   ├── pages/                # 4 módulos (uno por integrante)
│   ├── components/           # theme.py, charts.py, kpis.py, data.py
│   └── assets/style.css
├── notebooks/                # análisis exploratorio (01 calidad, 02 pronóstico,
│                             # 03 embudo, 04 ventana coincidente)
├── docs/
│   ├── PLAN.md                     # plan maestro y estado de avance
│   ├── asignacion_modulos.md
│   ├── memoria_tecnica.md          # entrega formal
│   ├── catalogo_indicadores.md     # ficha técnica (8 campos) de cada indicador
│   └── paleta_y_diseno.md          # paleta validada + teoría del color
├── tests/                    # 107 pruebas
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

---

## ⚙️ Instalación y ejecución

### Opción 1 — Local

```bash
# 1. Crear entorno (opcional pero recomendado)
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar el ETL (genera data/processed/)
python -m src.etl.pipeline

# 4. Levantar el dashboard
streamlit run app/app.py
```

Atajos con `Makefile`: `make install`, `make etl`, `make dashboard`, `make test`.

### Opción 2 — Docker

```bash
docker compose up --build
```

El dashboard quedará disponible en <http://localhost:8501>. Los datos se montan
por volumen (`./data:/app/data`), por lo que **no se copian al repositorio ni a
la imagen**.

---

## 🔁 Pipeline ETL

```bash
python -m src.etl.pipeline
```

1. **Load:** lee las tres fuentes (`.xlsx`, `.csv`, `.parquet`).
2. **Clean:** normaliza fechas y texto, aplica banderas de negocio.
3. **Transform:** construye las series y agregaciones del observatorio.
4. **Forecast:** 4 modelos comparados con backtest rolling-origin (§3 del plan).
5. **Save:** escribe `data/processed/*.parquet` y copias `.csv`.

Si el dashboard no encuentra `data/processed/`, ejecuta el pipeline
automáticamente.

### Hallazgos estructurales que condicionan el análisis

- El **corredor marítimo de Izabal no tiene embudo medible**: en Puerto Barrios,
  Livingston y Santo Tomás, los visitantes (2009-2016) y el tránsito (2023-2026)
  **nunca coinciden en un mismo mes** (0 meses de solape). El embudo medible es el
  terrestre, sobre las 9 fronteras alimentadoras.
- La encuesta **no tiene factor de expansión** y **no cubre fronteras marítimas**
  ni tiene categoría de transporte acuático.
- La fuente de ocupación **no contiene inventario de establecimientos**,
  habitaciones ni plazas cama: esa parte del Módulo 3 se documenta como
  limitación y se recomienda a INGUAT como dato a incorporar.

---

## 📐 Reglas metodológicas estrictas

1. **La ausencia de dato no es cero:** los períodos sin cobertura se muestran como vacíos o "Sin dato".
2. **Prohibido promediar la permanencia:** la estadía media se calcula como `suma(días-persona) / suma(visitantes)`, solo sobre el segmento > 1 día.
3. **No sumar la base diaria para obtener el mes:** la base diaria mide presencia por día.
4. **No sumar subdestinos para obtener el total:** los visitantes que recorren varios puntos se duplicarían.
5. **No mezclar aeronaves con personas:** magnitudes distintas, ejes distintos.
6. **No extrapolar encuestas a totales absolutos:** la encuesta se analiza como porcentajes muestrales.

---

## ✅ Pruebas

```bash
pytest -q
```

107 pruebas que validan el esquema de las fuentes, la definición de visitante, la
fórmula de estadía ponderada, las reglas estrictas (huecos conservados, no suma
de subdestinos, ausencia ≠ cero), los límites del pronóstico (dentro de
[0,1]), sus métricas de error, el mapeo 1:1 de fronteras, la tasa de
transferencia y una prueba de humo que ejecuta **cada página del dashboard y
sus selectores**.

---

## 📄 Entregables del curso

- Enlace al repositorio **privado** con docentes y auxiliares como colaboradores.
- Documento de **Memoria Técnica y Recomendaciones** (`docs/memoria_tecnica.md`).
