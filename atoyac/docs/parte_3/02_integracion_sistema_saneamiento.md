# Integración del sistema de saneamiento

La Parte 3 integra el universo textil y la solución espacial congelada de Parte 2 con los registros disponibles de PTAR, descargas, hidrografía y límites territoriales. El producto central es `outputs/parte_3/parte_3_sistema_saneamiento_integrado.gpkg`, generado por `scripts/302_integrar_sistema_saneamiento_parte3.py` en EPSG:32614.

Se reutilizaron directamente los 4,365 establecimientos y 22 clusters de `solucion_principal.gpkg`, así como la subdivisión diagnóstica del cluster 20. No se reconstruyó el universo DENUE. Los establecimientos conservan sus señales productivas, evidencia hídrica, persistencia, cluster y resultado de auditoría; se añadieron identificadores internos y una lectura preliminar de prioridad ambiental.

Las PTAR se homologaron sin borrar diferencias entre fuentes. Se conservaron 65 registros del CNGMD de INEGI y cuatro registros de la compilación manual. El registro de Global Denim se trasladó a descargas porque su tipo declarado es “Descarga industrial”. `ptar_fuentes` preserva la procedencia y `conciliacion_ptar.csv` documenta candidatos mediante nombre, municipio y distancia. Ninguna coincidencia se fusionó automáticamente.

Las 301 descargas INEGI permanecen como `no_especificado`, porque la fuente disponible no permite asignar con seguridad carácter municipal o industrial. Se añadió por separado la descarga industrial compilada. La red RH18 se usa como hidrografía superficial y nunca como red sanitaria.

No se recibió una geometría recuperable de colectores. Los nombres `Camino_contenedores_SMT` y `Camino_contenedores_huejotzingo` aparecen como nodos huérfanos del proyecto QGIS. Por ello, la capa `colectores` existe con su modelo de campos, pero permanece vacía. Tampoco se creó una capa artificial de cuerpos receptores a partir de toda la red hidrográfica.

Los niveles de evidencia son: A para registro o documento oficial explícito; B para consistencia entre fuentes o productos consolidados; C para evidencia parcial o proximidad espacial; y D para información desconocida o insuficiente. Las tablas establecimiento–descarga y establecimiento–PTAR son relaciones de proximidad euclidiana con nivel C. No representan conexión, cobertura ni destino del agua.

El control de calidad conserva 355 establecimientos fuera del límite estricto como contexto de borde heredado de Parte 2. También revisa geometrías, CRS, fechas, candidatos duplicados y diferencias entre capacidad y caudal. No se calcula eficiencia de tratamiento; cualquier cociente futuro deberá denominarse `utilizacion_capacidad_reportada`.

La integración habilita análisis posteriores de conectividad, presión potencial, cobertura de tratamiento, capacidad disponible, posición aguas arriba/abajo y selección de sitios de monitoreo. Para realizarlos todavía se requieren relieve, red sanitaria, geometrías verificadas de colectores, áreas de servicio y estado operativo de las PTAR, además de validación documental y de campo.

La documentación ampliada, el diccionario, la trazabilidad, las relaciones y los mapas se encuentran en `outputs/parte_3/`.
