"""Genera mapas finales y fichas visuales homogéneas del atlas de Parte 2."""

from importlib import import_module

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import seaborn as sns

comun = import_module("200_parte2_comun")

COLORES_TIPO = {
    "CONCENTRACION_MANUFACTURA": "#2166ac",
    "COEXISTENCIA_MIXTA": "#7b3294",
    "PREDOMINIO_MANUFACTURA": "#67a9cf",
    "PREDOMINIO_LAVANDERIAS": "#ef8a62",
    "CONCENTRACION_LAVANDERIAS": "#b2182b",
}


def escala_norte(ax, longitud_m=None):
    xmin, xmax = ax.get_xlim(); ymin, ymax = ax.get_ylim()
    ancho, alto = xmax - xmin, ymax - ymin
    if longitud_m is None:
        candidatos = np.array([250, 500, 1000, 2000, 5000, 10000, 20000])
        longitud_m = candidatos[np.argmin(np.abs(candidatos - ancho * 0.18))]
    x0, y0 = xmin + ancho * 0.07, ymin + alto * 0.06
    ax.plot([x0, x0 + longitud_m], [y0, y0], color="black", lw=3, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - alto*.008, y0 + alto*.008], color="black", lw=1)
    ax.plot([x0 + longitud_m, x0 + longitud_m], [y0 - alto*.008, y0 + alto*.008], color="black", lw=1)
    etiqueta = f"{longitud_m/1000:g} km" if longitud_m >= 1000 else f"{longitud_m:g} m"
    ax.text(x0 + longitud_m/2, y0 + alto*.015, etiqueta, ha="center", va="bottom", fontsize=8)
    ax.annotate("N", xy=(xmin + ancho*.93, ymin + alto*.91), xytext=(xmin + ancho*.93, ymin + alto*.82),
                ha="center", fontsize=10, fontweight="bold",
                arrowprops=dict(facecolor="black", width=2, headwidth=8))


