from __future__ import annotations

import re

import geopandas as gpd
import pandas as pd

from common import (
    PROCESSED_DIR,
    TABLES_DIR,
    clean_dataframe_columns,
    ensure_output_dirs,
    log,
    normalize_text,
    read_gpkg,
    relpath,
    safe_to_file,
)


# El analisis excluye comercio de prendas. Se queda con produccion,
# confeccion/maquila y procesos humedos o de acabado.
TEXTILE_KEYWORDS = [
    "textil",
    "textiles",
    "mezclilla",
    "denim",
    "confeccion",
    "maquila",
    "costura",
    "costurera",
    "sastreria",
    "modista",
    "bordado",
    "lavanderia",
    "laundry",
    "tintoreria",
    "tenido",
    "teñido",
    "acabado",
    "lavado",
    "deslavado",
    "tratado",
    "tratamiento",
    "deshebrado",
    "pantalon",
    "jeans",
]

HIGH_TERMS = [
    "lavanderia",
    "laundry",
    "tintoreria",
    "tenido",
    "teñido",
    "acabado",
    "lavado",
    "deslavado",
    "tratado",
    "tratamiento",
    "procesos humedos",
]
MEDIUM_TERMS = [
    "confeccion",
    "fabricacion",
    "elaboracion",
    "maquila",
    "costura",
    "costurera",
    "sastreria",
    "modista",
    "taller",
    "pantalon",
    "jeans",
    "mezclilla",
    "denim",
    "bordado",
    "deshebrado",
]
COMMERCE_TERMS = [
    "comercio",
    "venta",
    "tienda",
    "boutique",
    "novedades",
    "merceria",
    "zapateria",
    "uniformes escolares",
    "ropa infantil",
]
PRODUCTION_TERMS = HIGH_TERMS + MEDIUM_TERMS + ["industria", "industrial", "textilera", "manufactura"]
COMMERCE_SCIAN_PREFIXES = ("46",)
TEXTILE_SCIAN_PREFIXES = ("313", "314", "315", "8122")
NON_TEXTILE_EXCLUSION_TERMS = [
    "mecanico",
    "mecanica",
    "automotriz",
    "autolavado",
    "auto lavado",
    "autos",
    "vehiculo",
    "vehiculos",
    "motos",
    "bicicleta",
    "bicicletas",
    "carpinteria",
    "herreria",
    "torno",
    "celular",
    "celulares",
]


def detect_columns(gdf: gpd.GeoDataFrame) -> dict[str, str]:
    cols = list(gdf.columns)
    norm = {c: normalize_text(c) for c in cols}
    patterns = {
        "nombre_establecimiento": ["nombre", "unidad_economica", "nom_estab", "rama_activ"],
        "razon_social": ["razon", "social"],
        "actividad_economica": ["actividad", "scian", "clase", "codigo", "subrama_ac"],
        "codigo_scian": ["codigo", "scian", "clase", "subrama_ac"],
        "personal_ocupado_tamano": ["estrato", "personal", "tamano", "per_ocu"],
        "localidad": ["localidad", "loc"],
        "municipio": ["municipio", "mun"],
        "latitud": ["latitud", "lat", "clase_acti"],
        "longitud": ["longitud", "lon", "lng", "estrato_pe"],
    }
    detected: dict[str, str] = {}
    for field, tokens in patterns.items():
        for col, col_norm in norm.items():
            if all(token in col_norm for token in tokens[:2]) or any(token == col_norm for token in tokens):
                detected[field] = col
                break
        if field not in detected:
            for col, col_norm in norm.items():
                if any(token in col_norm for token in tokens):
                    detected[field] = col
                    break
    return detected


def scian_text_columns(gdf: gpd.GeoDataFrame) -> list[str]:
    usable = []
    for col in gdf.columns:
        if col == "geometry":
            continue
        if pd.api.types.is_object_dtype(gdf[col]) or "string" in str(gdf[col].dtype):
            usable.append(col)
        elif normalize_text(col) in {"codigo_de_la_clase_actividad_scian", "subrama_ac"}:
            usable.append(col)
    return usable


def build_search_text(gdf: gpd.GeoDataFrame) -> pd.Series:
    cols = scian_text_columns(gdf)
    if not cols:
        return pd.Series("", index=gdf.index)
    return gdf[cols].fillna("").astype(str).agg(" ".join, axis=1).map(normalize_text)


def scian_code_series(gdf: gpd.GeoDataFrame) -> pd.Series:
    for col in gdf.columns:
        if normalize_text(col) in {"codigo_de_la_clase_actividad_scian", "subrama_ac", "codigo_scian", "clase"}:
            return gdf[col].fillna("").astype(str).str.extract(r"(\d+)", expand=False).fillna("")
    return pd.Series("", index=gdf.index)


