"""Integra los universos complementarios MH sin perder su procedencia."""

from difflib import SequenceMatcher
from pathlib import Path
import re
import unicodedata

import geopandas as gpd
import pandas as pd


def _normalizar(texto):
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    ).casefold()
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _coordenada(texto):
    numeros = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", str(texto))]
    mayus = str(texto).upper()
    if ("N" in mayus or "W" in mayus) and len(numeros) >= 6:
        lat = numeros[0] + numeros[1] / 60 + numeros[2] / 3600
        lon = -(numeros[3] + numeros[4] / 60 + numeros[5] / 3600)
        return lat, lon
    if len(numeros) >= 2:
        return numeros[0], numeros[1]
    raise ValueError(f"Coordenada MH no reconocida: {texto}")


def _fila_sintetica(columnas, identificador, nombre, municipio, localidad, geometry):
    fila = {c: "" for c in columnas if c != "geometry"}
    fila.update({
        "d_llave": identificador,
        "nom_est": nombre,
        "Municipio": municipio,
        "localidad": localidad,
        "sector_textil": "REVISAR",
        "evidencia_hidrica": "SI",
        "evidencia_hidrica_original": "SIN_REGISTRO_DENUE_2026",
        "fuente_evidencia_hidrica": "MH_TRABAJO_CAMPO",
        "geometry": geometry,
    })
    return fila


