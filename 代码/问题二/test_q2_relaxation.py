"""Tests for the assumption-driven relaxations (Q2-R02, Q2-R07).

See 18-问题二算法条件松弛与假设驱动加速方案.md.

Q2-R02: fixing Omega0=0 and searching only u0 is exact for period-complete
        windows because a RAAN shift ``delta`` combined with an in-track shift
        ``-(n0/omega_e)*delta`` equals a time shift ``delta/omega_e`` of the
        whole Earth-fixed constellation.  This is validated here directly by the
        pointwise identity  c_B(t) = c_A(t - delta/omega_e).

Q2-R07: dropping representative points leaves the Deng-2021 Prop.3 sufficient
        critical set (corners + boundary + footprint intersections), which is a
        strict subset of the augmented set.
"""

from __future__ import annotations

import math
import unittest

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as fast


class TestFixRaan0PhaseGrid(unittest.TestCase):
    """Q2-R02 at the phase-grid level."""

    def test_fix_raan0_returns_single_raan_value(self) -> None:
        omega_free, u_free = q2.phase_grid(6, 8, 30.0, fix_raan0=False)
        omega_fixed, u_fixed = q2.phase_grid(6, 8, 30.0, fix_raan0=True)

        # Only one RAAN offset is searched, and it is exactly 0.
        self.assertEqual(len(omega_fixed), 1)
        self.assertAlmostEqual(float(omega_fixed[0]), 0.0)
        # The u0 grid is unchanged: only the RAAN dimension is removed.
        self.assertTrue(np.array_equal(u_free, u_fixed))
        # The free grid searches more than one RAAN offset for this structure.
        self.assertGreater(len(omega_free), 1)

    def test_fix_raan0_reduces_candidate_count(self) -> None:
        total = 24  # rich factorization -> several structures
        inclinations = (52.0, 55.0)
        free = list(
            q2.candidate_params_for_total(
                total, inclinations, phase_resolution_deg=30.0, fix_raan0=False
            )
        )
        fixed = list(
            q2.candidate_params_for_total(
                total, inclinations, phase_resolution_deg=30.0, fix_raan0=True
            )
        )
        self.assertGreater(len(free), 0)
        self.assertGreater(len(fixed), 0)
        # Fixing RAAN must not add candidates and should strictly reduce them.
        self.assertLess(len(fixed), len(free))
        # Every fixed candidate has raan0 == 0.
        self.assertTrue(all(p.raan0_deg == 0.0 for p in fixed))


class TestRaan0U0CollapseEquivalence(unittest.TestCase):
    """Q2-R02 validation: (Omega0, u0) collapse == exact time shift."""

    def test_grid_coverage_is_a_pure_time_shift(self) -> None:
        cfg = q2.CoverageConfig()
        n0 = cfg.mean_motion_rad_s
        we = cfg.earth_rotation_rad_s

        dt = 300.0
        k = 4  # integer time-step shift
        times = q2.make_time_grid(duration_s=6000.0, step_s=dt)
        lat, lon = q2.make_latlon_grid(step_deg=10.0)

        raan0_a, u0_a = 17.0, 23.0
        params_a = q2.ConstellationParams(
            planes=3, sats_per_plane=5, phase_factor=1,
            inclination_deg=55.0, raan0_deg=raan0_a, u0_deg=u0_a,
        )

        delta_t = k * dt
        delta_raan_deg = math.degrees(we * delta_t)      # RAAN shift delta
        delta_u_deg = -math.degrees(n0 * delta_t)        # = -(n0/we)*delta
        params_b = q2.ConstellationParams(
            planes=3, sats_per_plane=5, phase_factor=1,
            inclination_deg=55.0,
            raan0_deg=raan0_a + delta_raan_deg,
            u0_deg=u0_a + delta_u_deg,
        )

        counts_a = q2.coverage_counts(params_a, lat, lon, times, cfg)  # (K, L)
        counts_b = q2.coverage_counts(params_b, lat, lon, times, cfg)

        # c_B(t_j) = c_A(t_{j-k}) exactly on the fixed region.
        self.assertTrue(np.array_equal(counts_b[:, k:], counts_a[:, : counts_a.shape[1] - k]))

    def test_time_aggregated_metrics_are_raan_invariant(self) -> None:
        """A full-period window makes c_min / C1 essentially RAAN-invariant."""

        cfg = q2.CoverageConfig()
        n0 = cfg.mean_motion_rad_s
        we = cfg.earth_rotation_rad_s

        dt = 300.0
        k = 6
        # A long window so the boundary strip of width k*dt is a small fraction.
        times = q2.make_time_grid(duration_s=cfg.orbital_period_s * 3.0, step_s=dt)
        lat, lon = q2.make_latlon_grid(step_deg=8.0)

        base = dict(planes=4, sats_per_plane=6, phase_factor=1, inclination_deg=53.0)
        params_a = q2.ConstellationParams(raan0_deg=11.0, u0_deg=7.0, **base)

        delta_t = k * dt
        params_b = q2.ConstellationParams(
            raan0_deg=11.0 + math.degrees(we * delta_t),
            u0_deg=7.0 - math.degrees(n0 * delta_t),
            **base,
        )

        res_a = q2.evaluate_constellation(params_a, lat, lon, times, cfg)
        res_b = q2.evaluate_constellation(params_b, lat, lon, times, cfg)

        # Time-aggregated single-coverage rate matches within the small edge band.
        self.assertAlmostEqual(res_a.coverage_rate_q1, res_b.coverage_rate_q1, places=2)
        self.assertEqual(res_a.c_min, res_b.c_min)


