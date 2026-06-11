from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REQUIRED_AUDIT_COLUMNS = [
    "categoria_auditada",
    "notas_auditoria",
    "fuente_auditoria",
    "query_maps",
    "query_web",
    "keywords_detectadas",
    "criterio_auditoria",
    "criterio_auditoria_sugerido",
    "categoria_sugerida",
    "prioridad_revision",
    "decision_estudio",
]

VALID_CATEGORIA_AUDITADA = {"", "alta", "media", "excluir", "revisar"}

NAME_CANDIDATES = [
    "nom_estab",
    "nombre",
    "nombre_establecimiento",
    "establecimiento",
    "nombre_de_la_unidad_economica",
    "unidad_economica",
]
MUNICIPALITY_CANDIDATES = ["municipio", "nom_mun", "n_municipio", "municipio_nombre"]
LOCALITY_CANDIDATES = ["localidad", "nom_loc", "localidad_nombre", "nom_localidad"]
DISTANCE_CANDIDATES = [
    "dist_hidrografia_m",
    "distancia_hidrografia",
    "distancia_hidrografia_m",
    "dist_rio_m",
    "dist_to_hydro_m",
    "distance_to_hydro",
]

REGION_METADATA = {
    "huejotzingo": {
        "label": "Huejotzingo",
        "localidad": "Huejotzingo",
        "municipio": "Huejotzingo",
        "sheet": "Huejotzingo",
        "filename": "auditoria_revisar_huejotzingo_enriquecida.csv",
    },
    "xalmimilulco": {
        "label": "Santa Ana Xalmimilulco",
        "localidad": "Santa Ana Xalmimilulco",
        "municipio": "Huejotzingo",
        "sheet": "Xalmimilulco",
        "filename": "auditoria_revisar_xalmimilulco_enriquecida.csv",
    },
    "san_martin": {
        "label": "San Martin Texmelucan",
        "localidad": "San Martin Texmelucan",
        "municipio": "San Martin Texmelucan",
        "sheet": "San Martin Texmelucan",
        "filename": "auditoria_revisar_san_martin_enriquecida.csv",
    },
}

HIGH_KEYWORDS = [
    "tenido",
    "tintoreria",
    "lavanderia",
    "lavanderia industrial",
    "lavado",
    "deslavado",
    "acabado",
    "acabado textil",
    "estampado",
    "serigrafia",
    "sublimacion",
    "colorante",
    "tinte",
    "quimicos",
    "solvente",
    "tratamiento",
    "proceso humedo",
    "mezclilla",
    "denim",
    "industrial",
]

MEDIUM_KEYWORDS = [
    "maquila",
    "confeccion",
    "costura",
    "taller",
    "bordado",
    "uniformes",
    "ropa de trabajo",
    "fabricacion",
    "manufactura",
    "prendas",
    "textil",
    "hilado",
    "tejido",
    "corte",
    "ensamble",
]

LOW_KEYWORDS = [
    "boutique",
    "venta de ropa",
    "tienda",
    "comercio",
    "merceria",
    "telas",
    "blancos",
    "novedades",
    "ropa",
    "accesorios",
    "bazar",
    "zapateria",
]

WEB_TERMS_BY_CATEGORY = {
    "alta": "textil mezclilla lavanderia tintoreria acabado",
    "media": "textil maquila confeccion taller",
    "excluir": "ropa tienda comercio",
    "revisar": "textil mezclilla maquila lavanderia tintoreria confeccion taller",
}


def normalize_text(value: object) -> str:
    """Normalize text for matching without changing the source data."""
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalized_column_map(columns: Iterable[object]) -> dict[str, str]:
    out: dict[str, str] = {}
    for column in columns:
        out.setdefault(normalize_text(column).replace(" ", "_"), str(column))
    return out


def find_first_existing_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    """Find a column by flexible normalized-name matching."""
    columns = normalized_column_map(df.columns)
    normalized_candidates = [normalize_text(c).replace(" ", "_") for c in candidates]
    for candidate in normalized_candidates:
        if candidate in columns:
            return columns[candidate]
    for candidate in normalized_candidates:
        for normalized, original in columns.items():
            if candidate in normalized:
                return original
    return None


