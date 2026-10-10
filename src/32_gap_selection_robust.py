# 선정 강건성: 역 거리(동 대표점) 대신 역 반경 500·750m 커버 면적 비율로 공백 동·우선 대상 재선정 → 명단 겹침 확인
import pandas as pd, numpy as np, geopandas as gpd
from shapely.ops import unary_union
g=gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); g=g[g.sido=='11'].copy(); g['code']=g.adm_cd2.str[:8]; g=g.to_crs(5179)
st=pd.read_csv('data_raw/서울시 역사마스터 정보.csv',encoding='cp949')
S=gpd.GeoDataFrame(st,geometry=gpd.points_from_xy(st['경도'],st['위도']),crs=4326).to_crs(5179)
for r in (500,750):
    U=unary_union(S.buffer(r).geometry); g[f'cov{r}']=g.geometry.intersection(U).area/g.geometry.area
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str}).merge(g[['code','cov500','cov750']],on='code')
base_gap=set(D[D.gap_supply].code); base_pri=set(D[D.priority].code)
rows=[]
for v in ['cov500','cov750']:
    a=((1-D[v]).rank(pct=True)+(1-D.route_stop_density.rank(pct=True)))/2
    gap=a>=a.quantile(.75); pri=gap&(D.car_share15>=D.car_share15.quantile(.75))
    G=set(D[gap].code); P=set(D[pri].code)
    rows.append(dict(지표=v,공백동=len(G),공백겹침=len(G&base_gap),우선대상=len(P),우선겹침=len(P&base_pri),
        빠진곳=','.join(D[D.code.isin(base_pri-P)].nm),새로든곳=','.join(D[D.code.isin(P-base_pri)].nm)))
R=pd.DataFrame(rows); print(R.to_string(index=False))
P=pd.read_csv('work/priority_clusters.csv',dtype={'code':str})[['code','cluster']]
k=D.merge(P,on='code'); print(k.groupby('cluster')[['cov500','sub_dist_km']].mean().round(2))
print('서울 평균 cov500',round(D.cov500.mean(),2),'우선대상',round(D[D.priority].cov500.mean(),2))
print(D[D.nm.isin(['양재1동','도봉1동','방화2동','진관동','위례동','문정2동','목5동'])][['nm','sub_dist_km','cov500']].round(2).to_string(index=False))
R.to_csv('out/gap_selection_robust.csv',index=False,encoding='utf-8-sig')
