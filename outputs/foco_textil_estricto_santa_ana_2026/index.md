# Foco textil estricto Santa Ana Xalmimilulco 2026

Producto corregido para Santa Ana. Reemplaza el foco amplio cuando el objetivo es auditar procesos con mayor relevancia para agua: tratamiento, lavado, tintoreria, acabado, mezclilla/jeans/deshebrado o produccion material textil.

No incluye planchado, confeccion/alta costura, ropa terminada generica, talleres sin senal textil especifica, lavados no textiles, insumos para lavanderia, bodegas ni servicios de agua.

No implica evidencia de descarga ni contaminacion; es una capa de priorizacion y auditoria.

## Archivos principales

- `capas_qgis/foco_textil_estricto_santa_ana_2026.gpkg`
- `tablas/foco_textil_estricto_santa_ana_2026.csv`
- `capas_qgis/comparacion_estricto_vs_mh.gpkg`
- `tablas/comparacion_estricto_vs_mh.csv`
- `capas_qgis/excluidos_del_foco_amplio_santa_ana.gpkg`
- `tablas/excluidos_del_foco_amplio_santa_ana.csv`
- `mapas/mapa_foco_textil_estricto_santa_ana.html`
- `mapas/mapa_comparacion_estricto_vs_mh.html`
- `mapas/mapa_excluidos_del_foco_amplio.html`
- `reporte/reporte_foco_textil_estricto_santa_ana_2026.tex`
- `reporte/reporte_foco_textil_estricto_santa_ana_2026.pdf` si el compilador LaTeX esta disponible

## Lectura rapida

- Foco estricto Santa Ana: 67 registros.
- Registros del foco amplio que salen por criterio estricto: 273.
- Cruces con MH filtrado: 11 registros del foco estricto.
- Cruces con universo prioritario 2026 de Santa Ana: 37 registros.

## Conteos

### resumen_categoria_foco_estricto

| categoria_foco_estricto | registros |
| --- | --- |
| mezclilla_jeans_deshebrado | 44 |
| tratamiento_lavado_acabado_textil | 23 |

### resumen_membresias

| conjunto | registros |
| --- | --- |
| foco_textil_estricto_santa_ana_2026 | 67 |
| en_universo_prioritario_2026_santa_ana | 37 |
| en_universo_prioritario_actual_santa_ana | 34 |
| en_mh_filtrado | 11 |

### comparacion_estricto_vs_mh

| comparacion_estricto_mh | registros |
| --- | --- |
| estricto_y_mh | 11 |
| mh_sin_id | 6 |
| solo_estricto | 56 |
| solo_mh | 32 |

### excluidos_del_foco_amplio

| motivo_exclusion_foco_estricto | registros |
| --- | --- |
| confeccion_maquila_generica | 233 |
| planchado_o_costura_especializada | 17 |
| pendiente_sin_senal_estricta | 10 |
| bordado_o_textil_ligero | 8 |
| servicio_insumo_bodega_no_proceso | 5 |

### resumen_decision

| categoria_foco_estricto | decision_estudio_sugerida | registros |
| --- | --- | --- |
| mezclilla_jeans_deshebrado | incluir_contexto_productivo | 6 |
| mezclilla_jeans_deshebrado | validar_documentalmente | 38 |
| tratamiento_lavado_acabado_textil | incluir_prioritario | 23 |
## Comparacion directa con MH, filtrado 2026 y union previa

- Mapa 4 conjuntos: `mapas/mapa_comparacion_directa_4_conjuntos.html`
- Mapa foco estricto vs filtrado 2026: `mapas/mapa_foco_estricto_vs_filtrado_2026.html`
- Mapa foco estricto vs MH: `mapas/mapa_foco_estricto_vs_mh_directo.html`
- Mapa foco estricto vs union previa: `mapas/mapa_foco_estricto_vs_union_previa.html`
- Documento LaTeX: `../../docs/comparacion_foco_textil_estricto_santa_ana_2026.tex`
- PDF: `../../docs/comparacion_foco_textil_estricto_santa_ana_2026.pdf`

### resumen_tamanos

| conjunto | registros |
| --- | --- |
| foco_estricto_santa_ana_2026 | 67 |
| filtrado_prioritario_denue_2026_santa_ana | 42 |
| mh_filtrado | 49 |
| mh_filtrado_sin_id | 6 |
| union_previa_auditoria | 83 |
| union_total_comparacion_directa | 111 |

### perfil_comparacion

| perfil_comparacion | registros |
| --- | --- |
| 2026_union_no_estricto_no_mh | 5 |
| en_los_4 | 9 |
| estricto_2026_union_no_mh | 28 |
| estricto_y_mh_no_2026 | 2 |
| mh_sin_id | 6 |
| mh_union_no_estricto_no_2026 | 32 |
| solo_estricto | 28 |
| union_no_estricto_no_2026_no_mh | 1 |

