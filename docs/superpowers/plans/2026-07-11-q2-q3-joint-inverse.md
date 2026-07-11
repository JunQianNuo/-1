# 问题二—问题三联合反推 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现共享轨道与接入几何、批量最短路、双比例通信约束和多保真候选状态机，使问题二—问题三联合反推在保持可审计最优性口径的同时显著减少高保真计算。

**Architecture:** 用 `q3_joint_evaluator.py` 流式生成共享卫星快照，同时计算面积加权覆盖与通信指标；用 `q3_batched_routing.py` 在有向增广稀疏图上批量求全部 OD 时延；由 `q3_joint_search.py` 管理严格淘汰、延迟候选和星数层结论，`run_q3_joint_search.py` 负责发现/核验、缓存和输出。

**Tech Stack:** Python 3.12、NumPy、SciPy sparse/csgraph、pytest、Obsidian Markdown。

## Global Constraints

- 覆盖约束固定为 $C_1\ge0.999$、$C_2\ge0.95$。
- 通信约束固定为 $P_{30}^{\mathrm{reach}}\ge0.999$、$P_{30}^{\mathrm{all}}\ge0.95$。
- 等权可达样本最大超时数必须使用 $n_{\max}=\lfloor0.001R\rfloor$，禁止四舍五入。
- 低保真失败只能排序或进入 `deferred`；只有必要条件、严格上下界或完整高保真违规才能进入 `rejected`。
- 低、中、高保真网格必须嵌套，低层样本索引属于高层母样本。
- 不改变题面四邻接 ISL 规则、5000 km 距离限制和 0.5 ms/跳处理时延。
- 不声称连续参数域全局最优；只报告规定范围与离散精度下结论。
- 当前目录不是 Git 仓库，各任务以测试通过和文件差异复核作为检查点，不执行 commit。

---

## File Structure

| 文件 | 责任 |
|:--|:--|
| `代码/问题三/q3_joint_search.py` | 服务率预算、加权进度、候选状态和星数层调度 |
| `代码/问题三/q3_batched_routing.py` | 有向增广图和批量 OD 最短路 |
| `代码/问题三/q3_joint_evaluator.py` | 共享快照与单候选多保真联合评价 |
| `代码/问题三/run_q3_joint_search.py` | CLI、发现/核验、检查点和结果文件 |
| `代码/问题三/tests/test_q3_joint_search.py` | 新算法单元、集成和状态回归测试 |
| `问题分析/星链系统-文献驱动版/21-问题三参数化求解模型.md` | 双比例联合模型与最优性口径 |
| `问题分析/星链系统-文献驱动版/22-问题三求解算法设计.md` | 联合算法 L、复杂度和验证流程 |
| `代码/问题三/README.md` | 运行入口、依赖和输出说明 |

---

### Task 1: 双比例服务预算与面积加权上界

**Files:**
- Modify: `第一次/代码/问题三/q3_joint_search.py`
- Create: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- Produces: `max_reachable_late_samples(reachable_count: int, eta_reach: float = 0.999) -> int`
- Produces: `ServiceProgress(total_weight: float, eta_reach: float, eta_all: float)`
- Produces: `WeightedCoverageProgress(total_weight: float, c1_min: float, c2_min: float)`
- Consumes: no new project interfaces.

- [ ] **Step 1: Write failing tests for integer late-sample budgets**

```python
from q3_joint_search import max_reachable_late_samples


def test_reachable_late_budget_uses_floor_not_rounding():
    assert max_reachable_late_samples(999) == 0
    assert max_reachable_late_samples(1000) == 1
    assert max_reachable_late_samples(12782) == 12
    assert max_reachable_late_samples(1500) == 1
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
& 'C:\Users\Nuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_q3_joint_search.py::test_reachable_late_budget_uses_floor_not_rounding -q -p no:cacheprovider
```

Expected: FAIL because `max_reachable_late_samples` does not exist.

- [ ] **Step 3: Implement the integer budget**

```python
def max_reachable_late_samples(reachable_count: int, eta_reach: float = 0.999) -> int:
    if reachable_count < 0:
        raise ValueError("reachable_count must be non-negative")
    if not 0.0 <= eta_reach <= 1.0:
        raise ValueError("eta_reach must lie in [0, 1]")
    return math.floor((1.0 - eta_reach) * reachable_count + 1e-12)
```

