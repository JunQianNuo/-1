# Q2/Q3/Q4 Sensitivity and Monte Carlo Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone `第一次/代码/检验/` package that runs sensitivity analysis and Monte Carlo validation for Problems 2, 3, and 4 without changing their default solvers.

**Architecture:** The package imports existing Q2/Q3/Q4 evaluators through a single path bootstrap module. Each question owns its experiment and returns plain rows plus a summary dictionary; common code owns deterministic seeding, percentile intervals, and UTF-8 CSV/JSON output. The runner dispatches one question or all three and writes only inside the new validation directory.

**Tech Stack:** Python 3, NumPy, Matplotlib, pytest, existing Q2/Q3/Q4 modules.

## Global Constraints

- Create all validation code under `第一次/代码/检验/`.
- Do not change default behavior of `第一次/代码/问题二/`, `第一次/代码/问题三/`, or `第一次/代码/问题四/`.
- Use fixed explicit seeds; every result file records its seed and model parameters.
- Q2 Monte Carlo estimates coverage fractions only; it must not claim strict continuous full coverage.
- Q3 Bootstrap uses time snapshots as blocks; it must not claim an observational confidence interval.
- Q4 output remains a scenario analysis until real coverage/capacity inputs replace smoke inputs.

---

### Task 1: Create shared validation infrastructure

**Files:**
- Create: `第一次/代码/检验/common.py`
- Create: `第一次/代码/检验/tests/conftest.py`
- Create: `第一次/代码/检验/tests/test_common.py`

**Interfaces:**
- Produces `percentile_interval(values, level=0.95) -> tuple[float, float]`.
- Produces `make_rng(seed: int) -> numpy.random.Generator`.
- Produces `write_rows_csv(path, rows, fieldnames)` and `write_json(path, value)`.

- [ ] **Step 1: Write failing deterministic-statistics tests**

```python
def test_percentile_interval_and_seed_are_deterministic():
    from common import make_rng, percentile_interval
    assert percentile_interval([0, 1, 2, 3, 4]) == pytest.approx((0.1, 3.9))
    assert make_rng(7).integers(0, 1000) == make_rng(7).integers(0, 1000)
```

- [ ] **Step 2: Implement common utilities**

```python
def percentile_interval(values, level=0.95):
    data = np.asarray(values, dtype=float)
    if data.ndim != 1 or data.size == 0 or not np.all(np.isfinite(data)):
        raise ValueError("values must be a nonempty finite vector")
    if not 0.0 < level < 1.0:
        raise ValueError("level must lie in (0, 1)")
    alpha = (1.0 - level) / 2.0
    return tuple(float(x) for x in np.quantile(data, [alpha, 1.0 - alpha]))
```

`common.py` also appends `../问题二`, `../问题三`, and `../问题四` to `sys.path` only when absent; it never mutates source files.

- [ ] **Step 3: Run focused tests**

Run: `python -m pytest 检验/tests/test_common.py -q`

Expected: PASS.

### Task 2: Implement Q2 coverage sensitivity and Monte Carlo validation

**Files:**
- Create: `第一次/代码/检验/q2_validation.py`
- Create: `第一次/代码/检验/tests/test_q2_validation.py`

**Interfaces:**
- Produces `sample_area_uniform_region(n, rng, lat_bounds=(4,53), lon_bounds=(73,135)) -> tuple[np.ndarray, np.ndarray]`.
- Produces `run_q2_monte_carlo(params, config, samples, time_samples, replicates, seed) -> list[dict]`.
- Produces `run_q2_sensitivity(params, base_config, lat_deg, lon_deg, times_s) -> list[dict]`.

- [ ] **Step 1: Write failing tests for area-uniform sampling and repeatability**

```python
def test_q2_area_sampler_is_bounded_and_reproducible():
    lat_a, lon_a = sample_area_uniform_region(100, make_rng(3))
    lat_b, lon_b = sample_area_uniform_region(100, make_rng(3))
    assert np.all((4 <= lat_a) & (lat_a <= 53))
    assert np.all((73 <= lon_a) & (lon_a <= 135))
    assert np.array_equal(lat_a, lat_b) and np.array_equal(lon_a, lon_b)
```

