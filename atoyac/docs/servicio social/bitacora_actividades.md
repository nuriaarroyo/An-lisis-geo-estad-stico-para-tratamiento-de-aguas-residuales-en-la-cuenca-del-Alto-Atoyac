# Bitácora de actividades de servicio social

## Datos generales

| Campo | Información |
|---|---|
| Proyecto | Análisis geo-estadístico para tratamiento de aguas residuales en la cuenca del Alto Atoyac |
| Prestadora | Nuria Arroyo Bustamante |
| Matrícula | 173605 |
| Institución | Universidad de las Américas Puebla |
| Periodo documentado en Git | 25 de mayo–24 de septiembre de 2026 |
| Fecha de corte de la bitácora | 24 de septiembre de 2026 |
| Repositorio | Proyecto Alto Atoyac: carpetas `version_01/` y `atoyac/` |

## Propósito de la bitácora

Esta bitácora registra las actividades realizadas durante el desarrollo del proyecto, desde la construcción inicial de un universo textil local hasta la consolidación de un análisis regional de concentraciones económicas dentro de la cuenca del Alto Atoyac. Incluye investigación de fuentes, programación, depuración y auditoría de datos, análisis geoespacial, exploración estadística, documentación metodológica y preparación de productos de comunicación.

Las fechas proceden del historial de Git cuando existe un punto de control verificable. Muchas actividades se desarrollaron de manera continua entre commits; por ello la bitácora se organiza principalmente por etapas y productos, no como un registro diario de horas. Las horas incluidas en este documento son estimaciones retrospectivas basadas en el alcance, complejidad y productos de cada bloque de trabajo; deberán validarse con la coordinación institucional antes de emplearse como horas oficialmente acreditadas.

## Resumen solicitado para seguimiento de servicio social

### 1. Actividades en las que participa

La siguiente tabla reúne las actividades realizadas y las que continúan abiertas. El porcentaje indica avance del producto o tarea descrita, no porcentaje de horas del servicio social.

| Núm. | Actividad | Estado | Evidencia principal | Avance |
|---:|---|---|---|---:|
| 1 | Investigación y organización de fuentes DENUE, territoriales e hídricas | Realizada | `version_01/data/`, `atoyac/data/` | 100 % |
| 2 | Definición de códigos SCIAN, palabras clave y reglas auditables | Realizada | Configuración de `version_01/` y scripts `02–04` | 100 % |
| 3 | Construcción del universo textil independiente de Santa Ana Xalmimilulco | Realizada | `version_01/outputs/universo_independiente_3_localidades/` | 100 % |
| 4 | Auditoría manual y refinamiento de casos de Xalmimilulco | Realizada | Auditables, colas y productos legacy | 100 % |
| 5 | Comparación posterior con fuentes MH y canónicas | Realizada | `version_01/outputs/comparacion_3_localidades/` | 100 % |
| 6 | Integración de la evidencia de campo MH con trazabilidad de fuente | Realizada | Script `10_integrar_mh.py` y auditorías regionales | 100 % |
| 7 | Escalamiento a 26 municipios relacionados con la cuenca | Realizada | Script `101_main_cuenca_puebla.py` | 100 % |
| 8 | Construcción y comparación de cinco modalidades regionales | Realizada | `atoyac/outputs/cuenca_alto_atoyac_puebla*/` | 100 % |
| 9 | Generación de capas, mapas PNG y mapas interactivos | Realizada | Carpetas `layers/`, `maps/png/` y `maps/html/` | 100 % |
| 10 | Construcción de matriz maestra y control del efecto de borde | Realizada | `outputs/parte_2/00_auditoria/` a `02_geometrias/` | 100 % |
| 11 | Diagnóstico espacial con vecinos, KDE y mallas hexagonales | Realizada | `outputs/parte_2/03_diagnosticos/` | 100 % |
| 12 | Exploración de 57 configuraciones DBSCAN, HDBSCAN y OPTICS | Realizada | `outputs/parte_2/04_clustering/` | 100 % |
| 13 | Selección, estabilidad y sensibilidad de la solución espacial | Realizada | `outputs/parte_2/05_seleccion/` y `06_clusters/` | 100 % |
| 14 | Perfilado económico, territorial e hídrico de clusters y ruido | Realizada | `outputs/parte_2/07_perfiles/` | 100 % |
| 15 | Sobrerrepresentación, similitud y tipologías productivas | Realizada | `08_sobrerrepresentacion/` y `09_comparacion/` | 100 % |
| 16 | Diagnóstico del mega-cluster y subnúcleos exploratorios | Realizada | `11_cierre/` y `14_segunda_pasada/` | 100 % |
| 17 | Elaboración de atlas, figuras, presentación y explorador interactivo | Realizada | `12_atlas/`, `13_figuras_finales/` y HTML interactivo | 100 % |
| 18 | Elaboración del reporte maestro y reporte sintético | Realizada | `docs/reporte_completo/` y `docs/reporte_sintetico/` | 100 % |
| 19 | Inventario, trazabilidad, README y documentación metodológica | Realizada, con mantenimiento continuo | `docs/`, README raíz y `atoyac/README.md` | 95 % |
| 20 | Preparación conceptual de la integración hídrica futura | En desarrollo | Sección de siguientes pasos y diagrama de flujo | 35 % |
| 21 | Obtención e integración de red de drenaje, captadores y plantas | Pendiente de datos institucionales | Pendiente de capas del organismo operador | 0 % |
| 22 | Validación de campo, aforos, trazadores y muestreo | Pendiente de coordinación | Protocolo y campaña todavía no ejecutados | 0 % |
| 23 | Modelación de rutas de residuos y escenarios de tratamiento | Pendiente de las actividades 21–22 | No existe todavía un resultado hidráulico validado | 0 % |

