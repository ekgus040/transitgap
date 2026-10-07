# 사례 분석: 양재1동(A), 도봉1동(C), 진관동(A, 기존 DRT 셔클 운영지 → 외부 타당성 확인)
import duckdb, pandas as pd, numpy as np
con=duckdb.connect('work/mob.duckdb',read_only=True)
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str}); D['lab']=D.nm; info=D.set_index('code')
rows=[]
for name in ['양재1동','도봉1동','진관동']:
    c=D[D.nm==name].code.iloc[0]
    q=con.execute(f"""select d, sum(cnt)/4 car, sum(cnt*dist)/sum(cnt) md, sum(cnt*dist)/4000 pkm from allw where o='{c}' and left(d,2)='11' and m='8' and dist between 1000 and 4999 group by d order by car desc""").fetchdf()
    tot=q.car.sum(); q['share']=100*q.car/tot
    top5=q.head(5); t5=tuple(top5.d)
    ms=con.execute(f"select sum(case when m='8' then cnt end)/sum(cnt) from allw where o='{c}' and d in {t5} and dist between 1000 and 4999 and m in ('4','5','6','7','8','9')").fetchone()[0]
    mid=con.execute(f"select sum(case when left(st,2) in ('10','11','12','13','14','15') then cnt end)/sum(cnt) from allw where o='{c}' and left(d,2)='11' and m='8' and dist between 1000 and 4999").fetchone()[0]
    pkm=q.pkm.sum(); t_base=pkm*220/1e6*365
    rows.append(dict(동=name,유형=('A' if name!='도봉1동' else 'C'),차량건_일=round(tot),평균거리_km=round(np.average(q.md,weights=q.car)/1000,2),
        상위5목적지=', '.join(f"{info.loc[d,'lab']}({s:.0f}%)" for d,s in zip(top5.d,top5.share)),상위5합계_pct=round(top5.share.sum(),1),
        상위5목적지_평균역거리_km=round(np.average(top5.d.map(info.sub_dist_km),weights=top5.car),2),상위5구간_차량비중_pct=round(100*ms,1),
        낮시간_10_15시_pct=round(100*mid,1),출발지_역거리_km=round(info.loc[c,'sub_dist_km'],2),노선정류장밀도=round(info.loc[c,'route_stop_density'],1),
        고령_pct=round(info.loc[c,'elder_pct'],1),수급_pct=round(info.loc[c,'recip_pct'],1),연간CO2_기본_t=round(t_base),감축_10pct_t=round(t_base*.1),감축_30pct_t=round(t_base*.3)))
R=pd.DataFrame(rows); print(R.T.to_string()); R.to_csv('out/case_study.csv',index=False,encoding='utf-8-sig')
