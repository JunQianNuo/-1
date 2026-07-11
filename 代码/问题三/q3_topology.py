"""ISL topology construction and validation helpers for Problem 3."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import numpy as np

from q3_config import ConstellationParams, Q3Config
from q3_routing import WeightedGraph


@dataclass(frozen=True)
class _KDNode:
    index: int
    axis: int
    left: "_KDNode | None" = None
    right: "_KDNode | None" = None


class cKDTree:
    """Small cKDTree-compatible 3D nearest-neighbor index.

    The project only needs ``query(points, k=1)`` for tens of satellites per
    plane.  A local KD-tree avoids making topology construction depend on a
    heavy import path while preserving the same call shape as
    ``scipy.spatial.cKDTree``.
    """

    def __init__(self, data: np.ndarray):
        points = np.asarray(data, dtype=float)
        if points.ndim != 2:
            raise ValueError("KDTree data must be a 2D array")
        self.data = points
        self._root = self._build(list(range(points.shape[0])), depth=0)

    def query(self, points: np.ndarray, k: int = 1) -> tuple[np.ndarray, np.ndarray]:
        if k != 1:
            raise NotImplementedError("this lightweight KDTree only supports k=1")
        query_points = np.asarray(points, dtype=float)
        if query_points.ndim == 1:
            dist, idx = self._query_one(query_points)
            return np.asarray(dist), np.asarray(idx)
        distances: list[float] = []
        indices: list[int] = []
        for point in query_points:
            dist, idx = self._query_one(point)
            distances.append(dist)
            indices.append(idx)
        return np.asarray(distances, dtype=float), np.asarray(indices, dtype=int)

    def _build(self, indices: list[int], depth: int) -> _KDNode | None:
        if not indices:
            return None
        axis = depth % self.data.shape[1]
        indices.sort(key=lambda idx: self.data[idx, axis])
        mid = len(indices) // 2
        return _KDNode(
            index=indices[mid],
            axis=axis,
            left=self._build(indices[:mid], depth + 1),
            right=self._build(indices[mid + 1 :], depth + 1),
        )

    def _query_one(self, point: np.ndarray) -> tuple[float, int]:
        best_dist2 = math.inf
        best_idx = -1

        def visit(node: _KDNode | None) -> None:
            nonlocal best_dist2, best_idx
            if node is None:
                return
            diff_vec = point - self.data[node.index]
            dist2 = float(diff_vec @ diff_vec)
            if dist2 < best_dist2:
                best_dist2 = dist2
                best_idx = node.index

            axis = node.axis
            split = float(point[axis] - self.data[node.index, axis])
            near = node.left if split < 0 else node.right
            far = node.right if split < 0 else node.left
            visit(near)
            if split * split < best_dist2:
                visit(far)

        visit(self._root)
        return math.sqrt(best_dist2), best_idx


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
            current_ids = [satellite_id(m, n, N) for n in range(N)]
            current_pos = positions[current_ids]
            tree = cKDTree(next_pos)
            _distances, nearest_indices = tree.query(current_pos, k=1)
            for n, nearest_idx in enumerate(np.asarray(nearest_indices, dtype=int)):
                u = satellite_id(m, n, N)
                v = next_ids[int(nearest_idx)]
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
