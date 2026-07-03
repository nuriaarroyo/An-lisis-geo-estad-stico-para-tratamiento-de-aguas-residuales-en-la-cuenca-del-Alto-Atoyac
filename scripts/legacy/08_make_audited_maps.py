from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import MAPS_DIR, PROCESSED_DIR, ensure_output_dirs, log, normalize_text, read_gpkg, relpath


CATEGORY_COLORS = {
    "alta_relevancia_ambiental": "#b2182b",
    "media_relevancia_ambiental": "#ef8a62",
}

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


def source_filter(gdf, source_key: str):
    if gdf is None or gdf.empty or "source_folder" not in gdf.columns:
        return gdf
    mask = gdf["source_folder"].map(normalize_text).str.contains(source_key, na=False)
    return gdf.loc[mask].copy()


def line_geometries(gdf):
    if gdf is None or gdf.empty:
        return gdf
    return gdf[gdf.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()


def combined_bounds(*frames):
    valid = [gdf for gdf in frames if gdf is not None and not gdf.empty]
    if not valid:
        return None
    minxs, minys, maxxs, maxys = zip(*(gdf.total_bounds for gdf in valid))
    return min(minxs), min(minys), max(maxxs), max(maxys)


def crop_to_extent(gdf, bounds, pad=1600):
    if gdf is None or gdf.empty or bounds is None:
        return gdf
    minx, miny, maxx, maxy = bounds
    cropped = gdf.cx[minx - pad : maxx + pad, miny - pad : maxy + pad].copy()
    return cropped if not cropped.empty else gdf


def set_extent(ax, bounds, pad=600):
    if bounds is None:
        return
    minx, miny, maxx, maxy = bounds
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)


def plot_base(ax, agebs=None, localidades=None, hydro=None):
    if agebs is not None and not agebs.empty:
        agebs.plot(ax=ax, facecolor="#f7f7f7", edgecolor="#969696", linewidth=0.45)
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#525252", linewidth=0.8)
    if hydro is not None and not hydro.empty:
        hydro.plot(ax=ax, color="#2b8cbe", linewidth=0.55, alpha=0.8)


def finish_map(fig, ax, output_name: str) -> None:
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.tight_layout()
    out = MAPS_DIR / output_name
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    log(f"Mapa auditado guardado: {relpath(out)}")


def plot_region_audited(region_id: str, label: str, base_layers) -> None:
    denue = source_filter(base_layers["denue_auditado"], REGIONS[region_id]["source_key"])
    if denue is None or denue.empty:
        log(f"No hay DENUE auditado para {label}")
        return

    denue = denue[denue["categoria_relevancia_ambiental"].isin(CATEGORY_COLORS)].copy()
    if denue.empty:
        log(f"No hay categorias alta/media auditadas para {label}")
        return

    agebs = source_filter(base_layers["agebs"], REGIONS[region_id]["source_key"])
    localidades = source_filter(base_layers["localidades"], REGIONS[region_id]["source_key"])
    bounds = combined_bounds(agebs, localidades, denue)
    hydro = crop_to_extent(line_geometries(base_layers["hydro"]), bounds, pad=1600)

    fig, ax = plt.subplots(figsize=(10, 9))
    plot_base(ax, agebs=agebs, localidades=localidades, hydro=hydro)

    handles = []
    for category, color in CATEGORY_COLORS.items():
        group = denue[denue["categoria_relevancia_ambiental"].astype(str).eq(category)]
        if group.empty:
            continue
        group.plot(ax=ax, markersize=34, color=color, edgecolor="white", linewidth=0.35)
        handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=color, label=category, markersize=7))
    if handles:
        ax.legend(handles=handles, loc="best", fontsize=8, frameon=True, title="Categoria auditada")

    set_extent(ax, bounds)
    ax.set_title(f"{label}: DENUE textil auditado (solo alta y media)", fontsize=13)
    finish_map(fig, ax, f"14_{region_id}_denue_textil_auditado_alta_media.png")


def main() -> None:
    ensure_output_dirs()
    denue = optional_gpkg("denue_textil_auditado.gpkg")
    if denue is None or denue.empty:
        log("No existe data/processed/denue_textil_auditado.gpkg; ejecuta 07_apply_denue_audit.py primero.")
        return
    base_layers = {
        "denue_auditado": denue,
        "agebs": optional_gpkg("agebs.gpkg"),
        "localidades": optional_gpkg("localidades.gpkg"),
        "hydro": optional_gpkg("hidrografia.gpkg"),
    }
    for region_id, meta in REGIONS.items():
        plot_region_audited(region_id, meta["label"], base_layers)


if __name__ == "__main__":
    main()
