> Revisi?n actualizada con connect. Ver README del paquete 11 y auditoria_cambios_archivos.csv. Se conservan los resultados anteriores en el paquete 10.

# Grafos y corredores exploratorios: Santa Ana Xalmimilulco y Huejotzingo

## Resultado principal

La red descargada permite explorar rutas desde los 34 establecimientos prioritarios de Huejotzingo hasta las tres PTAR del núcleo. Los 31 prioritarios de Santa Ana están en otra componente: ninguno tiene ruta hacia esas plantas en los datos actuales. Esto demuestra un vacío de continuidad de la red disponible, no una imposibilidad territorial o hidráulica.

Entre los nodos de ambas componentes hay una separación mínima de 990 m. Es una línea de diagnóstico, NO una propuesta de colector ni la longitud de una calle faltante. No se unieron extremos ni se añadieron caminos supuestos. Hay que completar las vialidades interurbanas antes de comparar destinos desde Santa Ana.

## Alcance y método

- Se conserva el universo de 408 establecimientos: 337 Santa Ana y 71 Huejotzingo. Se enlazaron todos al grafo para diagnóstico; las rutas se calculan sólo para 65 prioritarios (31 Santa Ana, 34 Huejotzingo). Son reglas de prioridad productiva, no generación de caudal confirmada.
- Destinos: Cabecera Municipal (PTAR_066, asociado a 005), Paseo de los Sauces (067), Real Segovia (068). No se supone que operen o reciban efluente textil. Las plantas externas quedan fuera de esta primera comparación.
- Ventana de análisis: envolvente de establecimientos y destinos + 2.5 km. Se seleccionaron segmentos completos de cuatro entregas viales, incluida connect que intersectan esa ventana; una ruta exterior podría quedar fuera.
- Se usaron 3,630 tramos fuente. El grafo original tiene 6,998 nodos, 7,820 aristas y 81 componentes. Considerar cruces geométricos no redujo las 81 componentes del grafo construido con vértices originales.
- Se generó un grafo no dirigido, con longitud métrica como costo. El sentido vehicular no se usa como dirección hidráulica. Todos los tipos de vialidad se mantienen como candidatos, incluidos privados o peatonales, cuya disponibilidad constructiva no se acredita.
- Los cruces geométricos se consideran conectados: escenario permisivo pendiente de verificar puentes y pasos a desnivel. No se aplicaron tolerancias que unan brechas. Se conservaron atributos viales por proximidad del punto medio a la fuente; en tramos superpuestos esa asignación puede ser ambigua.
- Cada punto se proyecta sobre la arista más próxima y se divide la arista en ese lugar. Se conserva el punto original y un enlace geométrico independiente; no se atribuye una conexión sanitaria existente. Tras incorporar puntos de acceso resultan 7,400 nodos y 8,222 aristas.
- Los caminos mínimos se calculan sobre longitud vial. El total comparado suma dos accesos geométricos (establecimiento–calle y calle–PTAR). Los accesos no se someten a restricciones de propiedad o construcción.
- Los perfiles se muestrean cada 20 m y en ambos extremos sobre los dos MDT de 1.5 m, transformando al CRS nativo. No se usa MDS ni se rellenan vacíos. El perfil comienza y termina sobre la vialidad; no incluye accesos ni cota hidráulica de entrada a la planta. Una cobertura del 100 % de muestras no certifica cada píxel intermedio.

## Comparación de rutas desde Huejotzingo

| Destino | Origenes | Longitud min/med/max (km) | Muestras MDT validas | Tramo compartido por 34 (km) | Elementos hidrograficos intersectados |
| --- | --- | --- | --- | --- | --- |
| PLANTA DE LA CABECERA MUNICIPAL | 34 | 2.74 / 4.47 / 5.55 | 100.0 % | 1.82 | 0–1 |
| PASEO DE LOS SAUCES | 34 | 2.43 / 4.17 / 5.24 | 100.0 % | 1.42 | 0–1 |
| REAL SEGOVIA | 34 | 3.66 / 5.39 / 6.47 | 75.4 % | 2.61 | 0–1 |

Las longitudes min/med/max incluyen los accesos geométricos. La columna de hidrografía cuenta elementos RH18 intersectados, no cruces físicos independientes, puentes o permisos comprobados. Varios elementos pueden referirse al mismo cauce; faltan verificación y conciliación.

Paseo de los Sauces es el destino de menor longitud de los tres en esta red para los 34 orígenes. Esto no lo convierte en el destino técnicamente preferible: la capacidad libre, calidad admisible, pretratamiento y operación no están verificadas. Cabecera Municipal carece de capacidad reportada. Para Paseo y Real Segovia la compilación reporta 60/30 y 25/8 L/s de capacidad/caudal, respectivamente; la diferencia no debe presentarse como capacidad libre disponible.

## Qué muestra la elevación

