"""Conservative space-time box verification for continuous q-fold coverage.

The verifier uses triangle-inequality bounds in angular distance.  It can return
``covered`` (certificate under the stated spherical/circular-orbit model),
``uncovered`` (a rigorously rejected box), or ``inconclusive`` when the chosen
subdivision budget/tolerances are insufficient.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import numpy as np

import q2_constellation as q2
import q2_fast_coverage as fast


@dataclass(frozen=True)
class SpaceTimeBox:
    lat_min_deg: float
    lat_max_deg: float
    lon_min_deg: float
    lon_max_deg: float
    time_min_s: float
    time_max_s: float
    depth: int = 0

    def validate(self) -> None:
        if self.lat_max_deg < self.lat_min_deg:
            raise ValueError("invalid latitude interval")
        if self.lon_max_deg < self.lon_min_deg:
            raise ValueError("invalid longitude interval")
        if self.time_max_s < self.time_min_s:
            raise ValueError("invalid time interval")

    @property
    def center_lat_deg(self) -> float:
        return 0.5 * (self.lat_min_deg + self.lat_max_deg)

    @property
    def center_lon_deg(self) -> float:
        return 0.5 * (self.lon_min_deg + self.lon_max_deg)

    @property
    def center_time_s(self) -> float:
        return 0.5 * (self.time_min_s + self.time_max_s)

    @property
    def time_half_width_s(self) -> float:
        return 0.5 * (self.time_max_s - self.time_min_s)

    @property
    def lat_span_deg(self) -> float:
        return self.lat_max_deg - self.lat_min_deg

    @property
    def lon_span_deg(self) -> float:
        return self.lon_max_deg - self.lon_min_deg


@dataclass(frozen=True)
class BoxClassification:
    status: str
    guaranteed_count: int
    possible_count: int
    uncertainty_rad: float
    center_distances_rad: np.ndarray


@dataclass(frozen=True)
class ContinuousCoverageCertificate:
    status: str
    q: int
    processed_boxes: int
    covered_boxes: int
    uncertain_boxes: int
    max_depth: int
    failure_box: SpaceTimeBox | None
    unresolved_boxes: tuple[SpaceTimeBox, ...]
    message: str


def conservative_space_radius_rad(box: SpaceTimeBox) -> float:
    """Conservative angular radius for a latitude-longitude rectangle.

    Any point can be reached from the centre by first moving along a meridian
    and then along a parallel.  Replacing the parallel factor by one gives the
    safe upper bound ``half_lat_span + half_lon_span``.
    """

    box.validate()
    return 0.5 * math.radians(box.lat_span_deg + box.lon_span_deg)


def satellite_angular_speed_bound_rad_s(
    config: q2.CoverageConfig | None = None,
) -> float:
    """Conservative ECEF unit-vector angular speed bound ``n + omega_E``."""

    cfg = config or q2.CoverageConfig()
    return cfg.mean_motion_rad_s + cfg.earth_rotation_rad_s


def classify_space_time_box(
    params: q2.ConstellationParams,
    box: SpaceTimeBox,
    *,
    q: int = 1,
    config: q2.CoverageConfig | None = None,
) -> BoxClassification:
    """Classify a box as covered, uncovered, or uncertain."""

    box.validate()
    cfg = config or q2.CoverageConfig()
    if q <= 0 or q > params.total_satellites:
        raise ValueError("q must lie in [1, total satellites]")

    center_point = fast.latlon_to_unit(box.center_lat_deg, box.center_lon_deg)
    satellites = q2.satellite_unit_vectors(
        params,
        np.array([box.center_time_s], dtype=float),
        cfg,
    )[:, 0, :]
    dots = np.clip(satellites @ center_point, -1.0, 1.0)
    center_distances = np.arccos(dots)

    uncertainty = conservative_space_radius_rad(box)
    uncertainty += satellite_angular_speed_bound_rad_s(cfg) * box.time_half_width_s

    guaranteed = int(np.count_nonzero(center_distances + uncertainty <= cfg.coverage_angle_rad))
    possible = int(
        np.count_nonzero(
            np.maximum(0.0, center_distances - uncertainty) <= cfg.coverage_angle_rad
        )
    )

    if guaranteed >= q:
        status = "covered"
    elif possible < q:
        status = "uncovered"
    else:
        status = "uncertain"

    return BoxClassification(
        status=status,
        guaranteed_count=guaranteed,
        possible_count=possible,
        uncertainty_rad=uncertainty,
        center_distances_rad=center_distances,
    )


def subdivide_space_time_box(
    box: SpaceTimeBox,
    *,
    config: q2.CoverageConfig | None = None,
) -> tuple[SpaceTimeBox, SpaceTimeBox]:
    """Bisect the dimension contributing the largest angular uncertainty."""

    box.validate()
    cfg = config or q2.CoverageConfig()
    lat_contribution = math.radians(box.lat_span_deg)
    lon_contribution = math.radians(box.lon_span_deg)
    time_contribution = (
        satellite_angular_speed_bound_rad_s(cfg)
        * (box.time_max_s - box.time_min_s)
    )
    dimension = int(np.argmax([lat_contribution, lon_contribution, time_contribution]))
    depth = box.depth + 1

    if dimension == 0:
        middle = 0.5 * (box.lat_min_deg + box.lat_max_deg)
        return (
            SpaceTimeBox(
                box.lat_min_deg,
                middle,
                box.lon_min_deg,
                box.lon_max_deg,
                box.time_min_s,
                box.time_max_s,
                depth,
            ),
            SpaceTimeBox(
                middle,
                box.lat_max_deg,
                box.lon_min_deg,
                box.lon_max_deg,
                box.time_min_s,
                box.time_max_s,
                depth,
            ),
        )
    if dimension == 1:
        middle = 0.5 * (box.lon_min_deg + box.lon_max_deg)
        return (
            SpaceTimeBox(
                box.lat_min_deg,
                box.lat_max_deg,
                box.lon_min_deg,
                middle,
                box.time_min_s,
                box.time_max_s,
                depth,
            ),
            SpaceTimeBox(
                box.lat_min_deg,
                box.lat_max_deg,
                middle,
                box.lon_max_deg,
                box.time_min_s,
                box.time_max_s,
                depth,
            ),
        )

    middle = 0.5 * (box.time_min_s + box.time_max_s)
    return (
        SpaceTimeBox(
            box.lat_min_deg,
            box.lat_max_deg,
            box.lon_min_deg,
            box.lon_max_deg,
            box.time_min_s,
            middle,
            depth,
        ),
        SpaceTimeBox(
            box.lat_min_deg,
            box.lat_max_deg,
            box.lon_min_deg,
            box.lon_max_deg,
            middle,
            box.time_max_s,
            depth,
        ),
    )


def certify_continuous_coverage(
    params: q2.ConstellationParams,
    region: fast.LatLonRegion,
    *,
    duration_s: float,
    q: int = 1,
    config: q2.CoverageConfig | None = None,
    spatial_tolerance_deg: float = 0.05,
    time_tolerance_s: float = 1.0,
    max_boxes: int = 200_000,
    max_depth: int = 60,
    keep_unresolved: int = 20,
) -> ContinuousCoverageCertificate:
    """Attempt a conservative continuous-coverage certificate."""

    if duration_s <= 0.0:
        raise ValueError("duration_s must be positive")
    if spatial_tolerance_deg <= 0.0 or time_tolerance_s <= 0.0:
        raise ValueError("tolerances must be positive")
    if max_boxes <= 0 or max_depth <= 0:
        raise ValueError("max_boxes and max_depth must be positive")

    cfg = config or q2.CoverageConfig()
    initial = SpaceTimeBox(
        region.lat_min_deg,
        region.lat_max_deg,
        region.lon_min_deg,
        region.lon_max_deg,
        0.0,
        duration_s,
        0,
    )
    queue: deque[SpaceTimeBox] = deque([initial])
    processed = covered = 0
    deepest = 0
    unresolved: list[SpaceTimeBox] = []

    while queue and processed < max_boxes:
        box = queue.popleft()
        processed += 1
        deepest = max(deepest, box.depth)
        classification = classify_space_time_box(params, box, q=q, config=cfg)

        if classification.status == "covered":
            covered += 1
            continue
        if classification.status == "uncovered":
            return ContinuousCoverageCertificate(
                status="uncovered",
                q=q,
                processed_boxes=processed,
                covered_boxes=covered,
                uncertain_boxes=len(queue),
                max_depth=deepest,
                failure_box=box,
                unresolved_boxes=tuple(unresolved),
                message="Found a space-time box that cannot achieve the required coverage fold.",
            )

        spatial_small = max(box.lat_span_deg, box.lon_span_deg) <= spatial_tolerance_deg
        time_small = (box.time_max_s - box.time_min_s) <= time_tolerance_s
        if (spatial_small and time_small) or box.depth >= max_depth:
            if len(unresolved) < keep_unresolved:
                unresolved.append(box)
            continue

        queue.extend(subdivide_space_time_box(box, config=cfg))

    if not queue and not unresolved:
        return ContinuousCoverageCertificate(
            status="covered",
            q=q,
            processed_boxes=processed,
            covered_boxes=covered,
            uncertain_boxes=0,
            max_depth=deepest,
            failure_box=None,
            unresolved_boxes=(),
            message="All generated space-time boxes were conservatively certified covered.",
        )

    remaining = len(queue) + len(unresolved)
    if queue and len(unresolved) < keep_unresolved:
        unresolved.extend(list(queue)[: keep_unresolved - len(unresolved)])
    return ContinuousCoverageCertificate(
        status="inconclusive",
        q=q,
        processed_boxes=processed,
        covered_boxes=covered,
        uncertain_boxes=remaining,
        max_depth=deepest,
        failure_box=None,
        unresolved_boxes=tuple(unresolved),
        message=(
            "The conservative verifier exhausted its box budget or reached the "
            "requested resolution with unresolved boundary boxes."
        ),
    )
