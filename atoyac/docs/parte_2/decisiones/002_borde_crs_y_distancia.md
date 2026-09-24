# 002 — Borde, CRS y distancia

## Efecto de borde

Los clusters se detectan con los 4,365 establecimientos. Se conserva su membresía completa y después se cuentan sus miembros dentro y fuera de la cuenca. El análisis sustantivo se limita a la porción interior, sin fragmentar antes la estructura espacial.

Cada cluster registra `n_total_cluster`, `n_dentro_cuenca`, `n_fuera_cuenca`, porcentajes e indicador `cruza_limite_cuenca`.

## CRS

Las coordenadas DENUE EPSG:4326 se reproyectan a EPSG:32614. DBSCAN, HDBSCAN y OPTICS reciben únicamente coordenadas UTM en metros.

No se introducen SCIAN, señales, evidencia hídrica, municipio o tamaño de establecimiento en la detección ni en la selección.
