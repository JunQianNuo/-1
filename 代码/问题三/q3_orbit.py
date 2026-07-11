"""Orbit propagation and geometric grid utilities for Problem 3."""

from __future__ import annotations

import math

import numpy as np

from q3_config import ConstellationParams, Q3Config


def make_time_grid(duration_s: float, step_s: float) -> np.ndarray:
    """Return a nondecreasing time grid including 0 and the final duration."""

    if duration_s < 0:
        raise ValueError("duration_s must be non-negative")
    if step_s <= 0:
        raise ValueError("step_s must be positive")
    if duration_s == 0:
        return np.array([0.0])
    values = list(np.arange(0.0, duration_s, step_s, dtype=float))
    if not values or not math.isclose(values[-1], duration_s, rel_tol=0.0, abs_tol=1e-12):
        values.append(float(duration_s))
    return np.asarray(values, dtype=float)


def make_latlon_grid(
    lat_min_deg: float,
    lat_max_deg: float,
    lon_min_deg: float,
    lon_max_deg: float,
    step_deg: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Create a regular latitude-longitude grid including region endpoints."""

    if step_deg <= 0:
        raise ValueError("step_deg must be positive")
    if lat_max_deg < lat_min_deg or lon_max_deg < lon_min_deg:
        raise ValueError("max bounds must be no smaller than min bounds")
    lat = _axis_with_endpoint(lat_min_deg, lat_max_deg, step_deg)
    lon = _axis_with_endpoint(lon_min_deg, lon_max_deg, step_deg)
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    return lat_grid.ravel(), lon_grid.ravel()


def _axis_with_endpoint(start: float, stop: float, step: float) -> np.ndarray:
    values = list(np.arange(start, stop, step, dtype=float))
    if not values or not math.isclose(values[-1], stop, rel_tol=0.0, abs_tol=1e-12):
        values.append(float(stop))
    return np.asarray(values, dtype=float)


def ground_ecef(lat_deg: np.ndarray, lon_deg: np.ndarray, *, radius_km: float) -> np.ndarray:
    """Convert latitude/longitude arrays to ECEF position vectors."""

    lat = np.deg2rad(np.asarray(lat_deg, dtype=float))
    lon = np.deg2rad(np.asarray(lon_deg, dtype=float))
    if lat.shape != lon.shape:
        raise ValueError("lat_deg and lon_deg must have the same shape")
    cos_lat = np.cos(lat)
    return radius_km * np.column_stack(
        [cos_lat * np.cos(lon), cos_lat * np.sin(lon), np.sin(lat)]
    )


def satellite_positions(
    params: ConstellationParams,
    t_s: float,
    config: Q3Config | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ECI and ECEF satellite positions at one time instant.

    Satellites are indexed as ``sat_id = m * sats_per_plane + n``.
    """

    params.validate()
    cfg = config or Q3Config()
    radius = cfg.semi_major_axis_km
    inc = math.radians(params.inclination_deg)
    raan0 = math.radians(params.raan0_deg)
    u0 = math.radians(params.u0_deg)

    cos_i = math.cos(inc)
    sin_i = math.sin(inc)
    earth_angle = cfg.earth_rotation_rad_s * float(t_s)
    cos_e = math.cos(earth_angle)
    sin_e = math.sin(earth_angle)

    eci: list[list[float]] = []
    ecef: list[list[float]] = []
    for m in range(params.planes):
        raan = raan0 + 2.0 * math.pi * m / params.planes
        cos_o = math.cos(raan)
        sin_o = math.sin(raan)
        for n in range(params.sats_per_plane):
            phase = (
                u0
                + 2.0 * math.pi * n / params.sats_per_plane
                + 2.0 * math.pi * params.phase_factor * m / params.total_satellites
                + cfg.mean_motion_rad_s * float(t_s)
            )
            x_orb = radius * math.cos(phase)
            y_orb = radius * math.sin(phase)

            x_inc = x_orb
            y_inc = y_orb * cos_i
            z_inc = y_orb * sin_i

            x_i = cos_o * x_inc - sin_o * y_inc
            y_i = sin_o * x_inc + cos_o * y_inc
            z_i = z_inc
            eci.append([x_i, y_i, z_i])

            # R3(-omega_e t)
            x_e = cos_e * x_i + sin_e * y_i
            y_e = -sin_e * x_i + cos_e * y_i
            ecef.append([x_e, y_e, z_i])

    return np.asarray(eci, dtype=float), np.asarray(ecef, dtype=float)
