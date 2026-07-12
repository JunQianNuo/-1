# 问题二、三、四：敏感性与蒙特卡洛检验

本目录只调用各题已有的求解器，不改变原求解器的默认行为。所有随机过程显式记录种子，并把结果写入本目录下的 `results/`。

## 运行

```powershell
$py = 'C:\Users\Nuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py '检验\run_validation.py' --question all --quick
```

去掉 `--quick` 后使用标准样本量：问题二 30 组空间—时间抽样；问题三在独立、显式定义的 2° 覆盖格、15° 通信格和 300 s 快照上运行 500 次时间块 Bootstrap；问题四 10,000 条年度事件轨迹。旧饱和产物只保留样本数量而未保留通信点坐标，故该问题三检验格不宣称为旧搜索的逐坐标复现。问题三标准运行会较久；`--replicates N` 可将三者的重复次数同时覆盖为 `N` 次，适合调试或统一比较。

## 输出与解释边界

- `sensitivity.csv`：固定其余条件后的单因素情景扰动；`monte_carlo.csv`：逐次随机重复结果；`summary.json`：95% 分位区间与本次配置；`q*/sensitivity.png`：调试简图。
- 正式绘图接口为 `figures/fig_q2_validation.png`、`figures/fig_q3_validation.png`、`figures/fig_q4_validation.png`：每张均由原始 CSV 重绘为中文双面板图，展示敏感性和蒙特卡洛 95% 区间。只有不带 `--quick` 的 `results/final/figures/` 可作为论文最终图来源。
- 问题二的随机抽样仅检验离散覆盖率的抽样稳定性，**不能**替代对连续区域严格覆盖的证明。
- 问题三以完整时间快照为 Bootstrap 区块，区间反映模型内时空样本的波动，**不是**外部观测数据的置信区间。
- 问题四现阶段仍是情景鲁棒性分析；真实的覆盖时序和通信容量尚未耦合前，不能解释为实际轨道风险预测。

快速模式仅用于验证代码链路和输出格式，不能用于论文的数值结论。
