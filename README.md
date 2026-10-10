# transitgap
지하철이 먼 동네의 짧은 차량 이동: 생활이동 빅데이터와 AI로 찾은 서울 대중교통 공백과 탄소 부담
「AI와 함께하는 교통문제 해결을 위한 데이터 분석 공모전」(재단법인 숲과나눔·한겨레, 2026) 분석 코드

## 요약
- 서울 내부 1–5km 차량 이동: 하루 872,021건(보수)–1,120,202건(기본), 차량 이동의 31.3–40.2%
- LightGBM(출발-도착 행정동 쌍 22,882개) 출발 자치구 기준 공간 교차검증 R² 0.256 (거리만 쓴 기준 0.022, 버스 노선 변수 추가 전 0.234)
- SHAP 주요 요인: 이동 거리, 도착·출발지 버스 노선·정류장 밀도(−), 경사, 지하철역 거리(+)
- 공급 기준 접근성 5분위별 1–5km 차량 비중: 18.8 → 20.6 → 21.3 → 23.1 → 24.8%
- 구 고정효과 가중회귀: 지하철역 1km 멀수록 차량 비중 +2.4%p(p=0.006), 버스 노선·정류장 밀도 2배면 −1.2%p(p=0.011). 고소득 4개 구 제외 시에도 유지
- 대중교통 공백 동 106곳(지하철 접근성 3지표 + 버스 노선·정류장 밀도) 중 단거리 차량 의존 우선 대상 36곳: A 외곽 저밀형 9, B 버스 연계 부족형 15, C 취약 고령형 12
- 사례: 양재1동은 단거리 차량 이동의 47%가 역 가까운 5개 동으로 향함(출발지 역거리 1.64km → 목적지 0.95km). 우선 대상으로 꼽힌 진관동은 2021년 DRT '셔클' 운행지
- 우선 대상 36곳 1–5km 차량 이동 하루 12.4만 건(서울 내부 1–5km 차량 이동의 11.1%), 연간 배출 1.3만–2.8만–3.5만 tCO2. 서울 전체 10% 전환 잠재량 1.1만–3.1만 t
- 모델 시나리오: 버스 노선·정류장 밀도를 서울 중앙값까지 올리면 차량 비중 −1.1~1.4%p, 하루 0.46만–0.55만 건(3.7–4.5%), 연 490–1,560 t 배출 회피. 역 접근성까지 개선하는 상한 8.3–9.5%, 1,100–3,350 t
- 추가 데이터 검증: 5~9월 월간 동별 차량 비중 순위상관 0.989–0.997, 우선 대상 도착 기준 차량 비중 41.0–42.2%(나머지 27.8–28.8%), C유형 70세 이상 1인당 이동 1.08회(서울 1.59회, −32%), 정류소별 교통카드 승하차와 생활이동 버스 이동 로그 상관 0.72–0.76

## 폴더 구조
```
src/        분석 스크립트(번호 순서대로 실행)
data_raw/   원자료(직접 내려받기, slope_by_dong.txt만 포함)
work/       중간 산출물(실행 시 생성, 커밋 안 함)
out/        결과 표·그림
```

## 데이터 (data_raw/에 저장)
| 파일 | 출처 |
|---|---|
| d0826–d0829/ (seoul_trans_admdong3_final_202608DD.zip 압축 해제) | 서울 열린데이터광장 OA-22657 수도권 생활이동(출도착 행정동별 수단 데이터) |
| 서울시 버스정류소 위치정보.csv | 서울 열린데이터광장 OA-15067 |
| 서울시버스노선별정류소정보(20260902).xlsx | 서울 열린데이터광장 OA-1095 |
| 서울시 역사마스터 정보.csv | 서울 열린데이터광장 OA-21232 |
| 서울시 공공자전거 따릉이 대여소 마스터 정보.csv | 서울 열린데이터광장 OA-21235 |
| 201_DT_201004_O020029_*.csv (주민등록인구 각 세별/동별, 2026 2/4) | 서울시 통계 |
| 국민기초생활보장+수급자(2020+이후)_*.csv (2024) | 서울 열린데이터광장 DT201004O1100342020 |
| HangJeongDong_ver20250401.geojson | github.com/vuski/admdongkor (통계청 SGIS, CC BY 4.0) |
| extra/age_2026MM.csv (src/00_extra_agg_age.py로 집계) | 서울 열린데이터광장 수도권 생활이동(도착 행정동 성·연령별 수단), 2026년 5–9월 |
| extra/bus_stops.csv (src/00_extra_agg_bus.py로 집계) | 서울 열린데이터광장 버스노선별 정류장별 승하차 인원(교통카드), 2026년 5–9월 |
| slope_by_dong.txt (포함) | NASA SRTM 30m via OpenTopoData, 행정동별 평균 경사(%) |

파일명이 다르면 각 스크립트의 경로를 맞춰 주세요.