- [ ] **Step 4: Add failing tests for streaming service bounds**

```python
def test_service_progress_tracks_reachable_and_all_sample_upper_bounds():
    progress = ServiceProgress(total_weight=1000.0, eta_reach=0.999, eta_all=0.95)
    progress.update(weight=1.0, reachable=True, within_limit=False)
    reach_upper, all_upper = progress.upper_bounds()
    assert reach_upper == pytest.approx(999.0 / 1000.0)
    assert all_upper == pytest.approx(999.0 / 1000.0)
    assert progress.can_still_pass()

    progress.update(weight=1.0, reachable=True, within_limit=False)
    assert not progress.can_still_pass_reachable()


def test_unreachable_sample_only_reduces_all_sample_service_rate():
    progress = ServiceProgress(total_weight=20.0, eta_reach=0.999, eta_all=0.95)
    progress.update(weight=1.0, reachable=False, within_limit=False)
    assert progress.can_still_pass()
    progress.update(weight=1.0, reachable=False, within_limit=False)
    assert not progress.can_still_pass_all()
```

- [ ] **Step 5: Implement `ServiceProgress`**

```python
@dataclass
class ServiceProgress:
    total_weight: float
    eta_reach: float = 0.999
    eta_all: float = 0.95
    processed_weight: float = 0.0
    reachable_weight: float = 0.0
    within_limit_weight: float = 0.0

    def update(self, *, weight: float, reachable: bool, within_limit: bool) -> None:
        if weight <= 0.0:
            raise ValueError("weight must be positive")
        if self.processed_weight + weight > self.total_weight + 1e-12:
            raise ValueError("processed weight exceeds total weight")
        if within_limit and not reachable:
            raise ValueError("an unreachable sample cannot be within the delay limit")
        self.processed_weight += weight
        self.reachable_weight += weight * int(reachable)
        self.within_limit_weight += weight * int(within_limit)

    def upper_bounds(self) -> tuple[float, float]:
        remaining = self.total_weight - self.processed_weight
        reach_denominator = self.reachable_weight + remaining
        reach_upper = (
            (self.within_limit_weight + remaining) / reach_denominator
            if reach_denominator > 0.0 else 1.0
        )
        all_upper = (self.within_limit_weight + remaining) / self.total_weight
        return float(reach_upper), float(all_upper)

    def can_still_pass_reachable(self) -> bool:
        return self.upper_bounds()[0] + 1e-12 >= self.eta_reach

    def can_still_pass_all(self) -> bool:
        return self.upper_bounds()[1] + 1e-12 >= self.eta_all

    def can_still_pass(self) -> bool:
        return self.can_still_pass_reachable() and self.can_still_pass_all()
```

- [ ] **Step 6: Add and implement weighted coverage progress**

Test:

```python
def test_weighted_coverage_progress_uses_remaining_area_weight():
    progress = WeightedCoverageProgress(total_weight=10.0, c1_min=0.9, c2_min=0.8)
    progress.update(weight=6.0, single_covered=True, double_covered=False)
    assert progress.upper_bounds() == pytest.approx((1.0, 0.4))
    assert not progress.can_still_pass()
```

Implementation:

```python
@dataclass
class WeightedCoverageProgress:
    total_weight: float
    c1_min: float = 0.999
    c2_min: float = 0.95
    processed_weight: float = 0.0
    single_hit_weight: float = 0.0
    double_hit_weight: float = 0.0

    def update(self, *, weight: float, single_covered: bool, double_covered: bool) -> None:
        if weight <= 0.0:
            raise ValueError("weight must be positive")
        if self.processed_weight + weight > self.total_weight + 1e-12:
            raise ValueError("processed weight exceeds total weight")
        self.processed_weight += weight
        self.single_hit_weight += weight * int(single_covered)
        self.double_hit_weight += weight * int(double_covered)

    def upper_bounds(self) -> tuple[float, float]:
        remaining = self.total_weight - self.processed_weight
        return (
            (self.single_hit_weight + remaining) / self.total_weight,
            (self.double_hit_weight + remaining) / self.total_weight,
        )

    def can_still_pass(self) -> bool:
        c1_upper, c2_upper = self.upper_bounds()
        return c1_upper + 1e-12 >= self.c1_min and c2_upper + 1e-12 >= self.c2_min
```

