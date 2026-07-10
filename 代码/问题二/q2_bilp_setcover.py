"""Q2 BILP set-cover: minimum-satellite regional coverage via 0-1 programming.

Alternative to Walker enumeration, following Jeon 2025 (APC+BILP) and Deng 2021
(over-deploy then remove redundant) reduced to a coverage set-cover:

    min   sum_c x_c
    s.t.  sum_c A[d, c] x_c >= q   for every space-time demand d
          x_c in {0, 1}

where each candidate c is one satellite slot (RAAN, u0) at fixed inclination and
altitude, and demand d = (region grid point j, time t_l).  Selecting a subset of
the candidate pool yields a (possibly asymmetric) constellation, not restricted
to the Walker M x N lattice.

Deliverables:
- LP relaxation optimum  -> a fractional lower bound (fast, HiGHS linprog);
- greedy set-cover        -> a feasible integer upper bound;
- optional exact ILP      -> scipy.optimize.milp (HiGHS), time-limited.

Bound caveat: the LP value bounds the *discrete, pool-restricted* problem.  As a
bound on the true continuous minimum it is only approximate (relies on the
demand discretization being a relaxation and the pool being dense).
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import scipy.sparse as sp

import q2_constellation as q2


@dataclass(frozen=True)
class SetCoverResult:
    q: int
    num_candidates: int
    num_demands: int
    lp_lower_bound: float
    greedy_upper_bound: int
    greedy_selection: np.ndarray  # indices of chosen candidates
    ilp_optimum: int | None = None
    ilp_selection: np.ndarray | None = None
    ilp_status: str | None = None


def candidate_pool_subpoints(
    inclination_deg: float,
    n_raan: int,
    n_phase: int,
    times_s: np.ndarray,
    config: q2.CoverageConfig | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Propagate a pool of single-satellite slots (RAAN, u0) over ``times_s``.

    Returns ``(subpoints, params)`` where ``subpoints`` has shape
    ``(C, L, 3)`` (unit ECEF vectors) and ``params`` has shape ``(C, 2)`` giving
    each candidate's (RAAN_deg, u0_deg).
    """

    cfg = config or q2.CoverageConfig()
    if n_raan <= 0 or n_phase <= 0:
        raise ValueError("n_raan and n_phase must be positive")
    times = np.asarray(times_s, dtype=float)
    inc = math.radians(inclination_deg)
    cos_i, sin_i = math.cos(inc), math.sin(inc)
    n0 = cfg.mean_motion_rad_s
    we = cfg.earth_rotation_rad_s

    raan_grid = np.deg2rad(np.linspace(0.0, 360.0, n_raan, endpoint=False))
    phase_grid = np.deg2rad(np.linspace(0.0, 360.0, n_phase, endpoint=False))
    RA, PH = np.meshgrid(raan_grid, phase_grid, indexing="ij")
    raan = RA.ravel()          # (C,)
    u0 = PH.ravel()
    C = raan.size

    earth = we * times                       # (L,)
    cos_e, sin_e = np.cos(earth), np.sin(earth)
    u = u0[:, None] + n0 * times[None, :]     # (C, L)
    x_orb, y_orb = np.cos(u), np.sin(u)       # (C, L)
    # R1(i)
    x_inc = x_orb
    y_inc = y_orb * cos_i
    z_inc = y_orb * sin_i
    # R3(raan)
    co, so = np.cos(raan)[:, None], np.sin(raan)[:, None]
    x_i = co * x_inc - so * y_inc
    y_i = so * x_inc + co * y_inc
    z_i = z_inc
    # R3(-we t)
    x_e = cos_e[None, :] * x_i + sin_e[None, :] * y_i
    y_e = -sin_e[None, :] * x_i + cos_e[None, :] * y_i
    subpoints = np.stack([x_e, y_e, z_i], axis=-1)   # (C, L, 3)
    params = np.column_stack([np.rad2deg(raan), np.rad2deg(u0)])
    return subpoints, params


def build_coverage_matrix(
    subpoints: np.ndarray,
    ground_points: np.ndarray,
    coverage_radius_rad: float,
    *,
    dedup_demands: bool = True,
) -> tuple[sp.csr_matrix, np.ndarray]:
    """Build the demand x candidate boolean coverage matrix (sparse CSR).

    ``subpoints`` (C, L, 3); ``ground_points`` (K, 3).  A demand is a (point,
    time) pair; row index = j*L + l.  Optionally deduplicate identical rows
    (demands with the same covering-candidate set), returning a multiplicity
    weight per unique row.
    """

    C, L, _ = subpoints.shape
    ground = ground_points / np.linalg.norm(ground_points, axis=1, keepdims=True)
    K = ground.shape[0]
    cos_theta = math.cos(coverage_radius_rad)

    rows = []  # csr per time-block
    for l in range(L):
        dots = ground @ subpoints[:, l, :].T        # (K, C)
        rows.append(sp.csr_matrix(dots >= cos_theta))
    # stack so demand index = l*K + j  (time-major); order does not matter
    A = sp.vstack(rows, format="csr")               # (K*L, C) bool-ish
    A = A.astype(np.int8)

    if not dedup_demands:
        return A, np.ones(A.shape[0], dtype=np.int64)

    # Deduplicate identical rows via hashing their nonzero column patterns.
    A = A.tocsr()
    keys = {}
    keep = []
    weights = []
    indptr, indices = A.indptr, A.indices
    for r in range(A.shape[0]):
        cols = indices[indptr[r]:indptr[r + 1]]
        key = cols.tobytes()
        if key in keys:
            weights[keys[key]] += 1
        else:
            keys[key] = len(keep)
            keep.append(r)
            weights.append(1)
    A_ded = A[keep]
    return A_ded.tocsr(), np.asarray(weights, dtype=np.int64)


