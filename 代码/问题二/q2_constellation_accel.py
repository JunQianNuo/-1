"""Problem 2 LEO constellation coverage evaluator -- accelerated copy.

This file is intentionally a **copy** of ``q2_constellation.py`` for the
Problem 2 -> Problem 3 joint inverse search.  The original Problem 2 evaluator
is left untouched; experimental acceleration is isolated here.

This module implements the first runnable version of the model described in:

- 09-问题二假设与指标推导.md
- 10-问题二数值实现方案.md
- 11-问题二初步回答与建模表述.md

The implementation is intentionally small and explicit:

1. Walker-Delta style constellation parameterization.
2. ECI -> ECEF circular-orbit propagation.
3. Grid-time coverage count.
4. Coverage metrics and a scale-increasing search skeleton.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
import json
import math
import os
from pathlib import Path
from typing import Iterable

import numpy as np

# NOTE:
# ``numba`` is installed on the current machine, but importing it in this
# Windows/Obsidian session can hang for tens of seconds.  To keep this copied
# evaluator safe and runnable, the default path avoids importing numba at module
# import time.  The candidate-search acceleration is therefore implemented in
# ``run_q2_free_search_accel.py`` by parallelizing independent candidate
# evaluations, while this module preserves the reference NumPy geometry.
NUMBA_AVAILABLE = False
njit = None  # type: ignore[assignment]
prange = range  # type: ignore[assignment]


_COVERAGE_BACKEND = os.environ.get("Q2_ACCEL_BACKEND", "numpy").strip().lower()


def set_coverage_backend(name: str) -> None:
    """Set backend for this accelerated copy.

    Parameters
    ----------
    name:
        ``"numpy"`` for the reference evaluator, ``"numba"`` for the
        experimental parallel kernel, or ``"auto"`` to use numba when present.
    """

    normalized = name.strip().lower()
    if normalized not in {"numpy", "numba", "auto"}:
        raise ValueError("coverage backend must be one of: numpy, numba, auto")
    global _COVERAGE_BACKEND
    _COVERAGE_BACKEND = normalized


def _use_numba_backend() -> bool:
    return NUMBA_AVAILABLE and _COVERAGE_BACKEND in {"numba", "auto"}


def coverage_backend_name() -> str:
    """Return the active backend used by :func:`coverage_counts`.

    ``q2_constellation.py`` remains the reference NumPy implementation.  This
    copy defaults to a Numba-parallel evaluator when available, with a safe
    NumPy fallback that preserves bitwise model semantics up to floating-point
    roundoff.
    """

    if _use_numba_backend():
        return "numba-parallel"
    if _COVERAGE_BACKEND in {"numba", "auto"} and not NUMBA_AVAILABLE:
        return "numpy-fallback-numba-unavailable"
    return "numpy-reference"


@dataclass(frozen=True)
class CoverageConfig:
    """Physical constants and coverage口径."""

    earth_radius_km: float = 6371.0
    altitude_km: float = 550.0
    mu_km3_s2: float = 398600.4418
    earth_rotation_rad_s: float = 7.2921159e-5
    ground_coverage_radius_km: float = 506.0

    @property
    def semi_major_axis_km(self) -> float:
        return self.earth_radius_km + self.altitude_km

    @property
    def coverage_angle_rad(self) -> float:
        return self.ground_coverage_radius_km / self.earth_radius_km

    @property
    def mean_motion_rad_s(self) -> float:
        return math.sqrt(self.mu_km3_s2 / self.semi_major_axis_km**3)

    @property
    def orbital_period_s(self) -> float:
        return 2.0 * math.pi / self.mean_motion_rad_s


@dataclass(frozen=True)
class ConstellationParams:
    """Walker-Delta-like constellation parameters."""

    planes: int
    sats_per_plane: int
    phase_factor: int
    inclination_deg: float
    raan0_deg: float = 0.0
    u0_deg: float = 0.0

    @property
    def total_satellites(self) -> int:
        return self.planes * self.sats_per_plane

    def validate(self) -> None:
        if self.planes <= 0:
            raise ValueError("planes must be positive")
        if self.sats_per_plane <= 0:
            raise ValueError("sats_per_plane must be positive")
        if not (0 <= self.phase_factor < self.planes):
            raise ValueError("phase_factor must be in {0, ..., planes-1}")


@dataclass(frozen=True)
class CoverageMetrics:
    coverage_rate_q1: float
    coverage_rate_q2: float
    avg_multiplicity: float
    c_min: int
    max_gap_s: float
    strict_double_time_rate: float


@dataclass(frozen=True)
class EvaluationResult:
    params: ConstellationParams
    counts: np.ndarray
    lat_deg: np.ndarray
    lon_deg: np.ndarray
    times_s: np.ndarray
    weights: np.ndarray
    metrics: CoverageMetrics

    @property
    def coverage_rate_q1(self) -> float:
        return self.metrics.coverage_rate_q1

    @property
    def coverage_rate_q2(self) -> float:
        return self.metrics.coverage_rate_q2

    @property
    def avg_multiplicity(self) -> float:
        return self.metrics.avg_multiplicity

    @property
    def c_min(self) -> int:
        return self.metrics.c_min

    @property
    def max_gap_s(self) -> float:
        return self.metrics.max_gap_s

    @property
    def strict_double_time_rate(self) -> float:
        return self.metrics.strict_double_time_rate


@dataclass(frozen=True)
class SearchRunResult:
    """Result container for a constellation search run."""

    records: list[dict]
    best_result: EvaluationResult | None
    first_feasible: EvaluationResult | None
    evaluated_count: int


def deg2rad(values: np.ndarray | float) -> np.ndarray | float:
    return np.deg2rad(values)


def ground_unit_vectors(lat_deg: np.ndarray, lon_deg: np.ndarray) -> np.ndarray:
    """Return ECEF unit vectors for latitude/longitude arrays in degrees."""

    lat = np.deg2rad(np.asarray(lat_deg, dtype=float))
    lon = np.deg2rad(np.asarray(lon_deg, dtype=float))
    if lat.shape != lon.shape:
        raise ValueError("lat_deg and lon_deg must have the same shape")

    cos_lat = np.cos(lat)
    return np.column_stack(
        [
            cos_lat * np.cos(lon),
            cos_lat * np.sin(lon),
            np.sin(lat),
        ]
    )


def area_weights(lat_deg: np.ndarray) -> np.ndarray:
    """Cos(latitude) area weights normalized to sum to 1."""

    w = np.cos(np.deg2rad(np.asarray(lat_deg, dtype=float)))
    w = np.maximum(w, 0.0)
    total = float(w.sum())
    if total <= 0.0:
        raise ValueError("area weights sum to zero")
    return w / total


def make_latlon_grid(
    lat_min_deg: float = 4.0,
    lat_max_deg: float = 53.0,
    lon_min_deg: float = 73.0,
    lon_max_deg: float = 135.0,
    step_deg: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Create a regular latitude-longitude grid including endpoints."""

    if step_deg <= 0:
        raise ValueError("step_deg must be positive")
    if lat_max_deg < lat_min_deg or lon_max_deg < lon_min_deg:
        raise ValueError("max bounds must be greater than or equal to min bounds")

    lat_values = _axis_grid_with_endpoint(lat_min_deg, lat_max_deg, step_deg)
    lon_values = _axis_grid_with_endpoint(lon_min_deg, lon_max_deg, step_deg)
    lon_grid, lat_grid = np.meshgrid(lon_values, lat_values)
    return lat_grid.ravel(), lon_grid.ravel()


