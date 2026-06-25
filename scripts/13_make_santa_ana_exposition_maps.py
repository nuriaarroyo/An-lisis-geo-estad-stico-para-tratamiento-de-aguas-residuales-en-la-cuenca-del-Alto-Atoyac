from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from shapely.geometry import LineString

from common import OUTPUTS_DIR, PROCESSED_DIR, ensure_output_dirs, read_gpkg, relpath, safe_to_file


OUT_DIR = OUTPUTS_DIR / "auditoria_santa_ana_mh_filtrado"
LAYERS_DIR = OUT_DIR / "capas_qgis"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"
TARGET_CRS = "EPSG:6372"

PATHS = {
    "santa_actual": OUTPUTS_DIR
    / "universo_prioritario_denue"
    / "santa_ana_xalmimilulco"
    / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg",
    "universo2026": OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg",
    "denue2026_raw": PROCESSED_DIR / "denue2026_raw.gpkg",
    "mh2": PROCESSED_DIR / "capa_maryhelen" / "capa MH2.shp",
    "mh_filtrado": PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp",
    "mayra": PROCESSED_DIR / "capa_mayra" / "capa mayra.shp",
    "localidades": PROCESSED_DIR / "localidades.gpkg",
    "hidrografia": PROCESSED_DIR / "hidrografia.gpkg",
}

COLORS = {
    "coincide_actual_y_filtro2026": "#1b9e77",
    "actual_falta_en_filtro2026": "#d73027",
    "nuevo_filtro2026_santa_ana": "#7570b3",
    "coincide_actual_y_denue2026_base": "#1b9e77",
    "actual_falta_en_denue2026_base": "#d73027",
    "coincide_actual_y_mh2_base": "#1b9e77",
    "actual_falta_en_mh2_base": "#d73027",
    "actual_coincide_id_mh_filtrado": "#1b9e77",
    "mh_filtrado_coincide_id_actual": "#66c2a5",
    "actual_falta_en_mh_filtrado": "#d73027",
    "mh_filtrado_con_id_no_en_actual": "#e7298a",
    "mh_filtrado_sin_id": "#969696",
    "punto_actual_mismo_id": "#1b9e77",
    "punto_mh_mismo_id_desplazado": "#d95f02",
    "linea_mismo_id_desplazado": "#d95f02",
    "mayra_nombre_exactoy_cerca": "#1b9e77",
    "mayra_revisar_nombre_o_distancia": "#d95f02",
}


def ensure_dirs() -> None:
    ensure_output_dirs()
    for path in [OUT_DIR, LAYERS_DIR, MAPS_DIR, TABLES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def norm_id(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def norm_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).upper().strip()
    text = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_any(path: Path) -> gpd.GeoDataFrame:
    gdf = read_gpkg(path) if path.suffix.lower() == ".gpkg" else gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf.to_crs(TARGET_CRS)


def add_key(gdf: gpd.GeoDataFrame, id_col: str = "id") -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["_id_key"] = norm_id(out[id_col]) if id_col in out.columns else ""
    out["_id_key"] = out["_id_key"].replace({"nan": "", "None": ""})
    return out


def name_series(gdf: pd.DataFrame) -> pd.Series:
    for col in ["nombre_de_la_unidad_economica", "nom_estab", "Nombre", "Name"]:
        if col in gdf.columns:
            return gdf[col].fillna("").astype(str)
    return pd.Series("", index=gdf.index)


def keep_points(gdf: gpd.GeoDataFrame, cols: list[str]) -> gpd.GeoDataFrame:
    keep = [c for c in cols if c in gdf.columns]
    if "geometry" not in keep:
        keep.append("geometry")
    out = gdf[keep].copy()
    out["nombre_mapa"] = name_series(out)
    return out


def santa_vs_filtered_2026(santa: gpd.GeoDataFrame, universo2026: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    santa = add_key(santa)
    universo2026 = add_key(universo2026)
    u_santa = universo2026[universo2026["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")].copy()
    santa_ids = set(santa["_id_key"]) - {""}
    u_ids = set(u_santa["_id_key"]) - {""}

    current = keep_points(
        santa,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "etapa_productiva_sugerida",
            "distancia_hidrografia_m",
            "_id_key",
        ],
    )
    current["comparacion"] = current["_id_key"].map(
        lambda value: "coincide_actual_y_filtro2026" if value in u_ids else "actual_falta_en_filtro2026"
    )
    current["fuente_mapa"] = "universo_actual_santa_ana"

    new = u_santa[~u_santa["_id_key"].isin(santa_ids)].copy()
    new_points = keep_points(
        new,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "etapa_productiva_sugerida",
            "distancia_hidrografia_m",
            "_id_key",
        ],
    )
    new_points["comparacion"] = "nuevo_filtro2026_santa_ana"
    new_points["fuente_mapa"] = "universo_filtrado_2026"
    return gpd.GeoDataFrame(pd.concat([current, new_points], ignore_index=True), geometry="geometry", crs=santa.crs)


