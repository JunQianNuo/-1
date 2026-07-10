import math
import unittest
from pathlib import Path

import numpy as np

import q2_constellation as q2


class GeometryTests(unittest.TestCase):
    def test_ground_unit_vectors_match_axes(self):
        vec = q2.ground_unit_vectors(
            np.array([0.0, 0.0, 90.0]),
            np.array([0.0, 90.0, 123.0]),
        )

        np.testing.assert_allclose(vec[0], [1.0, 0.0, 0.0], atol=1e-12)
        np.testing.assert_allclose(vec[1], [0.0, 1.0, 0.0], atol=1e-12)
        np.testing.assert_allclose(vec[2], [0.0, 0.0, 1.0], atol=1e-12)

    def test_single_satellite_covers_subsatellite_point_only_nearby_points(self):
        config = q2.CoverageConfig()
        params = q2.ConstellationParams(
            planes=1,
            sats_per_plane=1,
            phase_factor=0,
            inclination_deg=0.0,
            raan0_deg=0.0,
            u0_deg=0.0,
        )
        result = q2.evaluate_constellation(
            params,
            lat_deg=np.array([0.0, 0.0]),
            lon_deg=np.array([0.0, 10.0]),
            times_s=np.array([0.0]),
            config=config,
        )

        self.assertEqual(result.counts.shape, (2, 1))
        self.assertEqual(int(result.counts[0, 0]), 1)
        self.assertEqual(int(result.counts[1, 0]), 0)
        self.assertEqual(result.c_min, 0)
        self.assertAlmostEqual(result.coverage_rate_q1, 0.5)

    def test_latlon_grid_stays_inside_region_and_includes_bounds(self):
        lat, lon = q2.make_latlon_grid(
            lat_min_deg=0.0,
            lat_max_deg=10.0,
            lon_min_deg=100.0,
            lon_max_deg=110.0,
            step_deg=6.0,
        )

        self.assertGreaterEqual(float(lat.min()), 0.0)
        self.assertLessEqual(float(lat.max()), 10.0)
        self.assertGreaterEqual(float(lon.min()), 100.0)
        self.assertLessEqual(float(lon.max()), 110.0)
        self.assertIn(10.0, set(lat.tolist()))
        self.assertIn(110.0, set(lon.tolist()))

    def test_time_grid_stays_within_duration_and_includes_endpoint(self):
        times = q2.make_time_grid(duration_s=10.0, step_s=6.0)

        self.assertGreaterEqual(float(times.min()), 0.0)
        self.assertLessEqual(float(times.max()), 10.0)
        self.assertIn(10.0, set(times.tolist()))


class MetricTests(unittest.TestCase):
    def test_metrics_for_known_coverage_counts(self):
        counts = np.array(
            [
                [1, 1, 0, 0],
                [2, 2, 2, 2],
            ],
            dtype=np.int16,
        )
        weights = np.array([1.0, 3.0])
        metrics = q2.compute_metrics(counts, weights=weights, dt_s=60.0)

        # Weighted single-coverage rate:
        # time 0,1: both covered => 1.0 each
        # time 2,3: only second point covered => 3/4 each
        expected_c1 = (1.0 + 1.0 + 0.75 + 0.75) / 4.0
        self.assertAlmostEqual(metrics.coverage_rate_q1, expected_c1)
        self.assertEqual(metrics.c_min, 0)
        self.assertEqual(metrics.max_gap_s, 120.0)
        self.assertAlmostEqual(metrics.strict_double_time_rate, 0.0)

    def test_result_summary_includes_total_satellites(self):
        params = q2.ConstellationParams(
            planes=2,
            sats_per_plane=3,
            phase_factor=0,
            inclination_deg=50.0,
        )
        result = q2.evaluate_constellation(
            params,
            lat_deg=np.array([0.0]),
            lon_deg=np.array([0.0]),
            times_s=np.array([0.0]),
        )

        summary = q2.result_summary_dict(result)

        self.assertEqual(summary["params"]["total_satellites"], 6)


