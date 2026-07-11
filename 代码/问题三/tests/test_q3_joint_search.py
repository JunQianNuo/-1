from pathlib import Path
import csv
import json
import math
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import q3_joint_search
import q3_joint_evaluator
import run_q3_joint_search
from q3_batched_routing import batched_ground_delay_matrix, build_augmented_csr
from q3_config import ConstellationParams, Q3Config
from q3_routing import WeightedGraph, min_delay_routes


def _write_q2_cache(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["S", "M", "N", "F", "i", "u0", "C1", "C2"])
        writer.writerows(rows)


def _tiny_cli_args(cache, out, *, workers=1, resume=None):
    args = [
        "--mode", "discover", "--q2-cache", str(cache), "--out", str(out),
        "--workers", str(workers), "--duration-s", "0",
        "--high-time-step-s", "900", "--coverage-high-step-deg", "4",
        "--communication-high-step-deg", "25", "--keep-low", "2",
        "--keep-medium", "2",
    ]
    if resume is not None:
        args.extend(["--resume", str(resume)])
    return args


def test_q2_cache_loader_deduplicates_and_validates_schema(tmp_path):
    cache = tmp_path / "fine_records.csv"
    _write_q2_cache(cache, [
        [6, 2, 3, 1, 50, 0, 0.999, 0.96],
        [6, 2, 3, 1, 50, 0, 1.0, 0.97],
        [8, 2, 4, 0, 50, 0, 1.0, 0.94],
    ])

    records = run_q3_joint_search.load_q2_discovery_candidates(cache)

    assert len(records) == 1
    assert records[0].c2 == pytest.approx(0.97)
    bad_s = tmp_path / "bad_s.csv"
    _write_q2_cache(bad_s, [[7, 2, 3, 0, 50, 0, 1.0, 1.0]])
    with pytest.raises(ValueError, match="M.N"):
        run_q3_joint_search.load_q2_discovery_candidates(bad_s)
    missing = tmp_path / "missing.csv"
    missing.write_text("S,M,N\n6,2,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        run_q3_joint_search.load_q2_discovery_candidates(missing)


def test_config_digest_is_canonical_and_sensitive():
    first = {"thresholds": {"c1": 0.999, "c2": 0.95}, "grid": {"step": 4}}
    reordered = {"grid": {"step": 4}, "thresholds": {"c2": 0.95, "c1": 0.999}}

    assert run_q3_joint_search.config_digest(first) == run_q3_joint_search.config_digest(reordered)
    assert run_q3_joint_search.config_digest(first) != run_q3_joint_search.config_digest(
        {"thresholds": first["thresholds"], "grid": {"step": 2}}
    )


def test_checkpoint_rejects_digest_mismatch_and_conflicting_terminal_duplicate(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    base = {
        "config_digest": "abc", "candidate_key": "candidate", "mode": "discover",
        "stage": "low", "status": "rejected", "reason": "bound",
    }
    run_q3_joint_search.append_checkpoint(path, base)
    with pytest.raises(ValueError, match="config digest"):
        run_q3_joint_search.load_checkpoint(path, expected_config_digest="def")
    run_q3_joint_search.append_checkpoint(path, {**base, "status": "verified"})
    with pytest.raises(ValueError, match="conflicting"):
        run_q3_joint_search.load_checkpoint(path, expected_config_digest="abc")


def test_nested_grids_are_exact_subsets_and_include_endpoints():
    args = run_q3_joint_search.parse_args([
        "--q2-cache", "unused.csv", "--duration-s", "1800",
        "--high-time-step-s", "300", "--coverage-high-step-deg", "2",
        "--communication-high-step-deg", "5",
    ])

    mother, grids = run_q3_joint_search.build_nested_grids(args, Q3Config())

    for grid in grids.values():
        assert set(grid.time_indices) <= set(range(len(mother.times_s)))
        assert set(grid.coverage_point_indices) <= set(range(len(mother.coverage_weights)))
        assert set(grid.communication_point_indices) <= set(
            range(len(mother.communication_ground_ecef_km))
        )
        assert grid.time_indices[0] == 0
        assert grid.time_indices[-1] == len(mother.times_s) - 1
    high = grids["high"]
    assert np.array_equal(high.time_indices, np.arange(len(mother.times_s)))
    assert high.coverage_point_indices[-1] == len(mother.coverage_weights) - 1
    assert high.communication_point_indices[-1] == len(mother.communication_ground_ecef_km) - 1


def test_worker_converts_exception_to_numerical_error(monkeypatch):
    args = run_q3_joint_search.parse_args([
        "--q2-cache", "unused.csv", "--duration-s", "0",
        "--high-time-step-s", "900", "--coverage-high-step-deg", "4",
        "--communication-high-step-deg", "25",
    ])
    mother, grids = run_q3_joint_search.build_nested_grids(args, Q3Config())

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(run_q3_joint_search, "evaluate_joint_candidate", fail)
    records, _state = run_q3_joint_search.evaluate_candidate_stages(
        ConstellationParams(2, 3, 0, 50.0), mother, grids, Q3Config(),
        run_q3_joint_search.SimulationConfig(), ("low",),
    )

    assert records[0].status == "numerical_error"
    assert not records[0].strict_evidence
    assert "RuntimeError: boom" in records[0].reason


def test_tiny_discovery_cli_outputs_and_resume_are_deterministic(tmp_path):
    cache = tmp_path / "fine_records.csv"
    _write_q2_cache(cache, [
        [6, 2, 3, 0, 50, 0, 1.0, 1.0],
        [8, 2, 4, 0, 50, 0, 1.0, 1.0],
    ])
    out = tmp_path / "joint"

    assert run_q3_joint_search.main(_tiny_cli_args(cache, out)) == 0

    expected = {
        "joint_candidate_records.csv", "joint_stage_timing.csv",
        "joint_checkpoint.jsonl", "joint_layer_summary.csv",
        "joint_summary.json", "joint_report.md",
    }
    assert expected == {path.name for path in out.iterdir()}
    summary_before = json.loads((out / "joint_summary.json").read_text(encoding="utf-8"))
    assert summary_before["claim"] != "infeasible"
    assert summary_before["search_claim"] == summary_before["claim"]
    assert "thresholds" in summary_before and "sample_counts" in summary_before
    lines_before = (out / "joint_checkpoint.jsonl").read_text(encoding="utf-8").splitlines()

    assert run_q3_joint_search.main(
        _tiny_cli_args(cache, out, resume=out / "joint_checkpoint.jsonl")
    ) == 0

    summary_after = json.loads((out / "joint_summary.json").read_text(encoding="utf-8"))
    for key in ("claim", "search_claim", "best_candidate", "sample_counts", "thresholds"):
        assert summary_after[key] == summary_before[key]
    assert (out / "joint_checkpoint.jsonl").read_text(encoding="utf-8").splitlines() == lines_before


def test_tiny_workers_one_and_two_have_identical_ordered_records(tmp_path):
    cache = tmp_path / "fine_records.csv"
    _write_q2_cache(cache, [
        [6, 2, 3, 0, 50, 0, 1.0, 1.0],
        [8, 2, 4, 0, 50, 0, 1.0, 1.0],
    ])
    out_one, out_two = tmp_path / "one", tmp_path / "two"

    run_q3_joint_search.main(_tiny_cli_args(cache, out_one, workers=1))
    run_q3_joint_search.main(_tiny_cli_args(cache, out_two, workers=2))

    assert (out_one / "joint_candidate_records.csv").read_text(encoding="utf-8") == (
        out_two / "joint_candidate_records.csv"
    ).read_text(encoding="utf-8")


def _audit_record(
    status,
    *,
    feasible=False,
    planes=2,
    sats_per_plane=3,
    phase_factor=0,
    inclination_deg=45.0,
    u0_deg=0.0,
    **metrics,
):
    return q3_joint_search.CandidateAuditRecord(
        params=ConstellationParams(
            planes,
            sats_per_plane,
            phase_factor,
            inclination_deg,
            u0_deg=u0_deg,
        ),
        status=status,
        fidelity="high",
        reason=status,
        feasible=feasible,
        **metrics,
    )


def test_stage_outcome_defers_proxy_failure_and_rejects_strict_failure():
    deferred = q3_joint_search.classify_stage_outcome(
        fidelity="low", feasible=False, strict_evidence=False, reason="proxy_failure"
    )
    rejected = q3_joint_search.classify_stage_outcome(
        fidelity="low", feasible=False, strict_evidence=True, reason="strict_upper_bound"
    )

    assert deferred == q3_joint_search.StageOutcome(
        "deferred", "proxy_failure", False, "low"
    )
    assert rejected.status == "rejected"


def test_stage_outcome_verifies_only_high_fidelity_feasible_results():
    high = q3_joint_search.classify_stage_outcome(
        fidelity="high", feasible=True, strict_evidence=False, reason="complete"
    )
    medium = q3_joint_search.classify_stage_outcome(
        fidelity="medium", feasible=True, strict_evidence=False, reason="complete"
    )

    assert high.status == "verified"
    assert medium.status == "active"


def test_stage_outcome_rejects_unknown_fidelity():
    with pytest.raises(ValueError, match="fidelity"):
        q3_joint_search.classify_stage_outcome(
            fidelity="preview", feasible=True, strict_evidence=False, reason="complete"
        )


def test_layer_with_rejected_and_deferred_is_inconclusive_but_all_rejected_is_infeasible():
    rejected = _audit_record("rejected")
    deferred = _audit_record("deferred")

    mixed = q3_joint_search.conclude_star_layer(6, [rejected, deferred])
    all_rejected = q3_joint_search.conclude_star_layer(6, [rejected, rejected])

    assert mixed.status == "inconclusive"
    assert mixed.counts == {"rejected": 1, "deferred": 1}
    assert all_rejected.status == "infeasible"
    assert all_rejected.best is None


def test_layer_selects_verified_feasible_candidate_by_robustness_margins():
    weaker = _audit_record(
        "verified",
        feasible=True,
        p30_reachable=0.9991,
        p30_all=0.96,
        c1=0.9995,
        c2=0.96,
        max_delay_s=0.020,
    )
    stronger = _audit_record(
        "verified",
        feasible=True,
        p30_reachable=0.9992,
        p30_all=0.951,
        c1=0.9991,
        c2=0.951,
        max_delay_s=0.029,
        phase_factor=1,
    )

    conclusion = q3_joint_search.conclude_star_layer(6, [weaker, stronger])

    assert conclusion.status == "feasible_discrete"
    assert conclusion.best is stronger
    assert conclusion.counts == {"verified": 2}


def test_numerical_error_without_feasible_record_leaves_layer_inconclusive():
    conclusion = q3_joint_search.conclude_star_layer(
        6, [_audit_record("numerical_error")]
    )

    assert conclusion.status == "inconclusive"
    assert conclusion.best is None


def test_layer_validates_star_count_and_empty_layer_is_inconclusive():
    empty = q3_joint_search.conclude_star_layer(6, [])

    assert empty.status == "inconclusive"
    assert empty.counts == {}
    with pytest.raises(ValueError, match="star_count"):
        q3_joint_search.conclude_star_layer(7, [_audit_record("rejected")])


def test_strict_filter_order_honors_dependencies_priority_and_name_ties():
    filters = [
        q3_joint_search.StrictFilterSpec("zeta", 0.5, 2.0),
        q3_joint_search.StrictFilterSpec("alpha", 0.25, 1.0),
        q3_joint_search.StrictFilterSpec(
            "dependent", 0.9, 1.0, frozenset({"topology"})
        ),
        q3_joint_search.StrictFilterSpec("fast", 0.8, 1.0),
    ]

    assert [
        item.name
        for item in q3_joint_search.order_ready_strict_filters(filters, completed=set())
    ] == ["fast", "alpha", "zeta"]
    assert [
        item.name
        for item in q3_joint_search.order_ready_strict_filters(
            filters, completed={"topology"}
        )
    ] == ["dependent", "fast", "alpha", "zeta"]


@pytest.mark.parametrize(
    "rejection_rate,cost",
    [(-0.1, 1.0), (1.1, 1.0), (math.nan, 1.0), (0.5, 0.0), (0.5, math.inf)],
)
def test_strict_filter_order_rejects_invalid_rates_and_costs(rejection_rate, cost):
    invalid = q3_joint_search.StrictFilterSpec("invalid", rejection_rate, cost)

    with pytest.raises(ValueError):
        q3_joint_search.order_ready_strict_filters([invalid], completed=set())


def test_batched_ground_delays_match_existing_routing_for_off_diagonal_pairs():
    graph = WeightedGraph(4)
    graph.add_edge(0, 1, 0.4)
    graph.add_edge(1, 2, 0.5)
    graph.add_edge(0, 3, 2.0)
    graph.add_edge(2, 3, 0.1)
    satellite = np.array(
        [[0.0, 0.0, 1.0], [2.0, 0.0, 1.0], [4.0, 0.0, 1.0], [4.0, 2.0, 1.0]]
    )
    ground = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [4.0, 1.0, 0.0]])
    access_sets = [[0], [1], [2, 3]]

    actual = batched_ground_delay_matrix(
        graph, access_sets, satellite, ground, c_km_s=10.0
    )
    expected = min_delay_routes(
        graph, access_sets, satellite, ground, c_km_s=10.0
    )

    assert actual.shape == (3, 3)
    assert np.issubdtype(actual.dtype, np.floating)
    for pair, route in expected.items():
        assert actual[pair] == pytest.approx(route.delay_s)