def _axis_grid_with_endpoint(start: float, stop: float, step: float) -> np.ndarray:
    values = np.arange(start, stop, step, dtype=float)
    if values.size == 0 or not math.isclose(float(values[-1]), stop, rel_tol=0.0, abs_tol=1e-10):
        values = np.append(values, float(stop))
    return values


def make_time_grid(duration_s: float = 86164.09, step_s: float = 180.0) -> np.ndarray:
    """Create a time grid including 0 and not exceeding duration_s."""

    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    if step_s <= 0:
        raise ValueError("step_s must be positive")
    return _axis_grid_with_endpoint(0.0, duration_s, step_s)


SIDEREAL_DAY_S: float = 86164.09


def symmetry_reduced_window_s(
    planes: int,
    config: CoverageConfig | None = None,
    *,
    sidereal_day_s: float = SIDEREAL_DAY_S,
) -> float:
    """Rotational-symmetry period ``max(T_orbit, T_sid/M)`` of the Walker SET.

    .. warning::
        Q2-R01 originally proposed this as a reduced fixed-region evaluation
        window.  Both a direct derivation and a numerical calibration (see
        18-...松弛与假设驱动加速方案.md §15.5) show this is **invalid for a
        fixed target region**: the Walker ``M``-fold symmetry maps plane ``m`` to
        ``m+1`` via a RAAN rotation ``2*pi/M`` *together with* an in-track shift
        ``2*pi*F/(MN)``.  Pure Earth rotation advances only the relative
        longitude (RAAN side), not the in-track phase, so
        ``coverage(D, phi+2*pi/M) != coverage(D, phi)`` for a fixed ``D``.
        Region coverage is therefore **not** ``2*pi/M``-periodic and a full
        sidereal day is still required.  This function is retained only as a
        constellation-set diagnostic; do not use it to shorten feasibility
        evaluation.  Use :func:`window_convergence_check` instead.
    """

    if planes <= 0:
        raise ValueError("planes must be positive")
    cfg = config or CoverageConfig()
    return max(cfg.orbital_period_s, sidereal_day_s / planes)


