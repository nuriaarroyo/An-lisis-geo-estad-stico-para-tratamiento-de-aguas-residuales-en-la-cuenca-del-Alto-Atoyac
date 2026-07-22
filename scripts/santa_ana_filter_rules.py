from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import PROJECT_ROOT, normalize_text, read_csv_robust


LOCALIDAD_OBJETIVO = "Santa Ana Xalmimilulco"
FILTER_VERSION = "v1"
FILTER_CONFIG_ROOT = PROJECT_ROOT / "config" / "filtros_textiles_santa_ana"
FILTER_CONFIG_DIR = FILTER_CONFIG_ROOT / "versiones" / FILTER_VERSION
KEYWORDS_PATH = FILTER_CONFIG_DIR / "palabras_clave.csv"
SCIAN_PATH = FILTER_CONFIG_DIR / "codigos_scian.csv"
CATEGORY_POLICY_PATH = FILTER_CONFIG_DIR / "politica_categorias.csv"
RULES_PATH = FILTER_CONFIG_DIR / "reglas_clasificacion.csv"

FILTER_CONFIG_PATHS = {
    "diccionario_palabras_clave": KEYWORDS_PATH,
    "catalogo_codigos_scian": SCIAN_PATH,
    "politica_categorias": CATEGORY_POLICY_PATH,
    "catalogo_reglas": RULES_PATH,
}


@dataclass(frozen=True)
class FilterCatalogs:
    keywords: pd.DataFrame
    scian: pd.DataFrame
    categories: pd.DataFrame
    rules: pd.DataFrame

    def terms(self, group: str) -> tuple[str, ...]:
        belongs = self.keywords["groups"].str.split("|").map(lambda groups: group in groups)
        return tuple(self.keywords.loc[belongs, "term_normalized"])

    def scian_codes(self, signal: str, match_type: str) -> tuple[str, ...]:
        selected = self.scian[
            self.scian["signal"].eq(signal) & self.scian["match_type"].eq(match_type)
        ]
        return tuple(selected["code"].astype(str))


def _require_columns(frame: pd.DataFrame, required: set[str], source: Path) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Faltan columnas en {source}: {', '.join(missing)}")


def load_filter_catalogs() -> FilterCatalogs:
    keywords = read_csv_robust(KEYWORDS_PATH, dtype=str).fillna("")
    scian = read_csv_robust(SCIAN_PATH, dtype=str).fillna("")
    categories = read_csv_robust(CATEGORY_POLICY_PATH, dtype=str).fillna("")
    rules = read_csv_robust(RULES_PATH, dtype=str).fillna("")

    _require_columns(
        keywords,
        {
            "keyword_id",
            "term",
            "groups",
            "process_stage",
            "universe",
            "evidence_level",
            "classification_role",
            "notes",
        },
        KEYWORDS_PATH,
    )
    _require_columns(
        scian,
        {
            "code",
            "match_type",
            "signal",
            "process_stage",
            "universe",
            "evidence_level",
            "description",
        },
        SCIAN_PATH,
    )
    _require_columns(
        categories,
        {
            "priority",
            "category",
            "relevance",
            "universe",
            "include_relevant",
            "include_review",
            "reason",
        },
        CATEGORY_POLICY_PATH,
    )
    _require_columns(
        rules,
        {"rule_id", "stage", "source", "criterion", "interpretation"},
        RULES_PATH,
    )

    keywords["term_normalized"] = keywords["term"].map(normalize_text)
    if keywords["keyword_id"].duplicated().any():
        raise ValueError("keyword_id debe ser unico en palabras_clave.csv")
    if keywords["term_normalized"].eq("").any():
        raise ValueError("palabras_clave.csv contiene terminos vacios")
    if rules["rule_id"].duplicated().any():
        raise ValueError("rule_id debe ser unico en reglas_clasificacion.csv")
    if categories["category"].duplicated().any():
        raise ValueError("category debe ser unico en politica_categorias.csv")

    categories["priority"] = pd.to_numeric(categories["priority"], errors="raise")
    for column in ["include_relevant", "include_review"]:
        categories[column] = categories[column].str.lower().map(
            {"true": True, "false": False}
        )
        if categories[column].isna().any():
            raise ValueError(f"{column} solo admite true o false")

    return FilterCatalogs(keywords, scian, categories, rules)


