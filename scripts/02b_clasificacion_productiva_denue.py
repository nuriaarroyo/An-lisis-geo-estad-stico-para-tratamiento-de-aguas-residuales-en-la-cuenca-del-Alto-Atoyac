from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
from openpyxl.styles import Font, PatternFill

from common import PROCESSED_DIR, TABLES_DIR, ensure_output_dirs, log, normalize_text, read_gpkg, relpath, safe_to_file


OUTPUT_DIR = TABLES_DIR / "denue_clasificacion_productiva"
AUDIT_DIR = TABLES_DIR / "auditoria_enriquecida"
RULE_CATALOG_FILE = OUTPUT_DIR / "catalogo_reglas_clasificacion_productiva.csv"
LOCALITY_SLUGS = {
    "Huejotzingo": "huejotzingo",
    "Santa Ana Xalmimilulco": "xalmimilulco",
    "San Martin Texmelucan": "san_martin",
}


RULE_TERMS: dict[str, list[str]] = {
    "lavado_deslavado": [
        "lavado",
        "lavado industrial",
        "deslavado",
        "prelavado",
        "enjuague",
        "stone wash",
        "stonewashed",
        "acid wash",
        "lavado de mezclilla",
        "lavado de jeans",
    ],
    "lavanderia_industrial": [
        "lavanderia",
        "lavanderia industrial",
        "lavanderia de prendas",
        "laundry",
        "clean clothes",
        "lavanderia y tintoreria",
    ],
    "tenido_tintoreria": [
        "tenido",
        "teñido",
        "tinte",
        "tintoreria",
        "tintoreria industrial",
        "teñido de prendas",
        "tenido de prendas",
    ],
    "acabado_tratamiento": [
        "acabado",
        "acabado textil",
        "acabado de prendas",
        "tratamiento",
        "tratamiento textil",
        "tratamiento de prendas",
        "tratamiento especial",
        "tratado",
        "blanqueado",
        "suavizado",
        "pigmentado",
        "decolorado",
        "procesos humedos",
        "procesamiento de ropa",
    ],
    "mezclilla_jeans": [
        "mezclilla",
        "denim",
        "jeans",
        "pantalon jeans",
        "pantalones de mezclilla",
        "prendas de mezclilla",
        "transformacion de mezclilla",
        "deshebrado",
    ],
    "industrial": [
        "industrial",
        "industria",
        "fabrica",
        "fabricacion",
        "maquiladora",
        "produccion",
        "procesamiento",
        "transformacion",
        "manufactura",
        "textilera",
        "corte industrial",
    ],
    "maquila": [
        "maquila",
        "maquiladora",
        "confeccion en serie",
        "ensamble de prendas",
        "taller textil",
        "taller de mezclilla",
    ],
    "confeccion": [
        "confeccion",
        "confecciones",
        "costura",
        "costurera",
        "elaboracion de ropa",
        "fabricacion de ropa",
        "prendas de vestir",
        "ropa",
        "pantalon",
    ],
    "confeccion_especializada": [
        "vestidos de novia",
        "novias",
        "xv años",
        "xv anos",
        "quinceañera",
        "quinceanera",
        "alta costura",
        "diseño de modas",
        "diseno de modas",
        "modista",
        "sastreria",
        "trajes de gala",
        "sobre medida",
        "arreglos de ropa",
        "composturas",
        "costura domestica",
        "uniformes escolares",
        "taller de vestidos",
        "confeccion artesanal",
    ],
    "bordado_estampado": [
        "bordado",
        "bordados",
        "estampado",
        "serigrafia",
        "sublimacion",
        "impresion textil",
    ],
    "comercio": [
        "venta",
        "tienda",
        "boutique",
        "local comercial",
        "accesorios",
        "ropa para dama",
        "ropa para caballero",
        "ropa infantil",
        "mayoreo",
        "menudeo",
        "distribuidora",
        "comercializadora",
        "outlet",
        "bazar",
        "merceria",
        "tienda de novias",
        "zapateria",
        "novedades",
    ],
    "renta": [
        "renta",
        "alquiler",
        "renta de vestidos",
        "renta de trajes",
        "renta de prendas",
        "accesorios para novia",
    ],
    "no_textil": [
        "autolavado",
        "auto lavado",
        "mecanico",
        "mecanica",
        "automotriz",
        "bicicleta",
        "carpinteria",
        "herreria",
        "celulares",
    ],
}

SCIAN_STAGE = {
    "812210": "lavanderia_industrial",
    "313": "fabricacion_textil",
    "314": "fabricacion_textil",
    "315": "confeccion_maquila",
    "323": "estampado_serigrafia",
}