class SearchTests(unittest.TestCase):
    def test_factor_pairs_are_exact_and_ordered(self):
        self.assertEqual(q2.factor_pairs(12), [(1, 12), (2, 6), (3, 4), (4, 3), (6, 2), (12, 1)])

    def test_phase_grid_uses_fundamental_intervals(self):
        omega, u = q2.phase_grid(planes=6, sats_per_plane=10, phase_resolution_deg=2.0)

        self.assertGreaterEqual(len(omega), 4)
        self.assertGreaterEqual(len(u), 4)
        self.assertTrue(np.all(omega >= 0.0))
        self.assertTrue(np.all(u >= 0.0))
        self.assertTrue(np.all(omega < 360.0 / 6.0))
        self.assertTrue(np.all(u < 360.0 / 10.0))
        self.assertLessEqual(float(np.diff(omega).max(initial=0.0)), 2.0 + 1e-12)
        self.assertLessEqual(float(np.diff(u).max(initial=0.0)), 2.0 + 1e-12)

    def test_single_coverage_search_records_candidates_and_first_feasible(self):
        search = q2.search_single_coverage(
            lat_deg=np.array([0.0]),
            lon_deg=np.array([0.0]),
            times_s=np.array([0.0]),
            start_total=1,
            stop_total=1,
            inclinations_deg=[0.0],
            phase_resolution_deg=360.0,
            stop_on_feasible=True,
        )

        self.assertGreater(search.evaluated_count, 0)
        self.assertGreater(len(search.records), 0)
        self.assertIsNotNone(search.best_result)
        self.assertIsNotNone(search.first_feasible)
        self.assertGreaterEqual(search.first_feasible.c_min, 1)

        first_record = search.records[0]
        for key in ["total_satellites", "planes", "sats_per_plane", "C1", "c_min"]:
            self.assertIn(key, first_record)


class DoubleCoverageTests(unittest.TestCase):
    def test_double_coverage_search_runs_and_returns_structure(self):
        """Smoke: double-coverage search with minimal settings."""
        search = q2.search_double_coverage(
            lat_deg=np.array([0.0]),
            lon_deg=np.array([0.0]),
            times_s=np.array([0.0, 60.0]),
            start_total=1,
            stop_total=1,
            inclinations_deg=[0.0],
            phase_resolution_deg=360.0,
            stop_on_feasible=False,
        )
        self.assertGreater(search.evaluated_count, 0)
        self.assertIsNotNone(search.best_result)
        self.assertGreaterEqual(search.best_result.strict_double_time_rate, 0.0)

    def test_double_coverage_score_ranks_feasible_above_infeasible(self):
        """A feasible candidate scores above any infeasible one."""

        feasible = q2.EvaluationResult(
            params=q2.ConstellationParams(2, 3, 0, 50),
            counts=np.ones((2, 2), dtype=np.int16) * 3,
            lat_deg=np.array([0.0, 0.0]),
            lon_deg=np.array([0.0, 1.0]),
            times_s=np.array([0.0, 1.0]),
            weights=np.array([0.5, 0.5]),
            metrics=q2.CoverageMetrics(
                coverage_rate_q1=1.0,
                coverage_rate_q2=1.0,
                avg_multiplicity=3.0,
                c_min=3,
                max_gap_s=0.0,
                strict_double_time_rate=1.0,
            ),
        )
        infeasible = q2.EvaluationResult(
            params=q2.ConstellationParams(1, 1, 0, 50),
            counts=np.array([[0]], dtype=np.int16),
            lat_deg=np.array([0.0]),
            lon_deg=np.array([0.0]),
            times_s=np.array([0.0]),
            weights=np.array([1.0]),
            metrics=q2.CoverageMetrics(
                coverage_rate_q1=0.0,
                coverage_rate_q2=0.0,
                avg_multiplicity=0.0,
                c_min=0,
                max_gap_s=10.0,
                strict_double_time_rate=0.0,
            ),
        )

        self.assertGreater(
            q2._double_coverage_score(feasible),
            q2._double_coverage_score(infeasible),
        )


if __name__ == "__main__":
    unittest.main()