def guardar(fig, nombre):
    fig.savefig(comun.OUT / f"13_figuras_finales/{nombre}.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def configurar_mapa(ax, titulo):
    ax.set_title(titulo, fontsize=14, fontweight="bold", pad=12)
    ax.set_axis_off()
    escala_norte(ax)


def main():
    comun.asegurar_directorios()
    sns.set_theme(style="whitegrid", context="notebook")
    puntos = gpd.read_file(comun.OUT / "06_clusters/solucion_principal.gpkg", layer="establecimientos_membresia")
    cuenca = gpd.read_file(comun.CUENCA).to_crs(puntos.crs)
    municipios = gpd.read_file(comun.MUNICIPIOS).to_crs(puntos.crs)
    municipios = municipios[municipios.intersects(cuenca.geometry.union_all())].copy()
    perfiles = pd.read_csv(comun.OUT / "07_perfiles/perfiles_clusters.csv")
    coexist = pd.read_csv(comun.OUT / "07_perfiles/analisis_coexistencia_lavanderias_manufactura.csv")
    cierre = pd.read_csv(comun.OUT / "11_cierre/fichas_resumen_clusters.csv")

    # 1. Universo de detección e interpretación.
    fig, ax = plt.subplots(figsize=(9, 10))
    cuenca.plot(ax=ax, facecolor="#eef5f9", edgecolor="#253746", linewidth=1.4)
    municipios.boundary.plot(ax=ax, color="#9aa6ac", linewidth=.45)
    puntos[~puntos.dentro_cuenca.astype(bool)].plot(ax=ax, color="#d95f02", marker="^", markersize=14, alpha=.65)
    puntos[puntos.dentro_cuenca.astype(bool)].plot(ax=ax, color="#1b9e77", markersize=5, alpha=.55)
    ax.legend(handles=[
        Line2D([], [], marker="o", linestyle="", color="#1b9e77", label="Dentro de cuenca (4,010)"),
        Line2D([], [], marker="^", linestyle="", color="#d95f02", label="Apoyo exterior (355)"),
    ], loc="lower left", frameon=True)
    configurar_mapa(ax, "Universos de detección e interpretación")
    guardar(fig, "01_universos_borde")

    # 2. Solución territorial con etiquetas.
    fig, ax = plt.subplots(figsize=(10, 10))
    cuenca.plot(ax=ax, facecolor="#fafafa", edgecolor="#222", linewidth=1.2)
    municipios.boundary.plot(ax=ax, color="#cccccc", linewidth=.4)
    puntos[puntos.cluster.lt(0) & puntos.dentro_cuenca.astype(bool)].plot(ax=ax, color="#bdbdbd", markersize=5, alpha=.45)
    activos = puntos[puntos.cluster.ge(0) & puntos.dentro_cuenca.astype(bool)]
    activos.plot(ax=ax, column="cluster", cmap="tab20", markersize=9, alpha=.78)
    for cid, parte in activos.groupby("cluster"):
        p = parte.geometry.union_all().centroid
        ax.text(p.x, p.y, str(int(cid)), fontsize=8, fontweight="bold", ha="center", va="center",
                bbox=dict(boxstyle="circle,pad=.22", facecolor="white", edgecolor="#333", alpha=.85))
    ax.legend(handles=[Line2D([], [], marker="o", linestyle="", color="#bdbdbd", label="Actividad dispersa")], loc="lower left")
    configurar_mapa(ax, "Solución espacial principal: clusters dentro de la cuenca")
    guardar(fig, "02_clusters_principales")

    # 3. Persistencia.
    fig, ax = plt.subplots(figsize=(10, 10))
    cuenca.boundary.plot(ax=ax, color="#222", linewidth=1.1)
    pal = {"NUCLEO_ROBUSTO": "#1b7837", "ESTABLE": "#80cdc1", "SENSIBLE": "#d73027"}
    interior = puntos[puntos.dentro_cuenca.astype(bool)]
    for clase in ["SENSIBLE", "ESTABLE", "NUCLEO_ROBUSTO"]:
        parte = interior[interior.clase_persistencia.eq(clase)]
        parte.plot(ax=ax, color=pal[clase], markersize=7, alpha=.72, label=clase.replace("_", " ").title())
    ax.legend(loc="lower left")
    configurar_mapa(ax, "Persistencia territorial entre especificaciones")
    guardar(fig, "03_persistencia_territorial")

    # 4. Tipos productivos, asignados sólo después del clustering.
    tipos_map = coexist.set_index("grupo_espacial").tipo_coexistencia_descriptivo.to_dict()
    fig, ax = plt.subplots(figsize=(10, 10))
    cuenca.plot(ax=ax, facecolor="#fafafa", edgecolor="#222", linewidth=1.1)
    for cid, parte in activos.groupby("cluster"):
        grupo = f"CLUSTER_{int(cid):03d}"
        tipo = tipos_map[grupo]
        parte.plot(ax=ax, color=COLORES_TIPO[tipo], markersize=9, alpha=.72)
    handles = [Patch(facecolor=c, label=k.replace("_", " ").title()) for k, c in COLORES_TIPO.items() if k in set(tipos_map.values())]
    ax.legend(handles=handles, loc="lower left", fontsize=8)
    configurar_mapa(ax, "Composición posterior: manufactura y lavanderías")
    guardar(fig, "04_tipos_productivos_clusters")

    # 5. Robustez de escenarios.
    sel = pd.read_csv(comun.OUT / "05_seleccion/seleccion_escenarios.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    sns.scatterplot(data=sel, x="pct_ruido", y="pct_cluster_mayor", hue="metodo", size="n_clusters", sizes=(25, 180), ax=axes[0])
    pri = sel[sel.rol.eq("PRINCIPAL")]
    axes[0].scatter(pri.pct_ruido, pri.pct_cluster_mayor, marker="*", color="black", s=320, zorder=9)
    axes[0].set(title="Equilibrio entre ruido y mega-cluster", xlabel="Ruido (%)", ylabel="Cluster mayor (%)")
    no_optics = sel[sel.metodo.ne("OPTICS")]
    sns.scatterplot(data=no_optics, x="ari_top5_mismo_metodo", y="ari_perturbacion_25m", hue="metodo", ax=axes[1])
    axes[1].scatter(pri.ari_top5_mismo_metodo, pri.ari_perturbacion_25m, marker="*", color="black", s=320, zorder=9)
    axes[1].set(title="Estabilidad entre parámetros y perturbaciones", xlabel="ARI con configuraciones próximas", ylabel="ARI ante perturbación de 25 m")
    fig.suptitle("Robustez de la solución espacial", fontsize=15, fontweight="bold")
    fig.tight_layout()
    guardar(fig, "05_robustez_escenarios")

    # 6. Heatmap de perfiles.
    cols = ["pct__actividad_lavanderia_tintoreria", "pct__actividad_confeccion", "pct__actividad_fabricacion_telas",
            "pct__actividad_acabado_textil", "pct__maquila", "pct__mezclilla", "pct__humedo_explicito", "pct__proceso_seco_explicito"]
    mat = perfiles.set_index("grupo_espacial")[cols]
    mat.columns = [c.replace("pct__", "").replace("actividad_", "") for c in cols]
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(mat, cmap="YlGnBu", vmin=0, vmax=100, linewidths=.25, ax=ax, cbar_kws={"label": "% del grupo"})
    ax.set(title="Composición multilabel de clusters y actividad dispersa", xlabel="", ylabel="")
    guardar(fig, "06_composicion_multilabel")

    # 7. Rasgos distintivos conservadores.
    rasgos = pd.read_csv(comun.OUT / "11_cierre/rasgos_distintivos_clusters.csv")
    pivot = rasgos.pivot(index="grupo_espacial", columns="senal", values="log2_lift").fillna(0)
    fig, ax = plt.subplots(figsize=(13, 8))
    sns.heatmap(pivot, cmap="RdBu_r", center=0, linewidths=.3, ax=ax, cbar_kws={"label": "log2(lift)"})
    ax.set(title="Rasgos sobrerrepresentados que superan criterios conservadores", xlabel="", ylabel="")
    guardar(fig, "07_rasgos_distintivos")

    # 8. Agrupados contra ruido.
    ruido_cmp = pd.read_csv(comun.OUT / "11_cierre/comparacion_clusters_ruido.csv").sort_values("diferencia_agrupado_menos_ruido")
    fig, ax = plt.subplots(figsize=(10, 7))
    colores = np.where(ruido_cmp.diferencia_agrupado_menos_ruido >= 0, "#2166ac", "#b2182b")
    ax.barh(ruido_cmp.senal, 100 * ruido_cmp.diferencia_agrupado_menos_ruido, color=colores)
    ax.axvline(0, color="black", lw=.8)
    ax.set(title="Actividad agrupada frente a actividad dispersa", xlabel="Diferencia de prevalencia (puntos porcentuales)", ylabel="")
    ax.text(.99, .02, "Azul: mayor en clusters · Rojo: mayor en dispersos", transform=ax.transAxes, ha="right", fontsize=9)
    fig.tight_layout()
    guardar(fig, "08_clusters_vs_ruido")

    # 9. Similitud de perfiles.
    d = pd.read_csv(comun.OUT / "09_comparacion/distancias_perfiles.csv").set_index("grupo_espacial")
    fig, ax = plt.subplots(figsize=(10, 8.5))
    sns.heatmap(d, cmap="mako_r", square=True, ax=ax, cbar_kws={"label": "Distancia de perfil"})
    ax.set(title="Similitud productiva entre clusters espacialmente distintos", xlabel="", ylabel="")
    guardar(fig, "09_similitud_perfiles")

    # 10. Mega-cluster diagnóstico.
    mega = gpd.read_file(comun.OUT / "11_cierre/diagnostico_mega_cluster.gpkg", layer="establecimientos_subnucleos")
    hexes = gpd.read_file(comun.OUT / "11_cierre/diagnostico_mega_cluster.gpkg", layer="hexagonos_250m")
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    mega.plot(ax=axes[0], column="subnucleo_diagnostico", cmap="tab20", markersize=7, alpha=.75)
    axes[0].set_title("Subnúcleos exploratorios internos")
    hexes.plot(ax=axes[1], column="n_establecimientos", cmap="magma", legend=True, edgecolor="none")
    axes[1].set_title("Densidad en hexágonos de 250 m")
    for ax in axes:
        ax.set_axis_off(); escala_norte(ax)
    fig.suptitle("Diagnóstico interno del mega-cluster 20 (sin redefinir membresías)", fontsize=15, fontweight="bold")
    guardar(fig, "10_diagnostico_mega_cluster")

    # 11. Borde.
    borde = pd.read_csv(comun.OUT / "06_clusters/resumen_clusters_borde.csv")
    borde = borde[borde.n_dentro_cuenca.gt(0)].sort_values("n_total_cluster")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(borde.cluster.astype(str), borde.n_dentro_cuenca, label="Dentro", color="#1b9e77")
    ax.barh(borde.cluster.astype(str), borde.n_fuera_cuenca, left=borde.n_dentro_cuenca, label="Fuera", color="#d95f02")
    ax.set(title="Composición de borde de los clusters interiores", xlabel="Establecimientos", ylabel="Cluster")
    ax.legend()
    guardar(fig, "11_efecto_borde")

    # Atlas: una lámina por cluster interior y una para ruido.
    tipologias = pd.read_csv(comun.OUT / "09_comparacion/tipologia_perfiles_clusters.csv").set_index("grupo_espacial").tipo_perfil.to_dict()
    rasgos = pd.read_csv(comun.OUT / "11_cierre/rasgos_distintivos_clusters.csv")
    for grupo in cierre.grupo_espacial:
        fila = cierre[cierre.grupo_espacial.eq(grupo)].iloc[0]
        es_ruido = grupo == "RUIDO_DISPERSO"
        cid = -1 if es_ruido else int(fila.cluster)
        parte = puntos[puntos.cluster.eq(cid) & puntos.dentro_cuenca.astype(bool)]
        fig, axes = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1.35, 1]})
        ax = axes[0]
        if es_ruido:
            cuenca.plot(ax=ax, facecolor="#f5f5f5", edgecolor="#333")
            parte.plot(ax=ax, color="#777", markersize=8, alpha=.6)
        else:
            xmin, ymin, xmax, ymax = parte.total_bounds
            margen = max(xmax - xmin, ymax - ymin) * .25 + 500
            contexto = puntos.cx[xmin-margen:xmax+margen, ymin-margen:ymax+margen]
            contexto.plot(ax=ax, color="#d9d9d9", markersize=5, alpha=.4)
            parte.plot(ax=ax, color="#2166ac", markersize=13, alpha=.8)
            externos = puntos[puntos.cluster.eq(cid) & ~puntos.dentro_cuenca.astype(bool)]
            if not externos.empty:
                externos.plot(ax=ax, color="#d95f02", marker="^", markersize=24)
            ax.set_xlim(xmin-margen, xmax+margen); ax.set_ylim(ymin-margen, ymax+margen)
        ax.set_axis_off(); escala_norte(ax)
        ax.set_title(f"Mapa local · {grupo.replace('_', ' ')}", fontweight="bold")
        metricas = {
            "Lavandería": fila.pct__actividad_lavanderia_tintoreria,
            "Manufactura": fila.pct__scian_textil,
            "Confección": fila.pct__actividad_confeccion,
            "Maquila": fila.pct__maquila,
            "Húmedo explícito": fila.pct__humedo_explicito,
            "Seco explícito": fila.pct__proceso_seco_explicito,
        }
        axes[1].barh(list(metricas), list(metricas.values()), color=["#b2182b", "#2166ac", "#67a9cf", "#4d9221", "#ef8a62", "#999999"])
        axes[1].set_xlim(0, 100); axes[1].set_xlabel("Porcentaje de establecimientos")
        axes[1].set_title("Composición seleccionada", fontweight="bold")
        texto = (
            f"n dentro: {int(fila.n_dentro_cuenca)} · n total: {int(fila.n_total_cluster) if pd.notna(fila.n_total_cluster) else int(fila.n_dentro_cuenca)}\n"
            f"Municipio: {fila.municipio_principal}\nLocalidad: {fila.localidad_principal}\n"
            f"Persistencia: {fila.persistencia_media:.2f} · Tipo perfil: {tipologias.get(grupo, 'No aplica')}\n"
            f"Tipo descriptivo: {fila.tipo_coexistencia_descriptivo.replace('_', ' ').title()}"
        )
        fig.suptitle(grupo.replace("_", " "), fontsize=16, fontweight="bold")
        fig.text(.52, .02, texto, ha="center", va="bottom", fontsize=9)
        fig.tight_layout(rect=[0, .12, 1, .94])
        nombre = "ruido_disperso" if es_ruido else f"cluster_{cid:03d}"
        fig.savefig(comun.OUT / f"12_atlas/{nombre}.png", dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    print(f"Figuras finales: 11; láminas de atlas: {len(cierre)}")


if __name__ == "__main__":
    main()
