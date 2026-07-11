"""Command-line smoke runner for Problem 3 algorithms.

This script is intentionally parameterized.  Its default run is a tiny smoke
case for verifying the algorithm chain; it is not the final numerical answer.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from q3_config import ConstellationParams, Q3Config, SimulationConfig
from q3_orbit import ground_ecef, make_latlon_grid, make_time_grid
from q3_pipeline import run_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Problem 3 LEO network algorithms")
    parser.add_argument("--planes", type=int, default=2)
    parser.add_argument("--sats-per-plane", type=int, default=4)
    parser.add_argument("--phase-factor", type=int, default=0)
    parser.add_argument("--inclination-deg", type=float, default=30.0)
    parser.add_argument("--raan0-deg", type=float, default=0.0)
    parser.add_argument("--u0-deg", type=float, default=0.0)
    parser.add_argument("--duration-s", type=float, default=0.0)
    parser.add_argument("--step-s", type=float, default=60.0)
    parser.add_argument("--lat-min", type=float, default=4.0)
    parser.add_argument("--lat-max", type=float, default=53.0)
    parser.add_argument("--lon-min", type=float, default=73.0)
    parser.add_argument("--lon-max", type=float, default=135.0)
    parser.add_argument("--grid-step-deg", type=float, default=25.0)
    parser.add_argument("--total-flow-gbps", type=float, default=1.0)
    parser.add_argument(
        "--topology-method",
        choices=("nearest", "walker"),
        default="nearest",
        help="Inter-plane ISL rule. The problem statement requires nearest.",
    )
    parser.add_argument(
        "--physical-coverage",
        action="store_true",
        help="Use the physical 506 km access angle. Default uses a wide smoke-test angle.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent
    results_dir = root / "results"
    figures_dir = root / "figures"
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    params = ConstellationParams(
        planes=args.planes,
        sats_per_plane=args.sats_per_plane,
        phase_factor=args.phase_factor,
        inclination_deg=args.inclination_deg,
        raan0_deg=args.raan0_deg,
        u0_deg=args.u0_deg,
    )
    coverage_angle = None if args.physical_coverage else np.deg2rad(180.0)
    cfg = Q3Config(coverage_angle_rad=coverage_angle, isl_max_distance_km=1e9 if not args.physical_coverage else 5000.0)
    sim = SimulationConfig(duration_s=args.duration_s, step_s=args.step_s, topology_method=args.topology_method)

    lat, lon = make_latlon_grid(args.lat_min, args.lat_max, args.lon_min, args.lon_max, args.grid_step_deg)
    ground = ground_ecef(lat, lon, radius_km=cfg.earth_radius_km)
    times = make_time_grid(args.duration_s, args.step_s)

    topology_rows: list[dict] = []
    access_rows: list[dict] = []
    delay_rows: list[dict] = []
    summary_rows: list[dict] = []

    for t_s in times:
        snapshot = run_snapshot(
            params,
            t_s=float(t_s),
            ground_points_ecef_km=ground,
            config=cfg,
            simulation=sim,
            total_flow_gbps=args.total_flow_gbps,
        )
        topology_rows.append({"t_s": float(t_s), **snapshot.topology})
        access_rows.append({"t_s": float(t_s), **snapshot.access})
        summary_rows.append({"t_s": float(t_s), **snapshot.delay_statistics})
        for (a, b), route in snapshot.routes.items():
            delay_rows.append(
                {
                    "t_s": float(t_s),
                    "source": a,
                    "target": b,
                    "delay_s": route.delay_s,
                    "hop_count": max(0, len(route.path) - 1),
                    "path": "-".join(map(str, route.path)),
                }
            )

    pd.DataFrame(topology_rows).to_csv(results_dir / "q3_topology_summary.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(access_rows).to_csv(results_dir / "q3_access_summary.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(delay_rows).to_csv(results_dir / "q3_delay_samples.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(summary_rows).to_csv(results_dir / "q3_delay_summary.csv", index=False, encoding="utf-8-sig")

    finite_delays = [row["delay_s"] for row in delay_rows if np.isfinite(row["delay_s"])]
    if finite_delays:
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans", "Arial"]
        plt.rcParams["axes.unicode_minus"] = False
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.hist(np.asarray(finite_delays) * 1000.0, bins=min(20, max(5, len(finite_delays))))
        ax.set_xlabel("Delay / ms")
        ax.set_ylabel("Sample count")
        ax.set_title("Q3 smoke delay distribution")
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        fig.savefig(figures_dir / "q3_smoke_delay_hist.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    report = results_dir / "q3_run_report.txt"
    report.write_text(
        "Problem 3 algorithm smoke run\n"
        "This is an implementation verification run, not a final numerical conclusion.\n"
        f"params=planes={params.planes}, sats_per_plane={params.sats_per_plane}, "
        f"phase_factor={params.phase_factor}, inclination_deg={params.inclination_deg}, "
        f"raan0_deg={params.raan0_deg}, u0_deg={params.u0_deg}\n"
        f"satellites={params.total_satellites}, time_steps={len(times)}, ground_points={len(ground)}, "
        f"physical_coverage={args.physical_coverage}, topology_method={sim.topology_method}\n"
        f"outputs={results_dir}\n",
        encoding="utf-8",
    )
    print(report.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
