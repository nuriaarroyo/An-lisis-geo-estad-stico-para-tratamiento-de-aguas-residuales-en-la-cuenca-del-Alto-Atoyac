from __future__ import annotations

import re

import geopandas as gpd
import pandas as pd

from common import (
    PROCESSED_DIR,
    TABLES_DIR,
    ensure_output_dirs,
    log,
    normalize_text,
    read_gpkg,
    safe_to_file,
)


AUDIT_FILES = {
    "huejotzingo": TABLES_DIR / "auditoria_revisar_huejotzingo.csv",
    "xalmimilulco": TABLES_DIR / "auditoria_revisar_xalmimilulco.csv",
    "san_martin": TABLES_DIR / "auditoria_revisar_san_martin.csv",
}

PRODUCTIVE_AUDIT_EXCEL = TABLES_DIR / "auditoria_enriquecida" / "auditoria_denue_textil_priorizada.xlsx"
PRODUCTIVE_CLASSIFIED_GPKG = PROCESSED_DIR / "denue_universo_textil_clasificado.gpkg"
PRODUCTIVE_TABLE_DIR = TABLES_DIR / "denue_clasificacion_productiva"

VALID_FINAL_CATEGORIES = {
    "alta_relevancia_ambiental",
    "media_relevancia_ambiental",
}


def canonical_category(value: object) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if text in {"alta", "alto", "alta_relevancia", "alta_relevancia_ambiental"}:
        return "alta_relevancia_ambiental"
    if text in {"media", "medio", "mediana", "media_relevancia", "media_relevancia_ambiental"}:
        return "media_relevancia_ambiental"
    if text in {"excluir", "no", "no_pertinente", "descartar", "fuera"}:
        return "excluir"
    if text in {"revisar", "mantener_revisar", "duda", "pendiente"}:
        return "mantener_revisar"
    return ""


def read_audit_tables() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for region, path in AUDIT_FILES.items():
        if not path.exists():
            log(f"No existe plantilla de auditoria para {region}: {path.name}")
            continue
        df = pd.read_csv(path, encoding="utf-8-sig")
        if df.empty:
            continue
        df["region_auditoria"] = region
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    audit = pd.concat(frames, ignore_index=True)
    if "categoria_auditada" not in audit.columns:
        audit["categoria_auditada"] = ""
    if "notas_auditoria" not in audit.columns:
        audit["notas_auditoria"] = ""
    audit["categoria_auditada_normalizada"] = audit["categoria_auditada"].map(canonical_category)
    return audit


def read_productive_audit_table() -> pd.DataFrame:
    if not PRODUCTIVE_AUDIT_EXCEL.exists():
        return pd.DataFrame()
    try:
        audit = pd.read_excel(PRODUCTIVE_AUDIT_EXCEL, sheet_name="todos_clasificados", engine="openpyxl")
    except ValueError:
        audit = pd.read_excel(PRODUCTIVE_AUDIT_EXCEL, sheet_name=0, engine="openpyxl")
    if audit.empty:
        return audit
    for column in [
        "categoria_auditada",
        "etapa_productiva_auditada",
        "notas_auditoria",
        "fuente_auditoria",
        "decision_estudio",
        "fecha_auditoria",
        "auditor_responsable",
    ]:
        if column not in audit.columns:
            audit[column] = ""
    audit["categoria_auditada_normalizada"] = audit["categoria_auditada"].map(canonical_category)
    return audit


def key_columns(df: pd.DataFrame) -> list[str]:
    if {"id", "clee"}.issubset(df.columns):
        return ["id", "clee"]
    if "id" in df.columns:
        return ["id"]
    if "clee" in df.columns:
        return ["clee"]
    raise ValueError("No se encontro columna id o clee para unir auditoria DENUE.")