- [ ] **Step 7: Run Task 1 tests and the existing suite**

Run:

```powershell
& 'C:\Users\Nuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_q3_joint_search.py tests/test_q3_algorithms.py -q -p no:cacheprovider
```

Expected: all tests PASS.

---

### Task 2: 有向增广图批量 Dijkstra

**Files:**
- Create: `第一次/代码/问题三/q3_batched_routing.py`
- Modify: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- Consumes: `q3_routing.WeightedGraph`
- Produces: `batched_ground_delay_matrix(graph, access_sets, satellite_ecef_km, ground_points_ecef_km, c_km_s) -> np.ndarray`
- Produces: `build_augmented_csr(graph: WeightedGraph, access_sets: list[list[int]], satellite_ecef_km: np.ndarray, ground_points_ecef_km: np.ndarray, *, c_km_s: float = 299792.458) -> tuple[csr_matrix, np.ndarray, np.ndarray]`

- [ ] **Step 1: Write a failing equivalence test against the existing router**

```python
def test_batched_delay_matrix_matches_existing_multi_source_routes():
    graph = WeightedGraph(4)
    graph.add_edge(0, 1, 0.4)
    graph.add_edge(1, 2, 0.3)
    graph.add_edge(2, 3, 0.2)
    sat = np.array([[1.0, 0, 0], [2.0, 0, 0], [3.0, 0, 0], [4.0, 0, 0]])
    ground = np.array([[1.0, 0, 0], [4.0, 0, 0], [2.0, 0, 0]])
    access = [[0], [3], [1, 2]]
    pairs = [(a, b) for a in range(3) for b in range(3) if a != b]
    expected = min_delay_routes(
        graph, access, sat, ground, od_pairs=pairs, c_km_s=1.0
    )
    actual = batched_ground_delay_matrix(
        graph, access, sat, ground, c_km_s=1.0
    )
    for pair, route in expected.items():
        assert actual[pair] == pytest.approx(route.delay_s)
```

- [ ] **Step 2: Run and verify RED**

Run the focused test; expect import failure for `q3_batched_routing`.

- [ ] **Step 3: Implement augmented CSR construction**

```python
def build_augmented_csr(
    graph: WeightedGraph,
    access_sets: list[list[int]],
    satellite_ecef_km: np.ndarray,
    ground_points_ecef_km: np.ndarray,
    *,
    c_km_s: float,
) -> tuple[csr_matrix, np.ndarray, np.ndarray]:
    sat = np.asarray(satellite_ecef_km, dtype=float)
    ground = np.asarray(ground_points_ecef_km, dtype=float)
    satellite_count = graph.node_count
    ground_count = len(ground)
    source_nodes = satellite_count + np.arange(ground_count)
    sink_nodes = satellite_count + ground_count + np.arange(ground_count)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for edge in graph.edges:
        rows.extend((edge.u, edge.v))
        cols.extend((edge.v, edge.u))
        data.extend((edge.weight_s, edge.weight_s))
    for ground_id, satellites in enumerate(access_sets):
        for sat_id in satellites:
            delay = float(np.linalg.norm(sat[sat_id] - ground[ground_id]) / c_km_s)
            rows.append(int(source_nodes[ground_id]))
            cols.append(int(sat_id))
            data.append(delay)
            rows.append(int(sat_id))
            cols.append(int(sink_nodes[ground_id]))
            data.append(delay)
    size = satellite_count + 2 * ground_count
    matrix = csr_matrix((data, (rows, cols)), shape=(size, size))
    return matrix, source_nodes, sink_nodes
```

- [ ] **Step 4: Implement batched delay extraction**

```python
def batched_ground_delay_matrix(
    graph: WeightedGraph,
    access_sets: list[list[int]],
    satellite_ecef_km: np.ndarray,
    ground_points_ecef_km: np.ndarray,
    *,
    c_km_s: float = 299792.458,
) -> np.ndarray:
    matrix, sources, sinks = build_augmented_csr(
        graph,
        access_sets,
        satellite_ecef_km,
        ground_points_ecef_km,
        c_km_s=c_km_s,
    )
    distances = scipy_dijkstra(
        matrix,
        directed=True,
        indices=sources,
        return_predecessors=False,
    )
    return np.asarray(distances[:, sinks], dtype=float)
```

