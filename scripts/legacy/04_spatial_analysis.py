from __future__ import annotations

import geopandas as gpd
import pandas as pd

from common import PROCESSED_DIR, TABLES_DIR, ensure_output_dirs, log, read_gpkg, relpath, safe_to_file


BUFFER_DISTANCES = [100, 250, 500, 1000]
DISTANCE_BINS = [-0.001, 100, 250, 500, 1000, float("inf")]
DISTANCE_LABELS = ["0-100 m", "100-250 m", "250-500 m", "500-1000 m", ">1000 m"]


def existing_gpkg(name: str):
    path = PROCESSED_DIR / name
    return path if path.exists() else None


def geom_class(gdf: gpd.GeoDataFrame, family: str) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    geom_types = gdf.geometry.geom_type.fillna("")
    if family == "line":
        return gdf[geom_types.str.contains("Line", case=False, na=False)].copy()
    if family == "polygon":
        return gdf[geom_types.str.contains("Polygon", case=False, na=False)].copy()
    return gdf


def nearest_distance_to_hydro(points: gpd.GeoDataFrame, hydro: gpd.GeoDataFrame) -> pd.Series:
    if points.empty or hydro.empty:
        return pd.Series(pd.NA, index=points.index, dtype="Float64")
    lines = geom_class(hydro, "line")
    source = lines if not lines.empty else hydro.copy()
    if lines.empty:
        polygons = geom_class(source, "polygon")
        if not polygons.empty:
            source = polygons.copy()
            source["geometry"] = source.boundary
    minx, miny, maxx, maxy = points.total_bounds
    source = source.cx[minx - 5000 : maxx + 5000, miny - 5000 : maxy + 5000].copy()
    if source.empty:
        source = lines if not lines.empty else hydro
    nearest = gpd.sjoin_nearest(
        points.reset_index(names="_point_id"),
        source[["geometry"]].reset_index(drop=True),
        how="left",
        distance_col="distancia_hidrografia_m",
    )
    distances = nearest.groupby("_point_id")["distancia_hidrografia_m"].min()
    return distances.reindex(points.index)


