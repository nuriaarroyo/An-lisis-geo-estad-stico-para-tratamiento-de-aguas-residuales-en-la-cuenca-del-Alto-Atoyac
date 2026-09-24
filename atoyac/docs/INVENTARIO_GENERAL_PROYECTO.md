# Inventario general del proyecto Alto Atoyac

**Corte del inventario:** 24 de septiembre de 2026  
**Alcance:** archivos presentes en el directorio del proyecto.  
**Propósito:** dejar constancia de qué se ha construido, con qué scripts, qué productos existen y cuál es su lugar dentro del flujo analítico.

## 1. Resumen ejecutivo

El trabajo realizado se organiza en cuatro bloques:

1. **Definición y depuración del universo económico.** Se cargó DENUE, se hicieron recortes territoriales, filtros SCIAN y filtros textuales, se construyeron variables auditables de inclusión y evidencia hídrica, y se integraron fuentes complementarias MH.
2. **Construcción territorial y comparación de modalidades.** Se generaron universos para localidades específicas y para 26 municipios relacionados con la cuenca, con cinco modalidades comparables; además se produjeron tablas, capas, mapas y presentaciones.
3. **Clustering espacial por densidad.** Se fijó un universo ampliado de 4,365 establecimientos para detectar agrupamientos reduciendo el efecto de borde, y 4,010 establecimientos dentro de la cuenca para interpretarlos. Se exploraron DBSCAN, HDBSCAN y OPTICS usando exclusivamente coordenadas métricas.
4. **Análisis de concentración y composición.** Se seleccionó una solución principal, se conservaron los registros clasificados como ruido, se perfilaron los clusters por actividad, municipio, localidad, personal y señales hídricas, se estudió sobrerrepresentación, coexistencia productiva, similitud entre perfiles, robustez y la estructura interna del mega-cluster.

Estado material del proyecto:

- 38 scripts Python en `scripts/`.
- Cinco corridas territoriales principales de cuenca, cada una con tablas, capas y 30 mapas HTML más 30 mapas PNG.
- 15 etapas o carpetas de resultados en `outputs/parte_2/`, desde `00_auditoria` hasta `14_segunda_pasada`.
- 12 PDF presentes en el proyecto, incluidos reporte técnico, presentación y atlas de Parte 2.
- No existe un repositorio Git en esta carpeta; por ello este inventario describe el estado actual, pero no puede reconstruir autorías, fechas de commits ni archivos eliminados.

## 2. Fuentes y datos de entrada

### 2.1 DENUE

- `data/raw/denue_2026/huejotzingo/INEGI_DENUE_04092026.*`: descarga DENUE usada para Huejotzingo y Santa Ana Xalmimilulco; incluye CSV y componentes de shapefile.
- `data/raw/denue_scian_313-314-315-81/INEGI_DENUE_11092026.*`: descarga estatal acotada a SCIAN 313, 314, 315 y 81; contiene 15,956 registros según los resúmenes de ejecución.
- `data/raw/denue_2026/denue_diccionario_de_datos.pdf`: diccionario de datos de referencia.

### 2.2 Insumos territoriales e hídricos

En `data/raw/cuenca_alto_atoyac/atoyac/` se conservan, en GeoPackage, GeoJSON y tablas auxiliares:

- polígono de la cuenca del Alto Atoyac;
- división municipal;
- red hidrográfica digital;
- metadatos de las capas.

Las capas operativas usadas por los scripts son:

- `caaresa_cuenca_alto_atoyac_21_reg_a.gpkg`;
- `caaresa_division_municipal_20_mun_a.gpkg`;
- `caaresa_red_hidro_digital_06_reg_l.gpkg`.

### 2.3 Datos procesados y auxiliares

- `data/processed/catalogs/giro_textil.csv`: catálogo de actividades/giros usado en la clasificación.
- `data/processed/auditables/`: tablas auditables preliminares de Huejotzingo y Xalmimilulco.
- `data/processed/mh/xalmi/` y `data/processed/mh/huejo/`: fuentes complementarias MH.
- `data/processed/legacy/`: universo hídrico preliminar, universo combinado tentativo MH y cola de revisión manual de SCIAN 314; se usan para comparación y trazabilidad histórica.

