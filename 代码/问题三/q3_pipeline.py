"""Pipeline helpers that compose Problem 3 algorithms A-K."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np

from q3_access import access_sets_naive, access_summary
from q3_config import ConstellationParams, Q3Config, SimulationConfig
from q3_orbit import satellite_positions
from q3_routing import RouteResult, min_delay_routes
from q3_statistics import delay_statistics
from q3_topology import build_isl_graph, topology_summary
from q3_traffic import baseline_loads, uniform_od_demand, LoadResult


@dataclass(frozen=True)
class SnapshotResult:
    t_s: float
    topology: dict
    access: dict
    routes: dict[tuple[int, int], RouteResult]
    delay_statistics: dict
    loads: LoadResult | None


def run_snapshot(
    params: ConstellationParams,
    *,
    t_s: float,
    ground_points_ecef_km: np.ndarray,
    config: Q3Config | None = None,
    simulation: SimulationConfig | None = None,
    od_pairs: Iterable[tuple[int, int]] | None = None,
    total_flow_gbps: float | None = None,
) -> SnapshotResult:
    """Run topology, access, routing, statistics, and optional load for one time."""

    cfg = config or Q3Config()
    sim = simulation or SimulationConfig()
    r_eci, r_ecef = satellite_positions(params, t_s, cfg)
    graph = build_isl_graph(r_eci, params, config=cfg, method=sim.topology_method)
    access = access_sets_naive(r_ecef, ground_points_ecef_km, cfg.access_angle_rad)

    if od_pairs is None:
        J = len(ground_points_ecef_km)
        od_pairs = [(a, b) for a in range(J) for b in range(J) if a != b]
    pairs = list(od_pairs)
    routes = min_delay_routes(
        graph,
        access,
        r_ecef,
        ground_points_ecef_km,
        od_pairs=pairs,
        c_km_s=cfg.speed_of_light_km_s,
    )
    stats = delay_statistics((route.delay_s for route in routes.values()), delay_limit_s=cfg.delay_limit_s)

    loads = None
    if total_flow_gbps is not None:
        demand = uniform_od_demand(len(ground_points_ecef_km), total_flow_gbps=total_flow_gbps, ordered=sim.od_ordered)
        path_table = {od: route.path for od, route in routes.items() if route.reachable}
        loads = baseline_loads(path_table, demand, satellite_count=params.total_satellites)

    return SnapshotResult(
        t_s=float(t_s),
        topology=topology_summary(graph),
        access=access_summary(access),
        routes=routes,
        delay_statistics=stats,
        loads=loads,
    )


def parameter_sensitivity(
    cases: Iterable[ConstellationParams],
    evaluator: Callable[[ConstellationParams], dict],
) -> list[dict]:
    """Algorithm K: run a caller-supplied evaluator over parameter cases."""

    records: list[dict] = []
    for params in cases:
        record = {
            "planes": params.planes,
            "sats_per_plane": params.sats_per_plane,
            "phase_factor": params.phase_factor,
            "inclination_deg": params.inclination_deg,
        }
        record.update(evaluator(params))
        records.append(record)
    return records
