# Análisis geo-estadístico para el desarrollo de tren de tratamiento de aguas residuales en la cuenca del Alto Atoyac

Este proyecto construye un diagnostico reproducible para identificar actividad textil/mezclilla potencialmente relevante en la zona alta del Atoyac. El flujo no afirma contaminacion directa por establecimiento; produce una priorizacion preliminar por tipo de actividad y proximidad a red hidrografica.

## Datos esperados

- `data/raw/agebs/`: capas SHP de INEGI organizadas por localidad/zona de descarga: Huejotzingo, Santa Ana Xalmimilulco y San Martin Texmelucan. En este proyecto los AGEB se tratan como recortes por localidad/zona, no como evidencia municipal completa.
- `data/raw/hidrografia_atoyac/` y `data/raw/hidrologia_atoyac/`: capas de red hidrografica, areas hidrologicas y elementos asociados.
- `data/raw/saic/`: CSV exportado de SAIC. SAIC esta a nivel municipal/entidad para esta consulta; por eso se compara Huejotzingo y San Martin Texmelucan como municipios. Xalmimilulco se analiza espacialmente con DENUE y capas locales porque pertenece al municipio de Huejotzingo y no aparece como unidad independiente en SAIC. San Salvador el Verde no se usa como evidencia censal principal si no aparece en la consulta.

## Criterio metodologico

El filtro DENUE textil usa dos fuentes de evidencia y excluye comercio de prendas:

- Codigo SCIAN cuando existe en los datos, especialmente 313, 314, 315 y 8122.
- Normalizacion de texto y palabras clave en columnas descriptivas del DENUE, como nombre de unidad economica, actividad, clase o campos equivalentes.
- Exclusion de comercio de prendas, boutiques, tiendas, novedades, mercerias, zapaterias y codigos comerciales 46*, salvo casos donde el nombre indica claramente un proceso relevante como lavanderia.

La categoria de relevancia ambiental potencial se asigna por palabras asociadas al tipo de actividad:

- `alta_relevancia_ambiental`: lavado, lavanderia, tintoreria, tenido, acabado y procesos humedos.
- `media_relevancia_ambiental`: confeccion, maquila, costura, prendas, ropa, pantalon, jeans y bordado.
- `revisar`: coincidencias ambiguas que conviene validar manualmente.

La proximidad ambiental se estima por distancia a la red hidrografica lineal. Los rangos `0-100 m`, `100-250 m`, `250-500 m`, `500-1000 m` y `>1000 m` son bandas de proximidad o cautela, no intervalos estadisticos de confianza. El resultado sirve para priorizacion preliminar, no para afirmar contaminacion directa.

SAIC permite extraer indicadores comparativos municipales, por ejemplo unidades economicas, personal ocupado, tamano promedio, proporcion familiar/no remunerada, proporcion remunerada, ingresos por unidad economica y peso de ingresos por maquila. Estos indicadores ayudan a discutir estructura productiva o posible presencia de unidades pequenas/familiares, pero no prueban informalidad por si solos.

## Scripts

- `scripts/00_inventory_raw_data.py`: inventaria shapefiles y registra errores de lectura.
- `scripts/01_prepare_geodata.py`: reproyecta y unifica capas en `data/processed/`.
- `scripts/02_filter_denue_textil.py`: filtra DENUE por palabras clave y codigos SCIAN textiles.
- `scripts/02b_clasificacion_productiva_denue.py`: clasifica todos los DENUE textiles por etapa productiva probable, presion ambiental potencial, prioridad de estudio, confianza y necesidad de auditoria.
- `scripts/03_process_saic.py`: limpia SAIC y calcula indicadores economicos.
- `scripts/04_spatial_analysis.py`: calcula distancias a hidrografia, buffers y cruces con AGEB/localidad.
- `scripts/05_make_maps.py`: genera mapas del diagnostico automatico, incluyendo la categoria `revisar`, y figura SAIC en PNG.
- `scripts/05b_make_productive_classification_maps.py`: genera mapas PNG de la clasificacion productiva DENUE.
- `scripts/06_make_interactive_maps.py`: genera mapas HTML interactivos para identificar establecimientos.
- `scripts/06b_make_plotly_productive_maps.py`: genera mapas interactivos Plotly e indice HTML de la clasificacion productiva.
- `scripts/07_apply_denue_audit.py`: aplica las categorias editadas manualmente en las plantillas de auditoria.
- `scripts/08_make_audited_maps.py`: genera mapas posteriores a la auditoria, solo con categorias alta y media.
- `scripts/run_all.py`: ejecuta todo el flujo en orden.

## Como correr

Instala dependencias en tu ambiente de Python:

```bash
pip install -r requirements.txt
```

Luego ejecuta:

```bash
python scripts/run_all.py
```

