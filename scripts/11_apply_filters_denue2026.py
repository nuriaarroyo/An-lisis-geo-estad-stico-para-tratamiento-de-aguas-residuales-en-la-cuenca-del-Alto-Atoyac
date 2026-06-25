from __future__ import annotations

import importlib.util
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import (
    OUTPUTS_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    SCRIPTS_DIR,
    TABLES_DIR,
    ensure_crs_and_project,
    ensure_output_dirs,
    log,
    read_gpkg,
    relpath,
    safe_to_file,
)


SOURCE = RAW_DIR / "denue2026" / "Denue26 area estudio.shp"
TABLE_OUT = TABLES_DIR / "denue2026_clasificacion_productiva"
UNIVERSE_OUT = OUTPUTS_DIR / "universo_prioritario_denue_2026"

PROCESSED_RAW = PROCESSED_DIR / "denue2026_raw.gpkg"
PROCESSED_TEXTIL = PROCESSED_DIR / "denue2026_textil.gpkg"
PROCESSED_DISTANCE = PROCESSED_DIR / "denue2026_textil_con_distancia.gpkg"
PROCESSED_CLASSIFIED = PROCESSED_DIR / "denue2026_universo_textil_clasificado.gpkg"


def load_script(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


filter_mod = load_script("02_filter_denue_textil.py", "filter_denue_textil")
spatial_mod = load_script("04_spatial_analysis.py", "spatial_analysis")
class_mod = load_script("02b_clasificacion_productiva_denue.py", "clasificacion_productiva_denue")
final_mod = load_script("09_make_final_priority_universe.py", "final_priority_universe")


def standardize_denue2026(path: Path) -> gpd.GeoDataFrame:
    denue = gpd.read_file(path)
    denue = denue.rename(
        columns={
            "nom_estab": "nombre_de_la_unidad_economica",
            "codigo_act": "codigo_de_la_clase_actividad_scian",
            "nombre_act": "nombre_clase_actividad_scian",
        }
    )
    denue["id"] = denue["id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    denue["clee"] = denue["clee"].astype(str).str.upper().str.strip()
    denue["source_path"] = relpath(path)
    denue["source_file"] = path.name
    denue["source_folder"] = "denue2026"
    denue["layer_type"] = "denue"
    denue = ensure_crs_and_project(denue, "EPSG:6372")
    return denue


def filter_textile(denue: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    search_text = filter_mod.build_search_text(denue)
    scian = filter_mod.scian_code_series(denue)
    regex = filter_mod.keyword_regex()
    candidate_mask = search_text.str.contains(regex, na=False) | scian.str.startswith(filter_mod.TEXTILE_SCIAN_PREFIXES)
    excluded_commerce = filter_mod.commerce_exclusion_mask(search_text, scian)
    excluded_non_textile = filter_mod.non_textile_exclusion_mask(search_text, scian)
    mask = candidate_mask & ~excluded_commerce & ~excluded_non_textile

    textil = denue.loc[mask].copy()
    textil["texto_busqueda"] = search_text.loc[mask]
    textil["codigo_scian_detectado"] = scian.loc[mask]
    textil["palabras_clave_detectadas"] = textil["texto_busqueda"].map(
        lambda value: "; ".join(sorted({match.group(0) for match in regex.finditer(value)}))
    )
    textil["categoria_relevancia_ambiental"] = textil["texto_busqueda"].map(filter_mod.classify_relevance)
    textil["nota_metodologica"] = (
        "Priorizacion preliminar por produccion, confeccion, maquila, acabado o lavado textil; "
        "se excluye comercio de prendas y no implica evidencia de contaminacion directa."
    )

    excluded = denue.loc[candidate_mask & (excluded_commerce | excluded_non_textile)].copy()
    if not excluded.empty:
        excluded["texto_busqueda"] = search_text.loc[excluded.index]
        excluded["codigo_scian_detectado"] = scian.loc[excluded.index]
    return textil, excluded


def add_distances(textil: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    hydro_path = PROCESSED_DIR / "hidrografia.gpkg"
    hydro = read_gpkg(hydro_path) if hydro_path.exists() else gpd.GeoDataFrame(geometry=[], crs=textil.crs)
    if not hydro.empty and hydro.crs != textil.crs:
        hydro = hydro.to_crs(textil.crs)
    out = textil.copy()
    out["distancia_hidrografia_m"] = spatial_mod.nearest_distance_to_hydro(out, hydro)
    out, _buffer_counts = spatial_mod.add_buffer_membership(out, hydro)
    out = spatial_mod.add_distance_ranges(out)
    return out


def classify_without_source_folder_override(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    if "localidad" not in out.columns:
        out["localidad"] = ""
    if "municipio" not in out.columns:
        out["municipio"] = ""
    records = [class_mod.classify_row(row) for _, row in out.iterrows()]
    classified = pd.DataFrame(records, index=out.index)
    for column in classified.columns:
        out[column] = classified[column]
    for column in class_mod.BOOLEAN_COLUMNS:
        if column in out.columns:
            out[column] = out[column].fillna(False).astype(bool)
    return out


def write_tables(classified: gpd.GeoDataFrame, excluded: gpd.GeoDataFrame) -> None:
    TABLE_OUT.mkdir(parents=True, exist_ok=True)
    universes = class_mod.universe_tables(classified)
    for name, gdf in universes.items():
        class_mod.tabular(gdf).to_csv(TABLE_OUT / f"denue2026_{name}.csv", index=False, encoding="utf-8-sig")
    class_mod.tabular(excluded).to_csv(TABLE_OUT / "denue2026_excluidos_comercio_prendas.csv", index=False, encoding="utf-8-sig")

    summary_rows = [
        {"indicador": "A_denue2026_total_area_estudio", "registros": len(read_gpkg(PROCESSED_RAW))},
        {"indicador": "B_textil_inicial_2026", "registros": len(classified)},
        {
            "indicador": "C_textil_depurado_2026",
            "registros": len(universes["universo_textil_depurado"]),
        },
        {
            "indicador": "D_alcance_proyecto_2026",
            "registros": int(classified["flag_universo_alcance_proyecto"].sum()),
        },
        {
            "indicador": "E_prioritario_automatico_2026",
            "registros": int(classified["flag_estudio_prioritario"].sum()),
        },
        {
            "indicador": "F_pendiente_auditoria_2026",
            "registros": int(classified["requiere_auditoria_manual"].sum()),
        },
    ]
    pd.DataFrame(summary_rows).to_csv(TABLE_OUT / "conteo_universos_2026.csv", index=False, encoding="utf-8-sig")

    by_locality = (
        classified.groupby("localidad", dropna=False)
        .agg(
            textil=("id", "count"),
            alcance=("flag_universo_alcance_proyecto", "sum"),
            prioritario=("flag_estudio_prioritario", "sum"),
        )
        .reset_index()
        .sort_values(["prioritario", "alcance", "textil"], ascending=False)
    )
    by_locality.to_csv(TABLE_OUT / "conteo_por_localidad_2026.csv", index=False, encoding="utf-8-sig")

    scian = classified["codigo_de_la_clase_actividad_scian"].astype(str).str.extract(r"(\d+)", expand=False).fillna("")
    textile_code = scian.str.startswith(("313", "314", "315", "8122"))
    priority = classified["flag_estudio_prioritario"].astype(bool)
    generic_terms = classified["palabras_clave_etapa"].fillna("").astype(str).str.contains(
        r"\btratamiento\b|\bacabado\b", case=False, regex=True
    )
    alerts = classified.loc[priority & ~textile_code & generic_terms].copy()
    alert_cols = [
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "nombre_clase_actividad_scian",
        "localidad",
        "municipio",
        "etapa_productiva_sugerida",
        "palabras_clave_etapa",
        "evidencia_clasificacion",
        "motivo_flag_estudio_prioritario",
        "distancia_hidrografia_m",
    ]
    alerts[[c for c in alert_cols if c in alerts.columns]].to_csv(
        TABLE_OUT / "alertas_posibles_falsos_positivos_prioritarios_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )


def write_final_universe(classified: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    UNIVERSE_OUT.mkdir(parents=True, exist_ok=True)
    manual_false = final_mod.read_manual_false_ids()
    with_manual = final_mod.add_manual_flags(classified, manual_false)
    final, excluded, manual_false_all, summary = final_mod.build_final_universe(with_manual)

    safe_to_file(final, UNIVERSE_OUT / "universo_prioritario_denue_2026.gpkg", layer="universo_prioritario_denue_2026")
    final.drop(columns="geometry", errors="ignore").to_csv(
        UNIVERSE_OUT / "universo_prioritario_denue_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )
    excluded.drop(columns="geometry", errors="ignore").to_csv(
        UNIVERSE_OUT / "excluidos_por_auditoria_manual_false_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )
    manual_false_all.drop(columns="geometry", errors="ignore").to_csv(
        UNIVERSE_OUT / "coincidencias_auditoria_manual_false_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary.to_csv(UNIVERSE_OUT / "resumen_universo_prioritario_denue_2026.csv", index=False, encoding="utf-8-sig")
    return final


def compare_with_current(final_2026: gpd.GeoDataFrame) -> None:
    current_path = OUTPUTS_DIR / "universo_prioritario_denue" / "universo_prioritario_denue.gpkg"
    if not current_path.exists():
        return
    current = read_gpkg(current_path)
    old_ids = set(current["id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip())
    new_ids = set(final_2026["id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip())
    rows = [
        {"comparacion": "en_ambos_universos_prioritarios", "registros": len(old_ids & new_ids)},
        {"comparacion": "solo_universo_actual", "registros": len(old_ids - new_ids)},
        {"comparacion": "solo_universo_2026", "registros": len(new_ids - old_ids)},
    ]
    pd.DataFrame(rows).to_csv(UNIVERSE_OUT / "comparacion_universo_actual_vs_2026.csv", index=False, encoding="utf-8-sig")

    old_only = current[current["id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().isin(old_ids - new_ids)].copy()
    new_only = final_2026[
        final_2026["id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().isin(new_ids - old_ids)
    ].copy()
    old_only["comparacion"] = "solo_universo_actual"
    new_only["comparacion"] = "solo_universo_2026"
    keep = [
        "comparacion",
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "localidad",
        "municipio",
        "etapa_productiva_sugerida",
        "distancia_hidrografia_m",
        "motivo_flag_estudio_prioritario",
    ]
    pd.concat([old_only, new_only], ignore_index=True)[lambda df: [c for c in keep if c in df.columns]].to_csv(
        UNIVERSE_OUT / "diferencias_universo_actual_vs_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )


def main() -> None:
    ensure_output_dirs()
    TABLE_OUT.mkdir(parents=True, exist_ok=True)
    UNIVERSE_OUT.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        log(f"No existe {relpath(SOURCE)}")
        return

    log("Estandarizando DENUE 2026")
    denue = standardize_denue2026(SOURCE)
    safe_to_file(denue, PROCESSED_RAW, layer="denue2026_raw")

    log("Aplicando filtro textil 2026")
    textil, excluded = filter_textile(denue)
    safe_to_file(textil, PROCESSED_TEXTIL, layer="denue2026_textil")

    log("Calculando distancia a hidrografia")
    textil_distance = add_distances(textil)
    safe_to_file(textil_distance, PROCESSED_DISTANCE, layer="denue2026_textil_con_distancia")

    log("Clasificando universo productivo 2026")
    classified = classify_without_source_folder_override(textil_distance)
    safe_to_file(classified, PROCESSED_CLASSIFIED, layer="denue2026_universo_textil_clasificado")
    classified.drop(columns="geometry", errors="ignore").to_csv(
        TABLE_OUT / "denue2026_universo_textil_clasificado.csv",
        index=False,
        encoding="utf-8-sig",
    )
    write_tables(classified, excluded)

    log("Construyendo universo prioritario 2026")
    final_2026 = write_final_universe(classified)
    compare_with_current(final_2026)
    log(f"Universo 2026 guardado en {relpath(UNIVERSE_OUT)}")


if __name__ == "__main__":
    main()
