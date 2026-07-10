"""Apply verified fixes to the actual submitted Problem 2 source.

Target:
    repository: JunQianNuo/-1
    commit: 5b37d76938e78e26778240a4574e5e9ee8b5b75d

Place this file in 代码/问题二 and run:
    python apply_q2_actual_fix.py
"""

from __future__ import annotations

from pathlib import Path
import py_compile
import shutil
import sys


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "run_q2_optimized_search.py"
COVERAGE = ROOT / "q2_kdtree_coverage.py"


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    """Replace exactly one old fragment, or accept an already patched file."""

    if new in text:
        if old in text:
            raise RuntimeError(
                f"{label}: both old and new fragments are present; mixed state."
            )
        print(f"[already fixed] {label}")
        return text, False

    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one old fragment, found {count}. "
            "The local file may not match commit "
            "5b37d76938e78e26778240a4574e5e9ee8b5b75d."
        )

    print(f"[patched] {label}")
    return text.replace(old, new, 1), True


def backup_once(path: Path) -> None:
    backup = path.with_name(path.name + ".bak_before_actual_fix")
    if backup.exists():
        print(f"[backup exists] {backup.name}")
        return
    shutil.copy2(path, backup)
    print(f"[backup] {backup.name}")


def patch_runner(text: str) -> tuple[str, int]:
    changes = 0

    old = """    active_times = q2.make_time_grid(
        args.screen_duration_hours * 3600.0,
        args.active_time_step,
    )
"""
    new = """    # The local active set must cover the same full horizon as the
    # separation oracle. Otherwise most of the 24 h domain is absent from
    # the continuous-parameter optimization.
    active_times = q2.make_time_grid(
        args.separation_duration_hours * 3600.0,
        args.active_time_step,
    )
"""
    text, changed = replace_once(
        text, old, new, "active set spans separation horizon"
    )
    changes += int(changed)

    old = """    all_screen_records: list[dict] = []
    all_refined_records: list[dict] = []
    structure_audit: list[dict] = []
    validated_solution: dict | None = None
    adaptive_certificate: dict | None = None
"""
    new = """    all_screen_records: list[dict] = []
    all_refined_records: list[dict] = []
    structure_audit: list[dict] = []

    # Numerical feasibility and continuous certification are different states.
    first_numerical_solution: dict | None = None
    validated_solution: dict | None = None
    adaptive_certificate: dict | None = None
    adaptive_certificates: list[dict] = []
"""
    text, changed = replace_once(
        text, old, new, "separate numerical and certified candidates"
    )
    changes += int(changed)

    old = """    for total_offset, total in enumerate(range(args.start_total, args.stop_total + 1)):
        total_candidates: list[tuple[dict, q2.ConstellationParams, WalkerStructure]] = []
        structures = walker_structures(total)
"""
    new = """    for total_offset, total in enumerate(range(args.start_total, args.stop_total + 1)):
        total_candidates: list[tuple[dict, q2.ConstellationParams, WalkerStructure]] = []
        current_total_solution: dict | None = None
        audit_start_index = len(structure_audit)
        structures = walker_structures(total)
"""
    text, changed = replace_once(
        text, old, new, "initialize per-total candidate and audit scope"
    )
    changes += int(changed)

    old = """                    q=args.q,
                    include_representatives=not args.no_representatives,
                    stop_if_margin_below=-0.02,
                )
                record = result_record(result, stage="screen")
"""
    new = """                    q=args.q,
                    include_representatives=not args.no_representatives,
                    # Ranking candidates requires the same complete time grid.
                    stop_if_margin_below=None,
                )
                if result.stopped_early or result.evaluated_time_steps != len(screen_times):
                    raise RuntimeError(
                        "Incomplete screening evaluation: expected "
                        f"{len(screen_times)} time steps, got "
                        f"{result.evaluated_time_steps}."
                    )
                record = result_record(result, stage="screen")
"""
    text, changed = replace_once(
        text, old, new, "disable biased screening early exit"
    )
    changes += int(changed)

    old = """                    "phase_factor": structure.phase_factor,
                    "screen_evaluations": len(structure_records),
                    "selected_for_refinement": len(selected),
                }
"""
    new = """                    "phase_factor": structure.phase_factor,
                    "screen_evaluations": len(structure_records),
                    "local_starts_retained": len(selected),
                    # Filled after the global per-total Top-K cut.
                    "selected_for_refinement": 0,
                }
"""
    text, changed = replace_once(
        text, old, new, "separate local and final audit counts"
    )
    changes += int(changed)

    old = """        total_candidates = total_candidates[: args.keep_top_per_total]

        for _screen_record, params, structure in total_candidates:
"""
    new = """        total_candidates = total_candidates[: args.keep_top_per_total]

        # Audit only starts that actually survive the global Top-K cut.
        final_selection_counts: dict[tuple[int, int, int], int] = {}
        for _record, _params, selected_structure in total_candidates:
            key = (
                selected_structure.planes,
                selected_structure.sats_per_plane,
                selected_structure.phase_factor,
            )
            final_selection_counts[key] = final_selection_counts.get(key, 0) + 1

        for audit_row in structure_audit[audit_start_index:]:
            key = (
                int(audit_row["planes"]),
                int(audit_row["sats_per_plane"]),
                int(audit_row["phase_factor"]),
            )
            audit_row["selected_for_refinement"] = final_selection_counts.get(key, 0)

        for _screen_record, params, structure in total_candidates:
"""
    text, changed = replace_once(
        text, old, new, "audit actual global Top-K refinement starts"
    )
    changes += int(changed)

    old = """            if (
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
"""
    new = """            if (
                refined.converged
                and record["c_min"] >= args.q
                and record["min_margin"] >= -args.margin_tolerance
            ):
                if (
                    current_total_solution is None
                    or score_record(record, args.q)
                    > score_record(current_total_solution, args.q)
                ):
                    current_total_solution = record
"""
    text, changed = replace_once(
        text, old, new, "select best numerical candidate per total"
    )
    changes += int(changed)

    old = """        if validated_solution is not None:
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
"""
    new = """        if current_total_solution is not None:
            if first_numerical_solution is None:
                first_numerical_solution = current_total_solution

            accepted = True
            if args.adaptive_verify:
                certificate_params = q2.ConstellationParams(
                    planes=int(current_total_solution["planes"]),
                    sats_per_plane=int(current_total_solution["sats_per_plane"]),
                    phase_factor=int(current_total_solution["phase_factor"]),
                    inclination_deg=float(current_total_solution["inclination_deg"]),
                    raan0_deg=float(current_total_solution["raan0_deg"]),
                    u0_deg=float(current_total_solution["u0_deg"]),
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
                adaptive_certificates.append(
                    {
                        "total_satellites": total,
                        "candidate": current_total_solution,
                        "certificate": adaptive_certificate,
                    }
                )
                accepted = certificate.status == "covered"

            if accepted:
                # Totals are processed in ascending order; first accepted is minimum.
                if validated_solution is None:
                    validated_solution = current_total_solution
                if not args.continue_after_validated:
                    break
"""
    text, changed = replace_once(
        text, old, new, "continue after failed or inconclusive certificate"
    )
    changes += int(changed)

    old = """        "screen_record_count": len(all_screen_records),
        "refined_record_count": len(all_refined_records),
        "validated_numerical_candidate": validated_solution,
        "adaptive_certificate": adaptive_certificate,
"""
    new = """        "screen_record_count": len(all_screen_records),
        "refined_record_count": len(all_refined_records),
        "first_numerical_candidate": first_numerical_solution,
        "validated_numerical_candidate": validated_solution,
        "adaptive_certificate": adaptive_certificate,
        "adaptive_certificates": adaptive_certificates,
"""
    text, changed = replace_once(
        text, old, new, "report numerical and certified outcomes separately"
    )
    changes += int(changed)

    old = """    print(f"Screen evaluations: {len(all_screen_records)}")
    print(f"Refined candidates: {len(all_refined_records)}")
    print(f"Best numerical candidate: {validated_solution}")
    print(f"Outputs: {args.output_dir}")
"""
    new = """    print(f"Screen evaluations: {len(all_screen_records)}")
    print(f"Refined candidates: {len(all_refined_records)}")
    print(f"First numerical candidate: {first_numerical_solution}")
    print(f"Accepted candidate: {validated_solution}")
    if args.adaptive_verify and adaptive_certificate is not None:
        print(f"Last adaptive certificate status: {adaptive_certificate['status']}")
    print(f"Outputs: {args.output_dir}")
"""
    text, changed = replace_once(
        text, old, new, "print unambiguous outcomes"
    )
    changes += int(changed)

    return text, changes


