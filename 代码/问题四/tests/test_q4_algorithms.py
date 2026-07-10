import math
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from q4_debris import (
    annual_probability,
    collision_cross_section_km2,
    conjunction_event_rate_per_year,
    flux_collision_rate_per_s,
    split_catalog_density,
)
from q4_collision import collision_probability_2d_gaussian, time_to_cpa
from q4_avoidance import avoidance_decision, max_miss_distance_km, required_delta_v_mps
from q4_capacity_cost import (
    annual_expected_failures,
    avoidance_cost_wanyuan,
    capacity_loss_ratio,
    replacement_unit_cost_wanyuan,
)
from q4_redundancy import (
    cold_standby_confidence,
    coverage_availability,
    ground_backup_confidence,
    satellite_criticality,
    space_backup_confidence,
)


def test_debris_density_split_uses_power_law_catalog_threshold():
    cat, uncat = split_catalog_density(total_density_km3=1e-8, catalog_threshold_cm=10.0, beta=2.0)
    assert cat == pytest.approx(1e-10)
    assert uncat == pytest.approx(9.9e-9)


def test_flux_collision_rate_and_event_rate_have_expected_units():
    sigma = collision_cross_section_km2(sat_radius_km=0.001, debris_diameter_cm=10.0)
    assert sigma == pytest.approx(math.pi * (0.001 + 0.5e-4) ** 2)
    rate = flux_collision_rate_per_s(cross_section_km2=sigma, relative_speed_km_s=10.0, density_km3=1e-8)
    assert rate == pytest.approx(sigma * 10.0 * 1e-8)
    assert annual_probability(rate, year_s=10.0) == pytest.approx(1.0 - math.exp(-10.0 * rate))
    events = conjunction_event_rate_per_year(
        screening_radius_km=5.0,
        relative_speed_km_s=10.0,
        catalog_density_km3=1e-10,
        year_s=100.0,
    )
    assert events == pytest.approx(math.pi * 25.0 * 10.0 * 1e-10 * 100.0)


def test_cpa_time_minimizes_relative_distance_for_linear_motion():
    assert time_to_cpa(np.array([10.0, 0.0, 0.0]), np.array([-2.0, 0.0, 0.0])) == pytest.approx(5.0)
    assert time_to_cpa(np.array([0.0, 3.0, 0.0]), np.array([1.0, 0.0, 0.0])) == pytest.approx(0.0)


def test_centered_isotropic_collision_probability_matches_analytic_case():
    sigma = 2.0
    radius = 1.0
    pc = collision_probability_2d_gaussian(
        miss_vector_km=np.array([0.0, 0.0]),
        covariance_km2=np.diag([sigma**2, sigma**2]),
        hard_body_radius_km=radius,
        radial_steps=240,
        angular_steps=240,
    )
    expected = 1.0 - math.exp(-(radius**2) / (2.0 * sigma**2))
    assert pc == pytest.approx(expected, rel=2e-3, abs=2e-5)


def test_collision_probability_decreases_with_miss_distance():
    cov = np.diag([1.0, 1.0])
    near = collision_probability_2d_gaussian(np.array([0.0, 0.0]), cov, 0.5)
    far = collision_probability_2d_gaussian(np.array([3.0, 0.0]), cov, 0.5)
    assert 0.0 <= far < near < 1.0


def test_avoidance_decision_combines_threshold_and_delta_v_feasibility():
    assert max_miss_distance_km(0.5, 2.0) == pytest.approx(1.0)
    assert required_delta_v_mps(current_miss_km=0.2, target_miss_km=1.2, sensitivity_km_per_mps=2.0) == pytest.approx(0.5)
    decision = avoidance_decision(
        collision_probability=1e-4,
        threshold=1e-5,
        current_miss_km=0.2,
        target_miss_km=1.2,
        sensitivity_km_per_mps=2.0,
        max_delta_v_mps=1.0,
    )
    assert decision.triggered
    assert decision.feasible
    assert decision.required_delta_v_mps == pytest.approx(0.5)


def test_capacity_and_cost_formulas_are_dimensionally_consistent():
    loss = capacity_loss_ratio(
        total_avoidances=100.0,
        satellite_count=1000,
        maneuver_duration_s=60.0,
        year_s=31_536_000.0,
        capacity_reduction=0.5,
    )
    assert loss == pytest.approx(0.5 * 60.0 * 100.0 / (1000.0 * 31_536_000.0))
    assert avoidance_cost_wanyuan(avoidance_count=3, cost_per_avoidance_wanyuan=2.0) == pytest.approx(6.0)
    assert replacement_unit_cost_wanyuan(500.0, 20_000.0, 60) == pytest.approx(500.0 + 20_000.0 / 60.0)
    assert annual_expected_failures(1000, 1e-6, 10.0) == pytest.approx(0.01)


def test_cold_standby_and_backup_confidence_match_poisson_formula():
    assert cold_standby_confidence(active_units=1, spare_units=0, unit_reliability=0.9) == pytest.approx(0.9)
    with_one_spare = cold_standby_confidence(active_units=1, spare_units=1, unit_reliability=0.9)
    assert with_one_spare > 0.9
    assert ground_backup_confidence(active_satellites=10, ground_spares=0, unit_reliability=0.95) == pytest.approx(0.95**10)
    expected_plane = 0.95**4 * (1.0 + (-4.0 * math.log(0.95)))
    assert space_backup_confidence(active_satellites=12, planes=3, space_spares=3, unit_reliability=0.95) == pytest.approx(expected_plane**3)


def test_coverage_availability_and_satellite_criticality_use_coverage_matrix():
    counts = np.array([[1, 2], [0, 1], [1, 1]])
    assert coverage_availability(counts) == pytest.approx(2.0 / 3.0)

    coverage = np.array(
        [
            [[1, 0], [1, 1]],
            [[0, 1], [0, 1]],
            [[0, 1], [0, 1]],
        ],
        dtype=bool,
    )
    crit = satellite_criticality(coverage)
    assert crit.shape == (2,)
    assert crit[0] == pytest.approx(1.0 / 3.0)
    assert crit[1] == pytest.approx(2.0 / 3.0)



def test_run_smoke_pipeline_creates_expected_outputs(tmp_path):
    from q4_pipeline import run_smoke_pipeline

    result = run_smoke_pipeline(output_dir=tmp_path / "results", figure_dir=tmp_path / "figures")
    assert result["scenario"] == "smoke_parameterized_non_final"
    assert result["single_satellite"]["catalog_density_km3"] > 0.0
    assert result["constellation"]["total_avoidances_per_year"] >= 0.0
    assert (tmp_path / "results" / "q4_summary.csv").exists()
    assert (tmp_path / "results" / "q4_run_report.txt").exists()
    assert (tmp_path / "figures" / "q4_threshold_sensitivity.png").exists()
