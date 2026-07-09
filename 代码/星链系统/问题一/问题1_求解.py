"""
Problem 1 numerical verification for the LEO constellation modeling task.

Outputs:
  - results/problem1_summary.csv
  - results/problem1_overlap_table.csv
  - results/problem1_results.txt
  - figures/Q1_N_vs_spacing.png
  - figures/Q1_N_vs_overlap_linear.png
  - figures/Q1_N_vs_overlap_area.png
  - figures/Q1_N_vs_bandwidth.png
  - figures/Q1_parameter_consistency.png

The implementation follows:
  - 03-问题一假设与覆盖几何推导.md
  - 04-问题一数值校验与曲线生成方案.md
"""

from __future__ import annotations

import csv
import math
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# -----------------------------
# Constants from the problem
# -----------------------------
R_EARTH_KM = 6371.0
ORBIT_ALTITUDE_KM = 550.0
ANTENNA_HALF_CONE_DEG = 40.46
GIVEN_GROUND_RADIUS_KM = 506.0
MU_EARTH_KM3_S2 = 398600.4418
OMEGA_EARTH_RAD_S = 7.2921159e-5

N_MIN = 30
N_MAX = 80
REPRESENTATIVE_N = 40
REPRESENTATIVE_INCLINATION_DEG = 50.0
TARGET_LAT_MIN_DEG = 30.0
TARGET_LAT_MAX_DEG = 50.0
SELECTED_SATELLITES = (1, 10, 20, 30, 40)
TRAJECTORY_SAMPLE_COUNT = 1200

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"


@dataclass(frozen=True)
class CoverageCase:
    """One coverage-parameter interpretation."""

    name: str
    theta_rad: float
    ground_radius_km: float
    area_km2: float
    n_min: int
    equivalent_alpha_deg: float | None = None

    @property
    def theta_deg(self) -> float:
        return math.degrees(self.theta_rad)


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def theta_from_antenna_half_cone(
    R_km: float, h_km: float, alpha_deg: float
) -> float:
    """Coverage Earth-center angle from nadir-pointing sensor half-cone angle."""

    alpha = math.radians(alpha_deg)
    rho = R_km + h_km
    value = (rho / R_km) * math.sin(alpha)
    if value > 1:
        raise ValueError("The half-cone angle exceeds the geometric horizon limit.")
    return math.asin(value) - alpha


def equivalent_alpha_from_theta(R_km: float, h_km: float, theta_rad: float) -> float:
    """Equivalent sensor half-cone angle corresponding to an Earth-center angle."""

    rho = R_km + h_km
    slant_range = math.sqrt(
        rho * rho + R_km * R_km - 2 * rho * R_km * math.cos(theta_rad)
    )
    cos_alpha = (rho - R_km * math.cos(theta_rad)) / slant_range
    cos_alpha = max(-1.0, min(1.0, cos_alpha))
    return math.degrees(math.acos(cos_alpha))


def orbit_mean_motion_rad_s(R_km: float = R_EARTH_KM, h_km: float = ORBIT_ALTITUDE_KM) -> float:
    """Circular-orbit mean motion."""

    semi_major_axis = R_km + h_km
    return math.sqrt(MU_EARTH_KM3_S2 / semi_major_axis**3)


def orbit_period_s(R_km: float = R_EARTH_KM, h_km: float = ORBIT_ALTITUDE_KM) -> float:
    """Circular-orbit period."""

    return 2 * math.pi / orbit_mean_motion_rad_s(R_km, h_km)


def wrap_longitude_deg(lon_deg: np.ndarray) -> np.ndarray:
    """Wrap longitudes to [-180, 180)."""

    return (lon_deg + 180.0) % 360.0 - 180.0


