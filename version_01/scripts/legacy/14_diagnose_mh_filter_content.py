from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from version_01.scripts.common import OUTPUTS_DIR, PROCESSED_DIR, ensure_output_dirs, read_gpkg, relpath


OUT_DIR = OUTPUTS_DIR / "auditoria_santa_ana_mh_filtrado" / "tablas"

MH_PATH = PROCESSED_DIR / "capa_maryhelen" / "capa MH.shp"
DENUE2026_PATH = PROCESSED_DIR / "denue2026_raw.gpkg"
CLASSIFIED2026_PATH = PROCESSED_DIR / "denue2026_universo_textil_clasificado.gpkg"
UNIVERSE2026_PATH = OUTPUTS_DIR / "universo_prioritario_denue_2026" / "universo_prioritario_denue_2026.gpkg"
SANTA_CURRENT_PATH = (
    OUTPUTS_DIR
    / "universo_prioritario_denue"
    / "santa_ana_xalmimilulco"
    / "capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg"
)


def read_any(path: Path) -> gpd.GeoDataFrame:
    gdf = read_gpkg(path) if path.suffix.lower() == ".gpkg" else gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf.to_crs("EPSG:6372")


def norm_id(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .replace({"nan": "", "None": "", "<NA>": ""})
    )


def main() -> None:
    ensure_output_dirs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mh = read_any(MH_PATH).reset_index(drop=True)
    denue = read_any(DENUE2026_PATH)
    classified = read_any(CLASSIFIED2026_PATH)
    universe = read_any(UNIVERSE2026_PATH)
    santa = read_any(SANTA_CURRENT_PATH)

    mh["mh_row_id"] = range(1, len(mh) + 1)
    mh["_id_key"] = norm_id(mh["ID DENUE"])
    denue["_id_key"] = norm_id(denue["id"])
    classified["_id_key"] = norm_id(classified["id"])
    universe["_id_key"] = norm_id(universe["id"])
    santa["_id_key"] = norm_id(santa["id"])

    denue_cols = [
        "_id_key",
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "nombre_clase_actividad_scian",
        "per_ocu",
        "municipio",
        "localidad",
        "geometry",
    ]
    class_cols = [
        "_id_key",
        "categoria_relevancia_ambiental",
        "etapa_productiva_sugerida",
        "presion_ambiental_potencial",
        "confianza_clasificacion",
        "evidencia_clasificacion",
        "palabras_clave_etapa",
        "reglas_activadas",
        "decision_estudio_sugerida",
        "decision_alcance_proyecto",
        "flag_universo_alcance_proyecto",
        "flag_estudio_prioritario",
        "flag_proceso_humedo_relevante",
        "flag_mezclilla_jeans",
        "flag_lavado_deslavado",
        "flag_tenido_tintoreria",
        "flag_acabado_tratamiento",
        "flag_maquila_productiva",
        "flag_cercania_hidrografia_250m",
        "distancia_hidrografia_m",
        "motivo_flag_estudio_prioritario",
        "motivo_universo_alcance_proyecto",
        "motivo_exclusion_prioritaria",
        "motivo_auditoria",
    ]

    mh_attrs = mh.drop(columns="geometry").copy()
    denue_attrs = denue[[c for c in denue_cols if c in denue.columns]].rename(columns={"geometry": "geometry_denue"})
    class_attrs = classified[[c for c in class_cols if c in classified.columns]]

    out = mh_attrs.merge(denue_attrs, on="_id_key", how="left").merge(class_attrs, on="_id_key", how="left")

    mh_geom = mh[["mh_row_id", "geometry"]].rename(columns={"geometry": "geometry_mh"})
    out = out.merge(mh_geom, on="mh_row_id", how="left")
    out["dist_m_mh_vs_denue2026"] = out.apply(
        lambda row: row["geometry_mh"].distance(row["geometry_denue"])
        if row.get("_id_key", "") and row.get("geometry_denue") is not None
        else pd.NA,
        axis=1,
    )
    out = out.drop(columns=["geometry_mh", "geometry_denue"], errors="ignore")

    denue_ids = set(denue["_id_key"]) - {""}
    classified_ids = set(classified["_id_key"]) - {""}
    universe_ids = set(universe["_id_key"]) - {""}
    santa_ids = set(santa["_id_key"]) - {""}

    out["en_denue2026_base"] = out["_id_key"].isin(denue_ids)
    out["en_mi_clasificacion_textil_2026"] = out["_id_key"].isin(classified_ids)
    out["en_mi_universo_prioritario_2026"] = out["_id_key"].isin(universe_ids)
    out["en_mi_santa_actual"] = out["_id_key"].isin(santa_ids)

    def situation(row: pd.Series) -> str:
        if not row["_id_key"]:
            return "sin_id_denue_en_mh"
        if not row["en_denue2026_base"]:
            return "id_mh_no_existe_en_denue2026"
        if row["en_mi_universo_prioritario_2026"]:
            return "si_entra_en_mi_universo_prioritario_2026"
        if row["en_mi_clasificacion_textil_2026"]:
            return "textil_en_denue2026_pero_no_prioritario"
        return "existe_en_denue2026_pero_no_entra_al_filtro_textil"

    out["situacion_comparativa"] = out.apply(situation, axis=1)

    def reason(row: pd.Series) -> str:
        if row["situacion_comparativa"] == "sin_id_denue_en_mh":
            return "La capa MH no trae ID DENUE; no se puede validar contra DENUE registro a registro."
        if row["situacion_comparativa"] == "id_mh_no_existe_en_denue2026":
            return "El ID de MH no esta en DENUE 2026 base."
        if row["en_mi_universo_prioritario_2026"]:
            return "Coincide con mi universo prioritario 2026."
        if row["en_mi_clasificacion_textil_2026"]:
            flags = []
            for label, col in [
                ("humedo", "flag_proceso_humedo_relevante"),
                ("mezclilla", "flag_mezclilla_jeans"),
                ("lavado", "flag_lavado_deslavado"),
                ("tenido", "flag_tenido_tintoreria"),
                ("acabado", "flag_acabado_tratamiento"),
            ]:
                if bool(row.get(col, False)):
                    flags.append(label)
            return (
                "Si es textil/candidato, pero no prioritario automatico: "
                f"decision={row.get('decision_estudio_sugerida', '')}; "
                f"etapa={row.get('etapa_productiva_sugerida', '')}; "
                f"banderas={','.join(flags) or 'sin bandera humeda/mezclilla prioritaria'}"
            )
        return "Existe en DENUE 2026, pero no paso el filtro textil inicial por keywords/SCIAN de alcance."

    out["razon_no_es_mi_prioritario"] = out.apply(reason, axis=1)

    keep = [
        "mh_row_id",
        "Name",
        "DENUE",
        "ID DENUE",
        "_id_key",
        "situacion_comparativa",
        "razon_no_es_mi_prioritario",
        "en_denue2026_base",
        "en_mi_clasificacion_textil_2026",
        "en_mi_universo_prioritario_2026",
        "en_mi_santa_actual",
        "dist_m_mh_vs_denue2026",
        "id",
        "clee",
        "nombre_de_la_unidad_economica",
        "codigo_de_la_clase_actividad_scian",
        "nombre_clase_actividad_scian",
        "per_ocu",
        "municipio",
        "localidad",
        "categoria_relevancia_ambiental",
        "etapa_productiva_sugerida",
        "decision_estudio_sugerida",
        "decision_alcance_proyecto",
        "flag_universo_alcance_proyecto",
        "flag_estudio_prioritario",
        "flag_proceso_humedo_relevante",
        "flag_mezclilla_jeans",
        "flag_lavado_deslavado",
        "flag_tenido_tintoreria",
        "flag_acabado_tratamiento",
        "flag_maquila_productiva",
        "flag_cercania_hidrografia_250m",
        "distancia_hidrografia_m",
        "evidencia_clasificacion",
        "palabras_clave_etapa",
        "motivo_flag_estudio_prioritario",
        "motivo_universo_alcance_proyecto",
        "motivo_exclusion_prioritaria",
        "motivo_auditoria",
    ]
    final = out[[c for c in keep if c in out.columns]].copy()
    final.to_csv(OUT_DIR / "diagnostico_mh_filtrado_registro_por_registro.csv", index=False, encoding="utf-8-sig")

    summaries = {
        "situacion": out.groupby("situacion_comparativa", dropna=False).size().reset_index(name="registros"),
        "scian": out[out["en_denue2026_base"]]
        .groupby(["codigo_de_la_clase_actividad_scian", "nombre_clase_actividad_scian"], dropna=False)
        .size()
        .reset_index(name="registros")
        .sort_values("registros", ascending=False),
        "etapa": out[out["en_mi_clasificacion_textil_2026"]]
        .groupby(["etapa_productiva_sugerida", "decision_estudio_sugerida", "flag_estudio_prioritario"], dropna=False)
        .size()
        .reset_index(name="registros")
        .sort_values("registros", ascending=False),
        "localidad": out[out["en_denue2026_base"]]
        .groupby(["localidad"], dropna=False)
        .size()
        .reset_index(name="registros")
        .sort_values("registros", ascending=False),
    }

    with pd.ExcelWriter(OUT_DIR / "diagnostico_mh_filtrado_resumen.xlsx", engine="openpyxl") as writer:
        final.to_excel(writer, sheet_name="registro_por_registro", index=False)
        for name, df in summaries.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)

    lines = [
        "# Diagnostico del filtrado MH contra DENUE 2026 y mi filtro",
        "",
        "## Resumen",
    ]
    for _, row in summaries["situacion"].iterrows():
        lines.append(f"- {row['situacion_comparativa']}: {int(row['registros'])}")
    lines.extend(
        [
            "",
            "## SCIAN en MH que si existe en DENUE 2026",
            "| SCIAN | actividad | registros |",
            "| --- | --- | --- |",
        ]
    )
    for _, row in summaries["scian"].iterrows():
        activity = str(row["nombre_clase_actividad_scian"]).replace("|", "/")
        lines.append(f"| {row['codigo_de_la_clase_actividad_scian']} | {activity} | {int(row['registros'])} |")
    lines.extend(
        [
            "",
            "## Lectura",
            "MH filtrado toma principalmente registros DENUE 2026 de confeccion/maquila de prendas. Mi universo prioritario 2026 es mas estrecho: prioriza senales de lavado, lavanderia, tintoreria, acabado/tratamiento textil o mezclilla/jeans con relevancia de estudio. Por eso muchos registros MH existen en DENUE 2026 pero no entran como prioritarios.",
            "",
            "## Archivos",
            "- diagnostico_mh_filtrado_registro_por_registro.csv",
            "- diagnostico_mh_filtrado_resumen.xlsx",
        ]
    )
    (OUT_DIR / "diagnostico_mh_filtrado.md").write_text("\n".join(lines), encoding="utf-8")

    print(summaries["situacion"].to_string(index=False))
    print()
    print(summaries["scian"].to_string(index=False))
    print()
    print(summaries["etapa"].to_string(index=False))
    print(f"\n[atoyac] Diagnostico MH guardado en {relpath(OUT_DIR)}")


if __name__ == "__main__":
    main()
