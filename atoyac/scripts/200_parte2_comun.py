"""Configuracion y utilidades compartidas del pipeline de Parte 2."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MUNICIPAL = ROOT / "outputs/cuenca_alto_atoyac_puebla_todos_scian/tables/universo_textil_26_municipios.csv"
SOURCE_CUENCA = ROOT / "outputs/cuenca_alto_atoyac_puebla_todos_scian/tables/universo_hidrico_dentro_cuenca.csv"
CUENCA = ROOT / "data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_cuenca_alto_atoyac_21_reg_a.gpkg"
MUNICIPIOS = ROOT / "data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_division_municipal_20_mun_a.gpkg"
RIOS = ROOT / "data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_red_hidro_digital_06_reg_l.gpkg"
OUT = ROOT / "outputs/parte_2"
DOCS = ROOT / "docs/parte_2"
CRS_GEOGRAFICO = "EPSG:4326"
CRS_METRICO = "EPSG:32614"
SEMILLA = 20260921
NOMBRE_UNIVERSO = (
    "Universo sectorial ampliado de actividades textiles, confección y "
    "servicios de lavandería/tintorería potencialmente relevantes"
)


def asegurar_directorios() -> None:
    for rel in [
        "00_auditoria", "01_matriz", "02_geometrias", "03_diagnosticos",
        "04_clustering", "05_seleccion", "06_clusters", "07_perfiles",
        "08_sobrerrepresentacion", "09_comparacion", "10_figuras",
        "11_cierre", "12_atlas", "13_figuras_finales", "14_segunda_pasada",
    ]:
        (OUT / rel).mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def guardar_json(objeto, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(objeto, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def guardar_csv(tabla: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(path, index=False, encoding="utf-8-sig")


def normalizar_texto(valor) -> str:
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).casefold())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip()


def cargar_fuentes() -> tuple[pd.DataFrame, pd.DataFrame]:
    municipal = pd.read_csv(SOURCE_MUNICIPAL, encoding="utf-8-sig", dtype=str)
    cuenca = pd.read_csv(SOURCE_CUENCA, encoding="utf-8-sig", dtype=str)
    return municipal, cuenca


def cargar_maestra() -> pd.DataFrame:
    return pd.read_csv(
        OUT / "01_matriz/matriz_maestra_establecimientos.csv",
        encoding="utf-8-sig",
        low_memory=False,
    )


def puntos_desde_tabla(tabla: pd.DataFrame, crs=CRS_GEOGRAFICO) -> gpd.GeoDataFrame:
    lon = pd.to_numeric(tabla["Longitud"], errors="coerce")
    lat = pd.to_numeric(tabla["Latitud"], errors="coerce")
    if lon.isna().any() or lat.isna().any():
        raise ValueError("Hay coordenadas faltantes o no numericas.")
    return gpd.GeoDataFrame(
        tabla.copy(), geometry=gpd.points_from_xy(lon, lat), crs=crs
    )


def leer_puntos_metricos() -> gpd.GeoDataFrame:
    return gpd.read_file(
        OUT / "02_geometrias/establecimientos_parte2.gpkg",
        layer="establecimientos_utm14n",
    )


def booleano(serie: pd.Series) -> pd.Series:
    if serie.dtype == bool:
        return serie.fillna(False)
    return serie.fillna("").astype(str).str.casefold().eq("true")


def codigo_limpio(serie: pd.Series) -> pd.Series:
    return serie.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def escenario_id(metodo: str, parametros: dict) -> str:
    partes = [metodo.lower()]
    for clave, valor in parametros.items():
        texto = str(valor).replace(".", "p").replace("-", "m")
        partes.append(f"{clave}-{texto}")
    return "__".join(partes)


def resumen_particion(labels: np.ndarray) -> dict:
    labels = np.asarray(labels, dtype=int)
    validos = labels[labels >= 0]
    tamanos = pd.Series(validos).value_counts() if len(validos) else pd.Series(dtype=int)
    n = len(labels)
    return {
        "n_establecimientos": n,
        "n_clusters": int(tamanos.size),
        "n_ruido": int((labels < 0).sum()),
        "pct_ruido": float(100 * (labels < 0).mean()),
        "tam_min": int(tamanos.min()) if len(tamanos) else 0,
        "tam_mediana": float(tamanos.median()) if len(tamanos) else 0.0,
        "tam_media": float(tamanos.mean()) if len(tamanos) else 0.0,
        "tam_max": int(tamanos.max()) if len(tamanos) else 0,
        "pct_cluster_mayor": float(100 * tamanos.max() / n) if len(tamanos) else 0.0,
    }


def membresias_path() -> Path:
    return OUT / "04_clustering/membresias_escenarios.csv.gz"


def leer_membresias() -> pd.DataFrame:
    return pd.read_csv(membresias_path(), compression="gzip", dtype={"d_llave": str})


def leer_solucion_principal() -> tuple[str, pd.DataFrame]:
    seleccion = pd.read_csv(OUT / "05_seleccion/seleccion_escenarios.csv")
    principal = seleccion.loc[seleccion["rol"].eq("PRINCIPAL"), "escenario_id"].iloc[0]
    membresias = leer_membresias()
    return principal, membresias[membresias["escenario_id"].eq(principal)].copy()