### 2. Horas realizadas

El repositorio conserva fechas de commits y productos, pero **no registra automáticamente las horas trabajadas**. A partir del alcance verificable de los entregables producidos entre el 25 de mayo y el 24 de septiembre de 2026 se estima una dedicación acumulada de **380 horas**. Esta cifra funciona como una reconstrucción razonada del esfuerzo y no sustituye la validación de una bitácora horaria o el visto bueno de la persona responsable del servicio social.

| Concepto | Horas |
|---|---:|
| Horas estimadas del periodo documentado | **380 h** |
| Horas oficialmente validadas | **Pendientes de validación institucional** |
| Total estimado acumulado a este corte | **380 h** |
| Meta total del programa | **Por confirmar con la institución** |

#### Desglose estimado de horas por bloque de actividad

| Fecha o periodo | Actividad | Horas estimadas | Evidencia/entregable | Validación |
|---|---|---:|---|---|
| Mayo–septiembre de 2026 | Desarrollo y auditoría de la versión 1 | 70 h | Scripts, tablas y reporte local | Estimación |
| Mayo–septiembre de 2026 | Construcción de universos regionales | 55 h | Cinco carpetas de resultados | Estimación |
| Mayo–septiembre de 2026 | Cartografía y análisis espacial | 60 h | Mapas, capas y diagnósticos | Estimación |
| Mayo–septiembre de 2026 | Clustering y evaluación de robustez | 80 h | Etapas 04–06 de Parte 2 | Estimación |
| Mayo–septiembre de 2026 | Perfilado y análisis estadístico | 45 h | Etapas 07–09 de Parte 2 | Estimación |
| Mayo–septiembre de 2026 | Reportes, atlas y documentación | 70 h | PDF, README e inventarios | Estimación |
|  | **Total estimado** | **380 h** |  | **Por validar** |

### 3. Porcentaje de avance de las actividades solicitadas

Para resumir el avance se distinguen dos alcances. El primero es el **análisis geo-estadístico actualmente comprometido**, que llega hasta la identificación, perfilado y documentación de concentraciones. El segundo es la **ampliación hidráulica futura**, que depende de capas y validaciones externas.

| Alcance evaluado | Criterio | Avance estimado |
|---|---|---:|
| Construcción y auditoría del universo | Fuentes, reglas, modalidades y matriz maestra terminadas | 100 % |
| Análisis territorial y cartografía | Capas y mapas estáticos/interactivos generados | 100 % |
| Clustering y robustez | Exploración, selección, sensibilidad y persistencia documentadas | 100 % |
| Perfilado e interpretación | Perfiles, sobrerrepresentación, similitud, ruido y mega-cluster terminados | 100 % |
| Comunicación y trazabilidad | Reportes, atlas, inventarios y README terminados; requieren mantenimiento al cambiar el proyecto | 95 % |
| **Avance del análisis geo-estadístico actual** | Promedio de los cinco componentes anteriores | **99 %** |
| Diseño conceptual de la fase hidráulica | Objetivos, capas necesarias, flujo y límites definidos | 35 % |
| Integración hidráulica aplicada | Drenaje, captadores, plantas, rutas y validación todavía no ejecutados | 0 % |

