"""Regenera las entradas de documentación del corte de entrega actual."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
FILES={
'README.md':'''# Actividad textil y saneamiento en la cuenca del Alto Atoyac

**Análisis territorial reproducible para identificar concentraciones de establecimientos y explorar su relación con la infraestructura de tratamiento.**

Autora: **Nuria Arroyo Bustamante** · Universidad de las Américas Puebla.  
Estado documentado: **23 de octubre de 2026**.

## Empieza aquí

- **Para conocer y compartir el trabajo:** [entrega de lectura](entrega/LEEME.md), con reportes, mapas, datos seleccionados y explorador interactivo.
- **Para entender el avance:** [estado actual y límites](docs/ESTADO_ACTUAL.md).
- **Para revisar o reproducir:** [guía técnica](docs/REPRODUCIR.md), [fuentes](docs/FUENTES.md) y [mapa del repositorio](docs/MAPA_REPOSITORIO.md).

## Qué se ha construido

| Etapa | Resultado | Estado |
|---|---|---|
| 1. Universo económico | Filtros SCIAN/texto, contraste con evidencia MH y cinco modalidades regionales. | Base documentada. |
| 2. Concentraciones | 4,365 establecimientos de detección; 4,010 dentro de cuenca; comparación de 57 escenarios. | Cierre analítico validado. |
| 3. Infraestructura y territorio | PTAR, descargas, hidrografía, vialidades, terreno y exploración local de caminos. | En desarrollo; revisión vigente `12_vialidades_amplias`. |
| 4. Propuesta de colectores | Red común, caudales, capacidad receptora, cotas y costos. | Pendiente; aún no es diseño hidráulico. |

La parte 2 seleccionó HDBSCAN y detectó 22 clusters en el universo con borde; 18 intersectan la cuenca. La parte 3 trabaja ahora con **Santa Ana Xalmimilulco y la localidad de Huejotzingo**: 408 establecimientos, de los que 65 tienen prioridad alta/media.

## Hallazgos locales actuales

- **Huejotzingo:** 102 caminos individuales desde 34 prioritarios hacia tres PTAR candidatas. Cabecera Municipal y Paseo de los Sauces tienen cobertura de terreno completa en las trazas; Real Segovia, parcial.
- **Santa Ana:** 31 prioritarios sin ruta continua a esas tres plantas en los archivos viales disponibles. Se exploran 62 recorridos internos hacia dos extremos de calle para inspección.
- Los caminos se calculan con **Dijkstra por longitud vial**. La pendiente se evalúa después. Cada camino une un establecimiento con un destino; aún no se optimiza una red conjunta que reúna todos los aportantes.

**Interpretación:** concentración no demuestra contaminación; proximidad no demuestra conexión sanitaria; registro de PTAR no acredita operación ni capacidad libre. Los resultados orientan investigación y prefactibilidad.

## Vista del trabajo

| Concentraciones regionales | Integración local de terreno y establecimientos |
|---|---|
| ![Clusters regionales](entrega/figuras/00_clusters_regionales.png) | ![Terreno de Huejotzingo](entrega/figuras/05_huejotzingo_elevacion.png) |

## Organización

```text
entrega/          Reportes, mapas y datos seleccionados para compartir
atoyac/          Proyecto analítico vigente: scripts, datos, documentos y resultados
docs/            Guías de lectura, reproducción, fuentes y organización
herramientas/    Verificación y preparación de la entrega
version_01/      Antecedente local y auditorías; se conserva para trazabilidad
mantenimiento/  Registro de limpieza y organización
```

La selección de productos vigentes está en [proyecto.json](proyecto.json). Las revisiones históricas conservan sus rutas porque los scripts y manifiestos las utilizan.

## Revisión rápida

```powershell
python -m pip install -r requirements.txt
python herramientas/verificar_repo.py
python herramientas/preparar_entrega.py
```

La entrega puede leerse sin instalar Python. Reconstruir los análisis requiere los insumos geográficos descritos en la [guía de reproducción](docs/REPRODUCIR.md). Los archivos nuevos en `data/raw` y `data/processed` son locales; su inventario se conserva en [el manifiesto de datos](atoyac/data/MANIFIESTO_FUENTES.csv).
''',
'atoyac/README.md':'''# Proyecto analítico vigente

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
''',
'docs/ESTADO_ACTUAL.md':'''# Estado actual del trabajo

Corte de lectura: 23 de octubre de 2026. Autora: Nuria Arroyo Bustamante.

## Pregunta y alcance

¿Dónde se concentran actividades textiles potencialmente relevantes y cómo se relacionan espacialmente con la infraestructura de saneamiento disponible? El trabajo avanza desde la construcción del universo económico hasta la exploración de corredores. No atribuye contaminación ni comprueba conexiones hidráulicas por proximidad.

## Parte 1: construir un universo auditable

Se combinan DENUE, filtros SCIAN y texto, evidencia de campo MH y fuentes territoriales. Se comparan cinco modalidades: amplia/estricta, con/sin MH y sectorial ampliada. La modalidad sectorial conserva posibles actividades que un filtro restrictivo podría excluir antes de validar sus procesos.

## Parte 2: identificar concentraciones

- Universo de detección con contexto de borde: 4,365 establecimientos.
- Interior de cuenca para interpretación: 4,010.
- Escenarios espaciales evaluados: 57.
- Referencia: HDBSCAN de scikit-learn, min_cluster_size=10, min_samples=20, EOM.
- 22 clusters en detección; 18 intersectan cuenca; 584 puntos como ruido.

Los perfiles productivos se incorporan después de fijar la solución espacial. La partición se conserva para que la integración posterior no cambie silenciosamente el universo.

## Parte 3: integrar infraestructura y explorar el territorio

Base regional: 69 registros PTAR (65 INEGI + 4 compilados), 302 descargas e hidrografía. Dos pares PTAR coinciden en nombre y coordenadas; los registros originales se conservan. No son 69 instalaciones físicas independientes confirmadas.

Foco actual: 337 establecimientos sectoriales de Santa Ana y 71 de Huejotzingo. Se exploran los 65 de prioridad alta/media: 31 y 34, respectivamente. Destinos del núcleo: Cabecera Municipal, Paseo de los Sauces y Real Segovia. Las plantas de contexto externo todavía no se analizan como destinos de esta comparación.

| Resultado | Interpretación |
|---|---|
| 102 rutas Huejotzingo–PTAR | Un camino por establecimiento y planta: 34 × 3. |
| 93 pares Santa Ana–PTAR sin ruta | La red disponible está desconectada; no prueba ausencia física de caminos o drenaje. |
| 62 recorridos internos de Santa Ana | 31 × 2 extremos existentes para inspección, no plantas. |
| Terreno completo hacia Cabecera y Paseo | Permite revisar perfiles superficiales; no acredita gravedad. |
| Terreno parcial hacia Real Segovia y Santa Ana occidental | Faltan hojas para comparar corredores completos. |

Dijkstra minimiza distancia vial. La pendiente se estudia sobre los caminos posteriormente y no decide todavía la ruta. La suma de caminos individuales repite tramos; su unión tampoco garantiza una red conjunta de menor costo.

## Parte 4: pendiente

La siguiente etapa requiere una red común hacia un destino, aportaciones de caudal/carga, cotas de tubería y entrada de planta, capacidad receptora verificada, cruces, derechos de vía y costos. No existe todavía una recomendación de obra o diseño definitivo.

## Qué puede revisar otra persona

La [entrega](../entrega/LEEME.md) reúne el resumen regional, la explicación ilustrada de caminos, mapas, tablas y capas seleccionadas. El [reporte técnico local](../atoyac/outputs/parte_3/12_vialidades_amplias/reporte_red_amplia_territorio.md) desarrolla el método y sus límites. Los scripts y manifiestos permiten seguir la procedencia de cada producto.
''',
'docs/MAPA_REPOSITORIO.md':'''# Mapa del repositorio

## Lectura y presentación

`entrega/` es la selección para compartir. Se regenera con `python herramientas/preparar_entrega.py`; sus copias conservan procedencia y hashes. Los archivos de trabajo permanecen en sus rutas originales.

`docs/` reúne guías actuales. `atoyac/docs/` conserva reportes, metodología, decisiones y fuentes de LaTeX. Las carpetas `dir1`, `presentaciones parciales` y `reportes` son entregas anteriores; no representan la versión local actual.

## Resultados de parte 3

| Carpeta | Función | Uso actual |
|---|---|---|
| `00_auditoria*` | Inspección de fuentes y proyecto QGIS | Trazabilidad. |
| `01_insumos_organizados` | Normalización de PTAR, descargas e hidrografía | Insumo de integración. |
| `03_relaciones_espaciales` / `04_control_calidad` | Proximidad y controles regionales | Evidencia de integración. |
| `05_mapas` / `06_analisis` | Primer análisis regional de infraestructura | Antecedente de alcance regional. |
| `07_factibilidad_red` | Diagnóstico previo a vialidades y MDT | Histórico; las afirmaciones de ausencia corresponden a esa entrega. |
| `08_integracion_vialidades_terreno` | Primera cobertura local y hashes de fuentes | Dependencia de auditoría histórica. |
| `09_foco_santa_ana_huejotzingo` | Selección de puntos y plantas núcleo/contexto | Insumo vigente de puntos. |
| `10_grafos_corredores` | Primer grafo exploratorio | Histórico. |
| `11_actualizacion_connect` | Revisión de la entrega connect | Histórico. |
| **`12_vialidades_amplias`** | Todas las vialidades, recorridos y relieve | **Revisión vigente de red y mapas.** |

El GeoPackage regional `parte_3_sistema_saneamiento_integrado.gpkg` conserva infraestructura y establecimientos de parte 2. El paquete 12 toma el foco de puntos del 09 y la vialidad actual directamente desde raw. No se deben borrar 08–11 sólo porque no sean la vista de lectura vigente: también documentan cambios y dependencias.

## Código y datos

- `atoyac/scripts/`: código del análisis actual, numerado por etapas; [índice de scripts](../atoyac/scripts/README.md).
- `atoyac/data/raw/`: entregas originales de DENUE, territorio, vialidades y terreno.
- `atoyac/data/processed/`: catálogos, evidencia MH y compilación Lesly.
- `atoyac/data/MANIFIESTO_FUENTES.csv`: archivos, tamaño y hash para identificar las fuentes locales.
- `version_01/`: antecedente local y reglas/auditorías iniciales; [entrada histórica](../version_01/README.md).

## Mantenimiento

`mantenimiento/` documenta la organización. Los temporales se trasladaron a `archivo_local/` (ignorado por Git) y tienen respaldo ZIP fuera del repositorio. Se conservaron PDF, fuentes, imágenes y resultados científicos. Los nombres originales de scripts y rutas científicas se mantienen para no romper referencias y manifiestos.
''',
'docs/REPRODUCIR.md':r'''# Cómo revisar y reproducir

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
''',
'docs/FUENTES.md':'''# Fuentes y trazabilidad

Las fuentes se conservan separadas de los resultados. La identificación de archivos locales está en [MANIFIESTO_FUENTES.csv](../atoyac/data/MANIFIESTO_FUENTES.csv); los manifiestos de cada análisis registran transformaciones y versiones.

| Fuente | Contenido y función | Precaución de interpretación |
|---|---|---|
| DENUE / INEGI | Nombre, SCIAN, ubicación y atributos declarados de establecimientos. | Registro económico, no verificación de actividad húmeda o descarga. |
| MH: Mary Helen Figueroa y Mayra Jaqueline Ramírez | Evidencia de campo y contrastes locales. | Se conserva como fuente independiente; no se extrapola automáticamente. |
| CAARESA y capas territoriales recibidas | Cuenca, municipios y contexto regional. | Usar el polígono adoptado y conservar su referencia. |
| INEGI CNGMD 2021, descarga 2023 | Registros de tratamiento y descargas. | Año del registro distinto al de descarga; no acredita operación actual. |
| Compilación `PTAR_Final.csv` | Cuatro PTAR y una descarga industrial; datos de 2021–2022 cuando se informan. | No sustituye al inventario INEGI; existen dos pares coincidentes entre fuentes. |
| INEGI RH18 | Red hidrográfica y contexto de cauces. | Una intersección geométrica no confirma descarga o cruce constructivo. |
| Entregas de vialidades | Calles de localidades, connect, c2, c3 y descarga amplia. | La cobertura amplia no garantiza continuidad ni permiso de uso. |
| MDT / MDS de INEGI, hojas E14B42C2 y E14B42C3 | Terreno y superficie de 1.5 m. Sólo MDT se usa para elevaciones. | Resolución no equivale a precisión vertical. Se conservan vacíos. |

## Cadena del análisis actual

Fuentes → universo regional → solución de parte 2 → integración regional de parte 3 → foco 09 → todas las vialidades del paquete 12 → Dijkstra y perfiles → entrega seleccionada.

Los vectores de trabajo usan EPSG:32614. Las consultas de elevación se transforman al CRS nativo del raster. Los GeoTIFF de pendiente de la entrega son productos de visualización a 15 m; no cambian el MDT fuente de 1.5 m.

El paquete para compartir contiene sus propios hashes y procedencia. Las condiciones de uso y atribución de las fuentes originales siguen aplicando. No se añadió una licencia global que pretenda relicenciar datos de terceros o el trabajo de la autora.
''',
'atoyac/scripts/README.md':'''# Índice de scripts

Los números conservan la secuencia de investigación. No deben renombrarse sin actualizar las importaciones dinámicas y las rutas documentadas.

| Serie / entrada | Función | Estado |
|---|---|---|
| `00–10`, `99`, `100` | Exploraciones y flujo local inicial | Antecedentes; `99` requiere API QGIS. |
| `101_main_cuenca_puebla.py` | Cinco modalidades regionales | Base del universo económico. |
| `102_presentacion_direccion.py` | Síntesis para dirección | Entrega intermedia. |
| `200_parte2_comun.py` | Configuración y utilidades | Dependencia compartida. |
| `201–211`, `213–218` | Análisis espacial y cierre | Parte 2. |
| **`219_ejecutar_parte2_completa.py`** | Ejecutor principal | Entrada vigente de parte 2. |
| `212_ejecutar_parte2.py` | Primer ejecutor de parte 2 | Histórico. |
| `220–223` | Segunda pasada y figuras | Complementos del cierre. |
| `300` | Auditoría de QGIS recibido | Trazabilidad. |
| `301–302` | Insumos e integración de infraestructura | Base de parte 3. |
| `303–304` | Análisis y diagnóstico inicial | Revisión anterior a nuevas vialidades/MDT. |
| `305–306` | Cobertura inicial y foco de puntos/plantas | Insumos del análisis local. |
| `307–309` | Primeros grafos y revisión connect | Revisiones históricas. |
| **`310–312`** | Todas las vialidades, terreno, recorridos y reporte | **Secuencia vigente de red local.** |
| **`313`** | PDF ilustrado de caminos mínimos | Explicación para lectores. |

Comandos y dependencias: [guía de reproducción](../../docs/REPRODUCIR.md). Verificación y preparación de la entrega: `herramientas/` en la raíz del repositorio.
''',
'atoyac/docs/parte_3/README.md':'''# Parte 3: infraestructura, territorio y exploración local

La parte 3 integra la información de tratamiento disponible con los análisis económicos y espaciales previos. El foco actual son Santa Ana Xalmimilulco y la localidad de Huejotzingo.

## Lectura recomendada

1. [Estado del proyecto](../../../docs/ESTADO_ACTUAL.md).
2. [Reporte vigente de red amplia, territorio y pendiente](04_red_amplia_territorio_pendientes.md).
3. [PDF ilustrado: qué representan los caminos mínimos](explicacion_caminos_minimos/explicacion_caminos_minimos.pdf).
4. [Entrega para compartir](../../../entrega/LEEME.md).

## Productos vigentes

- Puntos y selección de plantas: `outputs/parte_3/09_foco_santa_ana_huejotzingo`.
- Vialidades, grafos, recorridos y mapas de terreno: `outputs/parte_3/12_vialidades_amplias`.
- Explicación visual: `docs/parte_3/explicacion_caminos_minimos`.

Hay 102 rutas individuales de Huejotzingo hacia tres plantas, 93 pares Santa Ana–planta sin ruta y 62 recorridos internos de Santa Ana hacia extremos de inspección. No se ha optimizado una red conjunta de colectores ni acreditado funcionamiento por gravedad.

## Antecedentes conservados

El inventario de Archivos_PTAR, el reporte técnico regional de integración y los documentos 02/03 conservan su contexto histórico. Las afirmaciones de falta de vialidad/MDT del diagnóstico inicial corresponden a la entrega disponible entonces. Los paquetes 10 y 11 fueron sustituidos para lectura actual por 12, pero mantienen su procedencia.

La reproducción se documenta en [la guía técnica](../../../docs/REPRODUCIR.md). La numeración de scripts evolucionó durante el proyecto: el [índice real de scripts](../../scripts/README.md) describe su función actual.
''',
'atoyac/outputs/parte_3/README.md':'''# Resultados de parte 3

**Revisión vigente para vialidades, grafos y relieve: [12_vialidades_amplias](12_vialidades_amplias/README.md).**

- Base regional: `parte_3_sistema_saneamiento_integrado.gpkg` y sus auditorías.
- Foco de puntos y plantas: `09_foco_santa_ana_huejotzingo`.
- Vista de lectura: [entrega seleccionada](../../../entrega/LEEME.md).
- Resultados anteriores: etapas 07–11, conservadas para trazabilidad y dependencias.

El [mapa del repositorio](../../../docs/MAPA_REPOSITORIO.md) explica cada carpeta. Los caminos individuales no representan una red común optimizada, y la proximidad no acredita conexión sanitaria.
''',
'version_01/README.md':'''# Antecedente local: versión 01

Esta carpeta conserva el desarrollo inicial de Santa Ana Xalmimilulco: clasificación independiente por SCIAN/texto, auditorías manuales y contrastes con MH y otros universos.

El proyecto vigente está en [atoyac](../atoyac/README.md). Para conocer el trabajo completo empieza por [la entrada principal](../README.md).

## Qué se conserva

- [Reglas del filtro textil](filtros_textiles_santa_ana/README.md).
- [Descripción de datos](data/README.md).
- [Scripts legacy](scripts/legacy/README.md).
- [Resultados legacy](outputs/legacy/README.md).

Los universos y decisiones locales de esta etapa no se extrapolan automáticamente a toda la cuenca. Sus resultados son antecedentes de la evolución metodológica, no la última integración de infraestructura o grafos.
''',
'mantenimiento/README.md':'''# Organización del repositorio

La limpieza del 23 de octubre de 2026 separó lectura, ejecución y antecedentes.

- Se renovaron las entradas, guías, índice de scripts y estado de parte 3.
- Se creó una entrega seleccionada, con procedencia y hashes, sin mover los insumos científicos.
- Se trasladaron 441 archivos temporales (unos 22 MB) a `archivo_local/temporales_2026-10-23`, ignorado por Git. No se eliminaron fuentes, PDF, imágenes o resultados científicos.
- El respaldo ZIP adicional está en el directorio padre del repositorio: `respaldo_limpieza_repo_2026-10-23_completo.zip`.
- [Manifiesto de limpieza](limpieza_2026-10-23.json): rutas originales, hashes y condición de seguimiento Git. El ZIP contiene además las versiones anteriores de los documentos de entrada modificados.

Se conservaron los nombres y rutas del análisis porque son referenciados por importaciones, reportes y manifiestos. Los antecedentes tienen un índice y estado explícitos; no se presentan como resultados actuales.

Para recuperar un temporal, copiarlo desde archivo_local o extraer su entrada `temporales/<ruta original>` del respaldo a la ruta original. Para recuperar la documentación previa, extraer `documentacion_anterior/<ruta>`.
'''
}

def main():
    for relative,content in FILES.items():
        path=ROOT/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
    registry={'corte':'2026-10-23','autora':'Nuria Arroyo Bustamante','parte2':'atoyac/outputs/parte_2','parte3':'atoyac/outputs/parte_3/12_vialidades_amplias','foco_puntos':'atoyac/outputs/parte_3/09_foco_santa_ana_huejotzingo/foco_santa_ana_huejotzingo.gpkg','pdf_caminos':'atoyac/docs/parte_3/explicacion_caminos_minimos/explicacion_caminos_minimos.pdf','entrega':'entrega','estado':'exploracion; sin diseno hidraulico conjunto'}
    (ROOT/'proyecto.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(FILES)} entradas documentales escritas.')

if __name__=='__main__':main()
