"""Pure saturation-decision module for the Q3 performance-saturation search.

This module contains no I/O and no routing. It receives one best
high-fidelity, coverage-feasible observation per completed satellite-count
layer (sorted by ``stars``) and decides whether the first complete forward
window has saturated according to the two approved marginal-gain limits.

Definitions (fixed for this project):

* ``window_gain`` at S_i = (max ``p30_all`` over observations whose ``stars``
  lie in ``[S_i, S_i + forward_window_s]``) minus the ``p30_all`` of the
  observation at S_i.
* ``gain_per_100_stars`` = ``window_gain / (forward_window_s / 100.0)``.
* A window at S_i is *complete* iff some later observation has
  ``stars >= S_i + forward_window_s``.
* Saturation uses ``<=`` (equality counts as saturated): the first S_i whose
  complete window satisfies BOTH ``window_gain <= max_gain`` AND
  ``gain_per_100_stars <= max_gain_per_100`` is selected.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class SaturationObservation:
    """One best high-fidelity, coverage-feasible record for a satellite layer."""

    stars: int
    p30_all: float
    candidate_key: str
    p30_reachable: float
    c1: float
    c2: float
    max_delay_s: Optional[float]


@dataclass(frozen=True)
class SaturationDecision:
    """Outcome of the forward-window saturation test."""

    status: str
    selected: Optional[SaturationObservation]
    window_end_stars: Optional[int]
    window_max_p30_all: Optional[float]
    window_gain: Optional[float]
    gain_per_100_stars: Optional[float]


def _leq(value: float, limit: float) -> bool:
    """Tolerance-aware ``<=`` so the approved boundary (e.g. an exact one
    percentage-point gain that lands on ``0.010000000000000009`` after float
    subtraction) counts as satisfying the limit, matching "equality counts as
    saturated"."""
    return value <= limit or math.isclose(value, limit, rel_tol=1e-9, abs_tol=1e-12)


def _validate(observations: List[SaturationObservation]) -> None:
    """Raise ``ValueError`` if any numeric field is non-finite or ``stars`` is
    not strictly increasing across the observation list."""
    numeric_fields = ("stars", "p30_all", "p30_reachable", "c1", "c2")
    previous_stars: Optional[float] = None
    for obs in observations:
        for name in numeric_fields:
            value = getattr(obs, name)
            if not math.isfinite(value):
                raise ValueError(
                    f"non-finite value for field '{name}': {value!r}"
                )
        if obs.max_delay_s is not None and not math.isfinite(obs.max_delay_s):
            raise ValueError(
                f"non-finite value for field 'max_delay_s': {obs.max_delay_s!r}"
            )
        if previous_stars is not None and obs.stars <= previous_stars:
            raise ValueError(
                "stars must be strictly increasing across observations; "
                f"{obs.stars!r} does not exceed {previous_stars!r}"
            )
        previous_stars = obs.stars


def first_saturation_decision(
    observations: List[SaturationObservation],
    *,
    forward_window_s: int = 200,
    max_gain: float = 0.01,
    max_gain_per_100: float = 0.005,
) -> SaturationDecision:
    """Return the saturation decision for the first complete forward window.

    Scans layers in increasing ``stars`` order. For each S_i that has a
    *complete* forward window, computes ``window_gain`` and
    ``gain_per_100_stars`` and returns ``"saturated"`` at the first S_i whose
    window satisfies both ``<=`` limits. If no complete window ever exists the
    status is ``"insufficient_horizon"``; if complete windows exist but all
    fail the limits the status is ``"not_saturated"``.
    """
    _validate(observations)

    gain_denominator = forward_window_s / 100.0
    any_complete_window = False

    for index, base in enumerate(observations):
        window_end_target = base.stars + forward_window_s

        # A window is complete iff some later observation reaches the horizon.
        if not any(
            later.stars >= window_end_target
            for later in observations[index + 1 :]
        ):
            continue

        any_complete_window = True

        window_members = [
            obs
            for obs in observations
            if base.stars <= obs.stars <= window_end_target
        ]
        window_max_p30_all = max(obs.p30_all for obs in window_members)
        window_gain = window_max_p30_all - base.p30_all
        gain_per_100_stars = window_gain / gain_denominator

        if _leq(window_gain, max_gain) and _leq(gain_per_100_stars, max_gain_per_100):
            return SaturationDecision(
                status="saturated",
                selected=base,
                window_end_stars=window_end_target,
                window_max_p30_all=window_max_p30_all,
                window_gain=window_gain,
                gain_per_100_stars=gain_per_100_stars,
            )

    if not any_complete_window:
        return SaturationDecision(
            status="insufficient_horizon",
            selected=None,
            window_end_stars=None,
            window_max_p30_all=None,
            window_gain=None,
            gain_per_100_stars=None,
        )

    return SaturationDecision(
        status="not_saturated",
        selected=None,
        window_end_stars=None,
        window_max_p30_all=None,
        window_gain=None,
        gain_per_100_stars=None,
    )
