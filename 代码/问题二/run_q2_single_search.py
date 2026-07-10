"""Coarse single-coverage search for Problem 2.

This script keeps the full grid-time coverage model, but uses controllable
coarse resolution so the first formal search can finish quickly.  It is a
coarse screening run, not the final optimality proof.
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import q2_constellation as q2


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"


def parse_inclinations(text: str) -> list[float]:
    values = [float(item.strip()) for item in text.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("inclinations must not be empty")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Problem 2 coarse single-coverage search.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--lat-step", type=float, default=6.0, help="latitude/longitude grid step in degrees")
    parser.add_argument("--time-step", type=float, default=900.0, help="time step in seconds")
    parser.add_argument("--duration-hours", type=float, default=6.0, help="search duration in hours")
    parser.add_argument("--start-total", type=int, default=40, help="minimum total satellite count")
    parser.add_argument("--stop-total", type=int, default=40, help="maximum total satellite count")
    parser.add_argument(
        "--inclinations",
        type=parse_inclinations,
        default=parse_inclinations("49,50,51,52,53"),
        help="comma-separated inclination candidates in degrees",
    )
    parser.add_argument("--phase-resolution", type=float, default=30.0, help="phase search resolution in degrees")
    parser.add_argument(
        "--max-candidates-per-total",
        type=int,
        default=2000,
        help="candidate cap for each total satellite count; use 0 for no cap",
    )
    parser.add_argument(
        "--no-stop-on-feasible",
        action="store_true",
        help="continue evaluating all capped candidates after the first feasible one",
    )
    return parser


def setup_matplotlib() -> None:
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
        "Arial",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.linewidth"] = 1.2
    plt.rcParams["lines.linewidth"] = 1.8


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


def plot_min_count_map(result: q2.EvaluationResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    min_counts = result.counts.min(axis=1)
    vmax = max(1, int(np.max(min_counts)))

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    sc = ax.scatter(
        result.lon_deg,
        result.lat_deg,
        c=min_counts,
        s=42,
        cmap="viridis",
        vmin=0,
        vmax=vmax,
        edgecolor="none",
    )
    ax.set_xlabel("经度 / °E")
    ax.set_ylabel("纬度 / °N")
    ax.set_title("问题二粗搜索：各网格点最小覆盖重数")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("最小覆盖重数")
    cbar.set_ticks(range(vmax + 1) if vmax <= 10 else np.linspace(0, vmax, 6))
    ax.grid(True, linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_time_series(result: q2.EvaluationResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    min_count_t = result.counts.min(axis=0)
    weighted_mean_t = result.weights @ result.counts

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    t_hour = result.times_s / 3600.0
    ax.plot(t_hour, min_count_t, label="整区最小覆盖重数")
    ax.plot(t_hour, weighted_mean_t, label="面积加权平均覆盖重数")
    ax.set_xlabel("时间 / h")
    ax.set_ylabel("覆盖重数")
    ax.set_title("问题二粗搜索：覆盖重数时间序列")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def sorted_records(records: list[dict]) -> list[dict]:
    return sorted(
        records,
        key=lambda r: (
            r["total_satellites"],
            r["c_min"],
            r["C1"],
            r["avg_multiplicity"],
            -r["max_gap_s"],
        ),
        reverse=True,
    )


def main() -> None:
    args = build_parser().parse_args()
    setup_matplotlib()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    config = q2.CoverageConfig()
    lat_deg, lon_deg = q2.make_latlon_grid(step_deg=args.lat_step)
    times_s = q2.make_time_grid(duration_s=args.duration_hours * 3600.0, step_s=args.time_step)
    max_candidates = args.max_candidates_per_total
    if max_candidates == 0:
        max_candidates = None

    search = q2.search_single_coverage(
        lat_deg=lat_deg,
        lon_deg=lon_deg,
        times_s=times_s,
        start_total=args.start_total,
        stop_total=args.stop_total,
        inclinations_deg=args.inclinations,
        phase_resolution_deg=args.phase_resolution,
        max_candidates_per_total=max_candidates,
        stop_on_feasible=not args.no_stop_on_feasible,
        config=config,
    )

    if search.best_result is None:
        raise RuntimeError("no candidates were evaluated")

    records = sorted_records(search.records)
    write_candidates_csv(records, RESULTS_DIR / "q2_single_search_candidates.csv")

    best = search.best_result
    summary = {
        "note": "Coarse limited search only; not final optimization result.",
        "settings": {
            "lat_step_deg": args.lat_step,
            "time_step_s": args.time_step,
            "duration_hours": args.duration_hours,
            "start_total": args.start_total,
            "stop_total": args.stop_total,
            "inclinations_deg": args.inclinations,
            "phase_resolution_deg": args.phase_resolution,
            "max_candidates_per_total": max_candidates,
            "stop_on_feasible": not args.no_stop_on_feasible,
        },
        "grid_points": int(len(lat_deg)),
        "time_steps": int(len(times_s)),
        "coverage_angle_deg": float(np.rad2deg(config.coverage_angle_rad)),
        "orbital_period_min": config.orbital_period_s / 60.0,
        "evaluated_count": search.evaluated_count,
        "feasible_found": search.first_feasible is not None,
        "first_feasible": (
            q2.result_summary_dict(search.first_feasible) if search.first_feasible is not None else None
        ),
        "best_candidate": q2.result_summary_dict(best),
    }
    (RESULTS_DIR / "q2_single_search_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    plot_min_count_map(best, FIGURES_DIR / "Q2_single_search_best_min_count_map.png")
    plot_time_series(best, FIGURES_DIR / "Q2_single_search_best_time_series.png")

    print("Problem 2 coarse single-coverage search finished.")
    print(f"Grid points: {len(lat_deg)}, time steps: {len(times_s)}")
    print(f"Candidates evaluated: {search.evaluated_count}")
    print(f"Feasible found: {search.first_feasible is not None}")
    print(f"Best candidate params: {best.params}")
    print(f"Best metrics: {best.metrics}")
    print(f"Wrote: {RESULTS_DIR / 'q2_single_search_candidates.csv'}")
    print(f"Wrote: {RESULTS_DIR / 'q2_single_search_summary.json'}")
    print(f"Wrote: {FIGURES_DIR / 'Q2_single_search_best_min_count_map.png'}")
    print(f"Wrote: {FIGURES_DIR / 'Q2_single_search_best_time_series.png'}")


if __name__ == "__main__":
    main()
