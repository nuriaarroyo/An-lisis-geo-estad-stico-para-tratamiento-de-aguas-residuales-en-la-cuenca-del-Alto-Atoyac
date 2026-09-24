# 004 — Ruido, perfiles y sobrerrepresentación

Los establecimientos con etiqueta `-1` se conservan como `RUIDO_DISPERSO`: actividad sectorial espacialmente dispersa o no perteneciente a una concentración bajo la configuración seleccionada.

El perfilado posterior mantiene señales multilabel. Las proporciones no tienen que sumar 100%.

Para sobrerrepresentación se calculan conteo, prevalencia interna, prevalencia global, diferencia, lift, `log2(lift)`, odds ratio, intervalo aproximado, Fisher y ajuste Benjamini–Hochberg.

La bandera descriptiva conservadora exige simultáneamente:

- al menos cinco observaciones con la señal;
- prevalencia interna mínima de 5%;
- lift mínimo de 1.25;
- valor p ajustado no mayor a 0.05.

Esta bandera sirve para priorizar lectura; no valida procesos reales ni demuestra causalidad.
