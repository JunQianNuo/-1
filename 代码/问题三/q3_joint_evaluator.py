"""Incremental joint coverage and communication evaluation for one candidate."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

import numpy as np

from q3_access import access_sets_naive
from q3_batched_routing import batched_ground_delay_matrix
from q3_config import ConstellationParams, Q3Config, SimulationConfig
from q3_joint_search import (
    ServiceProgress,
    WeightedCoverageProgress,
    max_reachable_late_samples,
    optimistic_delay_lower_bounds,
)
from q3_orbit import satellite_positions
from q3_topology import build_isl_graph


@dataclass(frozen=True)
class MotherGrid:
    times_s: np.ndarray
    coverage_ground_unit: np.ndarray
    coverage_weights: np.ndarray
    communication_ground_ecef_km: np.ndarray
    communication_sample_weight: float = 1.0


@dataclass(frozen=True)
class FidelityGrid:
    name: str
    time_indices: np.ndarray
    coverage_point_indices: np.ndarray
    communication_point_indices: np.ndarray


@dataclass
class JointEvaluationState:
    coverage_progress: WeightedCoverageProgress
    service_progress: ServiceProgress
    processed_coverage_keys: set[tuple[int, int]]
    processed_od_keys: set[tuple[int, int, int]]
    _reachable_count: int = field(default=0, repr=False)
    _late_reachable_count: int = field(default=0, repr=False)
    _unreachable_count: int = field(default=0, repr=False)
    _max_delay_s: float | None = field(default=None, repr=False)
    _mother_digest: str = field(default="", repr=False)


@dataclass(frozen=True)
class ServiceSummary:
    p30_reachable: float
    p30_all: float
    reachable_count: int
    late_reachable_count: int
    unreachable_count: int
    max_delay_s: float | None
    feasible_reachable: bool
    feasible_all: bool


@dataclass(frozen=True)
class JointEvaluation:
    status: str
    c1: float
    c2: float
    p30_reachable: float
    p30_all: float
    reachable_count: int
    late_reachable_count: int
    unreachable_count: int
    max_delay_s: float | None
    processed_times: int
    message: str


def coverage_counts_from_ecef(
    satellite_ecef_km: np.ndarray,
    ground_unit_vectors: np.ndarray,
    *,
    coverage_angle_rad: float,
) -> np.ndarray:
    """Count satellites within the geocentric angular radius of each point."""

    satellite = _coordinate_matrix(satellite_ecef_km, "satellite_ecef_km", allow_empty=False)
    ground = _coordinate_matrix(ground_unit_vectors, "ground_unit_vectors", allow_empty=True)
    angle = _finite_float(coverage_angle_rad, "coverage_angle_rad")
    if not 0.0 <= angle <= math.pi:
        raise ValueError("coverage_angle_rad must lie in [0, pi]")
    sat_unit = satellite / np.linalg.norm(satellite, axis=1)[:, None]
    if len(ground) == 0:
        return np.zeros(0, dtype=int)
    ground_unit = ground / np.linalg.norm(ground, axis=1)[:, None]
    return np.count_nonzero(
        ground_unit @ sat_unit.T >= math.cos(angle) - 1e-12, axis=1
    ).astype(int)


def summarize_service_delays(
    delays_s: np.ndarray,
    *,
    delay_limit_s: float = 0.030,
    eta_reach: float = 0.999,
    eta_all: float = 0.95,
) -> ServiceSummary:
    """Summarize equal-weight delays, treating positive infinity as unreachable."""

    delays = np.asarray(delays_s, dtype=float)
    if delays.ndim != 1:
        raise ValueError("delays_s must be one-dimensional")
    if np.any(np.isnan(delays)) or np.any(delays < 0.0) or np.any(np.isneginf(delays)):
        raise ValueError("delays_s must contain nonnegative values or positive infinity")
    limit = _finite_float(delay_limit_s, "delay_limit_s")
    if limit < 0.0:
        raise ValueError("delay_limit_s must be nonnegative")
    _unit_interval(eta_reach, "eta_reach")
    _unit_interval(eta_all, "eta_all")

    finite = delays[np.isfinite(delays)]
    reachable = int(finite.size)
    late = int(np.count_nonzero(finite > limit))
    within = reachable - late
    unreachable = int(delays.size - reachable)
    p_reachable = 1.0 if reachable == 0 else within / reachable
    p_all = 1.0 if delays.size == 0 else within / delays.size
    return ServiceSummary(
        p30_reachable=float(p_reachable),
        p30_all=float(p_all),
        reachable_count=reachable,
        late_reachable_count=late,
        unreachable_count=unreachable,
        max_delay_s=None if reachable == 0 else float(np.max(finite)),
        feasible_reachable=late <= max_reachable_late_samples(reachable, eta_reach),
        feasible_all=p_all >= eta_all,
    )


def evaluate_joint_candidate(
    params: ConstellationParams,
    *,
    mother_grid: MotherGrid,
    fidelity: FidelityGrid,
    state: JointEvaluationState | None = None,
    config: Q3Config | None = None,
    simulation: SimulationConfig | None = None,
    c1_min: float = 0.999,
    c2_min: float = 0.95,
    eta_reach: float = 0.999,
    eta_all: float = 0.95,
) -> tuple[JointEvaluation, JointEvaluationState]:
    """Evaluate newly selected mother-grid keys, reusing prior progress."""

    params.validate()
    mother = _validate_mother_grid(mother_grid)
    selected = _validate_fidelity(fidelity, mother)
    cfg = config or Q3Config()
    sim = simulation or SimulationConfig()
    _unit_interval(c1_min, "c1_min")
    _unit_interval(c2_min, "c2_min")
    _unit_interval(eta_reach, "eta_reach")
    _unit_interval(eta_all, "eta_all")

    total_coverage = len(mother.times_s) * float(np.sum(mother.coverage_weights))
    ground_count = len(mother.communication_ground_ecef_km)
    total_service = (
        len(mother.times_s)
        * ground_count
        * (ground_count - 1)
        * mother.communication_sample_weight
    )
    if state is None:
        state = JointEvaluationState(
            WeightedCoverageProgress(total_coverage, c1_min, c2_min),
            ServiceProgress(total_service, eta_reach, eta_all),
            set(),
            set(),
            _mother_digest=_mother_grid_digest(mother),
        )
    else:
        _validate_state(
            state,
            _mother_grid_digest(mother),
            total_coverage,
            total_service,
            c1_min,
            c2_min,
            eta_reach,
            eta_all,
        )

    for time_index in selected.time_indices:
        t = int(time_index)
        new_coverage = [
            int(point)
            for point in selected.coverage_point_indices
            if (t, int(point)) not in state.processed_coverage_keys
        ]
        comm = [int(point) for point in selected.communication_point_indices]
        new_pairs = [
            (source, target)
            for source in comm
            for target in comm
            if source != target and (t, source, target) not in state.processed_od_keys
        ]
        if not new_coverage and not new_pairs:
            continue

        satellite_eci, satellite_ecef = satellite_positions(params, float(mother.times_s[t]), cfg)
        if new_coverage:
            counts = coverage_counts_from_ecef(
                satellite_ecef,
                mother.coverage_ground_unit[new_coverage],
                coverage_angle_rad=cfg.access_angle_rad,
            )
            for point, count in zip(new_coverage, counts):
                state.coverage_progress.update(
                    float(mother.coverage_weights[point]), count >= 1, count >= 2
                )
                state.processed_coverage_keys.add((t, point))
                if not state.coverage_progress.can_still_pass():
                    return _result(state, mother, "rejected", "coverage_upper_bound"), state

        if not new_pairs:
            continue
        communication_points = mother.communication_ground_ecef_km[comm]
        access = access_sets_naive(satellite_ecef, communication_points, cfg.access_angle_rad)
        local_index = {mother_index: local for local, mother_index in enumerate(comm)}
        local_pairs = [(local_index[a], local_index[b]) for a, b in new_pairs]
        lower_bounds = optimistic_delay_lower_bounds(
            access_sets=access,
            satellite_ecef_km=satellite_ecef,
            ground_points_ecef_km=communication_points,
            od_pairs=local_pairs,
            c_km_s=cfg.speed_of_light_km_s,
            processing_delay_s=cfg.processing_delay_s,
        )
        guaranteed_misses = sum(value > cfg.delay_limit_s for value in lower_bounds.values())
        optimistic_all = (
            state.service_progress.within_limit_weight
            + (state.service_progress.total_weight - state.service_progress.processed_weight)
            - guaranteed_misses * mother.communication_sample_weight
        ) / state.service_progress.total_weight
        if optimistic_all < eta_all:
            return _result(state, mother, "rejected", "delay_lower_bound_all_upper"), state

        graph = build_isl_graph(
            satellite_eci, params, config=cfg, method=sim.topology_method
        )
        delay_matrix = batched_ground_delay_matrix(
            graph,
            access,
            satellite_ecef,
            communication_points,
            c_km_s=cfg.speed_of_light_km_s,
        )
        for source, target in new_pairs:
            delay = float(delay_matrix[local_index[source], local_index[target]])
            reachable = math.isfinite(delay)
            within_limit = reachable and delay <= cfg.delay_limit_s
            state.service_progress.update(
                mother.communication_sample_weight, reachable, within_limit
            )
            state.processed_od_keys.add((t, source, target))
            if reachable:
                state._reachable_count += 1
                state._late_reachable_count += int(not within_limit)
                state._max_delay_s = delay if state._max_delay_s is None else max(state._max_delay_s, delay)
            else:
                state._unreachable_count += 1
        if not state.service_progress.can_still_pass():
            return _result(state, mother, "rejected", "communication_upper_bound"), state

    complete = (
        len(state.processed_coverage_keys) == len(mother.times_s) * len(mother.coverage_weights)
        and len(state.processed_od_keys)
        == len(mother.times_s) * ground_count * (ground_count - 1)
    )
    if not complete:
        return _result(state, mother, "active", "incomplete"), state
    feasible = (
        _coverage_rates(state, mother)[0] >= c1_min
        and _coverage_rates(state, mother)[1] >= c2_min
        and _service_rates(state, mother)[0] >= eta_reach
        and _service_rates(state, mother)[1] >= eta_all
    )
    status = "verified" if feasible else "rejected"
    return _result(state, mother, status, "constraints_pass" if feasible else "constraints_fail"), state


def _result(state: JointEvaluationState, mother: MotherGrid, status: str, message: str) -> JointEvaluation:
    c1, c2 = _coverage_rates(state, mother)
    p_reachable, p_all = _service_rates(state, mother)
    processed_times = len(
        {key[0] for key in state.processed_coverage_keys}
        | {key[0] for key in state.processed_od_keys}
    )
    return JointEvaluation(
        status, c1, c2, p_reachable, p_all, state._reachable_count,
        state._late_reachable_count, state._unreachable_count, state._max_delay_s,
        processed_times, message,
    )


def _coverage_rates(state: JointEvaluationState, mother: MotherGrid) -> tuple[float, float]:
    denominator = state.coverage_progress.processed_weight
    if len(state.processed_coverage_keys) == len(mother.times_s) * len(mother.coverage_weights):
        denominator = state.coverage_progress.total_weight
    if denominator == 0.0:
        return 1.0, 1.0
    return (
        state.coverage_progress.single_hit_weight / denominator,
        state.coverage_progress.double_hit_weight / denominator,
    )


def _service_rates(state: JointEvaluationState, mother: MotherGrid) -> tuple[float, float]:
    reachable = state.service_progress.reachable_weight
    p_reachable = 1.0 if reachable == 0.0 else state.service_progress.within_limit_weight / reachable
    ground_count = len(mother.communication_ground_ecef_km)
    complete = len(state.processed_od_keys) == len(mother.times_s) * ground_count * (ground_count - 1)
    denominator = (
        state.service_progress.total_weight
        if complete
        else state.service_progress.processed_weight
    )
    p_all = 1.0 if denominator == 0.0 else state.service_progress.within_limit_weight / denominator
    return float(p_reachable), float(p_all)


def _validate_mother_grid(grid: MotherGrid) -> MotherGrid:
    times = np.asarray(grid.times_s)
    if times.ndim != 1 or len(times) == 0:
        raise ValueError("times_s must be a nonempty one-dimensional array")
    if not np.issubdtype(times.dtype, np.number) or not np.all(np.isfinite(times)):
        raise ValueError("times_s must be finite")
    coverage = _coordinate_matrix(grid.coverage_ground_unit, "coverage_ground_unit", allow_empty=False)
    weights = np.asarray(grid.coverage_weights)
    if weights.ndim != 1 or len(weights) != len(coverage):
        raise ValueError("coverage_weights must match coverage_ground_unit")
    if not np.issubdtype(weights.dtype, np.number) or not np.all(np.isfinite(weights)) or np.any(weights <= 0):
        raise ValueError("coverage_weights must be positive and finite")
    communication = _coordinate_matrix(
        grid.communication_ground_ecef_km, "communication_ground_ecef_km", allow_empty=False
    )
    if len(communication) < 2:
        raise ValueError("communication_ground_ecef_km must contain at least two points")
    _positive_finite(grid.communication_sample_weight, "communication_sample_weight")
    return grid


def _validate_fidelity(grid: FidelityGrid, mother: MotherGrid) -> FidelityGrid:
    _index_array(grid.time_indices, "time_indices", len(mother.times_s))
    _index_array(grid.coverage_point_indices, "coverage_point_indices", len(mother.coverage_weights))
    _index_array(
        grid.communication_point_indices,
        "communication_point_indices",
        len(mother.communication_ground_ecef_km),
    )
    return grid


def _index_array(values: np.ndarray, name: str, upper: int) -> None:
    array = np.asarray(values)
    if array.ndim != 1 or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{name} must be a one-dimensional integer array")
    if len(np.unique(array)) != len(array):
        raise ValueError(f"{name} indices must be unique")
    if np.any(array < 0) or np.any(array >= upper):
        raise IndexError(f"{name} index out of range")


def _validate_state(
    state, mother_digest, coverage_total, service_total, c1, c2, eta_reach, eta_all
):
    if state._mother_digest != mother_digest:
        raise ValueError("state is incompatible with the mother grid")
    coverage = state.coverage_progress
    service = state.service_progress
    expected = (coverage_total, service_total, c1, c2, eta_reach, eta_all)
    actual = (coverage.total_weight, service.total_weight, coverage.c1_min, coverage.c2_min, service.eta_reach, service.eta_all)
    if any(not math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0) for a, b in zip(actual, expected)):
        raise ValueError("state is incompatible with the mother grid or thresholds")


def _mother_grid_digest(grid: MotherGrid) -> str:
    """Return an exact deterministic identity for state-to-mother binding."""

    digest = hashlib.sha256()
    for name, values in (
        ("times_s", grid.times_s),
        ("coverage_ground_unit", grid.coverage_ground_unit),
        ("coverage_weights", grid.coverage_weights),
        ("communication_ground_ecef_km", grid.communication_ground_ecef_km),
        ("communication_sample_weight", grid.communication_sample_weight),
    ):
        array = np.asarray(values)
        digest.update(name.encode("ascii"))
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(repr(array.shape).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _coordinate_matrix(values, name: str, *, allow_empty: bool) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[1:] != (3,) or (not allow_empty and len(array) == 0):
        raise ValueError(f"{name} must have shape (N, 3)")
    if not np.all(np.isfinite(array)) or np.any(np.linalg.norm(array, axis=1) == 0.0):
        raise ValueError(f"{name} must contain finite nonzero vectors")
    return array


def _finite_float(value, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive_finite(value, name: str) -> float:
    result = _finite_float(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return result


def _unit_interval(value, name: str) -> float:
    result = _finite_float(value, name)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1]")
    return result
