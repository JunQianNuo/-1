---
title: Chen 2021 · 巨型星座ISL路径
source_md: MD/04-星间链路(问题三)/Chen_2021_ISL_Paths_Mega_Constellation.md
source_pdf: PDF/04-星间链路(问题三)/Chen_2021_ISL_Paths_Mega_Constellation.pdf
subject: 星链数模-参考文献
problem: 问题三·星间链路
type: 精读解读
status: AI精读（待校对）
topics:
  - ISL跳数
  - Walker-Delta星座
  - 星链拓扑
  - 相位因子F
  - 端到端时延
---

# Chen 2021 · 巨型星座ISL路径（精读解读）

> **一句话总结**：本文提出一套**解析（闭式）算法**，仅凭两地用户的纬度与经度差即可快速估算 Walker-Delta 倾斜轨道巨型星座（如星链）中两地间的**最小 ISL 跳数**，无需跑昂贵的网络仿真，并揭示了跳数的空间分布规律、接入卫星选择的影响，以及通过优化相位因子 $F$ 降低平均跳数的方法。

## 一、论文速览

- **作者/年份/出处**：Quan Chen、Giovanni Giambene、Lei Yang、Chengguang Fan、Xiaoqian Chen，2021 年，*IEEE Transactions on Vehicular Technology*（DOI: 10.1109/TVT.2021.3058126）。作者主要来自国防科技大学与锡耶纳大学。
- **解决的问题**：巨型星座（MCN）中卫星数量巨大，两个地面用户被不同卫星接入时需要多次星间链路（ISL）中继。**跳数（hop-count）** 是路由复杂度与端到端时延的关键指标。以往跳数评估依赖复杂仿真，计算昂贵。本文要建立一个**理论/解析模型**直接算出任意两地间的最小 ISL 跳数。
- **核心贡献**（4 条）：
  1. 提出一个**显式（闭式）算法**，快速估算任意两地面用户间的最小 ISL 跳数（Algorithm 1），并用仿真验证精度（大星座相对误差约 5%）。
  2. 推导了跳数的若干**对称性与不变性**，证明在给定星座中跳数**只取决于两用户的纬度 $\varphi_1,\varphi_2$ 和经度差绝对值 $\lvert\Delta\lambda\rvert$**，与经度绝对位置、相对方位无关。
  3. 以星链为例给出**全球跳数分布图**及星座参数（$N_P,M_P,F$）的影响，发现**优化相位因子 $F$** 可有效降低平均跳数。
  4. 揭示用户切换接入卫星（升轨/降轨）时跳数会**剧烈变化**（星链中最大可达 45 跳差）。
- **方法类型**：**解析法（闭式几何模型）** 为主，辅以 STK/Matlab 仿真验证。

## 二、研究背景与动机

巨型星座（Starlink、OneWeb、Kuiper 等）在 LEO 部署成百上千颗卫星，配备星上处理（OBP）与星间链路（ISL）。当两地用户由不同接入卫星服务时，需经多跳 ISL 中继。卫星密度越大，路径需要的中继越多，路由复杂度与处理成本越高，因此**最小跳数**成为系统性能与复杂度的关键度量，被广泛用于卫星网络路由设计。

两个痛点：
1. 由于卫星运动和用户-卫星连接切换，两地间跳数**随时间变化**，直接求解困难；已有研究多依赖**网络仿真**，计算量大、且难以解释 ISL 中继的内在规律。
2. 倾斜轨道星座中，一个用户常同时被**升轨与降轨卫星**覆盖，用户切换接入卫星（星间切换）会导致路由路径与性能大幅变化，此现象此前研究不足。

因此需要一个**解析理论模型**，这在已有文献中尚属空白。

## 三、核心方法（分章节中文重述）

### 3.1 系统模型：Walker-Delta 星座与 ISL 连接方式

本文聚焦 **Walker-Delta** 星座，由 $N_P \times M_P$ 颗卫星构成：$N_P$ 为轨道面数，$M_P$ 为每面卫星数，所有轨道倾角相同为 $\alpha$，沿赤道均匀分布。关键相位关系：

- 相邻轨道面升交点赤经（RAAN）之差：$\Delta\Omega = 2\pi / N_P$
- 同一面内相邻卫星的相位差：$\Delta\Phi = 2\pi / M_P$
- 相邻面卫星之间的相位偏移：$\Delta f = 2\pi F/(N_P M_P)$，其中 $F$ 为**相位因子**（phasing factor）。

