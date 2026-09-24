from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import geopandas as gpd
import pandas as pd

from version_01.scripts.common import clean_dataframe_columns, normalize_text, read_csv_robust


@dataclass(frozen=True)
class Catalogs:
    keywords: pd.DataFrame
    scian: pd.DataFrame
    rules: pd.DataFrame
    categories: pd.DataFrame
    decisions: pd.DataFrame


def load_catalogs(config_dir: Path) -> Catalogs:
    tables = {
        "keywords": read_csv_robust(config_dir / "palabras_clave.csv"),
        "scian": read_csv_robust(config_dir / "codigos_scian.csv", dtype=str),
        "rules": read_csv_robust(config_dir / "reglas_clasificacion.csv"),
        "categories": read_csv_robust(config_dir / "politica_categorias.csv"),
        "decisions": read_csv_robust(config_dir / "matriz_decision.csv"),
    }
    for name, frame in tables.items():
        if frame.empty:
            raise ValueError(f"El catálogo {name} está vacío")
    if tables["keywords"]["keyword_id"].duplicated().any():
        raise ValueError("keyword_id debe ser único")
    if tables["rules"]["rule_id"].duplicated().any():
        raise ValueError("rule_id debe ser único")
    return Catalogs(**tables)


def _tokens(value: object) -> set[str]:
    return {token.strip() for token in str(value).split("|") if token.strip()}


def _phrase_pattern(term: str) -> re.Pattern:
    escaped = re.escape(normalize_text(term)).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


def _match_code(code: str, row: pd.Series) -> bool:
    target = str(row["code"]).strip()
    return code == target if row["match_type"] == "exact" else code.startswith(target)


