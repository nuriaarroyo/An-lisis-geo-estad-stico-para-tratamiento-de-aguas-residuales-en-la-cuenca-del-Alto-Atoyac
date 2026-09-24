"""Ejecuta una batería reproducible de escenarios exclusivamente espaciales."""

from importlib import import_module

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, HDBSCAN, OPTICS

comun = import_module("200_parte2_comun")


DBSCAN_EPS = [250, 400, 600, 800, 1200, 1600]
DBSCAN_MIN = [5, 10, 15, 25]
HDBSCAN_TAM = [10, 20, 30, 50, 75]
HDBSCAN_MIN = [5, 10, 20]
HDBSCAN_METODOS = ["eom", "leaf"]
OPTICS_MIN = [10, 20, 30]


def registrar(ids, metodo, parametros, labels, probabilidades, resumenes, membresias):
    eid = comun.escenario_id(metodo, parametros)
    resumen = {"escenario_id": eid, "metodo": metodo, **parametros, **comun.resumen_particion(labels)}
    if probabilidades is not None:
        validas = np.asarray(probabilidades)[np.asarray(labels) >= 0]
        resumen["probabilidad_media"] = float(validas.mean()) if len(validas) else np.nan
        resumen["pct_probabilidad_ge_0_8"] = float(100 * (validas >= 0.8).mean()) if len(validas) else np.nan
    resumenes.append(resumen)
    membresias.append(pd.DataFrame({
        "d_llave": ids,
        "escenario_id": eid,
        "metodo": metodo,
        "cluster": np.asarray(labels, dtype=int),
        "probabilidad": probabilidades if probabilidades is not None else np.where(np.asarray(labels) >= 0, 1.0, 0.0),
    }))


def main():
    comun.asegurar_directorios()
    puntos = comun.leer_puntos_metricos().sort_values("d_llave").reset_index(drop=True)
    ids = puntos["d_llave"].astype(str).to_numpy()
    xy = np.c_[puntos.geometry.x, puntos.geometry.y]
    resumenes, membresias = [], []

    for eps in DBSCAN_EPS:
        for minimo in DBSCAN_MIN:
            params = {"eps_m": eps, "min_samples": minimo}
            labels = DBSCAN(eps=eps, min_samples=minimo, n_jobs=-1).fit_predict(xy)
            registrar(ids, "DBSCAN", params, labels, None, resumenes, membresias)

    for tam in HDBSCAN_TAM:
        for minimo in HDBSCAN_MIN:
            for seleccion in HDBSCAN_METODOS:
                params = {"min_cluster_size": tam, "min_samples": minimo, "cluster_selection_method": seleccion}
                modelo = HDBSCAN(
                    min_cluster_size=tam,
                    min_samples=minimo,
                    cluster_selection_method=seleccion,
                    metric="euclidean",
                    n_jobs=-1,
                ).fit(xy)
                registrar(ids, "HDBSCAN", params, modelo.labels_, modelo.probabilities_, resumenes, membresias)

    for minimo in OPTICS_MIN:
        params = {"min_samples": minimo, "xi": 0.05, "min_cluster_size_frac": 0.01}
        modelo = OPTICS(min_samples=minimo, xi=0.05, min_cluster_size=0.01, n_jobs=-1).fit(xy)
        registrar(ids, "OPTICS", params, modelo.labels_, None, resumenes, membresias)

    resumen = pd.DataFrame(resumenes)
    comun.guardar_csv(resumen, comun.OUT / "04_clustering/resumen_escenarios.csv")
    pd.concat(membresias, ignore_index=True).to_csv(
        comun.membresias_path(), index=False, compression="gzip"
    )
    espacio = {
        "DBSCAN": {"eps_m": DBSCAN_EPS, "min_samples": DBSCAN_MIN},
        "HDBSCAN": {"min_cluster_size": HDBSCAN_TAM, "min_samples": HDBSCAN_MIN, "cluster_selection_method": HDBSCAN_METODOS},
        "OPTICS": {"min_samples": OPTICS_MIN, "xi": [0.05], "min_cluster_size_frac": [0.01]},
        "variables_usadas": ["x_utm14n", "y_utm14n"],
        "variables_excluidas": "Todas las variables económicas, textuales, hídricas y de tamaño",
    }
    comun.guardar_json(espacio, comun.OUT / "04_clustering/espacio_parametros.json")
    print(resumen.groupby("metodo").size().to_string())


if __name__ == "__main__":
    main()
