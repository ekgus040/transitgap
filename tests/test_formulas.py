"""원자료 없이 수행하는 회귀 입력·평일/주말 가중·탄소 산식 단위 테스트."""
import ast
from datetime import date
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TestFormulaContracts(unittest.TestCase):
    def test_weighted_distance_matches_manual_case(self):
        c=sqlite3.connect(':memory:')
        c.execute('create table t(dist real,cnt real)')
        c.executemany('insert into t values (?,?)', [(1000,10),(4000,1000)])
        avg,wavg=c.execute('select avg(dist),sum(dist*cnt)/sum(cnt) from t').fetchone()
        self.assertEqual(avg,2500)
        self.assertAlmostEqual(wavg, (1000*10+4000*1000)/1010)
        self.assertNotAlmostEqual(avg,wavg)
        code=(ROOT/'src/07_od_table.py').read_text()
        self.assertIn('sum(dist * cnt) / nullif(sum(cnt), 0)',code)
    def test_weekday_weekend_weights(self):
        dates=[date(2026,8,d) for d in (26,27,28,29)]
        self.assertEqual([d.weekday()<5 for d in dates],[True,True,True,False])
        # 평일 100건, 주말 40건이면 4일 단순평균 85건과 대표 주간 가중평균 약 82.86건이 다름
        plain=(100+100+100+40)/4
        weighted=(5*100+2*40)/7
        self.assertAlmostEqual(plain,85)
        self.assertAlmostEqual(weighted,82.857142857)
        self.assertNotAlmostEqual(plain,weighted)
        code=(ROOT/'src/20_priority_typology_carbon.py').read_text()
        self.assertIn("5*means['weekday']+2*means['weekend']", code)
    def test_carbon_units(self):
        passenger_km=100_000
        det,occ,ef=1.3,1.3,220
        annual=passenger_km*det/occ*ef/1e6*365
        self.assertAlmostEqual(annual,8030)
    def test_all_python_syntax(self):
        for f in (ROOT/'src').glob('*.py'):
            ast.parse(f.read_text(),filename=str(f))

if __name__=='__main__': unittest.main()
