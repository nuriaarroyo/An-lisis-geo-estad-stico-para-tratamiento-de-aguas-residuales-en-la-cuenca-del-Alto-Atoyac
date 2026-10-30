# Inventario y preparación de `Archivos_PTAR`

## Resultado de la extracción

Se preservó completa la carpeta original y se creó una versión de trabajo trazable en
`outputs/parte_3/01_insumos_organizados/`. El inventario registra 268 archivos y 64 capas
espaciales. El producto central es `parte_3_insumos_base.gpkg`, en EPSG:32614, con capas
homogéneas y recortadas a la geometría de la cuenca cuando corresponde.

| Capa organizada | Objetos | Uso preliminar |
|---|---:|---|
| `limite_cuenca` | 1 | Máscara espacial del análisis |
| `municipios_interseccion_cuenca` | 67 | Agregación y referencia administrativa |
| `rio_atoyac_referencia` | 1,918 | Trazos atribuidos al río Atoyac dentro de la cuenca |
| `franja_10m_referencia` | 1 | Franja geométrica de proximidad; no límite legal validado |
| `inegi_elementos_agua_cuenca` | 1,256 | Inventario conjunto de infraestructura y puntos del CNGMD |
| `inegi_ptar_cuenca` | 65 | Plantas de tratamiento declaradas por INEGI |
| `inegi_descargas_cuenca` | 301 | Puntos de descarga declarados por INEGI |
| `ptar_compilacion_manual` | 5 | Selección adicional con proceso, capacidad y caudal |
| `red_hidrografica_rh18_cuenca` | 12,161 | Hidrografía superficial para análisis de conectividad física |

## Qué contiene la fuente INEGI recortada a la cuenca

El archivo `PTAR-INEGI-Cuenca.csv` no contiene solamente PTAR. Reúne 1,256 registros de
cinco clases: 621 obras de toma, 301 puntos de descarga, 262 prestadores del servicio de
agua potable, 65 plantas de tratamiento y 7 plantas de potabilización. Por ello, el script
conserva la capa completa y además separa PTAR y descargas para evitar mezclar funciones.

La descarga se identifica como CNGMD 2021 distribuido en 2023. Esa temporalidad debe
mantenerse explícita: un registro confirma presencia en la fuente, pero no operación actual,
capacidad disponible ni condiciones de mantenimiento.

## Red hidrográfica RH18

La entrega incluye diez hojas (`RH18Aa` a `RH18Aj`) y cinco familias por hoja:

| Familia | Geometría | Objetos en las diez hojas | Lectura preliminar |
|---|---|---:|---|
| `hl` | Línea | 65,342 | Líneas de flujo/hidrografía; 12,161 quedan dentro de la cuenca |
| `ha` | Polígono | 1,341 | Áreas o cuerpos hidrográficos |
| `dr` | Punto | 52 | Puntos asociados al drenaje de la red hidrográfica |
| `to` | Punto | 3,913 | Elementos de apoyo topológico |
| `subc` | Polígono | 10 | Subcuencas de las hojas |

En esta primera organización solo se integra `hl`, porque es la familia directamente útil
para construir la red superficial. Antes de usar las demás familias se debe validar su
semántica exacta contra el documento técnico incluido. En particular, la palabra “drenaje”
en RH18 se refiere al drenaje natural de la red hidrográfica y no a tuberías de alcantarillado.

## Distinción entre las dos fuentes de PTAR

`inegi_ptar_cuenca` conserva 65 registros homogéneos extraídos del inventario INEGI.
`ptar_compilacion_manual` contiene cinco registros seleccionados con variables adicionales
como proceso, capacidad instalada y caudal tratado. No se fusionaron automáticamente porque
pueden representar años, criterios y entidades diferentes; primero debe realizarse una
conciliación por nombre, municipio, proximidad espacial y fuente temporal.

## Qué ya puede analizarse

- Distancias de concentraciones económicas a cauces, descargas y PTAR.
- Posición aguas arriba/abajo sobre la red superficial, después de validar dirección y
  continuidad topológica.
- Perfiles municipales de presencia de PTAR, descargas y captaciones.
- Vacíos territoriales y prioridades para verificar infraestructura en campo.
- Conciliación de las cinco PTAR compiladas con los 65 registros INEGI.

## Qué falta para la Parte 3 aplicada

- Un modelo digital de elevación para pendiente, dirección de flujo y rutas plausibles.
- La red de alcantarillado: atarjeas, colectores, interceptores, emisores y cárcamos.
- Los dos trazos mencionados en el QGIS para Huejotzingo y San Martín Texmelucan; siguen
  apareciendo como nodos sin geometría fuente recuperable.
- Estado operativo, capacidad efectiva y área de servicio de cada PTAR.
- Atributos de descarga industrial, caudal, contaminantes, vigencia y cuerpo receptor.
- Validación de campo y documental de conexiones. La cercanía espacial no prueba conexión.

## Archivos de auditoría

- `inventario_archivos.csv`: catálogo físico de la entrega.
- `inventario_capas_espaciales.csv`: geometría, CRS, conteo y campos por capa.
- `inventario_red_hidrografica_rh18.csv`: detalle por hoja y familia RH18.
- `resumen_red_hidrografica_rh18.csv`: totales por familia.
- `resumen_tipos_inegi_cuenca.csv`: composición del recorte INEGI.
- `resumen_organizacion.json`: cifras principales y advertencias metodológicas.
