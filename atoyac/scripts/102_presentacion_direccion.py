"""Presentación integrada de resultados y procedimiento; no modifica universos."""
from pathlib import Path
import subprocess
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
ASSETS = DOCS / 'direccion_imagenes'
ASSETS.mkdir(exist_ok=True)
MODOS = [('Sectorial', '_todos_scian'), ('Amplio DENUE', '_sin_mh'),
         ('Amplio + MH', ''), ('Estricto DENUE', '_estricto_sin_mh'),
         ('Estricto + MH', '_estricto_mh')]
bases = {n: ROOT / ('outputs/cuenca_alto_atoyac_puebla' + s) for n, s in MODOS}
datos = {n: pd.read_csv(p / 'tables/universo_hidrico_dentro_cuenca.csv', dtype=str).fillna('') for n,p in bases.items()}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12})

def guardar(fig, nombre):
    fig.savefig(ASSETS / nombre, dpi=180, bbox_inches='tight')
    plt.close(fig)

fig, ax = plt.subplots(figsize=(11,4))
ns = [len(datos[n]) for n,_ in MODOS]
ax.barh([n for n,_ in MODOS], ns, color=['#8798a5','#d6a347','#bf8041','#3a87ad','#185879'])
for i,v in enumerate(ns): ax.text(v+30,i,f'{v:,}',va='center')
ax.set_xlim(0,4500); ax.set_xlabel('Establecimientos dentro del recorte de cuenca'); ax.invert_yaxis()
ax.spines[['top','right']].set_visible(False)
guardar(fig,'modalidades.png')

fig, ax = plt.subplots(figsize=(11,4))
top = datos['Amplio + MH'].Municipio.value_counts().head(7).index
tabla = pd.DataFrame({n: datos[n].Municipio.value_counts().reindex(top,fill_value=0) for n in ['Amplio + MH','Estricto + MH']})
tabla.plot.barh(ax=ax,color=['#d6a347','#185879']); ax.invert_yaxis(); ax.set_xlabel('Establecimientos'); ax.set_ylabel('')
guardar(fig,'municipios.png')

cuenca = gpd.read_file(ROOT/'data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_cuenca_alto_atoyac_21_reg_a.gpkg').to_crs(4326)
rios = gpd.clip(gpd.read_file(ROOT/'data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_red_hidro_digital_06_reg_l.gpkg').to_crs(4326),cuenca)
fig, axs = plt.subplots(1,2,figsize=(12,6))
for ax,n in zip(axs,['Amplio + MH','Estricto + MH']):
    d=datos[n]; puntos=gpd.GeoDataFrame(d,geometry=gpd.points_from_xy(pd.to_numeric(d.Longitud,errors='coerce'),pd.to_numeric(d.Latitud,errors='coerce')),crs=4326)
    # Los suplementarios MH tienen coordenadas en la capa, no en las columnas DENUE.
    puntos=gpd.read_file(bases[n]/'layers/universo_hidrico_dentro_cuenca.gpkg').to_crs(4326)
    cuenca.plot(ax=ax,color='#f3f1e9',edgecolor='#455566',linewidth=.7)
    rios.plot(ax=ax,color='#91b9ce',linewidth=.35)
    puntos[puntos.fuente_evidencia_hidrica.eq('REGLAS_DENUE')].plot(ax=ax,color='#b7863b',markersize=3,alpha=.65,label='Reglas DENUE')
    puntos[puntos.fuente_evidencia_hidrica.eq('MH_TRABAJO_CAMPO')].plot(ax=ax,color='#b52e4b',markersize=10,label='Fuente MH')
    ax.set_title(f'{n}: {len(d):,}'); ax.set_axis_off(); ax.legend(loc='lower left',fontsize=9)
guardar(fig,'mapas_comparables.png')

# Comparaciones nuevas: misma extensión, escala absoluta común y porcentaje.
municipios_geo = gpd.read_file(ROOT/'data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_division_municipal_20_mun_a.gpkg').to_crs(4326)
municipios_geo = gpd.clip(municipios_geo[municipios_geo.nom_ent.eq('Puebla')], cuenca).reset_index(drop=True)
capas = {n: gpd.read_file(bases[n]/'layers/universo_hidrico_dentro_cuenca.gpkg').to_crs(4326) for n,_ in MODOS}
def conteo_espacial(puntos):
    asignados = gpd.sjoin(puntos[['geometry']], municipios_geo[['geometry']], how='left', predicate='within')
    return asignados.index_right.value_counts().reindex(municipios_geo.index,fill_value=0).astype(int)
conteos = {n: conteo_espacial(p) for n,p in capas.items()}
limite = max(int(c.max()) for c in conteos.values())
limite_pct = max(float(c.max()/len(capas[n])*100) for n,c in conteos.items())

def fondo(ax):
    municipios_geo.boundary.plot(ax=ax,color='#8d969c',linewidth=.45)
    rios.plot(ax=ax,color='#90b7d0',linewidth=.25,alpha=.65)
    x0,y0,x1,y1=cuenca.total_bounds
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_axis_off()

def coropleta(ax, valores, maximo):
    base=municipios_geo.copy(); base['valor']=valores
    base.plot(ax=ax,column='valor',cmap='YlOrRd',vmin=0,vmax=maximo,edgecolor='#aaa',linewidth=.45)
    fondo(ax)

for i,(n,_) in enumerate(MODOS):
    fig,axs=plt.subplots(1,2,figsize=(12,5.8))
    municipios_geo.plot(ax=axs[0],color='#f5f3ee',edgecolor='#aaa',linewidth=.4)
    capas[n].plot(ax=axs[0],color='#185879',markersize=3,alpha=.55)
    fondo(axs[0]); axs[0].set_title(f'Distribución: {len(capas[n]):,} registros')
    coropleta(axs[1],conteos[n],limite); axs[1].set_title('Concentración municipal (conteo)')
    fig.colorbar(ScalarMappable(norm=Normalize(0,limite),cmap='YlOrRd'),ax=axs[1],shrink=.72,label='Establecimientos')
    guardar(fig,f'comparacion_modo_{i}.png')

