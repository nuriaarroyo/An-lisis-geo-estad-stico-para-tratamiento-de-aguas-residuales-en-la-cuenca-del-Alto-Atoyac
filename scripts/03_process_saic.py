from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd

from common import RAW_DIR, TABLES_DIR, clean_dataframe_columns, ensure_output_dirs, log, normalize_text, read_csv_robust, relpath


VARIABLE_ALIASES = {
    "ue": ["ue", "unidades_economicas"],
    "h001a": ["h001a", "personal_ocupado_total"],
    "h020a": ["h020a", "personas_propietarias_familiares"],
    "h010a": ["h010a", "personal_remunerado_total"],
    "k000a": ["k000a", "gastos"],
    "m000a": ["m000a", "ingresos"],
    "a111a": ["a111a", "produccion_bruta_total"],
    "a131a": ["a131a", "valor_agregado_censal_bruto"],
    "m700a": ["m700a", "ingresos_por_maquilar"],
}


def find_saic_csv() -> Path:
    files = sorted((RAW_DIR / "saic").glob("*.csv"))
    if not files:
        raise FileNotFoundError("No se encontro CSV en data/raw/saic")
    return files[0]


def read_saic(path: Path) -> pd.DataFrame:
    df = read_csv_robust(path, skiprows=4)
    df = clean_dataframe_columns(df)
    df = df.loc[:, ~df.columns.str.startswith("unnamed")]
    df = df.replace("\x00", "", regex=True)
    if "ano_censal" in df.columns:
        df = df[pd.to_numeric(df["ano_censal"], errors="coerce").notna()].copy()
    df = df.dropna(how="all")
    return df


def detect_variables(df: pd.DataFrame) -> dict[str, str]:
    detected = {}
    for canonical, aliases in VARIABLE_ALIASES.items():
        for col in df.columns:
            ncol = normalize_text(col)
            if any(alias in ncol for alias in aliases):
                detected[canonical] = col
                break
    return detected


