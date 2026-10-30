# Santa Ana y Huejotzingo: vialidades amplias, grafos y relieve

## Resultado de la nueva entrega

Se revisaron las siete entregas de vialidad, incluidas la descarga de 46,146 tramos en la raíz de vialidades y las carpetas c2 y c3. Se homologaron a EPSG:32614 y se retiraron sólo geometrías exactamente repetidas. El análisis selecciona 3,805 tramos completos que intersectan la envolvente de los 408 establecimientos y tres PTAR + 2.5 km.

La descarga amplia NO cierra la conexión Santa Ana–Huejotzingo. Tras construir intersecciones, siguen 83 componentes. Los 31 orígenes prioritarios de Santa Ana permanecen en una componente distinta a las tres plantas. La separación mínima entre nodos de las dos componentes principales continúa en aproximadamente 990 m. Hay calles aisladas intermedias: esa cifra no significa 990 m exactos de vialidad faltante.

Este resultado no demuestra que físicamente no exista un camino. Muestra que ampliar el recorte de estas capas no agregó la continuidad necesaria. Debe revisarse la representación del enlace interurbano, sus interrupciones y posibles caminos/carreteras ausentes. No se inventaron líneas de conexión.

## Qué se pudo analizar para cada localidad

**Huejotzingo:** 34 orígenes alta/media con ruta a las tres PTAR (102 caminos). Las longitudes permanecen iguales a la revisión previa: la ampliación no cambió las rutas mínimas. Las PTAR son Cabecera Municipal PTAR_066 (asociada a 005), Paseo de los Sauces 067 y Real Segovia 068.

**Santa Ana:** se calcularon 62 caminos dentro de su red, desde los 31 orígenes alta/media hacia dos extremos viales existentes para inspección (EXT_01 y EXT_02). No son rutas a PTAR, puntos de descarga, cruces confirmados ni propuestas de conexión. Se seleccionaron extremos de grado uno dentro de su componente, próximos geométricamente al conjunto de PTAR y separados al menos 250 m entre sí. Sirven para explorar concentraciones de caminos y preparar reconocimiento en campo; no se eligieron por aptitud hidráulica.

| extremo | longitud | latitud |
| --- | --- | --- |
| EXT_01 | -98.392103 | 19.193471 |
| EXT_02 | -98.388918 | 19.193794 |

Los 408 establecimientos permanecen identificados y contextualizan los mapas; las rutas se limitan a los 65 de prioridad alta/media. La clasificación no acredita operación actual ni caudal. El grafo con accesos contiene 7,747 nodos y 8,601 aristas.

## ¿La elevación cubre bien el análisis?

| Localidad | Establecimientos | Con MDT | Área operativa con MDT % | Longitud vial con MDT % |
| --- | --- | --- | --- | --- |
| santa_ana | 337 | 331 | 66.39 | 75.82 |
| huejotzingo | 71 | 71 | 90.72 | 90.91 |

Las zonas operativas son envolventes de establecimientos + 2 km, no límites oficiales. Los porcentajes territoriales se calculan con la máscara de píxeles válidos del MDT, no sólo con los rectángulos de las hojas.

| Localidad | Destino | Rutas | Longitud vial min–max km | Cobertura MDT media/min % | Pendiente global min–max % |
| --- | --- | --- | --- | --- | --- |
| huejotzingo | PTAR_066 | 34 | 2.71–5.53 | 100.0 / 100.0 | -0.64–-0.39 |
| huejotzingo | PTAR_067 | 34 | 2.40–5.22 | 100.0 / 100.0 | -1.01–-0.60 |
| huejotzingo | PTAR_068 | 34 | 3.58–6.40 | 75.6 / 64.3 | sin dato |
| santa_ana | EXT_01 | 31 | 1.51–3.86 | 67.9 / 45.7 | sin dato |
| santa_ana | EXT_02 | 31 | 1.04–3.40 | 99.7 / 90.7 | -0.04–0.55 |

La cobertura de ruta anterior mide LONGITUD dentro de la máscara válida, no sólo porcentaje de muestras. Las distancias de esta tabla son exclusivamente viales; los accesos geométricos a edificios y plantas figuran por separado en la matriz origen–destino.

- Huejotzingo–Cabecera y Huejotzingo–Paseo: cobertura completa de elevación sobre las trazas calculadas. Se puede analizar el relieve de esos corredores.
- Huejotzingo–Real Segovia: falta aproximadamente una cuarta parte del MDT en promedio; no se conoce la elevación final del corredor y no procede evaluar una pendiente global hasta esa planta.
- Santa Ana–EXT_01: cobertura insuficiente; el promedio es cercano a 68 % y hay rutas por debajo de 50 %. El extremo occidental/suroccidental del recorrido deja la hoja disponible.
- Santa Ana–EXT_02: cobertura mucho mejor, cercana a 100 % de media, pero no todos los recorridos quedan completos. Los porcentajes particulares están en cobertura_pendientes_rutas.csv.

## Método del grafo

