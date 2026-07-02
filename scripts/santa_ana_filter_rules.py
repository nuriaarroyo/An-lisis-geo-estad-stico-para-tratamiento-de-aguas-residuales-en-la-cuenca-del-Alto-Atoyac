from __future__ import annotations

from dataclasses import asdict, dataclass

import geopandas as gpd
import pandas as pd

from common import normalize_text
from santa_ana_audit_utils import bool_series


LOCALIDAD_OBJETIVO = "Santa Ana Xalmimilulco"


@dataclass(frozen=True)
class FilterRule:
    rule_id: str
    rule_type: str
    source: str
    criterion: str
    interpretation: str


RULES = [
    FilterRule(
        "exc_nombre_no_objetivo",
        "exclusion",
        "nombre_de_la_unidad_economica",
        "planchado, costura, ropa terminada, lavado no textil, insumos, bodega u otro termino no objetivo",
        "Evita que una palabra generica como lavado o taller se interprete como proceso textil relevante.",
    ),
    FilterRule(
        "exc_actividad_no_objetivo",
        "exclusion",
        "nombre_clase_actividad_scian",
        "agua, calzado, bolsas, computadoras o comercio al por mayor",
        "Retira actividades cuyo giro declarado no corresponde al proceso textil estudiado.",
    ),
    FilterRule(
        "exc_decision_previa",
        "exclusion",
        "decision_estudio_sugerida",
        "decision previa de excluir por comercio, renta o del universo prioritario",
        "Respeta las exclusiones explícitas de la clasificación previa.",
    ),
    FilterRule(
        "inc_humedo_flags",
        "inclusion",
        "flags de clasificacion",
        "proceso humedo, lavado/deslavado, tenido/tintoreria o acabado/tratamiento",
        "Señal estructurada de tratamiento o proceso húmedo textil.",
    ),
    FilterRule(
        "inc_humedo_texto",
        "inclusion",
        "nombre, actividad y etapa",
        "lavanderia, lavado, deslavado, stone wash, tintoreria, tenido, acabado o poliproceso",
        "Señal textual explícita de proceso húmedo o acabado.",
    ),
    FilterRule(
        "inc_humedo_etapa_scian",
        "inclusion",
        "etapa_productiva_sugerida y SCIAN",
        "etapa húmeda reconocida o SCIAN 812210/313310",
        "Señal sectorial o de etapa compatible con lavado, tintorería o acabado.",
    ),
    FilterRule(
        "inc_mezclilla_nombre",
        "inclusion",
        "nombre_de_la_unidad_economica",
        "mezclilla, jeans, denim, deshebrado o variantes",
        "Identifica establecimientos vinculados explícitamente con mezclilla o jeans.",
    ),
    FilterRule(
        "inc_mezclilla_etapa",
        "inclusion",
        "etapa_productiva_sugerida",
        "fabricacion_mezclilla",
        "Conserva la señal de mezclilla asignada en la clasificación productiva.",
    ),
    FilterRule(
        "inc_material_textil",
        "inclusion",
        "SCIAN, nombre, actividad y etapa",
        "SCIAN 313 con señal de textil, tela, tejido, hilado o pasamaneria",
        "Incluye producción de material textil, no confección genérica de ropa terminada.",
    ),
]


EXCLUDED_NAME_PATTERN = (
    r"\b(?:"
    r"planch\w*|alta\s+costura|costur\w*|modist\w*|sastrer\w*|sastre\w*|novia\w*|xv|"
    r"vestid\w*|sobre\s+medida|lavadora\w*|autolavad\w*|engrasad\w*|agua\s+potable|"
    r"sosapahue|zapat\w*|calzad\w*|bols\w*|malet\w*|computador\w*|publicidad|"
    r"productos\s+para\s+lavander\w*|bodega\w*|desperdici\w*|servillet\w*|recuerdo\w*|piel"
    r")\b"
)
EXCLUDED_ACTIVITY_PATTERN = (
    r"captaci\w* tratamiento y suministro de agua|calzado|bolsos|maletas|"
    r"computadoras|comercio al por mayor"
)
WET_TEXT_PATTERN = (
    r"\b(?:lavander\w*|lavado\w*|deslav\w*|stone\s*wash|stone\s*lav|"
    r"tintorer\w*|tenid\w*|acab\w*|poliproces\w*)\b"
)
DENIM_PATTERN = r"\b(?:mezclill\w*|mesclill\w*|jean\w*|denim|deshebr\w*|desebr\w*|fosil)\b"
MATERIAL_PATTERN = r"\b(?:textil\w*|tela\w*|tejid\w*|hilad\w*|hilatur\w*|pasamaner\w*)\b"
MATERIAL_EXCLUSION_PATTERN = r"\b(?:servillet\w*|recuerdo\w*|piel)\b"
EXCLUDED_DECISIONS = {
    "excluir_por_comercio",
    "excluir_por_renta",
    "excluir_del_universo_prioritario",
}
WET_STAGES = {
    "lavado_deslavado",
    "lavanderia_industrial",
    "tenido_tintoreria",
    "acabado_textil",
}


def rule_catalog() -> pd.DataFrame:
    return pd.DataFrame(asdict(rule) for rule in RULES)


