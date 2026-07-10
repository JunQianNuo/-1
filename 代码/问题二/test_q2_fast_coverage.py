import math
import unittest

import numpy as np

import q2_fast_coverage as fast
from q2_constellation import ConstellationParams, CoverageConfig


class FastCoverageGeometryTests(unittest.TestCase):
    def test_neighbor_pairs_by_dot_keeps_only_close_pairs(self):
        vectors = np.array(
            [
                [1.0, 0.0, 0.0],
                [math.cos(math.radians(5.0)), math.sin(math.radians(5.0)), 0.0],
                [math.cos(math.radians(30.0)), math.sin(math.radians(30.0)), 0.0],
            ],
            dtype=float,
        )

        pairs = fast.neighbor_pairs_by_dot(vectors, math.radians(10.0), block_size=2)

        self.assertEqual(pairs, [(0, 1)])

    def test_small_circle_intersections_satisfy_both_coverage_boundaries(self):
        center_a = np.array([1.0, 0.0, 0.0])
        center_b = np.array(
            [math.cos(math.radians(60.0)), math.sin(math.radians(60.0)), 0.0],
            dtype=float,
        )
        radius = math.radians(45.0)

        points = fast.small_circle_intersections(center_a, center_b, radius)

        self.assertEqual(points.shape, (2, 3))
        np.testing.assert_allclose(np.linalg.norm(points, axis=1), 1.0, atol=1e-12)
        np.testing.assert_allclose(points @ center_a, math.cos(radius), atol=1e-12)
        np.testing.assert_allclose(points @ center_b, math.cos(radius), atol=1e-12)
        self.assertAlmostEqual(points[0, 2], -points[1, 2], places=12)

    def test_points_in_latlon_box_filters_region(self):
        region = fast.LatLonRegion(
            lat_min_deg=4.0,
            lat_max_deg=53.0,
            lon_min_deg=73.0,
            lon_max_deg=135.0,
        )
        points = np.vstack(
            [
                fast.latlon_to_unit(30.0, 100.0),
                fast.latlon_to_unit(60.0, 100.0),
                fast.latlon_to_unit(30.0, 150.0),
            ]
        )

        mask = fast.points_in_latlon_box(points, region)

        self.assertEqual(mask.tolist(), [True, False, False])

    def test_critical_points_at_time_includes_circle_intersections_and_corners(self):
        satellites = np.vstack(
            [
                fast.latlon_to_unit(0.0, 0.0),
                fast.latlon_to_unit(0.0, 60.0),
            ]
        )
        radius = math.radians(45.0)
        region = fast.LatLonRegion(
            lat_min_deg=-80.0,
            lat_max_deg=80.0,
            lon_min_deg=-120.0,
            lon_max_deg=120.0,
        )

        points = fast.critical_points_at_time(
            satellites,
            radius,
            region,
            block_size=1,
            include_region_boundary=False,
            include_representatives=False,
        )
        intersections = fast.small_circle_intersections(satellites[0], satellites[1], radius)

        self.assertEqual(points.shape[1], 3)
        np.testing.assert_allclose(np.linalg.norm(points, axis=1), 1.0, atol=1e-12)
        self.assertEqual(len(points), 6)
        for intersection in intersections:
            self.assertGreater(np.max(points @ intersection), 1.0 - 1e-12)

    def test_critical_points_at_time_filters_intersections_outside_region(self):
        satellites = np.vstack(
            [
                fast.latlon_to_unit(0.0, 0.0),
                fast.latlon_to_unit(0.0, 60.0),
            ]
        )
        radius = math.radians(45.0)
        region = fast.LatLonRegion(
            lat_min_deg=-10.0,
            lat_max_deg=10.0,
            lon_min_deg=-10.0,
            lon_max_deg=70.0,
        )

        points = fast.critical_points_at_time(
            satellites,
            radius,
            region,
            block_size=1,
            include_region_boundary=False,
            include_representatives=False,
        )

        self.assertEqual(len(points), 4)
        lat, _ = fast.unit_to_latlon(points)
        self.assertTrue(np.all(np.abs(lat) <= 10.0 + 1e-10))

    def test_critical_points_at_time_includes_circle_boundary_intersections(self):
        satellites = np.vstack([fast.latlon_to_unit(0.0, 0.0)])
        radius = math.radians(30.0)
        region = fast.LatLonRegion(
            lat_min_deg=-10.0,
            lat_max_deg=10.0,
            lon_min_deg=-40.0,
            lon_max_deg=40.0,
        )

        points = fast.critical_points_at_time(
            satellites,
            radius,
            region,
            include_representatives=False,
        )
        lat, lon = fast.unit_to_latlon(points)
        dots = points @ satellites[0]
        on_lat_edge = np.isclose(np.abs(lat), 10.0, atol=1e-10)
        on_boundary_circle = np.isclose(dots, math.cos(radius), atol=1e-10)

        self.assertEqual(len(points), 8)
        self.assertEqual(int(np.count_nonzero(on_lat_edge & on_boundary_circle)), 4)
        self.assertTrue(np.all(lon >= -40.0 - 1e-10))
        self.assertTrue(np.all(lon <= 40.0 + 1e-10))

    def test_coverage_arc_representative_points_sample_both_sides_of_boundary(self):
        center = fast.latlon_to_unit(0.0, 0.0)
        radius = math.radians(30.0)
        boundary_vertices = np.vstack(
            [
                fast.latlon_to_unit(30.0, 0.0),
                fast.latlon_to_unit(0.0, 30.0),
                fast.latlon_to_unit(-30.0, 0.0),
                fast.latlon_to_unit(0.0, -30.0),
            ]
        )

        points = fast.coverage_arc_representative_points(
            center,
            boundary_vertices,
            radius,
            offset_rad=1e-4,
        )
        dots = points @ center

        self.assertEqual(len(points), 8)
        np.testing.assert_allclose(np.linalg.norm(points, axis=1), 1.0, atol=1e-12)
        self.assertEqual(int(np.count_nonzero(dots > math.cos(radius))), 4)
        self.assertEqual(int(np.count_nonzero(dots < math.cos(radius))), 4)

    def test_critical_points_at_time_adds_representative_points(self):
        satellites = np.vstack([fast.latlon_to_unit(0.0, 0.0)])
        radius = math.radians(30.0)
        region = fast.LatLonRegion(
            lat_min_deg=-10.0,
            lat_max_deg=10.0,
            lon_min_deg=-40.0,
            lon_max_deg=40.0,
        )

        vertices_only = fast.critical_points_at_time(
            satellites,
            radius,
            region,
            include_representatives=False,
        )
        with_representatives = fast.critical_points_at_time(
            satellites,
            radius,
            region,
            include_representatives=True,
        )

        self.assertGreater(len(with_representatives), len(vertices_only))
        self.assertTrue(
            np.any((with_representatives @ satellites[0]) > math.cos(radius) + 1e-6)
        )

    def test_coverage_counts_at_points_counts_visible_satellites(self):
        satellites = np.vstack(
            [
                fast.latlon_to_unit(0.0, 0.0),
                fast.latlon_to_unit(0.0, 60.0),
            ]
        )
        radius = math.radians(45.0)
        boundary_points = fast.small_circle_intersections(satellites[0], satellites[1], radius)
        points = np.vstack(
            [
                boundary_points,
                fast.latlon_to_unit(0.0, 0.0),
                fast.latlon_to_unit(0.0, 180.0),
            ]
        )

        counts = fast.coverage_counts_at_points(satellites, points, radius)

        self.assertEqual(counts.tolist(), [2, 2, 1, 0])

    def test_evaluate_satellite_snapshots_fast_tracks_time_min_counts(self):
        region = fast.LatLonRegion(
            lat_min_deg=-5.0,
            lat_max_deg=5.0,
            lon_min_deg=-5.0,
            lon_max_deg=5.0,
        )
        snapshots = np.array(
            [
                [
                    fast.latlon_to_unit(0.0, 0.0),
                    fast.latlon_to_unit(0.0, 180.0),
                ]
            ]
        )

        result = fast.evaluate_satellite_snapshots_fast(
            snapshots,
            np.array([0.0, 60.0]),
            math.radians(10.0),
            region,
        )

        self.assertEqual(result.min_counts_by_time.tolist(), [1, 0])
        self.assertEqual(result.c_min, 0)
        self.assertAlmostEqual(result.single_coverage_time_rate, 0.5)
        self.assertGreater(result.critical_point_counts_by_time[0], 0)

    def test_evaluate_satellite_snapshots_fast_can_stop_after_first_failure(self):
        region = fast.LatLonRegion(
            lat_min_deg=-5.0,
            lat_max_deg=5.0,
            lon_min_deg=-5.0,
            lon_max_deg=5.0,
        )
        snapshots = np.array(
            [
                [
                    fast.latlon_to_unit(0.0, 180.0),
                    fast.latlon_to_unit(0.0, 0.0),
                ]
            ]
        )

        result = fast.evaluate_satellite_snapshots_fast(
            snapshots,
            np.array([0.0, 60.0]),
            math.radians(10.0),
            region,
            stop_if_min_count_below=1,
        )

        self.assertTrue(result.stopped_early)
        self.assertEqual(result.evaluated_time_steps, 1)
        self.assertEqual(result.times_s.tolist(), [0.0])
        self.assertEqual(result.min_counts_by_time.tolist(), [0])

    def test_evaluate_constellation_fast_uses_walker_satellite_positions(self):
        params = ConstellationParams(
            planes=1,
            sats_per_plane=1,
            phase_factor=0,
            inclination_deg=0.0,
            raan0_deg=0.0,
            u0_deg=0.0,
        )
        config = CoverageConfig()
        region = fast.LatLonRegion(
            lat_min_deg=-1.0,
            lat_max_deg=1.0,
            lon_min_deg=-1.0,
            lon_max_deg=1.0,
        )

        result = fast.evaluate_constellation_fast(
            params,
            np.array([0.0]),
            config=config,
            region=region,
        )

        self.assertEqual(result.params, params)
        self.assertEqual(result.c_min, 1)
        self.assertEqual(result.min_counts_by_time.tolist(), [1])


if __name__ == "__main__":
    unittest.main()
