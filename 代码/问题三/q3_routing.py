"""Shortest-path primitives used by the Problem 3 algorithms."""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class GraphEdge:
    u: int
    v: int
    weight_s: float
    distance_km: float = 0.0

    @property
    def key(self) -> tuple[int, int]:
        return normalized_edge(self.u, self.v)


class WeightedGraph:
    """Small undirected weighted graph with non-negative edge weights."""

    def __init__(self, node_count: int):
        if node_count < 0:
            raise ValueError("node_count must be non-negative")
        self.node_count = int(node_count)
        self._edges: dict[tuple[int, int], GraphEdge] = {}

    def add_edge(self, u: int, v: int, weight_s: float, distance_km: float = 0.0) -> None:
        if u == v:
            return
        self._check_node(u)
        self._check_node(v)
        if weight_s < 0:
            raise ValueError("Dijkstra requires non-negative weights")
        key = normalized_edge(u, v)
        old = self._edges.get(key)
        if old is None or weight_s < old.weight_s:
            self._edges[key] = GraphEdge(key[0], key[1], float(weight_s), float(distance_km))

    def copy(self) -> "WeightedGraph":
        new = WeightedGraph(self.node_count)
        new._edges = dict(self._edges)
        return new

    @property
    def edges(self) -> list[GraphEdge]:
        return list(self._edges.values())

    def edge_weight(self, u: int, v: int) -> float:
        return self._edges[normalized_edge(u, v)].weight_s

    def neighbors(self, node: int) -> list[tuple[int, float]]:
        self._check_node(node)
        out: list[tuple[int, float]] = []
        for edge in self._edges.values():
            if edge.u == node:
                out.append((edge.v, edge.weight_s))
            elif edge.v == node:
                out.append((edge.u, edge.weight_s))
        return out

    def degrees(self) -> dict[int, int]:
        degree = {i: 0 for i in range(self.node_count)}
        for edge in self._edges.values():
            degree[edge.u] += 1
            degree[edge.v] += 1
        return degree

    def _check_node(self, node: int) -> None:
        if not 0 <= node < self.node_count:
            raise IndexError(f"node index out of range: {node}")


def normalized_edge(u: int, v: int) -> tuple[int, int]:
    return (u, v) if u <= v else (v, u)


def multi_source_dijkstra(
    graph: WeightedGraph,
    sources: Iterable[tuple[int, float]],
    *,
    banned_edges: set[tuple[int, int]] | None = None,
    banned_nodes: set[int] | None = None,
    extra_edge_cost: dict[tuple[int, int], float] | None = None,
) -> tuple[list[float], list[int | None], list[int | None]]:
    """Run Dijkstra from multiple source nodes with initial distances."""

    blocked_edges = {normalized_edge(*e) for e in (banned_edges or set())}
    blocked_nodes = set(banned_nodes or set())
    extra = {normalized_edge(*k): float(v) for k, v in (extra_edge_cost or {}).items()}

    dist = [math.inf] * graph.node_count
    pred: list[int | None] = [None] * graph.node_count
    root: list[int | None] = [None] * graph.node_count
    heap: list[tuple[float, int]] = []

    for node, initial in sources:
        if node in blocked_nodes:
            continue
        if initial < dist[node]:
            dist[node] = float(initial)
            root[node] = node
            heapq.heappush(heap, (float(initial), node))

    while heap:
        current_dist, node = heapq.heappop(heap)
        if current_dist != dist[node]:
            continue
        for nbr, weight in graph.neighbors(node):
            edge_key = normalized_edge(node, nbr)
            if edge_key in blocked_edges or nbr in blocked_nodes:
                continue
            alt = current_dist + weight + extra.get(edge_key, 0.0)
            if alt < dist[nbr]:
                dist[nbr] = alt
                pred[nbr] = node
                root[nbr] = root[node]
                heapq.heappush(heap, (alt, nbr))

    return dist, pred, root


def shortest_path(pred: list[int | None], source: int, target: int) -> list[int]:
    """Reconstruct a path from predecessor pointers."""

    if source == target:
        return [source]
    path = [target]
    node = target
    while node != source:
        node = pred[node]
        if node is None:
            return []
        path.append(node)
    path.reverse()
    return path


@dataclass(frozen=True)
class RouteResult:
    delay_s: float
    path: list[int]
    access_source: int | None
    access_dest: int | None

    @property
    def reachable(self) -> bool:
        return math.isfinite(self.delay_s)


def min_delay_routes(
    graph: WeightedGraph,
    access_sets: list[list[int]],
    satellite_ecef_km: np.ndarray,
    ground_points_ecef_km: np.ndarray,
    *,
    od_pairs: Iterable[tuple[int, int]] | None = None,
    c_km_s: float = 299792.458,
) -> dict[tuple[int, int], RouteResult]:
    """Compute minimum end-to-end delay for ground OD pairs."""

    sat = np.asarray(satellite_ecef_km, dtype=float)
    ground = np.asarray(ground_points_ecef_km, dtype=float)
    if od_pairs is None:
        od_pairs = [(a, b) for a in range(len(ground)) for b in range(len(ground)) if a != b]
    pairs = list(od_pairs)
    by_source: dict[int, list[int]] = {}
    for a, b in pairs:
        by_source.setdefault(a, []).append(b)

    results: dict[tuple[int, int], RouteResult] = {}
    for source_ground, dests in by_source.items():
        source_access = access_sets[source_ground]
        if not source_access:
            for dest in dests:
                results[(source_ground, dest)] = RouteResult(math.inf, [], None, None)
            continue

        sources: list[tuple[int, float]] = []
        for sat_id in source_access:
            uplink = float(np.linalg.norm(sat[sat_id] - ground[source_ground]) / c_km_s)
            sources.append((sat_id, uplink))
        dist, pred, root = multi_source_dijkstra(graph, sources)

        for dest_ground in dests:
            best_delay = math.inf
            best_dest_sat: int | None = None
            for dest_sat in access_sets[dest_ground]:
                if not math.isfinite(dist[dest_sat]):
                    continue
                downlink = float(np.linalg.norm(sat[dest_sat] - ground[dest_ground]) / c_km_s)
                delay = dist[dest_sat] + downlink
                if delay < best_delay:
                    best_delay = delay
                    best_dest_sat = dest_sat

            if best_dest_sat is None:
                results[(source_ground, dest_ground)] = RouteResult(math.inf, [], None, None)
                continue
            source_sat = root[best_dest_sat]
            path = shortest_path(pred, int(source_sat), best_dest_sat) if source_sat is not None else []
            results[(source_ground, dest_ground)] = RouteResult(
                best_delay,
                path,
                int(source_sat) if source_sat is not None else None,
                best_dest_sat,
            )
    return results
