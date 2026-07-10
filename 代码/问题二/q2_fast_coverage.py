"""Problem 2 fast geometric helpers for LEO coverage.

This module is the first implementation step of the accelerated algorithm
described in the design note.  It intentionally keeps the API small:

1. filter nearby satellite-centre pairs by angular distance;
2. compute intersections of two equal-radius spherical coverage boundaries;
3. convert and filter candidate points in a latitude-longitude target box;
4. generate the first version of single-time critical points.

The functions are pure NumPy/Python and avoid allocating an ``S x K x L``
coverage tensor, which is the main memory risk in the original grid method.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class LatLonRegion:
    """Closed latitude-longitude rectangle in degrees."""

    lat_min_deg: float = 4.0
    lat_max_deg: float = 53.0
    lon_min_deg: float = 73.0
    lon_max_deg: float = 135.0

    def __post_init__(self) -> None:
        if self.lat_min_deg > self.lat_max_deg:
            raise ValueError("lat_min_deg must be <= lat_max_deg")
        if self.lon_min_deg > self.lon_max_deg:
            raise ValueError("lon_min_deg must be <= lon_max_deg")
        if self.lat_min_deg < -90.0 or self.lat_max_deg > 90.0:
            raise ValueError("latitude bounds must lie in [-90, 90] degrees")
        if self.lon_min_deg < -180.0 or self.lon_max_deg > 180.0:
            raise ValueError("longitude bounds must lie in [-180, 180] degrees")


@dataclass(frozen=True)
class FastCoverageResult:
    """Fast critical-point coverage summary over a time sequence."""

    params: object | None
    times_s: np.ndarray
    min_counts_by_time: np.ndarray
    critical_point_counts_by_time: np.ndarray
    c_min: int
    single_coverage_time_rate: float
    strict_double_time_rate: float
    max_uncovered_gap_s: float
    worst_time_index: int
    stopped_early: bool = False
    evaluated_time_steps: int = 0


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Return row-wise unit vectors.

    Parameters
    ----------
    vectors:
        Array with shape ``(..., 3)``.

    Raises
    ------
    ValueError
        If the final dimension is not 3 or any vector has zero norm.
    """

    arr = np.asarray(vectors, dtype=float)
    if arr.shape[-1:] != (3,):
        raise ValueError("vectors must have final dimension 3")

    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    if np.any(norms == 0.0):
        raise ValueError("zero-length vector cannot be normalized")
    return arr / norms


def latlon_to_unit(lat_deg: float | np.ndarray, lon_deg: float | np.ndarray) -> np.ndarray:
    """Convert geodetic latitude-longitude degrees to unit sphere vectors.

    The current problem uses spherical-Earth coverage geometry, so this is a
    geocentric spherical conversion rather than an ellipsoidal WGS-84 model.
    Scalars return a shape ``(3,)`` vector; arrays broadcast to ``(..., 3)``.
    """

    lat = np.deg2rad(np.asarray(lat_deg, dtype=float))
    lon = np.deg2rad(np.asarray(lon_deg, dtype=float))
    cos_lat = np.cos(lat)
    return np.stack(
        [cos_lat * np.cos(lon), cos_lat * np.sin(lon), np.sin(lat)],
        axis=-1,
    )