def rule_catalog(catalogs: FilterCatalogs | None = None) -> pd.DataFrame:
    loaded = catalogs or load_filter_catalogs()
    return loaded.rules.copy()


def _contains_any(series: pd.Series, terms: tuple[str, ...]) -> pd.Series:
    if not terms:
        return pd.Series(False, index=series.index)
    return series.map(lambda value: any(_term_in_text(value, term) for term in terms))


def _term_in_text(text: str, term: str) -> bool:
    pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
    return re.search(pattern, text) is not None


def _active_rules(row: pd.Series, columns: list[str]) -> str:
    return "; ".join(column.removeprefix("regla_") for column in columns if bool(row[column]))


def _matching_keyword_rows(text: str, keywords: pd.DataFrame) -> pd.DataFrame:
    return keywords.loc[
        keywords["term_normalized"].map(lambda term: _term_in_text(text, term))
    ]


def _joined_values(matches: pd.DataFrame, column: str) -> str:
    values: set[str] = set()
    for raw_value in matches[column]:
        values.update(value for value in str(raw_value).split("|") if value)
    return "; ".join(sorted(values))


def _add_keyword_trace(
    frame: gpd.GeoDataFrame,
    field_texts: dict[str, pd.Series],
    scian: pd.Series,
    catalogs: FilterCatalogs,
    saic_textile_prefixes: tuple[str, ...],
) -> None:
    matches = [
        _matching_keyword_rows(text, catalogs.keywords)
        for text in frame["texto_normalizado"]
    ]
    frame["keywords_detectadas"] = [
        "; ".join(sorted(set(found["term_normalized"]))) for found in matches
    ]
    frame["grupos_keywords_detectados"] = [
        _joined_values(found, "groups") for found in matches
    ]
    frame["etapas_productivas_detectadas"] = [
        _joined_values(found, "process_stage") for found in matches
    ]
    frame["universos_keywords_detectados"] = [
        _joined_values(found, "universe") for found in matches
    ]
    frame["niveles_evidencia_detectados"] = [
        _joined_values(found, "evidence_level") for found in matches
    ]
    frame["campos_coincidentes"] = [
        "; ".join(
            [
                *[
                    label
                    for label, series in field_texts.items()
                    if not _matching_keyword_rows(series.loc[index], catalogs.keywords).empty
                ],
                *(["scian_saic"] if scian.loc[index].startswith(saic_textile_prefixes) else []),
                *(
                    ["scian_servicio"]
                    if scian.loc[index].startswith(
                        catalogs.scian_codes("textile_service", "prefix")
                    )
                    else []
                ),
            ]
        )
        for index in frame.index
    ]


