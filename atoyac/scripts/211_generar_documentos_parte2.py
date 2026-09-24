"""Actualiza el reporte técnico y la presentación textual de Parte 2."""

from importlib import import_module

import pandas as pd

comun = import_module("200_parte2_comun")


def main():
    decision = pd.read_csv(comun.OUT / "05_seleccion/seleccion_escenarios.csv")
    principal = decision[decision.rol.eq("PRINCIPAL")].iloc[0]
    borde = pd.read_csv(comun.OUT / "06_clusters/resumen_clusters_borde.csv")
    perfiles = pd.read_csv(comun.OUT / "07_perfiles/perfiles_clusters.csv")
    coexist = pd.read_csv(comun.OUT / "07_perfiles/analisis_coexistencia_lavanderias_manufactura.csv")
    sobre = pd.read_csv(comun.OUT / "08_sobrerrepresentacion/sobrerrepresentacion_senales.csv")
    dentro = perfiles[~perfiles.grupo_espacial.eq("RUIDO_DISPERSO")]
    ruido = perfiles[perfiles.grupo_espacial.eq("RUIDO_DISPERSO")].iloc[0]
    tipos = coexist[~coexist.grupo_espacial.eq("RUIDO_DISPERSO")].tipo_coexistencia_descriptivo.value_counts()
    reporte = f"""# Reporte técnico de Parte 2

## Estado del análisis

Documento generado reproduciblemente por `211_generar_documentos_parte2.py`. La denominación oficial es **{comun.NOMBRE_UNIVERSO}**.

## Universo y borde

- Detección espacial: 4,365 establecimientos de los municipios de apoyo.
- Interpretación principal: 4,010 establecimientos dentro de la cuenca.
- Registros fuera de cuenca utilizados para evitar fragmentación de borde: 355.
- CRS de análisis: EPSG:32614; distancia euclidiana en metros.

## Separación metodológica

La detección y selección emplearon únicamente coordenadas proyectadas. SCIAN, señales textuales, evidencia hídrica y estrato de personal se incorporaron después de seleccionar la solución espacial.

## Solución principal

- Escenario: `{principal.escenario_id}`.
- Método: {principal.metodo}.
- Clusters detectados sobre el universo municipal: {int(principal.n_clusters)}.
- Ruido municipal: {int(principal.n_ruido)} ({principal.pct_ruido:.1f}%).
- Cluster mayor: {int(principal.tam_max)} ({principal.pct_cluster_mayor:.1f}% del universo de detección).
- Probabilidad media de pertenencia: {principal.probabilidad_media:.3f}.
- Estabilidad ARI promedio de las cinco configuraciones más próximas: {principal.ari_top5_mismo_metodo:.3f}.
- Clusters con establecimientos dentro de la cuenca: {len(dentro)}.
- Actividad dispersa dentro de la cuenca: {int(ruido.n_dentro_cuenca)} establecimientos.
- Clusters que cruzan el límite: {int(borde.cruza_limite_cuenca.sum())}.

La configuración es una solución operativa principal, no una partición territorial verdadera única. Se conserva una referencia DBSCAN y cuatro escenarios HDBSCAN de sensibilidad.

## Coexistencia sectorial descriptiva

Clasificación posterior de los clusters: {tipos.to_dict()}. Esta tipología no intervino en su construcción. La tabla auditable se encuentra en `outputs/parte_2/07_perfiles/analisis_coexistencia_lavanderias_manufactura.csv`.

## Sobrerrepresentación

Se ejecutaron {len(sobre):,} comparaciones cluster-señal. {int(sobre.evidencia_descriptiva_suficiente.sum())} cumplen simultáneamente conteo mínimo, prevalencia, lift y significancia con ajuste Benjamini–Hochberg. Estos criterios son descriptivos y no equivalen a causalidad ni a validación de procesos reales.

## Limitaciones vigentes

- DENUE puede omitir actividad informal o domiciliaria.
- SCIAN 812210 no distingue lavandería comercial de industrial.
- Las coordenadas válidas no garantizan precisión predial.
- El mega-cluster principal exige interpretación multiescala y comparación con sensibilidad.
- Cercanía o coexistencia no demuestran relación productiva, consumo de agua ni descarga.
"""
    presentacion = f"""# Presentación de Parte 2

---

## Pregunta

¿Dónde existen concentraciones del universo sectorial ampliado y qué actividades contienen?

---

## Universo

- 4,365 establecimientos para detectar continuidad territorial.
- 4,010 dentro de la cuenca para interpretación.
- Se conservan procesos secos, `SIN_EVIDENCIA` y ruido.

---

## Método

- EPSG:32614 y metros.
- 24 DBSCAN, 30 HDBSCAN y 3 OPTICS.
- KDE y hexágonos en tres resoluciones como diagnósticos.
- Selección exclusivamente espacial.

---

## Solución principal

- HDBSCAN: `min_cluster_size=10`, `min_samples=20`, EOM.
- {int(principal.n_clusters)} clusters y {principal.pct_ruido:.1f}% de ruido en la detección municipal.
- {len(dentro)} clusters intersectan la cuenca.
- {int(ruido.n_dentro_cuenca)} establecimientos dispersos dentro de la cuenca.

---

## Robustez

- ARI top-5: {principal.ari_top5_mismo_metodo:.3f}.
- Persistencia por establecimiento y Jaccard por cluster.
- Una referencia DBSCAN y cuatro escenarios próximos de sensibilidad.

---

## Perfilado posterior

- SCIAN, confección, telas, acabado, lavandería, maquila y señales multilabel.
- Lift, diferencia de prevalencias, odds ratio, Fisher e IC.
- Corrección Benjamini–Hochberg.

---

## Lectura responsable

La solución principal organiza el análisis, pero no representa una única geografía verdadera. Coexistencia espacial no implica relación productiva ni impacto ambiental.
"""
    (comun.DOCS / "reporte").mkdir(parents=True, exist_ok=True)
    (comun.DOCS / "presentacion").mkdir(parents=True, exist_ok=True)
    (comun.DOCS / "reporte/reporte_tecnico_parte_2.md").write_text(reporte, encoding="utf-8")
    (comun.DOCS / "presentacion/presentacion_parte_2.md").write_text(presentacion, encoding="utf-8")
    print("Reporte y presentación actualizados.")


if __name__ == "__main__":
    main()