def unit_to_latlon(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert unit or non-unit 3D vectors to latitude and longitude degrees."""

    unit = normalize_vectors(vectors)
    z = np.clip(unit[..., 2], -1.0, 1.0)
    lat = np.rad2deg(np.arcsin(z))
    lon = np.rad2deg(np.arctan2(unit[..., 1], unit[..., 0]))
    return lat, lon


def points_in_latlon_box(
    points: np.ndarray,
    region: LatLonRegion,
    *,
    tol_deg: float = 1e-10,
) -> np.ndarray:
    """Return a boolean mask for points inside a closed lat-lon rectangle."""

    lat, lon = unit_to_latlon(points)
    return (
        (lat >= region.lat_min_deg - tol_deg)
        & (lat <= region.lat_max_deg + tol_deg)
        & (lon >= region.lon_min_deg - tol_deg)
        & (lon <= region.lon_max_deg + tol_deg)
    )


def region_corner_points(region: LatLonRegion) -> np.ndarray:
    """Return the four corner points of a latitude-longitude rectangle."""

    return np.vstack(
        [
            latlon_to_unit(region.lat_min_deg, region.lon_min_deg),
            latlon_to_unit(region.lat_min_deg, region.lon_max_deg),
            latlon_to_unit(region.lat_max_deg, region.lon_min_deg),
            latlon_to_unit(region.lat_max_deg, region.lon_max_deg),
        ]
    )


def deduplicate_unit_vectors(
    points: np.ndarray,
    *,
    coordinate_tol: float = 1e-10,
) -> np.ndarray:
    """Deduplicate unit-sphere points by rounded Cartesian coordinates."""

    arr = np.asarray(points, dtype=float)
    if arr.size == 0:
        return np.empty((0, 3), dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("points must have shape (n, 3)")
    if coordinate_tol <= 0.0:
        raise ValueError("coordinate_tol must be positive")

    unit = normalize_vectors(arr)
    keys = np.round(unit / coordinate_tol).astype(np.int64)
    _, first_indices = np.unique(keys, axis=0, return_index=True)
    return unit[np.sort(first_indices)]


def coverage_counts_at_points(
    satellite_vectors: np.ndarray,
    ground_points: np.ndarray,
    coverage_radius_rad: float,
    *,
    block_size: int = 4096,
    atol: float = 1e-12,
) -> np.ndarray:
    """Count visible satellites for each target point.

    This is the point-set analogue of the grid coverage count.  It keeps only a
    ``block_size x S`` dot-product block in memory, so it is suitable for the
    critical-point candidate set used by the accelerated method.
    """

    if coverage_radius_rad < 0.0 or coverage_radius_rad > math.pi:
        raise ValueError("coverage_radius_rad must lie in [0, pi]")
    if block_size <= 0:
        raise ValueError("block_size must be positive")

    satellites = normalize_vectors(satellite_vectors)
    points = normalize_vectors(ground_points)
    if satellites.ndim != 2:
        raise ValueError("satellite_vectors must have shape (n, 3)")
    if points.ndim != 2:
        raise ValueError("ground_points must have shape (m, 3)")

    threshold = math.cos(coverage_radius_rad) - atol
    counts = np.zeros(points.shape[0], dtype=np.int32)
    for start in range(0, points.shape[0], block_size):
        end = min(start + block_size, points.shape[0])
        dots = points[start:end] @ satellites.T
        counts[start:end] = np.count_nonzero(dots >= threshold, axis=1)
    return counts


def _longest_uncovered_gap_s(covered_by_time: np.ndarray, times_s: np.ndarray) -> float:
    """Longest consecutive uncovered run measured with median time step."""

    covered = np.asarray(covered_by_time, dtype=bool)
    if covered.ndim != 1:
        raise ValueError("covered_by_time must be one-dimensional")
    if covered.size == 0:
        return 0.0

    times = np.asarray(times_s, dtype=float)
    if times.size >= 2:
        dt_s = float(np.median(np.diff(times)))
    else:
        dt_s = 0.0

    max_run = 0
    current = 0
    for is_covered in covered:
        if is_covered:
            max_run = max(max_run, current)
            current = 0
        else:
            current += 1
    max_run = max(max_run, current)
    return float(max_run * dt_s)


def neighbor_pairs_by_dot(
    unit_vectors: np.ndarray,
    max_angle_rad: float,
    *,
    block_size: int = 512,
    atol: float = 1e-12,
) -> list[tuple[int, int]]:
    """List unordered vector pairs whose angular distance is at most a limit.

    The implementation uses block matrix products instead of a full ``S x S``
    distance matrix.  For ``S=1600`` and ``block_size=512`` the largest working
    dot-product block is about 6.6 MB in float64, so it is safe under a 16 GB
    memory budget.
    """

    if max_angle_rad < 0.0:
        raise ValueError("max_angle_rad must be non-negative")
    if block_size <= 0:
        raise ValueError("block_size must be positive")

    vectors = normalize_vectors(unit_vectors)
    if vectors.ndim != 2:
        raise ValueError("unit_vectors must have shape (n, 3)")

    n = vectors.shape[0]
    threshold = math.cos(max_angle_rad) - atol
    pairs: list[tuple[int, int]] = []

    for start in range(0, n, block_size):
        end = min(start + block_size, n)
        dots = vectors[start:end] @ vectors.T
        for local_i, row in enumerate(dots):
            i = start + local_i
            candidate_js = np.flatnonzero(row[i + 1 :] >= threshold) + i + 1
            pairs.extend((i, int(j)) for j in candidate_js)

    return pairs


def small_circle_intersections(
    center_a: np.ndarray,
    center_b: np.ndarray,
    radius_rad: float,
    *,
    atol: float = 1e-12,
) -> np.ndarray:
    """Intersect two equal-radius small circles on the unit sphere.

    A coverage boundary with angular radius ``theta`` and centre ``a`` is

    ``a · p = cos(theta),  ||p|| = 1``.

    For two centres ``a`` and ``b`` with the same radius, a particular solution
    of the two linear constraints is

    ``p0 = cos(theta) (a + b) / (1 + a · b)``.

    The remaining degree of freedom is along ``a x b``.  Depending on geometry,
    the result contains zero, one (tangent), or two points.
    """

    if radius_rad < 0.0 or radius_rad > math.pi:
        raise ValueError("radius_rad must lie in [0, pi]")

    a = normalize_vectors(np.asarray(center_a, dtype=float))
    b = normalize_vectors(np.asarray(center_b, dtype=float))
    if a.shape != (3,) or b.shape != (3,):
        raise ValueError("center_a and center_b must be 3D vectors")

    dot_ab = float(np.clip(np.dot(a, b), -1.0, 1.0))
    cross = np.cross(a, b)
    cross_norm = float(np.linalg.norm(cross))

    # Coincident or antipodal centres are degenerate for the two-circle
    # intersection formula.  The accelerated coverage test can ignore these:
    # coincident boundaries do not create isolated critical vertices, and
    # antipodal equal-radius boundaries are either empty or infinitely many.
    if cross_norm <= atol or abs(1.0 + dot_ab) <= atol:
        return np.empty((0, 3), dtype=float)

    cos_radius = math.cos(radius_rad)
    p0 = cos_radius * (a + b) / (1.0 + dot_ab)
    height_sq = 1.0 - float(np.dot(p0, p0))

    if height_sq < -atol:
        return np.empty((0, 3), dtype=float)

    if abs(height_sq) <= atol:
        return normalize_vectors(p0).reshape(1, 3)

    direction = cross / cross_norm
    height = math.sqrt(max(0.0, height_sq))
    points = np.vstack([p0 + height * direction, p0 - height * direction])
    return normalize_vectors(points)


def _normalize_lon_deg(lon_deg: float) -> float:
    """Normalize longitude to [-180, 180]."""

    normalized = (lon_deg + 180.0) % 360.0 - 180.0
    if math.isclose(normalized, -180.0, abs_tol=1e-12) and lon_deg > 0.0:
        return 180.0
    return normalized


def _empty_points() -> np.ndarray:
    return np.empty((0, 3), dtype=float)


def small_circle_latitude_intersections(
    center: np.ndarray,
    radius_rad: float,
    lat_deg: float,
    lon_min_deg: float,
    lon_max_deg: float,
    *,
    atol: float = 1e-12,
) -> np.ndarray:
    """Intersect a coverage small circle with a constant-latitude segment."""

    c = normalize_vectors(np.asarray(center, dtype=float))
    if c.shape != (3,):
        raise ValueError("center must be a 3D vector")

    lat = math.radians(lat_deg)
    cos_lat = math.cos(lat)
    sin_lat = math.sin(lat)
    cos_radius = math.cos(radius_rad)

    a = c[0] * cos_lat
    b = c[1] * cos_lat
    d = cos_radius - c[2] * sin_lat
    amplitude = math.hypot(a, b)
    if amplitude <= atol or abs(d) > amplitude + atol:
        return _empty_points()

    ratio = float(np.clip(d / amplitude, -1.0, 1.0))
    base = math.atan2(b, a)
    delta = math.acos(ratio)

    points: list[np.ndarray] = []
    for lon_rad in (base + delta, base - delta):
        lon_deg = _normalize_lon_deg(math.degrees(lon_rad))
        if lon_min_deg - 1e-10 <= lon_deg <= lon_max_deg + 1e-10:
            points.append(latlon_to_unit(lat_deg, lon_deg))

    if not points:
        return _empty_points()
    return deduplicate_unit_vectors(np.vstack(points), coordinate_tol=max(atol, 1e-12))


def small_circle_longitude_intersections(
    center: np.ndarray,
    radius_rad: float,
    lon_deg: float,
    lat_min_deg: float,
    lat_max_deg: float,
    *,
    atol: float = 1e-12,
) -> np.ndarray:
    """Intersect a coverage small circle with a constant-longitude segment."""

    c = normalize_vectors(np.asarray(center, dtype=float))
    if c.shape != (3,):
        raise ValueError("center must be a 3D vector")

    lon = math.radians(lon_deg)
    cos_radius = math.cos(radius_rad)
    h = c[0] * math.cos(lon) + c[1] * math.sin(lon)
    amplitude = math.hypot(h, c[2])
    if amplitude <= atol or abs(cos_radius) > amplitude + atol:
        return _empty_points()

    ratio = float(np.clip(cos_radius / amplitude, -1.0, 1.0))
    base = math.atan2(c[2], h)
    delta = math.acos(ratio)

    points: list[np.ndarray] = []
    for lat_rad in (base + delta, base - delta):
        lat_deg = math.degrees(lat_rad)
        if lat_min_deg - 1e-10 <= lat_deg <= lat_max_deg + 1e-10:
            points.append(latlon_to_unit(lat_deg, lon_deg))

    if not points:
        return _empty_points()
    return deduplicate_unit_vectors(np.vstack(points), coordinate_tol=max(atol, 1e-12))


def small_circle_region_boundary_intersections(
    center: np.ndarray,
    radius_rad: float,
    region: LatLonRegion,
    *,
    atol: float = 1e-12,
) -> np.ndarray:
    """Intersect one coverage boundary with the target rectangle boundary."""

    batches = [
        small_circle_latitude_intersections(
            center,
            radius_rad,
            region.lat_min_deg,
            region.lon_min_deg,
            region.lon_max_deg,
            atol=atol,
        ),
        small_circle_latitude_intersections(
            center,
            radius_rad,
            region.lat_max_deg,
            region.lon_min_deg,
            region.lon_max_deg,
            atol=atol,
        ),
        small_circle_longitude_intersections(
            center,
            radius_rad,
            region.lon_min_deg,
            region.lat_min_deg,
            region.lat_max_deg,
            atol=atol,
        ),
        small_circle_longitude_intersections(
            center,
            radius_rad,
            region.lon_max_deg,
            region.lat_min_deg,
            region.lat_max_deg,
            atol=atol,
        ),
    ]
    non_empty = [batch for batch in batches if batch.size > 0]
    if not non_empty:
        return _empty_points()

    points = np.vstack(non_empty)
    mask = points_in_latlon_box(
        points,
        region,
        tol_deg=max(1e-10, math.degrees(atol)),
    )
    if not np.any(mask):
        return _empty_points()
    return deduplicate_unit_vectors(points[mask], coordinate_tol=max(atol, 1e-12))


def _small_circle_basis(center: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build an orthonormal basis of the plane perpendicular to ``center``."""

    c = normalize_vectors(np.asarray(center, dtype=float))
    reference = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(c, reference))) > 0.9:
        reference = np.array([1.0, 0.0, 0.0])
    e1 = normalize_vectors(reference - float(np.dot(reference, c)) * c)
    e2 = np.cross(c, e1)
    return e1, e2