def window_convergence_check(
    params: ConstellationParams,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    *,
    base_window_s: float = SIDEREAL_DAY_S,
    step_s: float = 300.0,
    factor: float = 2.0,
    config: CoverageConfig | None = None,
) -> dict:
    """Compare coverage metrics on a base window and a ``factor``x window.

    This is the surviving Q2-R01 verification hook: instead of *assuming* a
    reduced window is safe, it measures whether extending the window from
    ``base_window_s`` to ``factor * base_window_s`` changes the key metrics.  A
    candidate window is only trustworthy when the returned discrepancies are
    below the caller's tolerance.
    """

    if factor <= 1.0:
        raise ValueError("factor must be > 1")
    cfg = config or CoverageConfig()
    base = evaluate_constellation(
        params, lat_deg, lon_deg, make_time_grid(base_window_s, step_s), cfg
    )
    extended = evaluate_constellation(
        params, lat_deg, lon_deg, make_time_grid(base_window_s * factor, step_s), cfg
    )
    return {
        "base_window_s": float(base_window_s),
        "extended_window_s": float(base_window_s * factor),
        "c1_base": base.coverage_rate_q1,
        "c1_extended": extended.coverage_rate_q1,
        "c1_abs_diff": abs(base.coverage_rate_q1 - extended.coverage_rate_q1),
        "cmin_base": base.c_min,
        "cmin_extended": extended.c_min,
        "cmin_consistent": base.c_min == extended.c_min,
        "max_gap_base_s": base.max_gap_s,
        "max_gap_extended_s": extended.max_gap_s,
    }


