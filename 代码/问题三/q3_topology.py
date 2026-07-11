"""ISL topology construction and validation helpers for Problem 3."""

from __future__ import annotations

from collections import deque

import numpy as np

from q3_config import ConstellationParams, Q3Config
from q3_routing import WeightedGraph


def satellite_id(plane: int, sat_in_plane: int, sats_per_plane: int) -> int:
    return plane * sats_per_plane + sat_in_plane


def build_isl_graph(
    satellite_eci_km: np.ndarray,
    params: ConstellationParams,
    *,
    config: Q3Config | None = None,
    method: str = "walker",
    walker_shift: int | None = None,
) -> WeightedGraph:
    """Build one weighted ISL snapshot graph."""

    params.validate()
    cfg = config or Q3Config()
    positions = np.asarray(satellite_eci_km, dtype=float)
    if positions.shape != (params.total_satellites, 3):
        raise ValueError("satellite_eci_km shape does not match constellation")

    graph = WeightedGraph(params.total_satellites)
    candidates: set[tuple[int, int]] = set()
    M, N = params.planes, params.sats_per_plane

    for m in range(M):
        for n in range(N):
            u = satellite_id(m, n, N)
            candidates.add(_ordered_pair(u, satellite_id(m, (n + 1) % N, N)))

    if method == "walker":
        shift = _default_walker_shift(params) if walker_shift is None else int(walker_shift)
        for m in range(M):
            next_m = (m + 1) % M
            for n in range(N):
                u = satellite_id(m, n, N)
                v = satellite_id(next_m, (n + shift) % N, N)
                candidates.add(_ordered_pair(u, v))
    elif method in {"nearest", "kd_tree"}:
        for m in range(M):
            next_m = (m + 1) % M
            next_ids = [satellite_id(next_m, r, N) for r in range(N)]
            next_pos = positions[next_ids]
            for n in range(N):
                u = satellite_id(m, n, N)
                distances = np.linalg.norm(next_pos - positions[u], axis=1)
                v = next_ids[int(np.argmin(distances))]
                candidates.add(_ordered_pair(u, v))
    else:
        raise ValueError("method must be 'walker', 'nearest', or 'kd_tree'")

    for u, v in candidates:
        distance = float(np.linalg.norm(positions[u] - positions[v]))
        if distance <= cfg.isl_max_distance_km:
            weight = distance / cfg.speed_of_light_km_s + cfg.processing_delay_s
            graph.add_edge(u, v, weight, distance)
    return graph


def topology_summary(graph: WeightedGraph) -> dict[str, float | int]:
    degrees = graph.degrees()
    max_distance = max((edge.distance_km for edge in graph.edges), default=0.0)
    return {
        "satellite_count": graph.node_count,
        "edge_count": len(graph.edges),
        "max_degree": max(degrees.values(), default=0),
        "min_degree": min(degrees.values(), default=0),
        "component_count": len(connected_components(graph)),
        "max_link_distance_km": float(max_distance),
    }


def connected_components(graph: WeightedGraph) -> list[list[int]]:
    seen: set[int] = set()
    comps: list[list[int]] = []
    for start in range(graph.node_count):
        if start in seen:
            continue
        comp: list[int] = []
        queue: deque[int] = deque([start])
        seen.add(start)
        while queue:
            node = queue.popleft()
            comp.append(node)
            for nbr, _w in graph.neighbors(node):
                if nbr not in seen:
                    seen.add(nbr)
                    queue.append(nbr)
        comps.append(comp)
    return comps


def _default_walker_shift(params: ConstellationParams) -> int:
    if params.planes <= 0:
        return 0
    return int(round(params.phase_factor * params.sats_per_plane / max(1, params.total_satellites)))


def _ordered_pair(u: int, v: int) -> tuple[int, int]:
    return (u, v) if u <= v else (v, u)
