"""Capacity-loss and cost formulas for Problem 4."""

from __future__ import annotations

import math


def capacity_loss_ratio(
    *,
    total_avoidances: float,
    satellite_count: int,
    maneuver_duration_s: float,
    year_s: float,
    capacity_reduction: float = 0.5,
) -> float:
    """Fraction of constellation capacity-time lost to avoidance maneuvers."""

    if satellite_count <= 0:
        raise ValueError("satellite_count must be positive")
    if year_s <= 0:
        raise ValueError("year_s must be positive")
    if min(total_avoidances, maneuver_duration_s, capacity_reduction) < 0:
        raise ValueError("avoidances, duration, and reduction must be non-negative")
    return float(capacity_reduction * maneuver_duration_s * total_avoidances / (satellite_count * year_s))


def avoidance_cost_wanyuan(avoidance_count: float, cost_per_avoidance_wanyuan: float = 2.0) -> float:
    if avoidance_count < 0 or cost_per_avoidance_wanyuan < 0:
        raise ValueError("cost inputs must be non-negative")
    return float(avoidance_count * cost_per_avoidance_wanyuan)


def replacement_unit_cost_wanyuan(
    satellite_cost_wanyuan: float,
    launch_cost_wanyuan: float,
    satellites_per_launch: int,
) -> float:
    if satellite_cost_wanyuan < 0 or launch_cost_wanyuan < 0:
        raise ValueError("cost inputs must be non-negative")
    if satellites_per_launch <= 0:
        raise ValueError("satellites_per_launch must be positive")
    return float(satellite_cost_wanyuan + launch_cost_wanyuan / satellites_per_launch)


def annual_expected_failures(satellite_count: int, failure_rate_per_s: float, year_s: float) -> float:
    if satellite_count < 0 or failure_rate_per_s < 0 or year_s < 0:
        raise ValueError("failure inputs must be non-negative")
    return float(satellite_count * failure_rate_per_s * year_s)


def launch_batches_needed(satellite_count: int, satellites_per_launch: int) -> int:
    if satellite_count < 0:
        raise ValueError("satellite_count must be non-negative")
    if satellites_per_launch <= 0:
        raise ValueError("satellites_per_launch must be positive")
    return int(math.ceil(satellite_count / satellites_per_launch))
