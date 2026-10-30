# Proyecto analítico vigente

Este directorio contiene el trabajo científico y geoespacial del Alto Atoyac. Para una lectura de los resultados empieza por [la entrega](../entrega/LEEME.md); para reconstruirlos, consulta [la guía técnica](../docs/REPRODUCIR.md).

## Entradas por etapa

| Etapa | Código | Resultados | Documentación |
|---|---|---|---|
| Universo económico | `scripts/00_...` a `101_...` | Cinco modalidades `outputs/cuenca_alto_atoyac_puebla*` | [Inventario histórico](docs/INVENTARIO_GENERAL_PROYECTO.md) |
| Parte 2 | Serie `200` | `outputs/parte_2/` | [Clustering y cierre](docs/parte_2/README.md) |
| Parte 3 | Serie `300` | `outputs/parte_3/` | [Integración y foco local](docs/parte_3/README.md) |

La parte 3 integra la evidencia de tratamiento con los análisis previos. El foco actual son las localidades de Santa Ana Xalmimilulco y Huejotzingo, no ambos municipios completos. La parte 4 de diseño conjunto todavía está pendiente.

## Productos vigentes de parte 3

- [Reporte de territorio, grafo y pendiente](outputs/parte_3/12_vialidades_amplias/reporte_red_amplia_territorio.md).
- [Explorador interactivo](outputs/parte_3/12_vialidades_amplias/explorador_territorio_grafos.html).
- [Explicación ilustrada de caminos mínimos](docs/parte_3/explicacion_caminos_minimos/explicacion_caminos_minimos.pdf).
- GeoPackage: `outputs/parte_3/12_vialidades_amplias/grafo_corredores_exploratorios.gpkg`.

Las etapas 08–11 son revisiones anteriores y dependencias de puntos o auditorías. No deben confundirse con la red vial vigente del paquete 12. El [mapa del repositorio](../docs/MAPA_REPOSITORIO.md) explica su función.

## Ejecución

Todos los scripts encuentran las rutas desde su ubicación. Ejecutar desde `atoyac` ayuda a mantener una convención única:

```powershell
python scripts/219_ejecutar_parte2_completa.py
```

La reconstrucción actual de vialidades, terreno y explicación usa, después de preparar los puntos del paquete 09:

```powershell
python scripts/310_actualizar_vialidades_amplias.py
python scripts/311_territorio_pendientes_locales.py
python scripts/312_documentar_red_amplia.py
python scripts/313_explicar_caminos_minimos_pdf.py
```

La guía enlazada documenta los pasos previos y la diferencia entre validar productos existentes y reconstruir desde fuentes. Los reportes y datos históricos se conservan como evidencia, con su fecha y alcance originales.