- [ ] **Step 5: Add tests for empty access, disconnected ISL and forbidden ground transit**

```python
def test_batched_router_reports_infinite_delay_for_empty_access():
    graph = WeightedGraph(1)
    matrix = batched_ground_delay_matrix(
        graph,
        [[], [0]],
        np.array([[1.0, 0.0, 0.0]]),
        np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        c_km_s=1.0,
    )
    assert math.isinf(matrix[0, 1])


def test_augmented_graph_cannot_use_ground_sink_as_relay():
    # Satellite 0 and 1 are disconnected. Both can reach ground 1, but the
    # route 0 -> ground 1 -> 1 must not exist because sink nodes have no exits.
    graph = WeightedGraph(2)
    matrix = batched_ground_delay_matrix(
        graph,
        [[0], [0, 1], [1]],
        np.array([[1.0, 0.0, 0.0], [3.0, 0.0, 0.0]]),
        np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]),
        c_km_s=1.0,
    )
    assert math.isinf(matrix[0, 2])
```

- [ ] **Step 6: Run Task 2 and full Q3 tests**

Expected: equivalence, edge cases and all pre-existing tests PASS.

---

### Task 3: 共享快照联合评价器

**Files:**
- Create: `第一次/代码/问题三/q3_joint_evaluator.py`
- Modify: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- Consumes: `ServiceProgress`, `WeightedCoverageProgress`, `batched_ground_delay_matrix`
- Produces: `MotherGrid`, `FidelityGrid`, `JointEvaluationState`, `JointEvaluation`, `evaluate_joint_candidate(params: ConstellationParams, *, mother_grid: MotherGrid, fidelity: FidelityGrid, state: JointEvaluationState | None = None, config: Q3Config | None = None, simulation: SimulationConfig | None = None, c1_min: float = 0.999, c2_min: float = 0.95, eta_reach: float = 0.999, eta_all: float = 0.95) -> tuple[JointEvaluation, JointEvaluationState]`
- Produces: `coverage_counts_from_ecef(satellite_ecef_km: np.ndarray, ground_unit_vectors: np.ndarray, *, coverage_angle_rad: float) -> np.ndarray`
- Produces: `summarize_service_delays(delays_s: np.ndarray, *, delay_limit_s: float = 0.030, eta_reach: float = 0.999, eta_all: float = 0.95) -> ServiceSummary`
- Produces private helpers: `_update_weighted_coverage(counts: np.ndarray, weights: np.ndarray, progress: WeightedCoverageProgress) -> None`, `_update_empty_access_failures(access_sets: list[list[int]], progress: ServiceProgress, *, sample_weight: float) -> set[tuple[int, int]]`, `_update_service_from_delay_matrix(delay_matrix: np.ndarray, progress: ServiceProgress, *, sample_weight: float, already_counted_unreachable: set[tuple[int, int]], delay_limit_s: float) -> None`.

- [ ] **Step 1: Write failing coverage-count test from shared ECEF positions**

```python
def test_coverage_counts_from_ecef_matches_access_geometry():
    sat = np.array([[2.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    ground_units = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    counts = coverage_counts_from_ecef(
        sat,
        ground_units,
        coverage_angle_rad=math.radians(10.0),
    )
    assert counts.tolist() == [1, 1]
```

- [ ] **Step 2: Implement normalized dot-product coverage counts**

```python
def coverage_counts_from_ecef(satellite_ecef_km, ground_unit_vectors, *, coverage_angle_rad):
    sat = np.asarray(satellite_ecef_km, dtype=float)
    sat_unit = sat / np.linalg.norm(sat, axis=1, keepdims=True)
    ground = np.asarray(ground_unit_vectors, dtype=float)
    return np.count_nonzero(
        ground @ sat_unit.T >= math.cos(coverage_angle_rad),
        axis=1,
    )
```

- [ ] **Step 3: Define fidelity and result dataclasses**