星座记法为 $\alpha\!:\!N_P M_P / N_P / F$。每颗卫星有二维逻辑索引 $(v,h)$，表示第 $h$ 轨道面的第 $v$ 颗卫星。

**ISL 连接方式**：每颗卫星建立 4 条永久 ISL —— 2 条**面内**（intra-plane，与同轨道前后卫星）+ 2 条**面间**（inter-plane，与相邻轨道卫星）。相位因子 $F$ 允许取负，取值范围 $\{1-N_P, 2-N_P,\dots,0,1,\dots,N_P-1\}$。整个网络呈**环面（torus）状网格拓扑**。

**最小跳路径的两个方向分量**：从源到目的的最小跳路径，每个中继节点只有两个候选转发方向。令 $H_v$、$H_h$ 分别为**面内跳数**与**面间跳数**，二者带方向（符号）：
- $H_v>0$ 表示沿卫星运动方向转发，$H_v<0$ 相反；
- $H_h>0$ 表示向东中继，$H_h<0$ 表示向西中继。

### 3.2 升轨卫星与降轨卫星

按飞行方向把卫星分两类：**升轨卫星（Ascending, A）** 朝纬度增大方向飞，**降轨卫星（Descending, D）** 朝纬度减小方向飞。当倾角 $0^\circ<\alpha<90^\circ$ 时，升轨卫星飞向东北，降轨卫星飞向东南。**关键约束**：由于升/降轨卫星相对高速运动导致链路不稳定，**升轨与降轨卫星之间不建立面间 ISL** —— 升轨卫星一般只连升轨卫星，降轨只连降轨。这是后文 A2D/D2A 路径需要绕行的根本原因。

由于巨型星座多重覆盖，本文**假设每个用户至少被一颗升轨和一颗降轨卫星同时覆盖**。

### 3.3 卫星星下点（SSP）的地面位置

某卫星在地面的星下点由纬度 $\varphi$ 与经度 $\lambda$ 表示。在任意时刻 $t$：

$$
\varphi = \arcsin(\sin\alpha \sin u),\tag{1}
$$

$$
\lambda = \zeta(u) + L_0 - \omega_e t,\tag{2}
$$

$$
\zeta(u)=\begin{cases}\arctan(\cos\alpha\tan u), & \text{升轨段}\\ \arctan(\cos\alpha\tan u)+\pi, & \text{降轨段}\end{cases}\tag{3}
$$

符号解释：
- $\alpha$：轨道倾角（相对赤道），单位 弧度/度。
- $u\in[-\pi,\pi]$：卫星从升交点起算的**相位角**，描述卫星在轨位置。$u\in[-\pi/2,\pi/2]$ 为升轨段（飞向东北），其余为降轨段（飞向东南）。
- $\zeta(u)$：星下点相对升交点的**经度差**，随相位变化。
- $L_0$：轨道升交点的初始经度（绝对参数，决定轨道面位置）。
- $\omega_e$：地球自转角速度（rad/s）。

**关键简化假设**：由于星座密集、单星覆盖小，**假设接入卫星正好位于用户正上方**，即接入卫星与用户共享同一 $(\varphi,\lambda)$。这把"用户跳数"问题转化为"接入卫星跳数"问题，是全模型的核心近似。

### 3.4 通用跳数模型（本文最核心公式）

考虑两用户 User 1 $(\varphi_1,\lambda_1)$、User 2 $(\varphi_2,\lambda_2)$，其中 $\varphi_1,\varphi_2\in[-\alpha,\alpha]$。设 Sat 1 在西侧，经度差 $\Delta\lambda=\lambda_2-\lambda_1\in[0,\pi]$。

**第一步：面间跳数 $H_h$。** 两颗接入卫星所在轨道面的 RAAN 差有两种表达。几何上：

$$
\Delta L_0 = L_{0,2}-L_{0,1} = H_h \Delta\Omega.\tag{4}
$$

由式 (2) 又可写为：

$$
\Delta L_0 = \Delta\lambda + \zeta(u_1) - \zeta(u_2).\tag{5}
$$

联立 (4)(5) 求出面间跳数（四舍五入到最近整数）：

$$
H_h = \mathrm{Round}\!\left[\frac{\Delta L_0}{\Delta\Omega}\right] = \mathrm{Round}\!\left[\frac{\Delta\lambda+\zeta(u_1)-\zeta(u_2)}{\Delta\Omega}\right].\tag{6}
$$

