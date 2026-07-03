# Guia del filtro trazable de Santa Ana

## Objetivo

Este flujo conserva como canonico el universo original de 38 establecimientos
producido previamente para Santa Ana Xalmimilulco. Lo compara con la capa MH ya
filtrada de 49 puntos y con el universo relevante producido por el filtro
explicito nuevo.

El filtro explicito no sustituye al universo original. Responde a una pregunta
analitica mas amplia sobre senales de tratamiento, lavado, acabado, tintoreria,
mezclilla, jeans, deshebrado o produccion de material textil.

Ninguna salida constituye evidencia de descarga o contaminacion.

## Pipeline operativo unico

La ejecucion normal tiene una sola entrada:

```powershell
python scripts\run_santa_ana_pipeline.py
```

Cuando cambian los archivos de `data/raw/`, primero se prepara la información:

```powershell
python scripts\01_prepare_geodata.py
```

Este es el único importador. Detecta las capas geográficas y genera los
GeoPackage normalizados, incluido `data/processed/denue2026_raw.gpkg`.

Después, el pipeline analítico ejecuta cinco etapas:

1. **Clasificar SAIC:** obtiene las familias manufactureras textiles 313, 314 y 315.
2. **Clasificar DENUE:** busca esas familias, servicios 8122 y señales textuales en Santa Ana.
3. **Aplicar filtro explicito:** clasifica candidatos como relevantes, revisar o excluir.
4. **Comparar y validar:** cruza canónico, MH y foco alternativo.
5. **Documentar:** genera mapas, tablas, índice, manifiesto y PDF.

El estado de cada ejecucion queda en
`outputs/santa_ana_xalmimilulco/pipeline_manifest.json`.

## Que decide y que solo compara

- **Universo canonico:** tu universo original de Santa Ana, con 38 establecimientos.
- **MH filtrado:** la capa `capa MH.shp`, con 49 puntos: 43 con ID DENUE y 6 sin ID.
- **Alternativa analitica:** filtro ejecutado por
  `scripts/santa_ana_filter_rules.py` y definido por los catalogos de
  `config/filtros_textiles_santa_ana/`.
- **Antecedente diagnostico:** foco amplio conservado en `scripts/legacy/`. No forma parte del pipeline vigente.

Los scripts experimentales anteriores están en `scripts/legacy/` y no son
dependencias del pipeline vigente.

## Scripts vigentes

Los archivos activos para este análisis son:

- `scripts/01_prepare_geodata.py`: único importador desde `data/raw/`.
- `scripts/run_santa_ana_pipeline.py`: ejecuta todo el flujo analítico y define sus cinco etapas.
- `scripts/santa_ana_filter_rules.py`: carga catalogos y combina las senales
  mediante reglas booleanas visibles.
- `scripts/santa_ana_audit_utils.py`: concentra lectura, exportacion, mapas y LaTeX.

Los scripts anteriores se conservan en `scripts/legacy/` como historial y no
deben ejecutarse.

## Como leer el codigo

1. Abrir `scripts/run_santa_ana_pipeline.py` y comenzar por `main()` al final.
   Esa funcion muestra el orden completo sin detalles tecnicos.
2. Abrir `config/filtros_textiles_santa_ana/palabras_clave.csv`: contiene una
   palabra o frase por renglon.
3. Abrir `config/filtros_textiles_santa_ana/codigos_scian.csv`: contiene las
   senales por codigo o prefijo SCIAN.
4. Abrir `config/filtros_textiles_santa_ana/politica_categorias.csv`: muestra
   prioridad, relevancia y pertenencia a universos.
5. Leer `apply_filter_rules()` en `scripts/santa_ana_filter_rules.py`: muestra
   como se combinan las senales con AND, OR y exclusiones.
6. Consultar `scripts/santa_ana_audit_utils.py` solo cuando se necesite entender
   como se exporta un GeoPackage, mapa o documento.
7. Consultar `scripts/common.py` para normalizacion de texto, rutas y lectura
   geoespacial compartida.

No hay otro filtro vigente fuera de esos catalogos y
`santa_ana_filter_rules.py`.

## Outputs vigentes

La carpeta `outputs/santa_ana_xalmimilulco/` contiene solamente:

- Cinco GeoPackage: candidatos, clasificación completa, relevantes/revisar, universo relevante y comparación.
- Cuatro mapas en HTML y PNG.
- Quince tablas CSV de SAIC, DENUE, reglas, comparación anterior, resumen y validación.
- `index.md` y `pipeline_manifest.json`.
- El reporte principal en `docs/santa_ana_xalmimilulco/reporte_auditoria_universos_santa_ana.pdf`.

## Como auditar una decision

1. Abrir `outputs/santa_ana_xalmimilulco/tablas/clasificacion_explicita_todos.csv`.
2. Localizar el establecimiento por `_id_key`.
3. Revisar `reglas_inclusion_activadas`.
4. Revisar `reglas_exclusion_activadas`.
5. Confirmar `categoria_filtro`, `relevancia_ambiental` y `motivo_clasificacion`.
6. Consultar la definicion de cada regla en `catalogo_reglas_filtro.csv`.
7. Revisar `grupos_keywords_detectados`, `etapas_productivas_detectadas`,
   `universos_keywords_detectados` y `niveles_evidencia_detectados`.

Las exclusiones tienen prioridad. Por ejemplo, una unidad puede contener la
palabra "lavado", pero quedar fuera si tambien activa una exclusion de lavado
no textil, planchado, insumos o servicio.

## Como modificar el filtro

El vocabulario se modifica en
`config/filtros_textiles_santa_ana/palabras_clave.csv`. Los codigos se
modifican en `codigos_scian.csv`; la prioridad y el resultado de cada categoria
se modifican en `politica_categorias.csv`. Solo se edita Python cuando cambia la
forma de combinar senales.

Los CSV de `config/` son entradas versionadas y si deben editarse. Los CSV y
GeoPackage de `outputs/` son copias generadas y no deben editarse manualmente.
Despues de cualquier cambio se ejecuta
`python scripts\run_santa_ana_pipeline.py`.

Una modificacion se considera consistente cuando
`tablas/validacion_trazabilidad.csv` contiene exclusivamente resultados `OK`.
