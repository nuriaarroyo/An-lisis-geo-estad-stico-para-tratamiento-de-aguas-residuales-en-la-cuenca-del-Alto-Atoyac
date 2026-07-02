from __future__ import annotations

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


OUT_DIR = OUTPUTS_DIR / "foco_textil_estricto_santa_ana_2026"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"
LAYERS_DIR = OUT_DIR / "capas_qgis"
DOCS_DIR = PROJECT_ROOT / "docs"

FOCO_ESTRICTO = LAYERS_DIR / "foco_textil_estricto_santa_ana_2026.gpkg"
FILTRADO_2026 = OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg"
MH_REFERENCIA = PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp"
CANONICO_ORIGINAL = (
    OUTPUTS_DIR
    / "universo_prioritario_denue"
    / "santa_ana_xalmimilulco"
    / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg"
)
LOCALIDADES = PROCESSED_DIR / "localidades.gpkg"
HIDROGRAFIA = PROCESSED_DIR / "hidrografia.gpkg"
RULE_CATALOG = TABLES_DIR / "catalogo_reglas_filtro.csv"
OBSOLETE_OUTPUTS = [
    MAPS_DIR / "mapa_foco_estricto_vs_union_previa.html",
    MAPS_DIR / "mapa_foco_estricto_vs_union_previa.png",
    TABLES_DIR / "comparacion_directa_foco_vs_union_previa.csv",
]

COLORS = {
    "en_los_4": "#006837",
    "estricto_2026_union_no_mh": "#31a354",
    "estricto_y_2026_no_mh_no_union": "#78c679",
    "estricto_y_mh_no_2026": "#1f78b4",
    "solo_estricto": "#756bb1",
    "2026_union_no_estricto_no_mh": "#fdae61",
    "mh_union_no_estricto_no_2026": "#e7298a",
    "union_no_estricto_no_2026_no_mh": "#8c6d31",
    "solo_2026": "#f46d43",
    "solo_mh": "#d01c8b",
    "mh_sin_id": "#969696",
    "otro": "#636363",
    "estricto_y_filtrado_2026": "#1b9e77",
    "solo_foco_estricto": "#756bb1",
    "solo_filtrado_2026": "#f46d43",
    "estricto_y_mh": "#1b9e77",
    "solo_mh_con_id": "#e7298a",
    "fuera_union_previa": "#756bb1",
    "union_sin_foco_estricto": "#8c6d31",
    "canonico_y_mh": "#006837",
    "solo_canonico_original": "#2b8cbe",
    "solo_mh_filtrado": "#e7298a",
    "canonico_y_foco_estricto": "#1b9e77",
    "solo_foco_estricto": "#756bb1",
    "canonico_y_filtrado_2026": "#31a354",
    "canonico_foco_2026_no_mh": "#31a354",
    "canonico_2026_no_foco_no_mh": "#74c476",
    "mh_foco_no_canonico_no_2026": "#dd3497",
    "mh_foco_2026_no_canonico": "#ae017e",
    "foco_2026_no_canonico_no_mh": "#fd8d3c",
}
HOVER_FIELDS = [
    "_id_key",
    "id",
    "nombre_mapa",
    "nombre_de_la_unidad_economica",
    "Name",
    "perfil_comparacion",
    "membresias_resumen",
    "lectura_auditoria",
    "categoria_foco_estricto",
    "reglas_inclusion_activadas",
    "reglas_exclusion_activadas",
    "motivo_decision_filtro",
    "senales_foco_estricto",
    "codigo_de_la_clase_actividad_scian",
    "nombre_clase_actividad_scian",
    "en_foco_estricto",
    "en_universo_canonico_original",
    "en_filtrado_2026_santa",
    "en_mh_filtrado",
]
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
AUDIT_READINGS = {
    "en_los_4": (
        "Coincide en el universo canonico original, MH filtrado, foco estricto y filtrado 2026."
    ),
    "canonico_foco_2026_no_mh": (
        "Pertenece al canonico original, foco estricto y filtrado 2026; MH filtrado no lo conserva."
    ),
    "solo_canonico_original": "Pertenece exclusivamente al universo canonico original.",
    "solo_mh_filtrado": "Pertenece exclusivamente al universo MH ya filtrado.",
    "solo_foco_estricto": (
        "Entra solo en el foco estricto alternativo; revisar como ampliacion analitica."
    ),
    "mh_sin_id": "Punto de MH filtrado sin ID DENUE; no puede compararse por identificador.",
}


def ensure_dirs() -> None:
    ensure_directories([MAPS_DIR, TABLES_DIR, LAYERS_DIR, DOCS_DIR])
    for path in OBSOLETE_OUTPUTS:
        if path.exists():
            path.unlink()


