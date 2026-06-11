# Guia de ejecucion: clasificacion productiva DENUE

Esta guia documenta el flujo nuevo para clasificar establecimientos DENUE textiles por etapa productiva probable, presion ambiental potencial y prioridad de investigacion.

La clasificacion no prueba descargas, contaminacion ni incumplimiento. Sirve para priorizar auditoria documental y validacion en campo.

## Alcance operativo del proyecto

Para este proyecto, el universo real de analisis no es todo lo textil. El alcance operativo se define como la union de:

- procesos humedos o tratamiento de prendas;
- lavado, deslavado o lavanderia;
- mezclilla, denim o jeans.

Ese subconjunto queda marcado con `flag_universo_alcance_proyecto` y se guarda en `denue_universo_alcance_proyecto.csv`. Lo demas se conserva como contexto textil trazable, pero no como universo principal del alcance ambiental.

## Dependencias

```powershell
pip install -r requirements.txt
```

## Orden recomendado

```powershell
python scripts/00_inventory_raw_data.py
python scripts/01_prepare_geodata.py
python scripts/02_filter_denue_textil.py
python scripts/03_process_saic.py
python scripts/04_spatial_analysis.py
python scripts/02b_clasificacion_productiva_denue.py
python scripts/05_make_maps.py
python scripts/05b_make_productive_classification_maps.py
python scripts/06_make_interactive_maps.py
python scripts/06b_make_plotly_productive_maps.py
python scripts/07_apply_denue_audit.py
python scripts/08_make_audited_maps.py
```

Tambien se puede correr:

```powershell
python scripts/run_all.py
```

## Entradas principales

- `data/processed/denue_textil_con_distancia.gpkg`
- `data/processed/hidrografia.gpkg`
- tablas SAIC en `outputs/tables/`

## Salidas principales

- `outputs/tables/denue_clasificacion_productiva/denue_universo_textil_clasificado.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_universo_textil_depurado.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_universo_alcance_proyecto.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_estudio_prioritario.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_pendientes_auditoria.csv`
- `outputs/tables/denue_clasificacion_productiva/localidades/denue_universo_alcance_huejotzingo.csv`
- `outputs/tables/denue_clasificacion_productiva/localidades/denue_universo_alcance_xalmimilulco.csv`
- `outputs/tables/denue_clasificacion_productiva/localidades/denue_universo_alcance_san_martin.csv`
- `outputs/tables/denue_clasificacion_productiva/control_calidad_clasificacion.csv`
- `outputs/tables/auditoria_enriquecida/auditoria_denue_textil_priorizada.xlsx`
- `outputs/maps/denue_clasificacion_productiva/`
- `outputs/maps_interactive/denue_clasificacion_productiva/index.html`

## Como llenar el Excel de auditoria

Abrir:

`outputs/tables/auditoria_enriquecida/auditoria_denue_textil_priorizada.xlsx`

Llenar:

- `categoria_auditada`
- `etapa_productiva_auditada`
- `notas_auditoria`
- `fuente_auditoria`
- `decision_estudio`
- `fecha_auditoria`
- `auditor_responsable`

Valores sugeridos para `decision_estudio`:

- `incluir_prioritario`
- `incluir_contexto_productivo`
- `excluir_del_universo_prioritario`
- `excluir_por_comercio`
- `excluir_por_renta`
- `mantener_pendiente`
- `validar_documentalmente`
- `validar_en_campo`

## Aplicar auditoria

Despues de llenar el Excel:

```powershell
python scripts/07_apply_denue_audit.py
```

El script produce:

- `outputs/tables/denue_clasificacion_productiva/denue_clasificacion_productiva_auditada.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_clasificacion_productiva_pendiente_decision_manual.csv`
- `outputs/tables/denue_clasificacion_productiva/denue_clasificacion_productiva_con_decision_manual.csv`
- `data/processed/denue_clasificacion_productiva_auditada.gpkg`

## Abrir mapas HTML

Abrir en navegador:

`outputs/maps_interactive/denue_clasificacion_productiva/index.html`

Cada mapa Plotly permite inspeccionar puntos con nombre, SCIAN, etapa productiva, presion ambiental potencial, confianza, distancia a hidrografia y reglas activadas.

Los mapas interactivos tambien incluyen filtros ya separados por localidad en la carpeta:

`outputs/maps_interactive/denue_clasificacion_productiva/localidades/`

## Compilar documentos

Desde `docs/`:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error metodologia_diagnostico_textil_atoyac.tex
pdflatex -interaction=nonstopmode -halt-on-error metodologia_diagnostico_textil_atoyac.tex
pdflatex -interaction=nonstopmode -halt-on-error observaciones_diagnostico_atoyac.tex
pdflatex -interaction=nonstopmode -halt-on-error observaciones_diagnostico_atoyac.tex
pdflatex -interaction=nonstopmode -halt-on-error auditoria_clasificacion_denue_textil.tex
pdflatex -interaction=nonstopmode -halt-on-error auditoria_clasificacion_denue_textil.tex
```

## Problemas comunes

- Si no existe `denue_textil_con_distancia.gpkg`, correr primero `02_filter_denue_textil.py` y `04_spatial_analysis.py`.
- Si el Excel no tiene decisiones manuales, `07_apply_denue_audit.py` conservara los registros productivos como pendientes de decision manual.
- Si un mapa HTML no carga fondo, revisar conexion a internet porque Plotly usa teselas de OpenStreetMap.
- La distancia a hidrografia aumenta prioridad de investigacion, pero no debe interpretarse como evidencia de contaminacion.