BOOLEAN_COLUMNS = [
    "flag_universo_alcance_proyecto",
    "flag_fuera_alcance_productivo_textil",
    "flag_estudio_prioritario",
    "flag_proceso_humedo_relevante",
    "flag_mezclilla_jeans",
    "flag_lavado_deslavado",
    "flag_tenido_tintoreria",
    "flag_acabado_tratamiento",
    "flag_maquila_productiva",
    "flag_confeccion_especializada_baja_relevancia",
    "flag_comercio_o_renta",
    "flag_requiere_auditoria_manual",
    "flag_prioridad_campo",
    "flag_cercania_hidrografia_250m",
    "flag_senal_industrial",
    "flag_texto_ambiguo",
    "flag_posible_falso_positivo",
    "flag_posible_falso_negativo",
    "tiene_senal_proceso_humedo",
    "tiene_senal_mezclilla_jeans",
    "tiene_senal_lavado_deslavado",
    "tiene_senal_tenido_tintoreria",
    "tiene_senal_acabado_tratamiento",
    "tiene_senal_industrial",
    "tiene_senal_maquila",
    "es_confeccion_especializada",
    "es_comercio_o_renta",
    "requiere_auditoria_manual",
]


def norm_for_match(value: object) -> str:
    text = normalize_text(value)
    text = text.replace("ñ", "n")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def pattern_for(term: str) -> re.Pattern:
    normalized = re.escape(norm_for_match(term)).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){normalized}(?![a-z0-9])")


PATTERNS = {
    family: [(term, pattern_for(term)) for term in terms]
    for family, terms in RULE_TERMS.items()
}


