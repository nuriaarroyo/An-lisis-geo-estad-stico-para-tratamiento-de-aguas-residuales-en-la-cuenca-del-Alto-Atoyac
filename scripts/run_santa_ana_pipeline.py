from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import (
    OUTPUTS_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
    clean_dataframe_columns,
    normalize_text,
    read_csv_robust,
    relpath,
)
from santa_ana_audit_utils import (
    compile_latex,
    ensure_directories,
    export_geodata,
    latex_document,
    latex_escape,
    latex_table,
    markdown_table,
    normalize_denue_id,
    read_vector,
    save_interactive_map,
    save_static_map,
)
from santa_ana_filter_rules import (
    FILTER_CONFIG_PATHS,
    FilterCatalogs,
    apply_filter_rules,
    load_filter_catalogs,
    rule_catalog,
)


OUT_DIR = OUTPUTS_DIR / "santa_ana_xalmimilulco"
LAYERS_DIR = OUT_DIR / "capas_qgis"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"
DOCS_DIR = PROJECT_ROOT / "docs" / "santa_ana_xalmimilulco"
MANIFEST_PATH = OUT_DIR / "pipeline_manifest.json"
REPORT_TEX = DOCS_DIR / "reporte_auditoria_universos_santa_ana.tex"

DENUE_2026_RAW = PROCESSED_DIR / "denue2026_raw.gpkg"
PREVIOUS_CLASSIFICATION = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "santa_ana_xalmimilulco"
    / "filtro_anterior_clasificacion.csv"
)
EXPLICIT_CLASSIFICATION = PROCESSED_DIR / "denue2026_santa_ana_clasificacion_explicita.gpkg"
EXPLICIT_RELEVANT_REVIEW = PROCESSED_DIR / "denue2026_santa_ana_relevantes_revisar.gpkg"
MH_FILTERED = PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp"
SAIC_FILES = sorted((RAW_DIR / "saic").glob("*.csv"))
SAIC_SOURCE = SAIC_FILES[0] if SAIC_FILES else RAW_DIR / "saic" / "SAIC.csv"
CANONICAL_ORIGINAL = (
    OUT_DIR
    / "referencias"
    / "universo_canonico_original"
    / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg"
)
LOCALIDADES = PROCESSED_DIR / "localidades.gpkg"
HIDROGRAFIA = PROCESSED_DIR / "hidrografia.gpkg"

FOCUS_GPKG = LAYERS_DIR / "universo_relevante_filtro_explicito.gpkg"
CANDIDATES_GPKG = LAYERS_DIR / "denue_textil_candidatos.gpkg"
TRACE_GPKG = LAYERS_DIR / "clasificacion_explicita_todos.gpkg"
RELEVANT_REVIEW_GPKG = LAYERS_DIR / "relevantes_revisar.gpkg"
COMPARISON_GPKG = LAYERS_DIR / "comparacion_3_universos.gpkg"
FOCUS_CSV = TABLES_DIR / "universo_relevante_filtro_explicito.csv"
CANDIDATES_CSV = TABLES_DIR / "denue_textil_candidatos.csv"
TRACE_CSV = TABLES_DIR / "clasificacion_explicita_todos.csv"
RELEVANT_REVIEW_CSV = TABLES_DIR / "clasificacion_explicita_relevantes_revisar.csv"
SAIC_CSV = TABLES_DIR / "saic_actividades_textiles.csv"
COMPARISON_CSV = TABLES_DIR / "comparacion_3_universos.csv"
RULES_CSV = TABLES_DIR / "catalogo_reglas_filtro.csv"
KEYWORDS_CSV = TABLES_DIR / "diccionario_palabras_clave.csv"
SCIAN_RULES_CSV = TABLES_DIR / "catalogo_codigos_scian.csv"
CATEGORY_POLICY_CSV = TABLES_DIR / "politica_categorias.csv"
SIZES_CSV = TABLES_DIR / "resumen_conjuntos.csv"
PROFILES_CSV = TABLES_DIR / "resumen_perfiles.csv"
CATEGORY_SUMMARY_CSV = TABLES_DIR / "resumen_categorias_filtro.csv"
CANONICAL_MH_CSV = TABLES_DIR / "comparacion_canonico_vs_mh.csv"
CANONICAL_FOCUS_CSV = TABLES_DIR / "comparacion_canonico_vs_foco.csv"
VALIDATION_CSV = TABLES_DIR / "validacion_trazabilidad.csv"
PREVIOUS_COMPARISON_CSV = TABLES_DIR / "comparacion_filtro_anterior_vs_explicito.csv"
PREVIOUS_DETAIL_CSV = TABLES_DIR / "detalle_comparacion_filtro_anterior_vs_explicito.csv"

