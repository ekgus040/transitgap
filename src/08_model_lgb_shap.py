import pandas as pd, numpy as np, duckdb, lightgbm as lgb, shap
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
D=pd.read_csv('work/dong_features.csv',dtype={'code':str})
feats=['bike_density','bus_density','sub_dist_km','slope_pct','pop_density','elder_pct','recip_pct']
con=duckdb.connect('work/mob.duckdb')
od=con.execute("select o,d,dist,tot,car from od15 where tot>=20").fetchdf()
X=od.merge(D[['code','gu']+feats].add_prefix('o_'),left_on='o',right_on='o_code').merge(D[['code']+feats].add_prefix('d_'),left_on='d',right_on='d_code')
X['y']=X.car/X.tot
cols=['dist']+['o_'+f for f in feats]+['d_'+f for f in feats]
X=X.dropna(subset=cols+['y'])
print('OD samples',len(X),' weighted mean car share',round(np.average(X.y,weights=X.tot),3))
params=dict(objective='regression',learning_rate=0.05,num_leaves=31,min_data_in_leaf=50,feature_fraction=0.8,bagging_fraction=0.8,bagging_freq=1,verbose=-1,seed=7,deterministic=True,num_threads=1,force_row_wise=True)
oof=np.zeros(len(X)); gkf=GroupKFold(n_splits=5)
for tr,te in gkf.split(X,groups=X.o_gu):
    m=lgb.train(params,lgb.Dataset(X.iloc[tr][cols],X.iloc[tr].y,weight=X.iloc[tr].tot),num_boost_round=600)
    oof[te]=m.predict(X.iloc[te][cols])
print('spatial CV (by origin gu) weighted R2:',round(r2_score(X.y,oof,sample_weight=X.tot),3))
# baseline: distance only
oof0=np.zeros(len(X))
for tr,te in gkf.split(X,groups=X.o_gu):
    m0=lgb.train(params,lgb.Dataset(X.iloc[tr][['dist']],X.iloc[tr].y,weight=X.iloc[tr].tot),num_boost_round=300)
    oof0[te]=m0.predict(X.iloc[te][['dist']])
print('distance-only baseline R2:',round(r2_score(X.y,oof0,sample_weight=X.tot),3))
model=lgb.train(params,lgb.Dataset(X[cols],X.y,weight=X.tot),num_boost_round=600)
model.save_model('work/lgb_od.txt')
ex=shap.TreeExplainer(model); sv=ex.shap_values(X[cols].sample(5000,random_state=1))
imp=pd.Series(np.abs(sv).mean(0),index=cols).sort_values(ascending=False)
print('\nmean |SHAP| (car-share points):'); print((imp*100).round(2).to_string())
S=X[cols].sample(5000,random_state=1)
print('\nDirection (corr of feature value with its SHAP):')
for c in imp.index[:10]:
    print(f"  {c}: {np.corrcoef(S[c],sv[:,cols.index(c)])[0,1]:+.2f}")
X.to_pickle('work/od_model_data.pkl')
