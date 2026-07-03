# Comparacion DENUE 2026 y capas externas

Este reporte cruza llaves `id` y `clee` normalizadas. Para Mayra, la capa no trae `id`/`clee`, por lo que se usa nombre normalizado y vecino espacial mas cercano.

## Hallazgos principales

- Universo final actual: 239 registros; Santa Ana Xalmimilulco: 38 registros.
- DENUE 2026 trae 2114 registros; Maryhelen MH2 trae 2095 registros.
- DENUE 2026 y Maryhelen MH2 comparten 2092 ids; 22 ids estan solo en DENUE 2026 y 3 solo en Maryhelen MH2.
- De los 38 registros finales de Santa Ana, DENUE 2026 contiene 37 por id y falta 1.
- Maryhelen MH2 contiene 37 de esos 38 por id y falta 1; por `clee` coincide menos porque hay cambios de `clee` entre capas.
- Maryhelen MH contiene solo 7 de los 38 por id; parece una seleccion pequena, no un DENUE completo.

## Lectura metodologica

- No hay evidencia de mezcla de ids en la ruta vieja: `processed_raw`, `processed_textil`, `classified` y `final_santa_ana` conservan una relacion 1:1 por `id`/`clee`.
- La diferencia fuerte viene de versiones/fuentes: DENUE 2026 y Maryhelen MH2 casi son la misma base por `id`, pero no identicas; ademas algunos `clee` cambian aunque el `id` sea el mismo.
- `capa_mayra` requiere conciliacion por nombre y coordenadas porque no trae identificadores DENUE.
- El lenguaje de estos resultados debe leerse como priorizacion/posible presion por proceso textil; no como prueba de descarga o contaminacion.

## Archivos generados

- `resumen_fuentes.csv`
- `matriz_coincidencias_id_clee.csv`
- `cobertura_final_santa_ana_por_fuente.csv`
- `final_santa_ana_faltantes_en_fuentes_nuevas.csv`
- `denue2026_vs_maryhelen_mh2_diferencias.csv`
- `denue2026_vs_maryhelen_mh2_mismos_ids_cambios.csv`
- `mayra_cruce_denue2026_nombre_y_distancia.csv`
- `originales_raw_vs_processed_raw.csv`

## Reaplicar filtrado al DENUE 2026

Para hacerlo bien, conviene crear una rama de procesamiento 2026: convertir `data/raw/denue2026/Denue26 area estudio.shp` a un `denue_raw_2026.gpkg`, correr el mismo filtro textil, recalcular distancia a hidrografia, correr la clasificacion productiva, y solo despues aplicar auditoria/manual FALSE si los ids siguen vigentes. No conviene sobreescribir `data/processed/denue_raw.gpkg` hasta comparar resultados.

## Chequeo contra fuentes originales usadas antes

| fuente_original | ruta | processed_source_folder | registros_original | registros_processed_raw | ids_en_ambas | ids_original_no_processed | ids_processed_no_original | clee_en_ambas | clee_original_no_processed | clee_processed_no_original |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw_xalmimilulco | data\raw\agebs\xalmimilulco\INEGI_DENUE_.csv | agebs\xalmimilulco | 2059 | 2059 | 2059 | 0 | 0 | 2059 | 0 | 0 |
| raw_huejotzingo | data\raw\agebs\huejotzingo\INEGI_DENUE_.csv | agebs\huejotzingo | 4051 | 4051 | 4051 | 0 | 0 | 4051 | 0 | 0 |
| raw_san_martin | data\raw\agebs\san_martin\INEGI_DENUE_.csv | agebs\san_martin | 14201 | 14201 | 14201 | 0 | 0 | 14201 | 0 | 0 |