def coverage_arc_representative_points(
    center: np.ndarray,
    boundary_points: np.ndarray,
    radius_rad: float,
    *,
    offset_rad: float = 1e-4,
    coordinate_tol: float = 1e-10,
) -> np.ndarray:
    """Sample both sides of small-circle arcs between adjacent boundary vertices.

    Vertex-only checks may miss an open cell whose boundary consists of
    coverage-circle arcs.  For each neighbouring pair of vertices on the same
    coverage circle, this function samples the arc midpoint slightly inside and
    slightly outside the coverage cap.
    """

    if radius_rad <= 0.0 or radius_rad >= math.pi:
        return _empty_points()
    if offset_rad <= 0.0:
        raise ValueError("offset_rad must be positive")

    c = normalize_vectors(np.asarray(center, dtype=float))
    vertices = np.asarray(boundary_points, dtype=float)
    if vertices.size == 0:
        return _empty_points()
    vertices = normalize_vectors(vertices)
    if vertices.ndim != 2:
        raise ValueError("boundary_points must have shape (n, 3)")

    cos_radius = math.cos(radius_rad)
    sin_radius = math.sin(radius_rad)
    boundary_tol = max(1e-7, 10.0 * coordinate_tol)
    on_boundary = np.abs(vertices @ c - cos_radius) <= boundary_tol
    vertices = deduplicate_unit_vectors(
        vertices[on_boundary],
        coordinate_tol=coordinate_tol,
    )
    if len(vertices) < 2 or abs(sin_radius) <= coordinate_tol:
        return _empty_points()

    e1, e2 = _small_circle_basis(c)
    directions = normalize_vectors(vertices - cos_radius * c)
    angles = np.arctan2(directions @ e2, directions @ e1)
    order = np.argsort(angles)
    sorted_angles = angles[order]

    points: list[np.ndarray] = []
    n = len(sorted_angles)
    for idx, angle in enumerate(sorted_angles):
        next_angle = sorted_angles[(idx + 1) % n]
        if idx == n - 1:
            next_angle += 2.0 * math.pi
        gap = next_angle - angle
        if gap <= coordinate_tol:
            continue

        mid_angle = angle + 0.5 * gap
        u_mid = math.cos(mid_angle) * e1 + math.sin(mid_angle) * e2
        for sampled_radius in (radius_rad - offset_rad, radius_rad + offset_rad):
            if 0.0 <= sampled_radius <= math.pi:
                points.append(
                    math.cos(sampled_radius) * c
                    + math.sin(sampled_radius) * u_mid
                )

    if not points:
        return _empty_points()
    return deduplicate_unit_vectors(
        np.vstack(points),
        coordinate_tol=coordinate_tol,
    )


