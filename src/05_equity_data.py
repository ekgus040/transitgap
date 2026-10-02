import pandas as pd, io, json, re, csv
g=json.load(open('data_raw/HangJeongDong_ver20250401.geojson'))
A=pd.DataFrame([{'code':f['properties']['adm_cd2'][:8],'gu':f['properties']['sggnm'],'nm':f['properties']['adm_nm'].split(' ')[-1]} for f in g['features'] if f['properties']['sido']=='11'])
GUS=set(A.gu)
norm=lambda s: re.sub(r'[·\.\,\s]','',str(s))
# population
t=open('data_raw/201_DT_201004_O020029_20261001162219.csv','rb').read().decode('utf-8-sig','replace')
rows=[]; gu=None
for r in csv.reader(io.StringIO(t)):
    if not r or r[0] in ('동별',): continue
    name,age=r[0],r[1]; val=r[4] if len(r)>4 else ''
    if name in GUS: gu=name; continue
    if name=='합계': continue
    v=pd.to_numeric(val.replace(',',''),errors='coerce')
    m=re.match(r'(\d+)',age); a=int(m.group(1)) if m else None
    rows.append((gu,name,age,a,v))
P=pd.DataFrame(rows,columns=['gu','dong','age','a','v'])
pp=P.groupby(['gu','dong']).apply(lambda d: pd.Series({'pop':d[d.age=='합계'].v.sum(),'pop65':d[d.a>=65].v.sum()})).reset_index()
pp['k']=pp.dong.map(norm)
# recipients
t=open('data_raw/국민기초생활보장+수급자(2020+이후)_20261001162017.csv','rb').read().decode('utf-8-sig','replace')
R=pd.read_csv(io.StringIO(t),header=None,skiprows=4)[[0,1,4]]; R.columns=['gu','dong','recip']
R['gu']=R.gu.ffill(); R=R[(R.dong!='소계')&(R.gu.isin(GUS))]
R['recip']=pd.to_numeric(R.recip.astype(str).str.replace(',',''),errors='coerce'); R['k']=R.dong.map(norm)
A['k']=A.nm.map(norm)
M=A.merge(pp[['gu','k','pop','pop65']],on=['gu','k'],how='left').merge(R[['gu','k','recip']],on=['gu','k'],how='left')
print('pop matched',M['pop'].notna().sum(),'/',len(M),' recip matched',M.recip.notna().sum())
print('unmatched pop:',M[M['pop'].isna()][['gu','nm']].values.tolist())
print('unmatched recip:',M[M.recip.isna()][['gu','nm']].values.tolist())
M['elder_pct']=100*M.pop65/M['pop']; M['recip_pct']=100*M.recip/M['pop']
print(M[['elder_pct','recip_pct']].describe().round(1).to_string())
M.to_csv('work/equity_dong.csv',index=False,encoding='utf-8-sig')
