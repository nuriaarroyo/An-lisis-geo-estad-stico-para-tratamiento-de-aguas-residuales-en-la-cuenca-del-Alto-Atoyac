# Mapa del repositorio

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
