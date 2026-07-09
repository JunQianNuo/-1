---
title: Akella & Alfriend 2000 · 碰撞概率解析法
source_md: MD/05-碎片鲁棒性(问题四)/Akella_2000_Collision_Probability.md
source_pdf: PDF/05-碎片鲁棒性(问题四)/Akella_2000_Collision_Probability.pdf
subject: 星链数模-参考文献
problem: 问题四·碎片鲁棒性
type: 精读解读
status: AI精读（待校对）
topics:
  - 碰撞概率
  - 交会分析
  - 会合平面
  - 协方差投影
  - 空间碎片规避
---

# Akella & Alfriend 2000 · 碰撞概率解析法（精读解读）

> **一句话总结**：在两体近距离交会的极短时间窗内，把三维的"碎片撞入以航天器为球心、半径 $R$ 的碰撞球"问题，通过"会合平面（conjunction plane）"投影降为二维圆域上的高斯积分，并用两条不同思路（Foster 的最近点法 与 Khutorovsky 的时间积分法）推出**同一个碰撞概率公式**，从而证明两种风险评估方法等价。

## 一、论文速览
- **作者/年份/出处**：Maruthi R. Akella、Kyle T. Alfriend（Texas A&M University），2000，*Journal of Guidance, Control, and Dynamics*，DOI: 10.2514/2.4611。
- **解决的问题**：为国际空间站（ISS）及低轨（LEO）航天器的**碎片规避决策**提供严格的、基于概率的碰撞风险量化方法——即计算一次交会事件的碰撞概率 $\mathcal{P}_c$。取代"会合盒（conjunction box，5 km × 2 km × 2 km）"这类确定性判据（会导致过多不必要的规避机动、浪费燃料、干扰微重力实验）。
- **核心贡献**（3 条）：
  1. 给出 Foster 方法的详细推导：证明在最近接近点（CPA），会合矢量在相对速度方向上的不确定度恒为零，从而三维问题严格降为**二维会合平面内的高斯积分**。
  2. 提出一条**替代但等价**的直接路径（推广 Khutorovsky 方法）：把碰撞视为"随时间演化、穿越碰撞球面的通量事件"，对时间积分得到 $\mathcal{P}_c$，且**不需要**"航天器尺寸远小于碎片位置不确定度"这一限制性假设。
  3. 用一个矩阵求逆恒等式解析地证明两条路径给出**完全相同**的 $\mathcal{P}_c$ 公式，建立不同风险评估方法之间的等价性。
- **方法类型**：解析法（概率密度积分 + 坐标投影 + 线性误差理论）。

## 二、研究背景与动机
低轨航天器长期面临与在轨碎片碰撞的威胁，需要一套能定量评估单次交会风险、并在必要时建议规避机动的方法。

已有做法的不足：
- **确定性会合盒判据**：只要预测交会点落入以航天器为中心的固定尺寸盒（沿飞行方向 5 km、径向与法向各 2 km）就机动。用于 ISS 会触发过多机动；缩小盒子又会把风险抬到不可接受的水平。
- **概率法（Foster, Ref.4）**：把整次交会作为单一事件给出一个 $\mathcal{P}_c$ 值，优雅但为"单值"。
- **时间函数法（Khutorovsky, Ref.5）**：把碰撞概率写成时间的函数，更直接，但**假设主目标（航天器）尺寸相对碎片位置不确定度可忽略**——当航天器（如 ISS）尺寸不可忽略时该假设失效。

本文动机：去掉 Ref.5 的小尺寸假设，把两条路径统一，证明它们给出同一结果。

## 三、核心方法（分章节中文重述）

### 3.1 交会几何与五条简化假设
设 $t=0$ 为估计的最近接近点（CPA，即会合时刻）。ISS 与碎片在 CPA 的标称位置矢量记为 $\bar{r}_{\mathrm{so}}$、$\bar{r}_{\mathrm{do}}$；受扰（真实）轨迹为

$$ \tilde{r}_{\mathrm{so}} = \bar{r}_{\mathrm{so}} + e_s, \qquad \tilde{r}_{\mathrm{do}} = \bar{r}_{\mathrm{do}} + e_d \tag{1} $$

