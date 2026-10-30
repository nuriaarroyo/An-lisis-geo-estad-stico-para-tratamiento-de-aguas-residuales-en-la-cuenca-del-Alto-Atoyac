# Revisi?n de cobertura: Santa Ana y Huejotzingo

La entrega vial permite integrar los establecimientos del universo sectorial de ambas localidades. No se certifica el inventario completo de calles ni una red topol?gica: faltan l?mites oficiales de localidad y comprobaci?n de continuidad/cruces.

| Indicador | Santa Ana | Huejotzingo |
|---|---:|---:|
| Tramos en archivo recibido (incluye otras localidades) | 901 | 2804 |
| Establecimientos analizados | 337 | 71 |
| Establecimientos a menos de 100 m de vialidad del archivo local | 337 | 71 |
| Distancia m?xima a vialidad, m | 70.4 | 11.7 |
| Establecimientos con elevaci?n MDT | 331 | 71 |
| PTAR registradas a 10 km del centroide | 8 | 7 |
| PTAR con elevaci?n en MDT disponibles | 3 | 4 |
| Longitud vial de zona operativa cubierta por MDT | 78.56 % | 91.16 % |

Se cargaron dos MDT y dos MDS de 1.5 m: E14B42C2 y E14B42C3. Son hojas diagonales, por lo que la uni?n no cubre un rect?ngulo continuo entre ambas localidades. Faltan seis establecimientos del borde occidental de Santa Ana y partes de los alrededores/corredores a PTAR. No se rellenaron huecos ni se us? MDS para sustituir terreno.

La clave de Santa Ana es 210740029; la de Huejotzingo es 210740001. Los archivos contienen m?s localidades que las indicadas por su carpeta. Se conservan claves y procedencia. En la red de consulta se retiraron geometr?as exactamente repetidas; la cantidad por clave puede diferir del inventario original.

Resultados: localidades_vialidades_terreno.gpkg, mapas PNG, CSV por establecimiento y PTAR (elevaci?n y distancia a vialidad), inventario original, resumen de cobertura, hashes de fuentes y validaci?n de capas. Elevaciones calculadas transformando al CRS nativo de cada raster. La precisi?n vertical debe consultarse en los metadatos; resoluci?n de 1.5 m no equivale a exactitud vertical de 1.5 m.

Pendiente para comparar corredores: completar hojas MDT y cobertura vial exterior hacia los destinos seleccionados, comprobar topolog?a y conciliar registros PTAR. La proximidad geom?trica no acredita conexiones sanitarias.