def test_batched_ground_delays_return_infinity_for_empty_source_access():
    graph = WeightedGraph(2)
    graph.add_edge(0, 1, 1.0)
    satellite = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0]])
    ground = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    delays = batched_ground_delay_matrix(
        graph, [[], [1]], satellite, ground, c_km_s=1.0
    )

    assert math.isinf(delays[0, 1])


def test_augmented_graph_does_not_use_ground_points_as_relays():
    graph = WeightedGraph(2)
    satellite = np.array([[0.0, 0.0, 1.0], [10.0, 0.0, 1.0]])
    ground = np.array(
        [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [5.0, 0.0, 0.0]]
    )

    delays = batched_ground_delay_matrix(
        graph, [[0], [1], [0, 1]], satellite, ground, c_km_s=1.0
    )

    assert math.isinf(delays[0, 1])
    assert math.isinf(delays[1, 0])


@pytest.mark.parametrize(
    ("satellite", "ground"),
    [
        (np.zeros((2, 2)), np.zeros((1, 3))),
        (np.zeros((2, 3)), np.zeros((1, 2))),
    ],
)
def test_build_augmented_csr_rejects_invalid_coordinate_shapes(satellite, ground):
    with pytest.raises(ValueError):
        build_augmented_csr(WeightedGraph(2), [[0]], satellite, ground)


