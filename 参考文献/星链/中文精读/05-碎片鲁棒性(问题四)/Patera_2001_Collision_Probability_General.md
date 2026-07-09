---
title: Patera 2001 · 碰撞概率通用算法
source_md: MD/05-碎片鲁棒性(问题四)/Patera_2001_Collision_Probability_General.md
source_pdf: PDF/05-碎片鲁棒性(问题四)/Patera_2001_Collision_Probability_General.pdf
subject: 星链数模-参考文献
problem: 问题四·碎片鲁棒性
type: 精读解读
status: AI精读（待校对）
topics:
  - 碰撞概率
  - 短时交会
  - 降维路径积分
  - 硬体（hard body）
  - 误差协方差
---

# Patera 2001 · 碰撞概率通用算法（精读解读）

> **一句话总结**：本文把两颗在轨物体在最接近点（短时交会）的三维碰撞概率，通过"合并协方差 → 投影到交会平面 → 旋转+缩放使密度对称 → 面积分降维成沿硬体边界的一维闭合路径积分"这条链路，化为只含标量指数函数的绕行积分，从而高效、无简化假设地计算碰撞概率，并且天然支持非球形（不规则）物体。

## 一、论文速览
- **作者/年份/出处**：Russell P. Patera（The Aerospace Corporation），2001 年，*Journal of Guidance, Control, and Dynamics*，DOI: 10.2514/2.4771。
- **解决的问题**：给定两个在轨物体在最接近点（TCA）附近的状态向量与误差协方差矩阵，计算它们发生碰撞的概率。
- **核心贡献**（4 条）：
  1. 提出一个**通用**的碰撞概率计算方法，不需要任何简化假设（如误差函数近似、密度均匀近似等）。
  2. 用解析变换把交会平面上的**二维面积分降维为一维路径积分**，被积函数仅为一个简单指数，数值实现容易、计算量小（比当时业务代码快约 20 倍）。
  3. 该方法天然适用于**非球形/不规则形状**物体（如带大太阳能帆板的卫星、细长的运载火箭），只需定义投影多边形的边界即可积分。
  4. 由此可评估卫星/附件**姿态朝向对碰撞概率的影响**，为"通过改变姿态而非机动规避"提供定量依据。
- **方法类型**：解析降维 + 数值路径积分（半解析法）。

## 二、研究背景与动机
随着在轨物体数量增加，卫星与空间碎片/其他卫星碰撞的风险上升。传统的规避准则是"保持隔离体积"（keep-out volume，例如航天飞机采用以轨道器为中心的 $5\times2\times2$ km 禁飞盒）。这种准则的缺点是**不能量化碰撞风险**——无法把碰撞风险与"执行规避机动本身带来的风险"做权衡。要量化风险，就必须用到每个物体状态向量的精度信息，即**误差协方差矩阵**。

已有工作的脉络与不足：
- Chan 证明：只要在同一坐标系下表示，两个物体的误差协方差矩阵可**直接相加**得到相对协方差矩阵，对应一个描述相对位置不确定性的三维概率密度。
- 由于交会时相对速度极大、相对加速度可忽略，可沿相对速度方向积分，把三维问题**降到二维**（交会平面）。
- 若假设物体为球形，碰撞概率化为在交会平面上一个圆形区域上的二维积分。
- Alfriend 等、Chan、LeClair 等曾用**误差函数（error function）**把二维积分再"人为"降到一维，但误差函数本身也是积分，且在"相对间距 > 密度标准差"的区域**收敛很慢**，导致数值误差大、计算迟缓。
- 因此实际业务中仍靠**直接二维数值积分**求解。

本文动机：给出一个**无简化假设、又快又准**的方法，把二维积分变成一维、被积函数只含简单指数，且能处理任意形状。

## 三、核心方法（分章节中文重述）

