"""Avoidance-trigger and delta-v feasibility helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AvoidanceDecision:
    triggered: bool
    feasible: bool
    required_delta_v_mps: float
    residual_probability: float


def max_miss_distance_km(delta_v_mps: float, sensitivity_km_per_mps: float) -> float:
    """Maximum b-plane miss-distance increase under a scalar sensitivity model."""

    if delta_v_mps < 0.0:
        raise ValueError("delta_v_mps must be non-negative")
    if sensitivity_km_per_mps < 0.0:
        raise ValueError("sensitivity_km_per_mps must be non-negative")
    return float(delta_v_mps * sensitivity_km_per_mps)


def required_delta_v_mps(current_miss_km: float, target_miss_km: float, sensitivity_km_per_mps: float) -> float:
    """Delta-v needed to raise current miss distance to a target distance."""

    if sensitivity_km_per_mps <= 0.0:
        raise ValueError("sensitivity_km_per_mps must be positive")
    return float(max(0.0, target_miss_km - current_miss_km) / sensitivity_km_per_mps)


def avoidance_decision(
    *,
    collision_probability: float,
    threshold: float,
    current_miss_km: float,
    target_miss_km: float,
    sensitivity_km_per_mps: float,
    max_delta_v_mps: float,
    post_maneuver_probability: float = 0.0,
) -> AvoidanceDecision:
    """Apply threshold trigger and delta-v feasibility logic."""

    if threshold < 0.0 or collision_probability < 0.0:
        raise ValueError("probabilities must be non-negative")
    required = required_delta_v_mps(current_miss_km, target_miss_km, sensitivity_km_per_mps)
    triggered = collision_probability >= threshold
    feasible = triggered and required <= max_delta_v_mps
    residual = post_maneuver_probability if feasible else collision_probability
    return AvoidanceDecision(triggered, feasible, required, float(residual))