def test_build_augmented_csr_rejects_mismatched_access_length():
    with pytest.raises(ValueError):
        build_augmented_csr(
            WeightedGraph(2), [], np.zeros((2, 3)), np.zeros((1, 3))
        )


@pytest.mark.parametrize("satellite_index", [-1, 2])
def test_build_augmented_csr_rejects_invalid_access_index(satellite_index):
    with pytest.raises(IndexError):
        build_augmented_csr(
            WeightedGraph(2),
            [[satellite_index]],
            np.zeros((2, 3)),
            np.zeros((1, 3)),
        )


@pytest.mark.parametrize("speed", [0.0, -1.0, math.inf, math.nan])
def test_build_augmented_csr_rejects_invalid_propagation_speed(speed):
    with pytest.raises(ValueError):
        build_augmented_csr(
            WeightedGraph(1),
            [[0]],
            np.zeros((1, 3)),
            np.zeros((1, 3)),
            c_km_s=speed,
        )


@pytest.mark.parametrize(
    ("reachable_count", "expected"),
    [(999, 0), (1000, 1), (12782, 12), (1500, 1)],
)
def test_max_reachable_late_samples_respects_integer_boundaries(reachable_count, expected):
    assert q3_joint_search.max_reachable_late_samples(reachable_count) == expected


