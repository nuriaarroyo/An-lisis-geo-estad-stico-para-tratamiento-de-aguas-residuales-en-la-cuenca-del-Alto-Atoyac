from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

from version_01.scripts.common import read_gpkg, safe_to_file


TARGET_CRS = "EPSG:6372"


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def read_vector(path: Path, target_crs: str = TARGET_CRS) -> gpd.GeoDataFrame:
    gdf = read_gpkg(path) if path.suffix.lower() == ".gpkg" else gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf.to_crs(target_crs)


def normalize_denue_id(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .replace({"nan": "", "None": "", "<NA>": ""})
    )


def bool_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    return df[column].fillna(False).astype(bool)


def export_geodata(
    gdf: gpd.GeoDataFrame,
    gpkg_path: Path,
    csv_path: Path,
    layer: str,
) -> None:
    safe_to_file(gdf, gpkg_path, layer=layer)
    gdf.drop(columns="geometry", errors="ignore").to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
    )


@lru_cache(maxsize=8)
def _load_context_layers_cached(
    localidades_path: str,
    hidrografia_path: str,
    crs: str,
) -> tuple[gpd.GeoDataFrame | None, gpd.GeoDataFrame | None]:
    localidades_file = Path(localidades_path)
    hidrografia_file = Path(hidrografia_path)
    localidades = read_vector(localidades_file, crs) if localidades_file.exists() else None
    hidrografia = read_vector(hidrografia_file, crs) if hidrografia_file.exists() else None
    if hidrografia is not None and not hidrografia.empty:
        is_line = hidrografia.geometry.geom_type.fillna("").str.contains("Line", case=False)
        hidrografia = hidrografia.loc[is_line].copy()
    return localidades, hidrografia


def load_context_layers(
    localidades_path: Path,
    hidrografia_path: Path,
    crs: str,
) -> tuple[gpd.GeoDataFrame | None, gpd.GeoDataFrame | None]:
    return _load_context_layers_cached(str(localidades_path), str(hidrografia_path), crs)


def save_static_map(
    gdf: gpd.GeoDataFrame,
    color_column: str,
    path: Path,
    title: str,
    colors: dict[str, str],
    localidades_path: Path,
    hidrografia_path: Path,
    excluded_values: set[str] | None = None,
) -> None:
    plot = gdf.copy()
    if excluded_values and color_column in plot.columns:
        plot = plot.loc[~plot[color_column].isin(excluded_values)].copy()
    if plot.empty:
        return

    localidades, hidrografia = load_context_layers(
        localidades_path,
        hidrografia_path,
        str(plot.crs),
    )
    fig, ax = plt.subplots(figsize=(10.5, 8), dpi=180)
    if localidades is not None and not localidades.empty:
        localidades.plot(ax=ax, facecolor="none", edgecolor="#737373", linewidth=0.5)
    if hidrografia is not None and not hidrografia.empty:
        minx, miny, maxx, maxy = plot.total_bounds
        window = hidrografia.cx[minx - 1000 : maxx + 1000, miny - 1000 : maxy + 1000]
        if not window.empty:
            window.plot(ax=ax, color="#67a9cf", linewidth=0.7, alpha=0.75)

    for value, subset in plot.groupby(color_column, dropna=False):
        label = str(value) if str(value) else "sin_valor"
        subset.plot(
            ax=ax,
            markersize=42,
            color=colors.get(label, "#525252"),
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


def save_interactive_map(
    gdf: gpd.GeoDataFrame,
    color_column: str,
    path: Path,
    title: str,
    colors: dict[str, str],
    hover_candidates: Iterable[str],
    excluded_values: set[str] | None = None,
) -> None:
    plot = gdf.copy()
    if excluded_values and color_column in plot.columns:
        plot = plot.loc[~plot[color_column].isin(excluded_values)].copy()
    if plot.empty:
        return

    plot = plot.to_crs("EPSG:4326")
    plot["lon"] = plot.geometry.x
    plot["lat"] = plot.geometry.y
    hover_columns = [column for column in hover_candidates if column in plot.columns]
    fig = px.scatter_map(
        plot,
        lat="lat",
        lon="lon",
        color=color_column,
        color_discrete_map=colors,
        hover_data=hover_columns,
        zoom=12,
        height=760,
        title=title,
    )
    fig.update_traces(marker={"size": 10, "opacity": 0.86})
    fig.update_layout(
        map_style="open-street-map",
        margin={"r": 10, "t": 55, "l": 10, "b": 10},
    )
    fig.write_html(path, include_plotlyjs="cdn")


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
    lines.append(" & ".join(latex_escape(column) for column in columns) + r" \\")
    lines.append(r"\midrule")
    for _, row in df[columns].iterrows():
        lines.append(" & ".join(latex_escape(row[column]) for column in columns) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines)


def latex_document(title: str, body: Iterable[str]) -> str:
    lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=2cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\usepackage{hyperref}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        rf"\title{{{title}}}",
        r"\author{Proyecto Atoyac - salida reproducible}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
        *body,
        r"\end{document}",
    ]
    return "\n\n".join(lines)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin registros._"
    clean = df.astype(str).replace({"nan": "", "None": ""})
    headers = list(clean.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in clean.iterrows():
        values = [str(row[column]).replace("|", "/") for column in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def compile_latex(tex_path: Path) -> bool:
    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=tex_path.parent,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0
