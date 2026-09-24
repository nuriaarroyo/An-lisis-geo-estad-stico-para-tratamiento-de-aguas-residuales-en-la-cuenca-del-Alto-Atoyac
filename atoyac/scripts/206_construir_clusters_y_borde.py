"""Materializa la solución principal, el ruido y las métricas de borde."""

from importlib import import_module

import geopandas as gpd
import numpy as np
import pandas as pd

comun = import_module("200_parte2_comun")


def main():
    comun.asegurar_directorios()
    principal, membresia = comun.leer_solucion_principal()
    persistencia = pd.read_csv(comun.OUT / "05_seleccion/persistencia_establecimientos.csv", dtype={"d_llave": str})
    puntos = comun.leer_puntos_metricos()
    puntos["d_llave"] = puntos["d_llave"].astype(str)
    columnas = membresia[["d_llave", "cluster", "probabilidad"]].merge(
        persistencia[["d_llave", "persistencia_territorial", "clase_persistencia"]],
        on="d_llave", validate="one_to_one",
    )
    puntos = puntos.merge(columnas, on="d_llave", validate="one_to_one")
    puntos["tipo_resultado_espacial"] = np.where(
        puntos.cluster.lt(0), "DISPERSO_RUIDO", "CONCENTRACION"
    )
    filas, geometrias = [], []
    for cluster, parte in puntos[puntos.cluster.ge(0)].groupby("cluster"):
        n_total = len(parte)
        n_dentro = int(parte.dentro_cuenca.astype(bool).sum())
        n_fuera = n_total - n_dentro
        union = parte.geometry.union_all()
        hull = union.convex_hull
        buffered = parte.geometry.buffer(150).union_all().buffer(-150)
        filas.append({
            "cluster": int(cluster), "escenario_id": principal,
            "n_total_cluster": n_total, "n_dentro_cuenca": n_dentro,
            "n_fuera_cuenca": n_fuera,
            "pct_cluster_dentro_cuenca": 100 * n_dentro / n_total,
            "pct_cluster_fuera_cuenca": 100 * n_fuera / n_total,
            "cruza_limite_cuenca": bool(n_dentro > 0 and n_fuera > 0),
            "area_convexa_km2": hull.area / 1_000_000,
            "area_buffer_150m_km2": buffered.area / 1_000_000,
            "densidad_convexa_est_km2": n_total / (hull.area / 1_000_000) if hull.area else np.nan,
            "n_municipios": parte.Municipio.nunique(),
            "n_localidades": parte.localidad.nunique(),
            "persistencia_media": parte.persistencia_territorial.mean(),
        })
        geometrias.append(hull)
    resumen = pd.DataFrame(filas)
    comun.guardar_csv(resumen, comun.OUT / "06_clusters/resumen_clusters_borde.csv")
    destino = comun.OUT / "06_clusters/solucion_principal.gpkg"
    puntos.to_file(destino, layer="establecimientos_membresia", driver="GPKG")
    hulls = gpd.GeoDataFrame(resumen.copy(), geometry=geometrias, crs=puntos.crs)
    hulls.to_file(destino, layer="envolventes_convexas", driver="GPKG")
    puntos.drop(columns="geometry").to_csv(
        comun.OUT / "06_clusters/membresia_solucion_principal.csv", index=False, encoding="utf-8-sig"
    )
    print(f"{len(resumen)} clusters; ruido={int(puntos.cluster.lt(0).sum())}; escenario={principal}")


if __name__ == "__main__":
    main()
