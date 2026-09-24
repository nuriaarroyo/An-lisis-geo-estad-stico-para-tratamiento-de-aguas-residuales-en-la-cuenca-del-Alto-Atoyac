"""Crea las geometrías geográficas y métricas para el análisis espacial."""

from importlib import import_module

import geopandas as gpd

comun = import_module("200_parte2_comun")


def main():
    comun.asegurar_directorios()
    tabla = comun.cargar_maestra()
    puntos = comun.puntos_desde_tabla(tabla)
    metricos = puntos.to_crs(comun.CRS_METRICO)
    destino = comun.OUT / "02_geometrias/establecimientos_parte2.gpkg"
    puntos.to_file(destino, layer="establecimientos_wgs84", driver="GPKG")
    metricos.to_file(destino, layer="establecimientos_utm14n", driver="GPKG")
    cuenca = gpd.read_file(comun.CUENCA).to_crs(comun.CRS_METRICO)
    cuenca.to_file(comun.OUT / "02_geometrias/contexto_parte2.gpkg", layer="cuenca_utm14n", driver="GPKG")
    resumen = {
        "crs_origen": comun.CRS_GEOGRAFICO,
        "crs_analisis": comun.CRS_METRICO,
        "n_puntos": len(metricos),
        "bounds_utm": list(map(float, metricos.total_bounds)),
        "coordenadas_finitas": bool(metricos.geometry.x.notna().all() and metricos.geometry.y.notna().all()),
    }
    comun.guardar_json(resumen, comun.OUT / "02_geometrias/resumen_geometrias.json")
    print(resumen)


if __name__ == "__main__":
    main()
