"""Shared configuration objects for Problem 3 communication-network algorithms."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Q3Config:
    """Physical constants and problem-specific limits.

    Units are km, seconds, and Gbps unless the field name states otherwise.
    """

    earth_radius_km: float = 6371.0
    altitude_km: float = 550.0
    mu_km3_s2: float = 398600.4418
    earth_rotation_rad_s: float = 7.2921159e-5
    speed_of_light_km_s: float = 299792.458
    isl_max_distance_km: float = 5000.0
    processing_delay_s: float = 0.0005
    ground_coverage_radius_km: float = 506.0
    access_capacity_gbps: float = 20.0
    delay_limit_s: float = 0.030
    coverage_angle_rad: float | None = None

    @property
    def semi_major_axis_km(self) -> float:
        return self.earth_radius_km + self.altitude_km

    @property
    def mean_motion_rad_s(self) -> float:
        return math.sqrt(self.mu_km3_s2 / self.semi_major_axis_km**3)

    @property
    def orbital_period_s(self) -> float:
        return 2.0 * math.pi / self.mean_motion_rad_s

    @property
    def access_angle_rad(self) -> float:
        if self.coverage_angle_rad is not None:
            return self.coverage_angle_rad
        return self.ground_coverage_radius_km / self.earth_radius_km


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
        if self.phase_factor < 0:
            raise ValueError("phase_factor must be non-negative")
        if not 0.0 <= self.inclination_deg <= 180.0:
            raise ValueError("inclination_deg must be in [0, 180]")


@dataclass(frozen=True)
class SimulationConfig:
    duration_s: float = 0.0
    step_s: float = 60.0
    od_ordered: bool = True
    save_all_paths: bool = True
    topology_method: str = "nearest"
