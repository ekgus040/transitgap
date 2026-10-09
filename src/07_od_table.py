import duckdb, pandas as pd
con=duckdb.connect('work/mob.duckdb')
# OD-level 1-5km table (4-day avg) with mode split, for an OD-level model
con.execute("""create or replace table od15 as
 select o, d,
  sum(dist * cnt) / nullif(sum(cnt), 0) dist, -- OD 간 거리: 이동 인원수 가중 평균(m)
  sum(cnt)/4 tot,
  sum(case when m='8' then cnt else 0 end)/4 car,
  sum(case when m in ('4','5') then cnt else 0 end)/4 bus,
  sum(case when m='6' then cnt else 0 end)/4 sub,
  sum(case when m='7' then cnt else 0 end)/4 walk
 from allw where left(o,2)='11' and left(d,2)='11' and o<>d and dist between 1000 and 4999 and m in ('4','5','6','7','8','9')
 group by o,d""")
assert con.execute("select count(*) from od15 where dist is null or dist < 1000 or dist > 4999").fetchone()[0]==0, 'OD 거리 범위/분모 점검 실패'
print(con.execute("select count(*) n_od, round(sum(tot)) trips, round(sum(car)) car, round(sum(tot) filter (where tot>=20)) trips_od20, count(*) filter (where tot>=20) n_od20 from od15").fetchdf().to_string(index=False))
# dong-level context features
con.execute("""create or replace table dfeat as
 select o code, sum(cnt)/4 out_all,
  sum(case when m='6' then cnt else 0 end)/sum(cnt) sub_share_all,
  sum(case when m in ('4','5') then cnt else 0 end)/sum(cnt) bus_share_all,
  sum(case when m='8' then cnt else 0 end)/sum(cnt) car_share_all
 from allw where left(o,2)='11' and dist>=500 and m in ('4','5','6','7','8','9') group by o""")
print(con.execute("select count(*) from dfeat").fetchone())
