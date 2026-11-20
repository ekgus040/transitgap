# v3 선정 결과 내보내기: 동별 접근성 지표와 우선 대상 36곳(유형 포함)
import pandas as pd
D=pd.read_csv('work/dong_features_v2.csv')
cols=['code','gu','nm','car15','all15','car_share15','sub_dist_km','stop_wdist','cov500','sub_access_gap',
      'route_stop_density','bus_density','access_gap','gap_supply','priority','elder_pct','recip_pct']
D[cols].to_csv('out/dong_access_gap.csv',index=False,encoding='utf-8-sig')
G=pd.read_csv('work/priority_clusters.csv')
G['type']=G.cluster.map({2:'A 외곽 저밀형',1:'B 버스 연계 부족형',0:'C 취약 고령형'})
G[['code','gu','nm','type']+[c for c in cols if c not in ('code','gu','nm')]].sort_values(['type','gu']).to_csv('out/priority_clusters.csv',index=False,encoding='utf-8-sig')
print(D.gap_supply.sum(),D.priority.sum(),G.type.value_counts().to_dict())