其中 $\bar{r}_{\mathrm{so}}, \bar{r}_{\mathrm{do}}$ 为标称位置矢量（m）；$\tilde{r}_{\mathrm{so}}, \tilde{r}_{\mathrm{do}}$ 为真实（受扰）位置矢量（m）；$e_s, e_d$ 分别为 ISS 与碎片位置矢量的随机不确定性扰动（m）。下标 s = 空间站（station），d = 碎片（debris），o = 会合时刻标称（nominal at conjunction）。

**五条简化假设**（因交会持续仅数秒）：
1. 交会期间两物体标称轨迹可视为**匀速直线**运动；
2. 交会期间**无速度不确定性**（速度误差约几 m/s，时间极短，影响可忽略）；
3. 位置不确定性在交会期间**恒定**，等于会合时刻的值（是假设 2 的直接结果）；
4. 位置不确定性服从**高斯分布**，并把给定的位置协方差当作会合时刻状态不确定性的真实表征；
5. ISS **远大于**入侵碎片，故碎片可当作**质点**（碰撞几何等价于半径 $R$ 的球，$R$ 取 ISS 的等效半径）。

标称轨迹与受扰轨迹（匀速直线）：

$$ \bar{r}_s = \bar{r}_{\mathrm{so}} + v_s t, \quad \bar{r}_d = \bar{r}_{\mathrm{do}} + v_d t \tag{2} $$
$$ \tilde{r}_s(t) = \tilde{r}_{\mathrm{so}} + v_s t, \quad \tilde{r}_d(t) = \tilde{r}_{\mathrm{do}} + v_d t \tag{3} $$

其中 $v_s, v_d$ 为 ISS 与碎片的标称速度矢量（m/s），假设期间恒定。

### 3.2 相对（脱靶）矢量与最近接近时刻
两物体之间的脱靶矢量（miss-vector）：

$$ \tilde{\rho}(t) = \tilde{r}_d(t) - \tilde{r}_s(t) = \bar{\rho}_o + e_d - e_s + v_r t = \tilde{\rho}_o + v_r t \tag{4} $$

配套定义：

$$ \bar{\rho}_o = \bar{r}_{\mathrm{do}} - \bar{r}_{\mathrm{so}}, \qquad v_r = v_d - v_s, \qquad \tilde{\rho}_o = \bar{\rho}_o + e_d - e_s \tag{5} $$

- $\tilde{\rho}(t)$：$t$ 时刻真实相对（脱靶）矢量（m）；
- $\bar{\rho}_o$：会合时刻的**标称脱靶矢量**（m），即最近标称距离方向；
- $v_r = v_d - v_s$：**相对速度矢量**（m/s），交会期间恒定；
- $\tilde{\rho}_o$：把位置误差并入后的会合时刻真实相对矢量（m）。

最近接近点由 $\dfrac{\mathrm{d}}{\mathrm{d}t}(\tilde{\rho}\cdot\tilde{\rho})=0$ 决定，展开得

$$ 2\,\tilde{\rho}_o\cdot v_r + 2(v_r\cdot v_r)\,t = 0 \tag{6} $$

解出最近接近时刻：

$$ t_{\mathrm{cpa}} = -\frac{\tilde{\rho}_o\cdot v_r}{v_r\cdot v_r} \tag{7} $$

即 CPA 时刻等于"真实相对矢量在相对速度方向投影"除以"相对速率平方"取负。当误差为零（$e_d=e_s=0$）时 $\tilde{\rho}_o=\bar{\rho}_o$ 且 $t_{\mathrm{cpa}}=0$，代入 (7) 得到标称几何的正交条件：

$$ \bar{\rho}_o\cdot v_r = 0 \tag{8} $$

即**标称脱靶矢量与相对速度垂直**。

### 3.3 关键结论：相对速度方向上不确定度为零
把 $t_{\mathrm{cpa}}$ 代回，考察最近接近矢量误差在相对速度方向的投影：

$$ \big[\tilde{\rho}(t_{\mathrm{cpa}}) - \bar{\rho}_o\big]\cdot v_r = -\,\bar{\rho}_o\cdot v_r = 0 \tag{9} $$

**物理含义**：在 CPA 时刻，脱靶矢量的不确定性在**相对速度方向（$\hat{i}$ 方向）上分量恒为零**，对所有受扰轨迹都成立。于是全部位置不确定性都被限制在与 $v_r$ 垂直的平面内——这正是把三维问题降为二维的关键。

### 3.4 会合平面坐标系
用两物体速度构造正交坐标系（Foster 定义）：