```python
@dataclass(frozen=True)
class MotherGrid:
    times_s: np.ndarray
    coverage_ground_unit: np.ndarray
    coverage_weights: np.ndarray
    communication_ground_ecef_km: np.ndarray
    communication_sample_weight: float = 1.0


@dataclass(frozen=True)
class FidelityGrid:
    name: str
    time_indices: np.ndarray
    coverage_point_indices: np.ndarray
    communication_point_indices: np.ndarray


@dataclass
class JointEvaluationState:
    coverage_progress: WeightedCoverageProgress
    service_progress: ServiceProgress
    processed_coverage_keys: set[tuple[int, int]]
    processed_od_keys: set[tuple[int, int, int]]


@dataclass(frozen=True)
class JointEvaluation:
    status: str
    c1: float
    c2: float
    p30_reachable: float
    p30_all: float
    reachable_count: int
    late_reachable_count: int
    unreachable_count: int
    max_delay_s: float | None
    processed_times: int
    message: str
```

- [ ] **Step 4: Write a failing single-propagation test**

```python
def test_joint_evaluator_propagates_each_time_once(monkeypatch):
    calls = []
    real = q3_joint_evaluator.satellite_positions

    def counted(*args, **kwargs):
        calls.append(float(args[1]))
        return real(*args, **kwargs)

    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", counted)
    params = ConstellationParams(planes=2, sats_per_plane=3, phase_factor=0, inclination_deg=30.0)
    cfg = Q3Config(coverage_angle_rad=math.pi, isl_max_distance_km=1e9)
    coverage_ground = np.array([[1.0, 0.0, 0.0]])
    communication_ground = ground_ecef(
        np.array([0.0, 10.0]), np.array([0.0, 10.0]), radius_km=cfg.earth_radius_km
    )
    mother_grid = MotherGrid(
        times_s=np.array([0.0, 60.0]),
        coverage_ground_unit=coverage_ground,
        coverage_weights=np.array([1.0]),
        communication_ground_ecef_km=communication_ground,
    )
    fidelity = FidelityGrid(
        name="test",
        time_indices=np.array([0, 1]),
        coverage_point_indices=np.array([0]),
        communication_point_indices=np.array([0, 1]),
    )
    evaluation, state = evaluate_joint_candidate(
        params,
        mother_grid=mother_grid,
        fidelity=fidelity,
        config=cfg,
    )
    assert calls == list(mother_grid.times_s)
    assert evaluation.processed_times == len(fidelity.time_indices)
```

- [ ] **Step 5: Implement streaming joint evaluation**

Implementation order inside each time step:

```python
for time_index in fidelity.time_indices:
    time_s = mother_grid.times_s[time_index]
    r_eci, r_ecef = satellite_positions(params, float(time_s), config)
    counts = coverage_counts_from_ecef(
        r_ecef,
        mother_grid.coverage_ground_unit[fidelity.coverage_point_indices],
        coverage_angle_rad=config.access_angle_rad,
    )
    _update_weighted_coverage(
        counts,
        mother_grid.coverage_weights[fidelity.coverage_point_indices],
        coverage_progress,
    )
    if not coverage_progress.can_still_pass():
        return rejected("coverage_upper_bound")

    access_sets = access_sets_naive(
        r_ecef,
        mother_grid.communication_ground_ecef_km[fidelity.communication_point_indices],
        config.access_angle_rad,
    )
    already_counted_unreachable = _update_empty_access_failures(
        access_sets,
        service_progress,
        sample_weight=mother_grid.communication_sample_weight,
    )
    if not service_progress.can_still_pass_all():
        return rejected("p30_all_upper_bound")

    graph = build_isl_graph(r_eci, params, config=config, method=simulation.topology_method)
    delay_matrix = batched_ground_delay_matrix(
        graph,
        access_sets,
        r_ecef,
        mother_grid.communication_ground_ecef_km[fidelity.communication_point_indices],
        c_km_s=config.speed_of_light_km_s,
    )
    _update_service_from_delay_matrix(
        delay_matrix,
        service_progress,
        sample_weight=mother_grid.communication_sample_weight,
        already_counted_unreachable=already_counted_unreachable,
        delay_limit_s=config.delay_limit_s,
    )
    if not service_progress.can_still_pass():
        return rejected("communication_upper_bound")
```

At completion, calculate exact sampled `c1`, `c2`, `p30_reachable`, `p30_all`, integer late budget and diagnostic maximum delay.

- [ ] **Step 6: Add quasi-strict boundary tests**

