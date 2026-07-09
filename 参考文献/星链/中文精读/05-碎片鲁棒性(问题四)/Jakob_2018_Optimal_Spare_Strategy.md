---
title: Jakob & Ho 2018 · 多级库存备份策略
source_md: MD/05-碎片鲁棒性(问题四)/Jakob_2018_Optimal_Spare_Strategy.md
source_pdf: PDF/05-碎片鲁棒性(问题四)/Jakob_2018_Optimal_Spare_Strategy.pdf
subject: 星链数模-参考文献
problem: 问题四·碎片鲁棒性
type: 精读解读
status: AI精读（待校对）
topics:
  - 多级库存
  - 备份星策略
  - (s,Q)库存策略
  - 停泊轨道
  - 星座维护成本
---

# Jakob & Ho 2018 · 多级库存备份策略（精读解读）

> **一句话总结**：把巨型卫星星座的"备份星补给"建模成一条"地面（供应商）→ 停泊轨道（仓库）→ 星座轨道（零售商）"的多级供应链，用连续 $(s,Q)$ 库存策略在随机故障需求与随机前置期下解析地刻画缺货、库存与成本，再用混合整数非线性优化求出使年维护总成本最小的最优备份配置。

## 一、论文速览
- **作者/年份/出处**：Pauline Jakob、Koki Ho（伊利诺伊大学厄巴纳-香槟分校）与三菱电机的 Seiichi Shimizu、Shoji Yoshikawa；2018 年发表于 *Journal of Spacecraft and Rockets*，DOI: 10.2514/1.A34387。
- **解决的问题**：面向"巨型星座"（mega-constellation，成百上千颗低成本小卫星）的备份/补给策略设计。传统策略（地面按需发射、每个轨道面自带备份星）在卫星数量巨大、故障频繁时不可扩展、成本高。
- **核心贡献**（4 条）：
  1. 首次把卫星星座备份问题映射成**多级库存（multi-echelon inventory）供应链**：地面=供应商、停泊轨道=仓库、星座轨道面=零售商。
  2. 全部节点采用连续 $(s,Q)$ 策略，从而能**利用批量发射折扣**（batch launch discount）。
  3. 建立**解析模型**（无需蒙特卡洛仿真）计算缺货、订单满足率、平均库存与总成本，并用拉丁超立方仿真验证（平均相对误差 0.4%–4.1%）。
  4. 提出**混合整数非线性优化**框架求最优备份策略；算例显示多级策略比"纯轨道面备份"省成本 36.6%。
- **方法类型**：解析建模（随机库存论）＋ 优化（遗传算法）＋ 仿真验证。

## 二、研究背景与动机
- 巨型星座（OneWeb 约 900 星、SpaceX Starlink 近 12000 星）单星冗余低、可靠性低、故障多，必须有可扩展的补给策略维持服务可用性。
- 传统两类策略都失效：
  - **仅靠轨道面内备份（in-plane spares）**：每个轨道面要囤很多备份星 → 持有成本极高。
  - **按需地面发射**：发射档期不确定、单星专发成本高（OneWeb 单星补发成本约为常规批量发射的 7 倍）。
- 关键机会：火箭一次能带几十颗小卫星（如 OneWeb 单星 150 kg），若能**用好批量发射折扣**就能大幅降成本——这正是传统方法做不到的。
- 已有文献（Petri 网、马尔可夫决策过程）都有**状态空间爆炸**问题，不可扩展到巨型星座；用库存管理方法做星座补给的研究极少（Dishon & Weiss 的 $(N,M)$ 模型过于简单，未考虑停泊轨道和批量折扣）。

## 三、核心方法（分章节中文重述）

### 3.1 物理基础：轨道摄动与霍曼转移
本文备份策略的巧妙之处在于**利用地球扁率（$J_2$）引起的升交点赤经（RAAN）漂移**：不同高度的轨道漂移速率不同，停泊轨道（较低）相对星座轨道会缓慢"扫过"所有轨道面，因此**一个停泊轨道最终能补给所有星座轨道面**。

RAAN 漂移率：
$$ \frac{d\Omega}{dt} = -\frac{3 n R_{\mathrm{Earth}}^2 J_2}{2 a^2}\cos i $$
其中 $\Omega$ 是升交点赤经（rad），$n=\sqrt{\mu/a^3}$ 是平均角速度（rad/s），$R_{\mathrm{Earth}}$ 是地球平均半径（km），$J_2=0.0010826263$ 是地球扁率系数（无量纲），$a$ 是半长轴（km，由轨道高度决定），$i$ 是轨道倾角（deg），$\mu$ 是地球引力常数（$\mathrm{km^3/s^2}$）。因漂移率只依赖 $a$ 和 $i$，两条同倾角、不同高度的轨道就有相对漂移。

