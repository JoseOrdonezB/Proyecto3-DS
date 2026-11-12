"""Regla 1 en la participación del corredor (corrección de la Fase 4).

`corridor_share` calculaba la participación de Izabal en el corredor rellenando
con 0 los meses sin registro, lo que producía 107 filas que se leían como
"0 % de participación" cuando en realidad no había dato de visitantes de Izabal.

La regla estricta del proyecto dice: la ausencia de dato NO es cero.
Estas pruebas fijan ese contrato.
"""

import numpy as np
import pandas as pd

from src.config import IZABAL_BORDERS


def test_izabal_sin_dato_no_aparece_como_cero(outputs):
    """Desde 2017 Izabal no registra visitantes: debe quedar vacío, no en cero."""
    cs = outputs["corridor_share.parquet"]
    cs = cs.assign(fecha=pd.to_datetime(cs["fecha"]))
    sin_dato = cs[cs["fecha"] >= "2017-01-01"]
    assert not sin_dato.empty, "Debería haber meses posteriores a 2016 en el corredor."
    assert not (sin_dato["viajeros_izabal"] == 0).any(), (
        "Hay meses con 0 visitantes de Izabal: es ausencia de dato, no un cero real."
    )
    assert sin_dato["viajeros_izabal"].isna().all()


def test_participacion_vacia_sin_izabal(outputs):
    """Sin dato de Izabal, la participación no puede calcularse."""
    cs = outputs["corridor_share.parquet"]
    cs = cs.assign(fecha=pd.to_datetime(cs["fecha"]))
    sin_dato = cs[cs["fecha"] >= "2017-01-01"]
    assert sin_dato["participacion"].isna().all()


def test_participacion_calculada_solo_con_corredor_completo(outputs):
    """Con una frontera faltando, numerador y denominador están sesgados."""
    cs = outputs["corridor_share.parquet"]
    con_dato = cs[cs["participacion"].notna()]
    assert con_dato["corredor_completo"].all()
    incompleto = cs[~cs["corredor_completo"]]
    assert incompleto["participacion"].isna().all()


def test_ventana_2009_2016_tiene_participacion(outputs):
    """La ventana con las 5 fronteras del corredor debe sí tener participación.

    Hay una excepción real en los datos: 2010-04 tiene solo 4 de las 5 fronteras
    con registro (Santo Tomás no reporta ese mes). Ese mes debe quedar vacío y
    marcado como corredor incompleto, no rellenado con cero.
    """
    cs = outputs["corridor_share.parquet"]
    cs = cs.assign(fecha=pd.to_datetime(cs["fecha"]))
    v = cs[cs["fecha"].between("2009-01-01", "2016-12-01")]
    completo = v[v["corredor_completo"]]
    incompleto = v[~v["corredor_completo"]]

    assert len(completo) >= 95, "La ventana 2009-2016 debe tener el corredor completo."
    assert completo["participacion"].notna().all()
    assert completo["participacion"].between(0, 1).all()

    for _, fila in incompleto.iterrows():
        assert np.isnan(fila["participacion"]), (
            f"{fila['fecha'].date()}: con corredor incompleto la participación no se calcula."
        )
        assert fila["n_fronteras_con_dato"] < 5


def test_conteo_de_fronteras_coherente(outputs):
    """n_fronteras_con_dato cuenta fronteras, no columnas derivadas."""
    cs = outputs["corridor_share.parquet"]
    assert cs["n_fronteras_con_dato"].between(1, 5).all()
    assert (cs["corredor_completo"] == cs["n_fronteras_con_dato"].eq(5)).all()


def test_corredor_total_nunca_cero_sin_dato(outputs):
    """Un mes sin ninguna frontera con registro no puede reportarse con total 0."""
    cs = outputs["corridor_share.parquet"]
    assert not (cs["viajeros_corredor"] == 0).any()
