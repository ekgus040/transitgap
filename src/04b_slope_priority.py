import pandas as pd, numpy as np
toks=open('data_raw/slope_by_dong.txt').read().split()
sl={'11'+t.split(',')[0]: float(t.split(',')[1]) for t in toks}
print('slopes:',len(sl))
df=pd.read_csv('out/dong_short_car_vs_ddareungi.csv', dtype={'code':str})
df['slope_pct']=df.code.map(sl)
print('missing slope:', df.slope_pct.isna().sum())
print('slope quantiles:', df.slope_pct.quantile([.25,.5,.75]).round(1).to_dict())
# does slope explain low station density / high car share?
print('corr(slope, stations per 10k short car)=', round(df.slope_pct.corr(df.st_per_10k_short_car),2))
print('corr(slope, car_share15)=', round(df.slope_pct.corr(df.car_share15),2))
thr=df.slope_pct.quantile(.75)
df['terrain']=np.where(df.slope_pct>=thr,'경사','평지')
g=df[df.gap]
print(f"\nGap dongs: {len(g)} | 경사(slope>={thr:.1f}%) {int((g.terrain=='경사').sum())} / 평지 {int((g.terrain=='평지').sum())}")
cols=['gu','nm','car15','car_share15','stations','st_per_10k_short_car','slope_pct','terrain']
print(g.sort_values('car15',ascending=False)[cols].round(1).to_string(index=False))
df.round(2).to_csv('out/dong_priority_with_slope.csv',index=False,encoding='utf-8-sig')
