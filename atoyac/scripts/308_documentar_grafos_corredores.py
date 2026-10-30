"""Documenta resultados y genera explorador local del grafo de Parte 3."""
from pathlib import Path
import json,hashlib,platform
import pandas as pd
import geopandas as gpd
import networkx as nx
import numpy as np
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/parte_3/10_grafos_corredores'
DOC_REPORT='02_grafos_corredores_exploratorios.md'

def markdown(df):
    cols=list(df.columns)
    lines=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
    for row in df.itertuples(index=False,name=None):lines.append('| '+' | '.join(str(v) for v in row)+' |')
    return '\n'.join(lines)

def xy(geometries):
    x=[];y=[]
    for g in geometries:
        if g.geom_type=='MultiLineString':parts=g.geoms
        else:parts=[g]
        for part in parts:
            coords=list(part.coords);x.extend([c[0] for c in coords]+[None]);y.extend([c[1] for c in coords]+[None])
    return x,y

def main():
    gp=OUT/'grafo_corredores_exploratorios.gpkg'
    t=pd.read_csv(OUT/'matriz_origen_destino.csv')
    alt=pd.read_csv(OUT/'alternativas_representativas.csv')
    g=gpd.read_file(gp,layer='corredores_compartidos')
    summary=json.loads((OUT/'resumen.json').read_text(encoding='utf-8'))
    connected=t[t.conectado].copy()
    assert len(t)==195 and len(connected)==102 and not t.duplicated(['origen_id','destino_id']).any()
    assert connected.longitud_con_accesos_m.ge(connected.longitud_vial_m).all()
    graph=nx.read_graphml(OUT/'grafo_vial.graphml')
    assert len(graph)==summary['nodos_con_accesos']
    assert graph.number_of_edges()==summary['aristas_con_accesos']
    metrics=connected.groupby(['destino_id','destino']).agg(origenes=('origen_id','nunique'),min_m=('longitud_con_accesos_m','min'),median_m=('longitud_con_accesos_m','median'),max_m=('longitud_con_accesos_m','max'),mdt_pct=('muestras_mdt_validas_pct','mean'),cruces_min=('elementos_hidrografia_intersectados','min'),cruces_max=('elementos_hidrografia_intersectados','max')).reset_index()
    metrics.to_csv(OUT/'comparacion_destinos_huejotzingo.csv',index=False,encoding='utf-8-sig')
    comp=[]
    for _,r in metrics.iterrows():
        shared=g[g.destino_id.eq(r.destino_id)]
        comp.append({'Destino':r.destino,'Origenes':int(r.origenes),
            'Longitud min/med/max (km)':f'{r.min_m/1000:.2f} / {r.median_m/1000:.2f} / {r.max_m/1000:.2f}',
            'Muestras MDT validas':f'{r.mdt_pct:.1f} %','Tramo compartido por 34 (km)':f'{shared[shared.n_origenes.eq(34)].longitud_m.sum()/1000:.2f}',
            'Elementos hidrograficos intersectados':f'{int(r.cruces_min)}–{int(r.cruces_max)}'})
    altview=alt.copy()
    altview['longitud_km']=(altview.longitud_vial_m/1000).round(3)
    altview['incremento_m']=(altview.longitud_vial_m-altview.groupby('destino_id').longitud_vial_m.transform('min')).round(1)
    altview['longitud_nueva_m']=altview.longitud_nueva_vs_minima_m.round(1)
    metadata=[]
    for p in [ROOT/'scripts/307_grafos_corredores_exploratorios.py',ROOT/'scripts/308_documentar_grafos_corredores.py',ROOT/'outputs/parte_3/09_foco_santa_ana_huejotzingo/foco_santa_ana_huejotzingo.gpkg',ROOT/'outputs/parte_3/08_integracion_vialidades_terreno/localidades_vialidades_terreno.gpkg']+sorted((ROOT/'data/raw/terreno').rglob('*_mt.bil')):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        metadata.append({'ruta':str(p.relative_to(ROOT)),'sha256':h.hexdigest(),'bytes':p.stat().st_size})
    (OUT/'manifest_reproducibilidad.json').write_text(json.dumps({'python':platform.python_version(),'networkx':nx.__version__,'geopandas':gpd.__version__,'fuentes':metadata},ensure_ascii=False,indent=2),encoding='utf-8')
    report='''# Grafos y corredores exploratorios: Santa Ana Xalmimilulco y Huejotzingo

## Resultado principal

La red descargada permite explorar rutas desde los 34 establecimientos prioritarios de Huejotzingo hasta las tres PTAR del núcleo. Los 31 prioritarios de Santa Ana están en otra componente: ninguno tiene ruta hacia esas plantas en los datos actuales. Esto demuestra un vacío de continuidad de la red disponible, no una imposibilidad territorial o hidráulica.

Entre los nodos de ambas componentes hay una separación mínima de 1,282 m. Es una línea de diagnóstico, NO una propuesta de colector ni la longitud de una calle faltante. No se unieron extremos ni se añadieron caminos supuestos. Hay que completar las vialidades interurbanas antes de comparar destinos desde Santa Ana.

## Alcance y método

- Se conserva el universo de 408 establecimientos: 337 Santa Ana y 71 Huejotzingo. Se enlazaron todos al grafo para diagnóstico; las rutas se calculan sólo para 65 prioritarios (31 Santa Ana, 34 Huejotzingo). Son reglas de prioridad productiva, no generación de caudal confirmada.
- Destinos: Cabecera Municipal (PTAR_066, asociado a 005), Paseo de los Sauces (067), Real Segovia (068). No se supone que operen o reciban efluente textil. Las plantas externas quedan fuera de esta primera comparación.
- Ventana de análisis: envolvente de establecimientos y destinos + 2.5 km. Se seleccionaron segmentos completos de los tres archivos viales regionales que intersectan esa ventana; una ruta exterior podría quedar fuera.
- Se usaron 3,412 tramos fuente. El grafo original tiene 6,605 nodos, 7,390 aristas y 82 componentes. Considerar cruces geométricos no redujo las 82 componentes del grafo construido con vértices originales.
- Se generó un grafo no dirigido, con longitud métrica como costo. El sentido vehicular no se usa como dirección hidráulica. Todos los tipos de vialidad se mantienen como candidatos, incluidos privados o peatonales, cuya disponibilidad constructiva no se acredita.
- Los cruces geométricos se consideran conectados: escenario permisivo pendiente de verificar puentes y pasos a desnivel. No se aplicaron tolerancias que unan brechas. Se conservaron atributos viales por proximidad del punto medio a la fuente; en tramos superpuestos esa asignación puede ser ambigua.
- Cada punto se proyecta sobre la arista más próxima y se divide la arista en ese lugar. Se conserva el punto original y un enlace geométrico independiente; no se atribuye una conexión sanitaria existente. Tras incorporar puntos de acceso resultan 7,006 nodos y 7,791 aristas.
- Los caminos mínimos se calculan sobre longitud vial. El total comparado suma dos accesos geométricos (establecimiento–calle y calle–PTAR). Los accesos no se someten a restricciones de propiedad o construcción.
- Los perfiles se muestrean cada 20 m y en ambos extremos sobre los dos MDT de 1.5 m, transformando al CRS nativo. No se usa MDS ni se rellenan vacíos. El perfil comienza y termina sobre la vialidad; no incluye accesos ni cota hidráulica de entrada a la planta. Una cobertura del 100 % de muestras no certifica cada píxel intermedio.

## Comparación de rutas desde Huejotzingo

'''+markdown(pd.DataFrame(comp))+'''

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

'''+markdown(altview[['destino_id','alternativa','longitud_km','incremento_m','longitud_nueva_m']])+'''

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
python scripts/307_grafos_corredores_exploratorios.py
python scripts/308_documentar_grafos_corredores.py
```

Validación: los 102 caminos recorren aristas existentes y sus longitudes geométricas coinciden con la suma de costos; ninguna ruta atraviesa componentes desconectadas. Matriz sin pares duplicados, longitudes totales no menores a la vial, geometrías revisadas y grafo GraphML reabierto con los conteos esperados. Estos controles verifican la implementación, no la veracidad de conexiones físicas.
'''
    gap_table=pd.read_csv(OUT/'brechas_componentes.csv')
    if not gap_table.empty:
        report=report.replace('1,282 m',f"{gap_table.distancia_brecha_m.min():,.0f} m")
    report=report.replace('3,412 tramos',f"{summary['tramos_fuente']:,} tramos").replace('6,605 nodos',f"{summary['nodos_grafo_original']:,} nodos").replace('7,390 aristas',f"{summary['aristas_grafo_original']:,} aristas")
    report=report.replace('82 componentes',f"{summary['componentes_nodando_cruces']} componentes").replace('las 82 componentes',f"las {summary['componentes_nodando_cruces']} componentes")
    report=report.replace('7,006 nodos',f"{summary['nodos_con_accesos']:,} nodos").replace('7,791 aristas',f"{summary['aristas_con_accesos']:,} aristas")
    (OUT/'reporte_grafos_corredores.md').write_text(report,encoding='utf-8')
    docs=ROOT/'docs/parte_3';docs.mkdir(parents=True,exist_ok=True)
    (docs/DOC_REPORT).write_text(report,encoding='utf-8')
    # Explorador sin teselas: coordenadas métricas y contenidos locales.
    edges=gpd.read_file(gp,layer='aristas_grafo');orig=gpd.read_file(gp,layer='establecimientos_prioritarios')
    plants=gpd.read_file(gp,layer='ptar_destinos');routes=gpd.read_file(gp,layer='rutas_minimas')
    alternatives=gpd.read_file(gp,layer='alternativas');gaps=gpd.read_file(gp,layer='brechas_no_conectadas')
    fig=go.Figure()
    for component,color,name in [(None,'#bbbbbb','Otras componentes'),(0,'#1b9e77','Red Huejotzingo/PTAR'),(1,'#7570b3','Red Santa Ana')]:
        subset=edges[~edges.componente.isin([0,1])] if component is None else edges[edges.componente.eq(component)]
        x,y=xy(subset.geometry);fig.add_trace(go.Scattergl(x=x,y=y,mode='lines',line=dict(color=color,width=1),name=name,hoverinfo='skip'))
    fig.add_trace(go.Scattergl(x=orig.geometry.x,y=orig.geometry.y,mode='markers',marker=dict(size=6,color='#333333'),text=orig.establecimiento_id+' | '+orig.zona_analisis+' | '+orig.prioridad_ambiental,name='65 origenes prioritarios',hovertemplate='%{text}<extra></extra>'))
    fig.add_trace(go.Scattergl(x=plants.geometry.x,y=plants.geometry.y,mode='markers+text',marker=dict(size=14,color='red',symbol='triangle-up'),text=plants.nombre_fuente,textposition='top center',name='3 PTAR candidatas'))
    x,y=xy(gaps.geometry);fig.add_trace(go.Scatter(x=x,y=y,mode='lines',line=dict(color='red',width=3,dash='dash'),name='Brecha: NO es camino'))
    for _,d in plants.iterrows():
        subset=routes[routes.destino_id.eq(d.ptar_id)];x,y=xy(subset.geometry)
        fig.add_trace(go.Scattergl(x=x,y=y,mode='lines',line=dict(width=2),name='Rutas: '+d.nombre_fuente,visible='legendonly',hoverinfo='name'))
        subset=alternatives[(alternatives.destino_id==d.ptar_id)&(alternatives.alternativa==2)];x,y=xy(subset.geometry)
        fig.add_trace(go.Scatter(x=x,y=y,mode='lines',line=dict(width=3,dash='dot'),name='Desvio EST_03059: '+d.nombre_fuente,visible='legendonly',hoverinfo='name'))
    fig.update_layout(title='Santa Ana–Huejotzingo: grafo y corredores exploratorios<br><sup>Activa rutas y desvíos en la leyenda. La brecha roja no conecta las redes. No acredita viabilidad hidráulica.</sup>',template='plotly_white',height=850,legend=dict(orientation='h',y=-.12),margin=dict(b=180),xaxis_title='Este UTM (m), EPSG:32614',yaxis_title='Norte UTM (m), EPSG:32614')
    fig.update_yaxes(scaleanchor='x',scaleratio=1)
    fig.write_html(OUT/'explorador_grafos.html',include_plotlyjs=True,full_html=True)
    print(metrics.to_string(index=False));print('Reporte y explorador generados. Validaciones correctas.')

if __name__=='__main__':main()
