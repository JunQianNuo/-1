# Final Validation Figures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate three paper-ready Chinese final validation figures from the standard Q2/Q3/Q4 sensitivity and Monte Carlo result CSVs.

**Architecture:** Add a focused `final_figures.py` renderer that reads only raw result CSVs, validates their schemas, and writes one 300 dpi composite PNG per question. `run_validation.py` continues to own simulation execution and invokes the renderer only after the selected question has written its CSVs; no original Q2/Q3/Q4 solver changes are allowed.

**Tech Stack:** Python 3, NumPy, Pillow, pytest, existing `检验` CSV writers.

## Global Constraints

- Modify only `第一次/代码/检验/` for code and tests; leave original problem solvers unchanged.
- The three final figures are named `fig_q2_validation.png`, `fig_q3_validation.png`, and `fig_q4_validation.png` under `<out>/figures/`, saved at 300 dpi.
- Use a verified Chinese system font (`msyh.ttc`, `msyhbd.ttc`, or `simhei.ttf`); raise `RuntimeError` if none is usable.
- Render from raw `sensitivity.csv` and `monte_carlo.csv`, never summary JSON or `results/smoke/` values.
- Standard data: Q2 uses 30 replications; Q3 uses the 289×832×30 saturation-study grid and 500 time-block bootstraps; Q4 uses 10,000 annual trajectories.
- Q2 figure must say random sampling is not strict continuous coverage proof; Q3 must say the interval is model-snapshot variability; Q4 must say scenario analysis.
- Current workspace has no Git repository, so do not fabricate commits.

---

### Task 1: Add raw-CSV figure renderer and schema tests

**Files:**
- Create: `第一次/代码/检验/final_figures.py`
- Modify: `第一次/代码/检验/tests/test_runner.py`

**Interfaces:**
- Produces `generate_final_figure(question: str, results_dir: Path) -> Path`.
- Consumes `<results_dir>/<question>/sensitivity.csv` and `monte_carlo.csv`.
- Produces one high-resolution PNG in `<results_dir>/figures/`.

- [ ] **Step 1: Write failing figure-generation tests**

```python
def test_final_figure_builder_writes_paper_resolution_pngs(tmp_path):
    from final_figures import generate_final_figure
    from PIL import Image

    _write_all_minimal_q2_csvs(tmp_path)
    path = generate_final_figure("q2", tmp_path)
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.width >= 1800 and image.height >= 1000


def test_final_figure_builder_rejects_missing_required_column(tmp_path):
    from final_figures import generate_final_figure

    _write_csv(tmp_path / "q3" / "sensitivity.csv", [{"scenario": "baseline"}])
    _write_csv(tmp_path / "q3" / "monte_carlo.csv", [{"replicate": 0, "p30_all_bootstrap": .8}])
    with pytest.raises(ValueError, match="p30_all"):
        generate_final_figure("q3", tmp_path)
```

- [ ] **Step 2: Run the focused test and verify failure**

Run:

```powershell
$py='C:\Users\Nuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m pytest '检验\tests\test_runner.py' -q -p no:cacheprovider
```

Expected: FAIL because `final_figures` does not exist.

- [ ] **Step 3: Implement CSV loading, font selection, canvas primitives, and Q2 renderer**

```python
def generate_final_figure(question: str, results_dir: Path) -> Path:
    builders = {"q2": _draw_q2, "q3": _draw_q3, "q4": _draw_q4}
    if question not in builders:
        raise ValueError(f"unknown question: {question}")
    sensitivity = _read_csv(results_dir / question / "sensitivity.csv")
    monte_carlo = _read_csv(results_dir / question / "monte_carlo.csv")
    return builders[question](sensitivity, monte_carlo, results_dir / "figures")
```

Implement `_cjk_font(size)` by trying `C:\Windows\Fonts\msyh.ttc`, then `msyhbd.ttc`, then `simhei.ttf`; attempt `ImageFont.truetype` and raise `RuntimeError("未找到可用中文字体")` only after all candidates fail. Use 2400×1350 RGB canvases, `image.save(path, "PNG", dpi=(300, 300))`, labeled axes, fitted text, and fixed colors. `_draw_q2` uses a left sensitivity panel for C1/C2 and a right dot-whisker panel for raw-replicate 2.5%–97.5% intervals, with the strict-coverage interpretation note at the bottom.

- [ ] **Step 4: Run renderer tests and inspect the test image**

Run the focused test command from Step 2. Expected: PASS. Open its generated Q2 PNG and check Chinese glyphs, panel borders, labels, and interval whiskers are neither clipped nor garbled.

### Task 2: Implement Q3 and Q4 final panels

**Files:**
- Modify: `第一次/代码/检验/final_figures.py`
- Modify: `第一次/代码/检验/tests/test_runner.py`

**Interfaces:**
- `_draw_q3(sensitivity_rows, monte_carlo_rows, figures_dir) -> Path` requires `candidate`, `scenario`, and `p30_all` / `p30_all_bootstrap` columns.
- `_draw_q4(sensitivity_rows, monte_carlo_rows, figures_dir) -> Path` requires `candidate`, `scenario`, `annual_avoidances`, `conjunctions`, and `avoidances` columns.

- [ ] **Step 1: Write failing Q3/Q4 output tests**

```python
@pytest.mark.parametrize("question", ["q3", "q4"])
def test_final_figure_builder_writes_q3_and_q4_pngs(tmp_path, question):
    from final_figures import generate_final_figure

    _write_minimal_rows_for(question, tmp_path)
    path = generate_final_figure(question, tmp_path)
    assert path.name == f"fig_{question}_validation.png"
    assert path.is_file()
```

