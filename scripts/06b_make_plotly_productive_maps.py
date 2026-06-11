from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px

from common import OUTPUTS_DIR, PROCESSED_DIR, TABLES_DIR, ensure_output_dirs, log, read_gpkg, relpath


OUT_DIR = OUTPUTS_DIR / "maps_interactive" / "denue_clasificacion_productiva"
TABLE_DIR = TABLES_DIR / "denue_clasificacion_productiva"
LOCALITY_SLUGS = {
    "Huejotzingo": "huejotzingo",
    "Santa Ana Xalmimilulco": "xalmimilulco",
    "San Martin Texmelucan": "san_martin",
}

MAP_SPECS = [
    ("mapa_interactivo_universo_textil_inicial.html", "Universo textil detectado inicialmente", lambda df: df.index == df.index, "etapa_productiva_sugerida"),
    ("mapa_interactivo_universo_textil_depurado.html", "Universo textil depurado", lambda df: ~df["decision_estudio_sugerida"].isin(["excluir_por_comercio", "excluir_por_renta", "excluir_del_universo_prioritario"]), "etapa_productiva_sugerida"),
    ("mapa_interactivo_estudio_prioritario.html", "Establecimientos prioritarios para investigacion", lambda df: df["flag_estudio_prioritario"], "presion_ambiental_potencial"),
    ("mapa_interactivo_procesos_humedos.html", "Senales compatibles con procesos humedos", lambda df: df["flag_proceso_humedo_relevante"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_lavado_deslavado.html", "Lavado y deslavado", lambda df: df["flag_lavado_deslavado"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_tenido_tintoreria.html", "Tenido y tintoreria", lambda df: df["flag_tenido_tintoreria"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_acabado_tratamiento.html", "Acabado y tratamiento especial", lambda df: df["flag_acabado_tratamiento"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_mezclilla_jeans.html", "Mezclilla y jeans", lambda df: df["flag_mezclilla_jeans"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_maquila_productiva.html", "Maquila productiva", lambda df: df["flag_maquila_productiva"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_pendientes_auditoria.html", "Pendientes de auditoria", lambda df: df["requiere_auditoria_manual"], "prioridad_auditoria"),
    ("mapa_interactivo_cercania_hidrografia_250m.html", "Registros a 250 m o menos de hidrografia", lambda df: df["flag_cercania_hidrografia_250m"], "prioridad_campo"),
    ("mapa_interactivo_prioridad_campo.html", "Prioridad de campo", lambda df: df["flag_prioridad_campo"], "prioridad_campo"),
    ("mapa_interactivo_excluidos_comercio.html", "Excluidos por comercio o renta", lambda df: df["flag_comercio_o_renta"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_confeccion_especializada.html", "Confeccion especializada de baja relevancia", lambda df: df["flag_confeccion_especializada_baja_relevancia"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_consolidado_filtros.html", "Consolidado de clasificacion productiva", lambda df: df.index == df.index, "decision_estudio_sugerida"),
    ("mapa_interactivo_universo_alcance_proyecto.html", "Universo de alcance del proyecto", lambda df: df["flag_universo_alcance_proyecto"], "etapa_productiva_sugerida"),
    ("mapa_interactivo_fuera_alcance_contexto_textil.html", "Contexto textil fuera del alcance operativo", lambda df: df["flag_fuera_alcance_productivo_textil"], "etapa_productiva_sugerida"),
]

LOCALITY_MAP_SPECS = [
    ("universo_alcance", "Universo de alcance del proyecto", lambda df: df["flag_universo_alcance_proyecto"], "etapa_productiva_sugerida"),
    ("procesos_humedos", "Procesos humedos o tratamiento", lambda df: df["flag_proceso_humedo_relevante"], "etapa_productiva_sugerida"),
    ("lavado_deslavado", "Lavado o deslavado", lambda df: df["flag_lavado_deslavado"], "etapa_productiva_sugerida"),
    ("mezclilla_jeans", "Mezclilla o jeans", lambda df: df["flag_mezclilla_jeans"], "etapa_productiva_sugerida"),
]

COLOR_MAP = {
    "alta": "#b2182b",
    "media": "#ef8a62",
    "baja": "#4daf4a",
    "pendiente": "#7b3294",
    "lavado_deslavado": "#b2182b",
    "lavanderia_industrial": "#d6604d",
    "tenido_tintoreria": "#7b3294",
    "acabado_textil": "#e08214",
    "fabricacion_mezclilla": "#0571b0",
    "confeccion_maquila": "#4393c3",
    "fabricacion_textil": "#92c5de",
    "bordado": "#66bd63",
    "confeccion_especializada_baja_relevancia": "#a6dba0",
    "comercio_simple": "#999999",
    "revisar": "#762a83",
    "incluir_prioritario": "#b2182b",
    "incluir_contexto_productivo": "#4393c3",
    "validar_documentalmente": "#756bb1",
    "mantener_pendiente": "#7b3294",
    "excluir_del_universo_prioritario": "#969696",
    "excluir_por_comercio": "#bdbdbd",
}


def load_points() -> pd.DataFrame:
    gdf = read_gpkg(PROCESSED_DIR / "denue_universo_textil_clasificado.gpkg").to_crs("EPSG:4326")
    df = gdf.drop(columns="geometry").copy()
    df["lat_plot"] = gdf.geometry.y
    df["lon_plot"] = gdf.geometry.x
    for col in df.columns:
        if str(df[col].dtype) == "bool":
            df[col] = df[col].astype(bool)
    return df


def write_plot(df: pd.DataFrame, filename: str, title: str, color_col: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        html = f"<html><body><h1>{title}</h1><p>Sin registros para este filtro.</p></body></html>"
        out.write_text(html, encoding="utf-8")
        return
    hover_cols = [
        "nombre_de_la_unidad_economica",
        "codigo_scian_original",
        "actividad_denue_original",
        "etapa_productiva_sugerida",
        "presion_ambiental_potencial",
        "confianza_clasificacion",
        "decision_alcance_proyecto",
        "flag_universo_alcance_proyecto",
        "motivo_universo_alcance_proyecto",
        "flag_estudio_prioritario",
        "motivo_flag_estudio_prioritario",
        "distancia_hidrografia_m",
        "rango_distancia_hidrografia",
        "localidad",
        "municipio",
        "palabras_clave_etapa",
        "reglas_activadas",
        "query_maps",
        "query_web",
    ]
    hover_cols = [c for c in hover_cols if c in df.columns]
    fig = px.scatter_map(
        df,
        lat="lat_plot",
        lon="lon_plot",
        color=color_col,
        color_discrete_map=COLOR_MAP,
        hover_name="nombre_de_la_unidad_economica",
        hover_data=hover_cols,
        zoom=10,
        height=760,
        title=f"{title}<br><sup>Prioridad de investigacion; no evidencia descarga ni contaminacion</sup>",
    )
    fig.update_traces(marker={"size": 8, "opacity": 0.82})
    fig.update_layout(
        map_style="open-street-map",
        margin={"r": 10, "t": 70, "l": 10, "b": 10},
        legend_title_text=color_col.replace("_", " "),
    )
    fig.write_html(out, include_plotlyjs="cdn", full_html=True)
    log(f"Mapa Plotly guardado: {relpath(out)} ({len(df)} puntos)")


def html_escape(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_index(df: pd.DataFrame, generated: list[tuple[str, str, int]]) -> None:
    counts = pd.read_csv(TABLE_DIR / "conteo_universos.csv") if (TABLE_DIR / "conteo_universos.csv").exists() else pd.DataFrame()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    rows = "\n".join(f"<tr><td>{html_escape(r['universo'])}</td><td>{html_escape(r['registros'])}</td></tr>" for _, r in counts.iterrows())
    links = "\n".join(f"<li><a href=\"{html_escape(file)}\">{html_escape(title)}</a> ({n} registros)</li>" for file, title, n in generated)
    table_links = [
        "denue_universo_textil_clasificado.csv",
        "denue_universo_textil_depurado.csv",
        "denue_universo_alcance_proyecto.csv",
        "denue_estudio_prioritario.csv",
        "denue_pendientes_auditoria.csv",
        "localidades/denue_universo_alcance_huejotzingo.csv",
        "localidades/denue_universo_alcance_xalmimilulco.csv",
        "localidades/denue_universo_alcance_san_martin.csv",
        "control_calidad_clasificacion.csv",
    ]
    table_list = "\n".join(f"<li>../../tables/denue_clasificacion_productiva/{name}</li>" for name in table_links)
    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Clasificacion productiva DENUE</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #222; }}
    table {{ border-collapse: collapse; margin: 16px 0; }}
    td, th {{ border: 1px solid #ccc; padding: 6px 10px; }}
    th {{ background: #eef4f8; }}
    .note {{ background: #fff8dc; padding: 12px; border-left: 4px solid #d8a100; max-width: 900px; }}
  </style>
</head>
<body>
  <h1>Clasificacion productiva DENUE textil</h1>
  <p>Indice de mapas interactivos Plotly para explorar establecimientos textiles detectados en la zona alta del Atoyac.</p>
  <p class="note">La clasificacion representa prioridad de investigacion basada en actividad declarada, senales textuales y ubicacion. No constituye evidencia de descarga ni contaminacion atribuible al establecimiento.</p>
  <h2>Universos</h2>
  <table><tr><th>Universo</th><th>Registros</th></tr>{rows}</table>
  <p><b>Fecha de generacion:</b> {datetime.now().isoformat(timespec="seconds")}<br>
  <b>Commit actual:</b> {html_escape(commit.stdout.strip() if commit.returncode == 0 else "")}</p>
  <h2>Mapas HTML</h2>
  <ul>{links}</ul>
  <h2>Tablas principales</h2>
  <ul>{table_list}</ul>
  <h2>Descripcion breve</h2>
  <p>Universo A conserva todos los registros textiles iniciales. Universo B excluye comercio, renta y confeccion especializada de baja relevancia. Universo C es el alcance operativo del proyecto: procesos humedos, lavado/deslavado o mezclilla/jeans. Universo D contiene los establecimientos prioritarios para investigacion. Universo E conserva los registros que requieren auditoria documental o validacion.</p>
</body>
</html>
"""
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    log(f"Indice HTML guardado: {relpath(OUT_DIR / 'index.html')}")


def main() -> None:
    ensure_output_dirs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_points()
    generated = []
    for filename, title, mask_func, color_col in MAP_SPECS:
        subset = df.loc[mask_func(df)].copy()
        write_plot(subset, filename, title, color_col)
        generated.append((filename, title, len(subset)))
    for localidad, slug in LOCALITY_SLUGS.items():
        local = df.loc[df["localidad"].eq(localidad)].copy()
        for label, title, mask_func, color_col in LOCALITY_MAP_SPECS:
            subset = local.loc[mask_func(local)].copy()
            filename = f"localidades/{slug}_{label}.html"
            write_plot(subset, filename, f"{title} - {localidad}", color_col)
            generated.append((filename, f"{title} - {localidad}", len(subset)))
    write_index(df, generated)


if __name__ == "__main__":
    main()
