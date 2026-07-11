import math
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from q3_config import ConstellationParams, Q3Config, SimulationConfig
from q3_orbit import ground_ecef, make_time_grid, satellite_positions
from q3_topology import build_isl_graph, connected_components
from q3_access import access_sets_naive
from q3_routing import WeightedGraph, multi_source_dijkstra, min_delay_routes, shortest_path
from q3_statistics import delay_statistics
from q3_traffic import baseline_loads, uniform_od_demand
from q3_optimization import candidate_paths, multipath_flow_lp, throughput_binary_search
from q3_pipeline import run_snapshot
from q3_joint_search import (
    CommunicationEvaluation,
    CoverageEvaluation,
    JointSearchConfig,
    coverage_upper_bounds,
    generate_mn_layers,
    optimistic_delay_lower_bounds,
    search_constellations,
    u0_periodic_grid,
)


def test_simulation_config_defaults_to_nearest_inter_plane_links():
    """题面要求相邻轨道面内最近卫星建链，默认口径应为 nearest。"""

    sim = SimulationConfig()

    assert sim.topology_method == "nearest"


def test_run_snapshot_uses_simulation_topology_method(monkeypatch):
    """run_snapshot 应把 SimulationConfig.topology_method 传给拓扑构造器。"""

    import q3_pipeline
    from q3_routing import WeightedGraph

    captured: dict[str, str] = {}

    def fake_build_isl_graph(satellite_eci_km, params, *, config=None, method="walker", walker_shift=None):
        captured["method"] = method
        graph = WeightedGraph(params.total_satellites)
        if params.total_satellites >= 2:
            graph.add_edge(0, 1, 1.0, 1.0)
        return graph

    monkeypatch.setattr(q3_pipeline, "build_isl_graph", fake_build_isl_graph)
    params = ConstellationParams(planes=1, sats_per_plane=2, phase_factor=0, inclination_deg=0.0)
    cfg = Q3Config(coverage_angle_rad=math.radians(180.0))
    sim = SimulationConfig(duration_s=0.0, step_s=60.0)
    ground = ground_ecef(np.array([0.0]), np.array([0.0]), radius_km=cfg.earth_radius_km)

    run_snapshot(params, t_s=0.0, ground_points_ecef_km=ground, config=cfg, simulation=sim)

    assert captured["method"] == "nearest"


def test_generate_mn_layers_sorts_realizable_pairs_and_prunes_intra_distance():
    """联合搜索应按可实现星数排序，并先剪去同轨链路必断的 N。"""

    cfg = Q3Config(earth_radius_km=10.0, altitude_km=0.0, isl_max_distance_km=10.5)
    search = JointSearchConfig(
        s_lb=10,
        s_max=24,
        m_values=range(1, 5),
        n_values=range(2, 7),
        inclinations_deg=(0.0,),
        q3_config=cfg,
    )

    layers = generate_mn_layers(search)

    assert [layer.star_count for layer in layers] == [12, 18, 24]
    assert [layer.pairs for layer in layers] == [[(2, 6)], [(3, 6)], [(4, 6)]]


def test_u0_periodic_grid_only_spans_one_satellite_spacing():
    """u0 只需搜索一个同轨卫星间隔 [0, 360/N)。"""

    values = u0_periodic_grid(sats_per_plane=40, divisions=4)

    assert values == pytest.approx([0.0, 2.25, 4.5, 6.75])


def test_coverage_upper_bounds_support_strict_early_rejection():
    """覆盖评价上界低于阈值时，可以无漏解提前终止。"""

    c1_upper, c2_upper = coverage_upper_bounds(
        total_samples=100,
        processed_samples=60,
        single_hits=59,
        double_hits=50,
    )

    assert c1_upper == pytest.approx(0.99)
    assert c2_upper == pytest.approx(0.90)
    assert c1_upper < 0.999
    assert c2_upper < 0.95


def test_optimistic_delay_lower_bounds_detect_strict_impossibility():
    """若直连乐观下界已超过 30ms，则真实网络最短路必然不满足严格口径。"""

    sat = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]])
    ground = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]])
    bounds = optimistic_delay_lower_bounds(
        access_sets=[[0], [1]],
        satellite_ecef_km=sat,
        ground_points_ecef_km=ground,
        od_pairs=[(0, 1)],
        c_km_s=1.0,
        processing_delay_s=0.0,
    )

    assert bounds[(0, 1)] == pytest.approx(10.0)


