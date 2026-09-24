"""Ejecuta el flujo DENUE para Huejotzingo y Santa Ana Xalmimilulco."""

from importlib import import_module
from pathlib import Path
import sys
import unicodedata

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

recorte_territorial = import_module(
    "scripts.01_recorte_territorial"
).recorte_territorial
decisiones_preliminares = import_module(
    "scripts.04_desiciones_preliminares"
).decisiones_preliminares
crear_csv_finales = import_module(
    "scripts.05_csv_capa"
).crear_csv_finales
crear_capa_desde_ids = import_module(
    "scripts.99_crear_capa"
).crear_capa_desde_ids
crear_figuras = import_module(
    "scripts.06_crear_figuras"
).crear_figuras
comparar_universos = import_module(
    "scripts.07_comparaciones"
).comparar_universos


CSV_ORIGEN = ROOT / "data/raw/denue_2026/huejotzingo/INEGI_DENUE_04092026.csv"
CAPA_ORIGEN = ROOT / "data/raw/denue_2026/huejotzingo/INEGI_DENUE_04092026.shp"
CATALOGO = ROOT / "data/processed/catalogs/giro_textil.csv"
AUDITABLES = ROOT / "data/processed/auditables"
OUTPUTS = ROOT / "outputs"

LOCALIDADES = {
    "xalmimilulco": "Santa Ana Xalmimilulco",
    "huejotzingo": "Huejotzingo",
}

RENOMBRES = {
    "ID": "d_llave",
    "Clee": "clee",
    "Nombre de la Unidad Economica": "nom_est",
    "Razon social": "raz_soc",
    "Codigo de la clase de actividad SCIAN": "cve_scian",
    "Nombre de clase de la actividad": "desc_scian",
    "Clave localidad": "cve_loc",
    "Localidad": "localidad",
}


def sin_acentos(texto):
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    ).strip()


def cargar_denue():
    data = pd.read_csv(CSV_ORIGEN, encoding="cp1252", dtype=str)
    nombres_normalizados = {col: sin_acentos(col) for col in data.columns}
    data = data.rename(columns=nombres_normalizados).rename(columns=RENOMBRES)
    requeridas = {"d_llave", "nom_est", "raz_soc", "cve_scian", "desc_scian", "localidad"}
    faltantes = requeridas - set(data.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas DENUE: {sorted(faltantes)}")
    if data["d_llave"].duplicated().any():
        raise ValueError("El ID del DENUE contiene duplicados.")
    return data


def ejecutar_localidad(data, catalogo, slug, localidad):
    territorial = recorte_territorial(
        data,
        location_column="localidad",
        location_value=localidad,
    )
    if territorial.empty:
        raise ValueError(f"No se encontraron registros para {localidad}.")

    auditable = decisiones_preliminares(territorial, catalogo)
    AUDITABLES.mkdir(parents=True, exist_ok=True)
    ruta_auditable = AUDITABLES / f"{slug}_preliminar_auditable.csv"
    auditable.to_csv(ruta_auditable, index=False, encoding="utf-8-sig")

    resultados = crear_csv_finales(auditable, OUTPUTS / slug / "tables", slug)
    for nombre, info in resultados.items():
        ruta_capa = OUTPUTS / slug / "layers" / f"{slug}_{nombre}.gpkg"
        crear_capa_desde_ids(
            info["data"],
            CAPA_ORIGEN,
            ruta_capa,
            f"{slug}_{nombre}",
        )
        info["layer_path"] = ruta_capa

    crear_figuras(
        localidad,
        slug,
        territorial,
        resultados,
        CAPA_ORIGEN,
        OUTPUTS / slug / "figures",
    )

    print(
        f"{localidad}: territorio={len(territorial)}, "
        f"auditable={len(auditable)}, "
        + ", ".join(f"{nombre}={info['count']}" for nombre, info in resultados.items())
    )
    return resultados


def main():
    data = cargar_denue()
    catalogo = pd.read_csv(CATALOGO, encoding="utf-8-sig")
    resultados_por_localidad = {}
    for slug, localidad in LOCALIDADES.items():
        resultados_por_localidad[slug] = ejecutar_localidad(
            data, catalogo, slug, localidad
        )

    comparar_universos(
        ROOT / "data/processed/legacy/universo_combinado_tentativo_mh.csv",
        resultados_por_localidad["xalmimilulco"]["textil_hidrico_si_revisar"]["path"],
        OUTPUTS / "xalmimilulco/comparacion_combinado",
        universo_actual_path=(
            resultados_por_localidad["xalmimilulco"]["universo_textil"]["path"]
        ),
    )


if __name__ == "__main__":
    main()