其中 $\mathrm{Round}(x)$ 返回距 $x$ 最近的整数。含义：面间跳数 = 两轨道面 RAAN 之差 / 相邻面 RAAN 间隔，即"需要跨几个轨道面"。

**第二步：面内跳数 $H_v$。** 每次面内中继给相位角增加 $\Delta\Phi$，每次面间中继增加 $\Delta f$，故两卫星相位角之差：

$$
\Delta u = u_2 - u_1 = H_v \Delta\Phi + H_h \Delta f.\tag{7}
$$

其中 $u_1,u_2$ 满足（由式 (1) 反解）：

$$
\sin u = \sin\varphi / \sin\alpha.\tag{8}
$$

解出面内跳数：

$$
H_v = \mathrm{Round}\!\left[\frac{\Delta u - H_h \Delta f}{\Delta\Phi}\right].\tag{9}
$$

含义：先扣除面间中继已贡献的相位量 $H_h\Delta f$，剩余相位差除以面内相位间隔 $\Delta\Phi$，即"在轨道面内还要走几步"。

**第三步：总跳数** 取两分量绝对值之和：

$$
H = \lvert H_h\rvert + \lvert H_v\rvert.\tag{10}
$$

**环面归一化（重要细节）**：网络是环面状，报文也可反向到达目的。若某方向路径过长（如 $H_h>N_P/2$），应走反方向。因此式 (6) 前需把 $\Delta L_0$ 归一化到 $[-\pi,\pi]$，式 (9) 前需把 $\Delta U=\Delta u-H_h\Delta f$ 归一化，归一化函数：

$$
\overline{x}=\mathcal{N}(x)=\mathrm{mod}(x+\pi,\,2\pi)-\pi.\tag{11}
$$

这保证每一维都取"最短绕行方向"。

### 3.5 四种路径模式（A2A / A2D / D2A / D2D）

由式 (8) 解 $u$ 时是**多值**的，取决于卫星在升轨段还是降轨段：

$$
u=\begin{cases}\arcsin\dfrac{\sin\varphi}{\sin\alpha}, & \text{升轨段}\\[2mm] \dfrac{\varphi}{\lvert\varphi\rvert}\pi-\arcsin\dfrac{\sin\varphi}{\sin\alpha}, & \text{降轨段}\end{cases}\tag{12}
$$

其中 $\varphi/\lvert\varphi\rvert$ 指示卫星在北半球还是南半球。

因为每个用户既可接入升轨（A）也可接入降轨（D）卫星，两地组合共 **4 种路径模式：A2A、A2D、D2A、D2D**。每种模式下 $u_1,u_2,\zeta(u_1),\zeta(u_2)$ 取值不同（原文 Table II 列出）。以 A2A 为例：

$$
H_h^{\mathrm{A2A}}=\mathrm{Round}\!\left(\left[\Delta\lambda+\arctan\!\big(\cos\alpha\tan(\arcsin\tfrac{\sin\varphi_1}{\sin\alpha})\big)-\arctan\!\big(\cos\alpha\tan(\arcsin\tfrac{\sin\varphi_2}{\sin\alpha})\big)\right]\big/(2\pi/N_P)\right),\tag{13}
$$

$$
H_v^{\mathrm{A2A}}=\mathrm{Round}\!\left(\frac{\arcsin\tfrac{\sin\varphi_2}{\sin\alpha}-\arcsin\tfrac{\sin\varphi_1}{\sin\alpha}-H_h^{\mathrm{A2A}}F\tfrac{2\pi}{N_P M_P}}{2\pi/M_P}\right).\tag{14}
$$

（式 13、14 中 Round 内的分子都要先用式 (11) 归一化到 $[-\pi,\pi]$。）该模式总跳数 $H^{\mathrm{A2A}}=\lvert H_h^{\mathrm{A2A}}\rvert+\lvert H_v^{\mathrm{A2A}}\rvert$（式 15）。

**最终跳数取四模式最小值**：

$$
H = \min\{H^{\mathrm{A2A}},\,H^{\mathrm{A2D}},\,H^{\mathrm{D2A}},\,H^{\mathrm{D2D}}\}.\tag{16}
$$

