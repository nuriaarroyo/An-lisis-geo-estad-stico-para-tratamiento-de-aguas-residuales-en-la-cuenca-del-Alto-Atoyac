# Guia del filtro trazable de Santa Ana

## Objetivo

Este flujo conserva como canonico el universo original de 38 establecimientos
producido previamente para Santa Ana Xalmimilulco. Lo compara con la capa MH ya
filtrada de 49 puntos, el foco estricto alternativo de 67 y el filtrado
prioritario DENUE 2026 de 42.

El foco estricto no sustituye al universo original. Responde a una pregunta
analitica mas amplia sobre senales de tratamiento, lavado, acabado, tintoreria,
mezclilla, jeans, deshebrado o produccion de material textil.

Ninguna salida constituye evidencia de descarga o contaminacion.

## Pipeline operativo unico

La ejecucion normal tiene una sola entrada:

```powershell
python scripts\run_santa_ana_pipeline.py
```

El pipeline ejecuta cuatro etapas con objetivos distintos:

1. **Construir alternativa:** aplica el filtro estricto y registra la decision de cada establecimiento.
2. **Comparar:** cruza el canonico original con MH filtrado, el foco estricto y el filtrado 2026.
3. **Validar:** comprueba IDs, reglas, decisiones y membresias.
4. **Documentar:** genera mapas, tablas, indice, manifiesto y PDF.

El estado de cada ejecucion queda en
`outputs/santa_ana_xalmimilulco/pipeline_manifest.json`.

## Que decide y que solo compara

- **Universo canonico:** tu universo original de Santa Ana, con 38 establecimientos.
- **MH filtrado:** la capa `capa MH.shp`, con 49 puntos: 43 con ID DENUE y 6 sin ID.
- **Alternativa analitica:** foco estricto de 67, definido en `scripts/santa_ana_filter_rules.py`.
- **Comparacion contextual:** filtrado prioritario DENUE 2026 de Santa Ana, con 42.
- **Antecedente diagnostico:** foco amplio conservado en `scripts/legacy/`. No forma parte del pipeline vigente.

Los scripts numerados 16, 17 y 18 son etapas internas. Para una ejecucion normal
no deben lanzarse por separado.

## Scripts vigentes

Solo hay tres archivos activos para este analisis:

- `scripts/run_santa_ana_pipeline.py`: ejecuta todo el flujo y define las cuatro etapas.
- `scripts/santa_ana_filter_rules.py`: contiene exclusivamente las reglas auditables del foco alternativo.
- `scripts/santa_ana_audit_utils.py`: concentra lectura, exportacion, mapas y LaTeX.

Los scripts anteriores se conservan en `scripts/legacy/` como historial y no
deben ejecutarse.

## Outputs vigentes

La carpeta `outputs/santa_ana_xalmimilulco/` contiene solamente:

- Tres GeoPackage: foco alternativo, trazabilidad y comparacion.
- Cuatro mapas en HTML y PNG.
- Nueve tablas CSV de datos, reglas, resumen y validacion.
- `index.md` y `pipeline_manifest.json`.
- El reporte principal en `docs/santa_ana_xalmimilulco/reporte_auditoria_universos_santa_ana.pdf`.

## Como auditar una decision

1. Abrir `outputs/santa_ana_xalmimilulco/tablas/trazabilidad_filtro_santa_ana_2026.csv`.
2. Localizar el establecimiento por `_id_key`.
3. Revisar `reglas_inclusion_activadas`.
4. Revisar `reglas_exclusion_activadas`.
5. Confirmar `decision_filtro_estricto` y `motivo_decision_filtro`.
6. Consultar la definicion de cada regla en `catalogo_reglas_filtro.csv`.

Las exclusiones tienen prioridad. Por ejemplo, una unidad puede contener la
palabra "lavado", pero quedar fuera si tambien activa una exclusion de lavado
no textil, planchado, insumos o servicio.

## Como modificar el filtro

Las reglas se modifican solamente en `scripts/santa_ana_filter_rules.py`.
Despues se ejecuta nuevamente `python scripts\run_santa_ana_pipeline.py`.
No deben editarse manualmente los CSV o GeoPackage generados.

Una modificacion se considera consistente cuando
`tablas/validacion_trazabilidad.csv` contiene exclusivamente resultados `OK`.
