# Catalogos del filtro textil de Santa Ana

Cada subcarpeta de `versiones/` contiene la definicion exacta de un filtro.
La version activa se declara mediante `FILTER_VERSION` en
`scripts/santa_ana_filter_rules.py`. Las copias de `outputs/` son resultados.

La primera version operativa es `versiones/v1/`.

## Archivos

- `versiones/v1/palabras_clave.csv`: una palabra o frase por renglon. `groups`
  indica en que pruebas booleanas participa; `process_stage`, `universe` y
  `evidence_level` explican su interpretacion.
- `versiones/v1/codigos_scian.csv`: codigos exactos o prefijos y su senal.
- `versiones/v1/politica_categorias.csv`: prioridad de asignacion. Una prioridad mayor
  sustituye una categoria de prioridad menor cuando ambas condiciones se
  cumplen.
- `versiones/v1/reglas_clasificacion.csv`: catalogo humano de las reglas.

## Flujo

1. SAIC identifica los prefijos manufactureros textiles.
2. DENUE aporta codigo SCIAN y texto de nombre, razon social y actividad.
3. `santa_ana_filter_rules.py` normaliza el texto y consulta estos catalogos.
4. Las exclusiones tienen precedencia segun `politica_categorias.csv`.
5. Las salidas conservan palabras, grupos, campos y reglas activadas.

Las senales indican prioridad de investigacion o revision. No demuestran
descarga, contaminacion ni uso efectivo de un proceso dentro del establecimiento.
