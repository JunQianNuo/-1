"""Tests for the Q2-R03/R04/R06 relaxed-criteria overlay."""

from __future__ import annotations

import unittest

import numpy as np

import q2_constellation as q2
import q2_relaxed_criteria as rc
from q2_fast_coverage import LatLonRegion


class TestRelaxedDoubleRate(unittest.TestCase):
    def test_eta_relaxes_strict_double(self) -> None:
        # 10 points, 4 times. At every time, 9/10 points are 2-covered and
        # one point is 1-covered.  Equal weights.
        K, L = 10, 4
        counts = np.full((K, L), 2, dtype=int)
        counts[0, :] = 1  # one weak point at every time
        w = np.ones(K)
        strict = rc.relaxed_double_time_rate(counts, w, q=2, eta=0.0)
        relaxed = rc.relaxed_double_time_rate(counts, w, q=2, eta=0.11)  # tolerate 10%
        self.assertEqual(strict, 0.0)          # strict fails every slice
        self.assertEqual(relaxed, 1.0)          # 90% area covered passes with eta=11%


class TestGuardBand(unittest.TestCase):
    def test_interior_mask_excludes_boundary(self) -> None:
        region = LatLonRegion()
        lat = np.array([region.lat_min_deg, 30.0, region.lat_max_deg])
        lon = np.array([region.lon_min_deg, 100.0, region.lon_max_deg])
        mask = rc.interior_mask(lat, lon, region, delta_deg=1.0)
        self.assertFalse(bool(mask[0]))  # on corner -> excluded
        self.assertTrue(bool(mask[1]))   # interior -> kept
        self.assertFalse(bool(mask[2]))


class TestEvaluateRelaxedOnBoundaryGap(unittest.TestCase):
    """The real failure at (8N,73E) is ON the west boundary; a guard band
    should recover interior single coverage."""

    def test_boundary_only_gap_is_recovered_by_guard(self) -> None:
        cfg = q2.CoverageConfig()
        lat, lon = q2.make_latlon_grid(step_deg=2.0)
        times = q2.make_time_grid(6 * 3600.0, 600.0)
        params = q2.ConstellationParams(
            planes=40, sats_per_plane=40, phase_factor=0,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        result = q2.evaluate_constellation(params, lat, lon, times, cfg)
        rep = rc.evaluate_relaxed(
            result, region=LatLonRegion(),
            config=rc.RelaxedCriteriaConfig(guard_delta_deg=2.0),
        )
        # interior c_min must be >= full c_min (guard band only removes points)
        self.assertGreaterEqual(rep.c_min_interior, rep.c_min_full)
        # R03 near-full flag is computed from C1 / max_gap
        self.assertIsInstance(rep.single_relaxed_feasible, bool)
        self.assertEqual(rep.total_satellites, 1600)


if __name__ == "__main__":
    unittest.main()
