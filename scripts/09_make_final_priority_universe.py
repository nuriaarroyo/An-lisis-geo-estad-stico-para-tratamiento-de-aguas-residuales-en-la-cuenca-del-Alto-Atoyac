from __future__ import annotations

from datetime import datetime
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from matplotlib.lines import Line2D

from common import OUTPUTS_DIR, PROCESSED_DIR, ensure_output_dirs, log, normalize_text, read_gpkg, relpath, safe_to_file


SOURCE_GPKG = PROCESSED_DIR / "denue_universo_textil_clasificado.gpkg"
MANUAL_AUDIT = OUTPUTS_DIR / "tables" / "auditoria_enriquecida" / "auditoria_denue_textil_priorizada_manual.xlsx"
OUT_DIR = OUTPUTS_DIR / "universo_prioritario_denue"

LOCALITY_SLUGS = {
    "Huejotzingo": "huejotzingo",
    "Santa Ana Xalmimilulco": "santa_ana_xalmimilulco",
    "San Martin Texmelucan": "san_martin_texmelucan",
}

STAGE_COLORS = {
    "lavado_deslavado": "#b2182b",
    "lavanderia_industrial": "#d6604d",
    "tenido_tintoreria": "#7b3294",
    "acabado_textil": "#e08214",
    "tratamiento_especial_prenda": "#fdb863",
    "fabricacion_mezclilla": "#0571b0",
}


def audit_false_value(value: object) -> bool:
    text = normalize_text(value)
    text = text.replace("_", " ").strip()
    return text in {"false", "falso", "no", "0", "excluir", "fuera", "descartar"}


def read_manual_false_ids() -> pd.DataFrame:
    if not MANUAL_AUDIT.exists():
        log(f"No existe auditoria manual: {relpath(MANUAL_AUDIT)}")
        return pd.DataFrame(columns=["id", "clee", "categoria_auditada_manual", "notas_auditoria_manual"])
    audit = pd.read_excel(MANUAL_AUDIT, sheet_name="todos_clasificados", engine="openpyxl")
    if "categoria_auditada" not in audit.columns:
        return pd.DataFrame(columns=["id", "clee", "categoria_auditada_manual", "notas_auditoria_manual"])
    false_rows = audit[audit["categoria_auditada"].map(audit_false_value)].copy()
    for column in ["id", "clee", "notas_auditoria"]:
        if column not in false_rows.columns:
            false_rows[column] = ""
    out = false_rows[["id", "clee", "categoria_auditada", "notas_auditoria"]].copy()
    out = out.rename(
        columns={
            "categoria_auditada": "categoria_auditada_manual",
            "notas_auditoria": "notas_auditoria_manual",
        }
    )
    out["id"] = out["id"].astype(str)
    out["clee"] = out["clee"].astype(str)
    return out.drop_duplicates(subset=["id", "clee"], keep="last")