## 3. Inventario completo de scripts

### 3.1 Exploración, filtros y utilidades base

| Script | Papel | Entradas principales | Salidas o uso |
|---|---|---|---|
| `00_data_exploration.py` | Exploración genérica de un CSV: estructura, primeras filas, estadísticas, faltantes e histogramas. | CSV indicado al invocar la función. | Diagnóstico exploratorio en pantalla y gráficas; no forma parte de los ejecutores actuales. |
| `01_recorte_territorial.py` | Filtra registros por una columna y valor territorial; conserva compatibilidad con el nombre inicial de la función. | DataFrame DENUE. | DataFrame recortado. |
| `02_scian.py` | Marca/filtra el universo sectorial con códigos SCIAN textiles definidos en el catálogo. | DENUE y catálogo SCIAN. | Componente del filtro auditable. |
| `03_text_filter.py` | Normaliza texto y detecta términos asociados con procesos y señales hídricas; construye patrones priorizando frases largas. | Nombre, razón social, descripción y catálogo de términos. | Variables de coincidencia textual y evidencia. |
| `04_desiciones_preliminares.py` | Integra de forma independiente filtro SCIAN y filtro textual; clasifica el universo y la evidencia hídrica, incluida la modalidad estricta para lavanderías. | DataFrame territorial/estatal y catálogo. | Matriz auditable con indicadores, motivos y clasificación. |
| `05_csv_capa.py` | Separa el auditable local en tres subconjuntos publicables. | Tabla auditable. | CSV de universo textil, evidencia hídrica `SI` y evidencia `SI+REVISAR`. |
| `06_crear_figuras.py` | Produce cartografía de los subconjuntos de las dos localidades iniciales. | Capas de origen y subconjuntos. | Un panel resumen y tres mapas PNG por localidad. |
| `07_comparaciones.py` | Compara por ID DENUE un universo histórico con el universo actual y diagnostica altas/bajas. | CSV legacy y CSV actual. | Seis tablas de comparación y una figura por comparación. |
| `08_mapas_cuenca_puebla.py` | Genera cartografía estática e interactiva de cuenca, ríos, establecimientos, distancias, conteos, estratos y municipios. | Capas territoriales y universo elegido. | 30 HTML, 30 PNG, inventario de mapas y capa con distancia a la red hídrica por modalidad. |
| `09_presentacion_cuenca_puebla.py` | Construye una presentación Beamer con los mapas de una corrida territorial. | Inventario de mapas, resumen y resultados. | `.tex` y, cuando está disponible LaTeX, `.pdf`. |
| `10_integrar_mh.py` | Integra registros MH de Xalmimilulco y Huejotzingo, conserva procedencia, enlaza coincidencias y crea filas sintéticas cuando procede. | Universo DENUE, shapefile MH Xalmimilulco y CSV MH Huejotzingo. | Universo enriquecido y auditoría de integración MH. |
| `99_crear_capa.py` | Recupera geometría original por ID DENUE para una tabla filtrada. | Tabla por ID y shapefile DENUE. | Capa GeoPackage. |

### 3.2 Orquestación y productos de la primera fase

| Script | Papel | Estado |
|---|---|---|
| `100_main.py` | Ejecuta el flujo local para Huejotzingo y Santa Ana Xalmimilulco: carga y normaliza DENUE, recorta localidad, clasifica, guarda auditables, tablas, capas y figuras, y compara Xalmimilulco con el universo legacy. | Flujo local reproducible. |
| `101_main_cuenca_puebla.py` | Ejecuta el flujo estatal para los 26 municipios y la cuenca. Acepta modalidades amplia, estricta, con/sin MH y todos los SCIAN. Calcula intersección con cuenca, distancia a ríos, cobertura municipal, mapas y presentación. | Flujo territorial principal de la primera fase. |
| `102_presentacion_direccion.py` | Compara cinco modalidades, crea paneles, rankings, matrices municipales, análisis de establecimientos pequeños y posibles comerciales, y genera una presentación integrada para dirección. No redefine universos. | Producto comunicativo y comparativo. |

