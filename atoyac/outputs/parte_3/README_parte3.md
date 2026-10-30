# Parte 3 — Sistema de saneamiento integrado

Esta etapa integra los resultados territoriales de Parte 2 con PTAR, descargas e hidrografía. No afirma conexiones hidráulicas ni suficiencia de tratamiento.

## Ejecución

1. `python scripts/301_organizar_archivos_ptar.py`
2. `python scripts/302_integrar_sistema_saneamiento_parte3.py`

El producto central es `parte_3_sistema_saneamiento_integrado.gpkg`. Todas las capas métricas usan EPSG:32614.

## Estructura

- `00_auditoria/`: fuentes, capas, campos y advertencias.
- `01_insumos_homologados/`: espacio reservado para productos intermedios homologados.
- `02_integracion/`: espacio para tablas intermedias de integración.
- `03_relaciones_espaciales/`: proximidades derivadas, nunca conexiones asumidas.
- `04_control_calidad/`: QA en JSON y Markdown.
- `05_mapas/`: seis mapas diagnósticos.
- `docs/`: documento técnico de la integración.

Las capas vacías `colectores` y `cuerpos_receptores` son deliberadas: preservan el modelo de datos sin fabricar geometrías inexistentes.
