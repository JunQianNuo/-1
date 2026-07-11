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
