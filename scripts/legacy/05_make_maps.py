from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from common import (
    FIGURES_DIR,
    MAPS_DIR,
    PROCESSED_DIR,
    TABLES_DIR,
    ensure_output_dirs,
    log,
    normalize_text,
    read_gpkg,
    relpath,
)


CATEGORY_COLORS = {
    "alta_relevancia_ambiental": "#b2182b",
    "media_relevancia_ambiental": "#ef8a62",
    "revisar": "#7b3294",
}

DISTANCE_COLORS = {
    "0-100 m": "#7f0000",
    "100-250 m": "#d7301f",
    "250-500 m": "#fc8d59",
    "500-1000 m": "#91bfdb",
    ">1000 m": "#4575b4",
    "sin distancia": "#737373",
}

PROXIMITY_BANDS = [
    (1000, "#d9f0a3"),
    (500, "#addd8e"),
    (250, "#78c679"),
    (100, "#238443"),
]

REGIONS = {
    "huejotzingo": {"label": "Huejotzingo", "source_key": "huejotzingo"},
    "xalmimilulco": {"label": "Santa Ana Xalmimilulco", "source_key": "xalmimilulco"},
    "san_martin": {"label": "San Martin Texmelucan", "source_key": "san_martin"},
}


def optional_gpkg(name: str):
    path = PROCESSED_DIR / name
    if path.exists():
        return read_gpkg(path)
    return None


def finish_map(fig, ax, output_name: str) -> None:
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.tight_layout()
    out = MAPS_DIR / output_name
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    log(f"Mapa guardado: {relpath(out)}")


def source_filter(gdf, source_key: str):
    if gdf is None or gdf.empty or "source_folder" not in gdf.columns:
        return gdf
    mask = gdf["source_folder"].map(normalize_text).str.contains(source_key, na=False)
    return gdf.loc[mask].copy()


def line_geometries(gdf):
    if gdf is None or gdf.empty:
        return gdf
    return gdf[gdf.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()


def crop_to_extent(gdf, bounds, pad=1200):
    if gdf is None or gdf.empty or bounds is None:
        return gdf
    minx, miny, maxx, maxy = bounds
    cropped = gdf.cx[minx - pad : maxx + pad, miny - pad : maxy + pad].copy()
    return cropped if not cropped.empty else gdf


def combined_bounds(*frames):
    valid = [gdf for gdf in frames if gdf is not None and not gdf.empty]
    if not valid:
        return None
    minxs, minys, maxxs, maxys = zip(*(gdf.total_bounds for gdf in valid))
    return min(minxs), min(minys), max(maxxs), max(maxys)


def set_extent(ax, bounds, pad=600):
    if bounds is None:
        return
    minx, miny, maxx, maxy = bounds
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)


def plot_base(ax, agebs=None, manzanas=None, localidades=None, vialidades=None, caminos=None, hydro=None):
    if agebs is not None and not agebs.empty:
        agebs.plot(ax=ax, facecolor="#f7f7f7", edgecolor="#969696", linewidth=0.45)
    if manzanas is not None and not manzanas.empty:
        manzanas.plot(ax=ax, facecolor="none", edgecolor="#d0d0d0", linewidth=0.18)
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#525252", linewidth=0.8)
    if caminos is not None and not caminos.empty:
        caminos.plot(ax=ax, color="#8c6d31", linewidth=0.45, alpha=0.65)
    if vialidades is not None and not vialidades.empty:
        vialidades.plot(ax=ax, color="#636363", linewidth=0.25, alpha=0.55)
    if hydro is not None and not hydro.empty:
        hydro.plot(ax=ax, color="#2b8cbe", linewidth=0.55, alpha=0.8)


def load_layers():
    denue_textil = optional_gpkg("denue_textil_con_distancia.gpkg")
    if denue_textil is None:
        denue_textil = optional_gpkg("denue_textil.gpkg")
    return {
        "agebs": optional_gpkg("agebs.gpkg"),
        "manzanas": optional_gpkg("manzanas.gpkg"),
        "localidades": optional_gpkg("localidades.gpkg"),
        "vialidades": optional_gpkg("vialidades.gpkg"),
        "caminos": optional_gpkg("caminos_carreteras.gpkg"),
        "hydro": optional_gpkg("hidrografia.gpkg"),
        "denue_all": optional_gpkg("denue_raw.gpkg"),
        "denue_textil": denue_textil,
    }


