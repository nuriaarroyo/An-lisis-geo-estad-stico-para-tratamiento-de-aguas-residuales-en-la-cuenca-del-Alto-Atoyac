# Diagnóstico de las capas para una futura red dedicada

## Dictamen general

Los datos permiten definir puntos de origen territoriales y una lista preliminar de PTAR por estudiar, pero no permiten construir todavía un grafo de corredores ni evaluar factibilidad hidráulica. Los principales bloqueos son la ausencia de red vial vectorial, elevación, caudales por origen y geometrías verificadas de colectores.

## Capas suficientemente preparadas

- **Establecimientos de Parte 2:** 4,365 puntos con identificador, actividad, SCIAN, clasificación ambiental y cluster. Son adecuados para localizar posibles orígenes, pero no contienen caudal residual.
- **PTAR:** 69 registros por fuente, con duplicados potenciales conservados. Sirven para formar una lista de destinos por estudiar; no acreditan operación, capacidad libre o compatibilidad con efluente textil.
- **Descargas:** 302 puntos. Sirven como contexto y para identificar necesidades de verificación. El CNGMD no ofrece en este recorte caudal, vínculo de drenaje o receptor declarado.
- **Hidrografía RH18:** 12,161 segmentos dentro de la cuenca. Es útil como restricción territorial y contexto de cauces; no representa drenaje sanitario y carece de nombres de río por segmento.
- **Cuenca y municipios:** adecuados para delimitación regional.

## Capas contextuales o insuficientes

- La franja de 10 m es una referencia geométrica y no una delimitación legal acreditada.
- Los dos supuestos caminos de colectores son nodos huérfanos del proyecto QGIS, sin geometría recuperable.
- No existe capa de localidades; el piloto de Santa Ana usa una envolvente operativa de establecimientos DENUE y no un límite administrativo oficial.
- No existe red vial ni topografía en el repositorio.

## Descargas

La capa integrada contiene 302 puntos: uno en Huejotzingo, uno en San Martín Texmelucan y uno dentro de la envolvente operativa de Santa Ana Xalmimilulco más 2 km. `nom_tipo` fue reinterpretado correctamente como nombre del punto o sistema, no como cuerpo receptor. Para INEGI, `cuerpo_receptor` queda sin dato. `cauce_mas_cercano` y `distancia_cauce_m` son derivados geométricos de nivel C y no sustituyen un receptor declarado.

## PTAR

Las plantas se clasifican metodológicamente según la completitud de sus datos. La aptitud significa únicamente que hay información suficiente para estudiarlas; no que puedan recibir aguas textiles. Para evaluar un destino siguen faltando capacidad libre real, compatibilidad del proceso, calidad de influente admitida, operación actual, permisos y requisitos de pretratamiento.

## Hidrografía y cuerpos receptores

RH18 distingue segmentos y jerarquía hidrológica, pero no contiene nombres. La capa dedicada del Río Atoyac permite reconocerlo con confianza media. Río Xochiac, Tenitzatl y Xopanac están mencionados documentalmente, pero no se forzó su equivalencia con líneas RH18. El catálogo registra explícitamente esta falta.

## Red vial y topografía

No existen capas de calles/caminos ni DEM, CEM, SRTM, LiDAR, curvas o puntos de elevación. En consecuencia, no pueden evaluarse conectividad vial, pendientes, gravedad, bombeo, cruces o costos. Se recomienda obtener una red vial con intersecciones y jerarquía, y un DEM documentado de 5--15 m para prefactibilidad; el diseño requerirá topografía de mayor precisión.
