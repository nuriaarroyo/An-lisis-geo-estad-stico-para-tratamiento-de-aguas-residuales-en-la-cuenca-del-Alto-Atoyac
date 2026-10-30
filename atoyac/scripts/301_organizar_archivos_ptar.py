"""Inventaría y organiza los insumos de Archivos_PTAR para la Parte 3.

No modifica la entrega original. Genera tablas de auditoría y un GeoPackage de
trabajo en outputs/parte_3/01_insumos_organizados, todo en EPSG:32614.
"""

from __future__ import annotations

import csv
import json
import os
from io import BytesIO
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio


RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "data" / "processed" / "lesly" / "Archivos_PTAR"
SALIDA = RAIZ / "outputs" / "parte_3" / "01_insumos_organizados"
GPKG = SALIDA / "parte_3_insumos_base.gpkg"
CRS_TRABAJO = "EPSG:32614"


def ruta_windows_larga(ruta: Path) -> str:
    """Permite leer archivos cuya ruta supera el límite clásico de Windows."""
    absoluta = str(ruta.resolve())
    if os.name == "nt" and not absoluta.startswith("\\\\?\\"):
        return "\\\\?\\" + absoluta
    return absoluta


def leer_csv(ruta: Path, encoding: str = "latin1") -> pd.DataFrame:
    with open(ruta_windows_larga(ruta), "rb") as archivo:
        return pd.read_csv(BytesIO(archivo.read()), encoding=encoding)


def escribir_capa(gdf: gpd.GeoDataFrame, nombre: str) -> None:
    if gdf.empty:
        return
    gdf.to_file(GPKG, layer=nombre, driver="GPKG", index=False)


def inventariar_archivos() -> pd.DataFrame:
    filas = []
    for ruta in sorted(p for p in ENTRADA.rglob("*") if p.is_file()):
        relativo = ruta.relative_to(ENTRADA)
        filas.append(
            {
                "ruta_relativa": str(relativo),
                "nombre": ruta.name,
                "extension": ruta.suffix.lower(),
                "tamano_bytes": ruta.stat().st_size,
                "carpeta_fuente": relativo.parts[0] if len(relativo.parts) > 1 else "raiz",
            }
        )
    return pd.DataFrame(filas)


def inventariar_capas() -> pd.DataFrame:
    filas = []
    rutas = sorted(
        list(ENTRADA.rglob("*.gpkg"))
        + list(ENTRADA.rglob("*.geojson"))
        + list(ENTRADA.rglob("*.shp"))
    )
    for ruta in rutas:
        try:
            for capa, geometria in pyogrio.list_layers(ruta):
                info = pyogrio.read_info(ruta, layer=capa)
                filas.append(
                    {
                        "ruta_relativa": str(ruta.relative_to(ENTRADA)),
                        "capa": capa,
                        "geometria": geometria,
                        "objetos": info.get("features"),
                        "crs": info.get("crs"),
                        "campos": "|".join(info.get("fields", [])),
                        "estado_lectura": "correcto",
                    }
                )
        except Exception as exc:  # la auditoría debe registrar, no ocultar, fallas
            filas.append(
                {
                    "ruta_relativa": str(ruta.relative_to(ENTRADA)),
                    "capa": "",
                    "geometria": "",
                    "objetos": None,
                    "crs": "",
                    "campos": "",
                    "estado_lectura": f"error: {exc}",
                }
            )
    return pd.DataFrame(filas)


def cargar_capa(nombre_archivo: str) -> gpd.GeoDataFrame:
    return gpd.read_file(ENTRADA / nombre_archivo).to_crs(CRS_TRABAJO)


