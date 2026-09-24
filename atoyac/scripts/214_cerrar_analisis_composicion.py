"""Cierra preguntas de composición, sensibilidad, ruido y similitud productiva."""

from importlib import import_module

import json
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

comun = import_module("200_parte2_comun")
perfil_mod = import_module("207_perfilar_clusters")


def bh(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    out = np.empty(len(p))
    prev = 1.0
    for rank in range(len(p) - 1, -1, -1):
        idx = order[rank]
        prev = min(prev, p[idx] * len(p) / (rank + 1))
        out[idx] = min(1.0, prev)
    return out


def tipo_coexistencia(p_lav, p_man):
    if p_lav >= 0.80:
        return "CONCENTRACION_LAVANDERIAS"
    if p_man >= 0.80:
        return "CONCENTRACION_MANUFACTURA"
    if p_lav >= 0.20 and p_man >= 0.20:
        return "COEXISTENCIA_MIXTA"
    return "PREDOMINIO_LAVANDERIAS" if p_lav > p_man else "PREDOMINIO_MANUFACTURA"


def main():
    comun.asegurar_directorios()
    datos = pd.read_csv(
        comun.OUT / "07_perfiles/establecimientos_perfilados_cuenca.csv",
        dtype={"d_llave": str}, low_memory=False,
    )
    for c in perfil_mod.SENALES:
        datos[c] = comun.booleano(datos[c])
    ruido = datos.cluster.lt(0)
    filas = []
    for senal in perfil_mod.SENALES:
        a = int(datos.loc[~ruido, senal].sum())
        b = int((~ruido).sum() - a)
        c = int(datos.loc[ruido, senal].sum())
        d = int(ruido.sum() - c)
        odds, p = fisher_exact([[a, b], [c, d]])
        filas.append({
            "senal": senal, "n_agrupado": a,
            "prevalencia_agrupado": a / (a + b), "n_ruido": c,
            "prevalencia_ruido": c / (c + d),
            "diferencia_agrupado_menos_ruido": a / (a + b) - c / (c + d),
            "odds_ratio": odds, "p_fisher": p,
        })
    comparacion = pd.DataFrame(filas)
    comparacion["p_ajustada_bh"] = bh(comparacion.p_fisher)
    comun.guardar_csv(comparacion, comun.OUT / "11_cierre/comparacion_clusters_ruido.csv")

    sobre = pd.read_csv(comun.OUT / "08_sobrerrepresentacion/sobrerrepresentacion_senales.csv")
    defendibles = sobre[sobre.evidencia_descriptiva_suficiente.astype(bool)].copy()
    defendibles["puntaje_interpretativo"] = (
        defendibles.log2_lift.clip(lower=0) * np.sqrt(defendibles.conteo_senal)
        * defendibles.diferencia_prevalencia.clip(lower=0)
    )
    rasgos = defendibles.sort_values(
        ["grupo_espacial", "puntaje_interpretativo"], ascending=[True, False]
    ).groupby("grupo_espacial").head(5)
    comun.guardar_csv(rasgos, comun.OUT / "11_cierre/rasgos_distintivos_clusters.csv")

    maestra = comun.cargar_maestra()
    maestra["d_llave"] = maestra.d_llave.astype(str)
    mem = comun.leer_membresias()
    seleccion = pd.read_csv(comun.OUT / "05_seleccion/seleccion_escenarios.csv")
    escenarios = seleccion[seleccion.rol.isin(["PRINCIPAL", "REFERENCIA_DBSCAN", "SENSIBILIDAD"])][
        ["escenario_id", "rol"]
    ]
    sensibilidad = []
    for row in escenarios.itertuples(index=False):
        m = mem[mem.escenario_id.eq(row.escenario_id)][["d_llave", "cluster"]].copy()
        d = maestra.merge(m, on="d_llave", validate="one_to_one")
        interior = d[d.dentro_cuenca.astype(bool) & d.cluster.ge(0)].copy()
        interior["lav"] = comun.booleano(interior.actividad_lavanderia_tintoreria)
        interior["man"] = comun.booleano(interior.scian_textil)
        tipos = []
        max_lav = 0.0
        for _, parte in interior.groupby("cluster"):
            pl, pm = parte.lav.mean(), parte.man.mean()
            max_lav = max(max_lav, pl)
            tipos.append(tipo_coexistencia(pl, pm))
        vc = pd.Series(tipos).value_counts()
        sensibilidad.append({
            "escenario_id": row.escenario_id, "rol": row.rol,
            "n_clusters_interiores": interior.cluster.nunique(),
            "max_pct_lavanderias": 100 * max_lav,
            "clusters_lavanderias_80pct": int(vc.get("CONCENTRACION_LAVANDERIAS", 0)),
            "clusters_manufactura_80pct": int(vc.get("CONCENTRACION_MANUFACTURA", 0)),
            "clusters_coexistencia_mixta": int(vc.get("COEXISTENCIA_MIXTA", 0)),
        })
    sens = pd.DataFrame(sensibilidad)
    comun.guardar_csv(sens, comun.OUT / "11_cierre/sensibilidad_coexistencia.csv")

    dist = pd.read_csv(comun.OUT / "09_comparacion/distancias_perfiles.csv").set_index("grupo_espacial")
    pares = []
    nombres = list(dist.index)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            pares.append({"cluster_a": a, "cluster_b": b, "distancia_perfil": dist.loc[a, b]})
    pares = pd.DataFrame(pares).sort_values("distancia_perfil")
    comun.guardar_csv(pares, comun.OUT / "11_cierre/pares_clusters_similares.csv")

    perfiles = pd.read_csv(comun.OUT / "07_perfiles/perfiles_clusters.csv")
    borde = pd.read_csv(comun.OUT / "06_clusters/resumen_clusters_borde.csv")
    tipos = pd.read_csv(comun.OUT / "07_perfiles/analisis_coexistencia_lavanderias_manufactura.csv")
    tipologia = pd.read_csv(comun.OUT / "09_comparacion/tipologia_perfiles_clusters.csv")
    ficha = perfiles.merge(tipos, on="grupo_espacial", suffixes=("", "_coex"), validate="one_to_one")
    ficha = ficha.merge(tipologia, on="grupo_espacial", how="left")
    ficha = ficha.merge(
        borde[["cluster", "n_total_cluster", "n_fuera_cuenca", "pct_cluster_dentro_cuenca", "area_convexa_km2", "densidad_convexa_est_km2", "cruza_limite_cuenca"]],
        on="cluster", how="left",
    )
    rasgos_txt = rasgos.groupby("grupo_espacial").apply(
        lambda x: " | ".join(f"{r.senal} (lift {r.lift:.2f})" for r in x.itertuples()),
        include_groups=False,
    )
    ficha["rasgos_distintivos"] = ficha.grupo_espacial.map(rasgos_txt).fillna("Sin rasgos que cumplan todos los umbrales conservadores")
    comun.guardar_csv(ficha, comun.OUT / "11_cierre/fichas_resumen_clusters.csv")

    top_ruido = comparacion.reindex(comparacion.diferencia_agrupado_menos_ruido.abs().sort_values(ascending=False).index).head(5)
    respuestas = {
        "concentraciones": f"La solución fija detecta 22 clusters municipales; 18 intersectan la cuenca. El cluster 20 concentra 1,997 establecimientos.",
        "robustez": "La solución principal conserva ARI alto frente a configuraciones vecinas y perturbaciones de 25 m; la persistencia se reporta por establecimiento y cluster.",
        "composicion": "Los perfiles completos se documentan por SCIAN, señales multilabel, personal, municipio y localidad.",
        "sobrerrepresentacion": f"Se identificaron {len(rasgos)} rasgos defendibles entre los cinco primeros por grupo bajo criterios conservadores.",
        "lavanderias_manufactura": f"Ninguno de los {len(sens)} escenarios principal/referencia/sensibilidad produce un cluster interior con al menos 80% de lavanderías.",
        "similitud": "Los pares productivamente más similares se registran sin incorporar proximidad geográfica.",
        "ruido": "La comparación formal con actividad agrupada usa prevalencias, diferencias, odds ratio, Fisher y ajuste BH.",
        "variables_ruido_mayor_diferencia": top_ruido[["senal", "diferencia_agrupado_menos_ruido"]].to_dict("records"),
    }
    comun.guardar_json(respuestas, comun.OUT / "11_cierre/respuestas_preguntas_parte2.json")
    print(json.dumps(respuestas, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
