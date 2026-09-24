"""Compara particiones y selecciona soluciones usando sólo criterios espaciales."""

from importlib import import_module

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, HDBSCAN
from sklearn.metrics import adjusted_rand_score

comun = import_module("200_parte2_comun")


def metricas_continuidad(labels, xy):
    filas = []
    for cluster in sorted(set(labels) - {-1}):
        parte = xy[np.asarray(labels) == cluster]
        dx = parte[:, 0].max() - parte[:, 0].min()
        dy = parte[:, 1].max() - parte[:, 1].min()
        diagonal = float(np.hypot(dx, dy))
        filas.append((len(parte), diagonal))
    if not filas:
        return {"bbox_mediana_km": np.nan, "bbox_max_km": np.nan, "chaining_proxy_max": np.nan}
    tamanos = np.array([x[0] for x in filas])
    diagonales = np.array([x[1] for x in filas])
    return {
        "bbox_mediana_km": float(np.median(diagonales) / 1000),
        "bbox_max_km": float(diagonales.max() / 1000),
        "chaining_proxy_max": float(np.max(diagonales / np.sqrt(tamanos)) / 1000),
    }


def emparejar_clusters(base, alternativa):
    resultados = {}
    alt_clusters = sorted(set(alternativa) - {-1})
    for cluster in sorted(set(base) - {-1}):
        a = base == cluster
        mejor_cluster, mejor_j = None, 0.0
        for otro in alt_clusters:
            b = alternativa == otro
            union = np.logical_or(a, b).sum()
            j = np.logical_and(a, b).sum() / union if union else 0.0
            if j > mejor_j:
                mejor_cluster, mejor_j = otro, j
        resultados[cluster] = (mejor_cluster, mejor_j)
    return resultados


def estabilidad_perturbacion(fila, xy, labels_base, repeticiones=3, sigma_m=25):
    """ARI ante desplazamientos gaussianos pequeños y reproducibles."""
    if fila.metodo not in {"DBSCAN", "HDBSCAN"}:
        return np.nan
    semillas = np.random.SeedSequence(comun.SEMILLA).spawn(repeticiones)
    valores = []
    for semilla in semillas:
        rng = np.random.default_rng(semilla)
        perturbado = xy + rng.normal(0, sigma_m, size=xy.shape)
        if fila.metodo == "DBSCAN":
            modelo = DBSCAN(
                eps=float(fila.eps_m), min_samples=int(fila.min_samples), n_jobs=-1
            )
        else:
            modelo = HDBSCAN(
                min_cluster_size=int(fila.min_cluster_size),
                min_samples=int(fila.min_samples),
                cluster_selection_method=str(fila.cluster_selection_method),
                metric="euclidean", n_jobs=-1,
            )
        valores.append(adjusted_rand_score(labels_base, modelo.fit_predict(perturbado)))
    return float(np.mean(valores))


