from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import PROJECT_ROOT, safe_to_file


CONFIG_PATH = (
    PROJECT_ROOT / "config" / "filtros_textiles_santa_ana" / "versiones" / "v1"
    / "auditoria_6_especiales.csv"
)
INPUT_PATH = (
    PROJECT_ROOT / "outputs" / "universo_refinado_santa_ana" / "capas_qgis"
    / "universo_productivo_refinado.gpkg"
)
REFINEMENT_MANIFEST = (
    PROJECT_ROOT / "outputs" / "universo_refinado_santa_ana" / "manifest_refinamiento.json"
)
OUT_DIR = PROJECT_ROOT / "outputs" / "auditoria_6_especiales"


def normalize_id(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.upper()


def export(frame: gpd.GeoDataFrame, name: str) -> None:
    OUT_DIR.joinpath("capas_qgis").mkdir(parents=True, exist_ok=True)
    OUT_DIR.joinpath("tablas").mkdir(parents=True, exist_ok=True)
    safe_to_file(frame, OUT_DIR / "capas_qgis" / f"{name}.gpkg", layer=name)
    pd.DataFrame(frame.drop(columns="geometry")).to_csv(
        OUT_DIR / "tablas" / f"{name}.csv", index=False, encoding="utf-8-sig"
    )


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Primero ejecute 03_refine_and_prioritize.py")
    universe = gpd.read_file(INPUT_PATH, engine="pyogrio")
    audit = pd.read_csv(CONFIG_PATH, dtype=str).fillna("")
    universe["_id_key"] = normalize_id(universe["id"])
    audit["_id_key"] = normalize_id(audit["id_denue"])
    missing = set(audit["_id_key"]) - set(universe["_id_key"])
    if missing:
        raise ValueError(f"Los IDs auditados no están en el universo de entrada: {sorted(missing)}")

    audit_fields = audit[[
        "_id_key", "decision_auditoria", "prioridad_auditoria", "causa", "fuentes", "nota"
    ]].rename(columns={
        "causa": "causa_auditoria_especial",
        "fuentes": "fuentes_auditoria_especial",
        "nota": "nota_auditoria_especial",
    })
    result = universe.merge(audit_fields, on="_id_key", how="left")
    result["decision_auditoria"] = result["decision_auditoria"].fillna("NO_APLICA")
    result["prioridad_auditoria"] = result["prioridad_auditoria"].fillna(result["prioridad_refinada"])
    for column in ["causa_auditoria_especial", "fuentes_auditoria_especial", "nota_auditoria_especial"]:
        result[column] = result[column].fillna("")
    result = gpd.GeoDataFrame(result, geometry="geometry", crs=universe.crs)

    review_mask = result["decision_auditoria"].isin(["REVISAR_NO_TEXTIL", "REVISAR_DUPLICADO"])
    final_universe = result.loc[~review_mask].copy()
    special_review = result.loc[review_mask].copy()
    confirmed = result.loc[result["decision_auditoria"].eq("CONFIRMAR")].copy()
    export(result, "auditoria_6_completa")
    export(final_universe, "universo_productivo_auditado")
    export(special_review, "revision_6_especiales")
    export(confirmed, "prioridad_alta_confirmada")

    summary = pd.DataFrame([
        {"conjunto": "entrada_refinada", "registros": len(universe)},
        {"conjunto": "alta_confirmada", "registros": len(confirmed)},
        {"conjunto": "revision_especial", "registros": len(special_review)},
        {"conjunto": "universo_productivo_auditado", "registros": len(final_universe)},
    ])
    summary.to_csv(OUT_DIR / "tablas" / "resumen_auditoria_6.csv", index=False, encoding="utf-8-sig")
    validation = pd.DataFrame([
        {"validacion": "seis_ids_auditados", "resultado": "OK" if len(audit) == 6 else "ERROR"},
        {"validacion": "cuatro_altas_confirmadas", "resultado": "OK" if len(confirmed) == 4 else "ERROR"},
        {"validacion": "dos_en_revision_especial", "resultado": "OK" if len(special_review) == 2 else "ERROR"},
        {
            "validacion": "particion_conserva_entrada",
            "resultado": "OK" if len(final_universe) + len(special_review) == len(universe) else "ERROR",
        },
    ])
    validation.to_csv(OUT_DIR / "tablas" / "validacion_auditoria_6.csv", index=False, encoding="utf-8-sig")
    if validation["resultado"].eq("ERROR").any():
        raise RuntimeError("Falló la validación de la auditoría de seis casos")
    manifest = {
        "pipeline": "auditoria_seis_casos_especiales",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "refinement_manifest_sha256": hashlib.sha256(REFINEMENT_MANIFEST.read_bytes()).hexdigest(),
        "audit_policy_sha256": hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(),
        "input": len(universe),
        "confirmed_high": len(confirmed),
        "special_review": len(special_review),
        "final_universe": len(final_universe),
    }
    (OUT_DIR / "manifest_auditoria_6.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