def satellite_unit_vectors(
    params: ConstellationParams,
    times_s: np.ndarray,
    config: CoverageConfig | None = None,
) -> np.ndarray:
    """Return satellite ECEF unit vectors with shape (S, L, 3).

    Accelerated-copy change:
    the original evaluator builds this tensor by looping over every
    ``(plane, satellite)`` pair in Python.  Here all static Walker phases and
    RAANs are precomputed as length-``S`` arrays and propagated against the
    time grid by NumPy broadcasting.  This keeps the mathematical model exactly
    the same while removing the most frequent Python-level loop in large
    upper-bound expansions.
    """

    params.validate()
    cfg = config or CoverageConfig()
    times = np.asarray(times_s, dtype=np.float64)
    inc = math.radians(params.inclination_deg)
    cos_i = math.cos(inc)
    sin_i = math.sin(inc)

    phase0, cos_o, sin_o = _precompute_walker_phase_arrays(params)
    earth_angle = cfg.earth_rotation_rad_s * times
    cos_e = np.cos(earth_angle)
    sin_e = np.sin(earth_angle)

    u = phase0[:, None] + cfg.mean_motion_rad_s * times[None, :]
    x_orb = np.cos(u)
    y_orb = np.sin(u)

    # R1(i)
    x_inc = x_orb
    y_inc = y_orb * cos_i
    z_inc = y_orb * sin_i

    # R3(raan), inertial
    x_i = cos_o[:, None] * x_inc - sin_o[:, None] * y_inc
    y_i = sin_o[:, None] * x_inc + cos_o[:, None] * y_inc
    z_i = z_inc

    # R3(-omega_e t), Earth-fixed
    x_e = cos_e[None, :] * x_i + sin_e[None, :] * y_i
    y_e = -sin_e[None, :] * x_i + cos_e[None, :] * y_i

    return np.stack([x_e, y_e, z_i], axis=2)