def break_longitude_jumps(lon_deg: np.ndarray, lat_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Insert NaN at dateline jumps so ground tracks are not connected across the map."""

    lon_out: list[float] = [float(lon_deg[0])]
    lat_out: list[float] = [float(lat_deg[0])]
    for idx in range(1, len(lon_deg)):
        if abs(float(lon_deg[idx]) - float(lon_deg[idx - 1])) > 180.0:
            lon_out.append(math.nan)
            lat_out.append(math.nan)
        lon_out.append(float(lon_deg[idx]))
        lat_out.append(float(lat_deg[idx]))
    return np.array(lon_out), np.array(lat_out)


def subsatellite_lat_lon_deg(
    t_s: np.ndarray,
    satellite_index: int,
    total_satellites: int,
    inclination_deg: float,
    include_earth_rotation: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Sub-satellite latitude and longitude for a circular inclined orbit.

    satellite_index is 1-based.
    """

    mean_motion = orbit_mean_motion_rad_s()
    inclination = math.radians(inclination_deg)
    phase = 2 * math.pi * (satellite_index - 1) / total_satellites
    u = mean_motion * t_s + phase

    lat_rad = np.arcsin(np.sin(inclination) * np.sin(u))
    lon_rad = np.arctan2(np.cos(inclination) * np.sin(u), np.cos(u))
    if include_earth_rotation:
        lon_rad = lon_rad - OMEGA_EARTH_RAD_S * t_s

    return np.degrees(lat_rad), wrap_longitude_deg(np.degrees(lon_rad))


def spherical_cap_area(R_km: float, theta_rad: float) -> float:
    return 2 * math.pi * R_km**2 * (1 - math.cos(theta_rad))


def make_coverage_cases() -> tuple[CoverageCase, CoverageCase]:
    """Create both parameter interpretations used for sensitivity checking."""

    theta_alpha = theta_from_antenna_half_cone(
        R_EARTH_KM, ORBIT_ALTITUDE_KM, ANTENNA_HALF_CONE_DEG
    )
    radius_alpha = R_EARTH_KM * theta_alpha
    area_alpha = spherical_cap_area(R_EARTH_KM, theta_alpha)

    theta_given = GIVEN_GROUND_RADIUS_KM / R_EARTH_KM
    area_given = spherical_cap_area(R_EARTH_KM, theta_given)
    alpha_equiv = equivalent_alpha_from_theta(
        R_EARTH_KM, ORBIT_ALTITUDE_KM, theta_given
    )

    case_given = CoverageCase(
        name="given_radius_506km",
        theta_rad=theta_given,
        ground_radius_km=GIVEN_GROUND_RADIUS_KM,
        area_km2=area_given,
        n_min=math.ceil(math.pi / theta_given),
        equivalent_alpha_deg=alpha_equiv,
    )
    case_alpha = CoverageCase(
        name="cone_angle_40.46deg",
        theta_rad=theta_alpha,
        ground_radius_km=radius_alpha,
        area_km2=area_alpha,
        n_min=math.ceil(math.pi / theta_alpha),
        equivalent_alpha_deg=ANTENNA_HALF_CONE_DEG,
    )
    return case_given, case_alpha


def spacing_angle_rad(N: int) -> float:
    return 2 * math.pi / N


def linear_overlap_ratio(N: int, theta_rad: float) -> float:
    delta = spacing_angle_rad(N)
    return max(0.0, 1.0 - delta / (2 * theta_rad))


def area_overlap_ratio_flat(N: int, theta_rad: float, R_km: float) -> float:
    """Flat-circle approximation for adjacent coverage-area overlap ratio."""

    delta = spacing_angle_rad(N)
    r = R_km * theta_rad
    d = R_km * delta
    if d >= 2 * r:
        return 0.0
    intersection = (
        2 * r**2 * math.acos(d / (2 * r))
        - 0.5 * d * math.sqrt(max(0.0, 4 * r**2 - d**2))
    )
    return intersection / (math.pi * r**2)


def luders_band_half_width_rad(N: int, theta_rad: float) -> float | None:
    """Lüders same-plane continuous-coverage-band half-width."""

    denominator = math.cos(math.pi / N)
    if denominator <= 0:
        return None
    value = math.cos(theta_rad) / denominator
    if value < -1.0 or value > 1.0:
        return None
    return math.acos(value)


def compute_rows(cases: Iterable[CoverageCase]) -> list[dict[str, float | int | str]]:
    case_list = list(cases)
    rows: list[dict[str, float | int | str]] = []
    for N in range(N_MIN, N_MAX + 1):
        delta = spacing_angle_rad(N)
        row: dict[str, float | int | str] = {
            "N": N,
            "spacing_deg": math.degrees(delta),
            "spacing_km": R_EARTH_KM * delta,
        }
        for case in case_list:
            prefix = case.name
            psi = luders_band_half_width_rad(N, case.theta_rad)
            row[f"{prefix}_linear_overlap"] = linear_overlap_ratio(N, case.theta_rad)
            row[f"{prefix}_area_overlap_flat"] = area_overlap_ratio_flat(
                N, case.theta_rad, R_EARTH_KM
            )
            row[f"{prefix}_band_half_width_deg"] = (
                "" if psi is None else math.degrees(psi)
            )
            row[f"{prefix}_is_continuous"] = int(psi is not None)
        rows.append(row)
    return rows


def save_summary(cases: Iterable[CoverageCase]) -> None:
    path = RESULTS_DIR / "problem1_summary.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case",
                "theta_deg",
                "theta_rad",
                "ground_radius_km",
                "coverage_area_km2",
                "n_min",
                "equivalent_alpha_deg",
            ],
        )
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "case": case.name,
                    "theta_deg": case.theta_deg,
                    "theta_rad": case.theta_rad,
                    "ground_radius_km": case.ground_radius_km,
                    "coverage_area_km2": case.area_km2,
                    "n_min": case.n_min,
                    "equivalent_alpha_deg": case.equivalent_alpha_deg,
                }
            )