**Algorithm 1（跳数估算算法）流程**：输入 $\varphi_1,\varphi_2,\Delta\lambda$，对 4 种模式循环 → 按 Table II 定 $u_1,u_2,\zeta(u_1),\zeta(u_2)$ → 算 $\Delta L_0$ 并归一化 → $H_h=\mathrm{Round}(\overline{\Delta L_0}/\Delta\Omega)$ → 算 $\Delta U$ 并归一化 → $H_v=\mathrm{Round}(\overline{\Delta U}/\Delta\Phi)$ → $H^{X2X}=\lvert H_h\rvert+\lvert H_v\rvert$ → 取 4 者最小。整个算法**无需仿真、无需遍历卫星图，纯闭式代数计算**。

### 3.6 跳数的对称性（可大幅减少输入信息）

记 $H[(\varphi_1,\lambda_1),(\varphi_2,\lambda_2)]$ 为两地跳数。证明了以下性质：

- **命题 1（互易性 Reciprocity）**：$H[(\varphi_1,\lambda_1),(\varphi_2,\lambda_2)]=H[(\varphi_2,\lambda_2),(\varphi_1,\lambda_1)]$ —— 跳数无方向性（双向网络固有属性）。
- **命题 2（可交换性 Commutativity）**：$H[(\varphi_1,\lambda_1),(\varphi_2,\lambda_2)]=H[(\varphi_2,\lambda_1),(\varphi_1,\lambda_2)]$ —— 球面矩形对角顶点的用户对跳数相同。
- **性质 1（横向平移不变性）**：两用户沿纬线整体平移（$\lambda$ 同加常数）跳数不变，即 $H$ 只依赖 $\Delta\lambda$ 而非绝对经度。
- **性质 2（双侧对称）**：$H[(\varphi_1,0),(\varphi_2,\Delta\lambda)]=H[(\varphi_1,0),(\varphi_2,-\Delta\lambda)]$ —— 只依赖 $\lvert\Delta\lambda\rvert$。
- **性质 3（纬向对称）**：$H[(\varphi_1,\lambda_1),(\varphi_2,\lambda_2)]=H[(-\varphi_1,\lambda_1),(-\varphi_2,\lambda_2)]$ —— 关于赤道对称。

**核心结论**：给定 Walker-Delta 星座，两地跳数**只由 $\varphi_1,\varphi_2,\lvert\Delta\lambda\rvert$ 三个量决定**（$\varphi\in[-\alpha,\alpha]$）。对星链这类多层混合星座，该方法**逐层适用**。

## 四、关键结论与结果

**1）模型验证（Section IV-A）**。生成 1000 个全球均匀分布用户，与 STK/Matlab 仿真（每场景 30 分钟时间平均）对比。误差度量：

$$
H_{avg}=\frac{\sum_{j=1}^{N_U}\sum_{i=1}^{j}H(U_i,U_j)}{N_U(N_U-1)/2},\tag{17}
$$

$$
E_{avg}=\frac{\sum_{j=1}^{N_U}\sum_{i=1}^{j}\lvert H(U_i,U_j)-\widetilde{H}(U_i,U_j)\rvert}{N_U(N_U-1)/2},\qquad E_r=E_{avg}/H_{avg}.\tag{18,19}
$$

其中 $H(U_i,U_j)$ 为解析模型跳数，$\widetilde{H}(U_i,U_j)$ 为仿真时间平均跳数，$N_U$ 为用户总数。结果（Table III）：

| 星座 | 卫星数 | 面数×每面 | 倾角 | 平均跳数 | 绝对误差 | 相对误差 |
|:--|:--|:--|:--|:--|:--|:--|
| Celestri | 63 | 7×9 | $48^\circ$ | 2.45 | 0.38 | 15.48% |
| NeLS | 120 | 10×12 | $55^\circ$ | 3.38 | 0.45 | 13.18% |
| Quarter-Starlink | 400 | 16×25 | $53^\circ$ | 6.52 | 0.55 | 8.38% |
| Kuiper phase A | 1156 | 34×34 | $51.9^\circ$ | 10.68 | 0.71 | 6.41% |
| Starlink phase I-a | 1600 | 32×50 | $53^\circ$ | 12.73 | 0.56 | 4.45% |
| Starlink phase I-b | 1584 | 24×66 | $53^\circ$ | 13.62 | 0.67 | 4.93% |

