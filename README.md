# 🧭 Observatorio de Inteligencia Turística — Grupo 5

**Destino:** Río Dulce y Livingston, Izabal
**Reto especializado:** Conectividad Fluvial y Embudo de Transferencia
**Curso:** CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II 2026

---

## 👥 Equipo y módulos

El dashboard tiene **4 módulos**, uno por integrante. Ver la asignación en
[`docs/asignacion_modulos.md`](docs/asignacion_modulos.md).

| Módulo | Responsable |
|---|---|
| 1. Monitor de Demanda y Mercados Emisores | _por asignar_ |
| 2. Dinámica Temporal, Eventos y Pronóstico | _por asignar_ |
| 3. Oferta Hotelera y Desagregación Territorial | _por asignar_ |
| 4. Conectividad Fluvial y Embudo de Transferencia | _por asignar_ |

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
│   ├── config.py             # rutas y constantes de negocio
│   ├── data.py               # carga de datos procesados
│   ├── etl/
│   │   ├── load.py           # carga por formato (xlsx, csv, parquet)
│   │   ├── clean.py          # limpieza y normalización
│   │   ├── transform.py      # transformaciones analíticas
│   │   └── pipeline.py       # orquestador
│   ├── models/forecast.py    # pronóstico (Fase 3)
│   └── utils/helpers.py
├── app/
│   ├── app.py                # página principal
│   ├── pages/                # 4 módulos (uno por integrante)
│   ├── components/           # carga de datos y KPIs
│   └── assets/style.css
├── notebooks/                # análisis exploratorio
├── docs/
│   ├── Guia_Proyecto_Observatorio_Turistico_UVG.pdf
│   ├── asignacion_modulos.md
│   └── memoria_tecnica.md    # Fase 6
├── tests/
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
4. **Save:** escribe `data/processed/*.parquet` y copias `.csv`.

Si el dashboard no encuentra `data/processed/`, ejecuta el pipeline
automáticamente.

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

Validan el esquema de las fuentes, la definición de visitante, la fórmula de
estadía ponderada y las reglas estrictas (huecos conservados, no suma de
subdestinos, etc.).

---

## 📄 Entregables del curso

- Enlace al repositorio **privado** con docentes y auxiliares como colaboradores.
- Documento de **Memoria Técnica y Recomendaciones** (`docs/memoria_tecnica.md`).
