"""Debris density splitting and flux-based risk formulas for Problem 4."""

from __future__ import annotations

import math

CM_TO_KM = 1e-5
DEFAULT_YEAR_S = 31_536_000.0


def cumulative_power_law_density(total_density_km3: float, diameter_cm: float, beta: float) -> float:
    """Return n(>D) from n(>1 cm) using a cumulative power law."""

    if total_density_km3 < 0:
        raise ValueError("total_density_km3 must be non-negative")
    if diameter_cm <= 0:
        raise ValueError("diameter_cm must be positive")
    if beta < 0:
        raise ValueError("beta must be non-negative")
    return float(total_density_km3 * diameter_cm ** (-beta))


def split_catalog_density(total_density_km3: float, catalog_threshold_cm: float, beta: float) -> tuple[float, float]:
    """Split total >1 cm density into cataloged and uncataloged components."""

    catalog = cumulative_power_law_density(total_density_km3, catalog_threshold_cm, beta)
    catalog = min(catalog, total_density_km3)
    return catalog, float(max(0.0, total_density_km3 - catalog))


def collision_cross_section_km2(sat_radius_km: float, debris_diameter_cm: float) -> float:
    """Hard-body collision cross-section in km^2.

    `debris_diameter_cm` is converted to km before combining radii.
    """

    if sat_radius_km < 0:
        raise ValueError("sat_radius_km must be non-negative")
    if debris_diameter_cm < 0:
        raise ValueError("debris_diameter_cm must be non-negative")
    debris_radius_km = 0.5 * debris_diameter_cm * CM_TO_KM
    return float(math.pi * (sat_radius_km + debris_radius_km) ** 2)


def flux_collision_rate_per_s(cross_section_km2: float, relative_speed_km_s: float, density_km3: float) -> float:
    """Flux approximation rate sigma * v_rel * n in 1/s."""

    if cross_section_km2 < 0 or relative_speed_km_s < 0 or density_km3 < 0:
        raise ValueError("cross_section, speed, and density must be non-negative")
    return float(cross_section_km2 * relative_speed_km_s * density_km3)


def annual_probability(rate_per_s: float, year_s: float = DEFAULT_YEAR_S) -> float:
    """Convert a Poisson rate to probability over `year_s`."""

    if rate_per_s < 0:
        raise ValueError("rate_per_s must be non-negative")
    if year_s < 0:
        raise ValueError("year_s must be non-negative")
    return float(1.0 - math.exp(-rate_per_s * year_s))


def conjunction_event_rate_per_year(
    screening_radius_km: float,
    relative_speed_km_s: float,
    catalog_density_km3: float,
    year_s: float = DEFAULT_YEAR_S,
) -> float:
    """Expected yearly cataloged conjunction events through a screening cylinder."""

    if screening_radius_km < 0:
        raise ValueError("screening_radius_km must be non-negative")
    area_km2 = math.pi * screening_radius_km**2
    return float(area_km2 * relative_speed_km_s * catalog_density_km3 * year_s)
