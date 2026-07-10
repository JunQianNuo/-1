"""Verify the actual Problem 2 patch and optional run outputs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def expected_grid_size(duration_s: float, step_s: float) -> int:
    return int(math.ceil(duration_s / step_s)) + 1


def verify_source() -> list[str]:
    failures: list[str] = []
    runner_path = ROOT / "run_q2_optimized_search.py"
    coverage_path = ROOT / "q2_kdtree_coverage.py"

    if not runner_path.exists():
        return [f"missing {runner_path.name}"]
    if not coverage_path.exists():
        return [f"missing {coverage_path.name}"]

    runner = runner_path.read_text(encoding="utf-8")
    coverage = coverage_path.read_text(encoding="utf-8")

    required_runner = {
        "screen early exit disabled": "stop_if_margin_below=None",
        "screen completeness assertion": "Incomplete screening evaluation",
        "24 h active horizon": (
            "active_times = q2.make_time_grid(\n"
            "        args.separation_duration_hours * 3600.0,"
        ),
        "final audit count": 'audit_row["selected_for_refinement"]',
        "per-total solution": "current_total_solution",
        "certificate gate": 'accepted = certificate.status == "covered"',
        "first numerical result": '"first_numerical_candidate"',
        "certificate history": '"adaptive_certificates"',
    }
    for label, fragment in required_runner.items():
        if fragment not in runner:
            failures.append(f"runner missing: {label}")

    if "stop_if_margin_below=-0.02" in runner:
        failures.append("runner still contains old screening threshold")
    if (
        "active_times = q2.make_time_grid(\n"
        "        args.screen_duration_hours * 3600.0,"
    ) in runner:
        failures.append("runner still uses screen horizon for active set")

    required_coverage = {
        "actual-time gap": "times[index] - times[run_start]",
        "length check": "values and times_s must have equal length",
    }
    for label, fragment in required_coverage.items():
        if fragment not in coverage:
            failures.append(f"coverage missing: {label}")

    if "max(longest, current) * dt" in coverage:
        failures.append("coverage still uses run_length * dt")

    return failures


def verify_output(output_dir: Path) -> list[str]:
    failures: list[str] = []
    summary_path = output_dir / "q2_optimized_summary.json"
    screen_path = output_dir / "q2_optimized_screen.csv"
    refined_path = output_dir / "q2_optimized_refined.csv"
    audit_path = output_dir / "q2_structure_audit.csv"

    for path in (summary_path, screen_path, refined_path, audit_path):
        if not path.exists():
            failures.append(f"missing output: {path.name}")
    if failures:
        return failures

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    screen = read_csv(screen_path)
    refined = read_csv(refined_path) if refined_path.stat().st_size else []
    audit = read_csv(audit_path)

    settings = summary["settings"]
    screen_duration = float(settings["screen_duration_hours"]) * 3600.0
    separation_duration = float(settings["separation_duration_hours"]) * 3600.0
    expected_screen = expected_grid_size(
        screen_duration, float(settings["screen_time_step"])
    )
    expected_refined = expected_grid_size(
        separation_duration, float(settings["separation_time_step"])
    )

    if len(screen) != int(summary["screen_record_count"]):
        failures.append("screen row count differs from summary")
    if len(refined) != int(summary["refined_record_count"]):
        failures.append("refined row count differs from summary")

    bad_screen_steps = [
        row for row in screen
        if int(float(row["evaluated_time_steps"])) != expected_screen
    ]
    if bad_screen_steps:
        failures.append(
            f"{len(bad_screen_steps)} screen rows do not have "
            f"{expected_screen} time steps"
        )

    early = [row for row in screen if truthy(row["stopped_early"])]
    if early:
        failures.append(f"{len(early)} screen rows stopped early")

    if any(
        float(row["max_uncovered_gap_s"]) > screen_duration + 1e-9
        for row in screen
    ):
        failures.append("screen gap exceeds screen duration")

    bad_refined_steps = [
        row for row in refined
        if int(float(row["evaluated_time_steps"])) != expected_refined
    ]
    if bad_refined_steps:
        failures.append(
            f"{len(bad_refined_steps)} refined rows do not have "
            f"{expected_refined} time steps"
        )

    if any(
        float(row["max_uncovered_gap_s"]) > separation_duration + 1e-9
        for row in refined
    ):
        failures.append("refined gap exceeds separation duration")

    if audit:
        if "local_starts_retained" not in audit[0]:
            failures.append("audit lacks local_starts_retained")
        selected_count = sum(
            int(float(row["selected_for_refinement"])) for row in audit
        )
        if selected_count != len(refined):
            failures.append(
                "sum(selected_for_refinement) differs from refined rows: "
                f"{selected_count} != {len(refined)}"
            )

    if "first_numerical_candidate" not in summary:
        failures.append("summary lacks first_numerical_candidate")
    if "adaptive_certificates" not in summary:
        failures.append("summary lacks adaptive_certificates")

    print("Output summary:")
    print(f"  screen rows: {len(screen)}")
    print(f"  expected screen steps: {expected_screen}")
    print(f"  refined rows: {len(refined)}")
    print(f"  expected refined steps: {expected_refined}")
    if refined:
        best = max(refined, key=lambda row: float(row["min_margin"]))
        print(
            "  best refined: "
            f"S={best['total_satellites']}, "
            f"P={best['planes']}, "
            f"N={best['sats_per_plane']}, "
            f"F={best['phase_factor']}, "
            f"margin={best['min_margin']}, "
            f"converged={best.get('cegis_converged')}"
        )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", nargs="?", type=Path)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()

    failures = verify_source()
    if not args.source_only:
        if args.output_dir is None:
            print("ERROR: provide output_dir or use --source-only", file=sys.stderr)
            return 2
        failures.extend(verify_output(args.output_dir))

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS: source patch and requested output checks succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
