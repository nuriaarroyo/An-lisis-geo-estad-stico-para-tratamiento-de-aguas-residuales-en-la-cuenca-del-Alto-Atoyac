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

- `scripts/01_prepare_geodata.py`: unico importador; normaliza las capas de `data/raw/` y genera GeoPackage en `data/processed/`.
- `scripts/run_santa_ana_pipeline.py`: ejecuta SAIC, clasificacion DENUE, filtro estricto, comparaciones, mapas y validacion.
- `scripts/santa_ana_filter_rules.py`: catalogo unico de reglas auditables.
- `scripts/santa_ana_audit_utils.py`: lectura, exportacion, mapas y LaTeX.
- `scripts/common.py`: utilidades generales de rutas, texto y GeoPackage.
- `scripts/legacy/`: scripts experimentales conservados como historial; no forman parte del flujo vigente.

## Como correr

Instala dependencias en tu ambiente de Python:

```bash
pip install -r requirements.txt
```

Cuando cambian las fuentes:

```bash
python scripts/01_prepare_geodata.py
```

Para producir el analisis de Santa Ana:

```bash
python scripts/run_santa_ana_pipeline.py
```

## Outputs principales

- `data/processed/denue2026_raw.gpkg`: DENUE 2026 preparado, sin filtros experimentales.
- `outputs/santa_ana_xalmimilulco/`: unica carpeta vigente de la localidad.
- `outputs/santa_ana_xalmimilulco/capas_qgis/denue_textil_candidatos.gpkg`: candidatos derivados de SAIC y texto DENUE.
- `outputs/santa_ana_xalmimilulco/capas_qgis/universo_relevante_filtro_explicito.gpkg`: resultado relevante del filtro explícito.
- `outputs/santa_ana_xalmimilulco/tablas/saic_actividades_textiles.csv`: actividades SAIC usadas.
- `outputs/santa_ana_xalmimilulco/tablas/validacion_trazabilidad.csv`: controles del proceso.
- `outputs/legacy/`: resultados experimentales anteriores.

La guia vigente esta en `docs/santa_ana_xalmimilulco/guia_pipeline.md`.

## QGIS

Los scripts de `qgis_scripts/` son opcionales y deben ejecutarse desde el Python de QGIS:

- `load_processed_layers.py`: carga los GeoPackage procesados.
- `style_layers_basic.py`: aplica estilos basicos.
- `export_qgis_layout.py`: prepara y exporta un layout preliminar.
