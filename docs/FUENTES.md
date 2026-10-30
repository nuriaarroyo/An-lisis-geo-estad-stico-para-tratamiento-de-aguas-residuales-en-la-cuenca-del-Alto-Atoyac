# Fuentes y trazabilidad

Las fuentes se conservan separadas de los resultados. La identificación de archivos locales está en [MANIFIESTO_FUENTES.csv](../atoyac/data/MANIFIESTO_FUENTES.csv); los manifiestos de cada análisis registran transformaciones y versiones.

| Fuente | Contenido y función | Precaución de interpretación |
|---|---|---|
| DENUE / INEGI | Nombre, SCIAN, ubicación y atributos declarados de establecimientos. | Registro económico, no verificación de actividad húmeda o descarga. |
| MH: Mary Helen Figueroa y Mayra Jaqueline Ramírez | Evidencia de campo y contrastes locales. | Se conserva como fuente independiente; no se extrapola automáticamente. |
| CAARESA y capas territoriales recibidas | Cuenca, municipios y contexto regional. | Usar el polígono adoptado y conservar su referencia. |
| INEGI CNGMD 2021, descarga 2023 | Registros de tratamiento y descargas. | Año del registro distinto al de descarga; no acredita operación actual. |
| Compilación `PTAR_Final.csv` | Cuatro PTAR y una descarga industrial; datos de 2021–2022 cuando se informan. | No sustituye al inventario INEGI; existen dos pares coincidentes entre fuentes. |
| INEGI RH18 | Red hidrográfica y contexto de cauces. | Una intersección geométrica no confirma descarga o cruce constructivo. |
| Entregas de vialidades | Calles de localidades, connect, c2, c3 y descarga amplia. | La cobertura amplia no garantiza continuidad ni permiso de uso. |
| MDT / MDS de INEGI, hojas E14B42C2 y E14B42C3 | Terreno y superficie de 1.5 m. Sólo MDT se usa para elevaciones. | Resolución no equivale a precisión vertical. Se conservan vacíos. |

## Cadena del análisis actual

Fuentes → universo regional → solución de parte 2 → integración regional de parte 3 → foco 09 → todas las vialidades del paquete 12 → Dijkstra y perfiles → entrega seleccionada.

Los vectores de trabajo usan EPSG:32614. Las consultas de elevación se transforman al CRS nativo del raster. Los GeoTIFF de pendiente de la entrega son productos de visualización a 15 m; no cambian el MDT fuente de 1.5 m.

El paquete para compartir contiene sus propios hashes y procedencia. Las condiciones de uso y atribución de las fuentes originales siguen aplicando. No se añadió una licencia global que pretenda relicenciar datos de terceros o el trabajo de la autora.
