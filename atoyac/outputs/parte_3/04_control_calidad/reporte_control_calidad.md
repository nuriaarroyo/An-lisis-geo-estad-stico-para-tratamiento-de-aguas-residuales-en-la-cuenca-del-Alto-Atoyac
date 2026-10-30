# Reporte de control de calidad — Parte 3

- CRS métrico común: `EPSG:32614`.
- Geometrías inválidas: establecimientos=0, PTAR=0, descargas=0, hidrografía=0.
- Establecimientos fuera del límite estricto de cuenca: 355. Se conservan porque la solución de Parte 2 incluye contexto de borde; no son errores automáticos.
- PTAR fuera de cuenca: 0; descargas fuera de cuenca: 0.
- Coincidencias de PTAR con evidencia multicriterio suficiente para marcar como probables: 1. No se fusionaron físicamente.
- Dos nombres de colectores aparecen en el árbol QGIS, pero carecen de geometría fuente; la capa queda vacía.
- No se calculó eficiencia. El cociente caudal/capacidad, cuando sea aplicable, debe llamarse `utilizacion_capacidad_reportada`.

Las relaciones generadas son exclusivamente de proximidad espacial y no prueban conexión hidráulica, cobertura o tratamiento.
