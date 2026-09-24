"""Figuras explicativas y explorador HTML autocontenido de la segunda pasada."""
from importlib import import_module
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
import plotly

comun=import_module("200_parte2_comun"); perfil=import_module("207_perfilar_clusters")
OUT=comun.OUT/"14_segunda_pasada"; FIG=OUT/"figuras"; FIG.mkdir(parents=True,exist_ok=True)
def save(fig,n): fig.savefig(FIG/f"{n}.png",dpi=220,bbox_inches="tight",facecolor="white"); plt.close(fig)
def main():
 sns.set_theme(style="whitegrid")
 # Robustez: etiqueta exacta y region visual superior derecha.
 s=pd.read_csv(comun.OUT/"05_seleccion/seleccion_escenarios.csv"); q=s[s.metodo.ne("OPTICS")]; p=q[q.rol.eq("PRINCIPAL")].iloc[0]
 fig,ax=plt.subplots(figsize=(9,7)); ax.axvspan(.8,1,color="#d9f0d3",alpha=.45); ax.axhspan(.8,1,color="#d9f0d3",alpha=.45)
 sns.scatterplot(data=q,x="ari_top5_mismo_metodo",y="ari_perturbacion_25m",hue="metodo",size="n_clusters",sizes=(30,180),ax=ax)
 ax.scatter(p.ari_top5_mismo_metodo,p.ari_perturbacion_25m,s=400,marker="*",c="black",label="Solución principal",zorder=9)
 ax.annotate("Región superior derecha:\nestable ante especificaciones\ny perturbaciones",(.82,.81),fontsize=10,bbox=dict(fc="white",ec="#238b45",alpha=.9))
 ax.set(xlim=(max(0,q.ari_top5_mismo_metodo.min()-.04),1.01),ylim=(max(0,q.ari_perturbacion_25m.min()-.04),1.01),xlabel="ARI medio con las 5 particiones más similares del mismo método",ylabel="ARI medio en 3 perturbaciones gaussianas de 25 m",title="Robustez espacial: dos fuentes de variación")
 ax.legend(loc="lower left",fontsize=8); save(fig,"01_robustez_ari_documentada")
 # Estabilidad sin interferencia: leyenda exterior y escala separada.
 pts=gpd.read_file(comun.OUT/"06_clusters/solucion_principal.gpkg",layer="establecimientos_membresia"); cu=gpd.read_file(comun.CUENCA).to_crs(pts.crs); x=pts[pts.dentro_cuenca.astype(bool)]
 fig,ax=plt.subplots(figsize=(10,9)); cu.boundary.plot(ax=ax,color="#222",lw=1)
 pal={"SENSIBLE":"#d73027","ESTABLE":"#80cdc1","NUCLEO_ROBUSTO":"#1b7837"}
 for k in pal: x[x.clase_persistencia.eq(k)].plot(ax=ax,color=pal[k],markersize=7,alpha=.7,label=k.replace("_"," ").title())
 ax.set_axis_off(); ax.set_title("Estabilidad de membresía entre especificaciones",fontsize=15,pad=12); ax.legend(loc="center left",bbox_to_anchor=(1.01,.5),title="Clase")
 xmin,xmax=ax.get_xlim(); ymin,ymax=ax.get_ylim(); L=5000; y=ymin+(ymax-ymin)*.04; xx=xmin+(xmax-xmin)*.06; ax.plot([xx,xx+L],[y,y],c="k",lw=3); ax.text(xx+L/2,y+(ymax-ymin)*.015,"5 km",ha="center",fontsize=9)
 fig.subplots_adjust(right=.78); save(fig,"02_estabilidad_membresia")
 # Mega-cluster etiquetado.
 mega=gpd.read_file(comun.OUT/"11_cierre/diagnostico_mega_cluster.gpkg",layer="establecimientos_subnucleos"); fig,ax=plt.subplots(figsize=(10,9)); noise=mega[mega.subnucleo_diagnostico.lt(0)]; noise.plot(ax=ax,c="#d0d0d0",markersize=4,alpha=.4,label="No asignado interno")
 core=mega[mega.subnucleo_diagnostico.ge(0)]; core.plot(ax=ax,column="subnucleo_diagnostico",cmap="tab20",markersize=9,alpha=.8)
 for k,g in core.groupby("subnucleo_diagnostico"):
  c=g.geometry.union_all().centroid; ax.text(c.x,c.y,str(int(k)),ha="center",va="center",fontsize=8,fontweight="bold",bbox=dict(boxstyle="circle,pad=.2",fc="white",ec="black",alpha=.85))
 ax.set_axis_off(); ax.set_title("18 subnúcleos exploratorios del mega-cluster 20",fontsize=15); ax.legend(loc="upper left"); save(fig,"03_subnucleos_mega_etiquetados")
 # Heatmaps compacto/ampliado.
 pr=pd.read_csv(comun.OUT/"07_perfiles/perfiles_clusters.csv"); pr=pr[pr.cluster.ge(0)].set_index("grupo_espacial")
 compact=["actividad_lavanderia_tintoreria","actividad_confeccion","actividad_fabricacion_telas","actividad_acabado_textil","maquila","mezclilla","humedo_explicito","proceso_seco_explicito"]
 for name,vars_,size in [("04_heatmap_compacto",compact,(11,8)),("05_heatmap_ampliado",perfil.SENALES,(15,9))]:
  m=pr[[f"pct__{v}" for v in vars_]]; m.columns=vars_; fig,ax=plt.subplots(figsize=size); sns.heatmap(m,cmap="YlGnBu",vmin=0,vmax=100,ax=ax,cbar_kws={"label":"Prevalencia dentro del cluster (%)"}); ax.set(xlabel="Etiqueta canónica",ylabel="",title="Composición multilabel"+(" ampliada" if "ampliado" in name else " compacta")); save(fig,name)
 # Tres matrices y dendrograma.
 for n,title in [("distancia_coseno_senales","Distancia coseno: prevalencias multilabel"),("distancia_jensen_shannon_scian3","Distancia Jensen–Shannon: composición SCIAN-3"),("distancia_combinada_50_50","Distancia combinada = 0.5 coseno + 0.5 JS")]:
  m=pd.read_csv(OUT/f"{n}.csv").set_index("grupo_espacial"); fig,ax=plt.subplots(figsize=(10,8)); sns.heatmap(m,cmap="mako_r",vmin=0,vmax=1,square=True,ax=ax,cbar_kws={"label":"Distancia (0=idéntico; 1=máxima)"}); ax.set_title(title); save(fig,"06_"+n)
 m=pd.read_csv(OUT/"distancia_combinada_50_50.csv").set_index("grupo_espacial"); z=linkage(squareform(m.values,checks=False),method="average"); fig,ax=plt.subplots(figsize=(12,6)); dendrogram(z,labels=m.index,leaf_rotation=65,ax=ax); ax.set(title="Dendrograma de perfiles (enlace promedio)",ylabel="Distancia combinada"); save(fig,"07_dendrograma_perfiles")
 # Ranking lavanderia.
 rank=pr.sort_values("pct__actividad_lavanderia_tintoreria"); fig,ax=plt.subplots(figsize=(9,7)); ax.barh(rank.index,rank.pct__actividad_lavanderia_tintoreria,color="#7b3294"); ax.axvline(80,ls="--",c="#b2182b",label="Umbral descriptivo 80%"); ax.set(xlabel="Lavandería/tintorería (%)",ylabel="",title="Ranking de los 18 clusters interiores"); ax.legend(); save(fig,"08_ranking_lavanderia")
 # HTML custom autocontenido: selector doble, metrica y filtros.
 datos=pd.read_csv(comun.OUT/"07_perfiles/establecimientos_perfilados_cuenca.csv",low_memory=False); datos=datos[datos.cluster.ge(0)]
 prof=pd.read_csv(comun.OUT/"07_perfiles/perfiles_clusters.csv"); prof=prof[prof.cluster.ge(0)]
 ficha=pd.read_csv(comun.OUT/"11_cierre/fichas_resumen_clusters.csv"); ficha=ficha[ficha.cluster.ge(0)]
 over=pd.read_csv(OUT/"top_rasgos_por_cluster.csv"); overmap=over.groupby("cluster").rasgo.apply(lambda z:", ".join(z)).to_dict()
 records=[]
 for _,r in prof.iterrows():
  f=ficha[ficha.cluster.eq(r.cluster)].iloc[0]; g=datos[datos.cluster.eq(r.cluster)]
  spatial=pts[pts.cluster.eq(r.cluster)&pts.dentro_cuenca.astype(bool)]
  point_rows=[[round(z.geometry.x,2),round(z.geometry.y,2),str(z.nom_est),str(z.desc_scian),str(z.localidad),round(float(z.probabilidad),3),round(float(z.persistencia_territorial),3)] for z in spatial.itertuples()]
  records.append({"id":r.grupo_espacial,"cluster":int(r.cluster),"n":int(r.n_dentro_cuenca),"municipio":r.municipio_principal,"localidad":r.localidad_principal,"estabilidad":round(r.persistencia_media,3),"probabilidad":round(r.probabilidad_media,3),"borde":f"{int(f.n_fuera_cuenca) if pd.notna(f.n_fuera_cuenca) else 0} fuera", "scian":" | ".join(map(str,g.scian_3.value_counts().head(3).index)),"sobre":overmap.get(r.grupo_espacial,"Ninguno bajo filtro conservador"),"pct":{v:round(float(r[f'pct__{v}']),2) for v in perfil.SENALES},"count":{v:int(r[f'n__{v}']) for v in perfil.SENALES},"points":point_rows,"cx":round(float(spatial.geometry.x.mean()),2),"cy":round(float(spatial.geometry.y.mean()),2)})
 boundary=[]
 for geom in cu.geometry:
  polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else [geom]
  for poly in polys: boundary.append([[round(x,2),round(y,2)] for x,y in poly.exterior.coords])
 payload=json.dumps(records,ensure_ascii=False); js=plotly.offline.get_plotlyjs()
 html=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Explorador de clusters Parte 2</title><style>body{{font-family:Arial,sans-serif;margin:22px;color:#24323d}}.controls{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}select,label{{margin:4px}}#meta{{white-space:pre-wrap;background:#eef4f7;padding:12px;border-radius:6px}}#status{{padding:8px;color:#176b35}}.note{{font-size:13px;color:#555}}.panel{{border:1px solid #ccd7dd;border-radius:8px;margin:18px 0;padding:12px}}h2{{margin:4px 0 8px}}</style><script>{js}</script></head><body><h1>Explorador autocontenido de los 18 clusters</h1><p class="note">Perfilado posterior: ninguna señal productiva intervino en el clustering. Pase el cursor por el mapa para conocer cada establecimiento y su cluster; haga clic para seleccionarlo en el comparador.</p><div class="panel"><h2>Mapa interactivo de la solución espacial</h2><div id="map" style="height:720px"></div><p class="note">Los colores identifican clusters, los números señalan sus centros y el contorno corresponde a la cuenca. El mapa usa coordenadas métricas UTM 14N y no incorpora hidrología.</p></div><div class="panel"><h2>Comparación de composición</h2><div class="controls"><label>A <select id="clusterA"></select></label><label>B <select id="clusterB"></select></label><label>Métrica <select id="metric"><option value="pct">Porcentaje</option><option value="count">Conteo</option></select></label><label><input id="present" type="checkbox"> Sólo señales presentes</label><label><input id="expanded" type="checkbox" checked> Conjunto ampliado</label></div><div id="status">Cargando visualización…</div><div id="chart" style="height:570px"></div><div id="meta"></div></div><script>
const D={payload};
const boundary={json.dumps(boundary)};
const compact={json.dumps(compact)};
const allSignals={json.dumps(perfil.SENALES)};
const clusterA=document.getElementById('clusterA'), clusterB=document.getElementById('clusterB');
const metric=document.getElementById('metric'), present=document.getElementById('present'), expanded=document.getElementById('expanded');
const meta=document.getElementById('meta'), status=document.getElementById('status');
for(const e of D){{ clusterA.add(new Option(e.id,e.id)); clusterB.add(new Option(e.id,e.id)); }}
clusterB.selectedIndex=Math.min(1,D.length-1);
function mapHover(c){{return `<b>${{c.id}}</b><br>n=${{c.n}} · ${{c.municipio}} / ${{c.localidad}}<br>Lavandería ${{c.pct.actividad_lavanderia_tintoreria}}% · Manufactura ${{c.pct.scian_textil}}%<br>Confección ${{c.pct.actividad_confeccion}}% · Acabado ${{c.pct.actividad_acabado_textil}}% · Maquila ${{c.pct.maquila}}%<br>Húmedo ${{c.pct.humedo_explicito}}% · Seco ${{c.pct.proceso_seco_explicito}}% · Mezclilla/pantalón ${{c.pct.senal_mezclilla_o_pantalon}}%<br>SCIAN-3: ${{c.scian}}<br>Rasgos: ${{c.sobre}}<br>Estabilidad ${{c.estabilidad}} · Probabilidad ${{c.probabilidad}} · Borde ${{c.borde}}`;}}
function drawMap(){{
 const traces=[];
 for(const ring of boundary) traces.push({{type:'scattergl',mode:'lines',x:ring.map(p=>p[0]),y:ring.map(p=>p[1]),line:{{color:'#263238',width:1.5}},hoverinfo:'skip',showlegend:false}});
 D.forEach((c,i)=>{{const color=`hsl(${{(i*137.5)%360}},65%,45%)`;traces.push({{type:'scattergl',mode:'markers',name:c.id,x:c.points.map(p=>p[0]),y:c.points.map(p=>p[1]),marker:{{size:6,color:color,opacity:.72}},customdata:c.points,meta:c.id,hovertemplate:mapHover(c)+'<br><b>%{{customdata[2]}}</b><br>%{{customdata[3]}}<br>Localidad: %{{customdata[4]}}<br>Prob. punto: %{{customdata[5]}} · Estab. punto: %{{customdata[6]}}<extra></extra>'}});}});
 traces.push({{type:'scattergl',mode:'text',x:D.map(c=>c.cx),y:D.map(c=>c.cy),text:D.map(c=>String(c.cluster)),textfont:{{size:12,color:'black'}},hoverinfo:'skip',showlegend:false}});
 Plotly.newPlot('map',traces,{{margin:{{l:25,r:20,t:10,b:35}},xaxis:{{title:'Este (m)',showgrid:false,zeroline:false}},yaxis:{{title:'Norte (m)',showgrid:false,zeroline:false,scaleanchor:'x',scaleratio:1}},legend:{{orientation:'h',y:-.12}},hovermode:'closest'}},{{responsive:true,scrollZoom:true}}).then(()=>{{document.getElementById('map').on('plotly_click',ev=>{{const id=ev.points[0].data.meta;if(id){{clusterA.value=id;draw();document.getElementById('chart').scrollIntoView({{behavior:'smooth'}});}}}});}});
}}
function draw(){{
 try {{
  const A=D.find(x=>x.id===clusterA.value), B=D.find(x=>x.id===clusterB.value), m=metric.value;
  let vars=[...(expanded.checked?allSignals:compact)];
  if(present.checked) vars=vars.filter(v=>A[m][v]>0||B[m][v]>0);
  vars.sort((x,y)=>Math.max(B[m][y],A[m][y])-Math.max(B[m][x],A[m][x]));
  Plotly.react('chart',[{{type:'bar',orientation:'h',name:A.id,y:vars,x:vars.map(v=>A[m][v]),hovertemplate:'%{{y}}: %{{x}}<extra>'+A.id+'</extra>'}},{{type:'bar',orientation:'h',name:B.id,y:vars,x:vars.map(v=>B[m][v]),hovertemplate:'%{{y}}: %{{x}}<extra>'+B.id+'</extra>'}}],{{barmode:'group',margin:{{l:240,r:25,t:30,b:60}},xaxis:{{title:m==='pct'?'Prevalencia (%)':'Conteo'}},legend:{{orientation:'h'}}}},{{responsive:true}});
  meta.textContent=[A,B].map(x=>`${{x.id}} | n=${{x.n}} | ${{x.municipio}} / ${{x.localidad}}\\nSCIAN-3: ${{x.scian}}\\nSobrerrepresentados: ${{x.sobre}}\\nEstabilidad=${{x.estabilidad}} | Probabilidad=${{x.probabilidad}} | Borde=${{x.borde}}`).join('\\n\\n');
  status.textContent='Visualización lista · 18 clusters disponibles';
 }} catch(err) {{ status.textContent='Error al dibujar: '+err.message; status.style.color='#b2182b'; console.error(err); }}
}}
for(const control of [clusterA,clusterB,metric,present,expanded]) control.addEventListener('change',draw);
if(typeof Plotly==='undefined'){{status.textContent='Error: la biblioteca gráfica no quedó incorporada.';status.style.color='#b2182b';}}else{{drawMap();draw();}}
</script></body></html>'''
 (OUT/"explorador_interactivo_clusters.html").write_text(html,encoding="utf-8")
 # Registro de lectura para las figuras nuevas.
 reg=[
 ["01_robustez_ari_documentada","57 escenarios espaciales; panel sin OPTICS para ARI perturbado","ARI global","Comparación de particiones completas; media top-5 y 3 perturbaciones","Alto=particiones similares","Principal en región alta-alta","diagnostico_ari_variantes.csv","ARI global sensible a categorías grandes"],
 ["02_estabilidad_membresia","4,010 puntos interiores","Fracción de 5 especificaciones","Acuerdo individual con cluster emparejado por Jaccard","1=conserva membresía siempre","Predominan núcleos robustos","componentes_estabilidad_por_cluster.csv","No es cohesión ni persistencia HDBSCAN"],
 ["03_subnucleos_mega_etiquetados","1,997 puntos del cluster 20","HDBSCAN leaf espacial","mcs=30,min_samples=10","Etiqueta>=0=subnúcleo; -1=no asignado","18 subnúcleos, 44.5% no asignado","subnucleos_mega_cluster_documentados.csv","Diagnóstico posterior; no cambia solución"],
 ["04/05_heatmap","18 clusters interiores","Prevalencia multilabel","media de indicadores booleanos","Alto=mayor fracción, columnas no suman 100","Composición heterogénea","diccionario_variables_analiticas.csv","Etiquetas correlacionadas/no exclusivas"],
 ["06/07_distancias","18 perfiles","coseno, JS y combinación","0.5 d_cos+0.5 d_JS","0=perfiles iguales","Pares similares documentados","explicacion_pares_similares.csv","Perfil posterior, no proximidad geográfica"],
 ["08_ranking_lavanderia","18 clusters","prevalencia lavandería","conteo/n","80% es umbral descriptivo","ninguno alcanza 80%","perfiles_clusters.csv","No prueba vínculo productivo/hídrico"]]
 comun.guardar_csv(pd.DataFrame(reg,columns=["figura","datos","metrica","calculo","lectura","conclusion","resultados_completos","limitacion"]),OUT/"registro_documentacion_figuras.csv")
 print("Figuras y HTML generados")
if __name__=="__main__": main()
