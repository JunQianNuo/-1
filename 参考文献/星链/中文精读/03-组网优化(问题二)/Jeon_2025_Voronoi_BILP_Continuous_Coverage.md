---
title: Jeon 2025 · Voronoi + BILP 最少卫星连续覆盖与星间链路
source_pdf: PDF/03-组网优化(问题二)/2410.03354v3.pdf
subject: 星链数模-参考文献
problem: 问题二·组网优化
type: 精读解读
status: AI精读（pdftotext提取，公式待PDF核对）
topics:
  - 有界Voronoi图
  - 共地面轨迹星座
  - BILP整数规划
  - APC分解
  - 连续覆盖
  - 星间链路
---

# Jeon & Park 2025 · 最少卫星连续覆盖 + ISL（精读解读）

> **一句话总结**：本文给出**两条不依赖密集网格**的最少卫星星座设计路线——(1) 用**有界 Voronoi 图 (BVD)** 把"连续覆盖"化为"相邻星下点三角形外接圆半径 ≤ 覆盖角"的计算几何判据；(2) 对**共地面轨迹 (CGT) 星座**用 **APC 循环卷积分解 + 0-1 整数线性规划 (BILP)** 直接求最少卫星数。算例中 BILP 非对称 CGT 只需 **31 星**即可单重连续覆盖，比 Walker-Delta 的 40 星更省；但 Walker 的星间链路相对运动更短更稳。

## 一、论文速览
- **作者/年份/出处**：Soobin Jeon, Sang-Young Park（韩国延世大学天文系），2025，AAS 25-254（arXiv:2410.03354v3）。
- **解决的问题**：LEO 通信星座设计中，如何用**最少卫星**同时满足 (a) 目标区域**连续覆盖**、(b) **星间链路 (ISL)** 连通。
- **两大方法贡献**：
  1. **连续覆盖分析**：有界 Voronoi 图 (BVD) + APC 分解（两种，分别配 Walker 与 CGT）；
  2. **ISL 连续性分析**：相邻轨道面相对运动的**解析解**（最小/最大相对距离闭式）。
- **方法类型**：计算几何（Delaunay/Voronoi）+ 整数规划（BILP）+ 球面三角解析。

## 二、模型（星座参数化 + 覆盖几何）

### 2.1 两种星座族
- **Walker-Delta**：$T/P/F$（总星数/轨道面数/相位因子），$\Omega_m=\frac{360}{P}(m-1)$，$M_{m,n}=\frac{360}{T}F(m-1)+\frac{360}{S}(n-1)$，$S=T/P$。有**图案重复周期** $t_F,t_P$：$t_P$ 后星座图案与历元完全一致（对称性）。
- **共地面轨迹 CGT（本文重点）**：基于**重复地面轨迹 (RGT) 轨道**——周期比 $\kappa=N_P/N_D$（$N_P$ 圈/$N_D$ 天重复）。给定 $(\kappa,i,e)$ 唯一定出半长轴 $a$。**所有卫星共用同一条地面轨迹**，仅靠 $(\Omega_k,M_k)$ 沿"可行集" $N_P\Omega_k+N_D M_k=\text{const}\pmod{2\pi}$ 错开。设计问题 = 在这条线上放 $T$ 颗星的**时序位置**问题。

### 2.2 覆盖几何（降复杂度技巧）
角半径 $\rho$：$\sin\rho=R_E/(R_E+h)$；地心角 ECA $\lambda$、载荷天底角 $\lambda_{\max}$、最小仰角 $\varepsilon_{\min}$ 三者由球面三角互换：
$$\cos\eta=\sin\lambda_{\max}/\sin\rho,\qquad \lambda=90^\circ-\lambda_{\max}-\eta.$$
**要点**：三种口径（载荷波束 $\lambda_{\max}$、仰角 $\varepsilon_{\min}$、ECA $\lambda$）等价，**仿真只用其一即可**，省算力。

## 三、算法（三大可迁移武器）

### 3.1 有界 Voronoi 图 (BVD) —— 无网格连续覆盖判据 ★
**核心洞察**：连续覆盖 ⟺ 区域内任一点到最近星下点的角距 ≤ 覆盖角 $\lambda$ ⟺ **相邻三星下点的外接圆半径 ≤ $\lambda$**。
流程：星下点集合 → **Delaunay 三角化** → 对偶得 **Voronoi 图**（连接三角形外心）→ 限制在 AoI 纬度带内得**有界 Voronoi 图 (BVD)**。定义
$$\psi_{\max,k}=\max_l\psi_{k,l},\qquad \psi_{\max}=\max_k\psi_{\max,k},$$
（$\psi_{k,l}$ 为星下点 $p_k$ 到其 Voronoi 顶点 $C_{k,l}$ 的角距），**连续覆盖判据**：
$$\boxed{\psi_{\max}\le\lambda.}$$
**优势**：不做密集经纬网格逐点扫描，只在星下点集合上做计算几何，误差不来自网格分辨率。

### 3.2 APC 分解（Access–Pattern–Coverage 循环卷积）
覆盖时间线 $b_j[\tau]=\sum_k v_{k,j}[\tau]$（各星对目标点 $j$ 的接入廓线之和）。因 CGT 所有星是种子星的时移，故
$$b_j=v_{0,j}\circledast x=V_{0,j}\,x,$$
$v_{0,j}$ 是种子星接入廓线、$x$ 是**星座模式向量**（长度 $L$，$x[\tau]=1$ 表示该时隙放了一颗星），$V_{0,j}$ 是循环矩阵。**把 CGT 覆盖分析降为对 $x$ 的线性运算**——这是喂给 BILP 的关键。

