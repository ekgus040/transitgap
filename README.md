# transitgap
지하철이 먼 동네의 짧은 차량 이동: 생활이동 빅데이터와 AI로 찾은 서울 대중교통 공백과 이동 격차
「AI와 함께하는 교통문제 해결을 위한 데이터 분석 공모전」(재단법인 숲과나눔·한겨레, 2026) 분석 코드

## 요약
- 서울 내부 1–5km 차량 이동: 하루 87.2만(보수)–112.0만 건, 서울 내부 차량 이동의 31.3–40.2%
- LightGBM(출발-도착 행정동 쌍 22,882개), 출발 자치구 기준 공간 교차검증 R² 0.30 (거리만 0.02, 직결 노선 변수 추가 전 0.26)
- SHAP 주요 요인: 이동 거리, 출발-도착 동을 잇는 같은 지하철 노선(−)·직결 버스 노선 수(−), 도착·출발지 버스 노선·정류장 밀도(−), 경사(−), 지하철역 거리(+)
- 구 고정효과 가중회귀: 지하철역 1km 멀수록 차량 비중 +2.4%p(p=0.006), 버스 노선·정류장 밀도 2배면 −1.2%p(p=0.011), 같은 지하철 노선으로 이어진 동 쌍 −2.2%p(p<0.001). 고소득 4개 구 제외 시에도 유지
- 공급 기준 접근성 5분위별 1–5km 차량 비중: 18.8 → 20.6 → 21.3 → 23.1 → 24.8%
- 대중교통 공백 동 106곳 중 단거리 차량 의존 우선 대상 36곳: A 외곽 저밀형 9, B 버스 연계 부족형 15, C 취약 고령형 12
- 이동 격차: C유형 70세 이상 1인당 하루 이동 1.08회(서울 1.59회, −32%)
- 부수 효과(탄소): 버스 노선·정류장 밀도를 서울 중앙값까지 올리면 36곳 1–5km 차량 이동 3.7–4.5% 감소, 연 490–1,560 tCO2 배출 회피(연관 기반 시나리오)
- 추가 데이터 검증: 5–9월 동별 차량 비중 순위상관 0.99 이상, 버스 코드와 교통카드 승차 상관 0.72

## 폴더 구조
```
src/        분석 스크립트(번호 순서대로 실행)
data_raw/   원자료(직접 내려받기, slope_by_dong.txt만 포함)
work/       중간 산출물(실행 시 생성, 커밋 안 함)
out/        결과 표·그림
tests/      원자료 없이 도는 산식 단위 테스트
```

## 데이터 (data_raw/에 저장)
| 파일 | 출처 |
|---|---|
| d0826–d0829/ (seoul_trans_admdong3_final_202608DD.zip 압축 해제) | 서울 열린데이터광장 OA-22657 수도권 생활이동(출도착 행정동별 수단) |
| 서울시 버스정류소 위치정보.csv | 서울 열린데이터광장 OA-15067 |
| 서울시버스노선별정류소정보(20260902).xlsx | 서울 열린데이터광장 OA-1095 |
| 서울시 역사마스터 정보.csv | 서울 열린데이터광장 OA-21232 |
| 서울시 공공자전거 따릉이 대여소 마스터 정보.csv | 서울 열린데이터광장 OA-21235 |
| 201_DT_201004_O020029_*.csv (주민등록인구 각 세별/동별, 2026 2/4) | 서울시 통계 |
| 국민기초생활보장+수급자(2020+이후)_*.csv (2024) | 서울 열린데이터광장 DT201004O1100342020 |
| HangJeongDong_ver20250401.geojson | github.com/vuski/admdongkor (통계청 SGIS, CC BY 4.0) |
| extra/age_2026MM.csv (src/00_extra_agg_age.py로 집계) | 서울 열린데이터광장 OA-22655 수도권 생활이동(도착 행정동 성·연령별 수단), 2026년 5–9월 |
| extra/bus_stops.csv (src/00_extra_agg_bus.py로 집계) | 서울 열린데이터광장 OA-12912 버스노선별 정류장별 승하차 인원, 2026년 5–9월 |
| slope_by_dong.txt (포함) | NASA SRTM 30m via OpenTopoData, 행정동별 평균 경사(%) |

