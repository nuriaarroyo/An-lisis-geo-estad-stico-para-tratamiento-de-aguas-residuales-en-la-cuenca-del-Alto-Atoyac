from __future__ import annotations

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import MAPS_DIR, PROCESSED_DIR, ensure_output_dirs, log, normalize_text, read_gpkg, relpath


OUT_DIR = MAPS_DIR / "denue_clasificacion_productiva"
LOCALITY_SLUGS = {
    "Huejotzingo": "huejotzingo",
    "Santa Ana Xalmimilulco": "xalmimilulco",
    "San Martin Texmelucan": "san_martin",
}

COLORS = {
    "alta": "#b2182b",
    "media": "#ef8a62",
    "baja": "#4daf4a",
    "pendiente": "#7b3294",
    "muy_alta": "#67000d",
    "documental": "#756bb1",
}

STAGE_COLORS = {
    "lavado_deslavado": "#b2182b",
    "lavanderia_industrial": "#d6604d",
    "tenido_tintoreria": "#7b3294",
    "acabado_textil": "#e08214",
    "tratamiento_especial_prenda": "#fdb863",
    "fabricacion_mezclilla": "#0571b0",
    "confeccion_maquila": "#4393c3",
    "fabricacion_textil": "#92c5de",
    "bordado": "#66bd63",
    "estampado_serigrafia": "#1b7837",
    "comercio_simple": "#999999",
    "renta_prendas": "#bdbdbd",
    "confeccion_especializada_baja_relevancia": "#a6dba0",
    "revisar": "#762a83",
    "desconocido": "#525252",
}

MAP_SPECS = [
    ("01_universo_textil_inicial.png", "Universo textil detectado inicialmente", lambda g: g.index == g.index, "etapa_productiva_sugerida"),
    ("02_universo_textil_depurado.png", "Universo textil depurado", lambda g: ~g["decision_estudio_sugerida"].isin(["excluir_por_comercio", "excluir_por_renta", "excluir_del_universo_prioritario"]), "etapa_productiva_sugerida"),
    ("03_establecimientos_prioritarios_estudio.png", "Establecimientos prioritarios para investigacion", lambda g: g["flag_estudio_prioritario"], "presion_ambiental_potencial"),
    ("04_procesos_humedos_relevantes.png", "Senales compatibles con procesos humedos o tratamiento", lambda g: g["flag_proceso_humedo_relevante"], "etapa_productiva_sugerida"),
    ("05_lavado_deslavado.png", "Senales de lavado o deslavado", lambda g: g["flag_lavado_deslavado"], "etapa_productiva_sugerida"),
    ("06_lavanderias_industriales.png", "Lavanderias o tintorerias de prendas", lambda g: g["etapa_productiva_sugerida"].eq("lavanderia_industrial"), "presion_ambiental_potencial"),
    ("07_tenido_tintoreria.png", "Senales de tenido o tintoreria", lambda g: g["flag_tenido_tintoreria"], "etapa_productiva_sugerida"),
    ("08_acabado_tratamiento.png", "Senales de acabado o tratamiento especial", lambda g: g["flag_acabado_tratamiento"], "etapa_productiva_sugerida"),
    ("09_mezclilla_jeans.png", "Senales relacionadas con mezclilla o jeans", lambda g: g["flag_mezclilla_jeans"], "etapa_productiva_sugerida"),
    ("10_maquila_productiva.png", "Maquila o confeccion productiva", lambda g: g["flag_maquila_productiva"], "etapa_productiva_sugerida"),
    ("11_pendientes_auditoria.png", "Registros pendientes de auditoria documental", lambda g: g["requiere_auditoria_manual"], "prioridad_auditoria"),
    ("12_excluidos_comercio_renta.png", "Registros excluidos por comercio o renta", lambda g: g["flag_comercio_o_renta"], "etapa_productiva_sugerida"),
    ("13_confeccion_especializada_baja_relevancia.png", "Confeccion especializada de baja relevancia", lambda g: g["flag_confeccion_especializada_baja_relevancia"], "etapa_productiva_sugerida"),
    ("14_prioritarios_250m_hidrografia.png", "Prioritarios a 250 m o menos de hidrografia", lambda g: g["flag_estudio_prioritario"] & g["flag_cercania_hidrografia_250m"], "prioridad_campo"),
    ("15_nivel_confianza.png", "Clasificacion por nivel de confianza", lambda g: g.index == g.index, "confianza_clasificacion"),
    ("16_comparativo_municipio.png", "Universo clasificado por municipio", lambda g: g.index == g.index, "municipio"),
    ("17_prioridad_campo.png", "Prioridad de campo o revision territorial", lambda g: g["flag_prioridad_campo"], "prioridad_campo"),
    ("18_final_universo_recomendado.png", "Universo recomendado consolidado", lambda g: g["flag_estudio_prioritario"] | g["decision_estudio_sugerida"].isin(["incluir_contexto_productivo", "validar_documentalmente"]), "decision_estudio_sugerida"),
    ("19_universo_alcance_proyecto.png", "Universo de alcance del proyecto", lambda g: g["flag_universo_alcance_proyecto"], "etapa_productiva_sugerida"),
    ("20_fuera_alcance_contexto_textil.png", "Contexto textil fuera del alcance operativo", lambda g: g["flag_fuera_alcance_productivo_textil"], "etapa_productiva_sugerida"),
]

