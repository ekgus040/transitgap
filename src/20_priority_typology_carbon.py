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
# 군집 번호를 프로필로 고정(하위 스크립트 공통): A 외곽 저밀형=2(역 거리 최대), C 취약 고령형=0(고령 비율 최대), B 버스 연계 부족형=1
_p=G.groupby('cluster')[['sub_dist_km','elder_pct']].mean(); _a=_p.sub_dist_km.idxmax(); _c=_p.drop(_a).elder_pct.idxmax(); _b=[k for k in _p.index if k not in (_a,_c)][0]
G['cluster']=G.cluster.map({_a:2,_b:1,_c:0})
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
# 보조 분석: 평일(5/7)·주말(2/7)로 대표 주간 가중 평균을 구성해 연간 환산.
# 4일 중 실제 요일을 달력에서 확인하며, 평일/주말을 고정된 파일명 순서로 가정하지 않음.
from datetime import date
DAY_MAP={'0826':date(2026,8,26),'0827':date(2026,8,27),
         '0828':date(2026,8,28),'0829':date(2026,8,29)}
for dy,dt in DAY_MAP.items():
    assert dt.strftime('%m%d')==dy
assert sum(dt.weekday()<5 for dt in DAY_MAP.values())==3
rows_by_day=con.execute(f"""select a.dy,
 sum(a.cnt) trips,
 sum(a.cnt*a.dist)/1000 pkm,
 sum(case when a.tm>0 and a.dist/a.tm*0.06>=5 then a.cnt*a.dist else 0 end)/1000 pkm_conservative
 {B} group by a.dy order by a.dy""").fetchdf()
rows_by_day['day_type']=rows_by_day.dy.map(lambda d: 'weekday' if DAY_MAP[str(d)].weekday()<5 else 'weekend')
assert set(rows_by_day.dy.astype(str))==set(DAY_MAP), '원자료 날짜 누락: 연간 추정 중단'
weighted={}
for col in ('trips','pkm','pkm_conservative'):
    means=rows_by_day.groupby('day_type')[col].mean()
    weighted[col]=(5*means['weekday']+2*means['weekend'])/7
annual=[]
for lab,pcol,occ,det,ef in [('보수','pkm_conservative',1.8,1.2,187),
                            ('기본','pkm',1.3,1.3,220),('높음','pkm',1.3,1.4,255)]:
    annual_t=weighted[pcol]*det/occ*ef/1e6*365
    annual.append({'가정':lab,'연간_차량배출량_t':annual_t,
                   '10%_차량배출회피잠재량_t':annual_t*.1,
                   '20%_차량배출회피잠재량_t':annual_t*.2,
                   '30%_차량배출회피잠재량_t':annual_t*.3})
pd.DataFrame(annual).to_csv('out/priority_carbon_weekweighted.csv',index=False,encoding='utf-8-sig')
rows_by_day.to_csv('out/priority_carbon_daily_inputs.csv',index=False,encoding='utf-8-sig')
print('대표 주간 가중 차량 이동량/일:',round(weighted['trips']))
print('주의: 수단 전환 시 대체 교통수단 배출을 차감하지 않았으므로 순감축량이 아님.')
