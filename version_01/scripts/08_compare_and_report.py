from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from version_01.scripts.common import PROJECT_ROOT, normalize_text, safe_to_file


CONFIG_DIR = PROJECT_ROOT / "config" / "filtros_textiles_santa_ana" / "versiones" / "v1"
CLASS_DIR = PROJECT_ROOT / "outputs" / "universo_independiente_3_localidades"
REFINE_DIR = PROJECT_ROOT / "outputs" / "universo_refinado_santa_ana"
AUDITED_DIR = PROJECT_ROOT / "outputs" / "auditoria_6_especiales"
OUT_DIR = PROJECT_ROOT / "outputs" / "comparacion_3_localidades"
INCLUDED = AUDITED_DIR / "capas_qgis" / "universo_productivo_auditado.gpkg"
REVIEW = CLASS_DIR / "capas_qgis" / "universo_independiente_revision.gpkg"
MANIFEST = CLASS_DIR / "manifest_clasificacion.json"
REFINE_MANIFEST = AUDITED_DIR / "manifest_auditoria_6.json"
DENUE_2026_SOURCE = PROJECT_ROOT / "data" / "raw" / "denue2026" / "Denue26 area estudio.shp"


def normalize_id(series: pd.Series) -> pd.Series:
    return (
        series.fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
        .str.strip().str.upper()
    )


def bool_value(value: object) -> bool:
    return normalize_text(value) in {"true", "1", "si", "sí", "yes"}


def load_references(target_crs) -> tuple[dict[str, gpd.GeoDataFrame], pd.DataFrame]:
    cfg = pd.read_csv(CONFIG_DIR / "referencias_comparacion.csv", dtype=str).fillna("")
    cfg = cfg[cfg["activa"].map(bool_value)]
    references = {}
    audit = []
    for _, row in cfg.iterrows():
        path = PROJECT_ROOT / row["ruta"]
        if not path.exists():
            audit.append({**row.to_dict(), "estado": "NO_DISPONIBLE", "registros": 0})
            continue
        frame = gpd.read_file(path, engine="pyogrio")
        if row["filtro_columna"]:
            desired = row["filtro_valor"]
            if desired.lower() in {"true", "false"}:
                mask = frame[row["filtro_columna"]].map(bool_value).eq(bool_value(desired))
            else:
                mask = frame[row["filtro_columna"]].astype(str).eq(desired)
            frame = frame.loc[mask].copy()
        frame = frame.to_crs(target_crs)
        frame["_id_key"] = normalize_id(frame[row["campo_id"]])
        frame = frame.loc[frame["_id_key"].ne("")].drop_duplicates("_id_key").copy()
        frame["localidad_id_analisis"] = row["localidad_id"]
        references[row["referencia_id"]] = frame
        audit.append({**row.to_dict(), "estado": "DISPONIBLE", "registros": len(frame)})
    return references, pd.DataFrame(audit)


def build_comparison(
    included: gpd.GeoDataFrame, references: dict[str, gpd.GeoDataFrame]
) -> gpd.GeoDataFrame:
    base = included.copy()
    base["_id_key"] = normalize_id(base["id"])
    base["en_universo_independiente"] = True
    keep = [
        "_id_key", "id", "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian", "localidad_id_analisis",
        "localidad_analisis", "decision_clasificacion", "categoria_clasificacion",
        "regla_decisiva", "explicacion_decision", "en_universo_independiente",
        "regla_refinamiento", "decision_refinada", "prioridad_refinada",
        "motivo_refinamiento",
        "geometry",
    ]
    base = base[[column for column in keep if column in base.columns]]
    seen = set(base["_id_key"])
    pieces = [base]
    for reference_id, frame in references.items():
        new = frame.loc[~frame["_id_key"].isin(seen)].copy()
        if new.empty:
            continue
        new["en_universo_independiente"] = False
        new["localidad_analisis"] = new["localidad_id_analisis"]
        new["id"] = new["_id_key"]
        new["nombre_de_la_unidad_economica"] = next(
            (new[c] for c in ["nombre_de_la_unidad_economica", "Name", "nom_estab"] if c in new),
            pd.Series("", index=new.index),
        )
        pieces.append(new[[column for column in base.columns if column in new.columns]])
        seen.update(new["_id_key"])
    combined = gpd.GeoDataFrame(
        pd.concat(pieces, ignore_index=True), geometry="geometry", crs=included.crs
    )
    for reference_id, frame in references.items():
        combined[f"en_{reference_id}"] = combined["_id_key"].isin(set(frame["_id_key"]))
    for reference_id in ["mh_filtrado", "canonico_original"]:
        column = f"en_{reference_id}"
        if column not in combined:
            combined[column] = False

    has_reference = combined["localidad_id_analisis"].eq("santa_ana_xalmimilulco")
    signature = (
        combined["en_universo_independiente"].astype(int).astype(str)
        + combined["en_mh_filtrado"].astype(int).astype(str)
        + combined["en_canonico_original"].astype(int).astype(str)
    )
    labels = {
        "111": "en_los_tres", "110": "independiente_y_mh",
        "101": "independiente_y_canonico", "100": "solo_independiente",
        "011": "mh_y_canonico", "010": "solo_mh", "001": "solo_canonico",
    }
    combined["perfil_comparacion"] = signature.map(labels).fillna("sin_membresia")
    combined.loc[~has_reference, "perfil_comparacion"] = "sin_referencia_disponible"
    return combined


