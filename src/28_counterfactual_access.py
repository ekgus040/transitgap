# 모델 기반 시나리오: 우선 대상(36곳)의 접근성을 서울 중앙값 수준으로 개선했을 때 1~5km 차량 이동 감소와 배출 회피량
# 계수: 동 단위 구 고정효과 가중회귀(17번), 하한은 고소득 4개 구 제외 추정(18번)
import pandas as pd, numpy as np, duckdb
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
P=pd.read_csv('work/priority_clusters.csv',dtype={'code':str})[['code','cluster']]
lab={0:'C',1:'B',2:'A'}
G=D[D.priority].merge(P,on='code'); G['type']=G.cluster.map(lab)
med_rsd=D.route_stop_density.median(); med_sub=D.sub_dist_km.median()
coef={'중앙(구 고정효과)':(2.3838,-1.7727),'하한(고소득 구 제외)':(2.17,-1.48)}
con=duckdb.connect('work/mob.duckdb',read_only=True)
con.register('g',G[['code']])
pk=con.execute("""select a.o code, sum(cnt*dist)/4000 pkm, sum(case when tm>0 and dist/tm*0.06>=5 then cnt*dist else 0 end)/4000 pkm_c
 from allw a join g on a.o=g.code where left(a.d,2)='11' and a.m='8' and a.dist between 1000 and 4999 group by 1""").fetchdf()
G=G.merge(pk,on='code')
rows=[]
for sc,use_sub in [('S1 버스 노선·정류장 보강',False),('S2 + 역 연계(마을버스·DRT)',True)]:
    for cl,(bs,br) in coef.items():
        d_rsd=np.where(G.route_stop_density<med_rsd, br*np.log(med_rsd/G.route_stop_density),0)          # %p (음수)
        d_sub=np.where(use_sub&(G.sub_dist_km>med_sub), -bs*(G.sub_dist_km-med_sub),0)
        dp=(d_rsd+d_sub)/100                                    # 차량 비중 변화(비율)
        cut_trips=-(dp*G.all15)                                  # 하루 감소 차량 이동
        frac=cut_trips/G.car15
        avoid_pkm=(frac*G.pkm).sum(); avoid_pkm_c=(frac*G.pkm_c).sum()
        t={'보수':avoid_pkm_c*1.2/1.8*187/1e6*365,'기본':avoid_pkm*1.3/1.3*220/1e6*365,'높음':avoid_pkm*1.4/1.3*255/1e6*365}
        rows.append(dict(시나리오=sc,계수=cl,차량비중변화_pp=round(100*np.average(dp,weights=G.all15),2),
            감소_건_일=round(cut_trips.sum()),감소율_pct=round(100*cut_trips.sum()/G.car15.sum(),1),
            배출회피_보수_t=round(t['보수']),배출회피_기본_t=round(t['기본']),배출회피_높음_t=round(t['높음']),
            마을버스_대=round(cut_trips.sum()/490)))
R=pd.DataFrame(rows); print(R.to_string(index=False))
print('서울 중앙값 rsd',round(med_rsd,1),'sub',round(med_sub,2),'| 우선 대상 차량 1~5km/일',round(G.car15.sum()))
for ty,g in G.groupby('type'):
    bs,br=coef['중앙(구 고정효과)']
    d=np.where(g.route_stop_density<med_rsd, br*np.log(med_rsd/g.route_stop_density),0)+np.where(g.sub_dist_km>med_sub,-bs*(g.sub_dist_km-med_sub),0)
    print(ty,'S2 중앙 차량비중 변화 %p',round(np.average(d,weights=g.all15),2),'현재 비중',round(100*g.car15.sum()/g.all15.sum(),1))
R.to_csv('out/counterfactual_access_carbon.csv',index=False,encoding='utf-8-sig')
