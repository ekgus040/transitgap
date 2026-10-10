# 그림 v4: 그림 1(가)를 이동량 대신 1~5km 차량 비중(%) 지도로, 그림 4는 모델 시나리오를 버스 보강·역 연계 상한 2행으로 분리
import pandas as pd, numpy as np, geopandas as gpd, duckdb, matplotlib
matplotlib.use('Agg'); import koreanize_matplotlib, matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
SURF='#fcfcfb'; T1='#0b0b0b'; T2='#52514e'; GRID='#e4e3df'; TINT='#d9d7d0'
S1,S2,S3='#2a78d6','#eb6834','#1baf7a'
SEQ=['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b']
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'axes.edgecolor':GRID,'axes.labelcolor':T2,'xtick.color':T2,'ytick.color':T2,'font.size':11,'axes.titlesize':12.5,'axes.titleweight':'bold','axes.titlecolor':T1})
g=gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); g=g[g.sido=='11'].copy(); g['code']=g.adm_cd2.str[:8]
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
C=pd.read_csv('work/priority_clusters.csv',dtype={'code':str})[['code','cluster']]
G=g.merge(D,on='code',how='left').merge(C,on='code',how='left')
NP=int(G.cluster.notna().sum())
RICH=G[G.sggnm.isin(['강남구','서초구','송파구','용산구'])].dissolve(by='sggnm')
TYPE={2:('A 외곽 저밀형',S1),1:('B 버스 연계 부족형',S2),0:('C 취약 고령형',S3)}
fig,ax=plt.subplots(1,2,figsize=(7.4,2.95),gridspec_kw={'wspace':0.0})
fig.subplots_adjust(left=0,right=1,top=0.9,bottom=0)
G['sh']=100*G.car_share15; VMIN,VMAX=12,34
G.plot(column='sh',cmap=LinearSegmentedColormap.from_list('seq',SEQ),ax=ax[0],edgecolor=SURF,linewidth=0.2,vmin=VMIN,vmax=VMAX)
sm=plt.cm.ScalarMappable(cmap=LinearSegmentedColormap.from_list('seq',SEQ),norm=plt.Normalize(VMIN,VMAX))
cax=ax[0].inset_axes([0.02,0.06,0.03,0.38]); cb=fig.colorbar(sm,cax=cax); cb.ax.tick_params(labelsize=8.5); cb.outline.set_visible(False)
ax[0].text(0.0,0.47,'차량 %',transform=ax[0].transAxes,fontsize=8.5,color=T2,ha='left',va='bottom',bbox=dict(facecolor=SURF,edgecolor='none',pad=0.5))
ax[0].set_title('(가) 동별 1~5km 이동 중 차량 비중',fontsize=11.5); ax[0].axis('off')
G.plot(color='#efeee9',ax=ax[1],edgecolor=SURF,linewidth=0.2)
G[G.gap_supply==True].plot(color=TINT,ax=ax[1],edgecolor=SURF,linewidth=0.2)
for k,(lab,col) in TYPE.items(): G[G.cluster==k].plot(color=col,ax=ax[1],edgecolor=SURF,linewidth=0.4)
RICH.boundary.plot(ax=ax[1],color=T1,linewidth=0.8,linestyle=(0,(2,1.5)))
h=[Patch(color=c,label=f"{l[0]} {int((G.cluster==k).sum())}곳") for k,(l,c) in TYPE.items()]+[Patch(color=TINT,label='기타 공백 동'),Line2D([0],[0],color=T1,lw=0.8,ls=(0,(2,1.5)),label='고소득 4개 구')]
ax[1].legend(handles=h,loc='upper left',bbox_to_anchor=(-0.04,1.0),frameon=False,fontsize=8.6,labelcolor=T1,handlelength=1.1,labelspacing=0.3)
ax[1].set_title(f'(나) 우선 대상 {NP}곳(A·B·C 유형)',fontsize=11.5); ax[1].axis('off')
for nm_ in ['도봉1동','방화2동','양재1동','진관동']:
    r=G[G.adm_nm.str.endswith(nm_)].iloc[0]; p=r.geometry.representative_point()
    ax[1].annotate(nm_,(p.x,p.y),fontsize=8.6,color=T1,ha='center',xytext=(0,5),textcoords='offset points',fontweight='bold')
