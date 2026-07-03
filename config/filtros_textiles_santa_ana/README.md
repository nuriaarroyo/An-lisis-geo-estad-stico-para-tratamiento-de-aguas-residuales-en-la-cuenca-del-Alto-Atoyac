# Catalogos del filtro textil de Santa Ana

Estos archivos son entradas del pipeline y constituyen la definicion auditable
del filtro. Se editan aqui; las copias de `outputs/` son resultados generados.

## Archivos

- `palabras_clave.csv`: una palabra o frase normalizada por renglon. `groups`
  indica en que pruebas booleanas participa; `process_stage`, `universe` y
  `evidence_level` explican su interpretacion.
- `codigos_scian.csv`: codigos exactos o prefijos y la senal que representan.
- `politica_categorias.csv`: prioridad de asignacion. Una prioridad mayor
  sustituye una categoria de prioridad menor cuando ambas condiciones se
  cumplen.
- `reglas_clasificacion.csv`: catalogo humano de las reglas y su objetivo.

## Flujo

1. SAIC identifica los prefijos manufactureros textiles.
2. DENUE aporta codigo SCIAN y texto de nombre, razon social y actividad.
3. `santa_ana_filter_rules.py` normaliza el texto y consulta estos catalogos.
4. Las exclusiones tienen precedencia segun `politica_categorias.csv`.
5. Las salidas conservan palabras, grupos, campos y reglas activadas.

Las senales indican prioridad de investigacion o revision. No demuestran
descarga, contaminacion ni uso efectivo de un proceso dentro del establecimiento.
