# 소득 통제: 같은 구 안 비교(구 고정효과). 구 단위 소득·자동차 보유 차이를 흡수
import pandas as pd, numpy as np, statsmodels.formula.api as smf
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
D=D.dropna(subset=['sub_dist_km','route_stop_density','slope_pct','pop_density','elder_pct','recip_pct'])
D['y']=100*D.car_share15; D['l_rsd']=np.log(D.route_stop_density); D['l_pd']=np.log(D.pop_density)
f='y ~ sub_dist_km + l_rsd + slope_pct + l_pd + elder_pct + recip_pct'
out=[]
for lab,form in [('구 통제 없음',f),('구 고정효과',f+' + C(gu)')]:
    m=smf.wls(form,data=D,weights=D.all15).fit(cov_type='cluster',cov_kwds={'groups':D.gu})
    for v in ['sub_dist_km','l_rsd','slope_pct','recip_pct']:
        out.append(('동 단위',lab,v,m.params[v],m.bse[v],m.pvalues[v]))
    print(lab,'R2',round(m.rsquared,3),'n',int(m.nobs))
# OD 단위: 출발·도착 구 고정효과
X=pd.read_pickle('work/od_model_data.pkl')
R=pd.read_csv('work/bus_routes_dong.csv',dtype={'code':str})[['code','route_stop_density']]
X=X.merge(R.add_prefix('o_'),left_on='o',right_on='o_code',suffixes=('','_r')).merge(R.add_prefix('d_'),left_on='d',right_on='d_code',suffixes=('','_r'))
G=D[['code','gu']]; X=X.merge(G.rename(columns={'code':'d','gu':'d_gu'}),on='d',how='left')
X['y']=100*X.y if X.y.max()<=1 else X.y
for s in ('o','d'): X[f'{s}_l_rsd']=np.log(X[f'{s}_route_stop_density'].clip(lower=1))
fo='y ~ dist + o_sub_dist_km + d_sub_dist_km + o_l_rsd + d_l_rsd + o_slope_pct + d_slope_pct + o_recip_pct + d_recip_pct + o_elder_pct + d_elder_pct'
X=X.dropna(subset=['d_gu'])
for lab,form in [('구 통제 없음',fo),('출발·도착 구 고정효과',fo+' + C(o_gu) + C(d_gu)')]:
    m=smf.wls(form,data=X,weights=X.tot).fit(cov_type='cluster',cov_kwds={'groups':X.o_gu})
    for v in ['o_sub_dist_km','d_sub_dist_km','o_l_rsd','d_l_rsd']:
        out.append(('OD 단위',lab,v,m.params[v],m.bse[v],m.pvalues[v]))
    print(lab,'R2',round(m.rsquared,3),'n',int(m.nobs))
T=pd.DataFrame(out,columns=['단위','모형','변수','계수','SE','p']).round(4)
print(T.to_string(index=False)); T.to_csv('out/income_control_fe.csv',index=False,encoding='utf-8-sig')
X.to_pickle('work/od_model_data_v2.pkl')
