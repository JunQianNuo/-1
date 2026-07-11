# 问题三算法实现说明

本目录实现 [[22-问题三求解算法设计]] 中的算法 A-L。

> 默认运行是 smoke test，用于验证算法链路是否可执行，不代表最终数值结论。

## 文件结构

| 文件 | 功能 |
|:--|:--|
| `q3_config.py` | 星座参数、物理常数、仿真配置 |
| `q3_orbit.py` | 时间网格、地面点、卫星位置传播 |
| `q3_topology.py` | ISL 快照图生成、连通分量、拓扑摘要 |
| `q3_access.py` | 地面点可接入卫星集合计算 |
| `q3_routing.py` | 加权图、多源 Dijkstra、端到端最小时延路由 |
| `q3_statistics.py` | 平均、最大、分位数、不可达率等时延统计 |
| `q3_traffic.py` | 均匀 OD 需求矩阵、最短路基线负载统计 |
| `q3_optimization.py` | K 候选路径、线性规划多路径分流、吞吐量二分搜索 |
| `q3_joint_search.py` | 问题二覆盖与问题三通信的联合分支定界搜索 |
| `q3_batched_routing.py` | 有向增广稀疏图与批量 Dijkstra |
| `q3_joint_evaluator.py` | 共享快照和跨保真联合评价 |
| `q3_validation.py` | 拓扑合法性检查 |
| `q3_pipeline.py` | 单快照求解管线与参数敏感性外层循环 |
| `run_q3_pipeline.py` | 命令行运行入口 |
| `run_q3_joint_search.py` | 问题二—问题三联合反推入口 |
| `问题3_求解.py` | 题目规范入口，调用 `run_q3_pipeline.py` |
| `tests/test_q3_algorithms.py` | 原有算法单元测试与 smoke test |
| `tests/test_q3_joint_search.py` | 联合评价、批量路由、状态机与 CLI 测试 |

## 运行测试

运行依赖：`numpy`、`scipy`；测试另需 `pytest`。多路径分流由 `scipy.optimize.linprog` 的 HiGHS 后端求解。

```bash
python -m pytest tests -q
```

## 当前效率实现

- `WeightedGraph` 同时维护去重边表与邻接表；`neighbors()` 为按节点度数查询，避免 Dijkstra 每次扩展节点时扫描全边集。
- `build_isl_graph(..., method="nearest")` 使用 KD-tree 接口对相邻轨道面批量求最近卫星，将邻轨最近搜索由朴素 $O(MN^2)$ 降低到约 $O(MN\log N)$。
- 联合评价阶段在有向增广稀疏图上一次批量求解全部地面源点的 Dijkstra；原逐源实现保留为对照后端。
- 问题二覆盖与问题三通信共享同一时刻的卫星位置和星地几何，避免重复轨道传播。
- 多路径分流按需求守恒和链路容量约束联合求解线性规划，避免逐 OD 贪心分配造成顺序依赖和可行性误判。

## 联合搜索器

`q3_joint_search.py` 已实现：

- 合法 `(M,N)` 生成并按可实现星数 `S=MN` 分层排序；
- 同轨链路距离必要条件剪枝；
- `u0∈[0,360°/N)` 周期性降维；
- 面积加权覆盖上界工具 `WeightedCoverageProgress`；
- 代表时刻连通性筛查；
- OD 时延乐观下界筛查；
- $P_{30}^{\mathrm{reach}}$ 与 $P_{30}^{\mathrm{all}}$ 为诊断指标（只排序，不淘汰）；
- 覆盖 $\mathcal C_1\ge0.999$ 且 $\mathcal C_2\ge0.95$ 为唯一淘汰条件；
- `active/deferred/rejected/verified/numerical_error` 候选状态机；
- 按 $P_{30}^{\mathrm{all}}$ 主排序，$P_{30}^{\mathrm{reach}}$ / 最大时延为 tie-break。
- 当前星数层全部候选复核后，按鲁棒裕量选择候选。

覆盖模型由问题二代码提供，因此联合搜索主函数 `search_constellations(...)` 接收外部 `coverage_evaluator` 回调。

## 运行联合反推

先复用问题二缓存发现可行星数上界：

```bash
python run_q3_joint_search.py --mode discover --q2-cache ../问题二/results/q2_free_search/fine_records.csv --s-lb 1480 --s-max 1800 --workers 4
```

再从可靠下界执行离散核验；中断后可通过检查点恢复：

```bash
python run_q3_joint_search.py --mode certify --resume results/q3_joint/joint_checkpoint.jsonl --s-lb 1480 --s-max 1800 --workers 4
```

联合入口输出：