**规律**：星座越大，相对误差越小（星链约 5%，多数用户误差不超过 1 跳）。误差来源有二：① 稀疏星座中用户可能只被一颗卫星覆盖，四模式假设不成立；② 式 (6)(9) 的 Round 取整近似（大星座下单星覆盖小、误差更小）。**计算效率**：该方法算全球结果平均仅 **16.2 秒且与卫星数无关**，而仿真需数十到数千分钟。此外对 Walker-Star 星座（如类 OneWeb 648 星）稍加修改也适用，相对误差 <10%。

**2）跳数空间分布（Section IV-B）**。固定 User 1 于 $20^\circ$N，计算与全球 User 2 的跳数。发现跳数**不只取决于球面距离**：User 2 在正北/正南方向所需跳数明显多于东西方向。原因：轨道倾斜使面内 ISL 地面投影呈 SW-NE（或 NW-SE），面间 ISL 呈东西向，南北向用户需要额外面间跳。北半球高纬卫星更密，北向所需中继更多。当 User 1 在 $20^\circ$N 时最大跳数 28，平均 12.21；User 1 升到高纬时最大跳数升至 37。地理距离相近的两点，跳数（及时延）可差 80%。

**3）接入卫星选择的影响（Section IV-C，对问题三最关键之一）**。用户被多星覆盖时，换接入卫星会使跳数剧变。示例（$\varphi_1=30^\circ$N, $\varphi_2=20^\circ$N, $\Delta\lambda=100^\circ$）：User 2 接入升轨时 A2A 仅 9 跳（6 面间+3 面内），换接入降轨则 A2D 需 23 跳（3 面间+20 面内）—— 因升降轨间无直接 ISL，A2D 路径要绕高纬。当 $\Delta\lambda=45^\circ$ 时 D2D 与 D2A 差可达 29 跳。全球最大跳差 **45 跳**，出现在赤道附近（两用户在单星覆盖内但分属升/降轨），此值恰等于 $(N_P+M_P)/2$，即网格网络最大跳距。若用户盲目选接入卫星，平均会面临 10–20 跳的不确定性。**倾斜 LEO 星座的路径变化远大于极轨星座**（后者仅约 1 跳）。

**4）星座参数影响（Section IV-D）**。
- **$N_P$ 与 $M_P$**：即使总星数固定（如 1584），不同分解影响跳数。星链改用 $72\times22$ 版比 $24\times66$ 版平均跳数从 13.62 降到 **11.48（降 15.4%）**。原因：面内卫星变稀后，同样跳数能覆盖更远区域，$N_P/M_P$ 比越大越有利。
- **相位因子 $F$（本文最有价值的可调旋钮）**：$F$ 决定面间 ISL 相位差 $\Delta f$，从而改变面间 ISL 地面走向。$F=12$（$=N_P/2$，即 $\Delta f=\Delta\Phi/2$）时出现以 User 1 为中心的"蝴蝶形"低跳区，平均跳数 12.4，比 $F=0$ 低 **7.53%**。整体上：平均跳数随 $F$ 增大而下降（到 $\approx N_P/2$ 后趋平）；但最大跳数随 $F$ 增大而上升，在 $F\approx-20$ 时最大跳数最低。若更关注最大跳数则宜取负 $F$。**改变 $F$ 不改变网络/图拓扑**，但显著影响跳数，是"低成本可调"的优化手段。
- **美国-欧洲区域案例（Section IV-E）**：美国区 [30°N,50°N]×[125°W,70°W]、欧洲区 [35°N,55°N]×[10°W,30°E]，各撒 100 用户。$F=0$ 时平均跳数 8.99、最大 15，面间 ISL 占 68%。$F=8$ 时平均降到 8.19（降 8.82%）。因欧洲在美国东北方，小正 $F$ 使面间 ISL 也朝东北，方向一致故省跳。区域最优 $F$ 约 5–8。

## 五、对数模题目的启示（问题三·星间链路）

