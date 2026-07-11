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
| `q3_validation.py` | 拓扑合法性检查 |
| `q3_pipeline.py` | 单快照求解管线与参数敏感性外层循环 |
| `run_q3_pipeline.py` | 命令行运行入口 |
| `问题3_求解.py` | 题目规范入口，调用 `run_q3_pipeline.py` |
| `tests/test_q3_algorithms.py` | 算法单元测试与 smoke test |

## 运行测试

```bash
python -m pytest tests/test_q3_algorithms.py -q
```

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
