# 추가 데이터 ①: 수도권 생활이동(도착 행정동 기준 성·연령별 수단, 내국인) 2026년 5~9월
#  (1) 계절성: 동별 차량 비중 월간 순위상관, 우선 대상(36곳) vs 서울
#  (2) 고령자 이동 격차: 60·70대 이상 도착 이동의 수단 구성과 1인당 이동 횟수(유형별)
import pandas as pd, numpy as np, io, csv, re, json
E=pd.concat([pd.read_csv(f'data_raw/extra/age_2026{m:02d}.csv',dtype={'dong':str,'mode':str,'ym':str}) for m in range(5,10)])
days=E[E.dong=='_days'].groupby(['ym','wk']).cnt.sum()
E=E[E.dong!='_days']; E['dong']=E.dong.str[:8]
D=pd.read_csv('work/dong_features_v2.csv',dtype={'code':str})
P=pd.read_csv('work/priority_clusters.csv',dtype={'code':str})[['code','cluster']]
D=D.merge(P,on='code',how='left'); lab={0:'C',1:'B',2:'A'}
D['grp']=np.where(D.priority,D.cluster.map(lab),np.where(D.gap_supply,'공백(기타)','나머지'))
# 연령별 인구(60+, 70+)
g=json.load(open('data_raw/HangJeongDong_ver20250401.geojson'))
A=pd.DataFrame([{'code':f['properties']['adm_cd2'][:8],'gu':f['properties']['sggnm'],'nm':f['properties']['adm_nm'].split(' ')[-1]} for f in g['features'] if f['properties']['sido']=='11'])
GUS=set(A.gu); norm=lambda s: re.sub(r'[·\.\,\s]','',str(s))
t=open('data_raw/201_DT_201004_O020029_20261001162219.csv','rb').read().decode('utf-8-sig','replace'); rows=[]; gu=None
for r in csv.reader(io.StringIO(t)):
    if not r or r[0]=='동별': continue
    name,age=r[0],r[1]; val=r[4] if len(r)>4 else ''
    if name in GUS: gu=name; continue
    if name=='합계': continue
    m=re.match(r'(\d+)',age); rows.append((gu,name,age,int(m.group(1)) if m else None,pd.to_numeric(val.replace(',',''),errors='coerce')))
PP=pd.DataFrame(rows,columns=['gu','dong','age','a','v'])
pp=PP.groupby(['gu','dong']).apply(lambda d: pd.Series({'pop_all':d[d.age=='합계'].v.sum(),'pop60':d[d.a>=60].v.sum(),'pop70':d[d.a>=70].v.sum()})).reset_index()
pp['k']=pp.dong.map(norm); A['k']=A.nm.map(norm)
A=A.merge(pp.drop(columns='dong'),on=['gu','k'],how='left')
D=D.merge(A[['code','pop60','pop70']],on='code',how='left')
print('인구 매칭',D.pop60.notna().sum(),'/',len(D))
# 평일 기준
W=E[E.wk=='wd'].copy()
W['m']=W['mode'].map(lambda x:{'4':'bus','5':'bus','6':'sub','7':'walk','8':'car','9':'etc'}.get(x,'far'))
W=W[W.m!='far']
piv=W.pivot_table(index=['ym','dong','age'],columns='m',values='cnt',aggfunc='sum',fill_value=0).reset_index()
piv['tot']=piv[['bus','sub','walk','car','etc']].sum(axis=1)
# (1) 계절성: 전 연령 차량 비중(9번 제외 분모)
a=piv[piv.age=='all'].copy(); a['car_sh']=100*a.car/(a.tot-a.etc)
S=a.pivot(index='dong',columns='ym',values='car_sh').dropna()
S=S[S.index.isin(D.code)]
rc=S.corr(method='spearman').round(3); print(rc)
X=D[['code','grp','priority','car_share15']].merge(S,left_on='code',right_index=True)
print('4일 1~5km 차량비중 vs 월별 도착 차량비중 순위상관', {c: round(X['car_share15'].corr(X[c],method='spearman'),3) for c in S.columns})
seas=X.groupby('priority')[list(S.columns)].mean().round(1); print(seas)
# 우선 대상(36곳) 재현: 공백 동 중 월별 차량비중 상위 25%(전체 동 기준) → 기본 선정과 겹침
base=set(D[D.priority].code); res={}
for c in S.columns:
    thr=X[c].quantile(.75); sel=set(X[(X.code.isin(D[D.gap_supply].code))&(X[c]>=thr)].code); res[c]=(len(sel),len(sel&base))
