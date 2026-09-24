"""Construccion de los tres CSV finales a partir del auditable."""

from pathlib import Path

import pandas as pd


def crear_csv_finales(data, output_dir, prefijo):
    """
    Genera el universo textil y sus dos subconjuntos hidricos.

    Solamente considera decisiones sectoriales INCLUIR o REVISAR. Devuelve
    un diccionario con el nombre logico, ruta y numero de registros de cada
    archivo.
    """
    requeridas = {"sector_textil", "evidencia_hidrica", "d_llave"}
    faltantes = requeridas - set(data.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas para generar los CSV: {sorted(faltantes)}")

    if data["d_llave"].astype(str).duplicated().any():
        raise ValueError("d_llave contiene duplicados en el CSV auditable.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    universo = data.loc[
        data["sector_textil"].isin(["INCLUIR", "REVISAR"])
    ].copy()
    subconjuntos = {
        "textil_hidrico_si_revisar": universo.loc[
            universo["evidencia_hidrica"].isin(["SI", "REVISAR"])
        ].copy(),
        "textil_hidrico_si": universo.loc[
            universo["evidencia_hidrica"].eq("SI")
        ].copy(),
        "universo_textil": universo,
    }

    resultados = {}
    for nombre, tabla in subconjuntos.items():
        ruta = output_dir / f"{prefijo}_{nombre}.csv"
        tabla.to_csv(ruta, index=False, encoding="utf-8-sig")
        resultados[nombre] = {
            "data": tabla,
            "path": ruta,
            "count": len(tabla),
        }

    return resultados
