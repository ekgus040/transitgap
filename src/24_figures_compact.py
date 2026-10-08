# 보고서 분량용 압축 그림: 그림 2(상위 8개 요인), 그림 3·4(한 장, 큰 글씨)
import pandas as pd, numpy as np, duckdb, matplotlib
matplotlib.use('Agg'); import koreanize_matplotlib, matplotlib.pyplot as plt
import lightgbm as lgb, shap
SURF='#fcfcfb'; T1='#0b0b0b'; T2='#52514e'; GRID='#e4e3df'; S1='#2a78d6'
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'axes.edgecolor':GRID,'axes.labelcolor':T2,'xtick.color':T2,'ytick.color':T2,'font.size':11,'axes.titlesize':12,'axes.titleweight':'bold','axes.titlecolor':T1})
X=pd.read_pickle('work/od_model_data_v2.pkl'); m=lgb.Booster(model_file='work/lgb_od_v2.txt'); cols=m.feature_name()
Sm=X[cols].sample(5000,random_state=1); sv=shap.TreeExplainer(m).shap_values(Sm)
imp=pd.Series(np.abs(sv).mean(0)*100,index=cols).sort_values().tail(8)
sign={c:np.sign(np.corrcoef(Sm[c],sv[:,cols.index(c)])[0,1]) for c in imp.index}
nm={'route_stop_density':'버스 노선·정류장 밀도','bus_density':'버스정류장 밀도','slope_pct':'경사','sub_dist_km':'지하철역 거리','pop_density':'인구밀도','elder_pct':'고령인구 비율','bike_density':'따릉이 밀도','recip_pct':'수급자 비율'}
lab=lambda c: '이동 거리' if c=='dist' else ('출발지 ' if c[0]=='o' else '도착지 ')+nm[c[2:]]
fig,ax=plt.subplots(figsize=(8,3.1))
ax.barh([lab(c) for c in imp.index],imp.values,color=S1,height=0.62)
for i,c in enumerate(imp.index): ax.text(imp.values[i]+0.03,i,f"{imp.values[i]:.2f} ({'값↑ 차량↑' if sign[c]>0 else '값↑ 차량↓'})",va='center',fontsize=10,color=T2)
ax.set_xlabel('평균 |SHAP| (차량 이용 비율, %p)'); ax.set_xlim(0,imp.max()*1.5)
ax.grid(axis='x',color=GRID,lw=0.6); ax.set_axisbelow(True)
for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig2_shap_compact.png',dpi=220); plt.close()
# 그림 3·4
con=duckdb.connect('work/mob.duckdb',read_only=True)
h=con.execute("select left(st,2) hr, sum(cnt)/4 v from allw where left(o,2)='11' and left(d,2)='11' and m='8' and dist between 1000 and 4999 group by 1 order by 1").fetchdf()
P=pd.read_csv('out/priority_carbon.csv'); lo,ba,hi=P['연간배출_t'].tolist(); SL,SB,SH=111613,247256,308638
fig,(a1,a2)=plt.subplots(1,2,figsize=(11,3.1),gridspec_kw={'width_ratios':[1,1.15]})
a1.plot(h.hr.astype(int),h.v/1000,color=S1,lw=2); a1.fill_between(h.hr.astype(int),h.v/1000,color=S1,alpha=0.08)
a1.set_xticks(range(0,24,3)); a1.set_xlabel('출발 시각'); a1.set_ylabel('천 건/시간(4일 평균)')
a1.axvspan(10.5,13.5,color=GRID,alpha=0.6,lw=0); a1.text(12,h.v.max()/1000*0.1,'낮 생활 이동',ha='center',fontsize=10,color=T2)
a1.set_title('(가) 1~5km 차량 이동 시간대 분포',fontsize=11.5); a1.grid(axis='y',color=GRID,lw=0.6)
rows=[('40곳 10% 전환',lo*.1,ba*.1,hi*.1,S1),('40곳 20% 전환',lo*.2,ba*.2,hi*.2,S1),('40곳 30% 전환',lo*.3,ba*.3,hi*.3,S1),('서울 전체 10%(잠재량)',SL*.1,SB*.1,SH*.1,'#8a8984')]
for i,(l,a,b,c,col) in enumerate(rows[::-1]):
    a2.plot([a/1000,c/1000],[i,i],color=col,lw=6,solid_capstyle='round',alpha=0.35); a2.plot(b/1000,i,'o',color=col,ms=8,mec=SURF,mew=2)
    a2.text(c/1000+0.6,i,f"{a/1000:.1f}~{c/1000:.1f}천 t",va='center',fontsize=10,color=T2)
a2.axvline(0.962,color=T2,lw=1,ls='--'); a2.text(1.2,3.45,'따릉이 인증 감축량(962t)',fontsize=9.5,color=T2)
a2.set_yticks(range(4),[r[0] for r in rows[::-1]]); a2.set_xlabel('연간 CO2 감축량 (천 t)'); a2.set_ylim(-0.6,3.8); a2.set_xlim(0,SH*0.1/1000*1.4)
a2.set_title('(나) 전환 시 탄소 감축 시나리오',fontsize=11.5); a2.grid(axis='x',color=GRID,lw=0.6)
for ax in (a1,a2):
    for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig34_combined.png',dpi=220); plt.close(); print('ok')