```python
def test_joint_result_accepts_exact_late_budget_boundary():
    delays = np.full(1000, 0.020)
    delays[0] = 0.040
    metrics = summarize_service_delays(delays, delay_limit_s=0.030)
    assert metrics.p30_reachable == pytest.approx(0.999)
    assert metrics.feasible_reachable


def test_joint_result_rejects_one_over_late_budget():
    delays = np.full(1000, 0.020)
    delays[:2] = 0.040
    metrics = summarize_service_delays(delays, delay_limit_s=0.030)
    assert not metrics.feasible_reachable
```

- [ ] **Step 7: Run Task 3 tests and verify no repeated propagation**

Expected: all correctness tests PASS and propagation count equals the time-grid length.

---

### Task 4: 多保真候选状态机与星数层结论

**Files:**
- Modify: `第一次/代码/问题三/q3_joint_search.py`
- Modify: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- Consumes: `JointEvaluation`
- Produces: `CandidateStatus`, `StageOutcome`, `CandidateAuditRecord`, `LayerConclusion`
- Preserves: `search_constellations(config: JointSearchConfig, coverage_evaluator: Callable[[ConstellationParams], CoverageEvaluation], communication_evaluator: Callable[[ConstellationParams], CommunicationEvaluation], *, topology_filter: Callable[[ConstellationParams], bool] | None = None, lower_bound_filter: Callable[[ConstellationParams], bool] | None = None) -> SearchResult` and its existing tests.

- [ ] **Step 1: Write failing tests for deferred versus rejected semantics**

```python
def test_proxy_failure_is_deferred_not_rejected():
    outcome = classify_stage_outcome(
        fidelity="low",
        feasible=False,
        strict_evidence=False,
        reason="proxy_score_below_cutoff",
    )
    assert outcome.status == "deferred"


def test_strict_upper_bound_failure_is_rejected():
    outcome = classify_stage_outcome(
        fidelity="low",
        feasible=False,
        strict_evidence=True,
        reason="p30_all_upper_bound",
    )
    assert outcome.status == "rejected"
```

- [ ] **Step 2: Implement status dataclasses and classifier**

```python
CandidateStatus = Literal[
    "active", "deferred", "rejected", "verified", "numerical_error"
]

@dataclass(frozen=True)
class StageOutcome:
    status: CandidateStatus
    reason: str
    strict_evidence: bool
    fidelity: str


def classify_stage_outcome(*, fidelity, feasible, strict_evidence, reason):
    if feasible and fidelity == "high":
        return StageOutcome("verified", reason, strict_evidence, fidelity)
    if feasible:
        return StageOutcome("active", reason, strict_evidence, fidelity)
    status = "rejected" if strict_evidence else "deferred"
    return StageOutcome(status, reason, strict_evidence, fidelity)
```

- [ ] **Step 3: Write failing layer-conclusion tests**

```python
def test_layer_with_deferred_candidate_is_inconclusive():
    conclusion = conclude_star_layer([
        audit_record("rejected"),
        audit_record("deferred"),
    ])
    assert conclusion.status == "inconclusive"


def test_layer_is_infeasible_only_when_every_candidate_is_rejected():
    conclusion = conclude_star_layer([
        audit_record("rejected"),
        audit_record("rejected"),
    ])
    assert conclusion.status == "infeasible"


def test_layer_with_verified_feasible_candidate_returns_feasible_discrete():
    conclusion = conclude_star_layer([
        audit_record("rejected"),
        audit_record("verified", feasible=True),
    ])
    assert conclusion.status == "feasible_discrete"
```

- [ ] **Step 4: Implement layer conclusion and deterministic ranking**

Ranking key:

```python
(
    record.status == "verified" and record.feasible,
    record.p30_reachable - 0.999,
    record.p30_all - 0.95,
    record.c1 - 0.999,
    record.c2 - 0.95,
    -record.max_delay_s,
)
```

Return `inconclusive` whenever any candidate is `active`, `deferred` or `numerical_error` and no accepted final conclusion can be proven.

- [ ] **Step 5: Add a callback-order test for cost-aware strict filters**

Use fake filters with recorded call order. Verify that a filter with higher `observed_rejection_rate / mean_cost_s` runs first only when its declared dependencies are satisfied.

- [ ] **Step 6: Run existing and new search tests**

Expected: legacy `search_constellations` behavior remains green; new state tests PASS.

---

### Task 5: 联合搜索 CLI、发现/核验与检查点