霍曼转移（把备份星从停泊轨道送到星座轨道）所需燃料质量：
$$ m_{\text{fuel}} = m_{\text{dry}}\left(e^{\Delta V_{\text{Hohmann}}/v_{\text{ex}}} - 1\right) $$
其中 $m_{\text{fuel}}$ 为燃料质量（kg），$m_{\text{dry}}$ 为卫星干重（kg），$v_{\text{ex}}$ 为推进器有效排气速度（km/s），$\Delta V_{\text{Hohmann}}$ 为速度增量（km/s）。这是齐奥尔科夫斯基公式的变形。

速度增量与转移飞行时间：
$$ \Delta V_{\text{Hohmann}} = \sqrt{\frac{\mu}{a_0}}\left(\sqrt{\frac{2a_1}{a_0+a_1}}-1\right) + \sqrt{\frac{\mu}{a_1}}\left(1-\sqrt{\frac{2a_0}{a_0+a_1}}\right) $$
$$ TOF_{\mathrm{Hohmann}} = \pi\sqrt{\frac{(a_0+a_1)^3}{8\mu}} $$
其中 $a_0$、$a_1$ 分别是初始/目标轨道半长轴（km，本文 $a_1>a_0$，即从低的停泊轨道抬升到高的星座轨道），$TOF$ 为转移飞行时间（s，等于转移椭圆周期的一半）。

星座采用 **Walker Delta 构型**：总卫星分布在 $N_{\text{plane}}$ 个等间隔轨道面，每面 $N_{\text{sats}}$ 颗，共享高度 $h_{\text{plane}}$ 与倾角 $i$，RAAN 均匀分布 $\Omega_{k}=(k-1)\cdot 2\pi/N_{\text{plane}}$。

### 3.2 库存管理基础：$(s,Q)$ 策略、缺货、平均库存
每个设施（仓库/零售商）执行连续 $(s,Q)$ 策略：库存降到再订货点 $s$ 及以下时，就向上游订一批 $Q$ 个单位。选 $(s,Q)$ 而非 $(R,S)$、$(s,S)$ 是因为它能**固定批量 $Q$**，从而最大化批量发射折扣。

一个补给周期内的**期望缺货数**（backorder）：
$$ ES = \sum_{k\ge s+1}(k-s)\,P_\tau(D=k) $$
其中 $ES$ 是一个周期内的期望缺货件数，$s$ 是再订货点，$P_\tau(D=k)$ 是前置期 $\tau$ 内需求恰为 $k$ 件的概率（本文需求服从泊松分布），$k$ 从 $s+1$ 起求和即"超出 $s$ 的那部分需求"。

**订单满足率**（fill rate）：
$$ \rho = 1 - \frac{ES}{Q} $$
$\rho$ 表示一个周期内由现货满足的需求比例（越接近 1 越好），$ES$ 为期望缺货、$Q$ 为批量。

**平均库存水平**（用于算持有成本）：
$$ \overline{SL} = \frac{Q}{2} + s - N_{\text{fail}}(\tau) + \frac{1}{2} $$
其中 $\overline{SL}$ 是周期平均库存，$Q/2$ 来自库存在 $[s-N_{\text{fail}}, Q+s-N_{\text{fail}}]$ 间线性下降的平均，$s$ 为再订货点，$N_{\text{fail}}(\tau)$ 是前置期内的故障（需求）数，$+1/2$ 是离散→连续的连续性校正因子。

### 3.3 模型总体结构：三级备份
三级备份混合策略（Fig. 4/5）：
1. **轨道面内备份（in-plane spares，零售商）**：本面故障立即由本面备份星替换，几乎零延迟。
2. **停泊轨道备份（parking spares，仓库）**：位于较低高度、同倾角；靠 RAAN 相对漂移轮流对齐各星座轨道面，可补给**任意**轨道面（灵活性来源）。替换时间约 1–2 月。
3. **地面备份（ground spares，供应商）**：假设总是有货，靠火箭发射补给停泊轨道，前置期含发射档期等待。