- [ ] **Step 2: Implement Q2 experiment functions**

For every replicate, draw latitude by uniform sampling in `sin(latitude)`, longitude uniformly, and times uniformly over one sidereal day. Call `q2_constellation.evaluate_constellation`; return `C1`, `C2`, `c_min`, `max_gap_s`, replicate id, and seed. The sensitivity function must run the seven one-factor configurations `h={525,550,575}` and `r_g={480,506,530}`, changing exactly one parameter from the baseline per row.

- [ ] **Step 3: Add a tiny-grid integration test**

```python
def test_q2_monte_carlo_returns_requested_replications():
    rows = run_q2_monte_carlo(TINY_PARAMS, CoverageConfig(), 8, 4, 3, 11)
    assert len(rows) == 3
    assert {row["replicate"] for row in rows} == {0, 1, 2}
```

- [ ] **Step 4: Run Q2 validation tests**

Run: `python -m pytest 检验/tests/test_q2_validation.py -q`

Expected: PASS.

### Task 3: Implement Q3 parameter sensitivity and block bootstrap

**Files:**
- Create: `第一次/代码/检验/q3_validation.py`
- Create: `第一次/代码/检验/tests/test_q3_validation.py`

**Interfaces:**
- Produces `summarize_delay_blocks(delay_blocks, limit_s=0.03) -> np.ndarray` with one all-sample rate per time block.
- Produces `bootstrap_time_blocks(block_rates, replicates, seed) -> list[float]`.
- Produces `run_q3_sensitivity(params, mother_grid, fidelity, config, simulation) -> list[dict]`.

- [ ] **Step 1: Write failing block-bootstrap tests**

```python
def test_q3_block_bootstrap_is_seeded_and_preserves_constant_rate():
    rates = np.array([.8, .8, .8])
    draws = bootstrap_time_blocks(rates, replicates=20, seed=5)
    assert draws == pytest.approx([.8] * 20)
```

- [ ] **Step 2: Implement delay-block and sensitivity functions**

`run_q3_sensitivity` must construct exactly five rows: baseline plus `processing_delay_s={0,0.001}` and `isl_max_distance_km={4500,5500}` one factor at a time. Each row calls `evaluate_joint_candidate` with a full selected fidelity grid and returns coverage, `p30_all`, `p30_reachable`, reachability counts, and maximum delay. It must not pass any P30 feasibility threshold.

- [ ] **Step 3: Add a monkeypatched evaluator integration test**

```python
def test_q3_sensitivity_keeps_baseline_and_six_one_factor_rows(monkeypatch):
    monkeypatch.setattr(q3_validation, "evaluate_joint_candidate", fake_evaluate)
    rows = q3_validation.run_q3_sensitivity(TINY_PARAMS, TINY_MOTHER, TINY_FIDELITY, Q3Config(), SimulationConfig())
    assert len(rows) == 5
    assert rows[0]["scenario"] == "baseline"
```

The test expects five rows because the two physical parameter families have two alternatives each plus the baseline.

- [ ] **Step 4: Run Q3 validation tests**

Run: `python -m pytest 检验/tests/test_q3_validation.py -q`

Expected: PASS.

### Task 4: Implement Q4 scenario sensitivity and annual-event Monte Carlo

**Files:**
- Create: `第一次/代码/检验/q4_validation.py`
- Create: `第一次/代码/检验/tests/test_q4_validation.py`

**Interfaces:**
- Produces `simulate_annual_events(satellite_count, annual_conjunction_rate, trigger_probability, feasible_probability, failure_probability, replicates, seed) -> list[dict]`.
- Produces `run_q4_sensitivity(satellite_count, environment, avoidance, mission) -> list[dict]`.

- [ ] **Step 1: Write failing Poisson-event tests**

