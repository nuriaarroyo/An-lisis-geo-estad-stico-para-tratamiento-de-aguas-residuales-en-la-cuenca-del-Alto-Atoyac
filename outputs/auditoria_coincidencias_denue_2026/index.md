# Auditoria de coincidencias DENUE 2026

Estos mapas separan fuentes que no representan el mismo universo: universo prioritario actual, DENUE 2026 completo, Maryhelen MH2, Maryhelen MH y Mayra.

## Como leerlo

- `en_ambos`: aparece en el universo prioritario actual y en el universo prioritario recalculado con DENUE 2026.
- `solo_universo_actual`: estaba en tu universo prioritario previo, pero no queda en el universo prioritario 2026.
- `solo_universo_2026`: aparece al aplicar el filtro a DENUE 2026, pero no estaba en el universo final previo.
- `actual_falta_en_*`: registro de tu Santa Ana final que no aparece en esa fuente externa por ID.
- `mayra_revisar_nombre_o_distancia`: Mayra no trae ID/CLEE; se debe revisar por nombre, direccion y punto mas cercano.
- `posible_falso_positivo_2026`: prioridad automatica que debe revisarse antes de usar como textilera.

## Archivos principales

- `capas_qgis/*.gpkg`: abrir directamente en QGIS.
- `mapas/*.png`: revision rapida estatica.
- `mapas/*.html`: revision interactiva.
- `tablas/resumen_capas_coincidencias.csv`: conteos por categoria.

## Conteos

| capa | comparacion | registros |
| --- | --- | --- |
| 01_universo_actual_vs_universo_2026 | en_ambos | 46 |
| 01_universo_actual_vs_universo_2026 | solo_universo_2026 | 6 |
| 01_universo_actual_vs_universo_2026 | solo_universo_actual | 193 |
| 02_santa_ana_actual_vs_denue2026_raw | actual_falta_en_denue2026 | 1 |
| 02_santa_ana_actual_vs_denue2026_raw | actual_y_denue2026 | 37 |
| 03_santa_ana_actual_vs_maryhelen_mh2 | actual_falta_en_maryhelen_mh2 | 1 |
| 03_santa_ana_actual_vs_maryhelen_mh2 | actual_y_maryhelen_mh2 | 37 |
| 04_santa_ana_actual_vs_maryhelen_mh | actual_falta_en_maryhelen_mh | 31 |
| 04_santa_ana_actual_vs_maryhelen_mh | actual_y_maryhelen_mh | 7 |
| 04_santa_ana_actual_vs_maryhelen_mh | solo_maryhelen_mh | 42 |
| 05_denue2026_vs_maryhelen_mh2_diferencias | solo_denue2026 | 22 |
| 05_denue2026_vs_maryhelen_mh2_diferencias | solo_maryhelen_mh2 | 3 |
| 06_mayra_vs_denue2026_vecino_cercano | mayra_nombre_exactoy_cerca | 7 |
| 06_mayra_vs_denue2026_vecino_cercano | mayra_revisar_nombre_o_distancia | 42 |
| 07_alertas_falsos_positivos_2026 | posible_falso_positivo_2026 | 2 |

Nota: esto es un instrumento de limpieza/auditoria. No constituye evidencia de descarga, contaminacion ni incumplimiento.