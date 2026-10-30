# Actualización con entrega connect

Huejotzingo: sus seis archivos son idénticos por SHA-256 a la auditoría anterior. Tampoco cambiaron Santa Ana ni San Martín.

Connect: 1,539 tramos válidos; 333 geometrías no presentes en el paquete previo (se eliminaron repeticiones exactas en la red conjunta). La red regional pasa de 18,707 a 19,035 geometrías únicas.

La nueva entrega toca las redes previas de ambas localidades, pero sus diferentes grupos de calles no forman un puente continuo. El grafo sigue sin ruta desde los 31 orígenes prioritarios de Santa Ana hacia las tres PTAR. La brecha mínima entre nodos se reduce de 1282.2 a 989.8 m; se comprobó también por distancia entre líneas (989.8 m).

Extremos aproximados de la brecha (longitud, latitud): [(-98.39304697928091, 19.18457070266458), (-98.39210326022855, 19.193470539990955)]. La línea roja sólo diagnostica la falta de continuidad; no se creó como arista ni representa una propuesta constructiva. Completar esa franja de vialidades y revisar los cruces antes de volver a calcular.

Abrir [detalle de la nueva entrega](05_detalle_connect_brecha.png), [explorador actualizado](explorador_grafos.html) y [reporte actualizado](reporte_grafos_corredores.md). Para QGIS: grafo_corredores_exploratorios.gpkg. La red regional con connect y la brecha están en vialidades_con_connect.gpkg.

Los resultados anteriores de 08–10 se conservan. Esta revisión es la vigente para vialidades y rutas; repetir desde atoyac con `python scripts/309_actualizar_connect.py`. El paquete 09 sigue aportando puntos y destinos, que no cambiaron; el paquete 11 usa las vialidades actuales directamente desde raw. La elevación no cambia.
