# Scripts historicos de Santa Ana

Estos archivos documentan etapas anteriores del desarrollo del filtro y sus
comparaciones. No forman parte del flujo operativo vigente.

Incluyen las comparaciones exploratorias 10 y 12--18. El script
`11_apply_filters_denue2026.py` permanece fuera de esta carpeta porque prepara
los insumos DENUE 2026 que consume el pipeline actual.

La unica entrada que debe ejecutarse es:

```powershell
python scripts\run_santa_ana_pipeline.py
```

El pipeline vigente conserva el universo original como canonico, compara la
capa MH ya filtrada y construye el foco estricto solamente como alternativa
analitica trazable.