**Files:**
- Create: `第一次/代码/问题三/run_q3_joint_search.py`
- Modify: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- Consumes: Problem 2 `fine_records.csv`, `generate_mn_layers`, `evaluate_joint_candidate`
- Produces CLI flags: `--mode discover|certify|both`, `--s-lb`, `--s-max`, `--workers`, `--resume`, fidelity grid arguments.
- Produces the six output files from the design specification.

- [ ] **Step 1: Write failing cache-loader and checkpoint tests**

```python
def test_discovery_cache_loader_deduplicates_constellations(tmp_path):
    path = tmp_path / "fine_records.csv"
    path.write_text(
        "S,M,N,F,i,u0,C1,C2\n1480,37,40,31,50,0,1,0.96\n"
        "1480,37,40,31,50,0,1,0.97\n",
        encoding="utf-8",
    )
    records = load_q2_discovery_candidates(path, c1_min=0.999, c2_min=0.95)
    assert len(records) == 1
    assert records[0].c2 == pytest.approx(0.97)


def test_resume_rejects_mismatched_config_digest(tmp_path):
    checkpoint = tmp_path / "joint_checkpoint.jsonl"
    append_checkpoint(checkpoint, {"config_digest": "abc", "candidate": "x"})
    with pytest.raises(ValueError, match="config digest"):
        load_checkpoint(checkpoint, expected_config_digest="def")
```

- [ ] **Step 2: Implement deterministic candidate serialization and digest**

Use sorted JSON with SHA-256 over all model constants, grids, thresholds and code schema version. Candidate keys must format floats with round-trip-safe JSON numbers, not rounded display values.

- [ ] **Step 3: Implement discovery mode**

Flow:

```text
load q2 fine cache
filter C1/C2
deduplicate exact constellation parameter tuple
sort by S then coverage margin
evaluate low -> medium -> high until first feasible S upper bound
write every stage immediately
```

- [ ] **Step 4: Implement certification mode**

Flow:

```text
generate all configured realizable star layers from S_LB to min(S_max, S_UB)
apply structural strict filters
rank active candidates with low-fidelity scores
evaluate strict bounds and nested fidelity levels
process deferred queue before declaring a lower layer infeasible
stop after the first fully concluded feasible layer
```

- [ ] **Step 5: Implement process-level parallelism safely**

Before importing NumPy/SciPy in workers, set:

```python
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
```

Use `ProcessPoolExecutor(max_workers=args.workers)` with deterministic candidate sequence numbers. Parent process alone writes CSV/JSONL records in sequence-number order.

- [ ] **Step 6: Add CLI smoke test on a tiny constellation range**

Run the script with a temporary output directory, one worker, one time point and a tiny grid. Assert the presence and schemas of:

```text
joint_candidate_records.csv
joint_stage_timing.csv
joint_checkpoint.jsonl
joint_layer_summary.csv
joint_summary.json
joint_report.md
```

- [ ] **Step 7: Verify resume determinism**

Interrupt after a fixed candidate count using a test-only injected stop callback, resume, and compare normalized outputs with a continuous run. Expected: identical candidate keys, statuses and summary; timing columns may differ.

---

### Task 6: 更新 21/22 号模型文档与 README

**Files:**
- Modify: `第一次/问题分析/星链系统-文献驱动版/21-问题三参数化求解模型.md`
- Modify: `第一次/问题分析/星链系统-文献驱动版/22-问题三求解算法设计.md`
- Modify: `第一次/代码/问题三/README.md`

**Interfaces:**
- Consumes: implemented function names, CLI flags and verified complexity measurements.
- Produces: Obsidian-readable model and algorithm documentation.

- [ ] **Step 1: Update Section 7 and Section 13 of document 21**

Replace conditional-only service probability with both definitions:

```latex
P_{30}^{\mathrm{reach}}
=
\frac{\#\{(A,B,t)\in\mathcal R:T_{AB}(t)\le30\,\mathrm{ms}\}}{|\mathcal R|}
\ge0.999,
```

```latex
P_{30}^{\mathrm{all}}
=
\frac{\#\{(A,B,t):T_{AB}(t)\le30\,\mathrm{ms}\}}{|\mathcal P||\mathcal T|}
\ge0.95.
```

Add the equal-sample budget $n_{\max}=\lfloor0.001R\rfloor$, weighted equivalent, discovery/certification distinction and `inconclusive` conclusion.

