# Reporte de apoyo a auditoria manual DENUE

Este reporte apoya la auditoria manual de los registros DENUE clasificados como `revisar` dentro del universo textil/mezclilla del diagnostico.

Las categorias sugeridas son un apoyo operativo y no sustituyen la decision humana documentada en `categoria_auditada` y `notas_auditoria`.

La distancia a hidrografia se usa como criterio de priorizacion espacial con umbral de 250 m; no constituye prueba de contaminacion directa.

## Resultados procesados

- Total de registros procesados: 182
- Sugeridos como alta: 2
- Sugeridos como media: 13
- Sugeridos como excluir: 9
- Sugeridos como revisar: 158
- Registros cercanos a hidrografia: 41

## Siguientes pasos

1. Revisar manualmente `categoria_auditada`.
2. Llenar `notas_auditoria` con la evidencia o justificacion.
3. Correr `scripts/07_apply_denue_audit.py`.
4. Correr `scripts/08_make_audited_maps.py`.
