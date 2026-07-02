from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import OUTPUTS_DIR, PROCESSED_DIR, PROJECT_ROOT, relpath
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
from santa_ana_filter_rules import apply_filter_rules, rule_catalog


OUT_DIR = OUTPUTS_DIR / "santa_ana_xalmimilulco"
LAYERS_DIR = OUT_DIR / "capas_qgis"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"
DOCS_DIR = PROJECT_ROOT / "docs" / "santa_ana_xalmimilulco"
MANIFEST_PATH = OUT_DIR / "pipeline_manifest.json"
REPORT_TEX = DOCS_DIR / "reporte_auditoria_universos_santa_ana.tex"

CLASSIFIED_2026 = PROCESSED_DIR / "denue2026_universo_textil_clasificado.gpkg"
MH_FILTERED = PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp"
CANONICAL_ORIGINAL = (
    OUT_DIR
    / "referencias"
    / "universo_canonico_original"
    / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg"
)
FILTERED_2026 = OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg"
LOCALIDADES = PROCESSED_DIR / "localidades.gpkg"
HIDROGRAFIA = PROCESSED_DIR / "hidrografia.gpkg"

FOCUS_GPKG = LAYERS_DIR / "foco_estricto_alternativo.gpkg"
TRACE_GPKG = LAYERS_DIR / "trazabilidad_filtro_santa_ana_2026.gpkg"
COMPARISON_GPKG = LAYERS_DIR / "comparacion_directa_4_conjuntos.gpkg"
FOCUS_CSV = TABLES_DIR / "foco_estricto_alternativo.csv"
TRACE_CSV = TABLES_DIR / "trazabilidad_filtro_santa_ana_2026.csv"
COMPARISON_CSV = TABLES_DIR / "comparacion_directa_4_conjuntos.csv"
RULES_CSV = TABLES_DIR / "catalogo_reglas_filtro.csv"
SIZES_CSV = TABLES_DIR / "resumen_conjuntos.csv"
PROFILES_CSV = TABLES_DIR / "resumen_perfiles.csv"
CANONICAL_MH_CSV = TABLES_DIR / "comparacion_canonico_vs_mh.csv"
CANONICAL_FOCUS_CSV = TABLES_DIR / "comparacion_canonico_vs_foco.csv"
VALIDATION_CSV = TABLES_DIR / "validacion_trazabilidad.csv"

INPUTS = {
    "universo_canonico_original": CANONICAL_ORIGINAL,
    "mh_filtrado": MH_FILTERED,
    "denue_2026_clasificado": CLASSIFIED_2026,
    "filtrado_prioritario_2026": FILTERED_2026,
}
COLORS = {
    "en_los_4": "#006837",
    "canonico_foco_2026_no_mh": "#31a354",
    "canonico_2026_no_foco_no_mh": "#74c476",
    "solo_canonico_original": "#2b8cbe",
    "mh_foco_2026_no_canonico": "#ae017e",
    "mh_foco_no_canonico_no_2026": "#dd3497",
    "solo_mh_filtrado": "#e7298a",
    "foco_2026_no_canonico_no_mh": "#fd8d3c",
    "solo_foco_estricto": "#756bb1",
    "solo_filtrado_2026": "#f46d43",
    "mh_sin_id": "#969696",
    "canonico_y_mh": "#006837",
    "canonico_y_foco_estricto": "#1b9e77",
    "tratamiento_lavado_acabado_textil": "#d73027",
    "mezclilla_jeans_deshebrado": "#4575b4",
    "produccion_material_textil": "#1a9850",
}
PROFILE_BY_SIGNATURE = {
    (True, True, True, True): "en_los_4",
    (True, False, True, True): "canonico_foco_2026_no_mh",
    (True, False, False, True): "canonico_2026_no_foco_no_mh",
    (True, False, False, False): "solo_canonico_original",
    (False, True, True, True): "mh_foco_2026_no_canonico",
    (False, True, True, False): "mh_foco_no_canonico_no_2026",
    (False, True, False, False): "solo_mh_filtrado",
    (False, False, True, True): "foco_2026_no_canonico_no_mh",
    (False, False, True, False): "solo_foco_estricto",
    (False, False, False, True): "solo_filtrado_2026",
}
HOVER_FIELDS = [
    "_id_key",
    "nombre_mapa",
    "perfil_comparacion",
    "membresias_resumen",
    "categoria_foco_estricto",
    "reglas_inclusion_activadas",
    "reglas_exclusion_activadas",
    "motivo_decision_filtro",
    "en_universo_canonico_original",
    "en_mh_filtrado",
    "en_foco_estricto",
    "en_filtrado_2026_santa",
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
    return out


def load_source_sets() -> dict[str, gpd.GeoDataFrame]:
    filtered = read_vector(FILTERED_2026)
    filtered = filtered.loc[
        filtered["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")
    ].copy()
    return {
        "canonical": prepare_source(read_vector(CANONICAL_ORIGINAL), "canonico_original", "id"),
        "mh": prepare_source(read_vector(MH_FILTERED), "mh_filtrado", "ID DENUE"),
        "filtered": prepare_source(filtered, "filtrado_2026", "id"),
    }


def membership_ids(gdf: gpd.GeoDataFrame) -> set[str]:
    return set(gdf["_id_key"]) - {""}


def build_focus(sets: dict[str, gpd.GeoDataFrame]) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame]:
    trace = apply_filter_rules(read_vector(CLASSIFIED_2026))
    trace["_id_key"] = normalize_denue_id(trace["id"])
    trace["en_universo_canonico_original"] = trace["_id_key"].isin(membership_ids(sets["canonical"]))
    trace["en_mh_filtrado"] = trace["_id_key"].isin(membership_ids(sets["mh"]))
    trace["en_filtrado_2026_santa"] = trace["_id_key"].isin(membership_ids(sets["filtered"]))
    trace["senales_foco_estricto"] = trace["reglas_inclusion_activadas"].replace(
        {"": "sin senal estricta"}
    )
    trace["nota_metodologica_foco"] = (
        "Alternativa analitica trazable; no sustituye al universo canonico original "
        "ni constituye evidencia de descarga o contaminacion."
    )
    focus = trace.loc[trace["flag_foco_textil_estricto"]].copy()

    catalog = rule_catalog()
    catalog["registros_activados"] = catalog["rule_id"].map(
        lambda rule_id: int(trace[f"regla_{rule_id}"].sum())
    )
    return trace, focus, catalog


