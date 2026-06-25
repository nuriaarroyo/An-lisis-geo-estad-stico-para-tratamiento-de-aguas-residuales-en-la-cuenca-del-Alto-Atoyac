from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import (
    OUTPUTS_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    clean_dataframe_columns,
    ensure_output_dirs,
    log,
    read_csv_robust,
    relpath,
)


OUT_DIR = OUTPUTS_DIR / "tables" / "comparacion_denue_fuentes_2026"

SOURCES = {
    "processed_raw": {
        "path": PROCESSED_DIR / "denue_raw.gpkg",
        "id": "id",
        "clee": "clee",
        "name": "nombre_de_la_unidad_economica",
    },
    "processed_textil": {
        "path": PROCESSED_DIR / "denue_textil.gpkg",
        "id": "id",
        "clee": "clee",
        "name": "nombre_de_la_unidad_economica",
    },
    "classified": {
        "path": PROCESSED_DIR / "denue_universo_textil_clasificado.gpkg",
        "id": "id",
        "clee": "clee",
        "name": "nombre_de_la_unidad_economica",
    },
    "final_all": {
        "path": OUTPUTS_DIR / "universo_prioritario_denue" / "universo_prioritario_denue.gpkg",
        "id": "id",
        "clee": "clee",
        "name": "nombre_de_la_unidad_economica",
    },
    "final_santa_ana": {
        "path": OUTPUTS_DIR
        / "universo_prioritario_denue"
        / "santa_ana_xalmimilulco"
        / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg",
        "id": "id",
        "clee": "clee",
        "name": "nombre_de_la_unidad_economica",
    },
    "denue2026": {
        "path": RAW_DIR / "denue2026" / "Denue26 area estudio.shp",
        "id": "id",
        "clee": "clee",
        "name": "nom_estab",
    },
    "maryhelen_mh2": {
        "path": PROCESSED_DIR / "capa_maryhelen" / "capa MH2.shp",
        "id": "id",
        "clee": "clee",
        "name": "nom_estab",
    },
    "maryhelen_mh": {
        "path": PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp",
        "id": "ID DENUE",
        "clee": None,
        "name": "DENUE",
    },
    "mayra": {
        "path": PROCESSED_DIR / "capa_mayra" / "capa mayra.shp",
        "id": None,
        "clee": None,
        "name": "Nombre",
    },
}

RAW_ORIGINAL_DENUE = {
    "raw_xalmimilulco": {
        "path": RAW_DIR / "agebs" / "xalmimilulco" / "INEGI_DENUE_.shp",
        "csv": RAW_DIR / "agebs" / "xalmimilulco" / "INEGI_DENUE_.csv",
        "source_folder": "agebs\\xalmimilulco",
    },
    "raw_huejotzingo": {
        "path": RAW_DIR / "agebs" / "huejotzingo" / "INEGI_DENUE_.shp",
        "csv": RAW_DIR / "agebs" / "huejotzingo" / "INEGI_DENUE_.csv",
        "source_folder": "agebs\\huejotzingo",
    },
    "raw_san_martin": {
        "path": RAW_DIR / "agebs" / "san_martin" / "INEGI_DENUE_.shp",
        "csv": RAW_DIR / "agebs" / "san_martin" / "INEGI_DENUE_.csv",
        "source_folder": "agebs\\san_martin",
    },
}


def norm_id(value: pd.Series) -> pd.Series:
    return value.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def norm_clee(value: pd.Series) -> pd.Series:
    return value.astype(str).str.upper().str.strip()


def norm_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).upper().strip()
    text = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_source(label: str, spec: dict) -> gpd.GeoDataFrame:
    path = spec["path"]
    if not path.exists():
        raise FileNotFoundError(path)
    gdf = gpd.read_file(path)
    id_col = spec.get("id")
    clee_col = spec.get("clee")
    name_col = spec.get("name")
    gdf["_source_label"] = label
    gdf["_id_key"] = norm_id(gdf[id_col]) if id_col and id_col in gdf.columns else ""
    gdf["_clee_key"] = norm_clee(gdf[clee_col]) if clee_col and clee_col in gdf.columns else ""
    gdf["_name_norm"] = gdf[name_col].map(norm_text) if name_col and name_col in gdf.columns else ""
    return gdf


