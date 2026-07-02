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


OUT_DIR = OUTPUTS_DIR / "auditoria_coincidencias_denue_2026"
LAYERS_DIR = OUT_DIR / "capas_qgis"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"

TARGET_CRS = "EPSG:6372"

PATHS = {
    "current_all": OUTPUTS_DIR / "universo_prioritario_denue" / "universo_prioritario_denue.gpkg",
    "current_santa": OUTPUTS_DIR
    / "universo_prioritario_denue"
    / "santa_ana_xalmimilulco"
    / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg",
    "denue2026": PROCESSED_DIR / "denue2026_raw.gpkg",
    "universe2026": OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg",
    "maryhelen_mh2": PROCESSED_DIR / "capa_maryhelen" / "capa MH2.shp",
    "maryhelen_mh": PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp",
    "mayra": PROCESSED_DIR / "capa_mayra" / "capa mayra.shp",
    "localidades": PROCESSED_DIR / "localidades.gpkg",
    "hidrografia": PROCESSED_DIR / "hidrografia.gpkg",
    "alerts2026": OUTPUTS_DIR
    / "tables"
    / "denue2026_clasificacion_productiva"
    / "alertas_posibles_falsos_positivos_prioritarios_2026.csv",
}

COLORS = {
    "en_ambos": "#1b9e77",
    "solo_universo_actual": "#d95f02",
    "solo_universo_2026": "#7570b3",
    "actual_y_denue2026": "#1b9e77",
    "actual_falta_en_denue2026": "#d73027",
    "actual_y_maryhelen_mh2": "#1b9e77",
    "actual_falta_en_maryhelen_mh2": "#d73027",
    "actual_y_maryhelen_mh": "#1b9e77",
    "actual_falta_en_maryhelen_mh": "#d73027",
    "solo_maryhelen_mh": "#7570b3",
    "solo_denue2026": "#3182bd",
    "solo_maryhelen_mh2": "#e7298a",
    "mayra_nombre_exactoy_cerca": "#1b9e77",
    "mayra_revisar_nombre_o_distancia": "#d95f02",
    "posible_falso_positivo_2026": "#d73027",
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


def to_target(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf.to_crs(TARGET_CRS)


def read_layer(key: str) -> gpd.GeoDataFrame:
    path = PATHS[key]
    if not path.exists():
        return gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)
    gdf = read_gpkg(path) if path.suffix.lower() == ".gpkg" else gpd.read_file(path)
    return to_target(gdf)


def add_id_key(gdf: gpd.GeoDataFrame, column: str = "id") -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["_id_key"] = norm_id(out[column]) if column in out.columns else ""
    return out


def denue_name(row: pd.Series) -> str:
    for col in ["nombre_de_la_unidad_economica", "nom_estab", "Nombre", "DENUE"]:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col])
    return ""


def compact_points(gdf: gpd.GeoDataFrame, keep: list[str]) -> gpd.GeoDataFrame:
    cols = [c for c in keep if c in gdf.columns]
    if "geometry" not in cols:
        cols.append("geometry")
    out = gdf[cols].copy()
    out["nombre_mapa"] = [denue_name(row) for _, row in out.iterrows()]
    return out


def current_vs_universe2026(current: gpd.GeoDataFrame, universe2026: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    current = add_id_key(current)
    universe2026 = add_id_key(universe2026)
    current_ids = set(current["_id_key"])
    new_ids = set(universe2026["_id_key"])

    current_out = compact_points(
        current,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "municipio",
            "etapa_productiva_sugerida",
            "distancia_hidrografia_m",
            "_id_key",
        ],
    )
    current_out["comparacion"] = current_out["_id_key"].map(
        lambda value: "en_ambos" if value in new_ids else "solo_universo_actual"
    )
    current_out["fuente_mapa"] = "universo_actual"

    new_only = universe2026.loc[~universe2026["_id_key"].isin(current_ids)].copy()
    new_out = compact_points(
        new_only,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "municipio",
            "etapa_productiva_sugerida",
            "distancia_hidrografia_m",
            "_id_key",
        ],
    )
    new_out["comparacion"] = "solo_universo_2026"
    new_out["fuente_mapa"] = "universo_2026"
    return gpd.GeoDataFrame(pd.concat([current_out, new_out], ignore_index=True), geometry="geometry", crs=current.crs)


