# 이동 격차 직접 지표: 1인당 이동 횟수, 같은 거리 대중교통 소요시간(분/km), 대중교통/차량 시간비
import duckdb, pandas as pd, numpy as np
con=duckdb.connect('work/mob.duckdb',read_only=True)
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
P=pd.read_csv('work/priority_clusters.csv',dtype={'code':str})[['code','cluster']]
D=D.merge(P,on='code',how='left')
lab={0:'C 취약 고령형',1:'B 버스 연계 부족형',2:'A 외곽 저밀형'}
D['grp']=np.where(D.priority, D.cluster.map(lab), np.where(D.gap_supply,'공백 동(우선 대상 외)','나머지 동'))
q=con.execute("""select o code,
 sum(cnt)/4 trips,
 sum(case when m in ('4','5','6') and dist between 1000 and 4999 then cnt end)/4 tr15,
 sum(case when m in ('4','5','6') and dist between 1000 and 4999 and tm>0 then cnt*tm end)/sum(case when m in ('4','5','6') and dist between 1000 and 4999 and tm>0 then cnt*dist/1000 end) tr_min_km,
 sum(case when m='8' and dist between 1000 and 4999 and tm>0 then cnt*tm end)/sum(case when m='8' and dist between 1000 and 4999 and tm>0 then cnt*dist/1000 end) car_min_km
 from allw where left(o,2)='11' and left(d,2)='11' and dist>=500 and m in ('4','5','6','7','8','9') group by o""").fetchdf()
X=D.merge(q,on='code',how='inner'); X=X[X['pop']>0]
X['trips_pc']=X.trips/X['pop']; X['ratio']=X.tr_min_km/X.car_min_km
def summ(g):
    return pd.Series({'동수':len(g),
     '1인당이동_중앙값':g.trips_pc.median(),
     '대중교통_분per_km':np.average(g.tr_min_km,weights=g.tr15),
     '차량_분per_km':np.average(g.car_min_km,weights=g.car15),
     '대중교통_차량_시간비':np.average(g.ratio,weights=g.tr15)})
order=['A 외곽 저밀형','B 버스 연계 부족형','C 취약 고령형','공백 동(우선 대상 외)','나머지 동']
T=X.groupby('grp').apply(summ).reindex(order); T.loc['서울 전체']=summ(X)
print(T.round(2).to_string())
X['q']=pd.qcut(X.access_gap.rank(method='first'),5,labels=['1(좋음)','2','3','4','5(공백)'])
Q=X.groupby('q',observed=True).apply(summ); print(Q.round(2).to_string())
# 구 고정효과: 접근성 지표와 대중교통 분/km, 1인당 이동
import statsmodels.formula.api as smf
X['l_rsd']=np.log(X.route_stop_density)
for y,w in [('tr_min_km','tr15'),('trips_pc','pop')]:
    d=X.dropna(subset=[y]); d=d[np.isfinite(d[y])]
    if y=='trips_pc': d=d[d.trips_pc<d.trips_pc.quantile(.95)]   # 업무·상업 중심 동(유입 인구 과다) 제외
    m=smf.wls(f'{y} ~ sub_dist_km + l_rsd + elder_pct + C(gu)',data=d,weights=d[w]).fit(cov_type='cluster',cov_kwds={'groups':d.gu.astype('category').cat.codes})
    print(y,'n',len(d),{k:(round(m.params[k],3),round(m.pvalues[k],4)) for k in ['sub_dist_km','l_rsd','elder_pct']})
case=X[X.nm.isin(['도봉1동','양재1동','진관동'])][['nm','trips_pc','tr_min_km','car_min_km','ratio']]
print(case.round(2).to_string(index=False))
T.round(3).to_csv('out/mobility_gap_by_type.csv',encoding='utf-8-sig'); Q.round(3).to_csv('out/mobility_gap_by_quintile.csv',encoding='utf-8-sig')
