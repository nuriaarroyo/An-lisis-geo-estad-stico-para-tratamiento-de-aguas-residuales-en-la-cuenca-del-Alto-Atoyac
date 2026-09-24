# Parte 2 — concentraciones territoriales del universo sectorial ampliado

Esta fase estudia el **universo sectorial ampliado de actividades textiles, confección y servicios de lavandería/tintorería potencialmente relevantes**.

La detección espacial usa 4,365 establecimientos de los municipios de apoyo para reducir efectos de borde. La interpretación principal usa los 4,010 establecimientos dentro de la cuenca del Alto Atoyac.

Principios:

1. El clustering inicial utiliza exclusivamente coordenadas.
2. Las señales económicas, textuales e hídricas se usan después para perfilar.
3. Los registros clasificados como ruido se conservan como actividad espacialmente dispersa.
4. La solución principal no se presenta como una partición territorial verdadera única.
5. Todos los productos nuevos se guardan en `outputs/parte_2/` y no sobrescriben la Parte 1.

El pipeline completo y definitivo se ejecuta con:

```powershell
python scripts\219_ejecutar_parte2_completa.py
```

La numeración `200+` es independiente de la Parte 1. `200_parte2_comun.py` contiene configuración compartida y los pasos ejecutables comienzan en `201_`. El script `212_` se conserva como ejecutor histórico de la primera implementación; `219_` es el ejecutor final de cierre.

## Documentos vivos

- `decisiones/`: decisiones metodológicas tomadas antes y durante el análisis.
- `metodologia/`: definición operacional de variables y métodos.
- `trazabilidad/`: fuentes, scripts y outputs auditables.
- `reporte/`: reporte técnico regenerable.
- `presentacion/`: presentación regenerable.

## Entregables finales

- `reporte/reporte_tecnico_parte_2.tex` y `.pdf`.
- `presentacion/presentacion_parte_2.tex` y `.pdf`.
- `atlas/atlas_clusters.tex` y `.pdf`.
- `outputs/parte_2/11_cierre/`: auditorías, conclusiones y manifiesto.
- `outputs/parte_2/12_atlas/`: 19 láminas visuales.
- `outputs/parte_2/13_figuras_finales/`: 11 figuras definitivas.
