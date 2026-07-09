# 问题一数值实现说明

## 1. 目标

本目录实现问题一的单星覆盖几何与单轨道面连续覆盖数值校验。

对应建模文档：

- `数学建模/第一次/问题分析/星链系统-文献驱动版/03-问题一假设与覆盖几何推导.md`
- `数学建模/第一次/问题分析/星链系统-文献驱动版/04-问题一数值校验与曲线生成方案.md`

## 2. 运行方法

在本目录下运行：

```bash
python 问题1_求解.py
```

或在 vault 根目录运行：

```bash
python 数学建模/第一次/代码/星链系统/问题一/问题1_求解.py
```

## 3. 输出文件

### 结果表

| 文件 | 说明 |
|---|---|
| `results/problem1_summary.csv` | 两种参数口径的覆盖地心角、覆盖面积、最少卫星数 |
| `results/problem1_overlap_table.csv` | $N=30\sim80$ 的间距、重叠率、覆盖带半宽数据 |
| `results/problem1_results.txt` | 关键结果的文字说明 |

### 图像

| 文件 | 说明 |
|---|---|
| `figures/Q1_N_vs_spacing.png` | 单轨卫星数 $N$ 与相邻星下点弧长 |
| `figures/Q1_N_vs_overlap_linear.png` | 一维沿轨重叠率随 $N$ 的变化 |
| `figures/Q1_N_vs_overlap_area.png` | 平面近似面积重叠率随 $N$ 的变化 |
| `figures/Q1_N_vs_bandwidth.png` | Lüders 覆盖带半宽 $\psi(N)$ 随 $N$ 的变化 |
| `figures/Q1_parameter_consistency.png` | 题给半径口径与半锥角口径的差异对比 |
| `figures/Q1_subsatellite_latitude_time.png` | 代表卫星星下点纬度随时间变化 |
| `figures/Q1_ground_track_rotation_comparison.png` | 考虑/不考虑地球自转时的星下点经纬度轨迹对比 |

## 4. 当前结论

主口径采用题给有效覆盖半径 $506\,\mathrm{km}$：

- 覆盖地心角约 $4.55^\circ$；
- 单轨道面沿轨连续覆盖下界 $N_{\min}=40$。

半锥角 $40.46^\circ$ 只用于检查题给参数一致性，不作为主曲线和主结论。问题一主答案围绕题给 $506\,\mathrm{km}$ 口径展开。

星下点轨迹图采用代表性参数：

- 倾角 $i=50^\circ$；
- 单轨道面卫星数 $N=40$；
- 目标纬度带 $30^\circ\mathrm{N}\sim50^\circ\mathrm{N}$。

其中 `Q1_subsatellite_latitude_time.png` 用于说明星下点纬度的周期变化；`Q1_ground_track_rotation_comparison.png` 用于说明地球自转主要造成经度漂移，而不改变星下点纬度范围。

## 5. 注意

该数值实现只验证“单轨道面沿轨连续覆盖”。  
它不能证明单个轨道面可以覆盖整个 $30^\circ\mathrm{N}\sim50^\circ\mathrm{N}$ 纬度带全部经度；后者需要多轨道面模型，留到问题二。
