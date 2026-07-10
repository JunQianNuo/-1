from __future__ import annotations

import math
import unittest

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as fast
from q2_adaptive_verify import SpaceTimeBox, conservative_space_radius_rad, subdivide_space_time_box
from q2_coverage_margin import q_fold_margins_at_points
from q2_kdtree_coverage import (
    coverage_counts_and_margins_local,
    critical_points_at_time_kdtree,
    neighbor_pairs_kdtree,
)
from q2_search_space import fair_candidate_params_for_total, group_params_by_structure


class SearchSpaceTests(unittest.TestCase):
    def test_equal_budget_per_structure(self) -> None:
        samples = list(
            fair_candidate_params_for_total(
                12,
                samples_per_structure=3,
                inclination_min_deg=49.0,
                inclination_max_deg=60.0,
                seed=7,
            )
        )
        grouped = group_params_by_structure(samples)
        self.assertTrue(grouped)
        self.assertEqual({len(values) for values in grouped.values()}, {3})


class KDTreeCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(42)
        satellites = rng.normal(size=(30, 3))
        points = rng.normal(size=(20, 3))
        self.satellites = satellites / np.linalg.norm(satellites, axis=1, keepdims=True)
        self.points = points / np.linalg.norm(points, axis=1, keepdims=True)
        self.theta = math.radians(25.0)

    def test_neighbor_pairs_match_dense_method(self) -> None:
        expected = set(fast.neighbor_pairs_by_dot(self.satellites, 2.0 * self.theta))
        actual = set(neighbor_pairs_kdtree(self.satellites, 2.0 * self.theta))
        self.assertEqual(actual, expected)

    def test_local_counts_and_margins_match_dense_q1_q2(self) -> None:
        for q_value in (1, 2):
            dense = q_fold_margins_at_points(
                self.satellites,
                self.points,
                self.theta,
                q=q_value,
            )
            local = coverage_counts_and_margins_local(
                self.satellites,
                self.points,
                self.theta,
                q=q_value,
            )
            np.testing.assert_array_equal(local.counts, dense.counts)
            np.testing.assert_allclose(local.margins, dense.margins, atol=1e-12)

    def test_region_corners_are_present(self) -> None:
        region = fast.LatLonRegion()
        points = critical_points_at_time_kdtree(
            self.satellites,
            self.theta,
            region,
            include_region_boundary=False,
            include_representatives=False,
        )
        corners = fast.region_corner_points(region)
        for corner in corners:
            self.assertLess(np.min(np.linalg.norm(points - corner, axis=1)), 1e-9)


class AdaptiveVerifierTests(unittest.TestCase):
    def test_space_radius_is_conservative_positive(self) -> None:
        box = SpaceTimeBox(4.0, 6.0, 73.0, 77.0, 0.0, 10.0)
        self.assertAlmostEqual(conservative_space_radius_rad(box), math.radians(3.0))

    def test_subdivision_preserves_domain(self) -> None:
        box = SpaceTimeBox(4.0, 53.0, 73.0, 135.0, 0.0, 3600.0)
        left, right = subdivide_space_time_box(box)
        self.assertEqual(left.depth, 1)
        self.assertEqual(right.depth, 1)
        # The selected split must be contiguous in one dimension.
        contiguous = (
            math.isclose(left.lat_max_deg, right.lat_min_deg)
            or math.isclose(left.lon_max_deg, right.lon_min_deg)
            or math.isclose(left.time_max_s, right.time_min_s)
        )
        self.assertTrue(contiguous)


if __name__ == "__main__":
    unittest.main()