def current_against_raw_source(
    current_santa: gpd.GeoDataFrame,
    source: gpd.GeoDataFrame,
    label_match: str,
    label_missing: str,
    id_col_source: str = "id",
) -> gpd.GeoDataFrame:
    current_santa = add_id_key(current_santa)
    source = add_id_key(source, id_col_source)
    source_ids = set(source["_id_key"])
    out = compact_points(
        current_santa,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "municipio",
            "etapa_productiva_sugerida",
            "distancia_hidrografia_m",
            "_id_key",
        ],
    )
    out["comparacion"] = out["_id_key"].map(lambda value: label_match if value in source_ids else label_missing)
    out["fuente_mapa"] = "universo_actual_santa_ana"
    return out


def current_vs_maryhelen_mh(current_santa: gpd.GeoDataFrame, mh: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    current_santa = add_id_key(current_santa)
    mh = add_id_key(mh, "ID DENUE")
    current_ids = set(current_santa["_id_key"])
    mh_ids = set(mh["_id_key"]) - {""}

    current_out = compact_points(
        current_santa,
        [
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "municipio",
            "etapa_productiva_sugerida",
            "_id_key",
        ],
    )
    current_out["comparacion"] = current_out["_id_key"].map(
        lambda value: "actual_y_maryhelen_mh" if value in mh_ids else "actual_falta_en_maryhelen_mh"
    )
    current_out["fuente_mapa"] = "universo_actual_santa_ana"

    mh_only = mh.loc[~mh["_id_key"].isin(current_ids)].copy()
    mh_out = compact_points(mh_only, ["ID DENUE", "DENUE", "_id_key"])
    mh_out["id"] = mh_out.get("ID DENUE", "")
    mh_out["comparacion"] = "solo_maryhelen_mh"
    mh_out["fuente_mapa"] = "maryhelen_mh"
    return gpd.GeoDataFrame(pd.concat([current_out, mh_out], ignore_index=True), geometry="geometry", crs=current_santa.crs)


def denue2026_vs_maryhelen_mh2(denue2026: gpd.GeoDataFrame, mh2: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    denue2026 = add_id_key(denue2026)
    mh2 = add_id_key(mh2)
    d_ids = set(denue2026["_id_key"])
    m_ids = set(mh2["_id_key"])

    d_only = denue2026.loc[~denue2026["_id_key"].isin(m_ids)].copy()
    d_out = compact_points(d_only, ["id", "clee", "nom_estab", "codigo_act", "nombre_act", "localidad", "_id_key"])
    d_out["comparacion"] = "solo_denue2026"
    d_out["fuente_mapa"] = "denue2026"

    m_only = mh2.loc[~mh2["_id_key"].isin(d_ids)].copy()
    m_out = compact_points(m_only, ["id", "clee", "nom_estab", "codigo_act", "nombre_act", "localidad", "_id_key"])
    m_out["comparacion"] = "solo_maryhelen_mh2"
    m_out["fuente_mapa"] = "maryhelen_mh2"

    return gpd.GeoDataFrame(pd.concat([d_out, m_out], ignore_index=True), geometry="geometry", crs=denue2026.crs)


def mayra_nearest_denue2026(mayra: gpd.GeoDataFrame, denue2026: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    mayra = mayra.copy()
    denue2026 = add_id_key(denue2026)
    name_col = "nom_estab" if "nom_estab" in denue2026.columns else "nombre_de_la_unidad_economica"
    code_col = "codigo_act" if "codigo_act" in denue2026.columns else "codigo_de_la_clase_actividad_scian"
    activity_col = "nombre_act" if "nombre_act" in denue2026.columns else "nombre_clase_actividad_scian"
    mayra["_name_norm"] = mayra["Nombre"].map(norm_text) if "Nombre" in mayra.columns else ""
    denue2026["_name_norm"] = denue2026[name_col].map(norm_text) if name_col in denue2026.columns else ""
    denue2026["nombre_denue2026_cercano"] = denue2026[name_col] if name_col in denue2026.columns else ""
    denue2026["codigo_denue2026_cercano"] = denue2026[code_col] if code_col in denue2026.columns else ""
    denue2026["actividad_denue2026_cercana"] = denue2026[activity_col] if activity_col in denue2026.columns else ""
    denue_keep = denue2026[
        [
            "_id_key",
            "clee",
            "nombre_denue2026_cercano",
            "codigo_denue2026_cercano",
            "actividad_denue2026_cercana",
            "_name_norm",
            "geometry",
        ]
    ].copy()
    denue_keep = denue_keep.reset_index(drop=True)
    nearest = gpd.sjoin_nearest(mayra, denue_keep, how="left", distance_col="distancia_m_denue2026")
    nearest["nombre_exactamente_en_denue2026"] = nearest["_name_norm_left"].eq(nearest["_name_norm_right"])
    nearest["comparacion"] = nearest.apply(
        lambda row: "mayra_nombre_exactoy_cerca"
        if bool(row["nombre_exactamente_en_denue2026"]) and float(row["distancia_m_denue2026"]) <= 25
        else "mayra_revisar_nombre_o_distancia",
        axis=1,
    )
    nearest = nearest.rename(
        columns={
            "_id_key": "id_denue2026_cercano",
            "clee": "clee_denue2026_cercano",
        }
    )
    nearest["nombre_mapa"] = nearest.get("Nombre", "")
    nearest["fuente_mapa"] = "mayra"

    denue_by_index = denue_keep.reset_index(drop=True)
    lines = []
    for _, row in nearest.iterrows():
        right_index = row.get("index_right")
        if pd.isna(right_index):
            continue
        denue_geom = denue_by_index.loc[int(right_index), "geometry"]
        if row.geometry is not None and denue_geom is not None:
            try:
                start_geom = row.geometry.representative_point()
                end_geom = denue_geom.representative_point()
                start = (float(start_geom.x), float(start_geom.y))
                end = (float(end_geom.x), float(end_geom.y))
            except Exception:
                continue
            lines.append(
                {
                    "Nombre": row.get("Nombre", ""),
                    "id_denue2026_cercano": row.get("id_denue2026_cercano", ""),
                    "nombre_denue2026_cercano": row.get("nombre_denue2026_cercano", ""),
                    "distancia_m_denue2026": row.get("distancia_m_denue2026", pd.NA),
                    "comparacion": row.get("comparacion", ""),
                    "geometry": LineString([start, end]),
                }
            )
    line_gdf = gpd.GeoDataFrame(lines, geometry="geometry", crs=mayra.crs)
    return nearest, line_gdf


def alerts2026_layer(universe2026: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    csv_path = PATHS["alerts2026"]
    if not csv_path.exists() or universe2026.empty:
        return gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)
    alerts = pd.read_csv(csv_path, encoding="utf-8-sig")
    if alerts.empty or "id" not in alerts.columns:
        return gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)
    universe2026 = add_id_key(universe2026)
    alert_ids = set(norm_id(alerts["id"]))
    out = universe2026.loc[universe2026["_id_key"].isin(alert_ids)].copy()
    out["comparacion"] = "posible_falso_positivo_2026"
    out["fuente_mapa"] = "universo_2026"
    out["nombre_mapa"] = out["nombre_de_la_unidad_economica"]
    return out


def base_layers(crs: str) -> tuple[gpd.GeoDataFrame | None, gpd.GeoDataFrame | None]:
    localidades = read_layer("localidades") if PATHS["localidades"].exists() else None
    hydro = read_layer("hidrografia") if PATHS["hidrografia"].exists() else None
    if localidades is not None and not localidades.empty:
        localidades = localidades.to_crs(crs)
    if hydro is not None and not hydro.empty:
        hydro = hydro.to_crs(crs)
        hydro = hydro[hydro.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()
    return localidades, hydro


def static_map(gdf: gpd.GeoDataFrame, name: str, title: str) -> None:
    if gdf.empty:
        return
    localidades, hydro = base_layers(gdf.crs)
    fig, ax = plt.subplots(figsize=(10.5, 8), dpi=180)
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#737373", linewidth=0.5)
    if hydro is not None and not hydro.empty:
        minx, miny, maxx, maxy = gdf.total_bounds
        hydro_crop = hydro.cx[minx - 3000 : maxx + 3000, miny - 3000 : maxy + 3000]
        if not hydro_crop.empty:
            hydro_crop.plot(ax=ax, color="#2b8cbe", linewidth=0.5, alpha=0.75)
    for status, group in gdf.groupby("comparacion", dropna=False):
        color = COLORS.get(str(status), "#525252")
        marker = "x" if str(status).startswith("actual_falta") or "falso" in str(status) else "o"
        group.plot(ax=ax, color=color, marker=marker, markersize=42, edgecolor="white", linewidth=0.35, label=str(status))
    minx, miny, maxx, maxy = gdf.total_bounds
    pad_x = max((maxx - minx) * 0.12, 300)
    pad_y = max((maxy - miny) * 0.12, 300)
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
    web["color_value"] = web["comparacion"].astype(str)
    hover_cols = [
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
            "distancia_m_denue2026",
            "id_denue2026_cercano",
            "nombre_denue2026_cercano",
        ]
        if c in web.columns
    ]
    color_discrete_map = {status: COLORS.get(status, "#525252") for status in sorted(web["color_value"].unique())}
    fig = px.scatter_map(
        web,
        lat="lat",
        lon="lon",
        color="color_value",
        color_discrete_map=color_discrete_map,
        hover_name="nombre_mapa" if "nombre_mapa" in web.columns else None,
        hover_data=hover_cols,
        zoom=12,
        height=720,
        title=title,
    )
    fig.update_layout(map_style="open-street-map", margin={"r": 10, "t": 55, "l": 10, "b": 10})
    fig.write_html(MAPS_DIR / f"{name}.html", include_plotlyjs="cdn")


def save_layer(gdf: gpd.GeoDataFrame, name: str, title: str) -> pd.DataFrame:
    if gdf.empty:
        return pd.DataFrame([{"capa": name, "registros": 0, "detalle": "sin registros"}])
    path = LAYERS_DIR / f"{name}.gpkg"
    safe_to_file(gdf, path, layer=name)
    gdf.drop(columns="geometry", errors="ignore").to_csv(TABLES_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    static_map(gdf, name, title)
    interactive_map(gdf, name, title)
    counts = gdf.groupby("comparacion", dropna=False).size().reset_index(name="registros")
    counts.insert(0, "capa", name)
    return counts


def write_index(summaries: pd.DataFrame) -> None:
    summaries.to_csv(TABLES_DIR / "resumen_capas_coincidencias.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Auditoria de coincidencias DENUE 2026",
        "",
        "Estos mapas separan fuentes que no representan el mismo universo: universo prioritario actual, DENUE 2026 completo, Maryhelen MH2, Maryhelen MH y Mayra.",
        "",
        "## Como leerlo",
        "",
        "- `en_ambos`: aparece en el universo prioritario actual y en el universo prioritario recalculado con DENUE 2026.",
        "- `solo_universo_actual`: estaba en tu universo prioritario previo, pero no queda en el universo prioritario 2026.",
        "- `solo_universo_2026`: aparece al aplicar el filtro a DENUE 2026, pero no estaba en el universo final previo.",
        "- `actual_falta_en_*`: registro de tu Santa Ana final que no aparece en esa fuente externa por ID.",
        "- `mayra_revisar_nombre_o_distancia`: Mayra no trae ID/CLEE; se debe revisar por nombre, direccion y punto mas cercano.",
        "- `posible_falso_positivo_2026`: prioridad automatica que debe revisarse antes de usar como textilera.",
        "",
        "## Archivos principales",
        "",
        "- `capas_qgis/*.gpkg`: abrir directamente en QGIS.",
        "- `mapas/*.png`: revision rapida estatica.",
        "- `mapas/*.html`: revision interactiva.",
        "- `tablas/resumen_capas_coincidencias.csv`: conteos por categoria.",
        "",
        "## Conteos",
        "",
    ]
    clean = summaries.astype(str)
    lines.append("| capa | comparacion | registros |")
    lines.append("| --- | --- | --- |")
    for _, row in clean.iterrows():
        lines.append(f"| {row.get('capa', '')} | {row.get('comparacion', '')} | {row.get('registros', '')} |")
    lines.append("")
    lines.append(
        "Nota: esto es un instrumento de limpieza/auditoria. No constituye evidencia de descarga, contaminacion ni incumplimiento."
    )
    (OUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    current = read_layer("current_all")
    current_santa = read_layer("current_santa")
    denue2026 = read_layer("denue2026")
    universe2026 = read_layer("universe2026")
    mh2 = read_layer("maryhelen_mh2")
    mh = read_layer("maryhelen_mh")
    mayra = read_layer("mayra")

    layers: list[tuple[str, str, gpd.GeoDataFrame]] = []
    layers.append(
        (
            "01_universo_actual_vs_universo_2026",
            "Universo prioritario actual vs universo prioritario DENUE 2026",
            current_vs_universe2026(current, universe2026),
        )
    )
    layers.append(
        (
            "02_santa_ana_actual_vs_denue2026_raw",
            "Santa Ana final actual: cobertura por DENUE 2026 crudo",
            current_against_raw_source(
                current_santa,
                denue2026,
                "actual_y_denue2026",
                "actual_falta_en_denue2026",
            ),
        )
    )
    layers.append(
        (
            "03_santa_ana_actual_vs_maryhelen_mh2",
            "Santa Ana final actual: cobertura por Maryhelen MH2",
            current_against_raw_source(
                current_santa,
                mh2,
                "actual_y_maryhelen_mh2",
                "actual_falta_en_maryhelen_mh2",
            ),
        )
    )
    layers.append(
        (
            "04_santa_ana_actual_vs_maryhelen_mh",
            "Santa Ana final actual vs seleccion Maryhelen MH",
            current_vs_maryhelen_mh(current_santa, mh),
        )
    )
    layers.append(
        (
            "05_denue2026_vs_maryhelen_mh2_diferencias",
            "Diferencias de IDs entre DENUE 2026 y Maryhelen MH2",
            denue2026_vs_maryhelen_mh2(denue2026, mh2),
        )
    )
    mayra_points, mayra_lines = mayra_nearest_denue2026(mayra, denue2026)
    layers.append(("06_mayra_vs_denue2026_vecino_cercano", "Mayra vs DENUE 2026: vecino mas cercano", mayra_points))
    layers.append(("07_alertas_falsos_positivos_2026", "Alertas posibles falsos positivos en universo 2026", alerts2026_layer(universe2026)))

    summaries = []
    for name, title, gdf in layers:
        summaries.append(save_layer(gdf, name, title))
    if not mayra_lines.empty:
        safe_to_file(mayra_lines, LAYERS_DIR / "06b_mayra_lineas_a_denue2026_cercano.gpkg", layer="mayra_lineas_denue2026")
        mayra_lines.drop(columns="geometry", errors="ignore").to_csv(
            TABLES_DIR / "06b_mayra_lineas_a_denue2026_cercano.csv",
            index=False,
            encoding="utf-8-sig",
        )

    summary = pd.concat(summaries, ignore_index=True)
    write_index(summary)
    print(f"[atoyac] Mapas de auditoria guardados en {relpath(OUT_DIR)}")


if __name__ == "__main__":
    main()
