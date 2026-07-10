"""Fair, margin-based, KD-tree accelerated search for Problem 2.

This is a numerical search pipeline, not a formal continuous-time certificate.
It replaces the biased global candidate cap with equal per-structure budgets and
uses counterexample-guided refinement for the best candidates.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as fast
from q2_active_set import counterexample_guided_optimize, initial_active_set
from q2_adaptive_verify import certify_continuous_coverage
from q2_kdtree_coverage import KDTreeCoverageResult, evaluate_constellation_kdtree
from q2_search_space import (
    WalkerStructure,
    minimum_reachable_inclination_deg,
    sobol_continuous_params,
    walker_structures,
)


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results_optimized"


def result_record(result: KDTreeCoverageResult, *, stage: str) -> dict:
    params = result.params
    if params is None:
        raise ValueError("result.params is required")
    worst_time = (
        float(result.times_s[result.worst_time_index])
        if result.worst_time_index >= 0
        else None
    )
    return {
        "stage": stage,
        "planes": params.planes,
        "sats_per_plane": params.sats_per_plane,
        "total_satellites": params.total_satellites,
        "phase_factor": params.phase_factor,
        "inclination_deg": params.inclination_deg,
        "raan0_deg": params.raan0_deg,
        "u0_deg": params.u0_deg,
        "c_min": result.c_min,
        "min_margin": result.min_margin,
        "single_coverage_time_rate": result.single_coverage_time_rate,
        "strict_double_time_rate": result.strict_double_time_rate,
        "max_uncovered_gap_s": result.max_uncovered_gap_s,
        "worst_time_s": worst_time,
        "mean_critical_points": float(np.mean(result.critical_point_counts_by_time))
        if len(result.critical_point_counts_by_time)
        else 0.0,
        "max_critical_points": int(np.max(result.critical_point_counts_by_time))
        if len(result.critical_point_counts_by_time)
        else 0,
        "evaluated_time_steps": result.evaluated_time_steps,
        "stopped_early": result.stopped_early,
        "backend": result.backend,
    }


def score_record(record: dict, q: int) -> tuple:
    feasible = 1 if record["c_min"] >= q and record["min_margin"] >= 0.0 else 0
    return (
        feasible,
        record["min_margin"],
        record["single_coverage_time_rate"],
        record["strict_double_time_rate"],
        -record["max_uncovered_gap_s"],
    )


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Problem 2 optimized Walker search",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start-total", type=int, default=40)
    parser.add_argument("--stop-total", type=int, default=45)
    parser.add_argument("--q", type=int, default=1)
    parser.add_argument("--samples-per-structure", type=int, default=16)
    parser.add_argument("--local-starts-per-structure", type=int, default=2)
    parser.add_argument("--keep-top-per-total", type=int, default=10)
    parser.add_argument("--inclination-min", type=float, default=None)
    parser.add_argument("--inclination-max", type=float, default=90.0)
    parser.add_argument("--screen-duration-hours", type=float, default=6.0)
    parser.add_argument("--screen-time-step", type=float, default=300.0)
    parser.add_argument("--separation-duration-hours", type=float, default=24.0)
    parser.add_argument("--separation-time-step", type=float, default=120.0)
    parser.add_argument("--active-interior-step", type=float, default=8.0)
    parser.add_argument("--active-boundary-step", type=float, default=2.0)
    parser.add_argument("--active-time-step", type=float, default=900.0)
    parser.add_argument("--max-cegis-rounds", type=int, default=3)
    parser.add_argument("--local-max-evaluations", type=int, default=80)
    parser.add_argument("--margin-tolerance", type=float, default=1e-6)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--continue-after-validated", action="store_true")
    parser.add_argument("--adaptive-verify", action="store_true")
    parser.add_argument("--adaptive-spatial-tolerance", type=float, default=0.05)
    parser.add_argument("--adaptive-time-tolerance", type=float, default=1.0)
    parser.add_argument("--adaptive-max-boxes", type=int, default=200000)
    parser.add_argument("--no-representatives", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.start_total <= 0 or args.stop_total < args.start_total:
        raise ValueError("invalid satellite-total range")
    if args.q <= 0:
        raise ValueError("q must be positive")
    if args.samples_per_structure <= 0:
        raise ValueError("samples-per-structure must be positive")
    if args.local_starts_per_structure <= 0:
        raise ValueError("local-starts-per-structure must be positive")
    if args.keep_top_per_total <= 0:
        raise ValueError("keep-top-per-total must be positive")
    if args.max_cegis_rounds <= 0:
        raise ValueError("max-cegis-rounds must be positive")


def main() -> None:
    args = parse_args()
    validate_args(args)

    cfg = q2.CoverageConfig()
    region = fast.LatLonRegion()
    inclination_min = args.inclination_min
    if inclination_min is None:
        inclination_min = minimum_reachable_inclination_deg(
            region_lat_max_deg=region.lat_max_deg,
            coverage_angle_rad=cfg.coverage_angle_rad,
        )
    if args.inclination_max < inclination_min:
        raise ValueError("inclination-max must be >= the inclination lower bound")

    screen_times = q2.make_time_grid(
        args.screen_duration_hours * 3600.0,
        args.screen_time_step,
    )
    separation_times = q2.make_time_grid(
        args.separation_duration_hours * 3600.0,
        args.separation_time_step,
    )
    active_times = q2.make_time_grid(
        args.screen_duration_hours * 3600.0,
        args.active_time_step,
    )

    all_screen_records: list[dict] = []
    all_refined_records: list[dict] = []
    structure_audit: list[dict] = []
    validated_solution: dict | None = None
    adaptive_certificate: dict | None = None

    master_seed = np.random.SeedSequence(args.seed)
    total_seeds = master_seed.spawn(args.stop_total - args.start_total + 1)

    for total_offset, total in enumerate(range(args.start_total, args.stop_total + 1)):
        total_candidates: list[tuple[dict, q2.ConstellationParams, WalkerStructure]] = []
        structures = walker_structures(total)
        structure_seeds = total_seeds[total_offset].spawn(len(structures))

        for structure, seed_sequence in zip(structures, structure_seeds):
            seed = int(seed_sequence.generate_state(1, dtype=np.uint32)[0])
            samples = sobol_continuous_params(
                structure,
                args.samples_per_structure,
                inclination_min_deg=inclination_min,
                inclination_max_deg=args.inclination_max,
                seed=seed,
            )
            structure_records: list[tuple[dict, q2.ConstellationParams]] = []
            for params in samples:
                result = evaluate_constellation_kdtree(
                    params,
                    screen_times,
                    config=cfg,
                    region=region,
                    q=args.q,
                    include_representatives=not args.no_representatives,
                    stop_if_margin_below=-0.02,
                )
                record = result_record(result, stage="screen")
                all_screen_records.append(record)
                structure_records.append((record, params))

            structure_records.sort(
                key=lambda item: score_record(item[0], args.q),
                reverse=True,
            )
            selected = structure_records[: args.local_starts_per_structure]
            for record, params in selected:
                total_candidates.append((record, params, structure))

            structure_audit.append(
                {
                    "total_satellites": total,
                    "planes": structure.planes,
                    "sats_per_plane": structure.sats_per_plane,
                    "phase_factor": structure.phase_factor,
                    "screen_evaluations": len(structure_records),
                    "selected_for_refinement": len(selected),
                }
            )

        total_candidates.sort(
            key=lambda item: score_record(item[0], args.q),
            reverse=True,
        )
        total_candidates = total_candidates[: args.keep_top_per_total]

        for _screen_record, params, structure in total_candidates:
            active_set = initial_active_set(
                region,
                active_times,
                interior_step_deg=args.active_interior_step,
                boundary_step_deg=args.active_boundary_step,
            )
            refined = counterexample_guided_optimize(
                structure,
                params,
                active_set,
                separation_times,
                q=args.q,
                config=cfg,
                region=region,
                inclination_min_deg=inclination_min,
                inclination_max_deg=args.inclination_max,
                max_rounds=args.max_cegis_rounds,
                local_max_evaluations=args.local_max_evaluations,
                margin_tolerance=args.margin_tolerance,
                include_representatives=not args.no_representatives,
            )
            record = result_record(refined.separation_result, stage="refined")
            record["cegis_rounds"] = refined.rounds
            record["cegis_converged"] = refined.converged
            record["active_constraint_count"] = len(refined.active_set.times_s)
            all_refined_records.append(record)

            if (
                refined.converged
                and record["c_min"] >= args.q
                and record["min_margin"] >= -args.margin_tolerance
            ):
                if (
                    validated_solution is None
                    or record["total_satellites"] < validated_solution["total_satellites"]
                    or (
                        record["total_satellites"] == validated_solution["total_satellites"]
                        and score_record(record, args.q) > score_record(validated_solution, args.q)
                    )
                ):
                    validated_solution = record

        if validated_solution is not None:
            if args.adaptive_verify:
                certificate_params = q2.ConstellationParams(
                    planes=int(validated_solution["planes"]),
                    sats_per_plane=int(validated_solution["sats_per_plane"]),
                    phase_factor=int(validated_solution["phase_factor"]),
                    inclination_deg=float(validated_solution["inclination_deg"]),
                    raan0_deg=float(validated_solution["raan0_deg"]),
                    u0_deg=float(validated_solution["u0_deg"]),
                )
                certificate = certify_continuous_coverage(
                    certificate_params,
                    region,
                    duration_s=args.separation_duration_hours * 3600.0,
                    q=args.q,
                    config=cfg,
                    spatial_tolerance_deg=args.adaptive_spatial_tolerance,
                    time_tolerance_s=args.adaptive_time_tolerance,
                    max_boxes=args.adaptive_max_boxes,
                )
                adaptive_certificate = {
                    "status": certificate.status,
                    "processed_boxes": certificate.processed_boxes,
                    "covered_boxes": certificate.covered_boxes,
                    "uncertain_boxes": certificate.uncertain_boxes,
                    "max_depth": certificate.max_depth,
                    "message": certificate.message,
                    "failure_box": asdict(certificate.failure_box) if certificate.failure_box else None,
                    "unresolved_boxes": [asdict(box) for box in certificate.unresolved_boxes],
                }
            if not args.continue_after_validated:
                break

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(all_screen_records, args.output_dir / "q2_optimized_screen.csv")
    write_csv(all_refined_records, args.output_dir / "q2_optimized_refined.csv")
    write_csv(structure_audit, args.output_dir / "q2_structure_audit.csv")

    settings = vars(args).copy()
    settings["output_dir"] = str(settings["output_dir"])
    settings["computed_inclination_min_deg"] = inclination_min
    summary = {
        "note": (
            "Numerical multi-fidelity search. A refined feasible result still "
            "requires the separate adaptive continuous-time certificate stage."
        ),
        "settings": settings,
        "screen_record_count": len(all_screen_records),
        "refined_record_count": len(all_refined_records),
        "validated_numerical_candidate": validated_solution,
        "adaptive_certificate": adaptive_certificate,
    }
    (args.output_dir / "q2_optimized_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Problem 2 optimized search finished.")
    print(f"Screen evaluations: {len(all_screen_records)}")
    print(f"Refined candidates: {len(all_refined_records)}")
    print(f"Best numerical candidate: {validated_solution}")
    print(f"Outputs: {args.output_dir}")


if __name__ == "__main__":
    main()