**可复用的公式/方法**：
- **闭式跳数估算（式 6、9、10、11 + Algorithm 1）** 是本文对问题三最直接可用的成果：只需两地纬度和经度差，即可秒算最小 ISL 跳数，**不必对全星座建图跑 Dijkstra/BFS**。这对需要大量端到端评估（全球采样、时延统计）的数模任务极为高效。
- **端到端时延建模**：ISL 跳数 × 单跳时延（单跳传播时延 + 星上处理/排队时延）即可估算端到端 ISL 段时延；再加上/下行星地链路时延即得总时延。本文虽只算跳数、明确不含星地链路，但跳数是时延的主导项，可作为时延模型的骨架。
- **四路径模式取最小（式 16）** 提供了"用户接入卫星选择"的建模范式：把升/降轨接入作为离散决策变量，最优路由取 4 模式最小。
- **对称性（性质 1–3）** 可把二维经纬度输入降到 $(\varphi_1,\varphi_2,\lvert\Delta\lambda\rvert)$，**大幅压缩仿真/计算的参数空间**，便于绘制分布图或做敏感性分析。
- **相位因子 $F$ 优化** 给出一个"改拓扑参数降时延"的优化思路：可将 $F$ 设为决策变量，以平均跳数或最大跳数为目标做优化（本文给出 $F=N_P/2$ 使 $\Delta f=\Delta\Phi/2$ 的经验结论）。

**建模时如何用**：
1. 用星链真实参数（如 $53^\circ$: $24\times66$, phase I-b；或 $72\times22$）代入式 (6)(9) 直接算任意两城市跳数。
2. 端到端时延 = ISL 跳数 × 单跳时延 + 星地上下行时延；单跳传播时延可用相邻卫星几何距离/光速估算。
3. 若题目要求分析拓扑/相位对性能影响，可复现 $F$ 扫描曲线（平均与最大跳数 vs $F$）。
4. 用对称性快速构建全球跳数热力图，定位高时延区域。

**注意事项/局限**：
- 模型基于"接入卫星在用户正上方""每用户同时被升/降轨覆盖"两大近似，**小星座（<数百星）误差偏大**（相对误差可达 15%），星链等大星座才准（约 5%）。
- 只统计 **ISL 跳数，不含星地链路**；也**不直接解路由问题**，只给最小跳数作参考指标。最小跳路径未必是路由/稳定性最优路径。
- 假设升/降轨卫星间不建 ISL —— 若数模题设定 ISL 连接方式不同，需修改模型。
- 结果为准静态（跳数随时间波动小，约 ≤1 跳），若题目强调高动态时变还需补充。

## 六、术语与符号对照

| 英文/符号 | 中文 | 含义 |
|:--|:--|:--|
| Mega-constellation network (MCN) | 巨型星座网络 | 数百上千颗 LEO 卫星组网 |
| Inter-satellite link (ISL) | 星间链路 | 卫星间直接通信链路 |
| Hop-count | 跳数 | 端到端经过的 ISL 中继次数（本文仅指最小值） |
| Walker-Delta | Walker-Delta 星座 | 倾斜轨道均匀星座，记 $\alpha\!:\!N_P M_P/N_P/F$ |
| $N_P$ | 轨道面数 | 星座轨道平面数量 |
| $M_P$ | 每面卫星数 | 每个轨道面内卫星数 |
| $\alpha$ | 轨道倾角 | 相对赤道倾角（度/弧度） |
| $\Delta\Omega=2\pi/N_P$ | RAAN 面间差 | 相邻轨道面升交点赤经之差 |
| $\Delta\Phi=2\pi/M_P$ | 面内相位差 | 同面相邻卫星相位差 |
| $\Delta f=2\pi F/(N_P M_P)$ | 面间相位差 | 相邻面卫星相位偏移 |
| $F$ | 相位因子 | 决定 $\Delta f$，可调优化旋钮，范围 $\{1-N_P,\dots,N_P-1\}$ |
| $\varphi,\lambda$ | 纬度、经度 | 地面用户/星下点坐标 |
| $u$ | 相位角 | 卫星从升交点起算的在轨相位 |
| $L_0$ | 升交点初始经度 | 决定轨道面绝对位置 |
| $\zeta(u)$ | 经度差 | 星下点相对升交点的经度差 |
| $\omega_e$ | 地球自转角速度 | rad/s |
| $H_v,H_h$ | 面内/面间跳数 | 带方向（符号）的两维跳数分量 |
| $H^{X2X}$ | X2X 模式跳数 | X 取 A（升轨）或 D（降轨） |
| $H[(\varphi_1,\lambda_1),(\varphi_2,\lambda_2)]$ | 两地跳数 | 从用户 1 到用户 2 的最小跳数 |
| SSP (sub-satellite point) | 星下点 | 卫星在地面的投影点 |
| Ascending / Descending satellite | 升轨/降轨卫星 | 朝纬度增大/减小方向飞行的卫星 |
| $H_{avg},E_{avg},E_r$ | 平均跳数/绝对误差/相对误差 | 模型验证的三个度量 |
