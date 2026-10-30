# Documento técnico de integración — Parte 3

## Objetivo y alcance

La base integra el universo textil y la partición espacial congelada de Parte 2 con la infraestructura hídrica disponible. Su función es habilitar análisis posteriores de conectividad, presión potencial, cobertura, capacidad, posición aguas arriba/abajo y diseño de monitoreo. En esta etapa no se atribuyen descargas de establecimientos a colectores o PTAR.

## Estructura propuesta e implementada

La secuencia `300+` separa auditoría del proyecto QGIS (`300`), organización de archivos PTAR/RH18 (`301`) e integración analítica (`302`). Los outputs siguen seis etapas: auditoría, homologación, integración, relaciones, QA y mapas. El GeoPackage central contiene establecimientos, clusters, subnúcleos, colectores, descargas, PTAR, hidrografía, cuerpos receptores, municipios y límite de cuenca, además de tablas no espaciales de fuentes y proximidad.

## Archivos reutilizados de Partes 1 y 2

- `outputs/parte_2/06_clusters/solucion_principal.gpkg`: establecimientos y envolventes de clusters.
- `outputs/parte_2/11_cierre/diagnostico_mega_cluster.gpkg`: membresía exploratoria de subnúcleos.
- `outputs/parte_2/14_segunda_pasada/subnucleos_mega_cluster_documentados.csv`: atributos descriptivos de subnúcleos.
- `outputs/parte_3/01_insumos_organizados/parte_3_insumos_base.gpkg`: PTAR, descargas, hidrografía y límites ya normalizados.
- Reporte PDF y proyecto QGIS de Lesly: evidencia documental y de estructura, no sustitutos de geometrías faltantes.

No se reconstruyó el universo DENUE. Los 4,365 establecimientos y la solución HDBSCAN permanecen congelados como fueron entregados por Parte 2.

## Homologación y modelo de datos

Las capas se transformaron a EPSG:32614 y recibieron identificadores internos estables. Los establecimientos conservan `d_llave`, SCIAN, señales productivas, cluster, persistencia y auditoría. Los subnúcleos son envolventes diagnósticas de la subdivisión interna del cluster 20 y no una nueva solución regional.

El nivel de evidencia se interpreta así: A, registro o documento oficial explícito; B, consistencia entre fuentes o producto analítico consolidado; C, evidencia parcial o proximidad espacial; D, información desconocida o insuficiente. Una fuente oficial puede acreditar el registro sin acreditar operación actual.

## PTAR y conciliación

Se preservaron 65 registros INEGI y cuatro registros de PTAR de la compilación manual. El quinto elemento de `PTAR_Final.csv`, Global Denim, fue clasificado como descarga industrial por su propio campo `Tipo`. La tabla `ptar_fuentes` conserva la procedencia y `conciliacion_ptar.csv` compara cada registro manual con sus tres candidatos INEGI más próximos usando distancia, similitud de nombre y municipio. Las coincidencias probables no se fusionan físicamente sin revisión.

Capacidad instalada y caudal tratado son atributos reportados en fechas determinadas. Su cociente, si se usa después, se denominará `utilizacion_capacidad_reportada`; no mide eficiencia de remoción ni calidad del tratamiento.

## Colectores, descargas y cuerpos receptores

El QGIS menciona `Camino_contenedores_SMT` y `Camino_contenedores_huejotzingo`, pero son nodos sin entrada de capa ni geometría fuente. Por ello, `colectores` conserva un esquema vacío. No se digitalizaron líneas desde capturas del PDF ni se etiquetaron corredores propuestos como infraestructura existente.

Las 301 descargas INEGI se conservan como tipo `no_especificado`; no se infiere si son municipales o industriales. La descarga manual de Global Denim conserva su clasificación industrial y un estado por verificar. No existe una capa diferenciada y nominada de cuerpos receptores, por lo que su esquema también queda vacío; la hidrografía RH18 no se renombra automáticamente como cuerpo receptor.

## Relaciones espaciales derivadas

Se calcularon PTAR y descargas más cercanas para cada establecimiento. El nivel de evidencia es C y el método es exclusivamente proximidad euclidiana. La relación establecimiento–colector y colector–descarga queda vacía porque no hay geometrías de colectores. Ninguna de estas tablas prueba flujo, conexión, cobertura ni destino del agua residual.

## Control de calidad y ambigüedades

El QA revisa validez geométrica, CRS, puntos fuera de cuenca, PTAR candidatas a duplicidad, años faltantes y utilización reportada anómala. Se conservan 355 establecimientos fuera del límite estricto porque forman parte del contexto de borde de la solución de Parte 2. Las divergencias temporales y registrales se conservan en vez de eliminarse.

Persisten cuatro vacíos decisivos: red sanitaria real, geometrías verificadas de colectores, estado operativo/área de servicio de las PTAR y modelo de elevación para dirección de flujo. También se requiere validación documental y de campo antes de diseñar sitios finales de monitoreo.

## Alcance de los mapas

Los seis mapas son diagnósticos de coexistencia espacial e información disponible. La simbología no representa causalidad. El mapa de colectores vacío hace visible el vacío de información en lugar de ocultarlo.

## Conclusión

La integración establece una base común, trazable y reproducible para cruzar concentración textil e infraestructura. No permite concluir conectividad hidráulica, recepción por colectores, tratamiento efectivo ni capacidad suficiente. Es el punto de partida para incorporar relieve, drenaje sanitario, operación de PTAR y evidencia de campo en la siguiente etapa.
