"""Tests for the Q2-R05 Lipschitz-margin continuous coverage certificate.

The important tests here are the *soundness* checks: they verify empirically that
the analytic Lipschitz constants L_x = 1 and L_t = n0 + omega_e are genuine upper
bounds on the margin variation, which is what makes the certificate rigorous.
"""

from __future__ import annotations

import math
import unittest

import numpy as np

import q2_constellation as q2
import q2_lipschitz_certificate as cert
from q2_coverage_margin import q_fold_margins_at_points
from q2_fast_coverage import LatLonRegion


CFG = q2.CoverageConfig()
COS_THETA = math.cos(CFG.coverage_angle_rad)


def _random_region_point(rng: np.random.Generator) -> np.ndarray:
    lat = rng.uniform(4.0, 53.0)
    lon = rng.uniform(73.0, 135.0)
    return q2.ground_unit_vectors(np.array([lat]), np.array([lon]))[0]


class TestConstants(unittest.TestCase):
    def test_time_lipschitz_constant(self) -> None:
        expected = CFG.mean_motion_rad_s + CFG.earth_rotation_rad_s
        self.assertAlmostEqual(cert.time_lipschitz_constant(CFG), expected)

    def test_spatial_covering_radius(self) -> None:
        step = 2.0
        expected = math.radians(step) / math.sqrt(2.0)
        self.assertAlmostEqual(cert.spatial_covering_radius_rad(step), expected)

    def test_threshold_composition(self) -> None:
        step, dt = 1.0, 60.0
        rho = cert.spatial_covering_radius_rad(step)
        l_t = cert.time_lipschitz_constant(CFG)
        expected = rho + l_t * 0.5 * dt
        self.assertAlmostEqual(cert.certificate_threshold(step, dt, CFG), expected)

    def test_classify_branches(self) -> None:
        self.assertEqual(cert.classify_status(-0.1, 0.1), "uncovered")
        self.assertEqual(cert.classify_status(0.5, 0.1), "covered")
        self.assertEqual(cert.classify_status(0.05, 0.1), "inconclusive")


def _angular_margin(sat_vectors: np.ndarray, x: np.ndarray, q: int = 1) -> float:
    """theta - gamma^(q): the angular coverage margin used by the certificate."""
    dot_margin = q_fold_margins_at_points(
        sat_vectors, x[None, :], CFG.coverage_angle_rad, q=q
    ).margins[0]
    qth_dot = float(np.clip(dot_margin + COS_THETA, -1.0, 1.0))
    gamma = math.acos(qth_dot)
    return CFG.coverage_angle_rad - gamma


class TestLipschitzSoundness(unittest.TestCase):
    """The certificate is only rigorous if L_x, L_t are true upper bounds
    on the ANGULAR margin variation."""

    def setUp(self) -> None:
        self.params = q2.ConstellationParams(
            planes=8, sats_per_plane=6, phase_factor=1,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        self.rng = np.random.default_rng(20260711)

    def test_time_bound_holds(self) -> None:
        l_t = cert.time_lipschitz_constant(CFG)
        dt = 30.0
        for _ in range(40):
            x = _random_region_point(self.rng)
            t0 = float(self.rng.uniform(0.0, 5000.0))
            sat = q2.satellite_unit_vectors(self.params, np.array([t0, t0 + dt]), CFG)
            m0 = _angular_margin(sat[:, 0, :], x)
            m1 = _angular_margin(sat[:, 1, :], x)
            # |mu(t+dt) - mu(t)| <= L_t * dt  (geodesic distance moves <= subpoint).
            self.assertLessEqual(abs(m1 - m0), l_t * dt + 1e-9)

    def test_space_bound_holds(self) -> None:
        t0 = 1234.0
        sat = q2.satellite_unit_vectors(self.params, np.array([t0]), CFG)[:, 0, :]
        for _ in range(40):
            x = _random_region_point(self.rng)
            perturb = self.rng.normal(size=3)
            perturb -= (perturb @ x) * x
            perturb /= np.linalg.norm(perturb)
            xp = x + 1e-3 * perturb
            xp /= np.linalg.norm(xp)
            arc = math.acos(float(np.clip(x @ xp, -1.0, 1.0)))
            m0 = _angular_margin(sat, x)
            m1 = _angular_margin(sat, xp)
            # L_x = 1 must upper-bound |d mu / d(arc)| (geodesic is 1-Lipschitz).
            self.assertLessEqual(abs(m1 - m0), 1.0 * arc + 1e-9)


class TestCertifyEndToEnd(unittest.TestCase):
    def test_sparse_constellation_is_uncovered(self) -> None:
        params = q2.ConstellationParams(
            planes=2, sats_per_plane=3, phase_factor=0,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        result = cert.certify_continuous_coverage(
            params, grid_step_deg=10.0, time_step_s=600.0, duration_s=1200.0,
            q=1, region=LatLonRegion(),
        )
        # Six satellites cannot continuously cover China -> a gap point exists.
        self.assertEqual(result.status, "uncovered")
        self.assertLess(result.min_margin, 0.0)

    def test_fields_and_threshold_consistent(self) -> None:
        params = q2.ConstellationParams(
            planes=20, sats_per_plane=20, phase_factor=1,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        step, dt, dur = 8.0, 900.0, 1800.0
        result = cert.certify_continuous_coverage(
            params, grid_step_deg=step, time_step_s=dt, duration_s=dur,
            q=1, region=LatLonRegion(),
        )
        self.assertAlmostEqual(result.threshold, cert.certificate_threshold(step, dt, CFG))
        self.assertIn(result.status, {"covered", "uncovered", "inconclusive"})
        self.assertEqual(result.num_times, len(q2.make_time_grid(dur, dt)))

    def test_q_exceeding_satellites_is_uncovered(self) -> None:
        params = q2.ConstellationParams(
            planes=2, sats_per_plane=2, phase_factor=0,
            inclination_deg=53.0, raan0_deg=0.0, u0_deg=0.0,
        )
        result = cert.certify_continuous_coverage(
            params, grid_step_deg=15.0, time_step_s=900.0, duration_s=900.0,
            q=10, region=LatLonRegion(),
        )
        self.assertEqual(result.status, "uncovered")


if __name__ == "__main__":
    unittest.main()
