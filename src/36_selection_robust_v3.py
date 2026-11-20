# v3 선정 강건성: 지하철 접근성 단일 지표(대표점 거리 / 정류장 가중 거리 / 역 500m 면적 비율)로 각각 뽑았을 때 v3 우선 대상과의 겹침
import pandas as pd
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
base=set(D[D.priority].code); rows=[]
for lab,sub in [('대표점 거리',D.sub_dist_km),('정류장 가중 거리',D.stop_wdist),('역 500m 면적 비율',-D.cov500)]:
    a=(sub.rank(pct=True)+(1-D.route_stop_density.rank(pct=True)))/2; gap=a>=a.quantile(.75)
    s=set(D[gap&(D.car_share15>=D.car_share15.quantile(.75))].code)
    pil=all(c in s for c in D[D.nm.isin(['도봉1동','방화2동','방화3동'])].code)
    rows.append(dict(지표=lab,선정수=len(s),겹침=len(s&base),시범동유지=pil))
R=pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv('out/selection_robust_v3.csv',index=False,encoding='utf-8-sig')