def ensure_audit_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in REQUIRED_AUDIT_COLUMNS:
        if column not in out.columns:
            out[column] = ""
    return out


def infer_region_from_source_folder(value: object) -> str:
    text = normalize_text(value)
    if "xalmimilulco" in text:
        return "xalmimilulco"
    if "san martin" in text or "san_martin" in text:
        return "san_martin"
    if "huejotzingo" in text:
        return "huejotzingo"
    return ""


def first_nonempty(row: pd.Series, columns: Iterable[str | None]) -> str:
    for column in columns:
        if column and column in row.index:
            value = row[column]
            if not pd.isna(value) and str(value).strip():
                return str(value).strip()
    return ""


def region_value(row: pd.Series, region_id: str, field: str) -> str:
    if region_id in REGION_METADATA:
        return REGION_METADATA[region_id][field]
    return ""


def build_search_query(
    row: pd.Series,
    *,
    query_type: str,
    name_col: str | None,
    municipality_col: str | None,
    locality_col: str | None,
    region_id: str,
    category: str = "revisar",
) -> str:
    name = first_nonempty(row, [name_col])
    locality = first_nonempty(row, [locality_col]) or region_value(row, region_id, "localidad")
    municipality = first_nonempty(row, [municipality_col]) or region_value(row, region_id, "municipio")
    parts = []
    seen = set()
    for part in [name, locality, municipality, "Puebla"]:
        key = normalize_text(part)
        if part and key not in seen:
            parts.append(part)
            seen.add(key)
    if query_type == "maps":
        parts.append("Google Maps")
    else:
        parts.append(WEB_TERMS_BY_CATEGORY.get(category, WEB_TERMS_BY_CATEGORY["revisar"]))
    return " ".join(part for part in parts if part).strip()


def keyword_pattern(keyword: str) -> re.Pattern:
    escaped = re.escape(normalize_text(keyword))
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


KEYWORD_PATTERNS = {
    "alta": [(keyword, keyword_pattern(keyword)) for keyword in HIGH_KEYWORDS],
    "media": [(keyword, keyword_pattern(keyword)) for keyword in MEDIUM_KEYWORDS],
    "baja": [(keyword, keyword_pattern(keyword)) for keyword in LOW_KEYWORDS],
}


def build_relevant_text(row: pd.Series, columns: Iterable[str]) -> str:
    values = []
    for column in columns:
        if column in row.index:
            values.append(str(row[column]))
    return normalize_text(" ".join(values))


