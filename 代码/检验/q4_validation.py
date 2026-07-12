"""Problem 4 scenario sensitivity and annual-event Monte Carlo validation."""

from __future__ import annotations

from dataclasses import replace
import math

import numpy as np

from common import bootstrap_problem_paths, make_rng


bootstrap_problem_paths()

from q4_config import AvoidanceParameters, DebrisEnvironment, MissionParameters  # noqa: E402
from q4_avoidance import avoidance_decision  # noqa: E402
from q4_capacity_cost import capacity_loss_ratio  # noqa: E402
from q4_collision import collision_probability_2d_gaussian  # noqa: E402
from q4_debris import conjunction_event_rate_per_year, split_catalog_density  # noqa: E402


def simulate_annual_events(
    satellite_count: int,
    annual_conjunction_rate: float,
    trigger_probability: float,
    feasible_probability: float,
    failure_probability: float,
    replicates: int,
    seed: int,
) -> list[dict[str, int]]:
    """Sample annual conjunction, avoidance, and satellite-failure counts."""

    values = (annual_conjunction_rate, trigger_probability, feasible_probability, failure_probability)
    if not isinstance(satellite_count, (int, np.integer)) or int(satellite_count) <= 0:
        raise ValueError("satellite_count must be a positive integer")
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("event parameters must be finite")
    if float(annual_conjunction_rate) < 0.0 or any(not 0.0 <= float(value) <= 1.0 for value in values[1:]):
        raise ValueError("invalid event probabilities")
    if not isinstance(replicates, (int, np.integer)) or int(replicates) <= 0:
        raise ValueError("replicates must be a positive integer")
    rng = make_rng(seed)
    rows: list[dict[str, int]] = []
    for replicate in range(int(replicates)):
        conjunctions = int(rng.poisson(int(satellite_count) * float(annual_conjunction_rate)))
        triggered = int(rng.binomial(conjunctions, float(trigger_probability)))
        avoidances = int(rng.binomial(triggered, float(feasible_probability)))
        failures = int(rng.binomial(int(satellite_count), float(failure_probability)))
        rows.append(
            {
                "replicate": replicate,
                "conjunctions": conjunctions,
                "triggered": triggered,
                "avoidances": avoidances,
                "residual_conjunctions": conjunctions - avoidances,
                "failures": failures,
            }
        )
    return rows


def _annual_rate(environment: DebrisEnvironment) -> float:
    catalog_density, _uncatalog_density = split_catalog_density(
        environment.total_density_gt_1cm_km3,
        environment.catalog_threshold_cm,
        environment.beta,
    )
    return float(
        conjunction_event_rate_per_year(
            environment.screening_radius_km,
            environment.relative_speed_km_s,
            catalog_density,
            environment.year_s,
        )
    )


def _avoidance_probabilities(
    environment: DebrisEnvironment,
    avoidance: AvoidanceParameters,
) -> tuple[float, float, float]:
    """Estimate trigger, feasibility, and residual-risk proxies from the Q4 model.

    The miss-distance ensemble is an explicit *scenario input*, not an
    observation sample.  It is kept identical across one-factor scenarios so
    that the reported differences are attributable to the perturbed parameter.
    """

    miss_distances = np.linspace(0.0, 2.0, 41)
    covariance = np.diag([0.05**2, 0.08**2])
    hard_body_radius = environment.satellite_radius_km + 0.5 * environment.debris_diameter_cm * 1e-5
    decisions = []
    for miss in miss_distances:
        collision_probability = collision_probability_2d_gaussian(
            np.array([miss, 0.0]),
            covariance,
            hard_body_radius,
            radial_steps=48,
            angular_steps=64,
        )
        decisions.append(
            avoidance_decision(
                collision_probability=collision_probability,
                threshold=avoidance.threshold,
                current_miss_km=float(miss),
                target_miss_km=avoidance.target_miss_km,
                sensitivity_km_per_mps=avoidance.miss_distance_sensitivity_km_per_mps,
                max_delta_v_mps=avoidance.max_delta_v_mps,
                post_maneuver_probability=avoidance.safe_probability,
            )
        )
    triggered = [decision for decision in decisions if decision.triggered]
    trigger_probability = float(len(triggered) / len(decisions))
    feasible_probability = float(
        np.mean([decision.feasible for decision in triggered]) if triggered else 0.0
    )
    residual_probability = float(np.mean([decision.residual_probability for decision in decisions]))
    return trigger_probability, feasible_probability, residual_probability


def run_q4_sensitivity(
    satellite_count: int,
    environment: DebrisEnvironment,
    avoidance: AvoidanceParameters,
    mission: MissionParameters,
) -> list[dict[str, float | int | str]]:
    """Return one-factor debris, speed, threshold, and capacity scenarios."""

    if mission.satellite_count != satellite_count:
        raise ValueError("mission.satellite_count must equal satellite_count")
    scenarios = [
        ("baseline", environment, avoidance),
        ("density_x0.5", replace(environment, total_density_gt_1cm_km3=environment.total_density_gt_1cm_km3 * 0.5), avoidance),
        ("density_x2", replace(environment, total_density_gt_1cm_km3=environment.total_density_gt_1cm_km3 * 2.0), avoidance),
        ("speed_8kms", replace(environment, relative_speed_km_s=8.0), avoidance),
        ("speed_12kms", replace(environment, relative_speed_km_s=12.0), avoidance),
        ("threshold_1e-6", environment, replace(avoidance, threshold=1e-6)),
        ("threshold_1e-4", environment, replace(avoidance, threshold=1e-4)),
        ("capacity_reduction_0.25", environment, replace(avoidance, capacity_reduction=0.25)),
        ("capacity_reduction_0.75", environment, replace(avoidance, capacity_reduction=0.75)),
    ]
    rows: list[dict[str, float | int | str]] = []
    for scenario, env, avoid in scenarios:
        annual_rate = _annual_rate(env)
        trigger_probability, feasible_probability, residual_probability = _avoidance_probabilities(env, avoid)
        annual_avoidances = float(satellite_count * annual_rate * trigger_probability * feasible_probability)
        rows.append(
            {
                "scenario": scenario,
                "satellite_count": int(satellite_count),
                "annual_conjunction_rate": annual_rate,
                "trigger_probability": trigger_probability,
                "feasible_probability": feasible_probability,
                "residual_collision_probability_proxy": residual_probability,
                "annual_avoidances": annual_avoidances,
                "capacity_loss_ratio": capacity_loss_ratio(
                    total_avoidances=annual_avoidances,
                    satellite_count=satellite_count,
                    maneuver_duration_s=avoid.maneuver_duration_s,
                    year_s=env.year_s,
                    capacity_reduction=avoid.capacity_reduction,
                ),
                "debris_density_km3": float(env.total_density_gt_1cm_km3),
                "relative_speed_km_s": float(env.relative_speed_km_s),
                "threshold": float(avoid.threshold),
                "capacity_reduction": float(avoid.capacity_reduction),
            }
        )
    return rows
