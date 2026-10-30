"""Segunda iteración: análisis exploratorio y mapas autocontenidos de Parte 3."""
from __future__ import annotations
from pathlib import Path
import textwrap
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; P3=ROOT/'outputs'/'parte_3'; G=P3/'parte_3_sistema_saneamiento_integrado.gpkg'
OUT=P3/'06_analisis'; FIG=OUT/'figuras'; MAP=P3/'05_mapas'; CRS='EPSG:32614'
for d in (OUT,FIG,MAP): d.mkdir(parents=True,exist_ok=True)

def read(n): return gpd.read_file(G,layer=n).to_crs(CRS)
def nearest(a,b,aid,bid):
    if a.empty or b.empty:return pd.DataFrame(columns=[aid,bid,'distancia_m'])
    return gpd.sjoin_nearest(a[[aid,'geometry']],b[[bid,'geometry']],distance_col='distancia_m')[[aid,bid,'distancia_m']]
def add_scale(ax,length=10000):
    x0,x1=ax.get_xlim();y0,y1=ax.get_ylim(); x=x0+.72*(x1-x0); y=y0+.055*(y1-y0)
    ax.plot([x,x+length],[y,y],color='black',lw=3); ax.plot([x,x],[y-700,y+700],color='black',lw=1); ax.plot([x+length,x+length],[y-700,y+700],color='black',lw=1)
    ax.text(x+length/2,y+1200,f'{length/1000:g} km',ha='center',fontsize=8)
def add_north(ax):
    ax.annotate('N',xy=(.94,.92),xytext=(.94,.81),xycoords='axes fraction',ha='center',fontsize=11,fontweight='bold',arrowprops=dict(facecolor='black',width=3,headwidth=10))
def extent(ax,g,margin=.035):
    x0,y0,x1,y1=g.total_bounds;m=max(x1-x0,y1-y0)*margin;ax.set_xlim(x0-m,x1+m);ax.set_ylim(y0-m,y1+m)
def labels(ax,mun,only=None):
    q=mun if only is None else mun[mun.nom_mun.isin(only)]
    for _,r in q.iterrows():
        p=r.geometry.representative_point(); ax.text(p.x,p.y,str(r.nom_mun),fontsize=5.2,ha='center',color='#333',path_effects=[])
def base(ax,cuenca,mun,hid,detail=False):
    mun.boundary.plot(ax=ax,color='#bdbdbd',lw=.35,zorder=1);hid.plot(ax=ax,color='#4aa8d8',lw=.35 if not detail else .55,alpha=.72,zorder=2)
    cuenca.boundary.plot(ax=ax,color='#222',lw=1.2,zorder=8);extent(ax,cuenca);add_north(ax);add_scale(ax,5000 if detail else 10000);ax.set_axis_off()
def finish(fig,ax,title,subtitle,handles,source,filename):
    ax.set_title(title,fontsize=15,fontweight='bold',pad=23);ax.text(.5,1.008,subtitle,transform=ax.transAxes,ha='center',fontsize=8.5)
    ax.legend(handles=handles,loc='lower left',fontsize=7.2,frameon=True,ncol=1)
    fig.text(.01,.012,f'Fuente: {source} | CRS: WGS 84 / UTM zona 14N (EPSG:32614) | Elaboración: {pd.Timestamp.today():%Y-%m-%d}',fontsize=6.7)
    fig.text(.99,.012,'La proximidad espacial no implica conexión hidráulica.',ha='right',fontsize=6.7,color='#8b0000')
    fig.subplots_adjust(left=.02,right=.98,top=.90,bottom=.055);fig.savefig(filename,dpi=250,bbox_inches='tight');plt.close(fig)

est,clu,sub,des,ptar,hid,mun,cuenca=[read(x) for x in ['establecimientos_textiles','clusters_parte2','subnucleos_parte2','descargas','ptar','hidrografia','municipios','limite_cuenca']]
targets=['Huejotzingo','San Martín Texmelucan']; mt=mun[mun.nom_mun.isin(targets)].copy()

