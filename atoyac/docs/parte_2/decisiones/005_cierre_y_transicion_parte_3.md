# 005 — Cierre de Parte 2 y transición a Parte 3

## Solución espacial congelada

La solución principal permanece fija: HDBSCAN con `min_cluster_size=10`, `min_samples=20` y selección EOM. Los demás escenarios son evidencia de sensibilidad y robustez; no se reabre la optimización.

El diagnóstico interno del cluster 20 detecta heterogeneidad y subnúcleos exploratorios, pero no modifica su membresía principal.

## Conclusión de alcance

La Parte 2 responde dónde están las concentraciones y qué contienen. Sus entregables finales son el reporte técnico, la presentación narrativa, el atlas de 18 clusters interiores más la actividad dispersa y las tablas auditables de cierre.

## Límite con Parte 3

No se calcularon distancias a ríos, cauces próximos, grafos hidrográficos, rutas aguas abajo, convergencias, zonas de intercepción, colectores ni infraestructura de tratamiento.

La Parte 3 comenzará con numeración `300+` y podrá reutilizar:

- `d_llave` y la matriz maestra;
- la membresía principal congelada;
- persistencia y probabilidad de pertenencia;
- geometrías EPSG:32614;
- resúmenes de clusters y efecto de borde;
- perfiles productivos como atributos posteriores.