plt.savefig('out/fig/fig1_compact.png',dpi=250,bbox_inches='tight',pad_inches=0.03); plt.close()
# 그림 3·4
con=duckdb.connect('work/mob.duckdb',read_only=True)
h=con.execute("select left(st,2) hr, sum(cnt)/4 v from allw where left(o,2)='11' and left(d,2)='11' and m='8' and dist between 1000 and 4999 group by 1 order by 1").fetchdf()
P=pd.read_csv('out/priority_carbon.csv'); lo,ba,hi=P['연간배출_t'].tolist(); SL,SB,SH=111613,247256,308638
M=pd.read_csv('out/counterfactual_access_carbon.csv'); m2=M[M.시나리오.str.startswith('S2')]
m1=M[M.시나리오.str.startswith('S1')]; mlo=m1['배출회피_보수_t'].min(); mba=m1[m1.계수.str.startswith('중앙')]['배출회피_기본_t'].iloc[0]; mhi=m2['배출회피_높음_t'].max()
fig,(a1,a2)=plt.subplots(1,2,figsize=(11,3.3),gridspec_kw={'width_ratios':[1,1.25]})
a1.plot(h.hr.astype(int),h.v/1000,color=S1,lw=2); a1.fill_between(h.hr.astype(int),h.v/1000,color=S1,alpha=0.08)
a1.set_xticks(range(0,24,3)); a1.set_xlabel('출발 시각'); a1.set_ylabel('천 건/시간(4일 평균)')
a1.axvspan(10.5,13.5,color=GRID,alpha=0.6,lw=0); a1.text(12,h.v.max()/1000*0.1,'낮 생활 이동',ha='center',fontsize=10,color=T2)
a1.set_title('(가) 1~5km 차량 이동 시간대 분포',fontsize=11.5); a1.grid(axis='y',color=GRID,lw=0.6)
rows=[(f'{NP}곳 버스 보강(모델)',mlo,mba,m1['배출회피_높음_t'].max(),S3),('+역 연계 상한(모델)',m2['배출회피_보수_t'].min(),m2[m2.계수.str.startswith('중앙')]['배출회피_기본_t'].iloc[0],mhi,S3),(f'{NP}곳 10% 전환(가정)',lo*.1,ba*.1,hi*.1,S1),(f'{NP}곳 20% 전환(가정)',lo*.2,ba*.2,hi*.2,S1),(f'{NP}곳 30% 전환(가정)',lo*.3,ba*.3,hi*.3,S1),('서울 전체 10% 전환(가정)',SL*.1,SB*.1,SH*.1,'#8a8984')]
N=len(rows)
for i,(l,a,b,c,col) in enumerate(rows[::-1]):
    a2.plot([a/1000,c/1000],[i,i],color=col,lw=6,solid_capstyle='round',alpha=0.4); a2.plot(b/1000,i,'o',color=col,ms=8,mec=SURF,mew=2)
    a2.text(c/1000+0.6,i,f"{a/1000:.1f}~{c/1000:.1f}천 t",va='center',fontsize=10,color=T2)
a2.axvline(0.962,color=T2,lw=1,ls='--'); a2.text(1.2,N-0.55,'참고: 따릉이 인증 감축량(962t)',fontsize=9.5,color=T2)
a2.set_yticks(range(N),[r[0] for r in rows[::-1]]); a2.set_xlabel('연간 차량 배출 회피 잠재량 (천 tCO2)'); a2.set_ylim(-0.6,N-0.2); a2.set_xlim(0,SH*0.1/1000*1.4)
a2.set_title('(나) 차량 배출 회피 잠재량',fontsize=11.5); a2.grid(axis='x',color=GRID,lw=0.6)
for ax in (a1,a2):
    for s in ('top','right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig34_combined.png',dpi=220); plt.close(); print('ok',round(mlo),round(mba),round(mhi))