for porcentajes,nombre in [(False,'panel_conteos.png'),(True,'panel_participacion.png')]:
    fig,axs=plt.subplots(1,5,figsize=(17,5))
    for ax,(n,_) in zip(axs,MODOS):
        valores=conteos[n]/len(capas[n])*100 if porcentajes else conteos[n]
        coropleta(ax,valores,limite_pct if porcentajes else limite)
        ax.set_title(n+'\n'+f'n = {len(capas[n]):,}',fontsize=11)
    fig.colorbar(ScalarMappable(norm=Normalize(0,limite_pct if porcentajes else limite),cmap='YlOrRd'),ax=list(axs),shrink=.65,label='% del universo' if porcentajes else 'Establecimientos')
    guardar(fig,nombre)

matriz=pd.DataFrame({n: conteos[n].values for n,_ in MODOS},index=municipios_geo.nom_mun)
matriz=matriz.loc[matriz.sum(axis=1).sort_values(ascending=False).index]
fig,ax=plt.subplots(figsize=(12,7))
im=ax.imshow(np.log1p(matriz.values),cmap='YlOrRd',aspect='auto')
ax.set_xticks(range(5),matriz.columns,rotation=15,ha='right'); ax.set_yticks(range(len(matriz)),matriz.index)
for fila in range(len(matriz)):
    for col in range(5):
        v=int(matriz.iloc[fila,col]); ax.text(col,fila,str(v),ha='center',va='center',fontsize=9,color='white' if np.log1p(v)>np.log1p(limite)*.65 else '#222')
ax.set_title('Concentración municipal: conteos comparables'); fig.colorbar(im,ax=ax,label='Color = log(1 + conteo); cifras = conteos reales')
guardar(fig,'matriz_municipal.png')
matriz.to_csv(ASSETS/'concentracion_municipal_5_modalidades.csv',encoding='utf-8-sig')

amplio=capas['Amplio DENUE']; ids_estricto=set(capas['Estricto DENUE'].d_llave.astype(str))
comerciales=amplio[amplio.cve_scian.astype(str).eq('812210') & ~amplio.d_llave.astype(str).isin(ids_estricto)].copy()
conteo_comerciales=conteo_espacial(comerciales)
fig,axs=plt.subplots(1,2,figsize=(12,5.8))
coropleta(axs[0],conteo_comerciales,max(1,int(conteo_comerciales.max())))
axs[0].set_title('Posibles comerciales: concentración municipal')
fig.colorbar(ScalarMappable(norm=Normalize(0,max(1,int(conteo_comerciales.max()))),cmap='YlOrRd'),ax=axs[0],shrink=.7,label='Registros')
municipios_geo.plot(ax=axs[1],color='#f5f3ee',edgecolor='#aaa',linewidth=.4)
comerciales.plot(ax=axs[1],color='#b52e4b',markersize=5,alpha=.6); fondo(axs[1]); axs[1].set_title(f'Ubicaciones: {len(comerciales):,} registros')
guardar(fig,'posibles_comerciales.png')
ranking=comerciales.Municipio.value_counts()
fig,ax=plt.subplots(figsize=(11,4))
ranking.head(8).sort_values().plot.barh(ax=ax,color='#b52e4b')
for j,v in enumerate(ranking.head(8).sort_values()): ax.text(v+5,j,f'{v:,} ({100*v/len(comerciales):.1f}%)',va='center',fontsize=10)
ax.set_xlim(0,ranking.max()*1.35); ax.set_xlabel('Registros sin señal adicional, descartados por el estricto'); ax.set_ylabel('')
guardar(fig,'ranking_comerciales.png')
comerciales.drop(columns='geometry').to_csv(ASSETS/'posibles_comerciales_amplio_menos_estricto.csv',index=False,encoding='utf-8-sig')

estratos=['0 a 5 personas','6 a 10 personas']
resumen_pequenas=[]
for e,estrato in enumerate(estratos):
    seleccion={n:p[p['Descripcion estrato personal ocupado'].fillna('').eq(estrato)] for n,p in capas.items()}
    cuenta={n:conteo_espacial(p) for n,p in seleccion.items()}
    max_e=max(1,max(int(c.max()) for c in cuenta.values()))
    fig,axs=plt.subplots(1,5,figsize=(17,5))
    for ax,(n,_) in zip(axs,MODOS):
        coropleta(ax,cuenta[n],max_e)
        ax.set_title(n+'\n'+f'n = {len(seleccion[n]):,}',fontsize=11)
    fig.colorbar(ScalarMappable(norm=Normalize(0,max_e),cmap='YlOrRd'),ax=list(axs),shrink=.65,label=f'Establecimientos: {estrato}')
    guardar(fig,f'pequenas_panel_{e}.png')
    for i,(n,_) in enumerate(MODOS):
        p=seleccion[n]
        fig,axs=plt.subplots(1,2,figsize=(12,5.8))
        municipios_geo.plot(ax=axs[0],color='#f5f3ee',edgecolor='#aaa',linewidth=.4)
        if len(p): p.plot(ax=axs[0],color='#185879',markersize=5,alpha=.6)
        fondo(axs[0]); axs[0].set_title(f'{estrato}: {len(p):,} ubicaciones')
        coropleta(axs[1],cuenta[n],max_e); axs[1].set_title('Concentración municipal')
        fig.colorbar(ScalarMappable(norm=Normalize(0,max_e),cmap='YlOrRd'),ax=axs[1],shrink=.72,label='Establecimientos')
        guardar(fig,f'pequenas_{e}_modo_{i}.png')
        resumen_pequenas.append({'modalidad':n,'estrato':estrato,'n':len(p),'porcentaje_universo':100*len(p)/len(capas[n])})
    pd.DataFrame({n:cuenta[n].values for n,_ in MODOS},index=municipios_geo.nom_mun).to_csv(ASSETS/f'concentracion_pequenas_{e}.csv',encoding='utf-8-sig')
pd.DataFrame(resumen_pequenas).to_csv(ASSETS/'resumen_pequenas_5_modalidades.csv',index=False,encoding='utf-8-sig')

def esc(t):
    return ''.join({'&':r'\&','%':r'\%','_':r'\_','#':r'\#','$':r'\$'}.get(c,c) for c in str(t))