### 3.3 BILP（0-1 整数线性规划）求最少星 ★
$$\min_{x}\ \mathbf 1^T x\quad\text{s.t.}\quad V_{0,j}x\ge f_j\ (\forall j\in J),\quad x\in\{0,1\}^L.$$
目标 $\mathbf 1^T x=T$ 即卫星总数，约束 $V_{0,j}x\ge f_j$ 即每个目标格满足覆盖需求。**直接解出最少卫星的（可非对称）配置**。对照的 **quasi-symmetric** 法则要求等间距 $\lambda=L/T$。

### 3.4 相邻轨道面相对运动（ISL 解析解）
$$\sin(\Delta\rho_{\min}/2)=\sin(\Delta\alpha_R/2)\cos(i_R/2),\quad \cos(\Delta\rho_{\max}/2)=\cos(\Delta\alpha_R/2)\cos(i_R/2),$$
$\cos i_R=\cos^2 i+\sin^2 i\cos\Delta\Omega$。给出相邻面卫星最小/最大相对距离的**闭式**，用于判 ISL 是否始终在链路距离内。

## 四、关键结论（算例：首尔区域，$i=42^\circ$，$\varepsilon_{\min}=15^\circ$，1 天）
- **Walker-Delta**：连续覆盖最少 **40 星**，解为 $i{:}T/P/F=42{:}40/40(1)/30$，ECA $\lambda=15.86^\circ$。
- **CGT quasi-symmetric**：32 星单重覆盖。
- **CGT BILP**：**31 星**单重覆盖（比 Walker 少 9 星），代价是**非对称**配置。
- **ISL**：Walker-Delta 相对运动范围更短、更一致（9559–9590 km），利于 ISL；BILP 非对称→相对距离范围杂但整体更近。
- **总结**：**要最少星 → BILP CGT；要稳定 ISL → Walker-Delta。**

## 五、对问题二的启示（★ 用户想"换算法"的直接候选）

| 本文武器 | 替代我们现有的什么 | 迁移价值 | 迁移风险/差异 |
|:--|:--|:--|:--|
| **有界 Voronoi 判据** $\psi_{\max}\le\lambda$ | grid/临界点覆盖判定 | 无网格离散误差；可能比临界点法更干净地判连续覆盖，或缓解西南角"网格瞬时"伪影 | 论文 BVD 是**纬度带圆环**版（全球/带状）；固定矩形区域要改有界方式（与 Namvar 同类问题） |
| **CGT + BILP** | Walker 枚举 / 几何锁定 M 一维搜索 | 放开 Walker 对称、用重复地面轨迹族 + 0-1 规划求**全局最少星**；算例 40→31 的降幅暗示可能突破我们 Walker 的 1512 | CGT 依赖 **RGT 轨道**：高度不再自由，题目 $h=550$ km 固定 ⇒ 需先算 550 km 对应的 $\kappa=N_P/N_D$ 是否给出合理 RGT；且 BILP 得非对称构型，论文解释成本高 |
| **APC 循环卷积** | 逐时刻网格覆盖计算 | 把覆盖时间线化为循环卷积/矩阵乘，快速 | 依赖 CGT 的"同一地面轨迹"结构，Walker 不直接适用 |
| **仰角/ECA/波束三口径等价** | —— | 覆盖判据只用其一，省算力 | 需与我们 $r_g=506$ km 口径对齐 |

**最值得试的两条新路线**：
1. **有界 Voronoi 覆盖判据**替换/交叉验证我们的临界点法——纯计算几何，`scipy.spatial.SphericalVoronoi` 可用。
2. **BILP（0-1 规划）**求最少星——`pulp`/`scipy.optimize.milp` 可解；但需先把我们的"Walker 族"或"CGT 族"离散成 $x\in\{0,1\}^L$ 的位置选择问题。这是相对我们"枚举+几何锁定"的**全局优化**升级。

**不能直接照搬**：本文目标是单点（首尔）/小圆 + ISL；我们是 $4^\circ\text{–}53^\circ$N、$73^\circ\text{–}135^\circ$E 大矩形区域、无 ISL（问题二）。BVD 的纬度带处理、CGT 的固定高度约束都要按题目重做。

## 六、术语对照

| 英文/符号 | 中文 | 含义 |
|:--|:--|:--|
| Bounded Voronoi Diagram (BVD) | 有界 Voronoi 图 | 限制在目标纬度带内的 Voronoi 镶嵌，用于连续覆盖判据 |
| Delaunay triangulation | Delaunay 三角化 | 星下点集合三角剖分，Voronoi 的对偶 |
| $\psi_{\max}$ | 最大角距 | 星下点到 Voronoi 顶点的最大角距；$\le\lambda$ 即连续覆盖 |
| Common Ground-Track (CGT) | 共地面轨迹星座 | 所有卫星共用同一条地面轨迹 |
| Repeat Ground-Track (RGT) | 重复地面轨迹轨道 | $N_P$ 圈/$N_D$ 天重复，$\kappa=N_P/N_D$ |
| APC decomposition | 接入-模式-覆盖分解 | $b_j=v_{0,j}\circledast x$ 循环卷积 |
| constellation pattern vector $x$ | 星座模式向量 | $\{0,1\}^L$，标记各时隙是否放星 |
| BILP | 0-1 整数线性规划 | $\min \mathbf 1^Tx$ s.t. $V_{0,j}x\ge f_j$ |
| ECA $\lambda$ / $\rho$ / $\varepsilon_{\min}$ | 地心角/角半径/最小仰角 | 覆盖几何三等价口径 |
| $i_R$ / $\Delta\rho$ | 相对倾角 / 相对角距 | 相邻轨道面相对运动，判 ISL |