## 실행 (저장소 루트에서, 번호 순서대로)
```
pip install -r requirements.txt
python src/00_extra_agg_age.py ...; python src/00_extra_agg_bus.py ...   # 추가 데이터 집계(인자는 각 파일 상단 참고)
python src/01_load_mobility.py          # 생활이동 4일치 → DuckDB
python src/02_verify_headline.py        # 핵심 수치 원자료 대조
python src/03_dong_aggregate.py
python src/04_ddareungi_overlay.py; python src/04b_slope_priority.py
python src/05_equity_data.py; python src/06_dong_features.py
python src/07_od_table.py; python src/08_model_lgb_shap.py
python src/10_transit_gap.py; python src/12_robustness.py
python src/15_bus_routes.py             # 동별 버스 노선·정류장 밀도
python src/16_gap_redefine.py           # 공백 동 106곳 → 우선 대상 36곳
python src/17_income_control.py; python src/18_sensitivity_rich_gu.py   # 구 고정효과, 고소득 구 제외
python src/19_model_v2.py               # 기준 모델(직결 노선 변수 전)
python src/20_priority_typology_carbon.py   # K-평균 3유형, 탄소 시나리오
python src/23_case_study.py             # 사례(양재1동·도봉1동·진관동)
python src/25_review_checks.py; python src/26_validation_audit.py
python src/27_mobility_gap.py; python src/28_counterfactual_access.py; python src/29_station_coverage_check.py
python src/33_figures_v4.py             # 보고서 그림 1, 그림 3·4
python src/34_extra_age_season.py       # 계절성·고령자 이동
python src/35_extra_bus_validation.py   # 교통카드로 버스 수단 코드 검증
python src/36_selection_robust_v3.py    # 단일 지표 재선정 시 겹침
python src/37_export_v3.py              # out/dong_access_gap.csv, out/priority_clusters.csv
python src/38_direct_link_model.py      # 최종 모델(직결 노선 변수), 보고서 그림 2
python -m unittest discover -s tests
```
- 수단 코드: 8=차량, 6=지하철, 7=도보, 4·5=버스, 9=기타 (거리·속도 분포와 서울시 수단분담률 대조로 판정)
- 500m 미만 차량 행은 통신 기반 위치 추정 오차와 구분이 어려워 제외, 시속 5km 미만 차량 행은 보수 추정에서 제외
- LightGBM은 deterministic 설정으로 재현 가능

## 주요 결과 파일
- out/dong_access_gap.csv: 동별 접근성 지표, 공백 동·우선 대상 여부
- out/priority_clusters.csv: 우선 대상 36곳과 유형
- out/model_v3_direct_link.csv, out/shap_v3.csv: 최종 모델 검증·직결 노선 효과·SHAP
- out/income_control_fe.csv: 구 고정효과 회귀 계수
- out/elderly_mobility_by_type.csv, out/mobility_gap_*.csv: 이동 격차
- out/priority_carbon*.csv, out/counterfactual_access_carbon.csv: 탄소 시나리오
- out/season_*.csv, out/bus_card_validation.csv, out/selection_robust_v3.csv, out/robustness_table.csv: 검증·강건성
- out/case_study.csv: 사례 동 3곳
- out/fig/: 보고서 그림(fig1_compact, fig2_shap_v3, fig34_combined)

## 한계
통신 기반 수단 추정(택시·오분류 혼입 가능), 직선거리, 8월 말 4일 표본(일요일 미포함), 구 안의 소득 차이·차량 보유 미통제, 횡단면 상관관계(인과 아님). 출발 자치구 기준 교차검증은 처음 보는 출발 구에 대한 일반화를 본 것으로, 도착 구는 학습 데이터에 나올 수 있음.