### 3.3 Pipeline de clustering y análisis de concentraciones

| Script | Papel | Productos principales |
|---|---|---|
| `200_parte2_comun.py` | Configuración común: rutas, semilla `20260921`, CRS geográfico `EPSG:4326`, CRS métrico `EPSG:32614`, lectura/escritura y funciones de resumen. Define el universo como “sectorial ampliado”. | Utilidad importada por `201–222`; crea la estructura `00–14`. |
| `201_auditar_y_construir_matriz.py` | Audita fuentes, unicidad e integridad; une los 4,365 establecimientos de apoyo con la marca de 4,010 dentro de cuenca y construye señales analíticas. | `00_auditoria/*`, `01_matriz/matriz_maestra_establecimientos.csv`. |
| `202_preparar_geometrias.py` | Convierte puntos a WGS84 y UTM 14N y prepara el contexto territorial. | GeoPackages de establecimientos y cuenca; resumen de geometrías. |
| `203_diagnosticar_estructura_espacial.py` | Diagnóstico previo independiente de atributos económicos: distancias k-NN, densidad KDE y mallas hexagonales. | `03_diagnosticos/` con CSV, CSV.GZ y GeoPackage. |
| `204_evaluar_clustering_espacial.py` | Recorre una batería reproducible de DBSCAN, HDBSCAN y OPTICS usando sólo `x/y`. Registra etiquetas, probabilidades y estadísticas por escenario. | Espacio de parámetros, 57 escenarios resumidos y membresías comprimidas. |
| `205_seleccionar_solucion_espacial.py` | Compara particiones con ARI, Jaccard, continuidad, efecto de borde y perturbaciones espaciales; asigna roles principal, sensibilidad y referencia. | Selección, decisión JSON, ARI, Jaccard y persistencia por establecimiento. |
| `206_construir_clusters_y_borde.py` | Materializa la solución fija, sus envolventes convexas y métricas dentro/fuera de cuenca. | Membresía principal, resumen de borde y GeoPackage de solución. |
| `207_perfilar_clusters.py` | Después de fijar el clustering, perfila clusters y ruido por municipio, localidad, SCIAN, personal, evidencia hídrica y señales productivas multilabel. | Diez tablas en `07_perfiles/`. |
| `208_analizar_sobrerrepresentacion.py` | Compara cada señal contra el universo dentro de cuenca mediante proporciones, lift, odds ratio, prueba exacta de Fisher e ajuste Benjamini-Hochberg. | `sobrerrepresentacion_senales.csv`. |
| `209_comparar_perfiles_clusters.py` | Vectoriza perfiles, calcula distancias y produce una tipología exploratoria mediante clustering jerárquico. | Vectores, matriz de distancias, linkage y tipología. |
| `210_generar_figuras_y_coexistencia.py` | Produce las primeras figuras sintéticas y la comparación específica lavanderías/manufactura. | Cuatro PNG en `10_figuras/` y tabla de coexistencia. |
| `211_generar_documentos_parte2.py` | Genera versiones Markdown vivas del reporte y la presentación. | `reporte_tecnico_parte_2.md` y `presentacion_parte_2.md`. |
| `212_ejecutar_parte2.py` | Ejecuta en orden `201–211`. | Ejecutor histórico de la primera implementación de Parte 2. |
| `213_auditar_y_diagnosticar_cierre.py` | Verifica que la solución siga fija y estudia internamente el mega-cluster sin sustituir la membresía principal. | Auditoría, subnúcleos exploratorios, hexágonos y resumen del mega-cluster. |
| `214_cerrar_analisis_composicion.py` | Cierra análisis de ruido, sensibilidad de coexistencia, rasgos distintivos, similitud productiva y respuestas a preguntas centrales. | Tablas y JSON de `11_cierre/`. |
| `215_generar_figuras_finales_y_atlas.py` | Genera mapas finales comparables y láminas homogéneas por cluster y ruido. | 11 figuras finales y 19 láminas de atlas. |
| `216_generar_latex_parte2.py` | Construye las fuentes LaTeX del reporte técnico, presentación y atlas. | Tres archivos `.tex`. |
| `217_compilar_documentos_parte2.py` | Compila los tres documentos con `latexmk`. | Tres PDF finales y auxiliares LaTeX. |
| `218_validar_cierre_parte2.py` | Verifica integridad, conteos, unicidad, documentos y separación entre clustering y variables productivas; crea manifiesto con hashes. | `validacion_final.csv` e `inventario_cierre.csv`. |
| `219_ejecutar_parte2_completa.py` | Ejecuta `201–211` y `213–218`, desde fuentes hasta PDF. | Ejecutor definitivo del cierre original; no incluye `220–222`. |