def save_map(frame: gpd.GeoDataFrame) -> None:
    OUT_DIR.joinpath("mapas").mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13, 9))
    categories = sorted(frame["localidad_id_analisis"].dropna().unique())
    colors = ["#2b8cbe", "#31a354", "#756bb1"]
    for category, color in zip(categories, colors):
        part = frame[frame["localidad_id_analisis"].eq(category)]
        part.plot(ax=ax, color=color, markersize=8, alpha=.7, label=category)
    ax.set_title("Universo textil independiente incluido — tres localidades")
    ax.set_axis_off()
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "mapas" / "universo_independiente_3_localidades.png", dpi=180)
    plt.close(fig)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_Sin registros._"
    headers = list(frame.columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in headers) + " |")
    return "\n".join(lines)


def audit_reference_differences(comparison: gpd.GeoDataFrame) -> pd.DataFrame:
    refined_trace = pd.read_csv(REFINE_DIR / "tablas" / "refinamiento_completo.csv", dtype=str).fillna("")
    stage1_trace = pd.read_csv(CLASS_DIR / "tablas" / "clasificacion_completa.csv", dtype=str).fillna("")
    trace = pd.concat([refined_trace, stage1_trace], ignore_index=True).fillna("")
    trace["_id_key"] = normalize_id(trace["id"])
    raw = gpd.read_file(DENUE_2026_SOURCE, engine="pyogrio")
    raw["_id_key"] = normalize_id(raw["id"])
    raw_lookup = raw.drop_duplicates("_id_key").set_index("_id_key")
    trace_lookup = trace.drop_duplicates("_id_key", keep="first").set_index("_id_key")
    missing = comparison.loc[
        ~comparison["en_universo_independiente"]
        & (comparison["en_mh_filtrado"] | comparison["en_canonico_original"])
    ].copy()
    rows = []
    for _, row in missing.iterrows():
        key = row["_id_key"]
        if key in trace_lookup.index:
            classified = trace_lookup.loc[key]
            if classified.get("decision_refinada", "") != "RETENER":
                reason = (
                    f"{classified['decision_refinada']}: "
                    f"{classified['regla_refinamiento']} / {classified['motivo_refinamiento']}"
                )
            else:
                reason = (
                    f"{classified['decision_clasificacion']}: "
                    f"{classified['categoria_clasificacion']} / {classified['regla_decisiva']}"
                )
            source_status = "clasificado_no_incluido"
            name = classified.get("nombre_de_la_unidad_economica", "")
        elif key in raw_lookup.index:
            source = raw_lookup.loc[key]
            locality = str(source.get("localidad", ""))
            code = str(source.get("cve_loc", ""))
            reason = f"FUERA_AREA: localidad={locality}, cve_loc={code}; Santa Ana usa cve_loc=0029"
            source_status = "fuera_localidad_administrativa"
            name = source.get("nom_estab", "")
        else:
            reason = "AUSENTE_DENUE_2026: el ID de referencia no existe en la fuente DENUE 2026"
            source_status = "ausente_denue_2026"
            name = row.get("nombre_de_la_unidad_economica", "")
        rows.append({
            "id_denue": key,
            "nombre": name,
            "en_mh": bool(row["en_mh_filtrado"]),
            "en_canonico": bool(row["en_canonico_original"]),
            "estado_fuente": source_status,
            "razon_no_inclusion": reason,
        })
    return pd.DataFrame(rows)


