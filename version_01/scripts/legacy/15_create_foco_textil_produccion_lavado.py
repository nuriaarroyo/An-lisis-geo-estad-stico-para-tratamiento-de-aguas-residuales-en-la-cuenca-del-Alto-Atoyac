from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

from version_01.scripts.common import OUTPUTS_DIR, PROCESSED_DIR, ensure_output_dirs, read_gpkg, relpath, safe_to_file


OUT_DIR = OUTPUTS_DIR / "foco_textil_produccion_y_lavado_2026"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"
LAYERS_DIR = OUT_DIR / "capas_qgis"
REPORT_DIR = OUT_DIR / "reporte"

CLASSIFIED_2026 = PROCESSED_DIR / "denue2026_universo_textil_clasificado.gpkg"
PRIORITY_2026 = OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg"
CURRENT_PRIORITY = OUTPUTS_DIR / "universo_prioritario_denue" / "universo_prioritario_denue.gpkg"
MH_FILTERED = PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp"
MAYRA = PROCESSED_DIR / "capa_mayra" / "capa mayra.shp"
LOCALIDADES = PROCESSED_DIR / "localidades.gpkg"
HIDROGRAFIA = PROCESSED_DIR / "hidrografia.gpkg"

EXCLUDE_DECISIONS = {
    "excluir_por_comercio",
    "excluir_por_renta",
    "excluir_del_universo_prioritario",
}

COLORS = {
    "lavado_acabado_proceso_humedo": "#d73027",
    "mezclilla_produccion": "#4575b4",
    "maquila_confeccion_textil": "#1a9850",
    "textil_pendiente_revision": "#fdae61",
    "otro_contexto_textil": "#7570b3",
    "foco_y_mh": "#1b9e77",
    "solo_foco": "#7570b3",
    "solo_mh": "#e7298a",
    "mh_sin_id": "#969696",
}