各级替换时间对照（Table 1）：过量部署=无延迟；轨道面内=1–2 天；停泊轨道=1–2 月；地面=数月至 1 年。

**关键约束**：停泊轨道的批量与再订货点必须是轨道面批量 $Q_{\text{plane}}$ 的整数倍（因为要按批转移）：
$$ \begin{cases} Q_{\text{parking}} = k_{Q,\text{parking}}\,Q_{\text{plane}} \\ s_{\text{parking}} = k_{s,\text{parking}}\,Q_{\text{plane}} \end{cases} $$
其中 $k_{Q,\text{parking}}$、$k_{s,\text{parking}}$ 为整数倍数，$Q_{\text{parking}}$ 以卫星为单位、以 $Q_{\text{plane}}$ 为"批"单位。

### 3.4 轨道面内库存模型（零售商）
**需求（故障）模型**：卫星故障服从泊松过程。单个轨道面的日故障率：
$$ \lambda_{\text{plane}} = \frac{N_{\text{sats}}\,\lambda_{\text{sat}}}{N_{\text{days}}} $$
其中 $\lambda_{\text{plane}}$ 为每轨道面日故障率（失效/天），$N_{\text{sats}}$ 为每面运行卫星数，$\lambda_{\text{sat}}$ 为单星年故障率（失效/年），$N_{\text{days}}$ 为每年天数。

**前置期分布**（从停泊轨道到星座轨道）——这是本文最独特处：
- *停泊轨道可用概率* $P_{\text{av}}$：一条停泊轨道有现货的概率
$$ P_{\text{av}} = 1 - \frac{ES_{\text{parking}}}{k_{Q,\text{parking}}} $$
其中 $ES_{\text{parking}}$ 是停泊轨道一个周期的期望缺货（以批 $Q_{\text{plane}}$ 计），$k_{Q,\text{parking}}$ 是其批量倍数。
- *从第 $i$ 近停泊轨道取货的概率*（二项式型，各停泊轨道独立同 $P_{\text{av}}$）：
$$ P(i^{\text{th}}) = \sum_{k=1}^{N_{\text{parking}}-i+1}\binom{N_{\text{parking}}-i}{k-1}P_{\text{av}}^{k}(1-P_{\text{av}})^{N_{\text{parking}}-k} $$
其中 $N_{\text{parking}}$ 为停泊轨道数量，$i$ 为按等待时间排序的第 $i$ 近轨道。含义：第 $i$ 近轨道被选中，意味着更近的 $i-1$ 个都缺货、第 $i$ 个有货。
- *前置期本身* 服从分区间的均匀分布：把 $2\pi$ 的 RAAN 差按 $N_{\text{parking}}$ 等分，从第 $i$ 近轨道取货时对应 $\Delta\Omega\in[(i-1)\frac{2\pi}{N_{\text{parking}}}, i\frac{2\pi}{N_{\text{parking}}}]$：
$$ T_{\text{plane}}(i^{\text{th}}) \sim \mathcal{U}\left\{t_{\text{transfer}}\!\left(\Delta\Omega=(i-1)\tfrac{2\pi}{N_{\text{parking}}}\right),\; t_{\text{transfer}}\!\left(\Delta\Omega=i\tfrac{2\pi}{N_{\text{parking}}}\right)\right\} $$
其中 $t_{\text{transfer}}(\Delta\Omega)$ = 漂移等待时间（由式 (1) 的漂移率算）＋ 转移飞行时间（式 (4)）。结合 $P(i^{\text{th}})$ 与 $T_{\text{plane}}(i^{\text{th}})$ 即得完整前置期分布 $f_{\text{plane}}$。

**期望缺货**（对前置期分布积分）：
$$ ES_{\text{plane}} = \int_{T_{\text{plane}}} ES_{T_{\text{plane}}}(s_{\text{plane}})\, f_{\text{plane}}(T_{\text{plane}})\, \mathrm{d}T_{\text{plane}} $$
$$ \rho_{\text{plane}} = 1 - \frac{ES_{\text{plane}}}{Q_{\text{plane}}} $$
其中 $ES_{T_{\text{plane}}}(s_{\text{plane}})$ 是给定前置期与再订货点 $s_{\text{plane}}$ 时的期望缺货（用式 (5)），$f_{\text{plane}}$ 是前置期概率密度。