def detect_terms(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for family, patterns in PATTERNS.items():
        matches = [term for term, pattern in patterns if pattern.search(text)]
        out[family] = sorted(set(matches), key=lambda x: (len(x), x))
    return out


def yes(value: bool) -> bool:
    return bool(value)


def source_to_location(source_folder: object) -> tuple[str, str]:
    source = norm_for_match(source_folder)
    if "xalmimilulco" in source:
        return "Santa Ana Xalmimilulco", "Huejotzingo"
    if "san martin" in source or "san_martin" in source:
        return "San Martin Texmelucan", "San Martin Texmelucan"
    if "huejotzingo" in source:
        return "Huejotzingo", "Huejotzingo"
    return str(source_folder or ""), ""


def scian_stage(scian: str) -> tuple[str, str]:
    code = re.sub(r"\D+", "", str(scian or ""))
    if code in SCIAN_STAGE:
        return SCIAN_STAGE[code], f"scian_{code}"
    for prefix, stage in SCIAN_STAGE.items():
        if code.startswith(prefix):
            return stage, f"scian_prefijo_{prefix}"
    return "", ""


def build_search_queries(row: pd.Series, text_category: str) -> tuple[str, str]:
    name = str(row.get("nombre_de_la_unidad_economica", "") or "").strip()
    localidad = str(row.get("localidad", "") or "").strip()
    municipio = str(row.get("municipio", "") or "").strip()
    base_parts = []
    seen = set()
    for value in [name, localidad, municipio, "Puebla"]:
        key = norm_for_match(value)
        if value and key not in seen:
            base_parts.append(value)
            seen.add(key)
    maps = " ".join(base_parts + ["Google Maps"]).strip()
    web_terms = {
        "lavado_deslavado": "lavado deslavado mezclilla jeans",
        "lavanderia_industrial": "lavanderia industrial textil prendas",
        "tenido_tintoreria": "tintoreria tenido textil industrial",
        "acabado_textil": "acabado textil tratamiento prendas",
        "fabricacion_mezclilla": "mezclilla jeans maquila textil",
    }.get(text_category, "textil maquila confeccion lavanderia tintoreria")
    web = " ".join(base_parts + [web_terms]).strip()
    return maps, web


def classify_row(row: pd.Series) -> dict[str, object]:
    name = str(row.get("nombre_de_la_unidad_economica", "") or "")
    activity = str(row.get("texto_busqueda", "") or "")
    scian = str(row.get("codigo_de_la_clase_actividad_scian", row.get("codigo_scian_detectado", "")) or "")
    text = norm_for_match(" ".join([name, activity, scian, str(row.get("palabras_clave_detectadas", "") or "")]))
    found = detect_terms(text)
    stage_from_scian, scian_rule = scian_stage(scian)
    distance = pd.to_numeric(pd.Series([row.get("distancia_hidrografia_m", pd.NA)]), errors="coerce").iloc[0]
    near_250 = pd.notna(distance) and float(distance) <= 250

    has_lavado = bool(found["lavado_deslavado"] or found["lavanderia_industrial"])
    has_tenido = bool(found["tenido_tintoreria"])
    has_acabado = bool(found["acabado_tratamiento"])
    has_mezclilla = bool(found["mezclilla_jeans"])
    has_industrial = bool(found["industrial"])
    has_maquila = bool(found["maquila"])
    has_confeccion = bool(found["confeccion"])
    has_especializada = bool(found["confeccion_especializada"])
    has_commerce = bool(found["comercio"])
    has_renta = bool(found["renta"])
    has_no_textil = bool(found["no_textil"])
    has_bordado_estampado = bool(found["bordado_estampado"])
    process_humedo = has_lavado or has_tenido or has_acabado or stage_from_scian == "lavanderia_industrial"

    rules: list[str] = []
    evidence: list[str] = []
    if scian_rule:
        rules.append(scian_rule)
        evidence.append(f"SCIAN {scian}")
    for family, terms in found.items():
        if terms:
            rules.append(f"texto_{family}")
            evidence.append(f"{family}: {', '.join(terms)}")

    stage = "desconocido"
    secondary: list[str] = []
    pressure = "pendiente"
    decision = "mantener_pendiente"
    confidence = "baja"
    exclusion_reason = ""
    audit_reason: list[str] = []
    priority_reason: list[str] = []

    if has_no_textil and not (process_humedo or has_mezclilla or has_maquila):
        stage = "no_pertinente"
        pressure = "baja"
        decision = "excluir_del_universo_prioritario"
        confidence = "media"
        exclusion_reason = "senal no textil sin senales productivas relevantes"
    elif process_humedo:
        if found["lavado_deslavado"]:
            stage = "lavado_deslavado"
        elif found["lavanderia_industrial"] or stage_from_scian == "lavanderia_industrial":
            stage = "lavanderia_industrial"
        elif has_tenido:
            stage = "tenido_tintoreria"
        elif has_acabado:
            stage = "acabado_textil"
        else:
            stage = "tratamiento_especial_prenda"
        if has_mezclilla:
            secondary.append("fabricacion_mezclilla")
        if has_maquila:
            secondary.append("confeccion_maquila")
        pressure = "alta"
        decision = "incluir_prioritario"
        confidence = "alta" if (found["lavado_deslavado"] or found["tenido_tintoreria"] or found["acabado_tratamiento"]) else "media"
        priority_reason.append("senal compatible con proceso humedo o tratamiento de prendas")
    elif has_mezclilla and (has_maquila or has_industrial or has_confeccion or stage_from_scian == "confeccion_maquila"):
        stage = "fabricacion_mezclilla"
        if has_maquila or stage_from_scian == "confeccion_maquila":
            secondary.append("confeccion_maquila")
        pressure = "media"
        decision = "validar_documentalmente"
        confidence = "media"
        audit_reason.append("mezclilla/jeans sin evidencia directa de proceso humedo")
    elif has_maquila or (stage_from_scian == "confeccion_maquila" and (has_industrial or has_confeccion)):
        stage = "confeccion_maquila"
        pressure = "media"
        decision = "incluir_contexto_productivo"
        confidence = "media"
        audit_reason.append("maquila o confeccion productiva sin senal humeda")
    elif has_bordado_estampado:
        stage = "estampado_serigrafia" if any(t in found["bordado_estampado"] for t in ["estampado", "serigrafia", "sublimacion", "impresion textil"]) else "bordado"
        pressure = "media" if stage == "estampado_serigrafia" else "baja"
        decision = "validar_documentalmente" if stage == "estampado_serigrafia" else "incluir_contexto_productivo"
        confidence = "media"
    elif has_especializada and not (has_industrial or has_maquila or has_mezclilla):
        stage = "confeccion_especializada_baja_relevancia"
        pressure = "baja"
        decision = "excluir_del_universo_prioritario"
        confidence = "alta"
        exclusion_reason = "confeccion especializada o sobre medida sin senales industriales ni humedas"
    elif has_renta and not (has_industrial or has_maquila or has_mezclilla):
        stage = "renta_prendas"
        pressure = "baja"
        decision = "excluir_por_renta"
        confidence = "alta"
        exclusion_reason = "renta o alquiler de prendas sin senales productivas"
    elif has_commerce and not (has_industrial or has_maquila or has_mezclilla):
        stage = "comercio_simple"
        pressure = "baja"
        decision = "excluir_por_comercio"
        confidence = "alta"
        exclusion_reason = "comercio de prendas o accesorios sin senales productivas"
    elif stage_from_scian == "fabricacion_textil":
        stage = "fabricacion_textil"
        pressure = "media"
        decision = "incluir_contexto_productivo"
        confidence = "media"
    elif stage_from_scian == "confeccion_maquila" or has_confeccion:
        stage = "confeccion_maquila" if has_industrial else "revisar"
        pressure = "media" if stage == "confeccion_maquila" else "pendiente"
        decision = "validar_documentalmente" if stage == "confeccion_maquila" else "mantener_pendiente"
        confidence = "baja" if stage == "revisar" else "media"
        audit_reason.append("confeccion generica sin suficiente detalle operativo")
    else:
        stage = "revisar"
        pressure = "pendiente"
        decision = "mantener_pendiente"
        confidence = "baja"
        audit_reason.append("texto insuficiente o ambiguo")

    if stage_from_scian and stage_from_scian != stage and stage_from_scian not in secondary:
        secondary.append(stage_from_scian)

    flag_priority = process_humedo or (
        has_mezclilla and (has_lavado or has_tenido or has_acabado or has_industrial or has_maquila)
    )
    if process_humedo and near_250:
        field_priority = "muy_alta"
        priority_reason.append("proceso humedo o tratamiento y distancia <= 250 m a hidrografia")
    elif process_humedo:
        field_priority = "alta"
        priority_reason.append("proceso humedo o tratamiento")
    elif (stage in {"fabricacion_mezclilla", "confeccion_maquila", "estampado_serigrafia"} or has_mezclilla) and near_250:
        field_priority = "media"
        priority_reason.append("actividad productiva o ambigua cerca de hidrografia")
    elif stage in {"fabricacion_mezclilla", "confeccion_maquila", "fabricacion_textil", "estampado_serigrafia"}:
        field_priority = "media"
        priority_reason.append("contexto productivo textil")
    elif near_250 and stage not in {"comercio_simple", "renta_prendas", "confeccion_especializada_baja_relevancia"}:
        field_priority = "documental"
        priority_reason.append("registro ambiguo cerca de hidrografia")
    else:
        field_priority = "baja"

    text_ambiguous = stage in {"revisar", "desconocido"} or confidence == "baja"
    possible_false_positive = stage in {"comercio_simple", "renta_prendas", "confeccion_especializada_baja_relevancia", "no_pertinente"}
    possible_false_negative = (has_commerce or has_especializada) and (process_humedo or has_mezclilla or has_maquila or has_industrial)
    requires_audit = (
        text_ambiguous
        or confidence == "baja"
        or possible_false_negative
        or (near_250 and stage not in {"comercio_simple", "renta_prendas"})
        or decision in {"validar_documentalmente", "mantener_pendiente"}
    )
    audit_priority = "alta" if (flag_priority or near_250 or possible_false_negative) else ("media" if requires_audit else "baja")
    scope_motives: list[str] = []
    if process_humedo:
        scope_motives.append("senal de proceso humedo o tratamiento")
    if has_lavado:
        scope_motives.append("senal especifica de lavado/deslavado/lavanderia")
    if has_mezclilla:
        scope_motives.append("senal de mezclilla/jeans")
    scope_universe = process_humedo or has_lavado or has_mezclilla
    scope_decision = "dentro_alcance_proyecto" if scope_universe else "fuera_alcance_contexto_textil"

    if flag_priority:
        priority_motive = "; ".join(priority_reason or evidence or ["senal prioritaria"])
        decision = "incluir_prioritario" if process_humedo else decision
    else:
        priority_motive = "sin senales suficientes de proceso humedo, tratamiento, mezclilla prioritaria o maquila relevante"

    if has_commerce and (has_industrial or has_maquila or process_humedo):
        audit_reason.append("senal comercial mezclada con senal productiva")
    if near_250 and not flag_priority:
        audit_reason.append("cercania a hidrografia requiere cautela documental")

    query_maps, query_web = build_search_queries(row, stage)
    keywords = []
    for family in [
        "lavado_deslavado",
        "lavanderia_industrial",
        "tenido_tintoreria",
        "acabado_tratamiento",
        "mezclilla_jeans",
        "industrial",
        "maquila",
        "confeccion_especializada",
        "comercio",
        "renta",
    ]:
        keywords.extend(found[family])

    return {
        "actividad_denue_original": activity,
        "codigo_scian_original": scian,
        "texto_busqueda_normalizado": text,
        "etapa_productiva_sugerida": stage,
        "etapa_productiva_secundaria": "; ".join(sorted(set(secondary))),
        "subtipo_confeccion": "especializada_baja_relevancia" if has_especializada else ("maquila_productiva" if has_maquila else ("generica" if has_confeccion else "")),
        "presion_ambiental_potencial": pressure,
        "confianza_clasificacion": confidence,
        "evidencia_clasificacion": " | ".join(evidence),
        "palabras_clave_etapa": "; ".join(sorted(set(keywords))),
        "reglas_activadas": "; ".join(sorted(set(rules))),
        "tiene_senal_proceso_humedo": process_humedo,
        "tiene_senal_mezclilla_jeans": has_mezclilla,
        "tiene_senal_lavado_deslavado": has_lavado,
        "tiene_senal_tenido_tintoreria": has_tenido,
        "tiene_senal_acabado_tratamiento": has_acabado,
        "tiene_senal_industrial": has_industrial,
        "tiene_senal_maquila": has_maquila,
        "es_confeccion_especializada": has_especializada,
        "es_comercio_o_renta": has_commerce or has_renta,
        "requiere_auditoria_manual": requires_audit,
        "motivo_auditoria": "; ".join(sorted(set(audit_reason))) if requires_audit else "",
        "prioridad_auditoria": audit_priority,
        "prioridad_campo": field_priority,
        "motivo_prioridad_campo": "; ".join(sorted(set(priority_reason))),
        "decision_estudio_sugerida": decision,
        "decision_alcance_proyecto": scope_decision,
        "motivo_exclusion_prioritaria": exclusion_reason,
        "flag_universo_alcance_proyecto": scope_universe,
        "motivo_universo_alcance_proyecto": "; ".join(scope_motives) if scope_motives else "textil fuera del alcance operativo definido para este proyecto",
        "flag_fuera_alcance_productivo_textil": not scope_universe,
        "flag_estudio_prioritario": flag_priority,
        "motivo_flag_estudio_prioritario": priority_motive,
        "flag_proceso_humedo_relevante": process_humedo,
        "flag_mezclilla_jeans": has_mezclilla,
        "flag_lavado_deslavado": has_lavado,
        "flag_tenido_tintoreria": has_tenido,
        "flag_acabado_tratamiento": has_acabado,
        "flag_maquila_productiva": has_maquila or stage == "confeccion_maquila",
        "flag_confeccion_especializada_baja_relevancia": stage == "confeccion_especializada_baja_relevancia",
        "flag_comercio_o_renta": has_commerce or has_renta,
        "flag_requiere_auditoria_manual": requires_audit,
        "flag_prioridad_campo": field_priority in {"muy_alta", "alta", "media", "documental"},
        "flag_cercania_hidrografia_250m": near_250,
        "flag_senal_industrial": has_industrial,
        "flag_texto_ambiguo": text_ambiguous,
        "flag_posible_falso_positivo": possible_false_positive,
        "flag_posible_falso_negativo": possible_false_negative,
        "query_maps": query_maps,
        "query_web": query_web,
        "categoria_auditada": "",
        "etapa_productiva_auditada": "",
        "notas_auditoria": "",
        "fuente_auditoria": "",
        "decision_estudio": "",
        "fecha_auditoria": "",
        "auditor_responsable": "",
    }


def add_classification(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    localidades = out["source_folder"].map(source_to_location)
    out["localidad"] = [loc for loc, _ in localidades]
    out["municipio"] = [mun for _, mun in localidades]
    records = [classify_row(row) for _, row in out.iterrows()]
    classified = pd.DataFrame(records, index=out.index)
    for column in classified.columns:
        out[column] = classified[column]
    for column in BOOLEAN_COLUMNS:
        if column in out.columns:
            out[column] = out[column].fillna(False).astype(bool)
    if "distancia_hidrografia_m" not in out.columns:
        out["distancia_hidrografia_m"] = pd.NA
    if "rango_distancia_hidrografia" not in out.columns:
        out["rango_distancia_hidrografia"] = "sin distancia"
    return out


def tabular(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    return gdf.drop(columns="geometry", errors="ignore").copy()


def universe_tables(classified: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    depurado_mask = ~classified["decision_estudio_sugerida"].isin(
        ["excluir_por_comercio", "excluir_por_renta", "excluir_del_universo_prioritario"]
    )
    return {
        "universo_textil_inicial": classified.copy(),
        "universo_textil_depurado": classified.loc[depurado_mask].copy(),
        "universo_alcance_proyecto": classified.loc[classified["flag_universo_alcance_proyecto"]].copy(),
        "estudio_prioritario": classified.loc[classified["flag_estudio_prioritario"]].copy(),
        "pendientes_auditoria": classified.loc[classified["requiere_auditoria_manual"]].copy(),
    }


def summarize(classified: gpd.GeoDataFrame, universes: dict[str, gpd.GeoDataFrame]) -> dict[str, pd.DataFrame]:
    summaries: dict[str, pd.DataFrame] = {}
    summaries["conteo_universos"] = pd.DataFrame(
        [
            {"universo": "A_textil_inicial", "registros": len(universes["universo_textil_inicial"])},
            {"universo": "B_textil_depurado", "registros": len(universes["universo_textil_depurado"])},
            {"universo": "C_alcance_proyecto_humedos_lavado_mezclilla", "registros": len(universes["universo_alcance_proyecto"])},
            {"universo": "D_ambiental_prioritario", "registros": len(universes["estudio_prioritario"])},
            {"universo": "E_pendiente_auditoria", "registros": len(universes["pendientes_auditoria"])},
        ]
    )
    group_cols = [
        "municipio",
        "localidad",
        "codigo_scian_original",
        "etapa_productiva_sugerida",
        "presion_ambiental_potencial",
        "confianza_clasificacion",
        "prioridad_auditoria",
        "prioridad_campo",
        "rango_distancia_hidrografia",
        "flag_estudio_prioritario",
        "flag_universo_alcance_proyecto",
        "flag_proceso_humedo_relevante",
        "flag_mezclilla_jeans",
        "decision_alcance_proyecto",
        "motivo_exclusion_prioritaria",
    ]
    for col in group_cols:
        if col in classified.columns:
            summaries[f"conteo_por_{col}"] = (
                classified.groupby(col, dropna=False).size().reset_index(name="registros").sort_values("registros", ascending=False)
            )
    summaries["transicion_categoria_inicial"] = (
        classified.groupby(
            ["categoria_relevancia_ambiental", "etapa_productiva_sugerida", "decision_estudio_sugerida"],
            dropna=False,
        )
        .size()
        .reset_index(name="registros")
        .sort_values("registros", ascending=False)
    )
    flag_rows = []
    for col in BOOLEAN_COLUMNS:
        if col in classified.columns:
            flag_rows.append(
                {
                    "flag": col,
                    "verdadero": int(classified[col].astype(bool).sum()),
                    "falso": int((~classified[col].astype(bool)).sum()),
                }
            )
    summaries["conteo_flags_clave"] = pd.DataFrame(flag_rows)
    scope_rows = []
    for localidad in LOCALITY_SLUGS:
        local = classified[classified["localidad"].eq(localidad)]
        scope_rows.extend(
            [
                {"localidad": localidad, "categoria_alcance": "universo_alcance_proyecto", "registros": int(local["flag_universo_alcance_proyecto"].sum())},
                {"localidad": localidad, "categoria_alcance": "procesos_humedos", "registros": int(local["flag_proceso_humedo_relevante"].sum())},
                {"localidad": localidad, "categoria_alcance": "lavado_deslavado", "registros": int(local["flag_lavado_deslavado"].sum())},
                {"localidad": localidad, "categoria_alcance": "mezclilla_jeans", "registros": int(local["flag_mezclilla_jeans"].sum())},
                {"localidad": localidad, "categoria_alcance": "fuera_alcance_contexto_textil", "registros": int(local["flag_fuera_alcance_productivo_textil"].sum())},
            ]
        )
    summaries["conteo_alcance_por_localidad"] = pd.DataFrame(scope_rows)
    sample_groups = []
    sample_specs = {
        "prioritarios": classified["flag_estudio_prioritario"],
        "universo_alcance_proyecto": classified["flag_universo_alcance_proyecto"],
        "excluidos_comercio": classified["decision_estudio_sugerida"].eq("excluir_por_comercio"),
        "excluidos_renta": classified["decision_estudio_sugerida"].eq("excluir_por_renta"),
        "confeccion_especializada": classified["flag_confeccion_especializada_baja_relevancia"],
        "ambiguos_auditar": classified["requiere_auditoria_manual"],
        "procesos_humedos": classified["flag_proceso_humedo_relevante"],
    }
    for label, mask in sample_specs.items():
        sample = tabular(classified.loc[mask]).head(15)
        sample.insert(0, "tipo_ejemplo", label)
        sample_groups.append(sample)
    summaries["ejemplos_representativos"] = pd.concat(sample_groups, ignore_index=True) if sample_groups else pd.DataFrame()
    return summaries


def control_quality(classified: gpd.GeoDataFrame, source_count: int) -> pd.DataFrame:
    rows = []
    rows.append({"validacion": "sin_perdida_registros", "ok": len(classified) == source_count, "detalle": f"{len(classified)} de {source_count}"})
    rows.append({"validacion": "ids_duplicados", "ok": not classified["id"].astype(str).duplicated().any() if "id" in classified.columns else True, "detalle": ""})
    for column in ["etapa_productiva_sugerida", "presion_ambiental_potencial", "confianza_clasificacion", "decision_estudio_sugerida"]:
        empty = int(classified[column].fillna("").astype(str).str.strip().eq("").sum())
        rows.append({"validacion": f"campo_critico_{column}", "ok": empty == 0, "detalle": f"vacios={empty}"})
    priority_without_reason = int(
        classified["flag_estudio_prioritario"].astype(bool)
        .where(classified["motivo_flag_estudio_prioritario"].fillna("").astype(str).str.strip().ne(""), False)
        .eq(False)
        .where(classified["flag_estudio_prioritario"].astype(bool), False)
        .sum()
    )
    rows.append({"validacion": "prioritarios_con_motivo", "ok": priority_without_reason == 0, "detalle": f"sin_motivo={priority_without_reason}"})
    wet_excluded = int(
        (
            classified["flag_proceso_humedo_relevante"]
            & classified["decision_estudio_sugerida"].isin(["excluir_por_comercio", "excluir_por_renta", "excluir_del_universo_prioritario"])
        ).sum()
    )
    rows.append({"validacion": "excluidos_con_senal_humeda", "ok": wet_excluded == 0, "detalle": f"casos={wet_excluded}"})
    commerce_industrial = int((classified["flag_comercio_o_renta"] & classified["flag_senal_industrial"]).sum())
    rows.append({"validacion": "comercio_con_senal_industrial_identificado", "ok": True, "detalle": f"casos_para_revision={commerce_industrial}"})
    near_no_audit = int((classified["flag_cercania_hidrografia_250m"] & ~classified["requiere_auditoria_manual"] & ~classified["flag_estudio_prioritario"]).sum())
    rows.append({"validacion": "cercanos_no_prioritarios_sin_auditoria", "ok": near_no_audit == 0, "detalle": f"casos={near_no_audit}"})
    return pd.DataFrame(rows)


def catalog_rules() -> pd.DataFrame:
    rows = []
    descriptions = {
        "lavado_deslavado": "Senales de lavado, deslavado, prelavado o procesos de agua sobre prendas.",
        "lavanderia_industrial": "Senales de lavanderia o tintoreria de prendas; se considera presion potencial alta por uso de agua.",
        "tenido_tintoreria": "Senales de tenido, tinte o tintoreria.",
        "acabado_tratamiento": "Senales de acabado, tratamiento, blanqueado, suavizado o decolorado.",
        "mezclilla_jeans": "Senales de mezclilla, denim, jeans o pantalon de mezclilla.",
        "industrial": "Senales de escala productiva, industria, fabrica, manufactura o transformacion.",
        "maquila": "Senales de maquila, maquiladora o ensamble/confeccion productiva.",
        "confeccion_especializada": "Senales de modista, novias, sastreria o confeccion sobre medida de baja relevancia ambiental.",
        "comercio": "Senales de venta, tienda, boutique, merceria o comercializacion.",
        "renta": "Senales de renta o alquiler de prendas.",
    }
    for family, terms in RULE_TERMS.items():
        rows.append(
            {
                "familia_regla": family,
                "descripcion": descriptions.get(family, ""),
                "terminos": "; ".join(terms),
            }
        )
    return pd.DataFrame(rows)


def write_csv_outputs(classified: gpd.GeoDataFrame, universes: dict[str, gpd.GeoDataFrame], summaries: dict[str, pd.DataFrame], qc: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "universo_textil_inicial": OUTPUT_DIR / "denue_universo_textil_clasificado.csv",
        "universo_textil_depurado": OUTPUT_DIR / "denue_universo_textil_depurado.csv",
        "estudio_prioritario": OUTPUT_DIR / "denue_estudio_prioritario.csv",
        "universo_alcance_proyecto": OUTPUT_DIR / "denue_universo_alcance_proyecto.csv",
        "pendientes_auditoria": OUTPUT_DIR / "denue_pendientes_auditoria.csv",
    }
    for key, path in paths.items():
        tabular(universes[key]).to_csv(path, index=False, encoding="utf-8-sig")
    locality_dir = OUTPUT_DIR / "localidades"
    locality_dir.mkdir(parents=True, exist_ok=True)
    scope = universes["universo_alcance_proyecto"]
    for localidad, slug in LOCALITY_SLUGS.items():
        local_scope = scope.loc[scope["localidad"].eq(localidad)]
        tabular(local_scope).to_csv(locality_dir / f"denue_universo_alcance_{slug}.csv", index=False, encoding="utf-8-sig")
        for flag, label in [
            ("flag_proceso_humedo_relevante", "procesos_humedos"),
            ("flag_lavado_deslavado", "lavado_deslavado"),
            ("flag_mezclilla_jeans", "mezclilla_jeans"),
        ]:
            tabular(classified.loc[classified["localidad"].eq(localidad) & classified[flag]]).to_csv(
                locality_dir / f"denue_{label}_{slug}.csv",
                index=False,
                encoding="utf-8-sig",
            )
    for name, df in summaries.items():
        df.to_csv(OUTPUT_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    qc.to_csv(OUTPUT_DIR / "control_calidad_clasificacion.csv", index=False, encoding="utf-8-sig")
    catalog_rules().to_csv(RULE_CATALOG_FILE, index=False, encoding="utf-8-sig")
    safe_to_file(classified, PROCESSED_DIR / "denue_universo_textil_clasificado.gpkg", layer="denue_universo_textil_clasificado")


def audit_sheets(classified: gpd.GeoDataFrame, summaries: dict[str, pd.DataFrame], qc: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df = tabular(classified)
    sheet_cols = [
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_scian_original",
        "actividad_denue_original",
        "texto_busqueda_normalizado",
        "palabras_clave_etapa",
        "reglas_activadas",
        "etapa_productiva_sugerida",
        "etapa_productiva_secundaria",
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
        "latitud",
        "longitud",
        "query_maps",
        "query_web",
        "prioridad_auditoria",
        "prioridad_campo",
        "decision_estudio_sugerida",
        "motivo_auditoria",
        "motivo_prioridad_campo",
        "categoria_auditada",
        "etapa_productiva_auditada",
        "notas_auditoria",
        "fuente_auditoria",
        "decision_estudio",
        "fecha_auditoria",
        "auditor_responsable",
    ]
    df = df[[c for c in sheet_cols if c in df.columns]]
    instructions = pd.DataFrame(
        [
            {"campo": "categoria_auditada", "como_llenar": "Usar alta, media, baja, excluir, pendiente o revisar segun evidencia documental."},
            {"campo": "etapa_productiva_auditada", "como_llenar": "Confirmar o corregir la etapa sugerida: lavado_deslavado, tenido_tintoreria, acabado_textil, confeccion_maquila, comercio_simple, etc."},
            {"campo": "notas_auditoria", "como_llenar": "Registrar evidencia breve: nombre en Maps, actividad visible, pagina web, padron, visita o razon de incertidumbre."},
            {"campo": "fuente_auditoria", "como_llenar": "DENUE, Google Maps, busqueda web, padron municipal, directorio, foto, visita de campo u otra fuente."},
            {"campo": "decision_estudio", "como_llenar": "incluir_prioritario, incluir_contexto_productivo, excluir_por_comercio, excluir_por_renta, mantener_pendiente, validar_en_campo."},
            {"campo": "fecha_auditoria", "como_llenar": "Fecha en formato AAAA-MM-DD."},
            {"campo": "auditor_responsable", "como_llenar": "Nombre o iniciales de quien reviso."},
        ]
    )
    possible_dups = df[df.duplicated(subset=["nombre_de_la_unidad_economica", "localidad"], keep=False)] if {"nombre_de_la_unidad_economica", "localidad"}.issubset(df.columns) else df.iloc[0:0]
    return {
        "todos_clasificados": df,
        "resumen_control_calidad": pd.concat([qc, pd.DataFrame([{}]), summaries["conteo_universos"]], ignore_index=True),
        "universo_alcance_proyecto": df[df["flag_universo_alcance_proyecto"].astype(bool)],
        "alcance_huejotzingo": df[df["flag_universo_alcance_proyecto"].astype(bool) & df["localidad"].eq("Huejotzingo")],
        "alcance_xalmimilulco": df[df["flag_universo_alcance_proyecto"].astype(bool) & df["localidad"].eq("Santa Ana Xalmimilulco")],
        "alcance_san_martin": df[df["flag_universo_alcance_proyecto"].astype(bool) & df["localidad"].eq("San Martin Texmelucan")],
        "universo_prioritario": df[df["flag_estudio_prioritario"].astype(bool)],
        "procesos_humedos": df[df["presion_ambiental_potencial"].eq("alta")],
        "mezclilla_jeans": df[df["palabras_clave_etapa"].fillna("").str.contains("mezclilla|jeans|denim", case=False, na=False)],
        "auditoria_obligatoria": df[df["prioridad_auditoria"].isin(["alta", "media"])],
        "pendientes": df[df["decision_estudio_sugerida"].isin(["mantener_pendiente", "validar_documentalmente"]) if "decision_estudio_sugerida" in df.columns else df["prioridad_auditoria"].eq("alta")],
        "excluidos_comercio": df[df["etapa_productiva_sugerida"].eq("comercio_simple")],
        "excluidos_confeccion_especializada": df[df["etapa_productiva_sugerida"].eq("confeccion_especializada_baja_relevancia")],
        "cercanos_hidrografia_250m": df[pd.to_numeric(df["distancia_hidrografia_m"], errors="coerce").le(250)],
        "posibles_duplicados": possible_dups,
        "catalogo_reglas": catalog_rules(),
        "instrucciones_auditoria": instructions,
    }


def write_audit_excel(classified: gpd.GeoDataFrame, summaries: dict[str, pd.DataFrame], qc: pd.DataFrame) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIT_DIR / "auditoria_denue_textil_priorizada.xlsx"
    sheets = audit_sheets(classified, summaries, qc)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        workbook = writer.book
        header_fill = PatternFill("solid", fgColor="D9EAF7")
        for worksheet in workbook.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for cell in worksheet[1]:
                cell.font = Font(bold=True)
                cell.fill = header_fill
            for column_cells in worksheet.columns:
                max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 55)
    log(f"Excel de auditoria priorizada guardado: {relpath(path)}")


def write_markdown_report(classified: gpd.GeoDataFrame, summaries: dict[str, pd.DataFrame], qc: pd.DataFrame) -> None:
    counts = summaries["conteo_universos"].set_index("universo")["registros"].to_dict()
    lines = [
        "# Clasificacion productiva DENUE textil",
        "",
        "La clasificacion prioriza establecimientos para investigacion documental o de campo.",
        "No constituye evidencia de descarga, contaminacion ni incumplimiento normativo.",
        "",
        "## Conteos principales",
        "",
        f"- Universo textil inicial: {counts.get('A_textil_inicial', 0)}",
        f"- Universo textil depurado: {counts.get('B_textil_depurado', 0)}",
        f"- Universo de alcance del proyecto (humedos, lavado/deslavado o mezclilla/jeans): {counts.get('C_alcance_proyecto_humedos_lavado_mezclilla', 0)}",
        f"- Universo ambientalmente prioritario: {counts.get('D_ambiental_prioritario', 0)}",
        f"- Universo pendiente de auditoria: {counts.get('E_pendiente_auditoria', 0)}",
        f"- Prioritarios cerca de hidrografia <=250 m: {int((classified['flag_estudio_prioritario'] & classified['flag_cercania_hidrografia_250m']).sum())}",
        "",
        "## Archivos principales",
        "",
        "- `outputs/tables/denue_clasificacion_productiva/denue_universo_textil_clasificado.csv`",
        "- `outputs/tables/denue_clasificacion_productiva/denue_universo_textil_depurado.csv`",
        "- `outputs/tables/denue_clasificacion_productiva/denue_universo_alcance_proyecto.csv`",
        "- `outputs/tables/denue_clasificacion_productiva/denue_estudio_prioritario.csv`",
        "- `outputs/tables/denue_clasificacion_productiva/denue_pendientes_auditoria.csv`",
        "- `outputs/tables/auditoria_enriquecida/auditoria_denue_textil_priorizada.xlsx`",
        "",
        "## Control de calidad",
        "",
    ]
    for _, row in qc.iterrows():
        lines.append(f"- {row['validacion']}: {'OK' if row['ok'] else 'REVISAR'} ({row['detalle']})")
    (OUTPUT_DIR / "reporte_clasificacion_productiva.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = PROCESSED_DIR / "denue_textil_con_distancia.gpkg"
    if not source.exists():
        source = PROCESSED_DIR / "denue_textil.gpkg"
    if not source.exists():
        log("No existe DENUE textil procesado. Ejecuta 02_filter_denue_textil.py y 04_spatial_analysis.py primero.")
        return
    denue = read_gpkg(source)
    classified = add_classification(denue)
    universes = universe_tables(classified)
    summaries = summarize(classified, universes)
    qc = control_quality(classified, len(denue))
    write_csv_outputs(classified, universes, summaries, qc)
    write_audit_excel(classified, summaries, qc)
    write_markdown_report(classified, summaries, qc)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    metadata = pd.DataFrame(
        [
            {
                "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
                "script": Path(__file__).name,
                "git_commit_actual": commit.stdout.strip() if commit.returncode == 0 else "",
                "fuente": relpath(source),
                "registros": len(classified),
            }
        ]
    )
    metadata.to_csv(OUTPUT_DIR / "metadata_clasificacion.csv", index=False, encoding="utf-8-sig")
    log(f"Clasificacion productiva guardada en {relpath(OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