Las 68 rutas hacia Cabecera Municipal y Paseo de los Sauces tienen todas sus muestras MDT válidas. Sus puntos finales sobre la calle están entre 16–33 m y 23–40 m, respectivamente, por debajo del punto inicial de cada ruta. Es una tendencia descendente global, no garantía de conducción por gravedad: los perfiles contienen depresiones y ascensos locales.

Hacia Real Segovia, la cobertura media de muestras es 75.4 % y ningún perfil queda completo. No se puede calcular el desnivel final ni evaluar un perfil continuo hasta esa planta. Se necesita ampliar el MDT hacia su extremo oriental.

En Santa Ana la falta de ruta impide producir un perfil de corredor conectado. Además, seis establecimientos de su universo carecen de elevación en los MDT disponibles, según la auditoría previa.

## Corredores compartidos y alternativas

El grosor del mapa representa cuántos de los 34 caminos de Huejotzingo comparten cada arista PARA UN MISMO DESTINO. No se deben sumar las tres alternativas de planta como demanda independiente. No es caudal, diámetro, infraestructura existente ni una red optimizada de mínimo costo conjunto.

Hay 1.42 km compartidos por los 34 orígenes hacia Paseo, 1.82 km hacia Cabecera y 2.61 km hacia Real Segovia. Entre las vías identificadas aparece Avenida de los Zapadores. Esos segmentos merecen inspección como corredores preliminares, con revisión de derechos de vía, servicios enterrados, cruces y cotas.

Para el origen representativo EST_03059 (prioritario alcanzable más próximo al centroide de prioritarios de Huejotzingo) se obtuvieron alternativas geométricamente diferentes. Se buscaron hasta 80 cierres individuales de arista, conservando un desvío de al menos 300 m y al menos 15 % de longitud nueva respecto al camino mínimo. Es una búsqueda heurística, no una enumeración exhaustiva de alternativas.

| destino_id | alternativa | longitud_km | incremento_m | longitud_nueva_m |
| --- | --- | --- | --- | --- |
| PTAR_066 | 1 | 4.335 | 0.0 | 0.0 |
| PTAR_066 | 2 | 4.339 | 3.2 | 946.3 |
| PTAR_067 | 1 | 4.03 | 0.0 | 0.0 |
| PTAR_067 | 2 | 4.033 | 3.2 | 946.3 |
| PTAR_068 | 1 | 5.21 | 0.0 | 0.0 |
| PTAR_068 | 2 | 5.213 | 3.2 | 946.3 |

Las alternativas comparten el origen y destino. Unos 946 m de recorrido pueden cambiar con sólo aproximadamente 3.2 m adicionales de longitud total. Por tanto, la distancia por sí sola no permite elegir el corredor: completar relieve y restricciones puede ser más decisivo. Los perfiles de las alternativas de desvío no se calcularon; los perfiles publicados corresponden a los caminos mínimos.

## Qué revisar a continuación

1. Completar la vialidad entre Santa Ana y el conjunto urbano al sur. Revisar el tramo señalado por brechas_no_conectadas y ampliar la cobertura exterior de caminos; no digitalizar la línea de brecha como calle existente.
2. Completar hojas MDT para Santa Ana occidental y Real Segovia. Después muestrear perfiles de todos los corredores alternativos y accesos.
3. Verificar in situ los tramos comunes de Huejotzingo, pasos a desnivel, cauces, calles privadas, interferencias y puntos de descarga/conexión.
4. Obtener del operador estado operativo, cota de entrada, cobertura real y posibilidad de recibir efluente industrial de cada planta.
5. Incorporar caudales/cargas y topografía de campo antes de dimensionar diámetros, zanjas o bombeo.

## Productos y reproducción

- `explorador_grafos.html`: explorador autónomo con componentes, destinos, orígenes, rutas por planta y desvíos. No requiere servicios de mapas externos.
- `grafo_corredores_exploratorios.gpkg`: nodos, aristas, accesos, rutas, alternativas, corredores compartidos, brechas y contexto hidrográfico.
- `grafo_vial.graphml`: grafo computable con nodos identificados, coordenadas UTM y aristas con longitud y referencia de arista padre.
- `matriz_origen_destino.csv`: 195 pares (65 × 3), 102 conectados y 93 sin ruta; los no conectados no tienen longitud ni perfil.
- `perfiles_20m.csv`, `componentes.csv`, `brechas_componentes.csv`, `alternativas_representativas.csv`, `intersecciones_hidrografia.csv`, `comparacion_destinos_huejotzingo.csv`.
- PNG 01–04: componentes, corredores por destino, perfiles y alternativas.
- `manifest_reproducibilidad.json`, `resumen.json`, `validacion_capas.json`.

Desde atoyac, después de generar los paquetes 305 y 306:

```powershell
python scripts/309_actualizar_connect.py
```

Validación: los 102 caminos recorren aristas existentes y sus longitudes geométricas coinciden con la suma de costos; ninguna ruta atraviesa componentes desconectadas. Matriz sin pares duplicados, longitudes totales no menores a la vial, geometrías revisadas y grafo GraphML reabierto con los conteos esperados. Estos controles verifican la implementación, no la veracidad de conexiones físicas.