def ensure_dirs() -> None:
    ensure_output_dirs()
    for path in [OUT_DIR, MAPS_DIR, TABLES_DIR, LAYERS_DIR, REPORT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_any(path: Path) -> gpd.GeoDataFrame:
    gdf = read_gpkg(path) if path.suffix.lower() == ".gpkg" else gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf.to_crs("EPSG:6372")


def norm_id(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .replace({"nan": "", "None": "", "<NA>": ""})
    )


def bool_col(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    return df[column].fillna(False).astype(bool)


def build_focus_universe(classified: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = classified.copy()
    out["_id_key"] = norm_id(out["id"])

    decision = out["decision_estudio_sugerida"].fillna("").astype(str)
    stage = out["etapa_productiva_sugerida"].fillna("").astype(str)
    scian = out["codigo_de_la_clase_actividad_scian"].fillna("").astype(str).str.extract(r"(\d+)", expand=False).fillna("")

    wet = (
        bool_col(out, "flag_proceso_humedo_relevante")
        | bool_col(out, "flag_lavado_deslavado")
        | bool_col(out, "flag_tenido_tintoreria")
        | bool_col(out, "flag_acabado_tratamiento")
        | stage.isin(["lavado_deslavado", "lavanderia_industrial", "tenido_tintoreria", "acabado_textil"])
        | scian.isin(["812210", "313310"])
    )
    denim = bool_col(out, "flag_mezclilla_jeans") | stage.eq("fabricacion_mezclilla")
    production = (
        bool_col(out, "flag_maquila_productiva")
        | stage.isin(["confeccion_maquila", "fabricacion_textil", "bordado"])
        | scian.str.startswith(("313", "314", "315"))
    )
    pending = decision.eq("mantener_pendiente") | stage.eq("revisar")
    depurado = ~decision.isin(EXCLUDE_DECISIONS)
    include = depurado & (wet | denim | production | pending)

    foco = out.loc[include].copy()
    foco["flag_foco_lavado_acabado_humedo"] = wet.loc[foco.index].astype(bool)
    foco["flag_foco_mezclilla_produccion"] = denim.loc[foco.index].astype(bool)
    foco["flag_foco_maquila_confeccion"] = production.loc[foco.index].astype(bool)
    foco["flag_foco_pendiente_revision"] = pending.loc[foco.index].astype(bool)

    def class_row(row: pd.Series) -> str:
        if bool(row["flag_foco_lavado_acabado_humedo"]):
            return "lavado_acabado_proceso_humedo"
        if bool(row["flag_foco_mezclilla_produccion"]):
            return "mezclilla_produccion"
        if bool(row["flag_foco_maquila_confeccion"]):
            return "maquila_confeccion_textil"
        if bool(row["flag_foco_pendiente_revision"]):
            return "textil_pendiente_revision"
        return "otro_contexto_textil"

    foco["categoria_foco_textil"] = foco.apply(class_row, axis=1)
    foco["senales_foco_textil"] = foco.apply(signal_summary, axis=1)
    foco["nombre_universo"] = "foco_textil_produccion_y_lavado_2026"
    foco["nota_metodologica_foco"] = (
        "Universo operativo amplio para ubicar produccion, maquila, mezclilla, lavado, "
        "lavanderia, tintoreria, acabado o pendientes textiles. No implica evidencia de descarga ni contaminacion."
    )
    return foco


def signal_summary(row: pd.Series) -> str:
    signals = []
    for label, column in [
        ("lavado/deslavado", "flag_lavado_deslavado"),
        ("lavanderia o proceso humedo", "flag_proceso_humedo_relevante"),
        ("tenido/tintoreria", "flag_tenido_tintoreria"),
        ("acabado/tratamiento", "flag_acabado_tratamiento"),
        ("mezclilla/jeans", "flag_mezclilla_jeans"),
        ("maquila/confeccion", "flag_maquila_productiva"),
        ("cercania <=250m hidrografia", "flag_cercania_hidrografia_250m"),
    ]:
        if bool(row.get(column, False)):
            signals.append(label)
    if not signals and bool(row.get("flag_foco_maquila_confeccion", False)):
        signals.append("produccion/confeccion textil")
    if not signals and bool(row.get("flag_foco_pendiente_revision", False)):
        signals.append("pendiente de revision textil")
    return "; ".join(signals) if signals else "contexto textil sin senal especifica"


def add_memberships(foco: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = foco.copy()
    priority_2026 = read_any(PRIORITY_2026) if PRIORITY_2026.exists() else gpd.GeoDataFrame(geometry=[], crs=out.crs)
    current = read_any(CURRENT_PRIORITY) if CURRENT_PRIORITY.exists() else gpd.GeoDataFrame(geometry=[], crs=out.crs)
    mh = read_any(MH_FILTERED) if MH_FILTERED.exists() else gpd.GeoDataFrame(geometry=[], crs=out.crs)

    priority_2026["_id_key"] = norm_id(priority_2026["id"]) if "id" in priority_2026.columns else ""
    current["_id_key"] = norm_id(current["id"]) if "id" in current.columns else ""
    mh["_id_key"] = norm_id(mh["ID DENUE"]) if "ID DENUE" in mh.columns else ""

    priority_ids = set(priority_2026["_id_key"]) - {""}
    current_ids = set(current["_id_key"]) - {""}
    mh_ids = set(mh["_id_key"]) - {""}

    out["en_universo_prioritario_2026"] = out["_id_key"].isin(priority_ids)
    out["en_universo_prioritario_actual"] = out["_id_key"].isin(current_ids)
    out["en_mh_filtrado"] = out["_id_key"].isin(mh_ids)
    out["comparacion_mh_foco"] = out["en_mh_filtrado"].map(lambda value: "foco_y_mh" if value else "solo_foco")
    return out


def mh_vs_focus(foco: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if not MH_FILTERED.exists():
        return gpd.GeoDataFrame(geometry=[], crs=foco.crs)
    mh = read_any(MH_FILTERED)
    mh["_id_key"] = norm_id(mh["ID DENUE"]) if "ID DENUE" in mh.columns else ""
    foco_ids = set(foco["_id_key"]) - {""}
    foco_keep = foco[
        [
            "_id_key",
            "id",
            "clee",
            "nombre_de_la_unidad_economica",
            "codigo_de_la_clase_actividad_scian",
            "localidad",
            "categoria_foco_textil",
            "senales_foco_textil",
            "geometry",
        ]
    ].copy()
    foco_keep["comparacion_mh_foco"] = foco_keep["_id_key"].map(lambda value: "foco_y_mh" if value in set(mh["_id_key"]) else "solo_foco")
    foco_keep["fuente_comparacion"] = "foco_textil"
    foco_keep["nombre_mapa"] = foco_keep["nombre_de_la_unidad_economica"]

    mh_only = mh.loc[~mh["_id_key"].isin(foco_ids)].copy()
    mh_only["comparacion_mh_foco"] = mh_only["_id_key"].map(lambda value: "mh_sin_id" if not value else "solo_mh")
    mh_only["fuente_comparacion"] = "mh_filtrado"
    mh_only["id"] = mh_only["_id_key"]
    mh_only["nombre_mapa"] = "MH Name " + mh_only["Name"].fillna("").astype(str)
    mh_only["categoria_foco_textil"] = ""
    mh_only["senales_foco_textil"] = "fuera del universo foco o sin ID"

    keep = [
        "_id_key",
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "localidad",
        "categoria_foco_textil",
        "senales_foco_textil",
        "comparacion_mh_foco",
        "fuente_comparacion",
        "nombre_mapa",
        "Name",
        "DENUE",
        "ID DENUE",
        "geometry",
    ]
    combined = pd.concat(
        [foco_keep[[c for c in keep if c in foco_keep.columns]], mh_only[[c for c in keep if c in mh_only.columns]]],
        ignore_index=True,
    )
    return gpd.GeoDataFrame(combined, geometry="geometry", crs=foco.crs)


def count_table(foco: gpd.GeoDataFrame, mh_comp: gpd.GeoDataFrame) -> dict[str, pd.DataFrame]:
    tables = {
        "resumen_categoria_foco": foco.groupby("categoria_foco_textil", dropna=False).size().reset_index(name="registros"),
        "resumen_localidad": foco.groupby("localidad", dropna=False).size().reset_index(name="registros").sort_values("registros", ascending=False),
        "resumen_membresias": pd.DataFrame(
            [
                {"conjunto": "foco_textil_produccion_y_lavado_2026", "registros": len(foco)},
                {"conjunto": "en_universo_prioritario_2026", "registros": int(foco["en_universo_prioritario_2026"].sum())},
                {"conjunto": "en_universo_prioritario_actual", "registros": int(foco["en_universo_prioritario_actual"].sum())},
                {"conjunto": "en_mh_filtrado", "registros": int(foco["en_mh_filtrado"].sum())},
            ]
        ),
        "comparacion_mh_foco": mh_comp.groupby("comparacion_mh_foco", dropna=False).size().reset_index(name="registros"),
        "resumen_decision": foco.groupby(["categoria_foco_textil", "decision_estudio_sugerida"], dropna=False).size().reset_index(name="registros"),
    }
    return tables


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
        hydro.cx[minx - 3000 : maxx + 3000, miny - 3000 : maxy + 3000].plot(
            ax=ax, color="#2b8cbe", linewidth=0.45, alpha=0.75
        )
    for value, group in gdf.groupby(color_col, dropna=False):
        color = COLORS.get(str(value), "#525252")
        group.plot(ax=ax, color=color, markersize=35, edgecolor="white", linewidth=0.25, alpha=0.9, label=str(value))
    minx, miny, maxx, maxy = gdf.total_bounds
    pad_x = max((maxx - minx) * 0.12, 250)
    pad_y = max((maxy - miny) * 0.12, 250)
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()
    ax.legend(loc="best", fontsize=7, frameon=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def interactive_map(gdf: gpd.GeoDataFrame, color_col: str, path: Path, title: str) -> None:
    if gdf.empty:
        return
    web = gdf.to_crs("EPSG:4326").copy()
    web["lon"] = web.geometry.x
    web["lat"] = web.geometry.y
    web["nombre_mapa"] = web.get("nombre_de_la_unidad_economica", web.get("nombre_mapa", "")).fillna("").astype(str)
    hover = [
        c
        for c in [
            "id",
            "clee",
            "nombre_mapa",
            "localidad",
            "categoria_foco_textil",
            "senales_foco_textil",
            "codigo_de_la_clase_actividad_scian",
            "nombre_clase_actividad_scian",
            "etapa_productiva_sugerida",
            "decision_estudio_sugerida",
            "en_universo_prioritario_2026",
            "en_universo_prioritario_actual",
            "en_mh_filtrado",
            "distancia_hidrografia_m",
            "evidencia_clasificacion",
            "motivo_flag_estudio_prioritario",
            "nota_metodologica_foco",
            "comparacion_mh_foco",
            "fuente_comparacion",
            "Name",
            "ID DENUE",
        ]
        if c in web.columns
    ]
    color_map = {status: COLORS.get(status, "#525252") for status in sorted(web[color_col].fillna("").astype(str).unique())}
    fig = px.scatter_map(
        web,
        lat="lat",
        lon="lon",
        color=color_col,
        color_discrete_map=color_map,
        hover_name="nombre_mapa",
        hover_data=hover,
        zoom=11,
        height=760,
        title=title,
    )
    fig.update_layout(map_style="open-street-map", margin={"r": 10, "t": 55, "l": 10, "b": 10})
    fig.write_html(path, include_plotlyjs="cdn")


def latex_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.replace("\ufffd", "")
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
    header = " & ".join(latex_escape(c) for c in columns) + r" \\"
    lines = [r"\begin{tabular}{" + "l" * len(columns) + "}", r"\toprule", header, r"\midrule"]
    for _, row in df[columns].iterrows():
        lines.append(" & ".join(latex_escape(row[c]) for c in columns) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines)


def write_report(foco: gpd.GeoDataFrame, tables: dict[str, pd.DataFrame]) -> None:
    tex = REPORT_DIR / "reporte_foco_textil_produccion_y_lavado_2026.tex"
    cat = tables["resumen_categoria_foco"].copy()
    loc = tables["resumen_localidad"].head(10).copy()
    mem = tables["resumen_membresias"].copy()
    mh = tables["comparacion_mh_foco"].copy()

    lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=2cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\usepackage{longtable}",
        r"\usepackage{hyperref}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\title{Universo foco textil produccion y lavado 2026}",
        r"\author{Proyecto Atoyac - salida reproducible}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
        r"\section{Proposito}",
        (
            "Este reporte documenta un universo operativo amplio llamado "
            r"\texttt{foco\_textil\_produccion\_y\_lavado\_2026}. "
            "El objetivo es integrar, desde DENUE 2026, establecimientos con senales de produccion textil, "
            "maquila, confeccion, mezclilla, lavado, tintoreria, acabado o tratamiento. "
            "No es evidencia de descarga, contaminacion ni incumplimiento; es una herramienta de priorizacion y auditoria."
        ),
        r"\section{Criterio de construccion}",
        (
            "La base fue "
            r"\texttt{data/processed/denue2026\_universo\_textil\_clasificado.gpkg}. "
            "Se excluyeron decisiones automaticas de comercio, renta y no pertinencia. "
            "Se incluyeron registros con senales de proceso humedo/lavado/acabado, mezclilla, maquila/confeccion, "
            "fabricacion textil o pendientes de revision textil. Dentro del universo se conserva una categoria interna "
            "para distinguir lavado/acabado de maquila/confeccion."
        ),
        r"\section{Resultados}",
        f"El universo foco contiene {len(foco)} registros.",
        r"\subsection{Conteo por categoria}",
        latex_table(cat, ["categoria_foco_textil", "registros"]),
        r"\subsection{Conteo por localidad}",
        latex_table(loc, ["localidad", "registros"]),
        r"\subsection{Membresias con otros universos}",
        latex_table(mem, ["conjunto", "registros"]),
        r"\subsection{Comparacion con MH filtrado}",
        latex_table(mh, ["comparacion_mh_foco", "registros"]),
        r"\section{Mapas}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../mapas/mapa_foco_textil_por_categoria.png}",
        r"\caption{Universo foco textil produccion y lavado 2026 por categoria interna.}",
        r"\end{figure}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../mapas/mapa_comparacion_foco_vs_mh.png}",
        r"\caption{Comparacion entre universo foco y capa MH filtrada.}",
        r"\end{figure}",
        r"\section{Lectura comparativa}",
        (
            "La capa MH filtrada se solapa parcialmente con este universo, pero tambien contiene registros fuera del foco "
            "y algunos puntos sin ID DENUE. Esto sugiere que MH captura una nocion mas amplia de talleres o maquilas textiles. "
            "El nuevo universo foco permite dialogar con ese criterio amplio sin abandonar la trazabilidad por senales: "
            "produccion/confeccion, mezclilla y lavado/acabado quedan separados en campos auditables."
        ),
        r"\section{Archivos generados}",
        r"\begin{itemize}",
        r"\item \texttt{capas\_qgis/foco\_textil\_produccion\_y\_lavado\_2026.gpkg}",
        r"\item \texttt{tablas/foco\_textil\_produccion\_y\_lavado\_2026.csv}",
        r"\item \texttt{tablas/comparacion\_foco\_vs\_mh.csv}",
        r"\item \texttt{mapas/mapa\_foco\_textil\_por\_categoria.html}",
        r"\item \texttt{mapas/mapa\_comparacion\_foco\_vs\_mh.html}",
        r"\end{itemize}",
        r"\section{Conclusion}",
        (
            "El universo prioritario previo sigue siendo mas estricto para estudio ambiental. "
            "El universo foco textil produccion y lavado es un producto complementario, mas amplio, util para revisar "
            "talleres, maquilas y establecimientos con posible relacion productiva textil. "
            "Debe usarse como capa de trabajo y auditoria, no como prueba de contaminacion."
        ),
        r"\end{document}",
    ]
    tex.write_text("\n\n".join(lines), encoding="utf-8")


def write_index(tables: dict[str, pd.DataFrame]) -> None:
    def markdown_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "_Sin registros._"
        clean = df.astype(str).replace({"nan": "", "None": ""})
        clean = clean.map(lambda value: value.replace("\ufffd", "").replace("ï¿½", ""))
        headers = list(clean.columns)
        rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for _, row in clean.iterrows():
            rows.append("| " + " | ".join(str(row[col]).replace("|", "/") for col in headers) + " |")
        return "\n".join(rows)

    lines = [
        "# Universo foco textil produccion y lavado 2026",
        "",
        "Producto operativo amplio construido desde DENUE 2026. Integra senales de produccion, maquila, confeccion, mezclilla, lavado, lavanderia, tintoreria, acabado o tratamiento.",
        "",
        "No sustituye al universo prioritario ambiental; lo complementa para auditar talleres y maquilas textiles.",
        "",
        "## Archivos principales",
        "",
        "- `capas_qgis/foco_textil_produccion_y_lavado_2026.gpkg`",
        "- `tablas/foco_textil_produccion_y_lavado_2026.csv`",
        "- `tablas/comparacion_foco_vs_mh.csv`",
        "- `mapas/mapa_foco_textil_por_categoria.html`",
        "- `mapas/mapa_comparacion_foco_vs_mh.html`",
        "- `capas_qgis/santa_ana_foco_textil_produccion_y_lavado_2026.gpkg`",
        "- `tablas/santa_ana_foco_textil_produccion_y_lavado_2026.csv`",
        "- `mapas/santa_ana_mapa_foco_textil_por_categoria.html`",
        "- `mapas/santa_ana_mapa_comparacion_foco_vs_mh.html`",
        "- `reporte/reporte_foco_textil_produccion_y_lavado_2026.tex`",
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


def main() -> None:
    ensure_dirs()
    classified = read_any(CLASSIFIED_2026)
    foco = build_focus_universe(classified)
    foco = add_memberships(foco)
    mh_comp = mh_vs_focus(foco)
    tables = count_table(foco, mh_comp)

    safe_to_file(foco, LAYERS_DIR / "foco_textil_produccion_y_lavado_2026.gpkg", layer="foco_textil_produccion_y_lavado_2026")
    foco.drop(columns="geometry", errors="ignore").to_csv(TABLES_DIR / "foco_textil_produccion_y_lavado_2026.csv", index=False, encoding="utf-8-sig")
    safe_to_file(mh_comp, LAYERS_DIR / "comparacion_foco_vs_mh.gpkg", layer="comparacion_foco_vs_mh")
    mh_comp.drop(columns="geometry", errors="ignore").to_csv(TABLES_DIR / "comparacion_foco_vs_mh.csv", index=False, encoding="utf-8-sig")

    foco_santa = foco[foco["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")].copy()
    mh_comp_santa = mh_vs_focus(foco_santa)
    safe_to_file(
        foco_santa,
        LAYERS_DIR / "santa_ana_foco_textil_produccion_y_lavado_2026.gpkg",
        layer="santa_ana_foco_textil_produccion_y_lavado_2026",
    )
    foco_santa.drop(columns="geometry", errors="ignore").to_csv(
        TABLES_DIR / "santa_ana_foco_textil_produccion_y_lavado_2026.csv",
        index=False,
        encoding="utf-8-sig",
    )
    safe_to_file(
        mh_comp_santa,
        LAYERS_DIR / "santa_ana_comparacion_foco_vs_mh.gpkg",
        layer="santa_ana_comparacion_foco_vs_mh",
    )
    mh_comp_santa.drop(columns="geometry", errors="ignore").to_csv(
        TABLES_DIR / "santa_ana_comparacion_foco_vs_mh.csv",
        index=False,
        encoding="utf-8-sig",
    )

    for name, df in tables.items():
        df.to_csv(TABLES_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(TABLES_DIR / "resumen_foco_textil_produccion_y_lavado_2026.xlsx", engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)

    static_map(
        foco,
        "categoria_foco_textil",
        MAPS_DIR / "mapa_foco_textil_por_categoria.png",
        "Foco textil produccion y lavado 2026",
    )
    interactive_map(
        foco,
        "categoria_foco_textil",
        MAPS_DIR / "mapa_foco_textil_por_categoria.html",
        "Foco textil produccion y lavado 2026",
    )
    static_map(
        mh_comp,
        "comparacion_mh_foco",
        MAPS_DIR / "mapa_comparacion_foco_vs_mh.png",
        "Comparacion foco textil vs MH filtrado",
    )
    interactive_map(
        mh_comp,
        "comparacion_mh_foco",
        MAPS_DIR / "mapa_comparacion_foco_vs_mh.html",
        "Comparacion foco textil vs MH filtrado",
    )
    static_map(
        foco_santa,
        "categoria_foco_textil",
        MAPS_DIR / "santa_ana_mapa_foco_textil_por_categoria.png",
        "Santa Ana - foco textil produccion y lavado 2026",
    )
    interactive_map(
        foco_santa,
        "categoria_foco_textil",
        MAPS_DIR / "santa_ana_mapa_foco_textil_por_categoria.html",
        "Santa Ana - foco textil produccion y lavado 2026",
    )
    static_map(
        mh_comp_santa,
        "comparacion_mh_foco",
        MAPS_DIR / "santa_ana_mapa_comparacion_foco_vs_mh.png",
        "Santa Ana - comparacion foco textil vs MH filtrado",
    )
    interactive_map(
        mh_comp_santa,
        "comparacion_mh_foco",
        MAPS_DIR / "santa_ana_mapa_comparacion_foco_vs_mh.html",
        "Santa Ana - comparacion foco textil vs MH filtrado",
    )

    write_report(foco, tables)
    write_index(tables)
    print(f"[atoyac] Universo foco guardado en {relpath(OUT_DIR)} con {len(foco)} registros")


if __name__ == "__main__":
    main()
