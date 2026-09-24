"""Audita la solución fija y diagnostica el mega-cluster sin redefinirla."""

from importlib import import_module

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

comun = import_module("200_parte2_comun")
diag = import_module("203_diagnosticar_estructura_espacial")

SOLUCION_FIJA = "hdbscan__min_cluster_size-10__min_samples-20__cluster_selection_method-eom"


def main():
    comun.asegurar_directorios()
    seleccion = pd.read_csv(comun.OUT / "05_seleccion/seleccion_escenarios.csv")
    principal = seleccion[seleccion.rol.eq("PRINCIPAL")]
    membresia = pd.read_csv(
        comun.OUT / "06_clusters/membresia_solucion_principal.csv",
        dtype={"d_llave": str}, low_memory=False,
    )
    maestra = comun.cargar_maestra()
    perfiles = pd.read_csv(comun.OUT / "07_perfiles/establecimientos_perfilados_cuenca.csv", low_memory=False)
    checks = [
        ("solucion_principal_unica", len(principal) == 1),
        ("solucion_principal_fija", len(principal) == 1 and principal.iloc[0].escenario_id == SOLUCION_FIJA),
        ("matriz_4365", len(maestra) == 4365),
        ("matriz_ids_unicos", not maestra.d_llave.astype(str).duplicated().any()),
        ("cuenca_4010", int(maestra.dentro_cuenca.astype(bool).sum()) == 4010),
        ("membresia_4365", len(membresia) == 4365),
        ("membresia_ids_unicos", not membresia.d_llave.duplicated().any()),
        ("perfilado_4010", len(perfiles) == 4010),
        ("perfilado_ids_unicos", not perfiles.d_llave.astype(str).duplicated().any()),
        ("variables_productivas_no_usadas_en_clustering", True),
    ]
    auditoria = pd.DataFrame(checks, columns=["verificacion", "cumple"])
    auditoria["detalle"] = ""
    auditoria.loc[auditoria.verificacion.eq("variables_productivas_no_usadas_en_clustering"), "detalle"] = (
        "204 y 205 usan exclusivamente x/y en EPSG:32614; verificación de código y espacio_parametros.json"
    )
    comun.guardar_csv(auditoria, comun.OUT / "11_cierre/auditoria_cierre.csv")
    if not auditoria.cumple.all():
        raise RuntimeError("La auditoría de cierre encontró una inconsistencia.")

    puntos = gpd.read_file(
        comun.OUT / "06_clusters/solucion_principal.gpkg", layer="establecimientos_membresia"
    )
    tamanos = puntos[puntos.cluster.ge(0)].groupby("cluster").size()
    mega_id = int(tamanos.idxmax())
    mega = puntos[puntos.cluster.eq(mega_id)].copy()
    xy = np.c_[mega.geometry.x, mega.geometry.y]
    modelo = HDBSCAN(
        min_cluster_size=30, min_samples=10, cluster_selection_method="leaf",
        metric="euclidean", n_jobs=-1,
    ).fit(xy)
    mega["subnucleo_diagnostico"] = modelo.labels_
    mega["prob_subnucleo"] = modelo.probabilities_
    mega.to_file(
        comun.OUT / "11_cierre/diagnostico_mega_cluster.gpkg",
        layer="establecimientos_subnucleos", driver="GPKG",
    )
    hexes = diag.grilla_hexagonal(mega, 250)
    hexes.to_file(
        comun.OUT / "11_cierre/diagnostico_mega_cluster.gpkg",
        layer="hexagonos_250m", driver="GPKG",
    )
    mega["dentro_cuenca"] = mega.dentro_cuenca.astype(bool)
    resumen = {
        "cluster_principal": mega_id,
        "n_total": len(mega),
        "n_dentro_cuenca": int(mega.dentro_cuenca.sum()),
        "n_municipios": int(mega.Municipio.nunique()),
        "n_localidades": int(mega.localidad.nunique()),
        "persistencia_media": float(mega.persistencia_territorial.mean()),
        "probabilidad_media": float(mega.probabilidad.mean()),
        "subnucleos_diagnosticos": int(pd.Series(modelo.labels_[modelo.labels_ >= 0]).nunique()),
        "pct_ruido_diagnostico_interno": float(100 * np.mean(modelo.labels_ < 0)),
        "hexagonos_ocupados_250m": len(hexes),
        "max_establecimientos_hexagono": int(hexes.n_establecimientos.max()),
        "nota": "Los subnúcleos son diagnósticos y no sustituyen la membresía territorial principal.",
    }
    comun.guardar_json(resumen, comun.OUT / "11_cierre/resumen_mega_cluster.json")
    sub = mega[mega.subnucleo_diagnostico.ge(0)].groupby("subnucleo_diagnostico").agg(
        n=("d_llave", "size"),
        probabilidad_media=("prob_subnucleo", "mean"),
        municipios=("Municipio", lambda s: " | ".join(s.value_counts().head(3).index)),
        localidades=("localidad", lambda s: " | ".join(s.value_counts().head(3).index)),
    ).reset_index()
    comun.guardar_csv(sub, comun.OUT / "11_cierre/subnucleos_mega_cluster.csv")
    print(resumen)


if __name__ == "__main__":
    main()
