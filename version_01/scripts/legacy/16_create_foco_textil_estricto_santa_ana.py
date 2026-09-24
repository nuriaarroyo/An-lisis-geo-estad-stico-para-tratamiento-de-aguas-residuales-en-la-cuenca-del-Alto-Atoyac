from __future__ import annotations

import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

from version_01.scripts.common import OUTPUTS_DIR, PROCESSED_DIR, ensure_output_dirs, normalize_text, relpath
from version_01.scripts.santa_ana_audit_utils import (
    compile_latex,
    ensure_directories,
    export_geodata,
    latex_document,
    latex_table,
    markdown_table,
    normalize_denue_id,
    read_vector,
    save_interactive_map,
    save_static_map,
)
from version_01.scripts.santa_ana_filter_rules import apply_filter_rules, rule_catalog


OUT_DIR = OUTPUTS_DIR / "foco_textil_estricto_santa_ana_2026"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"
LAYERS_DIR = OUT_DIR / "capas_qgis"
REPORT_DIR = OUT_DIR / "reporte"

CLASSIFIED_2026 = PROCESSED_DIR / "denue2026_universo_textil_clasificado.gpkg"
BROAD_FOCUS = (
    OUTPUTS_DIR
    / "foco_textil_produccion_y_lavado_2026"
    / "capas_qgis"
    / "santa_ana_foco_textil_produccion_y_lavado_2026.gpkg"
)
PRIORITY_2026 = OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg"
CURRENT_PRIORITY_SANTA = (
    OUTPUTS_DIR
    / "universo_prioritario_denue"
    / "santa_ana_xalmimilulco"
    / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg"
)
MH_FILTERED = PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp"
LOCALIDADES = PROCESSED_DIR / "localidades.gpkg"
HIDROGRAFIA = PROCESSED_DIR / "hidrografia.gpkg"

COLORS = {
    "tratamiento_lavado_acabado_textil": "#d73027",
    "mezclilla_jeans_deshebrado": "#4575b4",
    "produccion_material_textil": "#1a9850",
    "confeccion_maquila_generica": "#d95f02",
    "bordado_o_textil_ligero": "#e6ab02",
    "planchado_o_costura_especializada": "#a6761d",
    "servicio_insumo_bodega_no_proceso": "#666666",
    "pendiente_sin_senal_estricta": "#66a61e",
    "otro_fuera_foco_estricto": "#8da0cb",
}
HOVER_FIELDS = [
    "id",
    "nombre_de_la_unidad_economica",
    "categoria_foco_estricto",
    "decision_filtro_estricto",
    "reglas_inclusion_activadas",
    "reglas_exclusion_activadas",
    "motivo_decision_filtro",
    "senales_foco_estricto",
    "motivo_exclusion_foco_estricto",
    "codigo_de_la_clase_actividad_scian",
    "nombre_clase_actividad_scian",
    "etapa_productiva_sugerida",
    "decision_estudio_sugerida",
    "en_universo_prioritario_2026",
    "en_universo_prioritario_actual",
    "en_mh_filtrado",
    "_id_key",
]


def ensure_dirs() -> None:
    ensure_output_dirs()
    ensure_directories([OUT_DIR, MAPS_DIR, TABLES_DIR, LAYERS_DIR, REPORT_DIR])


def signal_summary(row: pd.Series) -> str:
    labels: list[str] = []
    for label, column in [
        ("lavado/deslavado", "flag_lavado_deslavado"),
        ("proceso humedo", "flag_proceso_humedo_relevante"),
        ("tenido/tintoreria", "flag_tenido_tintoreria"),
        ("acabado/tratamiento", "flag_acabado_tratamiento"),
        ("mezclilla/jeans", "flag_mezclilla_jeans"),
        ("maquila productiva", "flag_maquila_productiva"),
        ("cercania <=250m hidrografia", "flag_cercania_hidrografia_250m"),
    ]:
        if bool(row.get(column, False)):
            labels.append(label)
    labels.extend(
        part.strip()
        for part in str(row.get("reglas_inclusion_activadas", "")).split(";")
        if part.strip()
    )
    return "; ".join(dict.fromkeys(labels)) or "sin señal estricta"


def membership_ids(path: Path, id_column: str, locality_only: bool = False) -> set[str]:
    gdf = read_vector(path)
    if locality_only:
        gdf = gdf.loc[
            gdf["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")
        ].copy()
    return set(normalize_denue_id(gdf[id_column])) - {""}