frames=[]
def slide(t, bullets):
    frames.append('\\begin{frame}{'+esc(t)+'}\n\\small\n\\begin{itemize}\n'+''.join('\\item '+esc(b)+'\n' for b in bullets)+'\\end{itemize}\n\\end{frame}\n')
def imagen(t, archivo, nota):
    frames.append('\\begin{frame}{'+esc(t)+'}\n\\centering\\includegraphics[width=.97\\textwidth,height=.72\\textheight,keepaspectratio]{'+archivo+'}\n\\par\\scriptsize '+esc(nota)+'\n\\end{frame}\n')
def tabla_slide(t, headers, rows, nota=''):
    frames.append('\\begin{frame}{'+esc(t)+'}\\centering\\scriptsize\n\\begin{tabular}{'+('l'*len(headers))+'}\\toprule\n'+' & '.join(map(esc,headers))+r'\\\midrule'+'\n'+''.join(' & '.join(map(esc,r))+r'\\'+'\n' for r in rows)+r'\bottomrule\end{tabular}'+'\n\\par\\medskip '+esc(nota)+'\\end{frame}\n')

slide('Qué entrega este estudio a dirección',[
'Un marco territorial reproducible para localizar establecimientos potencialmente relevantes y orientar la fase enfocada en lavanderías industriales.',
'Cinco modalidades permiten observar cuánto depende el resultado del filtro de lavanderías y de la integración de información MH.',
'El marco permite comparar cobertura, distribución y concentración de establecimientos según los criterios de selección.',
'Los conteos describen candidatos y evidencia disponible; no estiman consumo, descarga ni contaminación.'])
slide('Hallazgos que cambian la decisión',[
'El escenario amplio DENUE contiene 1,679 candidatos; el estricto DENUE, 469. La regla de lavanderías cambia 1,210 registros.',
'MH incorpora 38 registros al amplio y 41 al estricto; su aporte es localizado y recupera casos que las reglas no retienen.',
'El escenario estricto con MH reúne 510 candidatos; 419 quedan en REVISAR y 91 en SI bajo las etiquetas actuales.',
'Recomendación: usar estricto + MH para priorizar, acompañado del amplio para mostrar sensibilidad y conservando la procedencia de cada registro.'])
slide('Alcance: territorio, fecha y denominador',[
'Fuente estatal del flujo actual: INEGI_DENUE_11092026.csv; 15,956 registros descargados. El nombre del archivo indica la fecha de descarga, no demuestra la fecha de observación de cada registro.',
'La descarga es sectorial (carpeta 313-314-315-81); no representa todas las actividades económicas de Puebla.',
'Se seleccionan 26 municipios por nombre normalizado; 24 tienen candidatos en las tablas de cobertura.',
'Después se intersectan puntos con el polígono de cuenca. Cada cifra comparativa principal usa este mismo recorte dentro de la cuenca.',
'El alcance es el territorio trabajado de Puebla. No se debe presentar como inventario de toda la cuenca en ambos estados.'])
imagen('Territorio y red hidrográfica','../outputs/cuenca_alto_atoyac_puebla_estricto_mh/maps/png/01_cuenca_informacion_hidrica.png','Fuente: capas de cuenca, municipios y red hidrográfica incluidas en el proyecto; mapa del flujo 08.')
slide('Arquitectura completa del procedimiento',[
'1. Leer y normalizar DENUE; validar columnas e identificadores; construir puntos.',
'2. Ejecutar por separado filtro SCIAN y filtro textual; unir identificadores sin duplicar establecimientos.',
'3. Interpretar señales y asignar decisión sectorial y evidencia hídrica, como dimensiones distintas.',
'4. Seleccionar municipios; aplicar el corte hídrico de la modalidad; guardar el resultado previo a MH.',
'5. Integrar MH cuando corresponde; recortar puntos por cuenca; calcular distancia y agregaciones.',
'6. Exportar tablas CSV, capas GPKG, mapas PNG/HTML e inventarios. Esta presentación reutiliza esas salidas y añade comparaciones.'])
slide('Proceso 1: lectura, normalización y controles',[
'El flujo estatal lee el CSV como texto con codificación cp1252 y sustituye nulos por cadenas vacías.',
'Normaliza acentos en encabezados y renombra ID, nombre, razón social, SCIAN y localidad a los campos internos.',
'Exige ID, nombre, razón social, código y descripción SCIAN, municipio, localidad, latitud, longitud y estrato de personal.',
'Rechaza identificadores duplicados; elimina espacios exteriores de los campos clave.',
'Convierte longitud y latitud a números, construye puntos en EPSG:4326 y comprueba geometrías nulas.',
'Límite del control actual: no incorpora una comprobación explícita de rangos geográficos, vigencia de operación o coordenadas plausibles para Puebla.'])
slide('Proceso 2A: filtro estructurado SCIAN',[
'Normaliza el código como texto, elimina el sufijo .0 y espacios.',
'Retiene códigos que comienzan con 313, 314, 315 o 812210. El operador es coincidencia de prefijo.',
'Los prefijos 313/314/315 definen contexto sectorial textil en las reglas; no prueban proceso húmedo.',
'El código exacto 313310 genera la señal scian_acabado_humedo; el exacto 812210 genera scian_lavanderia.',
'812210 no distingue por sí solo lavandería comercial de lavandería industrial.',
'El filtro solo puede recuperar establecimientos presentes en la descarga: ampliar palabras no recupera actividades ausentes del archivo fuente.'])
slide('Proceso 2B: texto que efectivamente se analiza',[
'Se concatena nombre del establecimiento + razón social. Se pasa a minúsculas, se eliminan acentos y se normalizan espacios.',
'La descripción SCIAN se exige como columna, pero está comentada en la construcción de texto_filtro; no se analiza en el filtro textual actual.',
'El catálogo giro_textil.csv vincula cada palabra o frase con una señal; una frase puede generar más de una señal.',
'Se buscan palabras o frases completas mediante límites alfanuméricos; las frases largas se ordenan primero y los espacios se flexibilizan.',
'Limitaciones: nombres comerciales poco descriptivos, abreviaturas y variantes no incluidas pueden perder señales; palabras generales pueden crear coincidencias ambiguas.'])
catalogo=pd.read_csv(ROOT/'data/processed/catalogs/giro_textil.csv')
for title, sigs in [('Diccionario: contexto textil y productivo',['textil','mezclilla','produccion','maquila']),('Diccionario: procesos y exclusiones',['humedo_explicito','lavado_generico','proceso_seco_explicito','no_textil_explicito'])]:
    slide(title,[f'{s}: {len(catalogo[catalogo.senal.eq(s)])} entradas. Ejemplos: '+', '.join(catalogo[catalogo.senal.eq(s)].palabra.head(5)) for s in sigs]+['El catálogo completo se incluye al final, para que ninguna entrada quede omitida.'])
