"""Flujo estatal DENUE para los municipios y la cuenca del Alto Atoyac."""

from importlib import import_module
from pathlib import Path
import argparse
import sys
import unicodedata

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

decisiones_preliminares = import_module(
    "scripts.04_desiciones_preliminares"
).decisiones_preliminares
crear_mapas_cuenca = import_module(
    "scripts.08_mapas_cuenca_puebla"
).crear_mapas_cuenca
crear_presentacion = import_module(
    "scripts.09_presentacion_cuenca_puebla"
).crear_presentacion
integrar_mh = import_module(
    "scripts.10_integrar_mh"
).integrar_mh


DENUE_CSV = ROOT / "data/raw/denue_scian_313-314-315-81/INEGI_DENUE_11092026.csv"
CATALOGO = ROOT / "data/processed/catalogs/giro_textil.csv"
CUENCA = ROOT / "data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_cuenca_alto_atoyac_21_reg_a.gpkg"
MUNICIPIOS = ROOT / "data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_division_municipal_20_mun_a.gpkg"
RIOS = ROOT / "data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_red_hidro_digital_06_reg_l.gpkg"
OUTPUT = ROOT / "outputs/cuenca_alto_atoyac_puebla"

MUNICIPIOS_SOLICITADOS = [
    "Amozoc", "Calpan", "Chiautzingo", "Chignahuapan", "Coronango",
    "Cuautinchán", "Cuautlancingo", "Domingo Arenas", "Huejotzingo",
    "Ixtacamaxtitlán", "Juan C. Bonilla", "Ocoyucan", "Puebla",
    "San Andrés Cholula", "San Felipe Teotlalcingo", "San Gregorio Atzompa",
    "San Jerónimo Tecuanipan", "San Martín Texmelucan",
    "San Matías Tlalancaleca", "San Miguel Xoxtla", "San Pedro Cholula",
    "San Salvador el Verde", "Tepatlaxco de Hidalgo", "Tlahuapan",
    "Tlaltenango", "Tzicatlacoyan",
]

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


def clave_texto(texto):
    return " ".join(sin_acentos(texto).casefold().split())