El 99 % no significa que el problema ambiental o de infraestructura esté resuelto. Significa que el alcance actual de construcción del universo, análisis de concentraciones y documentación está prácticamente cerrado, con mantenimiento editorial menor pendiente. La etapa hidráulica es un nuevo alcance y no debe mezclarse con el porcentaje de terminación del análisis geo-estadístico.

## Resumen de aportaciones

1. Construcción de universos textiles e hídricos auditables a partir de DENUE.
2. Desarrollo y documentación de filtros SCIAN y reglas textuales.
3. Auditoría manual de establecimientos de Santa Ana Xalmimilulco.
4. Integración diferenciada de evidencia de campo MH.
5. Escalamiento del análisis a 26 municipios relacionados con la cuenca.
6. Generación de cinco modalidades comparables del universo regional.
7. Construcción de cartografía estática e interactiva.
8. Exploración de clustering espacial con DBSCAN, HDBSCAN y OPTICS.
9. Selección y evaluación de robustez de una solución espacial reproducible.
10. Perfilado productivo y territorial de clusters y actividad dispersa.
11. Análisis de sobrerrepresentación y similitud entre perfiles.
12. Diagnóstico interno del mega-cluster metropolitano.
13. Elaboración de atlas, presentaciones, reporte maestro y reporte sintético.
14. Organización de trazabilidad, inventarios, decisiones y siguientes pasos.
15. Preparación conceptual de la futura integración con hidrología, relieve, drenaje y tratamiento.

## Bitácora cronológica por etapas

### Etapa 1. Preparación del análisis geoespacial reproducible

**Periodo verificable:** mayo de 2026  
**Puntos de control Git:** `2eb2057`, `54d24f2`

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Revisión inicial del problema | Se tradujo el problema general de actividad textil y agua en una secuencia de análisis territorial reproducible. | Estructura inicial de `version_01/`. |
| Organización de fuentes geográficas | Se prepararon insumos DENUE, localidades y capas territoriales para su lectura con herramientas geoespaciales. | `version_01/data/` y scripts de preparación. |
| Normalización de identificadores | Se definieron llaves y criterios para conservar correspondencia entre registros tabulares y geometrías. | Capas y tablas auditables. |
| Definición de recortes territoriales | Se configuraron Santa Ana Xalmimilulco, Huejotzingo y San Martín Texmelucan como ámbitos de trabajo iniciales. | Configuración de localidades en `version_01/`. |
| Diseño de un flujo por etapas | Se separaron preparación, clasificación, refinamiento, auditoría y comparación. | Scripts numerados y ejecutor local. |
| Primeras auditorías | Se incorporaron controles de conteos, campos y decisiones para evitar clasificaciones opacas. | Commit de auditoría y productos de control. |

### Etapa 2. Construcción del universo textil independiente

**Periodo verificable:** mayo–junio de 2026  
**Puntos de control Git:** `5fab10d`, `f961955`

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Investigación de códigos SCIAN | Se identificaron actividades textiles, confección y servicios relacionados para construir el universo de interés. | `version_01/config/` y catálogos. |
| Construcción de catálogo de palabras | Se organizaron expresiones asociadas con textil, mezclilla, lavado, producción, maquila y procesos secos o húmedos. | `palabras_clave.csv`. |
| Diseño de reglas de clasificación | Se formalizó la precedencia entre señales SCIAN, coincidencias textuales, exclusiones y estados de revisión. | `reglas_clasificacion.csv` y `matriz_decision.csv`. |
| Separación de categorías | Se distinguieron pertenencia sectorial, prioridad analítica y evidencia potencialmente hídrica. | `politica_categorias.csv`. |
| Programación del clasificador | Se implementaron las reglas en Python sin utilizar todavía MH o el universo canónico como entrada de clasificación. | Scripts de `version_01/scripts/`. |
| Construcción del universo amplio | Se produjeron conjuntos independientes de establecimientos con señales textiles. | `version_01/outputs/universo_independiente_3_localidades/`. |
| Refinamiento de alcance | Se aplicaron exclusiones y prioridades sin buscar nuevos registros fuera del universo inicial. | `version_01/outputs/universo_refinado_santa_ana/`. |
| Generación de colas manuales | Se prepararon casos de SCIAN 314 y maquila para revisión humana, con enlaces cartográficos y campos de decisión. | `cola_revision_manual_314.csv` y `cola_revision_manual_20.csv`. |