def _precompute_walker_phase_arrays(params: ConstellationParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Precompute per-satellite static RAAN and phase arrays for acceleration."""

    params.validate()
    total = params.total_satellites
    phase0 = np.empty(total, dtype=np.float64)
    cos_raan = np.empty(total, dtype=np.float64)
    sin_raan = np.empty(total, dtype=np.float64)

    raan0 = math.radians(params.raan0_deg)
    u0 = math.radians(params.u0_deg)
    idx = 0
    for m in range(params.planes):
        raan = raan0 + 2.0 * math.pi * m / params.planes
        co = math.cos(raan)
        so = math.sin(raan)
        for n in range(params.sats_per_plane):
            phase0[idx] = (
                u0
                + 2.0 * math.pi * n / params.sats_per_plane
                + 2.0 * math.pi * params.phase_factor * m / params.total_satellites
            )
            cos_raan[idx] = co
            sin_raan[idx] = so
            idx += 1
    return phase0, cos_raan, sin_raan


if NUMBA_AVAILABLE:

    @njit(parallel=True, fastmath=True, cache=True)
    def _coverage_counts_numba_kernel(
        phase0: np.ndarray,
        cos_raan: np.ndarray,
        sin_raan: np.ndarray,
        ground: np.ndarray,
        times: np.ndarray,
        cos_i: float,
        sin_i: float,
        mean_motion: float,
        earth_rotation: float,
        cos_theta: float,
    ) -> np.ndarray:
        """Numba-parallel coverage count kernel.

        The loop order computes each satellite position once per time step and
        updates all ground-point counts for that time.  This avoids the large
        ``S x K x L`` boolean tensor and removes Python-loop overhead.
        """

        sat_count = phase0.shape[0]
        ground_count = ground.shape[0]
        time_count = times.shape[0]
        counts = np.zeros((ground_count, time_count), dtype=np.int16)

        for t_idx in prange(time_count):
            t = times[t_idx]
            earth_angle = earth_rotation * t
            cos_e = math.cos(earth_angle)
            sin_e = math.sin(earth_angle)

            for s_idx in range(sat_count):
                u = phase0[s_idx] + mean_motion * t
                x_orb = math.cos(u)
                y_orb = math.sin(u)

                # R1(i)
                x_inc = x_orb
                y_inc = y_orb * cos_i
                z_inc = y_orb * sin_i

                # R3(raan), inertial
                x_i = cos_raan[s_idx] * x_inc - sin_raan[s_idx] * y_inc
                y_i = sin_raan[s_idx] * x_inc + cos_raan[s_idx] * y_inc
                z_i = z_inc

                # R3(-omega_e t), Earth-fixed
                x_e = cos_e * x_i + sin_e * y_i
                y_e = -sin_e * x_i + cos_e * y_i

                for k_idx in range(ground_count):
                    dot = (
                        x_e * ground[k_idx, 0]
                        + y_e * ground[k_idx, 1]
                        + z_i * ground[k_idx, 2]
                    )
                    if dot >= cos_theta:
                        counts[k_idx, t_idx] += 1

        return counts


def _coverage_counts_numba(
    params: ConstellationParams,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    config: CoverageConfig,
) -> np.ndarray:
    """Compute coverage counts using the isolated accelerated backend."""

    ground = np.ascontiguousarray(ground_unit_vectors(lat_deg, lon_deg), dtype=np.float64)
    times = np.ascontiguousarray(np.asarray(times_s, dtype=np.float64))
    phase0, cos_raan, sin_raan = _precompute_walker_phase_arrays(params)
    inc = math.radians(params.inclination_deg)
    return _coverage_counts_numba_kernel(
        np.ascontiguousarray(phase0),
        np.ascontiguousarray(cos_raan),
        np.ascontiguousarray(sin_raan),
        ground,
        times,
        math.cos(inc),
        math.sin(inc),
        config.mean_motion_rad_s,
        config.earth_rotation_rad_s,
        math.cos(config.coverage_angle_rad),
    )


def _coverage_counts_numpy_reference(
    params: ConstellationParams,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    config: CoverageConfig,
) -> np.ndarray:
    """Original NumPy batched implementation kept as fallback/reference."""

    ground = ground_unit_vectors(lat_deg, lon_deg)
    cos_theta = math.cos(config.coverage_angle_rad)
    sat_all = satellite_unit_vectors(params, times_s, config)

    _S, L, _3 = sat_all.shape
    K = ground.shape[0]
    counts = np.zeros((K, L), dtype=np.int16)

    # Batch over time to keep memory bounded
    batch_size = max(1, min(L, 10))
    for start in range(0, L, batch_size):
        end = min(start + batch_size, L)
        sat_batch = sat_all[:, start:end, :]  # (S, B, 3)
        # dots: (S, B, K) — dot each satellite/time with every ground point
        dots_batch = np.einsum("sbD,kD->sbk", sat_batch, ground)
        covered = dots_batch >= cos_theta
        counts[:, start:end] = covered.sum(axis=0).T.astype(np.int16)

    return counts


def coverage_counts(
    params: ConstellationParams,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    config: CoverageConfig | None = None,
) -> np.ndarray:
    """Compute coverage multiplicity for each ground point and time.

    Returns an integer array with shape (K, L).  Batched over time steps
    to avoid allocating a (S, K, L) intermediate for large constellations.
    """

    cfg = config or CoverageConfig()
    if _use_numba_backend():
        return _coverage_counts_numba(params, lat_deg, lon_deg, times_s, cfg)
    return _coverage_counts_numpy_reference(params, lat_deg, lon_deg, times_s, cfg)


def coverage_counts_numpy_reference(
    params: ConstellationParams,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    config: CoverageConfig | None = None,
) -> np.ndarray:
    """Public reference helper for tests/benchmarking in the accelerated copy."""

    return _coverage_counts_numpy_reference(
        params,
        lat_deg,
        lon_deg,
        times_s,
        config or CoverageConfig(),
    )


def longest_uncovered_gap_s(covered: np.ndarray, dt_s: float) -> float:
    """Longest consecutive False run multiplied by dt_s."""

    max_run = 0
    current = 0
    for ok in covered:
        if ok:
            max_run = max(max_run, current)
            current = 0
        else:
            current += 1
    max_run = max(max_run, current)
    return float(max_run * dt_s)


def compute_metrics(counts: np.ndarray, weights: np.ndarray, dt_s: float) -> CoverageMetrics:
    """Compute coverage metrics from a K x L coverage-count matrix."""

    c = np.asarray(counts)
    if c.ndim != 2:
        raise ValueError("counts must have shape (K, L)")
    if c.shape[1] == 0:
        raise ValueError("counts must have at least one time column")

    w = np.asarray(weights, dtype=float)
    if w.shape != (c.shape[0],):
        raise ValueError("weights must have shape (K,)")
    w = w / w.sum()

    q1_by_time = w @ (c >= 1)
    q2_by_time = w @ (c >= 2)
    avg_by_time = w @ c

    max_gap = 0.0
    for row in c:
        max_gap = max(max_gap, longest_uncovered_gap_s(row >= 1, dt_s))

    strict_double = np.mean(np.min(c, axis=0) >= 2)

    return CoverageMetrics(
        coverage_rate_q1=float(np.mean(q1_by_time)),
        coverage_rate_q2=float(np.mean(q2_by_time)),
        avg_multiplicity=float(np.mean(avg_by_time)),
        c_min=int(np.min(c)),
        max_gap_s=float(max_gap),
        strict_double_time_rate=float(strict_double),
    )


def evaluate_constellation(
    params: ConstellationParams,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    config: CoverageConfig | None = None,
) -> EvaluationResult:
    """Evaluate one constellation on a target grid and time grid."""

    cfg = config or CoverageConfig()
    lat = np.asarray(lat_deg, dtype=float)
    lon = np.asarray(lon_deg, dtype=float)
    times = np.asarray(times_s, dtype=float)
    counts = coverage_counts(params, lat, lon, times, cfg)
    weights = area_weights(lat)

    if len(times) >= 2:
        dt_s = float(np.median(np.diff(times)))
    else:
        dt_s = 0.0
    metrics = compute_metrics(counts, weights=weights, dt_s=dt_s)
    return EvaluationResult(
        params=params,
        counts=counts,
        lat_deg=lat,
        lon_deg=lon,
        times_s=times,
        weights=weights,
        metrics=metrics,
    )


def factor_pairs(total: int) -> list[tuple[int, int]]:
    """All ordered positive factor pairs (M, N) with M*N=total."""

    if total <= 0:
        raise ValueError("total must be positive")
    pairs: list[tuple[int, int]] = []
    for m in range(1, total + 1):
        if total % m == 0:
            pairs.append((m, total // m))
    return pairs


def phase_grid(
    planes: int,
    sats_per_plane: int,
    phase_resolution_deg: float,
    *,
    fix_raan0: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Search Ω0 and u0 in symmetry fundamental intervals.

    Relaxation Q2-R02 (see 18-问题二算法条件松弛与假设驱动加速方案.md):
    over an integer/period-complete evaluation window the pair ``(Ω0, u0)``
    collapses to a single effective phase

        ``ũ0 = u0 + (n0 / ω_e) · Ω0  (mod 2π)``,

    because a shift ``δ`` in ``Ω0`` combined with a shift ``-(n0/ω_e)·δ`` in
    the in-track phase is exactly equivalent to a time shift ``δ/ω_e`` of the
    whole Earth-fixed constellation (the ``R3(-ω_e t)`` and ``R3(δ)`` rotations
    commute).  Time-aggregated metrics are therefore invariant, so scanning the
    two-dimensional phase grid is redundant.  With ``fix_raan0=True`` we fix
    ``Ω0=0`` and search only ``u0``, removing one continuous dimension exactly.
    """

    if planes <= 0 or sats_per_plane <= 0:
        raise ValueError("planes and sats_per_plane must be positive")
    if phase_resolution_deg <= 0:
        raise ValueError("phase_resolution_deg must be positive")

    omega_width = 360.0 / planes
    u_width = 360.0 / sats_per_plane
    k_u = max(4, math.ceil(u_width / phase_resolution_deg))
    u_values = np.linspace(0.0, u_width, k_u, endpoint=False)

    if fix_raan0:
        # Q2-R02: single representative RAAN offset; ũ0 is swept by u0 alone.
        omega_values = np.array([0.0])
    else:
        k_omega = max(4, math.ceil(omega_width / phase_resolution_deg))
        omega_values = np.linspace(0.0, omega_width, k_omega, endpoint=False)

    return omega_values, u_values


def candidate_params_for_total(
    total_satellites: int,
    inclinations_deg: Iterable[float],
    phase_resolution_deg: float = 2.0,
    max_candidates: int | None = None,
    *,
    fix_raan0: bool = False,
) -> Iterable[ConstellationParams]:
    """Yield Walker-Delta candidates for a fixed total satellite count.

    ``fix_raan0`` enables relaxation Q2-R02 (fix Ω0=0, search only u0).
    """

    yielded = 0
    for planes, sats_per_plane in factor_pairs(total_satellites):
        omega_values, u_values = phase_grid(
            planes, sats_per_plane, phase_resolution_deg, fix_raan0=fix_raan0
        )
        for phase_factor, inc, raan0, u0 in product(
            range(planes), inclinations_deg, omega_values, u_values
        ):
            yield ConstellationParams(
                planes=planes,
                sats_per_plane=sats_per_plane,
                phase_factor=phase_factor,
                inclination_deg=float(inc),
                raan0_deg=float(raan0),
                u0_deg=float(u0),
            )
            yielded += 1
            if max_candidates is not None and yielded >= max_candidates:
                return


def find_first_feasible_single_coverage(
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    start_total: int = 40,
    stop_total: int = 42,
    inclinations_deg: Iterable[float] = (49.0, 50.0, 51.0, 52.0, 53.0),
    phase_resolution_deg: float = 2.0,
    max_candidates_per_total: int | None = None,
    config: CoverageConfig | None = None,
) -> EvaluationResult | None:
    """Scale-increasing single-coverage feasibility search skeleton."""

    cfg = config or CoverageConfig()
    for total in range(start_total, stop_total + 1):
        for params in candidate_params_for_total(
            total,
            inclinations_deg=inclinations_deg,
            phase_resolution_deg=phase_resolution_deg,
            max_candidates=max_candidates_per_total,
        ):
            result = evaluate_constellation(params, lat_deg, lon_deg, times_s, cfg)
            if result.c_min >= 1:
                return result
    return None


def evaluation_record(result: EvaluationResult) -> dict:
    """Flatten one evaluation into a CSV-friendly record."""

    params = result.params
    return {
        "planes": params.planes,
        "sats_per_plane": params.sats_per_plane,
        "total_satellites": params.total_satellites,
        "phase_factor": params.phase_factor,
        "inclination_deg": params.inclination_deg,
        "raan0_deg": params.raan0_deg,
        "u0_deg": params.u0_deg,
        "C1": result.coverage_rate_q1,
        "C2": result.coverage_rate_q2,
        "avg_multiplicity": result.avg_multiplicity,
        "c_min": result.c_min,
        "max_gap_s": result.max_gap_s,
        "strict_double_time_rate": result.strict_double_time_rate,
    }


def _single_coverage_score(result: EvaluationResult) -> tuple:
    """Ordering key for single-coverage searches.

    Feasible candidates (c_min >= 1) are ranked above infeasible ones.
    Within the same feasibility class, prefer larger minimum multiplicity,
    larger weighted single-coverage rate, larger mean multiplicity, and shorter
    uncovered gaps.
    """

    feasible_flag = 1 if result.c_min >= 1 else 0
    return (
        feasible_flag,
        result.c_min,
        result.coverage_rate_q1,
        result.avg_multiplicity,
        -result.max_gap_s,
    )


def search_single_coverage(
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    start_total: int = 40,
    stop_total: int = 42,
    inclinations_deg: Iterable[float] = (49.0, 50.0, 51.0, 52.0, 53.0),
    phase_resolution_deg: float = 2.0,
    max_candidates_per_total: int | None = None,
    stop_on_feasible: bool = True,
    config: CoverageConfig | None = None,
) -> SearchRunResult:
    """Run a scale-increasing single-coverage search and keep all records."""

    if start_total <= 0:
        raise ValueError("start_total must be positive")
    if stop_total < start_total:
        raise ValueError("stop_total must be greater than or equal to start_total")

    cfg = config or CoverageConfig()
    records: list[dict] = []
    best_result: EvaluationResult | None = None
    best_score: tuple | None = None
    first_feasible: EvaluationResult | None = None
    evaluated_count = 0

    for total in range(start_total, stop_total + 1):
        for params in candidate_params_for_total(
            total,
            inclinations_deg=inclinations_deg,
            phase_resolution_deg=phase_resolution_deg,
            max_candidates=max_candidates_per_total,
        ):
            result = evaluate_constellation(params, lat_deg, lon_deg, times_s, cfg)
            evaluated_count += 1
            records.append(evaluation_record(result))

            score = _single_coverage_score(result)
            if best_score is None or score > best_score:
                best_score = score
                best_result = result

            if result.c_min >= 1 and first_feasible is None:
                first_feasible = result
                if stop_on_feasible:
                    return SearchRunResult(
                        records=records,
                        best_result=best_result,
                        first_feasible=first_feasible,
                        evaluated_count=evaluated_count,
                    )

    return SearchRunResult(
        records=records,
        best_result=best_result,
        first_feasible=first_feasible,
        evaluated_count=evaluated_count,
    )


def _double_coverage_score(result: EvaluationResult) -> tuple:
    """Ordering key for double-coverage searches.

    Feasible candidates (strict_double_time_rate >= 0.95) are ranked above
    infeasible ones.  Within the same feasibility class, prefer larger strict
    double-time rate, larger average multiplicity, and smaller total satellites.
    """

    feasible = 1 if result.strict_double_time_rate >= 0.95 else 0
    return (
        feasible,
        result.strict_double_time_rate,
        result.avg_multiplicity,
        result.coverage_rate_q2,
        -result.params.total_satellites,
    )


def search_double_coverage(
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
    start_total: int = 80,
    stop_total: int = 85,
    inclinations_deg: Iterable[float] = (49.0, 50.0, 51.0, 52.0, 53.0),
    phase_resolution_deg: float = 10.0,
    max_candidates_per_total: int | None = None,
    stop_on_feasible: bool = True,
    config: CoverageConfig | None = None,
) -> SearchRunResult:
    """Scale-increasing search for strict double-coverage (C2_strict >= 0.95).

    This mirrors ``search_single_coverage`` but uses ``strict_double_time_rate``
    as the feasibility criterion.  The start_total should typically be at least
    the single-coverage feasible size (or the area lower bound of 80).
    """

    if start_total <= 0:
        raise ValueError("start_total must be positive")
    if stop_total < start_total:
        raise ValueError("stop_total must be greater than or equal to start_total")

    cfg = config or CoverageConfig()
    records: list[dict] = []
    best_result: EvaluationResult | None = None
    best_score: tuple | None = None
    first_feasible: EvaluationResult | None = None
    evaluated_count = 0

    for total in range(start_total, stop_total + 1):
        for params in candidate_params_for_total(
            total,
            inclinations_deg=inclinations_deg,
            phase_resolution_deg=phase_resolution_deg,
            max_candidates=max_candidates_per_total,
        ):
            result = evaluate_constellation(params, lat_deg, lon_deg, times_s, cfg)
            evaluated_count += 1
            records.append(evaluation_record(result))

            score = _double_coverage_score(result)
            if best_score is None or score > best_score:
                best_score = score
                best_result = result

            if result.strict_double_time_rate >= 0.95 and first_feasible is None:
                first_feasible = result
                if stop_on_feasible:
                    return SearchRunResult(
                        records=records,
                        best_result=best_result,
                        first_feasible=first_feasible,
                        evaluated_count=evaluated_count,
                    )

    return SearchRunResult(
        records=records,
        best_result=best_result,
        first_feasible=first_feasible,
        evaluated_count=evaluated_count,
    )


def result_summary_dict(result: EvaluationResult) -> dict:
    params = asdict(result.params)
    params["total_satellites"] = result.params.total_satellites
    return {
        "params": params,
        "metrics": asdict(result.metrics),
        "num_grid_points": int(result.counts.shape[0]),
        "num_time_steps": int(result.counts.shape[1]),
    }


def save_result_summary(result: EvaluationResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result_summary_dict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
