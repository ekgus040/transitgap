import pandas as pd, numpy as np, geopandas as gpd, duckdb, matplotlib
matplotlib.use('Agg'); import koreanize_matplotlib, matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import lightgbm as lgb, shap
SURF='#fcfcfb'; T1='#0b0b0b'; T2='#52514e'; GRID='#e4e3df'; TINT='#d9d7d0'
S1,S2,S3='#2a78d6','#eb6834','#1baf7a'
SEQ=['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b']
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'axes.edgecolor':GRID,'axes.labelcolor':T2,'xtick.color':T2,'ytick.color':T2,'font.size':10,'axes.titlesize':12,'axes.titleweight':'bold','axes.titlecolor':T1})
g=gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); g=g[g.sido=='11'].copy(); g['code']=g.adm_cd2.str[:8]
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
C=pd.read_csv('work/priority_clusters.csv',dtype={'code':str})[['code','cluster']]
G=g.merge(D,on='code',how='left').merge(C,on='code',how='left')
TYPE={2:('A 외곽 저밀형',S1),1:('B 버스 연계 부족형',S2),0:('C 취약 고령형',S3)}
# 그림 1
fig,ax=plt.subplots(1,2,figsize=(12,5.6))
G.plot(column='car15',cmap=LinearSegmentedColormap.from_list('seq',SEQ),ax=ax[0],edgecolor=SURF,linewidth=0.3,legend=True,legend_kwds={'shrink':0.6,'label':'1~5km 차량 이동 (건/일, 출발 기준)'})
ax[0].set_title('(가) 동별 단거리(1~5km) 차량 이동량'); ax[0].axis('off')
G.plot(color='#efeee9',ax=ax[1],edgecolor=SURF,linewidth=0.3)
G[G.gap_supply==True].plot(color=TINT,ax=ax[1],edgecolor=SURF,linewidth=0.3)
for k,(lab,col) in TYPE.items(): G[G.cluster==k].plot(color=col,ax=ax[1],edgecolor=SURF,linewidth=0.6)
h=[Patch(color=TINT,label=f"대중교통 공백 동 ({int((G.gap_supply==True).sum())}곳, 공급 기준)")]+[Patch(color=c,label=f"{l} ({int((G.cluster==k).sum())}곳)") for k,(l,c) in TYPE.items()]
ax[1].legend(handles=h,loc='lower left',frameon=False,fontsize=8.5,labelcolor=T1)
ax[1].set_title('(나) 공백 동 중 단거리 차량 의존 우선 대상 40곳'); ax[1].axis('off')
for _,r in G[G.cluster.notna()].sort_values('car15',ascending=False).head(6).iterrows():
    p=r.geometry.representative_point(); ax[1].annotate(r.adm_nm.split()[-1],(p.x,p.y),fontsize=7.5,color=T1,ha='center',xytext=(0,6),textcoords='offset points')