### Etapa 3. Auditoría manual de Santa Ana Xalmimilulco

**Periodo verificable:** junio–julio de 2026  
**Puntos de control Git:** `6b640de`, `44eb26d`, `3f30762`, `f284fa6`, `86becfa`

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Revisión establecimiento por establecimiento | Se realizó manualmente la auditoría de casos prioritarios de Santa Ana Xalmimilulco. | Tablas legacy y auditables locales. |
| Registro de decisiones humanas | Se conservaron campos para evidencia, observaciones, inclusión y motivo de decisión. | Colas y tablas de auditoría. |
| Verificación de maquilas | Se preparó y revisó un subconjunto específico de unidades asociadas con maquila. | Script y cola de revisión de maquila. |
| Construcción del universo hídrico preliminar | Se combinaron reglas automáticas y decisiones manuales para un conjunto local preliminar. | `universo_hidrico_preliminar.csv`. |
| Comparación con MH | Se incorporó una comparación posterior con la evidencia de campo disponible. | Commits “comparacion mh” y productos de comparación. |
| Comparación con universo canónico | Se midieron coincidencias, altas y bajas sin usar el universo histórico para entrenar el clasificador independiente. | `version_01/outputs/comparacion_3_localidades/`. |
| Conservación de la trazabilidad legacy | Se organizaron los productos tempranos para impedir que fueran confundidos con el pipeline regional posterior. | `version_01/outputs/legacy/`. |
| Elaboración de reporte metodológico local | Se documentaron reglas, conteos, comparación y limitaciones de la fase. | `reporte_metodologico.md`. |

### Etapa 4. Formalización de la versión 1

**Periodo verificable:** julio–agosto de 2026  
**Puntos de control Git:** `b42c139`, `e5831b0`

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Consolidación del pipeline local | Se creó un ejecutor que reproduce las etapas principales de Santa Ana en orden. | `run_santa_ana_pipeline.py`. |
| Externalización de configuración | Se trasladaron reglas y políticas a CSV y JSON para evitar decisiones ocultas en código. | `version_01/config/filtros_textiles_santa_ana/versiones/v1/`. |
| Documentación del flujo | Se redactaron README para datos, scripts legacy, productos y filtros. | README internos de `version_01/`. |
| Control de resultados congelados | Se distinguieron resultados independientes de referencias abiertas posteriormente. | Manifiestos y reportes de comparación. |
| Identificación de límites | Se documentó que la fase local no debía extrapolarse manualmente a toda la cuenca. | Reporte metodológico y decisiones posteriores. |

### Etapa 5. Reorganización y transición al análisis regional

**Fecha de consolidación:** 24 de septiembre de 2026  
**Puntos de control Git:** `528c019`, `3d69baf`, `7cd11ab`

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Revisión y limpieza de filtros | Se actualizaron filtros y se separaron productos legacy de resultados vigentes. | Commit `528c019`. |
| Reorganización de la fase histórica | Se concentró el pipeline anterior bajo `version_01/`. | Commit `3d69baf`. |
| Creación de la fase moderna | Se integraron en `atoyac/` los flujos locales, regionales, scripts de clustering, documentación y outputs. | Commit `7cd11ab`. |
| Inventario de fuentes | Se documentaron DENUE, cuenca, municipios, hidrografía, MH y archivos legacy. | `atoyac/docs/INVENTARIO_GENERAL_PROYECTO.md`. |
| Distinción metodológica de MH | Se estableció que MH proviene de investigación de campo y no es un atributo original de DENUE. | Reporte maestro y auditorías de integración. |
| Definición de transición de alcance | Se explicó el paso de Xalmimilulco/Huejotzingo al conjunto regional de municipios. | Secciones 7–10 del reporte maestro. |

### Etapa 6. Construcción de universos regionales comparables

