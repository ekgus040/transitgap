# 검토 반영 수치: 날짜별 우선 대상 안정성, 경사-버스 비중, 시범 DRT 수송 용량 기반 감축량
import duckdb, pandas as pd, numpy as np
con=duckdb.connect('work/mob.duckdb',read_only=True)
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
base=set(D[D.priority].code); gap=set(D[D.gap_supply].code)
d=con.execute("""select dy, o code, sum(case when m='8' then cnt else 0 end) car, sum(cnt) allm from allw
 where left(o,2)='11' and left(d,2)='11' and dist between 1000 and 4999 and m in ('4','5','6','7','8','9') group by 1,2""").fetchdf()
d=d[d.code.isin(set(D.code))]; d['s']=d.car/d.allm
for dy,g in d.groupby('dy'):
    sel=set(g[(g.s>=g.s.quantile(.75))&g.code.isin(gap)].code); print(f"{dy}: 우선 대상 {len(sel)}곳, 기본 40곳과 겹침 {len(sel&base)}")
P=d.pivot(index='code',columns='dy',values='s'); print('날짜 간 Spearman 최소', round(P.corr(method='spearman').values[np.triu_indices(4,1)].min(),3))
ms=con.execute("""select o code, sum(case when m in ('4','5') then cnt else 0 end)/sum(cnt) busS from allw
 where left(o,2)='11' and left(d,2)='11' and dist between 1000 and 4999 and m in ('4','5','6','7','8','9') group by 1""").fetchdf()
X=D.merge(ms,on='code'); q=X.slope_pct>=X.slope_pct.quantile(.75)
for k,g in X.groupby(q): print('경사 상위25%' if k else '나머지', '버스 비중', round(100*np.average(g['busS'],weights=g.all15),1))
per_vehicle=17439/(91*6)   # 셔클 시범 3개월 실적(대당 일평균)
trips=2*2*per_vehicle; t=trips*2.9*0.22*365/1000
print(f"셔클 대당 하루 {per_vehicle:.1f}명 → 4대 하루 {trips:.0f}건, 차량 대체 시 연 {t:.0f} tCO2")