def main():
    comun.asegurar_directorios()
    resumen = pd.read_csv(comun.OUT / "04_clustering/resumen_escenarios.csv")
    mem = comun.leer_membresias()
    puntos = comun.leer_puntos_metricos().sort_values("d_llave").reset_index(drop=True)
    ids = puntos.d_llave.astype(str).to_numpy()
    xy = np.c_[puntos.geometry.x, puntos.geometry.y]
    escenarios = resumen.escenario_id.tolist()
    etiquetas = {}
    for eid in escenarios:
        parte = mem[mem.escenario_id.eq(eid)].set_index("d_llave").reindex(ids)
        etiquetas[eid] = parte.cluster.to_numpy(dtype=int)

    pares = []
    ari_por_escenario = {e: [] for e in escenarios}
    for i, e1 in enumerate(escenarios):
        for e2 in escenarios[i + 1:]:
            ari = adjusted_rand_score(etiquetas[e1], etiquetas[e2])
            pares.append({"escenario_a": e1, "escenario_b": e2, "ari": ari})
            if resumen.set_index("escenario_id").loc[e1, "metodo"] == resumen.set_index("escenario_id").loc[e2, "metodo"]:
                ari_por_escenario[e1].append(ari)
                ari_por_escenario[e2].append(ari)
    comun.guardar_csv(pd.DataFrame(pares), comun.OUT / "05_seleccion/ari_entre_escenarios.csv")

    continuidad = []
    for eid in escenarios:
        continuidad.append({"escenario_id": eid, **metricas_continuidad(etiquetas[eid], xy)})
    resumen = resumen.merge(pd.DataFrame(continuidad), on="escenario_id", how="left")
    resumen["ari_mediana_mismo_metodo"] = resumen.escenario_id.map(
        lambda e: float(np.median(ari_por_escenario[e])) if ari_por_escenario[e] else np.nan
    )
    resumen["ari_top5_mismo_metodo"] = resumen.escenario_id.map(
        lambda e: float(np.mean(sorted(ari_por_escenario[e], reverse=True)[:5])) if ari_por_escenario[e] else np.nan
    )
    resumen["ari_perturbacion_25m"] = [
        estabilidad_perturbacion(fila, xy, etiquetas[fila.escenario_id])
        for fila in resumen.itertuples(index=False)
    ]

    prob = resumen["probabilidad_media"].fillna(0.75).clip(0, 1)
    penal_ruido = (resumen["pct_ruido"] / 100 - 0.25).abs()
    penal_mega = np.maximum(0, resumen["pct_cluster_mayor"] / 100 - 0.35)
    penal_extremos = np.maximum(0, 3 - resumen["n_clusters"]) / 3 + np.maximum(0, resumen["n_clusters"] - 80) / 80
    penal_chaining = np.maximum(0, resumen["chaining_proxy_max"].fillna(0) - 1.5) / 5
    resumen["puntaje_espacial"] = (
        0.40 * resumen["ari_top5_mismo_metodo"].fillna(0)
        + 0.15 * resumen["ari_perturbacion_25m"].fillna(0)
        + 0.20 * prob
        + 0.15 * (1 - penal_ruido.clip(0, 1))
        + 0.15 * (1 - penal_mega.clip(0, 1))
        - 0.10 * penal_extremos
        - 0.10 * penal_chaining.clip(0, 1)
    )
    elegibles = resumen[
        resumen.n_clusters.between(3, 80)
        & resumen.pct_ruido.between(1, 75)
        & resumen.pct_cluster_mayor.le(60)
    ].copy()
    if elegibles[elegibles.metodo.eq("HDBSCAN")].empty:
        raise RuntimeError("Ningún escenario HDBSCAN pasó los criterios espaciales mínimos.")
    principal = elegibles[elegibles.metodo.eq("HDBSCAN")].nlargest(1, "puntaje_espacial").iloc[0].escenario_id
    referencia = elegibles[elegibles.metodo.eq("DBSCAN")].nlargest(1, "puntaje_espacial").iloc[0].escenario_id
    sensibilidad = elegibles[
        elegibles.metodo.eq("HDBSCAN") & ~elegibles.escenario_id.eq(principal)
    ].nlargest(4, "puntaje_espacial").escenario_id.tolist()
    resumen["rol"] = "NO_SELECCIONADO"
    resumen.loc[resumen.escenario_id.eq(principal), "rol"] = "PRINCIPAL"
    resumen.loc[resumen.escenario_id.eq(referencia), "rol"] = "REFERENCIA_DBSCAN"
    resumen.loc[resumen.escenario_id.isin(sensibilidad), "rol"] = "SENSIBILIDAD"
    resumen = resumen.sort_values(["rol", "puntaje_espacial"], ascending=[True, False])
    comun.guardar_csv(resumen, comun.OUT / "05_seleccion/seleccion_escenarios.csv")

    base = etiquetas[principal]
    seleccionados = [principal, referencia, *sensibilidad]
    persistencia_cluster = []
    soporte = np.zeros(len(ids), dtype=float)
    denominador = max(1, len(seleccionados) - 1)
    for otro in seleccionados[1:]:
        matches = emparejar_clusters(base, etiquetas[otro])
        for cluster, (match, jaccard) in matches.items():
            miembros = base == cluster
            coincide = etiquetas[otro] == match if match is not None else np.zeros(len(ids), dtype=bool)
            soporte[miembros] += coincide[miembros].astype(float)
            persistencia_cluster.append({
                "cluster_principal": cluster, "escenario_comparado": otro,
                "cluster_correspondiente": match, "jaccard": jaccard,
            })
        soporte[base < 0] += (etiquetas[otro][base < 0] < 0).astype(float)
    soporte /= denominador
    persistencia = pd.DataFrame({
        "d_llave": ids, "cluster_principal": base,
        "persistencia_territorial": soporte,
        "clase_persistencia": pd.cut(
            soporte, bins=[-0.01, 0.49, 0.79, 1.0],
            labels=["SENSIBLE", "ESTABLE", "NUCLEO_ROBUSTO"],
        ).astype(str),
    })
    comun.guardar_csv(persistencia, comun.OUT / "05_seleccion/persistencia_establecimientos.csv")
    pc = pd.DataFrame(persistencia_cluster)
    comun.guardar_csv(pc, comun.OUT / "05_seleccion/jaccard_clusters_seleccionados.csv")
    decision = {
        "solucion_principal": principal,
        "referencia_dbscan": referencia,
        "sensibilidad": sensibilidad,
        "criterio": "Puntaje reproducible construido sólo con estabilidad de partición, pertenencia, ruido, mega-clusters, número de clusters y chaining proxy.",
        "advertencia": "La solución principal es operativa y no se interpreta como una partición territorial verdadera única.",
    }
    comun.guardar_json(decision, comun.OUT / "05_seleccion/decision_solucion.json")
    print(decision)


if __name__ == "__main__":
    main()