def save_table(rows: list[dict[str, float | int | str]]) -> None:
    path = RESULTS_DIR / "problem1_overlap_table.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_text_report(cases: tuple[CoverageCase, CoverageCase]) -> None:
    given, alpha = cases
    radius_diff_pct = (
        (given.ground_radius_km - alpha.ground_radius_km) / alpha.ground_radius_km * 100
    )
    area_diff_pct = (given.area_km2 - alpha.area_km2) / alpha.area_km2 * 100

    text = f"""Problem 1 numerical verification report

Constants
---------
Earth radius R = {R_EARTH_KM:.3f} km
Orbit altitude h = {ORBIT_ALTITUDE_KM:.3f} km
Antenna half-cone angle alpha = {ANTENNA_HALF_CONE_DEG:.3f} deg
Given ground coverage radius = {GIVEN_GROUND_RADIUS_KM:.3f} km

Parameter interpretations
-------------------------
1) Given-radius interpretation:
   theta = {given.theta_deg:.6f} deg
   ground radius = {given.ground_radius_km:.6f} km
   coverage area = {given.area_km2:.6f} km^2
   equivalent alpha = {given.equivalent_alpha_deg:.6f} deg
   same-plane along-track N_min = {given.n_min}

2) Half-cone-angle interpretation:
   theta = {alpha.theta_deg:.6f} deg
   ground radius = {alpha.ground_radius_km:.6f} km
   coverage area = {alpha.area_km2:.6f} km^2
   alpha = {ANTENNA_HALF_CONE_DEG:.6f} deg
   same-plane along-track N_min = {alpha.n_min}

Consistency difference
----------------------
Radius difference = {radius_diff_pct:.3f} %
Area difference = {area_diff_pct:.3f} %

Conclusion
----------
Use the given 506 km ground-radius interpretation as the main numerical baseline.
The same-plane along-track continuous coverage threshold is N = 40 under the main
baseline. The half-cone-angle interpretation is reported only for parameter
consistency; it is not used as a second main result in the figures.

Representative sub-satellite track settings
-------------------------------------------
Inclination i = {REPRESENTATIVE_INCLINATION_DEG:.3f} deg
Representative satellites per plane N = {REPRESENTATIVE_N}
Orbit period T = {orbit_period_s() / 60:.3f} min
Target latitude band = {TARGET_LAT_MIN_DEG:.1f} deg N to {TARGET_LAT_MAX_DEG:.1f} deg N
"""
    (RESULTS_DIR / "problem1_results.txt").write_text(text, encoding="utf-8")


def set_plot_style() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": [
                "Microsoft YaHei",
                "SimHei",
                "SimSun",
                "KaiTi",
                "DejaVu Sans",
                "Arial",
            ],
            "axes.unicode_minus": False,
            "font.size": 10,
            "axes.linewidth": 1.2,
            "xtick.major.width": 1.2,
            "ytick.major.width": 1.2,
            "lines.linewidth": 2.2,
            "figure.dpi": 120,
        }
    )