def test_joint_search_finishes_current_star_layer_and_selects_robust_candidate():
    """第一个可行星数层内应完成全部候选复核，再选鲁棒裕量最大者。"""

    cfg = Q3Config(earth_radius_km=1.0, altitude_km=0.0, isl_max_distance_km=2.0)
    search = JointSearchConfig(
        s_lb=6,
        s_max=6,
        m_values=(2, 3),
        n_values=(3, 2),
        phase_values=(0,),
        inclinations_deg=(0.0,),
        u0_divisions=1,
        q3_config=cfg,
    )
    seen: list[tuple[int, int]] = []

    def coverage(_params):
        return CoverageEvaluation(c1=1.0, c2=1.0, feasible=True)

    def communication(params):
        seen.append((params.planes, params.sats_per_plane))
        margin = 0.20 if params.planes == 3 else 0.10
        return CommunicationEvaluation(
            feasible=True,
            p30=1.0,
            max_delay_s=0.030 - margin / 100.0,
            unreachable_rate=0.0,
            robustness_margin=margin,
        )

    result = search_constellations(search, coverage, communication)

    assert result.feasible
    assert result.params is not None
    assert result.params.planes == 3
    assert result.params.sats_per_plane == 2
    assert set(seen) == {(2, 3), (3, 2)}


def test_orbit_propagation_preserves_orbital_radius_and_shape():
    params = ConstellationParams(planes=2, sats_per_plane=3, phase_factor=1, inclination_deg=50.0)
    cfg = Q3Config(altitude_km=550.0)
    r_eci, r_ecef = satellite_positions(params, t_s=120.0, config=cfg)
    assert r_eci.shape == (6, 3)
    assert r_ecef.shape == (6, 3)
    expected_radius = cfg.earth_radius_km + cfg.altitude_km
    assert np.allclose(np.linalg.norm(r_eci, axis=1), expected_radius, rtol=0, atol=1e-8)
    assert np.allclose(np.linalg.norm(r_ecef, axis=1), expected_radius, rtol=0, atol=1e-8)


def test_time_grid_and_ground_ecef_are_well_formed():
    times = make_time_grid(10.0, 4.0)
    assert np.allclose(times, [0.0, 4.0, 8.0, 10.0])
    ground = ground_ecef(np.array([0.0, 90.0]), np.array([0.0, 0.0]), radius_km=2.0)
    assert np.allclose(ground[0], [2.0, 0.0, 0.0], atol=1e-12)
    assert np.allclose(ground[1], [0.0, 0.0, 2.0], atol=1e-12)


def test_build_isl_graph_respects_four_neighbor_limit_and_distance_threshold():
    params = ConstellationParams(planes=3, sats_per_plane=4, phase_factor=0, inclination_deg=50.0)
    cfg = Q3Config(isl_max_distance_km=1e9)
    r_eci, _ = satellite_positions(params, 0.0, cfg)
    graph = build_isl_graph(r_eci, params, config=cfg, method="walker")
    degrees = graph.degrees()
    assert max(degrees.values()) <= 4
    assert len(connected_components(graph)) == 1
    for edge in graph.edges:
        assert edge.distance_km <= cfg.isl_max_distance_km
        assert edge.weight_s > 0.0


def test_access_sets_naive_finds_visible_satellite():
    params = ConstellationParams(planes=1, sats_per_plane=1, phase_factor=0, inclination_deg=0.0)
    cfg = Q3Config(coverage_angle_rad=math.radians(10.0))
    _r_eci, r_ecef = satellite_positions(params, 0.0, cfg)
    ground = ground_ecef(np.array([0.0]), np.array([0.0]), radius_km=cfg.earth_radius_km)
    access = access_sets_naive(r_ecef, ground, cfg.coverage_angle_rad)
    assert access[0] == [0]


def test_multi_source_dijkstra_and_shortest_path_reconstructs_expected_route():
    graph = WeightedGraph(4)
    graph.add_edge(0, 1, 1.0)
    graph.add_edge(1, 2, 2.0)
    graph.add_edge(0, 2, 5.0)
    graph.add_edge(2, 3, 1.0)
    dist, pred, root = multi_source_dijkstra(graph, [(0, 0.0)])
    assert dist[3] == pytest.approx(4.0)
    assert shortest_path(pred, 0, 3) == [0, 1, 2, 3]
    assert root[3] == 0


def test_weighted_graph_keeps_adjacency_index_for_fast_neighbors():
    """neighbors 查询应由邻接表支持，避免 Dijkstra 反复扫描全边集。"""

    graph = WeightedGraph(4)
    graph.add_edge(0, 1, 5.0)
    graph.add_edge(0, 1, 3.0)
    graph.add_edge(0, 2, 2.0)

    assert hasattr(graph, "_adj")
    assert sorted(graph.neighbors(0)) == [(1, 3.0), (2, 2.0)]
    assert graph.degrees()[0] == 2