**平均库存**（在前置期分布上取期望）：
$$ \overline{SL_{\text{plane}}} = \int_{T_{\text{plane}}}\!\left\{\frac{Q_{\text{plane}}}{2} + s_{\text{plane}} - N_{\text{fail,plane}}(T_{\text{plane}}) + \frac{1}{2}\right\} f_{\text{plane}}(T_{\text{plane}})\,\mathrm{d}T_{\text{plane}} $$

### 3.5 停泊轨道库存模型（仓库）
**需求模型**：每个星座轨道面平均每 $Q_{\text{plane}}$ 次故障向停泊轨道下一次订单，故订单间隔服从 Erlang-$Q_{\text{plane}}$ 分布；当 $N_{\text{plane}}\ge 20$ 时，所有轨道面订单的叠加可近似为泊松过程。单条停泊轨道的日需求率：
$$ \lambda_{\text{parking}} = N_{\text{plane}}\,\frac{\lambda_{\text{plane}}}{Q_{\text{plane}}}\,\frac{1}{N_{\text{parking}}} $$
其中 $\lambda_{\text{parking}}$ 单位是"批 $Q_{\text{plane}}$/天"，含义：全体轨道面总需求率 $N_{\text{plane}}\lambda_{\text{plane}}/Q_{\text{plane}}$ 由 $N_{\text{parking}}$ 条停泊轨道均分。

**前置期（地面→停泊轨道）**：处理时间（常数）＋ 下一发射窗口等待（指数分布）：
$$ T_{\text{parking}} \sim \mathcal{E}(\mu_{\text{launch}}) + T_{\text{processing}} $$
其中 $\mathcal{E}(\mu_{\text{launch}})$ 是均值为 $\mu_{\text{launch}}$（发射间平均天数）的指数分布，$T_{\text{processing}}$ 是发射订单处理时间（天）。附录 A 用 Soyuz 火箭发射数据拟合出 $\mu_{\text{launch}}\approx 66.7$ 天。

**期望缺货与平均库存**（与轨道面对称）：
$$ ES_{\text{parking}} = \int_{T_{\text{parking}}} ES_{T_{\text{parking}}}(k_{s,\text{parking}})\, f_{\text{parking}}(T_{\text{parking}})\,\mathrm{d}T_{\text{parking}} $$
$$ \rho_{\text{parking}} = 1 - \frac{ES_{\text{parking}}}{k_{Q,\text{parking}}} $$
$$ \overline{SL_{\text{parking}}} = \int_{T_{\text{parking}}}\!\left\{\frac{k_{Q,\text{parking}}}{2} + k_{s,\text{parking}} - N_{\text{fail,parking}}(T_{\text{parking}}) + \frac{1}{2}\right\} f_{\text{parking}}(T_{\text{parking}})\,\mathrm{d}T_{\text{parking}} $$
以上均以"批 $Q_{\text{plane}}$"为单位。

### 3.6 总成本模型（TESSAC）
年度总期望备份策略成本（Total Expected Spare Strategy Annual Cost）：
$$ TESSAC = c_{\text{manufacturing}} + c_{\text{holding}} + c_{\text{launch}} + c_{\text{maneuvering}} $$

**制造成本**（一年总故障数 × 单星造价）：
$$ c_{\text{manufacturing}} = p_{\text{sat}}\,\lambda_{\text{plane}}\,N_{\text{plane}}\,N_{\text{days}} $$
$p_{\text{sat}}$ 为单星制造成本（百万美元/颗）。

**持有成本**（在轨备份星的运维/位保成本）：
$$ c_{\text{holding}} = p_{\text{holding}}\left\{\overline{SL_{\text{plane}}}\,N_{\text{plane}} + \overline{SL_{\text{parking}}}\,Q_{\text{plane}}\,N_{\text{parking}}\right\} $$
$p_{\text{holding}}$ 为单星年持有成本（百万美元/颗/年）；注意停泊轨道库存 $\overline{SL_{\text{parking}}}$ 以批计，故乘 $Q_{\text{plane}}$ 换算成卫星数。

**发射成本**（由停泊轨道产生的补给需求驱动）：
$$ c_{\text{launch}} = p_{\text{launch}}\,\frac{\lambda_{\text{parking}}\,Q_{\text{plane}}}{Q_{\text{parking}}}\,N_{\text{parking}}\,N_{\text{days}} $$
其中每次发射成本 $p_{\text{launch}}$ 取两种发射方式的较小值——整箭满载 vs 单星专发：
$$ p_{\text{launch}} = \min\left\{p_{\text{launch,full}},\; Q_{\text{parking}}\,p_{\text{launch,unit}}\right\} $$
$p_{\text{launch,full}}$ 为整箭发射固定价（与实际装载数无关，体现批量折扣），$p_{\text{launch,unit}}$ 为单星专发单价。