slide('Proceso 2C: retención textual y exclusiones',[
'Se crean siete señales positivas: textil, mezclilla, húmedo explícito, lavado genérico, producción, maquila y proceso seco explícito.',
'El subconjunto textual retiene filas con al menos una señal positiva; una señal de proceso seco también basta para ser candidato textual.',
'Se calcula no_textil_explicito con el mismo texto. Una coincidencia negativa excluye del subconjunto textual aunque haya señales positivas.',
'La exclusión textual no es un veto global: una fila puede permanecer por SCIAN al efectuar la unión.',
'Las señales positivas se incorporan desde el subconjunto textual retenido. Si una fila fue excluida allí y entra por SCIAN, esas señales quedan en False.',
'Por tanto, el resultado debe explicarse como ejecución de reglas, no como auditoría de actividad real.'])
slide('Proceso 3: unión e identificadores',[
'Se calculan los conjuntos de ID del filtro SCIAN y del filtro textual de forma independiente.',
'Candidatos = ID SCIAN unión ID texto. Se recupera una sola fila original por ID.',
'Se guardan coincide_filtro_scian y coincide_filtro_texto para explicar por qué entró cada registro.',
'Las señales textuales se añaden con unión uno a uno; señales ausentes se convierten a False.',
'El flujo estatal actual produce 15,956 candidatos auditables: coincide con la descarga. Esto no significa que todos tengan relevancia hídrica.'])
slide('Proceso 4A: condiciones intermedias exactas',[
'Contexto textil = SCIAN textil o señal textil o señal mezclilla.',
'Contexto productivo = señal producción o señal maquila.',
'Evidencia húmeda = SCIAN exacto 313310 o (húmedo explícito y contexto textil).',
'Señal adicional de lavandería = textil o mezclilla o húmedo explícito o producción o maquila. Lavado genérico solo no basta en modo estricto.',
'Mezclilla relevante = mezclilla y (lavado genérico o húmedo explícito o contexto productivo).',
'Estas condiciones combinan clasificación administrativa y vocabulario; no miden intensidad del proceso.'])
slide('Proceso 4B: decisión sectorial',[
'Cada candidato empieza con sector_textil = REVISAR.',
'Se asigna INCLUIR si tiene SCIAN textil; o contexto productivo y (textil o mezclilla); o evidencia húmeda.',
'La decisión sectorial y la evidencia hídrica son columnas distintas: INCLUIR no equivale a SI hídrico.',
'Una lavandería puede tener sector REVISAR y evidencia hídrica REVISAR o SI.',
'El universo hídrico estatal se selecciona por evidencia_hidrica; no exige sector_textil = INCLUIR como segunda condición.'])
slide('Proceso 4C: regla amplia y regla estricta',[
'Amplia: toda lavandería SCIAN 812210 es admisible como lavado por revisar, aun sin señal adicional.',
'Estricta: SCIAN 812210 es admisible por esa vía solo si tiene alguna señal adicional.',
'En ambas: lavado genérico y contexto textil también genera lavado por revisar. El modo estricto modifica una vía de admisión, no todos los criterios.',
'Las demás condiciones de evidencia húmeda y mezclilla relevante se mantienen.',
'Ventaja del amplio: mayor cobertura de nombres poco informativos. Ventaja del estricto: reduce ambigüedad.',
'Costo del amplio: mezcla perfiles comerciales e industriales. Costo del estricto: puede perder industriales reales sin señales en el nombre.'])
slide('Proceso 4D: clasificación hídrica y precedencia',[
'Cada candidato empieza como SIN_EVIDENCIA.',
'Pasa a REVISAR si cumple lavado por revisar o mezclilla relevante.',
'Pasa a SI si cumple evidencia húmeda. Esta asignación se ejecuta después y tiene prioridad sobre REVISAR.',
'La señal proceso_seco_explicito no veta la evidencia húmeda ni se usa como regla final de exclusión hídrica.',
'SIN_EVIDENCIA significa ausencia de señales bajo estas reglas, no ausencia demostrada de uso de agua.',
'SI automático significa evidencia administrativa o textual según el criterio; no confirma descarga ni carácter industrial.'])
tabla_slide('Ejemplos de aplicación de las reglas',['Caso hipotético','Amplio','Estricto'],[
['812210; nombre solo Lavandería Luna','REVISAR','SIN_EVIDENCIA'],
['812210; Lavandería Industrial Luna','REVISAR','REVISAR'],
['812210; Lavado de mezclilla Luna','SI','SI'],
['315; taller de costura sin otra señal','SIN_EVIDENCIA','SIN_EVIDENCIA'],
['315; maquila de mezclilla','REVISAR','REVISAR'],
['313310; nombre no descriptivo','SI','SI']],
'Ejemplos explicativos, no establecimientos observados. Industrial genera producción/húmedo, pero SI requiere contexto textil o 313310.')
slide('Proceso 5: municipios y modalidades',[
'Se normalizan nombres de municipio eliminando acentos, ajustando mayúsculas y espacios; se retienen los 26 nombres solicitados.',
'Resultado común: 4,365 candidatos sectoriales en los municipios seleccionados.',
'Amplio y estricto retienen SI y REVISAR y guardan primero universo_hidrico_26_municipios_solo_filtro.csv.',
'Con --sin-mh se mantiene solo DENUE y se registran las fuentes REGLAS_DENUE y FILTRO_DENUE.',
'Con --todos-scian se conservan todos los candidatos seleccionados, incluidos SIN_EVIDENCIA, y se omite MH.',
'La modalidad sectorial conserva la unión SCIAN/texto ya calculada; el nombre todos-scian no implica un nuevo censo completo.'])
tabla_slide('Comparación con denominadores explícitos',['Modalidad','26 municipios','Dentro de cuenca','SI','REVISAR'],[
[n, pd.read_csv(bases[n]/'tables/universo_hidrico_26_municipios.csv').shape[0],len(datos[n]),datos[n].evidencia_hidrica.eq('SI').sum(),datos[n].evidencia_hidrica.eq('REVISAR').sum()] for n,_ in MODOS],
'Sectorial incluye además 2,331 SIN_EVIDENCIA dentro de cuenca. Son escenarios de reglas, no intervalos estadísticos de población.')
imagen('Sensibilidad del tamaño del universo','direccion_imagenes/modalidades.png','Comparación del mismo recorte espacial. La mayor diferencia corresponde a la regla de lavanderías.')
slide('Cómo comparar distribución y concentración',[
'Distribución muestra cada establecimiento en su ubicación; concentración municipal suma puntos dentro de polígonos municipales recortados por cuenca.',
'Los cinco mapas de conteo usan la misma extensión, colores y escala de 0 a '+str(limite)+' registros. No se ajusta la escala por modalidad.',
'El segundo panel compara participación: porcentaje del total de cada modalidad que cae en cada municipio. Permite comparar estructura territorial pese a los distintos tamaños.',
'La matriz resume conteos reales; usa log(1 + conteo) solo en el color para hacer visibles municipios pequeños.',
'La asignación espacial usa within y puede dejar puntos de límite sin asignar. Estos conteos pueden diferir del municipio declarado por DENUE.'])
imagen('Cinco modalidades: concentración municipal absoluta','direccion_imagenes/panel_conteos.png','Escala común de conteos. Los colores comparan cantidades de establecimientos; no representan intensidad hídrica.')
imagen('Cinco modalidades: participación territorial','direccion_imagenes/panel_participacion.png','Escala común de porcentajes; denominador = total de registros dentro de cuenca de cada modalidad. No es densidad por km².')
imagen('Heatmap comparativo por municipio y modalidad','direccion_imagenes/matriz_municipal.png','Cifras = conteos espaciales. Color logarítmico para visibilidad; el orden de filas usa la suma de las cinco columnas, sin tratarla como universo único.')
for i,(n,_) in enumerate(MODOS):
    imagen('Distribución y concentración: '+n,f'direccion_imagenes/comparacion_modo_{i}.png','Puntos a la izquierda; conteo por polígono a la derecha. Escala absoluta idéntica en las cinco modalidades.')
