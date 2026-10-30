# Inspección inicial de la entrega de Lesly

## Archivos recibidos

- `data/processed/lesly/FINAL_ATOYAC.qgz`: proyecto QGIS comprimido.
- `data/processed/lesly/Reporte_Río_Atoyac_colectores_lesly.pdf`: reporte de avances de
  septiembre de 2026, 20 páginas.

## Hallazgo principal

La carpeta no contiene un GeoPackage con todas las capas. El archivo `FINAL_ATOYAC.qgz`
contiene el XML del proyecto QGIS y una base de estilos, pero las fuentes espaciales son
referencias relativas a archivos externos que no fueron entregados junto con el proyecto.
En consecuencia, el proyecto conserva nombres, CRS y simbología, pero actualmente no
permite contar elementos, revisar atributos ni ejecutar análisis de conectividad.

## Capas declaradas por el proyecto

El proyecto usa EPSG:32614 y declara 11 capas de datos:

| Contenido aparente | Archivo o fuente referenciada | Geometría/CRS | Estado en la carpeta |
|---|---|---|---|
| Zona federal o franja de restricción | `Limites_federales.gpkg`, capa `buffered` | Polígono, EPSG:32614 | Faltante |
| DENUE recortado | `Denue_clipped.gpkg` | Punto, CRS84 | Faltante |
| DENUE estatal/local | `INEGI_DENUE_29092026.shp` | Punto, CRS84 | Faltante |
| Heatmap DENUE | `OUTPUT.tif` en una ruta temporal de macOS | Raster, EPSG:32614 | Faltante y ruta temporal no portable |
| PTAR compiladas | `PTAR_Final.csv` | Punto, EPSG:4326 | Faltante |
| Cuenca reproyectada | `cuenca_reproyectada.gpkg` | Polígono, EPSG:32614 | Faltante |
| Municipios reproyectados | `municipios_reproyectado.gpkg` | Polígono, EPSG:32614 | Faltante |
| PTAR municipales INEGI | Shapefile `cngmd_2021_m5_agua_potable_y_saneamiento.shp` | Punto, EPSG:8999 | Faltante |
| DENUE recortado reproyectado | `denue_clipped_reproyectado.gpkg` | Punto, EPSG:32614 | Faltante |
| Límite estatal | `Estado_reproyectado.gpkg` | Polígono, EPSG:32614 | Faltante |
| Río Atoyac | `RioAtoyac_reproyecetado_FINAL.gpkg` | Línea, EPSG:32614 | Faltante |

El mapa base satelital es un servicio web de Esri y no constituye una capa local auditable.

## Elementos que no son capas recuperables

El árbol del proyecto incluye `Camino_contenedores_SMT` y
`Camino_contenedores_huejotzingo`, pero no existen entradas correspondientes en
`projectlayers`. Son nodos huérfanos: el QGZ no contiene sus geometrías ni una ruta de fuente.
No deben presentarse todavía como colectores existentes ni como trazos recuperados.

## Qué contiene realmente sobre los temas esperados

- **Hidrología/cauce:** solo se declara una capa lineal del río Atoyac; no se observó una red
  hidrográfica completa en el proyecto entregado.
- **Drenaje y puntos de descarga:** el PDF afirma que se utilizaron puntos de descarga del
  conjunto INEGI 2023, pero el shapefile referido no está incluido. No aparece una red de
  drenaje lineal ni atributos de conectividad en el QGZ disponible.
- **Colectores:** no hay una capa recuperable de colectores. Los dos “caminos de
  contenedores” parecen trazos gráficos o capas eliminadas y no pueden auditarse.
- **PTAR:** se referencian un CSV compilado y un shapefile de INEGI, ambos ausentes. El PDF
  documenta fuentes 2016, 2019, 2021/2022 y 2024 y advierte diferencias temporales y de
  definición.
- **Descargas industriales:** el PDF presenta algunos registros puntuales y cuerpos
  receptores, pero no se entregó una tabla espacial independiente para auditarlos.
- **Relieve:** no se encontró modelo digital de elevación ni capa de pendientes.

## Información documentada en el PDF que debe conservarse como fuente, no como verdad única

El reporte identifica y compara PTAR municipales y no municipales en Huejotzingo y San
Martín Texmelucan, incluye capacidades y caudales de diversas fechas, y muestra un primer
mapa conjunto con PTAR, una franja de 10 m, puntos de descarga, DENUE y flechas de flujo.
El propio reporte reconoce que presencia registral no demuestra operación actual, conexión
de establecimientos ni capacidad efectiva.

## Insumos que deben solicitarse antes del análisis aplicado

1. Todos los GeoPackages, shapefiles y CSV referenciados por el QGZ, con sus archivos
   auxiliares y metadatos.
2. Capa lineal de drenaje, atarjeas, colectores, emisores, interceptores y cárcamos.
3. Puntos de descarga con identificador, tipo, fuente, fecha, estado y cuerpo receptor.
4. Inventario consolidado de PTAR con fuente/año, coordenadas, capacidad, caudal, proceso,
   estado operativo y responsable.
5. Modelo digital de elevación y, si existe, topografía de detalle o cotas de infraestructura.
6. Geometrías originales de los trazos `Camino_contenedores_SMT` y
   `Camino_contenedores_huejotzingo`, aclarando si representan propuestas o infraestructura.
7. Diccionario de campos, licencia/condiciones de uso y responsable de cada fuente.

Hasta recibir esos insumos, la Parte 3 puede avanzar en normalización documental y diseño
de auditoría, pero no en inferencia de rutas hidráulicas ni evaluación de colectores.
