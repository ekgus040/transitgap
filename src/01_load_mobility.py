# 수도권 생활이동(출도착 행정동별 수단) 4일치 로드 -> DuckDB (data_raw/d2026MMDD/*.csv 압축 해제 필요)
import os; os.makedirs('work',exist_ok=True); os.makedirs('out/fig',exist_ok=True)
import duckdb
con=duckdb.connect('work/mob.duckdb')
for d in ('0826','0827','0828','0829'):
    con.execute(f"""create or replace table t{d} as select o_admdong_cd o, d_admdong_cd d, st_time_cd st, move_trans m,
     try_cast(move_dist as double) dist, try_cast(move_time as double) tm, try_cast(cnt as double) cnt
     from read_csv('data_raw/d{d}/*.csv', header=true, all_varchar=true, ignore_errors=true) where in_forn_div_nm='내국인'""")
con.execute("""create or replace table allw as select '0826' as dy,* from t0826 union all select '0827',* from t0827
 union all select '0828',* from t0828 union all select '0829',* from t0829""")
for t in ('t0826','t0827','t0828','t0829'):
    r=con.execute(f"""select sum(case when m='8' and dist>=500 then cnt end), sum(case when m='8' and dist between 1000 and 4999 then cnt end)
     from {t} where left(o,2)='11' and left(d,2)='11'""").fetchone()
    print(t, f"car {r[0]:,.0f} | car1-5km {r[1]:,.0f} ({100*r[1]/r[0]:.1f}%)")
# 서울 행정동 코드-이름 테이블
import json
g=json.load(open('data_raw/HangJeongDong_ver20250401.geojson'))
rows=[(f['properties']['adm_cd2'][:8], f['properties']['sggnm'], f['properties']['adm_nm'].split(' ')[-1]) for f in g['features'] if f['properties']['sido']=='11']
con.execute("create or replace table dong(code varchar, gu varchar, nm varchar)"); con.executemany("insert into dong values (?,?,?)", rows)
print('dongs', len(rows))