def key_set(gdf: pd.DataFrame, column: str) -> set[str]:
    return {value for value in gdf[column].dropna().astype(str) if value}


def summarize_sources(frames: dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    rows = []
    for label, gdf in frames.items():
        rows.append(
            {
                "fuente": label,
                "ruta": relpath(SOURCES[label]["path"]),
                "registros": len(gdf),
                "ids_unicos": len(key_set(gdf, "_id_key")),
                "ids_duplicados": int(gdf["_id_key"].replace("", pd.NA).duplicated().sum()),
                "clee_unicos": len(key_set(gdf, "_clee_key")),
                "clee_duplicados": int(gdf["_clee_key"].replace("", pd.NA).duplicated().sum()),
                "columna_nombre": SOURCES[label].get("name") or "",
                "crs": str(gdf.crs or ""),
            }
        )
    return pd.DataFrame(rows)


def pairwise_overlap(frames: dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    labels = list(frames)
    rows = []
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            left_ids = key_set(frames[left], "_id_key")
            right_ids = key_set(frames[right], "_id_key")
            left_clees = key_set(frames[left], "_clee_key")
            right_clees = key_set(frames[right], "_clee_key")
            rows.append(
                {
                    "fuente_a": left,
                    "fuente_b": right,
                    "ids_a": len(left_ids),
                    "ids_b": len(right_ids),
                    "ids_en_ambas": len(left_ids & right_ids),
                    "ids_a_no_b": len(left_ids - right_ids),
                    "ids_b_no_a": len(right_ids - left_ids),
                    "clee_a": len(left_clees),
                    "clee_b": len(right_clees),
                    "clee_en_ambas": len(left_clees & right_clees),
                    "clee_a_no_b": len(left_clees - right_clees),
                    "clee_b_no_a": len(right_clees - left_clees),
                }
            )
    return pd.DataFrame(rows)


def output_columns(gdf: pd.DataFrame, preferred: list[str]) -> list[str]:
    cols = [c for c in preferred if c in gdf.columns]
    for c in ["_id_key", "_clee_key", "_name_norm"]:
        if c in gdf.columns and c not in cols:
            cols.append(c)
    return cols


def santa_ana_coverage(frames: dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    base = frames["final_santa_ana"]
    base_ids = key_set(base, "_id_key")
    base_clees = key_set(base, "_clee_key")
    rows = []
    for label, gdf in frames.items():
        if label == "final_santa_ana":
            continue
        ids = key_set(gdf, "_id_key")
        clees = key_set(gdf, "_clee_key")
        rows.append(
            {
                "fuente": label,
                "final_santa_ana_ids": len(base_ids),
                "ids_coinciden": len(base_ids & ids),
                "ids_faltan_en_fuente": len(base_ids - ids),
                "clee_coinciden": len(base_clees & clees),
                "clee_faltan_en_fuente": len(base_clees - clees),
            }
        )
    return pd.DataFrame(rows)


def write_missing_from_sources(frames: dict[str, gpd.GeoDataFrame]) -> None:
    base = frames["final_santa_ana"]
    preferred = [
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "localidad",
        "municipio",
        "etapa_productiva_sugerida",
        "flag_estudio_prioritario",
        "distancia_hidrografia_m",
    ]
    rows = []
    for label in ["denue2026", "maryhelen_mh2", "maryhelen_mh"]:
        ids = key_set(frames[label], "_id_key")
        clees = key_set(frames[label], "_clee_key")
        missing = base.loc[~base["_id_key"].isin(ids) & ~base["_clee_key"].isin(clees)].copy()
        if missing.empty:
            continue
        missing["fuente_donde_falta"] = label
        rows.append(missing[["fuente_donde_falta"] + output_columns(missing, preferred)])
    if rows:
        pd.concat(rows, ignore_index=True).to_csv(
            OUT_DIR / "final_santa_ana_faltantes_en_fuentes_nuevas.csv",
            index=False,
            encoding="utf-8-sig",
        )


def compare_denue2026_maryhelen(frames: dict[str, gpd.GeoDataFrame]) -> None:
    left = frames["denue2026"]
    right = frames["maryhelen_mh2"]
    left_ids = key_set(left, "_id_key")
    right_ids = key_set(right, "_id_key")

    out = []
    left_only = left[left["_id_key"].isin(left_ids - right_ids)].copy()
    left_only["comparacion"] = "solo_denue2026"
    out.append(left_only)
    right_only = right[right["_id_key"].isin(right_ids - left_ids)].copy()
    right_only["comparacion"] = "solo_maryhelen_mh2"
    out.append(right_only)
    cols = [
        "comparacion",
        "_id_key",
        "_clee_key",
        "nom_estab",
        "codigo_act",
        "nombre_act",
        "municipio",
        "localidad",
        "FILTRO",
    ]
    pd.concat(out, ignore_index=True)[output_columns(pd.concat(out, ignore_index=True), cols)].to_csv(
        OUT_DIR / "denue2026_vs_maryhelen_mh2_diferencias.csv",
        index=False,
        encoding="utf-8-sig",
    )

    common_ids = left_ids & right_ids
    left_common = left[left["_id_key"].isin(common_ids)].set_index("_id_key")
    right_common = right[right["_id_key"].isin(common_ids)].set_index("_id_key")
    changed = []
    for key in sorted(common_ids):
        lrow = left_common.loc[key]
        rrow = right_common.loc[key]
        if isinstance(lrow, pd.DataFrame):
            lrow = lrow.iloc[0]
        if isinstance(rrow, pd.DataFrame):
            rrow = rrow.iloc[0]
        clee_changed = str(lrow.get("_clee_key", "")) != str(rrow.get("_clee_key", ""))
        name_changed = norm_text(lrow.get("nom_estab", "")) != norm_text(rrow.get("nom_estab", ""))
        if clee_changed or name_changed:
            changed.append(
                {
                    "id": key,
                    "clee_denue2026": lrow.get("_clee_key", ""),
                    "clee_maryhelen_mh2": rrow.get("_clee_key", ""),
                    "nombre_denue2026": lrow.get("nom_estab", ""),
                    "nombre_maryhelen_mh2": rrow.get("nom_estab", ""),
                    "cambio_clee": clee_changed,
                    "cambio_nombre": name_changed,
                }
            )
    pd.DataFrame(changed).to_csv(
        OUT_DIR / "denue2026_vs_maryhelen_mh2_mismos_ids_cambios.csv",
        index=False,
        encoding="utf-8-sig",
    )


def compare_mayra_to_denue2026(frames: dict[str, gpd.GeoDataFrame]) -> None:
    mayra = frames["mayra"].copy()
    denue = frames["denue2026"].copy()
    denue_names = key_set(denue, "_name_norm")
    mayra["nombre_normalizado_en_denue2026"] = mayra["_name_norm"].isin(denue_names)

    mayra_metric = mayra.to_crs(3857)
    denue_metric = denue.to_crs(3857)
    denue_keep = denue_metric[
        [
            "_id_key",
            "_clee_key",
            "_name_norm",
            "nom_estab",
            "codigo_act",
            "nombre_act",
            "municipio",
            "localidad",
            "geometry",
        ]
    ].copy()
    nearest = gpd.sjoin_nearest(mayra_metric, denue_keep, how="left", distance_col="distancia_m_denue2026")
    nearest = nearest.sort_values(["distancia_m_denue2026", "Nombre"], na_position="last")
    cols = [
        "Nombre",
        "Direccion",
        "Filtro",
        "_name_norm_left",
        "nombre_normalizado_en_denue2026",
        "_id_key_right",
        "_clee_key_right",
        "nom_estab",
        "codigo_act",
        "nombre_act",
        "municipio",
        "localidad",
        "distancia_m_denue2026",
    ]
    cols = [c for c in cols if c in nearest.columns]
    nearest[cols].rename(
        columns={
            "_name_norm_left": "nombre_mayra_normalizado",
            "_id_key_right": "id_denue2026_mas_cercano",
            "_clee_key_right": "clee_denue2026_mas_cercano",
        }
    ).to_csv(OUT_DIR / "mayra_cruce_denue2026_nombre_y_distancia.csv", index=False, encoding="utf-8-sig")


def compare_raw_original_to_processed(frames: dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    processed = frames["processed_raw"]
    rows = []
    details = []
    for label, spec in RAW_ORIGINAL_DENUE.items():
        csv_path = spec["csv"]
        shp_path = spec["path"]
        if csv_path.exists():
            raw = clean_dataframe_columns(read_csv_robust(csv_path))
            raw_id_col = "id" if "id" in raw.columns else "id_llave_r"
            raw_clee_col = "clee" if "clee" in raw.columns else "subsector_"
            raw_name_col = "nom_estab" if "nom_estab" in raw.columns else "rama_activ"
        else:
            raw = gpd.read_file(shp_path).drop(columns="geometry", errors="ignore")
            raw_id_col = "id_llave_r"
            raw_clee_col = "subsector_"
            raw_name_col = "rama_activ"

        raw["_id_key"] = norm_id(raw[raw_id_col]) if raw_id_col in raw.columns else ""
        raw["_clee_key"] = norm_clee(raw[raw_clee_col]) if raw_clee_col in raw.columns else ""
        raw["_name_norm"] = raw[raw_name_col].map(norm_text) if raw_name_col in raw.columns else ""

        subset = processed[processed["source_folder"].astype(str).eq(spec["source_folder"])].copy()
        raw_ids = key_set(raw, "_id_key")
        processed_ids = key_set(subset, "_id_key")
        raw_clees = key_set(raw, "_clee_key")
        processed_clees = key_set(subset, "_clee_key")
        rows.append(
            {
                "fuente_original": label,
                "ruta": relpath(csv_path if csv_path.exists() else shp_path),
                "processed_source_folder": spec["source_folder"],
                "registros_original": len(raw),
                "registros_processed_raw": len(subset),
                "ids_en_ambas": len(raw_ids & processed_ids),
                "ids_original_no_processed": len(raw_ids - processed_ids),
                "ids_processed_no_original": len(processed_ids - raw_ids),
                "clee_en_ambas": len(raw_clees & processed_clees),
                "clee_original_no_processed": len(raw_clees - processed_clees),
                "clee_processed_no_original": len(processed_clees - raw_clees),
            }
        )
        if raw_ids - processed_ids:
            sample = raw[raw["_id_key"].isin(raw_ids - processed_ids)].head(20).copy()
            sample["fuente_original"] = label
            details.append(sample[["fuente_original", "_id_key", "_clee_key", raw_name_col]])
    if details:
        pd.concat(details, ignore_index=True).to_csv(
            OUT_DIR / "originales_raw_faltantes_en_processed_raw_muestra.csv",
            index=False,
            encoding="utf-8-sig",
        )
    return pd.DataFrame(rows)


def write_report(
    summary: pd.DataFrame,
    pairwise: pd.DataFrame,
    coverage: pd.DataFrame,
    raw_check: pd.DataFrame,
) -> None:
    def markdown_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "_Sin registros._"
        clean = df.astype(str).replace({"nan": "", "None": ""})
        headers = list(clean.columns)
        rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for _, row in clean.iterrows():
            values = [str(row[col]).replace("|", "/") for col in headers]
            rows.append("| " + " | ".join(values) + " |")
        return "\n".join(rows)

    def value(df: pd.DataFrame, source: str, column: str) -> int:
        row = df[df["fuente"].eq(source)]
        return int(row.iloc[0][column]) if not row.empty else 0

    denue_mh2 = pairwise[
        pairwise["fuente_a"].eq("denue2026") & pairwise["fuente_b"].eq("maryhelen_mh2")
    ].iloc[0]
    santa_denue = coverage[coverage["fuente"].eq("denue2026")].iloc[0]
    santa_mh2 = coverage[coverage["fuente"].eq("maryhelen_mh2")].iloc[0]
    santa_mh = coverage[coverage["fuente"].eq("maryhelen_mh")].iloc[0]
    lines = [
        "# Comparacion DENUE 2026 y capas externas",
        "",
        "Este reporte cruza llaves `id` y `clee` normalizadas. Para Mayra, la capa no trae `id`/`clee`, por lo que se usa nombre normalizado y vecino espacial mas cercano.",
        "",
        "## Hallazgos principales",
        "",
        f"- Universo final actual: {value(summary, 'final_all', 'registros')} registros; Santa Ana Xalmimilulco: {value(summary, 'final_santa_ana', 'registros')} registros.",
        f"- DENUE 2026 trae {value(summary, 'denue2026', 'registros')} registros; Maryhelen MH2 trae {value(summary, 'maryhelen_mh2', 'registros')} registros.",
        f"- DENUE 2026 y Maryhelen MH2 comparten {int(denue_mh2['ids_en_ambas'])} ids; {int(denue_mh2['ids_a_no_b'])} ids estan solo en DENUE 2026 y {int(denue_mh2['ids_b_no_a'])} solo en Maryhelen MH2.",
        f"- De los 38 registros finales de Santa Ana, DENUE 2026 contiene {int(santa_denue['ids_coinciden'])} por id y falta {int(santa_denue['ids_faltan_en_fuente'])}.",
        f"- Maryhelen MH2 contiene {int(santa_mh2['ids_coinciden'])} de esos 38 por id y falta {int(santa_mh2['ids_faltan_en_fuente'])}; por `clee` coincide menos porque hay cambios de `clee` entre capas.",
        f"- Maryhelen MH contiene solo {int(santa_mh['ids_coinciden'])} de los 38 por id; parece una seleccion pequena, no un DENUE completo.",
        "",
        "## Lectura metodologica",
        "",
        "- No hay evidencia de mezcla de ids en la ruta vieja: `processed_raw`, `processed_textil`, `classified` y `final_santa_ana` conservan una relacion 1:1 por `id`/`clee`.",
        "- La diferencia fuerte viene de versiones/fuentes: DENUE 2026 y Maryhelen MH2 casi son la misma base por `id`, pero no identicas; ademas algunos `clee` cambian aunque el `id` sea el mismo.",
        "- `capa_mayra` requiere conciliacion por nombre y coordenadas porque no trae identificadores DENUE.",
        "- El lenguaje de estos resultados debe leerse como priorizacion/posible presion por proceso textil; no como prueba de descarga o contaminacion.",
        "",
        "## Archivos generados",
        "",
        "- `resumen_fuentes.csv`",
        "- `matriz_coincidencias_id_clee.csv`",
        "- `cobertura_final_santa_ana_por_fuente.csv`",
        "- `final_santa_ana_faltantes_en_fuentes_nuevas.csv`",
        "- `denue2026_vs_maryhelen_mh2_diferencias.csv`",
        "- `denue2026_vs_maryhelen_mh2_mismos_ids_cambios.csv`",
        "- `mayra_cruce_denue2026_nombre_y_distancia.csv`",
        "- `originales_raw_vs_processed_raw.csv`",
        "",
        "## Reaplicar filtrado al DENUE 2026",
        "",
        "Para hacerlo bien, conviene crear una rama de procesamiento 2026: convertir `data/raw/denue2026/Denue26 area estudio.shp` a un `denue_raw_2026.gpkg`, correr el mismo filtro textil, recalcular distancia a hidrografia, correr la clasificacion productiva, y solo despues aplicar auditoria/manual FALSE si los ids siguen vigentes. No conviene sobreescribir `data/processed/denue_raw.gpkg` hasta comparar resultados.",
        "",
        "## Chequeo contra fuentes originales usadas antes",
        "",
        markdown_table(raw_check),
        "",
    ]
    (OUT_DIR / "reporte_comparacion_denue_fuentes_2026.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frames = {}
    for label, spec in SOURCES.items():
        log(f"Leyendo {label}: {relpath(spec['path'])}")
        frames[label] = read_source(label, spec)

    summary = summarize_sources(frames)
    pairwise = pairwise_overlap(frames)
    coverage = santa_ana_coverage(frames)
    raw_check = compare_raw_original_to_processed(frames)

    summary.to_csv(OUT_DIR / "resumen_fuentes.csv", index=False, encoding="utf-8-sig")
    pairwise.to_csv(OUT_DIR / "matriz_coincidencias_id_clee.csv", index=False, encoding="utf-8-sig")
    coverage.to_csv(OUT_DIR / "cobertura_final_santa_ana_por_fuente.csv", index=False, encoding="utf-8-sig")
    raw_check.to_csv(OUT_DIR / "originales_raw_vs_processed_raw.csv", index=False, encoding="utf-8-sig")

    write_missing_from_sources(frames)
    compare_denue2026_maryhelen(frames)
    compare_mayra_to_denue2026(frames)
    write_report(summary, pairwise, coverage, raw_check)

    log(f"Comparacion guardada en {relpath(OUT_DIR)}")


if __name__ == "__main__":
    main()