**Fecha de consolidación:** 24 de septiembre de 2026

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Procesamiento de descarga estatal | Se trabajó con 15,956 registros acotados a actividades SCIAN seleccionadas. | Tablas regionales y resúmenes de ejecución. |
| Selección de municipios | Se definió un ámbito de 26 municipios relacionado con la cuenca; se registró presencia de datos en 24. | Coberturas municipales. |
| Construcción del universo sectorial | Se integraron 4,365 establecimientos como denominador amplio de detección. | `outputs/cuenca_alto_atoyac_puebla_todos_scian/`. |
| Intersección con la cuenca | Se identificaron 4,010 establecimientos dentro del polígono para interpretación. | Tablas y capas dentro de cuenca. |
| Modalidad amplia DENUE | Se construyó una selección de alta cobertura sin MH. | `outputs/cuenca_alto_atoyac_puebla_sin_mh/`. |
| Modalidad amplia + MH | Se integró MH manteniendo procedencia y enlaces de ID. | `outputs/cuenca_alto_atoyac_puebla/`. |
| Modalidad estricta DENUE | Se exigió señal adicional para lavanderías y se eliminaron procesos explícitamente secos cuando correspondía. | `outputs/cuenca_alto_atoyac_puebla_estricto_sin_mh/`. |
| Modalidad estricta + MH | Se añadió evidencia de campo al escenario restrictivo. | `outputs/cuenca_alto_atoyac_puebla_estricto_mh/`. |
| Auditoría de integración MH | Se documentaron coincidencias, registros añadidos, fuente original e identificadores enlazados. | `auditoria_integracion_mh.csv`. |
| Comparación entre modalidades | Se compararon conteos, composición municipal, unidades pequeñas y posibles lavanderías comerciales. | Presentación a dirección y tablas comparativas. |

### Etapa 7. Cartografía territorial y proximidad a hidrografía

**Fecha de consolidación:** 24 de septiembre de 2026

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Preparación de capas | Se generaron GeoPackages de universos, cuenca, municipios y contexto territorial. | Carpetas `layers/` de cada modalidad. |
| Reproyección métrica | Se utilizó EPSG:32614 para distancias y operaciones espaciales cuantitativas. | Scripts regionales y Parte 2. |
| Distancia a red hidrográfica | Se calculó la distancia euclidiana mínima entre establecimientos y la red disponible. | Tablas y mapas de distancia. |
| Clasificación por intervalos | Se resumieron distancias en 0–250 m, 250–500 m, 500–1,000 m, 1–2 km y más de 2 km. | Productos territoriales. |
| Mapas municipales y por localidad | Se generaron conteos, participaciones, estratos y distribuciones territoriales. | 30 PNG y 30 HTML por corrida regional. |
| Mapas interactivos | Se crearon productos HTML para inspección de establecimientos y contexto. | `maps/html/`. |
| Documentación de limitaciones | Se aclaró que proximidad a una línea hídrica no prueba conexión ni descarga. | Reportes y pies de figura. |

### Etapa 8. Diagnóstico espacial previo al clustering

**Fecha de consolidación:** 24 de septiembre de 2026

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Construcción de matriz maestra | Se consolidaron IDs, coordenadas, señales y marca dentro/fuera de cuenca para 4,365 registros. | `outputs/parte_2/01_matriz/`. |
| Auditoría de integridad | Se verificaron rutas, conteos, unicidad y hashes de fuentes. | `outputs/parte_2/00_auditoria/`. |
| Preparación de geometrías | Se produjeron capas en EPSG:4326 y EPSG:32614. | `outputs/parte_2/02_geometrias/`. |
| Diagnóstico k-NN | Se estudiaron distancias a vecinos para observar escalas y heterogeneidad. | Tablas y curvas k-distancia. |
| Estimación KDE | Se generaron superficies gaussianas a varias escalas para observar intensidad relativa. | Figuras KDE de cuenca y mega-cluster. |
| Mallas hexagonales | Se calcularon conteos directos en hexágonos de distintas escalas. | GeoPackages, tablas y figuras. |
| Corrección de visualización | Se evitó interpretar el recorte de la superficie gaussiana como límite matemático de densidad. | Figuras finales y explicación técnica. |
| Diagnóstico de densidad variable | Se concluyó que coexistían concentraciones compactas y zonas continuas, justificando comparar varias familias de clustering. | Sección 11 del reporte maestro. |

### Etapa 9. Exploración y selección del clustering

