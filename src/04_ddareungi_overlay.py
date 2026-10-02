import json, pandas as pd, duckdb
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
st=pd.read_csv('data_raw/서울시 공공자전거 따릉이 대여소 마스터 정보.csv', encoding='cp949')
st=st[(st['위도']>30)&(st['경도']>120)]
print('stations with coords:', len(st))
g=json.load(open('data_raw/HangJeongDong_ver20250401.geojson'))
polys=[];codes=[]
for f in g['features']:
    if f['properties']['sido']=='11':
        polys.append(shape(f['geometry'])); codes.append(f['properties']['adm_cd2'][:8])
area={c:p.area for c,p in zip(codes,polys)}
tree=STRtree(polys)
cnt={c:0 for c in codes}
for lat,lon in zip(st['위도'],st['경도']):
    pt=Point(lon,lat)
    for i in tree.query(pt):
        if polys[i].contains(pt): cnt[codes[i]]+=1; break
print('assigned:', sum(cnt.values()))
con=duckdb.connect('work/mob.duckdb')
df=con.execute("select d.gu, d.nm, s.* from dong4 s join dong d using(code)").fetchdf()
df['stations']=df.code.map(cnt).fillna(0)
df['st_per_10k_short_car']=df.stations/(df.car15/10000)
# gap: top quartile short-car volume AND bottom quartile stations per short car trip
q_car=df.car15.quantile(0.75); q_st=df.st_per_10k_short_car.quantile(0.25)
df['gap']=(df.car15>=q_car)&(df.st_per_10k_short_car<=q_st)
df['car_share15']=(100*df.car15/df.all15).round(1)
df=df.sort_values('car15',ascending=False)
df.round(1).to_csv('out/dong_short_car_vs_ddareungi.csv',index=False,encoding='utf-8-sig')
print(f"thresholds: car15>={q_car:,.0f}/day, stations per 10k short-car trips<={q_st:.1f}")
print('gap dongs:', int(df.gap.sum()))
print(df[df.gap][['gu','nm','car15','car_share15','stations','st_per_10k_short_car']].round(1).head(20).to_string(index=False))
print('corr(car15, stations)=', round(df.car15.corr(df.stations),2))
