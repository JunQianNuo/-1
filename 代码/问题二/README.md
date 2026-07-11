# 问题二 Python 代码说明

本目录是“问题二：多轨道面星座组网优化设计”的 Python 数值实现。

> **状态（已完成）**：地固系网格—时间覆盖判定 + 整恒星日搜索 + 假设驱动松弛（R02/R03/R05/R06/R07）+ **$N$ 放开的多保真搜索**（两问分别求最小星数）。
> **最终答案（松弛口径，$1^\circ/150\mathrm s$ 复核）**：
> - 第2问 单重 $\mathcal C_1\ge0.999$：$S_1\approx1302$（$M{=}62,N{=}21,F{=}30,i{=}51.5^\circ$）；
> - 第3问 单+二重 $\mathcal C_1\ge0.999$ 且 $\mathcal C_2\ge0.95$：$S_2\approx1480$（$M{=}37,N{=}40,F{=}31,i{=}50^\circ$）；$\Delta S{=}160$。
> - **$N$ 完全放开**（两问最优 $N$ 不同：单重 24、二重 40）；曾用的"几何锁定 $N{=}40$、$S{=}1512$"**已废弃**（单面覆盖带条件不适用于多面）。详见 `results/q2_free_search/summary.json`、[[问题分析/星链系统-文献驱动版/10-问题二数值实现方案]] §7、[[问题分析/星链系统-文献驱动版/18-问题二算法条件松弛与假设驱动加速方案]] §15.10。

## 文件结构

| 文件/目录 | 说明 |
|:--|:--|
| `q2_constellation.py` | 覆盖几何、Walker-Delta 参数化、指标、候选枚举、单/双搜索；`phase_grid(fix_raan0)`（R02 固定 Ω₀）、`symmetry_reduced_window_s` / `window_convergence_check`（R01 弃用后的窗长验证工具）|
| `q2_fast_coverage.py` | 加速评价核心：邻近卫星对、小圆交点、区域边界交点、临界点；`include_representatives=False` 即 R07 Deng 命题3 充分集 |
| `q2_coverage_margin.py` | 连续 $q$ 重覆盖余量（第 $q$ 近卫星点积余量），供证书器复用 |
| `q2_lipschitz_certificate.py` | **R05**：角度空间 Lipschitz 余量连续覆盖证书（单遍替代自适应盒），$L_x{=}1,L_t{=}n_0{+}\omega_e$ |
| `q2_relaxed_criteria.py` | **R03/R04/R06**：近全覆盖、护带域、二重空间容差判定层（overlay，不改覆盖模型）|
| `run_q2_fast_search.py` | 快速筛选搜索入口（`--fix-raan0`、`--critical-min` 开关）|
| `run_q2_fullday_scan.py` | 整恒星日 grid 扫描器（best-per-S，R02 固定 Ω₀），早期定位入口 |
| `run_q2_free_search.py` | **权威搜索入口**：$N$ 完全放开（全因子对）+ F 采样邻域细化 + 多保真（4°/900s 粗筛→2°/300s→1°/150s），求 S₁(单重)/S₂(单+二重) |
| `q2_bilp_setcover.py` | **替代算法探索**：BILP 0-1 集合覆盖最少卫星（LP 松弛下界≈1010 + 贪心 + HiGHS milp + CGT）。结论：本题规模精确不可解、贪心不敌 Walker、CGT 宽区域无解 → 不实用，唯一价值是 LP 下界 |
| `test_q2_constellation.py` / `test_q2_fast_coverage.py` / `test_q2_fast_search.py` | 基础与快速搜索单元测试 |
| `test_q2_relaxation.py` | R02 时移等价、R07 子集、R01 证伪等测试 |
| `test_q2_lipschitz_certificate.py` | R05 证书：$L_x,L_t$ 真上界抽验、三分类逻辑 |
| `test_q2_relaxed_criteria.py` | R03/R04/R06 判定层测试 |
| `test_q2_bilp_setcover.py` | BILP 集合覆盖 + CGT 测试 |
| `run_q2_smoke.py` / `run_q2_single_search.py` / `run_q2_scan.py` | 早期 smoke / 粗搜 / 多阶段扫描（保留）|
| `results/q2_free_search/` | **权威结果**：coarse/fine records + frontier + summary（S₁=1320/S₂=1480，可绘图）|
| `results/q2_final_answer.json` | 早期答案记录（1512，**已被 q2_free_search 更正**）|
| `results/q2_fullday_scan_coarse/`、`q2_fullday_scan_refine/` | 整日 S 扫描原始数据（前沿曲线）|
| `results/` / `figures/` | 结果与图表输出目录 |

