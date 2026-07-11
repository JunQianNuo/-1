"""Joint coverage-communication search helpers for Problem 3.

This module implements the *realizable-star-count ordered, multi-fidelity
branch-and-bound* skeleton used to search the intersection of the Problem 2
coverage feasible set and the Problem 3 communication feasible set.

The coverage model itself lives in the Problem 2 code, so this module accepts a
caller-supplied ``coverage_evaluator``.  Communication filters and the final
branch-and-bound loop are implemented here and can be reused with different
fidelity levels.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import math
from typing import Callable, Iterable, Literal, Sequence

import numpy as np

from q3_access import access_sets_naive
from q3_config import ConstellationParams, Q3Config, SimulationConfig
from q3_orbit import satellite_positions
from q3_routing import min_delay_routes
from q3_topology import build_isl_graph, connected_components


DelayPolicy = Literal["strict", "service_probability"]


@dataclass(frozen=True)
class StarCountLayer:
    """All engineering-valid ``(M, N)`` pairs that share one star count."""

    star_count: int
    pairs: list[tuple[int, int]]


@dataclass(frozen=True)
class CoverageEvaluation:
    """Coverage feasibility result supplied by the Problem 2 evaluator."""

    c1: float
    c2: float
    feasible: bool
    samples: int = 0
    message: str = ""


@dataclass(frozen=True)
class CommunicationEvaluation:
    """Communication feasibility result for one constellation candidate."""

    feasible: bool
    p30: float | None = None
    max_delay_s: float | None = None
    mean_delay_s: float | None = None
    unreachable_rate: float = 0.0
    reachable_count: int = 0
    sample_count: int = 0
    robustness_margin: float = -math.inf
    message: str = ""


@dataclass(frozen=True)
class SearchCandidate:
    params: ConstellationParams
    coverage: CoverageEvaluation
    communication: CommunicationEvaluation

    @property
    def star_count(self) -> int:
        return self.params.total_satellites


@dataclass(frozen=True)
class SearchResult:
    feasible: bool
    params: ConstellationParams | None
    coverage: CoverageEvaluation | None
    communication: CommunicationEvaluation | None
    star_count: int | None
    evaluated_candidates: int
    rejected: dict[str, int]
    message: str = ""


@dataclass(frozen=True)
class JointSearchConfig:
    """Configuration for ordered branch-and-bound constellation search."""

    s_lb: int
    s_max: int
    m_values: Iterable[int]
    n_values: Iterable[int]
    inclinations_deg: Sequence[float]
    s_seed: int | None = None
    phase_values: Sequence[int] | None = None
    u0_divisions: int = 4
    raan0_deg: float = 0.0
    c1_min: float = 0.999
    c2_min: float = 0.95
    eta_t: float = 0.95
    delay_policy: DelayPolicy = "service_probability"
    q3_config: Q3Config = field(default_factory=Q3Config)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)

    def __post_init__(self) -> None:
        if self.s_lb <= 0 or self.s_max <= 0:
            raise ValueError("s_lb and s_max must be positive")
        if self.s_lb > self.s_max:
            raise ValueError("s_lb must not exceed s_max")
        if self.u0_divisions <= 0:
            raise ValueError("u0_divisions must be positive")
        if not self.inclinations_deg:
            raise ValueError("at least one inclination must be provided")
        if self.delay_policy not in {"strict", "service_probability"}:
            raise ValueError("delay_policy must be 'strict' or 'service_probability'")


@dataclass
class CoverageProgress:
    """Strict upper-bound early stopping for streaming coverage evaluation."""

    total_samples: int
    c1_min: float = 0.999
    c2_min: float = 0.95
    processed_samples: int = 0
    single_hits: int = 0
    double_hits: int = 0

    def update(self, single_covered: bool, double_covered: bool) -> bool:
        """Add one sample and return whether the candidate can still pass."""

        if self.processed_samples >= self.total_samples:
            raise ValueError("processed samples exceed total_samples")
        self.processed_samples += 1
        self.single_hits += int(bool(single_covered))
        self.double_hits += int(bool(double_covered))
        c1_upper, c2_upper = self.upper_bounds()
        return c1_upper >= self.c1_min and c2_upper >= self.c2_min

    def upper_bounds(self) -> tuple[float, float]:
        return coverage_upper_bounds(
            total_samples=self.total_samples,
            processed_samples=self.processed_samples,
            single_hits=self.single_hits,
            double_hits=self.double_hits,
        )

    def final_evaluation(self) -> CoverageEvaluation:
        if self.total_samples <= 0:
            raise ValueError("total_samples must be positive")
        c1 = self.single_hits / self.total_samples
        c2 = self.double_hits / self.total_samples
        return CoverageEvaluation(
            c1=float(c1),
            c2=float(c2),
            feasible=c1 >= self.c1_min and c2 >= self.c2_min,
            samples=self.total_samples,
        )


def manufacturing_cost_wan(star_count: int) -> int:
    """Manufacturing plus launch cost in ten-thousand CNY."""

    if star_count <= 0:
        raise ValueError("star_count must be positive")
    return int(500 * star_count + 20000 * math.ceil(star_count / 60))


def intra_plane_distance_km(sats_per_plane: int, config: Q3Config | None = None) -> float:
    """Distance between adjacent satellites in the same circular orbit plane."""

    if sats_per_plane <= 0:
        raise ValueError("sats_per_plane must be positive")
    if sats_per_plane == 1:
        return 0.0
    cfg = config or Q3Config()
    return float(2.0 * cfg.semi_major_axis_km * math.sin(math.pi / sats_per_plane))


def generate_mn_layers(config: JointSearchConfig) -> list[StarCountLayer]:
    """Generate legal ``(M,N)`` pairs grouped and sorted by realizable star count."""

    grouped: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for m in sorted(set(int(v) for v in config.m_values)):
        if m <= 0:
            continue
        for n in sorted(set(int(v) for v in config.n_values)):
            if n <= 0:
                continue
            star_count = m * n
            if star_count < config.s_lb or star_count > config.s_max:
                continue
            if intra_plane_distance_km(n, config.q3_config) > config.q3_config.isl_max_distance_km:
                continue
            grouped[star_count].append((m, n))
    return [StarCountLayer(star_count=s, pairs=sorted(pairs)) for s, pairs in sorted(grouped.items())]


def u0_periodic_grid(*, sats_per_plane: int, divisions: int) -> list[float]:
    """Return a grid over the non-redundant interval ``[0, 360/N)`` in degrees."""

    if sats_per_plane <= 0:
        raise ValueError("sats_per_plane must be positive")
    if divisions <= 0:
        raise ValueError("divisions must be positive")
    period = 360.0 / sats_per_plane
    return [k * period / divisions for k in range(divisions)]


def coverage_upper_bounds(
    *,
    total_samples: int,
    processed_samples: int,
    single_hits: int,
    double_hits: int,
) -> tuple[float, float]:
    """Upper bounds of final single/double coverage rates after partial scans."""

    if total_samples <= 0:
        raise ValueError("total_samples must be positive")
    if not 0 <= processed_samples <= total_samples:
        raise ValueError("processed_samples must lie in [0, total_samples]")
    if not 0 <= single_hits <= processed_samples:
        raise ValueError("single_hits must lie in [0, processed_samples]")
    if not 0 <= double_hits <= processed_samples:
        raise ValueError("double_hits must lie in [0, processed_samples]")
    remaining = total_samples - processed_samples
    return ((single_hits + remaining) / total_samples, (double_hits + remaining) / total_samples)


def optimistic_delay_lower_bounds(
    *,
    access_sets: list[list[int]],
    satellite_ecef_km: np.ndarray,
    ground_points_ecef_km: np.ndarray,
    od_pairs: Iterable[tuple[int, int]],
    c_km_s: float = 299792.458,
    processing_delay_s: float = 0.0,
) -> dict[tuple[int, int], float]:
    """Compute a no-Dijkstra optimistic end-to-end delay lower bound for OD pairs."""

    sat = np.asarray(satellite_ecef_km, dtype=float)
    ground = np.asarray(ground_points_ecef_km, dtype=float)
    bounds: dict[tuple[int, int], float] = {}
    for a, b in od_pairs:
        best = math.inf
        for p in access_sets[a]:
            uplink = float(np.linalg.norm(ground[a] - sat[p]))
            for q in access_sets[b]:
                inter_sat = float(np.linalg.norm(sat[p] - sat[q]))
                downlink = float(np.linalg.norm(sat[q] - ground[b]))
                proc = processing_delay_s if p != q else 0.0
                best = min(best, (uplink + inter_sat + downlink) / c_km_s + proc)
        bounds[(a, b)] = best
    return bounds


def has_connected_representative_topology(
    params: ConstellationParams,
    *,
    times_s: Iterable[float],
    config: Q3Config | None = None,
    simulation: SimulationConfig | None = None,
) -> bool:
    """Return False if any representative ISL snapshot is disconnected."""

    cfg = config or Q3Config()
    sim = simulation or SimulationConfig()
    for t_s in times_s:
        r_eci, _r_ecef = satellite_positions(params, float(t_s), cfg)
        graph = build_isl_graph(r_eci, params, config=cfg, method=sim.topology_method)
        if len(connected_components(graph)) > 1:
            return False
    return True


def delay_lower_bound_screen(
    params: ConstellationParams,
    *,
    ground_points_ecef_km: np.ndarray,
    times_s: Iterable[float],
    od_pairs: Iterable[tuple[int, int]],
    config: Q3Config | None = None,
    policy: DelayPolicy = "strict",
    eta_t: float = 0.95,
) -> bool:
    """Screen a candidate by optimistic delay lower bounds only.

    ``False`` means the candidate is mathematically impossible under the chosen
    delay policy.  ``True`` means only "not ruled out".
    """

    cfg = config or Q3Config()
    pairs = list(od_pairs)
    times = list(times_s)
    if not pairs:
        return True
    total = len(pairs) * len(times)
    possible_hits = 0
    processed = 0
    for t_s in times:
        _r_eci, r_ecef = satellite_positions(params, float(t_s), cfg)
        access = access_sets_naive(r_ecef, ground_points_ecef_km, cfg.access_angle_rad)
        bounds = optimistic_delay_lower_bounds(
            access_sets=access,
            satellite_ecef_km=r_ecef,
            ground_points_ecef_km=ground_points_ecef_km,
            od_pairs=pairs,
            c_km_s=cfg.speed_of_light_km_s,
            processing_delay_s=cfg.processing_delay_s,
        )
        for value in bounds.values():
            processed += 1
            if value <= cfg.delay_limit_s:
                possible_hits += 1
            elif policy == "strict":
                return False
        if policy == "service_probability":
            remaining = total - processed
            if (possible_hits + remaining) / total < eta_t:
                return False
    return True


def evaluate_communication_feasibility(
    params: ConstellationParams,
    *,
    ground_points_ecef_km: np.ndarray,
    times_s: Iterable[float],
    od_pairs: Iterable[tuple[int, int]] | None = None,
    config: Q3Config | None = None,
    simulation: SimulationConfig | None = None,
    policy: DelayPolicy = "service_probability",
    eta_t: float = 0.95,
    stop_on_service_pass: bool = False,
) -> CommunicationEvaluation:
    """Evaluate communication feasibility with strict upper-bound early stopping."""

    cfg = config or Q3Config()
    sim = simulation or SimulationConfig()
    times = list(times_s)
    if od_pairs is None:
        j = len(ground_points_ecef_km)
        pairs = [(a, b) for a in range(j) for b in range(j) if a != b]
    else:
        pairs = list(od_pairs)
    total = len(times) * len(pairs)
    if total == 0:
        return CommunicationEvaluation(False, message="no communication samples")

    processed = 0
    hits = 0
    finite_delays: list[float] = []
    unreachable = 0

    for t_s in times:
        r_eci, r_ecef = satellite_positions(params, float(t_s), cfg)
        graph = build_isl_graph(r_eci, params, config=cfg, method=sim.topology_method)
        access = access_sets_naive(r_ecef, ground_points_ecef_km, cfg.access_angle_rad)
        routes = min_delay_routes(
            graph,
            access,
            r_ecef,
            ground_points_ecef_km,
            od_pairs=pairs,
            c_km_s=cfg.speed_of_light_km_s,
        )
        for route in routes.values():
            processed += 1
            delay = route.delay_s
            if math.isfinite(delay):
                finite_delays.append(delay)
                if delay <= cfg.delay_limit_s:
                    hits += 1
                elif policy == "strict":
                    return _communication_result(
                        False,
                        hits,
                        processed,
                        total,
                        finite_delays,
                        unreachable,
                        cfg.delay_limit_s,
                        eta_t,
                        "strict_delay_violation",
                    )
            else:
                unreachable += 1

            if policy == "service_probability":
                remaining = total - processed
                if (hits + remaining) / total < eta_t:
                    return _communication_result(
                        False,
                        hits,
                        processed,
                        total,
                        finite_delays,
                        unreachable,
                        cfg.delay_limit_s,
                        eta_t,
                        "p30_upper_bound_below_threshold",
                    )
                if stop_on_service_pass and hits / total >= eta_t:
                    return _communication_result(
                        True,
                        hits,
                        processed,
                        total,
                        finite_delays,
                        unreachable,
                        cfg.delay_limit_s,
                        eta_t,
                        "p30_threshold_already_met",
                    )

    if policy == "strict":
        feasible = bool(finite_delays) and max(finite_delays) <= cfg.delay_limit_s
    else:
        feasible = hits / total >= eta_t
    return _communication_result(
        feasible,
        hits,
        processed,
        total,
        finite_delays,
        unreachable,
        cfg.delay_limit_s,
        eta_t,
        "complete",
    )


def search_constellations(
    config: JointSearchConfig,
    coverage_evaluator: Callable[[ConstellationParams], CoverageEvaluation],
    communication_evaluator: Callable[[ConstellationParams], CommunicationEvaluation],
    *,
    topology_filter: Callable[[ConstellationParams], bool] | None = None,
    lower_bound_filter: Callable[[ConstellationParams], bool] | None = None,
) -> SearchResult:
    """Search star-count layers and return the most robust candidate in the first feasible layer."""

    rejected: dict[str, int] = defaultdict(int)
    evaluated = 0

    for layer in generate_mn_layers(config):
        feasible_candidates: list[SearchCandidate] = []
        for params in _iter_constellation_candidates(layer, config):
            if topology_filter is not None and not topology_filter(params):
                rejected["topology"] += 1
                continue
            coverage = coverage_evaluator(params)
            if not coverage.feasible or coverage.c1 < config.c1_min or coverage.c2 < config.c2_min:
                rejected["coverage"] += 1
                continue
            if lower_bound_filter is not None and not lower_bound_filter(params):
                rejected["delay_lower_bound"] += 1
                continue
            communication = communication_evaluator(params)
            evaluated += 1
            if not communication.feasible:
                rejected["communication"] += 1
                continue
            feasible_candidates.append(SearchCandidate(params, coverage, communication))

        if feasible_candidates:
            best = max(
                feasible_candidates,
                key=lambda item: (
                    item.communication.robustness_margin,
                    item.communication.p30 if item.communication.p30 is not None else -math.inf,
                    -(item.communication.max_delay_s if item.communication.max_delay_s is not None else math.inf),
                ),
            )
            return SearchResult(
                feasible=True,
                params=best.params,
                coverage=best.coverage,
                communication=best.communication,
                star_count=layer.star_count,
                evaluated_candidates=evaluated,
                rejected=dict(rejected),
                message="feasible_layer_found",
            )

    return SearchResult(
        feasible=False,
        params=None,
        coverage=None,
        communication=None,
        star_count=None,
        evaluated_candidates=evaluated,
        rejected=dict(rejected),
        message="no_feasible_candidate_in_search_range",
    )


def _iter_constellation_candidates(
    layer: StarCountLayer,
    config: JointSearchConfig,
) -> Iterable[ConstellationParams]:
    for m, n in layer.pairs:
        if config.phase_values is None:
            phase_values = range(m)
        else:
            phase_values = [int(v) for v in config.phase_values if 0 <= int(v) < m]
        for f in phase_values:
            for inc in config.inclinations_deg:
                for u0 in u0_periodic_grid(sats_per_plane=n, divisions=config.u0_divisions):
                    yield ConstellationParams(
                        planes=m,
                        sats_per_plane=n,
                        phase_factor=int(f),
                        inclination_deg=float(inc),
                        raan0_deg=float(config.raan0_deg),
                        u0_deg=float(u0),
                    )


def _communication_result(
    feasible: bool,
    hits: int,
    processed: int,
    total: int,
    finite_delays: list[float],
    unreachable: int,
    delay_limit_s: float,
    eta_t: float,
    message: str,
) -> CommunicationEvaluation:
    p30 = hits / total if total else math.nan
    max_delay = max(finite_delays) if finite_delays else None
    mean_delay = float(np.mean(finite_delays)) if finite_delays else None
    if max_delay is None:
        strict_margin = -math.inf
    else:
        strict_margin = delay_limit_s - max_delay
    p30_margin = p30 - eta_t
    return CommunicationEvaluation(
        feasible=feasible,
        p30=float(p30),
        max_delay_s=float(max_delay) if max_delay is not None else None,
        mean_delay_s=mean_delay,
        unreachable_rate=float(unreachable / processed) if processed else 0.0,
        reachable_count=len(finite_delays),
        sample_count=processed,
        robustness_margin=float(min(p30_margin, strict_margin)),
        message=message,
    )
