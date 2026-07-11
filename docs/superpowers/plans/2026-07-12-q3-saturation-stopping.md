# Q3 Performance-Saturation Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Q3's hard 30 ms acceptance thresholds with a coverage-constrained search that returns the smallest satellite count whose 30 ms all-sample service rate has saturated over the following 200 satellites.

**Architecture:** Coverage remains the only rejection criterion in the joint evaluator. A small pure module receives one best high-fidelity observation per satellite-count layer and decides whether the first complete forward window satisfies the two approved marginal-gain limits. The CLI gains a `saturation` mode that evaluates each layer, records its best coverage-feasible high-fidelity candidate, calls the pure decision function, and writes a saturation-specific summary and report.

**Tech Stack:** Python 3, NumPy, SciPy routing already used by the project, pytest, CSV and JSON output.

## Global Constraints

- Keep coverage constraints exactly `C1 >= 0.999` and `C2 >= 0.95`.
- Do not use `P30(reachable)` or `P30(all)` as a rejection condition.
- Use `P30(all)` as the primary ranking metric; tie-break by larger `P30(reachable)`, then smaller maximum delay, then deterministic parameter order.
- Default forward window is 200 satellites; maximum window gain is 0.01; maximum gain per 100 satellites is 0.005.
- A saturation conclusion requires a completed forward window; reaching `S_max` first is an inconclusive result.
- All outputs remain deterministic for one worker and multiple workers.

---

### Task 1: Add a pure saturation-decision module

**Files:**
- Create: `第一次/代码/问题三/q3_saturation.py`
- Modify: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- Produces `SaturationObservation`, `SaturationDecision`, and `first_saturation_decision(observations, forward_window_s=200, max_gain=0.01, max_gain_per_100=0.005)`.
- `observations` contains exactly one high-fidelity, coverage-feasible best record for each completed satellite-count layer and is sorted by `stars`.

- [ ] **Step 1: Write failing tests for the approved boundary and incomplete horizon**

```python
from q3_saturation import SaturationObservation, first_saturation_decision

def test_first_saturation_accepts_exact_one_percentage_point_gain():
    data = [
        SaturationObservation(1700, 0.86, "a", 0.90, 1.0, 0.97, 0.04),
        SaturationObservation(1800, 0.865, "b", 0.90, 1.0, 0.97, 0.04),
        SaturationObservation(1900, 0.87, "c", 0.90, 1.0, 0.97, 0.04),
    ]
    result = first_saturation_decision(data)
    assert result.status == "saturated"
    assert result.selected.stars == 1700
    assert result.window_gain == pytest.approx(0.01)

def test_first_saturation_requires_a_complete_200_satellite_horizon():
    data = [SaturationObservation(1700, 0.86, "a", 0.9, 1.0, 0.97, 0.04)]
    result = first_saturation_decision(data)
    assert result.status == "insufficient_horizon"
    assert result.selected is None
```

- [ ] **Step 2: Run the focused tests and confirm import failure**

Run: `python -m pytest tests/test_q3_joint_search.py -k saturation -q`

Expected: FAIL because `q3_saturation` does not exist.

- [ ] **Step 3: Implement the pure decision types and function**

```python
@dataclass(frozen=True)
class SaturationObservation:
    stars: int
    p30_all: float
    candidate_key: str
    p30_reachable: float
    c1: float
    c2: float
    max_delay_s: float | None

@dataclass(frozen=True)
class SaturationDecision:
    status: str
    selected: SaturationObservation | None
    window_end_stars: int | None
    window_max_p30_all: float | None
    window_gain: float | None
    gain_per_100_stars: float | None

def first_saturation_decision(observations, *, forward_window_s=200,
                              max_gain=0.01, max_gain_per_100=0.005):
    # validate finite inputs and strict increasing stars
    # for each observation with a later observation at stars >= stars + forward_window_s:
    # evaluate all observations whose stars lie in [stars, stars + forward_window_s]
    # return the first candidate satisfying both <= comparisons
    # otherwise return "insufficient_horizon" when no complete window exists,
    # and "not_saturated" when complete windows exist but all fail.
```

The function must calculate `gain_per_100_stars = window_gain / (forward_window_s / 100.0)` and treat equality as saturation.

- [ ] **Step 4: Add tests for rejection, first-point selection, and invalid inputs**

