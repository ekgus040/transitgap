# 추가 데이터 ②: 버스 정류소별 승하차(교통카드, 2026년 5~9월)로 생활이동 수단 코드(4·5=버스) 판정 검증
import pandas as pd, numpy as np, geopandas as gpd, duckdb
B=pd.read_csv('data_raw/extra/bus_stops.csv',dtype={'sid':str,'ars':str,'ym':str})
st=pd.read_csv('data_raw/서울시 버스정류소 위치정보.csv',encoding='cp949',dtype={'정류소번호':str})
st=st[st['정류소 타입']!='한강선착장']
st['sid']=st['정류소번호'].astype(str)
g=gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); g=g[g.sido=='11'][['adm_cd2','geometry']]; g['code']=g.adm_cd2.str[:8]
S=gpd.GeoDataFrame(st,geometry=gpd.points_from_xy(st['X좌표'],st['Y좌표']),crs=4326).sjoin(g.set_crs(4326,allow_override=True)[['code','geometry']],how='inner')
B['sid']=B.sid.astype(str)
m=B.merge(S[['sid','code']].drop_duplicates('sid'),on='sid',how='left')
print('정류소 매칭률(승차 기준)',round(m[m.code.notna()].cnt.sum()/m.cnt.sum(),3))
m=m.dropna(subset=['code'])
card4=m[(m.ym=='4day')].groupby('code').cnt.sum()/4
cardM=m[(m.kind=='off')&(m.wk=='wd')&(m.ym.isin(['202608','202609']))].groupby('code').cnt.sum()
con=duckdb.connect('work/mob.duckdb',read_only=True)
o=con.execute("select o code, sum(case when m in ('4','5') then cnt end)/4 bus, sum(case when m='6' then cnt end)/4 sub, sum(case when m='8' then cnt end)/4 car from allw where left(o,2)='11' group by o").fetchdf().set_index('code')
E=pd.concat([pd.read_csv(f'data_raw/extra/age_2026{x}.csv',dtype={'dong':str,'mode':str,'ym':str}) for x in ('08','09')])
E=E[(E.age=='all')&(E.wk=='wd')&(E.dong!='_days')]; E['dong']=E.dong.str[:8]
arr=E[E['mode'].isin(['4','5'])].groupby('dong').cnt.sum(); arrcar=E[E['mode']=='8'].groupby('dong').cnt.sum(); arrsub=E[E['mode']=='6'].groupby('dong').cnt.sum()
X=pd.DataFrame({'card4':card4,'bus4':o.bus,'car4':o.car,'sub4':o['sub']}).dropna(); X=X[(X.card4>0)&(X.bus4>0)]
Y=pd.DataFrame({'cardM':cardM,'arrbus':arr,'arrcar':arrcar,'arrsub':arrsub}).dropna(); Y=Y[(Y.cardM>0)]
r=lambda a,b: round(np.corrcoef(np.log(a),np.log(b))[0,1],3)
res={'동 수(4일)':len(X),'4일 출발 버스(4·5) vs 카드 승차 log상관':r(X.bus4,X.card4),
     '대조: 4일 출발 차량(8) vs 카드 승차':r(X.car4,X.card4),'대조: 4일 출발 지하철(6) vs 카드 승차':r(X.sub4,X.card4),
     '동 수(8~9월)':len(Y),'8~9월 도착 버스(4·5) vs 카드 하차 log상관':r(Y.arrbus,Y.cardM),
     '대조: 도착 차량(8) vs 카드 하차':r(Y.arrcar,Y.cardM),'대조: 도착 지하철(6) vs 카드 하차':r(Y.arrsub,Y.cardM),
     '스피어만(4일 버스 vs 카드)':round(X.bus4.corr(X.card4,method='spearman'),3)}
for k,v in res.items(): print(k,v)
print('규모비(생활이동 버스/카드 승차, 4일)',round(X.bus4.sum()/X.card4.sum(),2))
pd.Series(res).to_csv('out/bus_card_validation.csv',encoding='utf-8-sig')
