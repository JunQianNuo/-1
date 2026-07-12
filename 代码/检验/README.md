# 问题二、三、四：敏感性与蒙特卡洛检验

本目录只调用各题已有的求解器，不改变原求解器的默认行为。所有随机过程显式记录种子，并把结果写入本目录下的 `results/`。

## 运行

```powershell
$py = 'C:\Users\Nuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py '检验\run_validation.py' --question all --quick
```

去掉 `--quick` 后使用标准样本量：问题二 30 组空间—时间抽样，问题三 500 次时间块 Bootstrap，问题四 10,000 条年度事件轨迹。`--replicates N` 可将三者同时覆盖为 `N` 次，适合调试或统一比较。

## 输出与解释边界

- `sensitivity.csv`：固定其余条件后的单因素情景扰动；`monte_carlo.csv`：逐次随机重复结果；`summary.json`：95% 分位区间与本次配置；`sensitivity.png`：对应的简图。
- 问题二的随机抽样仅检验离散覆盖率的抽样稳定性，**不能**替代对连续区域严格覆盖的证明。
- 问题三以完整时间快照为 Bootstrap 区块，区间反映模型内时空样本的波动，**不是**外部观测数据的置信区间。
- 问题四现阶段仍是情景鲁棒性分析；真实的覆盖时序和通信容量尚未耦合前，不能解释为实际轨道风险预测。

快速模式仅用于验证代码链路和输出格式，不能用于论文的数值结论。
