"""Construye perfiles económicos posteriores a la selección espacial."""

from importlib import import_module

import pandas as pd

comun = import_module("200_parte2_comun")


SENALES = [
    "textil", "mezclilla", "humedo_explicito", "lavado_generico", "produccion",
    "maquila", "proceso_seco_explicito", "scian_textil", "scian_acabado_humedo",
    "scian_lavanderia", "actividad_lavanderia_tintoreria", "actividad_acabado_textil",
    "actividad_confeccion", "actividad_fabricacion_telas", "actividad_tejido_hilado",
    "actividad_bordado_deshilado", "senal_pantalon", "senal_mezclilla_o_pantalon",
]


def main():
    maestra = comun.cargar_maestra()
    membresia = pd.read_csv(
        comun.OUT / "06_clusters/membresia_solucion_principal.csv", dtype={"d_llave": str}
    )[["d_llave", "cluster", "probabilidad", "persistencia_territorial", "tipo_resultado_espacial"]]
    maestra["d_llave"] = maestra.d_llave.astype(str)
    datos = maestra.merge(membresia, on="d_llave", validate="one_to_one")
    datos = datos[datos.dentro_cuenca.astype(bool)].copy()
    datos["grupo_espacial"] = datos.cluster.map(lambda x: "RUIDO_DISPERSO" if x < 0 else f"CLUSTER_{int(x):03d}")
    for c in SENALES:
        datos[c] = comun.booleano(datos[c])

    resumenes = []
    for grupo, parte in datos.groupby("grupo_espacial"):
        fila = {
            "grupo_espacial": grupo, "cluster": int(parte.cluster.iloc[0]),
            "n_dentro_cuenca": len(parte), "n_municipios": parte.Municipio.nunique(),
            "n_localidades": parte.localidad.nunique(),
            "probabilidad_media": parte.probabilidad.mean(),
            "persistencia_media": parte.persistencia_territorial.mean(),
            "municipio_principal": parte.Municipio.value_counts().index[0],
            "localidad_principal": parte.localidad.value_counts().index[0],
        }
        for c in SENALES:
            fila[f"n__{c}"] = int(parte[c].sum())
            fila[f"pct__{c}"] = 100 * parte[c].mean()
        resumenes.append(fila)
    comun.guardar_csv(pd.DataFrame(resumenes), comun.OUT / "07_perfiles/perfiles_clusters.csv")

    dimensiones = {
        "scian_3": "composicion_scian_3.csv", "scian_4": "composicion_scian_4.csv",
        "scian_6": "composicion_scian_6.csv",
        "Descripcion estrato personal ocupado": "composicion_personal.csv",
        "evidencia_hidrica": "composicion_evidencia_hidrica.csv",
        "Municipio": "composicion_municipal.csv", "localidad": "composicion_localidad.csv",
    }
    for variable, nombre in dimensiones.items():
        tabla = datos.groupby(["grupo_espacial", variable], dropna=False).size().rename("n").reset_index()
        tabla["pct_grupo"] = 100 * tabla.n / tabla.groupby("grupo_espacial").n.transform("sum")
        comun.guardar_csv(tabla, comun.OUT / f"07_perfiles/{nombre}")
    comun.guardar_csv(datos, comun.OUT / "07_perfiles/establecimientos_perfilados_cuenca.csv")
    print(f"Perfiles creados: {datos.grupo_espacial.nunique()} grupos, incluido ruido.")


if __name__ == "__main__":
    main()