```python
def test_first_saturation_skips_an_early_window_with_excess_gain():
    data = [
        SaturationObservation(1700, .86, "a", .9, 1., .97, .04),
        SaturationObservation(1900, .88, "b", .9, 1., .97, .04),
        SaturationObservation(1920, .88, "c", .9, 1., .97, .04),
        SaturationObservation(2120, .885, "d", .9, 1., .97, .04),
    ]
    assert first_saturation_decision(data).selected.stars == 1900
```

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/test_q3_joint_search.py -k saturation -q`

Expected: PASS.

### Task 2: Make joint evaluation communication-diagnostic only

**Files:**
- Modify: `第一次/代码/问题三/q3_joint_evaluator.py`
- Modify: `第一次/代码/问题三/run_q3_joint_search.py`
- Modify: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- `evaluate_joint_candidate(..., c1_min=0.999, c2_min=0.95)` retains the same result fields.
- A full-grid result is `verified` exactly when coverage passes; its service statistics are always calculated.
- `evaluate_candidate_stages` no longer accepts or passes `eta_reach` / `eta_all`.

- [ ] **Step 1: Write failing tests that a low P30 value is retained, not rejected**

```python
def test_complete_coverage_feasible_candidate_is_verified_even_with_low_p30(monkeypatch):
    # reuse the existing tiny mother grid fixture and route stub
    # route delays contain one value over delay_limit_s
    result, _ = evaluate_joint_candidate(params, mother_grid=mother, fidelity=high)
    assert result.status == "verified"
    assert result.p30_all < 1.0
```

- [ ] **Step 2: Run the focused test and confirm the current threshold rejection**

Run: `python -m pytest tests/test_q3_joint_search.py -k low_p30 -q`

Expected: FAIL because the current evaluator returns `rejected`.

- [ ] **Step 3: Remove service-rate rejection paths while preserving service accounting**

Make these exact behavioral changes:

```python
# q3_joint_evaluator.py
# remove eta_reach and eta_all from public evaluator arguments and state validation
# delete the optimistic_all < eta_all early return
# delete state.service_progress.can_still_pass() early return
# at completion:
feasible = c1 >= c1_min and c2 >= c2_min
status = "verified" if feasible else "rejected"
message = "coverage_pass" if feasible else "coverage_fail"
```

Remove `eta_*` propagation from `evaluate_candidate_stages`, `_evaluate_stage_batch`, `_empty_state`, and all task tuples in `run_q3_joint_search.py`. Keep `p30_reachable`, `p30_all`, reachability counts, and maximum delay in every audit record.

- [ ] **Step 4: Update ranking to prioritize all-sample service rate**

```python
return (
    value("p30_all"), value("p30_reachable"),
    -value("max_delay_s", math.inf),
    float(coverage[0]), float(coverage[1]),
    tuple(-v if isinstance(v, (int, float)) else v for v in _record_parameter_values(row)),
)
```

- [ ] **Step 5: Run evaluator and runner tests**

Run: `python -m pytest tests/test_q3_joint_search.py -q`

Expected: PASS after replacing obsolete eta-threshold assertions with diagnostic-only assertions.

### Task 3: Add saturation search mode, outputs, and reports

**Files:**
- Modify: `第一次/代码/问题三/run_q3_joint_search.py`
- Modify: `第一次/代码/问题三/tests/test_q3_joint_search.py`

**Interfaces:**
- CLI adds `--mode saturation`, `--s-step` (default `20`), `--forward-window-s` (default `200`), `--max-window-gain` (default `0.01`), and `--max-gain-per-100` (default `0.005`).
- `joint_saturation_curve.csv` columns are `S,candidate_key,M,N,F,i,u0,c1,c2,p30_all,p30_reachable,max_delay_s`.
- Summary contains `objective: "p30_all_saturation"`, `saturation_decision`, and `best_candidate`; it contains no communication threshold or `n_max` field.

- [ ] **Step 1: Write a failing CLI parse test**

```python
def test_parse_saturation_defaults():
    args = run_q3_joint_search.parse_args(["--mode", "saturation"])
    assert (args.s_step, args.forward_window_s) == (20, 200)
    assert args.max_window_gain == pytest.approx(.01)
    assert args.max_gain_per_100 == pytest.approx(.005)
```

- [ ] **Step 2: Implement argument validation and mode dispatch**

Add `saturation` to `--mode` choices. Require positive integer `s_step`, positive integer `forward_window_s`, and finite nonnegative gain limits. In `main`, dispatch saturation independently of Q2 cache and write the standard audit/checkpoint files plus the curve CSV.

- [ ] **Step 3: Implement `_run_saturation`**

```python
def _run_saturation(args, mother, fidelities, config, simulation, digest,
                    checkpoint_path, completed, persisted, timing_rows,
                    layer_rows, sequence_counter):
    observations = []
    for layer in generate_mn_layers(_saturation_search_config(args, config, simulation)):
        if (layer.star_count - args.s_lb) % args.s_step:
            continue
        rows = _evaluate_layer_through_high(...)
        best = _best_verified_high_record(rows)
        if best is not None:
            observations.append(_observation_from_record(best))
        decision = first_saturation_decision(
            observations, forward_window_s=args.forward_window_s,
            max_gain=args.max_window_gain,
            max_gain_per_100=args.max_gain_per_100,
        )
        if decision.status == "saturated":
            return decision, observations
    return first_saturation_decision(...), observations