def region_edge_representative_points(
    vertices: np.ndarray,
    region: LatLonRegion,
    *,
    inward_offset_deg: float = 1e-4,
    edge_tol_deg: float = 1e-7,
    coordinate_tol: float = 1e-10,
) -> np.ndarray:
    """Sample intervals on target-region edges between adjacent vertices."""

    points = normalize_vectors(vertices)
    if points.size == 0:
        return _empty_points()
    if points.ndim != 2:
        raise ValueError("vertices must have shape (n, 3)")
    if inward_offset_deg < 0.0:
        raise ValueError("inward_offset_deg must be non-negative")

    lat, lon = unit_to_latlon(points)
    reps: list[np.ndarray] = []

    def add_lat_edge(lat_edge: float, inward_sign: float) -> None:
        mask = (
            (np.abs(lat - lat_edge) <= edge_tol_deg)
            & (lon >= region.lon_min_deg - edge_tol_deg)
            & (lon <= region.lon_max_deg + edge_tol_deg)
        )
        values = np.unique(np.round(lon[mask] / edge_tol_deg).astype(np.int64))
        edge_lons = np.sort(values.astype(float) * edge_tol_deg)
        if len(edge_lons) < 2:
            return
        for left, right in zip(edge_lons[:-1], edge_lons[1:]):
            if right - left <= edge_tol_deg:
                continue
            mid_lon = 0.5 * (left + right)
            reps.append(latlon_to_unit(lat_edge, mid_lon))
            shifted_lat = lat_edge + inward_sign * inward_offset_deg
            if region.lat_min_deg <= shifted_lat <= region.lat_max_deg:
                reps.append(latlon_to_unit(shifted_lat, mid_lon))

    def add_lon_edge(lon_edge: float, inward_sign: float) -> None:
        mask = (
            (np.abs(lon - lon_edge) <= edge_tol_deg)
            & (lat >= region.lat_min_deg - edge_tol_deg)
            & (lat <= region.lat_max_deg + edge_tol_deg)
        )
        values = np.unique(np.round(lat[mask] / edge_tol_deg).astype(np.int64))
        edge_lats = np.sort(values.astype(float) * edge_tol_deg)
        if len(edge_lats) < 2:
            return
        for low, high in zip(edge_lats[:-1], edge_lats[1:]):
            if high - low <= edge_tol_deg:
                continue
            mid_lat = 0.5 * (low + high)
            reps.append(latlon_to_unit(mid_lat, lon_edge))
            shifted_lon = lon_edge + inward_sign * inward_offset_deg
            if region.lon_min_deg <= shifted_lon <= region.lon_max_deg:
                reps.append(latlon_to_unit(mid_lat, shifted_lon))

    add_lat_edge(region.lat_min_deg, inward_sign=1.0)
    add_lat_edge(region.lat_max_deg, inward_sign=-1.0)
    add_lon_edge(region.lon_min_deg, inward_sign=1.0)
    add_lon_edge(region.lon_max_deg, inward_sign=-1.0)

    if not reps:
        return _empty_points()
    return deduplicate_unit_vectors(
        np.vstack(reps),
        coordinate_tol=coordinate_tol,
    )


