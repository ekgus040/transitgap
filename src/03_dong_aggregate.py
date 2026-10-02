import duckdb
con=duckdb.connect('work/mob.duckdb')
con.execute("""create or replace table allw as select '0826' as dy,* from t0826 union all select '0827',* from t0827 union all select '0828',* from t0828 union all select '0829',* from t0829""")
con.execute("""create or replace table dong4 as
 select o code, sum(case when m='8' and dist between 1000 and 4999 then cnt else 0 end)/4 car15,
 sum(case when dist between 1000 and 4999 and m in ('4','5','6','7','8','9') then cnt else 0 end)/4 all15,
 sum(case when m='8' and dist between 1000 and 4999 then cnt*dist else 0 end)/4000 car15_pkm
 from allw where left(o,2)='11' and left(d,2)='11' and dist>=500 group by o""")
con.execute("copy (select d.gu, d.nm, s.code, round(car15) car15_daily, round(all15) all15_daily, round(100*car15/nullif(all15,0),1) car_share15, round(car15_pkm) car15_pkm from dong4 s join dong d using(code) order by car15 desc) to 'out/dong_short_car_4day.csv' (header)")
print(con.execute("select d.gu, d.nm, round(car15) car15, round(100*car15/nullif(all15,0),1) as shr from dong4 s join dong d using(code) order by car15 desc limit 10").fetchdf().to_string())