- `joint_candidate_records.csv`
- `joint_stage_timing.csv`
- `joint_checkpoint.jsonl`
- `joint_layer_summary.csv`
- `joint_summary.json`
- `joint_report.md`

发现阶段没有找到可行解时只报告 `inconclusive`；只有核验阶段的较小星数层全部候选被严格否决，才能报告规定离散范围内不可行。

## 饱和停止搜索（覆盖为唯一淘汰、$P_{30}^{\mathrm{all}}$ 边际衰减判停）

覆盖 $\mathcal C_1\ge0.999$ 且 $\mathcal C_2\ge0.95$ 为唯一淘汰条件。按星数递增逐层跑低→中→高，取每层覆盖最优候选的 $P_{30}^{\mathrm{all}}$，若某 $S_i$ 在其后 200 星窗口内 $P_{30}^{\mathrm{all}}$ 最大增量 $\le1\%$ 且每百星增量 $\le0.5\%$，则认为已达饱和，$S_i$ 为最小推荐星数。

```bash
python run_q3_joint_search.py --mode saturation \
  --s-lb 1440 --s-max 2000 --s-step 20 \
  --forward-window-s 200 --max-window-gain 0.01 --max-gain-per-100 0.005 \
  --workers 4 --out results/q3_saturation
```

输出额外包含 `joint_saturation_curve.csv`（$S$—$P_{30}^{\mathrm{all}}$ 曲线数据）、饱和决策与窗口增益。

## 首次完整搜索实际结果（整恒星日 discover）

已用问题二双重覆盖可行缓存执行一次真实规模联合反推，结果落盘 `results/q3_joint/`（`joint_summary.json`、`joint_report.md`、`joint_candidate_records.csv`、`joint_stage_timing.csv`、`joint_layer_summary.csv`、`joint_checkpoint.jsonl`）。

命令：

```bash
python run_q3_joint_search.py --mode discover \
  --q2-cache ../问题二/results/q2_free_search/fine_records.csv \
  --s-lb 1480 --s-max 1800 --workers 10 \
  --duration-s 86164.09 \
  --high-time-step-s 150 --coverage-high-step-deg 1 --communication-high-step-deg 5 \
  --out results/q3_joint
```

| 项目 | 值 |
|:--|:--|
| 实际耗时 | 665.9 s（≈11 min，`workers=10`，28 核） |
| 高保真母网格 | 576 时刻 × 3150 覆盖点 × 154 通信点（23 562 OD 对/时刻） |
| 输入候选 | 257 个 Q2 可行构型（S∈[1480,1800]，C1≥0.999，C2≥0.95） |
| 阶段晋级 | 低保真 257 → 中保真 100 → 高保真 **0**（全部被中保真严格上界淘汰） |
| 通信满足率 | P30_reach ∈ [0.745, 0.839]（需 ≥0.999）；P30_all ∈ [0.743, 0.839]（需 ≥0.95） |
| 超时比例 | 约 20% 可达 OD 对超 30 ms；最大端到端时延 69–100 ms |
| 最优（仍被拒）构型 | S=1540 (M=35, N=44, F=24, i=50.25°)，P30_reach=0.839 |
| claim | `inconclusive`（discover 不证明不可行，只证明缓存内 Q2 最优构型全部不达标） |

**结论**：题面 4 邻接最近邻 ISL 规则下，问题二覆盖最优构型无法满足严格 30 ms——瓶颈是跨区长距 OD 时延（目标区域经度跨约 6000 km，最近邻 ISL 路径角对角绕行）。差距是数量级的，非网格细化可弥补。

**加速确认**：多保真阶梯 + 母网格严格上界使高保真通信评价对全部候选一次都未触发，11 分钟完成整日判定，验证了共享快照 + 批量最短路 + 减少高保真候选数的降本设计（详见 [[22-问题三求解算法设计]] §14、[[20-问题三分析审查]]）。

## 运行 smoke test

```bash
python 问题3_求解.py
```

输出文件：

- `results/q3_topology_summary.csv`
- `results/q3_access_summary.csv`
- `results/q3_delay_samples.csv`
- `results/q3_delay_summary.csv`
- `results/q3_run_report.txt`
- `figures/q3_smoke_delay_hist.png`

## 使用真实物理接入口径

默认 smoke test 为保证链路可跑通，使用宽接入角与宽 ISL 距离。若要使用题面物理接入口径，可运行：

```bash
python 问题3_求解.py --physical-coverage --planes 36 --sats-per-plane 42 --phase-factor 0 --inclination-deg 50 --u0-deg 6.429
```

此命令会产生数值样本，但是否作为最终结果需要另行设置足够的时间步长、地面采样密度和收敛检验。