def add_manual_flags(gdf: gpd.GeoDataFrame, manual_false: pd.DataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["id"] = out["id"].astype(str) if "id" in out.columns else ""
    out["clee"] = out["clee"].astype(str) if "clee" in out.columns else ""
    out["flag_excluido_auditoria_manual_false"] = False
    out["categoria_auditada_manual"] = ""
    out["notas_auditoria_manual"] = ""
    if manual_false.empty:
        return out
    manual = manual_false.copy()
    manual["id_key"] = manual["id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    manual["clee_key"] = manual["clee"].astype(str).str.upper().str.strip()
    out["id_key"] = out["id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    out["clee_key"] = out["clee"].astype(str).str.upper().str.strip()

    id_false = set(manual.loc[manual["id_key"].ne(""), "id_key"])
    clee_false = set(manual.loc[manual["clee_key"].ne(""), "clee_key"])
    out["flag_excluido_auditoria_manual_false"] = out["id_key"].isin(id_false) | out["clee_key"].isin(clee_false)

    notes_by_id = manual.drop_duplicates("id_key", keep="last").set_index("id_key")["notas_auditoria_manual"].to_dict()
    cat_by_id = manual.drop_duplicates("id_key", keep="last").set_index("id_key")["categoria_auditada_manual"].to_dict()
    notes_by_clee = manual.drop_duplicates("clee_key", keep="last").set_index("clee_key")["notas_auditoria_manual"].to_dict()
    cat_by_clee = manual.drop_duplicates("clee_key", keep="last").set_index("clee_key")["categoria_auditada_manual"].to_dict()
    out["categoria_auditada_manual"] = out["id_key"].map(cat_by_id).fillna(out["clee_key"].map(cat_by_clee)).fillna("")
    out["notas_auditoria_manual"] = out["id_key"].map(notes_by_id).fillna(out["clee_key"].map(notes_by_clee)).fillna("")
    out = out.drop(columns=["id_key", "clee_key"])
    return gpd.GeoDataFrame(out, geometry="geometry", crs=gdf.crs)


def build_final_universe(classified: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame]:
    priority = classified["flag_estudio_prioritario"].astype(bool)
    manual_false = classified["flag_excluido_auditoria_manual_false"].astype(bool)
    final = classified.loc[priority & ~manual_false].copy()
    excluded = classified.loc[priority & manual_false].copy()
    manual_false_all = classified.loc[manual_false].copy()
    summary = pd.DataFrame(
        [
            {"indicador": "prioritarios_automaticos", "registros": int(priority.sum())},
            {"indicador": "registros_false_en_auditoria_manual", "registros": int(manual_false.sum())},
            {"indicador": "excluidos_por_auditoria_manual_false", "registros": int((priority & manual_false).sum())},
            {"indicador": "false_manual_ya_fuera_por_filtro_automatico", "registros": int((~priority & manual_false).sum())},
            {"indicador": "universo_prioritario_denue_final", "registros": len(final)},
        ]
    )
    return final, excluded, manual_false_all, summary


def line_geometries(gdf: gpd.GeoDataFrame | None) -> gpd.GeoDataFrame | None:
    if gdf is None or gdf.empty:
        return gdf
    return gdf[gdf.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()


def optional_gpkg(name: str) -> gpd.GeoDataFrame | None:
    path = PROCESSED_DIR / name
    return read_gpkg(path) if path.exists() else None


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


def static_map(points: gpd.GeoDataFrame, out_path: Path, title: str, localidades: gpd.GeoDataFrame | None, hydro: gpd.GeoDataFrame | None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bounds = points.total_bounds if not points.empty else None
    fig, ax = plt.subplots(figsize=(10, 8))
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#636363", linewidth=0.7)
    cropped_hydro = crop(hydro, bounds, pad=2500)
    if cropped_hydro is not None and not cropped_hydro.empty:
        cropped_hydro.plot(ax=ax, color="#2b8cbe", linewidth=0.55, alpha=0.85)
    handles = []
    if not points.empty:
        for value, group in points.groupby("etapa_productiva_sugerida", dropna=False):
            color = STAGE_COLORS.get(str(value), "#525252")
            group.plot(ax=ax, markersize=30, color=color, edgecolor="white", linewidth=0.3, alpha=0.9)
            handles.append(
                Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markeredgecolor="white", label=f"{value} ({len(group)})", markersize=7)
            )
    if handles:
        ax.legend(handles=handles[:14], loc="best", fontsize=7, frameon=True, title="etapa sugerida")
    set_extent(ax, bounds)
    ax.set_title(f"{title}\nUniverso prioritario DENUE final; no evidencia descarga ni contaminacion", fontsize=11)
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(out_path, dpi=230, bbox_inches="tight")
    plt.close(fig)


def interactive_map(points: gpd.GeoDataFrame, out_path: Path, title: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if points.empty:
        out_path.write_text(f"<html><body><h1>{title}</h1><p>Sin registros.</p></body></html>", encoding="utf-8")
        return
    gdf = points.to_crs("EPSG:4326")
    df = gdf.drop(columns="geometry").copy()
    df["lat_plot"] = gdf.geometry.y
    df["lon_plot"] = gdf.geometry.x
    hover_cols = [
        "id",
        "clee",
        "codigo_scian_original",
        "actividad_denue_original",
        "etapa_productiva_sugerida",
        "presion_ambiental_potencial",
        "distancia_hidrografia_m",
        "rango_distancia_hidrografia",
        "localidad",
        "municipio",
        "palabras_clave_etapa",
        "motivo_flag_estudio_prioritario",
        "query_maps",
    ]
    hover_cols = [c for c in hover_cols if c in df.columns]
    fig = px.scatter_map(
        df,
        lat="lat_plot",
        lon="lon_plot",
        color="etapa_productiva_sugerida",
        color_discrete_map=STAGE_COLORS,
        hover_name="nombre_de_la_unidad_economica",
        hover_data=hover_cols,
        zoom=11,
        height=760,
        title=f"{title}<br><sup>Universo prioritario DENUE final; auditoria manual FALSE excluida</sup>",
    )
    fig.update_traces(marker={"size": 9, "opacity": 0.86})
    fig.update_layout(map_style="open-street-map", margin={"r": 10, "t": 70, "l": 10, "b": 10})
    fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)


def write_outputs(final: gpd.GeoDataFrame, excluded: gpd.GeoDataFrame, manual_false_all: gpd.GeoDataFrame, summary: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final.drop(columns="geometry", errors="ignore").to_csv(OUT_DIR / "universo_prioritario_denue.csv", index=False, encoding="utf-8-sig")
    excluded.drop(columns="geometry", errors="ignore").to_csv(OUT_DIR / "excluidos_por_auditoria_manual_false.csv", index=False, encoding="utf-8-sig")
    manual_false_all.drop(columns="geometry", errors="ignore").to_csv(OUT_DIR / "auditoria_manual_false_detectados.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(OUT_DIR / "resumen_universo_prioritario_denue.csv", index=False, encoding="utf-8-sig")
    safe_to_file(final, OUT_DIR / "universo_prioritario_denue.gpkg", layer="universo_prioritario_denue")

    localidades = optional_gpkg("localidades.gpkg")
    hydro = line_geometries(optional_gpkg("hidrografia.gpkg"))
    if localidades is not None and not localidades.empty and localidades.crs != final.crs:
        localidades = localidades.to_crs(final.crs)
    if hydro is not None and not hydro.empty and hydro.crs != final.crs:
        hydro = hydro.to_crs(final.crs)

    rows = []
    for localidad, slug in LOCALITY_SLUGS.items():
        folder = OUT_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)
        local = final.loc[final["localidad"].eq(localidad)].copy()
        rows.append({"localidad": localidad, "registros": len(local), "carpeta": relpath(folder)})
        local.drop(columns="geometry", errors="ignore").to_csv(folder / f"tabla_universo_prioritario_denue_{slug}.csv", index=False, encoding="utf-8-sig")
        safe_to_file(local, folder / f"capa_universo_prioritario_denue_{slug}.gpkg", layer=f"prioritario_{slug}"[:63])
        static_map(local, folder / f"mapa_universo_prioritario_denue_{slug}.png", f"Universo prioritario DENUE final - {localidad}", localidades, hydro)
        interactive_map(local, folder / f"mapa_universo_prioritario_denue_{slug}.html", f"Universo prioritario DENUE final - {localidad}")
    pd.DataFrame(rows).to_csv(OUT_DIR / "resumen_por_localidad.csv", index=False, encoding="utf-8-sig")

    index_links = "\n".join(
        f"<li><a href='{slug}/mapa_universo_prioritario_denue_{slug}.html'>{localidad}</a></li>"
        for localidad, slug in LOCALITY_SLUGS.items()
    )
    html = f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>Universo prioritario DENUE final</title></head>
<body>
<h1>Universo prioritario DENUE final</h1>
<p>Generado: {datetime.now().isoformat(timespec="seconds")}</p>
<p>Incluye registros DENUE prioritarios despues de aplicar filtros automaticos y excluir registros con <code>categoria_auditada = FALSE</code> en la auditoria manual.</p>
<ul>{index_links}</ul>
</body>
</html>
"""
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    if not SOURCE_GPKG.exists():
        log("No existe denue_universo_textil_clasificado.gpkg. Ejecuta 02b primero.")
        return
    classified = read_gpkg(SOURCE_GPKG).copy()
    manual_false = read_manual_false_ids()
    classified = add_manual_flags(classified, manual_false)
    final, excluded, manual_false_all, summary = build_final_universe(classified)
    write_outputs(final, excluded, manual_false_all, summary)
    log(f"Universo prioritario DENUE final guardado: {relpath(OUT_DIR)} ({len(final)} registros)")


if __name__ == "__main__":
    main()
