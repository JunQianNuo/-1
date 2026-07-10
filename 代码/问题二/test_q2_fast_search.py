import csv
from pathlib import Path
import tempfile
import unittest

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as fast
import run_q2_fast_search as fast_search


class FastSearchTests(unittest.TestCase):
    def test_total_range_supports_descending_order(self):
        totals = list(fast_search.total_range(1598, 1600, search_order="desc"))

        self.assertEqual(totals, [1600, 1599, 1598])

    def test_factor_pairs_for_search_prioritizes_balanced_pairs(self):
        pairs = fast_search.factor_pairs_for_search(1600)

        self.assertEqual(pairs[0], (40, 40))
        self.assertIn((32, 50), pairs[:5])
        self.assertNotEqual(pairs[0], (1, 1600))

    def test_stratified_candidate_generator_avoids_single_factor_pair_bias(self):
        candidates = list(
            fast_search.candidate_params_for_total_stratified(
                total_satellites=1600,
                inclinations_deg=[53.0],
                phase_resolution_deg=30.0,
                max_candidates=6,
            )
        )

        planes = {params.planes for params in candidates}
        self.assertEqual(len(candidates), 6)
        self.assertGreater(len(planes), 1)
        self.assertIn(40, planes)

    def test_fast_result_record_has_search_fields(self):
        params = q2.ConstellationParams(
            planes=1,
            sats_per_plane=1,
            phase_factor=0,
            inclination_deg=0.0,
            raan0_deg=0.0,
            u0_deg=0.0,
        )
        result = fast.FastCoverageResult(
            params=params,
            times_s=np.array([0.0, 60.0]),
            min_counts_by_time=np.array([1, 0]),
            critical_point_counts_by_time=np.array([4, 4]),
            c_min=0,
            single_coverage_time_rate=0.5,
            strict_double_time_rate=0.0,
            max_uncovered_gap_s=60.0,
            worst_time_index=1,
        )

        record = fast_search.fast_result_record(result)

        self.assertEqual(record["total_satellites"], 1)
        self.assertEqual(record["fast_c_min"], 0)
        self.assertEqual(record["fast_single_time_rate"], 0.5)
        self.assertEqual(record["fast_worst_time_s"], 60.0)
        self.assertEqual(record["fast_mean_critical_points"], 4.0)

    def test_run_fast_search_keeps_top_and_verifies_subset(self):
        config = q2.CoverageConfig()
        region = fast.LatLonRegion(
            lat_min_deg=-1.0,
            lat_max_deg=1.0,
            lon_min_deg=-1.0,
            lon_max_deg=1.0,
        )
        verify_lat, verify_lon = q2.make_latlon_grid(
            lat_min_deg=-1.0,
            lat_max_deg=1.0,
            lon_min_deg=-1.0,
            lon_max_deg=1.0,
            step_deg=1.0,
        )

        result = fast_search.run_fast_search(
            start_total=1,
            stop_total=1,
            inclinations_deg=[0.0],
            fast_times_s=np.array([0.0]),
            verify_times_s=np.array([0.0]),
            region=region,
            verify_lat_deg=verify_lat,
            verify_lon_deg=verify_lon,
            phase_resolution_deg=90.0,
            max_candidates_per_total=4,
            keep_top_fast=2,
            verify_top=1,
            config=config,
        )

        self.assertEqual(result.evaluated_count, 4)
        self.assertLessEqual(len(result.fast_records), 2)
        self.assertEqual(result.verified_count, 1)
        self.assertIsNotNone(result.best_fast_record)
        self.assertIsNotNone(result.best_verified_record)
        self.assertGreaterEqual(result.best_verified_record["c_min"], 1)

    def test_run_fast_search_records_fast_early_stop(self):
        config = q2.CoverageConfig()
        region = fast.LatLonRegion(
            lat_min_deg=-1.0,
            lat_max_deg=1.0,
            lon_min_deg=-1.0,
            lon_max_deg=1.0,
        )
        verify_lat, verify_lon = q2.make_latlon_grid(
            lat_min_deg=-1.0,
            lat_max_deg=1.0,
            lon_min_deg=-1.0,
            lon_max_deg=1.0,
            step_deg=1.0,
        )

        result = fast_search.run_fast_search(
            start_total=1,
            stop_total=1,
            inclinations_deg=[0.0],
            fast_times_s=np.array([0.0, 60.0]),
            verify_times_s=np.array([0.0]),
            region=region,
            verify_lat_deg=verify_lat,
            verify_lon_deg=verify_lon,
            phase_resolution_deg=90.0,
            max_candidates_per_total=4,
            keep_top_fast=4,
            verify_top=0,
            config=config,
            stop_if_min_count_below=2,
        )

        self.assertTrue(any(record["fast_stopped_early"] for record in result.fast_records))
        self.assertTrue(all(record["fast_evaluated_time_steps"] <= 2 for record in result.fast_records))

    def test_run_fast_search_streams_records_to_csv(self):
        config = q2.CoverageConfig()
        region = fast.LatLonRegion(
            lat_min_deg=-1.0,
            lat_max_deg=1.0,
            lon_min_deg=-1.0,
            lon_max_deg=1.0,
        )
        verify_lat, verify_lon = q2.make_latlon_grid(
            lat_min_deg=-1.0,
            lat_max_deg=1.0,
            lon_min_deg=-1.0,
            lon_max_deg=1.0,
            step_deg=1.0,
        )

        with tempfile.TemporaryDirectory() as tmp:
            stream_dir = Path(tmp)
            fast_search.run_fast_search(
                start_total=1,
                stop_total=1,
                inclinations_deg=[0.0],
                fast_times_s=np.array([0.0]),
                verify_times_s=np.array([0.0]),
                region=region,
                verify_lat_deg=verify_lat,
                verify_lon_deg=verify_lon,
                phase_resolution_deg=90.0,
                max_candidates_per_total=4,
                keep_top_fast=2,
                verify_top=1,
                config=config,
                stream_output_dir=stream_dir,
            )

            fast_path = stream_dir / "q2_fast_search_stream_fast_records.csv"
            verified_path = stream_dir / "q2_fast_search_stream_verified_records.csv"
            with fast_path.open(newline="", encoding="utf-8-sig") as f:
                fast_rows = list(csv.DictReader(f))
            with verified_path.open(newline="", encoding="utf-8-sig") as f:
                verified_rows = list(csv.DictReader(f))

            self.assertEqual(len(fast_rows), 4)
            self.assertEqual(len(verified_rows), 1)


if __name__ == "__main__":
    unittest.main()