INPUTS = {
    "universo_canonico_original": CANONICAL_ORIGINAL,
    "mh_filtrado": MH_FILTERED,
    "saic": SAIC_SOURCE,
    "denue_2026_preparado": DENUE_2026_RAW,
    "filtro_anterior_referencia": PREVIOUS_CLASSIFICATION,
    **FILTER_CONFIG_PATHS,
}
COLORS = {
    "en_los_3": "#006837",
    "canonico_y_foco_no_mh": "#31a354",
    "solo_canonico_original": "#2b8cbe",
    "mh_y_foco_no_canonico": "#dd3497",
    "solo_mh_filtrado": "#e7298a",
    "solo_foco_estricto": "#756bb1",
    "mh_sin_id": "#969696",
    "canonico_y_mh": "#006837",
    "canonico_y_foco_estricto": "#1b9e77",
    "lavado_acabado_textil": "#d73027",
    "produccion_textil": "#1a9850",
    "maquila_textil": "#4575b4",
    "tratamiento_lavado_acabado_textil": "#d73027",
    "mezclilla_jeans_deshebrado": "#4575b4",
    "produccion_material_textil": "#1a9850",
}
PROFILE_BY_SIGNATURE = {
    (True, True, True): "en_los_3",
    (True, False, True): "canonico_y_foco_no_mh",
    (True, False, False): "solo_canonico_original",
    (False, True, True): "mh_y_foco_no_canonico",
    (False, True, False): "solo_mh_filtrado",
    (False, False, True): "solo_foco_estricto",
}
HOVER_FIELDS = [
    "_id_key",
    "nombre_mapa",
    "perfil_comparacion",
    "membresias_resumen",
    "categoria_filtro",
    "relevancia_ambiental",
    "motivo_clasificacion",
    "keywords_detectadas",
    "grupos_keywords_detectados",
    "etapas_productivas_detectadas",
    "universos_keywords_detectados",
    "niveles_evidencia_detectados",
    "campos_coincidentes",
    "clasificacion_anterior",
    "categoria_foco_estricto",
    "reglas_inclusion_activadas",
    "reglas_exclusion_activadas",
    "motivo_decision_filtro",
    "en_universo_canonico_original",
    "en_mh_filtrado",
    "en_foco_estricto",
]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def clean_generated_outputs() -> None:
    expected_root = (OUTPUTS_DIR / "santa_ana_xalmimilulco").resolve()
    if OUT_DIR.resolve() != expected_root or OUT_DIR.resolve().parent != OUTPUTS_DIR.resolve():
        raise RuntimeError(f"Ruta de limpieza no permitida: {OUT_DIR.resolve()}")
    for directory in [LAYERS_DIR, MAPS_DIR, TABLES_DIR, OUT_DIR / "reporte"]:
        if not directory.exists():
            continue
        if directory.resolve().parent != OUT_DIR.resolve():
            raise RuntimeError(f"Subcarpeta de limpieza no permitida: {directory.resolve()}")
        children = list(directory.iterdir())
        if any(child.is_dir() for child in children):
            raise RuntimeError(f"No se limpiara una subcarpeta anidada: {directory.resolve()}")
        for child in children:
            child.unlink()
        directory.rmdir()
    for path in [OUT_DIR / "index.md", MANIFEST_PATH]:
        if path.exists():
            path.unlink()


