"""One-click staged search pipeline for Problem 2.

Prerequisites
-------------
Place this script in the corrected ``代码/问题二`` directory beside:

- run_q2_optimized_search.py
- verify_q2_actual_fix.py
- q2_constellation.py
- q2_fast_coverage.py
- q2_search_space.py
- q2_kdtree_coverage.py
- q2_active_set.py
- q2_adaptive_verify.py

The pipeline automatically performs:

1. anchor screening at selected satellite totals;
2. interval refinement with progressively smaller integer steps;
3. an ascending integer search with a stronger budget;
4. high-budget confirmation around the first numerical candidate;
5. adaptive continuous space-time verification;
6. checkpointed outputs and a final JSON/CSV report.

Important
---------
The inner search is stochastic/heuristic.  The returned value is the first
accepted solution found under the configured staged search.  It is not a
mathematical proof that no smaller Walker constellation exists.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "run_q2_optimized_search.py"
VALIDATOR = ROOT / "verify_q2_actual_fix.py"


@dataclass(frozen=True)
class Budget:
    samples_per_structure: int
    local_starts_per_structure: int
    keep_top_per_total: int
    max_cegis_rounds: int
    local_max_evaluations: int


@dataclass
class RunObservation:
    stage: str
    total_satellites: int
    output_dir: str
    budget: dict[str, int]
    first_numerical_found: bool
    accepted_found: bool
    certificate_status: str | None
    best_refined_margin: float | None
    best_refined_c_min: int | None
    best_refined_time_rate: float | None
    best_refined_max_gap_s: float | None
    best_refined_cegis_converged: bool | None
    best_planes: int | None
    best_sats_per_plane: int | None
    best_phase_factor: int | None


ANCHOR_BUDGET = Budget(1, 1, 1, 1, 20)
STEP100_BUDGET = Budget(1, 1, 2, 2, 50)
STEP20_BUDGET = Budget(2, 1, 3, 3, 100)
INTEGER_BUDGET = Budget(4, 2, 6, 5, 180)
CONFIRM_BUDGET = Budget(8, 3, 10, 8, 300)


def parse_int_list(text: str) -> list[int]:
    values = sorted({int(piece.strip()) for piece in text.split(",") if piece.strip()})
    if not values or any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("expected positive comma-separated integers")
    return values


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def as_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def to_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


def stage_dir(root: Path, stage: str, total: int) -> Path:
    return root / stage / f"S{total:04d}"


def summary_is_complete(output_dir: Path) -> bool:
    required = (
        output_dir / "q2_optimized_summary.json",
        output_dir / "q2_optimized_screen.csv",
        output_dir / "q2_optimized_refined.csv",
        output_dir / "q2_structure_audit.csv",
    )
    return all(path.exists() for path in required)


def stream_command(command: list[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print("\n$", subprocess.list2cmdline(command))
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        lines.append(line)
    return_code = process.wait()
    log_path.write_text("".join(lines), encoding="utf-8")
    if return_code != 0:
        raise RuntimeError(
            f"Command failed with exit code {return_code}. See {log_path}"
        )


def run_one_total(
    *,
    stage: str,
    total: int,
    budget: Budget,
    root_output: Path,
    adaptive_verify: bool,
    adaptive_spatial_tolerance: float,
    adaptive_time_tolerance: float,
    adaptive_max_boxes: int,
    resume: bool,
) -> RunObservation:
    output_dir = stage_dir(root_output, stage, total)

    if not (resume and summary_is_complete(output_dir)):
        command = [
            sys.executable,
            str(RUNNER),
            "--start-total", str(total),
            "--stop-total", str(total),
            "--samples-per-structure", str(budget.samples_per_structure),
            "--local-starts-per-structure", str(budget.local_starts_per_structure),
            "--keep-top-per-total", str(budget.keep_top_per_total),
            "--max-cegis-rounds", str(budget.max_cegis_rounds),
            "--local-max-evaluations", str(budget.local_max_evaluations),
            "--output-dir", str(output_dir),
        ]
        if adaptive_verify:
            command.extend([
                "--adaptive-verify",
                "--adaptive-spatial-tolerance", str(adaptive_spatial_tolerance),
                "--adaptive-time-tolerance", str(adaptive_time_tolerance),
                "--adaptive-max-boxes", str(adaptive_max_boxes),
            ])

        stream_command(command, output_dir / "run.log")
        stream_command(
            [sys.executable, str(VALIDATOR), str(output_dir)],
            output_dir / "validation.log",
        )
    else:
        print(f"[resume] {stage} S={total}: existing validated output reused")

    return load_observation(stage, total, output_dir, budget)


def load_observation(
    stage: str,
    total: int,
    output_dir: Path,
    budget: Budget,
) -> RunObservation:
    summary = json.loads(
        (output_dir / "q2_optimized_summary.json").read_text(encoding="utf-8")
    )
    refined = read_csv(output_dir / "q2_optimized_refined.csv")
    best = (
        max(refined, key=lambda row: float(row["min_margin"]))
        if refined else None
    )

    certificate = summary.get("adaptive_certificate")
    certificate_status = (
        str(certificate.get("status"))
        if isinstance(certificate, dict) and certificate.get("status") is not None
        else None
    )

    return RunObservation(
        stage=stage,
        total_satellites=total,
        output_dir=str(output_dir),
        budget=asdict(budget),
        first_numerical_found=summary.get("first_numerical_candidate") is not None,
        accepted_found=summary.get("validated_numerical_candidate") is not None,
        certificate_status=certificate_status,
        best_refined_margin=(
            to_float(best.get("min_margin")) if best else None
        ),
        best_refined_c_min=(
            to_int(best.get("c_min")) if best else None
        ),
        best_refined_time_rate=(
            to_float(best.get("single_coverage_time_rate")) if best else None
        ),
        best_refined_max_gap_s=(
            to_float(best.get("max_uncovered_gap_s")) if best else None
        ),
        best_refined_cegis_converged=(
            as_bool(best.get("cegis_converged")) if best else None
        ),
        best_planes=to_int(best.get("planes")) if best else None,
        best_sats_per_plane=to_int(best.get("sats_per_plane")) if best else None,
        best_phase_factor=to_int(best.get("phase_factor")) if best else None,
    )


def smallest_numerical(observations: Iterable[RunObservation]) -> RunObservation | None:
    candidates = [item for item in observations if item.first_numerical_found]
    return min(candidates, key=lambda item: item.total_satellites) if candidates else None


def smallest_accepted(observations: Iterable[RunObservation]) -> RunObservation | None:
    candidates = [item for item in observations if item.accepted_found]
    return min(candidates, key=lambda item: item.total_satellites) if candidates else None


def previous_tested_total(
    observations: Iterable[RunObservation],
    total: int,
) -> int | None:
    lower = sorted({
        item.total_satellites
        for item in observations
        if item.total_satellites < total
    })
    return lower[-1] if lower else None


def grid_between(lower: int, upper: int, step: int) -> list[int]:
    if upper <= lower:
        return []
    values = list(range(lower + step, upper, step))
    return [value for value in values if lower < value < upper]


def write_reports(
    root_output: Path,
    observations: list[RunObservation],
    *,
    status: str,
    final_total: int | None,
    message: str,
) -> None:
    root_output.mkdir(parents=True, exist_ok=True)

    report = {
        "status": status,
        "final_total_satellites": final_total,
        "message": message,
        "claim_level": (
            "First solution accepted by the configured staged heuristic search "
            "and adaptive verifier; not a proof of global minimality."
        ),
        "observations": [asdict(item) for item in observations],
    }
    (root_output / "q2_full_pipeline_result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    fieldnames = list(asdict(observations[0]).keys()) if observations else []
    with (root_output / "q2_full_pipeline_runs.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        if fieldnames:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for item in observations:
                row = asdict(item)
                row["budget"] = json.dumps(row["budget"], ensure_ascii=False)
                writer.writerow(row)

    print("\n" + "=" * 72)
    print(f"Pipeline status: {status}")
    print(f"Final total satellites: {final_total}")
    print(message)
    print(f"Report: {root_output / 'q2_full_pipeline_result.json'}")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-click staged minimum-satellite search pipeline"
    )
    parser.add_argument(
        "--anchors",
        type=parse_int_list,
        default=parse_int_list("400,800,1200,1600"),
        help="Comma-separated anchor totals.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "results_full_pipeline",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--integer-window",
        type=int,
        default=60,
        help=(
            "Maximum width of the final every-integer scan. "
            "A larger bracket is narrowed with step 20 first."
        ),
    )
    parser.add_argument(
        "--confirmation-lookback",
        type=int,
        default=3,
        help="High-budget rechecks immediately below the first numerical total.",
    )
    parser.add_argument(
        "--certificate-forward-limit",
        type=int,
        default=20,
        help=(
            "If the first numerical candidate is not certified, test up to this "
            "many larger totals with the confirmation budget."
        ),
    )
    parser.add_argument("--adaptive-spatial-tolerance", type=float, default=0.05)
    parser.add_argument("--adaptive-time-tolerance", type=float, default=1.0)
    parser.add_argument("--adaptive-max-boxes", type=int, default=200_000)
    args = parser.parse_args()

    if not RUNNER.exists() or not VALIDATOR.exists():
        print(
            "ERROR: place this script beside run_q2_optimized_search.py "
            "and verify_q2_actual_fix.py",
            file=sys.stderr,
        )
        return 2

    anchors = args.anchors
    observations: list[RunObservation] = []

    # Stage 1: anchor scan.
    for total in anchors:
        observations.append(
            run_one_total(
                stage="01_anchors",
                total=total,
                budget=ANCHOR_BUDGET,
                root_output=args.output_root,
                adaptive_verify=False,
                adaptive_spatial_tolerance=args.adaptive_spatial_tolerance,
                adaptive_time_tolerance=args.adaptive_time_tolerance,
                adaptive_max_boxes=args.adaptive_max_boxes,
                resume=args.resume,
            )
        )

    numerical = smallest_numerical(observations)
    if numerical is None:
        # Use the best-margin anchor as the only defensible diagnostic, but do not
        # pretend that a solution exists.
        best = max(
            observations,
            key=lambda item: (
                -math.inf
                if item.best_refined_margin is None
                else item.best_refined_margin
            ),
        )
        write_reports(
            args.output_root,
            observations,
            status="not_found_at_anchors",
            final_total=None,
            message=(
                "No numerical candidate was found at the configured anchors. "
                f"The best anchor was S={best.total_satellites} with refined "
                f"margin={best.best_refined_margin}. Increase the upper anchor "
                "or strengthen the anchor budget."
            ),
        )
        return 3

    upper = numerical.total_satellites
    previous_anchor = max([value for value in anchors if value < upper], default=max(1, upper - 400))

    # Stage 2: step 100 inside the first anchor bracket.
    for total in grid_between(previous_anchor, upper, 100):
        observations.append(
            run_one_total(
                stage="02_step100",
                total=total,
                budget=STEP100_BUDGET,
                root_output=args.output_root,
                adaptive_verify=False,
                adaptive_spatial_tolerance=args.adaptive_spatial_tolerance,
                adaptive_time_tolerance=args.adaptive_time_tolerance,
                adaptive_max_boxes=args.adaptive_max_boxes,
                resume=args.resume,
            )
        )

    numerical = smallest_numerical(observations)
    assert numerical is not None
    upper = numerical.total_satellites
    lower = previous_tested_total(observations, upper)
    if lower is None:
        lower = max(1, upper - 100)

    # Stage 3: step 20.
    for total in grid_between(lower, upper, 20):
        observations.append(
            run_one_total(
                stage="03_step20",
                total=total,
                budget=STEP20_BUDGET,
                root_output=args.output_root,
                adaptive_verify=False,
                adaptive_spatial_tolerance=args.adaptive_spatial_tolerance,
                adaptive_time_tolerance=args.adaptive_time_tolerance,
                adaptive_max_boxes=args.adaptive_max_boxes,
                resume=args.resume,
            )
        )

    numerical = smallest_numerical(observations)
    assert numerical is not None
    upper = numerical.total_satellites
    lower = previous_tested_total(observations, upper)
    if lower is None:
        lower = max(1, upper - args.integer_window)

    # Keep the expensive integer stage bounded.
    if upper - lower > args.integer_window:
        lower = upper - args.integer_window

    # Stage 4: ascending every-integer medium search.
    first_integer_numerical: RunObservation | None = None
    for total in range(lower + 1, upper + 1):
        observation = run_one_total(
            stage="04_integer",
            total=total,
            budget=INTEGER_BUDGET,
            root_output=args.output_root,
            adaptive_verify=False,
            adaptive_spatial_tolerance=args.adaptive_spatial_tolerance,
            adaptive_time_tolerance=args.adaptive_time_tolerance,
            adaptive_max_boxes=args.adaptive_max_boxes,
            resume=args.resume,
        )
        observations.append(observation)
        if observation.first_numerical_found:
            first_integer_numerical = observation
            break

    if first_integer_numerical is None:
        write_reports(
            args.output_root,
            observations,
            status="integer_stage_no_candidate",
            final_total=None,
            message=(
                "The stronger integer scan did not reproduce a numerical "
                "candidate in the narrowed interval. Increase the integer-stage "
                "budget or widen the interval."
            ),
        )
        return 4

    candidate_total = first_integer_numerical.total_satellites

    # Stage 5: high-budget confirmation below and at the candidate.
    confirm_start = max(lower + 1, candidate_total - args.confirmation_lookback)
    confirmed_numerical: RunObservation | None = None
    for total in range(confirm_start, candidate_total + 1):
        observation = run_one_total(
            stage="05_confirm",
            total=total,
            budget=CONFIRM_BUDGET,
            root_output=args.output_root,
            adaptive_verify=False,
            adaptive_spatial_tolerance=args.adaptive_spatial_tolerance,
            adaptive_time_tolerance=args.adaptive_time_tolerance,
            adaptive_max_boxes=args.adaptive_max_boxes,
            resume=args.resume,
        )
        observations.append(observation)
        if observation.first_numerical_found and confirmed_numerical is None:
            confirmed_numerical = observation

    if confirmed_numerical is None:
        write_reports(
            args.output_root,
            observations,
            status="confirmation_failed",
            final_total=None,
            message=(
                "The first medium-budget numerical candidate was not reproduced "
                "under the confirmation budget."
            ),
        )
        return 5

    # Stage 6: adaptive verification. If certification fails/inconclusive, move up.
    certificate_start = confirmed_numerical.total_satellites
    for total in range(
        certificate_start,
        certificate_start + args.certificate_forward_limit + 1,
    ):
        observation = run_one_total(
            stage="06_certificate",
            total=total,
            budget=CONFIRM_BUDGET,
            root_output=args.output_root,
            adaptive_verify=True,
            adaptive_spatial_tolerance=args.adaptive_spatial_tolerance,
            adaptive_time_tolerance=args.adaptive_time_tolerance,
            adaptive_max_boxes=args.adaptive_max_boxes,
            resume=args.resume,
        )
        observations.append(observation)

        if observation.accepted_found and observation.certificate_status == "covered":
            write_reports(
                args.output_root,
                observations,
                status="certified_candidate_found",
                final_total=total,
                message=(
                    f"S={total} is the first solution accepted by this staged "
                    "search and the adaptive continuous space-time verifier. "
                    "This remains a computational result, not a global "
                    "infeasibility proof for every smaller Walker structure."
                ),
            )
            return 0

    write_reports(
        args.output_root,
        observations,
        status="numerical_but_not_certified",
        final_total=confirmed_numerical.total_satellites,
        message=(
            "A numerical candidate was found, but no candidate in the configured "
            "forward verification window received a 'covered' certificate. "
            "Inspect certificate statuses and increase verification budget or "
            "search farther upward."
        ),
    )
    return 6


if __name__ == "__main__":
    raise SystemExit(main())