def plot_context() -> None:
    layers = load_layers()
    hydro_lines = line_geometries(layers["hydro"])
    fig, ax = plt.subplots(figsize=(11, 9))
    plot_base(
        ax,
        agebs=layers["agebs"],
        manzanas=layers["manzanas"],
        localidades=layers["localidades"],
        vialidades=layers["vialidades"],
        caminos=layers["caminos"],
        hydro=hydro_lines,
    )
    ax.set_title("Contexto territorial: zona alta del Atoyac", fontsize=13)
    finish_map(fig, ax, "01_contexto_territorial.png")


def plot_denue_categories() -> None:
    layers = load_layers()
    denue = layers["denue_textil"]
    hydro_lines = line_geometries(layers["hydro"])
    fig, ax = plt.subplots(figsize=(10, 9))
    plot_base(ax, localidades=layers["localidades"], hydro=hydro_lines)
    if denue is not None and not denue.empty:
        for category, group in denue.groupby("categoria_relevancia_ambiental", dropna=False):
            group.plot(
                ax=ax,
                markersize=24,
                color=CATEGORY_COLORS.get(str(category), "#525252"),
                edgecolor="white",
                linewidth=0.35,
                label=str(category),
            )
        ax.legend(loc="best", fontsize=8, frameon=True)
    ax.set_title("DENUE textil por categoria de relevancia ambiental potencial", fontsize=13)
    finish_map(fig, ax, "02_denue_textil_categorias.png")


def plot_buffers() -> None:
    layers = load_layers()
    denue = layers["denue_textil"]
    hydro = line_geometries(layers["hydro"])
    fig, ax = plt.subplots(figsize=(10, 9))
    handles = []
    if hydro is not None and not hydro.empty:
        bounds = denue.total_bounds if denue is not None and not denue.empty else None
        hydro_plot = crop_to_extent(hydro, bounds, pad=1500)
        hydro_plot = hydro_plot.copy()
        hydro_plot["geometry"] = hydro_plot.geometry.simplify(15)
        hydro_plot.plot(ax=ax, color="#2b8cbe", linewidth=0.6)
    if denue is not None and not denue.empty:
        for distance_label, color in DISTANCE_COLORS.items():
            if "rango_distancia_hidrografia" not in denue.columns:
                continue
            group = denue[denue["rango_distancia_hidrografia"].astype(str).eq(distance_label)]
            if group.empty:
                continue
            group.plot(ax=ax, color=color, markersize=18, edgecolor="white", linewidth=0.25)
            handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=color, label=distance_label, markersize=7))
    if handles:
        ax.legend(handles=handles, loc="best", fontsize=8, frameon=True, title="Distancia a cauce")
    ax.set_title("Rangos de proximidad a cauces con DENUE textil", fontsize=13)
    finish_map(fig, ax, "03_buffers_hidrografia_denue.png")


def plot_ageb_concentration() -> None:
    agebs = optional_gpkg("agebs.gpkg")
    counts_path = TABLES_DIR / "conteo_negocios_por_ageb.csv"
    if agebs is None or agebs.empty or not counts_path.exists():
        log("No hay insumos para mapa de concentracion por AGEB")
        return
    counts = pd.read_csv(counts_path)
    if counts.empty or "ageb_id" not in counts.columns:
        log("conteo_negocios_por_ageb.csv no contiene ageb_id")
        return
    totals = counts.groupby("ageb_id", dropna=False)["establecimientos"].sum().reset_index()
    totals["ageb_id"] = totals["ageb_id"].astype(str)
    agebs = agebs.copy()
    join_col = None
    for col in agebs.columns:
        if col != "geometry" and agebs[col].astype(str).isin(totals["ageb_id"]).any():
            join_col = col
            break
    if join_col is None:
        agebs["ageb_id"] = range(1, len(agebs) + 1)
        join_col = "ageb_id"
    agebs[join_col] = agebs[join_col].astype(str)
    mapped = agebs.merge(totals, left_on=join_col, right_on="ageb_id", how="left")
    mapped["establecimientos"] = mapped["establecimientos"].fillna(0)

    fig, ax = plt.subplots(figsize=(10, 9))
    mapped.plot(
        ax=ax,
        column="establecimientos",
        cmap="YlOrRd",
        legend=True,
        edgecolor="#8c8c8c",
        linewidth=0.35,
        missing_kwds={"color": "#f2f2f2"},
    )
    ax.set_title("Concentracion preliminar de actividad textil por AGEB", fontsize=13)
    finish_map(fig, ax, "04_concentracion_textil_por_ageb.png")


