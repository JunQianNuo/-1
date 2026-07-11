"""Runnable joint coverage and communication inverse-search entry point.

The entry point deliberately keeps persistence in the parent process.  Worker
results contain no wall-clock fields, which makes candidate records identical
for serial and process-parallel runs.
"""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import asdict, dataclass, fields, replace
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Iterable, Sequence

import numpy as np

from q3_config import ConstellationParams, Q3Config, SimulationConfig
from q3_joint_evaluator import (
    FidelityGrid,
    JointEvaluationState,
    MotherGrid,
    evaluate_joint_candidate,
)
from q3_joint_search import (
    CandidateAuditRecord,
    JointSearchConfig,
    ServiceProgress,
    WeightedCoverageProgress,
    conclude_star_layer,
    generate_mn_layers,
    max_reachable_late_samples,
    u0_periodic_grid,
)
from q3_orbit import ground_ecef, make_latlon_grid, make_time_grid
from q3_saturation import (
    SaturationObservation,
    first_saturation_decision,
)


SCHEMA_VERSION = "q3-joint-v1"
STAGES = ("low", "medium", "high")
STRICT_REASONS = {
    "coverage_upper_bound",
}
SATURATION_CURVE_COLUMNS = [
    "S", "candidate_key", "M", "N", "F", "i", "u0",
    "c1", "c2", "p30_all", "p30_reachable", "max_delay_s",
]
CANDIDATE_COLUMNS = [
    "sequence", "mode", "stage", "candidate_key", "S", "M", "N", "F",
    "i", "u0", "status", "strict_evidence", "feasible", "c1", "c2",
    "p30_reachable", "p30_all", "max_delay_s", "reachable_count",
    "late_reachable_count", "unreachable_count", "reason",
]
TIMING_COLUMNS = ["sequence", "mode", "stage", "candidate_key", "elapsed_s"]
LAYER_COLUMNS = ["mode", "S", "status", "candidate_count", "verified", "rejected", "numerical_error"]


@dataclass(frozen=True)
class CachedCandidate:
    params: ConstellationParams
    c1: float
    c2: float


