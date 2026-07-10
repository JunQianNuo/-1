"""Conjunction-plane collision-probability calculations."""

from __future__ import annotations

import math

import numpy as np


def time_to_cpa(relative_position_km: np.ndarray, relative_velocity_km_s: np.ndarray) -> float:
    """Time of closest approach for linear relative motion."""

    rho = np.asarray(relative_position_km, dtype=float)
    vel = np.asarray(relative_velocity_km_s, dtype=float)
    denom = float(np.dot(vel, vel))
    if denom <= 0.0:
        raise ValueError("relative velocity norm must be positive")
    return float(-np.dot(rho, vel) / denom)


def cpa_miss_vector(relative_position_km: np.ndarray, relative_velocity_km_s: np.ndarray) -> np.ndarray:
    """Return the relative miss vector at closest approach."""

    t_cpa = time_to_cpa(relative_position_km, relative_velocity_km_s)
    return np.asarray(relative_position_km, dtype=float) + np.asarray(relative_velocity_km_s, dtype=float) * t_cpa


def collision_probability_2d_gaussian(
    miss_vector_km: np.ndarray,
    covariance_km2: np.ndarray,
    hard_body_radius_km: float,
    *,
    radial_steps: int = 160,
    angular_steps: int = 160,
) -> float:
    """Integrate a 2-D Gaussian over a circular hard-body region.

    This deterministic polar quadrature is intended for transparent contest
    implementation and is verified against the centered isotropic analytic case.
    """

    if hard_body_radius_km <= 0.0:
        return 0.0
    if radial_steps <= 0 or angular_steps <= 0:
        raise ValueError("radial_steps and angular_steps must be positive")

    mu = np.asarray(miss_vector_km, dtype=float).reshape(2)
    cov = np.asarray(covariance_km2, dtype=float).reshape(2, 2)
    det = float(np.linalg.det(cov))
    if det <= 0.0:
        raise ValueError("covariance_km2 must be positive definite")
    inv = np.linalg.inv(cov)

    r = (np.arange(radial_steps, dtype=float) + 0.5) * hard_body_radius_km / radial_steps
    theta = (np.arange(angular_steps, dtype=float) + 0.5) * (2.0 * math.pi / angular_steps)
    x = r[:, None] * np.cos(theta)[None, :]
    y = r[:, None] * np.sin(theta)[None, :]
    dx = x - mu[0]
    dy = y - mu[1]
    exponent = -0.5 * (inv[0, 0] * dx**2 + 2.0 * inv[0, 1] * dx * dy + inv[1, 1] * dy**2)
    coeff = 1.0 / (2.0 * math.pi * math.sqrt(det))
    pdf = coeff * np.exp(exponent)
    dr = hard_body_radius_km / radial_steps
    dtheta = 2.0 * math.pi / angular_steps
    pc = float(np.sum(pdf * r[:, None]) * dr * dtheta)
    return min(1.0, max(0.0, pc))
