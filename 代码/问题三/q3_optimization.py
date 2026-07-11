"""Candidate path, traffic-engineering, and throughput search algorithms."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

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
    """Route fixed-path multi-commodity flow with a min-max-utilization search.

    The mathematical model is a linear program.  For portability in the contest
    workspace, the implementation below solves the feasibility form by binary
    searching the maximum utilization ``rho`` and greedily filling residual
    path bottlenecks.  This is exact for the common screening cases with
    edge-disjoint alternatives and remains a fast conservative engineering
    heuristic for larger coupled multi-commodity cases.
    """

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

    def try_route(rho: float) -> tuple[bool, dict[tuple[tuple[int, int], int], float], dict[tuple[int, int], float]]:
        loads = {edge: 0.0 for edge in capacities}
        flows: dict[tuple[tuple[int, int], int], float] = {}
        for od, demand in demand_gbps.items():
            remaining = float(demand)
            indexed_paths = list(enumerate(candidate_path_map.get(od, [])))
            indexed_paths.sort(key=lambda item: item[1].cost_s if delay_weight else 0.0)
            while remaining > 1e-9:
                best_idx: int | None = None
                best_path: PathOption | None = None
                best_bottleneck = 0.0
                for idx, path in indexed_paths:
                    constrained_edges = [edge for edge in path.edges if edge in capacities]
                    if not constrained_edges:
                        best_idx, best_path, best_bottleneck = idx, path, remaining
                        break
                    residual = min(rho * capacities[edge] - loads[edge] for edge in constrained_edges)
                    if residual > best_bottleneck:
                        best_idx, best_path, best_bottleneck = idx, path, residual
                if best_idx is None or best_path is None or best_bottleneck <= 1e-9:
                    return False, flows, loads
                flow = min(remaining, best_bottleneck)
                flows[(od, best_idx)] = flows.get((od, best_idx), 0.0) + flow
                for edge in best_path.edges:
                    if edge in loads:
                        loads[edge] += flow
                remaining -= flow
        return True, flows, loads

    hi = float(max_utilization) if max_utilization is not None else 1.0
    feasible, flows, loads = try_route(hi)
    while not feasible and max_utilization is None and hi < 1e6:
        hi *= 2.0
        feasible, flows, loads = try_route(hi)
    if not feasible:
        return MultipathResult(False, math.inf, message="demand exceeds path capacities")

    low = 0.0
    best_flows, best_loads = flows, loads
    for _ in range(60):
        mid = 0.5 * (low + hi)
        feasible_mid, flows_mid, loads_mid = try_route(mid)
        if feasible_mid:
            hi = mid
            best_flows, best_loads = flows_mid, loads_mid
        else:
            low = mid
    rho_actual = max((best_loads[e] / cap for e, cap in capacities.items()), default=0.0)
    return MultipathResult(True, float(rho_actual), best_flows, best_loads, "min-max utilization search")


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
