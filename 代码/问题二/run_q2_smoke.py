"""Smoke run for Problem 2 constellation coverage code.

This script is deliberately small. It verifies that the evaluator can:

1. build a target grid and time grid,
2. evaluate several Walker-Delta candidates,
3. write CSV/JSON results,
4. draw basic diagnostic figures.

It is NOT the final exhaustive optimization run.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import q2_constellation as q2


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"


def setup_matplotlib() -> None:
    plt.rcParams["font.sans-serif"] = [
        "SimHei",
        "Microsoft YaHei",
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
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
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
    ax.set_title("Smoke：各网格点最小覆盖重数")
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
    t_min = result.times_s / 60.0
    ax.plot(t_min, min_count_t, label="整区最小覆盖重数")
    ax.plot(t_min, weighted_mean_t, label="面积加权平均覆盖重数")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("覆盖重数")
    ax.set_title("Smoke：覆盖重数时间序列")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    setup_matplotlib()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    config = q2.CoverageConfig()

    # Deliberately coarse grids for smoke testing only.
    lat_deg, lon_deg = q2.make_latlon_grid(step_deg=12.0)
    times_s = q2.make_time_grid(duration_s=2.0 * 3600.0, step_s=600.0)

    rows: list[dict] = []
    best_result: q2.EvaluationResult | None = None
    best_score = (-1.0, -1.0)

    # Evaluate a small deterministic candidate subset.
    candidates = q2.candidate_params_for_total(
        total_satellites=40,
        inclinations_deg=[49.0, 51.0, 53.0],
        phase_resolution_deg=10.0,
        max_candidates=24,
    )

    for params in candidates:
        result = q2.evaluate_constellation(params, lat_deg, lon_deg, times_s, config)
        row = {
            "planes": params.planes,
            "sats_per_plane": params.sats_per_plane,
            "total_satellites": params.total_satellites,
            "phase_factor": params.phase_factor,
            "inclination_deg": params.inclination_deg,
            "raan0_deg": params.raan0_deg,
            "u0_deg": params.u0_deg,
            "C1": result.coverage_rate_q1,
            "C2": result.coverage_rate_q2,
            "avg_multiplicity": result.avg_multiplicity,
            "c_min": result.c_min,
            "max_gap_s": result.max_gap_s,
            "strict_double_time_rate": result.strict_double_time_rate,
        }
        rows.append(row)
        score = (result.coverage_rate_q1, result.avg_multiplicity)
        if score > best_score:
            best_score = score
            best_result = result

    if best_result is None:
        raise RuntimeError("no smoke candidates were evaluated")

    rows.sort(key=lambda r: (r["C1"], r["avg_multiplicity"]), reverse=True)
    write_candidates_csv(rows, RESULTS_DIR / "q2_smoke_candidates.csv")

    summary = {
        "note": "Smoke run only; not final optimization result.",
        "grid_points": int(len(lat_deg)),
        "time_steps": int(len(times_s)),
        "coverage_angle_deg": float(np.rad2deg(config.coverage_angle_rad)),
        "orbital_period_min": config.orbital_period_s / 60.0,
        "best_candidate": q2.result_summary_dict(best_result),
    }
    (RESULTS_DIR / "q2_smoke_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    plot_min_count_map(best_result, FIGURES_DIR / "Q2_smoke_min_count_map.png")
    plot_time_series(best_result, FIGURES_DIR / "Q2_smoke_time_series.png")

    print("Smoke run finished.")
    print(f"Grid points: {len(lat_deg)}, time steps: {len(times_s)}")
    print(f"Best candidate params: {best_result.params}")
    print(f"Best metrics: {best_result.metrics}")
    print(f"Wrote: {RESULTS_DIR / 'q2_smoke_candidates.csv'}")
    print(f"Wrote: {RESULTS_DIR / 'q2_smoke_summary.json'}")
    print(f"Wrote: {FIGURES_DIR / 'Q2_smoke_min_count_map.png'}")
    print(f"Wrote: {FIGURES_DIR / 'Q2_smoke_time_series.png'}")


if __name__ == "__main__":
    main()