## 실행
```
pip install -r requirements.txt
python src/01_load_mobility.py      # 저장소 루트에서 실행
python src/02_verify_headline.py
... 12_robustness.py까지 번호 순서대로 (04b 포함)
python src/15_bus_routes.py         # 동별 버스 노선·정류장 밀도
python src/16_gap_redefine.py       # 공백 지역 2단계 정의 v3(106곳 → 우선 대상 36곳). 이전 정의는 16_gap_redefine_v2.py
python src/17_income_control.py     # 구 고정효과 가중회귀(소득 직접 통제 아님)
python src/18_sensitivity_rich_gu.py
python src/19_model_v2.py           # LightGBM v2 + SHAP
python src/20_priority_typology_carbon.py
python src/21_figures_v2.py         # 보고서 그림 1–4
python src/22_robustness_v2.py
python src/23_case_study.py         # 사례 분석(양재1동·도봉1동·진관동)
python src/24_figures_compact.py    # 보고서용 압축 그림(그림 2)
python src/25_review_checks.py; python src/26_validation_audit.py
python src/27_mobility_gap.py       # 이동 격차(1인당 이동, 대중교통 소요시간)
python src/28_counterfactual_access.py  # 접근성 개선 시나리오(구 고정효과 계수)
python src/29_station_coverage_check.py # 역 500m 면적 비율로 바꾼 회귀
python src/33_figures_v4.py         # 보고서 그림 1, 그림 3·4 (30번 대체)
python src/34_extra_age_season.py   # 추가 데이터 ①: 계절성·고령자 이동
python src/35_extra_bus_validation.py   # 추가 데이터 ②: 교통카드로 버스 수단 코드 검증
python src/36_selection_robust_v3.py    # 단일 접근성 지표로 재선정 시 겹침
python src/37_export_v3.py          # out/dong_access_gap.csv, out/priority_clusters.csv
```
- 10·11·13번은 1차 분석(공백 34곳 정의)으로, 최종 결과는 15번 이후가 대체합니다. 30·31·32번은 이전 선정 기준(v2) 기록용입니다.
- 수단 코드: 8=차량, 6=지하철, 7=도보, 4·5=버스, 9=기타 (서울시 발표 수단 비율과 대조해 판정)
- 500m 미만 차량 행은 신호 잡음으로 제외, 시속 5km 미만 차량 행은 보수 추정에서 제외
- LightGBM은 deterministic 설정으로 결과 재현 가능

## 주요 결과 파일
- out/dong_access_gap.csv: 동별 접근성 지표, 공백 동·우선 대상 여부
- out/priority_clusters.csv: 우선 대상 36곳과 유형
- out/income_control_fe.csv: 구 고정효과 회귀 계수
- out/priority_carbon.csv: 우선 대상 36곳 탄소 시나리오
- out/counterfactual_access_carbon.csv: 접근성 개선 시나리오
- out/elderly_mobility_by_type.csv, out/season_*.csv, out/bus_card_validation.csv: 추가 데이터 검증
- out/selection_robust_v3.csv: 선정 강건성
- out/case_study.csv: 사례 동 3곳의 목적지·시간대·탄소
- out/fig/: 보고서 그림

## 한계
통신 신호 기반 수단 추정(택시·오분류 혼입 가능), 직선거리, 8월 말 4일 표본, 구 안의 소득 차이·차량 보유 미통제, 횡단면 상관관계(인과 아님)

## 검증 및 수정 안내 (2026-10-08)

- `src/07_od_table.py`에서 OD 평균 이동거리를 단순 행 평균에서 `cnt` 가중 평균으로 변경했습니다.
- `src/20_priority_typology_carbon.py`는 기존 단순 4일 평균표(`out/priority_carbon.csv`)에 더해, 평일(5/7)·주말(2/7) 가중 결과(`out/priority_carbon_weekweighted.csv`)와 일별 집계(`out/priority_carbon_daily_inputs.csv`)를 출력합니다. 이 값들은 **차량 배출 회피 잠재량**이지, 대체 교통수단 배출을 차감한 순감축이 아닙니다.
- `src/17_income_control.py`의 구 고정효과는 소득을 직접 통제하지 않습니다. 구 내부의 소득 차이 및 차량 소유 여부는 여전히 교란 요인일 수 있습니다.
- 출발 자치구 그룹별 CV는 미관측 출발 자치구에 대한 일반화를 검증합니다. 도착 자치구가 학습 데이터에도 나타날 수 있으며, 이는 출발·도착 양쪽이 처음 등장하는 지역에 대한 외삽 검증이 아닙니다.
- 2026-10-08 원자료로 재실행해 `out/` 결과를 수정 후 버전으로 갱신했습니다(변화 1% 미만).
- 전체 재현 시 **01~24번을 의존 순서대로 다시 실행**하고 기존 보고서와 변경량을 대조해야 합니다. 원본 데이터 없이는 재현성 검증을 완료할 수 없습니다.

## 원자료 재실행 결과 (2026-10-08)
위 수정을 원자료로 재실행한 결과 모든 핵심 수치의 변화가 1% 미만이었다(공간CV R² 0.256, 거리만 0.022, 구 고정효과 계수 동일, 요일 가중 배출 +0.07%). 비교표는 `out/rerun_comparison_1008.csv`, 상세는 `REPORT_CORRECTIONS.md` 참조. REPAIR_NOTES.md의 "보고서 수정 전 보류할 수치"는 재실행으로 해소되었다.

## 선정 기준 변경 (2026-10-10, v3)
- 지하철 접근성을 대표점 거리 하나에서 3지표 평균 백분위로 바꿨습니다: 행정동 대표점–최근접역 거리, 버스정류장에서 최근접역까지 평균 거리(정류장 가중), 역 500m 반경이 동 면적에서 차지하는 비율(역수).
- 대표점 하나로는 역이 동 경계에 붙은 동(문정2동·청담동·반포본동 등)이 우선 대상에 잡히는 문제를 줄이기 위함입니다.
- 결과: 공백 동 107→106곳, 우선 대상 40→36곳. 단일 지표로 각각 뽑아도 37–40곳 중 33곳이 겹칩니다(`out/selection_robust_v3.csv`).
- 20번은 KMeans 군집 번호를 프로필(역 거리 최대=A, 고령 비율 최대=C)로 고정해 실행마다 유형 이름이 바뀌지 않게 했습니다.
