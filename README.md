# Diagnóstico textil reproducible — Alto Atoyac

El proyecto construye un universo analítico independiente de establecimientos con señales
textiles. Actualmente está activa:

- Santa Ana Xalmimilulco

Huejotzingo y San Martín Texmelucan permanecen configuradas pero desactivadas en
`localidades.csv`.

La clasificación no utiliza las capas MH ni canónica. Esas referencias se abren solamente
después de materializar y registrar la capa independiente. Los resultados representan
prioridad de análisis; no prueban descargas ni contaminación.

## Ejecución

```powershell
pip install -r requirements.txt
python scripts/run_santa_ana_pipeline.py
```

También se pueden ejecutar las etapas por separado:

```powershell
python scripts/02_classify_independent_universe.py
python scripts/03_refine_and_prioritize.py
python scripts/05_apply_special_audit.py
python scripts/06_prepare_maquila_review.py
python scripts/08_compare_and_report.py
```

## Flujo

```text
denue_raw.gpkg + localidades.gpkg + catálogos CSV
                         ↓
       universo productivo amplio
                         ↓
          314 registros + revisión
                         ↓
       refinamiento y priorización
                         ↓
        312 retenidos + exclusiones
                         ↓  (resultado congelado)
              MH + canónico histórico
                         ↓
             comparación y reporte
```

`01_prepare_geodata.py` importa y normaliza las fuentes geográficas cuando estas cambian.
`02_classify_independent_universe.py` recorta las tres localidades y clasifica los registros.
`03_refine_and_prioritize.py` afina el alcance y asigna prioridades sin buscar nuevos registros.
`05_apply_special_audit.py` aplica la auditoría documentada de los seis casos prioritarios.
`06_prepare_maquila_review.py` genera la cola manual de maquilas con URLs ya llenas.
`08_compare_and_report.py` abre las referencias, compara y documenta los resultados.
La etapa de refinamiento genera `cola_revision_manual_314.csv` y
`cola_revision_manual_20.csv`, con enlaces de Google Maps y OpenStreetMap que no requieren API,
además de campos vacíos para registrar evidencia y decisiones humanas.
`run_santa_ana_pipeline.py` ejecuta las etapas en orden.

## Configuración externa editable

Los filtros están en `config/filtros_textiles_santa_ana/versiones/v1/`:

- `palabras_clave.csv`: términos, grupos y función metodológica.
- `codigos_scian.csv`: códigos exactos y prefijos.
- `reglas_clasificacion.csv`: catálogo legible de reglas.
- `matriz_decision.csv`: precedencia ejecutable, condiciones y decisiones.
- `politica_categorias.csv`: significado de las categorías.
- `politica_refinamiento.csv`: exclusiones de alcance y prioridades de la segunda etapa.
- `localidades.csv`: polígonos y método de recorte.
- `referencias_comparacion.csv`: referencias usadas después de clasificar.
- `version.json`: versión y alcance.

Para cambiar el método sin perder reproducibilidad, copie `v1` a una versión nueva, edite
los CSV y actualice la ruta `CONFIG_DIR` de los scripts. No edite manualmente las capas
generadas.

## Resultados

- `outputs/universo_independiente_3_localidades/`: clasificación, capas y manifiesto.
- `outputs/universo_refinado_santa_ana/`: refinamiento, prioridades y exclusiones de alcance.
- `outputs/comparacion_3_localidades/`: comparación, mapa y reporte metodológico.
- `outputs/comparacion_3_localidades/reporte_metodologico.md`: procedimiento completo,
  reglas, conteos, comparación y limitaciones.

La comparación MH/canónica se limita a Santa Ana porque no existen referencias equivalentes
para Huejotzingo y San Martín. Estas localidades se etiquetan como
`sin_referencia_disponible`.