def region_layers(layers, source_key):
    out = {key: source_filter(value, source_key) for key, value in layers.items() if key != "hydro"}
    bounds = combined_bounds(out.get("agebs"), out.get("localidades"), out.get("denue_all"), out.get("denue_textil"))
    out["hydro"] = crop_to_extent(line_geometries(layers["hydro"]), bounds, pad=1600)
    out["bounds"] = bounds
    return out


def plot_region_denue_total(region_id: str, label: str, layers) -> None:
    fig, ax = plt.subplots(figsize=(10, 9))
    plot_base(
        ax,
        agebs=layers["agebs"],
        manzanas=layers["manzanas"],
        localidades=layers["localidades"],
        vialidades=layers["vialidades"],
        caminos=layers["caminos"],
        hydro=layers["hydro"],
    )
    denue = layers["denue_all"]
    if denue is not None and not denue.empty:
        denue.plot(ax=ax, color="#252525", markersize=4, alpha=0.42)
    set_extent(ax, layers["bounds"])
    ax.set_title(f"{label}: DENUE total", fontsize=13)
    finish_map(fig, ax, f"10_{region_id}_denue_total.png")


def plot_region_textile(region_id: str, label: str, layers) -> None:
    fig, ax = plt.subplots(figsize=(10, 9))
    plot_base(ax, agebs=layers["agebs"], localidades=layers["localidades"], hydro=layers["hydro"])
    denue = layers["denue_textil"]
    handles = []
    if denue is not None and not denue.empty:
        for category, group in denue.groupby("categoria_relevancia_ambiental", dropna=False):
            color = CATEGORY_COLORS.get(str(category), "#525252")
            group.plot(ax=ax, markersize=30, color=color, edgecolor="white", linewidth=0.35)
            handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=color, label=str(category), markersize=7))
    if handles:
        ax.legend(handles=handles, loc="best", fontsize=8, frameon=True)
    set_extent(ax, layers["bounds"])
    ax.set_title(f"{label}: DENUE textil y relevancia ambiental potencial", fontsize=13)
    finish_map(fig, ax, f"11_{region_id}_denue_textil_categorias.png")


def plot_region_heatmap(region_id: str, label: str, layers) -> None:
    fig, ax = plt.subplots(figsize=(10, 9))
    plot_base(ax, agebs=layers["agebs"], localidades=layers["localidades"], hydro=layers["hydro"])
    denue = layers["denue_textil"]
    if denue is not None and not denue.empty:
        x = denue.geometry.x
        y = denue.geometry.y
        hb = ax.hexbin(x, y, gridsize=34, cmap="YlOrRd", mincnt=1, linewidths=0, alpha=0.82)
        fig.colorbar(hb, ax=ax, shrink=0.72, label="Establecimientos por celda")
    set_extent(ax, layers["bounds"])
    ax.set_title(f"{label}: mapa de calor DENUE textil", fontsize=13)
    finish_map(fig, ax, f"12_{region_id}_heatmap_denue_textil.png")


def plot_region_distance(region_id: str, label: str, layers) -> None:
    fig, ax = plt.subplots(figsize=(10, 9))
    plot_base(ax, agebs=layers["agebs"], localidades=layers["localidades"])
    hydro = layers["hydro"]
    handles = []
    if hydro is not None and not hydro.empty:
        hydro.plot(ax=ax, color="#08519c", linewidth=0.8)
    denue = layers["denue_textil"]
    if denue is not None and not denue.empty:
        col = "rango_distancia_hidrografia"
        for distance_label, color in DISTANCE_COLORS.items():
            if col in denue.columns:
                group = denue[denue[col].astype(str).eq(distance_label)]
            else:
                group = denue.iloc[0:0]
            if group.empty:
                continue
            group.plot(ax=ax, markersize=28, color=color, edgecolor="white", linewidth=0.35)
            handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=color, label=distance_label, markersize=7))
    if handles:
        ax.legend(handles=handles, loc="best", fontsize=8, frameon=True, title="Distancia a cauce")
    set_extent(ax, layers["bounds"])
    ax.set_title(f"{label}: rangos de distancia a cauces - DENUE textil", fontsize=13)
    finish_map(fig, ax, f"13_{region_id}_rangos_distancia_rio.png")