slide('Posibles comerciales: definición del grupo',[
'Se seleccionan registros SCIAN exacto 812210 del amplio DENUE que no aparecen en estricto DENUE; se comparan identificadores dentro de la misma cuenca.',
f'El grupo contiene {len(comerciales):,} registros. Representa {100*len(comerciales)/len(amplio):.1f}% del universo amplio DENUE.',
'Son lavanderías sin señal adicional suficiente bajo la regla estricta. El grupo permite localizar dónde se concentra la diferencia entre escenarios.',
'La ausencia de señal industrial en nombre/razón social no demuestra operación comercial: también puede haber industriales poco descriptivas.',
'Se usan escenarios sin MH para aislar el cambio de regla; el mapa no clasifica automáticamente los registros MH como comerciales o industriales.'])
imagen('Heatmap: dónde se concentran las posibles comerciales','direccion_imagenes/posibles_comerciales.png','Aproximación por falta de señal adicional: SCIAN 812210 en amplio DENUE y ausente del estricto. Escala propia de este grupo.')
imagen('Posibles comerciales: municipios con más registros','direccion_imagenes/ranking_comerciales.png','Conteo por municipio declarado, y porcentaje respecto al grupo de posibles comerciales; no es una verificación de tipo de operación.')
slide('Qué aporta esta comparación a dirección',[
f'{ranking.index[0]} concentra {int(ranking.iloc[0]):,} de {len(comerciales):,} posibles comerciales ({100*ranking.iloc[0]/len(comerciales):.1f}%).',
'Comparar conteos absolutos muestra dónde se reduce más el inventario; comparar participación muestra cómo cambia el peso relativo de las zonas.',
'Los mapas individuales conservan escala común para que un municipio no parezca igualmente concentrado en escenarios con cantidades muy distintas.',
'MH añade cobertura localizada; la caída del amplio al estricto corresponde principalmente al criterio de lavanderías, no a establecimientos que desaparecen.',
'Las tablas y el listado de este grupo se guardan en docs/direccion_imagenes para rastrear los registros que sostienen la comparación.'])
slide('Establecimientos pequeños: eje del marco territorial',[
'La comparación también separa los estratos DENUE 0 a 5 y 6 a 10 personas en las cinco modalidades.',
'La categoría de origen es 0 a 5; no se cambia a 1 a 5 porque el archivo no permite separar registros con cero personas.',
'Se utilizan como estratos operativos de establecimientos pequeños. El personal reportado no equivale por sí solo a una clasificación formal de microempresa ni mide producción.',
'Cada estrato tiene una escala de color común entre modalidades. Las escalas de 0 a 5 y 6 a 10 son distintas para hacer visible cada grupo.',
'Los registros con estrato vacío quedan fuera de ambos grupos y se mantienen como desconocidos. No se asignan automáticamente a los pequeños.'])
tabla_slide('Peso de los establecimientos pequeños en cada modalidad',
['Modalidad','0 a 5','% universo','6 a 10','% universo'],[
[n, int((datos[n]['Descripcion estrato personal ocupado']=='0 a 5 personas').sum()),
f"{100*(datos[n]['Descripcion estrato personal ocupado']=='0 a 5 personas').sum()/len(datos[n]):.1f}%",
int((datos[n]['Descripcion estrato personal ocupado']=='6 a 10 personas').sum()),
f"{100*(datos[n]['Descripcion estrato personal ocupado']=='6 a 10 personas').sum()/len(datos[n]):.1f}%"] for n,_ in MODOS],
'Denominador: todos los registros de cada modalidad dentro de cuenca, incluidos los de estrato desconocido.')
for e,estrato in enumerate(estratos):
    imagen('Cinco modalidades: pequeños de '+estrato,f'direccion_imagenes/pequenas_panel_{e}.png','Conteos espaciales con escala común dentro del estrato. Comparar solo mapas que tengan la misma barra de color.')
    for i,(n,_) in enumerate(MODOS):
        imagen(n+': establecimientos de '+estrato,f'direccion_imagenes/pequenas_{e}_modo_{i}.png','Distribución puntual y concentración municipal del mismo grupo; campos de personal ocupado reportados por DENUE.')