def santa_vs_base(santa: gpd.GeoDataFrame, source: gpd.GeoDataFrame, source_id_col: str, ok_label: str, missing_label: str) -> gpd.GeoDataFrame:
    santa = add_key(santa)
    source = add_key(source, source_id_col)
    source_ids = set(source["_id_key"]) - {""}
    out = keep_points(
        santa,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "etapa_productiva_sugerida",
            "_id_key",
        ],
    )
    out["comparacion"] = out["_id_key"].map(lambda value: ok_label if value in source_ids else missing_label)
    out["fuente_mapa"] = "universo_actual_santa_ana"
    return out


def santa_vs_mh_filtrado(santa: gpd.GeoDataFrame, mh: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    santa = add_key(santa)
    mh = add_key(mh, "ID DENUE")
    santa_ids = set(santa["_id_key"]) - {""}
    mh_ids = set(mh["_id_key"]) - {""}

    current = keep_points(
        santa,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "etapa_productiva_sugerida",
            "_id_key",
        ],
    )
    current["comparacion"] = current["_id_key"].map(
        lambda value: "actual_coincide_id_mh_filtrado" if value in mh_ids else "actual_falta_en_mh_filtrado"
    )
    current["fuente_mapa"] = "universo_actual_santa_ana"

    mh_points = keep_points(mh, ["Name", "DENUE", "ID DENUE", "_id_key"])
    mh_points["id"] = mh_points["_id_key"]
    mh_points["comparacion"] = mh_points["_id_key"].map(
        lambda value: "mh_filtrado_sin_id"
        if not value
        else ("mh_filtrado_coincide_id_actual" if value in santa_ids else "mh_filtrado_con_id_no_en_actual")
    )
    mh_points["fuente_mapa"] = "mh_filtrado"

    return gpd.GeoDataFrame(pd.concat([current, mh_points], ignore_index=True), geometry="geometry", crs=santa.crs)