**机动成本**（一年所有转移的燃料 × 转换系数）：
$$ c_{\text{maneuvering}} = m_{\text{fuel}}\,\lambda_{\text{plane}}\,N_{\text{plane}}\,N_{\text{days}}\,\epsilon_{\text{maneuvering}} $$
$\epsilon_{\text{maneuvering}}$ 为燃料质量→成本的转换系数（百万美元/kg）。

### 3.7 优化问题
决策变量（6 个，多为整数）：$\boldsymbol{x}=[N_{\text{parking}}, h_{\text{parking}}, Q_{\text{plane}}, s_{\text{plane}}, k_{Q,\text{parking}}, k_{s,\text{parking}}]$。
$$ \min_{\boldsymbol{x}} J(\boldsymbol{x}) = TESSAC(\boldsymbol{x}) $$
**约束一**（发射能力）：$Q_{\text{parking}} \le U_{\text{launch}}$，即一箭批量不超过运载能力。
**约束二**（全局效率）：
$$ \rho_{\text{global}} \le \rho_{\text{plane}}^{N_{\text{plane}}}\,\rho_{\text{parking}}^{N_{\text{parking}}} $$
其中 $\rho_{\text{global}}$ 是要求的全系统效率下限（如 0.95），右侧是各级 fill rate 的联合幂次；该约束把缺货压到可忽略，保证平均库存公式成立。求解器用 MATLAB 的单目标遗传算法（混合整数非线性）。

## 四、关键结论与结果
- **模型精度**（Table 4，拉丁超立方 25 组 × 每组 100 次仿真、每次 15 年）：解析模型 vs 仿真的平均相对误差 0.4%–4.1%——轨道面平均库存 1.7%、停泊轨道平均库存 4.1%、轨道面 fill rate 0.8%、停泊轨道 fill rate 0.4%、TESSAC 1.6%。说明解析模型能替代昂贵仿真。
- **算例**（LEO 巨型星座：$h_{\text{plane}}=1200$ km、$i=50°$、$N_{\text{plane}}=40$、$N_{\text{sats}}=40$、$\lambda_{\text{sat}}=0.05$/年、$\rho_{\text{global}}=0.95$）：
  - 多级最优解：3 条停泊轨道、高度 792.3 km、$(s_{\text{plane}},Q_{\text{plane}})=(3,4)$、$(s_{\text{parking}},Q_{\text{parking}})=(32,32)$，TESSAC = **319.1 百万美元/年**。
  - 纯轨道面策略：$(s_{\text{plane}},Q_{\text{plane}})=(4,20)$，TESSAC = 503.2 百万美元/年。
  - **多级策略省 36.6%**。
- **关键洞见**：
  1. 最优 $Q_{\text{parking}}=32$ 逼近运载上限 $U_{\text{launch}}=34$ → **批量发射折扣是降本主因**。
  2. 偏好 3 条停泊轨道 → 停泊轨道数量在"缩短前置期"与"增加持有成本"间存在折中甜点。
  3. 停泊高度 792.3 km 是"漂移对齐时间"与"机动燃料成本"的折中。
- **敏感性分析**（Fig. 6，$\lambda_{\text{sat}}$ 变化）：多级策略在所有故障率下都省钱；**中等故障率（约 0.01/年）节省最大，可达约 43%**。故障率过低（需求少、少用批量折扣）或过高（两种策略都能用批量折扣）时，多级策略的相对优势变小。
- **局限**：假设各停泊轨道/轨道面策略同构；假设地面永远有货；用硬效率约束而非把效率成本纳入目标；故障用泊松分布，未建模"婴儿期失效"与"退化状态"。