# Tablas analíticas
sd=nearest(sub,des,'subnucleo_id','descarga_id');sp=nearest(sub,ptar,'subnucleo_id','ptar_id');sh=nearest(sub,hid,'subnucleo_id','hidrografia_id')
rows=[]
for _,s in sub.iterrows():
    e=est[est.subnucleo_id==s.subnucleo_id]; dg=des[des.distance(s.geometry)<=1000]; pg=ptar[ptar.distance(s.geometry)<=5000]
    rows.append({'subnucleo_id':s.subnucleo_id,'n_establecimientos':len(e),'n_alta':(e.prioridad_ambiental=='alta').sum(),'n_media':(e.prioridad_ambiental=='media').sum(),'prop_alta_media':round(e.prioridad_ambiental.isin(['alta','media']).mean(),3) if len(e) else 0,'dist_descarga_m':sd.loc[sd.subnucleo_id==s.subnucleo_id,'distancia_m'].min(),'descargas_1km':len(dg),'dist_ptar_m':sp.loc[sp.subnucleo_id==s.subnucleo_id,'distancia_m'].min(),'ptar_5km':len(pg),'dist_hidrografia_m':sh.loc[sh.subnucleo_id==s.subnucleo_id,'distancia_m'].min(),'colector_disponible':False,'nota':'Dimensiones separadas; no constituye ranking ni conexión'})
subtab=pd.DataFrame(rows);subtab.to_csv(OUT/'01_subnucleos_infraestructura.csv',index=False,encoding='utf-8-sig')
dh=nearest(des,hid,'descarga_id','hidrografia_id').merge(des.drop(columns='geometry'),on='descarga_id')
dh['tipo_asociacion_cauce']='proximidad_geometrica';dh['nivel_evidencia']='C';dh.to_csv(OUT/'02_descargas_hidrografia.csv',index=False,encoding='utf-8-sig')
ps=nearest(ptar,sub,'ptar_id','subnucleo_id').merge(ptar.drop(columns='geometry'),on='ptar_id');ps['tipo_relacion']='proximidad_espacial';ps.to_csv(OUT/'03_ptar_subnucleos.csv',index=False,encoding='utf-8-sig')
cap=ptar[['ptar_id','nombre_fuente','municipio','tipo_ptar','fuente','anio_fuente','capacidad_ls','caudal_tratado_ls','proceso','cuerpo_receptor','estado_verificacion']].copy();cap['utilizacion_capacidad_reportada']=cap.caudal_tratado_ls/cap.capacidad_ls;cap.to_csv(OUT/'04_capacidad_ptar.csv',index=False,encoding='utf-8-sig')
capmun=cap.groupby('municipio',dropna=False).agg(n_ptar=('ptar_id','size'),n_con_datos=('utilizacion_capacidad_reportada','count'),capacidad_reportada_ls=('capacidad_ls','sum'),caudal_reportado_ls=('caudal_tratado_ls','sum')).reset_index();capmun['utilizacion_capacidad_reportada_agregada']=capmun.caudal_reportado_ls/capmun.capacidad_reportada_ls.replace(0,np.nan);capmun.to_csv(OUT/'05_capacidad_municipio.csv',index=False,encoding='utf-8-sig')
cmp=[]
for m in targets:
    poly=mt[mt.nom_mun==m].geometry.union_all();e=est[est.intersects(poly)];p=ptar[ptar.intersects(poly)];d=des[des.intersects(poly)];ss=sub[sub.intersects(poly)]
    cmp.append({'municipio':m,'establecimientos':len(e),'alta_relevancia':(e.prioridad_ambiental=='alta').sum(),'subnucleos_intersectados':len(ss),'ptar_registros':len(p),'ptar_con_capacidad':p.capacidad_ls.notna().sum(),'capacidad_reportada_ls':p.capacidad_ls.sum(),'caudal_tratado_reportado_ls':p.caudal_tratado_ls.sum(),'descargas_registradas':len(d),'trazos_colector_recuperables':0,'interpretacion':'Comparación de disponibilidad registral; no inventario operativo completo'})
pd.DataFrame(cmp).to_csv(OUT/'06_comparacion_huejotzingo_smt.csv',index=False,encoding='utf-8-sig')
rec=pd.concat([ptar[['ptar_id','nombre_fuente','cuerpo_receptor','fuente','anio_fuente']].rename(columns={'ptar_id':'elemento_id','nombre_fuente':'nombre','anio_fuente':'anio'}).assign(tipo='PTAR'),des[['descarga_id','nombre_sistema','cuerpo_receptor','fuente','anio']].rename(columns={'descarga_id':'elemento_id','nombre_sistema':'nombre'}).assign(tipo='descarga')]);rec['cauce_conciliado']=None;rec['nivel_evidencia_asociacion']=np.where(rec.cuerpo_receptor.notna(),'A_atributo_declarado_sin_conciliar_geometria','D_sin_dato');rec.to_csv(OUT/'07_cuerpos_receptores.csv',index=False,encoding='utf-8-sig')
zon=subtab.copy();zon['criterio_vacio_informacion']=(zon.ptar_5km==0)|(zon.dist_descarga_m>2000)|(~zon.colector_disponible);zon['zona_candidata_investigacion']=(zon.n_establecimientos>=zon.n_establecimientos.median())&(zon.dist_descarga_m<=1000)&(zon.dist_hidrografia_m<=250);zon.to_csv(OUT/'08_zonas_candidatas_y_vacios.csv',index=False,encoding='utf-8-sig')
evid=pd.DataFrame([
['establecimiento','colector','D','No existe geometría ni vínculo documental recuperable'],['establecimiento','descarga','C','Solo distancia euclidiana'],['establecimiento','PTAR','C','Solo distancia euclidiana'],['colector','descarga/PTAR','D','Sin geometría de colectores'],['descarga','cuerpo receptor','A/C','A si está declarado; C para cauce geométricamente próximo'],['PTAR','cuerpo receptor','A/D','A si está declarado; D si falta atributo'],['subnúcleo','infraestructura','C','Coincidencia territorial agregada'] ],columns=['origen','destino','nivel_evidencia','fundamento']);evid.to_csv(OUT/'09_matriz_evidencia.csv',index=False,encoding='utf-8-sig')

