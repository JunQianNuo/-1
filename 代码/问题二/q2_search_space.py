"""Fair Walker-Delta search-space generation for Problem 2.

This module fixes the enumeration-order bias in the original candidate
generator.  Every discrete Walker structure ``(M, N, F)`` receives its own
continuous-parameter sampling budget.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Iterator

import numpy as np

import q2_constellation as q2

try:  # SciPy is preferred but the module remains usable without it.
    from scipy.stats import qmc
except ImportError:  # pragma: no cover - exercised only in minimal environments.
    qmc = None


@dataclass(frozen=True, order=True)
class WalkerStructure:
    """Discrete Walker-Delta structure with ``M*N`` satellites."""

    planes: int
    sats_per_plane: int
    phase_factor: int

    @property
    def total_satellites(self) -> int:
        return self.planes * self.sats_per_plane

    def validate(self) -> None:
        if self.planes <= 0:
            raise ValueError("planes must be positive")
        if self.sats_per_plane <= 0:
            raise ValueError("sats_per_plane must be positive")
        if not 0 <= self.phase_factor < self.planes:
            raise ValueError("phase_factor must lie in [0, planes)")


def minimum_reachable_inclination_deg(
    *,
    region_lat_max_deg: float = 53.0,
    coverage_angle_rad: float,
) -> float:
    """Necessary inclination lower bound from latitude reachability."""

    if not 0.0 <= coverage_angle_rad <= math.pi:
        raise ValueError("coverage_angle_rad must lie in [0, pi]")
    return max(0.0, region_lat_max_deg - math.degrees(coverage_angle_rad))


def walker_structures(total_satellites: int) -> list[WalkerStructure]:
    """Return all discrete ``(M,N,F)`` structures for a fixed total.

    Ordered factor pairs are retained because ``(M,N)`` and ``(N,M)`` describe
    different Walker layouts.
    """

    if total_satellites <= 0:
        raise ValueError("total_satellites must be positive")

    structures: list[WalkerStructure] = []
    for planes, sats_per_plane in q2.factor_pairs(total_satellites):
        for phase_factor in range(planes):
            structures.append(
                WalkerStructure(
                    planes=planes,
                    sats_per_plane=sats_per_plane,
                    phase_factor=phase_factor,
                )
            )
    return structures


def phase_widths_deg(structure: WalkerStructure) -> tuple[float, float]:
    """Return Walker symmetry fundamental widths for ``Omega0`` and ``u0``."""

    structure.validate()
    return 360.0 / structure.planes, 360.0 / structure.sats_per_plane


def wrap_continuous_params(
    structure: WalkerStructure,
    inclination_deg: float,
    raan0_deg: float,
    u0_deg: float,
    *,
    inclination_min_deg: float,
    inclination_max_deg: float,
) -> q2.ConstellationParams:
    """Clip inclination and wrap periodic phase variables."""

    structure.validate()
    if inclination_max_deg < inclination_min_deg:
        raise ValueError("inclination_max_deg must be >= inclination_min_deg")

    omega_width, u_width = phase_widths_deg(structure)
    inclination = float(np.clip(inclination_deg, inclination_min_deg, inclination_max_deg))
    raan0 = float(raan0_deg % omega_width)
    u0 = float(u0_deg % u_width)
    return q2.ConstellationParams(
        planes=structure.planes,
        sats_per_plane=structure.sats_per_plane,
        phase_factor=structure.phase_factor,
        inclination_deg=inclination,
        raan0_deg=raan0,
        u0_deg=u0,
    )


def _unit_cube_samples(
    n_samples: int,
    *,
    seed: int | None,
    scramble: bool,
) -> np.ndarray:
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")

    if qmc is not None:
        sampler = qmc.Sobol(d=3, scramble=scramble, seed=seed)
        # random_base2 preserves the Sobol balance property when possible.
        exponent = int(math.ceil(math.log2(n_samples)))
        return sampler.random_base2(exponent)[:n_samples]

    rng = np.random.default_rng(seed)
    # Deterministic fallback.  It is not a Sobol sequence, but preserves equal
    # per-structure budgets instead of silently reverting to biased enumeration.
    return rng.random((n_samples, 3))


def sobol_continuous_params(
    structure: WalkerStructure,
    n_samples: int,
    *,
    inclination_min_deg: float,
    inclination_max_deg: float = 90.0,
    seed: int | None = None,
    scramble: bool = True,
) -> list[q2.ConstellationParams]:
    """Generate low-discrepancy samples for ``(i, Omega0, u0)``."""

    structure.validate()
    if inclination_max_deg < inclination_min_deg:
        raise ValueError("inclination_max_deg must be >= inclination_min_deg")

    unit = _unit_cube_samples(n_samples, seed=seed, scramble=scramble)
    omega_width, u_width = phase_widths_deg(structure)

    params: list[q2.ConstellationParams] = []
    for z_i, z_omega, z_u in unit:
        params.append(
            q2.ConstellationParams(
                planes=structure.planes,
                sats_per_plane=structure.sats_per_plane,
                phase_factor=structure.phase_factor,
                inclination_deg=float(
                    inclination_min_deg
                    + z_i * (inclination_max_deg - inclination_min_deg)
                ),
                raan0_deg=float(z_omega * omega_width),
                u0_deg=float(z_u * u_width),
            )
        )
    return params


def fair_candidate_params_for_total(
    total_satellites: int,
    *,
    samples_per_structure: int,
    inclination_min_deg: float,
    inclination_max_deg: float = 90.0,
    seed: int | None = None,
) -> Iterator[q2.ConstellationParams]:
    """Yield exactly ``samples_per_structure`` candidates for every structure."""

    structures = walker_structures(total_satellites)
    seed_sequence = np.random.SeedSequence(seed)
    child_seeds = seed_sequence.spawn(len(structures))

    for structure, child_seed in zip(structures, child_seeds):
        structure_seed = int(child_seed.generate_state(1, dtype=np.uint32)[0])
        yield from sobol_continuous_params(
            structure,
            samples_per_structure,
            inclination_min_deg=inclination_min_deg,
            inclination_max_deg=inclination_max_deg,
            seed=structure_seed,
        )


def group_params_by_structure(
    params: Iterable[q2.ConstellationParams],
) -> dict[WalkerStructure, list[q2.ConstellationParams]]:
    """Utility used by tests and audit reports."""

    grouped: dict[WalkerStructure, list[q2.ConstellationParams]] = {}
    for item in params:
        structure = WalkerStructure(
            item.planes,
            item.sats_per_plane,
            item.phase_factor,
        )
        grouped.setdefault(structure, []).append(item)
    return grouped