def name_series(gdf: pd.DataFrame) -> pd.Series:
    for column in ["nombre_de_la_unidad_economica", "nombre_mapa", "Name"]:
        if column in gdf.columns:
            return gdf[column].fillna("").astype(str)
    return pd.Series("", index=gdf.index)


def prepare_source(
    gdf: gpd.GeoDataFrame,
    source: str,
    id_column: str,
) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["_id_key"] = normalize_denue_id(out[id_column]) if id_column in out.columns else ""
    out["fuente_geometria"] = source
    out["nombre_mapa"] = name_series(out)
    return out


def load_sets() -> dict[str, gpd.GeoDataFrame]:
    focus = prepare_source(read_vector(FOCO_ESTRICTO), "foco_estricto", "id")
    filtered = read_vector(FILTRADO_2026)
    filtered = filtered.loc[
        filtered["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")
    ].copy()
    return {
        "canonical": prepare_source(
            read_vector(CANONICO_ORIGINAL),
            "universo_canonico_original",
            "id",
        ),
        "focus": focus,
        "filtered": prepare_source(filtered, "filtrado_2026", "id"),
        "mh": prepare_source(read_vector(MH_REFERENCIA), "mh_filtrado", "ID DENUE"),
    }


def first_by_id(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    keyed = gdf.loc[gdf["_id_key"].ne("")].copy()
    return keyed.sort_values("_id_key").drop_duplicates("_id_key", keep="first")


def union_by_preferred_geometry(sets: dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
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
        crs=sets["focus"].crs,
    )

    mh_without_id = sets["mh"].loc[sets["mh"]["_id_key"].eq("")].copy()
    if not mh_without_id.empty:
        mh_without_id["_id_key"] = [
            f"mh_sin_id_{position + 1}" for position in range(len(mh_without_id))
        ]
        combined = gpd.GeoDataFrame(
            pd.concat([combined, mh_without_id], ignore_index=True),
            geometry="geometry",
            crs=sets["focus"].crs,
        )
    return combined


def pair_membership(
    df: pd.DataFrame,
    left: str,
    right: str,
    both_label: str,
    left_label: str,
    right_label: str,
) -> pd.Series:
    result = pd.Series("fuera_de_ambos", index=df.index)
    result.loc[df[left]] = left_label
    result.loc[df[right]] = right_label
    result.loc[df[left] & df[right]] = both_label
    return result


def comparison_profile(row: pd.Series) -> str:
    if str(row["_id_key"]).startswith("mh_sin_id_"):
        return "mh_sin_id"
    signature = (
        bool(row["en_universo_canonico_original"]),
        bool(row["en_mh_filtrado"]),
        bool(row["en_foco_estricto"]),
        bool(row["en_filtrado_2026_santa"]),
    )
    return PROFILE_BY_SIGNATURE.get(signature, "otro")


def build_comparison(sets: dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    combined = union_by_preferred_geometry(sets)
    membership_columns = {
        "en_universo_canonico_original": set(sets["canonical"]["_id_key"]) - {""},
        "en_foco_estricto": set(sets["focus"]["_id_key"]) - {""},
        "en_filtrado_2026_santa": set(sets["filtered"]["_id_key"]) - {""},
        "en_mh_filtrado": set(sets["mh"]["_id_key"]) - {""},
    }
    for column, ids in membership_columns.items():
        combined[column] = combined["_id_key"].isin(ids)
    is_mh_without_id = combined["_id_key"].str.startswith("mh_sin_id_")
    combined.loc[is_mh_without_id, "en_mh_filtrado"] = True

    combined["perfil_comparacion"] = combined.apply(comparison_profile, axis=1)
    combined["comparacion_canonico_vs_mh"] = pair_membership(
        combined,
        "en_universo_canonico_original",
        "en_mh_filtrado",
        "canonico_y_mh",
        "solo_canonico_original",
        "solo_mh_filtrado",
    )
    combined.loc[is_mh_without_id, "comparacion_canonico_vs_mh"] = "mh_sin_id"
    combined["comparacion_canonico_vs_foco"] = pair_membership(
        combined,
        "en_universo_canonico_original",
        "en_foco_estricto",
        "canonico_y_foco_estricto",
        "solo_canonico_original",
        "solo_foco_estricto",
    )
    combined["comparacion_canonico_vs_2026"] = pair_membership(
        combined,
        "en_universo_canonico_original",
        "en_filtrado_2026_santa",
        "canonico_y_filtrado_2026",
        "solo_canonico_original",
        "solo_filtrado_2026",
    )
    combined["comparacion_estricto_vs_2026"] = pair_membership(
        combined,
        "en_foco_estricto",
        "en_filtrado_2026_santa",
        "estricto_y_filtrado_2026",
        "solo_foco_estricto",
        "solo_filtrado_2026",
    )
    combined["comparacion_estricto_vs_mh"] = pair_membership(
        combined,
        "en_foco_estricto",
        "en_mh_filtrado",
        "estricto_y_mh",
        "solo_foco_estricto",
        "solo_mh_con_id",
    )
    combined.loc[is_mh_without_id, "comparacion_estricto_vs_mh"] = "mh_sin_id"
    combined["membresias_resumen"] = combined.apply(membership_summary, axis=1)
    combined["lectura_auditoria"] = combined["perfil_comparacion"].map(AUDIT_READINGS).fillna(
        "Revisar en mapa y tabla por combinacion de membresias."
    )
    return combined


def membership_summary(row: pd.Series) -> str:
    labels = [
        label
        for column, label in [
            ("en_universo_canonico_original", "universo canonico original"),
            ("en_mh_filtrado", "MH filtrado"),
            ("en_foco_estricto", "foco estricto"),
            ("en_filtrado_2026_santa", "filtrado 2026"),
        ]
        if bool(row[column])
    ]
    return "; ".join(labels) or "sin membresia"


def count_pair(comp: pd.DataFrame, column: str) -> pd.DataFrame:
    relevant = comp.loc[comp[column].ne("fuera_de_ambos")].copy()
    return relevant.groupby(column, dropna=False).size().reset_index(name="registros")


def make_tables(
    comp: gpd.GeoDataFrame,
    sets: dict[str, gpd.GeoDataFrame],
) -> dict[str, pd.DataFrame]:
    return {
        "resumen_tamanos": pd.DataFrame(
            [
                {
                    "conjunto": "universo_canonico_original_santa_ana",
                    "registros": len(sets["canonical"]),
                },
                {"conjunto": "mh_filtrado", "registros": len(sets["mh"])},
                {
                    "conjunto": "mh_filtrado_con_id",
                    "registros": int(sets["mh"]["_id_key"].ne("").sum()),
                },
                {
                    "conjunto": "mh_filtrado_sin_id",
                    "registros": int(sets["mh"]["_id_key"].eq("").sum()),
                },
                {"conjunto": "foco_estricto_santa_ana_2026", "registros": len(sets["focus"])},
                {
                    "conjunto": "filtrado_prioritario_denue_2026_santa_ana",
                    "registros": len(sets["filtered"]),
                },
                {"conjunto": "union_total_comparacion_directa", "registros": len(comp)},
            ]
        ),
        "perfil_comparacion": comp.groupby("perfil_comparacion", dropna=False)
        .size()
        .reset_index(name="registros"),
        "canonico_vs_mh": count_pair(comp, "comparacion_canonico_vs_mh"),
        "canonico_vs_foco_estricto": count_pair(comp, "comparacion_canonico_vs_foco"),
        "canonico_vs_filtrado_2026": count_pair(comp, "comparacion_canonico_vs_2026"),
        "foco_vs_filtrado_2026": count_pair(comp, "comparacion_estricto_vs_2026"),
        "foco_vs_mh": count_pair(comp, "comparacion_estricto_vs_mh"),
    }


def write_rule_description(catalog: pd.DataFrame) -> str:
    lines = [r"\begin{description}"]
    for _, row in catalog.iterrows():
        label = latex_escape(row["rule_id"])
        source = latex_escape(row["source"])
        criterion = latex_escape(row["criterion"])
        interpretation = latex_escape(row["interpretation"])
        lines.append(
            rf"\item[\texttt{{{label}}}] Fuente: {source}. Criterio: {criterion}. {interpretation}"
        )
    lines.append(r"\end{description}")
    return "\n".join(lines)


def write_docs(tables: dict[str, pd.DataFrame]) -> Path:
    tex = DOCS_DIR / "comparacion_foco_textil_estricto_santa_ana_2026.tex"
    catalog = pd.read_csv(RULE_CATALOG, encoding="utf-8-sig")
    rule_summary = catalog[["rule_id", "rule_type", "registros_activados"]]
    body = [
        r"\section{Secuencia del análisis}",
        (
            r"La entrada operativa única es \texttt{python scripts\textbackslash "
            r"run\_santa\_ana\_pipeline.py}. El pipeline separa filtrado, comparación y validación."
        ),
        r"\begin{enumerate}",
        r"\item Se parte de la capa DENUE 2026 clasificada.",
        r"\item Se conservan exclusivamente registros de Santa Ana Xalmimilulco.",
        r"\item Se evalúan reglas explícitas de inclusión y exclusión.",
        r"\item Las exclusiones tienen prioridad sobre las señales de inclusión.",
        r"\item Se conserva como canónico el universo original producido previamente.",
        r"\item Se construye el foco textil estricto como alternativa analítica, no como reemplazo del canónico.",
        r"\item Se compara por ID DENUE con la capa MH ya filtrada y con el filtrado prioritario 2026.",
        r"\end{enumerate}",
        (
            "La comparación con MH mide coincidencia entre universos con criterios distintos. "
            "No se usa para convertir automáticamente todos los registros MH en señales de proceso húmedo, "
            "ni para interpretar algún conjunto como evidencia de descarga o contaminación."
        ),
        r"\section{Reglas trazables del foco estricto}",
        latex_table(rule_summary, ["rule_id", "rule_type", "registros_activados"]),
        write_rule_description(catalog),
        (
            r"La decisión de cada establecimiento puede auditarse en "
            r"\texttt{outputs/foco\_textil\_estricto\_santa\_ana\_2026/tablas/"
            r"trazabilidad\_filtro\_santa\_ana\_2026.csv}."
        ),
        (
            r"Las invariantes entre el filtro y la comparación se registran en "
            r"\texttt{outputs/foco\_textil\_estricto\_santa\_ana\_2026/tablas/"
            r"validacion\_trazabilidad.csv}."
        ),
        r"\section{Tamaños de los conjuntos}",
        latex_table(tables["resumen_tamanos"], ["conjunto", "registros"]),
        r"\section{Perfil de coincidencias}",
        latex_table(tables["perfil_comparacion"], ["perfil_comparacion", "registros"]),
        r"\section{Universo canónico original frente a MH filtrado}",
        latex_table(tables["canonico_vs_mh"], ["comparacion_canonico_vs_mh", "registros"]),
        r"\section{Universo canónico original frente al foco estricto alternativo}",
        latex_table(
            tables["canonico_vs_foco_estricto"],
            ["comparacion_canonico_vs_foco", "registros"],
        ),
        r"\section{Universo canónico original frente al filtrado 2026}",
        latex_table(
            tables["canonico_vs_filtrado_2026"],
            ["comparacion_canonico_vs_2026", "registros"],
        ),
        r"\section{Foco estricto alternativo frente al filtrado 2026}",
        latex_table(
            tables["foco_vs_filtrado_2026"],
            ["comparacion_estricto_vs_2026", "registros"],
        ),
        r"\section{Foco estricto alternativo frente a MH filtrado}",
        latex_table(tables["foco_vs_mh"], ["comparacion_estricto_vs_mh", "registros"]),
        r"\section{Mapas}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../outputs/foco_textil_estricto_santa_ana_2026/mapas/mapa_comparacion_directa_4_conjuntos.png}",
        r"\caption{Comparación directa entre los cuatro conjuntos.}",
        r"\end{figure}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../outputs/foco_textil_estricto_santa_ana_2026/mapas/mapa_canonico_original_vs_mh_filtrado.png}",
        r"\caption{Universo canónico original frente a MH filtrado.}",
        r"\end{figure}",
        r"\section{Conclusión operativa}",
        (
            "El universo original de 38 establecimientos permanece como canónico. MH aporta una capa ya filtrada "
            "de 49 puntos, de los cuales 43 tienen ID DENUE y seis no tienen ID. El foco estricto de 67 es una "
            "alternativa analítica para señales específicas de proceso textil y no sustituye al universo original."
        ),
    ]
    tex.write_text(
        latex_document(
            "Universo canónico original y comparaciones de Santa Ana 2026",
            body,
        ),
        encoding="utf-8",
    )
    return tex


def update_index(tables: dict[str, pd.DataFrame]) -> None:
    index = OUT_DIR / "index.md"
    text = index.read_text(encoding="utf-8") if index.exists() else ""
    marker = "## Comparación con universos de referencia"
    if marker in text:
        text = text.partition(marker)[0].rstrip()
    block = [
        "",
        marker,
        "",
        "El universo original de 38 establecimientos es el canónico. MH es su capa ya filtrada de referencia; el foco estricto de 67 es una alternativa analítica.",
        "",
        "- Mapa de cuatro conjuntos: `mapas/mapa_comparacion_directa_4_conjuntos.html`",
        "- Canónico original vs MH filtrado: `mapas/mapa_canonico_original_vs_mh_filtrado.html`",
        "- Canónico original vs foco estricto: `mapas/mapa_canonico_original_vs_foco_estricto.html`",
        "- Foco estricto vs filtrado 2026: `mapas/mapa_foco_estricto_vs_filtrado_2026.html`",
        "- Foco estricto vs MH: `mapas/mapa_foco_estricto_vs_mh_directo.html`",
        "- Documento: `../../docs/comparacion_foco_textil_estricto_santa_ana_2026.pdf`",
        "",
        "### Tamaños",
        "",
        markdown_table(tables["resumen_tamanos"]),
        "",
        "### Perfiles",
        "",
        markdown_table(tables["perfil_comparacion"]),
        "",
    ]
    index.write_text(text + "\n".join(block) + "\n", encoding="utf-8")


def save_maps(comp: gpd.GeoDataFrame) -> None:
    specifications = [
        (
            "perfil_comparacion",
            "mapa_comparacion_directa_4_conjuntos",
            "Santa Ana - comparación directa de cuatro conjuntos",
        ),
        (
            "comparacion_canonico_vs_mh",
            "mapa_canonico_original_vs_mh_filtrado",
            "Santa Ana - universo canonico original vs MH filtrado",
        ),
        (
            "comparacion_canonico_vs_foco",
            "mapa_canonico_original_vs_foco_estricto",
            "Santa Ana - universo canonico original vs foco estricto alternativo",
        ),
        (
            "comparacion_canonico_vs_2026",
            "mapa_canonico_original_vs_filtrado_2026",
            "Santa Ana - universo canonico original vs filtrado DENUE 2026",
        ),
        (
            "comparacion_estricto_vs_mh",
            "mapa_foco_estricto_vs_mh_directo",
            "Santa Ana - foco estricto alternativo vs MH filtrado",
        ),
        (
            "comparacion_estricto_vs_2026",
            "mapa_foco_estricto_vs_filtrado_2026",
            "Santa Ana - foco estricto alternativo vs filtrado DENUE 2026",
        ),
    ]
    for column, filename, title in specifications:
        save_static_map(
            comp,
            column,
            MAPS_DIR / f"{filename}.png",
            title,
            COLORS,
            LOCALIDADES,
            HIDROGRAFIA,
            excluded_values={"fuera_de_ambos"},
        )
        save_interactive_map(
            comp,
            column,
            MAPS_DIR / f"{filename}.html",
            title,
            COLORS,
            HOVER_FIELDS,
            excluded_values={"fuera_de_ambos"},
        )


def save_mh_compatibility_outputs(comp: gpd.GeoDataFrame) -> None:
    relevant = comp.loc[
        comp["en_foco_estricto"] | comp["en_mh_filtrado"]
    ].copy()
    relevant["comparacion_estricto_mh"] = relevant["comparacion_estricto_vs_mh"]
    export_geodata(
        relevant,
        LAYERS_DIR / "comparacion_estricto_vs_mh.gpkg",
        TABLES_DIR / "comparacion_estricto_vs_mh.csv",
        "comparacion_estricto_vs_mh",
    )
    save_static_map(
        relevant,
        "comparacion_estricto_mh",
        MAPS_DIR / "mapa_comparacion_estricto_vs_mh.png",
        "Santa Ana - foco estricto vs universo MH aceptado",
        COLORS,
        LOCALIDADES,
        HIDROGRAFIA,
    )
    save_interactive_map(
        relevant,
        "comparacion_estricto_mh",
        MAPS_DIR / "mapa_comparacion_estricto_vs_mh.html",
        "Santa Ana - foco estricto vs universo MH aceptado",
        COLORS,
        HOVER_FIELDS,
    )


def main() -> None:
    ensure_dirs()
    sets = load_sets()
    comparison = build_comparison(sets)
    tables = make_tables(comparison, sets)

    export_geodata(
        comparison,
        LAYERS_DIR / "comparacion_directa_4_conjuntos.gpkg",
        TABLES_DIR / "comparacion_directa_4_conjuntos.csv",
        "comparacion_directa_4_conjuntos",
    )
    for name, table in tables.items():
        table.to_csv(
            TABLES_DIR / f"comparacion_directa_{name}.csv",
            index=False,
            encoding="utf-8-sig",
        )
    save_maps(comparison)
    save_mh_compatibility_outputs(comparison)
    tex = write_docs(tables)
    compile_latex(tex)
    update_index(tables)

    print(f"[atoyac] Comparación trazable guardada en {relpath(OUT_DIR)}")
    print(tables["resumen_tamanos"].to_string(index=False))
    print(tables["perfil_comparacion"].to_string(index=False))


if __name__ == "__main__":
    main()
