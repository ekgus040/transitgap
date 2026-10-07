import pandas as pd, numpy as np, lightgbm as lgb, shap
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
X=pd.read_pickle('work/od_model_data_v2.pkl'); X['y']=X.y/100
m0=lgb.Booster(model_file='work/lgb_od_v2.txt'); cols=m0.feature_name()
P=dict(objective='regression',learning_rate=0.05,num_leaves=31,min_data_in_leaf=50,feature_fraction=0.8,bagging_fraction=0.8,bagging_freq=1,verbose=-1,deterministic=True,num_threads=1,force_row_wise=True)
oof=np.zeros(len(X))
for tr,te in KFold(5,shuffle=True,random_state=1).split(X):
    m=lgb.train(dict(P,seed=7),lgb.Dataset(X.iloc[tr][cols],X.iloc[tr].y,weight=X.iloc[tr].tot),600); oof[te]=m.predict(X.iloc[te][cols])
print('random CV R2',round(r2_score(X.y,oof,sample_weight=X.tot),3))
for sd in (1,2,3):
    m=lgb.train(dict(P,seed=sd),lgb.Dataset(X[cols],X.y,weight=X.tot),600)
    sv=shap.TreeExplainer(m).shap_values(X[cols].sample(4000,random_state=sd))
    print(sd, list(pd.Series(np.abs(sv).mean(0),index=cols).sort_values(ascending=False).index[:5]))
