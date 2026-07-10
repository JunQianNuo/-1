# 问题二优化代码使用说明

本目录新增的优化代码保留原有 `q2_constellation.py` 和
`q2_fast_coverage.py` 作为基准，不会覆盖原实现。

## 新增模块

- `q2_search_space.py`：完整生成 `(M,N,F)`，并为每个离散结构分配相同的 Sobol 采样预算；
- `q2_coverage_margin.py`：计算单重或多重覆盖的连续裕量；
- `q2_kdtree_coverage.py`：使用三维单位球 KD 树查找邻近卫星对和临界点附近卫星；
- `q2_active_set.py`：活动约束集、Powell 局部优化和反例驱动迭代；
- `q2_adaptive_verify.py`：基于角距离上下界的保守时空盒验证；
- `run_q2_optimized_search.py`：新的主搜索脚本；
- `tests/test_q2_optimized.py`：公平性、KD 树等价性和时空盒基础测试。

## 推荐环境

```bash
pip install numpy scipy
```

没有 SciPy 时，程序仍可导入，但 Sobol、KD 树和 Powell 优化会退化为较慢的备用实现。

## 快速试运行

在 `代码/问题二` 目录执行：

```bash
python run_q2_optimized_search.py \
  --start-total 40 \
  --stop-total 42 \
  --samples-per-structure 8 \
  --local-starts-per-structure 1 \
  --keep-top-per-total 5 \
  --max-cegis-rounds 2
```

该配置用于检查程序流程，不用于最终论文结论。

## 正式数值搜索建议

```bash
python run_q2_optimized_search.py \
  --start-total 40 \
  --stop-total 60 \
  --samples-per-structure 128 \
  --local-starts-per-structure 5 \
  --keep-top-per-total 20 \
  --screen-duration-hours 6 \
  --screen-time-step 300 \
  --separation-duration-hours 24 \
  --separation-time-step 60 \
  --max-cegis-rounds 10 \
  --local-max-evaluations 120
```

程序默认在发现首个数值可行的卫星总数后停止。使用
`--continue-after-validated` 才会继续搜索更大的卫星总数。

## 保守连续覆盖验证

在正式候选上追加：

```bash
--adaptive-verify \
--adaptive-spatial-tolerance 0.05 \
--adaptive-time-tolerance 1 \
--adaptive-max-boxes 200000
```

验证器可能返回：

- `covered`：在当前球形地球、圆轨道和角速度上界模型下完成保守覆盖证明；
- `uncovered`：发现一个无法满足覆盖重数的时空盒；
- `inconclusive`：达到细分精度或盒子预算后仍有未决区域。

`inconclusive` 不等于不可行，也不能写成已经证明连续覆盖。

## 输出文件

默认写入 `results_optimized/`：

- `q2_optimized_screen.csv`：全部公平初筛记录；
- `q2_optimized_refined.csv`：反例驱动精化记录；
- `q2_structure_audit.csv`：每个 `(M,N,F)` 的实际评价次数；
- `q2_optimized_summary.json`：参数、首个数值可行候选和可选验证证书。

## 测试

```bash
python -m unittest discover -s tests -p "test_q2_optimized.py" -v
```

其中 KD 树测试会将结果与原全量点积方法逐项比较。
