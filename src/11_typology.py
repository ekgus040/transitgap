import pandas as pd, numpy as np, duckdb
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
D=pd.read_csv('work/dong_features_plus.csv',dtype={'code':str})
con=duckdb.connect('work/mob.duckdb')
# time profile of 1-5km car trips per origin dong: commute peak share (07-09,17-19) vs midday (10-16)
tp=con.execute("""select o code,
 sum(case when left(st,2) in ('07','08','17','18') then cnt else 0 end)/sum(cnt) peak_share,
 sum(case when left(st,2) in ('10','11','12','13','14','15') then cnt else 0 end)/sum(cnt) midday_share
 from allw where left(o,2)='11' and left(d,2)='11' and m='8' and dist between 1000 and 4999 group by o""").fetchdf()
D=D.merge(tp,on='code',how='left')
G=D[D.forced].copy()
X=G[['sub_dist_km','bus_density','pop_density','elder_pct','recip_pct','car_share15','midday_share']]
Z=StandardScaler().fit_transform(X)
for k in (2,3,4,5):
    km=KMeans(k,n_init=20,random_state=0).fit(Z); print(k,'silhouette',round(silhouette_score(Z,km.labels_),3))
k=3; km=KMeans(k,n_init=20,random_state=0).fit(Z); G['cluster']=km.labels_
prof=G.groupby('cluster')[['sub_dist_km','bus_density','pop_density','elder_pct','recip_pct','car_share15','midday_share','car15']].mean().round(2)
prof['n']=G.cluster.value_counts().sort_index()
print(prof.to_string())
for c in range(k):
    print(c, G[G.cluster==c].sort_values('car15',ascending=False).apply(lambda r:f"{r.gu} {r.nm}",axis=1).tolist())
G.to_csv('work/gap34_clusters.csv',index=False,encoding='utf-8-sig')
