from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

from common import OUTPUTS_DIR, PROCESSED_DIR, ensure_output_dirs, read_gpkg, relpath, safe_to_file


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
TARGET_CRS = "EPSG:6372"

COLORS = {
    "tratamiento_lavado_acabado_textil": "#d73027",
    "mezclilla_jeans_deshebrado": "#4575b4",
    "produccion_material_textil": "#1a9850",
    "estricto_y_mh": "#1b9e77",
    "solo_estricto": "#7570b3",
    "solo_mh": "#e7298a",
    "mh_sin_id": "#969696",
    "confeccion_maquila_generica": "#d95f02",
    "bordado_o_textil_ligero": "#e6ab02",
    "planchado_o_costura_especializada": "#a6761d",
    "servicio_insumo_bodega_no_proceso": "#666666",
    "pendiente_sin_senal_estricta": "#66a61e",
    "otro_fuera_foco_estricto": "#8da0cb",
}


def ensure_dirs() -> None:
    ensure_output_dirs()
    for path in [OUT_DIR, MAPS_DIR, TABLES_DIR, LAYERS_DIR, REPORT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_any(path: Path) -> gpd.GeoDataFrame:
    gdf = read_gpkg(path) if path.suffix.lower() == ".gpkg" else gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf.to_crs(TARGET_CRS)


def norm_id(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .replace({"nan": "", "None": "", "<NA>": ""})
    )


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    text = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def bool_col(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    return df[column].fillna(False).astype(bool)


def contains(series: pd.Series, pattern: str) -> pd.Series:
    return series.str.contains(pattern, regex=True, na=False)


def build_rule_masks(df: gpd.GeoDataFrame) -> dict[str, pd.Series]:
    name = df["nombre_de_la_unidad_economica"].map(normalize_text)
    activity = df["nombre_clase_actividad_scian"].map(normalize_text)
    stage = df["etapa_productiva_sugerida"].fillna("").astype(str)
    stage_text = stage.map(normalize_text)
    decision = df["decision_estudio_sugerida"].fillna("").astype(str)
    scian = (
        df["codigo_de_la_clase_actividad_scian"]
        .fillna("")
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
        .fillna("")
    )
    relevant_text = name + " " + activity + " " + stage_text

    exclude_name = contains(
        name,
        r"\b(?:"
        r"planch\w*|alta\s+costura|costur\w*|modist\w*|sastrer\w*|sastre\w*|novia\w*|xv|"
        r"vestid\w*|sobre\s+medida|lavadora\w*|autolavad\w*|engrasad\w*|agua\s+potable|"
        r"sosapahue|zapat\w*|calzad\w*|bols\w*|malet\w*|computador\w*|publicidad|"
        r"productos\s+para\s+lavander\w*|bodega\w*|desperdici\w*|servillet\w*|recuerdo\w*|piel"
        r")\b",
    )
    exclude_activity = contains(
        activity,
        r"captaci\w* tratamiento y suministro de agua|calzado|bolsos|maletas|computadoras|comercio al por mayor",
    )
    exclude_decision = decision.isin(
        ["excluir_por_comercio", "excluir_por_renta", "excluir_del_universo_prioritario"]
    )
    explicit_exclusion = exclude_name | exclude_activity | exclude_decision

    wet_terms = contains(
        relevant_text,
        r"\b(?:"
        r"lavander\w*|lavado\w*|deslav\w*|stone\s*wash|stone\s*lav|tintorer\w*|"
        r"tenid\w*|acab\w*|poliproces\w*"
        r")\b",
    )
    wet_flags = (
        bool_col(df, "flag_proceso_humedo_relevante")
        | bool_col(df, "flag_lavado_deslavado")
        | bool_col(df, "flag_tenido_tintoreria")
        | bool_col(df, "flag_acabado_tratamiento")
        | stage.isin(["lavado_deslavado", "lavanderia_industrial", "tenido_tintoreria", "acabado_textil"])
        | scian.isin(["812210", "313310"])
    )
    denim_name = contains(name, r"\b(?:mezclill\w*|mesclill\w*|jean\w*|denim|deshebr\w*|desebr\w*|fosil)\b")
    material_textile = (
        scian.str.startswith("313")
        & contains(relevant_text, r"\b(?:textil\w*|tela\w*|tejid\w*|hilad\w*|hilatur\w*|pasamaner\w*)\b")
        & ~contains(name, r"\b(?:servillet\w*|recuerdo\w*|piel)\b")
    )

    wet_include = (wet_flags | wet_terms) & ~explicit_exclusion
    denim_include = (denim_name | stage.eq("fabricacion_mezclilla")) & ~explicit_exclusion
    material_include = material_textile & ~explicit_exclusion

    return {
        "name": name,
        "activity": activity,
        "stage": stage,
        "decision": decision,
        "scian": scian,
        "explicit_exclusion": explicit_exclusion,
        "wet_include": wet_include,
        "denim_include": denim_include,
        "material_include": material_include,
        "strict_include": wet_include | denim_include | material_include,
        "exclude_name": exclude_name,
        "exclude_activity": exclude_activity,
        "exclude_decision": exclude_decision,
    }


def signal_summary(row: pd.Series) -> str:
    signals: list[str] = []
    for label, column in [
        ("lavado/deslavado", "flag_lavado_deslavado"),
        ("lavanderia o proceso humedo", "flag_proceso_humedo_relevante"),
        ("tenido/tintoreria", "flag_tenido_tintoreria"),
        ("acabado/tratamiento", "flag_acabado_tratamiento"),
        ("mezclilla/jeans", "flag_mezclilla_jeans"),
        ("maquila productiva", "flag_maquila_productiva"),
        ("cercania <=250m hidrografia", "flag_cercania_hidrografia_250m"),
    ]:
        if bool(row.get(column, False)):
            signals.append(label)
    if bool(row.get("flag_foco_estricto_tratamiento", False)):
        signals.append("criterio estricto: tratamiento/lavado/acabado")
    if bool(row.get("flag_foco_estricto_mezclilla", False)):
        signals.append("criterio estricto: mezclilla/jeans/deshebrado")
    if bool(row.get("flag_foco_estricto_material_textil", False)):
        signals.append("criterio estricto: produccion material textil")
    return "; ".join(dict.fromkeys(signals)) if signals else "senal estricta por nombre/etapa"


def build_strict_focus(classified: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    santa = classified[classified["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")].copy()
    santa["_id_key"] = norm_id(santa["id"])
    masks = build_rule_masks(santa)

    foco = santa.loc[masks["strict_include"]].copy()
    foco["flag_foco_estricto_tratamiento"] = masks["wet_include"].loc[foco.index].astype(bool)
    foco["flag_foco_estricto_mezclilla"] = masks["denim_include"].loc[foco.index].astype(bool)
    foco["flag_foco_estricto_material_textil"] = masks["material_include"].loc[foco.index].astype(bool)

    foco["categoria_foco_estricto"] = "produccion_material_textil"
    foco.loc[foco["flag_foco_estricto_mezclilla"], "categoria_foco_estricto"] = "mezclilla_jeans_deshebrado"
    foco.loc[foco["flag_foco_estricto_tratamiento"], "categoria_foco_estricto"] = (
        "tratamiento_lavado_acabado_textil"
    )
    foco["senales_foco_estricto"] = foco.apply(signal_summary, axis=1)
    foco["nombre_universo"] = "foco_textil_estricto_santa_ana_2026"
    foco["nota_metodologica_foco"] = (
        "Filtro estricto solo para Santa Ana Xalmimilulco. Incluye tratamiento/lavado/acabado textil, "
        "mezclilla/jeans/deshebrado y produccion material textil. Excluye planchado, confeccion/alta costura, "
        "ropa terminada generica, talleres sin senal textil especifica, lavados no textiles, insumos y bodegas. "
        "No implica evidencia de descarga ni contaminacion."
    )
    return foco


def add_memberships(foco: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = foco.copy()
    priority_2026 = read_any(PRIORITY_2026)
    current = read_any(CURRENT_PRIORITY_SANTA)
    mh = read_any(MH_FILTERED)

    priority_2026 = priority_2026[priority_2026["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")].copy()
    priority_2026["_id_key"] = norm_id(priority_2026["id"])
    current["_id_key"] = norm_id(current["id"])
    mh["_id_key"] = norm_id(mh["ID DENUE"])

    priority_ids = set(priority_2026["_id_key"]) - {""}
    current_ids = set(current["_id_key"]) - {""}
    mh_ids = set(mh["_id_key"]) - {""}

    out["en_universo_prioritario_2026"] = out["_id_key"].isin(priority_ids)
    out["en_universo_prioritario_actual"] = out["_id_key"].isin(current_ids)
    out["en_mh_filtrado"] = out["_id_key"].isin(mh_ids)
    return out


def exclusion_reason(row: pd.Series) -> str:
    name = normalize_text(row.get("nombre_de_la_unidad_economica", ""))
    stage = str(row.get("etapa_productiva_sugerida", ""))
    category = str(row.get("categoria_foco_textil", ""))
    decision = str(row.get("decision_estudio_sugerida", ""))
    activity = normalize_text(row.get("nombre_clase_actividad_scian", ""))

    if re.search(r"\b(?:planch\w*|alta\s+costura|costur\w*|modist\w*|sastrer\w*|novia\w*|vestid\w*|sobre\s+medida)\b", name):
        return "planchado_o_costura_especializada"
    if re.search(
        r"\b(?:agua\s+potable|sosapahue|lavadora\w*|autolavad\w*|engrasad\w*|productos\s+para\s+lavander\w*|bodega\w*|desperdici\w*)\b",
        name,
    ) or "captaci" in activity or "comercio al por mayor" in activity:
        return "servicio_insumo_bodega_no_proceso"
    if stage == "bordado" or re.search(r"\b(?:bordad\w*|servillet\w*|recuerdo\w*)\b", name):
        return "bordado_o_textil_ligero"
    if stage == "revisar" or decision == "mantener_pendiente":
        return "pendiente_sin_senal_estricta"
    if category == "maquila_confeccion_textil" or stage == "confeccion_maquila":
        return "confeccion_maquila_generica"
    return "otro_fuera_foco_estricto"


def broad_exclusions(foco: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    broad = read_any(BROAD_FOCUS)
    broad["_id_key"] = norm_id(broad["id"])
    focus_ids = set(foco["_id_key"]) - {""}
    excluded = broad.loc[~broad["_id_key"].isin(focus_ids)].copy()
    excluded["motivo_exclusion_foco_estricto"] = excluded.apply(exclusion_reason, axis=1)
    excluded["nota_exclusion_foco_estricto"] = (
        "Sale del foco estricto porque no muestra senal suficiente de tratamiento/lavado/acabado textil, "
        "mezclilla/jeans/deshebrado o produccion material textil."
    )
    return excluded


def mh_vs_focus(foco: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    mh = read_any(MH_FILTERED)
    mh["_id_key"] = norm_id(mh["ID DENUE"])
    focus_ids = set(foco["_id_key"]) - {""}
    mh_ids = set(mh["_id_key"]) - {""}

    focus_keep = foco[
        [
            "_id_key",
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "nombre_clase_actividad_scian",
            "categoria_foco_estricto",
            "senales_foco_estricto",
            "en_universo_prioritario_2026",
            "en_universo_prioritario_actual",
            "en_mh_filtrado",
            "geometry",
        ]
    ].copy()
    focus_keep["comparacion_estricto_mh"] = focus_keep["_id_key"].map(
        lambda value: "estricto_y_mh" if value in mh_ids else "solo_estricto"
    )
    focus_keep["fuente_comparacion"] = "foco_estricto"
    focus_keep["nombre_mapa"] = focus_keep["nombre_de_la_unidad_economica"]

    mh_only = mh.loc[~mh["_id_key"].isin(focus_ids)].copy()
    mh_only["comparacion_estricto_mh"] = mh_only["_id_key"].map(lambda value: "mh_sin_id" if not value else "solo_mh")
    mh_only["fuente_comparacion"] = "mh_filtrado"
    mh_only["id"] = mh_only["_id_key"]
    mh_only["nombre_mapa"] = "MH - " + mh_only["Name"].fillna("").astype(str)
    mh_only["categoria_foco_estricto"] = ""
    mh_only["senales_foco_estricto"] = "fuera del foco estricto o sin ID DENUE"

    keep = [
        "_id_key",
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "nombre_clase_actividad_scian",
        "categoria_foco_estricto",
        "senales_foco_estricto",
        "en_universo_prioritario_2026",
        "en_universo_prioritario_actual",
        "en_mh_filtrado",
        "comparacion_estricto_mh",
        "fuente_comparacion",
        "nombre_mapa",
        "Name",
        "DENUE",
        "ID DENUE",
        "geometry",
    ]
    combined = pd.concat(
        [focus_keep[[c for c in keep if c in focus_keep.columns]], mh_only[[c for c in keep if c in mh_only.columns]]],
        ignore_index=True,
    )
    return gpd.GeoDataFrame(combined, geometry="geometry", crs=foco.crs)


def base_layers(crs: str):
    localidades = read_any(LOCALIDADES) if LOCALIDADES.exists() else None
    hydro = read_any(HIDROGRAFIA) if HIDROGRAFIA.exists() else None
    if localidades is not None and not localidades.empty:
        localidades = localidades.to_crs(crs)
    if hydro is not None and not hydro.empty:
        hydro = hydro.to_crs(crs)
        hydro = hydro[hydro.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()
    return localidades, hydro


def static_map(gdf: gpd.GeoDataFrame, color_col: str, path: Path, title: str) -> None:
    if gdf.empty:
        return
    localidades, hydro = base_layers(gdf.crs)
    fig, ax = plt.subplots(figsize=(10.5, 8), dpi=180)
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#737373", linewidth=0.5)
    if hydro is not None and not hydro.empty:
        minx, miny, maxx, maxy = gdf.total_bounds
        window = hydro.cx[minx - 1000 : maxx + 1000, miny - 1000 : maxy + 1000]
        if not window.empty:
            window.plot(ax=ax, color="#67a9cf", linewidth=0.7, alpha=0.75)
    for value, subset in gdf.groupby(color_col, dropna=False):
        label = str(value) if str(value) else "sin_valor"
        subset.plot(
            ax=ax,
            markersize=42,
            color=COLORS.get(label, "#525252"),
            edgecolor="white",
            linewidth=0.45,
            label=label,
            alpha=0.9,
        )
    ax.set_title(title, fontsize=12)
    ax.set_axis_off()
    ax.legend(loc="best", fontsize=8, frameon=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def interactive_map(gdf: gpd.GeoDataFrame, color_col: str, path: Path, title: str) -> None:
    if gdf.empty:
        return
    plot = gdf.to_crs("EPSG:4326").copy()
    plot["lon"] = plot.geometry.x
    plot["lat"] = plot.geometry.y
    hover_cols = [
        c
        for c in [
            "id",
            "nombre_mapa",
            "nombre_de_la_unidad_economica",
            "Name",
            "categoria_foco_estricto",
            "categoria_foco_textil",
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
        if c in plot.columns
    ]
    fig = px.scatter_map(
        plot,
        lat="lat",
        lon="lon",
        color=color_col,
        color_discrete_map=COLORS,
        hover_data=hover_cols,
        zoom=12,
        height=760,
        title=title,
    )
    fig.update_traces(marker={"size": 10, "opacity": 0.85})
    fig.update_layout(map_style="open-street-map", margin={"r": 10, "t": 55, "l": 10, "b": 10})
    fig.write_html(path, include_plotlyjs="cdn")


def count_tables(foco: gpd.GeoDataFrame, excluded: gpd.GeoDataFrame, mh_comp: gpd.GeoDataFrame) -> dict[str, pd.DataFrame]:
    return {
        "resumen_categoria_foco_estricto": foco.groupby("categoria_foco_estricto", dropna=False)
        .size()
        .reset_index(name="registros"),
        "resumen_membresias": pd.DataFrame(
            [
                {"conjunto": "foco_textil_estricto_santa_ana_2026", "registros": len(foco)},
                {"conjunto": "en_universo_prioritario_2026_santa_ana", "registros": int(foco["en_universo_prioritario_2026"].sum())},
                {"conjunto": "en_universo_prioritario_actual_santa_ana", "registros": int(foco["en_universo_prioritario_actual"].sum())},
                {"conjunto": "en_mh_filtrado", "registros": int(foco["en_mh_filtrado"].sum())},
            ]
        ),
        "comparacion_estricto_vs_mh": mh_comp.groupby("comparacion_estricto_mh", dropna=False)
        .size()
        .reset_index(name="registros"),
        "excluidos_del_foco_amplio": excluded.groupby("motivo_exclusion_foco_estricto", dropna=False)
        .size()
        .reset_index(name="registros")
        .sort_values("registros", ascending=False),
        "resumen_decision": foco.groupby(["categoria_foco_estricto", "decision_estudio_sugerida"], dropna=False)
        .size()
        .reset_index(name="registros"),
    }


def latex_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def latex_table(df: pd.DataFrame, columns: list[str]) -> str:
    lines = [r"\begin{tabular}{" + "l" * len(columns) + "}", r"\toprule"]
    lines.append(" & ".join(latex_escape(c) for c in columns) + r" \\")
    lines.append(r"\midrule")
    for _, row in df[columns].iterrows():
        lines.append(" & ".join(latex_escape(row[c]) for c in columns) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines)


def write_report(tables: dict[str, pd.DataFrame], foco: gpd.GeoDataFrame, excluded: gpd.GeoDataFrame) -> None:
    tex = REPORT_DIR / "reporte_foco_textil_estricto_santa_ana_2026.tex"
    cat = tables["resumen_categoria_foco_estricto"]
    mem = tables["resumen_membresias"]
    mh = tables["comparacion_estricto_vs_mh"]
    exc = tables["excluidos_del_foco_amplio"]

    lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=2cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\usepackage{hyperref}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\title{Foco textil estricto Santa Ana Xalmimilulco 2026}",
        r"\author{Proyecto Atoyac - salida reproducible}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
        r"\section{Proposito}",
        (
            "Este reporte corrige el universo foco amplio para Santa Ana Xalmimilulco. "
            "El producto nuevo se llama "
            r"\texttt{foco\_textil\_estricto\_santa\_ana\_2026} "
            "y se limita a establecimientos con senales de tratamiento, lavado, tintoreria, acabado, "
            "mezclilla, jeans, deshebrado o produccion material textil. No es una prueba de descarga ni contaminacion."
        ),
        r"\section{Criterio estricto}",
        (
            "Se partio de "
            r"\texttt{data/processed/denue2026\_universo\_textil\_clasificado.gpkg} "
            "y se filtro exclusivamente la localidad Santa Ana Xalmimilulco. "
            "Se excluyeron planchado, confeccion o alta costura, ropa terminada generica, talleres sin senal especifica, "
            "lavados no textiles, insumos para lavanderia, bodegas, servicios de agua y actividades no textiles. "
            "La senal de mezclilla/deshebrado se exigio en el nombre del establecimiento o en la etapa productiva ya clasificada."
        ),
        r"\section{Resultados}",
        f"El foco estricto contiene {len(foco)} registros. Del foco amplio de Santa Ana salen {len(excluded)} registros.",
        r"\subsection{Categorias incluidas}",
        latex_table(cat, ["categoria_foco_estricto", "registros"]),
        r"\subsection{Membresias}",
        latex_table(mem, ["conjunto", "registros"]),
        r"\subsection{Comparacion con MH filtrado}",
        latex_table(mh, ["comparacion_estricto_mh", "registros"]),
        r"\subsection{Registros excluidos del foco amplio}",
        latex_table(exc, ["motivo_exclusion_foco_estricto", "registros"]),
        r"\section{Mapas}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../mapas/mapa_foco_textil_estricto_santa_ana.png}",
        r"\caption{Foco textil estricto Santa Ana 2026 por categoria.}",
        r"\end{figure}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../mapas/mapa_comparacion_estricto_vs_mh.png}",
        r"\caption{Comparacion entre foco estricto y capa MH filtrada.}",
        r"\end{figure}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../mapas/mapa_excluidos_del_foco_amplio.png}",
        r"\caption{Registros que salieron del foco amplio al aplicar el criterio estricto.}",
        r"\end{figure}",
        r"\section{Lectura}",
        (
            "La diferencia principal frente al foco amplio es que se retira la maquila/confeccion generica. "
            "Esto reduce ruido para una auditoria ambiental porque muchos talleres de ropa terminada no muestran, "
            "por si solos, senal de lavado, acabado, tratamiento, mezclilla o produccion material textil. "
            "La capa MH filtrada conserva una nocion mas amplia: solo una parte cruza con este foco estricto."
        ),
        r"\section{Archivos generados}",
        r"\begin{itemize}",
        r"\item \texttt{capas\_qgis/foco\_textil\_estricto\_santa\_ana\_2026.gpkg}",
        r"\item \texttt{tablas/foco\_textil\_estricto\_santa\_ana\_2026.csv}",
        r"\item \texttt{tablas/excluidos\_del\_foco\_amplio\_santa\_ana.csv}",
        r"\item \texttt{mapas/mapa\_foco\_textil\_estricto\_santa\_ana.html}",
        r"\item \texttt{mapas/mapa\_comparacion\_estricto\_vs\_mh.html}",
        r"\item \texttt{mapas/mapa\_excluidos\_del\_foco\_amplio.html}",
        r"\end{itemize}",
        r"\end{document}",
    ]
    tex.write_text("\n\n".join(lines), encoding="utf-8")


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin registros._"
    clean = df.astype(str).replace({"nan": "", "None": ""})
    headers = list(clean.columns)
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in clean.iterrows():
        rows.append("| " + " | ".join(str(row[col]).replace("|", "/") for col in headers) + " |")
    return "\n".join(rows)


def write_index(tables: dict[str, pd.DataFrame], foco: gpd.GeoDataFrame, excluded: gpd.GeoDataFrame) -> None:
    lines = [
        "# Foco textil estricto Santa Ana Xalmimilulco 2026",
        "",
        "Producto corregido para Santa Ana. Reemplaza el foco amplio cuando el objetivo es auditar procesos con mayor relevancia para agua: tratamiento, lavado, tintoreria, acabado, mezclilla/jeans/deshebrado o produccion material textil.",
        "",
        "No incluye planchado, confeccion/alta costura, ropa terminada generica, talleres sin senal textil especifica, lavados no textiles, insumos para lavanderia, bodegas ni servicios de agua.",
        "",
        "No implica evidencia de descarga ni contaminacion; es una capa de priorizacion y auditoria.",
        "",
        "## Archivos principales",
        "",
        "- `capas_qgis/foco_textil_estricto_santa_ana_2026.gpkg`",
        "- `tablas/foco_textil_estricto_santa_ana_2026.csv`",
        "- `capas_qgis/comparacion_estricto_vs_mh.gpkg`",
        "- `tablas/comparacion_estricto_vs_mh.csv`",
        "- `capas_qgis/excluidos_del_foco_amplio_santa_ana.gpkg`",
        "- `tablas/excluidos_del_foco_amplio_santa_ana.csv`",
        "- `mapas/mapa_foco_textil_estricto_santa_ana.html`",
        "- `mapas/mapa_comparacion_estricto_vs_mh.html`",
        "- `mapas/mapa_excluidos_del_foco_amplio.html`",
        "- `reporte/reporte_foco_textil_estricto_santa_ana_2026.tex`",
        "- `reporte/reporte_foco_textil_estricto_santa_ana_2026.pdf` si el compilador LaTeX esta disponible",
        "",
        "## Lectura rapida",
        "",
        f"- Foco estricto Santa Ana: {len(foco)} registros.",
        f"- Registros del foco amplio que salen por criterio estricto: {len(excluded)}.",
        f"- Cruces con MH filtrado: {int(foco['en_mh_filtrado'].sum())} registros del foco estricto.",
        f"- Cruces con universo prioritario 2026 de Santa Ana: {int(foco['en_universo_prioritario_2026'].sum())} registros.",
        "",
        "## Conteos",
        "",
    ]
    for name, df in tables.items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(markdown_table(df))
        lines.append("")
    (OUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def compile_report() -> None:
    tex = REPORT_DIR / "reporte_foco_textil_estricto_santa_ana_2026.tex"
    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex.name],
            cwd=REPORT_DIR,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass


def update_audit_index_link() -> None:
    audit_index = OUTPUTS_DIR / "auditoria_santa_ana_mh_filtrado" / "index.md"
    if not audit_index.exists():
        return
    text = audit_index.read_text(encoding="utf-8")
    marker = "## Foco textil estricto Santa Ana 2026"
    block = (
        "\n\n"
        f"{marker}\n\n"
        "Se genero un producto separado para retirar el ruido del foco amplio: planchado, confeccion/alta costura, "
        "ropa terminada generica, talleres sin senal especifica, lavados no textiles, insumos, bodegas y servicios de agua.\n\n"
        "- Reporte: `../foco_textil_estricto_santa_ana_2026/index.md`\n"
        "- Mapa interactivo principal: `../foco_textil_estricto_santa_ana_2026/mapas/mapa_foco_textil_estricto_santa_ana.html`\n"
        "- Comparacion con MH: `../foco_textil_estricto_santa_ana_2026/mapas/mapa_comparacion_estricto_vs_mh.html`\n"
        "- Excluidos del foco amplio: `../foco_textil_estricto_santa_ana_2026/mapas/mapa_excluidos_del_foco_amplio.html`\n"
    )
    if marker not in text:
        audit_index.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    classified = read_any(CLASSIFIED_2026)
    foco = add_memberships(build_strict_focus(classified))
    excluded = broad_exclusions(foco)
    mh_comp = mh_vs_focus(foco)
    tables = count_tables(foco, excluded, mh_comp)

    safe_to_file(foco, LAYERS_DIR / "foco_textil_estricto_santa_ana_2026.gpkg", layer="foco_textil_estricto_santa_ana_2026")
    foco.drop(columns="geometry", errors="ignore").to_csv(
        TABLES_DIR / "foco_textil_estricto_santa_ana_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )
    safe_to_file(excluded, LAYERS_DIR / "excluidos_del_foco_amplio_santa_ana.gpkg", layer="excluidos_del_foco_amplio_santa_ana")
    excluded.drop(columns="geometry", errors="ignore").to_csv(
        TABLES_DIR / "excluidos_del_foco_amplio_santa_ana.csv",
        index=False,
        encoding="utf-8-sig",
    )
    safe_to_file(mh_comp, LAYERS_DIR / "comparacion_estricto_vs_mh.gpkg", layer="comparacion_estricto_vs_mh")
    mh_comp.drop(columns="geometry", errors="ignore").to_csv(
        TABLES_DIR / "comparacion_estricto_vs_mh.csv",
        index=False,
        encoding="utf-8-sig",
    )

    for name, table in tables.items():
        table.to_csv(TABLES_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(TABLES_DIR / "resumen_foco_textil_estricto_santa_ana_2026.xlsx", engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name[:31], index=False)

    static_map(
        foco,
        "categoria_foco_estricto",
        MAPS_DIR / "mapa_foco_textil_estricto_santa_ana.png",
        "Santa Ana - foco textil estricto 2026",
    )
    interactive_map(
        foco,
        "categoria_foco_estricto",
        MAPS_DIR / "mapa_foco_textil_estricto_santa_ana.html",
        "Santa Ana - foco textil estricto 2026",
    )
    static_map(
        mh_comp,
        "comparacion_estricto_mh",
        MAPS_DIR / "mapa_comparacion_estricto_vs_mh.png",
        "Santa Ana - foco estricto vs MH filtrado",
    )
    interactive_map(
        mh_comp,
        "comparacion_estricto_mh",
        MAPS_DIR / "mapa_comparacion_estricto_vs_mh.html",
        "Santa Ana - foco estricto vs MH filtrado",
    )
    static_map(
        excluded,
        "motivo_exclusion_foco_estricto",
        MAPS_DIR / "mapa_excluidos_del_foco_amplio.png",
        "Santa Ana - excluidos del foco amplio por filtro estricto",
    )
    interactive_map(
        excluded,
        "motivo_exclusion_foco_estricto",
        MAPS_DIR / "mapa_excluidos_del_foco_amplio.html",
        "Santa Ana - excluidos del foco amplio por filtro estricto",
    )

    write_report(tables, foco, excluded)
    compile_report()
    write_index(tables, foco, excluded)
    update_audit_index_link()
    print(f"[atoyac] Foco estricto Santa Ana guardado en {relpath(OUT_DIR)} con {len(foco)} registros")


if __name__ == "__main__":
    main()
