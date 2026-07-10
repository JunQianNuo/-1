"""Fast screening search for Problem 2 constellation candidates.

The script is deliberately a two-stage pipeline:

1. use ``q2_fast_coverage.evaluate_constellation_fast`` to screen candidates;
2. verify only the retained top candidates with the original grid evaluator.

It avoids the old pattern of exhaustive fine-grid evaluation for every
candidate and keeps only a bounded Top-K list in memory.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as fast


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"


@dataclass(frozen=True)
class FastSearchRunResult:
    """Bounded-memory result container for the fast search pipeline."""

    fast_records: list[dict]
    verified_records: list[dict]
    evaluated_count: int
    verified_count: int
    best_fast_record: dict | None
    best_verified_record: dict | None
    first_fast_feasible: dict | None
    first_verified_feasible: dict | None


def parse_inclinations(text: str) -> list[float]:
    values = [float(item.strip()) for item in text.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("inclinations must not be empty")
    return values


def fast_result_record(result: fast.FastCoverageResult) -> dict:
    """Flatten one fast critical-point result into a CSV-friendly record."""

    params = result.params
    if params is None:
        raise ValueError("FastCoverageResult.params is required for search records")

    worst_time_s = (
        float(result.times_s[result.worst_time_index])
        if result.worst_time_index >= 0 and len(result.times_s) > 0
        else None
    )
    return {
        "planes": params.planes,
        "sats_per_plane": params.sats_per_plane,
        "total_satellites": params.total_satellites,
        "phase_factor": params.phase_factor,
        "inclination_deg": params.inclination_deg,
        "raan0_deg": params.raan0_deg,
        "u0_deg": params.u0_deg,
        "fast_c_min": int(result.c_min),
        "fast_single_time_rate": float(result.single_coverage_time_rate),
        "fast_strict_double_time_rate": float(result.strict_double_time_rate),
        "fast_max_uncovered_gap_s": float(result.max_uncovered_gap_s),
        "fast_worst_time_s": worst_time_s,
        "fast_mean_critical_points": float(np.mean(result.critical_point_counts_by_time))
        if len(result.critical_point_counts_by_time)
        else 0.0,
        "fast_max_critical_points": int(np.max(result.critical_point_counts_by_time))
        if len(result.critical_point_counts_by_time)
        else 0,
    }


def params_from_record(record: dict) -> q2.ConstellationParams:
    return q2.ConstellationParams(
        planes=int(record["planes"]),
        sats_per_plane=int(record["sats_per_plane"]),
        phase_factor=int(record["phase_factor"]),
        inclination_deg=float(record["inclination_deg"]),
        raan0_deg=float(record["raan0_deg"]),
        u0_deg=float(record["u0_deg"]),
    )


def fast_record_score(record: dict) -> tuple:
    """Rank fast screening records; larger is better."""

    feasible = 1 if record["fast_c_min"] >= 1 else 0
    return (
        feasible,
        record["fast_c_min"],
        record["fast_single_time_rate"],
        record["fast_strict_double_time_rate"],
        -record["fast_max_uncovered_gap_s"],
        -record["total_satellites"],
    )


def verified_record_score(record: dict) -> tuple:
    """Rank verified grid records; larger is better."""

    feasible = 1 if record["c_min"] >= 1 else 0
    return (
        feasible,
        record["c_min"],
        record["C1"],
        record["C2"],
        record["avg_multiplicity"],
        -record["max_gap_s"],
        -record["total_satellites"],
    )


def keep_top_records(records: list[dict], record: dict, limit: int) -> list[dict]:
    """Insert a record and keep only the best ``limit`` fast records."""

    if limit <= 0:
        raise ValueError("limit must be positive")
    records.append(record)
    records.sort(key=fast_record_score, reverse=True)
    del records[limit:]
    return records


def write_records_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_fast_search(
    *,
    start_total: int,
    stop_total: int,
    inclinations_deg: Iterable[float],
    fast_times_s: np.ndarray,
    verify_times_s: np.ndarray,
    region: fast.LatLonRegion,
    verify_lat_deg: np.ndarray,
    verify_lon_deg: np.ndarray,
    phase_resolution_deg: float,
    max_candidates_per_total: int | None,
    keep_top_fast: int,
    verify_top: int,
    config: q2.CoverageConfig | None = None,
    stop_on_fast_feasible: bool = False,
    include_representatives: bool = True,
) -> FastSearchRunResult:
    """Run bounded Top-K fast screening and optional grid verification."""

    if start_total <= 0:
        raise ValueError("start_total must be positive")
    if stop_total < start_total:
        raise ValueError("stop_total must be greater than or equal to start_total")
    if keep_top_fast <= 0:
        raise ValueError("keep_top_fast must be positive")
    if verify_top < 0:
        raise ValueError("verify_top must be non-negative")

    cfg = config or q2.CoverageConfig()
    top_fast_records: list[dict] = []
    best_fast_record: dict | None = None
    first_fast_feasible: dict | None = None
    evaluated_count = 0

    for total in range(start_total, stop_total + 1):
        for params in q2.candidate_params_for_total(
            total_satellites=total,
            inclinations_deg=inclinations_deg,
            phase_resolution_deg=phase_resolution_deg,
            max_candidates=max_candidates_per_total,
        ):
            fast_result = fast.evaluate_constellation_fast(
                params,
                fast_times_s,
                config=cfg,
                region=region,
                include_representatives=include_representatives,
            )
            record = fast_result_record(fast_result)
            evaluated_count += 1
            top_fast_records = keep_top_records(top_fast_records, record, keep_top_fast)

            if best_fast_record is None or fast_record_score(record) > fast_record_score(best_fast_record):
                best_fast_record = record

            if record["fast_c_min"] >= 1 and first_fast_feasible is None:
                first_fast_feasible = record
                if stop_on_fast_feasible:
                    break
        if stop_on_fast_feasible and first_fast_feasible is not None:
            break

    verified_records: list[dict] = []
    first_verified_feasible: dict | None = None
    best_verified_record: dict | None = None

    for rank, fast_record in enumerate(top_fast_records[:verify_top], start=1):
        params = params_from_record(fast_record)
        grid_result = q2.evaluate_constellation(
            params,
            verify_lat_deg,
            verify_lon_deg,
            verify_times_s,
            cfg,
        )
        verified_record = dict(fast_record)
        verified_record["fast_rank"] = rank
        verified_record.update(q2.evaluation_record(grid_result))
        verified_records.append(verified_record)

        if best_verified_record is None or verified_record_score(verified_record) > verified_record_score(
            best_verified_record
        ):
            best_verified_record = verified_record

        if verified_record["c_min"] >= 1 and first_verified_feasible is None:
            first_verified_feasible = verified_record

    return FastSearchRunResult(
        fast_records=top_fast_records,
        verified_records=verified_records,
        evaluated_count=evaluated_count,
        verified_count=len(verified_records),
        best_fast_record=best_fast_record,
        best_verified_record=best_verified_record,
        first_fast_feasible=first_fast_feasible,
        first_verified_feasible=first_verified_feasible,
    )


def save_fast_search_outputs(result: FastSearchRunResult, output_dir: Path, settings: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fast_csv = output_dir / "q2_fast_search_top_fast_candidates.csv"
    verified_csv = output_dir / "q2_fast_search_verified_candidates.csv"
    summary_json = output_dir / "q2_fast_search_summary.json"

    write_records_csv(result.fast_records, fast_csv)
    write_records_csv(result.verified_records, verified_csv)
    summary = {
        "note": "Fast critical-point screening; final feasibility should rely on verified grid records.",
        "settings": settings,
        "evaluated_count": result.evaluated_count,
        "verified_count": result.verified_count,
        "best_fast_record": result.best_fast_record,
        "first_fast_feasible": result.first_fast_feasible,
        "best_verified_record": result.best_verified_record,
        "first_verified_feasible": result.first_verified_feasible,
        "outputs": {
            "fast_candidates_csv": str(fast_csv),
            "verified_candidates_csv": str(verified_csv),
            "summary_json": str(summary_json),
        },
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Problem 2 fast screening search.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start-total", type=int, default=40)
    parser.add_argument("--stop-total", type=int, default=45)
    parser.add_argument("--inclinations", type=parse_inclinations, default=parse_inclinations("49,50,51,52,53"))
    parser.add_argument("--phase-resolution", type=float, default=30.0)
    parser.add_argument("--max-candidates-per-total", type=int, default=300)
    parser.add_argument("--keep-top-fast", type=int, default=30)
    parser.add_argument("--verify-top", type=int, default=5)
    parser.add_argument("--duration-hours", type=float, default=6.0)
    parser.add_argument("--fast-time-step", type=float, default=900.0)
    parser.add_argument("--verify-time-step", type=float, default=900.0)
    parser.add_argument("--verify-grid-step", type=float, default=6.0)
    parser.add_argument("--stop-on-fast-feasible", action="store_true")
    parser.add_argument("--no-representatives", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = q2.CoverageConfig()
    max_candidates = args.max_candidates_per_total
    if max_candidates == 0:
        max_candidates = None

    region = fast.LatLonRegion()
    fast_times_s = q2.make_time_grid(args.duration_hours * 3600.0, args.fast_time_step)
    verify_times_s = q2.make_time_grid(args.duration_hours * 3600.0, args.verify_time_step)
    verify_lat, verify_lon = q2.make_latlon_grid(step_deg=args.verify_grid_step)

    result = run_fast_search(
        start_total=args.start_total,
        stop_total=args.stop_total,
        inclinations_deg=args.inclinations,
        fast_times_s=fast_times_s,
        verify_times_s=verify_times_s,
        region=region,
        verify_lat_deg=verify_lat,
        verify_lon_deg=verify_lon,
        phase_resolution_deg=args.phase_resolution,
        max_candidates_per_total=max_candidates,
        keep_top_fast=args.keep_top_fast,
        verify_top=args.verify_top,
        config=config,
        stop_on_fast_feasible=args.stop_on_fast_feasible,
        include_representatives=not args.no_representatives,
    )

    settings = {
        "start_total": args.start_total,
        "stop_total": args.stop_total,
        "inclinations_deg": args.inclinations,
        "phase_resolution_deg": args.phase_resolution,
        "max_candidates_per_total": max_candidates,
        "keep_top_fast": args.keep_top_fast,
        "verify_top": args.verify_top,
        "duration_hours": args.duration_hours,
        "fast_time_step_s": args.fast_time_step,
        "verify_time_step_s": args.verify_time_step,
        "verify_grid_step_deg": args.verify_grid_step,
        "include_representatives": not args.no_representatives,
    }
    save_fast_search_outputs(result, args.output_dir, settings)

    print("Problem 2 fast screening search finished.")
    print(f"Candidates evaluated by fast method: {result.evaluated_count}")
    print(f"Candidates verified by grid method: {result.verified_count}")
    print(f"Best fast record: {result.best_fast_record}")
    print(f"Best verified record: {result.best_verified_record}")
    print(f"Wrote: {args.output_dir / 'q2_fast_search_top_fast_candidates.csv'}")
    print(f"Wrote: {args.output_dir / 'q2_fast_search_verified_candidates.csv'}")
    print(f"Wrote: {args.output_dir / 'q2_fast_search_summary.json'}")


if __name__ == "__main__":
    main()