# Mapas autocontenidos
H=[Patch(fill=False,edgecolor='#222',label='Límite de la cuenca'),Line2D([0],[0],color='#bdbdbd',label='Límites municipales'),Line2D([0],[0],color='#4aa8d8',label='Red hidrográfica RH18')]
fig,ax=plt.subplots(figsize=(9,9));base(ax,cuenca,mun,hid);mt.boundary.plot(ax=ax,color='#e66101',lw=2);labels(ax,mun,targets);finish(fig,ax,'Contexto territorial de la Parte 3','Cuenca del Alto Atoyac, municipios y red hidrográfica superficial',H+[Patch(fill=False,edgecolor='#e66101',label='Municipios de interés')],'INEGI RH18; delimitaciones CAARESA',MAP/'01_contexto_territorial.png')
fig,ax=plt.subplots(figsize=(9,9));base(ax,cuenca,mun,hid);clu.boundary.plot(ax=ax,color='#7b3294',lw=.8);sub.boundary.plot(ax=ax,color='#fdb863',lw=1.2);est.plot(ax=ax,color='#252525',markersize=2,alpha=.5);labels(ax,mun,targets);finish(fig,ax,'Concentraciones textiles e hidrografía','Solución HDBSCAN congelada de Parte 2 y subnúcleos diagnósticos',H+[Line2D([0],[0],marker='o',color='none',markerfacecolor='#252525',label='Establecimientos',markersize=4),Patch(fill=False,edgecolor='#7b3294',label='Clusters Parte 2'),Patch(fill=False,edgecolor='#fdb863',label='Subnúcleos del cluster 20')],'DENUE/Parte 2; INEGI RH18',MAP/'02_establecimientos_clusters_hidrografia.png')
fig,ax=plt.subplots(figsize=(9,9));base(ax,cuenca,mun,hid);p1=ptar[ptar.fuente.str.startswith('INEGI')];p2=ptar[~ptar.fuente.str.startswith('INEGI')];p1.plot(ax=ax,color='#1f78b4',marker='^',markersize=32);p2.plot(ax=ax,color='#ff7f00',marker='^',markersize=42);labels(ax,mun,targets);finish(fig,ax,'Infraestructura de tratamiento registrada','Registros por fuente; presencia registral no acredita operación o cobertura',H+[Line2D([0],[0],marker='^',color='none',markerfacecolor='#1f78b4',label='PTAR INEGI CNGMD 2021',markersize=7),Line2D([0],[0],marker='^',color='none',markerfacecolor='#ff7f00',label='PTAR compilación 2021–2022',markersize=7)],'INEGI CNGMD 2021 (descarga 2023); PTAR_Final.csv',MAP/'03_ptar_tipo_fuente.png')
fig,ax=plt.subplots(figsize=(9,9));base(ax,cuenca,mun,hid);des.plot(ax=ax,color='#d73027',marker='x',markersize=22);labels(ax,mun,targets);finish(fig,ax,'Puntos de descarga e hidrografía','302 registros; 301 sin tipo municipal/industrial especificado y 1 industrial compilado',H+[Line2D([0],[0],marker='x',color='#d73027',linestyle='none',label='Punto de descarga',markersize=7)],'INEGI CNGMD 2021; PTAR_Final.csv; INEGI RH18',MAP/'04_descargas_hidrografia.png')
fig,ax=plt.subplots(figsize=(9,9));base(ax,cuenca,mun,hid);mt.boundary.plot(ax=ax,color='#e66101',lw=2);labels(ax,mun,targets);ax.text(.5,.5,'NO HAY GEOMETRÍAS DE COLECTORES RECUPERABLES\n\nLos dos nombres del proyecto QGIS son nodos sin fuente.\nNo se representan como infraestructura existente.',transform=ax.transAxes,ha='center',va='center',fontsize=12,bbox=dict(facecolor='white',edgecolor='#b2182b',alpha=.93,pad=12));finish(fig,ax,'Disponibilidad de información sobre colectores','Vacío de información cartográfica; no es evidencia de ausencia física',H+[Patch(fill=False,edgecolor='#e66101',label='Municipios mencionados en el reporte de Lesly'),Line2D([0],[0],color='none',label='Colectores recuperables: 0')],'Proyecto QGIS y reporte de Lesly, revisión 2026',MAP/'05_disponibilidad_colectores.png')
fig,ax=plt.subplots(figsize=(9,9));base(ax,cuenca,mun,hid);sub.boundary.plot(ax=ax,color='#fdb863',lw=1.1);est.plot(ax=ax,color='#542788',markersize=1.5,alpha=.35);des.plot(ax=ax,color='#d73027',marker='x',markersize=17);ptar.plot(ax=ax,color='#1b9e77',marker='^',markersize=25);labels(ax,mun,targets);finish(fig,ax,'Integración territorial de actividad textil e infraestructura','Vista general; se muestran coincidencias espaciales, no rutas de aguas residuales',H+[Line2D([0],[0],marker='o',color='none',markerfacecolor='#542788',label='Establecimientos',markersize=4),Patch(fill=False,edgecolor='#fdb863',label='Subnúcleos'),Line2D([0],[0],marker='x',color='#d73027',linestyle='none',label='Descargas',markersize=6),Line2D([0],[0],marker='^',color='none',markerfacecolor='#1b9e77',label='PTAR',markersize=7)],'Parte 2; INEGI CNGMD/RH18; compilación PTAR',MAP/'06_integracion_general.png')
for num,m in enumerate(targets,7):
    poly=mt[mt.nom_mun==m]; ee=est.loc[gpd.sjoin(est,poly,predicate='intersects',how='inner').index.unique()];dd=des.loc[gpd.sjoin(des,poly,predicate='intersects',how='inner').index.unique()];pp=ptar.loc[gpd.sjoin(ptar,poly,predicate='intersects',how='inner').index.unique()];hh=gpd.clip(hid,poly)
    fig,ax=plt.subplots(figsize=(9,9));mun.boundary.plot(ax=ax,color='#ccc',lw=.4);hh.plot(ax=ax,color='#3686b7',lw=.7);poly.boundary.plot(ax=ax,color='#222',lw=1.5);ee.plot(ax=ax,color='#542788',markersize=10,alpha=.65);dd.plot(ax=ax,color='#d73027',marker='x',markersize=45);pp.plot(ax=ax,color='#1b9e77',marker='^',markersize=65);extent(ax,poly,.08);add_north(ax);add_scale(ax,2000);ax.set_axis_off();finish(fig,ax,f'Detalle municipal: {m}','Establecimientos, PTAR, descargas y red hidrográfica disponible',[Line2D([0],[0],color='#3686b7',label='Red hidrográfica'),Patch(fill=False,edgecolor='#222',label='Límite municipal'),Line2D([0],[0],marker='o',color='none',markerfacecolor='#542788',label='Establecimientos',markersize=5),Line2D([0],[0],marker='x',color='#d73027',linestyle='none',label='Descargas'),Line2D([0],[0],marker='^',color='none',markerfacecolor='#1b9e77',label='PTAR')],'Parte 2; INEGI CNGMD/RH18; compilación PTAR',MAP/f'{num:02d}_detalle_{m.lower().replace(" ","_").replace("á","a")}.png')
zc=sub.merge(zon[['subnucleo_id','criterio_vacio_informacion','zona_candidata_investigacion']],on='subnucleo_id');fig,ax=plt.subplots(figsize=(9,9));base(ax,cuenca,mun,hid);zc[zc.criterio_vacio_informacion].plot(ax=ax,color='#fee08b',edgecolor='#d95f0e',alpha=.65);zc[zc.zona_candidata_investigacion].boundary.plot(ax=ax,color='#7f0000',lw=2);labels(ax,mun,targets);finish(fig,ax,'Vacíos de información y zonas candidatas','La clasificación señala necesidades de investigación, no carencias reales ni contaminación',H+[Patch(facecolor='#fee08b',edgecolor='#d95f0e',label='Vacío de información'),Patch(fill=False,edgecolor='#7f0000',label='Coincidencia textil–descarga–cauce')],'Integración Parte 3; criterios en 08_zonas_candidatas_y_vacios.csv',MAP/'09_vacios_y_zonas_candidatas.png')
print({'tablas':9,'mapas':9,'subnucleos':len(subtab),'candidatas':int(zon.zona_candidata_investigacion.sum())})
