# LightGBM v3(최종 모델): 출발-도착 동을 직접 잇는 노선 변수 추가 — 공간CV, 구 고정효과 확인, SHAP, 보고서 그림 2
#  - direct_bus : 두 동(경계 안)에 모두 정류장이 있는 버스 노선 수
#  - direct_rail: 두 동(경계 300m 이내)에 모두 역이 있는 같은 지하철 노선 수
# 출력: out/model_v3_direct_link.csv(공간CV R², 직결 노선별 차량 비중, 구 고정효과 계수), out/shap_v3.csv, out/fig/fig2_shap_v3.png
# 실행: 저장소 루트에서 python src/38_direct_link_model.py (data_raw/d0826~d0829 압축 해제 필요)
import duckdb, pandas as pd, numpy as np, geopandas as gpd, lightgbm as lgb, shap, statsmodels.formula.api as smf, matplotlib
from sklearn.model_selection import GroupKFold, KFold
from sklearn.metrics import r2_score
matplotlib.use('Agg'); import koreanize_matplotlib, matplotlib.pyplot as plt

# 1) 동 쌍별 1~5km 이동(4일 평균, 하루 20건 이상)
con = duckdb.connect()
od = con.execute("""select o_admdong_cd o, d_admdong_cd d,
  sum(try_cast(move_dist as double)*try_cast(cnt as double))/sum(try_cast(cnt as double)) dist,
  sum(try_cast(cnt as double))/4 tot, sum(case when move_trans='8' then try_cast(cnt as double) else 0 end)/4 car
  from read_csv('data_raw/d08*/*.csv', header=true, all_varchar=true, ignore_errors=true)
  where in_forn_div_nm='내국인' and left(o_admdong_cd,2)='11' and left(d_admdong_cd,2)='11' and o_admdong_cd<>d_admdong_cd
  and try_cast(move_dist as double) between 1000 and 4999 and move_trans in ('4','5','6','7','8','9')
  group by 1,2 having sum(try_cast(cnt as double))/4>=20""").fetchdf()

# 2) 직결 노선 변수
g = gpd.read_file('data_raw/HangJeongDong_ver20250401.geojson'); g = g[g.sido == '11'].copy()
g['code'] = g.adm_cd2.str[:8]; g = g[['code', 'geometry']]
B = pd.read_excel('data_raw/서울시버스노선별정류소정보(20260902).xlsx').dropna(subset=['X좌표', 'Y좌표'])
bs = gpd.sjoin(gpd.GeoDataFrame(B, geometry=gpd.points_from_xy(B['X좌표'], B['Y좌표']), crs=4326), g, predicate='within')[['ROUTE_ID', 'code']].drop_duplicates()
S = pd.read_csv('data_raw/서울시 역사마스터 정보.csv', encoding='cp949')
st = gpd.GeoDataFrame(S, geometry=gpd.points_from_xy(S['경도'], S['위도']), crs=4326).to_crs(5179)
gb = g.to_crs(5179); gb['geometry'] = gb.buffer(300)
sl = gpd.sjoin(st, gb, predicate='within')[['호선', 'code']].drop_duplicates()
def links(T, key, name):
    p = T.merge(T, on=key, suffixes=('_o', '_d')); p = p[p.code_o != p.code_d]
    return p.groupby(['code_o', 'code_d'])[key].nunique().rename(name).reset_index()
for L in (links(bs, 'ROUTE_ID', 'direct_bus'), links(sl, '호선', 'direct_rail')):
    od = od.merge(L, left_on=['o', 'd'], right_on=['code_o', 'code_d'], how='left').drop(columns=['code_o', 'code_d'])
od[['direct_bus', 'direct_rail']] = od[['direct_bus', 'direct_rail']].fillna(0)

# 3) 동 특성 결합
F = pd.read_csv('out/dong_features_plus.csv', dtype={'code': str})
F = F.merge(pd.read_csv('out/dong_access_gap.csv', dtype={'code': str})[['code', 'route_stop_density']], on='code')
feats = ['bike_density', 'bus_density', 'route_stop_density', 'sub_dist_km', 'slope_pct', 'pop_density', 'elder_pct', 'recip_pct']
X = od.merge(F[['code', 'gu'] + feats].add_prefix('o_'), left_on='o', right_on='o_code') \
      .merge(F[['code', 'gu'] + feats].add_prefix('d_'), left_on='d', right_on='d_code')
X['y'] = X.car / X.tot
base = ['dist'] + [f'{s}_{f}' for s in ('o', 'd') for f in feats]
cols = ['dist', 'direct_bus', 'direct_rail'] + base[1:]
X = X.dropna(subset=cols + ['y']).reset_index(drop=True)
assert X.o_gu.nunique() >= 5 and (X.tot > 0).all()

# 4) 공간 교차검증(출발 자치구 5-fold, 이동량 가중 R²)
P = dict(objective='regression', learning_rate=0.05, num_leaves=31, min_data_in_leaf=50, feature_fraction=0.8, bagging_fraction=0.8,
         bagging_freq=1, verbose=-1, seed=7, deterministic=True, num_threads=1, force_row_wise=True)
def cv(c, split):
    p = np.zeros(len(X))
    for tr, te in split:
        p[te] = lgb.train(P, lgb.Dataset(X.iloc[tr][c], X.iloc[tr].y, weight=X.iloc[tr].tot), 600).predict(X.iloc[te][c])
    return r2_score(X.y, p, sample_weight=X.tot)
