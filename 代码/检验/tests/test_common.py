from __future__ import annotations

import pytest


def test_percentile_interval_and_seed_are_deterministic():
    from common import make_rng, percentile_interval

    assert percentile_interval([0, 1, 2, 3, 4]) == pytest.approx((0.1, 3.9))
    assert make_rng(7).integers(0, 1000) == make_rng(7).integers(0, 1000)
