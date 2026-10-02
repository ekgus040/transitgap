import pandas as pd
car_all=car15=pkm15=0.0
for ch in pd.read_csv('data_raw/d0826/seoul_trans_admdong3_final_20260826.csv', dtype=str, chunksize=1_000_000, on_bad_lines='skip'):
    ch=ch[(ch.in_forn_div_nm=='내국인') & ch.o_admdong_cd.str.startswith('11') & ch.d_admdong_cd.str.startswith('11') & (ch.move_trans=='8')]
    dist=pd.to_numeric(ch.move_dist, errors='coerce'); cnt=pd.to_numeric(ch.cnt, errors='coerce')
    car_all+=cnt[dist>=500].sum()
    m=(dist>=1000)&(dist<=4999); car15+=cnt[m].sum(); pkm15+=(cnt[m]*dist[m]).sum()/1000
print(f"car>=500m {car_all:,.0f} | car1-5km {car15:,.0f} ({100*car15/car_all:.1f}%) | pkm {pkm15:,.0f}")
