# 동별 버스 서비스 수준: 경유 노선 수(정류장이 동 안에 있는 고유 노선), 노선-정류장 쌍 밀도
import json, pandas as pd, numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely.ops import transform
g=json.load(open('data_raw/HangJeongDong_ver20250401.geojson'))
F=[(f['properties']['adm_cd2'][:8], shape(f['geometry'])) for f in g['features'] if f['properties']['sido']=='11']
codes=[c for c,_ in F]; polys=[p for _,p in F]; tree=STRtree(polys)
proj=lambda x,y,z=None:(x*88.2,y*111.0)
area={c:transform(proj,p).area for c,p in F}
B=pd.read_excel('data_raw/서울시버스노선별정류소정보(20260902).xlsx')
B=B[(B['Y좌표']>37.4)&(B['Y좌표']<37.72)&(B['X좌표']>126.76)&(B['X좌표']<127.19)]
st=B.drop_duplicates('NODE_ID')[['NODE_ID','X좌표','Y좌표']]
def which(x,y):
    pt=Point(x,y)
    for i in tree.query(pt):
        if polys[i].contains(pt): return codes[i]
st['code']=[which(x,y) for x,y in zip(st['X좌표'],st['Y좌표'])]
print('stops',len(st),'assigned',st.code.notna().sum())
B=B.merge(st[['NODE_ID','code']],on='NODE_ID')
R=B.groupby('code').agg(bus_routes=('ROUTE_ID','nunique'), route_stop_pairs=('ROUTE_ID','size')).reset_index()
R['route_stop_density']=R.route_stop_pairs/R.code.map(area)
D=pd.DataFrame({'code':codes}).merge(R,on='code',how='left').fillna({'bus_routes':0,'route_stop_pairs':0,'route_stop_density':0})
D.to_csv('work/bus_routes_dong.csv',index=False)
print(D.describe().round(1).to_string())