def integrar_mh(auditable, hidrico, root):
    """Devuelve universo hídrico enriquecido y tabla de trazabilidad MH."""
    auditable = auditable.copy()
    resultado = hidrico.copy()
    resultado["evidencia_hidrica_original"] = resultado["evidencia_hidrica"]
    resultado["fuente_universo_hidrico"] = "FILTRO_DENUE"
    resultado["fuente_evidencia_hidrica"] = "REGLAS_DENUE"
    resultado["id_denue_origen_mh"] = ""
    auditoria = []

    # Santa Ana Xalmimilulco: primero se usa ID DENUE y luego se crean puntos
    # suplementarios para los registros sin correspondencia vigente.
    ruta_xalmi = Path(root) / "data/processed/mh/xalmi/capa final MH.shp"
    xalmi = gpd.read_file(ruta_xalmi).to_crs(4326)
    ids_auditable = set(auditable["d_llave"].astype(str))
    ids_resultado = set(resultado["d_llave"].astype(str))
    nuevas = []
    for indice, fila in xalmi.iterrows():
        id_valor = fila.get("ID DENUE")
        id_denue = "" if pd.isna(id_valor) else re.sub(r"\.0$", "", str(id_valor)).strip()
        nombre = str(fila.get("Nombre", "")).strip()
        if id_denue and id_denue in ids_resultado:
            mask = resultado["d_llave"].astype(str).eq(id_denue)
            resultado.loc[mask, "evidencia_hidrica"] = "SI"
            resultado.loc[mask, "fuente_universo_hidrico"] += "+MH_XALMI"
            resultado.loc[mask, "fuente_evidencia_hidrica"] = "MH_TRABAJO_CAMPO"
            resultado.loc[mask, "id_denue_origen_mh"] = id_denue
            accion = "YA_PRESENTE"
            id_salida = id_denue
        elif id_denue and id_denue in ids_auditable:
            original = auditable[auditable["d_llave"].astype(str).eq(id_denue)].iloc[0].to_dict()
            original["evidencia_hidrica_original"] = original.get("evidencia_hidrica", "")
            original["evidencia_hidrica"] = "SI"
            original["fuente_universo_hidrico"] = "MH_XALMI_RECUPERADO"
            original["fuente_evidencia_hidrica"] = "MH_TRABAJO_CAMPO"
            original["id_denue_origen_mh"] = id_denue
            nuevas.append(original)
            ids_resultado.add(id_denue)
            accion = "AGREGADO_DESDE_DENUE"
            id_salida = id_denue
        else:
            sufijo = id_denue or f"SIN_ID_{int(indice) + 1:03d}"
            id_salida = f"MH_XALMI_{sufijo}"
            nueva = _fila_sintetica(
                resultado.columns, id_salida, nombre, "Huejotzingo",
                "Santa Ana Xalmimilulco", fila.geometry,
            )
            nueva["fuente_universo_hidrico"] = "MH_XALMI_SUPLEMENTARIO"
            nueva["fuente_evidencia_hidrica"] = "MH_TRABAJO_CAMPO"
            nueva["id_denue_origen_mh"] = id_denue
            nuevas.append(nueva)
            ids_resultado.add(id_salida)
            accion = "AGREGADO_SUPLEMENTARIO"
        auditoria.append({
            "fuente": "MH_XALMI", "nombre_mh": nombre, "id_mh": id_denue,
            "id_salida": id_salida, "accion": accion, "distancia_match_m": "",
        })

    # Huejotzingo: el ID del CSV no es DENUE. Se vincula por nombre y distancia.
    ruta_huejo = Path(root) / "data/processed/mh/huejo/base_huejo(Hoja1) (1).csv"
    huejo = pd.read_csv(ruta_huejo, encoding="utf-8-sig", dtype=str).fillna("")
    huejo = huejo[huejo["Nombre"].str.strip().ne("")].copy()
    coords = huejo["Coordenadas "].map(_coordenada)
    huejo["lat"] = coords.map(lambda x: x[0])
    huejo["lon"] = coords.map(lambda x: x[1])
    huejo = gpd.GeoDataFrame(
        huejo,
        geometry=gpd.points_from_xy(huejo["lon"], huejo["lat"]), crs=4326,
    )
    candidatos = auditable[
        auditable["localidad"].astype(str).map(_normalizar).eq("huejotzingo")
    ].copy()
    candidatos_m = candidatos.to_crs(32614)
    huejo_m = huejo.to_crs(32614)

    for indice, fila_m in huejo_m.iterrows():
        distancias = candidatos_m.geometry.distance(fila_m.geometry)
        cercano_idx = distancias.idxmin()
        distancia = float(distancias.loc[cercano_idx])
        candidato = candidatos.loc[cercano_idx]
        similitud = SequenceMatcher(
            None, _normalizar(fila_m["Nombre"]), _normalizar(candidato["nom_est"])
        ).ratio()
        coincide = distancia <= 35 and similitud >= 0.45
        if coincide:
            id_denue = str(candidato["d_llave"])
            if id_denue in ids_resultado:
                mask = resultado["d_llave"].astype(str).eq(id_denue)
                resultado.loc[mask, "evidencia_hidrica"] = "SI"
                resultado.loc[mask, "fuente_universo_hidrico"] += "+MH_HUEJO"
                resultado.loc[mask, "fuente_evidencia_hidrica"] = "MH_TRABAJO_CAMPO"
                accion = "YA_PRESENTE"
            else:
                original = candidato.to_dict()
                original["evidencia_hidrica_original"] = original.get("evidencia_hidrica", "")
                original["evidencia_hidrica"] = "SI"
                original["fuente_universo_hidrico"] = "MH_HUEJO_RECUPERADO"
                original["fuente_evidencia_hidrica"] = "MH_TRABAJO_CAMPO"
                original["id_denue_origen_mh"] = id_denue
                nuevas.append(original)
                ids_resultado.add(id_denue)
                accion = "AGREGADO_DESDE_DENUE"
            id_salida = id_denue
        else:
            id_salida = f"MH_HUEJO_{str(fila_m['ID']).zfill(3)}"
            nueva = _fila_sintetica(
                resultado.columns, id_salida, str(fila_m["Nombre"]).strip(),
                "Huejotzingo", "Huejotzingo", huejo.loc[indice].geometry,
            )
            nueva["fuente_universo_hidrico"] = "MH_HUEJO_SUPLEMENTARIO"
            nueva["fuente_evidencia_hidrica"] = "MH_TRABAJO_CAMPO"
            nuevas.append(nueva)
            ids_resultado.add(id_salida)
            accion = "AGREGADO_SUPLEMENTARIO"
        auditoria.append({
            "fuente": "MH_HUEJO", "nombre_mh": fila_m["Nombre"],
            "id_mh": fila_m["ID"], "id_salida": id_salida, "accion": accion,
            "distancia_match_m": round(distancia, 1), "similitud_nombre": round(similitud, 3),
        })

    if nuevas:
        agregado = gpd.GeoDataFrame(nuevas, geometry="geometry", crs=4326)
        resultado = pd.concat([resultado, agregado], ignore_index=True)
        resultado = gpd.GeoDataFrame(resultado, geometry="geometry", crs=4326)
    if resultado["d_llave"].astype(str).duplicated().any():
        raise ValueError("La integracion MH produjo identificadores duplicados.")
    return resultado, pd.DataFrame(auditoria)
