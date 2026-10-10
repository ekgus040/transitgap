import zipfile, csv, io, sys, datetime, collections
# 도착 행정동×월×평일/주말×수단별, 연령군(0~59, 60대, 70+) 합계
out=collections.defaultdict(float)
for zp in sys.argv[2:]:
    z=zipfile.ZipFile(zp)
    for inf in z.infolist():
        if not inf.filename.endswith('.csv'): continue
        ymd=inf.filename.split('_')[-1][:8]; d=datetime.date(int(ymd[:4]),int(ymd[4:6]),int(ymd[6:8]))
        wk='we' if d.weekday()>=5 else 'wd'; mon=ymd[:6]
        r=csv.reader(io.TextIOWrapper(z.open(inf),encoding='utf-8',errors='replace')); h=next(r)
        ix={k:i for i,k in enumerate(h)}
        a60=[ix['male_60_cnt'],ix['feml_60_cnt']]; a70=[ix['male_70_cnt'],ix['feml_70_cnt']]; tot=ix['total_cnt']
        for row in r:
            dc=row[0]
            if not dc.startswith('11'): continue
            try:
                t=float(row[tot]); s60=sum(float(row[i]) for i in a60); s70=sum(float(row[i]) for i in a70)
            except: continue
            k=(mon,wk,dc,row[2]); out[k+('all',)]+=t; out[k+('60',)]+=s60; out[k+('70',)]+=s70
        out[(mon,wk,'_days','_','n')]+=1
with open(sys.argv[1],'w',newline='') as f:
    w=csv.writer(f); w.writerow(['ym','wk','dong','mode','age','cnt'])
    for k,v in out.items(): w.writerow(list(k)+[round(v,2)])
