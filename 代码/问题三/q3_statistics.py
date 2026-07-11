"""Delay statistics for Problem 3 routing samples."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def delay_statistics(delays_s: Iterable[float], *, delay_limit_s: float | None = None) -> dict[str, float | int | None]:
    values = np.asarray(list(delays_s), dtype=float)
    count = int(values.size)
    finite = values[np.isfinite(values)]
    reachable = int(finite.size)
    stats: dict[str, float | int | None] = {
        "count": count,
        "reachable_count": reachable,
        "unreachable_count": count - reachable,
        "unreachable_rate": float((count - reachable) / count) if count else 0.0,
        "mean_s": None,
        "max_s": None,
        "p50_s": None,
        "p90_s": None,
        "p95_s": None,
        "p99_s": None,
        "within_limit_rate": None,
    }
    if reachable:
        stats.update(
            {
                "mean_s": float(np.mean(finite)),
                "max_s": float(np.max(finite)),
                "p50_s": float(np.percentile(finite, 50)),
                "p90_s": float(np.percentile(finite, 90)),
                "p95_s": float(np.percentile(finite, 95)),
                "p99_s": float(np.percentile(finite, 99)),
            }
        )
    if delay_limit_s is not None:
        stats["within_limit_rate"] = float(np.count_nonzero(values <= delay_limit_s) / count) if count else math.nan
    return stats