## 运行测试

```bash
python test_q2_constellation.py
python -m unittest test_q2_fast_coverage test_q2_fast_search \
  test_q2_relaxation test_q2_lipschitz_certificate test_q2_relaxed_criteria test_q2_bilp_setcover
```

全部测试应通过（基础 11 + 加速/松弛/BILP 53）。

## 最终结果与复现

**最小接受星数（$N$ 放开、松弛口径，整恒星日 $1^\circ/150\mathrm s$ 复核）**：

| 小问 | 约束 | $S$ | 构型 | 指标 |
|:--|:--|--:|:--|:--|
| 第2问 单重 | $\mathcal C_1\ge0.999$ | **1302** | $M{=}62,N{=}21,F{=}30,i{=}51.5^\circ$ | $\mathcal C_1{=}0.99929$（1°/150s 复核）|
| 第3问 单+二重 | $\mathcal C_1\ge0.999$ 且 $\mathcal C_2\ge0.95$ | **1480** | $M{=}37,N{=}40,F{=}31,i{=}50^\circ$ | $\mathcal C_1{=}0.99979,\mathcal C_2{=}0.9694$（1°/150s 复核）|

$\Delta S{=}178$，$\Delta C{=}14$ 亿元。要点：

- **严格逐点 $c_{\min}\ge1$ 与严格整区二重在 $S\le1600$ 均不可行**（残差为西南边界亚时间步瞬时 / 整区二重恒为 0），故交付口径为近全覆盖 $\mathcal C_1\ge0.999$（R03）与面积—时间二重 $\mathcal C_2\ge0.95$；
- **$N$ 完全放开**（全因子对），两问最优 $N$ 不同（单重 24、二重 40）；~~"几何锁定 $N=40$、$S=1512$"~~ 已废弃——覆盖带 $N\ge\pi/\theta$ 是单面条件、多面不成立。唯一保留降维 $\Omega_0=0$（R02 证明）。

复现：

```bash
python run_q2_free_search.py --s-min 1300 --s-max 1560 --s-step-coarse 20 \
  --incl-coarse 49,50,51 --u0-coarse 2 --f-samples 6 --keep-top 12 \
  --out results/q2_free_search
# 结果：results/q2_free_search/summary.json（S1/S2/构型）、frontier.csv、coarse/fine_records.csv（可绘图）
```

> 结论为该参数化（$N$ 不受限）与松弛口径下的**最小接受星数（上界）**，非严格全局下界；$S$ 按每 20 一档扫，整数细化可能再降。

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

单重覆盖可行性：严格判据 $\min_{G_j,t_l} c(G_j,t_l)\ge 1$ 在 $S\le1600$ 不可行（测度零边界瞬时），**交付口径改用近全覆盖 R03**：

$$
\mathcal C_1\ge 1-\epsilon_0\ (\epsilon_0=10^{-3})\quad\text{或}\quad G_{\max}\le\tau_{\mathrm{tol}}.
$$

二重覆盖：严格整区 $\mathcal C_2^{\mathrm{strict}}\ge0.95$ 恒为 0，**交付口径改用面积—时间** $\mathcal C_2\ge0.95$。判定层实现于 `q2_relaxed_criteria.py`，连续覆盖证书实现于 `q2_lipschitz_certificate.py`。口径与假设的完整登记见 [[问题分析/星链系统-文献驱动版/假设台账-文献驱动版]] §4.2.1 与 [[问题分析/星链系统-文献驱动版/18-问题二算法条件松弛与假设驱动加速方案]]。
