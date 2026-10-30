# Herramientas de organización y entrega

Ejecutar desde la raíz del repositorio:

| Comando | Función |
|---|---|
| `python herramientas/verificar_repo.py` | Revisar enlaces, sintaxis e integridad de la entrega sin modificar análisis. |
| `python herramientas/verificar_repo.py --datos` | Añadir comprobación de rutas base de insumos. |
| `python herramientas/preparar_entrega.py` | Regenerar entrega seleccionada y ZIP en dist. |
| `python herramientas/inventariar_fuentes.py` | Actualizar listado y hashes de fuentes locales. |
| `python herramientas/documentar_repo.py` | Regenerar las entradas documentales de este corte; sobrescribe esas guías. |

Las herramientas de presentación no recalculan clustering ni caminos. Las secuencias científicas permanecen en `atoyac/scripts`; consultar [REPRODUCIR.md](../docs/REPRODUCIR.md).