def add_buffer_membership(points: gpd.GeoDataFrame, hydro: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    out = points.copy()
    rows = []
    for distance in BUFFER_DISTANCES:
        col = f"en_buffer_{distance}m"
        if "distancia_hidrografia_m" not in out.columns:
            out[col] = False
        else:
            out[col] = pd.to_numeric(out["distancia_hidrografia_m"], errors="coerce") <= distance
        counts = (
            out[out[col]]
            .groupby("categoria_relevancia_ambiental", dropna=False)
            .size()
            .reset_index(name="establecimientos")
        )
        counts["buffer_m"] = distance
        rows.append(counts)
    if rows:
        count_table = pd.concat(rows, ignore_index=True)
    else:
        count_table = pd.DataFrame(columns=["categoria_relevancia_ambiental", "establecimientos", "buffer_m"])
    return out, count_table[["buffer_m", "categoria_relevancia_ambiental", "establecimientos"]]


def add_distance_ranges(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = points.copy()
    distances = pd.to_numeric(out.get("distancia_hidrografia_m"), errors="coerce")
    out["rango_distancia_hidrografia"] = pd.cut(
        distances,
        bins=DISTANCE_BINS,
        labels=DISTANCE_LABELS,
        include_lowest=True,
    ).astype("string")
    out["rango_distancia_hidrografia"] = out["rango_distancia_hidrografia"].fillna("sin distancia")
    return out


def id_column(gdf: gpd.GeoDataFrame, preferred: list[str], fallback: str) -> str:
    for col in preferred:
        if col in gdf.columns:
            return col
    gdf[fallback] = range(1, len(gdf) + 1)
    return fallback


def spatial_count(points: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame, polygon_kind: str) -> pd.DataFrame:
    if points.empty or polygons.empty:
        return pd.DataFrame()
    polys = polygons.copy()
    if polygon_kind == "ageb":
        key = id_column(polys, ["cvegeo", "cve_ageb", "ageb", "id"], "ageb_id")
    else:
        key = id_column(polys, ["nom_loc", "nombre", "localidad", "loc", "id"], "localidad_id")
    joined = gpd.sjoin(points, polys[[key, "geometry"]], how="left", predicate="within")
    count = (
        joined.groupby([key, "categoria_relevancia_ambiental"], dropna=False)
        .size()
        .reset_index(name="establecimientos")
    )
    return count.rename(columns={key: f"{polygon_kind}_id"})


def main() -> None:
    ensure_output_dirs()
    denue_path = existing_gpkg("denue_textil.gpkg")
    hydro_path = existing_gpkg("hidrografia.gpkg")
    if denue_path is None:
        log("No existe denue_textil.gpkg; ejecuta 02_filter_denue_textil.py primero.")
        return
    denue = read_gpkg(denue_path)
    hydro = read_gpkg(hydro_path) if hydro_path else gpd.GeoDataFrame(geometry=[], crs=denue.crs)
    if not hydro.empty and hydro.crs != denue.crs:
        hydro = hydro.to_crs(denue.crs)

    denue["distancia_hidrografia_m"] = nearest_distance_to_hydro(denue, hydro)
    denue, buffer_counts = add_buffer_membership(denue, hydro)
    denue = add_distance_ranges(denue)

    out = PROCESSED_DIR / "denue_textil_con_distancia.gpkg"
    safe_to_file(denue, out, layer="denue_textil_con_distancia")
    denue.drop(columns="geometry").to_csv(TABLES_DIR / "denue_textil_distancias.csv", index=False, encoding="utf-8-sig")

    identification_cols = [
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "source_folder",
        "categoria_relevancia_ambiental",
        "palabras_clave_detectadas",
        "distancia_hidrografia_m",
        "rango_distancia_hidrografia",
        "latitud",
        "longitud",
        "nota_metodologica",
    ]
    denue[[c for c in identification_cols if c in denue.columns]].to_csv(
        TABLES_DIR / "denue_textil_identificacion.csv",
        index=False,
        encoding="utf-8-sig",
    )
    revisar = denue[denue.get("categoria_relevancia_ambiental", "").astype(str).eq("revisar")].copy()
    revisar[[c for c in identification_cols if c in revisar.columns]].to_csv(
        TABLES_DIR / "denue_revisar_para_auditoria.csv",
        index=False,
        encoding="utf-8-sig",
    )
    buffer_counts.to_csv(TABLES_DIR / "conteo_negocios_por_buffer.csv", index=False, encoding="utf-8-sig")

    distance_counts = (
        denue.groupby(["source_folder", "rango_distancia_hidrografia", "categoria_relevancia_ambiental"], dropna=False)
        .size()
        .reset_index(name="establecimientos")
    )
    distance_counts.to_csv(TABLES_DIR / "conteo_negocios_por_rango_distancia.csv", index=False, encoding="utf-8-sig")

    if (PROCESSED_DIR / "agebs.gpkg").exists():
        agebs = read_gpkg(PROCESSED_DIR / "agebs.gpkg").to_crs(denue.crs)
        count_ageb = spatial_count(denue, agebs, "ageb")
        count_ageb.to_csv(TABLES_DIR / "conteo_negocios_por_ageb.csv", index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame().to_csv(TABLES_DIR / "conteo_negocios_por_ageb.csv", index=False, encoding="utf-8-sig")

    if (PROCESSED_DIR / "localidades.gpkg").exists():
        localidades = read_gpkg(PROCESSED_DIR / "localidades.gpkg").to_crs(denue.crs)
        count_loc = spatial_count(denue, localidades, "localidad")
        count_loc.to_csv(TABLES_DIR / "conteo_negocios_por_localidad.csv", index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame().to_csv(TABLES_DIR / "conteo_negocios_por_localidad.csv", index=False, encoding="utf-8-sig")

    hydro_types = hydro.geometry.geom_type.value_counts(dropna=False).reset_index()
    hydro_types.columns = ["geometria", "features"]
    hydro_types.to_csv(TABLES_DIR / "hidrografia_tipos_geometria.csv", index=False, encoding="utf-8-sig")
    log(f"Cruces espaciales guardados en {relpath(out)}")


if __name__ == "__main__":
    main()
