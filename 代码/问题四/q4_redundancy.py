"""Redundancy confidence and coverage-availability helpers."""

from __future__ import annotations

import math

import numpy as np


def cold_standby_confidence(active_units: float, spare_units: int, unit_reliability: float) -> float:
    """Poisson cold-standby confidence from Liu et al. style formula."""

    if active_units < 0 or spare_units < 0:
        raise ValueError("active_units and spare_units must be non-negative")
    if not 0.0 <= unit_reliability <= 1.0:
        raise ValueError("unit_reliability must be in [0, 1]")
    if unit_reliability == 1.0:
        return 1.0
    if unit_reliability == 0.0:
        return 0.0
    mean_failures = -active_units * math.log(unit_reliability)
    series = sum(mean_failures**k / math.factorial(k) for k in range(spare_units + 1))
    return float(unit_reliability**active_units * series)


def ground_backup_confidence(active_satellites: int, ground_spares: int, unit_reliability: float) -> float:
    return cold_standby_confidence(active_satellites, ground_spares, unit_reliability)


def space_backup_confidence(active_satellites: int, planes: int, space_spares: int, unit_reliability: float) -> float:
    """Per-plane space-backup confidence with evenly distributed spares."""

    if planes <= 0:
        raise ValueError("planes must be positive")
    if active_satellites < 0 or space_spares < 0:
        raise ValueError("satellite counts must be non-negative")
    active_per_plane = active_satellites / planes
    base = space_spares // planes
    remainder = space_spares % planes
    confidence = 1.0
    for plane in range(planes):
        spares = base + (1 if plane < remainder else 0)
        confidence *= cold_standby_confidence(active_per_plane, spares, unit_reliability)
    return float(confidence)


def coverage_availability(coverage_counts: np.ndarray, min_coverage: int = 1) -> float:
    """Fraction of time steps whose every grid point meets min coverage."""

    counts = np.asarray(coverage_counts)
    if counts.ndim != 2:
        raise ValueError("coverage_counts must have shape (time, grid)")
    if counts.shape[0] == 0:
        raise ValueError("coverage_counts must contain at least one time step")
    ok = np.all(counts >= min_coverage, axis=1)
    return float(np.mean(ok))


def satellite_criticality(coverage_matrix: np.ndarray, min_coverage: int = 1) -> np.ndarray:
    """Fraction of time each satellite's removal creates any coverage hole.

    coverage_matrix shape is (time, grid, satellite), with boolean visibility.
    """

    coverage = np.asarray(coverage_matrix, dtype=bool)
    if coverage.ndim != 3:
        raise ValueError("coverage_matrix must have shape (time, grid, satellite)")
    counts = coverage.sum(axis=2)
    critical = []
    for sat in range(coverage.shape[2]):
        after_removal = counts - coverage[:, :, sat].astype(int)
        hole = np.any(after_removal < min_coverage, axis=1)
        critical.append(float(np.mean(hole)))
    return np.asarray(critical, dtype=float)


def expected_hole_time_s(
    failure_rates_per_s: np.ndarray,
    criticality: np.ndarray,
    recovery_time_s: float,
    horizon_s: float,
) -> float:
    rates = np.asarray(failure_rates_per_s, dtype=float)
    crit = np.asarray(criticality, dtype=float)
    if rates.shape != crit.shape:
        raise ValueError("failure_rates_per_s and criticality must have the same shape")
    if recovery_time_s < 0 or horizon_s < 0:
        raise ValueError("times must be non-negative")
    return float(np.sum(rates * horizon_s * crit * recovery_time_s))
