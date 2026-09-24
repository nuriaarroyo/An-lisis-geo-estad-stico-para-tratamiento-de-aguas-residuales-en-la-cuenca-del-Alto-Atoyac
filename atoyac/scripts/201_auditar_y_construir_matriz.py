"""Audita las fuentes y construye la matriz maestra de Parte 2."""

from importlib import import_module

import numpy as np
import pandas as pd

comun = import_module("200_parte2_comun")


def main():
    comun.asegurar_directorios()
    municipal, cuenca = comun.cargar_fuentes()
    if municipal["d_llave"].duplicated().any() or cuenca["d_llave"].duplicated().any():
        raise ValueError("Las fuentes contienen d_llave duplicado.")
    ids_cuenca = set(cuenca["d_llave"].astype(str))
    faltantes = ids_cuenca - set(municipal["d_llave"].astype(str))
    if faltantes:
        raise ValueError(f"Hay {len(faltantes)} registros de cuenca fuera del universo municipal.")

    maestra = municipal.copy()
    maestra["d_llave"] = maestra["d_llave"].astype(str)
    maestra["dentro_cuenca"] = maestra["d_llave"].isin(ids_cuenca)
    codigo = comun.codigo_limpio(maestra["cve_scian"])
    texto = (
        maestra["nom_est"].fillna("").astype(str) + " "
        + maestra["raz_soc"].fillna("").astype(str)
    ).map(comun.normalizar_texto)
    maestra["scian_3"] = codigo.str[:3]
    maestra["scian_4"] = codigo.str[:4]
    maestra["scian_6"] = codigo.str[:6]
    maestra["actividad_lavanderia_tintoreria"] = codigo.eq("812210")
    maestra["actividad_acabado_textil"] = codigo.eq("313310")
    maestra["actividad_confeccion"] = codigo.str.startswith("3152")
    maestra["actividad_fabricacion_telas"] = codigo.str.startswith(("3132", "3133"))
    maestra["actividad_tejido_hilado"] = codigo.str.startswith(("3131", "3151"))
    maestra["actividad_bordado_deshilado"] = codigo.eq("314991") | texto.str.contains(
        r"\b(?:bordad|deshilad|deshebrad)", regex=True
    )
    maestra["senal_pantalon"] = texto.str.contains(r"\bpantalon(?:es)?\b", regex=True)
    maestra["senal_mezclilla_o_pantalon"] = (
        comun.booleano(maestra["mezclilla"]) | maestra["senal_pantalon"]
    )
    maestra["universo_conceptual"] = comun.NOMBRE_UNIVERSO

    comun.guardar_csv(maestra, comun.OUT / "01_matriz/matriz_maestra_establecimientos.csv")
    auditoria = pd.DataFrame([
        {"metrica": "registros_municipales_deteccion", "valor": len(municipal)},
        {"metrica": "registros_dentro_cuenca", "valor": len(cuenca)},
        {"metrica": "registros_fuera_cuenca", "valor": len(municipal) - len(cuenca)},
        {"metrica": "ids_duplicados_municipal", "valor": int(municipal.d_llave.duplicated().sum())},
        {"metrica": "ids_duplicados_cuenca", "valor": int(cuenca.d_llave.duplicated().sum())},
        {"metrica": "coordenadas_validas", "valor": int(pd.to_numeric(municipal.Latitud, errors="coerce").notna().sum())},
        {"metrica": "municipios_deteccion", "valor": municipal.Municipio.nunique()},
        {"metrica": "localidades_deteccion", "valor": municipal.localidad.nunique()},
        {"metrica": "municipios_dentro_cuenca", "valor": cuenca.Municipio.nunique()},
        {"metrica": "localidades_dentro_cuenca", "valor": cuenca.localidad.nunique()},
    ])
    comun.guardar_csv(auditoria, comun.OUT / "00_auditoria/resumen_universo.csv")
    fuentes = pd.DataFrame([
        {"rol": "deteccion_y_borde", "ruta": str(comun.SOURCE_MUNICIPAL.relative_to(comun.ROOT)), "registros": len(municipal), "sha256": comun.sha256(comun.SOURCE_MUNICIPAL)},
        {"rol": "interpretacion_cuenca", "ruta": str(comun.SOURCE_CUENCA.relative_to(comun.ROOT)), "registros": len(cuenca), "sha256": comun.sha256(comun.SOURCE_CUENCA)},
        {"rol": "poligono_cuenca", "ruta": str(comun.CUENCA.relative_to(comun.ROOT)), "registros": np.nan, "sha256": comun.sha256(comun.CUENCA)},
    ])
    comun.guardar_csv(fuentes, comun.OUT / "00_auditoria/inventario_fuentes.csv")
    print(auditoria.to_string(index=False))


if __name__ == "__main__":
    main()
