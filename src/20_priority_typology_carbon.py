# 우선 대상(공급 공백 ∩ 차량 의존) 유형화 + 탄소
import pandas as pd, numpy as np, duckdb
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
con=duckdb.connect('work/mob.duckdb')
tp=con.execute("""select o code, sum(case when left(st,2) in ('10','11','12','13','14','15') then cnt else 0 end)/sum(cnt) midday_share
 from allw where left(o,2)='11' and left(d,2)='11' and m='8' and dist between 1000 and 4999 group by o""").fetchdf()
D=D.merge(tp,on='code',how='left')
G=D[D.priority].copy()
G['recip_pct']=G.recip_pct.fillna(D.recip_pct.median())  # 반포본동 수급자 자료 미매칭 → 서울 중앙값
F=['sub_dist_km','route_stop_density','pop_density','elder_pct','recip_pct','car_share15','midday_share']
Z=StandardScaler().fit_transform(G[F])
for k in (2,3,4): print(k,'silhouette',round(silhouette_score(Z,KMeans(k,n_init=20,random_state=0).fit(Z).labels_),3))
km=KMeans(3,n_init=20,random_state=0).fit(Z); G['cluster']=km.labels_
prof=G.groupby('cluster')[F+['car15']].mean(); prof['n']=G.cluster.value_counts().sort_index()
prof['sub_dist_km']=prof.sub_dist_km.round(2); print(prof.round(2).to_string())
for c in range(3): print(c, G[G.cluster==c].sort_values('car15',ascending=False).apply(lambda r:f"{r.gu} {r.nm}",axis=1).tolist())
seoul={'sub_dist_km':D.sub_dist_km.mean(),'route_stop_density':D.route_stop_density.mean(),'car_share15':D.car15.sum()/D.all15.sum(),'elder_pct':D.elder_pct.mean(),'recip_pct':D.recip_pct.mean()}
print('서울 평균',{k:round(v,3) for k,v in seoul.items()})
G.to_csv('work/priority_clusters.csv',index=False,encoding='utf-8-sig')
# 탄소
con.register('g',G[['code','cluster']])
B="from allw a join g on a.o=g.code where left(a.d,2)='11' and a.m='8' and a.dist between 1000 and 4999"
trips,pkm,pkm_c=con.execute(f"select sum(cnt)/4, sum(cnt*dist)/4000, sum(case when tm>0 and dist/tm*0.06>=5 then cnt*dist else 0 end)/4000 {B}").fetchone()
allt=con.execute("select sum(cnt)/4 from allw where left(o,2)='11' and left(d,2)='11' and m='8' and dist between 1000 and 4999").fetchone()[0]
print(f"우선 대상 {len(G)}곳 출발 1~5km 차량 이동 {trips:,.0f}건/일 (서울의 {100*trips/allt:.1f}%)")
rows=[]
for lab,p,occ,det,ef in [('보수',pkm_c,1.8,1.2,187),('기본',pkm,1.3,1.3,220),('높음',pkm,1.3,1.4,255)]:
    t=p*det/occ*ef/1e6*365; rows.append((lab,round(t),round(t*.1),round(t*.2),round(t*.3)))
R=pd.DataFrame(rows,columns=['가정','연간배출_t','10%전환_t','20%전환_t','30%전환_t']); print(R.to_string(index=False))
by=con.execute(f"select g.cluster, sum(cnt*dist)/4000*220/1e6*365 t {B} group by 1 order by 1").fetchdf(); print(by.round(0).to_string(index=False))
R.to_csv('out/priority_carbon.csv',index=False,encoding='utf-8-sig')
