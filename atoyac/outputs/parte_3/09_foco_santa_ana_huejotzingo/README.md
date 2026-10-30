# Foco actual: Santa Ana Xalmimilulco y Huejotzingo

Abrir foco_santa_ana_huejotzingo.gpkg. Ejecutar desde atoyac: `python scripts/306_separar_foco_santa_ana_huejotzingo.py`, después del 305.

## Alcance

408 establecimientos sectoriales: 337 de Santa Ana y 71 de la localidad de Huejotzingo, seleccionados por localidad DENUE exacta, no por municipio completo. Vialidades recortadas por selección de intersección con envolventes de establecimientos + 2 km; los segmentos se conservan completos. Estas zonas no son límites oficiales ni áreas tributarias.

## Plantas

Núcleo local: Cabecera Municipal, Paseo de los Sauces y Real Segovia, todas registradas en el municipio de Huejotzingo. No hay PTAR registrada dentro de la zona operativa de Santa Ana en el inventario utilizado (verificar por separado si se cambia su delimitación). No se adjudica exclusividad de servicio a ninguna localidad.

Contexto externo: Chiautzingo, Tres Besanas, San Lucas Atoyatenco y los dos registros de Domingo Arenas. Se conserva para comparación posterior, separado del núcleo. La selección original fue por 10 km desde el centroide de cada localidad; no acredita aptitud, conexión ni inventario exhaustivo de plantas existentes.

Se reúnen provisionalmente los pares 005/066 y 015/069 como instalaciones de trabajo; se conserva el registro manual como representante por sus datos complementarios. La capa ptar_registros_originales y ptar_registros_zonas.csv conservan los 10 registros y procedencias originales. Resultan 8 instalaciones de trabajo: 3 locales y 5 externas. Domingo Arenas sigue separado.

## Estado para iniciar

Establecimientos identificados: sí, dentro del universo sectorial analizado; actividad y procesos reales pendientes de campo.
Vialidad local: buena correspondencia con establecimientos, sin certificación de exhaustividad ni topología. Esta capa local no garantiza corredores continuos hasta PTAR; consultar la red regional del paquete 08 y ampliar donde falte.
Elevación: dos MDT de 1.5 m, 331/337 establecimientos de Santa Ana y 71/71 de Huejotzingo cubiertos. Cabecera Municipal y Paseo de los Sauces con MDT; Real Segovia sin MDT. Faltan hojas para completar Santa Ana occidental y corredores externos. MDS se conserva sólo como contexto. Los BIL originales se cargan aparte usando referencias_rasters.csv; no están embebidos en el GeoPackage.
Plantas: inventario registral integrado, no operación/capacidad de recepción confirmadas. Datos de capacidad disponibles para Paseo de los Sauces y Real Segovia, ausentes para Cabecera Municipal.

Se puede iniciar integración y diagnóstico espacial de Parte 3. Para comparar trazos por gravedad faltan completar MDT, revisar continuidad vial y cotas; para diseñar, confirmar operación de plantas, caudales, conexiones y topografía de campo.
