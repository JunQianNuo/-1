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
- 可达样本 $P_{30}^{\mathrm{reach}}\ge0.999$ 与全样本 $P_{30}^{\mathrm{all}}\ge0.95$ 双比例提前终止；
- 等权样本超时预算 $n_{\max}=\lfloor0.001R\rfloor$；
- `active/deferred/rejected/verified/numerical_error` 候选状态机；
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
