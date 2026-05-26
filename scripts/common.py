from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from shapely.validation import make_valid


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
MAPS_DIR = OUTPUTS_DIR / "maps"
FIGURES_DIR = OUTPUTS_DIR / "figures"
QGIS_DIR = PROJECT_ROOT / "qgis_scripts"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

OUTPUT_DIRS = [
    PROCESSED_DIR,
    MAPS_DIR,
    TABLES_DIR,
    FIGURES_DIR,
    SCRIPTS_DIR,
    QGIS_DIR,
]

TARGET_CRS_CANDIDATES = ["EPSG:6372", "EPSG:32614"]


def ensure_output_dirs() -> None:
    for directory in OUTPUT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    print(f"[atoyac] {message}", flush=True)


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except Exception:
        return str(path)


def strip_accents(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = strip_accents(str(value)).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_column_name(name: object) -> str:
    text = normalize_text(name)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "columna"


def make_unique_columns(columns: Iterable[object]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for column in columns:
        base = clean_column_name(column)
        count = seen.get(base, 0)
        out.append(base if count == 0 else f"{base}_{count + 1}")
        seen[base] = count + 1
    return out


def clean_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = make_unique_columns(df.columns)
    return df


def shapefiles() -> list[Path]:
    if not RAW_DIR.exists():
        return []
    return sorted(RAW_DIR.rglob("*.shp"))


def origin_folder(path: Path) -> str:
    try:
        return str(path.parent.relative_to(RAW_DIR))
    except Exception:
        return path.parent.name


def safe_read_vector(path: Path) -> gpd.GeoDataFrame:
    attempts = [
        {"engine": "pyogrio"},
        {"engine": "pyogrio", "encoding": "latin1"},
        {"engine": "pyogrio", "encoding": "cp1252"},
        {"encoding": "latin1"},
        {"encoding": "cp1252"},
    ]
    last_error: Exception | None = None
    for kwargs in attempts:
        try:
            return gpd.read_file(path, **kwargs)
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error
    return gpd.read_file(path)


def repair_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty or "geometry" not in gdf:
        return gdf
    gdf = gdf[gdf.geometry.notna()].copy()
    if gdf.empty:
        return gdf
    invalid = ~gdf.geometry.is_valid
    if invalid.any():
        gdf.loc[invalid, "geometry"] = gdf.loc[invalid, "geometry"].apply(make_valid)
    return gdf


def choose_target_crs() -> tuple[str, str]:
    test = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy([-98.2], [19.1]),
        crs="EPSG:4326",
    )
    errors: list[str] = []
    for crs in TARGET_CRS_CANDIDATES:
        try:
            projected = test.to_crs(crs)
            if np.isfinite(projected.geometry.x.iloc[0]):
                return crs, ""
        except Exception as exc:
            errors.append(f"{crs}: {exc}")
    raise RuntimeError("No se pudo seleccionar CRS metrico. " + " | ".join(errors))


def ensure_crs_and_project(
    gdf: gpd.GeoDataFrame,
    target_crs: str,
    assumed_crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    gdf = repair_geometries(gdf)
    if gdf.empty:
        gdf = gdf.set_crs(target_crs, allow_override=True) if gdf.crs is None else gdf
        return gdf
    if gdf.crs is None:
        gdf = gdf.set_crs(assumed_crs, allow_override=True)
    return gdf.to_crs(target_crs)


def add_source_fields(gdf: gpd.GeoDataFrame, path: Path, layer_type: str) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["source_path"] = relpath(path)
    gdf["source_file"] = path.name
    gdf["source_folder"] = origin_folder(path)
    gdf["layer_type"] = layer_type
    return gdf


def drop_empty_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty or "geometry" not in gdf:
        return gdf
    return gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()


def safe_to_file(gdf: gpd.GeoDataFrame, path: Path, layer: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    clean = gdf.copy()
    for column in clean.columns:
        if column == clean.geometry.name:
            continue
        if pd.api.types.is_object_dtype(clean[column]):
            clean[column] = clean[column].map(lambda x: "" if pd.isna(x) else str(x))
    pyogrio.write_dataframe(
        clean,
        path,
        layer=layer,
        driver="GPKG",
        encoding="utf-8",
        geometry_type="Unknown",
    )


def write_errors(errors: list[dict], filename: str) -> None:
    if errors:
        pd.DataFrame(errors).to_csv(TABLES_DIR / filename, index=False, encoding="utf-8-sig")


def read_gpkg(path: Path, layer: str | None = None) -> gpd.GeoDataFrame:
    return gpd.read_file(path, layer=layer, engine="pyogrio")


def read_csv_robust(path: Path, **kwargs) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding, **kwargs)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return pd.read_csv(path, **kwargs)