def test_max_reachable_late_samples_rejects_negative_counts():
    with pytest.raises(ValueError):
        q3_joint_search.max_reachable_late_samples(-1)


@pytest.mark.parametrize("eta_reach", [-0.1, 1.1, math.inf, math.nan])
def test_max_reachable_late_samples_rejects_invalid_eta(eta_reach):
    with pytest.raises(ValueError):
        q3_joint_search.max_reachable_late_samples(1000, eta_reach)


def test_max_reachable_late_samples_does_not_add_ulps_as_whole_samples():
    assert q3_joint_search.max_reachable_late_samples(10**30, 0.999) == 10**27


def test_max_reachable_late_samples_is_exact_beyond_decimal_context_precision():
    assert q3_joint_search.max_reachable_late_samples(10**30 + 999, 0.999) == 10**27


def test_service_progress_reachable_threshold_boundary():
    progress = q3_joint_search.ServiceProgress(total_weight=1000)

    assert progress.update(1, reachable=True, within_limit=False)
    assert progress.upper_bounds() == pytest.approx((0.999, 0.999))
    assert progress.can_still_pass()

    assert not progress.update(1, reachable=True, within_limit=False)
    assert not progress.can_still_pass_reachable()


def test_service_progress_all_sample_threshold_boundary():
    progress = q3_joint_search.ServiceProgress(total_weight=20)

    assert progress.update(1, reachable=False, within_limit=False)
    assert progress.can_still_pass_all()

    assert not progress.update(1, reachable=False, within_limit=False)
    assert not progress.can_still_pass_all()


