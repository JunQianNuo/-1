"""Ground access-set construction for Problem 3."""

from __future__ import annotations

import numpy as np


def access_sets_naive(
    satellite_ecef_km: np.ndarray,
    ground_points_ecef_km: np.ndarray,
    coverage_angle_rad: float,
) -> list[list[int]]:
    """Return visible satellite IDs for each ground point by angular threshold."""

    sat_unit = _normalize(np.asarray(satellite_ecef_km, dtype=float))
    grd_unit = _normalize(np.asarray(ground_points_ecef_km, dtype=float))
    cos_theta = float(np.cos(coverage_angle_rad))
    dots = grd_unit @ sat_unit.T
    return [np.flatnonzero(row >= cos_theta - 1e-12).astype(int).tolist() for row in dots]


def access_summary(access_sets: list[list[int]]) -> dict[str, float | int]:
    counts = np.asarray([len(items) for items in access_sets], dtype=int)
    if counts.size == 0:
        return {"ground_point_count": 0, "min_access": 0, "max_access": 0, "mean_access": 0.0, "empty_count": 0}
    return {
        "ground_point_count": int(counts.size),
        "min_access": int(counts.min()),
        "max_access": int(counts.max()),
        "mean_access": float(counts.mean()),
        "empty_count": int(np.count_nonzero(counts == 0)),
    }


def _normalize(vectors: np.ndarray) -> np.ndarray:
    if vectors.ndim != 2 or vectors.shape[1] != 3:
        raise ValueError("vectors must have shape (N, 3)")
    norms = np.linalg.norm(vectors, axis=1)
    if np.any(norms == 0):
        raise ValueError("zero vector cannot be normalized")
    return vectors / norms[:, None]
