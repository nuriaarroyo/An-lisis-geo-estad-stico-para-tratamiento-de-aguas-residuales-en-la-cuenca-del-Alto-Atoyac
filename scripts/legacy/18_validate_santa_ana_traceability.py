from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from common import OUTPUTS_DIR


OUT_DIR = OUTPUTS_DIR / "foco_textil_estricto_santa_ana_2026"
TABLES_DIR = OUT_DIR / "tablas"
FOCUS_CSV = TABLES_DIR / "foco_textil_estricto_santa_ana_2026.csv"
TRACE_CSV = TABLES_DIR / "trazabilidad_filtro_santa_ana_2026.csv"
RULES_CSV = TABLES_DIR / "catalogo_reglas_filtro.csv"
COMPARISON_CSV = TABLES_DIR / "comparacion_directa_4_conjuntos.csv"
CANONICAL_CSV = (
    OUTPUTS_DIR
    / "universo_prioritario_denue"
    / "santa_ana_xalmimilulco"
    / "tabla_universo_prioritario_denue_santa_ana_xalmimilulco.csv"
)
VALIDATION_CSV = TABLES_DIR / "validacion_trazabilidad.csv"

REQUIRED_TRACE_COLUMNS = {
    "_id_key",
    "flag_foco_textil_estricto",
    "decision_filtro_estricto",
    "reglas_inclusion_activadas",
    "reglas_exclusion_activadas",
    "motivo_decision_filtro",
}
REQUIRED_COMPARISON_COLUMNS = {
    "_id_key",
    "en_foco_estricto",
    "en_universo_canonico_original",
    "en_filtrado_2026_santa",
    "en_mh_filtrado",
    "perfil_comparacion",
}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")


def as_bool(series: pd.Series) -> pd.Series:
    return series.str.lower().isin({"true", "1", "yes", "si"})


def id_hash(ids: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()


def check(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {
        "validacion": name,
        "resultado": "OK" if passed else "ERROR",
        "detalle": detail,
    }


def validate() -> pd.DataFrame:
    focus = read_csv(FOCUS_CSV)
    trace = read_csv(TRACE_CSV)
    rules = read_csv(RULES_CSV)
    comparison = read_csv(COMPARISON_CSV)
    canonical = read_csv(CANONICAL_CSV)
    results: list[dict[str, str]] = []

    focus_ids = set(focus["_id_key"]) - {""}
    trace_focus_ids = set(
        trace.loc[trace["decision_filtro_estricto"].eq("incluir"), "_id_key"]
    ) - {""}
    comparison_focus_ids = set(
        comparison.loc[as_bool(comparison["en_foco_estricto"]), "_id_key"]
    ) - {""}
    canonical_ids = set(canonical["id"].str.replace(r"\.0$", "", regex=True).str.strip()) - {""}
    comparison_canonical_ids = set(
        comparison.loc[as_bool(comparison["en_universo_canonico_original"]), "_id_key"]
    ) - {""}

    results.append(
        check(
            "columnas_trazabilidad",
            REQUIRED_TRACE_COLUMNS.issubset(trace.columns),
            f"{len(REQUIRED_TRACE_COLUMNS)} columnas requeridas",
        )
    )
    results.append(
        check(
            "columnas_comparacion",
            REQUIRED_COMPARISON_COLUMNS.issubset(comparison.columns),
            f"{len(REQUIRED_COMPARISON_COLUMNS)} columnas requeridas",
        )
    )
    results.append(
        check(
            "ids_foco_unicos",
            len(focus_ids) == len(focus),
            f"{len(focus_ids)} IDs únicos en {len(focus)} filas",
        )
    )
    results.append(
        check(
            "foco_igual_a_decisiones_incluir",
            focus_ids == trace_focus_ids,
            f"hash={id_hash(focus_ids)}",
        )
    )
    results.append(
        check(
            "foco_igual_a_membresia_comparacion",
            focus_ids == comparison_focus_ids,
            f"{len(comparison_focus_ids)} IDs marcados en comparación",
        )
    )
    results.append(
        check(
            "canonico_original_igual_a_comparacion",
            canonical_ids == comparison_canonical_ids,
            f"{len(canonical_ids)} IDs del universo original",
        )
    )
    results.append(
        check(
            "mh_filtrado_total_en_comparacion",
            int(as_bool(comparison["en_mh_filtrado"]).sum()) == 49,
            f"{int(as_bool(comparison['en_mh_filtrado']).sum())} puntos MH filtrados",
        )
    )
    included_with_exclusion = trace.loc[
        trace["decision_filtro_estricto"].eq("incluir")
        & trace["reglas_exclusion_activadas"].ne("")
    ]
    results.append(
        check(
            "exclusion_tiene_prioridad",
            included_with_exclusion.empty,
            f"{len(included_with_exclusion)} incluidos con regla de exclusión",
        )
    )
    missing_rule_columns = [
        rule_id
        for rule_id in rules["rule_id"]
        if f"regla_{rule_id}" not in trace.columns
    ]
    results.append(
        check(
            "catalogo_corresponde_a_columnas",
            not missing_rule_columns,
            "faltantes=" + (", ".join(missing_rule_columns) or "ninguno"),
        )
    )
    results.append(
        check(
            "ids_comparacion_unicos",
            comparison["_id_key"].ne("").all()
            and not comparison["_id_key"].duplicated().any(),
            f"{len(comparison)} puntos comparables o casos MH sin ID separados",
        )
    )
    return pd.DataFrame(results)


def main() -> None:
    validation = validate()
    validation.to_csv(VALIDATION_CSV, index=False, encoding="utf-8-sig")
    print(validation.to_string(index=False))
    if validation["resultado"].eq("ERROR").any():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