def _join_active_rules(row: pd.Series, columns: list[str]) -> str:
    active = [column.removeprefix("regla_") for column in columns if bool(row[column])]
    return "; ".join(active)


def _decision_reason(row: pd.Series) -> str:
    if row["reglas_exclusion_activadas"]:
        return f"Exclusion prioritaria: {row['reglas_exclusion_activadas']}"
    if row["reglas_inclusion_activadas"]:
        return f"Inclusion: {row['reglas_inclusion_activadas']}"
    return "Fuera del foco: no activa una señal estricta de inclusión."


def apply_filter_rules(classified: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    santa = classified.loc[
        classified["localidad"].fillna("").astype(str).eq(LOCALIDAD_OBJETIVO)
    ].copy()
    name = santa["nombre_de_la_unidad_economica"].map(normalize_text)
    activity = santa["nombre_clase_actividad_scian"].map(normalize_text)
    stage = santa["etapa_productiva_sugerida"].fillna("").astype(str)
    stage_text = stage.map(normalize_text)
    decision = santa["decision_estudio_sugerida"].fillna("").astype(str)
    scian = (
        santa["codigo_de_la_clase_actividad_scian"]
        .fillna("")
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
        .fillna("")
    )
    relevant_text = name + " " + activity + " " + stage_text

    santa["regla_exc_nombre_no_objetivo"] = name.str.contains(
        EXCLUDED_NAME_PATTERN,
        regex=True,
        na=False,
    )
    santa["regla_exc_actividad_no_objetivo"] = activity.str.contains(
        EXCLUDED_ACTIVITY_PATTERN,
        regex=True,
        na=False,
    )
    santa["regla_exc_decision_previa"] = decision.isin(EXCLUDED_DECISIONS)
    santa["regla_inc_humedo_flags"] = (
        bool_series(santa, "flag_proceso_humedo_relevante")
        | bool_series(santa, "flag_lavado_deslavado")
        | bool_series(santa, "flag_tenido_tintoreria")
        | bool_series(santa, "flag_acabado_tratamiento")
    )
    santa["regla_inc_humedo_texto"] = relevant_text.str.contains(
        WET_TEXT_PATTERN,
        regex=True,
        na=False,
    )
    santa["regla_inc_humedo_etapa_scian"] = stage.isin(WET_STAGES) | scian.isin(
        ["812210", "313310"]
    )
    santa["regla_inc_mezclilla_nombre"] = name.str.contains(
        DENIM_PATTERN,
        regex=True,
        na=False,
    )
    santa["regla_inc_mezclilla_etapa"] = stage.eq("fabricacion_mezclilla")
    santa["regla_inc_material_textil"] = (
        scian.str.startswith("313")
        & relevant_text.str.contains(MATERIAL_PATTERN, regex=True, na=False)
        & ~name.str.contains(MATERIAL_EXCLUSION_PATTERN, regex=True, na=False)
    )

    exclusion_columns = [f"regla_{rule.rule_id}" for rule in RULES if rule.rule_type == "exclusion"]
    inclusion_columns = [f"regla_{rule.rule_id}" for rule in RULES if rule.rule_type == "inclusion"]
    explicit_exclusion = santa[exclusion_columns].any(axis=1)
    wet_signal = santa[
        [
            "regla_inc_humedo_flags",
            "regla_inc_humedo_texto",
            "regla_inc_humedo_etapa_scian",
        ]
    ].any(axis=1)
    denim_signal = santa[
        ["regla_inc_mezclilla_nombre", "regla_inc_mezclilla_etapa"]
    ].any(axis=1)
    material_signal = santa["regla_inc_material_textil"]

    santa["flag_foco_estricto_tratamiento"] = wet_signal & ~explicit_exclusion
    santa["flag_foco_estricto_mezclilla"] = denim_signal & ~explicit_exclusion
    santa["flag_foco_estricto_material_textil"] = material_signal & ~explicit_exclusion
    santa["flag_foco_textil_estricto"] = santa[
        [
            "flag_foco_estricto_tratamiento",
            "flag_foco_estricto_mezclilla",
            "flag_foco_estricto_material_textil",
        ]
    ].any(axis=1)
    santa["reglas_inclusion_activadas"] = santa.apply(
        _join_active_rules,
        axis=1,
        columns=inclusion_columns,
    )
    santa["reglas_exclusion_activadas"] = santa.apply(
        _join_active_rules,
        axis=1,
        columns=exclusion_columns,
    )
    santa["decision_filtro_estricto"] = santa["flag_foco_textil_estricto"].map(
        {True: "incluir", False: "excluir"}
    )
    santa["motivo_decision_filtro"] = santa.apply(_decision_reason, axis=1)

    santa["categoria_foco_estricto"] = "fuera_foco_estricto"
    material = santa["flag_foco_estricto_material_textil"]
    denim = santa["flag_foco_estricto_mezclilla"]
    wet = santa["flag_foco_estricto_tratamiento"]
    santa.loc[material, "categoria_foco_estricto"] = "produccion_material_textil"
    santa.loc[denim, "categoria_foco_estricto"] = "mezclilla_jeans_deshebrado"
    santa.loc[wet, "categoria_foco_estricto"] = "tratamiento_lavado_acabado_textil"
    return santa
