import pandas as pd, numpy as np
D=pd.read_csv('work/dong_features.csv',dtype={'code':str})
pr=pd.read_csv('out/dong_priority_with_slope.csv',dtype={'code':str})[['code','gap']]
D=D.merge(pr,on='code',how='left'); D['gap']=D.gap.fillna(False).astype(bool)
print('corr with car_share15:', {c:round(D.car_share15.corr(D[c]),2) for c in ['recip_pct','elder_pct','sub_dist_km','bus_density','bike_density','pop_density','slope_pct']})
print('corr with car15 volume:', {c:round(D.car15.corr(D[c]),2) for c in ['recip_pct','elder_pct','pop_density']})
D['vuln']=(D.recip_pct.rank(pct=True)+D.elder_pct.rank(pct=True)+D.sub_dist_km.rank(pct=True))/3
hi=D.vuln>=D.vuln.quantile(.75)
print(f"gap dongs that are high-vulnerability (top25%): {int((D.gap & hi).sum())} / {int(D.gap.sum())}")
print('gap dongs: mean recip%',round(D[D.gap].recip_pct.mean(),1),'vs all',round(D.recip_pct.mean(),1),'| elder%',round(D[D.gap].elder_pct.mean(),1),'vs',round(D.elder_pct.mean(),1))
# vulnerable + far from subway + high car share: "forced car" candidates
D['forced']=(D.sub_dist_km>=D.sub_dist_km.quantile(.75))&(D.car_share15>=D.car_share15.quantile(.75))
f=D[D.forced].sort_values('car15',ascending=False)
print(f"\n'transit-poor & car-dependent short trips' dongs: {len(f)}")
print(f[['gu','nm','car15','car_share15','sub_dist_km','bus_density','elder_pct','recip_pct']].round(2).head(15).to_string(index=False))
D.to_csv('work/dong_features_plus.csv',index=False,encoding='utf-8-sig')