$$ \hat{i} = \frac{v_r}{|v_r|}, \qquad \hat{j} = \frac{v_d\times v_s}{|v_d\times v_s|}, \qquad \hat{k} = \hat{i}\times\hat{j} \tag{10} $$

- $\hat{i}$：沿相对速度方向的单位矢量；
- $\hat{j}$：垂直于两速度所张平面的单位矢量；
- $\hat{k}$：由右手系补全。

$\hat{j}\text{-}\hat{k}$ 平面即**会合平面（conjunction plane）**。由于 $\bar{\rho}_o$ 在 $\hat{i}$ 方向无分量、且不确定度在 $\hat{i}$ 方向为零，问题完全落在会合平面上；ISS 球在该平面上投影为半径 $R$ 的圆。

存在正交变换矩阵 $C$（$CC^T=C^TC=I$）把原坐标 $(\hat{e}_1,\hat{e}_2,\hat{e}_3)$ 映到 $(\hat{i},\hat{j},\hat{k})$：

$$ \begin{Bmatrix}\hat{i}\\\hat{j}\\\hat{k}\end{Bmatrix} = C\begin{Bmatrix}\hat{e}_1\\\hat{e}_2\\\hat{e}_3\end{Bmatrix}, \qquad CC^T=C^TC=I \tag{11} $$

### 3.5 不确定度在会合平面的分量与协方差投影
CPA 处误差在三个新方向的投影：

$$ \alpha(t_{\mathrm{cpa}}) = (e_d-e_s)\cdot\hat{j}, \qquad \beta(t_{\mathrm{cpa}}) = (e_d-e_s)\cdot\hat{k}, \qquad \gamma(t_{\mathrm{cpa}}) = 0 \tag{15,16} $$

（$\gamma=0$ 正是式 (9) 的另一种表述。）用 $C$ 展开可写成矩阵形式

$$ \begin{Bmatrix}\alpha\\\beta\end{Bmatrix} = T\begin{Bmatrix}e_s\\e_d\end{Bmatrix}, \qquad T = T^*\begin{bmatrix}-C & C\end{bmatrix}, \qquad T^* = \begin{bmatrix}0&1&0\\0&0&1\end{bmatrix} \tag{17,18} $$

其中 $\alpha,\beta$ 是脱靶不确定度在会合平面 $\hat{j},\hat{k}$ 两轴上的分量（m）；$T^*$ 起"丢弃 $\hat{i}$ 分量、只保留平面内两维"的作用。

设 $P_s, P_d$ 为 ISS 与碎片的 $3\times3$ 位置协方差矩阵（m²），由线性误差理论，投影到会合平面的 $2\times2$ 协方差为

$$ P^* = T\begin{bmatrix}P_s&0\\0&P_d\end{bmatrix}T^T \tag{19} $$

其中 $P^*$ 为会合平面内 $(\alpha,\beta)$ 的 $2\times2$ 联合协方差（m²）；块对角结构假设 ISS 与碎片的误差相互独立。

### 3.6 Foster 的碰撞概率公式（二维圆域积分）
由于 $\hat{i}$ 方向无不确定度，Foster 把整次交会碰撞概率写为会合平面内半径 $R$ 圆域上的二维高斯积分：

$$ \mathcal{P}_c = \frac{1}{2\pi|P^*|^{1/2}}\int_{-R}^{R}\int_{-\sqrt{R^2-y^2}}^{\sqrt{R^2-y^2}}\exp(-S^*)\,\mathrm{d}z\,\mathrm{d}y \tag{20} $$

$$ S^* = \frac{1}{2}\big(\tilde{\rho}^*-\bar{\rho}_o^*\big)^T P^{*-1}\big(\tilde{\rho}^*-\bar{\rho}_o^*\big), \qquad \tilde{\rho}^* = T^*C\tilde{\rho}, \quad \bar{\rho}_o^* = T^*C\bar{\rho}_o \tag{21,22} $$

- $R$：ISS 碰撞球半径（碎片视为质点后的合并半径，m）；
- $|P^*|$：二维协方差行列式（m⁴），$1/(2\pi|P^*|^{1/2})$ 为二维高斯归一化常数；
- $S^*$：会合平面内的马氏距离平方的一半（无量纲）；
- $\bar{\rho}_o^*$：标称脱靶矢量在会合平面内的二维投影（m），即高斯分布的中心相对圆心的偏移。
- 积分区域是会合平面内以圆心为参考、半径 $R$ 的圆盘——**几何意义即"脱靶点落在碰撞圆内的概率"**。