def write_report(
    included: gpd.GeoDataFrame,
    review: gpd.GeoDataFrame,
    comparison: gpd.GeoDataFrame,
    reference_audit: pd.DataFrame,
    difference_audit: pd.DataFrame,
) -> None:
    class_summary = (
        pd.concat([included, review])
        .groupby(["localidad_analisis", "decision_clasificacion", "categoria_clasificacion"])
        .size().reset_index(name="registros")
    )
    comparison_summary = (
        comparison.groupby(["localidad_id_analisis", "perfil_comparacion"])
        .size().reset_index(name="registros")
    )
    rules = pd.read_csv(CONFIG_DIR / "reglas_clasificacion.csv")
    decisions = pd.read_csv(CONFIG_DIR / "matriz_decision.csv")
    refinement_policy = pd.read_csv(CONFIG_DIR / "politica_refinamiento.csv")
    refinement_summary = pd.read_csv(REFINE_DIR / "tablas" / "resumen_refinamiento.csv")
    codes = pd.read_csv(CONFIG_DIR / "codigos_scian.csv", dtype=str)
    locations = pd.read_csv(CONFIG_DIR / "localidades.csv")
    validation = pd.read_csv(CLASS_DIR / "tablas" / "validacion_clasificacion.csv")
    text = f"""# Reporte reproducible del universo textil independiente

Fecha de generación: {datetime.now().astimezone().isoformat(timespec="seconds")}

## 1. Objetivo y alcance

El procedimiento identifica establecimientos con señales de actividad textil en las
localidades marcadas como activas en `localidades.csv`. En esta ejecución únicamente está
activa Santa Ana Xalmimilulco. La clasificación representa prioridad
analítica y posible relevancia ambiental; no demuestra descargas ni contaminación.

## 2. Separación metodológica

La clasificación se ejecutó antes de abrir las capas MH y canónica. Su manifiesto declara:
`No se leyó ninguna capa MH ni canónica durante la clasificación.` La comparación de
referencias consume una capa independiente ya materializada y no modifica sus decisiones.

El proceso está dividido en dos etapas. La primera construye el universo productivo amplio.
La segunda lee esa capa sin volver a buscar establecimientos y aplica exclusiones de alcance
y prioridades mediante `politica_refinamiento.csv`.

## 3. Datos y delimitación territorial

Fuente operativa: `data/raw/denue2026/Denue26 area estudio.shp`.

La selección territorial usa el atributo administrativo DENUE `cve_loc=0029`. El polígono
se conserva como referencia cartográfica, pero no elimina registros que DENUE identifica
como Santa Ana. El criterio se controla desde `localidades.csv`:

{markdown_table(locations[["localidad_id", "nombre_salida", "metodo_seleccion", "campo_seleccion", "valor_seleccion", "activa"]])}

Los Encinos (`cve_loc=0093`) se mantiene separado y fuera del universo de Santa Ana. Esta
decisión explica la ausencia del establecimiento 6272576, aunque aparezca en MH.

## 4. Preparación del texto

Se concatenan los campos DENUE disponibles: nombre del establecimiento, razón social y
descripción SCIAN. Se eliminan acentos, se convierte a minúsculas y se normalizan espacios.
Las palabras se buscan como términos o frases completas, con límites alfanuméricos, para
reducir coincidencias parciales accidentales.

## 5. Construcción de candidatos y clasificación

Las reglas se almacenan fuera del código. Los archivos editables son:

- `palabras_clave.csv`: términos, grupos, etapa, evidencia y rol.
- `codigos_scian.csv`: códigos exactos o prefijos y su señal.
- `reglas_clasificacion.csv`: catálogo metodológico.
- `politica_categorias.csv`: categorías, prioridad y decisión.
- `localidades.csv`: polígonos incluidos.
- `referencias_comparacion.csv`: referencias que se abren solo en la comparación.

### Códigos SCIAN

{markdown_table(codes[["code", "match_type", "signal", "process_stage", "evidence_level"]])}

### Reglas

{markdown_table(rules[["rule_id", "stage", "source", "criterion", "interpretation"]])}

### Matriz ejecutable de precedencia

Esta tabla es leída directamente por el clasificador; las decisiones no están fijadas dentro
del script.

{markdown_table(decisions[["priority", "decision_rule", "all_flags", "any_flags", "none_flags", "category", "decision"]].fillna(""))}

### Política de refinamiento

{markdown_table(refinement_policy.fillna(""))}

### Resultado del refinamiento

{markdown_table(refinement_summary)}

## 6. Precedencia de decisión

1. Una exclusión fuerte no textil produce `EXCLUIR`.
2. Comercio o nombre excluido produce `EXCLUIR`, salvo que exista evidencia productiva
   explícita capaz de superar la exclusión condicional.
3. Proceso húmedo textual o SCIAN específico produce `INCLUIR_ALTA`.
4. Producción textil, mezclilla o maquila textil produce `INCLUIR_MEDIA`.
5. Lavado, maquila o señal textil ambigua produce `REVISAR`.
6. Sin evidencia suficiente produce `FUERA`.

La tabla `clasificacion_completa.csv` conserva, registro por registro, texto normalizado,
términos y códigos detectados, reglas activadas, regla decisiva, decisión y explicación.

## 7. Resultados independientes

{markdown_table(class_summary)}

Los registros `REVISAR` no forman parte de la capa incluida. Se entregan en una capa
separada para decisión humana.

## 8. Referencias disponibles

{markdown_table(reference_audit[["referencia_id", "localidad_id", "estado", "registros", "nota"]])}

MH y el canónico disponible corresponden a Santa Ana, la localidad activa en esta ejecución.

## 9. Comparación

{markdown_table(comparison_summary)}

La comparación se realiza por identificador DENUE normalizado. No se usa proximidad espacial
para declarar una coincidencia.

### Razones de referencias no incluidas

{markdown_table(difference_audit)}

Los identificadores 3327188 y 11096797 aparecen en referencias históricas pero no existen
en la fuente DENUE 2026 utilizada. Se documentan como ausencias de fuente y no como errores
del filtro.

## 10. Validaciones

{markdown_table(validation)}

## 11. Archivos de salida

- `outputs/universo_independiente_3_localidades/capas_qgis/`: base, clasificación e incluidos.
- `outputs/universo_independiente_3_localidades/tablas/`: trazabilidad y controles.
- `outputs/universo_independiente_3_localidades/manifest_clasificacion.json`: hashes de entradas.
- `outputs/comparacion_3_localidades/capas_qgis/comparacion_referencias.gpkg`.
- `outputs/comparacion_3_localidades/tablas/comparacion_referencias.csv`.
- `outputs/comparacion_3_localidades/mapas/universo_independiente_3_localidades.png`.

## 12. Limitaciones

DENUE describe unidades registradas y no prueba procesos observados en campo. La clasificación
depende de códigos y descripciones disponibles. La ausencia de un establecimiento no prueba
su inexistencia. Toda modificación metodológica debe crear una nueva versión de los CSV y
volver a ejecutar la clasificación completa.
"""
    (OUT_DIR / "reporte_metodologico.md").write_text(text, encoding="utf-8")


