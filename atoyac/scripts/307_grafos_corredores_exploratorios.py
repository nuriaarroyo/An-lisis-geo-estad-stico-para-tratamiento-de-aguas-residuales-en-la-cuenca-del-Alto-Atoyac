"""Grafo y corredores exploratorios Santa Ana-Huejotzingo; no diseño sanitario."""
from pathlib import Path
import json, hashlib
import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
from scipy.spatial import cKDTree
from shapely import unary_union
from shapely.geometry import Point, LineString
from shapely.strtree import STRtree
from pyproj import Transformer
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/parte_3/10_grafos_corredores'
FOCUS=ROOT/'outputs/parte_3/09_foco_santa_ana_huejotzingo/foco_santa_ana_huejotzingo.gpkg'
ROADS=ROOT/'outputs/parte_3/08_integracion_vialidades_terreno/localidades_vialidades_terreno.gpkg'
CRS='EPSG:32614'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    est=gpd.read_file(FOCUS,layer='establecimientos_foco')
    plants=gpd.read_file(FOCUS,layer='ptar_nucleo_local')
    envelope=unary_union(list(est.geometry)+list(plants.geometry)).convex_hull.buffer(2500)
    roads=gpd.read_file(ROADS,layer='vialidades_regionales')
    roads=roads[roads.intersects(envelope)].copy()
    raw=nx.Graph()
    for line in roads.geometry:
        coords=[tuple(c[:2]) for c in line.coords]
        raw.add_edges_from(zip(coords[:-1],coords[1:]))
    # Nodo en todo cruce geométrico. Escenario permisivo: no hay cotas de pasos a desnivel.
    merged=unary_union(roads.geometry.to_numpy())
    G=nx.Graph()
    for line in merged.geoms:
        coords=[tuple(c[:2]) for c in line.coords]
        for a,b in zip(coords[:-1],coords[1:]):
            length=float(np.hypot(b[0]-a[0],b[1]-a[1]))
            if length>1e-7:G.add_edge(a,b,longitud_m=length)
    original_comps=sorted(nx.connected_components(G),key=len,reverse=True)
    comp={n:i for i,c in enumerate(original_comps) for n in c}
    edges=[]
    for idx,(a,b,d) in enumerate(sorted(G.edges(data=True),key=lambda v:(v[0],v[1]))):
        eid=f'AR_{idx:05d}';G[a][b]['arista_padre']=eid
        edges.append({'arista_id':eid,'componente':comp[a],'longitud_m':d['longitud_m'],'geometry':LineString([a,b])})
    edgeg=gpd.GeoDataFrame(edges,crs=CRS)
    mids=edgeg.copy();mids.geometry=mids.geometry.interpolate(.5,normalized=True)
    provenance=gpd.sjoin_nearest(mids[['arista_id','geometry']],roads[['vialidad_id','TIPO_VIAL','NOM_VIAL','geometry']],distance_col='error_m')
    provenance=provenance.sort_values(['arista_id','error_m','vialidad_id']).drop_duplicates('arista_id').set_index('arista_id')
    for c in ['vialidad_id','TIPO_VIAL','NOM_VIAL']:edgeg[c]=edgeg.arista_id.map(provenance[c])
    lookup=edgeg.set_index('arista_id')
    tree=STRtree(edgeg.geometry.to_numpy())
    attachments=[];splits={}
    for kind,points,key in [('establecimiento',est,'establecimiento_id'),('ptar',plants,'ptar_id')]:
        for _,r in points.iterrows():
            index=int(tree.nearest(r.geometry));edge=edgeg.iloc[index];line=edge.geometry
            pos=line.project(r.geometry);foot=line.interpolate(pos);node=(foot.x,foot.y)
            a,b=list(line.coords);a=tuple(a);b=tuple(b)
            if pos<1e-7:node=a
            elif line.length-pos<1e-7:node=b
            splits.setdefault(index,[]).append((pos,node))
            attachments.append({'punto_id':r[key],'tipo':kind,'zona':r.get('zona_analisis','destino'),
                 'arista_id':edge.arista_id,'dist_acceso_m':r.geometry.distance(Point(node)),
                 'componente':int(edge.componente),'nodo':node,'geometry':r.geometry,
                 'enlace':LineString([r.geometry,Point(node)])})
    for idx,items in splits.items():
        edge=edgeg.iloc[idx];a,b=[tuple(c) for c in edge.geometry.coords]
        chain=sorted([(0,a),(edge.longitud_m,b)]+items,key=lambda x:x[0])
        G.remove_edge(a,b)
        for (d1,n1),(d2,n2) in zip(chain[:-1],chain[1:]):
            if n1!=n2 and d2-d1>1e-7:G.add_edge(n1,n2,longitud_m=float(d2-d1),arista_padre=edge.arista_id)
    attach={r['punto_id']:r for r in attachments}
    # Raster se consulta en CRS nativo, sin sustituir MDS por MDT ni interpolar NoData.
    terrain=[]
    for path in sorted((ROOT/'data/raw/terreno').rglob('*_mt.bil')):
        with rasterio.open(path) as src:
            terrain.append((path,src.read(1,masked=True),src.transform,Transformer.from_crs(CRS,src.crs,always_xy=True)))
    def sample(points):
        xx=np.array([p.x for p in points]);yy=np.array([p.y for p in points]);z=np.full(len(points),np.nan)
        for _,data,tr,tf in terrain:
            x,y=tf.transform(xx,yy);rows,cols=rasterio.transform.rowcol(tr,x,y)
            rows=np.asarray(rows);cols=np.asarray(cols)
            inside=(rows>=0)&(rows<data.shape[0])&(cols>=0)&(cols<data.shape[1])&np.isnan(z)
            ix=np.flatnonzero(inside)
            if len(ix):z[ix]=data[rows[ix],cols[ix]].filled(np.nan)
        return z
    origin=est[est.prioridad_ambiental.isin(['alta','media'])].copy()
    rows=[];routes=[];profile_rows=[];usage={};paths={}
    for _,dest in plants.iterrows():
        did=dest.ptar_id;target=attach[did]
        distances,allpaths=nx.single_source_dijkstra(G,target['nodo'],weight='longitud_m')
        for _,o in origin.iterrows():
            oid=o.establecimiento_id;a=attach[oid]
            row={'origen_id':oid,'zona':o.zona_analisis,'prioridad':o.prioridad_ambiental,
                 'destino_id':did,'destino':dest.nombre_fuente,'comp_origen':a['componente'],
                 'comp_destino':target['componente'],'acceso_origen_m':a['dist_acceso_m'],
                 'acceso_destino_m':target['dist_acceso_m'],'conectado':a['nodo'] in distances}
            if row['conectado']:
                path=list(reversed(allpaths[a['nodo']]));length=distances[a['nodo']]
                line=LineString(path) if len(path)>1 else LineString([path[0],path[0]])
                rid=f'{oid}_{did}';paths[rid]=path
                positions=np.unique(np.r_[np.arange(0,line.length,20.),line.length])
                samples=[line.interpolate(float(d)) for d in positions];z=sample(samples)
                fraction=float(np.isfinite(z).mean())
                row.update({'ruta_id':rid,'longitud_vial_m':length,
                     'longitud_con_accesos_m':length+a['dist_acceso_m']+target['dist_acceso_m'],
                     'muestras_mdt_validas_pct':fraction*100,'perfil_completo':bool(np.isfinite(z).all()),
                     'z_inicio_m':z[0],'z_final_m':z[-1],
                     'desnivel_final_menos_inicio_m':z[-1]-z[0]})
                routes.append({**row,'geometry':line})
                for d,v in zip(positions,z):profile_rows.append({'ruta_id':rid,'distancia_m':float(d),'z_mdt_m':float(v)})
                used=set()
                for n1,n2 in zip(path[:-1],path[1:]):
                    parent=G[n1][n2]['arista_padre']
                    if parent not in used:
                        used.add(parent);usage.setdefault((o.zona_analisis,did,parent),set()).add(oid)
            else: row.update({'motivo':'componentes_viales_distintas; no se inventan enlaces'})
            rows.append(row)
    table=pd.DataFrame(rows);table.to_csv(OUT/'matriz_origen_destino.csv',index=False,encoding='utf-8-sig')
    profiles=pd.DataFrame(profile_rows);profiles.to_csv(OUT/'perfiles_20m.csv',index=False,encoding='utf-8-sig')
    corridor=[]
    for (zone,did,eid),oids in usage.items():
        e=lookup.loc[eid]
        corridor.append({'zona':zone,'destino_id':did,'arista_id':eid,'n_origenes':len(oids),
            'longitud_m':e.longitud_m,'vialidad_fuente_id':e.vialidad_id,
            'tipo_vial':e.TIPO_VIAL,'nombre_vial':e.NOM_VIAL,'geometry':e.geometry})
    shared=gpd.GeoDataFrame(corridor,geometry='geometry',crs=CRS)
    # Alternativas para el origen alcanzable más próximo al centroide de cada localidad.
    alternatives=[];alternative_summary=[]
    for zone in ['santa_ana','huejotzingo']:
        oo=origin[origin.zona_analisis.eq(zone)]
        center=oo.geometry.union_all().centroid
        for _,dest in plants.iterrows():
            did=dest.ptar_id;available=table[(table.zona==zone)&(table.destino_id==did)&table.conectado]
            if available.empty:continue
            candidates=oo[oo.establecimiento_id.isin(available.origen_id)]
            representative=candidates.loc[candidates.distance(center).idxmin()]
            oid=representative.establecimiento_id
            basepath=nx.shortest_path(G,attach[oid]['nodo'],attach[did]['nodo'],weight='longitud_m')
            def edgekey(a,b):return tuple(sorted((a,b)))
            base_edges={edgekey(a,b) for a,b in zip(basepath[:-1],basepath[1:])}
            base_len=sum(G[a][b]['longitud_m'] for a,b in zip(basepath[:-1],basepath[1:]))
            candidates=[]
            # Buscar desv?os sustanciales; la segunda ruta matem?tica puede diferir s?lo en cent?metros.
            trial=sorted(zip(basepath[:-1],basepath[1:]),key=lambda ab:G[ab[0]][ab[1]]['longitud_m'],reverse=True)[:80]
            for a,b in trial:
                saved=G[a][b].copy();G.remove_edge(a,b)
                try:altpath=nx.shortest_path(G,attach[oid]['nodo'],attach[did]['nodo'],weight='longitud_m')
                except nx.NetworkXNoPath:altpath=None
                G.add_edge(a,b,**saved)
                if altpath is None:continue
                altlen=sum(G[x][y]['longitud_m'] for x,y in zip(altpath[:-1],altpath[1:]))
                novel=sum(G[x][y]['longitud_m'] for x,y in zip(altpath[:-1],altpath[1:]) if edgekey(x,y) not in base_edges)
                if novel>=300 and novel/altlen>=.15:candidates.append((altlen,novel,altpath))
            selected=[(base_len,0,basepath)]
            if candidates:selected.append(min(candidates,key=lambda v:v[0]))
            for rank,(length,novel,path) in enumerate(selected,1):
                d={'zona':zone,'origen_id':oid,'destino_id':did,'alternativa':rank,'longitud_vial_m':length,
                   'longitud_nueva_vs_minima_m':novel,'incremento_vs_minima_pct':100*(length/base_len-1),
                   'criterio_busqueda':'desvio de >=300 m y >=15% de longitud nueva; hasta 80 cierres de arista'}
                alternatives.append({**d,'geometry':LineString(path)});alternative_summary.append(d)
    pd.DataFrame(alternative_summary).to_csv(OUT/'alternativas_representativas.csv',index=False,encoding='utf-8-sig')
    # Brechas geométricas entre componentes: diagnóstico, nunca aristas de ruta.
    gaps=[]
    targetcomps=set(attach[i]['componente'] for i in plants.ptar_id)
    oc=sorted(set(attach[i]['componente'] for i in origin.establecimiento_id))
    for c in oc:
        if c in targetcomps:continue
        aa=np.array(sorted(original_comps[c]));treea=cKDTree(aa)
        for tc in sorted(targetcomps):
            bb=np.array(sorted(original_comps[tc]));dd,ii=treea.query(bb);j=int(dd.argmin())
            gaps.append({'comp_origen':c,'comp_destino':tc,'distancia_brecha_m':float(dd[j]),
                'interpretacion':'distancia geometrica minima entre nodos; no corredor construible',
                'geometry':LineString([aa[ii[j]],bb[j]])})
    gapg=gpd.GeoDataFrame(gaps,geometry='geometry',crs=CRS)
    gapg.drop(columns='geometry').to_csv(OUT/'brechas_componentes.csv',index=False,encoding='utf-8-sig')
    comp_rows=[]
    for c,nodes in enumerate(original_comps):
        comp_rows.append({'componente':c,'n_nodos':len(nodes),
            'n_establecimientos':sum(a['tipo']=='establecimiento' and a['componente']==c for a in attachments),
            'n_prioritarios':sum(attach[i]['componente']==c for i in origin.establecimiento_id),
            'n_ptar':sum(attach[i]['componente']==c for i in plants.ptar_id)})
    pd.DataFrame(comp_rows).to_csv(OUT/'componentes.csv',index=False,encoding='utf-8-sig')
    checks=[]
    for r in routes:
        path=paths[r['ruta_id']]
        assert all(G.has_edge(a,b) for a,b in zip(path[:-1],path[1:]))
        assert abs(r['geometry'].length-r['longitud_vial_m'])<.001
        assert r['comp_origen']==r['comp_destino']
    links=gpd.GeoDataFrame([{k:v for k,v in a.items() if k not in ['nodo','enlace','geometry']}|{'geometry':a['enlace']} for a in attachments],crs=CRS)
    points=gpd.GeoDataFrame([{k:v for k,v in a.items() if k not in ['nodo','enlace']} for a in attachments],crs=CRS)
    nodeids={n:f'N_{i:05d}' for i,n in enumerate(sorted(G.nodes))}
    finalcomp={n:i for i,c in enumerate(sorted(nx.connected_components(G),key=len,reverse=True)) for n in c}
    nodes=gpd.GeoDataFrame([{'nodo_id':nodeids[n],'componente':finalcomp[n],'grado':G.degree(n),'geometry':Point(n)} for n in sorted(G.nodes)],crs=CRS)
    finaledges=gpd.GeoDataFrame([{'nodo_u':nodeids[a],'nodo_v':nodeids[b],'longitud_m':d['longitud_m'],
        'arista_padre':d['arista_padre'],'geometry':LineString([a,b])} for a,b,d in G.edges(data=True)],crs=CRS)
    routeg=gpd.GeoDataFrame(routes,crs=CRS)
    hydro=gpd.read_file(ROOT/'outputs/parte_3/parte_3_sistema_saneamiento_integrado.gpkg',layer='hidrografia').to_crs(CRS)
    hydro=hydro[hydro.intersects(envelope)]
    water=gpd.sjoin(routeg[['ruta_id','geometry']],hydro[['hidrografia_id','geometry']],predicate='intersects')
    water[['ruta_id','hidrografia_id']].drop_duplicates().to_csv(OUT/'intersecciones_hidrografia.csv',index=False,encoding='utf-8-sig')
    counts=water.groupby('ruta_id').hidrografia_id.nunique()
    table['elementos_hidrografia_intersectados']=table.ruta_id.map(counts).fillna(0).astype(int)
    table.loc[~table.conectado,'elementos_hidrografia_intersectados']=np.nan
    table.to_csv(OUT/'matriz_origen_destino.csv',index=False,encoding='utf-8-sig')
    routeg['elementos_hidrografia_intersectados']=routeg.ruta_id.map(counts).fillna(0).astype(int)
    graph_export=nx.relabel_nodes(G,nodeids,copy=True)
    nx.set_node_attributes(graph_export,{nodeids[n]:{'x_utm':n[0],'y_utm':n[1],'componente':finalcomp[n]} for n in G})
    nx.write_graphml(graph_export,OUT/'grafo_vial.graphml')
    layers={'nodos_grafo':nodes,'aristas_con_accesos':finaledges,'hidrografia_contexto':hydro,'vialidades_fuente':roads,'aristas_grafo':edgeg,'puntos_enlace':points,'accesos_geometricos':links,
        'establecimientos_prioritarios':origin,'ptar_destinos':plants,'rutas_minimas':routeg,
        'corredores_compartidos':shared,'alternativas':gpd.GeoDataFrame(alternatives,crs=CRS),'brechas_no_conectadas':gapg}
    tmp=OUT/'grafo_temporal.gpkg'
    if tmp.exists():tmp.unlink()
    for name,g in layers.items():
        if len(g):
            g.to_file(tmp,layer=name,driver='GPKG',index=False)
            checks.append({'capa':name,'filas':len(g),'invalidas':int((~g.is_valid).sum())})
    tmp.replace(OUT/'grafo_corredores_exploratorios.gpkg')
    # Mapas de componentes, rutas y reutilización por destino.
    colors=['#1b9e77','#d95f02','#7570b3']
    fig,ax=plt.subplots(figsize=(11,10))
    edgeg[~edgeg.componente.isin([0,1])].plot(ax=ax,color='#bbbbbb',linewidth=.5)
    edgeg[edgeg.componente.eq(0)].plot(ax=ax,color='#1b9e77',linewidth=.65,label='Componente Huejotzingo y PTAR')
    edgeg[edgeg.componente.eq(1)].plot(ax=ax,color='#7570b3',linewidth=.65,label='Componente Santa Ana')
    est.plot(ax=ax,color='#555555',markersize=5,alpha=.5)
    plants.plot(ax=ax,color='red',marker='^',markersize=90,label='PTAR candidatas')
    gapg.plot(ax=ax,color='red',linestyle='--',linewidth=2,label='Brecha: no conectada')
    for _,p in plants.iterrows():ax.annotate(p.nombre_fuente,(p.geometry.x,p.geometry.y),fontsize=7)
    ax.set_title('Componentes del grafo vial y brechas Santa Ana-Huejotzingo')
    ax.set_aspect('equal');ax.legend();fig.tight_layout();fig.savefig(OUT/'01_componentes_y_brechas.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(18,8))
    for ax,(_,dest),color in zip(axes,plants.iterrows(),colors):
        roads.plot(ax=ax,color='#dddddd',linewidth=.35)
        selected=shared[shared.destino_id.eq(dest.ptar_id)]
        if len(selected):selected.plot(ax=ax,color=color,linewidth=.4+3*selected.n_origenes/selected.n_origenes.max())
        origin.plot(ax=ax,color='#333333',markersize=9)
        gpd.GeoSeries([dest.geometry],crs=CRS).plot(ax=ax,color='red',marker='^',markersize=90)
        ax.set_title(dest.nombre_fuente,fontsize=9);ax.set_aspect('equal');ax.tick_params(labelsize=6)
    fig.suptitle('Corredores de caminos mínimos: grosor = orígenes que comparten tramo\nNo representa caudal, colector existente ni factibilidad hidráulica',fontsize=12)
    fig.tight_layout();fig.savefig(OUT/'02_corredores_por_destino.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5))
    for j,(_,dest) in enumerate(plants.iterrows()):
        alt=[a for a in alternative_summary if a['destino_id']==dest.ptar_id and a['alternativa']==1]
        if not alt:continue
        rid=alt[0]['origen_id']+'_'+dest.ptar_id
        pf=profiles[profiles.ruta_id.eq(rid)]
        ax.plot(pf.distancia_m,pf.z_mdt_m,label=dest.nombre_fuente,color=colors[j])
    ax.set_xlabel('Distancia por la vialidad desde origen representativo (m)');ax.set_ylabel('Elevación MDT (m)')
    ax.set_title('Perfiles exploratorios de terreno: huecos = elevación no disponible')
    ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(OUT/'03_perfiles_representativos.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(18,7))
    for ax,(_,dest),color in zip(axes,plants.iterrows(),colors):
        subset=gpd.GeoDataFrame(alternatives,crs=CRS)
        subset=subset[subset.destino_id.eq(dest.ptar_id)]
        roads.plot(ax=ax,color='#dddddd',linewidth=.35)
        subset[subset.alternativa.eq(1)].plot(ax=ax,color=color,linewidth=2,label='Minima')
        subset[subset.alternativa.eq(2)].plot(ax=ax,color='black',linewidth=1,linestyle='--',label='Desvio significativo')
        plants[plants.ptar_id.eq(dest.ptar_id)].plot(ax=ax,color='red',marker='^',markersize=60)
        x0,y0,x1,y1=subset.total_bounds;ax.set_xlim(x0-300,x1+300);ax.set_ylim(y0-300,y1+300)
        ax.set_title(dest.nombre_fuente,fontsize=9);ax.set_aspect('equal');ax.legend(fontsize=7);ax.tick_params(labelsize=6)
    fig.suptitle('Alternativas para origen representativo EST_03059 de Huejotzingo')
    fig.tight_layout();fig.savefig(OUT/'04_alternativas_representativas.png',dpi=180);plt.close(fig)
    summary={'tramos_fuente' :len(roads),'nodos_grafo_original':len(comp),'aristas_grafo_original':len(edgeg),
        'componentes_sin_nodar_cruces':nx.number_connected_components(raw),'componentes_nodando_cruces':len(original_comps),
        'nodos_con_accesos':len(G),'aristas_con_accesos':G.number_of_edges(),'origenes_prioritarios':len(origin),
        'pares_origen_destino':len(table),'rutas_conectadas':len(routes),
        'rutas_perfil_completo':int(table.perfil_completo.eq(True).sum()),
        'componentes_origenes':oc,'componentes_ptar':sorted(targetcomps),'validacion_rutas':'todas sobre aristas existentes y longitudes consistentes'}
    (OUT/'resumen.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'validacion_capas.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print(table.groupby(['zona','destino']).agg(origenes=('origen_id','size'),conectados=('conectado','sum'),min_m=('longitud_vial_m','min'),max_m=('longitud_vial_m','max'),perfil_medio_pct=('muestras_mdt_validas_pct','mean')).to_string())
    print(gapg.drop(columns='geometry').to_string(index=False))

if __name__=='__main__':main()
