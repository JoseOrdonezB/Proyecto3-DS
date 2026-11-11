# Asignación de módulos — Grupo 5

**Destino:** Río Dulce y Livingston, Izabal · **Reto:** Conectividad Fluvial y Embudo de Transferencia
**Curso:** CC3084 Data Science · UVG · Semestre II 2026

| Módulo | Responsable | Alcance | Entregables clave |
|---|---|---|---|
| **M1** Monitor de Demanda y Mercados Emisores | _completar nombre_ | KPIs (visitantes/mes, días-persona, estadía ponderada), segmentación turista/excursionista, top 10 nacionalidades | `survey_segment_tourist_excursionist`, `survey_days_person_monthly`, página 1 |
| **M2** Dinámica Temporal, Eventos y Pronóstico | _completar nombre_ | Calendario de feriados con Lift, patrón semanal normalizado, sistema de pronóstico + backtest + métricas | `src/models/forecast.py`, `src/analysis/feriados.py`, página 2 |
| **M3** Oferta Hotelera y Desagregación Territorial | _completar nombre_ | Ocupación 2023-2025, ventana coincidente con cruce real, subdestinos, documentación del gap de capacidad instalada | `occupancy_vs_affluence`, página 3, sección de limitaciones |
| **M4** Conectividad Fluvial y Embudo de Transferencia | _completar nombre_ | Tasa de transferencia por frontera, flujo turístico vs comercial, conectividad fluvial, recomendaciones INGUAT | `src/analysis/embudo.py`, `survey_transfer_rate`, página 4 |
| **Transversal** | todos | Paleta y teoría del color, memoria técnica, notebooks | `docs/`, `notebooks/` |

## Dependencias
- **M2** es el camino crítico (el pronóstico bloquea la página 2): arranca primero.
- **M1, M3 y M4** son independientes entre sí y pueden avanzar en paralelo.

## Reglas comunes
Las 6 reglas metodológicas del README aplican a todos los módulos. `data/` nunca se sube al repositorio, y el repositorio debe ser **privado**.