LOCALITY_MAP_SPECS = [
    ("universo_alcance", "Universo de alcance del proyecto", lambda g: g["flag_universo_alcance_proyecto"], "etapa_productiva_sugerida"),
    ("procesos_humedos", "Procesos humedos o tratamiento", lambda g: g["flag_proceso_humedo_relevante"], "etapa_productiva_sugerida"),
    ("lavado_deslavado", "Lavado o deslavado", lambda g: g["flag_lavado_deslavado"], "etapa_productiva_sugerida"),
    ("mezclilla_jeans", "Mezclilla o jeans", lambda g: g["flag_mezclilla_jeans"], "etapa_productiva_sugerida"),
]


def optional_gpkg(name: str) -> gpd.GeoDataFrame | None:
    path = PROCESSED_DIR / name
    return read_gpkg(path) if path.exists() else None


def line_geometries(gdf: gpd.GeoDataFrame | None) -> gpd.GeoDataFrame | None:
    if gdf is None or gdf.empty:
        return gdf
    return gdf[gdf.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()


def crop(gdf: gpd.GeoDataFrame | None, bounds, pad: float = 1500) -> gpd.GeoDataFrame | None:
    if gdf is None or gdf.empty or bounds is None:
        return gdf
    minx, miny, maxx, maxy = bounds
    out = gdf.cx[minx - pad : maxx + pad, miny - pad : maxy + pad].copy()
    return out if not out.empty else gdf


def set_extent(ax, bounds, pad: float = 900) -> None:
    if bounds is None:
        return
    minx, miny, maxx, maxy = bounds
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)


def color_for(column: str, value: object) -> str:
    text = str(value)
    if column == "etapa_productiva_sugerida":
        return STAGE_COLORS.get(text, "#525252")
    if column in {"presion_ambiental_potencial", "prioridad_campo"}:
        return COLORS.get(text, "#525252")
    if column == "confianza_clasificacion":
        return {"alta": "#1a9850", "media": "#fee08b", "baja": "#d73027"}.get(text, "#525252")
    if column == "prioridad_auditoria":
        return {"alta": "#d73027", "media": "#fc8d59", "baja": "#91bfdb"}.get(text, "#525252")
    return "#377eb8"


def plot_base(ax, localidades=None, hydro=None) -> None:
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#636363", linewidth=0.7)
    if hydro is not None and not hydro.empty:
        hydro.plot(ax=ax, color="#2b8cbe", linewidth=0.55, alpha=0.85)


def plot_map(denue: gpd.GeoDataFrame, localidades: gpd.GeoDataFrame | None, hydro: gpd.GeoDataFrame | None, filename: str, title: str, mask_func, color_col: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mask = mask_func(denue)
    points = denue.loc[mask].copy()
    bounds_source = points if not points.empty else denue
    bounds = bounds_source.total_bounds if not bounds_source.empty else None
    fig, ax = plt.subplots(figsize=(11, 9))
    plot_base(ax, localidades=localidades, hydro=crop(hydro, bounds, pad=2500))
    handles = []
    if not points.empty:
        for value, group in points.groupby(color_col, dropna=False):
            color = color_for(color_col, value)
            group.plot(ax=ax, markersize=24, color=color, edgecolor="white", linewidth=0.25, alpha=0.88)
            label = str(value) if str(value) else "sin dato"
            handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markeredgecolor="white", label=f"{label} ({len(group)})", markersize=7))
    if handles:
        ax.legend(handles=handles[:16], loc="best", fontsize=7, frameon=True, title=color_col.replace("_", " "))
    set_extent(ax, bounds)
    ax.set_title(f"{title}\nPrioridad de investigacion; no evidencia descarga ni contaminacion", fontsize=12)
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.tight_layout()
    out = OUT_DIR / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=230, bbox_inches="tight")
    plt.close(fig)
    log(f"Mapa clasificacion guardado: {relpath(out)} ({len(points)} puntos)")


def plot_locality_maps(denue: gpd.GeoDataFrame, localidades: gpd.GeoDataFrame | None, hydro: gpd.GeoDataFrame | None) -> None:
    for localidad, slug in LOCALITY_SLUGS.items():
        local = denue.loc[denue["localidad"].eq(localidad)].copy()
        if local.empty:
            continue
        for label, title, mask_func, color_col in LOCALITY_MAP_SPECS:
            plot_map(
                local,
                localidades,
                hydro,
                f"localidades/{slug}_{label}.png",
                f"{title} - {localidad}",
                mask_func,
                color_col,
            )


def main() -> None:
    ensure_output_dirs()
    src = PROCESSED_DIR / "denue_universo_textil_clasificado.gpkg"
    if not src.exists():
        log("No existe denue_universo_textil_clasificado.gpkg. Ejecuta 02b primero.")
        return
    denue = read_gpkg(src)
    localidades = optional_gpkg("localidades.gpkg")
    hydro = line_geometries(optional_gpkg("hidrografia.gpkg"))
    if localidades is not None and not localidades.empty and localidades.crs != denue.crs:
        localidades = localidades.to_crs(denue.crs)
    if hydro is not None and not hydro.empty and hydro.crs != denue.crs:
        hydro = hydro.to_crs(denue.crs)
    for filename, title, mask_func, color_col in MAP_SPECS:
        plot_map(denue, localidades, hydro, filename, title, mask_func, color_col)
    plot_locality_maps(denue, localidades, hydro)


if __name__ == "__main__":
    main()
