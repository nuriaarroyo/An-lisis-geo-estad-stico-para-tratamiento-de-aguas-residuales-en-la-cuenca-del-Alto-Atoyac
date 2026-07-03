# Scripts historicos de Santa Ana

Estos archivos documentan etapas anteriores del desarrollo del filtro y sus
comparaciones. No forman parte del flujo operativo vigente.

Incluyen el inventario opcional, la cadena experimental 02--18, los mapas y las
auditorias anteriores. El pipeline vigente ya no importa estos modulos.

Los unicos scripts operativos en la raiz son `01_prepare_geodata.py`,
`run_santa_ana_pipeline.py`, `santa_ana_filter_rules.py`,
`santa_ana_audit_utils.py` y `common.py`.

La unica entrada que debe ejecutarse es:

```powershell
python scripts\run_santa_ana_pipeline.py
```

El pipeline vigente conserva el universo original como canonico, compara la
capa MH ya filtrada y construye el foco estricto solamente como alternativa
analitica trazable.
