# Organización del repositorio

La limpieza del 23 de octubre de 2026 separó lectura, ejecución y antecedentes.

- Se renovaron las entradas, guías, índice de scripts y estado de parte 3.
- Se creó una entrega seleccionada, con procedencia y hashes, sin mover los insumos científicos.
- Se trasladaron 441 archivos temporales (unos 22 MB) a `archivo_local/temporales_2026-10-23`, ignorado por Git. No se eliminaron fuentes, PDF, imágenes o resultados científicos.
- El respaldo ZIP adicional está en el directorio padre del repositorio: `respaldo_limpieza_repo_2026-10-23_completo.zip`.
- [Manifiesto de limpieza](limpieza_2026-10-23.json): rutas originales, hashes y condición de seguimiento Git. El ZIP contiene además las versiones anteriores de los documentos de entrada modificados.

Se conservaron los nombres y rutas del análisis porque son referenciados por importaciones, reportes y manifiestos. Los antecedentes tienen un índice y estado explícitos; no se presentan como resultados actuales.

Para recuperar un temporal, copiarlo desde archivo_local o extraer su entrada `temporales/<ruta original>` del respaldo a la ruta original. Para recuperar la documentación previa, extraer `documentacion_anterior/<ruta>`.