### 3.1 问题建立：从三维高斯到交会平面二维高斯
相对位置不确定性用三维高斯分布描述：
$$
\rho(\boldsymbol{x}) = \frac{1}{(2\pi)^{3/2}\sigma_x\sigma_y\sigma_z}\exp\!\left[-\frac{x^2}{2\sigma_x^2}-\frac{y^2}{2\sigma_y^2}-\frac{z^2}{2\sigma_z^2}\right]
$$
其中 $\rho$ 是三维概率密度函数（单位：体积$^{-1}$）；$x,y,z$ 是（对角化后的）相对位置坐标（单位 m）；$\sigma_x,\sigma_y,\sigma_z$ 是各主轴方向的位置标准差（单位 m），由合并后的相对协方差矩阵对角化得到。

因交会时相对速度可视为常量，把相对速度方向取为 $Z$ 轴并沿该方向积分，三维高斯就退化为交会平面上的二维高斯：
$$
h(\boldsymbol{x}) = \frac{1}{2^{3/2}\pi\,\sigma_x\sigma_y\sigma_z\sqrt{a}}\exp\!\left[-e x^2 - f y^2 - g x y\right]
$$
其中 $h$ 是**单位面积的碰撞概率密度**（交会平面上，单位：面积$^{-1}$）；$x,y$ 是交会平面内的坐标（单位 m）；$a,e,f,g$ 是由变换矩阵和标准差组合出来的辅助系数（见下）；$gxy$ 为交叉项，表示二维高斯的椭圆主轴尚未与坐标轴对齐。

交会坐标系与定义密度的坐标系通过正交变换矩阵 $U$ 相联系：
$$
\boldsymbol{x}_{\text{sigma}} = U\,\boldsymbol{x}_{\text{encounter}}
$$
其中 $U$ 是从"交会系"到"对角（sigma）系"的变换矩阵，$U_{ij}$ 为其元素（$i,j=1,2,3$）。

系数定义（均由 $U$ 的元素与 $\sigma_x,\sigma_y,\sigma_z$ 组成）：
$$
a = \frac{U_{13}^2}{2\sigma_x^2}+\frac{U_{23}^2}{2\sigma_y^2}+\frac{U_{33}^2}{2\sigma_z^2}
$$
$$
e = \frac{U_{11}^2}{2\sigma_x^2}+\frac{U_{21}^2}{2\sigma_y^2}+\frac{U_{31}^2}{2\sigma_z^2}-\frac{c^2}{4a},\qquad
f = \frac{U_{12}^2}{2\sigma_x^2}+\frac{U_{22}^2}{2\sigma_y^2}+\frac{U_{32}^2}{2\sigma_z^2}-\frac{d^2}{4a}
$$
$$
g = \frac{U_{11}U_{12}}{\sigma_x^2}+\frac{U_{21}U_{22}}{\sigma_y^2}+\frac{U_{31}U_{32}}{\sigma_z^2}-\frac{cd}{2a}
$$
其中辅助量
$$
c = \frac{U_{11}U_{13}}{\sigma_x^2}+\frac{U_{21}U_{23}}{\sigma_y^2}+\frac{U_{31}U_{33}}{\sigma_z^2},\qquad
d = \frac{U_{12}U_{13}}{\sigma_x^2}+\frac{U_{22}U_{23}}{\sigma_y^2}+\frac{U_{32}U_{33}}{\sigma_z^2}
$$
- $a$：与相对速度方向（第 3 列，被积掉的那一维）相关的系数，出现在归一化因子中；
- $c,d$：由沿速度方向那一维带来的交叉贡献，$e,f$ 中减去的 $c^2/4a$、$d^2/4a$ 正是"沿 $Z$ 积分消元"的结果；
- $e,f$：二维高斯在 $x^2,y^2$ 上的系数，越大表示该方向不确定性越小（分布越窄）。