slide('Qué implica la concentración de establecimientos pequeños',[
'La predominancia de registros pequeños caracteriza una estructura territorial de numerosas unidades de baja ocupación reportada.',
'Los mapas permiten ubicar agrupaciones territoriales para orientar preguntas sobre servicios compartidos, procesos o vínculos productivos; esos vínculos requieren evidencia adicional.',
'Cambiar el filtro puede modificar tanto el número como la distribución de pequeños. La comparación por estrato evita atribuir todo el cambio a industrias grandes.',
'Un establecimiento con pocas personas puede operar procesos intensivos; el estrato no permite estimar agua utilizada o descarga.',
'Los registros MH sin personal reportado no se deben interpretar como grandes ni como pequeños. Su información faltante queda visible.'])
slide('Proceso 6A: preparación e integración MH',[
'Fuentes: capa final MH.shp de Xalmimilulco y base_huejo(Hoja1) (1).csv de Huejotzingo.',
'Se conserva evidencia_hidrica_original y se añade fuente_universo_hidrico, fuente_evidencia_hidrica e id_denue_origen_mh.',
'El código asigna SI a los registros asociados con MH y etiqueta MH_TRABAJO_CAMPO.',
'Esta asignación es una decisión del procedimiento; no acredita por sí sola qué proceso se comprobó.',
'53 registros se procesan: 46 de Xalmimilulco y 7 de Huejotzingo; todos aparecen dentro del recorte de cuenca en las salidas actuales.'])
slide('Proceso 6B: correspondencia de Xalmimilulco',[
'La capa MH se transforma a EPSG:4326; se toma ID DENUE, eliminando .0 y tratando nulos como ID vacío.',
'Si ID ya está en universo hídrico: se conserva el registro DENUE, se cambia a SI y se añade procedencia MH; acción YA_PRESENTE.',
'Si ID está en auditable pero fuera del hídrico: se recupera la fila DENUE y se asigna SI; acción AGREGADO_DESDE_DENUE.',
'Si no hay correspondencia en auditable: se crea registro suplementario MH_XALMI_..., con nombre y geometría MH; acción AGREGADO_SUPLEMENTARIO.',
'Los suplementarios tienen sector REVISAR, evidencia original SIN_REGISTRO_DENUE_2026 y campos DENUE no conocidos vacíos.',
'La búsqueda es contra auditable; SIN_REGISTRO no acredita ausencia de cualquier registro en toda la base nacional DENUE.'])
slide('Proceso 6C: correspondencia de Huejotzingo',[
'El ID del CSV es local, no ID DENUE. Se excluyen nombres vacíos y se convierten coordenadas decimales o grados/minutos/segundos a latitud y longitud.',
'Se consideran candidatos auditables cuya localidad normalizada es Huejotzingo; se transforman a EPSG:32614.',
'Para cada fila MH se elige el candidato más cercano. Se calcula similitud de nombre con SequenceMatcher sobre texto normalizado.',
'Coincidencia = distancia menor o igual a 35 m y similitud mayor o igual a 0.45.',
'Si coincide: actualizar si ya está o recuperar desde DENUE. Si no: crear MH_HUEJO_... con geometría MH y campos administrativos vacíos.',
'Límite: se prueba solo el vecino más cercano; no se buscan otros vecinos si falla su nombre. Los umbrales no tienen validación estadística documentada.'])
slide('Proceso 6D: trazabilidad y controles MH',[
'La auditoría registra fuente, nombre, ID MH, ID de salida, acción, distancia y, para Huejotzingo, similitud de nombre.',
'Se concatenan recuperados y suplementarios; se rechazan ID de salida duplicados.',
'En las auditorías actuales no hay ID de salida repetidos. Esto no descarta duplicados físicos con ID distintos.',
'La evidencia original se conserva para evaluar cambios de clase; no se completa artificialmente el estrato de personal de suplementarios.',
'La cobertura MH es localizada: sus aportes no deben extrapolarse como tasa de omisión al resto del territorio.'])
tabla_slide('Qué cambia MH en cada modalidad',['Modalidad','Ya presentes','Recuperados DENUE','Suplementarios','Total MH'],[
['Amplio + MH',15,31,7,53],['Estricto + MH',12,34,7,53]],
'Incrementos netos: 38 y 41. En ambos, SI pasa de 41 a 91: MH reclasifica casos previos además de incorporar registros.')
slide('Cómo leer los 91 registros SI',[
'En amplio + MH y estricto + MH hay 53 SI con fuente MH_TRABAJO_CAMPO y 38 SI con fuente REGLAS_DENUE.',
'Antes de MH hay 41 SI automáticos. Tres de ellos cambian de fuente al estar también en MH.',
'Por eso 41 + 53 no se debe sumar como registros independientes: las fuentes se superponen.',
'La procedencia de la evidencia debe acompañar cada conteo SI para distinguir reglas automáticas de información MH.'])
slide('Proceso 7: recorte real de cuenca',[
'Se lee el polígono de cuenca y se transforma a EPSG:4326.',
'Se retienen puntos que intersectan la primera geometría del archivo de cuenca; un punto en el borde puede quedar incluido.',
'Se exportan por separado universo municipal y universo dentro de cuenca; no deben confundirse sus conteos.',
'El flujo cartográfico recorta red hidrográfica y polígonos municipales por la cuenca.',
'Los mapas de cada municipio usan puntos within del polígono recortado: un punto en el límite puede tratarse distinto del recorte intersects.',
'La operación usa geometry.iloc[0]; si cambia la estructura del archivo de cuenca, debe comprobarse que esa geometría represente el área completa.'])
imagen('Distribución: misma extensión, dos escenarios','direccion_imagenes/mapas_comparables.png','Comparación elaborada desde capas GPKG, con la misma extensión y simbología. La fuente MH se distingue en rojo.')
imagen('Dónde cambia la concentración municipal','direccion_imagenes/municipios.png','Conteos por municipio declarado en el registro, dentro del recorte de cuenca; no son tasas ni volúmenes de descarga.')
slide('Hallazgo territorial y efecto de cobertura',[
'Con MH, Puebla tiene 1,004 registros en amplio y 283 en estricto; Huejotzingo tiene 155 y 98, respectivamente.',
'La participación de Huejotzingo pasa de 9.0% a 19.2% al cambiar amplio + MH por estricto + MH.',
'Los 41 registros añadidos por MH al estricto están en el municipio de Huejotzingo: su conteo pasa de 57 a 98.',
'El orden y peso territorial dependen del filtro y de la cobertura de fuentes; no deben interpretarse automáticamente como diferencias de presión ambiental.',
'El marco permite contextualizar las zonas de interés dentro del inventario territorial.'])
slide('Proceso 8: tamaño y agregación espacial',[
'Tamaño = estrato de personal ocupado de DENUE; no se convierte a empleo exacto ni a capacidad productiva.',
'En estricto + MH, 441 de 510 registros (86.5%) reportan 0 a 5 personas; 35 (6.9%) reportan 6 a 10.',
'Los registros sin estrato se mantienen como desconocidos; no se asignan a microestablecimientos.',
'Los conteos municipales describen cantidad de registros. Las localidades se agregan por municipio + localidad.',
'Sin polígonos de localidad, el mapa usa centros medios de sus establecimientos: no son límites oficiales ni áreas de influencia.',
'El tamaño administrativo no permite concluir si una lavandería es comercial o industrial.'])
imagen('Concentración por localidad: estricto con MH','../outputs/cuenca_alto_atoyac_puebla_estricto_mh/maps/png/06_conteo_localidad.png','Agregaciones puntuales; el centro medio puede desplazarse al cambiar el conjunto de establecimientos.')
slide('Proceso 9: distancia a la red hidrográfica',[
'Se reproyectan puntos y red hidrográfica recortada a EPSG:32614 (UTM 14N).',
'Se une la geometría de la red y se calcula distancia mínima geométrica de cada punto, en metros.',
'Se agrupa con pd.cut: hasta 250 m; más de 250 hasta 500 m; más de 500 hasta 1,000 m; más de 1,000 hasta 2,000 m; más de 2,000 m.',
'Los intervalos de salida llevan etiquetas 0-250, 250-500, 500-1,000, 1-2 km y >2 km; los límites superiores se incluyen.',
'Es proximidad cartográfica a la red proporcionada. No incorpora drenaje, tuberías, topografía, ruta del efluente o punto real de descarga.',
'Sirve para contextualizar o priorizar información adicional; no mide conexión hidráulica ni causalidad ambiental.'])
imagen('Proximidad en el escenario de priorización','../outputs/cuenca_alto_atoyac_puebla_estricto_mh/maps/png/03_establecimientos_distancia_rio.png','Distancia euclidiana mínima a la red incluida y recortada por cuenca; interpretar con las limitaciones de la diapositiva anterior.')
slide('Ventajas y observaciones: sectorial y amplio',[
'Sectorial: ofrece contexto económico y distribución de la cadena textil; incluye actividades sin señales húmedas. Es el denominador contextual, no un universo de lavanderías industriales.',
'Amplio DENUE: cubre lavanderías de nombres poco informativos; 1,586 de sus 1,679 registros tienen SCIAN 812210.',
'El amplio evita descartar por falta de vocabulario, pero no separa lavanderías comerciales e industriales.',
'Amplio + MH: añade evidencia localizada y registros omitidos; mejora información en zonas cubiertas sin resolver la ambigüedad en todo el territorio.',
'Estas modalidades son útiles para contexto y sensibilidad, no para inferir cantidad de industrias contaminantes.'])
slide('Ventajas y observaciones: estricto',[
'Estricto DENUE: baja de 1,679 a 469 candidatos; conserva 376 SCIAN 812210. La reducción es operativa, no validación de exactitud.',
'Puede perder casos industriales por nombres genéricos; puede retener casos comerciales por señales generales como ropa o tintorería.',
'Estricto + MH: 510 candidatos; recupera 41 registros por información localizada. Es una base razonable de priorización acompañada de procedencia.',
'El catálogo contiene términos amplios, por ejemplo acabado y lavado de ropa; la categoría SI exige interpretar qué evidencia aportó el término.',
'No existen estimaciones documentadas de sensibilidad o precisión del clasificador. Ninguna modalidad constituye el conteo real verificado.'])
slide('Antecedente local y comparación histórica',[
'El flujo 100_main trabaja Huejotzingo y Santa Ana Xalmimilulco con descarga local del 04/09/2026: primero recorta localidad y después aplica las reglas.',
'Exporta candidatos, SI y SI + REVISAR; recupera geometrías desde la capa original por identificador y genera figuras locales.',
'El flujo 07 compara por ID normalizado contra universos legacy: coincidencias, solo actual, solo histórico y diagnóstico probable de ausencias.',
'Los históricos y los actuales pueden diferir en fuente, fecha, cobertura, registros sin ID y definición de candidato.',
'Su función es explicar evolución del procedimiento; no se interpretan diferencias como apertura o cierre de establecimientos sin evidencia adicional.'])
slide('Desajustes documentales que dirección debe conocer',[
'La presentación anterior afirma usar descripción SCIAN para exclusiones; el texto_filtro actual solo concatena nombre y razón social.',
'Algunos títulos anteriores dicen confirmados para todos los SI. Aquí se distingue SI por reglas de la procedencia MH.',
'El campo SIN_REGISTRO_DENUE_2026 en suplementarios refiere a ausencia de correspondencia en el conjunto auditable utilizado.',
'Las tablas actuales son las cifras de esta presentación; corregir títulos no cambia ni valida retrospectivamente los criterios.',
'Esta entrega no modifica el clasificador ni las fuentes: deja visibles sus decisiones y límites para acordar mejoras.'])
slide('Revisión viable para una zona extensa',[
'Mantener clasificación automática reproducible para todo el territorio y conservar la incertidumbre por registro.',
'Concentrar la revisión en correspondencias MH dudosas y casos que afecten una decisión concreta.',
'No condicionar el avance a una auditoría manual exhaustiva de los 4,010 registros sectoriales.',
'Si se requiere evaluar desempeño del filtro, diseñar después una revisión acotada por grupos: retenidos, descartados y tipos de evidencia.',
'Esa revisión serviría para conocer errores del método; no se presenta aquí como realizada ni como validación ya disponible.'])
slide('Decisiones propuestas para dirección',[
'Adoptar estricto + MH como escenario de priorización de candidatos y amplio como contraste de cobertura.',
'Conservar el sectorial como contexto económico; reportar siempre territorio, modalidad y fuente junto a cada cifra.',
'Definir qué se observó en MH antes de utilizar el término verificado.',
'Priorizar la actualización de información en registros cuya incertidumbre afecte decisiones del proyecto.',
'El entregable territorial queda como marco de relevancia y selección de preguntas; la fase siguiente aporta evidencia específica de operación.'])
slide('Trazabilidad y reproducción de las cinco modalidades',[
'Flujo actual: python scripts/101_main_cuenca_puebla.py (amplio + MH).',
'Agregar --sin-mh para amplio DENUE; --estricto para estricto + MH; --estricto --sin-mh para estricto DENUE.',
'Agregar --todos-scian para escenario sectorial; esa opción omite MH.',
'Reproducción de esta entrega: python scripts/102_presentacion_direccion.py. Lee las salidas existentes y compila el PDF.',
'Una nueva corrida territorial regenera HTML/PNG del directorio correspondiente. Para conservar versiones, archivar previamente salidas y catálogo.',
'Fecha de preparación: 17/09/2026. Fuentes: archivos locales del proyecto; no se incorporaron datos externos.'])
slide('Archivos y campos para auditar un resultado',[
'02_scian.py: prefijos; 03_text_filter.py + giro_textil.csv: señales; 04_desiciones_preliminares.py: decisiones y precedencia.',
'101_main_cuenca_puebla.py: carga, municipios, modalidades y cuenca; 10_integrar_mh.py: correspondencias y suplementarios.',
'08_mapas_cuenca_puebla.py: distancias, agregaciones y mapas; 09_presentacion_cuenca_puebla.py: presentaciones anteriores.',
'En cada carpeta outputs/cuenca_alto_atoyac_puebla*: tablas de ejecución, auditable estatal, universo sectorial, hídrico previo a MH, final, dentro de cuenca y distancias.',
'Auditar por d_llave, señales, coincide_filtro_scian/texto, sector_textil, evidencia_hidrica/original, fuentes e ID de origen MH.',
'El archivo auditoria_integracion_mh.csv explica cada acción de integración; inventario_mapas.csv localiza PNG y HTML.'])
municipios = ['Amozoc','Calpan','Chiautzingo','Chignahuapan','Coronango','Cuautinchán','Cuautlancingo','Domingo Arenas','Huejotzingo','Ixtacamaxtitlán','Juan C. Bonilla','Ocoyucan','Puebla','San Andrés Cholula','San Felipe Teotlalcingo','San Gregorio Atzompa','San Jerónimo Tecuanipan','San Martín Texmelucan','San Matías Tlalancaleca','San Miguel Xoxtla','San Pedro Cholula','San Salvador el Verde','Tepatlaxco de Hidalgo','Tlahuapan','Tlaltenango','Tzicatlacoyan']
for i in range(0,len(municipios),13):
    slide(f'Anexo: municipios solicitados ({i//13+1}/2)',['; '.join(municipios[j:min(j+4,i+13,len(municipios))]) for j in range(i,min(i+13,len(municipios)),4)])
