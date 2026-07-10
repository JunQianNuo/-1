# Q4 Robustness Algorithms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build scientifically grounded Problem 4 robustness model review, algorithm design, and Python implementation with tests, smoke outputs, and explicit git push scope.

**Architecture:** Keep Problem 4 code isolated under `代码/问题四/`, mirroring the existing Problem 3 modular style. Separate physics/risk formulas, conjunction probability, avoidance decisions, capacity/cost, redundancy availability, and pipeline orchestration into small files with focused interfaces.

**Tech Stack:** Python 3, numpy, pandas, matplotlib, pytest. No required network calls. Use local git only for explicit Problem 4 files.

## Global Constraints

- Do not produce final numerical conclusions before Problem 2 final constellation and coverage matrix are available.
- Keep Problem 4 formulas traceable to local reference documents and already-read literature notes.
- Use TDD: create failing tests before production code.
- Do not stage unrelated Q2/Q3 existing changes during git commit.
- Python is assumed because Problem 3 implementation already uses Python and the project suggested `问题四_求解.py`.

---

### Task 1: Model Scientific Review Documents

**Files:**
- Create: `问题分析/星链系统-文献驱动版/25-问题四模型科学依据审查与修正.md`
- Create: `问题分析/星链系统-文献驱动版/26-问题四求解算法设计与复杂度审查.md`
- Modify: `问题分析/星链系统-文献驱动版/19-问题四问题分析与建模入口.md`
- Modify: `问题分析/星链系统-文献驱动版/23-问题四文献证据与建模依据.md`
- Modify: `问题分析/星链系统-文献驱动版/24-问题四参数化求解模型.md`

**Interfaces:**
- Consumes: Q4 model formulas in document 24 and evidence in document 23.
- Produces: reviewed formulas and algorithm interfaces for code tasks.

- [ ] Write model review with scientific basis, listing accepted formulas, corrected unit conventions, and implementation constraints.
- [ ] Write algorithm design with complexity table and high-efficiency choices.
- [ ] Update prior notes to link to 25 and 26.
- [ ] Verify markdown frontmatter, links, and no stale planned-25 link.

### Task 2: TDD Tests for Q4 Core Algorithms

**Files:**
- Create: `代码/问题四/tests/test_q4_algorithms.py`

**Interfaces:**
- Consumes: planned module APIs.
- Produces: failing tests for modules not yet implemented.

- [ ] Write tests for debris density split, flux rate, exact centered Gaussian Pc case, CPA calculation, avoidance feasibility, capacity/cost, cold standby confidence, and coverage availability.
- [ ] Run `python -m pytest tests/test_q4_algorithms.py -q` from `代码/问题四`.
- [ ] Expected result: fail with `ModuleNotFoundError` or missing functions.

### Task 3: Q4 Core Implementation

**Files:**
- Create: `代码/问题四/q4_config.py`
- Create: `代码/问题四/q4_debris.py`
- Create: `代码/问题四/q4_collision.py`
- Create: `代码/问题四/q4_avoidance.py`
- Create: `代码/问题四/q4_capacity_cost.py`
- Create: `代码/问题四/q4_redundancy.py`

**Interfaces:**
- Produces functions imported by tests:
  - `cumulative_power_law_density`, `split_catalog_density`, `collision_cross_section_km2`, `flux_collision_rate_per_s`, `annual_probability`, `conjunction_event_rate_per_year`
  - `time_to_cpa`, `collision_probability_2d_gaussian`
  - `max_miss_distance_km`, `required_delta_v_mps`, `avoidance_decision`
  - `capacity_loss_ratio`, `avoidance_cost_wanyuan`, `replacement_unit_cost_wanyuan`, `annual_expected_failures`
  - `cold_standby_confidence`, `ground_backup_confidence`, `space_backup_confidence`, `coverage_availability`, `satellite_criticality`

- [ ] Implement minimal production code to satisfy tests.
- [ ] Run focused tests until green.
- [ ] Refactor only within Q4 code.

### Task 4: Pipeline, README, and Smoke Outputs

**Files:**
- Create: `代码/问题四/q4_pipeline.py`
- Create: `代码/问题四/run_q4_pipeline.py`
- Create: `代码/问题四/问题4_求解.py`
- Create: `代码/问题四/README.md`
- Generate: `代码/问题四/results/*`
- Generate: `代码/问题四/figures/*`

**Interfaces:**
- Consumes Q4 core modules.
- Produces smoke result tables and figures explicitly marked non-final.

- [ ] Implement smoke scenario using synthetic/parameterized inputs.
- [ ] Generate CSV/TXT outputs and one or more figures.
- [ ] Run `python 问题4_求解.py` and inspect output.

### Task 5: Verification, Commit, Push

**Files:**
- Stage only Problem 4 documents/code and this plan if appropriate.

**Interfaces:**
- Consumes all prior task outputs.
- Produces git commit and push to current branch if remote is accessible.

- [ ] Run markdown/link checks.
- [ ] Run `python -m pytest tests/test_q4_algorithms.py -q`.
- [ ] Run `python 问题4_求解.py`.
- [ ] Check `git status -sb` from `数学建模/第一次`.
- [ ] Stage explicit Problem 4 files only.
- [ ] Commit with message `feat: add q4 robustness algorithms`.
- [ ] Push current branch with `git push`.