### 3.2 碰撞概率的基本表达式（硬体圆 + 阶跃函数）
把两个球合并成一个等效"硬体球"（半径 = 两球半径之和 $s$），投影到交会平面得到**硬体圆**（碰撞截面）。硬体圆圆心在相对位移向量 $\boldsymbol{q}$（第二个物体在交会系中相对第一个物体的位置，无不确定性——所有不确定性都归到了原点处的第一个物体）。用阶跃函数 $u(\boldsymbol{x}-\boldsymbol{q})$ 圈出硬体圆（圆内取 1、圆外取 0），碰撞概率为密度在硬体圆上的积分：
$$
\mathrm{prob} = \iint h(\boldsymbol{x})\,u(\boldsymbol{x}-\boldsymbol{q})\,\mathrm{d}\boldsymbol{x}
$$
其中 $\boldsymbol{q}$ 是最接近点相对位置向量转到交会系后的向量（即脱靶量/碰撞碰撞参数，单位 m）；$s$ 为合并硬体半径（单位 m）。该式与其他学者的表达式等价，通常靠二维数值积分求解——本文的贡献就是把它降维。

### 3.3 旋转消交叉项 + 缩放使密度对称
**第一步：坐标旋转**消掉交叉项 $gxy$，得到主轴对齐的对称高斯：
$$
h(\boldsymbol{x}) = \frac{1}{2^{3/2}\pi\,\sigma_x\sigma_y\sigma_z\sqrt{a}}\exp\!\left[-\alpha x^2 - \beta y^2\right]
$$
$$
\alpha = \frac{e+f}{2}-\frac{\sqrt{g^2+(f-e)^2}}{2},\qquad
\beta = \frac{e+f}{2}+\frac{\sqrt{g^2+(f-e)^2}}{2}
$$
其中 $\alpha,\beta$ 是对角化后 $x^2,y^2$ 上的系数（$\alpha,\beta>0$，$\alpha\le\beta$），即二维高斯两个主轴方向的"陡度"。旋转把 $\boldsymbol{q}$ 变为 $\boldsymbol{q}_r=T\boldsymbol{q}$，旋转矩阵
$$
T = \begin{bmatrix}\cos\phi & \sin\phi\\ -\sin\phi & \cos\phi\end{bmatrix},\quad
\cos\phi = \sqrt{\tfrac{1}{2}\!\left[1-\tfrac{f-e}{\sqrt{g^2+(f-e)^2}}\right]},\quad
\sin\phi = \pm\sqrt{\tfrac{1}{2}\!\left[1+\tfrac{f-e}{\sqrt{g^2+(f-e)^2}}\right]}
$$
其中 $\phi$ 是消除交叉项所需的旋转角；$\sin\phi$ 的符号由"使交叉项为零"的条件 $2(f-e)\sin\phi\cos\phi+g[\cos^2\phi-\sin^2\phi]=0$ 确定。

