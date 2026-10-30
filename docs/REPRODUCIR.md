# Cómo revisar y reproducir

## Leer sin instalar

Abrir [entrega/LEEME.md](../entrega/LEEME.md). Los PDF y el explorador HTML son autónomos. Para capas espaciales puede usarse QGIS. Los datos de la entrega son una selección de resultados, no los insumos completos de reconstrucción.

## Entorno Python

El entorno usado fue Python 3.13 con las versiones directas registradas en [requirements.txt](../requirements.txt). Las dependencias directas están fijadas; no se afirma un bloqueo completo de dependencias transitivas ni portabilidad ya probada en otro sistema.

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe herramientas/verificar_repo.py
```

Para regenerar LaTeX se necesita además una distribución con `latexmk` y los paquetes solicitados por cada `.tex`. QGIS sólo es necesario para visualizar o ejecutar los scripts históricos que importan su API; no es dependencia del grafo actual. HDBSCAN se importa de **scikit-learn**, no del paquete externo `hdbscan`.

## Elegir qué ejecutar

| Objetivo | Comando desde la raíz |
|---|---|
| Revisar estructura, enlaces y entrega | `python herramientas/verificar_repo.py` |
| Inventariar fuentes locales | `python herramientas/inventariar_fuentes.py` |
| Preparar carpeta y ZIP para compartir | `python herramientas/preparar_entrega.py` |
| Revisar si están los insumos base | `python herramientas/verificar_repo.py --datos` |

La verificación no reconstruye análisis ni modifica resultados.

## Reconstrucción analítica

Los pasos siguientes se ejecutan desde `atoyac`. **Regeneran sus productos**; para revisar un resultado existente no hace falta ejecutarlos.

### Universo regional

Requiere DENUE, catálogos, MH y capas territoriales con las rutas declaradas en `scripts/101_main_cuenca_puebla.py`.

```powershell
python scripts/101_main_cuenca_puebla.py
python scripts/101_main_cuenca_puebla.py --sin-mh
python scripts/101_main_cuenca_puebla.py --estricto
python scripts/101_main_cuenca_puebla.py --estricto --sin-mh
python scripts/101_main_cuenca_puebla.py --todos-scian
```

### Parte 2

Parte de las tablas regionales anteriores. El ejecutor 219 va desde matriz y escenarios hasta documentos y validación, no desde la descarga original de DENUE.

```powershell
python scripts/219_ejecutar_parte2_completa.py
python scripts/220_segunda_pasada_analitica.py
python scripts/221_figuras_interactivo_segunda_pasada.py
python scripts/222_documentar_segunda_pasada.py
python scripts/223_figuras_diagnostico_kde_hex.py
python scripts/217_compilar_documentos_parte2.py
```

`219` ejecuta el cierre principal; `220–223` son productos adicionales. La segunda compilación sólo es necesaria si se regeneraron sus contenidos.

### Parte 3: base y foco

Requiere los resultados de parte 2 y la entrega `data/processed/lesly/Archivos_PTAR`.

```powershell
python scripts/301_organizar_archivos_ptar.py
python scripts/302_integrar_sistema_saneamiento_parte3.py
python scripts/305_integrar_vialidades_terreno.py
python scripts/306_separar_foco_santa_ana_huejotzingo.py
```

`300` audita el QGIS recibido y `303` produce el análisis regional inicial, pero no son necesarios para obtener el foco 09. `304`, `307–309` conservan diagnósticos/revisiones previas y no son la secuencia vigente de red.

### Parte 3: revisión vigente

```powershell
python scripts/310_actualizar_vialidades_amplias.py
python scripts/311_territorio_pendientes_locales.py
python scripts/312_documentar_red_amplia.py
python scripts/313_explicar_caminos_minimos_pdf.py
```

La salida vigente es `outputs/parte_3/12_vialidades_amplias`. El PDF ilustrado se escribe en `docs/parte_3/explicacion_caminos_minimos`. Después, desde la raíz, ejecutar `python herramientas/preparar_entrega.py` para actualizar la selección compartible.

## Insumos y límites de reproducibilidad

Los archivos nuevos de raw/processed no se incorporan automáticamente a Git por tamaño y procedencia. Un clon puede no contenerlos. [FUENTES.md](FUENTES.md) y el manifiesto de datos describen lo disponible; los enlaces a organismos no sustituyen los archivos exactos ni sus hashes. No existe una descarga automática completa de todas las entregas de colaboración.

La validación sobre este equipo confirma la integridad de productos existentes y la ejecución de las etapas locales ya realizadas. La limpieza documental no equivale a haber reconstruido los 57 escenarios o recompilado todos los reportes en un entorno nuevo.
