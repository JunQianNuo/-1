# 问题二 Python 代码说明

本目录是“问题二：多轨道面星座组网优化设计”的 Python 数值实现初版。

> 当前代码用于验证“地固系网格—时间覆盖判定”和递增规模搜索流程；`single_search` 仍是粗搜索，不是最终最优解证明。

## 文件结构

| 文件/目录 | 说明 |
|:--|:--|
| `q2_constellation.py` | 覆盖几何、Walker-Delta 星座参数化、指标计算、候选枚举与单重覆盖搜索接口 |
| `q2_fast_coverage.py` | 加速算法核心：邻近卫星对筛选、小圆交点、区域边界交点、弧段代表点、单时刻临界点、跨时间快速评价 |
| `run_q2_fast_search.py` | 快速筛选搜索入口：临界点—代表点法筛候选，Top-K 候选再做网格复核 |
| `test_q2_constellation.py` | 单元测试 |
| `test_q2_fast_coverage.py` | 加速算法几何基础的单元测试 |
| `test_q2_fast_search.py` | 快速搜索入口的单元测试 |
| `run_q2_smoke.py` | 最小 smoke run，用于确认模型链路可运行 |
| `run_q2_single_search.py` | 问题二单重覆盖正式粗搜索脚本 |
| `run_q2_scan.py` | 多阶段扫描：粗搜 → 中网格验证 → 细网格复核 → 二重覆盖 |
| `results/` | CSV/JSON 结果输出目录 |
| `results/scan/` | 多阶段扫描结果子目录 |
| `figures/` | 图表输出目录 |

## 运行测试

```bash
python test_q2_constellation.py
python -m unittest test_q2_fast_coverage.py
python -m unittest test_q2_fast_search.py
```

当前加速算法仍处于模块化实现阶段；正式大规模搜索前，应同时通过上述两组测试。

## 加速算法当前接口

`q2_fast_coverage.py` 目前提供以下接口：

| 接口 | 作用 |
|:--|:--|
| `neighbor_pairs_by_dot` | 分块筛选角距离不超过阈值的卫星对，避免保存三维覆盖张量 |
| `small_circle_intersections` | 计算两个等半径覆盖边界小圆的交点 |
| `small_circle_region_boundary_intersections` | 计算覆盖边界与目标经纬度矩形边界的交点 |
| `coverage_arc_representative_points` | 在覆盖圆弧两侧取代表点，降低只看交点时漏掉开区域空洞的风险 |
| `region_edge_representative_points` | 在目标区域边界相邻顶点之间取代表点 |
| `critical_points_at_time` | 生成一个时刻的临界点/代表点集合：区域角点、边界交点、覆盖圆交点、弧段代表点 |
| `coverage_counts_at_points` | 对临界点集合计算覆盖重数 |
| `evaluate_satellite_snapshots_fast` | 对给定卫星时间序列进行快速覆盖评价 |
| `evaluate_constellation_fast` | 接入 Walker 星座参数，生成卫星位置并快速评价 |

## 快速筛选搜索

推荐先使用 `run_q2_fast_search.py`，而不是直接放开旧枚举脚本：

```bash
python run_q2_fast_search.py
```

默认流程：

1. 使用 `evaluate_constellation_fast` 对候选星座做临界点—代表点快速评价；
2. 对同一总星数的因子对进行均衡抽样，优先测试接近平衡的多轨道面构型，避免 `M=1,N=S` 的顺序截断偏置；
3. 搜索过程中流式追加写出候选记录，避免长跑超时后没有任何结果；
4. 内存中只保留 Top-K 快速候选，避免旧脚本 `all_records` 累积；
5. 对 Top-K 中前若干候选调用 `q2_constellation.py` 的网格法复核；
6. 输出快速候选表、复核候选表和摘要 JSON。

输出：

| 输出 | 说明 |
|:--|:--|
| `results/q2_fast_search_top_fast_candidates.csv` | 快速法筛出的 Top-K 候选 |
| `results/q2_fast_search_verified_candidates.csv` | 经网格法复核的候选 |
| `results/q2_fast_search_summary.json` | 搜索设置、最优快速候选、最优复核候选 |
| `results/q2_fast_search_stream_fast_records.csv` | 搜索过程中逐条追加的快速评价记录，中断后仍可读取 |
| `results/q2_fast_search_stream_verified_records.csv` | 搜索过程中逐条追加的网格复核记录 |

小规模 smoke 示例：

```bash
python run_q2_fast_search.py --start-total 1 --stop-total 1 --inclinations 0 --phase-resolution 90 --max-candidates-per-total 4 --keep-top-fast 2 --verify-top 1 --duration-hours 0.001 --fast-time-step 10 --verify-time-step 10 --verify-grid-step 30 --output-dir results/fast_search_smoke
```

正式搜索时应逐步扩大：先增大 `--stop-total` 和 `--max-candidates-per-total`，再缩短 `--fast-time-step`，最后缩小 `--verify-grid-step` 和 `--verify-time-step`。最终可行性仍以复核表中的网格法指标为准。