def apply_audit() -> None:
    ensure_output_dirs()
    source = PROCESSED_DIR / "denue_textil_con_distancia.gpkg"
    if not source.exists():
        source = PROCESSED_DIR / "denue_textil.gpkg"
    denue = read_gpkg(source).copy()
    audit = read_audit_tables()

    denue["categoria_final"] = denue["categoria_relevancia_ambiental"].astype(str)
    denue["estado_auditoria"] = "clasificacion_automatica"
    denue["notas_auditoria"] = ""

    if not audit.empty:
        keys = key_columns(denue)
        keep = keys + ["categoria_auditada", "categoria_auditada_normalizada", "notas_auditoria", "region_auditoria"]
        audit = audit[[c for c in keep if c in audit.columns]].copy()
        for key in keys:
            audit[key] = audit[key].astype(str)
            denue[key] = denue[key].astype(str)
        audit = audit.drop_duplicates(subset=keys, keep="last")
        denue = denue.merge(audit, on=keys, how="left", suffixes=("", "_audit"))

        reviewed = denue["categoria_relevancia_ambiental"].astype(str).eq("revisar")
        has_manual = denue["categoria_auditada_normalizada"].fillna("").ne("")
        denue.loc[reviewed & has_manual, "categoria_final"] = denue.loc[reviewed & has_manual, "categoria_auditada_normalizada"]
        denue.loc[reviewed & has_manual, "estado_auditoria"] = "auditado_manual"
        denue.loc[reviewed & ~has_manual, "categoria_final"] = "pendiente_auditoria"
        denue.loc[reviewed & ~has_manual, "estado_auditoria"] = "pendiente_auditoria"
        if "notas_auditoria_audit" in denue.columns:
            denue["notas_auditoria"] = denue["notas_auditoria_audit"].fillna(denue["notas_auditoria"])
    else:
        denue.loc[denue["categoria_relevancia_ambiental"].astype(str).eq("revisar"), "categoria_final"] = "pendiente_auditoria"
        denue.loc[denue["categoria_relevancia_ambiental"].astype(str).eq("revisar"), "estado_auditoria"] = "pendiente_auditoria"

    final = denue[denue["categoria_final"].isin(VALID_FINAL_CATEGORIES)].copy()
    final["categoria_relevancia_ambiental"] = final["categoria_final"]

    out_gpkg = PROCESSED_DIR / "denue_textil_auditado.gpkg"
    safe_to_file(final, out_gpkg, layer="denue_textil_auditado")

    csv = final.drop(columns="geometry")
    csv.to_csv(TABLES_DIR / "denue_categorias_auditadas.csv", index=False, encoding="utf-8-sig")

    resumen = (
        csv.groupby(["source_folder", "categoria_final"], dropna=False)
        .size()
        .reset_index(name="establecimientos")
        .sort_values(["source_folder", "categoria_final"])
    )
    resumen.to_csv(TABLES_DIR / "resumen_denue_categorias_auditadas_por_localidad.csv", index=False, encoding="utf-8-sig")

    pendiente = denue[denue["categoria_final"].eq("pendiente_auditoria")].drop(columns="geometry")
    pendiente.to_csv(TABLES_DIR / "denue_pendiente_auditoria.csv", index=False, encoding="utf-8-sig")

    log(f"Categorias auditadas guardadas: outputs/tables/denue_categorias_auditadas.csv ({len(final)} registros)")
    log(f"GeoPackage auditado guardado: data/processed/denue_textil_auditado.gpkg")
    if len(pendiente):
        log(f"Pendientes de auditoria: {len(pendiente)} registros")

    apply_productive_audit()


def normalize_productive_decision(value: object) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    allowed = {
        "incluir_prioritario",
        "incluir_contexto_productivo",
        "excluir_del_universo_prioritario",
        "excluir_por_comercio",
        "excluir_por_renta",
        "mantener_pendiente",
        "validar_documentalmente",
        "validar_en_campo",
    }
    return text if text in allowed else ""


