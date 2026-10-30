
# Advertencias de integración

1. No existe una capa fuente recuperable de colectores. `Camino_contenedores_SMT` y `Camino_contenedores_huejotzingo` son nodos huérfanos del QGIS.
2. `PTAR_Final.csv` mezcla cuatro PTAR con una descarga industrial; se separaron por tipo.
3. El CNGMD confirma registros administrativos, no operación actual ni conexión.
4. La red RH18 representa hidrografía superficial, no drenaje sanitario.
5. La franja de 10 m no se interpreta como delimitación legal de zona federal.
6. Las 355 unidades fuera de la cuenca se preservan como contexto de borde heredado de Parte 2.
7. Las capas `colectores` y `cuerpos_receptores` conservan el esquema vacío hasta recibir geometrías verificables.
