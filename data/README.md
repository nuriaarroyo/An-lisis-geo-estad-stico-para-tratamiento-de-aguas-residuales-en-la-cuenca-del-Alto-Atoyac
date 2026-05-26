# Datos

Esta carpeta espera los insumos locales del proyecto:

- `raw/`: descargas originales de INEGI, DENUE, hidrografia/hidrologia y SAIC.
- `processed/`: GeoPackages y capas procesadas generadas por los scripts.

Estas carpetas no se versionan porque contienen archivos geoespaciales pesados o derivados reproducibles. Para reproducir el flujo, coloca los datos fuente en `data/raw/` y ejecuta:

```bash
python scripts/run_all.py
```
