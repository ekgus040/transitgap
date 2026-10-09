"""저장된 보고서 근거 CSV 내부 일관성 감사(재학습/원자료 검증과 구분)."""
from pathlib import Path
import pandas as pd
import numpy as np

root=Path(__file__).resolve().parents[1]
out=root/'out'
p=out/'priority40_clusters.csv'
assert p.exists(), f'필수 결과 파일 누락: {p}'
g=pd.read_csv(p,dtype={'code':str})
assert len(g)==40, f'우선 대상 개수가 40이 아님: {len(g)}'
assert g.code.nunique()==40, '우선 대상 코드 중복'
assert g.cluster.nunique()==3, '군집이 정확히 3개가 아님'
print('우선 대상 40개·고유 코드·3군집: PASS')
c=out/'priority_carbon.csv'
if c.exists():
    a=pd.read_csv(c)
    for ratio,col in ((.1,'10%전환_t'),(.2,'20%전환_t'),(.3,'30%전환_t')):
        err=abs(a['연간배출_t']*ratio-a[col]).max()
        assert err<=1.1, f'탄소 시나리오 반올림 오차 한도 초과: {err}'
    print('기존 탄소 시나리오 내부 산술: PASS (실제 감축 검증 아님)')
q=out/'priority_carbon_weekweighted.csv'
if q.exists():
    w=pd.read_csv(q)
    assert set(w['가정'])=={'보수','기본','높음'}
    print('요일 가중 탄소 결과 존재: PASS')
else:
    print('요일 가중 탄소 결과: 미생성 (원자료 필요)')
r=out/'model_spatial_cv_corrected.csv'
print('거리 수정 후 모델 CV:', '결과 존재' if r.exists() else '미생성 (원자료 필요)')
