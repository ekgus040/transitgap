# transitgap
지하철이 먼 동네의 짧은 차량 이동: 생활이동 빅데이터와 AI로 찾은 서울 대중교통 공백과 탄소 부담
「AI와 함께하는 교통문제 해결을 위한 데이터 분석 공모전」(재단법인 숲과나눔·한겨레, 2026) 분석 코드

## 요약
- 서울 내부 1–5km 차량 이동: 하루 872,021건(보수)–1,120,202건(기본), 차량 이동의 31.3–40.2%
- LightGBM(출발-도착 행정동 쌍 22,882개) 공간 교차검증 R² 0.260 (거리만 쓴 기준 0.032, 버스 노선 변수 추가 전 0.235)
- SHAP 주요 요인: 이동 거리, 도착·출발지 버스 노선·정류장 밀도(−), 경사, 지하철역 거리(+)
- 공급 기준 접근성 5분위별 1–5km 차량 비중: 19.8 → 20.0 → 21.6 → 22.4 → 24.7%
- 구 고정효과 가중회귀: 지하철역 1km 멀수록 차량 비중 +2.4%p(p=0.006), 버스 노선·정류장 밀도 2배면 −1.2%p(p=0.011). 고소득 4개 구 제외 시에도 유지
- 대중교통 공백 동 107곳(공급 기준) 중 단거리 차량 의존 우선 대상 40곳: A 외곽 저밀형 8, B 버스 연계 부족형 18, C 취약 고령형 14
- 우선 대상 40곳 1–5km 차량 이동 연간 배출 1.6만–4.2만 tCO2, 10% 전환 시 1,600–4,200 t 감축. 서울 전체 10% 전환 잠재량 1.1만–3.1만 t

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
| slope_by_dong.txt (포함) | NASA SRTM 30m via OpenTopoData, 행정동별 평균 경사(%) |

파일명이 다르면 각 스크립트의 경로를 맞춰 주세요.

## 실행
```
pip install -r requirements.txt
python src/01_load_mobility.py      # 저장소 루트에서 실행
python src/02_verify_headline.py
... 12_robustness.py까지 번호 순서대로 (04b 포함)
python src/15_bus_routes.py         # 동별 버스 노선·정류장 밀도
python src/16_gap_redefine.py       # 공백 지역 2단계 정의(107곳 → 우선 대상 40곳)
python src/17_income_control.py     # 구 고정효과 가중회귀(소득 통제)
python src/18_sensitivity_rich_gu.py
python src/19_model_v2.py           # LightGBM v2 + SHAP
python src/20_priority_typology_carbon.py
python src/21_figures_v2.py         # 보고서 그림 1–4
python src/22_robustness_v2.py
```
- 10·11·13번은 1차 분석(공백 34곳 정의)으로, 최종 결과는 15–22번이 대체합니다.
- 수단 코드: 8=차량, 6=지하철, 7=도보, 4·5=버스, 9=기타 (서울시 발표 수단 비율과 대조해 판정)
- 500m 미만 차량 행은 신호 잡음으로 제외, 시속 5km 미만 차량 행은 보수 추정에서 제외
- LightGBM은 deterministic 설정으로 결과 재현 가능

## 주요 결과 파일
- out/dong_access_gap.csv: 동별 접근성 지표, 공백 동·우선 대상 여부
- out/priority40_clusters.csv: 우선 대상 40곳과 유형
- out/income_control_fe.csv: 구 고정효과 회귀 계수
- out/priority_carbon.csv: 우선 대상 40곳 탄소 시나리오
- out/fig/: 보고서 그림

## 한계
통신 신호 기반 수단 추정(택시·오분류 혼입 가능), 직선거리, 8월 말 4일 표본, 구 안의 소득 차이·차량 보유 미통제, 횡단면 상관관계(인과 아님)