- [ ] **Step 2: Replace obsolete strict one-sample rejection language**

Search document 21 globally for:

```text
Tmax<=30
严格最大时延
一旦发现某个可达样本
立即停止
```

Each occurrence must either become a diagnostic metric statement or the new quota-based upper-bound rule. Verify with `rg` that no obsolete hard constraint remains.

- [ ] **Step 3: Add Algorithm L to document 22**

Document:

1. shared snapshot generation;
2. weighted coverage progress;
3. directed augmented graph;
4. batched Dijkstra;
5. dual service quota;
6. candidate state machine;
7. discovery and certification queues;
8. checkpoint and deterministic parallelism.

Include asymptotic complexity without claiming false improvement: the exact high-fidelity order remains dominated by coverage dot products and batched SSSP, while duplicate propagation, Python routing loops and high-fidelity candidate count decrease.

- [ ] **Step 4: Update README with exact commands**

Add:

```powershell
python run_q3_joint_search.py --mode discover --q2-cache ../问题二/results/q2_free_search/fine_records.csv --s-lb 1480 --s-max 1800 --workers 4
python run_q3_joint_search.py --mode certify --resume results/q3_joint/joint_checkpoint.jsonl --workers 4
```

Document SciPy, NumPy and pytest requirements and all output files.

- [ ] **Step 5: Validate Obsidian formatting**

Check:

- Mermaid labels containing punctuation are quoted;
- no `<br/>` appears;
- table math does not contain raw `|` inside LaTeX cells;
- wikilinks resolve by unique filename;
- frontmatter remains intact.

---

### Task 7: Correctness, performance and final verification

**Files:**
- Modify only if verification exposes defects in files from Tasks 1–6.
- Output benchmark records under `第一次/代码/问题三/results/benchmark_joint/`.

**Interfaces:**
- Consumes all completed implementation interfaces.
- Produces benchmark CSV/JSON and verification evidence.

- [ ] **Step 1: Run the full Q3 test suite**

```powershell
& 'C:\Users\Nuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests -q -p no:cacheprovider
```

Expected: zero failures and zero errors.

- [ ] **Step 2: Compile all changed Python modules**

```powershell
& 'C:\Users\Nuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m py_compile q3_joint_search.py q3_batched_routing.py q3_joint_evaluator.py run_q3_joint_search.py tests\test_q3_joint_search.py
```

Expected: exit code 0 and no output.

- [ ] **Step 3: Benchmark old versus new routing on identical snapshots**

Use the existing 1480-star configuration with the same 12 communication ground points and 97 time samples. Record:

```text
backend
snapshot_count
ground_count
od_count
elapsed_s
max_abs_delay_difference_s
```

Acceptance: maximum absolute finite-delay difference $\le10^{-10}$ s and new batched routing elapsed time no greater than one third of the old Python loop time.

- [ ] **Step 4: Benchmark fidelity funnel**

On a fixed cached candidate pool, record counts entering structural, lower-bound, low, medium and high stages. Acceptance: at most 20% of initial candidates enter high fidelity. If this target is missed, report the observed rate without weakening correctness or inventing a speedup claim.

- [ ] **Step 5: Run a small end-to-end discovery plus certification job**

Use a bounded range that completes during verification. Confirm:

- discovery finds or reports no upper bound without claiming infeasibility;
- certification never skips a `deferred` lower-layer candidate;
- result report states `feasible_discrete`, `infeasible` or `inconclusive` consistently with layer records;
- $n_{\max}$ in the report equals `floor(0.001 * reachable_count)`.

- [ ] **Step 6: Inspect the first 50 lines and search residual problems**

Open the first 50 lines of each changed Markdown file, then run global searches for obsolete strict-max hard constraints, placeholder markers, broken Mermaid labels and outdated entry-point names. Fix every match attributable to this task and rerun Steps 1–2.

---

## Completion Criteria

The implementation is complete only when:

1. all new and existing Q3 tests pass;
2. batch and reference routing agree numerically;
3. shared evaluation proves one propagation per candidate/time;
4. `n_max` boundary behavior is tested at 999, 1000, 12782 and 1500 samples;
5. no proxy-only failure can become `rejected`;
6. checkpoint resume is deterministic;
7. documents 21, 22 and README match actual code interfaces;
8. performance claims are backed by saved benchmark output.
