import pandas as pd, numpy as np, lightgbm as lgb, shap
X=pd.read_pickle('work/od_model_data.pkl'); m=lgb.Booster(model_file='work/lgb_od.txt')
cols=m.feature_name()
S=X[cols].sample(5000,random_state=1); sv=shap.TreeExplainer(m).shap_values(S)
for c in ['o_bike_density','d_bike_density','o_elder_pct','o_recip_pct','d_recip_pct','o_slope_pct']:
    print(f"{c}: corr(value,SHAP)={np.corrcoef(S[c],sv[:,cols.index(c)])[0,1]:+.2f}")
# partial dependence for bike density (o and d jointly)
D=pd.read_csv('work/dong_features.csv',dtype={'code':str})
pr=pd.read_csv('out/dong_priority_with_slope.csv',dtype={'code':str})
gap=set(pr[pr.gap].code)
base=m.predict(X[cols]); 
def scen(target_pct, only_gap=True):
    t=D.bike_density.quantile(target_pct)
    Z=X.copy()
    for side in ('o','d'):
        mask=Z[side].isin(gap) if only_gap else np.ones(len(Z),bool)
        Z.loc[mask,f'{side}_bike_density']=np.maximum(Z.loc[mask,f'{side}_bike_density'],t)
    p=m.predict(Z[cols]); dcar=((base-p)*Z.tot)
    aff=(Z.o.isin(gap)|Z.d.isin(gap)) if only_gap else np.ones(len(Z),bool)
    return t, dcar.sum(), (dcar*Z.dist).sum()/1000, Z.tot[aff].sum(), (base*Z.tot)[aff].sum()
for q in (0.5,0.75):
    t,dc,dpkm,tot_aff,car_aff=scen(q)
    tco2=dpkm*1.3/1.3*220/1e6*365
    print(f"gap dongs -> bike density >= p{int(q*100)} ({t:.1f}/km2): car trips shifted/day={dc:,.0f} ({100*dc/car_aff:.2f}% of car trips on affected ODs) | pkm/day={dpkm:,.0f} | ~{tco2:,.0f} tCO2/yr (base EF)")
t,dc,dpkm,_,car_all=scen(0.75,only_gap=False)
print(f"ALL dongs -> p75: car trips shifted/day={dc:,.0f} ({100*dc/car_all:.2f}%) | ~{dpkm*220/1e6*365:,.0f} tCO2/yr")
