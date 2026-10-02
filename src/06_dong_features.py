import json, pandas as pd, numpy as np, duckdb
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely.ops import transform
g=json.load(open('data_raw/HangJeongDong_ver20250401.geojson'))
F=[(f['properties']['adm_cd2'][:8], shape(f['geometry'])) for f in g['features'] if f['properties']['sido']=='11']
codes=[c for c,_ in F]; polys=[p for _,p in F]
proj=lambda x,y,z=None:(x*88.2,y*111.0)  # km at 37.5N
area={c:transform(proj,p).area for c,p in F}
cent={c:p.representative_point() for c,p in F}
tree=STRtree(polys)
def count(lats,lons):
    cnt=dict.fromkeys(codes,0)
    for la,lo in zip(lats,lons):
        pt=Point(lo,la)
        for i in tree.query(pt):
            if polys[i].contains(pt): cnt[codes[i]]+=1; break
    return cnt
U='data_raw/'
bike=pd.read_csv(U+'서울시 공공자전거 따릉이 대여소 마스터 정보.csv',encoding='cp949'); bike=bike[bike['위도']>30]
bus=pd.read_csv(U+'서울시 버스정류소 위치정보.csv',encoding='cp949'); bus=bus[bus['정류소 타입']!='한강선착장']
sub=pd.read_csv(U+'서울시 역사마스터 정보.csv',encoding='cp949')
sub=sub[(sub['위도']>37.4)&(sub['위도']<37.72)&(sub['경도']>126.76)&(sub['경도']<127.19)].drop_duplicates('역사명')
cb=count(bike['위도'],bike['경도']); cs=count(bus['Y좌표'],bus['X좌표']); cw=count(sub['위도'],sub['경도'])
print('assigned bike/bus/subway:',sum(cb.values()),sum(cs.values()),sum(cw.values()))
sp=[(la,lo) for la,lo in zip(sub['위도'],sub['경도'])]
def nearest_sub_km(c):
    p=cent[c]; return min(np.hypot((p.x-lo)*88.2,(p.y-la)*111.0) for la,lo in sp)
D=pd.DataFrame({'code':codes})
D['area_km2']=D.code.map(area); D['bike_st']=D.code.map(cb); D['bus_st']=D.code.map(cs); D['sub_st']=D.code.map(cw)
D['sub_dist_km']=D.code.map(nearest_sub_km)
sl={'11'+t.split(',')[0]:float(t.split(',')[1]) for t in open('data_raw/slope_by_dong.txt').read().split()}
D['slope_pct']=D.code.map(sl)
E=pd.read_csv('work/equity_dong.csv',dtype={'code':str})[['code','gu','nm','pop','elder_pct','recip_pct']]
D=D.merge(E,on='code',how='left')
D['pop_density']=D['pop']/D.area_km2
D['bike_density']=D.bike_st/D.area_km2; D['bus_density']=D.bus_st/D.area_km2
con=duckdb.connect('work/mob.duckdb')
M=con.execute("select code, car15, all15, car15_pkm from dong4").fetchdf()
D=D.merge(M,on='code',how='left'); D['car_share15']=D.car15/D.all15
D.to_csv('work/dong_features.csv',index=False,encoding='utf-8-sig')
print(D.describe().T[['mean','50%','min','max']].round(2).to_string())
