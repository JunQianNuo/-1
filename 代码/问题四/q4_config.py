"""Configuration objects for Problem 4 debris-avoidance and robustness models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DebrisEnvironment:
    """Debris and conjunction-screening parameters.

    Units: km, seconds, and counts per km^3 unless a field says otherwise.
    """

    total_density_gt_1cm_km3: float = 1e-8
    beta: float = 2.25
    catalog_threshold_cm: float = 10.0
    relative_speed_km_s: float = 10.0
    screening_radius_km: float = 5.0
    satellite_radius_km: float = 0.001
    debris_diameter_cm: float = 10.0
    year_s: float = 31_536_000.0


@dataclass(frozen=True)
class AvoidanceParameters:
    threshold: float = 1e-5
    safe_probability: float = 1e-6
    max_delta_v_mps: float = 1.0
    target_miss_km: float = 1.0
    miss_distance_sensitivity_km_per_mps: float = 2.0
    maneuver_duration_s: float = 600.0
    capacity_reduction: float = 0.5


@dataclass(frozen=True)
class CostParameters:
    avoidance_cost_wanyuan: float = 2.0
    satellite_cost_wanyuan: float = 500.0
    launch_cost_wanyuan: float = 20_000.0
    satellites_per_launch: int = 60


@dataclass(frozen=True)
class MissionParameters:
    satellite_count: int
    design_life_years: float = 5.0
    intrinsic_failure_rate_per_s: float = 0.0