def apply_productive_audit() -> None:
    if not PRODUCTIVE_CLASSIFIED_GPKG.exists():
        return
    PRODUCTIVE_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    classified = read_gpkg(PRODUCTIVE_CLASSIFIED_GPKG).copy()
    audit = read_productive_audit_table()
    classified["estado_auditoria_productiva"] = "sin_decision_manual"
    classified["decision_estudio_final"] = classified.get("decision_estudio_sugerida", "").astype(str)
    classified["etapa_productiva_final"] = classified.get("etapa_productiva_sugerida", "").astype(str)
    classified["categoria_ambiental_final"] = classified.get("presion_ambiental_potencial", "").astype(str)

    if not audit.empty:
        keys = key_columns(classified)
        keep = keys + [
            "categoria_auditada",
            "categoria_auditada_normalizada",
            "etapa_productiva_auditada",
            "notas_auditoria",
            "fuente_auditoria",
            "decision_estudio",
            "fecha_auditoria",
            "auditor_responsable",
        ]
        audit = audit[[c for c in keep if c in audit.columns]].copy()
        for key in keys:
            audit[key] = audit[key].astype(str)
            classified[key] = classified[key].astype(str)
        audit = audit.drop_duplicates(subset=keys, keep="last")
        manual_cols = [
            "categoria_auditada",
            "categoria_auditada_normalizada",
            "etapa_productiva_auditada",
            "notas_auditoria",
            "fuente_auditoria",
            "decision_estudio",
            "fecha_auditoria",
            "auditor_responsable",
        ]
        classified = classified.drop(columns=[c for c in manual_cols if c in classified.columns], errors="ignore")
        classified = classified.merge(audit, on=keys, how="left", suffixes=("", "_audit"))

        has_decision = classified.get("decision_estudio", pd.Series("", index=classified.index)).fillna("").astype(str).str.strip().ne("")
        normalized_decision = classified.get("decision_estudio", pd.Series("", index=classified.index)).map(normalize_productive_decision)
        has_stage = classified.get("etapa_productiva_auditada", pd.Series("", index=classified.index)).fillna("").astype(str).str.strip().ne("")
        has_category = classified.get("categoria_auditada_normalizada", pd.Series("", index=classified.index)).fillna("").astype(str).str.strip().ne("")
        classified.loc[has_decision & normalized_decision.ne(""), "decision_estudio_final"] = normalized_decision[has_decision & normalized_decision.ne("")]
        classified.loc[has_stage, "etapa_productiva_final"] = classified.loc[has_stage, "etapa_productiva_auditada"]
        classified.loc[has_category, "categoria_ambiental_final"] = classified.loc[has_category, "categoria_auditada_normalizada"]
        classified.loc[has_decision | has_stage | has_category, "estado_auditoria_productiva"] = "auditado_manual"

    pending = classified[classified["estado_auditoria_productiva"].eq("sin_decision_manual")].copy()
    audited = classified[classified["estado_auditoria_productiva"].eq("auditado_manual")].copy()
    out_gpkg = PROCESSED_DIR / "denue_clasificacion_productiva_auditada.gpkg"
    safe_to_file(classified, out_gpkg, layer="denue_clasificacion_productiva_auditada")
    classified.drop(columns="geometry", errors="ignore").to_csv(
        PRODUCTIVE_TABLE_DIR / "denue_clasificacion_productiva_auditada.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pending.drop(columns="geometry", errors="ignore").to_csv(
        PRODUCTIVE_TABLE_DIR / "denue_clasificacion_productiva_pendiente_decision_manual.csv",
        index=False,
        encoding="utf-8-sig",
    )
    audited.drop(columns="geometry", errors="ignore").to_csv(
        PRODUCTIVE_TABLE_DIR / "denue_clasificacion_productiva_con_decision_manual.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary = (
        classified.groupby(["estado_auditoria_productiva", "decision_estudio_final"], dropna=False)
        .size()
        .reset_index(name="registros")
    )
    summary.to_csv(PRODUCTIVE_TABLE_DIR / "resumen_auditoria_productiva_aplicada.csv", index=False, encoding="utf-8-sig")
    log(f"Auditoria productiva aplicada: {len(audited)} auditados manuales, {len(pending)} pendientes")


if __name__ == "__main__":
    apply_audit()