**Fecha de consolidación:** 24 de septiembre de 2026

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Definición experimental | Se estableció que el clustering usaría exclusivamente coordenadas, sin atributos productivos. | Decisiones metodológicas. |
| Evaluación de DBSCAN | Se recorrieron configuraciones con radios fijos como referencia interpretable. | `outputs/parte_2/04_clustering/`. |
| Evaluación de HDBSCAN | Se exploraron tamaños mínimos, vecinos y selección EOM/leaf. | Escenarios y membresías. |
| Evaluación de OPTICS | Se utilizó como contraste para estructuras de densidad variable. | Resumen de escenarios. |
| Comparación de 57 configuraciones | Se almacenaron clusters, ruido, tamaños, cluster mayor y probabilidades. | `resumen_escenarios.csv`. |
| Exclusión de soluciones degeneradas | Se aplicaron límites de clusters, ruido y dominio del grupo mayor. | Script de selección. |
| Construcción de puntaje operativo | Se combinaron estabilidad, pertenencia, ruido, mega-cluster, resolución y encadenamiento. | Decisión JSON y tablas. |
| Selección de solución principal | Se eligió HDBSCAN con `min_cluster_size=10`, `min_samples=20`, EOM. | `solucion_principal.gpkg`. |
| Comparación con alternativas cercanas | Se documentó que dos HDBSCAN tienen puntajes 0.962 frente a 0.963 y son prácticamente equivalentes. | Reporte maestro, sección 13.3. |
| Control del efecto de borde | Se detectó sobre 4,365 puntos y se interpretó sobre 4,010 interiores. | Resumen de borde. |

### Etapa 10. Robustez, persistencia y ruido

**Fecha de consolidación:** 24 de septiembre de 2026

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Comparación ARI | Se midió similitud global entre particiones seleccionadas. | Matrices ARI. |
| Comparación Jaccard | Se emparejaron clusters para medir solapamiento local. | Tablas Jaccard. |
| Perturbación posicional | Se desplazaron coordenadas 25 m para evaluar sensibilidad a imprecisión espacial. | Resúmenes de robustez. |
| Persistencia por establecimiento | Se calculó la frecuencia con la que cada unidad conserva asignación equivalente. | `persistencia_establecimientos.csv`. |
| Clasificación de estabilidad | Se identificaron 4,107 núcleos robustos, 94 estables y 164 sensibles. | Figuras y tablas. |
| Conservación del ruido | Se mantuvieron 584 registros como actividad dispersa en detección, sin tratarlos como irrelevantes. | Capas y perfiles de ruido. |
| Análisis clusters vs. ruido | Se comparó composición productiva de actividad agrupada y dispersa. | `08_clusters_vs_ruido.png` y tablas. |

### Etapa 11. Perfil económico y productivo posterior

**Fecha de consolidación:** 24 de septiembre de 2026

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Perfilado territorial | Se resumieron municipios, localidades y composición de cada cluster. | `outputs/parte_2/07_perfiles/`. |
| Perfilado SCIAN | Se calcularon composiciones por nivel de actividad. | Tablas SCIAN. |
| Perfil de tamaño laboral | Se analizaron estratos de personal ocupado sin convertirlos en producción o carga. | Tablas y gráficas. |
| Perfil multilabel | Se describieron confección, maquila, mezclilla, tejido, lavado, procesos húmedos y secos. | `composicion_multilabel.csv`. |
| Sobrerrepresentación | Se calcularon prevalencia, diferencia, lift, OR, IC, Fisher y BH para 342 pares grupo–señal. | `sobrerrepresentacion_senales.csv`. |
| Limitación inferencial | Se aclaró que DENUE no es muestra probabilística y los contrastes no corrigen dependencia espacial. | Reporte maestro. |
| Sensibilidad del cluster 20 | Se compararon lavandería sectorial, universo estricto, evidencia SI/SI+REVISAR, húmedo explícito y lavado contextualizado. | Sección 16.3 del reporte. |
| Similitud entre perfiles | Se calcularon distancias y tipologías productivas exploratorias. | `outputs/parte_2/09_comparacion/`. |
| Interpretación territorial | Se identificaron perfiles distintivos de Xalmimilulco, Huejotzingo, Tlahuapan, Texmelucan, Xoxtla, Amozoc y el sistema metropolitano. | Reportes y figuras. |

### Etapa 12. Segunda pasada y diagnóstico del mega-cluster