def cargar_denue():
    data = pd.read_csv(DENUE_CSV, encoding="cp1252", dtype=str).fillna("")
    data = data.rename(columns={c: sin_acentos(c) for c in data.columns})
    data = data.rename(columns=RENOMBRES)
    requeridas = {
        "d_llave", "nom_est", "raz_soc", "cve_scian", "desc_scian",
        "Municipio", "localidad", "Latitud", "Longitud",
        "Descripcion estrato personal ocupado",
    }
    faltantes = requeridas - set(data.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas DENUE: {sorted(faltantes)}")
    if data["d_llave"].duplicated().any():
        raise ValueError("El ID DENUE estatal contiene duplicados.")
    for columna in ["Municipio", "localidad", "nom_est", "raz_soc", "cve_scian"]:
        data[columna] = data[columna].astype(str).str.strip()
    data["geometry"] = gpd.points_from_xy(
        pd.to_numeric(data["Longitud"], errors="coerce"),
        pd.to_numeric(data["Latitud"], errors="coerce"),
    )
    if data["geometry"].isna().any():
        raise ValueError("Existen coordenadas DENUE no validas.")
    return gpd.GeoDataFrame(data, geometry="geometry", crs=4326)


def guardar_tabla(gdf, ruta_csv, ruta_gpkg, capa):
    ruta_csv.parent.mkdir(parents=True, exist_ok=True)
    ruta_gpkg.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(gdf.drop(columns="geometry")).to_csv(
        ruta_csv, index=False, encoding="utf-8-sig"
    )
    gdf.to_file(ruta_gpkg, layer=capa, driver="GPKG")


def main(sin_mh=False, estricto=False, todos_scian=False):
    if todos_scian:
        output = ROOT / "outputs/cuenca_alto_atoyac_puebla_todos_scian"
    elif estricto and sin_mh:
        output = ROOT / "outputs/cuenca_alto_atoyac_puebla_estricto_sin_mh"
    elif estricto:
        output = ROOT / "outputs/cuenca_alto_atoyac_puebla_estricto_mh"
    elif sin_mh:
        output = ROOT / "outputs/cuenca_alto_atoyac_puebla_sin_mh"
    else:
        output = OUTPUT
    for carpeta in ["tables", "layers", "maps/html", "maps/png"]:
        (output / carpeta).mkdir(parents=True, exist_ok=True)
    # Cada corrida publica un inventario de mapas autocontenido. Solo se
    # eliminan derivados HTML/PNG dentro del directorio de salida de este flujo.
    for carpeta in [output / "maps/html", output / "maps/png"]:
        for derivado in carpeta.glob("*"):
            if derivado.is_file() and derivado.suffix.lower() in {".html", ".png"}:
                derivado.unlink()

    denue = cargar_denue()
    catalogo = pd.read_csv(CATALOGO, encoding="utf-8-sig")
    atributos = pd.DataFrame(denue.drop(columns="geometry"))
    auditable = decisiones_preliminares(
        atributos, catalogo, lavanderias_solo_con_senal=estricto
    )
    auditable = denue[["d_llave", "geometry"]].merge(
        auditable, on="d_llave", how="right", validate="one_to_one"
    )
    auditable = gpd.GeoDataFrame(auditable, geometry="geometry", crs=4326)

    guardar_tabla(
        auditable,
        output / "tables/estado_puebla_auditable.csv",
        output / "layers/estado_puebla_auditable.gpkg",
        "estado_puebla_auditable",
    )

    claves = {clave_texto(m) for m in MUNICIPIOS_SOLICITADOS}
    seleccion = auditable[auditable["Municipio"].map(clave_texto).isin(claves)].copy()
    hidrico_municipios = seleccion[
        seleccion["evidencia_hidrica"].isin(["SI", "REVISAR"])
    ].copy()
    if todos_scian:
        hidrico_municipios = seleccion.copy()

    guardar_tabla(
        hidrico_municipios,
        output / "tables/universo_hidrico_26_municipios_solo_filtro.csv",
        output / "layers/universo_hidrico_26_municipios_solo_filtro.gpkg",
        "universo_hidrico_solo_filtro",
    )
    if sin_mh or todos_scian:
        hidrico_municipios["evidencia_hidrica_original"] = (
            hidrico_municipios["evidencia_hidrica"]
        )
        hidrico_municipios["fuente_universo_hidrico"] = "FILTRO_DENUE"
        hidrico_municipios["fuente_evidencia_hidrica"] = "REGLAS_DENUE"
        hidrico_municipios["id_denue_origen_mh"] = ""
        auditoria_mh = pd.DataFrame(columns=["fuente", "accion"])
    else:
        hidrico_municipios, auditoria_mh = integrar_mh(
            auditable, hidrico_municipios, ROOT
        )
        auditoria_mh.to_csv(
            output / "tables/auditoria_integracion_mh.csv",
            index=False, encoding="utf-8-sig",
        )

    cuenca = gpd.read_file(CUENCA).to_crs(4326)
    dentro = hidrico_municipios.geometry.intersects(cuenca.geometry.iloc[0])
    hidrico_cuenca = hidrico_municipios[dentro].copy()

    guardar_tabla(
        seleccion,
        output / "tables/universo_textil_26_municipios.csv",
        output / "layers/universo_textil_26_municipios.gpkg",
        "universo_textil_26_municipios",
    )
    guardar_tabla(
        hidrico_municipios,
        output / "tables/universo_hidrico_26_municipios.csv",
        output / "layers/universo_hidrico_26_municipios.gpkg",
        "universo_hidrico_26_municipios",
    )
    guardar_tabla(
        hidrico_cuenca,
        output / "tables/universo_hidrico_dentro_cuenca.csv",
        output / "layers/universo_hidrico_dentro_cuenca.gpkg",
        "universo_hidrico_dentro_cuenca",
    )

    cobertura = pd.DataFrame({"municipio_solicitado": MUNICIPIOS_SOLICITADOS})
    conteos = seleccion.groupby("Municipio").size()
    mapa_conteos = {clave_texto(k): int(v) for k, v in conteos.items()}
    cobertura["registros_textiles"] = cobertura["municipio_solicitado"].map(
        lambda x: mapa_conteos.get(clave_texto(x), 0)
    )
    cobertura.to_csv(
        output / "tables/cobertura_municipios_solicitados.csv",
        index=False, encoding="utf-8-sig",
    )

    municipios = gpd.read_file(MUNICIPIOS)
    municipios = municipios[municipios["nom_ent"].eq("Puebla")].copy()
    rios = gpd.read_file(RIOS)
    inventario, hidrico_distancia = crear_mapas_cuenca(
        cuenca, rios, municipios, hidrico_cuenca, output / "maps"
    )
    hidrico_distancia.drop(columns="geometry").to_csv(
        output / "tables/universo_hidrico_cuenca_distancia.csv",
        index=False, encoding="utf-8-sig",
    )

    resumen = {
        "denue_estatal_descargado": len(denue),
        "auditable_estatal": len(auditable),
        "universo_textil_municipios": len(seleccion),
        "universo_hidrico_municipios": len(hidrico_municipios),
        "universo_hidrico_dentro_cuenca": len(hidrico_cuenca),
        "registros_mh_revisados": len(auditoria_mh),
        "registros_mh_agregados": int(
            auditoria_mh["accion"].str.startswith("AGREGADO").sum()
        ),
        "municipios_solicitados": len(MUNICIPIOS_SOLICITADOS),
        "municipios_con_registros": int((cobertura["registros_textiles"] > 0).sum()),
        "mapas_generados": len(inventario),
        "regla_lavanderias_estricta": int(estricto),
        "modo_todos_scian": int(todos_scian),
    }
    pd.DataFrame(resumen.items(), columns=["metrica", "valor"]).to_csv(
        output / "tables/resumen_ejecucion.csv", index=False, encoding="utf-8-sig"
    )
    crear_presentacion(
        ROOT,
        output,
        inventario,
        resumen,
        hidrico_distancia,
        nombre_base=(
            "presentacion_cuenca_puebla_todos_scian"
            if todos_scian
            else "presentacion_cuenca_puebla_estricto_sin_mh"
            if estricto and sin_mh
            else "presentacion_cuenca_puebla_estricto_mh"
            if estricto
            else "presentacion_cuenca_puebla_sin_mh"
            if sin_mh
            else "presentacion_cuenca_puebla"
        ),
        subtitulo=(
            "Todos los registros SCIAN 313, 314, 315 y 812210"
            if todos_scian
            else "Regla estricta de lavanderías — sólo DENUE"
            if estricto and sin_mh
            else "Regla estricta de lavanderías — DENUE + MH de campo"
            if estricto
            else "Regla inclusiva de lavanderías — sólo DENUE"
            if sin_mh
            else "Regla inclusiva de lavanderías — DENUE + MH de campo"
        ),
    )
    print(" | ".join(f"{k}={v}" for k, v in resumen.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sin-mh", action="store_true",
        help="Genera una versión comparativa basada solamente en filtros DENUE.",
    )
    parser.add_argument(
        "--estricto", action="store_true",
        help="Exige señal adicional para admitir lavanderías SCIAN 812210.",
    )
    parser.add_argument(
        "--todos-scian", action="store_true",
        help="Mapea todos los registros de los SCIAN descargados, sin corte hídrico.",
    )
    argumentos = parser.parse_args()
    main(
        sin_mh=argumentos.sin_mh,
        estricto=argumentos.estricto,
        todos_scian=argumentos.todos_scian,
    )
