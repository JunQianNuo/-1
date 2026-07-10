"""Counterexample-guided continuous-parameter refinement for Problem 2."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as fast
from q2_coverage_margin import ActiveSetMarginResult, evaluate_active_constraints
from q2_kdtree_coverage import KDTreeCoverageResult, evaluate_constellation_kdtree
from q2_search_space import WalkerStructure, wrap_continuous_params

try:
    from scipy.optimize import minimize
except ImportError:  # pragma: no cover
    minimize = None


@dataclass
class ActiveConstraintSet:
    """Pairs of unit-sphere ground points and associated times."""

    ground_points: np.ndarray
    times_s: np.ndarray

    def __post_init__(self) -> None:
        self.ground_points = np.asarray(self.ground_points, dtype=float)
        self.times_s = np.asarray(self.times_s, dtype=float)
        if self.ground_points.ndim != 2 or self.ground_points.shape[1] != 3:
            raise ValueError("ground_points must have shape (A,3)")
        if self.times_s.ndim != 1 or len(self.times_s) != len(self.ground_points):
            raise ValueError("times_s must have one value per point")
        if not len(self.times_s):
            raise ValueError("active constraint set must not be empty")
        norms = np.linalg.norm(self.ground_points, axis=1, keepdims=True)
        if np.any(norms == 0.0):
            raise ValueError("active-set points must be nonzero")
        self.ground_points = self.ground_points / norms

    def add(self, point: np.ndarray, time_s: float, *, tol: float = 1e-9) -> bool:
        point = np.asarray(point, dtype=float)
        if point.shape != (3,):
            raise ValueError("point must have shape (3,)")
        point = point / np.linalg.norm(point)
        same_time = np.abs(self.times_s - float(time_s)) <= tol
        if np.any(same_time):
            distances = np.linalg.norm(self.ground_points[same_time] - point, axis=1)
            if np.any(distances <= tol):
                return False
        self.ground_points = np.vstack([self.ground_points, point])
        self.times_s = np.append(self.times_s, float(time_s))
        return True


@dataclass(frozen=True)
class ContinuousOptimizationResult:
    params: q2.ConstellationParams
    active_margin: ActiveSetMarginResult
    objective_evaluations: int
    success: bool
    message: str


@dataclass(frozen=True)
class CounterexampleSearchResult:
    params: q2.ConstellationParams
    active_set: ActiveConstraintSet
    separation_result: KDTreeCoverageResult
    rounds: int
    converged: bool
    history: tuple[dict, ...]


def _axis_with_endpoint(start: float, stop: float, step: float) -> np.ndarray:
    values = np.arange(start, stop, step, dtype=float)
    if values.size == 0 or not math.isclose(float(values[-1]), stop, abs_tol=1e-12):
        values = np.append(values, stop)
    return values


def initial_active_set(
    region: fast.LatLonRegion,
    times_s: Iterable[float],
    *,
    interior_step_deg: float = 8.0,
    boundary_step_deg: float = 2.0,
) -> ActiveConstraintSet:
    """Construct a small, deterministic coarse active set."""

    if interior_step_deg <= 0.0 or boundary_step_deg <= 0.0:
        raise ValueError("grid steps must be positive")
    times = np.asarray(list(times_s), dtype=float)
    if not len(times):
        raise ValueError("times_s must not be empty")

    interior_lats = _axis_with_endpoint(region.lat_min_deg, region.lat_max_deg, interior_step_deg)
    interior_lons = _axis_with_endpoint(region.lon_min_deg, region.lon_max_deg, interior_step_deg)
    lon_grid, lat_grid = np.meshgrid(interior_lons, interior_lats)
    base_points = fast.latlon_to_unit(lat_grid.ravel(), lon_grid.ravel())

    boundary_points: list[np.ndarray] = []
    edge_lons = _axis_with_endpoint(region.lon_min_deg, region.lon_max_deg, boundary_step_deg)
    edge_lats = _axis_with_endpoint(region.lat_min_deg, region.lat_max_deg, boundary_step_deg)
    boundary_points.extend(
        [
            fast.latlon_to_unit(np.full_like(edge_lons, region.lat_min_deg), edge_lons),
            fast.latlon_to_unit(np.full_like(edge_lons, region.lat_max_deg), edge_lons),
            fast.latlon_to_unit(edge_lats, np.full_like(edge_lats, region.lon_min_deg)),
            fast.latlon_to_unit(edge_lats, np.full_like(edge_lats, region.lon_max_deg)),
        ]
    )
    points = fast.deduplicate_unit_vectors(
        np.vstack([base_points, *boundary_points]),
        coordinate_tol=1e-10,
    )

    repeated_points = np.tile(points, (len(times), 1))
    repeated_times = np.repeat(times, len(points))
    return ActiveConstraintSet(repeated_points, repeated_times)


def optimize_continuous_params(
    structure: WalkerStructure,
    initial_params: q2.ConstellationParams,
    active_set: ActiveConstraintSet,
    *,
    q: int = 1,
    config: q2.CoverageConfig | None = None,
    inclination_min_deg: float,
    inclination_max_deg: float = 90.0,
    max_evaluations: int = 120,
) -> ContinuousOptimizationResult:
    """Maximize minimum active-set margin with a derivative-free optimizer."""

    cfg = config or q2.CoverageConfig()
    evaluations = 0
    best_params = initial_params
    best_margin = evaluate_active_constraints(
        initial_params,
        active_set.ground_points,
        active_set.times_s,
        q=q,
        config=cfg,
    )

    if minimize is None:
        return ContinuousOptimizationResult(
            params=best_params,
            active_margin=best_margin,
            objective_evaluations=1,
            success=False,
            message="SciPy is unavailable; returned the initial candidate",
        )

    def objective(vector: np.ndarray) -> float:
        nonlocal evaluations, best_params, best_margin
        evaluations += 1
        params = wrap_continuous_params(
            structure,
            vector[0],
            vector[1],
            vector[2],
            inclination_min_deg=inclination_min_deg,
            inclination_max_deg=inclination_max_deg,
        )
        result = evaluate_active_constraints(
            params,
            active_set.ground_points,
            active_set.times_s,
            q=q,
            config=cfg,
        )
        if result.min_margin > best_margin.min_margin:
            best_params = params
            best_margin = result
        return -result.min_margin

    x0 = np.array(
        [
            initial_params.inclination_deg,
            initial_params.raan0_deg,
            initial_params.u0_deg,
        ],
        dtype=float,
    )
    result = minimize(
        objective,
        x0,
        method="Powell",
        options={
            "maxfev": max_evaluations,
            "xtol": 1e-4,
            "ftol": 1e-8,
            "disp": False,
        },
    )
    return ContinuousOptimizationResult(
        params=best_params,
        active_margin=best_margin,
        objective_evaluations=evaluations,
        success=bool(result.success),
        message=str(result.message),
    )


def counterexample_guided_optimize(
    structure: WalkerStructure,
    initial_params: q2.ConstellationParams,
    active_set: ActiveConstraintSet,
    separation_times_s: np.ndarray,
    *,
    q: int = 1,
    config: q2.CoverageConfig | None = None,
    region: fast.LatLonRegion | None = None,
    inclination_min_deg: float,
    inclination_max_deg: float = 90.0,
    max_rounds: int = 5,
    local_max_evaluations: int = 120,
    margin_tolerance: float = 1e-6,
    include_representatives: bool = True,
) -> CounterexampleSearchResult:
    """Alternate active-set optimization and critical-point separation."""

    cfg = config or q2.CoverageConfig()
    target_region = region or fast.LatLonRegion()
    params = initial_params
    history: list[dict] = []
    separation: KDTreeCoverageResult | None = None

    for round_index in range(1, max_rounds + 1):
        optimized = optimize_continuous_params(
            structure,
            params,
            active_set,
            q=q,
            config=cfg,
            inclination_min_deg=inclination_min_deg,
            inclination_max_deg=inclination_max_deg,
            max_evaluations=local_max_evaluations,
        )
        params = optimized.params
        separation = evaluate_constellation_kdtree(
            params,
            separation_times_s,
            config=cfg,
            region=target_region,
            q=q,
            include_representatives=include_representatives,
        )
        history.append(
            {
                "round": round_index,
                "active_min_margin": optimized.active_margin.min_margin,
                "separation_min_margin": separation.min_margin,
                "separation_c_min": separation.c_min,
                "active_constraints": len(active_set.times_s),
                "objective_evaluations": optimized.objective_evaluations,
            }
        )

        if separation.min_margin >= -margin_tolerance:
            return CounterexampleSearchResult(
                params=params,
                active_set=active_set,
                separation_result=separation,
                rounds=round_index,
                converged=True,
                history=tuple(history),
            )

        if separation.worst_point is None or separation.worst_time_index < 0:
            break
        worst_time = float(separation.times_s[separation.worst_time_index])
        added = active_set.add(separation.worst_point, worst_time)
        if not added:
            break

    if separation is None:  # Defensive; max_rounds is validated by caller usage.
        separation = evaluate_constellation_kdtree(
            params,
            separation_times_s,
            config=cfg,
            region=target_region,
            q=q,
            include_representatives=include_representatives,
        )
    return CounterexampleSearchResult(
        params=params,
        active_set=active_set,
        separation_result=separation,
        rounds=len(history),
        converged=False,
        history=tuple(history),
    )