def add_memberships(trace: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = trace.copy()
    priority_ids = membership_ids(PRIORITY_2026, "id", locality_only=True)
    current_ids = membership_ids(CURRENT_PRIORITY_SANTA, "id")
    mh_ids = membership_ids(MH_FILTERED, "ID DENUE")
    out["en_universo_prioritario_2026"] = out["_id_key"].isin(priority_ids)
    out["en_universo_prioritario_actual"] = out["_id_key"].isin(current_ids)
    out["en_mh_filtrado"] = out["_id_key"].isin(mh_ids)
    return out


def build_trace(classified: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    trace = apply_filter_rules(classified)
    trace["_id_key"] = normalize_denue_id(trace["id"])
    trace = add_memberships(trace)
    trace["senales_foco_estricto"] = trace.apply(signal_summary, axis=1)
    trace["nombre_universo"] = "foco_textil_estricto_santa_ana_2026"
    trace["nota_metodologica_foco"] = (
        "Filtro trazable para Santa Ana Xalmimilulco. Cada registro conserva reglas de inclusion, "
        "reglas de exclusion, decision y motivo. No implica evidencia de descarga ni contaminacion."
    )
    return trace


def exclusion_reason(row: pd.Series) -> str:
    name = normalize_text(row.get("nombre_de_la_unidad_economica", ""))
    stage = str(row.get("etapa_productiva_sugerida", ""))
    category = str(row.get("categoria_foco_textil", ""))
    decision = str(row.get("decision_estudio_sugerida", ""))
    activity = normalize_text(row.get("nombre_clase_actividad_scian", ""))

    if re.search(
        r"\b(?:planch\w*|alta\s+costura|costur\w*|modist\w*|sastrer\w*|"
        r"novia\w*|vestid\w*|sobre\s+medida)\b",
        name,
    ):
        return "planchado_o_costura_especializada"
    if (
        re.search(
            r"\b(?:agua\s+potable|sosapahue|lavadora\w*|autolavad\w*|engrasad\w*|"
            r"productos\s+para\s+lavander\w*|bodega\w*|desperdici\w*)\b",
            name,
        )
        or "captaci" in activity
        or "comercio al por mayor" in activity
    ):
        return "servicio_insumo_bodega_no_proceso"
    if stage == "bordado" or re.search(r"\b(?:bordad\w*|servillet\w*|recuerdo\w*)\b", name):
        return "bordado_o_textil_ligero"
    if stage == "revisar" or decision == "mantener_pendiente":
        return "pendiente_sin_senal_estricta"
    if category == "maquila_confeccion_textil" or stage == "confeccion_maquila":
        return "confeccion_maquila_generica"
    return "otro_fuera_foco_estricto"


def broad_exclusions(trace: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    strict_ids = set(trace.loc[trace["flag_foco_textil_estricto"], "_id_key"]) - {""}
    if BROAD_FOCUS.exists():
        source = read_vector(BROAD_FOCUS)
        source["_id_key"] = normalize_denue_id(source["id"])
        excluded = source.loc[~source["_id_key"].isin(strict_ids)].copy()
        trace_columns = [
            "_id_key",
            "reglas_inclusion_activadas",
            "reglas_exclusion_activadas",
            "decision_filtro_estricto",
            "motivo_decision_filtro",
        ]
        excluded = excluded.merge(
            trace[trace_columns].drop_duplicates("_id_key"),
            on="_id_key",
            how="left",
        )
        excluded = gpd.GeoDataFrame(excluded, geometry="geometry", crs=source.crs)
    else:
        excluded = trace.loc[~trace["flag_foco_textil_estricto"]].copy()
    excluded["motivo_exclusion_foco_estricto"] = excluded.apply(exclusion_reason, axis=1)
    excluded["nota_exclusion_foco_estricto"] = (
        "No muestra señal suficiente de tratamiento/lavado/acabado textil, "
        "mezclilla/jeans/deshebrado o producción de material textil."
    )
    return excluded


def rule_usage_table(trace: gpd.GeoDataFrame) -> pd.DataFrame:
    catalog = rule_catalog()
    catalog["registros_activados"] = catalog["rule_id"].map(
        lambda rule_id: int(trace[f"regla_{rule_id}"].sum())
    )
    return catalog


def count_tables(
    trace: gpd.GeoDataFrame,
    focus: gpd.GeoDataFrame,
    excluded: gpd.GeoDataFrame,
) -> dict[str, pd.DataFrame]:
    return {
        "catalogo_reglas_filtro": rule_usage_table(trace),
        "resumen_decision_filtro": trace.groupby("decision_filtro_estricto", dropna=False)
        .size()
        .reset_index(name="registros"),
        "resumen_categoria_foco_estricto": focus.groupby("categoria_foco_estricto", dropna=False)
        .size()
        .reset_index(name="registros"),
        "resumen_membresias": pd.DataFrame(
            [
                {"conjunto": "foco_textil_estricto_santa_ana_2026", "registros": len(focus)},
                {
                    "conjunto": "foco_en_universo_prioritario_2026",
                    "registros": int(focus["en_universo_prioritario_2026"].sum()),
                },
                {
                    "conjunto": "foco_en_universo_prioritario_actual",
                    "registros": int(focus["en_universo_prioritario_actual"].sum()),
                },
                {
                    "conjunto": "foco_en_mh_filtrado",
                    "registros": int(focus["en_mh_filtrado"].sum()),
                },
            ]
        ),
        "excluidos_del_foco_amplio": excluded.groupby(
            "motivo_exclusion_foco_estricto",
            dropna=False,
        )
        .size()
        .reset_index(name="registros")
        .sort_values("registros", ascending=False),
    }


def write_report(
    trace: gpd.GeoDataFrame,
    focus: gpd.GeoDataFrame,
    excluded: gpd.GeoDataFrame,
    tables: dict[str, pd.DataFrame],
) -> Path:
    tex = REPORT_DIR / "reporte_foco_textil_estricto_santa_ana_2026.tex"
    rules = tables["catalogo_reglas_filtro"][["rule_id", "rule_type", "registros_activados"]]
    body = [
        r"\section{Flujo reproducible}",
        (
            "La fuente es la capa DENUE 2026 clasificada. Primero se selecciona Santa Ana Xalmimilulco; "
            "después se evalúan nueve reglas explícitas; las exclusiones tienen prioridad; finalmente se "
            "construye un foco estricto alternativo y se compara, en un paso posterior, con el "
            "universo canónico original y con MH filtrado. "
            "Cada registro conserva las reglas activadas y el motivo de su decisión."
        ),
        r"\section{Reglas}",
        latex_table(rules, ["rule_id", "rule_type", "registros_activados"]),
        r"\section{Resultado del filtro}",
        (
            f"Se evaluaron {len(trace)} registros de Santa Ana. El foco estricto alternativo contiene {len(focus)} "
            f"registros y el diagnóstico frente al foco amplio contiene {len(excluded)} exclusiones. "
            "La selección expresa prioridad de estudio, no evidencia de descarga ni contaminación."
        ),
        latex_table(
            tables["resumen_categoria_foco_estricto"],
            ["categoria_foco_estricto", "registros"],
        ),
        r"\section{Trazabilidad disponible}",
        (
            r"La tabla \texttt{trazabilidad\_filtro\_santa\_ana\_2026.csv} contiene todos los registros "
            r"evaluados, incluidos y excluidos. Las columnas \texttt{reglas\_inclusion\_activadas}, "
            r"\texttt{reglas\_exclusion\_activadas}, \texttt{decision\_filtro\_estricto} y "
            r"\texttt{motivo\_decision\_filtro} permiten reconstruir cada decisión."
        ),
        r"\section{Mapa}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../mapas/mapa_foco_textil_estricto_santa_ana.png}",
        r"\caption{Foco textil estricto por categoría de señal.}",
        r"\end{figure}",
    ]
    tex.write_text(
        latex_document("Filtro trazable alternativo de Santa Ana 2026", body),
        encoding="utf-8",
    )
    return tex


def write_index(
    trace: gpd.GeoDataFrame,
    focus: gpd.GeoDataFrame,
    excluded: gpd.GeoDataFrame,
    tables: dict[str, pd.DataFrame],
) -> None:
    lines = [
        "# Foco textil estricto alternativo Santa Ana Xalmimilulco 2026",
        "",
        "## Flujo trazable",
        "",
        "Entrada operativa única: `python scripts/run_santa_ana_pipeline.py`.",
        "",
        "1. Fuente: `data/processed/denue2026_universo_textil_clasificado.gpkg`.",
        "2. Selección territorial exclusiva de Santa Ana Xalmimilulco.",
        "3. Evaluación de reglas documentadas en `tablas/catalogo_reglas_filtro.csv`.",
        "4. Prioridad de exclusiones explícitas sobre señales de inclusión.",
        "5. Construcción del foco estricto como alternativa analítica, no como universo canónico.",
        "6. Comparación posterior con el universo original canónico y con MH ya filtrado.",
        "",
        "Cada fila conserva qué reglas activó y el motivo final. El foco indica prioridad de estudio; no demuestra descarga ni contaminación.",
        "",
        "## Archivos principales",
        "",
        "- `capas_qgis/foco_textil_estricto_santa_ana_2026.gpkg`",
        "- `tablas/foco_textil_estricto_santa_ana_2026.csv`",
        "- `capas_qgis/trazabilidad_filtro_santa_ana_2026.gpkg`",
        "- `tablas/trazabilidad_filtro_santa_ana_2026.csv`",
        "- `tablas/catalogo_reglas_filtro.csv`",
        "- `tablas/validacion_trazabilidad.csv`",
        "- `mapas/mapa_foco_textil_estricto_santa_ana.html`",
        "- `reporte/reporte_foco_textil_estricto_santa_ana_2026.pdf`",
        "- `pipeline_manifest.json`",
        "- `../../docs/guia_filtro_trazable_santa_ana.md`",
        "",
        "## Conteos",
        "",
        f"- Registros evaluados en Santa Ana: {len(trace)}.",
        f"- Registros incluidos en el foco estricto: {len(focus)}.",
        f"- Excluidos al comparar con el foco amplio: {len(excluded)}.",
        "",
    ]
    for name, table in tables.items():
        lines.extend([f"### {name}", "", markdown_table(table), ""])
    (OUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def update_audit_index_link() -> None:
    audit_index = OUTPUTS_DIR / "auditoria_santa_ana_mh_filtrado" / "index.md"
    if not audit_index.exists():
        return
    text = audit_index.read_text(encoding="utf-8")
    marker = "## Foco textil estricto Santa Ana 2026"
    block = (
        f"\n\n{marker}\n\n"
        "El filtro estricto y su trazabilidad registro por registro están documentados en:\n\n"
        "- Reporte: `../foco_textil_estricto_santa_ana_2026/index.md`\n"
        "- Catálogo de reglas: `../foco_textil_estricto_santa_ana_2026/tablas/catalogo_reglas_filtro.csv`\n"
        "- Trazabilidad completa: `../foco_textil_estricto_santa_ana_2026/tablas/trazabilidad_filtro_santa_ana_2026.csv`\n"
        "- Comparación con MH aceptado: `../foco_textil_estricto_santa_ana_2026/mapas/mapa_foco_estricto_vs_mh_directo.html`\n"
    )
    if marker in text:
        text = text.partition(marker)[0].rstrip()
    audit_index.write_text(text + block + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    trace = build_trace(read_vector(CLASSIFIED_2026))
    focus = trace.loc[trace["flag_foco_textil_estricto"]].copy()
    excluded = broad_exclusions(trace)
    tables = count_tables(trace, focus, excluded)

    export_geodata(
        focus,
        LAYERS_DIR / "foco_textil_estricto_santa_ana_2026.gpkg",
        TABLES_DIR / "foco_textil_estricto_santa_ana_2026.csv",
        "foco_textil_estricto_santa_ana_2026",
    )
    export_geodata(
        trace,
        LAYERS_DIR / "trazabilidad_filtro_santa_ana_2026.gpkg",
        TABLES_DIR / "trazabilidad_filtro_santa_ana_2026.csv",
        "trazabilidad_filtro_santa_ana_2026",
    )
    export_geodata(
        excluded,
        LAYERS_DIR / "excluidos_del_foco_amplio_santa_ana.gpkg",
        TABLES_DIR / "excluidos_del_foco_amplio_santa_ana.csv",
        "excluidos_del_foco_amplio_santa_ana",
    )
    for name, table in tables.items():
        table.to_csv(TABLES_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(
        TABLES_DIR / "resumen_foco_textil_estricto_santa_ana_2026.xlsx",
        engine="openpyxl",
    ) as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name[:31], index=False)

    save_static_map(
        focus,
        "categoria_foco_estricto",
        MAPS_DIR / "mapa_foco_textil_estricto_santa_ana.png",
        "Santa Ana - foco textil estricto 2026",
        COLORS,
        LOCALIDADES,
        HIDROGRAFIA,
    )
    save_interactive_map(
        focus,
        "categoria_foco_estricto",
        MAPS_DIR / "mapa_foco_textil_estricto_santa_ana.html",
        "Santa Ana - foco textil estricto 2026",
        COLORS,
        HOVER_FIELDS,
    )
    save_static_map(
        excluded,
        "motivo_exclusion_foco_estricto",
        MAPS_DIR / "mapa_excluidos_del_foco_amplio.png",
        "Santa Ana - excluidos del foco amplio por filtro estricto",
        COLORS,
        LOCALIDADES,
        HIDROGRAFIA,
    )
    save_interactive_map(
        excluded,
        "motivo_exclusion_foco_estricto",
        MAPS_DIR / "mapa_excluidos_del_foco_amplio.html",
        "Santa Ana - excluidos del foco amplio por filtro estricto",
        COLORS,
        HOVER_FIELDS,
    )

    tex = write_report(trace, focus, excluded, tables)
    compile_latex(tex)
    write_index(trace, focus, excluded, tables)
    update_audit_index_link()
    print(
        f"[atoyac] Filtro trazable guardado en {relpath(OUT_DIR)}: "
        f"{len(trace)} evaluados, {len(focus)} incluidos."
    )


if __name__ == "__main__":
    main()