def recortar(gdf: gpd.GeoDataFrame, mascara: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs != mascara.crs:
        gdf = gdf.to_crs(mascara.crs)
    return gpd.clip(gdf, mascara)


def preparar_puntos_csv(tabla: pd.DataFrame, fuente: str) -> gpd.GeoDataFrame:
    tabla = tabla.copy()
    tabla["fuente_datos"] = fuente
    tabla["latitud"] = pd.to_numeric(tabla["latitud"], errors="coerce")
    tabla["longitud"] = pd.to_numeric(tabla["longitud"], errors="coerce")
    tabla = tabla.dropna(subset=["latitud", "longitud"])
    return gpd.GeoDataFrame(
        tabla,
        geometry=gpd.points_from_xy(tabla["longitud"], tabla["latitud"]),
        crs="EPSG:4326",
    ).to_crs(CRS_TRABAJO)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    if GPKG.exists():
        GPKG.unlink()

    archivos = inventariar_archivos()
    capas = inventariar_capas()
    archivos.to_csv(SALIDA / "inventario_archivos.csv", index=False, encoding="utf-8-sig")
    capas.to_csv(SALIDA / "inventario_capas_espaciales.csv", index=False, encoding="utf-8-sig")

    cuenca = cargar_capa("cuenca_reproyectada.gpkg")
    municipios = recortar(cargar_capa("municipios_reproyectado.gpkg"), cuenca)
    rio = recortar(cargar_capa("RioAtoyac_reproyecetado_FINAL.gpkg"), cuenca)
    franja = recortar(cargar_capa("Limites_federales.gpkg"), cuenca)

    escribir_capa(cuenca, "limite_cuenca")
    escribir_capa(municipios, "municipios_interseccion_cuenca")
    escribir_capa(rio, "rio_atoyac_referencia")
    escribir_capa(franja, "franja_10m_referencia")

    csv_inegi = (
        ENTRADA
        / "PTAR_municipales_INEGI-2023-descarga original"
        / "conjunto_de_datos"
        / "PTAR-INEGI-Cuenca.csv"
    )
    tabla_inegi = leer_csv(csv_inegi, encoding="latin1")
    puntos_inegi = preparar_puntos_csv(tabla_inegi, "INEGI CNGMD 2021, descarga 2023")
    puntos_inegi = recortar(puntos_inegi, cuenca)
    escribir_capa(puntos_inegi, "inegi_elementos_agua_cuenca")
    escribir_capa(
        puntos_inegi[puntos_inegi["tipo"].eq("Planta de tratamiento")].copy(),
        "inegi_ptar_cuenca",
    )
    escribir_capa(
        puntos_inegi[puntos_inegi["tipo"].eq("Punto de descarga")].copy(),
        "inegi_descargas_cuenca",
    )

    tabla_manual = pd.read_csv(ENTRADA / "PTAR_Final.csv", encoding="utf-8-sig")
    tabla_manual = tabla_manual.rename(columns={"Latitud": "latitud", "Longitud": "longitud"})
    puntos_manual = preparar_puntos_csv(tabla_manual, "Compilación PTAR_Final")
    escribir_capa(recortar(puntos_manual, cuenca), "ptar_compilacion_manual")

    tipos = (
        puntos_inegi.groupby("tipo", dropna=False)
        .size()
        .rename("objetos")
        .reset_index()
        .sort_values("objetos", ascending=False)
    )
    tipos.to_csv(SALIDA / "resumen_tipos_inegi_cuenca.csv", index=False, encoding="utf-8-sig")

    # RH18: HL son líneas hidrográficas superficiales; se unen y recortan.
    resumen_rh = []
    lineas = []
    for shp in sorted(ENTRADA.rglob("RH18*_*.shp")):
        sufijo = shp.stem.rsplit("_", 1)[-1].lower()
        info = pyogrio.read_info(shp)
        resumen_rh.append(
            {
                "hoja": shp.parent.name,
                "familia": sufijo,
                "geometria": info.get("geometry_type"),
                "objetos": info.get("features"),
                "crs": info.get("crs"),
            }
        )
        if sufijo == "hl":
            capa = gpd.read_file(shp).to_crs(CRS_TRABAJO)
            capa["hoja_fuente"] = shp.parent.name
            lineas.append(capa)
    resumen_rh_df = pd.DataFrame(resumen_rh)
    resumen_rh_df.to_csv(SALIDA / "inventario_red_hidrografica_rh18.csv", index=False, encoding="utf-8-sig")
    agregado_rh = (
        resumen_rh_df.groupby(["familia", "geometria", "crs"], dropna=False)["objetos"]
        .agg(["count", "sum"])
        .reset_index()
        .rename(columns={"count": "n_hojas", "sum": "objetos_total"})
    )
    agregado_rh.to_csv(SALIDA / "resumen_red_hidrografica_rh18.csv", index=False, encoding="utf-8-sig")
    if lineas:
        red = gpd.GeoDataFrame(pd.concat(lineas, ignore_index=True), crs=CRS_TRABAJO)
        escribir_capa(recortar(red, cuenca), "red_hidrografica_rh18_cuenca")

    resumen = {
        "carpeta_entrada": str(ENTRADA.relative_to(RAIZ)),
        "salida": str(SALIDA.relative_to(RAIZ)),
        "archivos_inventariados": int(len(archivos)),
        "capas_espaciales_inventariadas": int(len(capas)),
        "elementos_inegi_en_csv_cuenca": int(len(tabla_inegi)),
        "elementos_inegi_dentro_geometria_cuenca": int(len(puntos_inegi)),
        "ptar_inegi_dentro_cuenca": int((puntos_inegi["tipo"] == "Planta de tratamiento").sum()),
        "descargas_inegi_dentro_cuenca": int((puntos_inegi["tipo"] == "Punto de descarga").sum()),
        "ptar_compilacion_manual_dentro_cuenca": int(len(recortar(puntos_manual, cuenca))),
        "advertencias": [
            "La familia RH18 es hidrografía superficial; no equivale a una red de drenaje sanitario.",
            "La franja de 10 m es una geometría de referencia y no acredita por sí sola un límite federal legal.",
            "Los registros de distintas fuentes y años no demuestran operación, capacidad disponible ni conexión hidráulica.",
            "Los colectores de Huejotzingo y San Martín Texmelucan siguen sin una capa fuente recuperable.",
        ],
    }
    (SALIDA / "resumen_organizacion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resumen, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
