# 003 — Métodos, parámetros y selección

## Batería inicial

- DBSCAN: `eps` 250, 400, 600, 800, 1,200 y 1,600 metros; `min_samples` 5, 10, 15 y 25.
- HDBSCAN: `min_cluster_size` 10, 20, 30, 50 y 75; `min_samples` 5, 10 y 20; selección EOM y leaf.
- OPTICS: `min_samples` 10, 20 y 30; `xi=0.05`; tamaño mínimo del 1%.
- KDE: anchos de banda 500, 1,000 y 2,000 metros.
- Hexágonos: radios 250, 500 y 1,000 metros.

## Selección

La tabla `outputs/parte_2/05_seleccion/seleccion_escenarios.csv` registra tamaño, ruido, mega-cluster, probabilidad, estabilidad ARI, extensión y un proxy de chaining. También registra el ARI medio de tres repeticiones con perturbaciones gaussianas de 25 metros, usando una semilla fija.

El puntaje usa solamente criterios espaciales. La solución principal debe ser HDBSCAN; se conserva una referencia DBSCAN y cuatro escenarios HDBSCAN cercanos.

La fórmula y sus componentes están en `205_seleccionar_solucion_espacial.py`. Es una regla reproducible inicial sujeta a revisión sustantiva, no una función universal de calidad.

La persistencia territorial se estima comparando la solución principal con los escenarios seleccionados mediante Jaccard de clusters correspondientes y soporte de membresía por establecimiento.
