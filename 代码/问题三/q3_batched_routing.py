"""Batched ground-to-ground shortest paths on an augmented sparse graph."""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from q3_routing import WeightedGraph


def build_augmented_csr(
    graph: WeightedGraph,
    access_sets: list[list[int]],
    satellite_ecef_km: np.ndarray,
    ground_points_ecef_km: np.ndarray,
    *,
    c_km_s: float = 299792.458,
) -> tuple[csr_matrix, np.ndarray, np.ndarray]:
    """Build directed satellite, ground-source, and ground-sink graph copies."""

    satellite = np.asarray(satellite_ecef_km, dtype=float)
    ground = np.asarray(ground_points_ecef_km, dtype=float)
    satellite_count = graph.node_count

    if satellite.shape != (satellite_count, 3):
        raise ValueError(
            f"satellite_ecef_km must have shape ({satellite_count}, 3)"
        )
    if ground.ndim != 2 or ground.shape[1] != 3:
        raise ValueError("ground_points_ecef_km must have shape (J, 3)")

    ground_count = ground.shape[0]
    if len(access_sets) != ground_count:
        raise ValueError("access_sets length must match the number of ground points")
    try:
        speed = float(c_km_s)
    except (TypeError, ValueError) as exc:
        raise ValueError("c_km_s must be finite and positive") from exc
    if not np.isfinite(speed) or speed <= 0.0:
        raise ValueError("c_km_s must be finite and positive")

    rows: list[int] = []
    columns: list[int] = []
    weights: list[float] = []

    for edge in graph.edges:
        rows.extend((edge.u, edge.v))
        columns.extend((edge.v, edge.u))
        weights.extend((edge.weight_s, edge.weight_s))

    source_nodes = np.arange(
        satellite_count, satellite_count + ground_count, dtype=np.int64
    )
    sink_nodes = np.arange(
        satellite_count + ground_count,
        satellite_count + 2 * ground_count,
        dtype=np.int64,
    )
    for ground_id, access in enumerate(access_sets):
        validated_access: set[int] = set()
        for satellite_id in access:
            if not isinstance(satellite_id, (int, np.integer)):
                raise IndexError(f"satellite index out of range: {satellite_id}")
            satellite_id = int(satellite_id)
            if not 0 <= satellite_id < satellite_count:
                raise IndexError(f"satellite index out of range: {satellite_id}")
            validated_access.add(satellite_id)

        for satellite_id in validated_access:
            link_delay = float(
                np.linalg.norm(satellite[satellite_id] - ground[ground_id]) / speed
            )
            rows.extend((int(source_nodes[ground_id]), satellite_id))
            columns.extend((satellite_id, int(sink_nodes[ground_id])))
            weights.extend((link_delay, link_delay))

    node_count = satellite_count + 2 * ground_count
    matrix = csr_matrix(
        (np.asarray(weights, dtype=float), (rows, columns)),
        shape=(node_count, node_count),
        dtype=float,
    )
    return matrix, source_nodes, sink_nodes


def batched_ground_delay_matrix(
    graph: WeightedGraph,
    access_sets: list[list[int]],
    satellite_ecef_km: np.ndarray,
    ground_points_ecef_km: np.ndarray,
    *,
    c_km_s: float = 299792.458,
) -> np.ndarray:
    """Return all ground-to-ground minimum delays using one compiled Dijkstra call."""

    matrix, source_nodes, sink_nodes = build_augmented_csr(
        graph,
        access_sets,
        satellite_ecef_km,
        ground_points_ecef_km,
        c_km_s=c_km_s,
    )
    distances = dijkstra(
        matrix,
        directed=True,
        indices=source_nodes,
        return_predecessors=False,
    )
    return np.asarray(distances[:, sink_nodes], dtype=float)