### 3.7 替代路径：时间通量积分法（推广 Khutorovsky）
不用"最近点"概念，而把碰撞看作**碎片穿越 ISS 球面的通量事件**。会合平面坐标系下相对运动的三维协方差为

$$ P = \begin{bmatrix}-C & C\end{bmatrix}\begin{bmatrix}P_s&0\\0&P_d\end{bmatrix}\begin{bmatrix}-C^T\\C^T\end{bmatrix} \tag{23} $$

$t$ 时刻相对运动的概率密度：

$$ p[\tilde{\rho}(t),t] = \frac{1}{(2\pi)^{3/2}|P|^{1/2}}\exp(-S), \qquad S = \frac{1}{2}(\tilde{\rho}-\bar{\rho}_o)^T P^{-1}(\tilde{\rho}-\bar{\rho}_o) \tag{24,25} $$

**核心几何洞察**：对球形碰撞体，每条穿入球体的轨迹此后必有一个落在球内的 CPA；每条穿出球体的轨迹此前也已有球内 CPA。故"对所有在球内取得 CPA 的事件求系综平均"与"对所有进入/离开碰撞球的轨迹求系综平均"**几何与数学上等价**（此结论仅对球形体成立）。

在 $(t, t+\mathrm{d}t)$ 内穿过球面 dA* 面元的条件碰撞概率，配合通量项 $v_r\cdot n\,\mathrm{d}A^* = v_r\,\mathrm{d}y\,\mathrm{d}z$（$n$ 为面元外法向），对时间积分得整次交会概率：

$$ \mathcal{P}_c = \frac{v_r}{(2\pi)^{3/2}|P|^{1/2}}\int_{-\infty}^{\infty}\!\int_{c}\exp(-S)\,\mathrm{d}y\,\mathrm{d}z\,\mathrm{d}t \tag{28} $$

其中 $v_r=|v_r|$ 为相对速率（m/s）；内层对圆盘 $c$（半径 $R$）积分，外层对时间从 $-\infty$ 到 $\infty$。

### 3.8 两式等价性证明（矩阵求逆恒等式）
记 $u = \tilde{\rho}(t)-\bar{\rho}_o$（随时间线性变化）、$v = [\alpha,\beta]^T$（与时间无关）。把三维协方差按会合平面分块

$$ P = \begin{bmatrix}\eta^2 & w^T\\ w & P^*\end{bmatrix}, \qquad \eta\in\mathcal{R},\ w\in\mathcal{R}^2 \tag{33} $$

利用求逆恒等式（可由 Junkins–Kim 矩阵求逆引理导出，对任意 $n\times n$ 对称正定阵成立）

$$ P^{-1} = \begin{bmatrix}0&0\\0&P^{*-1}\end{bmatrix} + \frac{|P^*|}{|P|}\begin{bmatrix}1 & -w^T P^{*-1}\\ -P^{*-1}w & P^{*-1}ww^T P^{*-1}\end{bmatrix} \tag{34} $$

可把二次型分解为

$$ u^T P^{-1} u = v^T P^{*-1} v + \frac{|P^*|}{|P|}u^T[\cdots]u \tag{35} $$

再用高斯积分 $\int_{-\infty}^{\infty}\exp(-\tfrac{1}{2}\lambda^2)\,\mathrm{d}\lambda=\sqrt{2\pi}$ 完成对时间的积分，即证得

$$ \int_{-\infty}^{\infty}\exp\!\Big(-\tfrac{1}{2}u^T P^{-1}u\Big)\mathrm{d}t = \frac{\sqrt{2\pi}}{v_r}\sqrt{\frac{|P|}{|P^*|}}\exp\!\Big(-\tfrac{1}{2}v^T P^{*-1}v\Big) \tag{32} $$

代回 (28) 便还原出 (20)，从而**证明两条路径给出同一个 $\mathcal{P}_c$**。

## 四、关键结论与结果
- **降维核心**：在 CPA 时刻脱靶不确定度沿相对速度方向恒为零（式 9），三维碰撞概率严格化为**会合平面内半径 $R$ 圆域上的二维高斯积分**（式 20）。
- **两法等价**：Foster 的"最近点系综"法 与 推广 Khutorovsky 的"时间通量积分"法给出**完全相同**的公式，用矩阵求逆恒等式解析证明（式 32–36）。
- **去除限制假设**：新路径不需要"航天器尺寸远小于碎片不确定度"的假设，适用于 ISS 这类尺寸不可忽略的目标。
- **适用范围与局限**：仅严格适用于**球形碰撞体**；依赖匀速直线、无速度误差、位置误差高斯且协方差已知等假设；结果对所设位置协方差高度敏感（式 20 的 $\mathcal{P}_c$ 强烈依赖 $P_s,P_d$ 的取值）。本文不涉及协方差本身的估计误差。

