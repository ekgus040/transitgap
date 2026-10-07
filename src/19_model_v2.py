# LightGBM v2: 버스 노선-정류장 밀도 추가, 공간 교차검증, SHAP
import pandas as pd, numpy as np, lightgbm as lgb, shap
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
X=pd.read_pickle('work/od_model_data_v2.pkl'); X['y']=X.y/100
feats=['bike_density','bus_density','route_stop_density','sub_dist_km','slope_pct','pop_density','elder_pct','recip_pct']
cols=['dist']+[f'{s}_{f}' for s in ('o','d') for f in feats]
P=dict(objective='regression',learning_rate=0.05,num_leaves=31,min_data_in_leaf=50,feature_fraction=0.8,bagging_fraction=0.8,bagging_freq=1,verbose=-1,seed=7,deterministic=True,num_threads=1,force_row_wise=True)
def cv(c):
    oof=np.zeros(len(X))
    for tr,te in GroupKFold(5).split(X,groups=X.o_gu):
        m=lgb.train(P,lgb.Dataset(X.iloc[tr][c],X.iloc[tr].y,weight=X.iloc[tr].tot),600); oof[te]=m.predict(X.iloc[te][c])
    return r2_score(X.y,oof,sample_weight=X.tot)
old=[c for c in cols if 'route_stop' not in c]
print('공간CV R2 기존 변수',round(cv(old),3),'| 버스 노선 추가',round(cv(cols),3),'| 거리만',round(cv(['dist']),3))
m=lgb.train(P,lgb.Dataset(X[cols],X.y,weight=X.tot),600); m.save_model('work/lgb_od_v2.txt')
S=X[cols].sample(5000,random_state=1); sv=shap.TreeExplainer(m).shap_values(S)
imp=pd.Series(np.abs(sv).mean(0)*100,index=cols).sort_values(ascending=False)
sg={c:np.corrcoef(S[c],sv[:,cols.index(c)])[0,1] for c in cols}
print(pd.DataFrame({'mean|SHAP|%p':imp.round(2),'방향':[f"{sg[c]:+.2f}" for c in imp.index]}).head(10).to_string())
