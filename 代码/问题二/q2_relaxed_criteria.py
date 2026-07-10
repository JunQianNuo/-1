"""Q2-R03 / R04 / R06: relaxed coverage-criteria overlay for Problem 2.

These are *decision-layer* relaxations applied on top of an existing
``EvaluationResult`` (grid-time coverage counts); they do not change the
coverage model, only how feasibility is judged.  See
18-问题二算法条件松弛与假设驱动加速方案.md §4, §6.

- R03 near-full single coverage: feasible if C1 >= 1 - eps0  OR  max_gap <= tau.
- R04 guard-band region D_delta: the hard single-coverage constraint is applied
  on interior points at least ``delta`` from the boundary; the boundary is
  monitored, not used to reject.
- R06 per-instant spatial tolerance for double coverage: a time slice counts as
  "double covered" if a fraction >= 1 - eta of the area is 2-covered, and the
  target is that >= 95% of time slices qualify.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from q2_fast_coverage import LatLonRegion


@dataclass(frozen=True)
class RelaxedCriteriaConfig:
    eps0: float = 1e-3          # R03: C1 >= 1 - eps0
    tau_tol_s: float = 60.0     # R03: OR max_gap <= tau_tol_s
    guard_delta_deg: float = 1.0  # R04: inset for the interior hard constraint
    double_eta: float = 1e-2    # R06: per-instant spatial outage tolerance
    double_time_target: float = 0.95


@dataclass(frozen=True)
class RelaxedReport:
    total_satellites: int
    c1: float
    max_gap_s: float
    c_min_full: int
    c_min_interior: int
    boundary_c_min: int
    single_strict_feasible: bool
    single_relaxed_feasible: bool   # R03
    single_guard_feasible: bool     # R04
    c2_strict_time_rate: float      # eta = 0 (whole region)
    c2_relaxed_time_rate: float     # R06 eta
    c2_area: float
    double_relaxed_feasible: bool


def interior_mask(lat_deg, lon_deg, region: LatLonRegion, delta_deg: float) -> np.ndarray:
    """Boolean mask of points at least ``delta_deg`` inside the rectangle."""
    lat = np.asarray(lat_deg, dtype=float)
    lon = np.asarray(lon_deg, dtype=float)
    return (
        (lat >= region.lat_min_deg + delta_deg)
        & (lat <= region.lat_max_deg - delta_deg)
        & (lon >= region.lon_min_deg + delta_deg)
        & (lon <= region.lon_max_deg - delta_deg)
    )


def relaxed_double_time_rate(counts, weights, *, q: int = 2, eta: float = 1e-2) -> float:
    """Fraction of time slices where >= (1-eta) of the area is q-covered (R06)."""
    c = np.asarray(counts)
    w = np.asarray(weights, dtype=float)
    if c.ndim != 2 or w.shape != (c.shape[0],):
        raise ValueError("counts must be (K,L) and weights (K,)")
    w = w / w.sum()
    area_frac_by_time = w @ (c >= q)          # (L,)
    return float(np.mean(area_frac_by_time >= 1.0 - eta))


def evaluate_relaxed(
    result,
    *,
    region: LatLonRegion | None = None,
    config: RelaxedCriteriaConfig | None = None,
) -> RelaxedReport:
    """Compute the R03/R04/R06 relaxed feasibility overlay for one evaluation."""

    cfg = config or RelaxedCriteriaConfig()
    region = region or LatLonRegion()
    counts = np.asarray(result.counts)
    lat = np.asarray(result.lat_deg, dtype=float)
    lon = np.asarray(result.lon_deg, dtype=float)
    weights = np.asarray(result.weights, dtype=float)

    c_min_full = int(counts.min())

    mask = interior_mask(lat, lon, region, cfg.guard_delta_deg)
    c_min_interior = int(counts[mask].min()) if mask.any() else c_min_full
    boundary = ~mask
    boundary_c_min = int(counts[boundary].min()) if boundary.any() else c_min_full

    single_strict = c_min_full >= 1
    single_relaxed = (result.coverage_rate_q1 >= 1.0 - cfg.eps0) or (
        result.max_gap_s <= cfg.tau_tol_s
    )
    single_guard = c_min_interior >= 1

    c2_strict = float(result.strict_double_time_rate)
    c2_relaxed = relaxed_double_time_rate(counts, weights, q=2, eta=cfg.double_eta)

    return RelaxedReport(
        total_satellites=int(counts.shape[0] and result.params.total_satellites),
        c1=float(result.coverage_rate_q1),
        max_gap_s=float(result.max_gap_s),
        c_min_full=c_min_full,
        c_min_interior=c_min_interior,
        boundary_c_min=boundary_c_min,
        single_strict_feasible=single_strict,
        single_relaxed_feasible=single_relaxed,
        single_guard_feasible=single_guard,
        c2_strict_time_rate=c2_strict,
        c2_relaxed_time_rate=c2_relaxed,
        c2_area=float(result.coverage_rate_q2),
        double_relaxed_feasible=c2_relaxed >= cfg.double_time_target,
    )
