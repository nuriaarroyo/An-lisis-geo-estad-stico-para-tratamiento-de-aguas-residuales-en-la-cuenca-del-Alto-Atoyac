"""Recupera la geometria DENUE por identificador y crea una capa final."""

from pathlib import Path
import re

import geopandas as gpd


def _normalizar_id(serie):
    return serie.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def crear_capa_desde_ids(
    data,
    capa_origen,
    output_path,
    layer_name,
    id_csv="d_llave",
    id_capa="id",
):
    """Une la geometria original a ``data`` mediante ID y escribe GeoPackage."""
    if id_csv not in data.columns:
        raise ValueError(f"El CSV no contiene la llave '{id_csv}'.")

    tabla = data.copy()
    tabla[id_csv] = _normalizar_id(tabla[id_csv])
    if tabla[id_csv].duplicated().any():
        raise ValueError(f"La llave '{id_csv}' contiene duplicados.")

    origen = gpd.read_file(capa_origen)
    if id_capa not in origen.columns:
        raise ValueError(f"La capa no contiene la llave '{id_capa}'.")
    origen[id_capa] = _normalizar_id(origen[id_capa])
    if origen[id_capa].duplicated().any():
        raise ValueError(f"La llave '{id_capa}' contiene duplicados en la capa.")

    geometria = origen[[id_capa, "geometry"]].rename(columns={id_capa: id_csv})
    resultado = geometria.merge(
        tabla,
        on=id_csv,
        how="right",
        validate="one_to_one",
    )
    sin_geometria = int(resultado.geometry.isna().sum())
    if sin_geometria:
        raise ValueError(
            f"{sin_geometria} identificadores del CSV no existen en la capa original."
        )

    resultado = gpd.GeoDataFrame(resultado, geometry="geometry", crs=origen.crs)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    layer_name = re.sub(r"[^a-zA-Z0-9_]", "_", layer_name)[:63]
    resultado.to_file(output_path, layer=layer_name, driver="GPKG")
    return resultado