**Fecha de consolidación:** 24 de septiembre de 2026

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Congelamiento de membresía | Se mantuvo intacta la solución principal durante análisis posteriores. | Auditoría de cierre. |
| Diagnóstico multiescala interno | Se repitieron KDE y hexágonos dentro del cluster 20. | Figuras del mega-cluster. |
| Identificación de subnúcleos | Se documentaron 18 ramas exploratorias con HDBSCAN leaf. | `subnucleos_mega_cluster_documentados.csv`. |
| Conservación de no asignados internos | Se registró que 44.5 % no pertenece a una rama local, pero conserva membresía principal. | Diagnóstico y mapas. |
| Figuras de estabilidad | Se generaron visualizaciones de ARI, persistencia y distancias entre perfiles. | `outputs/parte_2/14_segunda_pasada/figuras/`. |
| Explorador interactivo | Se construyó un HTML autocontenido con establecimientos, clusters y filtros. | `explorador_interactivo_clusters.html`. |
| Registro de documentación | Se inventariaron figuras y variables analíticas de la segunda pasada. | CSV y glosario de la etapa 14. |

### Etapa 13. Comunicación, reportes y trazabilidad

**Fecha de consolidación:** 24 de septiembre de 2026  
**Puntos de control Git:** `a72c504`, `991d1ff`, `985173c`, `e6c43c0`

| Actividad | Descripción | Evidencia o producto |
|---|---|---|
| Presentación a dirección | Se sintetizaron modalidades, conteos, mapas, diferencias municipales y límites. | `atoyac/docs/dir1/`. |
| Atlas de clusters | Se produjeron fichas comparables para 18 clusters interiores y ruido. | `outputs/parte_2/12_atlas/`. |
| Figuras finales | Se generaron mapas de universos, clusters, persistencia, perfiles, robustez, rasgos y mega-cluster. | `outputs/parte_2/13_figuras_finales/`. |
| Reporte maestro | Se estructuró la trazabilidad desde el problema de decisión hasta siguientes pasos y anexos. | `docs/reporte_completo/`. |
| Corrección metodológica | Se precisaron selección no única, bases de lift/OR, límites de Fisher/BH y sensibilidad del cluster 20. | Secciones 11, 13 y 16. |
| Reporte sintético | Se creó un documento de 17 páginas para público menos técnico. | `docs/reporte_sintetico/`. |
| Diagrama de flujo | Se representó la transición desde fuentes hasta integración hídrica futura. | Reporte sintético, sección 4. |
| Diccionario de conceptos | Se agregó un anexo con términos metodológicos, territoriales e hidráulicos. | Reporte sintético, anexo A. |
| Changelog y pendientes | Se documentaron cambios y decisiones que todavía requieren intervención humana. | Markdown del reporte sintético. |
| Inventario del proyecto | Se creó un inventario general de scripts, fuentes, outputs y vacíos. | `docs/INVENTARIO_GENERAL_PROYECTO.md`. |
| README de la fase regional | Se documentaron estado, resultados, ejecución y próxima etapa. | `atoyac/README.md`. |
| README general | Se actualizó la portada del repositorio para explicar `version_01/` y `atoyac/`. | README raíz. |

### Etapa 14. Preparación de la integración hídrica futura

**Estado:** propuesta metodológica; no constituye un análisis ya ejecutado.

| Actividad realizada | Alcance alcanzado | Trabajo todavía requerido |
|---|---|---|
| Definición conceptual de la siguiente fase | Se estableció que debe integrar concentraciones con hidrología, relieve y drenaje. | Conseguir y validar las capas operativas. |
| Identificación de infraestructura necesaria | Se enumeraron atarjeas, colectores, pozos, cárcamos, captadores, interceptores y plantas. | Obtener trazos, cotas, capacidad y estado. |
| Formulación de rutas potenciales | Se definió la necesidad de estudiar flujos por gravedad o bombeo hacia cuerpos de agua. | Modelar y verificar rutas con el organismo operador. |
| Diseño de validación | Se propusieron inspección, aforos, trazadores y muestreo fisicoquímico. | Definir protocolo, laboratorio, cadena de custodia y muestra. |
| Marco de decisión | Se señalaron caudal, carga, CAPEX, OPEX, riesgo, permisos y gobernanza. | Acordar criterios institucionales y escenarios de inversión. |

## Actividades técnicas transversales

Además de las etapas anteriores, durante el proyecto se realizaron de manera recurrente:

- lectura, limpieza y normalización de CSV, GeoPackage, GeoJSON y shapefiles;
- homologación de campos, IDs, texto, fechas y valores booleanos;
- control de duplicados, faltantes, geometrías y sistemas de referencia;
- programación modular en Python;
- generación y revisión de mapas con GeoPandas, Matplotlib y Folium;
- preparación de tablas para hojas de cálculo, SIG y análisis estadístico;
- compilación de documentos LaTeX y revisión de tablas, figuras y desbordamientos;
- creación de manifiestos, hashes e inventarios de productos;
- documentación de decisiones, limitaciones, sesgos y condiciones de revisión;
- control de versiones con Git y publicación de avances en GitHub;
- preservación de productos legacy sin sobrescribir resultados históricos;
- revisión de consistencia entre texto, tablas, código y archivos de salida.

## Productos consultables

| Producto | Ruta |
|---|---|
| README general | `README.md` en la raíz del repositorio |
| README regional | `atoyac/README.md` |
| Inventario detallado | `atoyac/docs/INVENTARIO_GENERAL_PROYECTO.md` |
| Reporte maestro | `atoyac/docs/reporte_completo/reporte_compelto.pdf` |
| Reporte sintético | `atoyac/docs/reporte_sintetico/reporte_sintetico.pdf` |
| Matriz maestra | `atoyac/outputs/parte_2/01_matriz/matriz_maestra_establecimientos.csv` |
| Solución espacial | `atoyac/outputs/parte_2/06_clusters/solucion_principal.gpkg` |
| Perfiles | `atoyac/outputs/parte_2/07_perfiles/` |
| Sobrerrepresentación | `atoyac/outputs/parte_2/08_sobrerrepresentacion/` |
| Auditoría de cierre | `atoyac/outputs/parte_2/11_cierre/` |
| Atlas | `atoyac/outputs/parte_2/12_atlas/` |
| Figuras finales | `atoyac/outputs/parte_2/13_figuras_finales/` |
| Segunda pasada | `atoyac/outputs/parte_2/14_segunda_pasada/` |

## Competencias desarrolladas y aplicadas

- Gestión y documentación de datos públicos.
- Diseño de reglas de clasificación auditables.
- Análisis espacial y sistemas de información geográfica.
- Programación y automatización con Python.
- Clustering por densidad y evaluación de sensibilidad.
- Estadística descriptiva y contraste de asociaciones.
- Visualización cartográfica y comunicación de resultados.
- Trazabilidad, reproducibilidad y control de versiones.
- Traducción de resultados técnicos a preguntas operativas.
- Identificación responsable de límites antes de decisiones de infraestructura.

## Pendientes que requieren coordinación humana o institucional

- Confirmar responsable formal, asesoría, periodo y horas reconocidas del servicio social.
- Completar metadatos, fecha, protocolo y condiciones de uso de la fuente MH.
- Obtener cartografía actualizada de drenaje y tratamiento del organismo operador.
- Definir una campaña de verificación de establecimientos y descargas.
- Acordar protocolo de aforo, muestreo, laboratorio y cadena de custodia.
- Validar qué registros sectoriales corresponden a lavanderías industriales reales.
- Definir criterios de evaluación económica, ambiental y de gobernanza.
- Crear un entorno de software fijado para reproducir todo el repositorio en otro equipo.

## Registro resumido de hitos Git

| Fecha | Commit | Hito |
|---|---|---|
| 25 mayo 2026 | `2eb2057` | Inicio del análisis geoespacial reproducible. |
| 25 mayo 2026 | `54d24f2` | Incorporación de auditoría. |
| 11 junio 2026 | `5fab10d` | Avance de controles auditables. |
| 25 junio 2026 | `6b640de` | Comparación con MH. |
| 2 julio 2026 | `f284fa6` | Organización de productos legacy. |
| 27 agosto 2026 | `e5831b0` | Pipeline textil e hídrico auditable de Santa Ana. |
| 24 septiembre 2026 | `3d69baf` | Reorganización de la fase histórica en `version_01`. |
| 24 septiembre 2026 | `7cd11ab` | Integración de la fase moderna regional. |
| 24 septiembre 2026 | `a72c504` | Reporte metodológico y siguientes pasos. |
| 24 septiembre 2026 | `991d1ff` | Reporte sintético y ajustes metodológicos. |
| 24 septiembre 2026 | `e6c43c0` | README general del repositorio. |

## Nota para entrega institucional

Esta bitácora describe actividades y productos comprobables en el repositorio. Para convertirla en un formato oficial de servicio social deben validarse las 380 horas estimadas y agregarse, cuando la institución lo requiera, las fechas exactas por jornada, firma o visto bueno, objetivos del programa y relación de cada actividad con las competencias o metas oficiales.