def main() -> None:
    if not MANIFEST.exists() or not REFINE_MANIFEST.exists():
        raise FileNotFoundError("Primero ejecute las etapas 02 y 03 de clasificación y refinamiento")
    included = gpd.read_file(INCLUDED, engine="pyogrio")
    review = gpd.read_file(REVIEW, engine="pyogrio")
    references, reference_audit = load_references(included.crs)
    comparison = build_comparison(included, references)
    OUT_DIR.joinpath("capas_qgis").mkdir(parents=True, exist_ok=True)
    OUT_DIR.joinpath("tablas").mkdir(parents=True, exist_ok=True)
    safe_to_file(comparison, OUT_DIR / "capas_qgis" / "comparacion_referencias.gpkg", "comparacion_referencias")
    pd.DataFrame(comparison.drop(columns="geometry")).to_csv(
        OUT_DIR / "tablas" / "comparacion_referencias.csv", index=False, encoding="utf-8-sig"
    )
    reference_audit.to_csv(OUT_DIR / "tablas" / "fuentes_referencia.csv", index=False, encoding="utf-8-sig")
    difference_audit = audit_reference_differences(comparison)
    difference_audit.to_csv(
        OUT_DIR / "tablas" / "razones_referencias_no_incluidas.csv",
        index=False,
        encoding="utf-8-sig",
    )
    save_map(included)
    write_report(included, review, comparison, reference_audit, difference_audit)
    manifest = {
        "pipeline": "comparacion_referencias_3_localidades",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "classification_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "classification_was_modified": False,
        "comparison_rows": len(comparison),
    }
    (OUT_DIR / "manifest_comparacion.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Comparación terminada: {len(comparison)} registros")


if __name__ == "__main__":
    main()