def test_nearest_topology_uses_kdtree_for_inter_plane_links(monkeypatch):
    """nearest 拓扑应使用 KDTree 批量求相邻轨道面的最近卫星。"""

    import q3_topology

    calls: list[tuple[str, tuple[int, ...], int | None]] = []

    class FakeTree:
        def __init__(self, data):
            calls.append(("init", np.asarray(data).shape, None))

        def query(self, points, k=1):
            point_array = np.asarray(points)
            calls.append(("query", point_array.shape, k))
            return np.zeros(point_array.shape[0]), np.zeros(point_array.shape[0], dtype=int)

    monkeypatch.setattr(q3_topology, "cKDTree", FakeTree, raising=False)
    params = ConstellationParams(planes=2, sats_per_plane=3, phase_factor=0, inclination_deg=20.0)
    cfg = Q3Config(isl_max_distance_km=1e9)
    r_eci, _ = satellite_positions(params, 0.0, cfg)

    build_isl_graph(r_eci, params, config=cfg, method="nearest")

    assert ("query", (params.sats_per_plane, 3), 1) in calls


def test_min_delay_routes_chooses_best_access_satellites():
    graph = WeightedGraph(3)
    graph.add_edge(0, 1, 1.0)
    graph.add_edge(1, 2, 1.0)
    sat = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    ground = np.array([[1.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    routes = min_delay_routes(graph, [[0], [2]], sat, ground, od_pairs=[(0, 1)], c_km_s=1.0)
    route = routes[(0, 1)]
    assert route.delay_s == pytest.approx(2.0)
    assert route.path == [0, 1, 2]


def test_delay_statistics_handles_infinite_samples():
    stats = delay_statistics([1.0, 2.0, math.inf, 4.0], delay_limit_s=2.5)
    assert stats["count"] == 4
    assert stats["reachable_count"] == 3
    assert stats["unreachable_rate"] == pytest.approx(0.25)
    assert stats["mean_s"] == pytest.approx(7.0 / 3.0)
    assert stats["within_limit_rate"] == pytest.approx(2.0 / 4.0)


def test_uniform_od_demand_and_baseline_loads_conserve_flow():
    demand = uniform_od_demand(3, total_flow_gbps=6.0)
    assert sum(demand.values()) == pytest.approx(6.0)
    paths = {(0, 1): [0, 1], (1, 2): [1, 2]}
    loads = baseline_loads(paths, {(0, 1): 2.0, (1, 2): 3.0}, satellite_count=3)
    assert loads.link_load_gbps[(0, 1)] == pytest.approx(2.0)
    assert loads.link_load_gbps[(1, 2)] == pytest.approx(3.0)
    assert sum(loads.access_load_gbps.values()) == pytest.approx(10.0)


def test_candidate_paths_and_lp_split_flow_across_parallel_routes():
    graph = WeightedGraph(4)
    graph.add_edge(0, 1, 1.0)
    graph.add_edge(1, 3, 1.0)
    graph.add_edge(0, 2, 1.0)
    graph.add_edge(2, 3, 1.0)
    paths = candidate_paths(graph, 0, 3, k=2, strategy="delete_edges")
    path_nodes = {tuple(p.nodes) for p in paths}
    assert (0, 1, 3) in path_nodes
    assert (0, 2, 3) in path_nodes

    result = multipath_flow_lp(
        candidate_path_map={(0, 1): paths},
        demand_gbps={(0, 1): 10.0},
        link_capacity_gbps={(0, 1): 5.0, (1, 3): 5.0, (0, 2): 5.0, (2, 3): 5.0},
    )
    assert result.feasible
    assert result.rho_max == pytest.approx(1.0, abs=1e-8)
    assert sum(result.path_flows_gbps.values()) == pytest.approx(10.0)


def test_throughput_binary_search_scales_until_capacity_limit():
    graph = WeightedGraph(3)
    graph.add_edge(0, 1, 1.0)
    graph.add_edge(1, 2, 1.0)
    paths = candidate_paths(graph, 0, 2, k=1)
    search = throughput_binary_search(
        candidate_path_map={(0, 1): paths},
        base_demand_gbps={(0, 1): 1.0},
        link_capacity_gbps={(0, 1): 4.0, (1, 2): 4.0},
        high=10.0,
        tol=1e-4,
    )
    assert search.lambda_star == pytest.approx(4.0, rel=1e-3)
    assert search.throughput_gbps == pytest.approx(4.0, rel=1e-3)


def test_run_snapshot_smoke_pipeline_returns_expected_sections():
    params = ConstellationParams(planes=2, sats_per_plane=4, phase_factor=0, inclination_deg=30.0)
    cfg = Q3Config(isl_max_distance_km=1e9, coverage_angle_rad=math.radians(180.0))
    sim = SimulationConfig(duration_s=0.0, step_s=60.0)
    ground = ground_ecef(np.array([0.0, 10.0]), np.array([0.0, 10.0]), radius_km=cfg.earth_radius_km)
    result = run_snapshot(params, t_s=0.0, ground_points_ecef_km=ground, config=cfg, simulation=sim)
    assert result.topology["satellite_count"] == 8
    assert result.delay_statistics["count"] == 2
    assert result.topology["max_degree"] <= 4