def load_q2_discovery_candidates(
    path: Path, *, c1_min: float = 0.999, c2_min: float = 0.95
) -> list[CachedCandidate]:
    """Load, audit, filter and deterministically deduplicate a Q2 CSV cache."""

    required = {"S", "M", "N", "F", "i", "u0", "C1", "C2"}
    best: dict[tuple[int, int, int, float, float], CachedCandidate] = {}
    try:
        handle = Path(path).open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ValueError(f"cannot read Q2 cache: {path}") from exc
    with handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Q2 cache missing columns: {', '.join(sorted(missing))}")
        for line_number, row in enumerate(reader, 2):
            try:
                s, m, n, f = (int(row[name]) for name in ("S", "M", "N", "F"))
                inclination, u0 = float(row["i"]), float(row["u0"])
                c1, c2 = float(row["C1"]), float(row["C2"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid Q2 cache value on line {line_number}") from exc
            if s != m * n:
                raise ValueError(f"Q2 cache S != M*N on line {line_number}")
            if not all(math.isfinite(value) for value in (inclination, u0, c1, c2)):
                raise ValueError(f"non-finite Q2 cache value on line {line_number}")
            if c1 < c1_min or c2 < c2_min:
                continue
            params = ConstellationParams(m, n, f, inclination, u0_deg=u0)
            params.validate()
            candidate = CachedCandidate(params, c1, c2)
            key = (m, n, f, inclination, u0)
            previous = best.get(key)
            if previous is None or (c2, c1) > (previous.c2, previous.c1):
                best[key] = candidate
    return sorted(
        best.values(),
        key=lambda item: (
            item.params.total_satellites, -item.c2, -item.c1,
            _parameter_tuple(item.params),
        ),
    )


def config_digest(config: dict) -> str:
    """SHA-256 digest of compact canonical JSON."""

    payload = json.dumps(
        config, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def append_checkpoint(path: Path, record: dict) -> None:
    """Append one UTF-8 JSONL record and flush it before returning."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_checkpoint(path: Path, *, expected_config_digest: str) -> dict[str, dict]:
    """Load and validate terminal stage records from a checkpoint."""

    loaded: dict[str, dict] = {}
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed checkpoint record on line {line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"malformed checkpoint record on line {line_number}")
            if record.get("config_digest") != expected_config_digest:
                raise ValueError(f"checkpoint config digest mismatch on line {line_number}")
            candidate = record.get("candidate_key", record.get("candidate"))
            if not isinstance(candidate, str) or not candidate:
                raise ValueError(f"malformed checkpoint candidate on line {line_number}")
            identity = _checkpoint_identity(record, candidate)
            previous = loaded.get(identity)
            if previous is not None and _terminal_payload(previous) != _terminal_payload(record):
                raise ValueError(f"conflicting duplicate terminal record for {identity}")
            loaded[identity] = record
    return loaded


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("discover", "certify", "both", "saturation"), default="both")
    parser.add_argument("--q2-cache", type=Path)
    parser.add_argument("--out", type=Path, default=Path("results/q3_joint"))
    parser.add_argument("--s-lb", type=int, default=1)
    parser.add_argument("--s-max", type=int, default=1800)
    parser.add_argument("--s-step", type=int, default=20)
    parser.add_argument("--forward-window-s", type=int, default=200)
    parser.add_argument("--max-window-gain", type=float, default=0.01)
    parser.add_argument("--max-gain-per-100", type=float, default=0.005)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--duration-s", type=float, default=86164.09)
    parser.add_argument("--high-time-step-s", type=float, default=150.0)
    parser.add_argument("--coverage-high-step-deg", type=float, default=1.0)
    parser.add_argument("--communication-high-step-deg", type=float, default=5.0)
    parser.add_argument("--inclinations-deg", default="49,50,51")
    parser.add_argument("--u0-divisions", type=int, default=4)
    parser.add_argument("--m-min", type=int, default=1)
    parser.add_argument("--m-max", type=int, default=60)
    parser.add_argument("--n-min", type=int, default=1)
    parser.add_argument("--n-max", type=int, default=60)
    parser.add_argument("--keep-low", type=int, default=100)
    parser.add_argument("--keep-medium", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        args.inclinations_deg = tuple(float(value.strip()) for value in args.inclinations_deg.split(",") if value.strip())
    except ValueError as exc:
        parser.error(f"invalid --inclinations-deg: {exc}")
    _validate_args(args, parser)
    return args


def build_nested_grids(
    args: argparse.Namespace, q3_config: Q3Config
) -> tuple[MotherGrid, dict[str, FidelityGrid]]:
    """Build independent coverage/communication mother grids and index subsets."""

    high_time = float(args.high_time_step_s)
    high_coverage = float(args.coverage_high_step_deg)
    high_communication = float(args.communication_high_step_deg)
    level_steps = {
        "low": (max(900.0, high_time), max(4.0, high_coverage), max(25.0, high_communication)),
        "medium": (max(300.0, high_time), max(2.0, high_coverage), max(10.0, high_communication)),
        "high": (high_time, high_coverage, high_communication),
    }
    for time_step, coverage_step, communication_step in level_steps.values():
        _require_multiple(time_step, high_time, "time")
        _require_multiple(coverage_step, high_coverage, "coverage")
        _require_multiple(communication_step, high_communication, "communication")

    times = make_time_grid(args.duration_s, high_time)
    cov_lat, cov_lon = make_latlon_grid(4.0, 53.0, 73.0, 135.0, high_coverage)
    comm_lat, comm_lon = make_latlon_grid(4.0, 53.0, 73.0, 135.0, high_communication)
    coverage_ecef = ground_ecef(cov_lat, cov_lon, radius_km=1.0)
    communication_ecef = ground_ecef(
        comm_lat, comm_lon, radius_km=q3_config.earth_radius_km
    )
    mother = MotherGrid(
        times_s=times,
        coverage_ground_unit=coverage_ecef,
        coverage_weights=np.cos(np.deg2rad(cov_lat)),
        communication_ground_ecef_km=communication_ecef,
    )
    grids: dict[str, FidelityGrid] = {}
    for name, (time_step, coverage_step, communication_step) in level_steps.items():
        grids[name] = FidelityGrid(
            name=name,
            time_indices=_axis_subset_indices(times, make_time_grid(args.duration_s, time_step)),
            coverage_point_indices=_latlon_subset_indices(
                cov_lat, cov_lon, coverage_step
            ),
            communication_point_indices=_latlon_subset_indices(
                comm_lat, comm_lon, communication_step
            ),
        )
    return mother, grids


def evaluate_candidate_stages(
    params: ConstellationParams,
    mother_grid: MotherGrid,
    fidelities: dict[str, FidelityGrid],
    config: Q3Config,
    simulation: SimulationConfig,
    stages: tuple[str, ...],
) -> tuple[list[CandidateAuditRecord], JointEvaluationState]:
    """Evaluate stages in order, carrying state and converting exceptions to evidence."""

    state: JointEvaluationState | None = None
    records: list[CandidateAuditRecord] = []
    for stage in stages:
        if stage not in fidelities:
            raise ValueError(f"unknown fidelity stage: {stage}")
        try:
            result, state = evaluate_joint_candidate(
                params,
                mother_grid=mother_grid,
                fidelity=fidelities[stage],
                state=state,
                config=config,
                simulation=simulation,
            )
            strict = result.status == "rejected" and (
                result.message in STRICT_REASONS or stage == "high"
            )
            status = result.status
            if stage == "high" and result.status == "verified":
                status = "verified"
            record = CandidateAuditRecord(
                params=params,
                status=status,
                fidelity=stage,
                reason=result.message,
                strict_evidence=strict,
                feasible=result.status == "verified",
                c1=result.c1,
                c2=result.c2,
                p30_reachable=result.p30_reachable,
                p30_all=result.p30_all,
                max_delay_s=result.max_delay_s,
            )
        except Exception as exc:  # A numerical failure must never become a proof.
            record = CandidateAuditRecord(
                params=params,
                status="numerical_error",
                fidelity=stage,
                reason=f"{type(exc).__name__}: {exc}",
            )
            records.append(record)
            if state is None:
                state = _empty_state(mother_grid)
            break
        records.append(record)
        if record.status in {"rejected", "numerical_error"}:
            break
    if state is None:
        state = _empty_state(mother_grid)
    return records, state


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    started = time.perf_counter()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "joint_checkpoint.jsonl"
    q3_config = Q3Config()
    simulation = SimulationConfig(duration_s=args.duration_s, step_s=args.high_time_step_s)
    mother, fidelities = build_nested_grids(args, q3_config)
    config = _digest_config(args, q3_config, simulation, mother, fidelities)
    digest = config_digest(config)

    completed: dict[str, dict] = {}
    if args.resume is not None:
        completed = load_checkpoint(args.resume, expected_config_digest=digest)
        if args.resume.resolve() != checkpoint_path.resolve():
            checkpoint_path.write_text("", encoding="utf-8")
            for record in sorted(completed.values(), key=lambda row: (row.get("sequence", 0), row.get("mode", ""), row.get("stage", ""))):
                append_checkpoint(checkpoint_path, record)
    else:
        checkpoint_path.write_text("", encoding="utf-8")

    persisted = list(completed.values())
    timing_rows: list[dict] = []
    layer_rows: list[dict] = []
    sequence_counter = [1 + max((int(row.get("sequence", -1)) for row in persisted), default=-1)]
    discovered_upper: int | None = None
    best_record: dict | None = None
    claim = "inconclusive"

    if args.mode == "saturation":
        summary_extra: dict = {}
        decision, observations = _run_saturation(
            args, mother, fidelities, q3_config, simulation, digest,
            checkpoint_path, completed, persisted, timing_rows, layer_rows,
            sequence_counter, summary_extra,
        )
        records = sorted(persisted, key=lambda row: (int(row["sequence"]), row["mode"], row["stage"]))
        _write_csv(output / "joint_candidate_records.csv", CANDIDATE_COLUMNS, records)
        _write_csv(output / "joint_stage_timing.csv", TIMING_COLUMNS, timing_rows)
        _write_csv(output / "joint_layer_summary.csv", LAYER_COLUMNS, layer_rows)
        curve_rows = [_curve_row_from_observation(obs) for obs in observations]
        _write_csv(output / "joint_saturation_curve.csv", SATURATION_CURVE_COLUMNS, curve_rows)
        claim = _saturation_claim(decision.status)
        best_candidate = None if decision.selected is None else _observation_summary(decision.selected)
        summary = {
            "schema_version": SCHEMA_VERSION,
            "config_digest": digest,
            "mode": args.mode,
            "claim": claim,
            "search_claim": claim,
            "objective": "p30_all_saturation",
            "coverage_constraints": {"c1_min": 0.999, "c2_min": 0.95},
            "forward_window": {
                "s_step": args.s_step,
                "forward_window_s": args.forward_window_s,
                "max_window_gain": args.max_window_gain,
                "max_gain_per_100": args.max_gain_per_100,
            },
            "saturation_decision": _decision_summary(decision),
            "sample_counts": {
                "times": len(mother.times_s),
                "coverage_points": len(mother.coverage_weights),
                "communication_points": len(mother.communication_ground_ecef_km),
            },
            "best_candidate": best_candidate,
            "observation_count": len(observations),
            "layer_status": None if not layer_rows else layer_rows[-1]["status"],
            "candidate_stage_records": len(records),
            "elapsed_s": time.perf_counter() - started,
            **summary_extra,
        }
        (output / "joint_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        _write_report(output / "joint_report.md", summary)
        return 0

    if args.mode in {"discover", "both"}:
        if args.q2_cache is None:
            raise ValueError("--q2-cache is required for discover and both modes")
        candidates = load_q2_discovery_candidates(args.q2_cache)
        discovered_upper, discover_best = _run_discovery(
            candidates, args, mother, fidelities, q3_config, simulation, digest,
            checkpoint_path, completed, persisted, timing_rows, layer_rows,
            sequence_counter,
        )
        if discover_best is not None:
            claim = "discovered_upper_bound"
            best_record = discover_best

    if args.mode in {"certify", "both"}:
        certify_max = discovered_upper if args.mode == "both" and discovered_upper is not None else args.s_max
        certify_claim, certify_best = _run_certification(
            args, certify_max, mother, fidelities, q3_config, simulation, digest,
            checkpoint_path, completed, persisted, timing_rows, layer_rows,
            sequence_counter,
        )
        claim = certify_claim
        if certify_best is not None:
            best_record = certify_best

    records = sorted(persisted, key=lambda row: (int(row["sequence"]), row["mode"], row["stage"]))
    _write_csv(output / "joint_candidate_records.csv", CANDIDATE_COLUMNS, records)
    _write_csv(output / "joint_stage_timing.csv", TIMING_COLUMNS, timing_rows)
    _write_csv(output / "joint_layer_summary.csv", LAYER_COLUMNS, layer_rows)
    reachable = 0 if best_record is None else int(best_record.get("reachable_count") or 0)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "config_digest": digest,
        "mode": args.mode,
        "claim": claim,
        "search_claim": claim,
        "thresholds": {"c1_min": 0.999, "c2_min": 0.95, "delay_limit_s": q3_config.delay_limit_s},
        "sample_counts": {
            "times": len(mother.times_s),
            "coverage_points": len(mother.coverage_weights),
            "communication_points": len(mother.communication_ground_ecef_km),
            "reachable_count": reachable,
            "n_max": max_reachable_late_samples(reachable),
        },
        "best_candidate": best_record,
        "layer_status": None if not layer_rows else layer_rows[-1]["status"],
        "candidate_stage_records": len(records),
        "elapsed_s": time.perf_counter() - started,
    }
    (output / "joint_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    _write_report(output / "joint_report.md", summary)
    return 0


def _run_discovery(
    cached: list[CachedCandidate], args, mother, fidelities, config, simulation,
    digest, checkpoint_path, completed, persisted, timing_rows, layer_rows,
    sequence_counter,
) -> tuple[int | None, dict | None]:
    active = list(cached)
    coverage = {candidate_key(item.params): (item.c1, item.c2) for item in cached}
    latest: dict[str, dict] = {}
    for stage, keep in (("low", args.keep_low), ("medium", args.keep_medium), ("high", None)):
        if not active:
            break
        evaluated = _evaluate_stage_batch(
            [item.params for item in active], stage, "discover", args.workers,
            mother, fidelities, config, simulation, digest, checkpoint_path,
            completed, persisted, timing_rows, sequence_counter,
        )
        latest.update({row["candidate_key"]: row for row in evaluated})
        survivors = [item for item in active if latest[candidate_key(item.params)]["status"] not in {"rejected", "numerical_error"}]
        survivors.sort(key=lambda item: _rank_key(latest[candidate_key(item.params)], coverage[candidate_key(item.params)]), reverse=True)
        promoted = survivors if keep is None else survivors[:keep]
        promoted_keys = {candidate_key(item.params) for item in promoted}
        if keep is not None:
            for item in survivors:
                if candidate_key(item.params) not in promoted_keys:
                    row = latest[candidate_key(item.params)]
                    row["status"] = "deferred"
                    row["reason"] = f"not_promoted_after_{stage}"
        active = promoted

    verified = [row for row in latest.values() if row["stage"] == "high" and row["status"] == "verified" and row["feasible"]]
    best = min(verified, key=lambda row: (int(row["S"]), tuple(_record_parameter_values(row)))) if verified else None
    grouped: dict[int, list[dict]] = {}
    for row in latest.values():
        grouped.setdefault(int(row["S"]), []).append(row)
    for star_count, rows in sorted(grouped.items()):
        layer_rows.append(_layer_row("discover", star_count, "discovered_upper_bound" if any(r["status"] == "verified" for r in rows) else "inconclusive", rows))
    return (None if best is None else int(best["S"]), best)


def _run_certification(
    args, s_max, mother, fidelities, config, simulation, digest,
    checkpoint_path, completed, persisted, timing_rows, layer_rows,
    sequence_counter,
) -> tuple[str, dict | None]:
    search = JointSearchConfig(
        s_lb=args.s_lb,
        s_max=s_max,
        m_values=range(args.m_min, args.m_max + 1),
        n_values=range(args.n_min, args.n_max + 1),
        inclinations_deg=args.inclinations_deg,
        u0_divisions=args.u0_divisions,
        q3_config=config,
        simulation=simulation,
    )
    lower_inconclusive = False
    any_layer = False
    for layer in generate_mn_layers(search):
        any_layer = True
        params = [
            ConstellationParams(m, n, phase, inclination, u0_deg=u0)
            for m, n in layer.pairs
            for phase in range(m)
            for inclination in args.inclinations_deg
            for u0 in u0_periodic_grid(sats_per_plane=n, divisions=args.u0_divisions)
        ]
        terminal: dict[str, dict] = {}
        active = params
        for stage in STAGES:
            if not active:
                break
            rows = _evaluate_stage_batch(
                active, stage, "certify", args.workers, mother, fidelities,
                config, simulation, digest, checkpoint_path, completed, persisted,
                timing_rows, sequence_counter,
            )
            terminal.update({row["candidate_key"]: row for row in rows})
            active = [p for p in active if terminal[candidate_key(p)]["status"] not in {"rejected", "numerical_error"}]
            active.sort(key=lambda p: _rank_key(terminal[candidate_key(p)], (0.0, 0.0)), reverse=True)
        audit = [_dict_to_audit(row) for row in terminal.values()]
        conclusion = conclude_star_layer(layer.star_count, audit)
        layer_rows.append(_layer_row("certify", layer.star_count, conclusion.status, list(terminal.values())))
        if conclusion.status == "inconclusive":
            lower_inconclusive = True
        if conclusion.status == "feasible_discrete":
            best = terminal[candidate_key(conclusion.best.params)] if conclusion.best else None
            return ("inconclusive" if lower_inconclusive else "feasible_discrete", best)
    if not any_layer or lower_inconclusive:
        return "inconclusive", None
    return "infeasible", None


def _saturation_search_config(args, config, simulation) -> JointSearchConfig:
    """Search bounds for saturation mode.  ``s_lb`` is used unmodified so the
    sampled layers start at the user-provided lower bound."""
    return JointSearchConfig(
        s_lb=args.s_lb,
        s_max=args.s_max,
        m_values=range(args.m_min, args.m_max + 1),
        n_values=range(args.n_min, args.n_max + 1),
        inclinations_deg=args.inclinations_deg,
        u0_divisions=args.u0_divisions,
        q3_config=config,
        simulation=simulation,
    )


def _evaluate_layer_through_high(
    layer, args, mother, fidelities, config, simulation, digest,
    checkpoint_path, completed, persisted, timing_rows, sequence_counter,
) -> dict[str, dict]:
    """Run the low -> medium -> high pipeline for every candidate in one layer.

    Returns the terminal audit row for each candidate keyed by candidate_key.
    """
    params = [
        ConstellationParams(m, n, phase, inclination, u0_deg=u0)
        for m, n in layer.pairs
        for phase in range(m)
        for inclination in args.inclinations_deg
        for u0 in u0_periodic_grid(sats_per_plane=n, divisions=args.u0_divisions)
    ]
    terminal: dict[str, dict] = {}
    active = params
    for stage in STAGES:
        if not active:
            break
        rows = _evaluate_stage_batch(
            active, stage, "saturation", args.workers, mother, fidelities,
            config, simulation, digest, checkpoint_path, completed, persisted,
            timing_rows, sequence_counter,
        )
        terminal.update({row["candidate_key"]: row for row in rows})
        active = [p for p in active if terminal[candidate_key(p)]["status"] not in {"rejected", "numerical_error"}]
        active.sort(key=lambda p: _rank_key(terminal[candidate_key(p)], (0.0, 0.0)), reverse=True)
    return terminal


def _best_verified_high_record(terminal: dict[str, dict]) -> dict | None:
    """Best coverage-feasible high-fidelity row by ``_rank_key`` ordering."""
    verified = [
        row for row in terminal.values()
        if row["stage"] == "high" and row["status"] == "verified" and row["feasible"]
    ]
    if not verified:
        return None
    return max(
        verified,
        key=lambda row: _rank_key(
            row, (float(row.get("c1") or 0.0), float(row.get("c2") or 0.0))
        ),
    )


def _observation_from_record(row: dict) -> SaturationObservation:
    max_delay = row.get("max_delay_s")
    return SaturationObservation(
        stars=int(row["S"]),
        p30_all=float(row["p30_all"]),
        candidate_key=row["candidate_key"],
        p30_reachable=float(row["p30_reachable"]),
        c1=float(row["c1"]),
        c2=float(row["c2"]),
        max_delay_s=None if max_delay is None else float(max_delay),
    )


def _run_saturation(
    args, mother, fidelities, config, simulation, digest, checkpoint_path,
    completed, persisted, timing_rows, layer_rows, sequence_counter, summary_extra,
) -> tuple["SaturationDecision", list[SaturationObservation]]:
    search = _saturation_search_config(args, config, simulation)
    observations: list[SaturationObservation] = []
    for layer in generate_mn_layers(search):
        if (layer.star_count - args.s_lb) % args.s_step:
            continue
        terminal = _evaluate_layer_through_high(
            layer, args, mother, fidelities, config, simulation, digest,
            checkpoint_path, completed, persisted, timing_rows, sequence_counter,
        )
        best = _best_verified_high_record(terminal)
        layer_rows.append(_layer_row(
            "saturation", layer.star_count,
            "verified" if best is not None else "inconclusive",
            list(terminal.values()),
        ))
        if best is None:
            continue
        observations.append(_observation_from_record(best))
        decision = first_saturation_decision(
            observations, forward_window_s=args.forward_window_s,
            max_gain=args.max_window_gain, max_gain_per_100=args.max_gain_per_100,
        )
        if decision.status == "saturated":
            summary_extra["layers_sampled"] = len(observations)
            return decision, observations
    summary_extra["layers_sampled"] = len(observations)
    return (
        first_saturation_decision(
            observations, forward_window_s=args.forward_window_s,
            max_gain=args.max_window_gain, max_gain_per_100=args.max_gain_per_100,
        ),
        observations,
    )


def _curve_row_from_observation(obs: SaturationObservation) -> dict:
    planes, sats_per_plane, phase_factor, inclination, _raan0, u0 = json.loads(obs.candidate_key)
    return {
        "S": obs.stars,
        "candidate_key": obs.candidate_key,
        "M": planes,
        "N": sats_per_plane,
        "F": phase_factor,
        "i": inclination,
        "u0": u0,
        "c1": obs.c1,
        "c2": obs.c2,
        "p30_all": obs.p30_all,
        "p30_reachable": obs.p30_reachable,
        "max_delay_s": obs.max_delay_s,
    }


def _observation_summary(obs: SaturationObservation) -> dict:
    return _curve_row_from_observation(obs)


def _decision_summary(decision) -> dict:
    return {
        "status": decision.status,
        "selected": None if decision.selected is None else _observation_summary(decision.selected),
        "window_end_stars": decision.window_end_stars,
        "window_max_p30_all": decision.window_max_p30_all,
        "window_gain": decision.window_gain,
        "gain_per_100_stars": decision.gain_per_100_stars,
    }


def _saturation_claim(status: str) -> str:
    return {
        "saturated": "saturated_minimum",
        "not_saturated": "not_saturated",
        "insufficient_horizon": "insufficient_horizon",
    }.get(status, status)


def _evaluate_stage_batch(
    params_list, stage, mode, workers, mother, fidelities, config, simulation,
    digest, checkpoint_path, completed, persisted, timing_rows, sequence_counter,
) -> list[dict]:
    rows: list[dict] = []
    pending: list[tuple[int, ConstellationParams]] = []
    for params in params_list:
        identity = _checkpoint_identity({"mode": mode, "stage": stage}, candidate_key(params))
        if identity in completed:
            rows.append(completed[identity])
        else:
            sequence = sequence_counter[0]
            sequence_counter[0] += 1
            pending.append((sequence, params))
    tasks = [(params, mother, fidelities, config, simulation, STAGES[: STAGES.index(stage) + 1]) for _, params in pending]
    start_times = {sequence: time.perf_counter() for sequence, _ in pending}
    if workers == 1:
        results = [evaluate_candidate_stages(*task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_evaluate_task, tasks))
    for (sequence, params), (audit_records, state) in sorted(zip(pending, results), key=lambda item: item[0][0]):
        target = next((record for record in audit_records if record.fidelity == stage), audit_records[-1])
        row = _audit_to_dict(target, sequence, mode, digest, state)
        append_checkpoint(checkpoint_path, row)
        identity = _checkpoint_identity(row, row["candidate_key"])
        completed[identity] = row
        persisted.append(row)
        rows.append(row)
        timing_rows.append({
            "sequence": sequence, "mode": mode, "stage": stage,
            "candidate_key": row["candidate_key"],
            "elapsed_s": time.perf_counter() - start_times[sequence],
        })
    return sorted(rows, key=lambda row: int(row["sequence"]))


def _evaluate_task(task):
    return evaluate_candidate_stages(*task)


def candidate_key(params: ConstellationParams) -> str:
    return json.dumps(
        [params.planes, params.sats_per_plane, params.phase_factor,
         params.inclination_deg, params.raan0_deg, params.u0_deg],
        separators=(",", ":"), allow_nan=False,
    )


def _audit_to_dict(record, sequence, mode, digest, state):
    params = record.params
    return {
        "config_digest": digest,
        "sequence": sequence,
        "mode": mode,
        "stage": record.fidelity,
        "candidate_key": candidate_key(params),
        "S": params.total_satellites,
        "M": params.planes,
        "N": params.sats_per_plane,
        "F": params.phase_factor,
        "i": params.inclination_deg,
        "u0": params.u0_deg,
        "status": record.status,
        "strict_evidence": record.strict_evidence,
        "feasible": record.feasible,
        "c1": record.c1,
        "c2": record.c2,
        "p30_reachable": record.p30_reachable,
        "p30_all": record.p30_all,
        "max_delay_s": record.max_delay_s,
        "reachable_count": getattr(state, "_reachable_count", 0),
        "late_reachable_count": getattr(state, "_late_reachable_count", 0),
        "unreachable_count": getattr(state, "_unreachable_count", 0),
        "reason": record.reason,
    }


def _dict_to_audit(row):
    return CandidateAuditRecord(
        params=ConstellationParams(int(row["M"]), int(row["N"]), int(row["F"]), float(row["i"]), u0_deg=float(row["u0"])),
        status=row["status"], fidelity=row["stage"], reason=row["reason"],
        strict_evidence=bool(row["strict_evidence"]), feasible=bool(row["feasible"]),
        c1=row.get("c1"), c2=row.get("c2"), p30_reachable=row.get("p30_reachable"),
        p30_all=row.get("p30_all"), max_delay_s=row.get("max_delay_s"),
    )


def _rank_key(row, coverage):
    def value(name, missing=-math.inf):
        result = row.get(name)
        return missing if result is None else float(result)
    return (
        value("p30_all"), value("p30_reachable"),
        -value("max_delay_s", math.inf),
        float(coverage[0]), float(coverage[1]),
        tuple(-v if isinstance(v, (int, float)) else v for v in _record_parameter_values(row)),
    )


def _empty_state(mother):
    coverage_total = len(mother.times_s) * float(np.sum(mother.coverage_weights))
    ground_count = len(mother.communication_ground_ecef_km)
    service_total = len(mother.times_s) * ground_count * (ground_count - 1) * mother.communication_sample_weight
    return JointEvaluationState(
        WeightedCoverageProgress(coverage_total), ServiceProgress(service_total), set(), set()
    )


def _digest_config(args, config, simulation, mother, fidelities):
    return {
        "schema_version": SCHEMA_VERSION,
        "thresholds": {"c1_min": 0.999, "c2_min": 0.95},
        "model_constants": asdict(config),
        "simulation": asdict(simulation),
        "region": {"lat": [4.0, 53.0], "lon": [73.0, 135.0]},
        "grid": {
            "duration_s": args.duration_s,
            "high_time_step_s": args.high_time_step_s,
            "coverage_high_step_deg": args.coverage_high_step_deg,
            "communication_high_step_deg": args.communication_high_step_deg,
            "samples": {
                "times": len(mother.times_s), "coverage": len(mother.coverage_weights),
                "communication": len(mother.communication_ground_ecef_km),
            },
            "fidelity_indices": {
                name: {
                    "time": grid.time_indices.tolist(),
                    "coverage": grid.coverage_point_indices.tolist(),
                    "communication": grid.communication_point_indices.tolist(),
                } for name, grid in fidelities.items()
            },
        },
        "search": {
            "mode": args.mode, "s_lb": args.s_lb, "s_max": args.s_max,
            "m": [args.m_min, args.m_max], "n": [args.n_min, args.n_max],
            "inclinations_deg": args.inclinations_deg,
            "u0_divisions": args.u0_divisions,
            "keep_low": args.keep_low, "keep_medium": args.keep_medium,
            "s_step": args.s_step,
            "forward_window_s": args.forward_window_s,
            "max_window_gain": args.max_window_gain,
            "max_gain_per_100": args.max_gain_per_100,
        },
    }


def _axis_subset_indices(mother, coarse):
    indices = []
    for value in coarse:
        matches = np.flatnonzero(np.isclose(mother, value, rtol=0.0, atol=1e-10))
        if len(matches) != 1:
            raise ValueError("coarse time grid is not an exact mother subset")
        indices.append(int(matches[0]))
    return np.asarray(indices, dtype=int)


def _latlon_subset_indices(mother_lat, mother_lon, step):
    coarse_lat, coarse_lon = make_latlon_grid(4.0, 53.0, 73.0, 135.0, step)
    mapping = {
        (round(float(lat), 12), round(float(lon), 12)): index
        for index, (lat, lon) in enumerate(zip(mother_lat, mother_lon))
    }
    try:
        return np.asarray([
            mapping[(round(float(lat), 12), round(float(lon), 12))]
            for lat, lon in zip(coarse_lat, coarse_lon)
        ], dtype=int)
    except KeyError as exc:
        raise ValueError("coarse spatial grid is not an exact mother subset") from exc


def _require_multiple(coarse, high, name):
    ratio = coarse / high
    if not math.isclose(ratio, round(ratio), rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(f"high {name} step must divide coarser steps")


def _validate_args(args, parser):
    if args.workers <= 0:
        parser.error("--workers must be positive")
    if args.s_lb <= 0 or args.s_max < args.s_lb:
        parser.error("invalid satellite bounds")
    if args.s_step <= 0:
        parser.error("--s-step must be a positive integer")
    if args.forward_window_s <= 0:
        parser.error("--forward-window-s must be a positive integer")
    for name in ("max_window_gain", "max_gain_per_100"):
        value = getattr(args, name)
        if not math.isfinite(value) or value < 0:
            parser.error(f"--{name.replace('_', '-')} must be finite and nonnegative")
    if args.m_min <= 0 or args.m_max < args.m_min or args.n_min <= 0 or args.n_max < args.n_min:
        parser.error("invalid M/N bounds")
    if args.u0_divisions <= 0 or args.keep_low < 0 or args.keep_medium < 0:
        parser.error("u0 divisions and keep counts must be nonnegative/positive")
    if not args.inclinations_deg:
        parser.error("at least one inclination is required")
    for name in ("high_time_step_s", "coverage_high_step_deg", "communication_high_step_deg"):
        if not math.isfinite(getattr(args, name)) or getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive and finite")
    if not math.isfinite(args.duration_s) or args.duration_s < 0:
        parser.error("--duration-s must be nonnegative and finite")


def _checkpoint_identity(record, candidate):
    mode, stage = record.get("mode"), record.get("stage")
    return candidate if mode is None and stage is None else f"{mode or ''}|{stage or ''}|{candidate}"


def _terminal_payload(record):
    ignored = {"elapsed_s", "timing_s"}
    return {key: value for key, value in record.items() if key not in ignored}


def _parameter_tuple(params):
    return (params.planes, params.sats_per_plane, params.phase_factor, params.inclination_deg, params.raan0_deg, params.u0_deg)


def _record_parameter_values(row):
    return (int(row["M"]), int(row["N"]), int(row["F"]), float(row["i"]), float(row["u0"]))


def _layer_row(mode, star_count, status, rows):
    return {
        "mode": mode, "S": star_count, "status": status,
        "candidate_count": len(rows),
        "verified": sum(row["status"] == "verified" for row in rows),
        "rejected": sum(row["status"] == "rejected" for row in rows),
        "numerical_error": sum(row["status"] == "numerical_error" for row in rows),
    }


def _write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_report(path, summary):
    if summary.get("mode") == "saturation":
        _write_saturation_report(path, summary)
        return
    thresholds = summary["thresholds"]
    samples = summary["sample_counts"]
    best = summary["best_candidate"]
    lines = [
        "# Joint Q2/Q3 Search Report", "",
        f"- Claim: `{summary['claim']}`",
        f"- Layer status: `{summary['layer_status']}`",
        f"- Elapsed: {summary['elapsed_s']:.6f} s",
        f"- Thresholds: C1 >= {thresholds['c1_min']}, C2 >= {thresholds['c2_min']}",
        f"- Samples: {samples['times']} times, {samples['coverage_points']} coverage points, {samples['communication_points']} communication points",
        f"- Reachable samples: {samples['reachable_count']}; n_max=floor(0.001*reachable_count)={samples['n_max']}",
        f"- Best candidate: `{json.dumps(best, ensure_ascii=False, sort_keys=True)}`" if best else "- Best candidate: none",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_saturation_report(path, summary):
    coverage = summary["coverage_constraints"]
    window = summary["forward_window"]
    samples = summary["sample_counts"]
    decision = summary["saturation_decision"]
    best = summary["best_candidate"]
    status = decision["status"]
    lines = [
        "# Q3 Performance-Saturation Search Report", "",
        f"- Claim: `{summary['claim']}`",
        f"- Objective: `{summary['objective']}` (maximize P30(all); tie-break by P30(reachable), then smaller max delay)",
        f"- Coverage hard constraints: C1 >= {coverage['c1_min']}, C2 >= {coverage['c2_min']}",
        f"- Forward-window parameters: s_step={window['s_step']}, forward_window_s={window['forward_window_s']}, "
        f"max_window_gain={window['max_window_gain']}, max_gain_per_100={window['max_gain_per_100']}",
        f"- Samples: {samples['times']} times, {samples['coverage_points']} coverage points, {samples['communication_points']} communication points",
        f"- Decision status: `{status}`",
    ]
    if status == "saturated" and best is not None:
        lines.extend([
            f"- Selected scale: S = {best['S']} satellites",
            f"- Window end: {decision['window_end_stars']} satellites",
            f"- Window maximum P30(all): {decision['window_max_p30_all']}",
            f"- Cumulative window gain: {decision['window_gain']}",
            f"- Gain per 100 satellites: {decision['gain_per_100_stars']}",
        ])
    elif status == "insufficient_horizon":
        lines.append(
            "- No decision: `insufficient_horizon` — the search did not extend at least "
            f"forward_window_s={window['forward_window_s']} satellites past a candidate point."
        )
    else:  # not_saturated
        lines.append(
            "- No decision: `not_saturated` — every completed forward window exceeded the "
            "approved marginal-gain limits."
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