def test_service_progress_rejects_within_limit_when_unreachable():
    progress = q3_joint_search.ServiceProgress(total_weight=1)

    with pytest.raises(ValueError):
        progress.update(1, reachable=False, within_limit=True)


def test_weighted_coverage_progress_uses_area_weights_for_bounds():
    progress = q3_joint_search.WeightedCoverageProgress(total_weight=10, c1_min=0.9, c2_min=0.8)

    assert not progress.update(6, single_covered=True, double_covered=False)
    assert progress.upper_bounds() == pytest.approx((1.0, 0.4))
    assert not progress.can_still_pass()


@pytest.mark.parametrize(
    "progress_type",
    [q3_joint_search.ServiceProgress, q3_joint_search.WeightedCoverageProgress],
)
@pytest.mark.parametrize("total_weight", [0.0, -1.0, math.inf, math.nan])
def test_weighted_progress_rejects_invalid_total_weight(progress_type, total_weight):
    with pytest.raises(ValueError):
        progress_type(total_weight=total_weight)


@pytest.mark.parametrize(
    ("progress_type", "threshold_name"),
    [
        (q3_joint_search.ServiceProgress, "eta_reach"),
        (q3_joint_search.ServiceProgress, "eta_all"),
        (q3_joint_search.WeightedCoverageProgress, "c1_min"),
        (q3_joint_search.WeightedCoverageProgress, "c2_min"),
    ],
)
@pytest.mark.parametrize("threshold", [-0.1, 1.1, math.inf, math.nan])
def test_weighted_progress_rejects_invalid_thresholds(
    progress_type, threshold_name, threshold
):
    with pytest.raises(ValueError):
        progress_type(total_weight=1.0, **{threshold_name: threshold})


@pytest.mark.parametrize(
    ("progress_type", "update_args"),
    [
        (q3_joint_search.ServiceProgress, (True, True)),
        (q3_joint_search.WeightedCoverageProgress, (True, True)),
    ],
)
@pytest.mark.parametrize("weight", [0.0, -1.0, math.inf, math.nan])
def test_weighted_progress_rejects_invalid_update_weight(progress_type, update_args, weight):
    progress = progress_type(total_weight=1.0)

    with pytest.raises(ValueError):
        progress.update(weight, *update_args)


@pytest.mark.parametrize(
    ("progress_type", "update_args"),
    [
        (q3_joint_search.ServiceProgress, (True, True)),
        (q3_joint_search.WeightedCoverageProgress, (True, True)),
    ],
)
def test_weighted_progress_rejects_overflow_for_tiny_totals(progress_type, update_args):
    progress = progress_type(total_weight=1e-15)

    with pytest.raises(ValueError):
        progress.update(2e-15, *update_args)


def test_service_progress_roundoff_never_pushes_counters_above_total():
    progress = q3_joint_search.ServiceProgress(total_weight=0.3)

    progress.update(0.1, reachable=True, within_limit=True)
    progress.update(0.2, reachable=True, within_limit=True)

    assert progress.processed_weight <= progress.total_weight
    assert progress.reachable_weight <= progress.total_weight
    assert progress.within_limit_weight <= progress.total_weight


def test_weighted_coverage_roundoff_never_pushes_hits_above_total():
    progress = q3_joint_search.WeightedCoverageProgress(total_weight=0.3)

    progress.update(0.1, single_covered=True, double_covered=True)
    progress.update(0.2, single_covered=True, double_covered=True)

    assert progress.processed_weight <= progress.total_weight
    assert progress.single_hit_weight <= progress.total_weight
    assert progress.double_hit_weight <= progress.total_weight


