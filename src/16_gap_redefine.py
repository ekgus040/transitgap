# 공백 지역 2단계 정의(v3): (1) 공급 기준(결과 변수 미사용) 대중교통 공백 → (2) 그중 단거리 차량 의존 우선 대상
# v3 변경: 지하철 접근성을 단일 지표(동 대표점-역 직선거리) 대신 세 지표의 평균 백분위로 측정해 넓은 동의 대표점 편향 완화
#   ① 동 대표점-최근접역 거리 ② 동 안 버스정류장(생활 거점 대용)-최근접역 평균 거리 ③ 역 반경 500m가 덮는 동 면적 비율(역방향)
import geopandas as gpd
from shapely.ops import unary_union
import pandas as pd, numpy as np
D=pd.read_csv('work/dong_features_plus.csv',dtype={'code':str})
R=pd.read_csv('work/bus_routes_dong.csv',dtype={'code':str})
D=D.merge(R,on='code',how='left')
D=D[D.car15.notna() & D['pop'].notna()].copy()
_g=gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); _g=_g[_g.sido=='11'].copy(); _g['code']=_g.adm_cd2.str[:8]; _g=_g.to_crs(5179)
_st=pd.read_csv('data_raw/서울시 역사마스터 정보.csv',encoding='cp949')
_S=gpd.GeoDataFrame(_st,geometry=gpd.points_from_xy(_st['경도'],_st['위도']),crs=4326).to_crs(5179)
_U=unary_union(_S.buffer(500).geometry); _g['cov500']=_g.geometry.intersection(_U).area/_g.geometry.area
D=D.merge(_g[['code','cov500']],on='code',how='left')
_b=pd.read_csv('data_raw/서울시 버스정류소 위치정보.csv',encoding='cp949'); _b=_b[_b['정류소 타입']!='한강선착장']
_B=gpd.GeoDataFrame(_b,geometry=gpd.points_from_xy(_b['X좌표'],_b['Y좌표']),crs=4326).to_crs(5179).sjoin(_g[['code','geometry']],how='inner')
_B=gpd.sjoin_nearest(_B.drop(columns='index_right'),_S[['geometry']],distance_col='d')
D['stop_wdist']=D.code.map(_B.groupby('code').d.mean()/1000)
D['sub_access_gap']=(D.sub_dist_km.rank(pct=True)+D.stop_wdist.rank(pct=True)+(1-D.cov500.rank(pct=True)))/3
# 공급 지표: 지하철 접근성 복합 지표(높을수록 나쁨), 버스 노선-정류장 밀도(낮을수록 나쁨)
D['access_gap']=(D.sub_access_gap.rank(pct=True)+(1-D.route_stop_density.rank(pct=True)))/2
D['gap_supply']=D.access_gap>=D.access_gap.quantile(.75)
med=np.average(D.car_share15,weights=D.all15)
D['priority']=D.gap_supply & (D.car_share15>=D.car_share15.quantile(.75))
print('공급 기준 공백 동:',int(D.gap_supply.sum()),'| 그중 차량 의존 상위25% 우선 대상:',int(D.priority.sum()))
old=set(pd.read_csv('work/bak_v2/dong_features_v2.csv',dtype={'code':str}).query('priority').code); new=set(D[D.priority].code)
print('v2(역 거리 기준) 우선 대상과 겹침',len(old&new),'| 신규',len(new-old),'| 빠짐',len(old-new))
print('빠진 동:',D[D.code.isin(old-new)][['gu','nm','sub_dist_km','route_stop_density','bus_density']].round(2).to_string(index=False))
print('추가된 동:',D[D.code.isin(new-old)][['gu','nm','sub_dist_km','route_stop_density','car_share15']].round(2).to_string(index=False))
# 공급 공백 vs 비공백 차량 비중 (결과를 정의에 쓰지 않았을 때도 차이가 나는지)
for k,gp in D.groupby('gap_supply'):
    print('gap_supply',k,'n',len(gp),'1~5km 차량 비중(이동량 가중)',round(100*gp.car15.sum()/gp.all15.sum(),1),'%')
q=pd.qcut(D.access_gap,5,labels=['1(좋음)','2','3','4','5(공백)'])
print((D.groupby(q,observed=True).apply(lambda x: 100*x.car15.sum()/x.all15.sum())).round(1).to_string())
D.to_csv('work/dong_features_v2.csv',index=False,encoding='utf-8-sig')