def to_numeric_series(df: pd.DataFrame, col: str | None) -> pd.Series:
    if col is None or col not in df.columns:
        return pd.Series(np.nan, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace({0: np.nan})
    return numerator / denominator


def split_code_name(value: object) -> tuple[str, str]:
    text = "" if pd.isna(value) else str(value)
    parts = text.split(" ", 1)
    if parts and parts[0].isdigit():
        return parts[0], parts[1] if len(parts) > 1 else ""
    match = re.search(r"\b(\d{3,6})\b", text)
    if match:
        code = match.group(1)
        name = re.sub(r"^\D*" + re.escape(code), "", text, count=1).strip(" -:")
        return code, name or text
    return "", text


def main() -> None:
    ensure_output_dirs()
    path = find_saic_csv()
    log(f"Leyendo SAIC: {relpath(path)}")
    df = read_saic(path)
    detected = detect_variables(df)
    pd.DataFrame([{"variable": k, "columna_detectada": v} for k, v in detected.items()]).to_csv(
        TABLES_DIR / "saic_columnas_detectadas.csv", index=False, encoding="utf-8-sig"
    )

    for canonical in VARIABLE_ALIASES:
        df[canonical] = to_numeric_series(df, detected.get(canonical))

    if "municipio" in df.columns:
        split = df["municipio"].map(split_code_name)
        df["municipio_clave"] = split.map(lambda x: x[0])
        df["municipio_nombre"] = split.map(lambda x: x[1] or x[0])
    else:
        df["municipio_clave"] = ""
        df["municipio_nombre"] = "Puebla total"
    df["municipio_nombre"] = df["municipio_nombre"].replace("", "Puebla total").fillna("Puebla total")

    if "actividad_economica" in df.columns:
        split = df["actividad_economica"].map(split_code_name)
        df["actividad_codigo"] = split.map(lambda x: x[0])
        df["actividad_nombre"] = split.map(lambda x: x[1] or x[0])
    else:
        df["actividad_codigo"] = ""
        df["actividad_nombre"] = ""

    df["personal_promedio"] = safe_divide(df.get("h001a"), df.get("ue"))
    df["proporcion_familiar"] = safe_divide(df.get("h020a"), df.get("h001a"))
    df["proporcion_remunerado"] = safe_divide(df.get("h010a"), df.get("h001a"))
    df["ingresos_por_ue"] = safe_divide(df.get("m000a"), df.get("ue"))
    df["produccion_por_ue"] = safe_divide(df.get("a111a"), df.get("ue"))
    df["valor_agregado_por_ue"] = safe_divide(df.get("a131a"), df.get("ue"))
    df["maquila_sobre_ingresos"] = safe_divide(df.get("m700a"), df.get("m000a"))
    df["nota_metodologica"] = "SAIC a nivel municipal/entidad; Xalmimilulco se analiza espacialmente con DENUE."

    df.to_csv(TABLES_DIR / "saic_limpio.csv", index=False, encoding="utf-8-sig")
    df.to_csv(TABLES_DIR / "saic_indicadores.csv", index=False, encoding="utf-8-sig")

    group_cols = ["municipio_nombre", "actividad_codigo", "actividad_nombre"]
    sums = ["ue", "h001a", "h020a", "h010a", "k000a", "m000a", "a111a", "a131a", "m700a"]
    resumen = df.groupby(group_cols, dropna=False)[[c for c in sums if c in df.columns]].sum(min_count=1).reset_index()
    resumen["personal_promedio"] = safe_divide(resumen.get("h001a"), resumen.get("ue"))
    resumen["proporcion_familiar"] = safe_divide(resumen.get("h020a"), resumen.get("h001a"))
    resumen["proporcion_remunerado"] = safe_divide(resumen.get("h010a"), resumen.get("h001a"))
    resumen["ingresos_por_ue"] = safe_divide(resumen.get("m000a"), resumen.get("ue"))
    resumen["produccion_por_ue"] = safe_divide(resumen.get("a111a"), resumen.get("ue"))
    resumen["valor_agregado_por_ue"] = safe_divide(resumen.get("a131a"), resumen.get("ue"))
    resumen["maquila_sobre_ingresos"] = safe_divide(resumen.get("m700a"), resumen.get("m000a"))
    resumen.to_csv(TABLES_DIR / "saic_resumen_municipio_actividad.csv", index=False, encoding="utf-8-sig")

    lectura = resumen.copy()
    lectura["proxy_unidades_pequenas_familiares"] = lectura["proporcion_familiar"]
    lectura["proxy_intensidad_maquila"] = lectura["maquila_sobre_ingresos"]
    lectura["lectura_metodologica"] = (
        "Indicadores exploratorios a nivel municipal; no prueban informalidad ni contaminacion. "
        "Sirven para comparar estructura productiva, tamano promedio, dependencia de trabajo familiar/no remunerado "
        "e ingresos por maquila."
    )
    lectura[
        [
            "municipio_nombre",
            "actividad_codigo",
            "actividad_nombre",
            "ue",
            "h001a",
            "personal_promedio",
            "proporcion_familiar",
            "proporcion_remunerado",
            "ingresos_por_ue",
            "maquila_sobre_ingresos",
            "proxy_unidades_pequenas_familiares",
            "proxy_intensidad_maquila",
            "lectura_metodologica",
        ]
    ].to_csv(TABLES_DIR / "saic_indicadores_lectura_analitica.csv", index=False, encoding="utf-8-sig")

    if "estrato" in df.columns:
        micro = df[df["estrato"].astype(str).str.contains(r"0\s*a\s*10", case=False, na=False, regex=True)].copy()
        if not micro.empty:
            micro_resumen = (
                micro.groupby(["municipio_nombre", "actividad_codigo", "actividad_nombre", "estrato"], dropna=False)[
                    ["ue", "h001a", "h020a", "h010a", "m000a", "m700a"]
                ]
                .sum(min_count=1)
                .reset_index()
            )
            micro_resumen["personal_promedio"] = safe_divide(micro_resumen["h001a"], micro_resumen["ue"])
            micro_resumen["proporcion_familiar"] = safe_divide(micro_resumen["h020a"], micro_resumen["h001a"])
            micro_resumen["proporcion_remunerado"] = safe_divide(micro_resumen["h010a"], micro_resumen["h001a"])
            micro_resumen["ingresos_por_ue"] = safe_divide(micro_resumen["m000a"], micro_resumen["ue"])
            micro_resumen["maquila_sobre_ingresos"] = safe_divide(micro_resumen["m700a"], micro_resumen["m000a"])
            micro_resumen["lectura_metodologica"] = (
                "Estrato SAIC 0 a 10: evidencia agregada municipal de unidades pequenas. "
                "No identifica negocios ni permite ubicarlos espacialmente, pero ayuda a inferir actividad pequena "
                "que podria no observarse completamente en DENUE."
            )
            micro_resumen.to_csv(TABLES_DIR / "saic_microempresas_estrato_0_10.csv", index=False, encoding="utf-8-sig")
    log(f"SAIC procesado: {len(df)} filas")


if __name__ == "__main__":
    main()
