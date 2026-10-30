# Integración local de vialidades y terreno

Ejecutar desde atoyac: `python scripts/305_integrar_vialidades_terreno.py`.

Abrir `localidades_vialidades_terreno.gpkg` en QGIS. Los BIL originales se cargan por separado; la capa cobertura_rasters conserva sus rutas y tipo MDT/MDS. Todos los vectores se homologan a EPSG:32614; el muestreo transforma cada punto al CRS nativo del raster. No se reproyectan ni alteran los originales.

Las localidades se seleccionan por nombre exacto de DENUE y vialidades por CVEGEO 210740029 (Santa Ana) / 210740001 (Huejotzingo). No se cuenta con polígonos oficiales de localidad: no se acredita exhaustividad de calles mediante un límite oficial. La zona operativa es envolvente de establecimientos + 2 km, no área tributaria. Los puntos de PTAR se seleccionan a 10 km del centroide; son registros sin conciliación física.

La cobertura MDT usa la máscara de píxeles válidos, no sólo el rectángulo del archivo. Se informa cobertura en establecimientos, PTAR y longitud de vialidad dentro de la zona; no certifica corredores externos hasta PTAR. Las elevaciones se muestrean por píxel, sin interpolar huecos. Se utiliza exclusivamente MDT para z_mdt_m; MDS queda como referencia. Revisar precisión y referencia vertical en los metadatos antes de calcular pendientes hidráulicas.

Las distancias a vialidad se calculan contra los tres archivos regionales y conservan el ID de tramo. Umbrales 50/100 m son indicadores diagnósticos de proximidad, no prueba de acceso ni conexión. No se ajustan los puntos a calles. No se valida topología, cruces a distinto nivel, transitabilidad o continuidad de un grafo sanitario. Se eliminan únicamente geometrías viales exactamente repetidas en la red de consulta.

Los diagnósticos históricos 304 sobre ausencia de vialidad y topografía quedaron desactualizados: sus mensajes están fijados en código. Este producto registra la nueva entrega sin sobrescribir la integración previa.
