import csv, sys, collections, datetime
out=collections.defaultdict(float)
for p in sys.argv[2:]:
    with open(p,encoding='cp949',errors='replace') as f:
        r=csv.reader(f); next(r)
        for row in r:
            try: d=row[0]; ars=row[4]; sid=row[3]; on=float(row[6]); off=float(row[7])
            except: continue
            dt=datetime.date(int(d[:4]),int(d[4:6]),int(d[6:8])); wk='we' if dt.weekday()>=5 else 'wd'
            out[(d[:6],wk,sid,ars,'on')]+=on; out[(d[:6],wk,sid,ars,'off')]+=off
            if d in ('20260826','20260827','20260828','20260829'): out[('4day','x',sid,ars,'on')]+=on
with open(sys.argv[1],'w',newline='') as f:
    w=csv.writer(f); w.writerow(['ym','wk','sid','ars','kind','cnt'])
    for k,v in out.items(): w.writerow(list(k)+[v])