如果已有较大规模可行上界，例如 $S=1600$ 已经通过单重覆盖复核，则推荐从上界向下搜索，而不是从明显不可行的小规模向上搜索：

```bash
python run_q2_fast_search.py --start-total 1200 --stop-total 1600 --search-order desc --inclinations 50,53,55,58,60 --phase-resolution 30 --max-candidates-per-total 200 --keep-top-fast 50 --verify-top 5 --duration-hours 6 --fast-time-step 900 --verify-time-step 900 --verify-grid-step 6 --output-dir results/fast_search_S1600_down_coarse
```

说明：

- `--search-order desc` 表示按 $1600,1599,\ldots,1200$ 的顺序搜索；
- `--stop-if-min-count-below 1` 为默认值，表示某候选只要任一时间片最小覆盖重数小于 1，就提前停止该候选的快速评价；
- 若需要完整统计每个候选全部时间片，可设置 `--stop-if-min-count-below -1` 关闭早停，但耗时会显著增加。

可用 `--min-planes`、`--max-planes`、`--min-sats-per-plane`、`--max-sats-per-plane` 约束构型范围。例如若不希望测试单轨道面，可设置 `--min-planes 10`。

## 最小链路验证

```bash
python run_q2_smoke.py
```

输出：

| 输出 | 说明 |
|:--|:--|
| `results/q2_smoke_candidates.csv` | 少量候选星座的覆盖指标 |
| `results/q2_smoke_summary.json` | smoke run 摘要 |
| `figures/Q2_smoke_min_count_map.png` | 网格点最小覆盖重数图 |
| `figures/Q2_smoke_time_series.png` | 覆盖重数时间序列 |

## 单重覆盖粗搜索

默认运行：

```bash
python run_q2_single_search.py
```

默认参数为：空间步长 $6^\circ$，时间步长 $900\,\mathrm{s}$，时长 $6\,\mathrm{h}$，总星数从 $S=40$ 开始，候选倾角为 $49^\circ,50^\circ,51^\circ,52^\circ,53^\circ$，相位步长 $30^\circ$，每个总星数最多评估 2000 个候选。

输出：

| 输出 | 说明 |
|:--|:--|
| `results/q2_single_search_candidates.csv` | 单重覆盖粗搜索候选表 |
| `results/q2_single_search_summary.json` | 粗搜索摘要、最优候选、首个可行候选 |
| `figures/Q2_single_search_best_min_count_map.png` | 当前最佳候选的网格点最小覆盖重数图 |
| `figures/Q2_single_search_best_time_series.png` | 当前最佳候选的覆盖重数时间序列 |

可扩大搜索：

```bash
python run_q2_single_search.py --lat-step 2 --time-step 180 --duration-hours 23.934 --phase-resolution 10 --max-candidates-per-total 0 --no-stop-on-feasible
```

扩大搜索时应分阶段进行：先降低空间步长，再降低时间步长，最后取消候选数上限；每一阶段都比较 `c_min`、`C1`、`max_gap_s` 是否稳定。

## 多阶段扫描

> 注意：`run_q2_scan.py` 和 `run_q2_sweep.py` 属于旧枚举法实验脚本。若直接放开候选上限并扩大到大规模 $S$，时间开销会很高；正式搜索应优先使用后续的 `q2_fast_coverage.py` 临界点/候选压缩流程，再用 `q2_constellation.py` 做网格复核。

```bash
python run_q2_scan.py
```

默认配置：
- Phase 1（粗搜）：网格 $3^\circ$、时间步长 $180\,\mathrm{s}$、S=40→150、倾角 $48.5^\circ\sim60^\circ$
- Phase 2（中网格验证）：网格 $1^\circ$、时间步长 $60\,\mathrm{s}$，对 Phase 1 可行 S 验证
- Phase 3（细网格复核）：网格 $0.5^\circ$、时间步长 $30\,\mathrm{s}$，最优候选复核
- Phase 4（二重覆盖）：从 single 可行 S 开始，搜索 $\mathcal C_2^{\text{strict}}\ge 0.95$

跳过二重覆盖搜索：

```bash
python run_q2_scan.py --skip-double
```

手动指定范围：

```bash
python run_q2_scan.py --single-start 40 --single-stop 120 --double-start 100 --double-stop 200
```

## 模型口径

核心模型来自：

- `08-问题二文献证据与建模依据.md`
- `09-问题二假设与指标推导.md`
- `10-问题二数值实现方案.md`
- `11-问题二初步回答与建模表述.md`

主要参数：

$$
R_e=6371\,\mathrm{km},\quad
h=550\,\mathrm{km},\quad
r_g=506\,\mathrm{km}.
$$

覆盖地心角：

$$
\theta=\frac{r_g}{R_e}.
$$

单重覆盖可行性在程序中按

$$
\min_{G_j,t_l} c(G_j,t_l)\ge 1
$$

判定。