def plot_region_maps() -> None:
    base_layers = load_layers()
    for region_id, meta in REGIONS.items():
        layers = region_layers(base_layers, meta["source_key"])
        plot_region_denue_total(region_id, meta["label"], layers)
        plot_region_textile(region_id, meta["label"], layers)
        plot_region_heatmap(region_id, meta["label"], layers)
        plot_region_distance(region_id, meta["label"], layers)


def plot_river_only() -> None:
    hydro = line_geometries(optional_gpkg("hidrografia.gpkg"))
    denue = optional_gpkg("denue_raw.gpkg")
    if hydro is None or hydro.empty:
        log("No hay hidrografia lineal para mapa de cauces")
        return
    bounds = denue.total_bounds if denue is not None and not denue.empty else None
    hydro = crop_to_extent(hydro, bounds, pad=3000)
    hydro = hydro.copy()
    hydro["geometry"] = hydro.geometry.simplify(12)
    fig, ax = plt.subplots(figsize=(11, 9))
    hydro.plot(ax=ax, color="#08519c", linewidth=0.45, alpha=0.85)
    ax.set_title("Cauces y red hidrografica - zona alta del Atoyac", fontsize=13)
    set_extent(ax, bounds, pad=3000)
    finish_map(fig, ax, "05_cauces_rio_red_hidrografica.png")


def plot_rh18ad() -> None:
    hydro = optional_gpkg("hidrografia.gpkg")
    if hydro is None or hydro.empty or "source_path" not in hydro.columns:
        log("No hay insumos para mapa RH18Ad")
        return
    rh18ad = hydro[hydro["source_path"].map(normalize_text).str.contains("rh18ad", na=False)].copy()
    if rh18ad.empty:
        log("No se encontraron features RH18Ad")
        return
    denue = optional_gpkg("denue_raw.gpkg")
    bounds = denue.total_bounds if denue is not None and not denue.empty else None
    rh18ad = crop_to_extent(rh18ad, bounds, pad=3000)
    rh18ad["geometry"] = rh18ad.geometry.simplify(10)
    fig, ax = plt.subplots(figsize=(10, 9))
    lines = line_geometries(rh18ad)
    polygons = rh18ad[rh18ad.geometry.geom_type.fillna("").str.contains("Polygon", case=False)].copy()
    points = rh18ad[rh18ad.geometry.geom_type.fillna("").str.contains("Point", case=False)].copy()
    if not polygons.empty:
        polygons.plot(ax=ax, facecolor="#deebf7", edgecolor="#9ecae1", linewidth=0.35, alpha=0.45)
    if lines is not None and not lines.empty:
        lines.plot(ax=ax, color="#08519c", linewidth=0.65)
    if not points.empty:
        points.plot(ax=ax, color="#238b45", markersize=8, alpha=0.7)
    ax.set_title("Area RH18Ad: red hidrografica especifica", fontsize=13)
    set_extent(ax, bounds, pad=3000)
    finish_map(fig, ax, "06_rh18ad_hidrografia_especifica.png")