def setcover_lp_lower_bound(A: sp.csr_matrix, q: int = 1) -> float:
    """LP relaxation optimum of the set cover (a lower bound on the ILP)."""

    from scipy.optimize import linprog

    D, C = A.shape
    # minimize 1^T x  s.t.  A x >= q,  0 <= x <= 1   ==>   -A x <= -q
    res = linprog(
        c=np.ones(C),
        A_ub=(-A).tocsr(),
        b_ub=-q * np.ones(D),
        bounds=[(0.0, 1.0)] * C,
        method="highs",
    )
    if not res.success:
        raise RuntimeError(f"LP relaxation failed: {res.message}")
    return float(res.fun)


def greedy_setcover(A: sp.csr_matrix, q: int = 1, weights: np.ndarray | None = None) -> np.ndarray:
    """Greedy q-cover: repeatedly pick the candidate covering the most
    still-deficient demands.  Returns chosen candidate indices."""

    A = A.tocsc().astype(np.int32)
    D, C = A.shape
    need = np.full(D, q, dtype=np.int32)          # remaining cover needed per demand
    w = np.ones(D) if weights is None else weights.astype(float)
    chosen = []
    available = np.ones(C, dtype=bool)
    At = A.tocsr()
    while np.any(need > 0):
        deficient = need > 0
        # gain of each candidate = weighted number of still-deficient demands it covers
        gain = (A.T @ (deficient.astype(np.int32) * 1))  # (C,)
        gain = np.asarray(gain).ravel().astype(float)
        gain[~available] = -1.0
        c = int(np.argmax(gain))
        if gain[c] <= 0:
            raise RuntimeError("greedy stalled: demands not coverable by pool")
        chosen.append(c)
        available[c] = False
        covered = A[:, c].toarray().ravel() > 0
        need[covered] -= 1
    return np.asarray(sorted(chosen), dtype=np.int64)


def setcover_ilp(A: sp.csr_matrix, q: int = 1, *, time_limit_s: float = 60.0):
    """Exact 0-1 ILP via scipy.optimize.milp (HiGHS), time-limited.

    Returns (optimum, selection, status)."""

    from scipy.optimize import milp, LinearConstraint, Bounds

    D, C = A.shape
    constraints = LinearConstraint(A.tocsr(), lb=q * np.ones(D), ub=np.inf)
    integrality = np.ones(C)
    bounds = Bounds(lb=np.zeros(C), ub=np.ones(C))
    res = milp(
        c=np.ones(C),
        constraints=constraints,
        integrality=integrality,
        bounds=bounds,
        options={"time_limit": time_limit_s},
    )
    if res.x is None:
        return None, None, res.message
    sel = np.where(res.x > 0.5)[0].astype(np.int64)
    return int(round(res.fun)), sel, res.message


def rgt_altitude_km(revs_per_sidereal_day: int, config: q2.CoverageConfig | None = None) -> float:
    """Altitude of the repeat-ground-track orbit with N_P revs per sidereal day."""
    cfg = config or q2.CoverageConfig()
    T_orb = q2.SIDEREAL_DAY_S / revs_per_sidereal_day
    a = (cfg.mu_km3_s2 * (T_orb / (2.0 * math.pi)) ** 2) ** (1.0 / 3.0)
    return a - cfg.earth_radius_km


