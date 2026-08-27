from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import PROCESSED_DIR, PROJECT_ROOT, safe_to_file
from filter_engine import classify, load_catalogs


CONFIG_DIR = PROJECT_ROOT / "config" / "filtros_textiles_santa_ana" / "versiones" / "v1"
SOURCE_DENUE = PROJECT_ROOT / "data" / "raw" / "denue2026" / "Denue26 area estudio.shp"
LOCALITIES = PROCESSED_DIR / "localidades.gpkg"
OUT_DIR = PROJECT_ROOT / "outputs" / "universo_independiente_3_localidades"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(gdf: gpd.GeoDataFrame, name: str) -> None:
    safe_to_file(gdf, OUT_DIR / "capas_qgis" / f"{name}.gpkg", layer=name)
    pd.DataFrame(gdf.drop(columns="geometry")).to_csv(
        OUT_DIR / "tablas" / f"{name}.csv", index=False, encoding="utf-8-sig"
    )


def main() -> None:
    version_info = json.loads((CONFIG_DIR / "version.json").read_text(encoding="utf-8"))
    version = str(version_info["version"])
    locations_cfg = pd.read_csv(CONFIG_DIR / "localidades.csv", dtype=str)
    locations_cfg = locations_cfg[locations_cfg["activa"].str.lower().eq("true")]
    denue = gpd.read_file(SOURCE_DENUE, engine="pyogrio")
    denue = denue.rename(columns={
        "nom_estab": "nombre_de_la_unidad_economica",
        "codigo_act": "codigo_de_la_clase_actividad_scian",
        "nombre_act": "nombre_clase_actividad_scian",
    })
    polygons = gpd.read_file(LOCALITIES, engine="pyogrio").to_crs(denue.crs)
    catalogs = load_catalogs(CONFIG_DIR)
    OUT_DIR.joinpath("capas_qgis").mkdir(parents=True, exist_ok=True)
    OUT_DIR.joinpath("tablas").mkdir(parents=True, exist_ok=True)

    territorial_parts = []
    territorial_counts = []
    for _, cfg in locations_cfg.iterrows():
        if cfg["metodo_seleccion"] == "atributo":
            field = cfg["campo_seleccion"]
            selected = denue.loc[
                denue[field].fillna("").astype(str).str.zfill(len(cfg["valor_seleccion"]))
                .eq(cfg["valor_seleccion"])
            ].copy()
        else:
            polygon = polygons.loc[polygons["id"].astype(str).eq(cfg["poligono_id"])]
            if polygon.empty:
                raise ValueError(f"No existe polígono {cfg['poligono_id']} para {cfg['localidad_id']}")
            polygon = polygon.dissolve()
            selected = gpd.sjoin(
                denue, polygon[["geometry"]], how="inner", predicate=cfg["metodo_seleccion"]
            ).drop(columns=["index_right"], errors="ignore")
        selected["localidad_id_analisis"] = cfg["localidad_id"]
        selected["localidad_analisis"] = cfg["nombre_salida"]
        selected["poligono_id_analisis"] = cfg["poligono_id"]
        selected["metodo_recorte"] = cfg["metodo_seleccion"]
        selected["criterio_recorte"] = (
            f"{cfg['campo_seleccion']}={cfg['valor_seleccion']}"
            if cfg["metodo_seleccion"] == "atributo" else cfg["poligono_id"]
        )
        territorial_parts.append(selected)
        territorial_counts.append({
            "etapa": "base_territorial",
            "localidad_id": cfg["localidad_id"],
            "registros": len(selected),
        })

    territorial = gpd.GeoDataFrame(
        pd.concat(territorial_parts, ignore_index=True), geometry="geometry", crs=denue.crs
    ).drop_duplicates(["id", "localidad_id_analisis"])
    classified = classify(territorial, catalogs, version)
    export(territorial, "denue_base_territorial")
    export(classified, "clasificacion_completa")
    decisions = {
        "universo_independiente_incluido": classified["decision_clasificacion"].isin(
            ["INCLUIR_ALTA", "INCLUIR_MEDIA"]
        ),
        "universo_independiente_revision": classified["decision_clasificacion"].eq("REVISAR"),
        "universo_independiente_excluido": classified["decision_clasificacion"].eq("EXCLUIR"),
    }
    for name, mask in decisions.items():
        export(classified.loc[mask].copy(), name)

    summary = (
        classified.groupby(
            ["localidad_id_analisis", "decision_clasificacion", "categoria_clasificacion"],
            dropna=False,
        ).size().reset_index(name="registros")
    )
    summary.to_csv(OUT_DIR / "tablas" / "resumen_clasificacion.csv", index=False, encoding="utf-8-sig")
    locality_audit = (
        denue.groupby(["cve_loc", "localidad"], dropna=False).size().reset_index(name="registros")
        if {"cve_loc", "localidad"}.issubset(denue.columns) else pd.DataFrame()
    )
    locality_audit.to_csv(OUT_DIR / "tablas" / "auditoria_localidades_fuente.csv", index=False, encoding="utf-8-sig")
    validation = pd.DataFrame([
        {"validacion": "ids_unicos_por_localidad", "resultado": "OK" if not classified.duplicated(["id", "localidad_id_analisis"]).any() else "ERROR"},
        {"validacion": "todas_decisiones_asignadas", "resultado": "OK" if classified["decision_clasificacion"].notna().all() else "ERROR"},
        {"validacion": "incluidos_sin_exclusion_fuerte", "resultado": "OK" if classified.loc[classified["decision_clasificacion"].str.startswith("INCLUIR"), "exclusion_fuerte"].eq(False).all() else "ERROR"},
        {
            "validacion": "localidades_activas_presentes",
            "resultado": "OK"
            if set(classified["localidad_id_analisis"]) == set(locations_cfg["localidad_id"])
            else "ERROR",
        },
    ])
    validation.to_csv(OUT_DIR / "tablas" / "validacion_clasificacion.csv", index=False, encoding="utf-8-sig")
    if validation["resultado"].eq("ERROR").any():
        raise RuntimeError("Falló la validación de la clasificación")

    input_files = [SOURCE_DENUE, LOCALITIES] + [
        CONFIG_DIR / name for name in
        ["version.json", "localidades.csv", "palabras_clave.csv", "codigos_scian.csv",
         "reglas_clasificacion.csv", "politica_categorias.csv", "matriz_decision.csv"]
    ]
    manifest = {
        "pipeline": "clasificacion_independiente_3_localidades",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "filter_version": version,
        "independence_statement": "No se leyó ninguna capa MH ni canónica durante la clasificación.",
        "inputs": [{"path": str(p.relative_to(PROJECT_ROOT)), "sha256": sha256(p)} for p in input_files],
        "counts": territorial_counts,
        "total_classified": len(classified),
    }
    (OUT_DIR / "manifest_clasificacion.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
