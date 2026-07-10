---
title: 问题二 BILP 集合覆盖尝试与下界评估
subject: 数学建模-星链系统
type: 算法评估
version: 初稿
status: 已实测
created: 2026-07-11
source:
  - "[[数学建模/第一次/参考文献/星链/中文精读/03-组网优化(问题二)/Jeon_2025_Voronoi_BILP_Continuous_Coverage.md|Jeon 2025 精读]]"
  - "[[数学建模/第一次/参考文献/星链/MD/03-组网优化(问题二)/Deng_2021_How_Many_Satellites.md|Deng 2021]]"
  - "代码/问题二/q2_bilp_setcover.py"
topics:
  - 问题二
  - BILP
  - 集合覆盖
  - 整数规划
  - 下界
---

# 问题二 BILP 集合覆盖尝试与下界评估

> 目的：尝试 Jeon 2025 / Deng 2021 的 **0-1 整数规划（BILP）最少卫星**思路作为 Walker 枚举的替代，并借 **LP 松弛下界**回答"1512 离最优有多远"。

## 1. 形式化（集合覆盖）

候选池：固定 $i=50^\circ,h=550$ km，把 $(\Omega,u_0)$ 离散成候选卫星槽位（每槽 = 一颗星）。时空需求 $d=(G_j,t_\ell)$。覆盖矩阵 $A_{d,c}=1$ 表示候选 $c$ 在需求 $d$ 处覆盖。模型：
$$
\min_{x\in\{0,1\}^C}\ \mathbf 1^Tx\quad\text{s.t.}\quad \sum_c A_{d,c}x_c\ge q\ \ \forall d.
$$
选中子集 = 一个（可非对称）星座，不受 Walker $M\times N$ 格点限制。**LP 松弛**（$x\in[0,1]$）给下界，**贪心**给可行上界，**HiGHS milp** 给限时精解。实现见 `代码/问题二/q2_bilp_setcover.py`（6 单测通过，含 LP=1.5<ILP=2 的分数松弛校验）。

## 2. 实测结果（$i=50^\circ$，候选池 $45\times45=2025$）

| 求解 | 粗 $4^\circ/900\mathrm s$ | 细 $3^\circ/450\mathrm s$ |
|:--|--:|--:|
| **LP 松弛下界** | 1005 | 1012 |
| 贪心可行上界 | 1337 | 1547 |
| 精确 ILP（HiGHS 180 s 限时）| 1325（gap 大，未收敛）| — |
| 贪心解在 $2^\circ/300\mathrm s$ 复核 | C1=0.982, $c_{\min}=0$ ✗ | C1=0.998, $c_{\min}=0$ ✗ |
| Walker 几何锁定（$2^\circ/300\mathrm s$ 验证）| — | **1512, C1=0.9999** ✓ |

## 3. 结论（诚实）

1. **LP 松弛下界 ≈ 1010（稳定）**：这是本次最有价值的产出——在该池/离散口径下，最少星数 $\gtrsim1010$。故 Walker 的 **1512 约为下界的 1.5 倍**：有改进空间，但**不可能低于约 1010**。
2. **粗网格 BILP 解会过拟合**：贪心 1337（粗）在 $2^\circ/300\mathrm s$ 复核只有 C1=0.982——与"6h 快速筛选"同类的乐观陷阱。**BILP 必须在目标分辨率上求解**才公平。
3. **贪心在本规模不敌 Walker**：细网格贪心 1547 > Walker 1512 且 C1 更低（近似比 $\ln$ 差距 + 8° 池粒度粗）。
4. **精确 ILP 在本规模不可解到最优**：2025 变量、选 ~1300、$\sim2\times10^4$ 约束，HiGHS 180 s 只从 1337 挪到 1325，离 LP 下界 1005 仍有大 gap。
5. **为何 Jeon 能 40→31 而我们看不到清晰优势**：Jeon 用**共地面轨迹 (CGT)**把 2D $(\Omega,u_0)$ 坍缩为**长度 $L\approx288$ 的 1D 模式向量**，ILP 小、可解到最优；我们的 2D 集合覆盖在 ~1500 星规模是巨型 ILP，只能贪心/限时。

## 4. 评价与建议

- **作为"换算法"**：直接的 2D 集合覆盖 BILP 在本题规模上**不实用**（精确不可解、贪心不敌 Walker）；但它给出了**下界 ≈1010**，这是 Walker 枚举给不了的、回答"最优性"的关键信息。
- **真正可行的 BILP 路线是 Jeon 的 CGT + BILP**：需采用**重复地面轨迹 (RGT)** 轨道把问题降为 1D 模式向量（$L\sim300$）的小型精确 ILP。代价：$h=550$ km 需微调到某个 RGT 周期比 $\kappa=N_P/N_D$（如 $\approx15$ 圈/日对应 $\sim561$ km，或多日重复），偏离题目固定高度需作敏感性说明。
- **保留结论**：问题二交付答案仍取 **Walker 几何锁定 $S^\ast\approx1512$（$C_1=0.9999$）**；BILP 的贡献是**下界 ≈1010** 与"非对称原则上可再省一点、但下界封顶"的判断。

## 5. 复现

```bash
python -m unittest test_q2_bilp_setcover        # 6 单测
python - <<'PY'
import q2_bilp_setcover as bilp
r=bilp.solve_q2_setcover(inclination_deg=50, n_raan=45, n_phase=45,
                         grid_step_deg=4.0, time_step_s=900.0, q=1)
print("LP下界",round(r.lp_lower_bound), "贪心",r.greedy_upper_bound)
PY
```

> 边界：LP 下界是**离散需求 + 有限池**下的下界，作为连续最小值的下界只是**近似**（依赖需求离散是松弛、池足够密）。
