"""Candidate path, traffic-engineering LP, and throughput search algorithms."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np
from scipy.optimize import linprog

from q3_routing import WeightedGraph, multi_source_dijkstra, normalized_edge, shortest_path


@dataclass(frozen=True)
class PathOption:
    nodes: list[int]
    cost_s: float

    @property
    def edges(self) -> list[tuple[int, int]]:
        return [normalized_edge(u, v) for u, v in zip(self.nodes, self.nodes[1:])]


@dataclass(frozen=True)
class MultipathResult:
    feasible: bool
    rho_max: float
    path_flows_gbps: dict[tuple[tuple[int, int], int], float] = field(default_factory=dict)
    link_load_gbps: dict[tuple[int, int], float] = field(default_factory=dict)
    message: str = ""


@dataclass(frozen=True)
class ThroughputResult:
    lambda_star: float
    throughput_gbps: float
    iterations: int
    feasible: bool


def candidate_paths(
    graph: WeightedGraph,
    source: int,
    target: int,
    *,
    k: int = 3,
    strategy: str = "yen",
    max_delay_s: float | None = None,
    edge_penalty: dict[tuple[int, int], float] | None = None,
) -> list[PathOption]:
    """Generate up to ``k`` loop-free candidate paths."""

    if k <= 0:
        return []
    if strategy == "delete_edges":
        return _candidate_paths_delete_edges(graph, source, target, k, max_delay_s=max_delay_s)
    if strategy == "penalty":
        path = _shortest_path_option(graph, source, target, extra_edge_cost=edge_penalty)
        return _filter_paths([path], max_delay_s)
    if strategy != "yen":
        raise ValueError("strategy must be 'yen', 'delete_edges', or 'penalty'")
    return _candidate_paths_yen(graph, source, target, k, max_delay_s=max_delay_s)


def multipath_flow_lp(
    *,
    candidate_path_map: dict[tuple[int, int], list[PathOption]],
    demand_gbps: dict[tuple[int, int], float],
    link_capacity_gbps: dict[tuple[int, int], float] | None = None,
    max_utilization: float | None = None,
    delay_weight: float = 0.0,
) -> MultipathResult:
    """Solve fixed-path multi-commodity flow as a linear program."""

    variables: list[tuple[tuple[int, int], int, PathOption]] = []
    for od, paths in candidate_path_map.items():
        for idx, path in enumerate(paths):
            variables.append((od, idx, path))
    if not variables:
        return MultipathResult(False, math.inf, message="no candidate paths")

    n_flow = len(variables)
    rho_idx = n_flow
    c = np.zeros(n_flow + 1)
    c[rho_idx] = 1.0
    if delay_weight:
        for j, (_od, _idx, path) in enumerate(variables):
            c[j] = float(delay_weight) * path.cost_s

    A_eq: list[list[float]] = []
    b_eq: list[float] = []
    for od, demand in demand_gbps.items():
        row = [0.0] * (n_flow + 1)
        for j, (var_od, _idx, _path) in enumerate(variables):
            if var_od == od:
                row[j] = 1.0
        if not any(row[:-1]) and demand > 0:
            return MultipathResult(False, math.inf, message=f"no path for OD {od}")
        A_eq.append(row)
        b_eq.append(float(demand))

    A_ub: list[list[float]] = []
    b_ub: list[float] = []
    capacities = {normalized_edge(*e): float(cap) for e, cap in (link_capacity_gbps or {}).items()}
    for edge, cap in capacities.items():
        if cap <= 0:
            return MultipathResult(False, math.inf, message=f"non-positive capacity for {edge}")
        row = [0.0] * (n_flow + 1)
        for j, (_od, _idx, path) in enumerate(variables):
            if edge in path.edges:
                row[j] = 1.0
        row[rho_idx] = -cap
        A_ub.append(row)
        b_ub.append(0.0)

    if max_utilization is not None:
        row = [0.0] * (n_flow + 1)
        row[rho_idx] = 1.0
        A_ub.append(row)
        b_ub.append(float(max_utilization))

    bounds = [(0.0, None)] * (n_flow + 1)
    result = linprog(
        c,
        A_ub=np.asarray(A_ub) if A_ub else None,
        b_ub=np.asarray(b_ub) if b_ub else None,
        A_eq=np.asarray(A_eq) if A_eq else None,
        b_eq=np.asarray(b_eq) if b_eq else None,
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        return MultipathResult(False, math.inf, message=result.message)

    flows: dict[tuple[tuple[int, int], int], float] = {}
    link_loads: dict[tuple[int, int], float] = {edge: 0.0 for edge in capacities}
    for j, (od, idx, path) in enumerate(variables):
        flow = float(result.x[j])
        flows[(od, idx)] = flow
        for edge in path.edges:
            if edge in capacities:
                link_loads[edge] += flow
    return MultipathResult(True, float(result.x[rho_idx]), flows, link_loads, result.message)


def throughput_binary_search(
    *,
    candidate_path_map: dict[tuple[int, int], list[PathOption]],
    base_demand_gbps: dict[tuple[int, int], float],
    link_capacity_gbps: dict[tuple[int, int], float],
    high: float,
    tol: float = 1e-3,
    max_iter: int = 60,
) -> ThroughputResult:
    """Find maximum demand scale whose LP is feasible at utilization <= 1."""

    low = 0.0
    hi = float(high)
    feasible_seen = False
    iterations = 0
    for iterations in range(1, max_iter + 1):
        mid = 0.5 * (low + hi)
        scaled = {od: mid * demand for od, demand in base_demand_gbps.items()}
        result = multipath_flow_lp(
            candidate_path_map=candidate_path_map,
            demand_gbps=scaled,
            link_capacity_gbps=link_capacity_gbps,
            max_utilization=1.0,
        )
        if result.feasible:
            low = mid
            feasible_seen = True
        else:
            hi = mid
        if hi - low <= tol:
            break
    return ThroughputResult(
        lambda_star=low,
        throughput_gbps=low * sum(base_demand_gbps.values()),
        iterations=iterations,
        feasible=feasible_seen,
    )


def _candidate_paths_delete_edges(
    graph: WeightedGraph,
    source: int,
    target: int,
    k: int,
    *,
    max_delay_s: float | None,
) -> list[PathOption]:
    first = _shortest_path_option(graph, source, target)
    if first is None:
        return []
    candidates = [first]
    seen = {tuple(first.nodes)}
    for edge in first.edges:
        path = _shortest_path_option(graph, source, target, banned_edges={edge})
        if path is not None and tuple(path.nodes) not in seen:
            candidates.append(path)
            seen.add(tuple(path.nodes))
    candidates.sort(key=lambda item: item.cost_s)
    return _filter_paths(candidates[:k], max_delay_s)

def _candidate_paths_yen(
    graph: WeightedGraph,
    source: int,
    target: int,
    k: int,
    *,
    max_delay_s: float | None,
) -> list[PathOption]:
    first = _shortest_path_option(graph, source, target)
    if first is None:
        return []
    accepted = [first]
    pool: list[PathOption] = []
    seen = {tuple(first.nodes)}

    while len(accepted) < k:
        last = accepted[-1]
        for spur_index in range(len(last.nodes) - 1):
            root_nodes = last.nodes[: spur_index + 1]
            spur = root_nodes[-1]
            banned_edges: set[tuple[int, int]] = set()
            banned_nodes = set(root_nodes[:-1])
            for path in accepted:
                if path.nodes[: spur_index + 1] == root_nodes and len(path.nodes) > spur_index + 1:
                    banned_edges.add(normalized_edge(path.nodes[spur_index], path.nodes[spur_index + 1]))
            spur_path = _shortest_path_option(
                graph,
                spur,
                target,
                banned_edges=banned_edges,
                banned_nodes=banned_nodes,
            )
            if spur_path is None:
                continue
            total_nodes = root_nodes[:-1] + spur_path.nodes
            key = tuple(total_nodes)
            if key in seen:
                continue
            option = PathOption(total_nodes, _path_cost(graph, total_nodes))
            seen.add(key)
            pool.append(option)
        if not pool:
            break
        pool.sort(key=lambda item: item.cost_s)
        accepted.append(pool.pop(0))
    return _filter_paths(accepted, max_delay_s)


def _shortest_path_option(
    graph: WeightedGraph,
    source: int,
    target: int,
    *,
    banned_edges: set[tuple[int, int]] | None = None,
    banned_nodes: set[int] | None = None,
    extra_edge_cost: dict[tuple[int, int], float] | None = None,
) -> PathOption | None:
    dist, pred, _root = multi_source_dijkstra(
        graph,
        [(source, 0.0)],
        banned_edges=banned_edges,
        banned_nodes=banned_nodes,
        extra_edge_cost=extra_edge_cost,
    )
    if not math.isfinite(dist[target]):
        return None
    path = shortest_path(pred, source, target)
    if not path:
        return None
    return PathOption(path, float(dist[target]))


def _path_cost(graph: WeightedGraph, nodes: list[int]) -> float:
    return float(sum(graph.edge_weight(u, v) for u, v in zip(nodes, nodes[1:])))


def _filter_paths(paths: list[PathOption | None], max_delay_s: float | None) -> list[PathOption]:
    out: list[PathOption] = []
    for path in paths:
        if path is None:
            continue
        if max_delay_s is None or path.cost_s <= max_delay_s:
            out.append(path)
    return out