```

`_evaluate_layer_through_high` must run the existing low/medium/high pipeline for one layer. A layer is represented in the curve only by its best high-fidelity record with status `verified`; a layer with no coverage-feasible high result receives a layer summary but no curve row. The saturation decision must use only curve rows and must require an observation at or beyond `S_i + forward_window_s`.

- [ ] **Step 4: Write an integration test using monkeypatched layer results**

```python
def test_saturation_main_writes_curve_and_selects_first_stable_layer(tmp_path, monkeypatch):
    # patch layer evaluation to return P30(all) .86 at 1700, .865 at 1800, .87 at 1900
    code = run_q3_joint_search.main(["--mode", "saturation", "--out", str(tmp_path)])
    summary = json.loads((tmp_path / "joint_summary.json").read_text(encoding="utf-8"))
    assert code == 0
    assert summary["claim"] == "saturated_minimum"
    assert summary["best_candidate"]["S"] == 1700
    assert (tmp_path / "joint_saturation_curve.csv").exists()
```

- [ ] **Step 5: Rewrite report fields for saturation mode**

`_write_report` must emit the coverage hard constraints, objective name, forward-window parameters, decision status, selected scale, window end, window maximum, cumulative gain, and per-100-satellite gain. It must not state P30 thresholds or `n_max`. If no decision is available, state whether the result is `not_saturated` or `insufficient_horizon`.

- [ ] **Step 6: Run all joint-search tests and CLI help**

Run: `python -m pytest tests/test_q3_joint_search.py -q; python run_q3_joint_search.py --help`

Expected: all tests pass and help lists `saturation` plus its four stopping controls.

### Task 4: Synchronize model documentation and validate the implementation

**Files:**
- Modify: `第一次/问题分析/星链系统-文献驱动版/21-问题三参数化求解模型.md`
- Modify: `第一次/问题分析/星链系统-文献驱动版/22-问题三求解算法设计.md`
- Modify: `第一次/代码/问题三/README.md`
- Test: `第一次/代码/问题三/tests/test_q3_joint_search.py`

- [ ] **Step 1: Replace hard P30 constraints with the saturation objective**

Document the coverage feasible set, `P^star(S)`, the 200-satellite forward window, 1 percentage-point cumulative-gain limit, 0.5 percentage-point-per-100-satellite limit, and the `S_max` inconclusive rule. Describe P30(reachable) as a diagnostic tie-breaker.

- [ ] **Step 2: Add the runnable saturation command to README**

```powershell
python run_q3_joint_search.py --mode saturation --s-lb 1440 --s-max 2000 --s-step 20 --forward-window-s 200 --max-window-gain 0.01 --max-gain-per-100 0.005 --workers 4 --out results/q3_saturation
```

State that the command must run at least 200 satellites past any proposed saturation point before a conclusion is valid.

- [ ] **Step 3: Run complete verification**

Run: `python -m pytest tests -q -p no:cacheprovider; python -m py_compile q3_joint_search.py q3_joint_evaluator.py q3_saturation.py run_q3_joint_search.py`

Expected: all tests pass and compilation exits with code 0.

- [ ] **Step 4: Run a small saturation smoke test**

Run: `python run_q3_joint_search.py --mode saturation --s-lb 1440 --s-max 1460 --s-step 20 --duration-s 900 --high-time-step-s 900 --coverage-high-step-deg 25 --communication-high-step-deg 25 --m-min 30 --m-max 60 --n-min 20 --n-max 60 --keep-low 2 --keep-medium 1 --out results/q3_saturation_smoke`

Expected: exit code 0; report says `insufficient_horizon`, and `joint_saturation_curve.csv` plus the normal audit files exist.

## Self-Review

- Spec coverage: Task 2 implements coverage-only feasibility; Task 1 implements the two approved stability inequalities; Task 3 supplies the search controller and reports; Task 4 synchronizes the mathematical and user-facing documentation.
- Placeholder scan: no deferred implementation language is used; each behavior has an explicit interface, test, command, or output schema.
- Type consistency: `SaturationObservation` is created only from high-fidelity, coverage-verified audit rows and is the sole input to `first_saturation_decision`; `SaturationDecision` is the sole source of saturation report fields.
