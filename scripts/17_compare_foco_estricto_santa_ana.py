from __future__ import annotations

import subprocess
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

from common import OUTPUTS_DIR, PROCESSED_DIR, PROJECT_ROOT, read_gpkg, relpath, safe_to_file


OUT_DIR = OUTPUTS_DIR / "foco_textil_estricto_santa_ana_2026"
MAPS_DIR = OUT_DIR / "mapas"
TABLES_DIR = OUT_DIR / "tablas"
LAYERS_DIR = OUT_DIR / "capas_qgis"
DOCS_DIR = PROJECT_ROOT / "docs"

FOCO_ESTRICTO = OUT_DIR / "capas_qgis" / "foco_textil_estricto_santa_ana_2026.gpkg"
FILTRADO_2026 = OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg"
MH_FILTRADO = PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp"
UNION_PREVIA = (
    OUTPUTS_DIR
    / "auditoria_santa_ana_mh_filtrado"
    / "capas_qgis"
    / "09_union_conjuntos_santa_ana_senales.gpkg"
)
LOCALIDADES = PROCESSED_DIR / "localidades.gpkg"
HIDROGRAFIA = PROCESSED_DIR / "hidrografia.gpkg"
TARGET_CRS = "EPSG:6372"

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
    "en_union_previa": "#1b9e77",
    "fuera_union_previa": "#756bb1",
}


def ensure_dirs() -> None:
    for path in [MAPS_DIR, TABLES_DIR, LAYERS_DIR, DOCS_DIR]:
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


def name_col(gdf: pd.DataFrame) -> pd.Series:
    for col in ["nombre_de_la_unidad_economica", "nombre_mapa", "Name"]:
        if col in gdf.columns:
            return gdf[col].fillna("").astype(str)
    return pd.Series("", index=gdf.index)


def keep_source(gdf: gpd.GeoDataFrame, source: str, id_col: str = "id") -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["_id_key"] = norm_id(out[id_col]) if id_col in out.columns else ""
    out["fuente_geometria"] = source
    out["nombre_mapa"] = name_col(out)
    return out


def load_sets() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    foco = keep_source(read_any(FOCO_ESTRICTO), "foco_estricto", "id")
    filtrado = read_any(FILTRADO_2026)
    filtrado = filtrado[filtrado["localidad"].fillna("").astype(str).eq("Santa Ana Xalmimilulco")].copy()
    filtrado = keep_source(filtrado, "filtrado_2026", "id")
    mh = keep_source(read_any(MH_FILTRADO), "mh_filtrado", "ID DENUE")
    union = keep_source(read_any(UNION_PREVIA), "union_previa", "id")
    return foco, filtrado, mh, union