def save_figure(fig: plt.Figure, filename: str) -> None:
    fig.savefig(FIGURES_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_spacing(rows: list[dict[str, float | int | str]]) -> None:
    N = [int(r["N"]) for r in rows]
    spacing_km = [float(r["spacing_km"]) for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.plot(N, spacing_km, color="#1f77b4")
    ax.axhline(
        2 * GIVEN_GROUND_RADIUS_KM,
        color="#d62728",
        linestyle="--",
        label="2×506 km 覆盖直径",
    )
    ax.axvline(40, color="#2ca02c", linestyle="--", label="$N=40$ 基准")
    ax.set_xlabel("单轨道面卫星数 $N$")
    ax.set_ylabel("相邻星下点弧长 / km")
    ax.set_title("卫星数与相邻星下点间距关系")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(frameon=False)
    save_figure(fig, "Q1_N_vs_spacing.png")


def plot_overlap(rows: list[dict[str, float | int | str]], metric: str, filename: str, ylabel: str) -> None:
    N = [int(r["N"]) for r in rows]
    y_given = [float(r[f"given_radius_506km_{metric}"]) for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.plot(N, y_given, color="#1f77b4", label="题给覆盖半径 506 km")
    ax.axvline(40, color="#2ca02c", linestyle=":", label="$N=40$ 基准")
    ax.set_xlabel("单轨道面卫星数 $N$")
    ax.set_ylabel(ylabel)
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(f"{ylabel}随卫星数变化")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(frameon=False)
    save_figure(fig, filename)


def plot_bandwidth(rows: list[dict[str, float | int | str]]) -> None:
    N = [int(r["N"]) for r in rows]

    def to_float_or_nan(value: float | int | str) -> float:
        return math.nan if value == "" else float(value)

    y_given = [
        to_float_or_nan(r["given_radius_506km_band_half_width_deg"]) for r in rows
    ]

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.plot(N, y_given, color="#1f77b4", label="题给覆盖半径 506 km")
    ax.axvline(40, color="#2ca02c", linestyle=":", label="$N=40$ 基准")
    ax.set_xlabel("单轨道面卫星数 $N$")
    ax.set_ylabel("覆盖带半宽 $\\psi$ / (°)")
    ax.set_title("Lüders 覆盖带半宽随卫星数变化")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(frameon=False)
    save_figure(fig, "Q1_N_vs_bandwidth.png")


def plot_parameter_consistency(cases: tuple[CoverageCase, CoverageCase]) -> None:
    given, alpha = cases

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.8))

    labels = ["题给半径口径", "半锥角口径"]
    colors = ["#1f77b4", "#ff7f0e"]

    ax1.bar(labels, [given.ground_radius_km, alpha.ground_radius_km], color=colors)
    ax1.set_ylabel("地面覆盖半径 / km")
    ax1.set_title("覆盖半径口径对比")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    ax2.bar(labels, [given.n_min, alpha.n_min], color=colors)
    ax2.set_ylabel("单轨沿轨连续下界 $N_{\\min}$")
    ax2.set_title("最少卫星数阈值对比")
    ax2.grid(axis="y", linestyle="--", alpha=0.4)

    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.tight_layout()
    save_figure(fig, "Q1_parameter_consistency.png")


def plot_subsatellite_latitude_time() -> None:
    """Plot representative satellite subpoint latitude versus time."""

    period = orbit_period_s()
    time_s = np.linspace(0.0, period, TRAJECTORY_SAMPLE_COUNT)
    time_min = time_s / 60.0

    fig, ax = plt.subplots(figsize=(8.0, 5.4))
    ax.axhspan(
        TARGET_LAT_MIN_DEG,
        TARGET_LAT_MAX_DEG,
        color="#b3d9ff",
        alpha=0.35,
        label="目标纬度带 $30^{\\circ}$N–$50^{\\circ}$N",
    )
    for sat_idx in SELECTED_SATELLITES:
        lat_deg, _ = subsatellite_lat_lon_deg(
            time_s,
            satellite_index=sat_idx,
            total_satellites=REPRESENTATIVE_N,
            inclination_deg=REPRESENTATIVE_INCLINATION_DEG,
            include_earth_rotation=True,
        )
        ax.plot(time_min, lat_deg, label=f"第 {sat_idx} 颗卫星")

    ax.axhline(TARGET_LAT_MIN_DEG, color="#1f77b4", linestyle="--", linewidth=1.2)
    ax.axhline(TARGET_LAT_MAX_DEG, color="#1f77b4", linestyle="--", linewidth=1.2)
    ax.axhline(REPRESENTATIVE_INCLINATION_DEG, color="#d62728", linestyle=":", linewidth=1.2, label="$+i$")
    ax.axhline(-REPRESENTATIVE_INCLINATION_DEG, color="#d62728", linestyle=":", linewidth=1.2, label="$-i$")
    ax.set_xlabel("时间 / min")
    ax.set_ylabel("星下点纬度 / (°)")
    ax.set_title(
        f"星下点纬度随时间变化（$i={REPRESENTATIVE_INCLINATION_DEG:.0f}^{{\\circ}}$, "
        f"$N={REPRESENTATIVE_N}$）"
    )
    ax.set_ylim(-60, 60)
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(frameon=False, fontsize=9, loc="center left", bbox_to_anchor=(1.02, 0.5))
    save_figure(fig, "Q1_subsatellite_latitude_time.png")


def plot_ground_track_rotation_comparison() -> None:
    """Compare ground tracks with and without Earth rotation."""

    period = orbit_period_s()
    time_s = np.linspace(0.0, 2 * period, TRAJECTORY_SAMPLE_COUNT)

    lat_no_rot, lon_no_rot = subsatellite_lat_lon_deg(
        time_s,
        satellite_index=1,
        total_satellites=REPRESENTATIVE_N,
        inclination_deg=REPRESENTATIVE_INCLINATION_DEG,
        include_earth_rotation=False,
    )
    lat_rot, lon_rot = subsatellite_lat_lon_deg(
        time_s,
        satellite_index=1,
        total_satellites=REPRESENTATIVE_N,
        inclination_deg=REPRESENTATIVE_INCLINATION_DEG,
        include_earth_rotation=True,
    )

    lon_no_rot_plot, lat_no_rot_plot = break_longitude_jumps(lon_no_rot, lat_no_rot)
    lon_rot_plot, lat_rot_plot = break_longitude_jumps(lon_rot, lat_rot)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.9), sharey=True)

    panels = [
        (ax1, lon_no_rot_plot, lat_no_rot_plot, "不考虑地球自转"),
        (ax2, lon_rot_plot, lat_rot_plot, "考虑地球自转"),
    ]
    for ax, lon_plot, lat_plot, title in panels:
        ax.axhspan(TARGET_LAT_MIN_DEG, TARGET_LAT_MAX_DEG, color="#b3d9ff", alpha=0.35)
        ax.plot(lon_plot, lat_plot, color="#1f77b4", linewidth=2.0)
        ax.axhline(TARGET_LAT_MIN_DEG, color="#1f77b4", linestyle="--", linewidth=1.0)
        ax.axhline(TARGET_LAT_MAX_DEG, color="#1f77b4", linestyle="--", linewidth=1.0)
        ax.set_xlim(-180, 180)
        ax.set_ylim(-60, 60)
        ax.set_xlabel("经度 / (°)")
        ax.set_title(title)
        ax.grid(True, linestyle="--", alpha=0.4)
    ax1.set_ylabel("纬度 / (°)")
    fig.suptitle(
        f"星下点经纬度轨迹对比（第 1 颗卫星，$0\\sim2T$，$i={REPRESENTATIVE_INCLINATION_DEG:.0f}^{{\\circ}}$）",
        y=1.02,
    )
    fig.tight_layout()
    save_figure(fig, "Q1_ground_track_rotation_comparison.png")


