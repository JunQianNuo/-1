"""Candidate path, traffic-engineering, and throughput search algorithms."""

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
    """Solve the fixed-path multi-commodity min-max-utilization linear program."""

    variables: list[tuple[tuple[int, int], int, PathOption]] = []
    for od, paths in candidate_path_map.items():
        for idx, path in enumerate(paths):
            variables.append((od, idx, path))
    if not variables:
        return MultipathResult(False, math.inf, message="no candidate paths")

    for od, demand in demand_gbps.items():
        if not candidate_path_map.get(od) and demand > 0:
            return MultipathResult(False, math.inf, message=f"no path for OD {od}")

    capacities = {normalized_edge(*e): float(cap) for e, cap in (link_capacity_gbps or {}).items()}
    for edge, cap in capacities.items():
        if cap <= 0:
            return MultipathResult(False, math.inf, message=f"non-positive capacity for {edge}")

    if not capacities:
        flows: dict[tuple[tuple[int, int], int], float] = {}
        for od, demand in demand_gbps.items():
            paths = candidate_path_map.get(od, [])
            if demand > 0 and not paths:
                return MultipathResult(False, math.inf, message=f"no path for OD {od}")
            if paths:
                flows[(od, 0)] = float(demand)
        return MultipathResult(True, 0.0, flows, {}, "unconstrained links")

    variable_count = len(variables)
    optimize_rho = max_utilization is None
    rho_index = variable_count if optimize_rho else None
    column_count = variable_count + int(optimize_rho)

    objective = np.zeros(column_count, dtype=float)
    if delay_weight and not optimize_rho:
        objective[:variable_count] = [delay_weight * path.cost_s for _od, _idx, path in variables]
    if rho_index is not None:
        objective[rho_index] = 1.0

    equality_rows: list[np.ndarray] = []
    equality_rhs: list[float] = []
    for od, demand in demand_gbps.items():
        row = np.zeros(column_count, dtype=float)
        for column, (variable_od, _idx, _path) in enumerate(variables):
            if variable_od == od:
                row[column] = 1.0
        equality_rows.append(row)
        equality_rhs.append(float(demand))

    capacity_rows: list[np.ndarray] = []
    capacity_rhs: list[float] = []
    for edge, capacity in capacities.items():
        row = np.zeros(column_count, dtype=float)
        for column, (_od, _idx, path) in enumerate(variables):
            if edge in path.edges:
                row[column] = 1.0
        if rho_index is not None:
            row[rho_index] = -capacity
            rhs = 0.0
        else:
            rhs = float(max_utilization) * capacity
        capacity_rows.append(row)
        capacity_rhs.append(rhs)

    solution = linprog(
        objective,
        A_ub=np.asarray(capacity_rows),
        b_ub=np.asarray(capacity_rhs),
        A_eq=np.asarray(equality_rows),
        b_eq=np.asarray(equality_rhs),
        bounds=[(0.0, None)] * column_count,
        method="highs",
    )
    if not solution.success:
        return MultipathResult(False, math.inf, message=f"linear program infeasible: {solution.message}")

    if optimize_rho and delay_weight:
        secondary_objective = np.zeros(column_count, dtype=float)
        secondary_objective[:variable_count] = [
            delay_weight * path.cost_s for _od, _idx, path in variables
        ]
        rho_optimum = float(solution.x[rho_index])
        secondary_bounds = [(0.0, None)] * variable_count + [(0.0, rho_optimum + 1e-9)]
        secondary_solution = linprog(
            secondary_objective,
            A_ub=np.asarray(capacity_rows),
            b_ub=np.asarray(capacity_rhs),
            A_eq=np.asarray(equality_rows),
            b_eq=np.asarray(equality_rhs),
            bounds=secondary_bounds,
            method="highs",
        )
        if secondary_solution.success:
            solution = secondary_solution

    flows: dict[tuple[tuple[int, int], int], float] = {}
    loads = {edge: 0.0 for edge in capacities}
    for column, (od, path_index, path) in enumerate(variables):
        flow = float(solution.x[column])
        if flow <= 1e-9:
            continue
        flows[(od, path_index)] = flow
        for edge in path.edges:
            if edge in loads:
                loads[edge] += flow
    rho_actual = max((loads[edge] / capacity for edge, capacity in capacities.items()), default=0.0)
    return MultipathResult(True, float(rho_actual), flows, loads, "linear program solved")


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
