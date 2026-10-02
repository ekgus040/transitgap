import json, pandas as pd, numpy as np, geopandas as gpd, duckdb, matplotlib
matplotlib.use('Agg'); import koreanize_matplotlib, matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import lightgbm as lgb, shap
SURF='#fcfcfb'; T1='#0b0b0b'; T2='#52514e'; GRID='#e4e3df'
S1,S2,S3='#2a78d6','#eb6834','#1baf7a'
SEQ=['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b']
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'axes.edgecolor':GRID,'axes.labelcolor':T2,'xtick.color':T2,'ytick.color':T2,'font.size':10,'axes.titlesize':12,'axes.titleweight':'bold','axes.titlecolor':T1})
g=gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); g=g[g.sido=='11'].copy(); g['code']=g.adm_cd2.str[:8]
D=pd.read_csv('work/dong_features_plus.csv',dtype={'code':str})
C=pd.read_csv('work/gap34_clusters.csv',dtype={'code':str})[['code','cluster']]
G=g.merge(D,on='code',how='left').merge(C,on='code',how='left')
TYPE={0:('A 외곽 저밀형',S1),1:('B 역세권 단절형',S2),2:('C 취약 고령형',S3)}
# Fig1: two panels
fig,ax=plt.subplots(1,2,figsize=(12,5.6))
cmap=LinearSegmentedColormap.from_list('seq',SEQ)
G.plot(column='car15',cmap=cmap,ax=ax[0],edgecolor=SURF,linewidth=0.3,legend=True,legend_kwds={'shrink':0.6,'label':'1~5km 차량 이동 (건/일, 출발 기준)'})
ax[0].set_title('① 동별 단거리(1~5km) 차량 이동량'); ax[0].axis('off')
G.plot(color='#e9e8e4',ax=ax[1],edgecolor=SURF,linewidth=0.3)
for k,(lab,col) in TYPE.items():
    sub=G[G.cluster==k]; sub.plot(color=col,ax=ax[1],edgecolor=SURF,linewidth=0.6,label=lab)
from matplotlib.patches import Patch
ax[1].legend(handles=[Patch(color=c,label=f"{l} ({int((G.cluster==k).sum())}곳)") for k,(l,c) in TYPE.items()],loc='lower left',frameon=False,fontsize=9,labelcolor=T1)
ax[1].set_title('② 대중교통 공백 + 단거리 차량 의존 동 34곳 (유형별)'); ax[1].axis('off')
for _,r in G[G.cluster.notna()].sort_values('car15',ascending=False).head(6).iterrows():
    p=r.geometry.representative_point(); ax[1].annotate(r.adm_nm.split()[-1],(p.x,p.y),fontsize=7.5,color=T1,ha='center',xytext=(0,6),textcoords='offset points')
fig.text(0.01,0.01,'자료: 서울시·KT 수도권 생활이동(2026.8.26~29), 서울 열린데이터광장, 통계청 SGIS 경계(vuski/admdongkor)',fontsize=7.5,color=T2)
plt.tight_layout(); plt.savefig('out/fig/fig1_map.png',dpi=200); plt.close()
# Fig2: SHAP importance
X=pd.read_pickle('work/od_model_data.pkl'); m=lgb.Booster(model_file='work/lgb_od.txt'); cols=m.feature_name()
Sm=X[cols].sample(5000,random_state=1); sv=shap.TreeExplainer(m).shap_values(Sm)
imp=pd.Series(np.abs(sv).mean(0)*100,index=cols).sort_values().tail(10)
sign={c:np.sign(np.corrcoef(Sm[c],sv[:,cols.index(c)])[0,1]) for c in imp.index}
LAB={'dist':'이동 거리','o_bus_density':'출발지 버스정류장 밀도','d_bus_density':'도착지 버스정류장 밀도','o_slope_pct':'출발지 경사','d_slope_pct':'도착지 경사','d_sub_dist_km':'도착지 지하철역 거리','o_sub_dist_km':'출발지 지하철역 거리','o_pop_density':'출발지 인구밀도','d_pop_density':'도착지 인구밀도','d_elder_pct':'도착지 고령인구 비율','o_elder_pct':'출발지 고령인구 비율','o_bike_density':'출발지 따릉이 밀도','d_bike_density':'도착지 따릉이 밀도','o_recip_pct':'출발지 수급자 비율','d_recip_pct':'도착지 수급자 비율'}
fig,ax=plt.subplots(figsize=(7.5,4.6))
ax.barh([LAB[c] for c in imp.index],imp.values,color=S1,height=0.6)
for i,c in enumerate(imp.index):
    ax.text(imp.values[i]+0.03,i,f"{imp.values[i]:.2f}  ({'값↑ 차량↑' if sign[c]>0 else '값↑ 차량↓'})",va='center',fontsize=8.5,color=T2)
ax.set_xlabel('평균 |SHAP| (차량 이용 비율, %p)'); ax.set_xlim(0,imp.max()*1.55)
ax.set_title('③ 단거리 차량 이용을 설명하는 요인 (LightGBM + SHAP)'); ax.grid(axis='x',color=GRID,lw=0.6); ax.set_axisbelow(True)
for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig2_shap.png',dpi=200); plt.close()
# Fig3: hourly profile
con=duckdb.connect('work/mob.duckdb')
h=con.execute("select left(st,2) hr, sum(cnt)/4 v from allw where left(o,2)='11' and left(d,2)='11' and m='8' and dist between 1000 and 4999 group by 1 order by 1").fetchdf()
fig,ax=plt.subplots(figsize=(7.5,3.4))
ax.plot(h.hr.astype(int),h.v/1000,color=S1,lw=2); ax.fill_between(h.hr.astype(int),h.v/1000,color=S1,alpha=0.08)
ax.set_xticks(range(0,24,2)); ax.set_xlabel('출발 시각'); ax.set_ylabel('천 건/일')
ax.axvspan(10.5,13.5,color=GRID,alpha=0.6,lw=0); ax.text(12,h.v.max()/1000*0.12,'낮 생활 이동',ha='center',fontsize=8.5,color=T2)
ax.set_title('④ 1~5km 차량 이동의 시간대 분포 (4일 평균)'); ax.grid(axis='y',color=GRID,lw=0.6)
for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig3_hourly.png',dpi=200); plt.close()
# Fig4: carbon scenario ranges
low,base,high=111613,247256,308638
fig,ax=plt.subplots(figsize=(7.5,3.2))
for i,r in enumerate([0.05,0.10,0.20]):
    ax.plot([low*r/1000,high*r/1000],[i,i],color=S1,lw=6,solid_capstyle='round',alpha=0.35)
    ax.plot(base*r/1000,i,'o',color=S1,ms=9,mec=SURF,mew=2)
    ax.text(high*r/1000+0.8,i,f"{low*r/1000:.1f}~{high*r/1000:.1f}천 t (기본 {base*r/1000:.1f})",va='center',fontsize=8.5,color=T2)
ax.axvline(0.962,color=T2,lw=1,ls='--'); ax.text(0.962,2.45,' 따릉이 인증 감축량(연 962t)',fontsize=8,color=T2)
ax.set_yticks(range(3),['5% 전환','10% 전환','20% 전환']); ax.set_xlabel('연간 CO2 감축량 (천 t)'); ax.set_ylim(-0.6,2.8); ax.set_xlim(0,high*0.2/1000*1.6)
ax.set_title('⑤ 단거리 차량 이동 전환 시 탄소 감축 시나리오'); ax.grid(axis='x',color=GRID,lw=0.6)
for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig4_carbon.png',dpi=200); plt.close()
print('done')