1. **Geometría métrica y topología.** Grafo no dirigido en NetworkX. Nodos en vértices y cruces de líneas mediante unary_union; aristas entre vértices consecutivos, con costo igual a longitud en metros. No se impone sentido vehicular como dirección de flujo. Se consideran cruces geométricos conectados, pendiente verificar pasos a distinto nivel. No se unen extremos con una tolerancia arbitraria ni se rellenan brechas.
2. **Accesos.** Cada establecimiento y PTAR conserva su ubicación original. Se proyecta sobre la arista más próxima y se divide esa arista en el punto proyectado. El segmento de acceso se registra aparte y no demuestra conexión sanitaria o derecho de paso.
3. **Camino mínimo.** Dijkstra con peso longitud_m. Se obtiene la ruta de menor distancia vial desde cada origen a cada destino alcanzable. Una componente distinta se registra como SIN RUTA, no como distancia cero.
4. **Corredores compartidos.** Se cuenta cuántos caminos utilizan una arista por destino; no es caudal ni un diseño conjunto de colector. Las tres plantas son alternativas: sus demandas no deben sumarse.
5. **Alternativas.** Para un origen representativo alcanzable se prueban hasta 80 cierres individuales de aristas y se conserva un desvío con al menos 300 m y 15 % de longitud nueva. Es exploración heurística, no búsqueda exhaustiva de diseños.
6. **Relieve posterior.** La pendiente NO es todavía el peso del grafo ni restringe el sentido de recorrido. Primero se calcula por distancia; después se audita elevación y pendiente sobre la traza.

## Método para elevación y pendiente

Se utilizan sólo los dos MDT de terreno originales de 1.5 m, transformando las coordenadas de consulta al CRS de cada archivo. No se utiliza MDS como sustituto, no se interpolan faltantes y no se asigna elevación a segmentos sin datos.

- **Perfiles longitudinales:** elevación cada 20 m y en extremos del camino, sin incluir accesos. Son alturas del suelo, no cotas de fondo de tubería o entrada hidráulica a planta.
- **Pendiente longitudinal exploratoria:** cada 100 m (último intervalo puede ser más corto), p = 100 × (z_final − z_inicial) / longitud. Se informa sólo si ambos extremos tienen dato y toda la traza del intervalo queda cubierta. Valor positivo significa subida en el sentido origen–destino; negativo, descenso.
- **Pendiente global:** diferencia de alturas de los extremos dividida por longitud vial total. No resume los obstáculos intermedios; sólo se presenta si las alturas de ambos extremos están disponibles. Debe revisarse además la cobertura del recorrido.
- **Mapas de pendiente superficial:** el MDT se agrega por promedio a celdas de 15 m y se calcula 100 × sqrt((dz/dx)^2+(dz/dy)^2) usando diferencias finitas. Es magnitud de la inclinación del terreno, sin dirección de conducción. La escala de color se limita a 0–15 % para visualizar, sin recortar los valores del GeoTIFF. El MDT original sigue siendo 1.5 m; los 15 m son un producto cartográfico derivado.

Los perfiles de Huejotzingo hacia Cabecera y Paseo descienden globalmente, pero todos contienen al menos un intervalo válido con ascenso superior a 0.5 %. Este umbral sólo señala dónde revisar; no es un criterio de bombeo o aceptación hidráulica. Santa Ana presenta pendientes globales suaves y algunos recorridos con subida neta en el extremo cubierto. La incertidumbre vertical y las variaciones locales impiden deducir gravedad a partir de la pendiente global.

## Mapas y archivos

- [Explorador del territorio y grafo](../explorador.html), autónomo, sin mapas de internet. Activar capas en la leyenda.
- [Santa Ana: elevación](../figuras/05_santa_ana_elevacion.png) y [pendiente superficial](../figuras/05_santa_ana_pendiente.png).
- [Huejotzingo: elevación](../figuras/05_huejotzingo_elevacion.png) y [pendiente superficial](../figuras/05_huejotzingo_pendiente.png).
- [Santa Ana: recorridos internos](../figuras/06_santa_ana_corredores.png) y [perfiles](../figuras/07_santa_ana_perfiles.png).
- [Huejotzingo: rutas a PTAR](../figuras/06_huejotzingo_corredores.png) y [perfiles](../figuras/07_huejotzingo_perfiles.png).
- grafo_corredores_exploratorios.gpkg: red, rutas hacia PTAR, rutas locales de inspección, extremos y cobertura MDT, en capas distintas.
- GeoTIFF *_elevacion_15m.tif y *_pendiente_pct_15m.tif: productos cartográficos en EPSG:32614, con NoData explícito.
- matriz_origen_destino.csv: 195 pares origen–PTAR (102 conectados, 93 sin ruta).
- cobertura_pendientes_rutas.csv: 164 recorridos perfilados (102 hacia PTAR + 62 internos).
- pendientes_longitudinales_100m.csv: pendientes con validez de cobertura por intervalo.
- Inventarios de entregas, MDT, cobertura territorial, resúmenes y manifiestos para trazabilidad.

## Qué permite concluir y qué falta

Se puede continuar la exploración de corredores dentro de ambas localidades y comparar caminos hacia las plantas desde Huejotzingo. No se puede afirmar todavía que Santa Ana esté conectada a una PTAR por las vialidades actuales. Tampoco se puede afirmar viabilidad por gravedad, caudal atendido, diámetros o necesidad de bombeo.

Prioridades: revisar la conexión vial interurbana con una fuente que represente el enlace, completar MDT en Santa Ana occidental y Real Segovia, revisar cruces y accesos privados, y confirmar cotas de entrada/operación de PTAR. Para diseño se necesitan caudales y topografía de campo.

## Reproducción

Desde atoyac, con los puntos de establecimientos y plantas del paquete 09:

```powershell
python scripts/310_actualizar_vialidades_amplias.py
python scripts/311_territorio_pendientes_locales.py
python scripts/312_documentar_red_amplia.py
```

Los paquetes 08–11 se conservan como revisiones anteriores. El paquete 12 es la revisión vigente para vialidades, grafos y mapas de relieve. La selección del foco económico y de PTAR permanece igual.
