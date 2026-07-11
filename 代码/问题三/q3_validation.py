"""Validation helpers for Problem 3 outputs."""

from __future__ import annotations

from q3_routing import WeightedGraph
from q3_topology import topology_summary


def validate_topology(graph: WeightedGraph, *, max_degree: int = 4, max_distance_km: float | None = None) -> list[str]:
    """Return human-readable validation issues; empty list means pass."""

    issues: list[str] = []
    summary = topology_summary(graph)
    if summary["max_degree"] > max_degree:
        issues.append(f"max degree {summary['max_degree']} exceeds {max_degree}")
    if max_distance_km is not None and summary["max_link_distance_km"] > max_distance_km + 1e-9:
        issues.append("link distance exceeds threshold")
    if any(edge.weight_s <= 0 for edge in graph.edges):
        issues.append("non-positive edge weight found")
    return issues
