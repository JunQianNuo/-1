from __future__ import annotations

import numpy as np


def test_q2_area_sampler_is_bounded_and_reproducible():
    from common import make_rng
    from q2_validation import sample_area_uniform_region

    lat_a, lon_a = sample_area_uniform_region(100, make_rng(3))
    lat_b, lon_b = sample_area_uniform_region(100, make_rng(3))
    assert np.all((4 <= lat_a) & (lat_a <= 53))
    assert np.all((73 <= lon_a) & (lon_a <= 135))
    assert np.array_equal(lat_a, lat_b)
    assert np.array_equal(lon_a, lon_b)


def test_q2_monte_carlo_returns_requested_replications():
    from q2_constellation import ConstellationParams, CoverageConfig
    from q2_validation import run_q2_monte_carlo

    rows = run_q2_monte_carlo(
        ConstellationParams(planes=2, sats_per_plane=2, phase_factor=0, inclination_deg=50.0),
        CoverageConfig(),
        samples=8,
        time_samples=4,
        replicates=3,
        seed=11,
    )
    assert len(rows) == 3
    assert {row["replicate"] for row in rows} == {0, 1, 2}
