"""Problem 3 parameter sensitivity and time-block bootstrap validation."""

from __future__ import annotations

from dataclasses import replace
import math

import numpy as np

from common import bootstrap_problem_paths, make_rng


bootstrap_problem_paths()

from q3_access import access_sets_naive  # noqa: E402
from q3_batched_routing import batched_ground_delay_matrix  # noqa: E402
from q3_config import ConstellationParams, Q3Config, SimulationConfig  # noqa: E402
from q3_joint_evaluator import FidelityGrid, MotherGrid, evaluate_joint_candidate  # noqa: E402
from q3_orbit import satellite_positions  # noqa: E402
from q3_topology import build_isl_graph  # noqa: E402


def summarize_delay_blocks(delay_blocks: list[np.ndarray] | np.ndarray, limit_s: float = 0.03) -> np.ndarray:
    """Return one all-sample 30 ms rate for every time block."""

    if not math.isfinite(float(limit_s)) or float(limit_s) < 0.0:
        raise ValueError("limit_s must be finite and nonnegative")
    rates: list[float] = []
    for block in delay_blocks:
        delays = np.asarray(block, dtype=float).ravel()
        if delays.size == 0 or np.any(np.isnan(delays)) or np.any(delays < 0.0):
            raise ValueError("each delay block must be nonempty and nonnegative")
        rates.append(float(np.mean(np.isfinite(delays) & (delays <= float(limit_s)))))
    if not rates:
        raise ValueError("delay_blocks must be nonempty")
    return np.asarray(rates, dtype=float)


def bootstrap_time_blocks(block_rates: np.ndarray, replicates: int, seed: int) -> list[float]:
    """Bootstrap whole time snapshots to preserve within-snapshot OD dependence."""

    rates = np.asarray(block_rates, dtype=float)
    if rates.ndim != 1 or rates.size == 0 or not np.all(np.isfinite(rates)):
        raise ValueError("block_rates must be a nonempty finite vector")
    if np.any((rates < 0.0) | (rates > 1.0)):
        raise ValueError("block_rates must lie in [0, 1]")
    if not isinstance(replicates, (int, np.integer)) or int(replicates) <= 0:
        raise ValueError("replicates must be a positive integer")
    rng = make_rng(seed)
    draws = rng.integers(0, rates.size, size=(int(replicates), rates.size))
    return [float(np.mean(rates[indices])) for indices in draws]


def evaluate_q3_time_block_rates(
    params: ConstellationParams,
    times_s: np.ndarray,
    ground_ecef_km: np.ndarray,
    config: Q3Config,
    simulation: SimulationConfig,
) -> np.ndarray:
    """Recompute one P30(all) value per snapshot for a real block bootstrap."""

    times = np.asarray(times_s, dtype=float)
    ground = np.asarray(ground_ecef_km, dtype=float)
    if times.ndim != 1 or times.size == 0 or not np.all(np.isfinite(times)):
        raise ValueError("times_s must be a nonempty finite vector")
    if ground.ndim != 2 or ground.shape[0] < 2 or ground.shape[1] != 3:
        raise ValueError("ground_ecef_km must have shape (J, 3), J >= 2")
    rates: list[float] = []
    off_diagonal = ~np.eye(ground.shape[0], dtype=bool)
    for time_s in times:
        satellite_eci, satellite_ecef = satellite_positions(params, float(time_s), config)
        access = access_sets_naive(satellite_ecef, ground, config.access_angle_rad)
        graph = build_isl_graph(satellite_eci, params, config=config, method=simulation.topology_method)
        delays = batched_ground_delay_matrix(
            graph, access, satellite_ecef, ground, c_km_s=config.speed_of_light_km_s
        )[off_diagonal]
        rates.append(float(np.mean(np.isfinite(delays) & (delays <= config.delay_limit_s))))
    return np.asarray(rates, dtype=float)


def run_q3_sensitivity(
    params: ConstellationParams,
    mother_grid: MotherGrid,
    fidelity: FidelityGrid,
    config: Q3Config,
    simulation: SimulationConfig,
) -> list[dict[str, float | int | str]]:
    """Evaluate baseline and four one-factor physical scenarios without P30 pruning."""

    scenarios = [
        ("baseline", config),
        ("processing_0ms", replace(config, processing_delay_s=0.0)),
        ("processing_1ms", replace(config, processing_delay_s=0.001)),
        ("isl_4500km", replace(config, isl_max_distance_km=4500.0)),
        ("isl_5500km", replace(config, isl_max_distance_km=5500.0)),
    ]
    rows: list[dict[str, float | int | str]] = []
    for scenario, candidate_config in scenarios:
        result, _state = evaluate_joint_candidate(
            params,
            mother_grid=mother_grid,
            fidelity=fidelity,
            config=candidate_config,
            simulation=simulation,
        )
        rows.append(
            {
                "scenario": scenario,
                "processing_delay_s": float(candidate_config.processing_delay_s),
                "isl_max_distance_km": float(candidate_config.isl_max_distance_km),
                "C1": float(result.c1),
                "C2": float(result.c2),
                "p30_all": float(result.p30_all),
                "p30_reachable": float(result.p30_reachable),
                "reachable_count": int(result.reachable_count),
                "late_reachable_count": int(result.late_reachable_count),
                "unreachable_count": int(result.unreachable_count),
                "max_delay_s": None if result.max_delay_s is None else float(result.max_delay_s),
            }
        )
    return rows
