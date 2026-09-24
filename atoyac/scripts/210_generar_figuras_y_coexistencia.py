"""Genera figuras y la tabla específica de coexistencia sectorial."""

from importlib import import_module

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

comun = import_module("200_parte2_comun")


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(comun.OUT / f"10_figuras/{nombre}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    sns.set_theme(style="whitegrid")
    gdf = gpd.read_file(comun.OUT / "06_clusters/solucion_principal.gpkg", layer="establecimientos_membresia")
    cuenca = gpd.read_file(comun.CUENCA).to_crs(gdf.crs)
    fig, ax = plt.subplots(figsize=(10, 10))
    cuenca.boundary.plot(ax=ax, color="black", linewidth=1.2)
    ruido = gdf[gdf.cluster.lt(0)]
    activos = gdf[gdf.cluster.ge(0)]
    ruido.plot(ax=ax, color="#bdbdbd", markersize=5, alpha=0.55, label="Disperso/ruido")
    activos.plot(ax=ax, column="cluster", cmap="tab20", markersize=10, alpha=0.8, legend=False)
    ax.set_title("Solución espacial principal HDBSCAN\nDetección sobre 4,365 establecimientos")
    ax.set_axis_off()
    ax.legend(loc="lower left")
    guardar(fig, "01_solucion_principal")

    seleccion = pd.read_csv(comun.OUT / "05_seleccion/seleccion_escenarios.csv")
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(
        data=seleccion, x="pct_ruido", y="pct_cluster_mayor", hue="metodo",
        size="n_clusters", sizes=(30, 200), alpha=0.75, ax=ax,
    )
    principal = seleccion[seleccion.rol.eq("PRINCIPAL")]
    ax.scatter(principal.pct_ruido, principal.pct_cluster_mayor, marker="*", s=350, color="black", label="Principal")
    ax.set_xlabel("Establecimientos clasificados como ruido (%)")
    ax.set_ylabel("Peso del cluster más grande (%)")
    ax.set_title("Comparación espacial de configuraciones")
    guardar(fig, "02_comparacion_escenarios")

    perfiles = pd.read_csv(comun.OUT / "07_perfiles/perfiles_clusters.csv")
    cols = [
        "pct__actividad_lavanderia_tintoreria", "pct__actividad_confeccion",
        "pct__actividad_fabricacion_telas", "pct__actividad_acabado_textil",
        "pct__maquila", "pct__mezclilla", "pct__humedo_explicito",
        "pct__proceso_seco_explicito",
    ]
    etiquetas = [c.replace("pct__", "") for c in cols]
    matriz = perfiles.set_index("grupo_espacial")[cols]
    matriz.columns = etiquetas
    fig, ax = plt.subplots(figsize=(11, max(6, len(matriz) * 0.38)))
    sns.heatmap(matriz, cmap="YlGnBu", vmin=0, vmax=100, ax=ax, cbar_kws={"label": "% del grupo"})
    ax.set_title("Perfiles multilabel posteriores al clustering")
    ax.set_xlabel("")
    ax.set_ylabel("")
    guardar(fig, "03_perfiles_clusters")

    datos = pd.read_csv(comun.OUT / "07_perfiles/establecimientos_perfilados_cuenca.csv", low_memory=False)
    datos["es_lavanderia"] = comun.booleano(datos["actividad_lavanderia_tintoreria"])
    datos["es_manufactura_textil"] = comun.booleano(datos["scian_textil"])
    filas = []
    for grupo, parte in datos.groupby("grupo_espacial"):
        n = len(parte)
        lav = int(parte.es_lavanderia.sum())
        man = int(parte.es_manufactura_textil.sum())
        pl, pm = 100 * lav / n, 100 * man / n
        if pl >= 80:
            tipo = "CONCENTRACION_LAVANDERIAS"
        elif pm >= 80:
            tipo = "CONCENTRACION_MANUFACTURA"
        elif pl >= 20 and pm >= 20:
            tipo = "COEXISTENCIA_MIXTA"
        elif pl > pm:
            tipo = "PREDOMINIO_LAVANDERIAS"
        else:
            tipo = "PREDOMINIO_MANUFACTURA"
        filas.append({
            "grupo_espacial": grupo, "n": n, "n_lavanderia_tintoreria": lav,
            "pct_lavanderia_tintoreria": pl, "n_manufactura_textil": man,
            "pct_manufactura_textil": pm, "tipo_coexistencia_descriptivo": tipo,
        })
    coexistencia = pd.DataFrame(filas)
    comun.guardar_csv(coexistencia, comun.OUT / "07_perfiles/analisis_coexistencia_lavanderias_manufactura.csv")
    fig, ax = plt.subplots(figsize=(8, 7))
    clusters = coexistencia[~coexistencia.grupo_espacial.eq("RUIDO_DISPERSO")]
    sns.scatterplot(
        data=clusters, x="pct_manufactura_textil", y="pct_lavanderia_tintoreria",
        size="n", hue="tipo_coexistencia_descriptivo", sizes=(40, 500), ax=ax,
    )
    ax.axvline(50, color="grey", linestyle="--", linewidth=0.8)
    ax.axhline(50, color="grey", linestyle="--", linewidth=0.8)
    ax.set_title("Coexistencia posterior: lavanderías y manufactura textil")
    guardar(fig, "04_coexistencia_lavanderias_manufactura")
    print(coexistencia.tipo_coexistencia_descriptivo.value_counts().to_string())


if __name__ == "__main__":
    main()