def _joint_grid(*, times=(0.0,), coverage_points=None, communication_points=None):
    if coverage_points is None:
        coverage_points = np.array([[1.0, 0.0, 0.0]])
    if communication_points is None:
        communication_points = np.array([[6371.0, 0.0, 0.0], [6371.0, 0.0, 0.0]])
    return q3_joint_evaluator.MotherGrid(
        times_s=np.asarray(times, dtype=float),
        coverage_ground_unit=np.asarray(coverage_points, dtype=float),
        coverage_weights=np.ones(len(coverage_points)),
        communication_ground_ecef_km=np.asarray(communication_points, dtype=float),
    )


def _fidelity(*, times=(0,), coverage=(0,), communication=(0, 1)):
    return q3_joint_evaluator.FidelityGrid(
        "test", np.asarray(times), np.asarray(coverage), np.asarray(communication)
    )


def test_coverage_counts_from_ecef_finds_visible_satellite_for_orthogonal_points():
    counts = q3_joint_evaluator.coverage_counts_from_ecef(
        np.array([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0]]),
        np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        coverage_angle_rad=0.0,
    )
    assert counts.tolist() == [1, 1]


def test_service_summary_exact_reachable_boundary_and_unreachable_semantics():
    one_late = q3_joint_evaluator.summarize_service_delays(
        np.r_[np.full(999, 0.01), 0.04]
    )
    two_late = q3_joint_evaluator.summarize_service_delays(
        np.r_[np.full(998, 0.01), 0.04, 0.04]
    )
    with_unreachable = q3_joint_evaluator.summarize_service_delays(
        np.array([0.01, np.inf]), eta_all=0.75
    )
    assert one_late.feasible_reachable
    assert not two_late.feasible_reachable
    assert with_unreachable.p30_reachable == 1.0
    assert with_unreachable.p30_all == 0.5
    assert with_unreachable.unreachable_count == 1


@pytest.mark.parametrize(
    "mother,fidelity,error",
    [
        (
            q3_joint_evaluator.MotherGrid(np.zeros((1, 1)), np.ones((1, 3)), np.ones(1), np.ones((2, 3))),
            _fidelity(),
            "times_s",
        ),
        (
            q3_joint_evaluator.MotherGrid(np.zeros(1), np.ones((1, 2)), np.ones(1), np.ones((2, 3))),
            _fidelity(),
            "coverage_ground_unit",
        ),
        (_joint_grid(), _fidelity(times=(0, 0)), "unique"),
        (_joint_grid(), _fidelity(coverage=(1,)), "range"),
    ],
)
def test_joint_grid_validation_rejects_bad_shapes_and_indices(mother, fidelity, error):
    with pytest.raises((ValueError, IndexError), match=error):
        q3_joint_evaluator.evaluate_joint_candidate(
            ConstellationParams(1, 1, 0, 0.0), mother_grid=mother, fidelity=fidelity
        )


def test_joint_evaluation_propagates_once_per_selected_time(monkeypatch):
    calls = []

    def positions(params, time_s, config):
        calls.append(time_s)
        sat = np.array([[7000.0, 0.0, 0.0]])
        return sat, sat

    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", positions)
    monkeypatch.setattr(q3_joint_evaluator, "batched_ground_delay_matrix", lambda *a, **k: np.zeros((2, 2)))
    result, _ = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 1, 0, 0.0),
        mother_grid=_joint_grid(times=(0.0, 10.0)),
        fidelity=_fidelity(times=(0, 1)),
        config=Q3Config(coverage_angle_rad=math.pi),
        c1_min=0.0,
        c2_min=0.0,
        eta_reach=0.0,
        eta_all=0.0,
    )
    assert result.status == "verified"
    assert calls == [0.0, 10.0]


def test_repeated_fidelity_does_no_new_work_or_propagation(monkeypatch):
    calls = []

    def positions(params, time_s, config):
        calls.append(time_s)
        sat = np.array([[7000.0, 0.0, 0.0]])
        return sat, sat

    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", positions)
    monkeypatch.setattr(q3_joint_evaluator, "batched_ground_delay_matrix", lambda *a, **k: np.zeros((2, 2)))
    kwargs = dict(
        params=ConstellationParams(1, 1, 0, 0.0),
        mother_grid=_joint_grid(),
        fidelity=_fidelity(),
        config=Q3Config(coverage_angle_rad=math.pi),
        c1_min=0.0,
        c2_min=0.0,
        eta_reach=0.0,
        eta_all=0.0,
    )
    first, state = q3_joint_evaluator.evaluate_joint_candidate(**kwargs)
    weights = (state.coverage_progress.processed_weight, state.service_progress.processed_weight)
    second, state = q3_joint_evaluator.evaluate_joint_candidate(**kwargs, state=state)
    assert calls == [0.0]
    assert weights == (state.coverage_progress.processed_weight, state.service_progress.processed_weight)
    assert first == second