**第二步：$y$ 轴缩放**使密度各向同性（把椭圆等高线变成圆形密度）：令 $y=\sqrt{\alpha/\beta}\,y'$，得
$$
h(\boldsymbol{x}) = \frac{\sqrt{\alpha}}{2^{3/2}\pi\,\sigma_x\sigma_y\sigma_z\sqrt{a\beta}}\exp\!\left[-\alpha x^2 - \alpha y'^2\right]
$$
相应地，$\boldsymbol{q}_r$ 的 $y$ 分量按同一因子缩放：$q_{rs}(2)=\sqrt{\beta/\alpha}\,q_r(2)$；硬体圆随之变成椭圆
$$
\left(\frac{x}{s}\right)^2 + \left(\frac{y}{s}\right)^2\frac{\alpha}{\beta} = 1
$$
其中 $s$ 是初始合并硬体半径。**关键**：缩放让密度变对称，代价是硬体区域从圆变成椭圆——但硬体边界依然容易参数化，这正是后续降维的前提。

### 3.4 面积分降维为一维路径（绕行）积分
把对称密度代入概率式并转极坐标（$r,\theta$），因密度对称，对 $r$ 的积分可**立即解析完成**：
$$
\mathrm{prob} = \frac{\sqrt{\alpha}}{2^{3/2}\pi\,\sigma_x\sigma_y\sigma_z\sqrt{a\beta}}\iint_{\text{ellipse}}\exp(-\alpha r^2)\,r\,\mathrm{d}r\,\mathrm{d}\theta
$$
对 $r$ 积分后剩下沿边界 $\theta$ 的积分（$s_1,s_2$ 为硬体椭圆的两段边界轮廓）：
$$
\mathrm{prob} = \frac{1}{4\sqrt{2}\,\pi\,\sigma_x\sigma_y\sigma_z\sqrt{a\beta\alpha}}\left(\int_{s_2}\exp(-\alpha r^2)\,\mathrm{d}\theta - \int_{s_1}\exp(-\alpha r^2)\,\mathrm{d}\theta\right)
$$
两段轮廓可合并为绕硬体椭圆一圈的**闭合路径积分**（负号表示逆时针绕行）：
$$
\mathrm{prob} = \frac{-1}{4\sqrt{2}\,\pi\,\sigma_x\sigma_y\sigma_z\sqrt{a\beta\alpha}}\oint_{\text{ellipse}}\exp(-\alpha r^2)\,\mathrm{d}\theta
$$
化简系数后得到本文最优美的结论——**碰撞概率只是绕硬体边界的一个标量指数积分**：
$$
\boxed{\ \mathrm{prob} = \frac{-1}{2\pi}\oint_{\text{ellipse}}\exp(-\alpha r^2)\,\mathrm{d}\theta\ }\qquad(\text{原点在硬体外})
$$
$$
\mathrm{prob} = 1 - \frac{1}{2\pi}\oint_{\text{ellipse}}\exp(-\alpha r^2)\,\mathrm{d}\theta\qquad(\text{原点在硬体内})
$$
其中 $r$ 是硬体边界上一点到原点（密度中心）的距离；$\alpha$ 为对称化后的密度陡度系数；$\theta$ 为绕行角度参数。**两种情形的区别**：若密度中心（原点）落在硬体椭圆内部，路径积分会绕原点包一个无穷小圆、额外贡献 $2\pi$，故用 (26b) 的"$1-\cdots$"形式（此时碰撞概率接近 1）。

> 直观理解：原本要在整个圆面上做二维积分（$\sim$ 面积 $\propto$ 步数），现在只需沿周长走一圈（$\sim$ 周长 $\propto \sqrt{\text{面积}}$），被积函数还只是一个 $\exp$。这就是"少一维、快一截"的来源。

### 3.5 数值实现（对称情形）
在单位圆上取初始点 $X=(1,0)$，用无穷小旋转矩阵推进：$X'=RX$，
$$
R = \begin{bmatrix}\cos\varepsilon & -\sin\varepsilon\\ \sin\varepsilon & \cos\varepsilon\end{bmatrix}
$$
其中 $\varepsilon$ 是绕硬体椭圆推进的小角步长。两点各乘缩放矩阵 $M$ 映到硬体椭圆：
$$
\boldsymbol{X}_m' = M\boldsymbol{X}',\quad \boldsymbol{X}_m = M\boldsymbol{X},\qquad
M = \begin{bmatrix}s & 0\\ 0 & s\sqrt{\beta/\alpha}\end{bmatrix}
$$
再加上位移向量得到边界点到原点的向量 $\boldsymbol{X}_e' = \boldsymbol{X}_m' + [q_r(1),\,q_{rs}(2)]^{\mathsf T}$（$\boldsymbol{X}_e$ 同理）。相邻两向量的夹角 $\mathrm{d}\theta$ 由叉积求出：
$$
\mathrm{d}\theta = \sin^{-1}\!\left(\frac{\boldsymbol{X}_e\times\boldsymbol{X}_e'}{|\boldsymbol{X}_e|\,|\boldsymbol{X}_e'|}\right)
$$
被积函数在两向量中点处取值：
$$
\mathrm{int} = \exp\!\left\{-\alpha\left[(X_e+X_e')/2\right]^2\right\}
$$
累加 $\mathrm{sum}\leftarrow\mathrm{sum}+(\mathrm{int})(\mathrm{d}\theta)$，绕椭圆一整圈后：
$$
\mathrm{prob} = -\mathrm{sum}/2\pi\ (\text{原点在硬体外}),\qquad \mathrm{prob} = 1-\mathrm{sum}/2\pi\ (\text{原点在硬体内})
$$
其中 $\boldsymbol{X}_e,\boldsymbol{X}_e'$ 为硬体边界上相邻两点相对原点的位置向量；$s$ 为硬体半径；$q_r(1),q_{rs}(2)$ 为旋转+缩放后位移向量的两个分量。

### 3.6 推广到非对称（不规则）物体
把主物体真实几何用一组网格点（构成一系列多边形、围成封闭曲面）表示。为把"两物体的合并硬体"表达出来，将每个网格点按次物体半径向外扩张（次物体仍设为球形，因其姿态多未知）。然后把封闭曲面投影到交会平面，**只保留逆时针环绕的那一半多边形**（相当于取朝向观察者的面）。同样做旋转+缩放对称化，对每个投影多边形做逆时针路径积分并求和：
$$
\mathrm{prob} = \sum_i \mathrm{prob}_i
$$
每个多边形的贡献与对称情形同形（原点在外/在内两式）：
$$
\mathrm{prob}_i = \frac{-1}{2\pi}\oint_{\text{polygon}}\exp(-\alpha r^2)\,\mathrm{d}\theta\quad\text{或}\quad \mathrm{prob}_i = 1-\frac{1}{2\pi}\oint_{\text{polygon}}\exp(-\alpha r^2)\,\mathrm{d}\theta
$$
数值上，在相邻顶点 $\mathbf{x}_1,\mathbf{x}_2$ 之间用 $J$ 步线性插值出一串点：
$$
X_n' = \frac{\mathbf{x}_2(n)+\mathbf{x}_1(J-n-1)}{J-1},\qquad
X_n = \frac{\mathbf{x}_2(n-1)+\mathbf{x}_1(J-n)}{J-1}
$$
其中 $J$ 为两顶点间的积分步数；$n$ 从 1 到 $J-1$ 时两向量从 $\mathbf{x}_1$ 移到 $\mathbf{x}_2$。其余（叉积求 $\mathrm{d}\theta$、中点取 $\exp$、累加）与对称情形一致。

## 四、关键结论与结果
- **精度**：对 26 个真实交会算例（运载火箭 200 m 隔离半径 vs 编目空间物体），本文模型与业务软件 PERFCT option 5（基于 NASA 模型、做二维数值积分，等价于式 (10)）**差异 < 1%**，覆盖很宽的物体尺寸与协方差范围（见 Table 1，碰撞概率量级约 $10^{-6}\sim10^{-4}$）。
- **速度**：在 Sun Ultra 60（360 MHz）上，跑 1000/10000 次评估，本文模型 0.99/10.12 s，PERFCT option 5 为 5.60/57.52 s，约**快 5.7 倍**；把积分步数从 400 降到 27（周长 $\propto\sqrt{\text{面积}}$，故 $\sqrt{400}\approx27$ 步以公平对比）后，精度几乎不降（0.001792 → 0.001791，对照 0.00193），CPU 时间降到 0.26 s，**约快 21 倍**。
- **形状效应**：把火箭建成 $200\times35\times35$ m 长方体（仅需 8 个顶点）后，多数算例的碰撞概率**显著降低**（分数缩减 0.15~0.9，Table 2）；但当次物体（碎片）尺寸远大于主物体时，由于网格点扩张方式保守，非对称模型反而可能**高估**概率（缩减因子 >1，如 1.5~1.8）。
- **适用范围与局限**：面向**短时交会**（相对速度远大于相对加速度、速度可视为常量）；次物体默认球形；当次物体远大于主物体时建议两者都当球形以免保守偏差。

## 五、对数模题目的启示（问题四·碎片鲁棒性）
- **可复用的公式/方法**：
  - **合并协方差 → 交会平面二维高斯 → 硬体圆上二维积分**（式 1、2、10）是碰撞概率的标准骨架，可直接用于评估星链卫星与碎片的单次交会碰撞概率。
  - **降维路径积分**（式 25、26）给出一个又快又准、无近似假设的算法，特别适合"要对海量交会事件批量算概率"的场景（星链上万颗卫星 × 大量碎片 → 海量交会对），计算效率是关键卖点。
  - **累加式数值实现**（式 27–37）是可以直接照抄成代码的伪流程（旋转推进 + 叉积求角 + 中点取值 + 求和）。
- **建模时如何用**：
  - 用"三倍标准差误差椭球是否重叠"作为**粗筛准则**先剔除不可能碰撞的碎片，再对候选者算概率——正好对应问题四"在大量碎片中识别高风险者"的分层思路。
  - 硬体半径 $s$ = 卫星等效半径 + 碎片等效半径；脱靶量 $\boldsymbol{q}$ = 最接近点相对位置。把星链单星尺寸、碎片 RCS 折算半径代入即可。
  - **鲁棒性视角**：本文指出可通过**调整卫星/帆板姿态**降低碰撞概率（式 38 的多边形投影法能定量比较不同朝向），这为"不做规避机动、仅靠姿态调整提升碎片鲁棒性"提供了可量化的建模抓手。
  - 可把单次碰撞概率沿任务周期/全星座累加，评估整体碰撞风险与鲁棒性指标。
- **注意事项/局限**：
  - 方法仅对**短时交会**成立；若相对速度不大（如同轨道近距离长期伴飞），速度常量假设失效，需改用其他方法。
  - 非对称建模里网格点向外扩张是**保守近似**，次物体（碎片）比主物体大很多时会高估概率，需谨慎或退回球形假设。
  - 结果强依赖协方差矩阵质量；星链场景若拿不到真实协方差，需要合理假定并做敏感性分析。

## 六、术语与符号对照
| 英文/符号 | 中文 | 含义 |
|:--|:--|:--|
| encounter frame | 交会（坐标）系 | 以相对速度方向为一轴的坐标系，垂直于速度的平面即交会平面 |
| hard body / hard-body circle | 硬体 / 硬体圆 | 两物体半径之和构成的等效碰撞体，投影到交会平面成圆（或椭圆/多边形） |
| miss distance / $\boldsymbol{q}$ | 脱靶量 / 相对位移 | 最接近点两物体相对位置向量（碰撞碰撞参数） |
| covariance matrix | 协方差矩阵 | 描述状态向量精度的不确定性矩阵；两物体相加得相对协方差 |
| $\rho(\boldsymbol{x})$ | 三维概率密度 | 相对位置不确定性的三维高斯分布 |
| $h(\boldsymbol{x})$ | 二维概率密度 | 沿速度方向积分后交会平面上的单位面积碰撞概率密度 |
| $\sigma_{x,y,z}$ | 各轴标准差 | 对角化后各主轴方向的位置标准差（m） |
| $U$ | 变换矩阵 | 交会系到对角（sigma）系的正交变换，元素 $U_{ij}$ |
| $a,c,d,e,f,g$ | 辅助系数 | 由 $U$ 与 $\sigma$ 组合出的中间参数；$g$ 为交叉项系数 |
| $\alpha,\beta$ | 密度陡度系数 | 对角化后 $x^2,y^2$ 项系数（主轴方向的窄陡程度） |
| $\phi$ | 旋转角 | 消除交叉项 $gxy$ 所需的坐标旋转角 |
| $T,R,M$ | 旋转/推进/缩放矩阵 | $T$ 旋转位移向量、$R$ 数值积分小角推进、$M$ 缩放到硬体椭圆 |
| $s$ | 硬体半径 | 两物体半径之和（m） |
| $\varepsilon$ | 小角步长 | 沿硬体边界数值推进的角步长 |
| $\theta$ / $\mathrm{d}\theta$ | 积分角 / 角增量 | 路径积分的角度参数，由相邻向量叉积求得 |
| $J,n$ | 步数 / 步索引 | 非对称情形两顶点间的插值步数及索引 |
| prob / sum / int | 概率 / 累加和 / 被积值 | 数值实现中的三个累加量 |
| RCS | 雷达散射截面 | 用于折算空间物体等效半径 |
