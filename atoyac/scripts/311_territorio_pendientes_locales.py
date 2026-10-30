"""Exploración interna de Santa Ana, cobertura MDT, pendientes y mapas territoriales."""
from pathlib import Path
import json,hashlib
import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
from scipy.spatial import cKDTree
from shapely import unary_union
from shapely.geometry import Point,LineString,box,shape
from shapely.ops import substring
from pyproj import Transformer
import rasterio
from rasterio.features import shapes
from rasterio.warp import calculate_default_transform,reproject,Resampling
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/parte_3/12_vialidades_amplias'
CRS='EPSG:32614'
FOCUS=ROOT/'outputs/parte_3/09_foco_santa_ana_huejotzingo/foco_santa_ana_huejotzingo.gpkg'

def sample(points,terrain):
    x=np.array([p.x for p in points]);y=np.array([p.y for p in points]);values=np.full(len(points),np.nan)
    for data,tr,tf in terrain:
        xx,yy=tf.transform(x,y);rr,cc=rasterio.transform.rowcol(tr,xx,yy);rr=np.array(rr);cc=np.array(cc)
        sel=(rr>=0)&(cc>=0)&(rr<data.shape[0])&(cc<data.shape[1])&np.isnan(values);ix=np.flatnonzero(sel)
        if len(ix):values[ix]=data[rr[ix],cc[ix]].filled(np.nan)
    return values

