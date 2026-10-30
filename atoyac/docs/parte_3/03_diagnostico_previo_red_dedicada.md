# Diagnóstico previo al diseño exploratorio de una red dedicada

## Qué sabemos

Santa Ana Xalmimilulco contiene 337 establecimientos del universo sectorial de Parte 2, todos dentro del cluster 8. Ocho tienen relevancia ambiental alta, 23 media y ocho evidencia de proceso húmedo; 306 permanecen por revisar. Esto permite localizar una concentración productiva, pero no cuantificar el agua residual generada.

La delimitación piloto no es un límite oficial de localidad: se construyó como envolvente convexa de los establecimientos cuyo campo `localidad` es Santa Ana Xalmimilulco, ampliada 2 km para observar infraestructura próxima. Debe reemplazarse por una delimitación oficial cuando esté disponible.

Dentro de esa zona operativa aparece un punto de descarga de INEGI. El conjunto no declara su cuerpo receptor, caudal o conexión con drenaje. Se calculó únicamente el segmento RH18 más próximo, marcado como proximidad geométrica.

## Respuestas para el caso piloto

1. **Posibles orígenes.** Los 31 establecimientos de prioridad alta o media constituyen candidatos individuales iniciales. También se conserva el conjunto completo de 337 establecimientos como origen territorial agregado del cluster 8, sin tratar su centroide como conexión física.
2. **Procesos prioritarios.** Ocho establecimientos son de prioridad alta, 23 media y ocho tienen señal de proceso húmedo. La señal no sustituye medición de caudal o caracterización del efluente.
3. **Descargas próximas.** Hay un punto registrado dentro de la envolvente operativa. No se conoce su vínculo con establecimientos.
4. **Cauces próximos.** La red RH18 atraviesa el entorno y permite medir cercanía. Sus segmentos no traen nombre, por lo que no se asignaron automáticamente a Xochiac, Tenitzatl o Xopanac.
5. **PTAR cercanas.** Dentro de 10 km del centroide operativo aparecen ocho registros: Real Segovia (3.33 km), Paseo de los Sauces (3.64 km), la planta de la cabecera municipal en dos fuentes (4.14 km), Tres Besanas (5.01 km), Chiautzingo (7.58 km) y San Lucas Atoyatenco en dos fuentes (8.94 km). Los duplicados por fuente se conservan.
6. **PTAR en Santa Ana.** Ninguna fuente permite confirmar una PTAR localizada y operativa dentro de la delimitación de la localidad. Las plantas próximas son registros territoriales; deben verificarse documentalmente.
7. **Destinos posteriores.** Las ocho entradas cercanas forman una lista de alternativas por estudiar, no una selección. También podría estudiarse posteriormente una nueva zona de pretratamiento, pero no hay datos para localizarla todavía.
8. **Red vial.** No existe una capa vial vectorial, por lo que no puede determinarse si conecta los focos con los destinos.
9. **Elevación.** No existe topografía; no puede evaluarse funcionamiento por gravedad o necesidad de bombeo.
10. **Datos previos a una función objetivo.** Se requieren caudales y calidad por origen, red vial conectada, DEM, restricciones de construcción, cruces, derechos de vía, suelo/inundación, capacidad libre y compatibilidad de las PTAR, costos, permisos y reglas de penalización.

## Qué capas son suficientemente buenas para modelar

Los establecimientos, límites e hidrografía son adecuados para definir nodos y restricciones preliminares. PTAR y descargas son parciales: sirven como candidatos/contexto, no como nodos hidráulicos confirmados. Colectores, red vial y topografía están ausentes.

## Qué puede hacerse ya

Puede depurarse la lista de orígenes, solicitar caudal/calidad a establecimientos prioritarios, conciliar duplicados de PTAR, verificar operación en campo y preparar criterios para adquirir red vial y elevación. También pueden levantarse receptores declarados y validar los nombres de cauces.

## Qué no puede afirmarse todavía

No puede afirmarse que exista una ruta factible, que funcione por gravedad, que una PTAR pueda recibir efluente textil, que un establecimiento use una descarga determinada, ni que el corredor más corto sea construible.

## Parte 3B — exploración de corredores candidatos sobre red vial

La siguiente etapa deberá usar como orígenes los establecimientos prioritarios verificados y, cuando sea apropiado, nodos agregados con caudal documentado. Los destinos serán PTAR conciliadas y verificadas o zonas nuevas definidas mediante criterios territoriales explícitos. Antes de optimizar se incorporarán una red vial topológicamente conectada, elevación por nodo, cruces de cauces, restricciones y costos.

Una futura función objetivo podría combinar longitud, pendiente adversa, necesidad de bombeo, número de cruces, jerarquía vial, restricciones territoriales, incertidumbre, costo unitario y capacidad compatible del destino. No debe ejecutarse hasta completar los componentes críticos marcados como ausentes en `matriz_prefactibilidad_red.csv`.