def critical_points_at_time(
    satellite_vectors: np.ndarray,
    coverage_radius_rad: float,
    region: LatLonRegion,
    *,
    block_size: int = 512,
    include_region_corners: bool = True,
    include_region_boundary: bool = True,
    include_representatives: bool = True,
    representative_offset_rad: float = 1e-4,
    coordinate_tol: float = 1e-10,
) -> np.ndarray:
    """Generate first-version critical points for one time snapshot.

    The current implementation returns:

    1. target-region corner points;
    2. intersections between a satellite coverage boundary and the target
       rectangle boundary;
    3. intersections of two satellite coverage boundaries that fall inside the
       target latitude-longitude rectangle.
    4. optional representative points on both sides of coverage arcs and target
       boundary intervals, used to detect open cells not represented by
       vertices alone.
    """

    if coverage_radius_rad < 0.0 or coverage_radius_rad > math.pi:
        raise ValueError("coverage_radius_rad must lie in [0, pi]")

    satellites = normalize_vectors(satellite_vectors)
    if satellites.ndim != 2:
        raise ValueError("satellite_vectors must have shape (n, 3)")

    point_batches: list[np.ndarray] = []
    if include_region_corners:
        point_batches.append(region_corner_points(region))

    if include_region_boundary:
        for satellite in satellites:
            boundary_points = small_circle_region_boundary_intersections(
                satellite,
                coverage_radius_rad,
                region,
                atol=max(coordinate_tol, 1e-12),
            )
            if boundary_points.size > 0:
                point_batches.append(boundary_points)

    if satellites.shape[0] >= 2:
        max_pair_angle = min(math.pi, 2.0 * coverage_radius_rad)
        pairs = neighbor_pairs_by_dot(
            satellites,
            max_pair_angle,
            block_size=block_size,
            atol=max(coordinate_tol, 1e-12),
        )
        for i, j in pairs:
            intersections = small_circle_intersections(
                satellites[i],
                satellites[j],
                coverage_radius_rad,
                atol=max(coordinate_tol, 1e-12),
            )
            if intersections.size == 0:
                continue
            mask = points_in_latlon_box(
                intersections,
                region,
                tol_deg=max(1e-10, math.degrees(coordinate_tol)),
            )
            if np.any(mask):
                point_batches.append(intersections[mask])

    if not point_batches:
        return np.empty((0, 3), dtype=float)
    vertices = deduplicate_unit_vectors(
        np.vstack(point_batches),
        coordinate_tol=coordinate_tol,
    )

    if not include_representatives:
        return vertices

    representative_batches: list[np.ndarray] = []
    edge_points = region_edge_representative_points(
        vertices,
        region,
        inward_offset_deg=math.degrees(representative_offset_rad),
        coordinate_tol=coordinate_tol,
    )
    if edge_points.size > 0:
        representative_batches.append(edge_points)

    cos_radius = math.cos(coverage_radius_rad)
    boundary_tol = max(1e-7, 10.0 * coordinate_tol)
    for satellite in satellites:
        on_circle = np.abs(vertices @ satellite - cos_radius) <= boundary_tol
        if np.count_nonzero(on_circle) < 2:
            continue
        arc_points = coverage_arc_representative_points(
            satellite,
            vertices[on_circle],
            coverage_radius_rad,
            offset_rad=representative_offset_rad,
            coordinate_tol=coordinate_tol,
        )
        if arc_points.size == 0:
            continue
        mask = points_in_latlon_box(
            arc_points,
            region,
            tol_deg=max(1e-10, math.degrees(coordinate_tol)),
        )
        if np.any(mask):
            representative_batches.append(arc_points[mask])

    if not representative_batches:
        return vertices
    return deduplicate_unit_vectors(
        np.vstack([vertices, *representative_batches]),
        coordinate_tol=coordinate_tol,
    )