## 五、对数模题目的启示（问题四·碎片鲁棒性）
- **可复用的方法/公式**：
  - **多级 $(s,Q)$ 库存框架**：把"星座失效→补给"抽象成 供应商-仓库-零售商 三级链，是刻画"星座在碎片/故障冲击下如何维持规模"的现成骨架。缺货式 (5)、fill rate 式 (6)、平均库存式 (7) 都可直接搬用。
  - **泊松故障 → 需求率**：式 (9) 把单星故障率换算成轨道面/系统需求率，可直接用于问题四中"碎片撞击导致的卫星失效速率"建模（把碎片致损率并入 $\lambda_{\text{sat}}$）。
  - **RAAN 漂移共享补给**：式 (1) + 停泊轨道概念揭示"一个低轨库存点可轮流服务所有轨道面"，对设计**鲁棒的备份星调度**极有启发。
  - **总成本分解 TESSAC**（式 21–26）：制造＋持有＋发射＋机动四项，是给"维持星座鲁棒性"做成本-效益权衡的完整目标函数模板。
- **建模时如何用**：
  - 若问题四要评估"碎片环境下需要多少备份星、如何补给最省"，可把碎片致损纳入故障率 $\lambda_{\text{sat}}$，套用本文优化式 (30)–(32)，以 fill rate 联合约束式 (32) 表达"服务可用性/鲁棒性要求"。
  - 用 fill rate 联合幂次 $\rho_{\text{plane}}^{N_{\text{plane}}}\rho_{\text{parking}}^{N_{\text{parking}}}\ge \rho_{\text{global}}$ 表征"整星座在冲击下仍满足最低可用度"，是把"鲁棒性"量化为可优化约束的好范例。
  - 解析模型（免仿真）适合数模比赛快速评估大量方案；需要时再用少量仿真校核。
- **注意事项/局限**：
  - 本文需求是"渐进/稳态"泊松失效，**不直接刻画碎片级联（如凯斯勒效应）的突发大规模失效**；若问题四强调碎片突发冲击，需把泊松假设换成更重尾/成簇的失效过程。
  - "地面永远有货""各轨道面同构"等假设在极端场景下偏乐观。
  - 前置期分布依赖 $J_2$ 漂移几何，仅对同倾角、圆轨道成立；异面机动被排除。

## 六、术语与符号对照
| 英文/符号 | 中文 | 含义 |
|:--|:--|:--|
| Multi-echelon inventory | 多级库存 | 供应商-仓库-零售商多层库存系统 |
| $(s,Q)$ policy | $(s,Q)$ 库存策略 | 库存降到 $s$ 就订一批 $Q$ |
| In-plane spares | 轨道面内备份 | 星座轨道面自带的备份星（零售商） |
| Parking orbit / spares | 停泊轨道/停泊备份 | 低轨仓库层备份星（仓库） |
| Ground spares | 地面备份 | 地面待发射的备份星（供应商） |
| Backorder, $ES$ | 缺货/期望缺货 | 一周期内未被现货满足的需求（件） |
| Fill rate, $\rho$ | 订单满足率 | 由现货满足的需求比例 |
| Lead time, $T$ | 前置期 | 下单到到货的时间（随机） |
| $\lambda_{\text{sat}}$ | 单星故障率 | 失效/年 |
| $\lambda_{\text{plane}}$ | 轨道面故障率 | 失效/天 |
| $\lambda_{\text{parking}}$ | 停泊轨道需求率 | 批 $Q_{\text{plane}}$/天 |
| $N_{\text{plane}}$ / $N_{\text{sats}}$ | 轨道面数/每面卫星数 | 星座构型参数 |
| $N_{\text{parking}}$ | 停泊轨道数 | 优化变量 |
| $Q_{\text{plane}}$ / $Q_{\text{parking}}$ | 轨道面/停泊批量 | 每次订货数（卫星） |
| $s_{\text{plane}}$ / $s_{\text{parking}}$ | 再订货点 | 触发订货的库存阈值 |
| $k_{Q,\text{parking}}$ / $k_{s,\text{parking}}$ | 停泊批量/再订货倍数 | $Q_{\text{parking}}=k_Q Q_{\text{plane}}$ 等 |
| $P_{\text{av}}$ | 停泊轨道可用概率 | 一条停泊轨道有现货的概率 |
| RAAN, $\Omega$ | 升交点赤经 | 由 $J_2$ 引起漂移 |
| $\Delta V_{\text{Hohmann}}$ | 霍曼速度增量 | 转移所需 $\Delta V$ |
| $U_{\text{launch}}$ | 运载能力 | 一箭最多卫星数 |
| $\mu_{\text{launch}}$ | 平均发射间隔 | 指数分布均值（天） |
| TESSAC | 年度总备份成本 | 制造+持有+发射+机动 |
| $\epsilon_{\text{maneuvering}}$ | 燃料成本转换系数 | 百万美元/kg |