def patch_coverage(text: str) -> tuple[str, int]:
    old = """def _longest_false_gap_s(values: np.ndarray, times_s: np.ndarray) -> float:
    values = np.asarray(values, dtype=bool)
    if not len(values):
        return 0.0
    dt = float(np.median(np.diff(times_s))) if len(times_s) >= 2 else 0.0
    longest = current = 0
    for value in values:
        if value:
            longest = max(longest, current)
            current = 0
        else:
            current += 1
    return float(max(longest, current) * dt)
"""
    new = """def _longest_false_gap_s(values: np.ndarray, times_s: np.ndarray) -> float:
    \"""Return the longest sampled uncovered interval from actual time coordinates.\"""

    covered = np.asarray(values, dtype=bool)
    times = np.asarray(times_s, dtype=float)
    if covered.ndim != 1 or times.ndim != 1:
        raise ValueError("values and times_s must be one-dimensional")
    if len(covered) != len(times):
        raise ValueError("values and times_s must have equal length")
    if not len(covered):
        return 0.0
    if np.any(np.diff(times) < 0.0):
        raise ValueError("times_s must be nondecreasing")

    longest = 0.0
    run_start: int | None = None
    for index, is_covered in enumerate(covered):
        if not is_covered and run_start is None:
            run_start = index
        elif is_covered and run_start is not None:
            longest = max(longest, float(times[index] - times[run_start]))
            run_start = None

    if run_start is not None:
        longest = max(longest, float(times[-1] - times[run_start]))

    return longest
"""
    text, changed = replace_once(
        text, old, new, "compute uncovered gaps from actual times"
    )
    return text, int(changed)


def main() -> int:
    for path in (RUNNER, COVERAGE):
        if not path.exists():
            print(f"ERROR: missing {path}", file=sys.stderr)
            return 2

    runner_original = RUNNER.read_text(encoding="utf-8")
    coverage_original = COVERAGE.read_text(encoding="utf-8")

    try:
        runner_fixed, runner_changes = patch_runner(runner_original)
        coverage_fixed, coverage_changes = patch_coverage(coverage_original)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if runner_changes:
        backup_once(RUNNER)
        RUNNER.write_text(runner_fixed, encoding="utf-8")
    if coverage_changes:
        backup_once(COVERAGE)
        COVERAGE.write_text(coverage_fixed, encoding="utf-8")

    try:
        py_compile.compile(str(RUNNER), doraise=True)
        py_compile.compile(str(COVERAGE), doraise=True)
    except py_compile.PyCompileError as exc:
        print(f"ERROR: patched code did not compile: {exc}", file=sys.stderr)
        return 4

    print(
        "SUCCESS: actual submitted code patched and compiled. "
        f"Changes: runner={runner_changes}, coverage={coverage_changes}."
    )
    print("Next: python verify_q2_actual_fix.py --source-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
