# 问题四算法实现说明

本目录实现 [[数学建模/第一次/问题分析/星链系统-文献驱动版/26-问题四求解算法设计与复杂度审查.md]] 中的问题四参数化算法。

> 默认运行是 smoke test，用于验证“碎片分层 → 碰撞概率 → 避撞决策 → 容量/成本 → 冗余可用性”的算法链路是否可执行，不代表最终数值结论。最终求解需要等待问题二最终星座构型、覆盖矩阵和问题三容量口径。

## 文件结构

| 文件 | 功能 |
|:--|:--|
| `q4_config.py` | 碎片环境、避撞、成本、任务参数 dataclass |
| `q4_debris.py` | 幂律尺寸分层、通量碰撞率、交会事件率 |
| `q4_collision.py` | CPA 与二维高斯圆域碰撞概率积分 |
| `q4_avoidance.py` | 阈值触发与 $\Delta V$ 可行性判定 |
| `q4_capacity_cost.py` | 容量损失、避撞成本、更换成本 |
| `q4_redundancy.py` | 冷储备置信度、覆盖可用性、单星关键性 |
| `q4_pipeline.py` | 非最终 smoke scenario 与结果/图表输出 |
| `run_q4_pipeline.py` | 命令行运行入口 |
| `问题4_求解.py` | 题目规范入口 |
| `tests/test_q4_algorithms.py` | TDD 单元测试与 smoke 测试 |

## 运行测试

```bash
python -m pytest tests/test_q4_algorithms.py -q
```

## 运行 smoke test

```bash
python 问题4_求解.py
```

输出文件：

- `results/q4_summary.csv`
- `results/q4_threshold_sensitivity.csv`
- `results/q4_run_report.txt`
- `figures/q4_threshold_sensitivity.png`

## 科学依据口径

- 通量法只用于物理撞击率；
- 单次交会概率使用会合平面二维高斯圆域积分；
- 避撞次数来自“交会事件率 × 超阈值概率 × 机动可行概率”；
- 失效率避免重复计数：不可编目通量风险与可编目残余风险分开；
- 99% 可用性最终必须接入问题二覆盖矩阵计算。
