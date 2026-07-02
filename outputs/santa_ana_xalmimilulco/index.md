# Pipeline único de Santa Ana Xalmimilulco

Ejecución: `python scripts/run_santa_ana_pipeline.py`.

## Jerarquía

- Canónico: universo original de 38 establecimientos.
- Referencia: MH ya filtrado, 49 puntos.
- Alternativa analítica: foco estricto trazable, 67 establecimientos.
- Contexto: filtrado prioritario DENUE 2026, 42 establecimientos.

## Archivos

- `referencias/universo_canonico_original/capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg`
- `capas_qgis/comparacion_directa_4_conjuntos.gpkg`
- `capas_qgis/foco_estricto_alternativo.gpkg`
- `capas_qgis/trazabilidad_filtro_santa_ana_2026.gpkg`
- `mapas/mapa_comparacion_directa_4_conjuntos.html`
- `mapas/mapa_canonico_original_vs_mh_filtrado.html`
- `tablas/comparacion_directa_4_conjuntos.csv`
- `tablas/trazabilidad_filtro_santa_ana_2026.csv`
- `tablas/validacion_trazabilidad.csv`
- `pipeline_manifest.json`
- `../../docs/santa_ana_xalmimilulco/guia_pipeline.md`
- `../../docs/santa_ana_xalmimilulco/reporte_auditoria_universos_santa_ana.pdf`

## Tamaños

| conjunto | registros |
| --- | --- |
| universo_canonico_original_santa_ana | 38 |
| mh_filtrado | 49 |
| mh_filtrado_con_id | 43 |
| mh_filtrado_sin_id | 6 |
| foco_estricto_alternativo | 67 |
| filtrado_prioritario_2026 | 42 |
| union_comparacion | 111 |

## Canónico vs MH

| comparacion_canonico_vs_mh | registros |
| --- | --- |
| canonico_y_mh | 7 |
| mh_sin_id | 6 |
| solo_canonico_original | 31 |
| solo_mh_filtrado | 36 |

## Validación

| validacion | resultado | detalle |
| --- | --- | --- |
| foco_ids_unicos | OK | 67 IDs |
| foco_igual_a_trazabilidad | OK | 67 IDs |
| foco_igual_a_comparacion | OK | 67 IDs |
| canonico_igual_a_comparacion | OK | 38 IDs |
| mh_filtrado_total | OK | 49 puntos |
| exclusion_tiene_prioridad | OK | 0 inclusiones con exclusion |
| catalogo_corresponde_a_columnas | OK | ninguna |
| ids_comparacion_unicos | OK | 111 puntos |