def require_inputs() -> None:
    missing = [f"{name}: {relpath(path)}" for name, path in INPUTS.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("Faltan entradas:\n" + "\n".join(missing))


def prepare_source(gdf: gpd.GeoDataFrame, source: str, id_column: str) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["_id_key"] = normalize_denue_id(out[id_column])
    out["fuente_geometria"] = source
    for column in ["nombre_de_la_unidad_economica", "nombre_mapa", "Name"]:
        if column in out.columns:
            out["nombre_mapa"] = out[column].fillna("").astype(str)
            break
    explicit_columns = {
        "_id_key",
        "id",
        "ID DENUE",
        "clee",
        "nombre_mapa",
        "nombre_de_la_unidad_economica",
        "Name",
        "raz_social",
        "codigo_de_la_clase_actividad_scian",
        "nombre_clase_actividad_scian",
        "per_ocu",
        "localidad",
        "municipio",
        "latitud",
        "longitud",
        "fuente_geometria",
        "texto_normalizado",
        "keywords_detectadas",
        "campos_coincidentes",
        "clasificacion_anterior",
        "comparacion_filtro",
        "relevancia_ambiental",
        "geometry",
    }
    audit_prefixes = (
        "regla_",
        "match_",
        "flag_",
        "decision_",
        "motivo_",
        "categoria_",
        "senales_",
        "nota_metodologica",
    )
    keep = [
        column
        for column in out.columns
        if column in explicit_columns or column.startswith(audit_prefixes)
    ]
    return out[keep].copy()


def load_source_sets() -> dict[str, gpd.GeoDataFrame]:
    return {
        "canonical": prepare_source(read_vector(CANONICAL_ORIGINAL), "canonico_original", "id"),
        "mh": prepare_source(read_vector(MH_FILTERED), "mh_filtrado", "ID DENUE"),
    }


def membership_ids(gdf: gpd.GeoDataFrame) -> set[str]:
    return set(gdf["_id_key"]) - {""}


def add_previous_classification(trace: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = trace.copy()
    out["flag_anterior"] = False
    out["clasificacion_anterior"] = "sin_registro_en_filtro_anterior"
    if PREVIOUS_CLASSIFICATION.exists():
        previous = read_csv_robust(PREVIOUS_CLASSIFICATION, dtype=str).fillna("")
        previous["_id_key"] = normalize_denue_id(previous["id"])
        priority_raw = previous.get(
            "flag_estudio_prioritario",
            pd.Series(False, index=previous.index),
        ).fillna(False)
        priority = (
            priority_raw.astype(bool)
            if pd.api.types.is_bool_dtype(priority_raw)
            else priority_raw.astype(str).str.lower().isin({"true", "1", "si", "yes"})
        )
        previous_ids = set(previous["_id_key"]) - {""}
        priority_ids = set(previous.loc[priority, "_id_key"]) - {""}
        out["flag_anterior"] = out["_id_key"].isin(priority_ids)
        out.loc[
            out["_id_key"].isin(previous_ids),
            "clasificacion_anterior",
        ] = "no_prioritario_anterior"
        out.loc[out["flag_anterior"], "clasificacion_anterior"] = "prioritario_anterior"

    old = out["flag_anterior"]
    new = out["flag_nuevo_relevante"]
    review = out["flag_nuevo_revisar"]
    out["comparacion_filtro"] = "antes_no_ahora_fuera"
    out.loc[~old & review, "comparacion_filtro"] = "revisar"
    out.loc[~old & new, "comparacion_filtro"] = "antes_no_ahora_entra"
    out.loc[old & ~new & ~review, "comparacion_filtro"] = "antes_entraba_ahora_excluye"
    out.loc[old & review, "comparacion_filtro"] = "antes_entraba_ahora_revisar"
    out.loc[old & new, "comparacion_filtro"] = "antes_y_ahora_entra"
    return out


def classify_saic_activities() -> tuple[pd.DataFrame, tuple[str, ...]]:
    raw = read_csv_robust(SAIC_SOURCE, skiprows=4)
    raw = clean_dataframe_columns(raw)
    raw = raw.loc[:, ~raw.columns.str.startswith("unnamed")].dropna(how="all")
    activity_column = next(
        (
            column
            for column in raw.columns
            if "actividad_economica" in normalize_text(column)
        ),
        None,
    )
    if activity_column is None:
        raise ValueError("SAIC no contiene una columna de actividad economica.")
    activity = raw[activity_column].fillna("").astype(str)
    catalog = pd.DataFrame(
        {
            "actividad_codigo": activity.str.extract(r"\b(\d{3,6})\b", expand=False).fillna(""),
            "actividad_nombre": activity.str.replace(r"^\D*\d{3,6}\s*", "", regex=True).str.strip(),
        }
    ).drop_duplicates()
    normalized_name = catalog["actividad_nombre"].map(normalize_text)
    catalog["es_actividad_textil"] = (
        catalog["actividad_codigo"].str.startswith(("313", "314", "315"))
        | normalized_name.str.contains(r"textil|prendas de vestir", regex=True, na=False)
    )
    catalog["prefijo_scian_busqueda"] = catalog["actividad_codigo"].str[:3]
    textile = catalog.loc[
        catalog["es_actividad_textil"] & catalog["prefijo_scian_busqueda"].ne("")
    ].copy()
    prefixes = tuple(sorted(textile["prefijo_scian_busqueda"].unique()))
    if not prefixes:
        raise ValueError("SAIC no produjo prefijos textiles para filtrar DENUE.")
    return textile, prefixes


def build_focus(
    sets: dict[str, gpd.GeoDataFrame],
    saic_prefixes: tuple[str, ...],
    catalogs: FilterCatalogs,
) -> tuple[
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    pd.DataFrame,
]:
    trace = apply_filter_rules(read_vector(DENUE_2026_RAW), saic_prefixes, catalogs)
    trace["_id_key"] = normalize_denue_id(trace["id"])
    trace = add_previous_classification(trace)
    trace["en_universo_canonico_original"] = trace["_id_key"].isin(membership_ids(sets["canonical"]))
    trace["en_mh_filtrado"] = trace["_id_key"].isin(membership_ids(sets["mh"]))
    trace["senales_foco_estricto"] = trace["reglas_inclusion_activadas"].replace(
        {"": "sin senal estricta"}
    )
    trace["nota_metodologica_foco"] = (
        "Clasificacion directa SAIC -> DENUE -> filtro explicito. El resultado no sustituye al canonico original "
        "ni constituye evidencia de descarga o contaminacion."
    )
    candidates = trace.loc[trace["flag_candidato_textil"]].copy()
    focus = trace.loc[trace["flag_foco_textil_estricto"]].copy()
    relevant_review = trace.loc[
        trace["flag_nuevo_relevante"] | trace["flag_nuevo_revisar"]
    ].copy()

    catalog = rule_catalog(catalogs)
    catalog["registros_activados"] = catalog["rule_id"].map(
        lambda rule_id: int(trace[f"regla_{rule_id}"].sum())
    )
    return trace, candidates, focus, relevant_review, catalog


def first_by_id(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    keyed = gdf.loc[gdf["_id_key"].ne("")].copy()
    return keyed.sort_values("_id_key").drop_duplicates("_id_key", keep="first")


def comparison_union(sets: dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    pieces: list[gpd.GeoDataFrame] = []
    seen: set[str] = set()
    for key in ["canonical", "focus", "mh"]:
        source = first_by_id(sets[key])
        new_rows = source.loc[~source["_id_key"].isin(seen)].copy()
        pieces.append(new_rows)
        seen.update(new_rows["_id_key"])
    combined = gpd.GeoDataFrame(
        pd.concat(pieces, ignore_index=True),
        geometry="geometry",
        crs=sets["canonical"].crs,
    )
    mh_without_id = sets["mh"].loc[sets["mh"]["_id_key"].eq("")].copy()
    if not mh_without_id.empty:
        mh_without_id["_id_key"] = [
            f"mh_sin_id_{position + 1}" for position in range(len(mh_without_id))
        ]
        combined = gpd.GeoDataFrame(
            pd.concat([combined, mh_without_id], ignore_index=True),
            geometry="geometry",
            crs=sets["canonical"].crs,
        )
    return combined


def pair_membership(
    frame: pd.DataFrame,
    left: str,
    right: str,
    both_label: str,
    left_label: str,
    right_label: str,
) -> pd.Series:
    result = pd.Series("fuera_de_ambos", index=frame.index)
    result.loc[frame[left]] = left_label
    result.loc[frame[right]] = right_label
    result.loc[frame[left] & frame[right]] = both_label
    return result


def build_comparison(sets: dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    combined = comparison_union(sets)
    membership = {
        "en_universo_canonico_original": membership_ids(sets["canonical"]),
        "en_mh_filtrado": membership_ids(sets["mh"]),
        "en_foco_estricto": membership_ids(sets["focus"]),
    }
    for column, ids in membership.items():
        combined[column] = combined["_id_key"].isin(ids)
    mh_without_id = combined["_id_key"].str.startswith("mh_sin_id_")
    combined.loc[mh_without_id, "en_mh_filtrado"] = True

    def profile(row: pd.Series) -> str:
        if str(row["_id_key"]).startswith("mh_sin_id_"):
            return "mh_sin_id"
        signature = tuple(bool(row[column]) for column in membership)
        return PROFILE_BY_SIGNATURE.get(signature, "otro")

    combined["perfil_comparacion"] = combined.apply(profile, axis=1)
    combined["comparacion_canonico_vs_mh"] = pair_membership(
        combined,
        "en_universo_canonico_original",
        "en_mh_filtrado",
        "canonico_y_mh",
        "solo_canonico_original",
        "solo_mh_filtrado",
    )
    combined.loc[mh_without_id, "comparacion_canonico_vs_mh"] = "mh_sin_id"
    combined["comparacion_canonico_vs_foco"] = pair_membership(
        combined,
        "en_universo_canonico_original",
        "en_foco_estricto",
        "canonico_y_foco_estricto",
        "solo_canonico_original",
        "solo_foco_estricto",
    )

    labels = [
        label
        for column, label in [
            ("en_universo_canonico_original", "canonico original"),
            ("en_mh_filtrado", "MH filtrado"),
            ("en_foco_estricto", "filtro explicito relevante"),
        ]
        if column in combined
    ]
    combined["membresias_resumen"] = combined.apply(
        lambda row: "; ".join(
            label
            for column, label in zip(membership, labels)
            if bool(row[column])
        ),
        axis=1,
    )
    return combined


def count_pair(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    relevant = frame.loc[frame[column].ne("fuera_de_ambos")]
    return relevant.groupby(column, dropna=False).size().reset_index(name="registros")


def make_summaries(
    sets: dict[str, gpd.GeoDataFrame],
    comparison: gpd.GeoDataFrame,
    trace: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
) -> dict[str, pd.DataFrame]:
    return {
        "sizes": pd.DataFrame(
            [
                {"conjunto": "denue_2026_santa_ana_total", "registros": len(trace)},
                {"conjunto": "denue_textil_candidatos", "registros": len(candidates)},
                {"conjunto": "universo_canonico_original_santa_ana", "registros": len(sets["canonical"])},
                {"conjunto": "mh_filtrado", "registros": len(sets["mh"])},
                {
                    "conjunto": "mh_filtrado_con_id",
                    "registros": int(sets["mh"]["_id_key"].ne("").sum()),
                },
                {
                    "conjunto": "mh_filtrado_sin_id",
                    "registros": int(sets["mh"]["_id_key"].eq("").sum()),
                },
                {"conjunto": "universo_relevante_filtro_explicito", "registros": len(sets["focus"])},
                {
                    "conjunto": "registros_revisar_filtro_explicito",
                    "registros": int(trace["flag_nuevo_revisar"].sum()),
                },
                {"conjunto": "union_comparacion", "registros": len(comparison)},
            ]
        ),
        "profiles": comparison.groupby("perfil_comparacion", dropna=False)
        .size()
        .reset_index(name="registros"),
        "filter_categories": trace.groupby(
            ["categoria_filtro", "relevancia_ambiental"],
            dropna=False,
        )
        .size()
        .reset_index(name="registros")
        .sort_values("registros", ascending=False),
        "canonical_mh": count_pair(comparison, "comparacion_canonico_vs_mh"),
        "canonical_focus": count_pair(comparison, "comparacion_canonico_vs_foco"),
    }


def validate_pipeline(
    trace: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
    focus: gpd.GeoDataFrame,
    comparison: gpd.GeoDataFrame,
    sets: dict[str, gpd.GeoDataFrame],
    catalog: pd.DataFrame,
    catalogs: FilterCatalogs,
) -> pd.DataFrame:
    focus_ids = membership_ids(sets["focus"])
    trace_focus_ids = set(trace.loc[trace["flag_nuevo_relevante"], "_id_key"])
    comparison_focus_ids = set(comparison.loc[comparison["en_foco_estricto"], "_id_key"])
    comparison_canonical_ids = set(
        comparison.loc[comparison["en_universo_canonico_original"], "_id_key"]
    )
    missing_rules = [
        rule_id for rule_id in catalog["rule_id"] if f"regla_{rule_id}" not in trace.columns
    ]
    checks = [
        (
            "candidatos_son_subconjunto_denue",
            set(candidates["_id_key"]).issubset(set(trace["_id_key"])),
            f"{len(candidates)} candidatos",
        ),
        (
            "foco_es_subconjunto_candidatos",
            focus_ids.issubset(set(candidates["_id_key"])),
            f"{len(focus_ids)} IDs",
        ),
        ("foco_ids_unicos", len(focus_ids) == len(focus), f"{len(focus_ids)} IDs"),
        ("foco_igual_a_trazabilidad", focus_ids == trace_focus_ids, f"{len(focus_ids)} IDs"),
        (
            "foco_igual_a_comparacion",
            focus_ids == comparison_focus_ids,
            f"{len(comparison_focus_ids)} IDs",
        ),
        (
            "canonico_igual_a_comparacion",
            membership_ids(sets["canonical"]) == comparison_canonical_ids,
            f"{len(comparison_canonical_ids)} IDs",
        ),
        (
            "mh_filtrado_total",
            int(comparison["en_mh_filtrado"].sum()) == len(sets["mh"]),
            f"{len(sets['mh'])} puntos",
        ),
        (
            "exclusion_tiene_prioridad",
            trace.loc[
                trace["flag_nuevo_relevante"]
                & (trace["match_comercio_excluir"] | trace["match_lavado_no_textil"])
            ].empty,
            "0 inclusiones con exclusion",
        ),
        ("catalogo_corresponde_a_columnas", not missing_rules, ", ".join(missing_rules) or "ninguna"),
        (
            "ids_comparacion_unicos",
            comparison["_id_key"].ne("").all() and not comparison["_id_key"].duplicated().any(),
            f"{len(comparison)} puntos",
        ),
        (
            "diccionario_keywords_ids_unicos",
            not catalogs.keywords["keyword_id"].duplicated().any(),
            f"{len(catalogs.keywords)} palabras",
        ),
        (
            "politica_cubre_resultados",
            set(trace["categoria_filtro"]).issubset(set(catalogs.categories["category"])),
            f"{trace['categoria_filtro'].nunique()} categorias usadas",
        ),
    ]
    return pd.DataFrame(
        {
            "validacion": [name for name, _, _ in checks],
            "resultado": ["OK" if passed else "ERROR" for _, passed, _ in checks],
            "detalle": [detail for _, _, detail in checks],
        }
    )


def save_maps(focus: gpd.GeoDataFrame, comparison: gpd.GeoDataFrame) -> None:
    specifications = [
        (
            comparison,
            "perfil_comparacion",
            "mapa_comparacion_3_universos",
            "Santa Ana - comparacion de los tres universos",
        ),
        (
            comparison,
            "comparacion_canonico_vs_mh",
            "mapa_canonico_original_vs_mh_filtrado",
            "Santa Ana - universo canonico original vs MH filtrado",
        ),
        (
            comparison,
            "comparacion_canonico_vs_foco",
            "mapa_canonico_original_vs_filtro_explicito",
            "Santa Ana - universo canonico original vs filtro explicito",
        ),
        (
            focus,
            "categoria_filtro",
            "mapa_universo_relevante_filtro_explicito",
            "Santa Ana - universo relevante del filtro explicito",
        ),
    ]
    for frame, column, filename, title in specifications:
        save_static_map(
            frame,
            column,
            MAPS_DIR / f"{filename}.png",
            title,
            COLORS,
            LOCALIDADES,
            HIDROGRAFIA,
            excluded_values={"fuera_de_ambos"},
        )
        save_interactive_map(
            frame,
            column,
            MAPS_DIR / f"{filename}.html",
            title,
            COLORS,
            HOVER_FIELDS,
            excluded_values={"fuera_de_ambos"},
        )


def write_report(
    catalog: pd.DataFrame,
    summaries: dict[str, pd.DataFrame],
) -> None:
    rules = catalog[["rule_id", "stage", "registros_activados"]]
    previous_comparison = pd.read_csv(PREVIOUS_COMPARISON_CSV, encoding="utf-8-sig")
    body = [
        r"\section{Objetivo y jerarquía}",
        (
            "El universo original de Santa Ana es el canónico. MH es una capa ya filtrada de referencia. "
            "El filtro explícito nuevo es una alternativa analítica trazable. "
            "Ningún conjunto constituye evidencia de descarga o contaminación."
        ),
        r"\section{Pipeline único}",
        (
            r"La ejecución completa se realiza con \texttt{python scripts\textbackslash "
            r"run\_santa\_ana\_pipeline.py}. Primero SAIC define las familias manufactureras textiles; "
            r"después esas familias y los servicios 8122 se buscan en DENUE; finalmente se aplican "
            r"las exclusiones y señales estrictas aprendidas."
        ),
        r"\section{Tamaños}",
        (
            r"Los vocabularios, codigos SCIAN y prioridades se leen desde "
            r"\texttt{config\textbackslash filtros\_textiles\_santa\_ana}. "
            r"Ningun script historico es entrada de esta ejecucion."
        ),
        latex_table(summaries["sizes"], ["conjunto", "registros"]),
        r"\section{Resultado del filtro explícito}",
        latex_table(
            summaries["filter_categories"],
            ["categoria_filtro", "relevancia_ambiental", "registros"],
        ),
        r"\section{Comparación con el filtro anterior}",
        latex_table(previous_comparison, ["comparacion_filtro", "registros"]),
        r"\section{Canónico original frente a MH filtrado}",
        latex_table(
            summaries["canonical_mh"],
            ["comparacion_canonico_vs_mh", "registros"],
        ),
        r"\section{Canónico original frente al filtro explícito}",
        latex_table(
            summaries["canonical_focus"],
            ["comparacion_canonico_vs_foco", "registros"],
        ),
        r"\section{Reglas de la alternativa analítica}",
        latex_table(rules, ["rule_id", "stage", "registros_activados"]),
        r"\begin{description}",
        *[
            (
                rf"\item[\texttt{{{latex_escape(row['rule_id'])}}}] "
                f"{latex_escape(row['interpretation'])}"
            )
            for _, row in catalog.iterrows()
        ],
        r"\end{description}",
        r"\section{Mapas}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../../outputs/santa_ana_xalmimilulco/mapas/mapa_comparacion_3_universos.png}",
        r"\caption{Comparación de los tres universos vigentes.}",
        r"\end{figure}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../../outputs/santa_ana_xalmimilulco/mapas/mapa_canonico_original_vs_mh_filtrado.png}",
        r"\caption{Universo canónico original frente a MH filtrado.}",
        r"\end{figure}",
    ]
    REPORT_TEX.write_text(
        latex_document("Auditoría de universos de Santa Ana Xalmimilulco", body),
        encoding="utf-8",
    )
    if not compile_latex(REPORT_TEX):
        raise RuntimeError(f"No se pudo compilar {relpath(REPORT_TEX)}")
    for suffix in [".aux", ".fdb_latexmk", ".fls", ".log", ".out", ".synctex.gz"]:
        auxiliary = REPORT_TEX.with_suffix(suffix)
        for attempt in range(5):
            try:
                auxiliary.unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.25)


def write_index(
    summaries: dict[str, pd.DataFrame],
    validation: pd.DataFrame,
) -> None:
    lines = [
        "# Pipeline único de Santa Ana Xalmimilulco",
        "",
        "Ejecución: `python scripts/run_santa_ana_pipeline.py`.",
        "",
        "Proceso: `SAIC -> candidatos textiles DENUE -> filtro explícito -> comparaciones`.",
        "",
        "## Jerarquía",
        "",
        "- Canónico: universo original de 38 establecimientos.",
        "- Referencia: MH ya filtrado, 49 puntos.",
        "- Alternativa analítica: filtro explícito trazable con categorías relevante y revisar.",
        "",
        "## Archivos",
        "",
        "- `../../config/filtros_textiles_santa_ana/README.md`",
        "- `../../config/filtros_textiles_santa_ana/palabras_clave.csv`",
        "- `../../config/filtros_textiles_santa_ana/codigos_scian.csv`",
        "- `../../config/filtros_textiles_santa_ana/politica_categorias.csv`",
        "- `referencias/universo_canonico_original/capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg`",
        "- `capas_qgis/denue_textil_candidatos.gpkg`",
        "- `capas_qgis/comparacion_3_universos.gpkg`",
        "- `capas_qgis/universo_relevante_filtro_explicito.gpkg`",
        "- `capas_qgis/clasificacion_explicita_todos.gpkg`",
        "- `capas_qgis/relevantes_revisar.gpkg`",
        "- `mapas/mapa_comparacion_3_universos.html`",
        "- `mapas/mapa_canonico_original_vs_mh_filtrado.html`",
        "- `tablas/comparacion_3_universos.csv`",
        "- `tablas/saic_actividades_textiles.csv`",
        "- `tablas/denue_textil_candidatos.csv`",
        "- `tablas/clasificacion_explicita_todos.csv`",
        "- `tablas/clasificacion_explicita_relevantes_revisar.csv`",
        "- `tablas/diccionario_palabras_clave.csv`",
        "- `tablas/catalogo_codigos_scian.csv`",
        "- `tablas/politica_categorias.csv`",
        "- `tablas/catalogo_reglas_filtro.csv`",
        "- `tablas/comparacion_filtro_anterior_vs_explicito.csv`",
        "- `tablas/resumen_categorias_filtro.csv`",
        "- `tablas/validacion_trazabilidad.csv`",
        "- `pipeline_manifest.json`",
        "- `../../docs/santa_ana_xalmimilulco/guia_pipeline.md`",
        "- `../../docs/santa_ana_xalmimilulco/reporte_auditoria_universos_santa_ana.pdf`",
        "",
        "## Tamaños",
        "",
        markdown_table(summaries["sizes"]),
        "",
        "## Canónico vs MH",
        "",
        markdown_table(summaries["canonical_mh"]),
        "",
        "## Categorías del filtro explícito",
        "",
        markdown_table(summaries["filter_categories"]),
        "",
        "## Validación",
        "",
        markdown_table(validation),
        "",
    ]
    (OUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def file_metadata(path: Path) -> dict[str, object]:
    return {
        "path": relpath(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def id_hash(focus: gpd.GeoDataFrame) -> str:
    ids = sorted(membership_ids(focus))
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def write_manifest(
    started_at: str,
    status: str,
    stages: list[dict[str, object]],
    summary: dict[str, object] | None = None,
) -> None:
    manifest = {
        "pipeline": "auditoria_santa_ana",
        "goal": "Conservar el original como canónico y comparar tres conjuntos secundarios.",
        "started_at": started_at,
        "finished_at": now() if status != "running" else None,
        "status": status,
        "inputs": {name: file_metadata(path) for name, path in INPUTS.items()},
        "stages": stages,
        "summary": summary or {},
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    started_at = now()
    require_inputs()
    clean_generated_outputs()
    ensure_directories([OUT_DIR, LAYERS_DIR, MAPS_DIR, TABLES_DIR, DOCS_DIR])
    stages: list[dict[str, object]] = []
    write_manifest(started_at, "running", stages)

    try:
        catalogs = load_filter_catalogs()
        catalogs.keywords.to_csv(KEYWORDS_CSV, index=False, encoding="utf-8-sig")
        catalogs.scian.to_csv(SCIAN_RULES_CSV, index=False, encoding="utf-8-sig")
        catalogs.categories.to_csv(CATEGORY_POLICY_CSV, index=False, encoding="utf-8-sig")
        saic_activities, saic_prefixes = classify_saic_activities()
        saic_activities.to_csv(SAIC_CSV, index=False, encoding="utf-8-sig")
        stages.append(
            {
                "stage": "clasificar_saic",
                "status": "ok",
                "prefijos_scian": list(saic_prefixes),
            }
        )

        sets = load_source_sets()
        trace, candidates, focus, relevant_review, catalog = build_focus(
            sets,
            saic_prefixes,
            catalogs,
        )
        sets["focus"] = prepare_source(focus, "filtro_explicito_relevante", "id")
        export_geodata(
            candidates,
            CANDIDATES_GPKG,
            CANDIDATES_CSV,
            "denue_textil_candidatos",
        )
        export_geodata(focus, FOCUS_GPKG, FOCUS_CSV, "universo_relevante_explicito")
        export_geodata(trace, TRACE_GPKG, TRACE_CSV, "clasificacion_explicita")
        export_geodata(
            relevant_review,
            RELEVANT_REVIEW_GPKG,
            RELEVANT_REVIEW_CSV,
            "relevantes_revisar",
        )
        export_geodata(
            trace,
            EXPLICIT_CLASSIFICATION,
            TRACE_CSV,
            "clasificacion_explicita",
        )
        export_geodata(
            relevant_review,
            EXPLICIT_RELEVANT_REVIEW,
            RELEVANT_REVIEW_CSV,
            "relevantes_revisar",
        )
        catalog.to_csv(RULES_CSV, index=False, encoding="utf-8-sig")
        (
            trace.groupby("comparacion_filtro", dropna=False)
            .size()
            .reset_index(name="registros")
            .to_csv(PREVIOUS_COMPARISON_CSV, index=False, encoding="utf-8-sig")
        )
        comparison_detail_columns = [
            "_id_key",
            "id",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "nombre_clase_actividad_scian",
            "clasificacion_anterior",
            "flag_anterior",
            "categoria_filtro",
            "flag_nuevo_relevante",
            "flag_nuevo_revisar",
            "comparacion_filtro",
            "motivo_clasificacion",
            "keywords_detectadas",
        ]
        trace[comparison_detail_columns].to_csv(
            PREVIOUS_DETAIL_CSV,
            index=False,
            encoding="utf-8-sig",
        )
        stages.append(
            {
                "stage": "clasificar_denue",
                "status": "ok",
                "candidatos_textiles": len(candidates),
                "filtro_explicito_relevante": len(focus),
            }
        )

        comparison = build_comparison(sets)
        summaries = make_summaries(sets, comparison, trace, candidates)
        export_geodata(comparison, COMPARISON_GPKG, COMPARISON_CSV, "comparacion_3_universos")
        summaries["sizes"].to_csv(SIZES_CSV, index=False, encoding="utf-8-sig")
        summaries["profiles"].to_csv(PROFILES_CSV, index=False, encoding="utf-8-sig")
        summaries["filter_categories"].to_csv(
            CATEGORY_SUMMARY_CSV,
            index=False,
            encoding="utf-8-sig",
        )
        summaries["canonical_mh"].to_csv(CANONICAL_MH_CSV, index=False, encoding="utf-8-sig")
        summaries["canonical_focus"].to_csv(
            CANONICAL_FOCUS_CSV,
            index=False,
            encoding="utf-8-sig",
        )
        save_maps(focus, comparison)
        stages.append({"stage": "comparar", "status": "ok", "registros": len(comparison)})

        validation = validate_pipeline(
            trace,
            candidates,
            focus,
            comparison,
            sets,
            catalog,
            catalogs,
        )
        validation.to_csv(VALIDATION_CSV, index=False, encoding="utf-8-sig")
        if validation["resultado"].eq("ERROR").any():
            raise RuntimeError("La validacion produjo errores.")
        stages.append(
            {
                "stage": "validar",
                "status": "ok",
                "validaciones": int(validation["resultado"].eq("OK").sum()),
            }
        )

        write_report(catalog, summaries)
        write_index(summaries, validation)
        stages.append({"stage": "documentar", "status": "ok"})

        summary = {
            "denue_2026_santa_ana_total": len(trace),
            "denue_textil_candidatos": len(candidates),
            "prefijos_textiles_saic": list(saic_prefixes),
            "universo_canonico_original": len(sets["canonical"]),
            "mh_filtrado": len(sets["mh"]),
            "mh_con_id": int(sets["mh"]["_id_key"].ne("").sum()),
            "mh_sin_id": int(sets["mh"]["_id_key"].eq("").sum()),
            "universo_relevante_filtro_explicito": len(focus),
            "registros_revisar": int(trace["flag_nuevo_revisar"].sum()),
            "union_comparacion": len(comparison),
            "validaciones_ok": int(validation["resultado"].eq("OK").sum()),
            "sha256_ids_filtro_explicito": id_hash(focus),
        }
        write_manifest(started_at, "ok", stages, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    except Exception:
        write_manifest(started_at, "error", stages)
        raise


if __name__ == "__main__":
    main()
