"""Laminas KDE y hexagonales para documentar el diagnostico espacial."""

from importlib import import_module
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm
from scipy.spatial import cKDTree
from sklearn.neighbors import KernelDensity

comun = import_module("200_parte2_comun")
diag = import_module("203_diagnosticar_estructura_espacial")

OUT = comun.OUT / "03_diagnosticos" / "figuras"


def kde_panel(ax, puntos, mascara, ancho, titulo, precalculado=None):
    if precalculado is None:
        xy = np.c_[puntos.geometry.x, puntos.geometry.y]
        xmin, ymin, xmax, ymax = mascara.bounds
        paso = 250
        xs = np.arange(xmin, xmax + paso, paso)
        ys = np.arange(ymin, ymax + paso, paso)
        xx, yy = np.meshgrid(xs, ys)
        muestra = np.c_[xx.ravel(), yy.ravel()]
        modelo = KernelDensity(bandwidth=ancho, kernel="gaussian").fit(xy)
        z = np.exp(modelo.score_samples(muestra)).reshape(xx.shape) * 1_000_000
        datos = gpd.GeoDataFrame(
            {"densidad_est_km2": z.ravel()},
            geometry=gpd.points_from_xy(muestra[:, 0], muestra[:, 1]), crs=puntos.crs,
        )
    else:
        datos = precalculado[precalculado.bandwidth_m.eq(ancho)].copy()
    im = ax.scatter(
        datos.geometry.x, datos.geometry.y, c=datos.densidad_est_km2,
        s=4, marker="s", linewidths=0, cmap="YlOrRd",
    )
    gpd.GeoSeries([mascara], crs=puntos.crs).boundary.plot(ax=ax, color="#263238", linewidth=.7)
    ax.set_title(titulo)
    ax.set_axis_off()
    plt.colorbar(im, ax=ax, fraction=.035, pad=.01, label="Densidad KDE normalizada (km⁻²)")


def hex_panel(ax, puntos, mascara, radio, titulo):
    hexes = diag.grilla_hexagonal(puntos, radio)
    hexes = gpd.clip(hexes, gpd.GeoDataFrame(geometry=[mascara], crs=puntos.crs))
    vmax = max(int(hexes.n_establecimientos.max()), 1)
    hexes.plot(
        ax=ax,
        column="n_establecimientos",
        cmap="YlGnBu",
        norm=LogNorm(vmin=1, vmax=vmax),
        edgecolor="none",
        legend=True,
        legend_kwds={"label": "Establecimientos por hexagono", "shrink": .68},
    )
    gpd.GeoSeries([mascara], crs=puntos.crs).boundary.plot(ax=ax, color="#263238", linewidth=.7)
    ax.set_title(titulo)
    ax.set_axis_off()


def lamina(puntos, mascara, nombre, titulo, anchos, radios, kde_precalculado=None):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    for ax, ancho in zip(axes[0], anchos):
        kde_panel(
            ax, puntos, mascara, ancho,
            f"KDE gaussiano · bandwidth {ancho:,} m", kde_precalculado,
        )
    for ax, radio in zip(axes[1], radios):
        hex_panel(ax, puntos, mascara, radio, f"Malla hexagonal · radio {radio:,} m")
    fig.suptitle(titulo, fontsize=16, fontweight="bold")
    fig.text(
        .5, .015,
        "El KDE se muestra continuo a ambos lados del limite; la linea delimita el area de interpretacion. "
        "Los hexagonos muestran conteos observados y ninguno de los dos diagnosticos define membresias.",
        ha="center", fontsize=10,
    )
    fig.tight_layout(rect=[0, .04, 1, .96])
    fig.savefig(OUT / nombre, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def curvas_k_distancia(puntos):
    """Grafica distancias ordenadas para mostrar escalas y codos multiples."""
    xy = np.c_[puntos.geometry.x, puntos.geometry.y]
    tree = cKDTree(xy)
    ks = [2, 5, 10, 20, 30, 50]
    colores = plt.cm.viridis(np.linspace(.08, .92, len(ks)))
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8))
    for k, color in zip(ks, colores):
        distancias, _ = tree.query(xy, k=k)
        ordenadas = np.sort(distancias[:, -1])
        percentil = 100 * np.arange(1, len(ordenadas) + 1) / len(ordenadas)
        axes[0].plot(percentil, ordenadas, color=color, lw=1.8, label=f"k={k}")
        axes[1].plot(percentil, ordenadas, color=color, lw=1.8, label=f"k={k}")
    axes[0].set(
        xlim=(0, 99), ylim=(0, 7000),
        title="Curvas completas hasta el percentil 99",
        xlabel="Percentil de establecimientos", ylabel="Distancia al vecino k (m)",
    )
    axes[1].set(
        xlim=(50, 99), ylim=(0, 7000),
        title="Ampliacion de la cola: cambios de pendiente",
        xlabel="Percentil de establecimientos", ylabel="Distancia al vecino k (m)",
    )
    for ax in axes:
        ax.grid(alpha=.25)
        ax.axvline(90, color="#b2182b", ls="--", lw=1, alpha=.8)
        ax.axvline(95, color="#ef8a62", ls=":", lw=1.2, alpha=.9)
        ax.legend(ncol=2, frameon=False)
    fig.suptitle(
        "Curvas k-distancia ordenadas: multiples escalas, sin un codo unico",
        fontsize=15, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, .94])
    fig.savefig(OUT / "03_curvas_k_distancia.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    puntos = comun.leer_puntos_metricos()
    curvas_k_distancia(puntos)
    cuenca = gpd.read_file(comun.CUENCA).to_crs(puntos.crs).geometry.union_all()
    kde_csv = pd.read_csv(comun.OUT / "03_diagnosticos" / "kde_grilla.csv.gz")
    kde_cuenca = gpd.GeoDataFrame(
        kde_csv.drop(columns="geometry"),
        geometry=gpd.GeoSeries.from_wkt(kde_csv.geometry), crs=puntos.crs,
    )
    lamina(
        puntos,
        cuenca,
        "01_kde_hex_cuenca.png",
        "Diagnostico multiescala del universo sectorial en la cuenca",
        [500, 1000, 2000],
        [250, 500, 1000],
        kde_cuenca,
    )

    mega = gpd.read_file(
        comun.OUT / "11_cierre" / "diagnostico_mega_cluster.gpkg",
        layer="establecimientos_subnucleos",
    )
    mascara_mega = mega.geometry.union_all().convex_hull.buffer(500)
    lamina(
        mega,
        mascara_mega,
        "02_kde_hex_mega_cluster.png",
        "Diagnostico multiescala interno del mega-cluster 20",
        [250, 500, 1000],
        [250, 500, 1000],
    )


if __name__ == "__main__":
    main()
