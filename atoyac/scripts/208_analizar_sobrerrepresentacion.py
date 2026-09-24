"""Mide sobrerrepresentación de señales respecto del universo dentro de cuenca."""

from importlib import import_module

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

comun = import_module("200_parte2_comun")
perfil = import_module("207_perfilar_clusters")


def ajustar_bh(pvalores):
    p = np.asarray(pvalores, dtype=float)
    orden = np.argsort(p)
    ajustados = np.empty(len(p))
    acumulado = 1.0
    for rango in range(len(p) - 1, -1, -1):
        idx = orden[rango]
        valor = p[idx] * len(p) / (rango + 1)
        acumulado = min(acumulado, valor)
        ajustados[idx] = min(1.0, acumulado)
    return ajustados


def main():
    datos = pd.read_csv(
        comun.OUT / "07_perfiles/establecimientos_perfilados_cuenca.csv",
        encoding="utf-8-sig", low_memory=False,
    )
    for c in perfil.SENALES:
        datos[c] = comun.booleano(datos[c])
    total = len(datos)
    filas = []
    for grupo, parte in datos.groupby("grupo_espacial"):
        fuera = datos[~datos.index.isin(parte.index)]
        for senal in perfil.SENALES:
            a = int(parte[senal].sum())
            b = len(parte) - a
            c = int(fuera[senal].sum())
            d = len(fuera) - c
            prev_g = a / len(parte)
            prev_u = int(datos[senal].sum()) / total
            lift = prev_g / prev_u if prev_u else np.nan
            odds, p = fisher_exact([[a, b], [c, d]], alternative="two-sided")
            # Corrección de Haldane-Anscombe para IC estable con ceros.
            log_or = np.log((a + 0.5) * (d + 0.5) / ((b + 0.5) * (c + 0.5)))
            se = np.sqrt(sum(1 / (x + 0.5) for x in [a, b, c, d]))
            filas.append({
                "grupo_espacial": grupo, "senal": senal, "n_grupo": len(parte),
                "conteo_senal": a, "prevalencia_grupo": prev_g,
                "prevalencia_universo": prev_u, "diferencia_prevalencia": prev_g - prev_u,
                "lift": lift, "log2_lift": np.log2(lift) if lift and lift > 0 else np.nan,
                "odds_ratio_fisher": odds, "or_ic95_inf": np.exp(log_or - 1.96 * se),
                "or_ic95_sup": np.exp(log_or + 1.96 * se), "p_fisher": p,
            })
    resultado = pd.DataFrame(filas)
    resultado["p_ajustada_bh"] = ajustar_bh(resultado.p_fisher)
    resultado["evidencia_descriptiva_suficiente"] = (
        resultado.conteo_senal.ge(5)
        & resultado.prevalencia_grupo.ge(0.05)
        & resultado.lift.ge(1.25)
        & resultado.p_ajustada_bh.le(0.05)
    )
    comun.guardar_csv(resultado, comun.OUT / "08_sobrerrepresentacion/sobrerrepresentacion_senales.csv")
    print(f"Comparaciones={len(resultado):,}; suficientes={int(resultado.evidencia_descriptiva_suficiente.sum())}")


if __name__ == "__main__":
    main()