### 3.4 Segunda pasada analítica y documental

| Script | Papel | Productos principales |
|---|---|---|
| `220_segunda_pasada_analitica.py` | Profundiza sin modificar la solución espacial: documenta ARI, estabilidad de membresía, matrices de distancia separadas y combinadas, pares similares, sobrerrepresentación completa y subnúcleos del mega-cluster. | 15 archivos analíticos en `14_segunda_pasada/`. |
| `221_figuras_interactivo_segunda_pasada.py` | Genera diez figuras explicativas y un explorador HTML autocontenido con selectores, métricas y filtros. | `14_segunda_pasada/figuras/`, explorador HTML y captura de verificación. |
| `222_documentar_segunda_pasada.py` | Regenera y amplía reporte y presentación LaTeX incorporando la segunda pasada; actualiza el glosario metodológico y registra figuras. | `.tex` actualizados, glosario y registro de documentación. |

**Nota de reproducibilidad:** `220–222` sí se ejecutaron y tienen productos, pero no están llamados por `219_ejecutar_parte2_completa.py`. Para rehacer el estado más reciente se requiere ejecutar primero `219` y después `220`, `221` y `222`; tras `222` debe compilarse de nuevo con `217` si se quieren PDF sincronizados con los `.tex` más recientes.

## 4. Universos y modalidades construidos

Las cinco corridas territoriales parten de 15,956 registros estatales, encuentran registros en 24 de los 26 municipios solicitados y generan 30 mapas por formato.

| Modalidad / carpeta | Universo sectorial municipal | Universo seleccionado municipal | Dentro de cuenca | MH agregados | Sentido |
|---|---:|---:|---:|---:|---|
| `cuenca_alto_atoyac_puebla` | 4,365 | 1,756 | 1,717 | 38 | Regla hídrica amplia + MH. |
| `cuenca_alto_atoyac_puebla_sin_mh` | 4,365 | 1,718 | 1,679 | 0 | Regla hídrica amplia, sólo DENUE. |
| `cuenca_alto_atoyac_puebla_estricto_mh` | 4,365 | 517 | 510 | 41 | Regla estricta para lavanderías + MH. |
| `cuenca_alto_atoyac_puebla_estricto_sin_mh` | 4,365 | 476 | 469 | 0 | Regla estricta, sólo DENUE. |
| `cuenca_alto_atoyac_puebla_todos_scian` | 4,365 | 4,365 | 4,010 | 0 | Universo sectorial ampliado completo; base de Parte 2. |

Cada carpeta contiene normalmente:

- `tables/`: universo auditable estatal, universo de 26 municipios, universo dentro de cuenca, distancias y resumen;
- `layers/`: seis GeoPackages equivalentes para trabajo SIG;
- `maps/html/`: 30 mapas interactivos;
- `maps/png/`: 30 mapas estáticos;
- `maps/inventario_mapas.csv`: índice de cartografía.

Además:

- `outputs/huejotzingo/` y `outputs/xalmimilulco/` contienen tres tablas, tres capas y cuatro figuras cada uno;
- `outputs/xalmimilulco/comparacion_legacy/` y `comparacion_combinado/` guardan comparaciones con universos anteriores;
- `docs/presentaciones parciales/`, `docs/reportes/` y `docs/dir1/` conservan entregables intermedios y la presentación a dirección.

