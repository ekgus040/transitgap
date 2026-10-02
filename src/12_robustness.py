import pandas as pd, numpy as np, duckdb, lightgbm as lgb, shap
from sklearn.model_selection import GroupKFold, KFold
from sklearn.metrics import r2_score
con=duckdb.connect('work/mob.duckdb'); rows=[]
B="from allw where left(o,2)='11' and left(d,2)='11' and m='8'"
allcar=con.execute(f"select sum(cnt)/4 {B} and dist>=500").fetchone()[0]
def add(cat,case,val,note=''): rows.append((cat,case,val,note))
for lab,cond in [('기본: 1~5km','dist between 1000 and 4999'),('보수: 1~5km, 시속5km 미만 제외','dist between 1000 and 4999 and tm>0 and dist/tm*0.06>=5'),('1~3km','dist between 1000 and 2999'),('1~5km, 택시 9% 차감 가정','dist between 1000 and 4999')]:
    v=con.execute(f"select sum(cnt)/4 {B} and {cond}").fetchone()[0]
    if '택시' in lab: v*=0.91
    add('단거리 차량 이동 규모',lab,f"{v:,.0f}건/일 ({100*v/allcar:.1f}%)")
# daily stability
for dy in ('0826','0827','0828','0829'):
    a,b=con.execute(f"select sum(cnt) filter (where dist between 1000 and 4999), sum(cnt) filter (where dist>=500) from allw where dy='{dy}' and left(o,2)='11' and left(d,2)='11' and m='8'").fetchone()
    add('날짜별 안정성',f"2026-08-{dy[2:]}",f"{100*a/b:.1f}%")
# transit-gap definition sensitivity
D=pd.read_csv('work/dong_features_plus.csv',dtype={'code':str})
base=set(D[D.forced].code)
for q in (0.7,0.8):
    s=set(D[(D.sub_dist_km>=D.sub_dist_km.quantile(q))&(D.car_share15>=D.car_share15.quantile(q))].code)
    add('공백 지역 기준',f"상위 {int(round((1-q)*100))}% 기준",f"{len(s)}곳, 기본(상위25%) 34곳과 겹침 {len(s&base)}곳")
# model robustness
X=pd.read_pickle('work/od_model_data.pkl'); m0=lgb.Booster(model_file='work/lgb_od.txt'); cols=m0.feature_name()
params=dict(objective='regression',learning_rate=0.05,num_leaves=31,min_data_in_leaf=50,feature_fraction=0.8,bagging_fraction=0.8,bagging_freq=1,verbose=-1,deterministic=True,num_threads=1,force_row_wise=True)
def cv(splitter,groups=None,seed=7):
    oof=np.zeros(len(X)); p=dict(params,seed=seed)
    for tr,te in splitter.split(X,groups=groups):
        m=lgb.train(p,lgb.Dataset(X.iloc[tr][cols],X.iloc[tr].y,weight=X.iloc[tr].tot),600); oof[te]=m.predict(X.iloc[te][cols])
    return r2_score(X.y,oof,sample_weight=X.tot)
add('모델 성능','공간 교차검증(출발 구 단위)',f"R² {cv(GroupKFold(5),X.o_gu):.3f}")
add('모델 성능','무작위 교차검증',f"R² {cv(KFold(5,shuffle=True,random_state=1)):.3f}",'공간 CV보다 높으면 공간 과적합 주의')
tops=[]
for sd in (1,2,3):
    m=lgb.train(dict(params,seed=sd),lgb.Dataset(X[cols],X.y,weight=X.tot),600)
    sv=shap.TreeExplainer(m).shap_values(X[cols].sample(4000,random_state=sd))
    tops.append(list(pd.Series(np.abs(sv).mean(0),index=cols).sort_values(ascending=False).index[:5]))
add('SHAP 순위 안정성','시드 3회 상위 5개 변수',' / '.join(','.join(t) for t in tops))
# carbon
pkm_full=con.execute(f"select sum(cnt*dist)/4000 {B} and dist between 1000 and 4999").fetchone()[0]
pkm_cons=con.execute(f"select sum(cnt*dist)/4000 {B} and dist between 1000 and 4999 and tm>0 and dist/tm*0.06>=5").fetchone()[0]
for lab,pkm,occ,det,ef in [('보수',pkm_cons,1.8,1.2,187),('기본',pkm_full,1.3,1.3,220),('높음',pkm_full,1.3,1.4,255)]:
    t=pkm*det/occ*ef/1e6*365
    add('탄소 (연간)',f"{lab}: 재차{occ}, 우회{det}, {ef}g/km",f"{t:,.0f} tCO2, 10% 전환 시 {t*0.1:,.0f} t")
R=pd.DataFrame(rows,columns=['구분','조건','결과','비고'])
R.to_csv('out/robustness_table.csv',index=False,encoding='utf-8-sig'); print(R.to_string(index=False))