def main():
    gp=OUT/'grafo_corredores_exploratorios.gpkg'
    graph=nx.read_graphml(OUT/'grafo_vial.graphml')
    nodes=gpd.read_file(gp,layer='nodos_grafo');edges=gpd.read_file(gp,layer='aristas_grafo')
    links=gpd.read_file(gp,layer='puntos_enlace');plants=gpd.read_file(gp,layer='ptar_destinos')
    est=gpd.read_file(FOCUS,layer='establecimientos_foco')
    priority=gpd.read_file(gp,layer='establecimientos_prioritarios')
    roads=gpd.read_file(gp,layer='vialidades_fuente');globalroutes=gpd.read_file(gp,layer='rutas_minimas')
    hydro=gpd.read_file(gp,layer='hidrografia_contexto')
    santa=links[(links.zona=='santa_ana')&(links.tipo=='establecimiento')].componente.value_counts().idxmax()
    ends=nodes[(nodes.componente==santa)&nodes.grado.eq(1)].copy()
    ends['dist_a_ptar_m']=ends.distance(plants.geometry.union_all())
    gates=[]
    for _,r in ends.sort_values(['dist_a_ptar_m','nodo_id']).iterrows():
        if gates and min(r.geometry.distance(p['geometry']) for p in gates)<250:continue
        gates.append({'extremo_id':f'EXT_{len(gates)+1:02d}','nodo_id':r.nodo_id,'criterio':'extremo vial existente cercano a PTAR; inspeccion, no conexion confirmada','geometry':r.geometry})
        if len(gates)==2:break
    gates=gpd.GeoDataFrame(gates,crs=CRS)
    xyz=np.c_[nodes.geometry.x,nodes.geometry.y];tree=cKDTree(xyz)
    edge_lookup=edges.set_index('arista_id');attach=links.set_index('punto_id')
    local=[]
    for _,o in priority[priority.zona_analisis.eq('santa_ana')].iterrows():
        at=attach.loc[o.establecimiento_id];line=edge_lookup.loc[at.arista_id].geometry
        foot=line.interpolate(line.project(o.geometry));distance,index=tree.query((foot.x,foot.y));assert distance<1e-5
        source=nodes.iloc[index].nodo_id
        for _,gate in gates.iterrows():
            path=nx.shortest_path(graph,source,gate.nodo_id,weight='longitud_m')
            geom=LineString([(graph.nodes[n]['x_utm'],graph.nodes[n]['y_utm']) for n in path])
            length=sum(graph[a][b]['longitud_m'] for a,b in zip(path[:-1],path[1:]))
            assert abs(geom.length-length)<.001
            local.append({'ruta_id':o.establecimiento_id+'_'+gate.extremo_id,'origen_id':o.establecimiento_id,
                'zona':'santa_ana','destino_id':gate.extremo_id,'destino':'extremo de inspeccion '+gate.extremo_id,
                'tipo':'exploracion_local_no_ruta_a_ptar','longitud_vial_m':length,'geometry':geom})
    local=gpd.GeoDataFrame(local,crs=CRS)
    terrain=[];footprints=[];raster_inventory=[];cartographic=[]
    for path in sorted((ROOT/'data/raw/terreno').rglob('*_mt.bil')):
        with rasterio.open(path) as src:
            terrain.append((src.read(1,masked=True),src.transform,Transformer.from_crs(CRS,src.crs,always_xy=True)))
            valid=src.read_masks(1)>0
            poly=unary_union([shape(s) for s,v in shapes(valid.astype('uint8'),mask=valid,transform=src.transform) if v==1])
            footprints.append(gpd.GeoDataFrame([{'fuente':str(path.relative_to(ROOT)),'resolucion_m':src.res[0],'geometry':poly}],crs=src.crs).to_crs(CRS))
            tf,w,h=calculate_default_transform(src.crs,CRS,src.width,src.height,*src.bounds,resolution=15)
            elevation=np.full((h,w),np.nan,dtype='float32')
            reproject(terrain[-1][0].filled(np.nan),elevation,src_transform=src.transform,src_crs=src.crs,
                src_nodata=np.nan,dst_transform=tf,dst_crs=CRS,dst_nodata=np.nan,resampling=Resampling.average)
            assert np.nanmin(elevation)>0 and np.nanmax(elevation)<10000, 'NoData no enmascarado'
            gy,gx=np.gradient(elevation,abs(tf.e),tf.a);slope=100*np.hypot(gx,gy)
            for suffix,data in [('elevacion_15m',elevation),('pendiente_pct_15m',slope)]:
                output=OUT/f'{path.stem}_{suffix}.tif'
                with rasterio.open(output,'w',driver='GTiff',width=w,height=h,count=1,dtype='float32',
                    crs=CRS,transform=tf,nodata=-9999,compress='deflate') as dst:
                    dst.write(np.where(np.isfinite(data),data,-9999).astype('float32'),1)
                    dst.update_tags(uso='cartografia exploratoria; no diseno hidraulico',mdt_fuente=str(path.relative_to(ROOT)),metodo='MDT promedio a 15m; pendiente=100*hypot(gradiente_x,gradiente_y)')
            cartographic.append((elevation,slope,tf))
            raster_inventory.append({'fuente':str(path.relative_to(ROOT)),'resolucion_original_m':src.res[0],
                'crs_original':str(src.crs),'crs_cartografia':CRS,'resolucion_cartografia_m':15,
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    coverage=gpd.GeoDataFrame(pd.concat(footprints,ignore_index=True),crs=CRS)
    valid_area=coverage.geometry.union_all()
    # Cobertura exacta geométrica de la traza sobre máscara MDT y pendientes cada 100 m.
    allroutes=pd.concat([globalroutes[['ruta_id','origen_id','zona','destino_id','destino','longitud_vial_m','geometry']],local],ignore_index=True)
    allroutes=gpd.GeoDataFrame(allroutes,crs=CRS)
    profiles=[];grades=[];metrics=[]
    for _,r in allroutes.iterrows():
        line=r.geometry
        ds=np.unique(np.r_[np.arange(0,line.length,20),line.length]);zz=sample([line.interpolate(float(d)) for d in ds],terrain)
        for d,z in zip(ds,zz):profiles.append({'ruta_id':r.ruta_id,'distancia_m':d,'z_mdt_m':z})
        d100=np.unique(np.r_[np.arange(0,line.length,100),line.length]);z100=sample([line.interpolate(float(d)) for d in d100],terrain)
        intervals=[]
        for j in range(len(d100)-1):
            a,b=d100[j:j+2];length=b-a;geom=substring(line,float(a),float(b))
            covered=geom.intersection(valid_area).length
            known=np.isfinite(z100[j:j+2]).all() and covered>=length-.01
            grade=100*(z100[j+1]-z100[j])/length if known else np.nan
            record={'ruta_id':r.ruta_id,'desde_m':a,'hasta_m':b,'pendiente_longitudinal_pct':grade,'intervalo_mdt_completo':bool(known)}
            grades.append(record);intervals.append(record)
        length_valid=line.intersection(valid_area).length
        known=[p for p in intervals if p['intervalo_mdt_completo']]
        ups=[p for p in known if p['pendiente_longitudinal_pct']>.5]
        metrics.append({'ruta_id':r.ruta_id,'zona':r.zona,'destino_id':r.destino_id,
            'tipo':'local_inspeccion' if r.destino_id.startswith('EXT') else 'hacia_ptar',
            'longitud_vial_m':line.length,'longitud_con_mdt_m':length_valid,'cobertura_longitud_pct':100*length_valid/line.length,
            'muestras_mdt_validas_pct':100*np.isfinite(zz).mean(),'desnivel_final_menos_inicio_m':zz[-1]-zz[0],
            'pendiente_global_pct':100*(zz[-1]-zz[0])/line.length,
            'intervalos_100m_validos':len(known),'intervalos_ascenso_mayor_05pct':len(ups),
            'longitud_intervalos_ascenso_m':sum(p['hasta_m']-p['desde_m'] for p in ups),
            'pendiente_min_100m_pct':min((p['pendiente_longitudinal_pct'] for p in known),default=np.nan),
            'pendiente_max_100m_pct':max((p['pendiente_longitudinal_pct'] for p in known),default=np.nan)})
    metrics=pd.DataFrame(metrics);metrics.to_csv(OUT/'cobertura_pendientes_rutas.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(profiles).to_csv(OUT/'perfiles_globales_y_locales_20m.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(grades).to_csv(OUT/'pendientes_longitudinales_100m.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(raster_inventory).to_csv(OUT/'inventario_mdt.csv',index=False,encoding='utf-8-sig')
    local=local.merge(metrics.drop(columns=['zona','destino_id','longitud_vial_m']),on='ruta_id')
    for name,g in [('extremos_inspeccion_santa_ana',gates),('rutas_locales_santa_ana',local),('cobertura_mdt_valida',coverage)]:
        assert g.is_valid.all() and g.crs.to_epsg()==32614
        g.to_file(gp,layer=name,driver='GPKG',index=False)
    territory=[]
    for zone in ['santa_ana','huejotzingo']:
        points=est[est.zona_analisis.eq(zone)];area=points.geometry.union_all().convex_hull.buffer(2000)
        rr=roads[roads.intersects(area)]
        zz=sample(list(points.geometry),terrain)
        territory.append({'zona':zone,'establecimientos':len(points),'establecimientos_con_mdt':int(np.isfinite(zz).sum()),
             'area_zona_con_mdt_pct':100*area.intersection(valid_area).area/area.area,
             'longitud_vial_con_mdt_pct':100*rr.geometry.intersection(valid_area).length.sum()/rr.length.sum()})
        for typ,title in [(0,'Elevacion del terreno'),(1,'Pendiente del terreno (%)')]:
            fig,ax=plt.subplots(figsize=(11,9));last=None
            for elev,slope,tf in cartographic:
                image=elev if typ==0 else slope;h,w=image.shape
                last=ax.imshow(image,extent=(tf.c,tf.c+w*tf.a,tf.f+h*tf.e,tf.f),origin='upper',
                    cmap='terrain' if typ==0 else 'YlOrRd',vmin=min(np.nanmin(t[0]) for t in cartographic) if typ==0 else 0,vmax=max(np.nanmax(t[0]) for t in cartographic) if typ==0 else 15,
                    alpha=.8,interpolation='nearest')
            rr.plot(ax=ax,color='#555555',linewidth=.4,alpha=.65)
            hydro[hydro.intersects(area)].plot(ax=ax,color='#1478b8',linewidth=.7)
            points.plot(ax=ax,color='#5e2b97',markersize=9,alpha=.8)
            plants.plot(ax=ax,color='#d7191c',marker='^',markersize=80)
            if zone=='santa_ana':gates.plot(ax=ax,color='black',marker='s',markersize=45)
            coverage.boundary.plot(ax=ax,color='#1b9e77',linewidth=1.3)
            x0,y0,x1,y1=area.bounds;ax.set_xlim(x0,x1);ax.set_ylim(y0,y1);ax.set_aspect('equal')
            fig.colorbar(last,ax=ax,label='Elevacion (m)' if typ==0 else 'Pendiente superficial (%)',shrink=.8)
            ax.set_title(f'{zone.replace("_"," ").title()}: {title}\nMDT original 1.5 m; cartografia agregada a 15 m; blanco = sin dato',fontsize=11)
            ax.legend(handles=[Line2D([0],[0],color='#555555',label='Vialidad'),Line2D([0],[0],color='#1478b8',label='Hidrografia'),
                 Line2D([0],[0],marker='o',linestyle='',color='#5e2b97',label='Establecimientos'),Line2D([0],[0],marker='^',linestyle='',color='#d7191c',label='PTAR'),Line2D([0],[0],color='#1b9e77',label='Limite MDT valido')],fontsize=7,loc='lower left')
            fig.tight_layout();fig.savefig(OUT/f'05_{zone}_{"elevacion" if typ==0 else "pendiente"}.png',dpi=180);plt.close(fig)
    pd.DataFrame(territory).to_csv(OUT/'cobertura_territorial.csv',index=False,encoding='utf-8-sig')
    # Corredores y perfiles separados por localidad para no confundir extremos con PTAR.
    pf=pd.DataFrame(profiles)
    for zone in ['santa_ana','huejotzingo']:
        rr=local if zone=='santa_ana' else globalroutes
        destinations=sorted(rr.destino_id.unique());fig,axes=plt.subplots(1,len(destinations),figsize=(6*len(destinations),8),squeeze=False)
        colors=['#1b9e77','#d95f02','#7570b3']
        for j,did in enumerate(destinations):
            ax=axes[0,j];roads.plot(ax=ax,color='#cccccc',linewidth=.35)
            qq=rr[rr.destino_id.eq(did)];qq.plot(ax=ax,color=colors[j],linewidth=.8,alpha=.6)
            priority[priority.zona_analisis.eq(zone)].plot(ax=ax,color='black',markersize=12)
            target=gates[gates.extremo_id.eq(did)] if zone=='santa_ana' else plants[plants.ptar_id.eq(did)]
            target.plot(ax=ax,color='red',marker='s' if zone=='santa_ana' else '^',markersize=70)
            x0,y0,x1,y1=qq.total_bounds;ax.set_xlim(x0-250,x1+250);ax.set_ylim(y0-250,y1+250);ax.set_aspect('equal')
            ax.set_title(did+(' | inspeccion, no PTAR' if zone=='santa_ana' else ''),fontsize=10)
        fig.suptitle('Santa Ana: rutas internas hacia extremos para inspeccion' if zone=='santa_ana' else 'Huejotzingo: caminos minimos hacia PTAR')
        fig.tight_layout();fig.savefig(OUT/f'06_{zone}_corredores.png',dpi=180);plt.close(fig)
        fig,ax=plt.subplots(figsize=(11,5))
        center=priority[priority.zona_analisis.eq(zone)].geometry.union_all().centroid
        pool=priority[priority.zona_analisis.eq(zone)]
        representative=pool.loc[pool.distance(center).idxmin()].establecimiento_id
        for did in destinations:
            q=pf[pf.ruta_id.eq(representative+'_'+did)]
            ax.plot(q.distancia_m,q.z_mdt_m,label=did)
        ax.set_title(f'{zone}: perfiles del origen representativo {representative}; huecos = sin MDT')
        ax.set_xlabel('Distancia por la vialidad (m)');ax.set_ylabel('Elevacion MDT (m)');ax.grid(alpha=.2);ax.legend()
        fig.tight_layout();fig.savefig(OUT/f'07_{zone}_perfiles.png',dpi=180);plt.close(fig)
    summary=metrics.groupby(['zona','destino_id','tipo']).agg(rutas=('ruta_id','size'),cobertura_media_pct=('cobertura_longitud_pct','mean'),cobertura_min_pct=('cobertura_longitud_pct','min'),longitud_min_m=('longitud_vial_m','min'),longitud_max_m=('longitud_vial_m','max'),pendiente_global_min_pct=('pendiente_global_pct','min'),pendiente_global_max_pct=('pendiente_global_pct','max'),rutas_con_ascensos=('intervalos_ascenso_mayor_05pct',lambda s:int(s.gt(0).sum()))).reset_index()
    summary.to_csv(OUT/'resumen_cobertura_pendientes.csv',index=False,encoding='utf-8-sig')
    def line_trace(fig,geoms,name,color,width=1,visible=True):
        xs=[];ys=[]
        for line in geoms:
            c=list(line.coords);xs.extend([q[0] for q in c]+[None]);ys.extend([q[1] for q in c]+[None])
        fig.add_trace(go.Scattergl(x=xs,y=ys,mode='lines',name=name,line=dict(color=color,width=width),visible=visible,hoverinfo='name'))
    fig=go.Figure();line_trace(fig,roads.geometry,'Calles disponibles','#aaaaaa')
    line_trace(fig,edges[edges.componente.eq(santa)].geometry,'Red de Santa Ana','#7570b3')
    fig.add_trace(go.Scattergl(x=priority.geometry.x,y=priority.geometry.y,mode='markers',text=priority.establecimiento_id+' | '+priority.zona_analisis,marker=dict(color='black',size=6),name='65 origenes prioritarios',hovertemplate='%{text}<extra></extra>'))
    fig.add_trace(go.Scatter(x=plants.geometry.x,y=plants.geometry.y,mode='markers+text',text=plants.nombre_fuente,marker=dict(color='red',size=12,symbol='triangle-up'),textposition='top center',name='PTAR'))
    fig.add_trace(go.Scatter(x=gates.geometry.x,y=gates.geometry.y,mode='markers+text',text=gates.extremo_id+' inspeccion',marker=dict(color='black',size=10,symbol='square'),name='Extremos inspeccion Santa Ana'))
    for did in globalroutes.destino_id.unique():line_trace(fig,globalroutes[globalroutes.destino_id.eq(did)].geometry,'Huejotzingo a '+did,'#d95f02',2,'legendonly')
    for did in local.destino_id.unique():line_trace(fig,local[local.destino_id.eq(did)].geometry,'Santa Ana a '+did+' (no PTAR)','#7570b3',2,'legendonly')
    for _,q in coverage.iterrows():
        for poly in ([q.geometry] if q.geometry.geom_type=='Polygon' else q.geometry.geoms):line_trace(fig,[poly.exterior],'Limite MDT 1.5 m','#1b9e77',2)
    fig.update_layout(title='Vialidades amplias: Huejotzingo hacia PTAR y Santa Ana dentro de su red<br><sup>Activa caminos en la leyenda; los extremos de inspeccion NO son plantas ni conexiones verificadas</sup>',height=900,template='plotly_white',legend=dict(orientation='h',y=-.12),margin=dict(b=200),xaxis_title='Este UTM (m)',yaxis_title='Norte UTM (m)')
    fig.update_yaxes(scaleanchor='x',scaleratio=1);fig.write_html(OUT/'explorador_territorio_grafos.html',include_plotlyjs=True)
    (OUT/'validacion_local_terreno.json').write_text(json.dumps({'rutas_locales':len(local),'extremos_inspeccion':len(gates),'rutas_ptar':len(globalroutes),'rutas_perfiladas':len(metrics),'cobertura_entre_0_y_100':bool(metrics.cobertura_longitud_pct.between(-.001,100.001).all()),'longitudes_locales_verificadas':True},indent=2),encoding='utf-8')
    print(summary.to_string(index=False));print(pd.DataFrame(territory).to_string(index=False))

if __name__=='__main__':main()
