"""Informe ilustrado: interpretación de caminos mínimos individuales frente a red conjunta."""
from pathlib import Path
import textwrap,json,hashlib
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'outputs/parte_3/12_vialidades_amplias'
OUT=ROOT/'docs/parte_3/explicacion_caminos_minimos'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
BLUE='#194a68';PURPLE='#7452a0';GREEN='#278569';ORANGE='#cc6935'

def page(title,subtitle=''):
    fig=plt.figure(figsize=(8.27,11.69),facecolor='white')
    fig.text(.07,.95,title,fontsize=18,fontweight='bold',color=BLUE,va='top')
    if subtitle:fig.text(.07,.912,subtitle,fontsize=10,color='#555555',va='top')
    return fig

def para(fig,text,y,x=.07,width=103,size=10,color='#222222'):
    lines=textwrap.wrap(text,width=width,break_long_words=False,break_on_hyphens=False)
    fig.text(x,y,'\n'.join(lines),fontsize=size,color=color,va='top',linespacing=1.45)
    return y-len(lines)*.0175-.016

def heading(fig,text,y):
    fig.text(.07,y,text,fontsize=12,fontweight='bold',color=BLUE,va='top')
    return y-.032

def footer(fig,n):
    fig.text(.07,.028,'Alto Atoyac | Parte 3 | Resultados exploratorios de vialidad y terreno',fontsize=7,color='#666666')
    fig.text(.93,.028,str(n),ha='right',fontsize=8,color='#666666')

def save(pdf,fig,n):
    footer(fig,n);pdf.savefig(fig);fig.savefig(OUT/f'pagina_{n:02d}.png',dpi=130);plt.close(fig)

