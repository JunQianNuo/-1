"""Tests for q2_bilp_setcover."""

from __future__ import annotations

import math
import unittest

import numpy as np
import scipy.sparse as sp

import q2_constellation as q2
import q2_bilp_setcover as bilp


class TestSetCoverCore(unittest.TestCase):
    def test_disjoint_cover_optimum(self) -> None:
        # 3 candidates covering disjoint pairs of 6 demands -> min cover = 3.
        A = sp.csr_matrix(np.array([
            [1, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 1],
        ], dtype=np.int8))
        lp = bilp.setcover_lp_lower_bound(A, q=1)
        greedy = bilp.greedy_setcover(A, q=1)
        self.assertAlmostEqual(lp, 3.0, places=6)
        self.assertEqual(greedy.size, 3)

    def test_fractional_lp_below_integer(self) -> None:
        # Classic triangle: 3 demands, 3 candidates each covering a pair.
        # ILP optimum = 2, LP relaxation = 1.5.
        A = sp.csr_matrix(np.array([
            [1, 0, 1],   # demand 0 covered by cand 0,2
            [1, 1, 0],   # demand 1 covered by cand 0,1
            [0, 1, 1],   # demand 2 covered by cand 1,2
        ], dtype=np.int8))
        lp = bilp.setcover_lp_lower_bound(A, q=1)
        greedy = bilp.greedy_setcover(A, q=1)
        self.assertAlmostEqual(lp, 1.5, places=6)
        self.assertGreaterEqual(greedy.size, 2)     # integer feasible >= 2
        self.assertLessEqual(lp, greedy.size)        # LB <= UB

    def test_double_cover(self) -> None:
        # q=2: each demand needs 2 covers. 4 candidates, demand covered by 3.
        A = sp.csr_matrix(np.array([
            [1, 1, 1, 0],
            [1, 1, 0, 1],
        ], dtype=np.int8))
        greedy = bilp.greedy_setcover(A, q=2)
        # both demands reach 2 covers
        cov = np.asarray(A[:, greedy].sum(axis=1)).ravel()
        self.assertTrue(np.all(cov >= 2))

    def test_ilp_small(self) -> None:
        A = sp.csr_matrix(np.array([
            [1, 0, 1],
            [1, 1, 0],
            [0, 1, 1],
        ], dtype=np.int8))
        opt, sel, status = bilp.setcover_ilp(A, q=1, time_limit_s=10.0)
        self.assertEqual(opt, 2)
        cov = np.asarray(A[:, sel].sum(axis=1)).ravel()
        self.assertTrue(np.all(cov >= 1))


class TestCandidatePool(unittest.TestCase):
    def test_pool_shape_and_unit(self) -> None:
        cfg = q2.CoverageConfig()
        times = q2.make_time_grid(1800.0, 600.0)
        sub, params = bilp.candidate_pool_subpoints(50.0, 6, 5, times, cfg)
        self.assertEqual(sub.shape, (30, len(times), 3))
        self.assertEqual(params.shape, (30, 2))
        norms = np.linalg.norm(sub, axis=-1)
        self.assertTrue(np.allclose(norms, 1.0, atol=1e-9))

    def test_coverage_matrix_dedup_conserves_count(self) -> None:
        cfg = q2.CoverageConfig()
        times = q2.make_time_grid(1800.0, 900.0)
        sub, _ = bilp.candidate_pool_subpoints(50.0, 8, 8, times, cfg)
        lat, lon = q2.make_latlon_grid(step_deg=10.0)
        ground = q2.ground_unit_vectors(lat, lon)
        A, w = bilp.build_coverage_matrix(sub, ground, cfg.coverage_angle_rad)
        # total demands = K * L; dedup weights must sum to it
        self.assertEqual(int(w.sum()), len(lat) * len(times))
        self.assertLessEqual(A.shape[0], len(lat) * len(times))


class TestCGT(unittest.TestCase):
    def test_rgt_altitude(self) -> None:
        cfg = q2.CoverageConfig()
        h = bilp.rgt_altitude_km(15, cfg)
        self.assertGreater(h, 500.0)
        self.assertLess(h, 620.0)   # ~561 km for 15 revs/sidereal day

    def test_single_track_infeasible_for_wide_region(self) -> None:
        # A single ground track cannot continuously cover the whole China box
        # (permanent inter-pass longitude gaps) -> BILP reports infeasible.
        r = bilp.solve_q2_cgt_bilp(inclination_deg=50.0, revs_per_sidereal_day=15,
                                   n_slots=96, grid_step_deg=6.0, q=1)
        self.assertFalse(r["feasible"])
        self.assertGreater(r["uncoverable_demands"], 0)


if __name__ == "__main__":
    unittest.main()
