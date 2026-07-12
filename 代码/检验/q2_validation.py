"""Problem 2 coverage sensitivity and spatial-temporal Monte Carlo checks."""

from __future__ import annotations

from dataclasses import replace
import math
from typing import Iterable

import numpy as np

from common import bootstrap_problem_paths, make_rng


bootstrap_problem_paths()

from q2_constellation import (  # noqa: E402
    ConstellationParams,
    CoverageConfig,
    EvaluationResult,
    evaluate_constellation,
)


SIDEREAL_DAY_S = 86164.09


def sample_area_uniform_region(
    n: int,
    rng: np.random.Generator,
    lat_bounds: tuple[float, float] = (4.0, 53.0),
    lon_bounds: tuple[float, float] = (73.0, 135.0),
) -> tuple[np.ndarray, np.ndarray]:
    """Sample latitude by uniform sine and longitude uniformly in a rectangle."""

    if not isinstance(n, (int, np.integer)) or int(n) <= 0:
        raise ValueError("n must be a positive integer")
    lat_min, lat_max = (float(value) for value in lat_bounds)
    lon_min, lon_max = (float(value) for value in lon_bounds)
    if not -90.0 <= lat_min <= lat_max <= 90.0 or lon_min > lon_max:
        raise ValueError("invalid latitude/longitude bounds")
    sine = rng.uniform(math.sin(math.radians(lat_min)), math.sin(math.radians(lat_max)), int(n))
    lat = np.degrees(np.arcsin(sine))
    lon = rng.uniform(lon_min, lon_max, int(n))
    return np.asarray(lat, dtype=float), np.asarray(lon, dtype=float)


def _row_from_result(result: EvaluationResult, *, replicate: int | None, seed: int, scenario: str) -> dict[str, float | int | str]:
    metrics = result.metrics
    return {
        "scenario": scenario,
        "replicate": -1 if replicate is None else int(replicate),
        "seed": int(seed),
        "C1": float(metrics.coverage_rate_q1),
        "C2": float(metrics.coverage_rate_q2),
        "c_min": int(metrics.c_min),
        "max_gap_s": float(metrics.max_gap_s),
        "avg_multiplicity": float(metrics.avg_multiplicity),
        "strict_double_time_rate": float(metrics.strict_double_time_rate),
    }


def run_q2_monte_carlo(
    params: ConstellationParams,
    config: CoverageConfig,
    samples: int,
    time_samples: int,
    replicates: int,
    seed: int,
) -> list[dict[str, float | int | str]]:
    """Evaluate independent area-uniform ground/time samples for one constellation."""

    if not isinstance(time_samples, (int, np.integer)) or int(time_samples) <= 0:
        raise ValueError("time_samples must be a positive integer")
    if not isinstance(replicates, (int, np.integer)) or int(replicates) <= 0:
        raise ValueError("replicates must be a positive integer")
    rng = make_rng(seed)
    rows: list[dict[str, float | int | str]] = []
    for replicate in range(int(replicates)):
        lat, lon = sample_area_uniform_region(int(samples), rng)
        times = np.sort(rng.uniform(0.0, SIDEREAL_DAY_S, int(time_samples)))
        result = evaluate_constellation(params, lat, lon, times, config)
        rows.append(_row_from_result(result, replicate=replicate, seed=seed, scenario="monte_carlo"))
    return rows


def run_q2_sensitivity(
    params: ConstellationParams,
    base_config: CoverageConfig,
    lat_deg: np.ndarray,
    lon_deg: np.ndarray,
    times_s: np.ndarray,
) -> list[dict[str, float | int | str]]:
    """Run one-factor altitude and coverage-radius scenarios around the baseline."""

    scenarios = [("baseline", base_config)]
    scenarios.extend((f"altitude_{altitude:g}km", replace(base_config, altitude_km=float(altitude))) for altitude in (525.0, 575.0))
    scenarios.extend((f"radius_{radius:g}km", replace(base_config, ground_coverage_radius_km=float(radius))) for radius in (480.0, 530.0))
    rows: list[dict[str, float | int | str]] = []
    for scenario, config in scenarios:
        row = _row_from_result(
            evaluate_constellation(params, lat_deg, lon_deg, times_s, config),
            replicate=None,
            seed=0,
            scenario=scenario,
        )
        row["altitude_km"] = float(config.altitude_km)
        row["coverage_radius_km"] = float(config.ground_coverage_radius_km)
        rows.append(row)
    return rows