def test_low_fidelity_empirical_failure_remains_active(monkeypatch):
    sat = np.array([[-7000.0, 0.0, 0.0]])
    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", lambda *a: (sat, sat))
    result, _ = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 1, 0, 0.0),
        mother_grid=_joint_grid(times=(0.0, 1.0), communication_points=np.array([[-6371.0, 0.0, 0.0], [-6371.0, 0.0, 0.0]])),
        fidelity=_fidelity(times=(0,)),
        config=Q3Config(coverage_angle_rad=0.0),
        c1_min=0.5,
        c2_min=0.5,
        eta_reach=0.0,
        eta_all=0.0,
    )
    assert result.status == "active"
    assert result.c1 == 0.0


def test_coverage_upper_bound_rejects_before_batched_routing(monkeypatch):
    sat = np.array([[-7000.0, 0.0, 0.0]])
    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", lambda *a: (sat, sat))
    monkeypatch.setattr(q3_joint_evaluator, "batched_ground_delay_matrix", lambda *a, **k: pytest.fail("routing called"))
    result, _ = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 1, 0, 0.0),
        mother_grid=_joint_grid(),
        fidelity=_fidelity(),
        config=Q3Config(coverage_angle_rad=0.0),
    )
    assert result.status == "rejected"
    assert result.message == "coverage_upper_bound"


def test_tiny_connected_candidate_processes_all_samples_consistently(monkeypatch):
    sat = np.array([[7000.0, 0.0, 0.0], [0.0, 7000.0, 0.0]])
    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", lambda *a: (sat, sat))
    mother = _joint_grid(
        coverage_points=np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        communication_points=np.array([[6371.0, 0.0, 0.0], [0.0, 6371.0, 0.0]]),
    )
    result, state = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 2, 0, 0.0),
        mother_grid=mother,
        fidelity=_fidelity(coverage=(0, 1)),
        config=Q3Config(coverage_angle_rad=math.pi, isl_max_distance_km=1e9, delay_limit_s=1.0),
    )
    assert result.status == "verified"
    assert (result.c1, result.c2, result.p30_reachable, result.p30_all) == (1.0, 1.0, 1.0, 1.0)
    assert result.reachable_count == 2
    assert result.late_reachable_count == result.unreachable_count == 0
    assert len(state.processed_coverage_keys) == 2
    assert len(state.processed_od_keys) == 2


def test_state_rejects_same_total_mother_grid_with_swapped_weights(monkeypatch):
    sat = np.array([[7000.0, 0.0, 0.0]])
    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", lambda *a: (sat, sat))
    original = q3_joint_evaluator.MotherGrid(
        np.array([0.0, 1.0]),
        np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        np.array([1.0, 2.0]),
        np.array([[6371.0, 0.0, 0.0], [6371.0, 0.0, 0.0]]),
    )
    fidelity = _fidelity(times=(0,), coverage=(0,), communication=(0,))
    _, state = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 1, 0, 0.0),
        mother_grid=original,
        fidelity=fidelity,
        config=Q3Config(coverage_angle_rad=math.pi),
        c1_min=0.0,
        c2_min=0.0,
        eta_reach=0.0,
        eta_all=0.0,
    )
    swapped = q3_joint_evaluator.MotherGrid(
        original.times_s,
        original.coverage_ground_unit,
        np.array([2.0, 1.0]),
        original.communication_ground_ecef_km,
    )
    with pytest.raises(ValueError, match="mother grid"):
        q3_joint_evaluator.evaluate_joint_candidate(
            ConstellationParams(1, 1, 0, 0.0),
            mother_grid=swapped,
            fidelity=fidelity,
            state=state,
            config=Q3Config(coverage_angle_rad=math.pi),
            c1_min=0.0,
            c2_min=0.0,
            eta_reach=0.0,
            eta_all=0.0,
        )