def cgt_candidate_subpoints(
    inclination_deg: float,
    altitude_km: float,
    n_slots: int,
    config: q2.CoverageConfig | None = None,
) -> np.ndarray:
    """Common-ground-track candidate pool: L time-shifted copies of one seed.

    On a repeat-ground-track orbit the ground track repeats exactly over one
    sidereal day (= ``n_slots`` slots).  A CGT satellite at temporal offset ``s``
    has, in ECEF, the subpoint the seed reaches ``s`` slots later.  Hence the
    candidate pool is the set of circular shifts of the seed's ECEF trajectory,
    giving a *circulant* coverage structure and a tiny (L-variable) ILP.
    """
    cfg = config or q2.CoverageConfig()
    base = q2.CoverageConfig(
        earth_radius_km=cfg.earth_radius_km, altitude_km=altitude_km,
        mu_km3_s2=cfg.mu_km3_s2, earth_rotation_rad_s=cfg.earth_rotation_rad_s,
        ground_coverage_radius_km=cfg.ground_coverage_radius_km,
    )
    times = q2.make_time_grid(q2.SIDEREAL_DAY_S, q2.SIDEREAL_DAY_S / n_slots)[:n_slots]
    seed = q2.ConstellationParams(planes=1, sats_per_plane=1, phase_factor=0,
                                  inclination_deg=inclination_deg, raan0_deg=0.0, u0_deg=0.0)
    seed_sub = q2.satellite_unit_vectors(seed, times, base)[0]     # (L, 3)
    L = seed_sub.shape[0]
    # candidate s at slot tau = seed at (tau + s) mod L
    cand = np.empty((L, L, 3), dtype=float)
    for s in range(L):
        cand[s] = np.roll(seed_sub, -s, axis=0)
    return cand


def solve_q2_cgt_bilp(
    *,
    inclination_deg: float = 50.0,
    revs_per_sidereal_day: int = 15,
    n_slots: int = 288,
    grid_step_deg: float = 4.0,
    q: int = 1,
    config: q2.CoverageConfig | None = None,
    milp_time_limit_s: float = 120.0,
) -> dict:
    """CGT + BILP: min ground-track satellites for continuous q-coverage (exact ILP)."""
    cfg = config or q2.CoverageConfig()
    h_rgt = rgt_altitude_km(revs_per_sidereal_day, cfg)
    cand = cgt_candidate_subpoints(inclination_deg, h_rgt, n_slots, cfg)
    lat, lon = q2.make_latlon_grid(step_deg=grid_step_deg)
    ground = q2.ground_unit_vectors(lat, lon)
    A, _w = build_coverage_matrix(cand, ground, cfg.coverage_angle_rad)
    # Feasibility precheck: a region point the single ground track NEVER covers
    # makes the BILP infeasible (a wide region has permanent inter-pass gaps).
    row_cover = np.asarray(A.sum(axis=1)).ravel()
    n_uncoverable = int((row_cover == 0).sum())
    if n_uncoverable > 0:
        return {
            "rgt_altitude_km": h_rgt, "n_slots": n_slots, "num_demands": int(A.shape[0]),
            "feasible": False, "uncoverable_demands": n_uncoverable,
            "reason": "single ground track leaves region points never covered "
                      "(inter-pass longitude gaps); CGT suits localized targets, "
                      "not wide 2-D regions",
            "lp_lower_bound": None, "greedy": None, "ilp_optimum": None,
            "ilp_status": "infeasible", "ilp_selection": None,
        }
    lp = setcover_lp_lower_bound(A, q=q)
    greedy = greedy_setcover(A, q=q)
    opt, sel, status = setcover_ilp(A, q=q, time_limit_s=milp_time_limit_s)
    return {
        "rgt_altitude_km": h_rgt, "n_slots": n_slots, "num_demands": int(A.shape[0]),
        "feasible": True, "lp_lower_bound": lp, "greedy": int(greedy.size),
        "ilp_optimum": opt, "ilp_status": status, "ilp_selection": sel,
    }


def solve_q2_setcover(
    *,
    inclination_deg: float = 50.0,
    n_raan: int = 45,
    n_phase: int = 45,
    grid_step_deg: float = 4.0,
    time_step_s: float = 900.0,
    duration_s: float | None = None,
    q: int = 1,
    config: q2.CoverageConfig | None = None,
    run_ilp: bool = False,
    ilp_time_limit_s: float = 60.0,
) -> SetCoverResult:
    """End-to-end BILP set-cover for the China region (coarse demonstration)."""

    cfg = config or q2.CoverageConfig()
    duration = duration_s if duration_s is not None else q2.SIDEREAL_DAY_S
    times = q2.make_time_grid(duration, time_step_s)
    lat, lon = q2.make_latlon_grid(step_deg=grid_step_deg)
    ground = q2.ground_unit_vectors(lat, lon)

    subpoints, _params = candidate_pool_subpoints(inclination_deg, n_raan, n_phase, times, cfg)
    A, weights = build_coverage_matrix(subpoints, ground, cfg.coverage_angle_rad)

    lp_lb = setcover_lp_lower_bound(A, q=q)
    greedy_sel = greedy_setcover(A, q=q, weights=weights)

    ilp_opt = ilp_sel = ilp_status = None
    if run_ilp:
        ilp_opt, ilp_sel, ilp_status = setcover_ilp(A, q=q, time_limit_s=ilp_time_limit_s)

    return SetCoverResult(
        q=q,
        num_candidates=subpoints.shape[0],
        num_demands=int(A.shape[0]),
        lp_lower_bound=lp_lb,
        greedy_upper_bound=int(greedy_sel.size),
        greedy_selection=greedy_sel,
        ilp_optimum=ilp_opt,
        ilp_selection=ilp_sel,
        ilp_status=ilp_status,
    )
