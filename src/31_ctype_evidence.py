# C유형 처방 근거 보강: 낮 시간(10~16시) 비중, 1~5km 도보·버스 의존, 대중교통 소요시간
import duckdb, pandas as pd, numpy as np
con=duckdb.connect('work/mob.duckdb',read_only=True)
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
P=pd.read_csv('work/priority_clusters.csv',dtype={'code':str})[['code','cluster']]
D=D.merge(P,on='code',how='left').drop(columns=['car15','all15'])
lab={0:'C',1:'B',2:'A'}
D['grp']=np.where(D.priority, D.cluster.map(lab), np.where(D.gap_supply,'공백(기타)','나머지'))
q=con.execute("""select o code,
 sum(case when m='8' and dist between 1000 and 4999 then cnt end) car15,
 sum(case when m='8' and dist between 1000 and 4999 and cast(st as int) between 10 and 15 then cnt end) car15_mid,
 sum(case when m='8' and dist between 1000 and 4999 and (cast(left(st,2) as int) in (7,8,17,18)) then cnt end) car15_peak,
 sum(case when m in ('4','5','6','7','8') and dist between 1000 and 4999 then cnt end) all15,
 sum(case when m='7' and dist between 1000 and 4999 then cnt end) walk15,
 sum(case when m in ('4','5') and dist between 1000 and 4999 then cnt end) bus15
 from allw where left(o,2)='11' and left(d,2)='11' group by o""").fetchdf()
X=D.merge(q,on='code')
g=X.groupby('grp')[['car15','car15_mid','car15_peak','all15','walk15','bus15']].sum()
g.loc['서울 전체']=X[['car15','car15_mid','car15_peak','all15','walk15','bus15']].sum()
r=pd.DataFrame({'동수':X.groupby('grp').size(),
 '차량중_낮10-16시%':100*g.car15_mid/g.car15,'차량중_출퇴근%':100*g.car15_peak/g.car15,
 '도보%':100*g.walk15/g.all15,'버스%':100*g.bus15/g.all15,'차량%':100*g.car15/g.all15})
r.loc['서울 전체','동수']=len(X)
print(r.round(1).to_string())
# 동 단위: 고령 비율과 낮 시간 차량 비중 상관(구 고정효과)
import statsmodels.formula.api as smf
X['mid']=100*X.car15_mid/X.car15; X=X.dropna(subset=['mid','elder_pct','recip_pct','car15'])
m=smf.wls('mid ~ elder_pct + recip_pct + C(gu)',data=X,weights=X.car15).fit(cov_type='cluster',cov_kwds={'groups':X.gu.astype('category').cat.codes})
print({k:(round(m.params[k],3),round(m.pvalues[k],4)) for k in ['elder_pct','recip_pct']}, 'n',len(X))
r.round(2).to_csv('out/ctype_evidence.csv',encoding='utf-8-sig')
