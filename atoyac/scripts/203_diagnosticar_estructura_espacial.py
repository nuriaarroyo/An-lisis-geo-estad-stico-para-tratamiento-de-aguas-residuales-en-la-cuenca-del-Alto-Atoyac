"""Diagnósticos espaciales independientes de las características económicas."""

from importlib import import_module

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
from sklearn.neighbors import KernelDensity

comun = import_module("200_parte2_comun")


def hexagono(cx, cy, radio):
    angulos = np.deg2rad(np.arange(0, 360, 60))
    return Polygon([(cx + radio * np.cos(a), cy + radio * np.sin(a)) for a in angulos])


def grilla_hexagonal(puntos, radio):
    xmin, ymin, xmax, ymax = puntos.total_bounds
    dx, dy = 1.5 * radio, np.sqrt(3) * radio
    geometrias = []
    x, columna = xmin - radio, 0
    while x <= xmax + radio:
        y = ymin - radio + (columna % 2) * dy / 2
        while y <= ymax + radio:
            geometrias.append(hexagono(x, y, radio))
            y += dy
        x += dx
        columna += 1
    grid = gpd.GeoDataFrame({"hex_id": range(len(geometrias))}, geometry=geometrias, crs=puntos.crs)
    join = gpd.sjoin(puntos[["geometry"]], grid, predicate="within", how="left")
    conteos = join.groupby("index_right").size()
    grid["n_establecimientos"] = grid.index.map(conteos).fillna(0).astype(int)
    grid["radio_m"] = radio
    return grid[grid["n_establecimientos"].gt(0)].copy()


def main():
    comun.asegurar_directorios()
    puntos = comun.leer_puntos_metricos()
    xy = np.c_[puntos.geometry.x, puntos.geometry.y]
    tree = cKDTree(xy)
    filas = []
    for k in [2, 3, 5, 10, 15, 20, 30, 50]:
        distancias, _ = tree.query(xy, k=k)
        kth = distancias[:, -1]
        for q in [0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]:
            filas.append({"k": k, "cuantil": q, "distancia_m": float(np.quantile(kth, q))})
    comun.guardar_csv(pd.DataFrame(filas), comun.OUT / "03_diagnosticos/distancias_k_vecinos.csv")

    gpkg = comun.OUT / "03_diagnosticos/diagnosticos_territoriales.gpkg"
    for radio in [250, 500, 1000]:
        grid = grilla_hexagonal(puntos, radio)
        grid.to_file(gpkg, layer=f"hex_radio_{radio}m", driver="GPKG")

    xmin, ymin, xmax, ymax = puntos.total_bounds
    paso = 250
    xs = np.arange(xmin, xmax + paso, paso)
    ys = np.arange(ymin, ymax + paso, paso)
    xx, yy = np.meshgrid(xs, ys)
    muestra = np.c_[xx.ravel(), yy.ravel()]
    kde_filas = []
    for ancho in [500, 1000, 2000]:
        modelo = KernelDensity(bandwidth=ancho, kernel="gaussian").fit(xy)
        densidad = np.exp(modelo.score_samples(muestra)) * 1_000_000
        kde_filas.append(gpd.GeoDataFrame(
            {"bandwidth_m": ancho, "densidad_est_km2": densidad},
            geometry=gpd.points_from_xy(muestra[:, 0], muestra[:, 1]), crs=puntos.crs,
        ))
    pd.concat(kde_filas, ignore_index=True).to_csv(
        comun.OUT / "03_diagnosticos/kde_grilla.csv.gz", index=False, compression="gzip"
    )
    print(f"Diagnósticos generados para {len(puntos):,} puntos.")


if __name__ == "__main__":
    main()