class TestCriticalMinSet(unittest.TestCase):
    """Q2-R07: the Deng sufficient set is a subset of the augmented set."""

    def _snapshot(self) -> np.ndarray:
        cfg = q2.CoverageConfig()
        params = q2.ConstellationParams(
            planes=6, sats_per_plane=8, phase_factor=1,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        times = np.array([0.0])
        sat = q2.satellite_unit_vectors(params, times, cfg)  # (S, 1, 3)
        return sat[:, 0, :]

    def test_critical_min_points_are_subset(self) -> None:
        cfg = q2.CoverageConfig()
        region = fast.LatLonRegion()
        sat_t = self._snapshot()

        min_set = fast.critical_points_at_time(
            sat_t, cfg.coverage_angle_rad, region, include_representatives=False
        )
        full_set = fast.critical_points_at_time(
            sat_t, cfg.coverage_angle_rad, region, include_representatives=True
        )

        # The minimal (sufficient) set must be non-empty and no larger.
        self.assertGreater(len(min_set), 0)
        self.assertLessEqual(len(min_set), len(full_set))

        # Every minimal-set point is present in the augmented set (subset).
        combined = fast.deduplicate_unit_vectors(np.vstack([min_set, full_set]))
        self.assertEqual(len(combined), len(full_set))

    def test_fast_evaluation_runs_with_critical_min(self) -> None:
        cfg = q2.CoverageConfig()
        params = q2.ConstellationParams(
            planes=6, sats_per_plane=8, phase_factor=1,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        times = q2.make_time_grid(duration_s=1800.0, step_s=600.0)
        result = fast.evaluate_constellation_fast(
            params, times, config=cfg, include_representatives=False
        )
        self.assertEqual(result.evaluated_time_steps, len(times))
        self.assertGreaterEqual(result.c_min, 0)


class TestR01WindowIsInvalidForFixedRegion(unittest.TestCase):
    """Q2-R01 refutation: T_sid/M does NOT reduce the fixed-region window."""

    def test_region_coverage_not_periodic_in_2pi_over_m(self) -> None:
        cfg = q2.CoverageConfig()
        M, N = 20, 20
        params = q2.ConstellationParams(
            planes=M, sats_per_plane=N, phase_factor=1,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        t_phi = q2.SIDEREAL_DAY_S / M
        lat, lon = q2.make_latlon_grid(step_deg=6.0)
        times = np.array([0.0, t_phi])
        counts = q2.coverage_counts(params, lat, lon, times, cfg)

        # If the fixed-region coverage were 2*pi/M-periodic, the two snapshots
        # would be identical.  They are not -> the M-fold time reduction fails.
        self.assertFalse(np.array_equal(counts[:, 0], counts[:, 1]))

    def test_window_convergence_check_detects_short_window_bias(self) -> None:
        cfg = q2.CoverageConfig()
        params = q2.ConstellationParams(
            planes=20, sats_per_plane=20, phase_factor=1,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        lat, lon = q2.make_latlon_grid(step_deg=8.0)
        t_star = q2.symmetry_reduced_window_s(20, cfg)
        # Extend all the way to a full sidereal day, where the bias is largest.
        factor = q2.SIDEREAL_DAY_S / t_star

        report = q2.window_convergence_check(
            params, lat, lon, base_window_s=t_star, step_s=400.0, factor=factor
        )
        # The extended window's time samples are a superset of the base window's,
        # so its max gap is monotonically >= the base.  For this infeasible case
        # the full day reveals a strictly longer coverage gap, i.e. the short T*
        # window under-reports gaps -> unsafe for feasibility (Q2-R01 rejected).
        self.assertGreaterEqual(report["max_gap_extended_s"], report["max_gap_base_s"])
        self.assertGreater(report["max_gap_extended_s"], report["max_gap_base_s"])
        self.assertIn("cmin_consistent", report)


if __name__ == "__main__":
    unittest.main()



