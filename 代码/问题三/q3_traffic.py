"""Traffic demand and baseline load calculations for Problem 3."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from q3_routing import normalized_edge


@dataclass(frozen=True)
class LoadResult:
    access_load_gbps: dict[int, float] = field(default_factory=dict)
    relay_load_gbps: dict[int, float] = field(default_factory=dict)
    link_load_gbps: dict[tuple[int, int], float] = field(default_factory=dict)


def uniform_od_demand(
    ground_point_count: int,
    *,
    total_flow_gbps: float,
    weights: np.ndarray | None = None,
    ordered: bool = True,
    exclude_self: bool = True,
) -> dict[tuple[int, int], float]:
    """Construct a normalized uniform OD demand matrix."""

    if ground_point_count <= 0:
        raise ValueError("ground_point_count must be positive")
    if total_flow_gbps < 0:
        raise ValueError("total_flow_gbps must be non-negative")
    if weights is None:
        w = np.full(ground_point_count, 1.0 / ground_point_count)
    else:
        w = np.asarray(weights, dtype=float)
        if w.shape != (ground_point_count,):
            raise ValueError("weights shape mismatch")
        if np.any(w < 0) or w.sum() <= 0:
            raise ValueError("weights must be non-negative with positive sum")
        w = w / w.sum()

    pairs: list[tuple[int, int]] = []
    for a in range(ground_point_count):
        for b in range(ground_point_count):
            if exclude_self and a == b:
                continue
            if not ordered and b <= a:
                continue
            pairs.append((a, b))
    denom = sum(float(w[a] * w[b]) for a, b in pairs)
    if denom <= 0:
        raise ValueError("OD denominator is zero")
    return {(a, b): float(total_flow_gbps * w[a] * w[b] / denom) for a, b in pairs}


def baseline_loads(
    paths: dict[tuple[int, int], list[int]],
    demand_gbps: dict[tuple[int, int], float],
    *,
    satellite_count: int,
) -> LoadResult:
    """Accumulate access, relay, and ISL loads for all-on-shortest-path routing."""

    access = {s: 0.0 for s in range(satellite_count)}
    relay = {s: 0.0 for s in range(satellite_count)}
    link: dict[tuple[int, int], float] = {}

    for od, flow in demand_gbps.items():
        path = paths.get(od, [])
        if not path or flow <= 0:
            continue
        access[path[0]] += float(flow)
        access[path[-1]] += float(flow)
        for node in path[1:-1]:
            relay[node] += float(flow)
        for u, v in zip(path, path[1:]):
            key = normalized_edge(u, v)
            link[key] = link.get(key, 0.0) + float(flow)
    return LoadResult(access, relay, link)
