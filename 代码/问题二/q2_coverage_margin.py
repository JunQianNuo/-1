"""Continuous q-fold coverage margins for Problem 2.

A positive margin means the q-th nearest satellite is inside the coverage
boundary; a negative margin measures how far the constraint is from feasibility
in dot-product space.  This gives optimizers more information than an integer
minimum coverage count alone.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

import q2_constellation as q2


@dataclass(frozen=True)
class PointMarginResult:
    counts: np.ndarray
    margins: np.ndarray
    q: int
    worst_point_index: int

    @property
    def min_count(self) -> int:
        return int(np.min(self.counts)) if len(self.counts) else 0

    @property
    def min_margin(self) -> float:
        return float(np.min(self.margins)) if len(self.margins) else -math.inf


@dataclass(frozen=True)
class ActiveSetMarginResult:
    margins: np.ndarray
    counts: np.ndarray
    min_margin: float
    min_count: int
    worst_constraint_index: int
    q: int


def _validate_q(q: int, satellite_count: int) -> None:
    if q <= 0:
        raise ValueError("q must be positive")
    if q > satellite_count:
        raise ValueError("q cannot exceed the number of satellites")


def q_fold_margins_at_points(
    satellite_vectors: np.ndarray,
    ground_points: np.ndarray,
    coverage_radius_rad: float,
    *,
    q: int = 1,
    block_size: int = 4096,
    atol: float = 1e-12,
) -> PointMarginResult:
    """Compute exact counts and q-fold margins by blocked dense products."""

    satellites = np.asarray(satellite_vectors, dtype=float)
    points = np.asarray(ground_points, dtype=float)
    if satellites.ndim != 2 or satellites.shape[1] != 3:
        raise ValueError("satellite_vectors must have shape (S,3)")
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("ground_points must have shape (Q,3)")
    if block_size <= 0:
        raise ValueError("block_size must be positive")

    satellites = satellites / np.linalg.norm(satellites, axis=1, keepdims=True)
    points = points / np.linalg.norm(points, axis=1, keepdims=True)
    _validate_q(q, len(satellites))

    threshold = math.cos(coverage_radius_rad)
    counts = np.empty(len(points), dtype=np.int32)
    margins = np.empty(len(points), dtype=float)
    kth_index = len(satellites) - q

    for start in range(0, len(points), block_size):
        end = min(start + block_size, len(points))
        dots = points[start:end] @ satellites.T
        counts[start:end] = np.count_nonzero(dots >= threshold - atol, axis=1)
        qth = np.partition(dots, kth_index, axis=1)[:, kth_index]
        margins[start:end] = qth - threshold

    worst = int(np.argmin(margins)) if len(margins) else -1
    return PointMarginResult(counts=counts, margins=margins, q=q, worst_point_index=worst)


def evaluate_active_constraints(
    params: q2.ConstellationParams,
    ground_points: np.ndarray,
    constraint_times_s: np.ndarray,
    *,
    q: int = 1,
    config: q2.CoverageConfig | None = None,
) -> ActiveSetMarginResult:
    """Evaluate one ground point at one associated time for each constraint."""

    points = np.asarray(ground_points, dtype=float)
    times = np.asarray(constraint_times_s, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("ground_points must have shape (A,3)")
    if times.ndim != 1 or len(times) != len(points):
        raise ValueError("constraint_times_s must have one value per point")
    if len(points) == 0:
        raise ValueError("active constraint set must not be empty")

    cfg = config or q2.CoverageConfig()
    unique_times, inverse = np.unique(times, return_inverse=True)
    snapshots = q2.satellite_unit_vectors(params, unique_times, cfg)

    counts = np.empty(len(points), dtype=np.int32)
    margins = np.empty(len(points), dtype=float)
    for time_index in range(len(unique_times)):
        mask = inverse == time_index
        result = q_fold_margins_at_points(
            snapshots[:, time_index, :],
            points[mask],
            cfg.coverage_angle_rad,
            q=q,
        )
        counts[mask] = result.counts
        margins[mask] = result.margins

    worst = int(np.argmin(margins))
    return ActiveSetMarginResult(
        margins=margins,
        counts=counts,
        min_margin=float(margins[worst]),
        min_count=int(np.min(counts)),
        worst_constraint_index=worst,
        q=q,
    )
