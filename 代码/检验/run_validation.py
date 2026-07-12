"""Run standalone sensitivity and Monte Carlo validation experiments."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
from PIL import Image, ImageDraw

from common import (
    bootstrap_problem_paths,
    percentile_interval,
    write_json,
    write_rows_csv,
)
from final_figures import generate_final_figure


bootstrap_problem_paths()

from q2_constellation import (  # noqa: E402
    ConstellationParams as Q2Params,
    CoverageConfig,
    make_latlon_grid as make_q2_latlon_grid,
    make_time_grid as make_q2_time_grid,
)
from q2_validation import run_q2_monte_carlo, run_q2_sensitivity  # noqa: E402
from q3_config import (  # noqa: E402
    ConstellationParams as Q3Params,
    Q3Config,
    SimulationConfig,
)
from q3_joint_evaluator import FidelityGrid, MotherGrid  # noqa: E402
from q3_orbit import (  # noqa: E402
    ground_ecef,
    make_latlon_grid as make_q3_latlon_grid,
    make_time_grid as make_q3_time_grid,
)
from q3_validation import (  # noqa: E402
    bootstrap_time_blocks,
    evaluate_q3_time_block_rates,
    run_q3_sensitivity,
)
from q4_config import AvoidanceParameters, DebrisEnvironment, MissionParameters  # noqa: E402
from q4_debris import (  # noqa: E402
    annual_probability,
    collision_cross_section_km2,
    flux_collision_rate_per_s,
    split_catalog_density,
)
from q4_validation import run_q4_sensitivity, simulate_annual_events  # noqa: E402


Q2_CASES = (
    ("single_S1302", Q2Params(62, 21, 30, 51.5, u0_deg=11.4)),
    ("double_S1480", Q2Params(37, 40, 31, 50.0)),
)
Q3_CASES = (
    ("S1540", Q3Params(35, 44, 24, 50.0)),
    ("S1680", Q3Params(35, 48, 21, 50.0)),
    ("S1760", Q3Params(32, 55, 12, 50.0)),
)
Q4_CASES = (
    ("q2_single_S1302", 1302, 62),
    ("q2_double_S1480", 1480, 37),
    ("q3_saturation_S1680", 1680, 35),
)


def _fieldnames(rows: Iterable[Mapping[str, object]]) -> list[str]:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    return fields


def _interval(values: list[float]) -> dict[str, float]:
    lower, upper = percentile_interval(values)
    return {
        "mean": float(np.mean(values)),
        "p2_5": lower,
        "p97_5": upper,
    }


def _write_plot(path: Path, rows: list[dict[str, object]], y_key: str, title: str) -> None:
    """Write one dependency-light categorical sensitivity PNG."""

    values = [float(row[y_key]) for row in rows]
    width, height = max(720, 70 * len(values)), 420
    left, right, top, bottom = 70, 30, 48, 65
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((left, 15), title, fill="black")
    draw.line((left, top, left, height - bottom), fill="black", width=2)
    draw.line((left, height - bottom, width - right, height - bottom), fill="black", width=2)
    low, high = min(values), max(values)
    if np.isclose(low, high):
        low, high = low - 0.5, high + 0.5
    draw.text((4, top), f"{high:.4g}", fill="black")
    draw.text((4, height - bottom - 12), f"{low:.4g}", fill="black")
    usable_width = width - left - right
    usable_height = height - top - bottom
    points = []
    for index, value in enumerate(values):
        x = left + usable_width * (index / max(1, len(values) - 1))
        y = top + usable_height * (1.0 - (value - low) / (high - low))
        points.append((round(x), round(y)))
        draw.text((round(x) - 4, height - bottom + 10), str(index + 1), fill="black")
    if len(points) > 1:
        draw.line(points, fill=(31, 119, 180), width=3)
    for point in points:
        draw.ellipse((point[0] - 4, point[1] - 4, point[0] + 4, point[1] + 4), fill=(214, 39, 40))
    draw.text((left, height - 25), f"scenario index; y={y_key}", fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def _q2_grid(quick: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    step_deg = 12.0 if quick else 3.0
    step_s = 14_400.0 if quick else 600.0
    lat_deg, lon_deg = make_q2_latlon_grid(step_deg=step_deg)
    return lat_deg, lon_deg, make_q2_time_grid(step_s=step_s)


def run_q2_validation(output_dir: str | Path, *, replicates: int, seed: int, quick: bool) -> dict[str, object]:
    """Run Q2 checks for the final single- and double-coverage candidates."""

    target = Path(output_dir) / "q2"
    config = CoverageConfig()
    lat_deg, lon_deg, times_s = _q2_grid(quick)
    sensitivity_rows: list[dict[str, object]] = []
    monte_carlo_rows: list[dict[str, object]] = []
    mc_samples = 32 if quick else 200
    mc_times = 6 if quick else 24
    for index, (candidate, params) in enumerate(Q2_CASES):
        for row in run_q2_sensitivity(params, config, lat_deg, lon_deg, times_s):
            sensitivity_rows.append({"candidate": candidate, "S": params.total_satellites, **row})
        for row in run_q2_monte_carlo(
            params,
            config,
            samples=mc_samples,
            time_samples=mc_times,
            replicates=replicates,
            seed=seed + index,
        ):
            monte_carlo_rows.append({"candidate": candidate, "S": params.total_satellites, **row})

    write_rows_csv(target / "sensitivity.csv", sensitivity_rows, _fieldnames(sensitivity_rows))
    write_rows_csv(target / "monte_carlo.csv", monte_carlo_rows, _fieldnames(monte_carlo_rows))
    summary = {
        "question": "q2",
        "mode": "quick" if quick else "standard",
        "seed": seed,
        "grid": {"points": int(len(lat_deg)), "times": int(len(times_s))},
        "monte_carlo": {
            candidate: {
                "replicates": sum(row["candidate"] == candidate for row in monte_carlo_rows),
                "C1": _interval([float(row["C1"]) for row in monte_carlo_rows if row["candidate"] == candidate]),
                "C2": _interval([float(row["C2"]) for row in monte_carlo_rows if row["candidate"] == candidate]),
            }
            for candidate, _params in Q2_CASES
        },
        "interpretation_limit": "Monte Carlo estimates sampled coverage fractions; it is not a proof of continuous strict coverage.",
    }
    summary["final_figure"] = str(generate_final_figure("q2", Path(output_dir)))
    write_json(target / "summary.json", summary)
    _write_plot(target / "sensitivity.png", sensitivity_rows, "C1", "Q2 sensitivity: C1")
    return summary


def _q3_mother_grid(quick: bool, config: Q3Config) -> tuple[MotherGrid, FidelityGrid]:
    if quick:
        lat_axis = np.array([4.0, 53.0])
        lon_axis = np.array([73.0, 135.0])
        lon_grid, lat_grid = np.meshgrid(lon_axis, lat_axis)
        cov_lat, cov_lon = lat_grid.ravel(), lon_grid.ravel()
        comm_lat = np.array([4.0, 4.0, 53.0, 53.0])
        comm_lon = np.array([73.0, 135.0, 73.0, 135.0])
        times_s = np.array([0.0, 43_082.045])
    else:
        # Independent standard validation grid.  The archived saturation
        # output retains only sample counts, not its communication coordinates;
        # this explicit 2°/15°/300 s lattice is therefore not claimed as an
        # exact coordinate-by-coordinate reproduction of that archived run.
        cov_lat, cov_lon = make_q3_latlon_grid(4.0, 53.0, 73.0, 135.0, 2.0)
        comm_lat, comm_lon = make_q3_latlon_grid(4.0, 53.0, 73.0, 135.0, 15.0)
        times_s = make_q3_time_grid(86_164.09, 300.0)
    coverage_ecef = ground_ecef(cov_lat, cov_lon, radius_km=config.earth_radius_km)
    coverage_unit = coverage_ecef / np.linalg.norm(coverage_ecef, axis=1)[:, None]
    communication_ecef = ground_ecef(comm_lat, comm_lon, radius_km=config.earth_radius_km)
    mother = MotherGrid(
        times_s=times_s,
        coverage_ground_unit=coverage_unit,
        coverage_weights=np.cos(np.deg2rad(cov_lat)),
        communication_ground_ecef_km=communication_ecef,
    )
    fidelity = FidelityGrid(
        name="validation_full_mother",
        time_indices=np.arange(len(times_s), dtype=int),
        coverage_point_indices=np.arange(len(coverage_unit), dtype=int),
        communication_point_indices=np.arange(len(communication_ecef), dtype=int),
    )
    return mother, fidelity


def run_q3_validation(output_dir: str | Path, *, replicates: int, seed: int, quick: bool) -> dict[str, object]:
    """Run Q3 parameter scenarios and snapshot-block bootstrap checks."""

    target = Path(output_dir) / "q3"
    config = Q3Config()
    simulation = SimulationConfig(topology_method="nearest")
    mother, fidelity = _q3_mother_grid(quick, config)
    cases = (Q3_CASES[1],) if quick else Q3_CASES
    sensitivity_rows: list[dict[str, object]] = []
    monte_carlo_rows: list[dict[str, object]] = []
    for index, (candidate, params) in enumerate(cases):
        for row in run_q3_sensitivity(params, mother, fidelity, config, simulation):
            sensitivity_rows.append({"candidate": candidate, "S": params.total_satellites, **row})
        block_rates = evaluate_q3_time_block_rates(
            params,
            mother.times_s,
            mother.communication_ground_ecef_km,
            config,
            simulation,
        )
        for replicate, value in enumerate(bootstrap_time_blocks(block_rates, replicates, seed + index)):
            monte_carlo_rows.append(
                {
                    "candidate": candidate,
                    "S": params.total_satellites,
                    "replicate": replicate,
                    "seed": seed + index,
                    "p30_all_bootstrap": value,
                }
            )

    write_rows_csv(target / "sensitivity.csv", sensitivity_rows, _fieldnames(sensitivity_rows))
    write_rows_csv(target / "monte_carlo.csv", monte_carlo_rows, _fieldnames(monte_carlo_rows))
    summary = {
        "question": "q3",
        "mode": "quick" if quick else "standard",
        "seed": seed,
        "mother_grid": {
            "coverage_points": int(len(mother.coverage_weights)),
            "communication_points": int(len(mother.communication_ground_ecef_km)),
            "time_snapshots": int(len(mother.times_s)),
        },
        "bootstrap_p30_all": {
            candidate: _interval(
                [float(row["p30_all_bootstrap"]) for row in monte_carlo_rows if row["candidate"] == candidate]
            )
            for candidate, _params in cases
        },
        "interpretation_limit": "The time-block bootstrap quantifies model-sample variability, not an observational confidence interval.",
    }
    summary["final_figure"] = str(generate_final_figure("q3", Path(output_dir)))
    write_json(target / "summary.json", summary)
    _write_plot(target / "sensitivity.png", sensitivity_rows, "p30_all", "Q3 sensitivity: P30(all)")
    return summary


def _annual_failure_probability(environment: DebrisEnvironment) -> float:
    _catalog, uncatalog = split_catalog_density(
        environment.total_density_gt_1cm_km3,
        environment.catalog_threshold_cm,
        environment.beta,
    )
    cross_section = collision_cross_section_km2(
        environment.satellite_radius_km,
        environment.debris_diameter_cm,
    )
    rate = flux_collision_rate_per_s(cross_section, environment.relative_speed_km_s, uncatalog)
    return annual_probability(rate, environment.year_s)


def run_q4_validation(output_dir: str | Path, *, replicates: int, seed: int, quick: bool) -> dict[str, object]:
    """Run Q4 scenario sensitivity and annual-event Monte Carlo checks."""

    target = Path(output_dir) / "q4"
    environment = DebrisEnvironment()
    avoidance = AvoidanceParameters()
    sensitivity_rows: list[dict[str, object]] = []
    monte_carlo_rows: list[dict[str, object]] = []
    failure_probability = _annual_failure_probability(environment)
    for index, (candidate, satellite_count, planes) in enumerate(Q4_CASES):
        mission = MissionParameters(satellite_count=satellite_count)
        case_sensitivity = run_q4_sensitivity(satellite_count, environment, avoidance, mission)
        for row in case_sensitivity:
            sensitivity_rows.append({"candidate": candidate, "plane_count": planes, **row})
        baseline = next(row for row in case_sensitivity if row["scenario"] == "baseline")
        for row in simulate_annual_events(
            satellite_count=satellite_count,
            annual_conjunction_rate=float(baseline["annual_conjunction_rate"]),
            trigger_probability=float(baseline["trigger_probability"]),
            feasible_probability=float(baseline["feasible_probability"]),
            failure_probability=failure_probability,
            replicates=replicates,
            seed=seed + index,
        ):
            monte_carlo_rows.append(
                {"candidate": candidate, "plane_count": planes, "seed": seed + index, **row}
            )

    write_rows_csv(target / "sensitivity.csv", sensitivity_rows, _fieldnames(sensitivity_rows))
    write_rows_csv(target / "monte_carlo.csv", monte_carlo_rows, _fieldnames(monte_carlo_rows))
    summary = {
        "question": "q4",
        "mode": "quick" if quick else "standard",
        "seed": seed,
        "environment": asdict(environment),
        "annual_event_monte_carlo": {
            candidate: {
                "replicates": sum(row["candidate"] == candidate for row in monte_carlo_rows),
                "conjunctions": _interval([float(row["conjunctions"]) for row in monte_carlo_rows if row["candidate"] == candidate]),
                "avoidances": _interval([float(row["avoidances"]) for row in monte_carlo_rows if row["candidate"] == candidate]),
                "failures": _interval([float(row["failures"]) for row in monte_carlo_rows if row["candidate"] == candidate]),
            }
            for candidate, _satellite_count, _planes in Q4_CASES
        },
        "interpretation_limit": "This remains a calibrated-scenario analysis until real coverage time series and communication-capacity inputs replace the smoke coupling.",
    }
    summary["final_figure"] = str(generate_final_figure("q4", Path(output_dir)))
    write_json(target / "summary.json", summary)
    _write_plot(target / "sensitivity.png", sensitivity_rows, "annual_avoidances", "Q4 sensitivity: annual avoidances")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", choices=("q2", "q3", "q4", "all"), default="all")
    parser.add_argument("--replicates", type=int, default=None, help="Override the question-specific replication default.")
    parser.add_argument("--seed", type=int, default=20260712)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "results"))
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(argv)
    if args.replicates is not None and args.replicates <= 0:
        parser.error("--replicates must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.out)
    summaries: dict[str, object] = {}
    if args.question in ("q2", "all"):
        summaries["q2"] = run_q2_validation(
            output_dir,
            replicates=args.replicates or (3 if args.quick else 30),
            seed=args.seed,
            quick=args.quick,
        )
    if args.question in ("q3", "all"):
        summaries["q3"] = run_q3_validation(
            output_dir,
            replicates=args.replicates or (30 if args.quick else 500),
            seed=args.seed,
            quick=args.quick,
        )
    if args.question in ("q4", "all"):
        summaries["q4"] = run_q4_validation(
            output_dir,
            replicates=args.replicates or (100 if args.quick else 10_000),
            seed=args.seed,
            quick=args.quick,
        )
    write_json(output_dir / "validation_summary.json", {"quick": args.quick, "results": summaries})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
