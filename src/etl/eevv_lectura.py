import io

import msoffcrypto
import pandas as pd

from src.etl.comun import cargar_config, ruta


def archivo(anio, config=None):
    config = config or cargar_config()
    carpeta = ruta(config, "raw") / "dane" / "eevv"
    return next(carpeta.glob(f"dane_eevv_defunciones_no_fetales_{anio}.xls*"))


def libro(anio, config=None):
    """Abre el cuadro del DANE en memoria; los .xls vienen con la clave de apertura por defecto de Excel y no se modifica data/raw."""
    f = archivo(anio, config)
    with open(f, "rb") as h:
        o = msoffcrypto.OfficeFile(h)
        if o.is_encrypted():
            o.load_key(password="VelvetSweatshop")
            b = io.BytesIO()
            o.decrypt(b)
            b.seek(0)
            return pd.ExcelFile(b)
    return pd.ExcelFile(f)