@pytest.mark.parametrize(
    "mother,fidelity,error",
    [
        (
            q3_joint_evaluator.MotherGrid(np.zeros(1), np.ones((1, 3)), np.array([0.0]), np.ones((2, 3))),
            _fidelity(),
            "coverage_weights",
        ),
        (
            q3_joint_evaluator.MotherGrid(np.zeros(1), np.ones((1, 3)), np.ones(1), np.ones((2, 3)), 0.0),
            _fidelity(),
            "communication_sample_weight",
        ),
        (_joint_grid(), _fidelity(coverage=(0, 0)), "unique"),
        (_joint_grid(), _fidelity(communication=(0, 0)), "unique"),
        (_joint_grid(), _fidelity(times=(1,)), "range"),
        (_joint_grid(), _fidelity(communication=(0, 2)), "range"),
    ],
)
def test_joint_grid_validation_additional_invalid_inputs(mother, fidelity, error):
    with pytest.raises((ValueError, IndexError), match=error):
        q3_joint_evaluator.evaluate_joint_candidate(
            ConstellationParams(1, 1, 0, 0.0), mother_grid=mother, fidelity=fidelity
        )


def test_delay_lower_bound_all_upper_returns_before_graph_and_routing(monkeypatch):
    sat = np.array([[7000.0, 0.0, 0.0]])
    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", lambda *a: (sat, sat))
    monkeypatch.setattr(q3_joint_evaluator, "build_isl_graph", lambda *a, **k: pytest.fail("graph built"))
    monkeypatch.setattr(q3_joint_evaluator, "batched_ground_delay_matrix", lambda *a, **k: pytest.fail("routing called"))
    result, _ = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 1, 0, 0.0),
        mother_grid=_joint_grid(
            times=(0.0, 1.0),
            communication_points=np.array([[-6371.0, 0.0, 0.0], [-6371.0, 0.0, 0.0]]),
        ),
        fidelity=_fidelity(times=(0,)),
        config=Q3Config(coverage_angle_rad=0.0),
        c1_min=0.0,
        c2_min=0.0,
        eta_reach=1.0,
        eta_all=0.75,
    )
    assert result.status == "rejected"
    assert result.message == "delay_lower_bound_all_upper"


def test_lower_bound_misses_do_not_make_reachable_ratio_impossible(monkeypatch):
    sat = np.array([[7000.0, 0.0, 0.0]])
    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", lambda *a: (sat, sat))
    monkeypatch.setattr(q3_joint_evaluator, "build_isl_graph", lambda *a, **k: WeightedGraph(1))
    monkeypatch.setattr(q3_joint_evaluator, "batched_ground_delay_matrix", lambda *a, **k: np.full((2, 2), np.inf))
    result, _ = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 1, 0, 0.0),
        mother_grid=_joint_grid(
            times=(0.0, 1.0),
            communication_points=np.array([[-6371.0, 0.0, 0.0], [-6371.0, 0.0, 0.0]]),
        ),
        fidelity=_fidelity(times=(0,)),
        config=Q3Config(coverage_angle_rad=0.0),
        c1_min=0.0,
        c2_min=0.0,
        eta_reach=1.0,
        eta_all=0.5,
    )
    assert result.status == "active"
    assert result.p30_reachable == 1.0
    assert result.p30_all == 0.0


def test_communication_upper_bound_rejects_after_actual_routes(monkeypatch):
    sat = np.array([[7000.0, 0.0, 0.0]])
    monkeypatch.setattr(q3_joint_evaluator, "satellite_positions", lambda *a: (sat, sat))
    monkeypatch.setattr(q3_joint_evaluator, "optimistic_delay_lower_bounds", lambda **k: {(0, 1): 0.0, (1, 0): 0.0})
    monkeypatch.setattr(q3_joint_evaluator, "build_isl_graph", lambda *a, **k: WeightedGraph(1))
    monkeypatch.setattr(q3_joint_evaluator, "batched_ground_delay_matrix", lambda *a, **k: np.array([[0.0, 0.1], [0.1, 0.0]]))
    result, _ = q3_joint_evaluator.evaluate_joint_candidate(
        ConstellationParams(1, 1, 0, 0.0),
        mother_grid=_joint_grid(),
        fidelity=_fidelity(),
        config=Q3Config(coverage_angle_rad=math.pi, delay_limit_s=0.03),
        c1_min=0.0,
        c2_min=0.0,
    )
    assert result.status == "rejected"
    assert result.message == "communication_upper_bound"
