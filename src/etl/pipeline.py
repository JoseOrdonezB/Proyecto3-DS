"""Orquestador del pipeline ETL.

Ejecuta: carga -> limpieza -> transformación -> guardado.

Uso:
    python -m src.etl.pipeline
"""

from pathlib import Path

import pandas as pd

from src.config import (
    DATA_PROCESSED,
    ISABAL_FEEDER_BORDERS,
    VISITOR_TYPES,
)
from src.etl.clean import clean_migration, clean_occupancy, clean_survey
from src.etl.load import load_migration, load_occupancy, load_survey
from src.etl import transform as t
from src.models import forecast as fc
from src.analysis import embudo as e


def run(save: bool = True, output_dir: Path | str | None = None) -> dict:
    """Ejecuta el pipeline completo y devuelve los DataFrames resultantes."""
    output_dir = Path(output_dir) if output_dir else DATA_PROCESSED
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Carga
    mig_raw = load_migration()
    occ_raw = load_occupancy()
    sur_raw = load_survey()

    # 2. Limpieza
    mig = clean_migration(mig_raw)
    occ = clean_occupancy(occ_raw)
    sur = clean_survey(sur_raw)

    # 3. Transformación
    outputs = {
        # Migración oficial (conteos absolutos)
        "migration_monthly.parquet": t.migration_monthly(mig),
        "destination_monthly.parquet": t.destination_monthly(mig),
        "destination_transit_monthly.parquet": t.destination_transit_monthly(mig),
        "destination_cruise_monthly.parquet": t.destination_cruise_monthly(mig),
        "nationality_top.parquet": t.nationality_top(mig),
        "corridor_monthly.parquet": t.corridor_monthly(mig),
        "corridor_transit_monthly.parquet": t.corridor_transit_monthly(mig),
        "corridor_share.parquet": t.corridor_share(mig),
        # Ocupación hotelera
        "occupancy_monthly.parquet": t.occupancy_series(occ),
        # Encuesta (muestral, sin factor de expansión)
        "survey_daily.parquet": t.survey_daily(sur),
        "survey_izabal_daily.parquet": t.survey_izabal_daily(sur),
        "survey_funnel.parquet": t.survey_funnel(sur),
        "survey_subdestino.parquet": t.survey_subdestino(sur),
        "survey_stay.parquet": t.survey_stay(sur),
        "survey_stay_izabal.parquet": t.survey_stay_izabal(sur),
        "survey_lodging.parquet": t.survey_lodging(sur),
        "survey_transport.parquet": t.survey_transport(sur),
        "survey_residence.parquet": t.survey_residence(sur),
        # Fase 2 · transformaciones transversales
        "survey_segment.parquet": t.survey_segment_tourist_excursionist(sur),
        "survey_days_person_monthly.parquet": t.survey_days_person_monthly(sur),
        "survey_izabal_cube.parquet": t.survey_izabal_cube(sur),
        "survey_weekly_pattern.parquet": t.survey_weekly_pattern(sur),
        "survey_holiday_lift.parquet": t.survey_holiday_lift(sur),
        "survey_border_migration.parquet": t.survey_border_migration(sur, mig),
        "survey_transfer_rate.parquet": t.survey_transfer_rate(sur, mig),
        "survey_border_node_flow.parquet": t.survey_border_node_flow(sur),
        "survey_node_transport.parquet": t.survey_node_transport(sur),
        "maritime_flow_profile.parquet": t.maritime_flow_profile(mig),
        "survey_itinerarios.parquet": e.perfil_itinerarios(sur),
        "corridor_funnel_matrix.parquet": t.corridor_funnel_matrix(mig),
        "migration_seasonal_index.parquet": t.migration_seasonal_index(mig),
        "occupancy_vs_affluence.parquet": t.occupancy_vs_affluence(occ, sur, mig),
        "occupancy_departments.parquet": occ[["fecha", "departamento", "indice_ocupacion"]]
        .sort_values(["departamento", "fecha"])
        .reset_index(drop=True),
        # Calidad de datos (limitaciones documentadas)
        "data_quality.parquet": t.data_quality(mig, sur),
    }

    # 3b. Pronóstico (Módulo 2). M3 usa la migración de las 9 fronteras
    # alimentadoras de Izabal (ISABAL_FEEDER_BORDERS): son las que registran
    # visitantes con destino Izabal en la encuesta y tienen serie continua
    # 2009-2026, a diferencia de las marítimas (que se apagan en 2016).
    feeders = ISABAL_FEEDER_BORDERS
    mig_feeders = fc.serie_mensual_migracion(
        outputs["migration_monthly.parquet"], feeders, VISITOR_TYPES
    )
    outputs.update(
        fc.generar_salidas(
            outputs["occupancy_monthly.parquet"],
            outputs["survey_izabal_daily.parquet"],
            migracion=mig_feeders,
        )
    )

    # 4. Guardado (parquet + copia csv para inspección)
    if save:
        for nombre, df in outputs.items():
            df.to_parquet(output_dir / nombre, index=False)
            df.to_csv(output_dir / nombre.replace(".parquet", ".csv"), index=False)

    return outputs


if __name__ == "__main__":
    resultados = run()
    print("=" * 60)
    print("Pipeline ETL completado")
    print("=" * 60)
    for nombre, df in resultados.items():
        print(f"{nombre:38s} {df.shape[0]:>8,} filas x {df.shape[1]} cols")
    print("=" * 60)
    print(f"Salida: {DATA_PROCESSED}")