print('월별 재선정(선정수, 기본 선정과 겹침)',res)
# (2) 고령자: 8월+9월 평일 평균 일 이동, 수단 구성
dw=days.xs('wd',level='wk')
b=piv[piv.ym.isin(['202608','202609'])].groupby(['dong','age'])[['bus','sub','walk','car','etc','tot']].sum().reset_index()
nd=dw.loc[['202608','202609']].sum()
b[['bus','sub','walk','car','etc','tot']]=b[['bus','sub','walk','car','etc','tot']]/nd
Bm=b.pivot(index='dong',columns='age',values=['bus','sub','walk','car','etc','tot'])
Bm.columns=[f'{m}_{a}' for m,a in Bm.columns]; Bm=Bm.reset_index().rename(columns={'dong':'code'})
Y=D.merge(Bm,on='code')
Y['young_car']=Y.car_all-Y.car_60-Y.car_70; Y['young_tot']=Y.tot_all-Y.tot_60-Y.tot_70
def summ(g):
    s=lambda c: g[c].sum()
    el_tot=s('tot_60')+s('tot_70')-s('etc_60')-s('etc_70')
    return pd.Series({'동수':len(g),
     '고령(60+) 차량%':100*(s('car_60')+s('car_70'))/el_tot,
     '고령 버스·지하철%':100*(s('bus_60')+s('bus_70')+s('sub_60')+s('sub_70'))/el_tot,
     '고령 도보%':100*(s('walk_60')+s('walk_70'))/el_tot,
     '60세 미만 차량%':100*s('young_car')/(s('young_tot')-(s('etc_all')-s('etc_60')-s('etc_70'))),
     '70+ 1인당 일 이동':s('tot_70')/s('pop70'),
     '60+ 1인당 일 이동':(s('tot_60')+s('tot_70'))/s('pop60')})
order=['A','B','C','공백(기타)','나머지']
T=Y.dropna(subset=['pop60']).groupby('grp').apply(summ).reindex(order); T.loc['서울 전체']=summ(Y.dropna(subset=['pop60']))
print(T.round(2).to_string())
# 구 고정효과: 접근성 지표와 70+ 1인당 이동(인구 가중)
import statsmodels.formula.api as smf
Y['trip70pc']=Y.tot_70/Y.pop70; Y['l_rsd']=np.log(Y.route_stop_density)
Z=Y.dropna(subset=['trip70pc']); Z=Z[(Z.pop70>500)&(Z.trip70pc<Z.trip70pc.quantile(.95))]
for y in ['trip70pc']:
    m=smf.wls(f'{y} ~ sub_dist_km + l_rsd + slope_pct + C(gu)',data=Z,weights=Z.pop70).fit(cov_type='cluster',cov_kwds={'groups':Z.gu})
    print(y,'n',len(Z),{k:(round(m.params[k],3),round(m.pvalues[k],4)) for k in ['sub_dist_km','l_rsd','slope_pct']})
print(Y[Y.nm.isin(['도봉1동','방화2동','방화3동','진관동','양재1동'])][['nm','trip70pc']].round(2).to_string(index=False))
T.round(2).to_csv('out/elderly_mobility_by_type.csv',encoding='utf-8-sig'); rc.to_csv('out/season_rankcorr.csv',encoding='utf-8-sig'); seas.to_csv('out/season_priority_carshare.csv',encoding='utf-8-sig')
pd.DataFrame(res,index=['선정수','기본선정겹침']).to_csv('out/season_reselect.csv',encoding='utf-8-sig')