def _flag_set(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    return _tokens(value)


def _select_decision(flags: dict[str, bool], decisions: pd.DataFrame) -> pd.Series:
    ordered = decisions.sort_values("priority", ascending=False)
    for _, decision in ordered.iterrows():
        required = _flag_set(decision.get("all_flags", ""))
        alternatives = _flag_set(decision.get("any_flags", ""))
        forbidden = _flag_set(decision.get("none_flags", ""))
        if required and not all(flags.get(flag, False) for flag in required):
            continue
        if alternatives and not any(flags.get(flag, False) for flag in alternatives):
            continue
        if forbidden and any(flags.get(flag, False) for flag in forbidden):
            continue
        return decision
    raise ValueError("La matriz de decisión no contiene una regla aplicable")


def classify(gdf: gpd.GeoDataFrame, catalogs: Catalogs, version: str) -> gpd.GeoDataFrame:
    out = clean_dataframe_columns(gdf)
    name_fields = [
        column for column in
        ["nombre_de_la_unidad_economica", "raz_social", "nombre_clase_actividad_scian"]
        if column in out.columns
    ]
    if not name_fields:
        raise ValueError("DENUE no contiene campos textuales utilizables")
    for field in name_fields:
        out[field] = out[field].fillna("").astype(str)
    out["texto_normalizado"] = out[name_fields].agg(" | ".join, axis=1).map(normalize_text)
    code_field = "codigo_de_la_clase_actividad_scian"
    out["codigo_scian_normalizado"] = (
        out.get(code_field, "").fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    )

    keyword_rows = list(catalogs.keywords.to_dict("records"))
    patterns = {row["keyword_id"]: _phrase_pattern(row["term"]) for row in keyword_rows}
    scian_rows = list(catalogs.scian.to_dict("records"))

    records: list[dict[str, object]] = []
    for _, row in out.iterrows():
        text = row["texto_normalizado"]
        code = row["codigo_scian_normalizado"]
        hits = [item for item in keyword_rows if patterns[item["keyword_id"]].search(text)]
        groups = set().union(*(_tokens(item["groups"]) for item in hits)) if hits else set()
        roles = {str(item["classification_role"]) for item in hits}
        code_hits = [item for item in scian_rows if _match_code(code, pd.Series(item))]
        signals = {str(item["signal"]) for item in code_hits}

        strong_exclusion = bool(groups & {"non_textile", "non_textile_wash", "excluded_activity"})
        conditional_exclusion = bool(groups & {"commerce", "excluded_name", "material_exclusion"}) or "commerce" in signals
        wet_text = "wet_specific" in groups
        wet_code = "wet_process" in signals
        textile_code = "textile_manufacturing" in signals
        textile_text = "textile_explicit" in groups
        denim = "denim" in groups
        production = "production" in groups
        maquila = "maquila" in groups
        generic_wash = "wash_generic" in groups or "textile_service" in signals
        generic_terms = {"elaboracion", "industrial", "industria", "fabricacion", "produccion", "manufactura"}
        detected_terms = {normalize_text(item["term"]) for item in hits}
        generic_nontextile_only = (
            bool(detected_terms)
            and detected_terms.issubset(generic_terms)
            and not textile_code
            and "textile_service" not in signals
            and not bool(groups & {"textile_explicit", "denim", "wet_specific", "maquila", "material"})
        )
        service_storage_contradiction = (
            "textile_service" in signals
            and bool({item["term"] for item in hits} & {"bodega", "bodegas", "desperdicio"})
        )
        explicit_positive = wet_text or wet_code or denim or (textile_code and (textile_text or production))
        commerce_overridden = conditional_exclusion and explicit_positive and not strong_exclusion
        flags = {
            "strong_exclusion": strong_exclusion,
            "conditional_exclusion": conditional_exclusion,
            "commerce_overridden": commerce_overridden,
            "wet_text": wet_text,
            "wet_code": wet_code,
            "textile_code": textile_code,
            "textile_text": textile_text,
            "denim": denim,
            "production": production,
            "production_and_textile": production and textile_text,
            "maquila": maquila,
            "generic_wash": generic_wash,
            "service_storage_contradiction": service_storage_contradiction,
            "generic_nontextile_only": generic_nontextile_only,
            "has_alert_role": "alerta" in roles,
        }
        selected = _select_decision(flags, catalogs.decisions)
        category = selected["category"]
        decision = selected["decision"]
        relevance = selected["relevance"]
        decisive = selected["decisive_rule"]

        activated = []
        if textile_code:
            activated.append("base_saic_textil")
        if "textile_service" in signals:
            activated.append("base_servicio_textil")
        if groups & {"candidate_textile", "textile_explicit"}:
            activated.append("base_texto_textil")
        if strong_exclusion:
            activated.append("exc_actividad_no_objetivo")
        if conditional_exclusion:
            activated.append("exc_comercio_o_giro_no_textil")
        if wet_text:
            activated.append("inc_humedo_texto")
        if wet_code:
            activated.append("inc_humedo_scian")
        if denim:
            activated.append("inc_mezclilla_texto")

        evidence = [f"SCIAN:{item['code']}:{item['signal']}" for item in code_hits]
        evidence += [f"{item['keyword_id']}:{item['term']}" for item in hits]
        explanation = (
            f"{decision}: {selected['explanation']}; regla decisiva {decisive}; "
            f"{len(code_hits)} coincidencias SCIAN y {len(hits)} coincidencias textuales."
        )
        records.append({
            "keywords_detectadas": "|".join(item["keyword_id"] for item in hits),
            "terminos_detectados": "|".join(item["term"] for item in hits),
            "grupos_detectados": "|".join(sorted(groups)),
            "codigos_regla_detectados": "|".join(str(item["code"]) for item in code_hits),
            "evidencias_detectadas": "|".join(evidence),
            "reglas_activadas": "|".join(dict.fromkeys(activated)),
            "regla_decisiva": decisive,
            "categoria_clasificacion": category,
            "decision_clasificacion": decision,
            "relevancia_ambiental": relevance,
            "explicacion_decision": explanation,
            "exclusion_fuerte": strong_exclusion,
            "exclusion_condicional": conditional_exclusion,
            "exclusion_condicional_superada": commerce_overridden,
            "version_filtro": version,
        })

    classified = pd.concat([out.reset_index(drop=True), pd.DataFrame(records)], axis=1)
    return gpd.GeoDataFrame(classified, geometry=out.geometry.name, crs=out.crs)