for senal, grupo in catalogo.groupby('senal',sort=False):
    palabras=grupo.palabra.tolist()
    for i in range(0,len(palabras),20):
        slide('Anexo: catálogo completo / '+senal,[', '.join(palabras[j:j+4]) for j in range(i,min(i+20,len(palabras)),4)]+[f'Entradas {i+1} a {min(i+20,len(palabras))} de {len(palabras)} para esta señal. La lista conserva entradas por señal.'])

head=r'''\documentclass[aspectratio=169,10pt]{beamer}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot]{babel}
\usepackage{graphicx,booktabs}
\definecolor{Direccion}{HTML}{185879}
\setbeamercolor{structure}{fg=Direccion}
\setbeamercolor{frametitle}{fg=white,bg=Direccion}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}{\hfill\scriptsize Alto Atoyac | Presentación a dirección\hspace{1em}\insertframenumber/\inserttotalframenumber\hspace{1em}\vspace{2mm}}
\setbeamersize{text margin left=7mm,text margin right=7mm}
\title{Marco territorial de establecimientos\\potencialmente relevantes}
\subtitle{Hallazgos, filtros y modalidades\\de distribución y concentración territorial}
\author{Proyecto Alto Atoyac | Presentación a dirección}
\date{17 de septiembre de 2026}
\begin{document}
\begin{frame}\titlepage\end{frame}
'''
tex=DOCS/'presentacion a direccion.tex'
tex.write_text(head+''.join(frames)+'\\end{document}\n',encoding='utf-8')
pd.DataFrame([{'modalidad':n,'dentro_cuenca':len(datos[n]),'SI':datos[n].evidencia_hidrica.eq('SI').sum(),'REVISAR':datos[n].evidencia_hidrica.eq('REVISAR').sum(),'SIN_EVIDENCIA':datos[n].evidencia_hidrica.eq('SIN_EVIDENCIA').sum()} for n,_ in MODOS]).to_csv(ASSETS/'comparacion_modalidades.csv',index=False,encoding='utf-8-sig')
for _ in range(2):
    result=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',tex.name],cwd=DOCS,capture_output=True,text=True)
    if result.returncode:
        print(result.stdout[-5000:]); raise SystemExit(result.returncode)
print(f'PDF generado: {DOCS / "presentacion a direccion.pdf"}; {len(frames)+1} diapositivas')
