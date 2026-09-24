"""Compara clusters espaciales y construye una tipología exploratoria de perfiles."""

from importlib import import_module

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import jensenshannon, pdist, squareform
from sklearn.metrics.pairwise import cosine_distances

comun = import_module("200_parte2_comun")
perfil = import_module("207_perfilar_clusters")


def main():
    datos = pd.read_csv(comun.OUT / "07_perfiles/establecimientos_perfilados_cuenca.csv", low_memory=False)
    datos = datos[datos.cluster.ge(0)].copy()
    for c in perfil.SENALES:
        datos[c] = comun.booleano(datos[c]).astype(float)
    grupos = sorted(datos.grupo_espacial.unique())
    senales = datos.groupby("grupo_espacial")[perfil.SENALES].mean().reindex(grupos).fillna(0)
    scian = pd.crosstab(datos.grupo_espacial, datos.scian_3, normalize="index").reindex(grupos).fillna(0)
    personal = pd.crosstab(
        datos.grupo_espacial, datos["Descripcion estrato personal ocupado"], normalize="index"
    ).reindex(grupos).fillna(0)
    vector = pd.concat([
        senales.add_prefix("senal__"), scian.add_prefix("scian3__"), personal.add_prefix("personal__")
    ], axis=1)
    comun.guardar_csv(vector.reset_index(), comun.OUT / "09_comparacion/vectores_perfiles_clusters.csv")

    d_cos = cosine_distances(senales)
    d_js = np.zeros((len(grupos), len(grupos)))
    for i in range(len(grupos)):
        for j in range(i + 1, len(grupos)):
            d_js[i, j] = d_js[j, i] = jensenshannon(scian.iloc[i] + 1e-12, scian.iloc[j] + 1e-12)
    combinada = 0.5 * d_cos + 0.5 * d_js
    matriz = pd.DataFrame(combinada, index=grupos, columns=grupos)
    matriz.index.name = "grupo_espacial"
    matriz.reset_index().to_csv(comun.OUT / "09_comparacion/distancias_perfiles.csv", index=False, encoding="utf-8-sig")

    if len(grupos) >= 4:
        z = linkage(squareform(combinada, checks=False), method="average")
        k = max(2, min(6, round(np.sqrt(len(grupos)))))
        tipos = fcluster(z, t=k, criterion="maxclust")
        tipologia = pd.DataFrame({"grupo_espacial": grupos, "tipo_perfil": tipos})
        comun.guardar_csv(tipologia, comun.OUT / "09_comparacion/tipologia_perfiles_clusters.csv")
        comun.guardar_csv(pd.DataFrame(z, columns=["nodo_a", "nodo_b", "distancia", "n_elementos"]), comun.OUT / "09_comparacion/linkage_tipologia.csv")
    print(f"Comparados {len(grupos)} clusters espaciales mediante perfiles posteriores.")


if __name__ == "__main__":
    main()
