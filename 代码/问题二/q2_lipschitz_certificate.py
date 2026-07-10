"""Q2-R05: Lipschitz-margin continuous coverage certificate.

A cheaper, single-pass replacement for the adaptive space-time box verifier
(``q2_adaptive_verify.py``).  See 18-问题二算法条件松弛与假设驱动加速方案.md §5.

The coverage margin is measured in ANGULAR (geodesic) units, not dot-product
units.  In dot-product space the coverage cap is very flat -- the largest
possible margin ``1 - cos(theta)`` is only ~0.003 for ``theta ~ 4.55 deg`` --
so a linear Lipschitz bound there is useless.  In angular space the margin
scale is ``theta`` itself and the geodesic distance is intrinsically
1-Lipschitz, which makes certification achievable::

    mu(x, t) = theta - gamma^(q)(x, t)

where ``gamma^(q)`` is the angular distance from ``x`` to the q-th nearest
satellite subpoint.  ``mu >= 0`` iff ``x`` is q-fold covered at time ``t``.

Because a spherical geodesic distance is 1-Lipschitz in arc length and moves no
faster than the subpoint, the analytic Lipschitz constants are::

    L_x = 1              # |d gamma / d(arc)| <= 1 (geodesic distance)
    L_t = n0 + omega_e   # |d gamma / dt| <= subpoint angular speed <= n0 + we

Certificate (sufficient condition for CONTINUOUS q-fold coverage):
if on a grid with spatial covering radius ``rho_x`` (rad) and time step
``Delta_t`` (s) every sampled margin satisfies ::

    mu(x_j, t_l) >= L_x * rho_x + L_t * (Delta_t / 2)   [radians]

then ``mu > 0`` for every continuous ``(x, t)`` in the region and time window.
This keeps the rigor of a continuous certificate at the cost of one grid pass
instead of adaptive box subdivision + CEGIS iterations.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

import q2_constellation as q2
from q2_coverage_margin import q_fold_margins_at_points

try:  # region type; optional to keep the module importable in isolation
    from q2_fast_coverage import LatLonRegion
except Exception:  # pragma: no cover
    LatLonRegion = None  # type: ignore


@dataclass(frozen=True)
class CertificateResult:
    """Outcome of a Lipschitz-margin continuous coverage certificate."""

    status: str  # 'covered' | 'uncovered' | 'inconclusive'
    q: int
    min_margin: float
    threshold: float
    spatial_covering_radius_rad: float
    time_half_step_s: float
    lipschitz_time_const: float
    worst_lat_deg: float
    worst_lon_deg: float
    worst_time_s: float
    num_points: int
    num_times: int


def time_lipschitz_constant(config: q2.CoverageConfig | None = None) -> float:
    """Analytic upper bound on ``|dm/dt|`` in dot-product units (per second)."""

    cfg = config or q2.CoverageConfig()
    return cfg.mean_motion_rad_s + cfg.earth_rotation_rad_s


def spatial_covering_radius_rad(grid_step_deg: float) -> float:
    """Half-diagonal covering radius of an equal-step lat-lon grid (radians).

    For latitude/longitude steps ``Delta`` (rad) the great-circle distance from
    any point to the nearest node is at most ``0.5 * sqrt(Delta^2 + Delta^2)``,
    because ``ds^2 = dphi^2 + cos^2(phi) dlambda^2 <= dphi^2 + dlambda^2``.
    """

    if grid_step_deg <= 0.0:
        raise ValueError("grid_step_deg must be positive")
    step = math.radians(grid_step_deg)
    return step / math.sqrt(2.0)


def certificate_threshold(
    grid_step_deg: float,
    time_step_s: float,
    config: q2.CoverageConfig | None = None,
    *,
    spatial_lipschitz: float = 1.0,
) -> float:
    """Lipschitz safety margin ``L_x * rho_x + L_t * Delta_t / 2``."""

    if time_step_s <= 0.0:
        raise ValueError("time_step_s must be positive")
    rho_x = spatial_covering_radius_rad(grid_step_deg)
    l_t = time_lipschitz_constant(config)
    return spatial_lipschitz * rho_x + l_t * (0.5 * time_step_s)


def classify_status(min_margin: float, threshold: float) -> str:
    """Three-way certificate decision from the worst sampled margin."""

    if min_margin < 0.0:
        return "uncovered"
    if min_margin >= threshold:
        return "covered"
    return "inconclusive"


def certify_continuous_coverage(
    params: q2.ConstellationParams,
    *,
    grid_step_deg: float,
    time_step_s: float,
    duration_s: float,
    q: int = 1,
    region=None,
    config: q2.CoverageConfig | None = None,
) -> CertificateResult:
    """Certify continuous q-fold coverage of ``region`` over ``[0, duration_s]``.

    Returns ``covered`` (rigorous certificate under the spherical circular-orbit
    model), ``uncovered`` (a sampled gap was found), or ``inconclusive`` (the
    grid is too coarse relative to the Lipschitz threshold; refine and retry).
    """

    cfg = config or q2.CoverageConfig()
    if LatLonRegion is not None and region is None:
        region = LatLonRegion()
    if region is None:
        raise ValueError("region is required (LatLonRegion unavailable)")

    lat, lon = q2.make_latlon_grid(
        region.lat_min_deg,
        region.lat_max_deg,
        region.lon_min_deg,
        region.lon_max_deg,
        grid_step_deg,
    )
    times = q2.make_time_grid(duration_s, time_step_s)
    ground = q2.ground_unit_vectors(lat, lon)
    sat_all = q2.satellite_unit_vectors(params, times, cfg)  # (S, L, 3)
    total_sats = sat_all.shape[0]

    threshold = certificate_threshold(grid_step_deg, time_step_s, cfg)
    rho_x = spatial_covering_radius_rad(grid_step_deg)
    l_t = time_lipschitz_constant(cfg)

    # More satellites than q are needed for q-fold coverage to be possible.
    if q > total_sats:
        return CertificateResult(
            status="uncovered", q=q, min_margin=-math.inf, threshold=threshold,
            spatial_covering_radius_rad=rho_x, time_half_step_s=0.5 * time_step_s,
            lipschitz_time_const=l_t, worst_lat_deg=float("nan"),
            worst_lon_deg=float("nan"), worst_time_s=float("nan"),
            num_points=len(lat), num_times=len(times),
        )

    global_min = math.inf
    worst_point = -1
    worst_time_idx = -1
    for time_index in range(len(times)):
        result = q_fold_margins_at_points(
            sat_all[:, time_index, :], ground, cfg.coverage_angle_rad, q=q
        )
        if result.min_margin < global_min:
            global_min = result.min_margin
            worst_point = result.worst_point_index
            worst_time_idx = time_index
            # Early exit: a strictly negative margin already proves 'uncovered'.
            if global_min < 0.0:
                break

    # Convert the worst dot-product margin to an ANGULAR margin (radians).
    # arccos is monotone, so argmin of the dot margin == argmin of the angular
    # margin; only the scalar value needs converting.
    cos_theta = math.cos(cfg.coverage_angle_rad)
    worst_dot = float(np.clip(global_min + cos_theta, -1.0, 1.0))
    min_margin_rad = cfg.coverage_angle_rad - math.acos(worst_dot)

    status = classify_status(min_margin_rad, threshold)
    return CertificateResult(
        status=status,
        q=q,
        min_margin=float(min_margin_rad),
        threshold=float(threshold),
        spatial_covering_radius_rad=float(rho_x),
        time_half_step_s=float(0.5 * time_step_s),
        lipschitz_time_const=float(l_t),
        worst_lat_deg=float(lat[worst_point]) if worst_point >= 0 else float("nan"),
        worst_lon_deg=float(lon[worst_point]) if worst_point >= 0 else float("nan"),
        worst_time_s=float(times[worst_time_idx]) if worst_time_idx >= 0 else float("nan"),
        num_points=len(lat),
        num_times=len(times),
    )
