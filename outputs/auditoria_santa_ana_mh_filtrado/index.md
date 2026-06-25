# Santa Ana: exposicion de coincidencias y problema MH filtrado

Lectura principal: el universo actual de Santa Ana coincide con DENUE 2026/MH2 salvo un registro; el problema fuerte aparece en `capa MH`, que no conserva bien correspondencia por ID y punto.

## Conteos clave

| capa | comparacion | registros |
| --- | --- | --- |
| 01_santa_ana_actual_vs_filtrado_2026 | actual_falta_en_filtro2026 | 1 |
| 01_santa_ana_actual_vs_filtrado_2026 | coincide_actual_y_filtro2026 | 37 |
| 01_santa_ana_actual_vs_filtrado_2026 | nuevo_filtro2026_santa_ana | 5 |
| 02_santa_ana_actual_vs_denue2026_base | actual_falta_en_denue2026_base | 1 |
| 02_santa_ana_actual_vs_denue2026_base | coincide_actual_y_denue2026_base | 37 |
| 03_santa_ana_actual_vs_mh2_base | actual_falta_en_mh2_base | 1 |
| 03_santa_ana_actual_vs_mh2_base | coincide_actual_y_mh2_base | 37 |
| 04_santa_ana_actual_vs_mh_filtrado | actual_coincide_id_mh_filtrado | 7 |
| 04_santa_ana_actual_vs_mh_filtrado | actual_falta_en_mh_filtrado | 31 |
| 04_santa_ana_actual_vs_mh_filtrado | mh_filtrado_coincide_id_actual | 7 |
| 04_santa_ana_actual_vs_mh_filtrado | mh_filtrado_con_id_no_en_actual | 36 |
| 04_santa_ana_actual_vs_mh_filtrado | mh_filtrado_sin_id | 6 |
| 05_mh_filtrado_mismos_ids_desplazados | punto_actual_mismo_id | 7 |
| 05_mh_filtrado_mismos_ids_desplazados | punto_mh_mismo_id_desplazado | 7 |
| 06_mayra_vs_denue2026_vecino_cercano | mayra_nombre_exactoy_cerca | 7 |
| 06_mayra_vs_denue2026_vecino_cercano | mayra_revisar_nombre_o_distancia | 42 |
| 07_mh_filtrado_vs_denue2026_base | mh_filtrado_sin_id | 6 |
| 07_mh_filtrado_vs_denue2026_base | mh_id_en_denue2026_base | 42 |
| 07_mh_filtrado_vs_denue2026_base | mh_id_no_en_denue2026_base | 1 |
| 08_mh_filtrado_vs_filtrado_2026 | mh_filtrado_sin_id | 6 |
| 08_mh_filtrado_vs_filtrado_2026 | mh_id_en_filtro2026 | 10 |
| 08_mh_filtrado_vs_filtrado_2026 | mh_id_no_en_filtro2026 | 33 |
| 09_union_conjuntos_santa_ana_senales | 2026_y_mh_no_actual | 2 |
| 09_union_conjuntos_santa_ana_senales | actual_2026_y_mh | 7 |
| 09_union_conjuntos_santa_ana_senales | actual_y_2026_no_mh | 30 |
| 09_union_conjuntos_santa_ana_senales | mh_sin_id | 6 |
| 09_union_conjuntos_santa_ana_senales | solo_2026 | 3 |
| 09_union_conjuntos_santa_ana_senales | solo_actual | 1 |
| 09_union_conjuntos_santa_ana_senales | solo_mh | 34 |

## Fuentes usadas

| fuente | ruta |
| --- | --- |
| santa_actual | outputs\universo_prioritario_denue\santa_ana_xalmimilulco\capa_universo_prioritario_denue_santa_ana_xalmimilulco.gpkg |
| universo2026 | outputs\universo_prioritario_denue_2026\universo_prioritario_denue_2026.gpkg |
| denue2026_raw | data\processed\denue2026_raw.gpkg |
| mh2 | data\processed\capa_maryhelen\capa MH2.shp |
| mh_filtrado | data\processed\capa_maryhelen\capa MH.shp |
| mayra | data\processed\capa_mayra\capa mayra.shp |

## Nota

Estos mapas son para limpieza y auditoria. No constituyen evidencia de descarga, contaminacion ni incumplimiento.

## Foco textil estricto Santa Ana 2026

Se genero un producto separado para retirar el ruido del foco amplio: planchado, confeccion/alta costura, ropa terminada generica, talleres sin senal especifica, lavados no textiles, insumos, bodegas y servicios de agua.

- Reporte: `../foco_textil_estricto_santa_ana_2026/index.md`
- Mapa interactivo principal: `../foco_textil_estricto_santa_ana_2026/mapas/mapa_foco_textil_estricto_santa_ana.html`
- Comparacion con MH: `../foco_textil_estricto_santa_ana_2026/mapas/mapa_comparacion_estricto_vs_mh.html`
- Excluidos del foco amplio: `../foco_textil_estricto_santa_ana_2026/mapas/mapa_excluidos_del_foco_amplio.html`