fig.text(0.01,0.01,'자료: 서울시·KT 수도권 생활이동(2026.8.26~29), 서울 열린데이터광장(지하철역·버스 노선별 정류소), 통계청 SGIS 경계(vuski/admdongkor)',fontsize=7.5,color=T2)
plt.tight_layout(); plt.savefig('out/fig/fig1_map.png',dpi=200); plt.close()
# 그림 2
X=pd.read_pickle('work/od_model_data_v2.pkl'); m=lgb.Booster(model_file='work/lgb_od_v2.txt'); cols=m.feature_name()
Sm=X[cols].sample(5000,random_state=1); sv=shap.TreeExplainer(m).shap_values(Sm)
imp=pd.Series(np.abs(sv).mean(0)*100,index=cols).sort_values().tail(10)
sign={c:np.sign(np.corrcoef(Sm[c],sv[:,cols.index(c)])[0,1]) for c in imp.index}
nm={'dist':'이동 거리','bus_density':'버스정류장 밀도','route_stop_density':'버스 노선·정류장 밀도','slope_pct':'경사','sub_dist_km':'지하철역 거리','pop_density':'인구밀도','elder_pct':'고령인구 비율','bike_density':'따릉이 밀도','recip_pct':'수급자 비율'}
lab=lambda c: '이동 거리' if c=='dist' else ('출발지 ' if c[0]=='o' else '도착지 ')+nm[c[2:]]
fig,ax=plt.subplots(figsize=(7.5,4.6))
ax.barh([lab(c) for c in imp.index],imp.values,color=S1,height=0.6)
for i,c in enumerate(imp.index): ax.text(imp.values[i]+0.03,i,f"{imp.values[i]:.2f}  ({'값↑ 차량↑' if sign[c]>0 else '값↑ 차량↓'})",va='center',fontsize=8.5,color=T2)
ax.set_xlabel('평균 |SHAP| (차량 이용 비율, %p)'); ax.set_xlim(0,imp.max()*1.55)
ax.set_title('단거리 차량 이용을 설명하는 요인 (LightGBM + SHAP)'); ax.grid(axis='x',color=GRID,lw=0.6); ax.set_axisbelow(True)
for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig2_shap.png',dpi=200); plt.close()
# 그림 3
con=duckdb.connect('work/mob.duckdb',read_only=True)
h=con.execute("select left(st,2) hr, sum(cnt)/4 v from allw where left(o,2)='11' and left(d,2)='11' and m='8' and dist between 1000 and 4999 group by 1 order by 1").fetchdf()
fig,ax=plt.subplots(figsize=(7.5,3.4))
ax.plot(h.hr.astype(int),h.v/1000,color=S1,lw=2); ax.fill_between(h.hr.astype(int),h.v/1000,color=S1,alpha=0.08)
ax.set_xticks(range(0,24,2)); ax.set_xlabel('출발 시각'); ax.set_ylabel('천 건/일')
ax.axvspan(10.5,13.5,color=GRID,alpha=0.6,lw=0); ax.text(12,h.v.max()/1000*0.12,'낮 생활 이동',ha='center',fontsize=8.5,color=T2)
ax.set_title('1~5km 차량 이동의 시간대 분포 (4일 평균)'); ax.grid(axis='y',color=GRID,lw=0.6)
for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig3_hourly.png',dpi=200); plt.close()
# 그림 4: 우선 대상 40곳(정책 효과) vs 서울 전체(잠재량)
P=pd.read_csv('out/priority_carbon.csv'); lo,ba,hi=P['연간배출_t'].tolist()
SL,SB,SH=111613,247256,308638
rows=[('우선 대상 40곳 10% 전환',lo*.1,ba*.1,hi*.1,S1),('우선 대상 40곳 20% 전환',lo*.2,ba*.2,hi*.2,S1),('우선 대상 40곳 30% 전환',lo*.3,ba*.3,hi*.3,S1),('(참고) 서울 전체 10% 전환 잠재량',SL*.1,SB*.1,SH*.1,'#8a8984')]
fig,ax=plt.subplots(figsize=(7.5,3.4))
for i,(l,a,b,c,col) in enumerate(rows[::-1]):
    ax.plot([a/1000,c/1000],[i,i],color=col,lw=6,solid_capstyle='round',alpha=0.35); ax.plot(b/1000,i,'o',color=col,ms=9,mec=SURF,mew=2)
    ax.text(c/1000+0.6,i,f"{a/1000:.1f}~{c/1000:.1f}천 t (기본 {b/1000:.1f})",va='center',fontsize=8.5,color=T2)
ax.axvline(0.962,color=T2,lw=1,ls='--'); ax.text(0.962,3.45,' 따릉이 인증 감축량(연 962t)',fontsize=8,color=T2)
ax.set_yticks(range(4),[r[0] for r in rows[::-1]]); ax.set_xlabel('연간 CO2 감축량 (천 t)'); ax.set_ylim(-0.6,3.8); ax.set_xlim(0,SH*0.1/1000*1.45)
ax.set_title('단거리 차량 이동 전환 시 탄소 감축 시나리오'); ax.grid(axis='x',color=GRID,lw=0.6)
for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig4_carbon.png',dpi=200); plt.close()
# 그림 3·4 나란히(보고서 분량용)
from PIL import Image
a=Image.open('out/fig/fig3_hourly.png'); b=Image.open('out/fig/fig4_carbon.png')
W=Image.new('RGB',(a.width+b.width+40,max(a.height,b.height)),(252,252,251)); W.paste(a,(0,0)); W.paste(b,(a.width+40,0)); W.save('out/fig/fig34_combined.png'); print('done')