- [ ] **Step 2: Run the new tests and verify failure**

Run the Step 1 test with `-q -p no:cacheprovider`. Expected: FAIL because the dispatcher lacks Q3/Q4 builders.

- [ ] **Step 3: Implement the two composite figures**

`_draw_q3` draws all candidate sensitivity lines in the left panel and a red horizontal 0.95 reference line; the right panel draws one dot and 2.5%–97.5% time-block Bootstrap whisker per candidate, with the note “区间反映模型快照重抽样波动”. `_draw_q4` draws annual avoidance sensitivity by scenario and candidate in the left panel; the right panel uses a log-scale-equivalent transformed vertical coordinate for raw annual conjunction and avoidance counts, with separate colored interval markers and the note “模型情景分析，非实测轨道风险预测”. Both builders validate every required field before drawing and write exactly the required filename at 300 dpi.

- [ ] **Step 4: Run all figure tests**

Run:

```powershell
& $py -m pytest '检验\tests\test_runner.py' -q -p no:cacheprovider
```

Expected: PASS, including Q2/Q3/Q4 filenames, resolution, and invalid-schema behavior.

### Task 3: Integrate final figures with the validation runner

**Files:**
- Modify: `第一次/代码/检验/run_validation.py`
- Modify: `第一次/代码/检验/tests/test_runner.py`
- Modify: `第一次/代码/检验/README.md`

**Interfaces:**
- `main()` calls `generate_final_figure(question, output_dir)` after each selected question writes both CSV files.
- Each question run writes its final figure into `<out>/figures/`, including quick-mode runs; quick-mode figures retain their mode limitation in `summary.json` and are never named as formal results by documentation.

- [ ] **Step 1: Write a failing runner integration assertion**

```python
def test_runner_writes_q4_final_figure_in_quick_mode(tmp_path):
    from run_validation import run_q4_validation

    run_q4_validation(tmp_path, replicates=3, seed=7, quick=True)
    assert (tmp_path / "figures" / "fig_q4_validation.png").is_file()
```

- [ ] **Step 2: Run it and verify failure**

Run the one test above. Expected: FAIL because `run_q4_validation` currently writes only `q4/sensitivity.png`.

- [ ] **Step 3: Wire the renderer after CSV writes and preserve legacy smoke output**

```python
from final_figures import generate_final_figure

# immediately after write_rows_csv(...) calls in each run_q*_validation
final_figure = generate_final_figure("q4", Path(output_dir))
summary["final_figure"] = str(final_figure)
```

Apply the same pattern to Q2 and Q3. Keep `q*/sensitivity.png` unchanged only as an internal diagnostic; update README to identify `<out>/figures/fig_q*_validation.png` as the formal chart interface and to state `--quick` is not paper data.

- [ ] **Step 4: Run the full validation test suite and a quick end-to-end run**

Run:

```powershell
& $py -m pytest '检验\tests' -q -p no:cacheprovider
& $py '检验\run_validation.py' --question all --quick --out '检验\results\final_smoke'
```

Expected: all tests pass and exactly three files exist in `检验/results/final_smoke/figures/`.

### Task 4: Formal data generation and final visual acceptance

**Files:**
- Create at runtime: `第一次/代码/检验/results/final/q2/*`
- Create at runtime: `第一次/代码/检验/results/final/q3/*`
- Create at runtime: `第一次/代码/检验/results/final/q4/*`
- Create at runtime: `第一次/代码/检验/results/final/figures/fig_q2_validation.png`, `fig_q3_validation.png`, `fig_q4_validation.png`

**Interfaces:**
- The formal command uses the standard default replication counts and never passes `--quick`.

- [ ] **Step 1: Re-run static checks before formal computation**

```powershell
& $py -m py_compile '检验\common.py' '检验\q2_validation.py' '检验\q3_validation.py' '检验\q4_validation.py' '检验\final_figures.py' '检验\run_validation.py'
& $py -m pytest '检验\tests' -q -p no:cacheprovider
```

Expected: zero compile errors and all validation tests pass.

- [ ] **Step 2: Launch the standard run**

```powershell
& $py '检验\run_validation.py' --question all --out '检验\results\final'
```

Expected: Q2 and Q4 complete quickly; Q3 may run for a long time because it recomputes 3×5 communication scenarios on the 289×832×30 standard grid.

- [ ] **Step 3: Validate formal outputs and visually inspect all three images**

```powershell
Get-ChildItem '检验\results\final\figures\fig_*_validation.png'
Get-Content -Raw '检验\results\final\validation_summary.json'
```

Open all three PNGs at original resolution. Confirm: Chinese labels render; Q3 contains a 0.95 reference line; Q2/Q3/Q4 right panels contain whiskers; Q4 says scenario analysis; no labels overlap or clip; each plot uses data from `results/final`, not smoke data.

## Self-Review

- Spec coverage: Task 1 provides paper-resolution Chinese rendering and Q2 data traceability; Task 2 adds Q3/Q4 plots and their required notes; Task 3 integrates the runner and documents the formal output; Task 4 creates and accepts the actual final data and figures.
- Placeholder scan: no deferred implementation language, undefined interfaces, or unbounded chart requirements remain.
- Type consistency: `generate_final_figure(question: str, results_dir: Path) -> Path` is used uniformly by the runner and all tests; all builders consume raw CSV row mappings.