## 5. Parte 2: inventario por etapa de resultados

| Carpeta | Archivos | Contenido |
|---|---:|---|
| `00_auditoria` | 2 | Inventario con rutas, conteos y SHA-256 de fuentes; resumen del universo. |
| `01_matriz` | 1 | Matriz maestra de 4,365 establecimientos con marca dentro/fuera de cuenca y variables de análisis. |
| `02_geometrias` | 3 | Puntos en EPSG:4326 y EPSG:32614, contexto de cuenca y resumen. |
| `03_diagnosticos` | 3 | Distancias a vecinos, KDE y diagnósticos territoriales hexagonales. |
| `04_clustering` | 3 | Parámetros, resumen de escenarios y todas las membresías. |
| `05_seleccion` | 5 | ARI, Jaccard, persistencia, escenarios seleccionados y decisión formal. |
| `06_clusters` | 3 | Membresía principal, métricas de borde y capa espacial de clusters. |
| `07_perfiles` | 10 | Perfil por cluster y composiciones municipal, local, SCIAN, personal, hídrica y de coexistencia. |
| `08_sobrerrepresentacion` | 1 | Contrastes estadísticos de señales por cluster. |
| `09_comparacion` | 4 | Vectores, distancias, linkage y tipología de perfiles. |
| `10_figuras` | 4 | Primera síntesis visual de solución, escenarios, perfiles y coexistencia. |
| `11_cierre` | 12 | Auditoría final, ruido, sensibilidad, rasgos, pares similares, fichas, mega-cluster, respuestas y manifiesto. |
| `12_atlas` | 19 | Láminas para 18 clusters interiores y ruido disperso. |
| `13_figuras_finales` | 11 | Universos/borde, clusters, persistencia, tipos, robustez, composición, rasgos, ruido, similitud, mega-cluster y borde. |
| `14_segunda_pasada` | 26 | 16 productos en la raíz, diez figuras, matrices desagregadas, estabilidad y explorador interactivo. |

## 6. Decisiones metodológicas ya formalizadas

Los documentos de `docs/parte_2/decisiones/` registran cinco decisiones:

1. Definición del universo sectorial ampliado y separación entre universo de detección y universo de interpretación.
2. Uso de municipios de apoyo para reducir efecto de borde, proyección UTM 14N y distancias en metros.
3. Exploración de DBSCAN, HDBSCAN y OPTICS y selección mediante criterios espaciales, no productivos.
4. Conservación del ruido y perfilado económico posterior; sobrerrepresentación con base comparativa explícita.
5. Congelamiento de la solución para el cierre, uso sólo diagnóstico de subnúcleos y transición hacia análisis posteriores.

También existen documentos sobre variables y señales, limitaciones y sesgos, y glosario metodológico en `docs/parte_2/metodologia/`.

## 7. Resultados estructurales verificados

- Universo para detección y control de borde: **4,365 establecimientos**.
- Universo dentro de la cuenca para interpretación: **4,010 establecimientos**.
- Solución principal: `hdbscan__min_cluster_size-10__min_samples-20__cluster_selection_method-eom`.
- La solución principal trabaja con HDBSCAN, `min_cluster_size=10`, `min_samples=20`, selección `eom`.
- Resultado sobre los 4,365 puntos: **22 clusters**, **584 registros de ruido (13.38%)** y un cluster mayor de **1,997 registros (45.75%)**.
- En el atlas se documentan **18 clusters interiores** más el ruido disperso; por ello el número de láminas no coincide mecánicamente con los 22 clusters del universo ampliado de detección.
- Las auditorías confirman IDs únicos, membresía completa de 4,365, perfilado de 4,010 y ausencia de variables productivas en la construcción del clustering.
- La segunda pasada conserva inmutable la solución principal y usa un subclustering HDBSCAN (`mcs=30`, `min_samples=10`, `leaf`) únicamente para diagnosticar el mega-cluster.

