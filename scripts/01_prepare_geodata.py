from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import (
    PROCESSED_DIR,
    TABLES_DIR,
    add_source_fields,
    choose_target_crs,
    clean_dataframe_columns,
    drop_empty_geometry,
    ensure_crs_and_project,
    ensure_output_dirs,
    log,
    normalize_text,
    read_csv_robust,
    relpath,
    safe_read_vector,
    safe_to_file,
    shapefiles,
    write_errors,
)


OUTPUTS = {
    "agebs": "agebs.gpkg",
    "manzanas": "manzanas.gpkg",
    "localidades": "localidades.gpkg",
    "vialidades": "vialidades.gpkg",
    "caminos_carreteras": "caminos_carreteras.gpkg",
    "cuencas": "cuencas.gpkg",
    "hidrografia": "hidrografia.gpkg",
    "denue": "denue_raw.gpkg",
}


def classify_layer(path: Path) -> str | None:
    text = normalize_text(relpath(path))
    name = normalize_text(path.stem)
    if "hidrografia_atoyac" in text or "hidrologia_atoyac" in text:
        return "hidrografia"
    if "denue" in name:
        return "denue"
    if "ageb" in name and "arearurales" not in name:
        return "agebs"
    if "arearuralesnoamanzanadas" in name:
        return None
    if "manzana" in name:
        return "manzanas"
    if "localidad" in name:
        return "localidades"
    if "vialidad" in name or "vialidades" in name:
        return "vialidades"
    if "camino" in name or "carretera" in name:
        return "caminos_carreteras"
    if "cuenca" in name or "subcuenca" in name:
        return "cuencas"
    return None


def read_sidecar_csv(path: Path) -> pd.DataFrame | None:
    csv_path = path.with_suffix(".csv")
    if not csv_path.exists():
        return None
    df = read_csv_robust(csv_path)
    df = clean_dataframe_columns(df)
    df = df.loc[:, ~df.columns.str.startswith("unnamed")]
    return df


def enrich_denue_from_csv(gdf: gpd.GeoDataFrame, path: Path) -> gpd.GeoDataFrame:
    attrs = read_sidecar_csv(path)
    if attrs is None or attrs.empty:
        return gdf
    attrs = attrs.reset_index(drop=True)
    gdf = gdf.reset_index(drop=True)
    if len(attrs) == len(gdf):
        keep_geom = gdf[["geometry"]].copy()
        merged = gpd.GeoDataFrame(pd.concat([attrs, keep_geom], axis=1), geometry="geometry", crs=gdf.crs)
        return merged

    id_cols = [c for c in attrs.columns if c in {"id", "id_llave_r"}]
    gdf_id_cols = [c for c in gdf.columns if c in {"id", "id_llave_r"}]
    if id_cols and gdf_id_cols:
        left = gdf[[gdf_id_cols[0], "geometry"]].rename(columns={gdf_id_cols[0]: "_join_id"})
        right = attrs.rename(columns={id_cols[0]: "_join_id"})
        merged = left.merge(right, on="_join_id", how="left").drop(columns=["_join_id"])
        return gpd.GeoDataFrame(merged, geometry="geometry", crs=gdf.crs)
    return gdf


def read_prepare_one(path: Path, layer_type: str, target_crs: str) -> gpd.GeoDataFrame:
    gdf = safe_read_vector(path)
    gdf = clean_dataframe_columns(gdf)
    if layer_type == "denue":
        gdf = enrich_denue_from_csv(gdf, path)
        gdf = clean_dataframe_columns(gdf)
    gdf = ensure_crs_and_project(gdf, target_crs)
    gdf = drop_empty_geometry(gdf)
    return add_source_fields(gdf, path, layer_type)


def combine_layers(paths: list[Path], layer_type: str, target_crs: str, errors: list[dict]) -> gpd.GeoDataFrame:
    frames = []
    for path in paths:
        try:
            log(f"Preparando {layer_type}: {relpath(path)}")
            frames.append(read_prepare_one(path, layer_type, target_crs))
        except Exception as exc:
            errors.append({"script": "01_prepare_geodata", "ruta": relpath(path), "error": f"{type(exc).__name__}: {exc}"})
            log(f"Error en {relpath(path)}: {exc}")
    if not frames:
        return gpd.GeoDataFrame(geometry=[], crs=target_crs)
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry="geometry", crs=target_crs)


def main() -> None:
    ensure_output_dirs()
    target_crs, crs_note = choose_target_crs()
    errors: list[dict] = []
    layer_paths: dict[str, list[Path]] = {key: [] for key in OUTPUTS}
    for path in shapefiles():
        layer_type = classify_layer(path)
        if layer_type:
            layer_paths[layer_type].append(path)

    pd.DataFrame(
        [{"tipo_capa": key, "archivo": value, "capas_detectadas": len(layer_paths[key])} for key, value in OUTPUTS.items()]
    ).to_csv(TABLES_DIR / "resumen_capas_procesadas.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame([{"target_crs": target_crs, "nota": crs_note or "CRS metrico seleccionado correctamente"}]).to_csv(
        TABLES_DIR / "crs_procesamiento.csv", index=False, encoding="utf-8-sig"
    )

    for layer_type, filename in OUTPUTS.items():
        combined = combine_layers(layer_paths[layer_type], layer_type, target_crs, errors)
        if combined.empty:
            log(f"Sin datos para {layer_type}; se omite {filename}")
            continue
        out = PROCESSED_DIR / filename
        safe_to_file(combined, out, layer=layer_type)
        log(f"Guardado {relpath(out)} con {len(combined)} features")

    write_errors(errors, "errores_prepare_geodata.csv")
    log("Preparacion geoespacial terminada")


if __name__ == "__main__":
    main()