def plot_all(rows: list[dict[str, float | int | str]], cases: tuple[CoverageCase, CoverageCase]) -> None:
    set_plot_style()
    plot_spacing(rows)
    plot_overlap(
        rows,
        metric="linear_overlap",
        filename="Q1_N_vs_overlap_linear.png",
        ylabel="一维沿轨重叠率",
    )
    plot_overlap(
        rows,
        metric="area_overlap_flat",
        filename="Q1_N_vs_overlap_area.png",
        ylabel="平面近似面积重叠率",
    )
    plot_bandwidth(rows)
    plot_parameter_consistency(cases)
    plot_subsatellite_latitude_time()
    plot_ground_track_rotation_comparison()


def print_key_results(cases: tuple[CoverageCase, CoverageCase]) -> None:
    given, alpha = cases
    print("Problem 1 numerical verification")
    print("=" * 40)
    print(f"Main baseline: given ground radius = {given.ground_radius_km:.3f} km")
    print(f"  theta = {given.theta_deg:.6f} deg")
    print(f"  area = {given.area_km2:.3f} km^2")
    print(f"  equivalent alpha = {given.equivalent_alpha_deg:.6f} deg")
    print(f"  N_min = {given.n_min}")
    print()
    print(f"Sensitivity baseline: alpha = {ANTENNA_HALF_CONE_DEG:.3f} deg")
    print(f"  theta = {alpha.theta_deg:.6f} deg")
    print(f"  radius = {alpha.ground_radius_km:.3f} km")
    print(f"  area = {alpha.area_km2:.3f} km^2")
    print(f"  N_min = {alpha.n_min}")
    print()
    print(f"Representative orbit period = {orbit_period_s() / 60:.3f} min")
    print(f"Representative trajectory inclination = {REPRESENTATIVE_INCLINATION_DEG:.1f} deg")
    print()
    print(f"Results saved to: {RESULTS_DIR}")
    print(f"Figures saved to: {FIGURES_DIR}")


def main() -> None:
    ensure_dirs()
    cases = make_coverage_cases()
    rows = compute_rows(cases)

    save_summary(cases)
    save_table(rows)
    save_text_report(cases)
    plot_all(rows, cases)
    print_key_results(cases)


if __name__ == "__main__":
    main()
