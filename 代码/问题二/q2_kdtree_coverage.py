"""KD-tree accelerated critical-point coverage evaluation.

The original critical-point implementation reduced memory but still performed
``O(S^2)`` satellite-pair products and ``O(Q*S)`` point coverage products.  This
module uses a 3-D unit-sphere ``cKDTree`` to query only geometrically relevant
pairs and nearest satellites.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as legacy

try:
    from scipy.spatial import cKDTree
except ImportError:  # pragma: no cover
    cKDTree = None


@dataclass(frozen=True)
class LocalCoverageResult:
    counts: np.ndarray
    margins: np.ndarray
    q: int
    backend: str

    @property
    def min_count(self) -> int:
        return int(np.min(self.counts)) if len(self.counts) else 0

    @property
    def min_margin(self) -> float:
        return float(np.min(self.margins)) if len(self.margins) else -math.inf

    @property
    def worst_point_index(self) -> int:
        return int(np.argmin(self.margins)) if len(self.margins) else -1


@dataclass(frozen=True)
class KDTreeCoverageResult:
    params: object | None
    times_s: np.ndarray
    min_counts_by_time: np.ndarray
    min_margins_by_time: np.ndarray
    critical_point_counts_by_time: np.ndarray
    c_min: int
    min_margin: float
    single_coverage_time_rate: float
    strict_double_time_rate: float
    max_uncovered_gap_s: float
    worst_time_index: int
    worst_point: np.ndarray | None
    stopped_early: bool
    evaluated_time_steps: int
    backend: str


def _normalize(vectors: np.ndarray) -> np.ndarray:
    return legacy.normalize_vectors(vectors)


def angular_radius_to_chord(angle_rad: float) -> float:
    if not 0.0 <= angle_rad <= math.pi:
        raise ValueError("angle_rad must lie in [0, pi]")
    return 2.0 * math.sin(0.5 * angle_rad)


def neighbor_pairs_kdtree(
    unit_vectors: np.ndarray,
    max_angle_rad: float,
) -> list[tuple[int, int]]:
    """Return pairs within an angular radius using a unit-sphere KD tree."""

    vectors = _normalize(unit_vectors)
    if vectors.ndim != 2:
        raise ValueError("unit_vectors must have shape (S,3)")

    if cKDTree is None:
        return legacy.neighbor_pairs_by_dot(vectors, max_angle_rad)

    tree = cKDTree(vectors)
    pairs = tree.query_pairs(
        angular_radius_to_chord(max_angle_rad) + 1e-12,
        output_type="ndarray",
    )
    if pairs.size == 0:
        return []
    return [(int(i), int(j)) for i, j in np.asarray(pairs)]


def coverage_counts_and_margins_local(
    satellite_vectors: np.ndarray,
    ground_points: np.ndarray,
    coverage_radius_rad: float,
    *,
    q: int = 1,
) -> LocalCoverageResult:
    """Compute exact local counts and q-th-nearest coverage margins.

    On the unit sphere, Euclidean chord distance ``d`` and dot product satisfy
    ``dot = 1 - d^2/2``.  The q-th nearest satellite therefore gives the exact
    q-th largest dot product without scanning all satellites per point.
    """

    satellites = _normalize(satellite_vectors)
    points = _normalize(ground_points)
    if satellites.ndim != 2 or points.ndim != 2:
        raise ValueError("satellite_vectors and ground_points must be 2-D")
    if q <= 0 or q > len(satellites):
        raise ValueError("q must lie in [1, number of satellites]")

    if cKDTree is None:
        from q2_coverage_margin import q_fold_margins_at_points

        dense = q_fold_margins_at_points(
            satellites,
            points,
            coverage_radius_rad,
            q=q,
        )
        return LocalCoverageResult(
            counts=dense.counts,
            margins=dense.margins,
            q=q,
            backend="dense-fallback",
        )

    tree = cKDTree(satellites)
    cover_chord = angular_radius_to_chord(coverage_radius_rad) + 1e-12
    neighborhoods = tree.query_ball_point(points, cover_chord)
    counts = np.fromiter((len(items) for items in neighborhoods), dtype=np.int32, count=len(points))

    distances, _indices = tree.query(points, k=q)
    distances = np.asarray(distances, dtype=float)
    if q == 1:
        qth_distances = distances.reshape(-1)
    else:
        qth_distances = distances[:, -1]
    qth_dots = 1.0 - 0.5 * np.square(qth_distances)
    margins = qth_dots - math.cos(coverage_radius_rad)

    return LocalCoverageResult(
        counts=counts,
        margins=margins,
        q=q,
        backend="scipy-cKDTree",
    )


def critical_points_at_time_kdtree(
    satellite_vectors: np.ndarray,
    coverage_radius_rad: float,
    region: legacy.LatLonRegion,
    *,
    include_region_corners: bool = True,
    include_region_boundary: bool = True,
    include_representatives: bool = True,
    representative_offset_rad: float = 1e-4,
    coordinate_tol: float = 1e-10,
) -> np.ndarray:
    """Generate the legacy critical-point set with KD-tree pair discovery."""

    satellites = _normalize(satellite_vectors)
    point_batches: list[np.ndarray] = []

    if include_region_corners:
        point_batches.append(legacy.region_corner_points(region))

    if include_region_boundary:
        for satellite in satellites:
            boundary = legacy.small_circle_region_boundary_intersections(
                satellite,
                coverage_radius_rad,
                region,
                atol=max(coordinate_tol, 1e-12),
            )
            if boundary.size:
                point_batches.append(boundary)

    if len(satellites) >= 2:
        max_pair_angle = min(math.pi, 2.0 * coverage_radius_rad)
        for i, j in neighbor_pairs_kdtree(satellites, max_pair_angle):
            intersections = legacy.small_circle_intersections(
                satellites[i],
                satellites[j],
                coverage_radius_rad,
                atol=max(coordinate_tol, 1e-12),
            )
            if not intersections.size:
                continue
            mask = legacy.points_in_latlon_box(
                intersections,
                region,
                tol_deg=max(1e-10, math.degrees(coordinate_tol)),
            )
            if np.any(mask):
                point_batches.append(intersections[mask])

    if not point_batches:
        return np.empty((0, 3), dtype=float)

    vertices = legacy.deduplicate_unit_vectors(
        np.vstack(point_batches),
        coordinate_tol=coordinate_tol,
    )
    if not include_representatives:
        return vertices

    representative_batches: list[np.ndarray] = []
    edge_points = legacy.region_edge_representative_points(
        vertices,
        region,
        inward_offset_deg=math.degrees(representative_offset_rad),
        coordinate_tol=coordinate_tol,
    )
    if edge_points.size:
        representative_batches.append(edge_points)

    cos_radius = math.cos(coverage_radius_rad)
    boundary_tol = max(1e-7, 10.0 * coordinate_tol)
    for satellite in satellites:
        on_circle = np.abs(vertices @ satellite - cos_radius) <= boundary_tol
        if np.count_nonzero(on_circle) < 2:
            continue
        arc_points = legacy.coverage_arc_representative_points(
            satellite,
            vertices[on_circle],
            coverage_radius_rad,
            offset_rad=representative_offset_rad,
            coordinate_tol=coordinate_tol,
        )
        if not arc_points.size:
            continue
        mask = legacy.points_in_latlon_box(
            arc_points,
            region,
            tol_deg=max(1e-10, math.degrees(coordinate_tol)),
        )
        if np.any(mask):
            representative_batches.append(arc_points[mask])

    if not representative_batches:
        return vertices
    return legacy.deduplicate_unit_vectors(
        np.vstack([vertices, *representative_batches]),
        coordinate_tol=coordinate_tol,
    )


def _longest_false_gap_s(values: np.ndarray, times_s: np.ndarray) -> float:
    values = np.asarray(values, dtype=bool)
    if not len(values):
        return 0.0
    dt = float(np.median(np.diff(times_s))) if len(times_s) >= 2 else 0.0
    longest = current = 0
    for value in values:
        if value:
            longest = max(longest, current)
            current = 0
        else:
            current += 1
    return float(max(longest, current) * dt)


def evaluate_satellite_snapshots_kdtree(
    satellite_vectors: np.ndarray,
    times_s: np.ndarray,
    coverage_radius_rad: float,
    region: legacy.LatLonRegion,
    *,
    params: object | None = None,
    q: int = 1,
    include_representatives: bool = True,
    representative_offset_rad: float = 1e-4,
    stop_if_margin_below: float | None = None,
    coordinate_tol: float = 1e-10,
) -> KDTreeCoverageResult:
    """Evaluate a satellite time series with KD-tree critical points."""

    snapshots = _normalize(satellite_vectors)
    times = np.asarray(times_s, dtype=float)
    if snapshots.ndim != 3 or snapshots.shape[1] != len(times):
        raise ValueError("satellite_vectors must have shape (S,L,3)")

    min_counts: list[int] = []
    min_margins: list[float] = []
    point_counts: list[int] = []
    evaluated_times: list[float] = []
    worst_points: list[np.ndarray | None] = []
    stopped_early = False
    backend = "scipy-cKDTree" if cKDTree is not None else "dense-fallback"

    for time_index, time_s in enumerate(times):
        satellites_t = snapshots[:, time_index, :]
        points = critical_points_at_time_kdtree(
            satellites_t,
            coverage_radius_rad,
            region,
            include_representatives=include_representatives,
            representative_offset_rad=representative_offset_rad,
            coordinate_tol=coordinate_tol,
        )
        point_counts.append(int(len(points)))
        evaluated_times.append(float(time_s))

        if not len(points):
            min_counts.append(0)
            min_margins.append(-math.inf)
            worst_points.append(None)
        else:
            local = coverage_counts_and_margins_local(
                satellites_t,
                points,
                coverage_radius_rad,
                q=q,
            )
            worst_index = local.worst_point_index
            min_counts.append(local.min_count)
            min_margins.append(local.min_margin)
            worst_points.append(points[worst_index].copy())
            backend = local.backend

        if stop_if_margin_below is not None and min_margins[-1] < stop_if_margin_below:
            stopped_early = True
            break

    count_array = np.asarray(min_counts, dtype=np.int32)
    margin_array = np.asarray(min_margins, dtype=float)
    point_count_array = np.asarray(point_counts, dtype=np.int32)
    evaluated_times_array = np.asarray(evaluated_times, dtype=float)

    if len(margin_array):
        worst_time_index = int(np.argmin(margin_array))
        min_margin = float(margin_array[worst_time_index])
        c_min = int(np.min(count_array))
        worst_point = worst_points[worst_time_index]
    else:
        worst_time_index = -1
        min_margin = -math.inf
        c_min = 0
        worst_point = None

    covered_once = count_array >= 1
    covered_twice = count_array >= 2
    return KDTreeCoverageResult(
        params=params,
        times_s=evaluated_times_array,
        min_counts_by_time=count_array,
        min_margins_by_time=margin_array,
        critical_point_counts_by_time=point_count_array,
        c_min=c_min,
        min_margin=min_margin,
        single_coverage_time_rate=float(np.mean(covered_once)) if len(count_array) else 0.0,
        strict_double_time_rate=float(np.mean(covered_twice)) if len(count_array) else 0.0,
        max_uncovered_gap_s=_longest_false_gap_s(covered_once, evaluated_times_array),
        worst_time_index=worst_time_index,
        worst_point=worst_point,
        stopped_early=stopped_early,
        evaluated_time_steps=len(evaluated_times_array),
        backend=backend,
    )


def evaluate_constellation_kdtree(
    params: q2.ConstellationParams,
    times_s: np.ndarray,
    *,
    config: q2.CoverageConfig | None = None,
    region: legacy.LatLonRegion | None = None,
    q: int = 1,
    include_representatives: bool = True,
    representative_offset_rad: float = 1e-4,
    stop_if_margin_below: float | None = None,
) -> KDTreeCoverageResult:
    cfg = config or q2.CoverageConfig()
    target_region = region or legacy.LatLonRegion()
    times = np.asarray(times_s, dtype=float)
    snapshots = q2.satellite_unit_vectors(params, times, cfg)
    return evaluate_satellite_snapshots_kdtree(
        snapshots,
        times,
        cfg.coverage_angle_rad,
        target_region,
        params=params,
        q=q,
        include_representatives=include_representatives,
        representative_offset_rad=representative_offset_rad,
        stop_if_margin_below=stop_if_margin_below,
    )