## Outputs principales

- `outputs/tables/inventario_capas.csv`
- `data/processed/agebs.gpkg`, `manzanas.gpkg`, `localidades.gpkg`, `vialidades.gpkg`, `caminos_carreteras.gpkg`, `cuencas.gpkg`, `hidrografia.gpkg`, `denue_raw.gpkg`
- `data/processed/denue_textil.gpkg`
- `data/processed/denue_textil_con_distancia.gpkg`
- `outputs/tables/denue_textil.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_universo_textil_clasificado.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_universo_textil_depurado.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_universo_alcance_proyecto.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_estudio_prioritario.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_pendientes_auditoria.csv`
- `outputs/tables/denue_clasificacion_productiva/localidades/denue_universo_alcance_huejotzingo.csv`
- `outputs/tables/denue_clasificacion_productiva/localidades/denue_universo_alcance_xalmimilulco.csv`
- `outputs/tables/denue_clasificacion_productiva/localidades/denue_universo_alcance_san_martin.csv`
- `outputs/tables/auditoria_enriquecida/auditoria_denue_textil_priorizada.xlsx`
- `outputs/tables/denue_excluidos_comercio_prendas.csv`
- `outputs/tables/auditoria_revisar_huejotzingo.csv`
- `outputs/tables/auditoria_revisar_xalmimilulco.csv`
- `outputs/tables/auditoria_revisar_san_martin.csv`
- `outputs/tables/denue_categorias_auditadas.csv`
- `outputs/tables/saic_indicadores.csv`
- `outputs/tables/saic_indicadores_lectura_analitica.csv`
- `outputs/tables/conteo_negocios_por_buffer.csv`
- `outputs/tables/conteo_negocios_por_rango_distancia.csv`
- `outputs/maps/01_contexto_territorial.png`
- `outputs/maps/02_denue_textil_categorias.png`
- `outputs/maps/03_buffers_hidrografia_denue.png`
- `outputs/maps/04_concentracion_textil_por_ageb.png`
- `outputs/maps/05_cauces_rio_red_hidrografica.png`
- `outputs/maps/06_rh18ad_hidrografia_especifica.png`
- `outputs/maps/07_hidrologia_completa_por_tipo.png`
- `outputs/maps/08_hidrologia_completa_por_area_rh.png`
- `outputs/maps/10_huejotzingo_denue_total.png`
- `outputs/maps/11_huejotzingo_denue_textil_categorias.png`
- `outputs/maps/12_huejotzingo_heatmap_denue_textil.png`
- `outputs/maps/13_huejotzingo_rangos_distancia_rio.png`
- `outputs/maps/10_xalmimilulco_denue_total.png`
- `outputs/maps/11_xalmimilulco_denue_textil_categorias.png`
- `outputs/maps/12_xalmimilulco_heatmap_denue_textil.png`
- `outputs/maps/13_xalmimilulco_rangos_distancia_rio.png`
- `outputs/maps/10_san_martin_denue_total.png`
- `outputs/maps/11_san_martin_denue_textil_categorias.png`
- `outputs/maps/12_san_martin_heatmap_denue_textil.png`
- `outputs/maps/13_san_martin_rangos_distancia_rio.png`
- `outputs/maps/14_huejotzingo_denue_textil_auditado_alta_media.png`
- `outputs/maps/14_xalmimilulco_denue_textil_auditado_alta_media.png`
- `outputs/maps/14_san_martin_denue_textil_auditado_alta_media.png`
- `outputs/maps/denue_clasificacion_productiva/`
- `outputs/figures/saic_indicadores_municipio.png`
- `outputs/maps_interactive/denue_textil_productivo_interactivo.html`
- `outputs/maps_interactive/huejotzingo_denue_textil_productivo_interactivo.html`
- `outputs/maps_interactive/xalmimilulco_denue_textil_productivo_interactivo.html`
- `outputs/maps_interactive/san_martin_denue_textil_productivo_interactivo.html`
- `outputs/maps_interactive/denue_clasificacion_productiva/index.html`

La guia detallada del flujo nuevo esta en `docs/guia_ejecucion_clasificacion_denue.md`.

El universo operativo del alcance ambiental queda marcado con `flag_universo_alcance_proyecto`: procesos humedos/tratamiento, lavado/deslavado/lavanderia o mezclilla/jeans. Los registros textiles fuera de ese criterio se conservan como contexto, pero no como universo principal de la auditoria ambiental.

## QGIS

Los scripts de `qgis_scripts/` son opcionales y deben ejecutarse desde el Python de QGIS:

- `load_processed_layers.py`: carga los GeoPackage procesados.
- `style_layers_basic.py`: aplica estilos basicos.
- `export_qgis_layout.py`: prepara y exporta un layout preliminar.