sp = lambda: GroupKFold(5).split(X, groups=X.o_gu)
res = {'n_pairs': len(X), 'spatialCV_R2_distance_only': cv(['dist'], sp()), 'spatialCV_R2_before_direct': cv(base, sp()),
       'spatialCV_R2_v3': cv(cols, sp()), 'randomCV_R2_v3': cv(cols, KFold(5, shuffle=True, random_state=1).split(X))}
for lab, grp in X.groupby(pd.cut(X.direct_bus, [-1, 0, 2, 5, 1e9], labels=['0', '1-2', '3-5', '6+']), observed=True):
    res[f'car_share_direct_bus_{lab}'] = np.average(grp.y, weights=grp.tot)
for lab, grp in X.groupby(X.direct_rail > 0):
    res[f'car_share_direct_rail_{lab}'] = np.average(grp.y, weights=grp.tot)

# 5) 구 고정효과 가중회귀(출발·도착 구 FE, 출발 구 군집 표준오차)
X['yp'] = 100 * X.y; X['l_db'] = np.log1p(X.direct_bus); X['rail'] = (X.direct_rail > 0).astype(int)
for s in ('o', 'd'): X[f'{s}_l_rsd'] = np.log(X[f'{s}_route_stop_density'].clip(lower=1))
f = ('yp ~ dist + l_db + rail + o_sub_dist_km + d_sub_dist_km + o_l_rsd + d_l_rsd + o_slope_pct + d_slope_pct'
     ' + o_recip_pct + d_recip_pct + o_elder_pct + d_elder_pct + C(o_gu) + C(d_gu)')
r = smf.wls(f, data=X, weights=X.tot).fit(cov_type='cluster', cov_kwds={'groups': X.o_gu})
for v in ('rail', 'l_db', 'o_l_rsd', 'd_l_rsd', 'o_sub_dist_km', 'd_sub_dist_km'):
    res[f'FE_coef_{v}'] = r.params[v]; res[f'FE_p_{v}'] = r.pvalues[v]
pd.Series(res).to_csv('out/model_v3_direct_link.csv', header=['value'], encoding='utf-8-sig')
print(pd.Series(res).round(4).to_string())

# 6) 최종 모델 SHAP + 시드 안정성 + 그림 2
m = lgb.train(P, lgb.Dataset(X[cols], X.y, weight=X.tot), 600); m.save_model('work/lgb_od_v3.txt') if __import__('os').path.isdir('work') else None
Sm = X[cols].sample(5000, random_state=1); sv = shap.TreeExplainer(m).shap_values(Sm)
imp = pd.Series(np.abs(sv).mean(0) * 100, index=cols).sort_values(ascending=False)
sg = {c: np.corrcoef(Sm[c], sv[:, cols.index(c)])[0, 1] for c in cols}
pd.DataFrame({'mean_abs_shap_pp': imp, 'direction': [sg[c] for c in imp.index]}).to_csv('out/shap_v3.csv', encoding='utf-8-sig')
for sd in (1, 2, 3):
    s2 = shap.TreeExplainer(lgb.train(dict(P, seed=sd), lgb.Dataset(X[cols], X.y, weight=X.tot), 600)).shap_values(X[cols].sample(4000, random_state=sd))
    print('seed', sd, 'top5', list(pd.Series(np.abs(s2).mean(0), index=cols).sort_values(ascending=False).index[:5]))
SURF, T2, GRID, S1, S2 = '#fcfcfb', '#52514e', '#e4e3df', '#2a78d6', '#e8743b'
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'axes.edgecolor': GRID, 'axes.labelcolor': T2, 'xtick.color': T2, 'ytick.color': T2, 'font.size': 11})
nm = {'route_stop_density': '버스 노선·정류장 밀도', 'bus_density': '버스정류장 밀도', 'slope_pct': '경사', 'sub_dist_km': '지하철역 거리',
      'pop_density': '인구밀도', 'elder_pct': '고령인구 비율', 'bike_density': '따릉이 밀도', 'recip_pct': '수급자 비율'}
lab = lambda c: {'dist': '이동 거리', 'direct_bus': '출발-도착 직결 버스 노선 수', 'direct_rail': '출발-도착 같은 지하철 노선'}.get(c) \
    or ('출발지 ' if c[0] == 'o' else '도착지 ') + nm[c[2:]]
top = imp.head(8)[::-1]
fig, ax = plt.subplots(figsize=(8, 3.1))
ax.barh([lab(c) for c in top.index], top.values, color=[S2 if c.startswith('direct') else S1 for c in top.index], height=0.62)
for i, c in enumerate(top.index):
    ax.text(top.values[i] + 0.03, i, f"{top.values[i]:.2f} ({'값↑ 차량↑' if sg[c] > 0 else '값↑ 차량↓'})", va='center', fontsize=10, color=T2)
ax.set_xlabel('평균 |SHAP| (차량 이용 비율, %p)    주황: 출발-도착 동을 직접 잇는 노선'); ax.set_xlim(0, top.max() * 1.5)
ax.grid(axis='x', color=GRID, lw=0.6); ax.set_axisbelow(True)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('out/fig/fig2_shap_v3.png', dpi=220); plt.close()
