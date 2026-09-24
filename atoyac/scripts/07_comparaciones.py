"""Compara el universo hidrico historico con el resultado actual de Santa Ana."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pandas as pd


def _normalizar_id(serie):
    return serie.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def comparar_universos(
    legacy_path,
    actual_path,
    output_dir,
    expected_legacy_count=78,
    universo_actual_path=None,
):
    """Genera tablas y una figura de comparación usando el ID DENUE."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    legacy = pd.read_csv(legacy_path, encoding="utf-8-sig", dtype=str).fillna("")
    actual = pd.read_csv(actual_path, encoding="utf-8-sig", dtype=str).fillna("")
    if "id" not in legacy.columns or "d_llave" not in actual.columns:
        raise ValueError("La comparación requiere legacy.id y actual.d_llave.")

    legacy["id_comparacion"] = _normalizar_id(legacy["id"])
    actual["id_comparacion"] = _normalizar_id(actual["d_llave"])
    if legacy["id_comparacion"].duplicated().any():
        raise ValueError("El universo legacy contiene ID duplicados.")
    if actual["id_comparacion"].duplicated().any():
        raise ValueError("El universo actual contiene ID duplicados.")

    ids_legacy = set(legacy["id_comparacion"])
    ids_actual = set(actual["id_comparacion"])
    ids_ambos = ids_legacy & ids_actual
    ids_solo_legacy = ids_legacy - ids_actual
    ids_solo_actual = ids_actual - ids_legacy
    union = ids_legacy | ids_actual

    legacy_pref = legacy.add_prefix("legacy_").rename(
        columns={"legacy_id_comparacion": "id_comparacion"}
    )
    actual_pref = actual.add_prefix("actual_").rename(
        columns={"actual_id_comparacion": "id_comparacion"}
    )
    detalle = legacy_pref.merge(
        actual_pref,
        on="id_comparacion",
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    detalle["resultado_comparacion"] = detalle["_merge"].map(
        {"both": "AMBOS", "left_only": "SOLO_LEGACY", "right_only": "SOLO_ACTUAL"}
    )
    detalle = detalle.drop(columns="_merge")

    coincidencias = detalle.loc[detalle["resultado_comparacion"].eq("AMBOS")].copy()
    solo_legacy = detalle.loc[detalle["resultado_comparacion"].eq("SOLO_LEGACY")].copy()
    solo_actual = detalle.loc[detalle["resultado_comparacion"].eq("SOLO_ACTUAL")].copy()

    # Diagnosticar si los registros solo-legacy siguen siendo candidatos
    # textiles actuales pero carecen de senal hidrica, o si fueron excluidos
    # por completo del universo sectorial actual.
    solo_legacy["causa_probable_ausencia_actual"] = "NO_EVALUADA"
    if universo_actual_path is not None:
        universo_actual = pd.read_csv(
            universo_actual_path, encoding="utf-8-sig", dtype=str
        ).fillna("")
        ids_universo = set(_normalizar_id(universo_actual["d_llave"]))
        esta_en_universo = solo_legacy["id_comparacion"].isin(ids_universo)
        solo_legacy.loc[esta_en_universo, "causa_probable_ausencia_actual"] = (
            "SIGUE_EN_UNIVERSO_TEXTIL_PERO_SIN_EVIDENCIA_HIDRICA"
        )
        solo_legacy.loc[~esta_en_universo, "causa_probable_ausencia_actual"] = (
            "EXCLUIDO_DEL_UNIVERSO_TEXTIL_ACTUAL"
        )

        ids_sin_denue = solo_legacy["id_comparacion"].str.startswith("MH_SIN_ID_")
        solo_legacy.loc[ids_sin_denue, "causa_probable_ausencia_actual"] = (
            "SIN_ID_DENUE_COMPARABLE"
        )
        if "legacy_localidad" in solo_legacy.columns:
            localidad = solo_legacy["legacy_localidad"].astype(str).str.strip()
            fuera_localidad = localidad.ne("") & localidad.ne("Santa Ana Xalmimilulco")
            solo_legacy.loc[fuera_localidad, "causa_probable_ausencia_actual"] = (
                "FUERA_DEL_RECORTE_TERRITORIAL_ACTUAL"
            )
        if "legacy_nombre_act" in solo_legacy.columns:
            actividad = solo_legacy["legacy_nombre_act"].astype(str).str.lower()
            comercio_ropa = actividad.str.contains(
                "comercio al por menor de ropa", regex=False, na=False
            )
            solo_legacy.loc[comercio_ropa, "causa_probable_ausencia_actual"] = (
                "EXCLUIDO_POR_SENAL_NO_TEXTIL_EXPLICITA"
            )
        if "legacy_razon_situacion" in solo_legacy.columns:
            sin_correspondencia = solo_legacy["legacy_razon_situacion"].str.contains(
                "NO_CALIFICA_AUN_O_FUERA_AREA", regex=False, na=False
            ) & solo_legacy["causa_probable_ausencia_actual"].eq(
                "EXCLUIDO_DEL_UNIVERSO_TEXTIL_ACTUAL"
            )
            solo_legacy.loc[sin_correspondencia, "causa_probable_ausencia_actual"] = (
                "SIN_CORRESPONDENCIA_DENUE_2026_O_FUERA_AREA"
            )

    conteo_legacy = len(legacy)
    conteo_actual = len(actual)
    resumen = pd.DataFrame(
        [
            ("registros_legacy_observados", conteo_legacy),
            ("registros_legacy_esperados", expected_legacy_count),
            ("diferencia_legacy_esperado_observado", expected_legacy_count - conteo_legacy),
            ("registros_actuales", conteo_actual),
            ("presentes_en_ambos", len(ids_ambos)),
            ("solo_legacy", len(ids_solo_legacy)),
            ("solo_actual", len(ids_solo_actual)),
            ("union_de_ids", len(union)),
            ("porcentaje_legacy_recuperado", round(100 * len(ids_ambos) / conteo_legacy, 2)),
            ("porcentaje_actual_ya_en_legacy", round(100 * len(ids_ambos) / conteo_actual, 2)),
            ("similitud_jaccard_porcentaje", round(100 * len(ids_ambos) / len(union), 2)),
        ],
        columns=["metrica", "valor"],
    )
    resumen["alerta"] = ""
    if conteo_legacy != expected_legacy_count:
        resumen.loc[resumen["metrica"].eq("registros_legacy_observados"), "alerta"] = (
            f"Se esperaban {expected_legacy_count}, pero el archivo contiene {conteo_legacy}."
        )

    resumen.to_csv(output_dir / "comparacion_resumen.csv", index=False, encoding="utf-8-sig")
    detalle.to_csv(output_dir / "comparacion_detallada.csv", index=False, encoding="utf-8-sig")
    coincidencias.to_csv(output_dir / "coincidencias_ambos.csv", index=False, encoding="utf-8-sig")
    solo_legacy.to_csv(output_dir / "solo_legacy.csv", index=False, encoding="utf-8-sig")
    solo_legacy.to_csv(
        output_dir / "solo_legacy_diagnostico.csv", index=False, encoding="utf-8-sig"
    )
    solo_actual.to_csv(output_dir / "solo_actual.csv", index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), constrained_layout=True)
    categorias = ["Legacy\nobservado", "Actual", "En ambos", "Solo\nlegacy", "Solo\nactual"]
    valores = [conteo_legacy, conteo_actual, len(ids_ambos), len(ids_solo_legacy), len(ids_solo_actual)]
    colores = ["#7a5195", "#2878b5", "#2f9e44", "#b07aa1", "#59a5d8"]
    barras = axes[0].bar(categorias, valores, color=colores)
    axes[0].bar_label(barras, padding=3, fontweight="bold")
    axes[0].set_ylabel("Número de establecimientos")
    axes[0].set_title("Conteos de la comparación")
    axes[0].set_ylim(0, max(valores) * 1.2)
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].add_patch(Circle((0.43, 0.5), 0.29, color="#7a5195", alpha=0.55))
    axes[1].add_patch(Circle((0.62, 0.5), 0.29, color="#2878b5", alpha=0.55))
    axes[1].text(0.27, 0.5, str(len(ids_solo_legacy)), ha="center", va="center", fontsize=18, fontweight="bold")
    axes[1].text(0.525, 0.5, str(len(ids_ambos)), ha="center", va="center", fontsize=18, fontweight="bold")
    axes[1].text(0.78, 0.5, str(len(ids_solo_actual)), ha="center", va="center", fontsize=18, fontweight="bold")
    axes[1].text(0.30, 0.84, f"Legacy observado\n(n={conteo_legacy})", ha="center", fontweight="bold")
    axes[1].text(0.75, 0.84, f"Actual\n(n={conteo_actual})", ha="center", fontweight="bold")
    axes[1].set_xlim(0, 1.05)
    axes[1].set_ylim(0.1, 0.95)
    axes[1].set_aspect("equal")
    axes[1].axis("off")
    axes[1].set_title("Coincidencia por ID DENUE")
    subtitulo = f"Combinado: {conteo_legacy}; universo actual: {conteo_actual}"
    if conteo_legacy != expected_legacy_count:
        subtitulo += f" (se esperaban {expected_legacy_count})"
    fig.suptitle(
        "Universo hídrico preliminar — Santa Ana Xalmimilulco\n" + subtitulo,
        fontsize=14,
        fontweight="bold",
    )
    fig.savefig(output_dir / "comparacion_legacy_actual.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(
        f"Comparación legacy/actual: legacy={conteo_legacy}, actual={conteo_actual}, "
        f"ambos={len(ids_ambos)}, solo_legacy={len(ids_solo_legacy)}, "
        f"solo_actual={len(ids_solo_actual)}"
    )
    if conteo_legacy != expected_legacy_count:
        print(
            f"ADVERTENCIA: se esperaban {expected_legacy_count} registros legacy, "
            f"pero el archivo contiene {conteo_legacy}."
        )
    return resumen, detalle


def main():
    root = Path(__file__).resolve().parents[1]
    comparar_universos(
        root / "data/processed/legacy/universo_combinado_tentativo_mh.csv",
        root / "outputs/xalmimilulco/tables/xalmimilulco_textil_hidrico_si_revisar.csv",
        root / "outputs/xalmimilulco/comparacion_combinado",
        universo_actual_path=(
            root / "outputs/xalmimilulco/tables/xalmimilulco_universo_textil.csv"
        ),
    )


if __name__ == "__main__":
    main()
