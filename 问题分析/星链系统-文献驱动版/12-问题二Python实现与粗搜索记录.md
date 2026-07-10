# 12-问题二 Python 实现与粗搜索记录

## 1. 本轮代码产出

代码位置：

- `数学建模/第一次/代码/问题二/q2_constellation.py`
- `数学建模/第一次/代码/问题二/run_q2_single_search.py`
- `数学建模/第一次/代码/问题二/test_q2_constellation.py`
- `数学建模/第一次/代码/问题二/README.md`

已实现的核心接口：

1. 圆轨道 Walker-Delta 型星座参数化；
2. 惯性系到地固系的卫星星下点传播；
3. 目标区域经纬度网格与时间网格生成；
4. 网格点覆盖重数矩阵

$$
c(G_j,t_l)=\sum_{m,n}\mathbf{1}\{\gamma_{m,n,j}(t_l)\le \theta\};
$$

5. 单重覆盖指标 $C_1,\bar c,c_{\min},G_{\max}$；
6. 递增规模单重覆盖搜索接口 `search_single_coverage`。

## 2. 代码检验

单元测试采用先写测试、再实现的方式补入，当前覆盖：

- 地面点单位向量几何；
- 单星覆盖子星点的基本几何；
- 覆盖指标计算；
- 经纬度网格不越界并包含边界；
- 时间网格不越界并包含终点；
- 候选因子对与相位基本区间；
- 单重覆盖搜索接口会输出候选记录与首个可行解字段。

验证命令：

```bash
python test_q2_constellation.py
python -m py_compile q2_constellation.py run_q2_smoke.py run_q2_single_search.py test_q2_constellation.py
python run_q2_single_search.py
```

## 3. 当前粗搜索设置

本轮仅做第一版粗搜索：

| 项目 | 设置 |
|:--|:--|
| 目标区域 | $4^\circ\mathrm{N}\sim53^\circ\mathrm{N}$，$73^\circ\mathrm{E}\sim135^\circ\mathrm{E}$ |
| 空间步长 | $6^\circ$ |
| 时间步长 | $900\,\mathrm{s}$ |
| 仿真时长 | $6\,\mathrm{h}$ |
| 总星数 | $S=40$ |
| 候选倾角 | $49^\circ,50^\circ,51^\circ,52^\circ,53^\circ$ |
| 相位步长 | $30^\circ$ |
| 候选上限 | 2000 个 |

当前输出：

- `数学建模/第一次/代码/问题二/results/q2_single_search_candidates.csv`
- `数学建模/第一次/代码/问题二/results/q2_single_search_summary.json`
- `数学建模/第一次/代码/问题二/figures/Q2_single_search_best_min_count_map.png`
- `数学建模/第一次/代码/问题二/figures/Q2_single_search_best_time_series.png`

## 4. 当前粗搜索结果

在上述粗网格、短时长、候选上限下，程序评估 2000 个候选后未发现满足

$$
c_{\min}=\min_{G_j,t_l}c(G_j,t_l)\ge 1
$$

的 $S=40$ 候选。

当前最佳候选的粗搜索指标为：

| 指标 | 数值 |
|:--|:--|
| $S$ | 40 |
| $M,N$ | $1,40$ |
| $i$ | $53^\circ$ |
| $\Omega_0$ | $30^\circ$ |
| $u_0$ | $0^\circ$ |
| $C_1$ | 0.1503567382 |
| $c_{\min}$ | 0 |
| $G_{\max}$ | $22500\,\mathrm{s}$ |

因此，本轮只能说明：在当前非常粗的搜索设置下，$S=40$ 尚未找到连续单重覆盖方案；不能据此证明 $S=40$ 不可行。

## 5. 图像记录

![[数学建模/第一次/代码/问题二/figures/Q2_single_search_best_min_count_map.png]]

![[数学建模/第一次/代码/问题二/figures/Q2_single_search_best_time_series.png]]

## 6. 下一步

下一步应从“是否存在可行解”而不是“当前最佳均值覆盖率”出发，进行递增规模粗筛：

1. 保持粗网格，搜索 $S=40,41,\ldots$，寻找首个 $c_{\min}\ge1$ 的候选；
2. 对首个可行规模附近进行更细相位搜索；
3. 将时间范围扩大到一个恒星日；
4. 将空间步长降到 $2^\circ$ 或更细；
5. 对最终候选做边界加密与时间步长收敛检验。