## 8. Documentos y productos de comunicación

### Parte 2

- `docs/parte_2/reporte/reporte_tecnico_parte_2.md`, `.tex` y `.pdf`.
- `docs/parte_2/presentacion/presentacion_parte_2.md`, `.tex` y `.pdf`.
- `docs/parte_2/atlas/atlas_clusters.tex` y `.pdf`.
- `outputs/parte_2/14_segunda_pasada/explorador_interactivo_clusters.html` (autocontenido, aproximadamente 5.4 MB).

### Entregables previos

- `docs/reportes/`: versiones de reportes DENUE/textil y reporte actualizado.
- `docs/presentaciones parciales/`: presentaciones de las distintas modalidades de cuenca.
- `docs/dir1/`: presentación a dirección y 33 insumos gráficos/tabulares.

## 9. Dependencias técnicas observadas

El código usa principalmente:

- `pandas`, `numpy`;
- `geopandas`, `shapely`;
- `scikit-learn` (DBSCAN, HDBSCAN, OPTICS, métricas y KDE);
- `scipy` (pruebas, distancias y clustering jerárquico);
- `matplotlib`, `seaborn`, `plotly`;
- `latexmk`/`pdflatex` para documentos.

No se encontró en la raíz un archivo explícito de entorno (`requirements.txt`, `pyproject.toml`, `environment.yml`) ni un repositorio Git. Esto limita la reproducibilidad en otra computadora aunque los scripts y las fuentes estén presentes.

## 10. Flujo reproducible actualmente identificable

### Reconstrucción del universo territorial

```powershell
python scripts\101_main_cuenca_puebla.py --todos-scian
```

Las demás modalidades dependen de las banderas definidas en ese script (`--sin-mh`, `--estricto` y combinaciones).

### Parte 2 hasta el cierre original

```powershell
python scripts\219_ejecutar_parte2_completa.py
```

### Extensión de segunda pasada

```powershell
python scripts\220_segunda_pasada_analitica.py
python scripts\221_figuras_interactivo_segunda_pasada.py
python scripts\222_documentar_segunda_pasada.py
python scripts\217_compilar_documentos_parte2.py
```

## 11. Vacíos y observaciones de organización

- El inventario anterior `docs/parte_2/trazabilidad/inventario_scripts_200.md` termina en `219`; no incluye la segunda pasada `220–222`.
- El ejecutor `219` tampoco incorpora `220–222`; convendría crear un ejecutor de estado final o ampliar el existente.
- La carpeta contiene auxiliares de compilación LaTeX (`.aux`, `.log`, `.toc`, etc.) y archivos de sistema/cache; son derivados, no resultados sustantivos.
- La primera fase usa nombres históricos como `universo_hidrico` incluso en la modalidad `todos_scian`; en Parte 2 ésta se interpreta correctamente como universo sectorial ampliado, no como selección de evidencia hídrica.
- Hay un script con el nombre histórico `04_desiciones_preliminares.py`; se conserva así porque otros scripts lo importan con ese nombre.
- Sin control de versiones no es posible asegurar que el inventario abarque trabajo previo borrado o que cada PDF corresponda exactamente al `.tex` más reciente. Los archivos presentes y las auditorías internas sí permiten reconstruir el flujo actual.

## 12. Mapa sintético del proyecto

```text
DENUE + catálogo + capas territoriales + fuentes MH/legacy
                         |
                         v
       recorte + SCIAN + texto + evidencia auditable
                         |
             +-----------+-----------+
             |                       |
             v                       v
  localidades iniciales      5 modalidades de cuenca
                                     |
                                     v
                    universo ampliado 4,365 / cuenca 4,010
                                     |
                                     v
           diagnóstico -> 57 escenarios -> selección espacial
                                     |
                                     v
         clusters + ruido -> perfiles -> sobrerrepresentación
                                     |
                                     v
       similitud + coexistencia + robustez + mega-cluster diagnóstico
                                     |
                                     v
              figuras + atlas + explorador + reporte + presentación
```
