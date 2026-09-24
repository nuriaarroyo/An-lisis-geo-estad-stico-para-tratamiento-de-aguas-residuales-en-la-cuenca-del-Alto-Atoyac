# Presentación de Parte 2

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
- 22 clusters y 13.4% de ruido en la detección municipal.
- 18 clusters intersectan la cuenca.
- 578 establecimientos dispersos dentro de la cuenca.

---

## Robustez

- ARI top-5: 0.937.
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