def evaluate_satellite_snapshots_fast(
    satellite_vectors: np.ndarray,
    times_s: np.ndarray,
    coverage_radius_rad: float,
    region: LatLonRegion,
    *,
    params: object | None = None,
    block_size: int = 512,
    count_block_size: int = 4096,
    include_representatives: bool = True,
    representative_offset_rad: float = 1e-4,
    stop_if_min_count_below: int | None = None,
    coordinate_tol: float = 1e-10,
) -> FastCoverageResult:
    """Evaluate a satellite time series using critical-point samples.

    Parameters
    ----------
    satellite_vectors:
        Unit-vector snapshots with shape ``(S, L, 3)``, where ``S`` is the
        number of satellites and ``L`` is the number of time steps.
    times_s:
        Time grid with length ``L``.
    coverage_radius_rad:
        Ground coverage angular radius.
    region:
        Target latitude-longitude rectangle.
    """

    snapshots = normalize_vectors(satellite_vectors)
    if snapshots.ndim != 3:
        raise ValueError("satellite_vectors must have shape (S, L, 3)")
    times = np.asarray(times_s, dtype=float)
    if times.ndim != 1:
        raise ValueError("times_s must be one-dimensional")
    if snapshots.shape[1] != len(times):
        raise ValueError("time dimension of satellite_vectors must match times_s")

    min_counts_list: list[int] = []
    point_counts_list: list[int] = []
    evaluated_times: list[float] = []
    stopped_early = False

    for time_index in range(len(times)):
        satellites_t = snapshots[:, time_index, :]
        points = critical_points_at_time(
            satellites_t,
            coverage_radius_rad,
            region,
            block_size=block_size,
            include_representatives=include_representatives,
            representative_offset_rad=representative_offset_rad,
            coordinate_tol=coordinate_tol,
        )
        point_counts_list.append(int(len(points)))
        evaluated_times.append(float(times[time_index]))
        if len(points) == 0:
            min_count_t = 0
        else:
            counts = coverage_counts_at_points(
                satellites_t,
                points,
                coverage_radius_rad,
                block_size=count_block_size,
                atol=max(coordinate_tol, 1e-12),
            )
            min_count_t = int(np.min(counts))
        min_counts_list.append(min_count_t)

        if stop_if_min_count_below is not None and min_count_t < stop_if_min_count_below:
            stopped_early = True
            break

    min_counts = np.asarray(min_counts_list, dtype=np.int32)
    point_counts = np.asarray(point_counts_list, dtype=np.int32)
    evaluated_times_array = np.asarray(evaluated_times, dtype=float)

    if len(min_counts) == 0:
        c_min = 0
        worst_time_index = -1
    else:
        c_min = int(np.min(min_counts))
        worst_time_index = int(np.argmin(min_counts))

    covered_once = min_counts >= 1
    covered_twice = min_counts >= 2
    return FastCoverageResult(
        params=params,
        times_s=evaluated_times_array,
        min_counts_by_time=min_counts,
        critical_point_counts_by_time=point_counts,
        c_min=c_min,
        single_coverage_time_rate=float(np.mean(covered_once)) if len(evaluated_times_array) else 0.0,
        strict_double_time_rate=float(np.mean(covered_twice)) if len(evaluated_times_array) else 0.0,
        max_uncovered_gap_s=_longest_uncovered_gap_s(covered_once, evaluated_times_array),
        worst_time_index=worst_time_index,
        stopped_early=stopped_early,
        evaluated_time_steps=int(len(evaluated_times_array)),
    )


def evaluate_constellation_fast(
    params: object,
    times_s: np.ndarray,
    *,
    config: object | None = None,
    region: LatLonRegion | None = None,
    block_size: int = 512,
    count_block_size: int = 4096,
    include_representatives: bool = True,
    representative_offset_rad: float = 1e-4,
    stop_if_min_count_below: int | None = None,
    coordinate_tol: float = 1e-10,
) -> FastCoverageResult:
    """Evaluate a Walker-style constellation with the fast critical-point method."""

    from q2_constellation import CoverageConfig, satellite_unit_vectors

    cfg = config or CoverageConfig()
    target_region = region or LatLonRegion()
    times = np.asarray(times_s, dtype=float)
    satellite_vectors = satellite_unit_vectors(params, times, cfg)
    return evaluate_satellite_snapshots_fast(
        satellite_vectors,
        times,
        cfg.coverage_angle_rad,
        target_region,
        params=params,
        block_size=block_size,
        count_block_size=count_block_size,
        include_representatives=include_representatives,
        representative_offset_rad=representative_offset_rad,
        stop_if_min_count_below=stop_if_min_count_below,
        coordinate_tol=coordinate_tol,
    )
