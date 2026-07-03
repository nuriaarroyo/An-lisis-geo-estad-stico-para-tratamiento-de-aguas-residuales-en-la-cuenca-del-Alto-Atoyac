# Pipeline único de Santa Ana Xalmimilulco

Ejecución: `python scripts/run_santa_ana_pipeline.py`.

Proceso: `SAIC -> candidatos textiles DENUE -> filtro explícito -> comparaciones`.

## Jerarquía

- Canónico: universo original de 38 establecimientos.
- Referencia: MH ya filtrado, 49 puntos.
- Alternativa analítica: filtro explícito trazable con categorías relevante y revisar.

## Archivos

- `../../config/filtros_textiles_santa_ana/README.md`
- `../../config/filtros_textiles_santa_ana/palabras_clave.csv`
- `../../config/filtros_textiles_santa_ana/codigos_scian.csv`
- `../../config/filtros_textiles_santa_ana/politica_categorias.csv`
- `referencias/universo_canonico_original/capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg`
- `capas_qgis/denue_textil_candidatos.gpkg`
- `capas_qgis/comparacion_3_universos.gpkg`
- `capas_qgis/universo_relevante_filtro_explicito.gpkg`
- `capas_qgis/clasificacion_explicita_todos.gpkg`
- `capas_qgis/relevantes_revisar.gpkg`
- `mapas/mapa_comparacion_3_universos.html`
- `mapas/mapa_canonico_original_vs_mh_filtrado.html`
- `tablas/comparacion_3_universos.csv`
- `tablas/saic_actividades_textiles.csv`
- `tablas/denue_textil_candidatos.csv`
- `tablas/clasificacion_explicita_todos.csv`
- `tablas/clasificacion_explicita_relevantes_revisar.csv`
- `tablas/diccionario_palabras_clave.csv`
- `tablas/catalogo_codigos_scian.csv`
- `tablas/politica_categorias.csv`
- `tablas/catalogo_reglas_filtro.csv`
- `tablas/comparacion_filtro_anterior_vs_explicito.csv`
- `tablas/resumen_categorias_filtro.csv`
- `tablas/validacion_trazabilidad.csv`
- `pipeline_manifest.json`
- `../../docs/santa_ana_xalmimilulco/guia_pipeline.md`
- `../../docs/santa_ana_xalmimilulco/reporte_auditoria_universos_santa_ana.pdf`

## Tamaños

| conjunto | registros |
| --- | --- |
| denue_2026_santa_ana_total | 1732 |
| denue_textil_candidatos | 361 |
| universo_canonico_original_santa_ana | 38 |
| mh_filtrado | 49 |
| mh_filtrado_con_id | 43 |
| mh_filtrado_sin_id | 6 |
| universo_relevante_filtro_explicito | 293 |
| registros_revisar_filtro_explicito | 18 |
| union_comparacion | 322 |

## Canónico vs MH

| comparacion_canonico_vs_mh | registros |
| --- | --- |
| canonico_y_mh | 7 |
| mh_sin_id | 6 |
| solo_canonico_original | 31 |
| solo_mh_filtrado | 36 |

## Categorías del filtro explícito

| categoria_filtro | relevancia_ambiental | registros |
| --- | --- | --- |
| excluir_comercio | excluir | 795 |
| fuera_filtro | fuera | 589 |
| maquila_textil | media | 171 |
| produccion_textil | media | 114 |
| excluir_actividad_no_objetivo | excluir | 29 |
| revisar_lavado_generico | revisar | 16 |
| excluir_lavado_no_textil | excluir | 8 |
| lavado_acabado_textil | alta | 8 |
| revisar_maquila_sola | revisar | 2 |

## Validación

| validacion | resultado | detalle |
| --- | --- | --- |
| candidatos_son_subconjunto_denue | OK | 361 candidatos |
| foco_es_subconjunto_candidatos | OK | 293 IDs |
| foco_ids_unicos | OK | 293 IDs |
| foco_igual_a_trazabilidad | OK | 293 IDs |
| foco_igual_a_comparacion | OK | 293 IDs |
| canonico_igual_a_comparacion | OK | 38 IDs |
| mh_filtrado_total | OK | 49 puntos |
| exclusion_tiene_prioridad | OK | 0 inclusiones con exclusion |
| catalogo_corresponde_a_columnas | OK | ninguna |
| ids_comparacion_unicos | OK | 322 puntos |
| diccionario_keywords_ids_unicos | OK | 201 palabras |
| politica_cubre_resultados | OK | 9 categorias usadas |