```python
def test_q4_annual_event_simulation_is_nonnegative_and_seeded():
    rows_a = simulate_annual_events(10, 2.0, .5, 1.0, .1, 5, 19)
    rows_b = simulate_annual_events(10, 2.0, .5, 1.0, .1, 5, 19)
    assert rows_a == rows_b
    assert all(row["avoidances"] >= 0 and row["failures"] >= 0 for row in rows_a)
```

- [ ] **Step 2: Implement annual events and sensitivity rows**

For one annual replicate, sample conjunctions with `Poisson(S * annual_conjunction_rate)`, triggered feasible avoidances with binomial thinning, and failures with `Binomial(S, failure_probability)`. The sensitivity table contains baseline plus the two alternatives for debris density factor, relative speed, threshold, and capacity reduction. All rows explicitly record `satellite_count`; this supports the 1302/1480/1680 scenario comparison without claiming that the smoke coverage input is final.

- [ ] **Step 3: Add sensitivity monotonicity test**

```python
def test_q4_higher_debris_density_increases_expected_avoidances():
    rows = run_q4_sensitivity(1480, DebrisEnvironment(), AvoidanceParameters(), MissionParameters(1480))
    low = next(row for row in rows if row["scenario"] == "density_x0.5")
    high = next(row for row in rows if row["scenario"] == "density_x2")
    assert high["annual_conjunction_rate"] > low["annual_conjunction_rate"]
```

- [ ] **Step 4: Run Q4 validation tests**

Run: `python -m pytest 检验/tests/test_q4_validation.py -q`

Expected: PASS.

### Task 5: Add runner, outputs, figures, and documentation

**Files:**
- Create: `第一次/代码/检验/run_validation.py`
- Create: `第一次/代码/检验/README.md`
- Modify: `第一次/问题分析/星链系统-文献驱动版/09-问题二假设与指标推导.md`
- Modify: `第一次/问题分析/星链系统-文献驱动版/21-问题三参数化求解模型.md`
- Modify: `第一次/问题分析/星链系统-文献驱动版/24-问题四参数化求解模型.md`

**Interfaces:**
- CLI: `python run_validation.py --question {q2,q3,q4,all} --replicates N --seed N --out PATH`.
- Writes `<out>/<question>/sensitivity.csv`, `<out>/<question>/monte_carlo.csv`, `<out>/<question>/summary.json`, and one PNG figure.

- [ ] **Step 1: Write runner parsing test**

```python
def test_validation_runner_accepts_question_and_seed():
    args = run_validation.parse_args(["--question", "q4", "--replicates", "10", "--seed", "2"])
    assert (args.question, args.replicates, args.seed) == ("q4", 10, 2)
```

- [ ] **Step 2: Implement runner and lightweight plots**

The runner writes UTF-8 CSV/JSON and creates: Q2 parameter-versus-coverage plot, Q3 parameter-versus-P30 plot, and Q4 parameter-versus-annual-risk plot. `--quick` selects small sample sizes for smoke tests; normal defaults are Q2 30 replications, Q3 500 bootstrap replications, and Q4 10,000 annual replications.

- [ ] **Step 3: Document exact scope limits**

README must state that Q2 random sampling is not a proof of continuous coverage, Q3 intervals quantify model-sample variability only, and Q4 remains scenario analysis until real coverage/capacity inputs are connected.

- [ ] **Step 4: Run full tests, compilation, and quick smoke**

Run: `python -m pytest 检验/tests -q; python -m py_compile 检验/*.py; python 检验/run_validation.py --question all --quick --out 检验/results/smoke`

Expected: all tests pass, compilation exits 0, and each question has summary/CSV/PNG output.

## Self-Review

- Spec coverage: Tasks 2–4 implement the three required sensitivity and Monte Carlo modules; Task 5 supplies isolated execution, results, figures, and model-document links.
- Placeholder scan: each task has concrete filenames, interfaces, tests, and commands.
- Type consistency: all question modules return list-of-dict rows; common writers and the runner consume only those rows.
