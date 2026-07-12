"""Shared helpers for standalone Q2/Q3/Q4 validation experiments."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Iterable, Mapping, Sequence

import numpy as np


VALIDATION_DIR = Path(__file__).resolve().parent


def bootstrap_problem_paths() -> None:
    """Make sibling question modules importable without editing their sources."""

    for name in ("问题二", "问题三", "问题四"):
        path = str(VALIDATION_DIR.parent / name)
        if path not in sys.path:
            sys.path.append(path)


def make_rng(seed: int) -> np.random.Generator:
    """Return a reproducible NumPy generator for one explicit seed."""

    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise ValueError("seed must be an integer")
    return np.random.default_rng(int(seed))


def percentile_interval(values: Sequence[float] | np.ndarray, level: float = 0.95) -> tuple[float, float]:
    """Return the central finite percentile interval."""

    data = np.asarray(values, dtype=float)
    if data.ndim != 1 or data.size == 0 or not np.all(np.isfinite(data)):
        raise ValueError("values must be a nonempty finite vector")
    if not 0.0 < level < 1.0:
        raise ValueError("level must lie in (0, 1)")
    alpha = (1.0 - float(level)) / 2.0
    low, high = np.quantile(data, [alpha, 1.0 - alpha])
    return float(low), float(high)


def _json_default(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"cannot encode {type(value).__name__}")


def write_json(path: str | Path, value: Mapping[str, object]) -> None:
    """Write deterministic UTF-8 JSON, creating parent directories."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def write_rows_csv(path: str | Path, rows: Iterable[Mapping[str, object]], fieldnames: Sequence[str]) -> None:
    """Write rows to a UTF-8 CSV with an explicit stable schema."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