def detect_keywords(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {"alta": [], "media": [], "baja": []}
    for family, patterns in KEYWORD_PATTERNS.items():
        for keyword, pattern in patterns:
            if pattern.search(text):
                found[family].append(keyword)
    return found


def flatten_keywords(found: dict[str, list[str]]) -> str:
    parts = []
    labels = {"alta": "alta", "media": "media", "baja": "baja_comercio"}
    for family in ["alta", "media", "baja"]:
        if found.get(family):
            parts.append(f"{labels[family]}: {', '.join(found[family])}")
    return " | ".join(parts)


def suggest_category(found: dict[str, list[str]]) -> str:
    has_high = bool(found.get("alta"))
    has_medium = bool(found.get("media"))
    has_low = bool(found.get("baja"))
    if has_high:
        return "alta"
    if has_medium and not has_high:
        return "media"
    if has_low and not has_high and not has_medium:
        return "excluir"
    return "revisar"


def criterion_for_category(category: str, found: dict[str, list[str]]) -> str:
    if category == "alta":
        return "posible proceso humedo/textil: contiene keywords de lavado, tenido, tintoreria, acabado o insumos quimicos"
    if category == "media":
        return "posible proceso productivo textil sin evidencia humeda/quimica"
    if category == "excluir":
        return "parece comercio simple de prendas o telas"
    if any(found.values()):
        return "hay senales mixtas o insuficientes; requiere revision manual"
    return "sin evidencia suficiente; requiere revision manual"


def suggest_priority(
    category: str,
    distance_value: object,
    *,
    hydro_threshold_m: float,
) -> str:
    distance = pd.to_numeric(pd.Series([distance_value]), errors="coerce").iloc[0]
    near_hydro = pd.notna(distance) and distance <= hydro_threshold_m
    if category == "alta" or near_hydro:
        return "alta"
    if category == "media":
        return "media"
    if category == "excluir":
        return "baja"
    return "manual"


def category_sort_key(category: str) -> int:
    return {"alta": 0, "revisar": 1, "media": 2, "excluir": 3}.get(str(category), 4)


def priority_sort_key(priority: str) -> int:
    return {"alta": 0, "manual": 1, "media": 2, "baja": 3}.get(str(priority), 4)


def prepare_audit_table(
    df: pd.DataFrame,
    *,
    region_id: str,
    hydro_threshold_m: float = 250,
) -> pd.DataFrame:
    original_columns = list(df.columns)
    out = ensure_audit_columns(df)

    name_col = find_first_existing_column(out, NAME_CANDIDATES)
    municipality_col = find_first_existing_column(out, MUNICIPALITY_CANDIDATES)
    locality_col = find_first_existing_column(out, LOCALITY_CANDIDATES)
    distance_col = find_first_existing_column(out, DISTANCE_CANDIDATES)

    text_columns = [
        col
        for col in [
            name_col,
            municipality_col,
            locality_col,
            "razon_social",
            "codigo_de_la_clase_actividad_scian",
            "nombre_clase_actividad_scian",
            "descripcion_scian",
            "palabras_clave_detectadas",
            "source_folder",
        ]
        if col and col in out.columns
    ]

    categories = []
    criteria = []
    keywords = []
    priorities = []
    maps_queries = []
    web_queries = []
    combined_text = []

    for _, row in out.iterrows():
        text = build_relevant_text(row, text_columns)
        found = detect_keywords(text)
        category = suggest_category(found)
        categories.append(category)
        criteria.append(criterion_for_category(category, found))
        keywords.append(flatten_keywords(found))
        priorities.append(
            suggest_priority(
                category,
                row[distance_col] if distance_col else np.nan,
                hydro_threshold_m=hydro_threshold_m,
            )
        )
        maps_queries.append(
            build_search_query(
                row,
                query_type="maps",
                name_col=name_col,
                municipality_col=municipality_col,
                locality_col=locality_col,
                region_id=region_id,
                category=category,
            )
        )
        web_queries.append(
            build_search_query(
                row,
                query_type="web",
                name_col=name_col,
                municipality_col=municipality_col,
                locality_col=locality_col,
                region_id=region_id,
                category=category,
            )
        )
        combined_text.append(text)

    out["keywords_detectadas"] = keywords
    out["criterio_auditoria"] = criteria
    out["criterio_auditoria_sugerido"] = criteria
    out["categoria_sugerida"] = categories
    out["prioridad_revision"] = priorities
    out["query_maps"] = maps_queries
    out["query_web"] = web_queries
    out["texto_auditoria_normalizado"] = combined_text
    out["region_auditoria"] = region_id
    out["localidad_auditoria"] = REGION_METADATA.get(region_id, {}).get("localidad", "")
    out["municipio_auditoria"] = REGION_METADATA.get(region_id, {}).get("municipio", "")
    out["archivo_origen_auditoria"] = REGION_METADATA.get(region_id, {}).get("filename", "")
    out["distancia_hidrografia_auditoria_m"] = (
        pd.to_numeric(out[distance_col], errors="coerce") if distance_col else np.nan
    )
    out["__original_columns"] = ", ".join(original_columns)
    out["__priority_sort"] = out["prioridad_revision"].map(priority_sort_key)
    out["__category_sort"] = out["categoria_sugerida"].map(category_sort_key)
    out = out.sort_values(
        by=["__priority_sort", "distancia_hidrografia_auditoria_m", "__category_sort"],
        ascending=[True, True, True],
        na_position="last",
    ).drop(columns=["__priority_sort", "__category_sort"])
    return out


def load_audit_templates(audit_files: dict[str, Path]) -> dict[str, pd.DataFrame]:
    return {
        region_id: pd.read_csv(path, encoding="utf-8-sig")
        for region_id, path in audit_files.items()
    }


def audit_status_counts(df: pd.DataFrame) -> pd.DataFrame:
    category = df.get("categoria_auditada", pd.Series([""] * len(df), index=df.index))
    notes = df.get("notas_auditoria", pd.Series([""] * len(df), index=df.index))
    normalized_category = category.fillna("").map(lambda x: normalize_text(x))
    has_category = normalized_category.ne("")
    has_notes = notes.fillna("").astype(str).str.strip().ne("")
    return pd.DataFrame(
        [
            {"estado": "total", "registros": len(df)},
            {"estado": "pendientes_categoria", "registros": int((~has_category).sum())},
            {"estado": "auditados_categoria", "registros": int(has_category.sum())},
            {"estado": "con_notas", "registros": int(has_notes.sum())},
        ]
    )


def make_initial_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for region_id, df in tables.items():
        meta = REGION_METADATA.get(region_id, {})
        status = audit_status_counts(df).set_index("estado")["registros"].to_dict()
        rows.append(
            {
                "region": region_id,
                "localidad": meta.get("label", region_id),
                "registros": len(df),
                "columnas": len(df.columns),
                "columnas_disponibles": ", ".join(df.columns),
                "categoria_auditada_vacia": status.get("pendientes_categoria", 0),
                "auditados": status.get("auditados_categoria", 0),
                "con_notas": status.get("con_notas", 0),
            }
        )
    return pd.DataFrame(rows)


def make_audit_summary(
    enriched_tables: dict[str, pd.DataFrame],
    *,
    hydro_threshold_m: float,
) -> dict[str, pd.DataFrame | int]:
    all_df = pd.concat(enriched_tables.values(), ignore_index=True)
    distance = pd.to_numeric(all_df["distancia_hidrografia_auditoria_m"], errors="coerce")
    summary = {
        "total_registros": len(all_df),
        "por_localidad": all_df.groupby("localidad_auditoria", dropna=False).size().reset_index(name="registros"),
        "por_categoria_sugerida": all_df.groupby("categoria_sugerida", dropna=False).size().reset_index(name="registros"),
        "por_prioridad_revision": all_df.groupby("prioridad_revision", dropna=False).size().reset_index(name="registros"),
        "categoria_por_localidad": all_df.pivot_table(
            index="localidad_auditoria",
            columns="categoria_sugerida",
            values="id" if "id" in all_df.columns else all_df.columns[0],
            aggfunc="count",
            fill_value=0,
        ).reset_index(),
        "prioridad_por_localidad": all_df.pivot_table(
            index="localidad_auditoria",
            columns="prioridad_revision",
            values="id" if "id" in all_df.columns else all_df.columns[0],
            aggfunc="count",
            fill_value=0,
        ).reset_index(),
        "posible_alta_relevancia": int((all_df["categoria_sugerida"] == "alta").sum()),
        "cercanos_hidrografia": int((distance <= hydro_threshold_m).sum()),
        "requieren_revision_manual": int((all_df["categoria_sugerida"] == "revisar").sum()),
        "probablemente_excluibles": int((all_df["categoria_sugerida"] == "excluir").sum()),
    }
    return summary


def validate_audit_outputs(
    *,
    original_tables: dict[str, pd.DataFrame],
    enriched_tables: dict[str, pd.DataFrame],
    output_paths: Iterable[Path],
    expected_total: int = 182,
) -> pd.DataFrame:
    rows = []
    all_df = pd.concat(enriched_tables.values(), ignore_index=True)
    category_values = (
        all_df.get("categoria_auditada", pd.Series([""] * len(all_df), index=all_df.index))
        .fillna("")
        .map(normalize_text)
    )
    rows.append(
        {
            "validacion": "categoria_auditada_valores_permitidos",
            "ok": bool(category_values.isin(VALID_CATEGORIA_AUDITADA).all()),
            "detalle": ", ".join(sorted(set(category_values) - VALID_CATEGORIA_AUDITADA)),
        }
    )
    for region_id, original in original_tables.items():
        enriched = enriched_tables[region_id]
        missing = [col for col in original.columns if col not in enriched.columns]
        rows.append(
            {
                "validacion": f"columnas_originales_conservadas_{region_id}",
                "ok": not missing,
                "detalle": ", ".join(missing),
            }
        )
    rows.append(
        {
            "validacion": "total_registros",
            "ok": len(all_df) == expected_total,
            "detalle": f"{len(all_df)} de {expected_total}",
        }
    )
    present_regions = set(enriched_tables)
    expected_regions = {"huejotzingo", "xalmimilulco", "san_martin"}
    rows.append(
        {
            "validacion": "tres_localidades_presentes",
            "ok": expected_regions.issubset(present_regions),
            "detalle": ", ".join(sorted(present_regions)),
        }
    )
    for path in output_paths:
        rows.append(
            {
                "validacion": f"archivo_guardado_{path.name}",
                "ok": path.exists() and path.stat().st_size > 0,
                "detalle": str(path),
            }
        )
    return pd.DataFrame(rows)


def export_audit_outputs(
    enriched_tables: dict[str, pd.DataFrame],
    *,
    output_dir: Path,
    summary: dict[str, pd.DataFrame | int],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    all_df = pd.concat(enriched_tables.values(), ignore_index=True)
    for region_id, df in enriched_tables.items():
        path = output_dir / REGION_METADATA[region_id]["filename"]
        df.to_csv(path, index=False, encoding="utf-8-sig")
        paths[region_id] = path
    all_path = output_dir / "auditoria_revisar_todos_enriquecida.csv"
    all_df.to_csv(all_path, index=False, encoding="utf-8-sig")
    paths["todos_csv"] = all_path

    xlsx_path = output_dir / "auditoria_revisar_todos_enriquecida.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for region_id, df in enriched_tables.items():
            df.to_excel(writer, sheet_name=REGION_METADATA[region_id]["sheet"][:31], index=False)
        all_df.to_excel(writer, sheet_name="Todos", index=False)
        pd.DataFrame(
            [
                {"indicador": "total_registros", "valor": summary["total_registros"]},
                {"indicador": "posible_alta_relevancia", "valor": summary["posible_alta_relevancia"]},
                {"indicador": "cercanos_hidrografia", "valor": summary["cercanos_hidrografia"]},
                {"indicador": "requieren_revision_manual", "valor": summary["requieren_revision_manual"]},
                {"indicador": "probablemente_excluibles", "valor": summary["probablemente_excluibles"]},
            ]
        ).to_excel(writer, sheet_name="Resumen", index=False, startrow=0)
        summary["por_localidad"].to_excel(writer, sheet_name="Resumen", index=False, startrow=8)
        summary["por_categoria_sugerida"].to_excel(writer, sheet_name="Resumen", index=False, startrow=15)
        summary["por_prioridad_revision"].to_excel(writer, sheet_name="Resumen", index=False, startrow=23)

        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for column_cells in worksheet.columns:
                max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 55)
    paths["todos_xlsx"] = xlsx_path
    return paths


def write_markdown_report(
    *,
    path: Path,
    summary: dict[str, pd.DataFrame | int],
    hydro_threshold_m: float,
) -> Path:
    category_counts = dict(
        zip(
            summary["por_categoria_sugerida"]["categoria_sugerida"],
            summary["por_categoria_sugerida"]["registros"],
        )
    )
    lines = [
        "# Reporte de apoyo a auditoria manual DENUE",
        "",
        "Este reporte apoya la auditoria manual de los registros DENUE clasificados como `revisar` dentro del universo textil/mezclilla del diagnostico.",
        "",
        "Las categorias sugeridas son un apoyo operativo y no sustituyen la decision humana documentada en `categoria_auditada` y `notas_auditoria`.",
        "",
        f"La distancia a hidrografia se usa como criterio de priorizacion espacial con umbral de {hydro_threshold_m:g} m; no constituye prueba de contaminacion directa.",
        "",
        "## Resultados procesados",
        "",
        f"- Total de registros procesados: {summary['total_registros']}",
        f"- Sugeridos como alta: {category_counts.get('alta', 0)}",
        f"- Sugeridos como media: {category_counts.get('media', 0)}",
        f"- Sugeridos como excluir: {category_counts.get('excluir', 0)}",
        f"- Sugeridos como revisar: {category_counts.get('revisar', 0)}",
        f"- Registros cercanos a hidrografia: {summary['cercanos_hidrografia']}",
        "",
        "## Siguientes pasos",
        "",
        "1. Revisar manualmente `categoria_auditada`.",
        "2. Llenar `notas_auditoria` con la evidencia o justificacion.",
        "3. Correr `scripts/07_apply_denue_audit.py`.",
        "4. Correr `scripts/08_make_audited_maps.py`.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
