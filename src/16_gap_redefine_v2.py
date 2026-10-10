# 공백 지역 2단계 정의: (1) 공급 기준(결과 변수 미사용) 대중교통 공백 → (2) 그중 단거리 차량 의존 우선 대상
import pandas as pd, numpy as np
D=pd.read_csv('work/dong_features_plus.csv',dtype={'code':str})
R=pd.read_csv('work/bus_routes_dong.csv',dtype={'code':str})
D=D.merge(R,on='code',how='left')
D=D[D.car15.notna() & D['pop'].notna()].copy()
# 공급 지표: 지하철 거리(멀수록 나쁨), 버스 노선-정류장 밀도(낮을수록 나쁨)
D['access_gap']=(D.sub_dist_km.rank(pct=True)+(1-D.route_stop_density.rank(pct=True)))/2
D['gap_supply']=D.access_gap>=D.access_gap.quantile(.75)
med=np.average(D.car_share15,weights=D.all15)
D['priority']=D.gap_supply & (D.car_share15>=D.car_share15.quantile(.75))
print('공급 기준 공백 동:',int(D.gap_supply.sum()),'| 그중 차량 의존 상위25% 우선 대상:',int(D.priority.sum()))
old=set(D[D.forced].code); new=set(D[D.priority].code)
print('기존 34곳과 겹침',len(old&new),'| 신규',len(new-old),'| 빠짐',len(old-new))
print('빠진 동:',D[D.code.isin(old-new)][['gu','nm','sub_dist_km','route_stop_density','bus_density']].round(2).to_string(index=False))
print('추가된 동:',D[D.code.isin(new-old)][['gu','nm','sub_dist_km','route_stop_density','car_share15']].round(2).to_string(index=False))
# 공급 공백 vs 비공백 차량 비중 (결과를 정의에 쓰지 않았을 때도 차이가 나는지)
for k,gp in D.groupby('gap_supply'):
    print('gap_supply',k,'n',len(gp),'1~5km 차량 비중(이동량 가중)',round(100*gp.car15.sum()/gp.all15.sum(),1),'%')
q=pd.qcut(D.access_gap,5,labels=['1(좋음)','2','3','4','5(공백)'])
print((D.groupby(q,observed=True).apply(lambda x: 100*x.car15.sum()/x.all15.sum())).round(1).to_string())
D.to_csv('work/dong_features_v2.csv',index=False,encoding='utf-8-sig')
