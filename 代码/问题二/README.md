# 问题二 Python 代码说明

本目录是“问题二：多轨道面星座组网优化设计”的 Python 数值实现初版。

> 当前代码用于验证“地固系网格—时间覆盖判定”和递增规模搜索流程；`single_search` 仍是粗搜索，不是最终最优解证明。

## 文件结构

| 文件/目录 | 说明 |
|:--|:--|
| `q2_constellation.py` | 覆盖几何、Walker-Delta 星座参数化、指标计算、候选枚举与单重覆盖搜索接口 |
| `test_q2_constellation.py` | 单元测试 |
| `run_q2_smoke.py` | 最小 smoke run，用于确认模型链路可运行 |
| `run_q2_single_search.py` | 问题二单重覆盖正式粗搜索脚本 |
| `results/` | CSV/JSON 结果输出目录 |
| `figures/` | 图表输出目录 |

## 运行测试

```bash
python test_q2_constellation.py
```

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
