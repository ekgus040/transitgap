# 민감도: 고소득 4개 구(강남·서초·송파·용산) 제외 후에도 효과가 유지되는지
import pandas as pd, numpy as np, statsmodels.formula.api as smf
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str}).dropna(subset=['sub_dist_km','route_stop_density','slope_pct','pop_density','elder_pct','recip_pct'])
D['y']=100*D.car_share15; D['l_rsd']=np.log(D.route_stop_density); D['l_pd']=np.log(D.pop_density)
E=D[~D.gu.isin(['강남구','서초구','송파구','용산구'])]
m=smf.wls('y ~ sub_dist_km + l_rsd + slope_pct + l_pd + elder_pct + recip_pct + C(gu)',data=E,weights=E.all15).fit(cov_type='cluster',cov_kwds={'groups':E.gu})
print('고소득 4개 구 제외 n',int(m.nobs)); print(m.params[['sub_dist_km','l_rsd']].round(2).to_dict(), m.pvalues[['sub_dist_km','l_rsd']].round(4).to_dict())
q=pd.qcut(E.access_gap,5,labels=['1(좋음)','2','3','4','5(공백)'])
print('제외 후 접근성 5분위별 차량 비중:',(E.groupby(q,observed=True).apply(lambda x:100*x.car15.sum()/x.all15.sum())).round(1).to_dict())
