# 측정 강건성: 역 거리(동 대표점 기준) 대신 '역 반경 750m 안에 드는 동 면적 비율'로 바꿔 구 고정효과 회귀 재확인
import pandas as pd, numpy as np, geopandas as gpd, statsmodels.formula.api as smf
from shapely.ops import unary_union
g=gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); g=g[g.sido=='11'].copy(); g['code']=g.adm_cd2.str[:8]; g=g.to_crs(5179)
st=pd.read_csv('data_raw/서울시 역사마스터 정보.csv',encoding='cp949')
S=gpd.GeoDataFrame(st,geometry=gpd.points_from_xy(st['경도'],st['위도']),crs=4326).to_crs(5179)
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
out={}
for r in (500,750):
    U=unary_union(S.buffer(r).geometry)
    g[f'cov{r}']=g.geometry.intersection(U).area/g.geometry.area
X=D.merge(g[['code','cov500','cov750']],on='code')
X['y']=100*X.car_share15; X['l_rsd']=np.log(X.route_stop_density); X['l_pd']=np.log(X.pop_density)
X=X.dropna(subset=['recip_pct','elder_pct'])
for v in ['sub_dist_km','cov500','cov750']:
    m=smf.wls(f'y ~ {v} + l_rsd + slope_pct + l_pd + elder_pct + recip_pct + C(gu)',data=X,weights=X.all15).fit(cov_type='cluster',cov_kwds={'groups':X.gu})
    out[v]=(round(m.params[v],3),round(m.pvalues[v],4),round(m.params['l_rsd'],3),round(m.pvalues['l_rsd'],4))
    print(v,out[v])
print(X[X.nm.isin(['양재1동','도봉1동','진관동','방화2동','방화3동'])][['nm','sub_dist_km','cov500','cov750']].round(2).to_string(index=False))
P=X[X.priority]; print('cov750 우선대상 평균',round(P.cov750.mean(),2),'서울',round(X.cov750.mean(),2))
pd.DataFrame(out,index=['역지표계수','p','l_rsd계수','l_rsd_p']).T.to_csv('out/station_coverage_check.csv',encoding='utf-8-sig')