def first_by_id(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    keyed = gdf.loc[gdf["_id_key"].ne("")].copy()
    return keyed.sort_values("_id_key").drop_duplicates("_id_key", keep="first")


def comparison_union(sets: dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    pieces: list[gpd.GeoDataFrame] = []
    seen: set[str] = set()
    for key in ["canonical", "focus", "filtered", "mh"]:
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
        "en_filtrado_2026_santa": membership_ids(sets["filtered"]),
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
            ("en_foco_estricto", "foco estricto alternativo"),
            ("en_filtrado_2026_santa", "filtrado 2026"),
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
) -> dict[str, pd.DataFrame]:
    return {
        "sizes": pd.DataFrame(
            [
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
                {"conjunto": "foco_estricto_alternativo", "registros": len(sets["focus"])},
                {"conjunto": "filtrado_prioritario_2026", "registros": len(sets["filtered"])},
                {"conjunto": "union_comparacion", "registros": len(comparison)},
            ]
        ),
        "profiles": comparison.groupby("perfil_comparacion", dropna=False)
        .size()
        .reset_index(name="registros"),
        "canonical_mh": count_pair(comparison, "comparacion_canonico_vs_mh"),
        "canonical_focus": count_pair(comparison, "comparacion_canonico_vs_foco"),
    }


def validate_pipeline(
    trace: gpd.GeoDataFrame,
    focus: gpd.GeoDataFrame,
    comparison: gpd.GeoDataFrame,
    sets: dict[str, gpd.GeoDataFrame],
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    focus_ids = membership_ids(sets["focus"])
    trace_focus_ids = set(trace.loc[trace["decision_filtro_estricto"].eq("incluir"), "_id_key"])
    comparison_focus_ids = set(comparison.loc[comparison["en_foco_estricto"], "_id_key"])
    comparison_canonical_ids = set(
        comparison.loc[comparison["en_universo_canonico_original"], "_id_key"]
    )
    missing_rules = [
        rule_id for rule_id in catalog["rule_id"] if f"regla_{rule_id}" not in trace.columns
    ]
    checks = [
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
                trace["decision_filtro_estricto"].eq("incluir")
                & trace["reglas_exclusion_activadas"].ne("")
            ].empty,
            "0 inclusiones con exclusion",
        ),
        ("catalogo_corresponde_a_columnas", not missing_rules, ", ".join(missing_rules) or "ninguna"),
        (
            "ids_comparacion_unicos",
            comparison["_id_key"].ne("").all() and not comparison["_id_key"].duplicated().any(),
            f"{len(comparison)} puntos",
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
            "mapa_comparacion_directa_4_conjuntos",
            "Santa Ana - comparacion de los cuatro conjuntos",
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
            "mapa_canonico_original_vs_foco_estricto",
            "Santa Ana - universo canonico original vs foco estricto alternativo",
        ),
        (
            focus,
            "categoria_foco_estricto",
            "mapa_foco_estricto_alternativo",
            "Santa Ana - foco estricto alternativo",
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
    rules = catalog[["rule_id", "rule_type", "registros_activados"]]
    body = [
        r"\section{Objetivo y jerarquía}",
        (
            "El universo original de Santa Ana es el canónico. MH es una capa ya filtrada de referencia. "
            "El foco estricto es una alternativa analítica trazable y el filtrado 2026 es contextual. "
            "Ningún conjunto constituye evidencia de descarga o contaminación."
        ),
        r"\section{Pipeline único}",
        (
            r"La ejecución completa se realiza con \texttt{python scripts\textbackslash "
            r"run\_santa\_ana\_pipeline.py}: construir alternativa, comparar, documentar y validar."
        ),
        r"\section{Tamaños}",
        latex_table(summaries["sizes"], ["conjunto", "registros"]),
        r"\section{Canónico original frente a MH filtrado}",
        latex_table(
            summaries["canonical_mh"],
            ["comparacion_canonico_vs_mh", "registros"],
        ),
        r"\section{Canónico original frente al foco estricto alternativo}",
        latex_table(
            summaries["canonical_focus"],
            ["comparacion_canonico_vs_foco", "registros"],
        ),
        r"\section{Reglas de la alternativa analítica}",
        latex_table(rules, ["rule_id", "rule_type", "registros_activados"]),
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
        r"\includegraphics[width=0.95\linewidth]{../../outputs/santa_ana_xalmimilulco/mapas/mapa_comparacion_directa_4_conjuntos.png}",
        r"\caption{Comparación de los cuatro conjuntos.}",
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
    for suffix in [".aux", ".log", ".out"]:
        auxiliary = REPORT_TEX.with_suffix(suffix)
        if auxiliary.exists():
            auxiliary.unlink()


def write_index(
    summaries: dict[str, pd.DataFrame],
    validation: pd.DataFrame,
) -> None:
    lines = [
        "# Pipeline único de Santa Ana Xalmimilulco",
        "",
        "Ejecución: `python scripts/run_santa_ana_pipeline.py`.",
        "",
        "## Jerarquía",
        "",
        "- Canónico: universo original de 38 establecimientos.",
        "- Referencia: MH ya filtrado, 49 puntos.",
        "- Alternativa analítica: foco estricto trazable, 67 establecimientos.",
        "- Contexto: filtrado prioritario DENUE 2026, 42 establecimientos.",
        "",
        "## Archivos",
        "",
        "- `referencias/universo_canonico_original/capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg`",
        "- `capas_qgis/comparacion_directa_4_conjuntos.gpkg`",
        "- `capas_qgis/foco_estricto_alternativo.gpkg`",
        "- `capas_qgis/trazabilidad_filtro_santa_ana_2026.gpkg`",
        "- `mapas/mapa_comparacion_directa_4_conjuntos.html`",
        "- `mapas/mapa_canonico_original_vs_mh_filtrado.html`",
        "- `tablas/comparacion_directa_4_conjuntos.csv`",
        "- `tablas/trazabilidad_filtro_santa_ana_2026.csv`",
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
        sets = load_source_sets()
        trace, focus, catalog = build_focus(sets)
        sets["focus"] = prepare_source(focus, "foco_estricto_alternativo", "id")
        export_geodata(focus, FOCUS_GPKG, FOCUS_CSV, "foco_estricto_alternativo")
        export_geodata(trace, TRACE_GPKG, TRACE_CSV, "trazabilidad_filtro")
        catalog.to_csv(RULES_CSV, index=False, encoding="utf-8-sig")
        stages.append({"stage": "construir_alternativa", "status": "ok", "registros": len(focus)})

        comparison = build_comparison(sets)
        summaries = make_summaries(sets, comparison)
        export_geodata(comparison, COMPARISON_GPKG, COMPARISON_CSV, "comparacion_4_conjuntos")
        summaries["sizes"].to_csv(SIZES_CSV, index=False, encoding="utf-8-sig")
        summaries["profiles"].to_csv(PROFILES_CSV, index=False, encoding="utf-8-sig")
        summaries["canonical_mh"].to_csv(CANONICAL_MH_CSV, index=False, encoding="utf-8-sig")
        summaries["canonical_focus"].to_csv(
            CANONICAL_FOCUS_CSV,
            index=False,
            encoding="utf-8-sig",
        )
        save_maps(focus, comparison)
        stages.append({"stage": "comparar", "status": "ok", "registros": len(comparison)})

        validation = validate_pipeline(trace, focus, comparison, sets, catalog)
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
            "universo_canonico_original": len(sets["canonical"]),
            "mh_filtrado": len(sets["mh"]),
            "mh_con_id": int(sets["mh"]["_id_key"].ne("").sum()),
            "mh_sin_id": int(sets["mh"]["_id_key"].eq("").sum()),
            "foco_estricto_alternativo": len(focus),
            "filtrado_prioritario_2026": len(sets["filtered"]),
            "union_comparacion": len(comparison),
            "validaciones_ok": int(validation["resultado"].eq("OK").sum()),
            "sha256_ids_foco_alternativo": id_hash(focus),
        }
        write_manifest(started_at, "ok", stages, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    except Exception:
        write_manifest(started_at, "error", stages)
        raise


if __name__ == "__main__":
    main()