def first_by_id(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    keyed = gdf[gdf["_id_key"].ne("")].copy()
    if keyed.empty:
        return keyed
    return keyed.sort_values("_id_key").drop_duplicates("_id_key", keep="first")


def build_comparison(
    foco: gpd.GeoDataFrame,
    filtrado: gpd.GeoDataFrame,
    mh: gpd.GeoDataFrame,
    union: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    foco_ids = set(foco["_id_key"]) - {""}
    filtrado_ids = set(filtrado["_id_key"]) - {""}
    mh_ids = set(mh["_id_key"]) - {""}
    union_ids = set(union["_id_key"]) - {""}

    pieces: list[gpd.GeoDataFrame] = []
    for source_gdf in [first_by_id(foco), first_by_id(filtrado), first_by_id(union), first_by_id(mh)]:
        ids_already = set(pd.concat(pieces)["_id_key"]) if pieces else set()
        add = source_gdf[~source_gdf["_id_key"].isin(ids_already)].copy()
        pieces.append(add)
    combined = gpd.GeoDataFrame(pd.concat(pieces, ignore_index=True), geometry="geometry", crs=foco.crs)

    mh_no_id = mh[mh["_id_key"].eq("")].copy()
    if not mh_no_id.empty:
        mh_no_id = mh_no_id.copy()
        mh_no_id["_id_key"] = [f"mh_sin_id_{i + 1}" for i in range(len(mh_no_id))]
        combined = gpd.GeoDataFrame(pd.concat([combined, mh_no_id], ignore_index=True), geometry="geometry", crs=foco.crs)

    combined["en_foco_estricto"] = combined["_id_key"].isin(foco_ids)
    combined["en_filtrado_2026_santa"] = combined["_id_key"].isin(filtrado_ids)
    combined["en_mh_filtrado"] = combined["_id_key"].isin(mh_ids)
    combined["en_union_previa"] = combined["_id_key"].isin(union_ids)
    combined.loc[combined["_id_key"].str.startswith("mh_sin_id_"), "en_mh_filtrado"] = True
    combined["en_universo_actual_santa"] = False
    if "en_universo_actual_santa" in union.columns:
        actual_ids = set(union.loc[union["en_universo_actual_santa"].astype(str).str.lower().eq("true"), "_id_key"]) - {""}
        combined["en_universo_actual_santa"] = combined["_id_key"].isin(actual_ids)

    combined["perfil_comparacion"] = combined.apply(profile_row, axis=1)
    combined["comparacion_estricto_vs_2026"] = combined.apply(pair_strict_2026, axis=1)
    combined["comparacion_estricto_vs_mh"] = combined.apply(pair_strict_mh, axis=1)
    combined["comparacion_estricto_vs_union"] = combined.apply(pair_strict_union, axis=1)
    combined["membresias_resumen"] = combined.apply(membership_summary, axis=1)
    combined["lectura_auditoria"] = combined.apply(audit_reading, axis=1)
    return combined


def profile_row(row: pd.Series) -> str:
    strict = bool(row["en_foco_estricto"])
    f2026 = bool(row["en_filtrado_2026_santa"])
    mh = bool(row["en_mh_filtrado"])
    union = bool(row["en_union_previa"])
    if str(row["_id_key"]).startswith("mh_sin_id_"):
        return "mh_sin_id"
    if strict and f2026 and mh and union:
        return "en_los_4"
    if strict and f2026 and union and not mh:
        return "estricto_2026_union_no_mh"
    if strict and f2026 and not mh and not union:
        return "estricto_y_2026_no_mh_no_union"
    if strict and mh and not f2026:
        return "estricto_y_mh_no_2026"
    if strict and not f2026 and not mh:
        return "solo_estricto"
    if f2026 and union and not strict and not mh:
        return "2026_union_no_estricto_no_mh"
    if mh and union and not strict and not f2026:
        return "mh_union_no_estricto_no_2026"
    if union and not strict and not f2026 and not mh:
        return "union_no_estricto_no_2026_no_mh"
    if f2026 and not strict and not mh:
        return "solo_2026"
    if mh and not strict:
        return "solo_mh"
    return "otro"


def pair_strict_2026(row: pd.Series) -> str:
    if row["en_foco_estricto"] and row["en_filtrado_2026_santa"]:
        return "estricto_y_filtrado_2026"
    if row["en_foco_estricto"]:
        return "solo_foco_estricto"
    if row["en_filtrado_2026_santa"]:
        return "solo_filtrado_2026"
    return "fuera_de_ambos"


def pair_strict_mh(row: pd.Series) -> str:
    if str(row["_id_key"]).startswith("mh_sin_id_"):
        return "mh_sin_id"
    if row["en_foco_estricto"] and row["en_mh_filtrado"]:
        return "estricto_y_mh"
    if row["en_foco_estricto"]:
        return "solo_foco_estricto"
    if row["en_mh_filtrado"]:
        return "solo_mh_con_id"
    return "fuera_de_ambos"


def pair_strict_union(row: pd.Series) -> str:
    if row["en_foco_estricto"] and row["en_union_previa"]:
        return "en_union_previa"
    if row["en_foco_estricto"]:
        return "fuera_union_previa"
    if row["en_union_previa"]:
        return "union_sin_foco_estricto"
    return "fuera_de_ambos"


def membership_summary(row: pd.Series) -> str:
    labels = []
    if row["en_foco_estricto"]:
        labels.append("foco estricto")
    if row["en_filtrado_2026_santa"]:
        labels.append("filtrado 2026")
    if row["en_mh_filtrado"]:
        labels.append("MH filtrado")
    if row["en_union_previa"]:
        labels.append("union previa")
    if row["en_universo_actual_santa"]:
        labels.append("universo actual")
    return "; ".join(labels) if labels else "sin membresia"


def audit_reading(row: pd.Series) -> str:
    profile = row["perfil_comparacion"]
    if profile == "en_los_4":
        return "Coincide en foco estricto, filtrado 2026, MH y union previa."
    if profile == "estricto_2026_union_no_mh":
        return "Coincide entre foco estricto y filtrado 2026; MH no lo conserva."
    if profile == "solo_estricto":
        return "Entra por criterio estricto nuevo, pero no estaba en filtrado 2026 ni MH; revisar como ampliacion focalizada."
    if profile == "2026_union_no_estricto_no_mh":
        return "Estaba en filtrado 2026/union previa, pero sale por el filtro estricto; probable falso positivo o senal no textil suficiente."
    if profile == "mh_union_no_estricto_no_2026":
        return "MH lo conserva, pero no entra en foco estricto ni filtrado 2026; probable criterio MH mas amplio."
    if profile == "mh_sin_id":
        return "Punto MH sin ID DENUE; no puede compararse por identificador."
    return "Revisar en mapa y tabla por combinacion de membresias."


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
    plot = gdf[gdf[color_col].ne("fuera_de_ambos")].copy() if color_col in gdf.columns else gdf.copy()
    if plot.empty:
        return
    localidades, hydro = base_layers(plot.crs)
    fig, ax = plt.subplots(figsize=(10.5, 8), dpi=180)
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#737373", linewidth=0.5)
    if hydro is not None and not hydro.empty:
        minx, miny, maxx, maxy = plot.total_bounds
        hydro.cx[minx - 1000 : maxx + 1000, miny - 1000 : maxy + 1000].plot(
            ax=ax, color="#67a9cf", linewidth=0.7, alpha=0.75
        )
    for value, subset in plot.groupby(color_col, dropna=False):
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
    plot = gdf[gdf[color_col].ne("fuera_de_ambos")].copy() if color_col in gdf.columns else gdf.copy()
    if plot.empty:
        return
    plot = plot.to_crs("EPSG:4326")
    plot["lon"] = plot.geometry.x
    plot["lat"] = plot.geometry.y
    hover_cols = [
        c
        for c in [
            "_id_key",
            "id",
            "nombre_mapa",
            "nombre_de_la_unidad_economica",
            "Name",
            "perfil_comparacion",
            "membresias_resumen",
            "lectura_auditoria",
            "categoria_foco_estricto",
            "senales_foco_estricto",
            "etapa_productiva_sugerida",
            "decision_estudio_sugerida",
            "codigo_de_la_clase_actividad_scian",
            "nombre_clase_actividad_scian",
            "en_foco_estricto",
            "en_filtrado_2026_santa",
            "en_mh_filtrado",
            "en_union_previa",
            "en_universo_actual_santa",
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
    fig.update_traces(marker={"size": 10, "opacity": 0.86})
    fig.update_layout(map_style="open-street-map", margin={"r": 10, "t": 55, "l": 10, "b": 10})
    fig.write_html(path, include_plotlyjs="cdn")


def make_tables(comp: gpd.GeoDataFrame, foco: gpd.GeoDataFrame, filtrado: gpd.GeoDataFrame, mh: gpd.GeoDataFrame, union: gpd.GeoDataFrame) -> dict[str, pd.DataFrame]:
    no_id_mh = int(mh["_id_key"].eq("").sum())
    def count_pair(column: str) -> pd.DataFrame:
        pair = comp[comp[column].ne("fuera_de_ambos")].copy()
        return pair.groupby(column, dropna=False).size().reset_index(name="registros")

    tables = {
        "resumen_tamanos": pd.DataFrame(
            [
                {"conjunto": "foco_estricto_santa_ana_2026", "registros": len(foco)},
                {"conjunto": "filtrado_prioritario_denue_2026_santa_ana", "registros": len(filtrado)},
                {"conjunto": "mh_filtrado", "registros": len(mh)},
                {"conjunto": "mh_filtrado_sin_id", "registros": no_id_mh},
                {"conjunto": "union_previa_auditoria", "registros": len(union)},
                {"conjunto": "union_total_comparacion_directa", "registros": len(comp)},
            ]
        ),
        "perfil_comparacion": comp.groupby("perfil_comparacion", dropna=False).size().reset_index(name="registros"),
        "foco_vs_filtrado_2026": count_pair("comparacion_estricto_vs_2026"),
        "foco_vs_mh": count_pair("comparacion_estricto_vs_mh"),
        "foco_vs_union_previa": count_pair("comparacion_estricto_vs_union"),
    }
    return tables


def latex_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    for old, new in {
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
    }.items():
        text = text.replace(old, new)
    return text


def latex_table(df: pd.DataFrame, cols: list[str]) -> str:
    lines = [r"\begin{tabular}{" + "l" * len(cols) + "}", r"\toprule"]
    lines.append(" & ".join(latex_escape(c) for c in cols) + r" \\")
    lines.append(r"\midrule")
    for _, row in df[cols].iterrows():
        lines.append(" & ".join(latex_escape(row[c]) for c in cols) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines)


def write_docs(tables: dict[str, pd.DataFrame]) -> None:
    tex = DOCS_DIR / "comparacion_foco_textil_estricto_santa_ana_2026.tex"
    lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=2cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\usepackage{hyperref}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\title{Comparacion del foco textil estricto Santa Ana 2026}",
        r"\author{Proyecto Atoyac - salida reproducible}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
        r"\section{Objetivo}",
        (
            "Este documento compara directamente cuatro conjuntos para Santa Ana Xalmimilulco: "
            "el foco textil estricto 2026, el filtrado prioritario DENUE 2026, la capa MH filtrada y la union previa "
            "construida en la auditoria. La comparacion se hace por ID DENUE cuando existe; los puntos MH sin ID se "
            "mantienen como casos auditables separados. Ningun conjunto se interpreta como evidencia de descarga o "
            "contaminacion; se usa como priorizacion y revision de consistencia."
        ),
        r"\section{Criterio de lectura}",
        (
            "El foco estricto retira confeccion/maquila generica, planchado, alta costura, ropa terminada, bodegas, "
            "insumos y servicios no textiles. Por eso puede ser menor que MH o que la union previa, pero mas alineado "
            "con procesos de lavado, acabado, tintoreria, mezclilla, jeans, deshebrado o tratamiento textil."
        ),
        r"\section{Tamanos de conjuntos}",
        latex_table(tables["resumen_tamanos"], ["conjunto", "registros"]),
        r"\section{Perfil de coincidencias}",
        latex_table(tables["perfil_comparacion"], ["perfil_comparacion", "registros"]),
        r"\section{Cruce foco estricto vs filtrado 2026}",
        latex_table(tables["foco_vs_filtrado_2026"], ["comparacion_estricto_vs_2026", "registros"]),
        r"\section{Cruce foco estricto vs MH}",
        latex_table(tables["foco_vs_mh"], ["comparacion_estricto_vs_mh", "registros"]),
        r"\section{Cruce foco estricto vs union previa}",
        latex_table(tables["foco_vs_union_previa"], ["comparacion_estricto_vs_union", "registros"]),
        r"\section{Mapas}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../outputs/foco_textil_estricto_santa_ana_2026/mapas/mapa_comparacion_directa_4_conjuntos.png}",
        r"\caption{Comparacion directa entre foco estricto, filtrado 2026, MH y union previa.}",
        r"\end{figure}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../outputs/foco_textil_estricto_santa_ana_2026/mapas/mapa_foco_estricto_vs_filtrado_2026.png}",
        r"\caption{Foco estricto frente al filtrado prioritario DENUE 2026.}",
        r"\end{figure}",
        r"\begin{figure}[h!]\centering",
        r"\includegraphics[width=0.95\linewidth]{../outputs/foco_textil_estricto_santa_ana_2026/mapas/mapa_foco_estricto_vs_mh_directo.png}",
        r"\caption{Foco estricto frente a MH filtrado.}",
        r"\end{figure}",
        r"\section{Conclusion operativa}",
        (
            "El foco estricto conserva el nucleo de establecimientos con senales mas pertinentes para auditoria "
            "ambiental de proceso textil. La capa MH filtrada coincide solo parcialmente, lo que confirma que MH usa "
            "un criterio mas amplio de talleres o maquilas. El filtrado DENUE 2026 coincide en una parte importante, "
            "pero algunos registros salen del foco estricto por ser servicios de agua, insumos, bodegas o senales no "
            "suficientemente textiles. La union previa es util como inventario de auditoria, mientras que el foco "
            "estricto es la capa recomendada para presentar un universo depurado de proceso textil."
        ),
        r"\section{Archivos generados}",
        r"\begin{itemize}",
        r"\item \texttt{outputs/foco\_textil\_estricto\_santa\_ana\_2026/capas\_qgis/comparacion\_directa\_4\_conjuntos.gpkg}",
        r"\item \texttt{outputs/foco\_textil\_estricto\_santa\_ana\_2026/tablas/comparacion\_directa\_4\_conjuntos.csv}",
        r"\item \texttt{outputs/foco\_textil\_estricto\_santa\_ana\_2026/mapas/mapa\_comparacion\_directa\_4\_conjuntos.html}",
        r"\item \texttt{outputs/foco\_textil\_estricto\_santa\_ana\_2026/mapas/mapa\_foco\_estricto\_vs\_filtrado\_2026.html}",
        r"\item \texttt{outputs/foco\_textil\_estricto\_santa\_ana\_2026/mapas/mapa\_foco\_estricto\_vs\_mh\_directo.html}",
        r"\end{itemize}",
        r"\end{document}",
    ]
    tex.write_text("\n\n".join(lines), encoding="utf-8")

    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
            cwd=DOCS_DIR,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass


def update_index(tables: dict[str, pd.DataFrame]) -> None:
    index = OUT_DIR / "index.md"
    if not index.exists():
        return
    text = index.read_text(encoding="utf-8")
    marker = "## Comparacion directa con MH, filtrado 2026 y union previa"
    if marker in text:
        text = text.split(marker)[0].rstrip()

    def md_table(df: pd.DataFrame) -> str:
        clean = df.astype(str)
        headers = list(clean.columns)
        rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for _, row in clean.iterrows():
            rows.append("| " + " | ".join(row[h].replace("|", "/") for h in headers) + " |")
        return "\n".join(rows)

    block = [
        "",
        marker,
        "",
        "- Mapa 4 conjuntos: `mapas/mapa_comparacion_directa_4_conjuntos.html`",
        "- Mapa foco estricto vs filtrado 2026: `mapas/mapa_foco_estricto_vs_filtrado_2026.html`",
        "- Mapa foco estricto vs MH: `mapas/mapa_foco_estricto_vs_mh_directo.html`",
        "- Mapa foco estricto vs union previa: `mapas/mapa_foco_estricto_vs_union_previa.html`",
        "- Documento LaTeX: `../../docs/comparacion_foco_textil_estricto_santa_ana_2026.tex`",
        "- PDF: `../../docs/comparacion_foco_textil_estricto_santa_ana_2026.pdf`",
        "",
        "### resumen_tamanos",
        "",
        md_table(tables["resumen_tamanos"]),
        "",
        "### perfil_comparacion",
        "",
        md_table(tables["perfil_comparacion"]),
        "",
    ]
    index.write_text(text + "\n".join(block) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    foco, filtrado, mh, union = load_sets()
    comp = build_comparison(foco, filtrado, mh, union)
    tables = make_tables(comp, foco, filtrado, mh, union)

    safe_to_file(comp, LAYERS_DIR / "comparacion_directa_4_conjuntos.gpkg", layer="comparacion_directa_4_conjuntos")
    comp.drop(columns="geometry", errors="ignore").to_csv(
        TABLES_DIR / "comparacion_directa_4_conjuntos.csv",
        index=False,
        encoding="utf-8-sig",
    )
    for name, table in tables.items():
        table.to_csv(TABLES_DIR / f"comparacion_directa_{name}.csv", index=False, encoding="utf-8-sig")

    static_map(comp, "perfil_comparacion", MAPS_DIR / "mapa_comparacion_directa_4_conjuntos.png", "Santa Ana - comparacion directa 4 conjuntos")
    interactive_map(comp, "perfil_comparacion", MAPS_DIR / "mapa_comparacion_directa_4_conjuntos.html", "Santa Ana - comparacion directa 4 conjuntos")
    static_map(comp, "comparacion_estricto_vs_2026", MAPS_DIR / "mapa_foco_estricto_vs_filtrado_2026.png", "Santa Ana - foco estricto vs filtrado DENUE 2026")
    interactive_map(comp, "comparacion_estricto_vs_2026", MAPS_DIR / "mapa_foco_estricto_vs_filtrado_2026.html", "Santa Ana - foco estricto vs filtrado DENUE 2026")
    static_map(comp, "comparacion_estricto_vs_mh", MAPS_DIR / "mapa_foco_estricto_vs_mh_directo.png", "Santa Ana - foco estricto vs MH filtrado")
    interactive_map(comp, "comparacion_estricto_vs_mh", MAPS_DIR / "mapa_foco_estricto_vs_mh_directo.html", "Santa Ana - foco estricto vs MH filtrado")
    static_map(comp, "comparacion_estricto_vs_union", MAPS_DIR / "mapa_foco_estricto_vs_union_previa.png", "Santa Ana - foco estricto vs union previa")
    interactive_map(comp, "comparacion_estricto_vs_union", MAPS_DIR / "mapa_foco_estricto_vs_union_previa.html", "Santa Ana - foco estricto vs union previa")

    write_docs(tables)
    update_index(tables)
    print(f"[atoyac] Comparacion directa guardada en {relpath(OUT_DIR)}")
    print(tables["resumen_tamanos"].to_string(index=False))
    print(tables["perfil_comparacion"].to_string(index=False))


if __name__ == "__main__":
    main()