def keyword_regex() -> re.Pattern:
    words = [normalize_text(w) for w in TEXTILE_KEYWORDS]
    return re.compile("|".join(re.escape(w) for w in sorted(set(words), key=len, reverse=True)))


def classify_relevance(text: str) -> str:
    if any(term in text for term in HIGH_TERMS):
        return "alta_relevancia_ambiental"
    if any(term in text for term in MEDIUM_TERMS):
        return "media_relevancia_ambiental"
    return "revisar"


def commerce_exclusion_mask(text: pd.Series, scian: pd.Series) -> pd.Series:
    has_commerce_text = text.map(lambda value: any(term in value for term in COMMERCE_TERMS))
    has_production_text = text.map(lambda value: any(term in value for term in PRODUCTION_TERMS))
    commerce_code = scian.str.startswith(COMMERCE_SCIAN_PREFIXES)
    return commerce_code | (has_commerce_text & ~has_production_text)


def non_textile_exclusion_mask(text: pd.Series, scian: pd.Series) -> pd.Series:
    has_non_textile = text.map(lambda value: any(term in value for term in NON_TEXTILE_EXCLUSION_TERMS))
    textile_code = scian.str.startswith(TEXTILE_SCIAN_PREFIXES)
    return has_non_textile & ~textile_code


def main() -> None:
    ensure_output_dirs()
    src = PROCESSED_DIR / "denue_raw.gpkg"
    if not src.exists():
        log("No existe data/processed/denue_raw.gpkg. Ejecuta 01_prepare_geodata.py primero.")
        return

    denue = read_gpkg(src)
    denue = clean_dataframe_columns(denue)
    detected = detect_columns(denue)
    pd.DataFrame([{"campo_estandar": k, "columna_detectada": v} for k, v in detected.items()]).to_csv(
        TABLES_DIR / "denue_columnas_detectadas.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame({"columna": [c for c in denue.columns], "dtype": [str(denue[c].dtype) for c in denue.columns]}).to_csv(
        TABLES_DIR / "denue_columnas_disponibles.csv", index=False, encoding="utf-8-sig"
    )

    search_text = build_search_text(denue)
    scian = scian_code_series(denue)
    regex = keyword_regex()
    candidate_mask = search_text.str.contains(regex, na=False) | scian.str.startswith(TEXTILE_SCIAN_PREFIXES)
    excluded_commerce = commerce_exclusion_mask(search_text, scian)
    excluded_non_textile = non_textile_exclusion_mask(search_text, scian)
    mask = candidate_mask & ~excluded_commerce & ~excluded_non_textile

    textil = denue.loc[mask].copy()
    textil["texto_busqueda"] = search_text.loc[mask]
    textil["codigo_scian_detectado"] = scian.loc[mask]
    textil["palabras_clave_detectadas"] = textil["texto_busqueda"].map(
        lambda x: "; ".join(sorted({m.group(0) for m in regex.finditer(x)}))
    )
    textil["categoria_relevancia_ambiental"] = textil["texto_busqueda"].map(classify_relevance)
    textil["nota_metodologica"] = (
        "Priorizacion preliminar por produccion, confeccion, maquila, acabado o lavado textil; "
        "se excluye comercio de prendas y no implica evidencia de contaminacion directa."
    )

    excluidos = denue.loc[candidate_mask & (excluded_commerce | excluded_non_textile)].copy()
    if not excluidos.empty:
        excluidos["texto_busqueda"] = search_text.loc[excluidos.index]
        excluidos["codigo_scian_detectado"] = scian.loc[excluidos.index]
        excluidos.drop(columns="geometry").to_csv(
            TABLES_DIR / "denue_excluidos_comercio_prendas.csv",
            index=False,
            encoding="utf-8-sig",
        )

    out_gpkg = PROCESSED_DIR / "denue_textil.gpkg"
    safe_to_file(textil, out_gpkg, layer="denue_textil")
    textil.drop(columns="geometry").to_csv(TABLES_DIR / "denue_textil.csv", index=False, encoding="utf-8-sig")

    loc_col = detected.get("localidad") or "source_folder"
    if loc_col not in textil.columns:
        loc_col = "source_folder"
    resumen = (
        textil.groupby([loc_col, "categoria_relevancia_ambiental"], dropna=False)
        .size()
        .reset_index(name="establecimientos")
        .rename(columns={loc_col: "localidad_o_fuente"})
    )
    resumen.to_csv(TABLES_DIR / "resumen_denue_por_localidad_categoria.csv", index=False, encoding="utf-8-sig")

    log(f"DENUE textil productivo guardado en {relpath(out_gpkg)} con {len(textil)} establecimientos")
    log(f"Comercios de prendas excluidos del analisis: {len(excluidos)}")


if __name__ == "__main__":
    main()
