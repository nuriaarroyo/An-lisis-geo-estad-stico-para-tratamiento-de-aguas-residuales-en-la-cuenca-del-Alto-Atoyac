from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio

from common import RAW_DIR, TABLES_DIR, ensure_output_dirs, log, origin_folder, relpath, shapefiles


def bounds_to_json(bounds) -> str:
    if bounds is None:
        return ""
    try:
        if len(bounds) == 4:
            keys = ["minx", "miny", "maxx", "maxy"]
            return json.dumps(dict(zip(keys, [float(x) for x in bounds])), ensure_ascii=False)
    except Exception:
        pass
    return ""


def inspect_with_pyogrio(path: Path) -> dict:
    last_error: Exception | None = None
    info = None
    for kwargs in [{}, {"encoding": "latin1"}, {"encoding": "cp1252"}]:
        try:
            info = pyogrio.read_info(path, **kwargs)
            break
        except Exception as exc:
            last_error = exc
    if info is None:
        raise last_error or RuntimeError("No se pudo leer la capa")
    fields = info.get("fields") or []
    dtypes = info.get("dtypes") or []
    columns = [str(field) for field in fields]
    return {
        "ruta": relpath(path),
        "nombre_archivo": path.name,
        "carpeta_origen": origin_folder(path),
        "numero_features": info.get("features"),
        "geometria": info.get("geometry_type") or "",
        "crs": str(info.get("crs") or ""),
        "columnas_disponibles": "; ".join(columns),
        "tipos_columnas": "; ".join([f"{c}:{t}" for c, t in zip(columns, dtypes)]),
        "bounds_extension_espacial": bounds_to_json(info.get("total_bounds")),
        "estado": "ok",
        "error": "",
    }


def inspect_with_geopandas(path: Path, previous_error: Exception) -> dict:
    gdf = gpd.read_file(path)
    bounds = gdf.total_bounds.tolist() if not gdf.empty else None
    geom_types = sorted(gdf.geometry.geom_type.dropna().unique().tolist()) if "geometry" in gdf else []
    return {
        "ruta": relpath(path),
        "nombre_archivo": path.name,
        "carpeta_origen": origin_folder(path),
        "numero_features": len(gdf),
        "geometria": "; ".join(geom_types),
        "crs": str(gdf.crs or ""),
        "columnas_disponibles": "; ".join([str(c) for c in gdf.columns if c != "geometry"]),
        "tipos_columnas": "; ".join([f"{c}:{gdf[c].dtype}" for c in gdf.columns if c != "geometry"]),
        "bounds_extension_espacial": bounds_to_json(bounds),
        "estado": "ok_geopandas_fallback",
        "error": f"pyogrio_read_info fallo: {previous_error}",
    }


def inspect_layer(path: Path) -> dict:
    try:
        return inspect_with_pyogrio(path)
    except Exception as exc:
        try:
            return inspect_with_geopandas(path, exc)
        except Exception as second_exc:
            return {
                "ruta": relpath(path),
                "nombre_archivo": path.name,
                "carpeta_origen": origin_folder(path),
                "numero_features": "",
                "geometria": "",
                "crs": "",
                "columnas_disponibles": "",
                "tipos_columnas": "",
                "bounds_extension_espacial": "",
                "estado": "error",
                "error": f"{type(second_exc).__name__}: {second_exc}",
            }


def main() -> None:
    ensure_output_dirs()
    layers = shapefiles()
    log(f"Shapefiles detectados: {len(layers)}")
    if not RAW_DIR.exists():
        log("No existe data/raw. Se crea inventario vacio.")
    rows = []
    for i, path in enumerate(layers, start=1):
        log(f"Inventariando {i}/{len(layers)}: {relpath(path)}")
        rows.append(inspect_layer(path))

    out = TABLES_DIR / "inventario_capas.csv"
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False, encoding="utf-8-sig")

    errors = df[df.get("estado", "") == "error"]
    errors.to_csv(TABLES_DIR / "errores_inventario_capas.csv", index=False, encoding="utf-8-sig")
    log(f"Inventario guardado en {relpath(out)}")
    log(f"Capas con error: {len(errors)}")


if __name__ == "__main__":
    main()