## 五、对数模题目的启示（问题四·碎片鲁棒性）
- **可直接复用的公式/方法**：
  - **二维碰撞概率积分（式 20）** 是本领域标准结果，可直接用于星链任一卫星与某碎片一次交会的碰撞概率计算：只需三样输入——相对几何（标称脱靶矢量 $\bar{\rho}_o$ 及其在会合平面内投影 $\bar{\rho}_o^*$）、合并半径 $R$、会合平面协方差 $P^*$。
  - **会合平面构造（式 10）+ 协方差投影（式 17–19）** 给出从三维状态协方差 $P_s,P_d$ 到二维 $P^*$ 的完整流程，是把 TLE/星历不确定度转成碰撞概率的关键中间步骤。
  - **CPA 时刻公式（式 7）** 可用于筛查：先算最近接近距离与时刻，只对 $\mathcal{P}_c$ 超阈值的交会做规避。
- **建模时如何用**：
  - 问题四要评估"碎片环境下星座的鲁棒性"，可把每颗星与碎片编目做两两交会筛查，用式 20 累加得到**单星单次/单日碰撞概率**，再对全星座、全时段求和/取期望，作为鲁棒性指标（如期望碰撞次数、需机动次数）。
  - 合并半径取 $R = R_{\text{卫星}} + R_{\text{碎片}}$（把碎片尺寸并入球半径），协方差 $P^*$ 由两者位置误差合成。
  - 阈值 $\mathcal{P}_c$（如 $10^{-4}$、$10^{-5}$）可作为触发规避机动的判据，用于评估"机动次数—燃料消耗—碰撞风险"的权衡，正对应问题四的鲁棒性/代价分析。
- **注意事项/局限**：
  - 假设交会仅数秒、匀速直线——对星链低轨高相对速度交会成立，但对慢速接近或长时窗需另作处理。
  - 结果对协方差敏感；若碎片轨道误差大，$\mathcal{P}_c$ 会被显著放大，建模时应做**协方差敏感性分析**。
  - 仅对球形碰撞几何严格成立；卫星按等效球半径近似即可。
  - 式 20 的二维积分无解析闭式，需数值积分（如极坐标或级数展开）实现。

## 六、术语与符号对照
| 英文/符号 | 中文 | 含义 |
|:--|:--|:--|
| $\mathcal{P}_c$ | 碰撞概率 | 一次交会内碎片撞入碰撞球的概率 |
| CPA (closest point of approach) | 最近接近点/时刻 | 两物体距离最小的时刻，取为 $t=0$ |
| conjunction plane | 会合平面 | 垂直于相对速度、含全部位置不确定度的二维平面（$\hat{j}\text{-}\hat{k}$） |
| conjunction box | 会合盒 | 确定性判据用的固定尺寸盒（5 km × 2 km × 2 km） |
| miss-vector $\tilde{\rho}$ | 脱靶矢量/相对位置矢量 | 碎片相对 ISS 的位置矢量 |
| $\bar{\rho}_o$ | 标称脱靶矢量 | 会合时刻标称相对位置矢量 |
| $v_r = v_d - v_s$ | 相对速度矢量 | 碎片相对 ISS 的速度，交会期间恒定 |
| $e_s, e_d$ | 位置不确定扰动 | ISS、碎片位置误差（高斯） |
| $P_s, P_d$ | 位置协方差矩阵 | ISS、碎片的 $3\times3$ 位置协方差 |
| $P^*$ | 会合平面协方差 | 投影到二维会合平面的 $2\times2$ 协方差 |
| $R$ | 碰撞球半径 | ISS 等效半径（碎片视为质点后并入的合并半径） |
| $C$ | 正交变换矩阵 | 原坐标系到会合平面坐标系的旋转 |
| $\hat{i},\hat{j},\hat{k}$ | 会合坐标基 | 相对速度方向及会合平面两轴 |
| ISS | 国际空间站 | 主目标航天器（可推广到任一在轨资产） |
| LEO | 低地球轨道 | 碎片威胁主要区域 |
