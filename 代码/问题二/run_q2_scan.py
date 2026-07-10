"""Staged single- and double-coverage search for Problem 2.

This script implements the multi-stage strategy from 10-问题二数值实现方案:

Phase 1 (coarse):   grid 3°,  time 180 s,  find feasible S range.
Phase 2 (medium):   grid 1°,  time  60 s,  verify best candidates.
Phase 3 (fine):     grid 0.5°,time  30 s,  final refinement.

After single-coverage search converges, the script optionally runs a
double-coverage search starting from the single-coverage optimum S_1.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time as time_mod
import warnings
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

import q2_constellation as q2

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
SEARCH_DIR = RESULTS_DIR / "scan"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_float_list(text: str) -> list[float]:
    values = [float(item.strip()) for item in text.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("empty list")
    return values


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Problem 2 staged coverage search.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--single-start", type=int, default=40,
        help="starting total satellites for single-coverage search",
    )
    p.add_argument(
        "--single-stop", type=int, default=150,
        help="maximum total satellites for single-coverage search",
    )
    p.add_argument(
        "--inclinations",
        type=parse_float_list,
        default=parse_float_list("48.5,50,52,54,56,58,60"),
        help="comma-separated inclination candidates in degrees",
    )
    p.add_argument(
        "--phase-coarse", type=float, default=15.0,
        help="phase search resolution in degrees (coarse stage)",
    )
    p.add_argument(
        "--phase-fine", type=float, default=5.0,
        help="phase search resolution in degrees (fine stage)",
    )
    p.add_argument(
        "--max-candidates", type=int, default=0,
        help="candidate cap per S; 0 = no cap",
    )
    p.add_argument(
        "--skip-double",
        action="store_true",
        help="skip double-coverage search after single",
    )
    p.add_argument(
        "--double-start", type=int, default=0,
        help="manual double-coverage start S; 0 = auto (single feasible S)",
    )
    p.add_argument(
        "--double-stop", type=int, default=200,
        help="maximum total satellites for double-coverage search",
    )
    p.add_argument(
        "--duration-hours", type=float, default=23.934,
        help="evaluation duration in hours",
    )
    return p


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------


def setup_matplotlib() -> None:
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans", "Arial",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.linewidth"] = 1.2
    plt.rcParams["lines.linewidth"] = 1.8


def plot_min_count_map(
    result: q2.EvaluationResult,
    path: Path,
    title: str = "各网格点最小覆盖重数",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    min_counts = result.counts.min(axis=1)
    vmax = max(1, int(np.max(min_counts)))

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    sc = ax.scatter(
        result.lon_deg, result.lat_deg,
        c=min_counts, s=42, cmap="viridis", vmin=0, vmax=vmax, edgecolor="none",
    )
    ax.set_xlabel("经度 / °E")
    ax.set_ylabel("纬度 / °N")
    ax.set_title(title)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("最小覆盖重数")
    ticks = range(vmax + 1) if vmax <= 10 else np.linspace(0, vmax, 6)
    cbar.set_ticks(ticks)
    ax.grid(True, linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_time_series(
    result: q2.EvaluationResult,
    path: Path,
    title: str = "覆盖重数时间序列",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    min_count_t = result.counts.min(axis=0)
    weighted_mean_t = result.weights @ result.counts

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    t_hour = result.times_s / 3600.0
    ax.plot(t_hour, min_count_t, label="整区最小覆盖重数")
    ax.plot(t_hour, weighted_mean_t, label="面积加权平均覆盖重数")
    ax.set_xlabel("时间 / h")
    ax.set_ylabel("覆盖重数")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# CSV / JSON I/O
# ---------------------------------------------------------------------------


def write_candidates_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def top_records(records: list[dict], n: int = 10) -> list[dict]:
    return sorted(
        records,
        key=lambda r: (r["c_min"], r["C1"], r["avg_multiplicity"], -r["max_gap_s"]),
        reverse=True,
    )[:n]


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------


def run_stage(
    label: str,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    start_total: int,
    stop_total: int,
    inclinations: Sequence[float],
    phase_res: float,
    max_cand: int | None,
    mode: str = "single",
) -> tuple[q2.SearchRunResult, float]:
    """Run one stage and return (search_result, elapsed_seconds)."""

    t0 = time_mod.perf_counter()
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  S = {start_total} .. {stop_total}")
    print(f"  grid points = {len(lat_deg)}, time steps = {len(times_s)}")
    print(f"  inclinations = {list(inclinations)}")
    print(f"  phase resolution = {phase_res} deg")
    print(f"  max_candidates_per_total = {max_cand}")
    print(f"{'='*60}")

    if mode == "single":
        search = q2.search_single_coverage(
            lat_deg=lat_deg, lon_deg=lon_deg, times_s=times_s,
            start_total=start_total, stop_total=stop_total,
            inclinations_deg=inclinations,
            phase_resolution_deg=phase_res,
            max_candidates_per_total=max_cand,
            stop_on_feasible=True,
        )
    elif mode == "double":
        search = q2.search_double_coverage(
            lat_deg=lat_deg, lon_deg=lon_deg, times_s=times_s,
            start_total=start_total, stop_total=stop_total,
            inclinations_deg=inclinations,
            phase_resolution_deg=phase_res,
            max_candidates_per_total=max_cand,
            stop_on_feasible=True,
        )
    else:
        raise ValueError(f"unknown mode: {mode}")

    elapsed = time_mod.perf_counter() - t0
    feas = "YES" if search.first_feasible is not None else "NO"
    print(f"  evaluated: {search.evaluated_count}  feasible: {feas}  time: {elapsed:.1f} s")
    if search.first_feasible is not None:
        p = search.first_feasible.params
        print(f"  first feasible: M={p.planes} N={p.sats_per_plane} S={p.total_satellites} "
              f"F={p.phase_factor} i={p.inclination_deg}")
    if search.best_result is not None:
        print(f"  best: {search.best_result.metrics}")
    return search, elapsed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = build_parser().parse_args()
    setup_matplotlib()
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)

    config = q2.CoverageConfig()
    max_cand = args.max_candidates if args.max_candidates > 0 else None

    # ------------------------------------------------------------------
    # Phase 1: coarse single-coverage search
    # ------------------------------------------------------------------
    lat_c, lon_c = q2.make_latlon_grid(step_deg=3.0)
    times_c = q2.make_time_grid(
        duration_s=args.duration_hours * 3600.0, step_s=180.0,
    )

    search1, t1 = run_stage(
        label="Phase 1 · Single-coverage coarse search",
        lat_deg=lat_c, lon_deg=lon_c, times_s=times_c,
        start_total=args.single_start, stop_total=args.single_stop,
        inclinations=args.inclinations,
        phase_res=args.phase_coarse,
        max_cand=max_cand,
        mode="single",
    )

    write_candidates_csv(
        sorted(search1.records, key=lambda r: (r["total_satellites"], -r["C1"])),
        SEARCH_DIR / "phase1_single_candidates.csv",
    )
    _write_stage_summary(search1, t1, "phase1", lat_c, times_c, args, SEARCH_DIR)

    if search1.best_result is not None:
        plot_min_count_map(search1.best_result, FIGURES_DIR / "Q2_scan_phase1_map.png")
        plot_time_series(search1.best_result, FIGURES_DIR / "Q2_scan_phase1_ts.png")

    if search1.first_feasible is None:
        print("\n[STOP] No single-coverage feasible solution in Phase 1 range.")
        print("       Try increasing --single-stop or adding inclinations.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Phase 2: medium-grid verification of feasible candidates
    # ------------------------------------------------------------------
    s1_feasible = search1.first_feasible.params.total_satellites
    print(f"\nPhase 1 found feasible at S = {s1_feasible}.  Proceeding to Phase 2.")

    lat_m, lon_m = q2.make_latlon_grid(step_deg=1.0)
    times_m = q2.make_time_grid(
        duration_s=args.duration_hours * 3600.0, step_s=60.0,
    )

    search2, t2 = run_stage(
        label="Phase 2 · Single-coverage medium verification",
        lat_deg=lat_m, lon_deg=lon_m, times_s=times_m,
        start_total=s1_feasible, stop_total=s1_feasible,
        inclinations=args.inclinations,
        phase_res=args.phase_fine,
        max_cand=max_cand,
        mode="single",
    )

    write_candidates_csv(
        sorted(search2.records, key=lambda r: (-r["c_min"], -r["C1"])),
        SEARCH_DIR / "phase2_single_candidates.csv",
    )
    _write_stage_summary(search2, t2, "phase2", lat_m, times_m, args, SEARCH_DIR)

    if search2.best_result is not None:
        plot_min_count_map(search2.best_result, FIGURES_DIR / "Q2_scan_phase2_map.png",
                           title="中网格验证：各网格点最小覆盖重数")
        plot_time_series(search2.best_result, FIGURES_DIR / "Q2_scan_phase2_ts.png",
                         title="中网格验证：覆盖重数时间序列")

    if search2.first_feasible is None:
        print("\n[WARN] Phase 1 feasible solution failed medium-grid verification.")
        print("       Falling back to Phase 1 result as best estimate.")
        best_single = search1.first_feasible
    else:
        best_single = search2.first_feasible

    s1_opt = best_single.params.total_satellites
    print(f"\nSingle-coverage optimum: S1 = {s1_opt}")
    print(f"  params: {best_single.params}")
    print(f"  metrics: {best_single.metrics}")

    # ------------------------------------------------------------------
    # Phase 3: fine grid final verification (best candidate only)
    # ------------------------------------------------------------------
    lat_f, lon_f = q2.make_latlon_grid(step_deg=0.5)
    times_f = q2.make_time_grid(
        duration_s=args.duration_hours * 3600.0, step_s=30.0,
    )
    result_fine = q2.evaluate_constellation(best_single.params, lat_f, lon_f, times_f, config)
    print(f"\nPhase 3 · Fine-grid verification (S1 = {s1_opt}):")
    print(f"  grid points: {len(lat_f)}, time steps: {len(times_f)}")
    print(f"  metrics: {result_fine.metrics}")

    if result_fine.c_min >= 1:
        print("  [OK] Fine-grid verification PASSED.")
    else:
        print("  [WARN] Fine-grid c_min < 1 — candidate may have resolution gaps.")

    plot_min_count_map(result_fine, FIGURES_DIR / "Q2_scan_phase3_map.png",
                       title=f"细网格验证 S={s1_opt}：各网格点最小覆盖重数")
    plot_time_series(result_fine, FIGURES_DIR / "Q2_scan_phase3_ts.png",
                     title=f"细网格验证 S={s1_opt}：覆盖重数时间序列")

    q2.save_result_summary(result_fine, SEARCH_DIR / "phase3_fine_summary.json")

    # ------------------------------------------------------------------
    # Phase 4: double-coverage search (optional)
    # ------------------------------------------------------------------
    if args.skip_double:
        print("\nDouble-coverage search skipped (--skip-double).")
        return

    s2_start = args.double_start if args.double_start > 0 else max(s1_opt, 80)
    print(f"\nStarting double-coverage search from S = {s2_start}")

    search4, t4 = run_stage(
        label="Phase 4 · Double-coverage coarse search",
        lat_deg=lat_c, lon_deg=lon_c, times_s=times_c,
        start_total=s2_start, stop_total=args.double_stop,
        inclinations=args.inclinations,
        phase_res=args.phase_coarse,
        max_cand=max_cand,
        mode="double",
    )

    write_candidates_csv(
        sorted(search4.records, key=lambda r: (r["total_satellites"], -r["strict_double_time_rate"])),
        SEARCH_DIR / "phase4_double_candidates.csv",
    )
    _write_stage_summary(search4, t4, "phase4", lat_c, times_c, args, SEARCH_DIR)

    if search4.first_feasible is not None:
        s2 = search4.first_feasible.params.total_satellites
        print(f"\nDouble-coverage feasible at S2 = {s2}")
        print(f"  cost increase: {s2 - s1_opt} satellites ({(s2/s1_opt - 1)*100:.1f}%)")
    else:
        print(f"\n[STOP] No double-coverage feasible solution up to S = {args.double_stop}.")


def _write_stage_summary(
    search: q2.SearchRunResult,
    elapsed: float,
    tag: str,
    lat_deg: np.ndarray,
    times_s: np.ndarray,
    args: argparse.Namespace,
    out_dir: Path,
) -> None:
    summary: dict = {
        "tag": tag,
        "elapsed_s": elapsed,
        "evaluated_count": search.evaluated_count,
        "feasible_found": search.first_feasible is not None,
        "grid_points": int(len(lat_deg)),
        "time_steps": int(len(times_s)),
    }
    if search.first_feasible is not None:
        summary["first_feasible"] = q2.result_summary_dict(search.first_feasible)
    if search.best_result is not None:
        summary["best"] = q2.result_summary_dict(search.best_result)
    (out_dir / f"{tag}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )


if __name__ == "__main__":
    main()
