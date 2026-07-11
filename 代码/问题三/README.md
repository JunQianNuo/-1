# 问题三算法实现说明

本目录实现 [[数学建模/第一次/问题分析/星链系统-文献驱动版/22-问题三求解算法设计.md]] 中的算法 A-K。

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
| `q3_validation.py` | 拓扑合法性检查 |
| `q3_pipeline.py` | 单快照求解管线与参数敏感性外层循环 |
| `run_q3_pipeline.py` | 命令行运行入口 |
| `问题3_求解.py` | 题目规范入口，调用 `run_q3_pipeline.py` |
| `tests/test_q3_algorithms.py` | 算法单元测试与 smoke test |

## 运行测试

```bash
python -m pytest tests/test_q3_algorithms.py -q
```

## 当前效率实现

- `WeightedGraph` 同时维护去重边表与邻接表；`neighbors()` 为按节点度数查询，避免 Dijkstra 每次扩展节点时扫描全边集。
- `build_isl_graph(..., method="nearest")` 使用 KD-tree 接口对相邻轨道面批量求最近卫星，将邻轨最近搜索由朴素 $O(MN^2)$ 降低到约 $O(MN\log N)$。
- 路由阶段保留“每个地面源点一次多源 Dijkstra”的实现，复用同源到全网卫星的最短路结果。

## 联合搜索器

`q3_joint_search.py` 已实现：

- 合法 `(M,N)` 生成并按可实现星数 `S=MN` 分层排序；
- 同轨链路距离必要条件剪枝；
- `u0∈[0,360°/N)` 周期性降维；
- 覆盖评价上界提前终止工具 `CoverageProgress`；
- 代表时刻连通性筛查；
- OD 时延乐观下界筛查；
- 严格最大时延 / `P30` 服务比例口径的通信提前终止；
- 当前星数层全部候选复核后，按鲁棒裕量选择候选。

覆盖模型由问题二代码提供，因此联合搜索主函数 `search_constellations(...)` 接收外部 `coverage_evaluator` 回调。

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