def apply_filter_rules(
    denue: gpd.GeoDataFrame,
    saic_textile_prefixes: tuple[str, ...],
    catalogs: FilterCatalogs | None = None,
) -> gpd.GeoDataFrame:
    config = catalogs or load_filter_catalogs()
    santa = denue.loc[
        denue["localidad"].fillna("").astype(str).eq(LOCALIDAD_OBJETIVO)
    ].copy()

    name = santa["nombre_de_la_unidad_economica"].map(normalize_text)
    business = santa.get("raz_social", pd.Series("", index=santa.index)).map(normalize_text)
    activity = santa["nombre_clase_actividad_scian"].map(normalize_text)
    search_text = name + " " + business + " " + activity
    santa["texto_normalizado"] = search_text.str.replace(r"\s+", " ", regex=True).str.strip()
    scian = (
        santa["codigo_de_la_clase_actividad_scian"]
        .fillna("")
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
        .fillna("")
    )

    candidate_terms = config.terms("candidate_textile")
    textile_terms = config.terms("textile_explicit")
    maquila_terms = config.terms("maquila")
    wash_terms = config.terms("wash_generic")
    wet_terms = config.terms("wet_specific")
    industrial_terms = config.terms("industrial")
    production_terms = config.terms("production")
    commerce_terms = config.terms("commerce")
    non_textile_terms = config.terms("non_textile")
    non_textile_wash_terms = config.terms("non_textile_wash")
    excluded_name_terms = config.terms("excluded_name")
    excluded_activity_terms = config.terms("excluded_activity")
    denim_terms = config.terms("denim")
    material_terms = config.terms("material")
    material_exclusion_terms = config.terms("material_exclusion")

    service_prefixes = config.scian_codes("textile_service", "prefix")
    commerce_prefixes = config.scian_codes("commerce", "prefix")
    wet_scian_codes = config.scian_codes("wet_process", "exact")

    santa["regla_base_saic_textil"] = scian.str.startswith(saic_textile_prefixes)
    santa["regla_base_servicio_textil"] = scian.str.startswith(service_prefixes)
    santa["regla_base_texto_textil"] = _contains_any(search_text, candidate_terms)
    candidate_signal = santa[
        ["regla_base_saic_textil", "regla_base_servicio_textil", "regla_base_texto_textil"]
    ].any(axis=1)

    has_production = _contains_any(search_text, production_terms)
    has_industrial = _contains_any(search_text, industrial_terms)
    has_commerce = _contains_any(search_text, commerce_terms)
    non_textile = _contains_any(search_text, non_textile_terms) & ~(
        santa["regla_base_saic_textil"] | santa["regla_base_servicio_textil"]
    )
    commerce = scian.str.startswith(commerce_prefixes) | (
        has_commerce & ~(has_production | has_industrial)
    )
    santa["regla_exc_comercio_o_giro_no_textil"] = commerce | non_textile
    santa["flag_candidato_textil"] = candidate_signal & ~santa[
        "regla_exc_comercio_o_giro_no_textil"
    ]

    santa["regla_exc_nombre_no_objetivo"] = _contains_any(
        search_text, excluded_name_terms
    )
    santa["regla_exc_actividad_no_objetivo"] = (
        _contains_any(activity, excluded_activity_terms)
        | scian.str.startswith(commerce_prefixes)
    )
    santa["regla_inc_humedo_texto"] = _contains_any(search_text, wet_terms)
    santa["regla_inc_humedo_scian"] = scian.isin(wet_scian_codes)
    santa["regla_inc_mezclilla_texto"] = _contains_any(search_text, denim_terms)
    santa["regla_inc_material_textil"] = (
        scian.str.startswith("313")
        & _contains_any(search_text, material_terms)
        & ~_contains_any(search_text, material_exclusion_terms)
    )

    has_maquila = _contains_any(search_text, maquila_terms)
    has_wash = _contains_any(search_text, wash_terms)
    lexical_textile = _contains_any(search_text, textile_terms)
    wet_specific = _contains_any(search_text, wet_terms)

    santa["match_textil_explicito"] = lexical_textile | scian.str.startswith(
        saic_textile_prefixes
    )
    santa["match_lavado_no_textil"] = _contains_any(
        search_text, non_textile_wash_terms
    )
    santa["match_lavado_textil"] = (
        wet_specific
        | (has_wash & (lexical_textile | has_industrial))
        | scian.isin(wet_scian_codes)
    ) & ~santa["match_lavado_no_textil"]
    santa["match_produccion_textil"] = (
        scian.str.startswith(saic_textile_prefixes)
        | (has_production & lexical_textile)
    )
    santa["match_maquila_textil"] = has_maquila & lexical_textile
    santa["match_maquila_senal_textil"] = (
        has_maquila
        & (has_production | has_industrial | santa["match_lavado_textil"])
        & ~santa["match_maquila_textil"]
    )
    santa["match_maquila_sola"] = (
        has_maquila
        & ~santa["match_maquila_textil"]
        & ~santa["match_maquila_senal_textil"]
    )

    productive_evidence = (
        santa["match_lavado_textil"]
        | santa["match_produccion_textil"]
        | santa["match_maquila_textil"]
        | santa["match_maquila_senal_textil"]
    )
    santa["match_comercio_excluir"] = (
        scian.str.startswith(commerce_prefixes) | has_commerce
    ) & ~productive_evidence
    santa["match_actividad_no_objetivo"] = (
        santa["regla_exc_nombre_no_objetivo"]
        | santa["regla_exc_actividad_no_objetivo"]
        | non_textile
    ) & ~santa["regla_inc_humedo_texto"]
    generic_wash = (
        has_wash
        & ~santa["match_lavado_textil"]
        & ~santa["match_lavado_no_textil"]
    )

    category_conditions = {
        "fuera_filtro": pd.Series(True, index=santa.index),
        "revisar_textil_ambiguo": santa["match_textil_explicito"] & ~productive_evidence,
        "revisar_lavado_generico": generic_wash,
        "revisar_maquila_sola": santa["match_maquila_sola"],
        "revisar_maquila_senal_textil": santa["match_maquila_senal_textil"],
        "produccion_textil": santa["match_produccion_textil"],
        "maquila_textil": santa["match_maquila_textil"],
        "lavado_acabado_textil": santa["match_lavado_textil"],
        "excluir_actividad_no_objetivo": santa["match_actividad_no_objetivo"],
        "excluir_lavado_no_textil": santa["match_lavado_no_textil"],
        "excluir_comercio": santa["match_comercio_excluir"],
    }
    policy_categories = set(config.categories["category"])
    missing_policy = sorted(set(category_conditions) - policy_categories)
    if missing_policy:
        raise ValueError(
            "Faltan categorias en politica_categorias.csv: " + ", ".join(missing_policy)
        )

    santa["categoria_filtro"] = "fuera_filtro"
    for category in config.categories.sort_values("priority")["category"]:
        condition = category_conditions.get(category)
        if condition is not None:
            santa.loc[condition, "categoria_filtro"] = category

    protected_exclusions = {"excluir_comercio", "excluir_lavado_no_textil"}
    outside_candidate = ~santa["flag_candidato_textil"] & ~santa[
        "categoria_filtro"
    ].isin(protected_exclusions)
    santa.loc[outside_candidate, "categoria_filtro"] = "fuera_filtro"

    policy = config.categories.set_index("category")
    santa["relevancia_ambiental"] = santa["categoria_filtro"].map(policy["relevance"])
    santa["universo_filtro"] = santa["categoria_filtro"].map(policy["universe"])
    santa["flag_nuevo_relevante"] = santa["categoria_filtro"].map(
        policy["include_relevant"]
    )
    santa["flag_nuevo_revisar"] = santa["categoria_filtro"].map(
        policy["include_review"]
    )
    santa["motivo_clasificacion"] = santa["categoria_filtro"].map(policy["reason"])

    _add_keyword_trace(
        santa,
        {
            "nombre_unidad": name,
            "razon_social": business,
            "actividad_denue": activity,
        },
        scian,
        config,
        saic_textile_prefixes,
    )

    candidate_columns = [
        "regla_base_saic_textil",
        "regla_base_servicio_textil",
        "regla_base_texto_textil",
    ]
    inclusion_columns = [
        "regla_inc_humedo_texto",
        "regla_inc_humedo_scian",
        "regla_inc_mezclilla_texto",
        "regla_inc_material_textil",
    ]
    exclusion_columns = [
        "regla_exc_comercio_o_giro_no_textil",
        "regla_exc_nombre_no_objetivo",
        "regla_exc_actividad_no_objetivo",
    ]
    santa["flag_foco_estricto_tratamiento"] = santa["match_lavado_textil"]
    santa["flag_foco_estricto_mezclilla"] = (
        santa["match_maquila_textil"] & santa["regla_inc_mezclilla_texto"]
    )
    santa["flag_foco_estricto_material_textil"] = santa["match_produccion_textil"]
    santa["flag_foco_textil_estricto"] = santa["flag_nuevo_relevante"]
    santa["reglas_candidato_activadas"] = santa.apply(
        _active_rules, axis=1, columns=candidate_columns
    )
    santa["reglas_inclusion_activadas"] = santa.apply(
        _active_rules, axis=1, columns=inclusion_columns
    )
    santa["reglas_exclusion_activadas"] = santa.apply(
        _active_rules, axis=1, columns=exclusion_columns
    )
    santa["decision_filtro_estricto"] = santa["categoria_filtro"]
    santa["motivo_decision_filtro"] = santa["motivo_clasificacion"]
    santa["categoria_foco_estricto"] = santa["categoria_filtro"]
    return santa
