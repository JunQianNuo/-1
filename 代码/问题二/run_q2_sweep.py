"""Focused sweep: find single-coverage feasible S and then double-coverage.

Strategy: only evaluate factor pairs with N >= 40 (along-track swath criterion).
Progressively sweep S, stop when feasible, then refine.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import time as time_mod
from pathlib import Path

import numpy as np

import q2_constellation as q2

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "sweep"
FIGS = ROOT / "figures"


def good_factor_pairs(s: int) -> list[tuple[int, int]]:
    """Factor pairs (M, N) with N >= 40, sorted by increasing M."""
    pairs = []
    for m in range(1, s + 1):
        if s % m == 0:
            n = s // m
            if n >= 40:
                pairs.append((m, n))
    return pairs


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    config = q2.CoverageConfig()
    lat, lon = q2.make_latlon_grid(step_deg=3.0)
    times = q2.make_time_grid(duration_s=6 * 3600, step_s=120.0)
    inclinations = (48.5, 50.0, 52.0, 54.0, 56.0, 58.0, 60.0)
    phase_res = 30.0  # coarse Ω₀, u₀ sampling to keep search tractable

    print(f"Grid: {len(lat)} points, Time: {len(times)} steps @ 120s")
    print(f"Inclinations: {inclinations}")
    print(f"Phase res for Ω₀,u₀: {phase_res}°")
    print(f"{'='*70}")

    all_records: list[dict] = []
    best_feasible: q2.EvaluationResult | None = None
    t0 = time_mod.perf_counter()
    total_eval = 0

    for s in range(40, 401, 10):
        pairs = good_factor_pairs(s)
        if not pairs:
            continue
        print(f"\nS={s}: factor pairs={pairs}")

        s_best: q2.EvaluationResult | None = None
        s_best_cmin = -1
        s_eval = 0

        for m, n in pairs:
            omega_vals, u_vals = q2.phase_grid(m, n, phase_res)
            for f in range(m):
                for inc in inclinations:
                    for omega0 in omega_vals:
                        for u0 in u_vals:
                            params = q2.ConstellationParams(m, n, f, float(inc), float(omega0), float(u0))
                            result = q2.evaluate_constellation(params, lat, lon, times, config)
                            s_eval += 1
                            all_records.append(q2.evaluation_record(result))

                            if result.c_min > s_best_cmin or (
                                result.c_min == s_best_cmin
                                and (s_best is None or result.coverage_rate_q1 > s_best.coverage_rate_q1)
                            ):
                                s_best_cmin = result.c_min
                                s_best = result

        total_eval += s_eval
        elapsed = time_mod.perf_counter() - t0
        print(f"  evaluated={s_eval}  best_cmin={s_best_cmin}  "
              f"best_C1={s_best.coverage_rate_q1:.4f}  "
              f"best_params=M={s_best.params.planes},N={s_best.params.sats_per_plane},"
              f"F={s_best.params.phase_factor},i={s_best.params.inclination_deg}  "
              f"total_time={elapsed:.0f}s")

        if s_best_cmin >= 1:
            best_feasible = s_best
            print(f"\n>>> FEASIBLE at S={s} <<<")
            break

    # Save sweep records
    if all_records:
        fieldnames = list(all_records[0].keys())
        with (OUT / "sweep_all.csv").open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(all_records)

    if best_feasible is None:
        print(f"\nNo feasible found up to S=400. Total: {total_eval} evals, "
              f"{time_mod.perf_counter()-t0:.0f}s")
        _save_summary(None, total_eval, time_mod.perf_counter() - t0, OUT)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Phase 2: medium verification at feasible S
    # ------------------------------------------------------------------
    s1 = best_feasible.params.total_satellites
    print(f"\nPhase 2: medium-grid verification at S={s1}")

    lat_m, lon_m = q2.make_latlon_grid(step_deg=1.0)
    times_m = q2.make_time_grid(duration_s=24 * 3600, step_s=60.0)
    print(f"  grid: {len(lat_m)} points, time: {len(times_m)} steps @ 60s")

    search2 = q2.search_single_coverage(
        lat_deg=lat_m, lon_deg=lon_m, times_s=times_m,
        start_total=s1, stop_total=s1,
        inclinations_deg=inclinations,
        phase_resolution_deg=5.0,
        stop_on_feasible=True,
        config=config,
    )

    if search2.first_feasible:
        best = search2.first_feasible
        print(f"  [OK] Medium-grid PASSED: c_min={best.c_min}, C1={best.coverage_rate_q1:.4f}")
    else:
        best = best_feasible
        print(f"  [WARN] Medium-grid NOT feasible — using coarse best")

    q2.save_result_summary(best, OUT / "phase2_single_summary.json")
    _plot(best, "phase2_single", FIGS)

    # ------------------------------------------------------------------
    # Phase 3: fine-grid final check
    # ------------------------------------------------------------------
    print(f"\nPhase 3: fine-grid check at S={best.params.total_satellites}")
    lat_f, lon_f = q2.make_latlon_grid(step_deg=0.5)
    times_f = q2.make_time_grid(duration_s=24 * 3600, step_s=30.0)
    fine = q2.evaluate_constellation(best.params, lat_f, lon_f, times_f, config)
    print(f"  grid: {len(lat_f)} points, time: {len(times_f)} steps")
    print(f"  c_min={fine.c_min}, C1={fine.coverage_rate_q1:.4f}, "
          f"max_gap={fine.max_gap_s:.0f}s")
    q2.save_result_summary(fine, OUT / "phase3_fine_summary.json")
    _plot(fine, "phase3_fine", FIGS)

    # ------------------------------------------------------------------
    # Phase 4: double-coverage search
    # ------------------------------------------------------------------
    s2_start = best.params.total_satellites
    print(f"\nPhase 4: double-coverage search from S={s2_start}")

    lat_c, lon_c = q2.make_latlon_grid(step_deg=3.0)
    times_c = q2.make_time_grid(duration_s=6 * 3600, step_s=120.0)

    for s in range(s2_start, 601, 20):
        pairs = good_factor_pairs(s)
        if not pairs:
            continue
        print(f"  S={s}...", end=" ", flush=True)
        s_best_c2 = 0.0
        s_best_result = None
        for m, n in pairs:
            for f in range(min(m, 3)):
                for inc in inclinations:
                    params = q2.ConstellationParams(m, n, f, float(inc))
                    result = q2.evaluate_constellation(params, lat_c, lon_c, times_c, config)
                    if result.strict_double_time_rate > s_best_c2:
                        s_best_c2 = result.strict_double_time_rate
                        s_best_result = result

        print(f"C2_strict={s_best_c2:.4f}", flush=True)
        if s_best_c2 >= 0.95:
            print(f">>> DOUBLE-COVERAGE FEASIBLE at S={s} <<<")
            q2.save_result_summary(s_best_result, OUT / "phase4_double_summary.json")
            _plot(s_best_result, "phase4_double", FIGS)
            break

    t_total = time_mod.perf_counter() - t0
    print(f"\nDone. Total time: {t_total:.0f}s")
    _save_summary(best_feasible, total_eval, t_total, OUT)


def _plot(result, tag: str, figs_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # Min count map
    min_counts = result.counts.min(axis=1)
    vmax = max(1, int(np.max(min_counts)))
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(result.lon_deg, result.lat_deg, c=min_counts, s=30,
               cmap="viridis", vmin=0, vmax=vmax)
    ax.set_xlabel("lon / deg E"); ax.set_ylabel("lat / deg N")
    ax.set_title(f"{tag}: min coverage count")
    fig.colorbar(ax.collections[0], ax=ax)
    fig.savefig(figs_dir / f"{tag}_map.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Time series
    min_t = result.counts.min(axis=0)
    mean_t = result.weights @ result.counts
    fig, ax = plt.subplots(figsize=(7, 4))
    t_h = result.times_s / 3600
    ax.plot(t_h, min_t, label="min")
    ax.plot(t_h, mean_t, label="weighted mean")
    ax.set_xlabel("time / h"); ax.set_ylabel("coverage count")
    ax.set_title(f"{tag}: coverage time series")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.savefig(figs_dir / f"{tag}_ts.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def _save_summary(feasible, evals, elapsed, out_dir):
    (out_dir / "sweep_summary.json").write_text(
        json.dumps({
            "feasible_found": feasible is not None,
            "feasible_S": feasible.params.total_satellites if feasible else None,
            "total_evals": evals,
            "elapsed_s": elapsed,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