def mapbase(ax,roads,extent):
    roads.plot(ax=ax,color='#d3d3d3',linewidth=.4)
    x0,y0,x1,y1=extent;ax.set_xlim(x0-250,x1+250);ax.set_ylim(y0-250,y1+250)
    ax.set_aspect('equal');ax.tick_params(labelsize=7);ax.ticklabel_format(style='plain',useOffset=False)
    ax.set_xlabel('Este UTM (m)',fontsize=8);ax.set_ylabel('Norte UTM (m)',fontsize=8)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    matrix=pd.read_csv(DATA/'matriz_origen_destino.csv');connected=matrix[matrix.conectado].copy()
    gp=DATA/'grafo_corredores_exploratorios.gpkg'
    routes=gpd.read_file(gp,layer='rutas_minimas');corridors=gpd.read_file(gp,layer='corredores_compartidos')
    est=gpd.read_file(ROOT/'outputs/parte_3/09_foco_santa_ana_huejotzingo/foco_santa_ana_huejotzingo.gpkg',layer='establecimientos_foco')
    plants=gpd.read_file(gp,layer='ptar_destinos');roads=gpd.read_file(gp,layer='vialidades_fuente')
    origins=est[(est.zona_analisis=='huejotzingo')&est.prioridad_ambiental.isin(['alta','media'])]
    aa=connected[connected.destino_id.eq('PTAR_067')].sort_values('longitud_vial_m')
    pick=aa.iloc[[0,16,-1]];ids=pick.ruta_id.tolist();palette=[GREEN,PURPLE,ORANGE]
    summary=connected.groupby(['destino_id','destino']).longitud_vial_m.agg(['size','min','median','max']).reset_index()
    targetpdf=OUT/'explicacion_caminos_minimos.pdf'
    with PdfPages(targetpdf,metadata={'Title':'Qué representan los caminos mínimos de Santa Ana y Huejotzingo','Subject':'Caminos individuales, corredores compartidos y límites del análisis','Author':'Proyecto Alto Atoyac'}) as pdf:
        fig=page('¿Qué representan las distancias?','Respuesta: caminos individuales desde cada establecimiento hasta un destino fijo.')
        y=para(fig,'Cada fila corresponde a UN establecimiento y UNA planta. El algoritmo busca el camino vial más corto entre esos dos puntos. Repetimos el cálculo para cada establecimiento y para cada una de las tres plantas.',.865)
        y=heading(fig,'La tabla resume muchos caminos individuales',y)
        y=para(fig,'Ejemplo: para Paseo de los Sauces calculamos 34 caminos desde Huejotzingo. El mínimo de 2.404 km corresponde al establecimiento más cercano por la red; la mediana es 4.146 km y el máximo 5.221 km. No son tres longitudes de un mismo colector.',y)
        ax=fig.add_axes([.09,.31,.82,.29]);ax.set_xlim(0,10);ax.set_ylim(0,6);ax.axis('off')
        points={'A':(1,5),'B':(1,3),'C':(1,1),'U':(4,3),'V':(6.5,3),'P':(9,3)}
        for a,b in [('A','U'),('B','U'),('C','U'),('U','V'),('V','P')]:
            x1,y1=points[a];x2,y2=points[b];ax.plot([x1,x2],[y1,y2],color='#aaaaaa',lw=5,zorder=1)
        for name,color,dy in [('A',GREEN,.09),('B',PURPLE,0),('C',ORANGE,-.09)]:
            seq=[points[name],points['U'],points['V'],points['P']]
            ax.plot([p[0] for p in seq],[p[1]+dy for p in seq],lw=1.8,color=color)
            ax.scatter(*points[name],s=100,color=color,zorder=3);ax.text(.2,points[name][1],name,fontsize=12,fontweight='bold')
        ax.scatter(*points['P'],marker='^',s=200,color='#bd2638',zorder=4);ax.text(8.4,3.5,'PTAR',fontsize=12,fontweight='bold')
        ax.text(5.1,2.3,'tramos compartidos',ha='center',fontsize=10)
        ax.text(5,-.15,'Esquema conceptual: A→PTAR, B→PTAR y C→PTAR son cálculos separados.',ha='center',fontsize=9,color='#555555')
        y=heading(fig,'¿Pasa por todos los prioritarios?',.265)
        y=para(fig,'No se impuso visitar todos los establecimientos. Un camino puede coincidir con otro y pasar cerca de otros puntos, pero eso no demuestra que los atienda o reciba su descarga.',y)
        y=para(fig,'Para proponer un colector que reúna aportaciones de varios establecimientos necesitamos optimizar una RED conjunta, normalmente ramificada. La unión de caminos mínimos que mostramos es una base exploratoria; no garantiza la menor longitud o costo de una red común.',y)
        save(pdf,fig,1)

        fig=page('Cómo leer los resultados de Huejotzingo','34 establecimientos prioritarios × 3 plantas = 102 caminos individuales.')
        para(fig,'Estas longitudes recorren las calles. Los accesos geométricos desde el establecimiento a la calle y desde la calle a la planta se guardaron aparte. Tampoco son distancias en línea recta.',.865)
        ax=fig.add_axes([.07,.655,.86,.14]);ax.axis('off')
        rows=[]
        for _,r in summary.iterrows():rows.append([r.destino_id,r.destino.replace('PLANTA DE LA CABECERA MUNICIPAL','Cabecera Municipal').title(),int(r['size']),f'{r["min"]/1000:.3f}',f'{r["median"]/1000:.3f}',f'{r["max"]/1000:.3f}'])
        tab=ax.table(cellText=rows,colLabels=['Destino','Planta','Rutas','Mín. km','Med. km','Máx. km'],loc='center',cellLoc='center',colWidths=[.14,.30,.10,.15,.15,.15])
        tab.auto_set_font_size(False);tab.set_fontsize(8);tab.scale(1,1.7)
        for (row,col),cell in tab.get_celld().items():
            cell.set_edgecolor('#dddddd')
            if row==0:cell.set_facecolor(BLUE);cell.set_text_props(color='white',fontweight='bold')
        ax=fig.add_axes([.16,.17,.75,.43]);vals=aa.longitud_vial_m.to_numpy()/1000
        ax.barh(np.arange(len(aa)),vals,color='#73a89b');ax.invert_yaxis()
        ax.set_yticks(np.arange(len(aa)));ax.set_yticklabels(aa.origen_id,fontsize=6)
        median=float(aa.longitud_vial_m.median()/1000);ax.axvline(median,color=ORANGE,linestyle='--',label=f'Mediana {median:.3f} km')
        ax.set_xlabel('Longitud vial del camino individual a Paseo de los Sauces (km)')
        ax.set_title('Cada barra es un establecimiento distinto',fontsize=11);ax.legend(fontsize=8);ax.grid(axis='x',alpha=.2)
        para(fig,'El mínimo no es “el mejor colector”: identifica el menor de los 34 caminos. Cada barra ya es el camino mínimo de su propio origen a esa planta, bajo el costo de distancia utilizado.',.115,size=9,width=112)
        save(pdf,fig,2)

        fig=page('Tres ejemplos reales hacia la misma planta','Destino: Paseo de los Sauces (PTAR_067). Las líneas muestran recorridos individuales.')
        extent=routes[routes.destino_id.eq('PTAR_067')].total_bounds
        ax=fig.add_axes([.11,.31,.78,.55]);mapbase(ax,roads,extent)
        origins.plot(ax=ax,color='#777777',markersize=10,alpha=.5)
        legends=[]
        for (_,r),color in zip(pick.iterrows(),palette):
            route=routes[routes.ruta_id.eq(r.ruta_id)];route.plot(ax=ax,color=color,linewidth=2)
            o=est[est.establecimiento_id.eq(r.origen_id)];o.plot(ax=ax,color=color,markersize=50)
            legends.append(Line2D([0],[0],color=color,lw=2,label=f'{r.origen_id}: {r.longitud_vial_m/1000:.3f} km'))
        plant=plants[plants.ptar_id.eq('PTAR_067')];plant.plot(ax=ax,color='#bd2638',marker='^',markersize=100)
        legends.append(Line2D([0],[0],marker='^',color='#bd2638',linestyle='',label='Paseo de los Sauces'))
        ax.legend(handles=legends,fontsize=7,loc='lower left')
        y=.265
        names=est.set_index('establecimiento_id').nombre
        for label,(_,r) in zip(['Menor longitud','Cercano a la mediana','Mayor longitud'],pick.iterrows()):
            y=para(fig,f'{label}: {r.origen_id}, {names.loc[r.origen_id]}; {r.longitud_vial_m/1000:.3f} km.',y,size=9,width=112)
        para(fig,'Los tres ejemplos terminan en la misma planta. No deben encadenarse: representan orígenes alternativos e independientes. El origen cercano a la mediana es un ejemplo real, no la mediana estadística exacta.',y,size=9,width=112)
        save(pdf,fig,3)

        fig=page('Qué significan los corredores compartidos','Contamos cuántos caminos individuales utilizan cada tramo hacia un mismo destino.')
        ax=fig.add_axes([.11,.32,.78,.55]);mapbase(ax,roads,extent)
        shared=corridors[corridors.destino_id.eq('PTAR_067')]
        shared.plot(ax=ax,column='n_origenes',cmap='viridis',linewidth=.5+4*shared.n_origenes/34,legend=True,legend_kwds={'label':'Caminos que comparten el tramo','shrink':.65})
        origins.plot(ax=ax,color='#444444',markersize=10);plant.plot(ax=ax,color='#bd2638',marker='^',markersize=100)
        all34=float(shared[shared.n_origenes.eq(34)].longitud_m.sum()/1000)
        union=float(shared.longitud_m.sum()/1000)
        summed=float(aa.longitud_vial_m.sum()/1000)
        y=para(fig,f'Hacia Paseo de los Sauces, {all34:.2f} km de tramos son utilizados por los 34 caminos. La suma de las 34 distancias es {summed:.2f} km, mientras que la unión geométrica de sus aristas suma {union:.2f} km.',.275)
        y=para(fig,'Sumar las distancias individuales cuenta repetidas veces los tramos compartidos. La unión cuenta cada arista una sola vez; aun así, puede no ser la red conjunta de menor costo.',y)
        para(fig,'Los corredores permiten localizar dónde revisar un posible tronco colector. El grosor y el color representan número de caminos, no caudal, diámetro o capacidad. Los destinos son escenarios separados; no se suman las tres plantas como si recibieran simultáneamente las mismas aportaciones.',y,size=9,width=112)
        save(pdf,fig,4)

        fig=page('Santa Ana: qué se calculó y qué falta','Los 62 recorridos internos no llegan a plantas de tratamiento.')
        y=para(fig,'Los 31 establecimientos prioritarios no tienen camino continuo hacia las tres PTAR en la red disponible. Comprobamos también las 50,212 geometrías de la red regional completa: la desconexión persiste.',.865)
        y=para(fig,'Para avanzar dentro de Santa Ana calculamos 31 caminos a EXT_01 y 31 a EXT_02. Son extremos de calles existentes seleccionados para inspección, no plantas, descargas ni enlaces sanitarios confirmados.',y)
        ax=fig.add_axes([.07,.32,.86,.40]);ax.imshow(plt.imread(DATA/'06_santa_ana_corredores.png'));ax.axis('off')
        y=.285
        y=para(fig,'EXT_01: longitudes de 1.506 a 3.863 km; mediana 2.697 km. La cobertura media de MDT es 67.9 %. EXT_02: de 1.035 a 3.404 km; mediana 2.512 km y cobertura media de MDT de 99.7 %.',y)
        y=para(fig,'Estos resultados sirven para comparar recorridos internos y preparar inspecciones. No permiten elegir una planta para Santa Ana ni afirmar que un único camino recoge todos sus establecimientos.',y)
        para(fig,'La separación de aproximadamente 990 m entre las dos componentes principales es un diagnóstico geométrico. Hay calles aisladas intermedias; no equivale a la longitud exacta de un colector o una calle faltante.',y,size=9,width=112)
        save(pdf,fig,5)

        fig=page('Método, pendiente y siguiente análisis','El cálculo actual minimiza distancia vial; la pendiente se revisa después.')
        y=.865
        for title,body in [
            ('1. Grafo vial','Nodos en vértices y cruces; aristas en tramos de calle. Grafo no dirigido, con longitud en metros como costo. Los pasos a desnivel y la posibilidad de usar calles privadas requieren verificación.'),
            ('2. Accesos y Dijkstra','Cada punto se proyecta a su arista más próxima. Dijkstra calcula el camino mínimo entre el establecimiento y una planta fija. El enlace de acceso se conserva separado y no acredita conexión sanitaria.'),
            ('3. Perfiles de terreno','Se consulta el MDT original de 1.5 m cada 20 m del camino. Se calcula pendiente longitudinal por intervalos de 100 m cuando toda la traza del intervalo tiene cobertura. Los mapas de pendiente superficial se agregan a 15 m para visualización.'),
            ('4. Interpretación hidráulica','Los caminos hacia Cabecera y Paseo tienen terreno disponible en toda su traza y descenso global, pero también subidas locales. Hacia Real Segovia falta alrededor de 24 % del MDT. La pendiente no interviene todavía como costo o restricción del grafo.'),
            ('5. Si queremos atender a todos los prioritarios','El siguiente problema es diseñar una red común hacia una planta: elegir ramales y tronco compartido, asignar aportaciones y comparar longitud única, costos, cruces, excavación, cotas y capacidad de tratamiento. Ese problema todavía no se resolvió con los caminos individuales.')]:
            y=heading(fig,title,y);y=para(fig,body,y,size=9,width=112)
        y=heading(fig,'Qué entregan los archivos actuales',y)
        y=para(fig,'matriz_origen_destino.csv: 195 pares evaluados; 102 con ruta y 93 sin ruta. caminos_minimos_calculados.csv: 164 caminos realmente calculados (102 hacia PTAR y 62 internos de Santa Ana). Las geometrías están en rutas_minimas y rutas_locales_santa_ana del GeoPackage.',y,size=9,width=112)
        para(fig,'Reproducción de este informe: python scripts/313_explicar_caminos_minimos_pdf.py, desde atoyac. Fuentes: paquete outputs/parte_3/12_vialidades_amplias. Las longitudes y ejemplos fueron extraídos directamente de esos resultados.',y,size=8,width=125)
        save(pdf,fig,6)
    info={'paginas':6,'rutas_hacia_ptar':len(routes),'rutas_ptar_067':len(aa),'ejemplos_reales':pick[['ruta_id','origen_id','longitud_vial_m']].to_dict('records'),
        'suma_distancias_ptar_067_km':summed,'union_aristas_ptar_067_km':union,'tramos_compartidos_34_km':all34,
        'pdf_sha256':hashlib.sha256(targetpdf.read_bytes()).hexdigest()}
    assert len(routes)==102 and len(aa)==34 and targetpdf.stat().st_size>100000
    (OUT/'datos_informe.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'README.md').write_text('''# Interpretación ilustrada de caminos mínimos

Abrir [PDF de seis páginas](explicacion_caminos_minimos.pdf). Cada página también se guarda como PNG.

Son caminos individuales de un establecimiento a un destino fijo, calculados con Dijkstra por longitud vial. El mínimo de la tabla es el menor de esos caminos individuales. No se optimizó una ruta que visite todos los establecimientos ni una red conjunta de colectores.

Se muestran ejemplos reales, corredores compartidos, diferencia entre sumar distancias y unir aristas, recorridos internos de Santa Ana y límites de la elevación. Reproducir desde atoyac: `python scripts/313_explicar_caminos_minimos_pdf.py`.
''',encoding='utf-8')
    print(json.dumps(info,ensure_ascii=False,indent=2));print(targetpdf.resolve())

if __name__=='__main__':main()