def plot_hydrology_complete_by_type() -> None:
    hydro = optional_gpkg("hidrografia.gpkg")
    denue = optional_gpkg("denue_raw.gpkg")
    if hydro is None or hydro.empty:
        log("No hay hidrografia para mapa completo por tipo")
        return
    bounds = denue.total_bounds if denue is not None and not denue.empty else None
    hydro_plot = crop_to_extent(hydro, bounds, pad=4500).copy()
    hydro_plot["geometry"] = hydro_plot.geometry.simplify(15)
    fig, ax = plt.subplots(figsize=(11, 9))
    polygons = hydro_plot[hydro_plot.geometry.geom_type.fillna("").str.contains("Polygon", case=False)].copy()
    lines = line_geometries(hydro_plot)
    points = hydro_plot[hydro_plot.geometry.geom_type.fillna("").str.contains("Point", case=False)].copy()
    if not polygons.empty:
        polygons.plot(ax=ax, facecolor="#deebf7", edgecolor="#9ecae1", linewidth=0.3, alpha=0.45, label="Areas hidrologicas")
    if lines is not None and not lines.empty:
        lines.plot(ax=ax, color="#08519c", linewidth=0.55, alpha=0.85, label="Cauces/red lineal")
    if not points.empty:
        points.plot(ax=ax, color="#238b45", markersize=6, alpha=0.65, label="Elementos puntuales")
    ax.legend(loc="best", fontsize=8, frameon=True)
    ax.set_title("Hidrologia completa por tipo de geometria", fontsize=13)
    set_extent(ax, bounds, pad=4500)
    finish_map(fig, ax, "07_hidrologia_completa_por_tipo.png")


def plot_hydrology_complete_by_source() -> None:
    hydro = line_geometries(optional_gpkg("hidrografia.gpkg"))
    denue = optional_gpkg("denue_raw.gpkg")
    if hydro is None or hydro.empty:
        log("No hay hidrografia lineal para mapa por fuente")
        return
    bounds = denue.total_bounds if denue is not None and not denue.empty else None
    hydro_plot = crop_to_extent(hydro, bounds, pad=4500).copy()
    hydro_plot["geometry"] = hydro_plot.geometry.simplify(15)
    fig, ax = plt.subplots(figsize=(11, 9))
    if "source_folder" in hydro_plot.columns:
        hydro_plot["rh_area"] = hydro_plot["source_folder"].astype(str).str.extract(r"(RH\d+[A-Za-z]+)", expand=False).fillna("hidrologia_atoyac")
        hydro_plot.plot(ax=ax, column="rh_area", categorical=True, linewidth=0.55, legend=True, cmap="tab20")
    else:
        hydro_plot.plot(ax=ax, color="#08519c", linewidth=0.55)
    ax.set_title("Hidrologia completa: cauces por area/fuente RH", fontsize=13)
    set_extent(ax, bounds, pad=4500)
    finish_map(fig, ax, "08_hidrologia_completa_por_area_rh.png")


def plot_saic_figure() -> None:
    path = TABLES_DIR / "saic_resumen_municipio_actividad.csv"
    if not path.exists():
        log("No existe saic_resumen_municipio_actividad.csv")
        return
    df = pd.read_csv(path)
    if df.empty:
        return
    mask = df["municipio_nombre"].astype(str).str.contains("Huejotzingo|San Martin|San Martín", case=False, na=False)
    muni = df.loc[mask].copy()
    if muni.empty:
        log("SAIC no contiene Huejotzingo o San Martin para la figura")
        return
    summary = muni.groupby("municipio_nombre", dropna=False).agg(
        ue=("ue", "sum"),
        personal_ocupado=("h001a", "sum"),
        ingresos=("m000a", "sum"),
        personal_familiar=("h020a", "sum"),
    )
    summary["proporcion_familiar"] = summary["personal_familiar"] / summary["personal_ocupado"].replace(0, pd.NA)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    metrics = [
        ("ue", "Unidades economicas"),
        ("personal_ocupado", "Personal ocupado"),
        ("ingresos", "Ingresos"),
        ("proporcion_familiar", "Proporcion familiar/no remunerada"),
    ]
    for ax, (metric, title) in zip(axes.ravel(), metrics):
        summary[metric].plot(kind="bar", ax=ax, color=["#4c78a8", "#f58518"])
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("")
        ax.tick_params(axis="x", labelrotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("SAIC: indicadores textiles municipales", fontsize=13)
    fig.tight_layout()
    out = FIGURES_DIR / "saic_indicadores_municipio.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    log(f"Figura guardada: {relpath(out)}")


def main() -> None:
    ensure_output_dirs()
    plot_context()
    plot_denue_categories()
    plot_buffers()
    plot_ageb_concentration()
    plot_river_only()
    plot_rh18ad()
    plot_hydrology_complete_by_type()
    plot_hydrology_complete_by_source()
    plot_region_maps()
    plot_saic_figure()


if __name__ == "__main__":
    main()