def same_id_displacement(santa: gpd.GeoDataFrame, mh: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    santa = add_key(santa)
    mh = add_key(mh, "ID DENUE")
    pairs = santa.merge(
        mh[["_id_key", "Name", "DENUE", "ID DENUE", "geometry"]],
        on="_id_key",
        how="inner",
        suffixes=("_actual", "_mh"),
    )
    point_rows = []
    line_rows = []
    for _, row in pairs.iterrows():
        g_actual = row["geometry_actual"]
        g_mh = row["geometry_mh"]
        dist = float(g_actual.distance(g_mh))
        point_rows.append(
            {
                "id": row["_id_key"],
                "nombre_mapa": row.get("nombre_de_la_unidad_economica", ""),
                "comparacion": "punto_actual_mismo_id",
                "fuente_mapa": "universo_actual_santa_ana",
                "distancia_m_actual_vs_mh": dist,
                "geometry": g_actual,
            }
        )
        point_rows.append(
            {
                "id": row["_id_key"],
                "nombre_mapa": f"MH Name {row.get('Name', '')}",
                "comparacion": "punto_mh_mismo_id_desplazado",
                "fuente_mapa": "mh_filtrado",
                "distancia_m_actual_vs_mh": dist,
                "geometry": g_mh,
            }
        )
        line_rows.append(
            {
                "id": row["_id_key"],
                "nombre_actual": row.get("nombre_de_la_unidad_economica", ""),
                "name_mh": row.get("Name", ""),
                "distancia_m_actual_vs_mh": dist,
                "comparacion": "linea_mismo_id_desplazado",
                "geometry": LineString([(g_actual.x, g_actual.y), (g_mh.x, g_mh.y)]),
            }
        )
    points = gpd.GeoDataFrame(point_rows, geometry="geometry", crs=santa.crs)
    lines = gpd.GeoDataFrame(line_rows, geometry="geometry", crs=santa.crs)
    return points, lines


def mayra_nearest(mayra: gpd.GeoDataFrame, denue2026: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    denue2026 = add_key(denue2026)
    denue2026["_name_norm"] = name_series(denue2026).map(norm_text)
    denue2026["nombre_denue2026_cercano"] = name_series(denue2026)
    mayra = mayra.copy()
    mayra["_name_norm"] = mayra["Nombre"].map(norm_text) if "Nombre" in mayra.columns else ""
    right = denue2026[["_id_key", "clee", "nombre_denue2026_cercano", "_name_norm", "geometry"]].reset_index(drop=True)
    nearest = gpd.sjoin_nearest(mayra, right, how="left", distance_col="distancia_m_denue2026")
    nearest["nombre_exactamente_en_denue2026"] = nearest["_name_norm_left"].eq(nearest["_name_norm_right"])
    nearest["comparacion"] = nearest.apply(
        lambda row: "mayra_nombre_exactoy_cerca"
        if bool(row["nombre_exactamente_en_denue2026"]) and float(row["distancia_m_denue2026"]) <= 25
        else "mayra_revisar_nombre_o_distancia",
        axis=1,
    )
    nearest = nearest.rename(columns={"_id_key": "id_denue2026_cercano", "clee": "clee_denue2026_cercano"})
    nearest["nombre_mapa"] = nearest.get("Nombre", "")
    nearest["fuente_mapa"] = "mayra"

    lines = []
    for _, row in nearest.iterrows():
        idx = row.get("index_right")
        if pd.isna(idx):
            continue
        g2 = right.loc[int(idx), "geometry"]
        g1 = row.geometry
        lines.append(
            {
                "Nombre": row.get("Nombre", ""),
                "id_denue2026_cercano": row.get("id_denue2026_cercano", ""),
                "nombre_denue2026_cercano": row.get("nombre_denue2026_cercano", ""),
                "distancia_m_denue2026": row.get("distancia_m_denue2026", pd.NA),
                "comparacion": row.get("comparacion", ""),
                "geometry": LineString([(g1.x, g1.y), (g2.x, g2.y)]),
            }
        )
    return nearest, gpd.GeoDataFrame(lines, geometry="geometry", crs=mayra.crs)


def base_layers(crs: str) -> tuple[gpd.GeoDataFrame | None, gpd.GeoDataFrame | None]:
    localidades = read_any(PATHS["localidades"]) if PATHS["localidades"].exists() else None
    hydro = read_any(PATHS["hidrografia"]) if PATHS["hidrografia"].exists() else None
    if localidades is not None and not localidades.empty:
        localidades = localidades.to_crs(crs)
    if hydro is not None and not hydro.empty:
        hydro = hydro.to_crs(crs)
        hydro = hydro[hydro.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()
    return localidades, hydro


def static_map(gdf: gpd.GeoDataFrame, name: str, title: str, line_gdf: gpd.GeoDataFrame | None = None) -> None:
    if gdf.empty:
        return
    localidades, hydro = base_layers(gdf.crs)
    fig, ax = plt.subplots(figsize=(10.5, 8), dpi=180)
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#737373", linewidth=0.5)
    if hydro is not None and not hydro.empty:
        minx, miny, maxx, maxy = gdf.total_bounds
        hydro.cx[minx - 3000 : maxx + 3000, miny - 3000 : maxy + 3000].plot(
            ax=ax, color="#2b8cbe", linewidth=0.45, alpha=0.75
        )
    if line_gdf is not None and not line_gdf.empty:
        line_gdf.plot(ax=ax, color="#d95f02", linewidth=0.85, alpha=0.65)
    for status, group in gdf.groupby("comparacion", dropna=False):
        color = COLORS.get(str(status), "#525252")
        marker = "x" if "falta" in str(status) or "desplazado" in str(status) else "o"
        group.plot(ax=ax, color=color, marker=marker, markersize=44, edgecolor="white", linewidth=0.35, label=str(status))
    minx, miny, maxx, maxy = gdf.total_bounds
    if line_gdf is not None and not line_gdf.empty:
        lminx, lminy, lmaxx, lmaxy = line_gdf.total_bounds
        minx, miny, maxx, maxy = min(minx, lminx), min(miny, lminy), max(maxx, lmaxx), max(maxy, lmaxy)
    pad_x = max((maxx - minx) * 0.12, 250)
    pad_y = max((maxy - miny) * 0.12, 250)
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()
    ax.legend(loc="best", fontsize=7, frameon=True)
    fig.tight_layout()
    fig.savefig(MAPS_DIR / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def interactive_map(gdf: gpd.GeoDataFrame, name: str, title: str) -> None:
    if gdf.empty:
        return
    web = gdf.to_crs("EPSG:4326").copy()
    web["lon"] = web.geometry.x
    web["lat"] = web.geometry.y
    hover = [
        c
        for c in [
            "id",
            "_id_key",
            "clee",
            "nombre_mapa",
            "comparacion",
            "fuente_mapa",
            "localidad",
            "etapa_productiva_sugerida",
            "distancia_hidrografia_m",
            "distancia_m_actual_vs_mh",
            "distancia_m_denue2026",
            "id_denue2026_cercano",
            "nombre_denue2026_cercano",
            "ID DENUE",
            "DENUE",
        ]
        if c in web.columns
    ]
    color_map = {status: COLORS.get(status, "#525252") for status in sorted(web["comparacion"].astype(str).unique())}
    fig = px.scatter_map(
        web,
        lat="lat",
        lon="lon",
        color="comparacion",
        color_discrete_map=color_map,
        hover_name="nombre_mapa" if "nombre_mapa" in web.columns else None,
        hover_data=hover,
        zoom=12,
        height=720,
        title=title,
    )
    fig.update_layout(map_style="open-street-map", margin={"r": 10, "t": 55, "l": 10, "b": 10})
    fig.write_html(MAPS_DIR / f"{name}.html", include_plotlyjs="cdn")


def save_layer(
    gdf: gpd.GeoDataFrame,
    name: str,
    title: str,
    line_gdf: gpd.GeoDataFrame | None = None,
    line_name: str | None = None,
) -> pd.DataFrame:
    safe_to_file(gdf, LAYERS_DIR / f"{name}.gpkg", layer=name)
    gdf.drop(columns="geometry", errors="ignore").to_csv(TABLES_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    if line_gdf is not None and not line_gdf.empty and line_name:
        safe_to_file(line_gdf, LAYERS_DIR / f"{line_name}.gpkg", layer=line_name)
        line_gdf.drop(columns="geometry", errors="ignore").to_csv(
            TABLES_DIR / f"{line_name}.csv", index=False, encoding="utf-8-sig"
        )
    static_map(gdf, name, title, line_gdf=line_gdf)
    interactive_map(gdf, name, title)
    counts = gdf.groupby("comparacion", dropna=False).size().reset_index(name="registros")
    counts.insert(0, "capa", name)
    return counts


def write_manifest(summaries: pd.DataFrame) -> None:
    source_rows = [
        {"fuente": key, "ruta": relpath(path)}
        for key, path in PATHS.items()
        if key not in {"localidades", "hidrografia"} and path.exists()
    ]
    pd.DataFrame(source_rows).to_csv(TABLES_DIR / "fuentes_usadas.csv", index=False, encoding="utf-8-sig")
    summaries.to_csv(TABLES_DIR / "resumen_santa_ana_exposicion.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Santa Ana: exposicion de coincidencias y problema MH filtrado",
        "",
        "Lectura principal: el universo actual de Santa Ana coincide con DENUE 2026/MH2 salvo un registro; el problema fuerte aparece en `capa MH`, que no conserva bien correspondencia por ID y punto.",
        "",
        "## Conteos clave",
        "",
        "| capa | comparacion | registros |",
        "| --- | --- | --- |",
    ]
    for _, row in summaries.astype(str).iterrows():
        lines.append(f"| {row['capa']} | {row['comparacion']} | {row['registros']} |")
    lines.extend(
        [
            "",
            "## Fuentes usadas",
            "",
            "| fuente | ruta |",
            "| --- | --- |",
        ]
    )
    for row in source_rows:
        lines.append(f"| {row['fuente']} | {row['ruta']} |")
    lines.extend(
        [
            "",
            "## Nota",
            "",
            "Estos mapas son para limpieza y auditoria. No constituyen evidencia de descarga, contaminacion ni incumplimiento.",
        ]
    )
    (OUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    santa = read_any(PATHS["santa_actual"])
    u2026 = read_any(PATHS["universo2026"])
    denue2026 = read_any(PATHS["denue2026_raw"])
    mh2 = read_any(PATHS["mh2"])
    mh = read_any(PATHS["mh_filtrado"])
    mayra = read_any(PATHS["mayra"])

    summaries = []
    summaries.append(
        save_layer(
            santa_vs_filtered_2026(santa, u2026),
            "01_santa_ana_actual_vs_filtrado_2026",
            "Santa Ana: universo actual vs filtrado DENUE 2026",
        )
    )
    summaries.append(
        save_layer(
            santa_vs_base(
                santa,
                denue2026,
                "id",
                "coincide_actual_y_denue2026_base",
                "actual_falta_en_denue2026_base",
            ),
            "02_santa_ana_actual_vs_denue2026_base",
            "Santa Ana: universo actual vs DENUE 2026 base",
        )
    )
    summaries.append(
        save_layer(
            santa_vs_base(santa, mh2, "id", "coincide_actual_y_mh2_base", "actual_falta_en_mh2_base"),
            "03_santa_ana_actual_vs_mh2_base",
            "Santa Ana: universo actual vs Maryhelen MH2 base",
        )
    )
    summaries.append(
        save_layer(
            santa_vs_mh_filtrado(santa, mh),
            "04_santa_ana_actual_vs_mh_filtrado",
            "Santa Ana: universo actual vs MH filtrado",
        )
    )
    displaced_points, displaced_lines = same_id_displacement(santa, mh)
    summaries.append(
        save_layer(
            displaced_points,
            "05_mh_filtrado_mismos_ids_desplazados",
            "MH filtrado: mismos IDs, puntos desplazados",
            line_gdf=displaced_lines,
            line_name="05b_lineas_mismos_ids_actual_vs_mh_filtrado",
        )
    )
    mayra_points, mayra_lines = mayra_nearest(mayra, denue2026)
    summaries.append(
        save_layer(
            mayra_points,
            "06_mayra_vs_denue2026_vecino_cercano",
            "Mayra vs DENUE 2026: vecino mas cercano",
            line_gdf=mayra_lines,
            line_name="06b_lineas_mayra_a_denue2026_cercano",
        )
    )
    summary = pd.concat(summaries, ignore_index=True)
    write_manifest(summary)
    print(f"[atoyac] Paquete Santa Ana/MH guardado en {relpath(OUT_DIR)}")


if __name__ == "__main__":
    main()
