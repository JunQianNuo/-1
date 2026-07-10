"""Problem 4 smoke pipeline for parameterized debris-robustness calculations.

The default scenario is deliberately labeled non-final: it validates the
algorithm chain before Problem 2 final constellation and coverage matrices are
available.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from q4_avoidance import avoidance_decision
from q4_capacity_cost import (
    annual_expected_failures,
    avoidance_cost_wanyuan,
    capacity_loss_ratio,
    replacement_unit_cost_wanyuan,
)
from q4_collision import collision_probability_2d_gaussian
from q4_config import AvoidanceParameters, CostParameters, DebrisEnvironment, MissionParameters
from q4_debris import (
    annual_probability,
    collision_cross_section_km2,
    conjunction_event_rate_per_year,
    flux_collision_rate_per_s,
    split_catalog_density,
)
from q4_redundancy import coverage_availability, ground_backup_confidence, space_backup_confidence


def run_smoke_pipeline(
    *,
    output_dir: str | Path = "results",
    figure_dir: str | Path = "figures",
    satellite_count: int = 1000,
) -> dict:
    """Run a deterministic non-final scenario and write tables/figures."""

    output_path = Path(output_dir)
    figure_path = Path(figure_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    figure_path.mkdir(parents=True, exist_ok=True)

    env = DebrisEnvironment()
    avoid = AvoidanceParameters()
    cost = CostParameters()
    mission = MissionParameters(satellite_count=satellite_count)

    catalog_density, uncatalog_density = split_catalog_density(
        env.total_density_gt_1cm_km3,
        env.catalog_threshold_cm,
        env.beta,
    )
    cross_section = collision_cross_section_km2(env.satellite_radius_km, env.debris_diameter_cm)
    uncat_rate = flux_collision_rate_per_s(cross_section, env.relative_speed_km_s, uncatalog_density)
    annual_uncat_prob = annual_probability(uncat_rate, env.year_s)
    conjunction_rate = conjunction_event_rate_per_year(
        env.screening_radius_km,
        env.relative_speed_km_s,
        catalog_density,
        env.year_s,
    )

    miss_distances = np.linspace(0.0, 2.0, 81)
    covariance = np.diag([0.05**2, 0.08**2])
    hard_body_radius = env.satellite_radius_km + 0.5 * env.debris_diameter_cm * 1e-5
    pc_samples = np.array(
        [
            collision_probability_2d_gaussian(
                np.array([miss, 0.0]),
                covariance,
                hard_body_radius,
                radial_steps=80,
                angular_steps=96,
            )
            for miss in miss_distances
        ],
        dtype=float,
    )

    thresholds = np.array([1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4], dtype=float)
    sensitivity_rows = []
    chosen_row = None
    for threshold in thresholds:
        decisions = [
            avoidance_decision(
                collision_probability=float(pc),
                threshold=float(threshold),
                current_miss_km=float(miss),
                target_miss_km=avoid.target_miss_km,
                sensitivity_km_per_mps=avoid.miss_distance_sensitivity_km_per_mps,
                max_delta_v_mps=avoid.max_delta_v_mps,
                post_maneuver_probability=avoid.safe_probability,
            )
            for pc, miss in zip(pc_samples, miss_distances)
        ]
        p_trig = float(np.mean([d.triggered for d in decisions]))
        p_feas = float(np.mean([d.feasible for d in decisions if d.triggered])) if any(d.triggered for d in decisions) else 0.0
        expected_avoidances_per_sat = conjunction_rate * p_trig * p_feas
        total_avoidances = satellite_count * expected_avoidances_per_sat
        residual_cat_events_per_year = conjunction_rate * float(np.mean([d.residual_probability for d in decisions]))
        row = {
            "threshold": float(threshold),
            "p_trigger": p_trig,
            "p_feasible_given_trigger": p_feas,
            "avoidances_per_satellite_year": expected_avoidances_per_sat,
            "total_avoidances_per_year": total_avoidances,
            "residual_catalog_events_per_satellite_year": residual_cat_events_per_year,
        }
        sensitivity_rows.append(row)
        if np.isclose(threshold, avoid.threshold):
            chosen_row = row
    if chosen_row is None:
        chosen_row = sensitivity_rows[2]

    total_avoidances = chosen_row["total_avoidances_per_year"]
    cap_loss = capacity_loss_ratio(
        total_avoidances=total_avoidances,
        satellite_count=satellite_count,
        maneuver_duration_s=avoid.maneuver_duration_s,
        year_s=env.year_s,
        capacity_reduction=avoid.capacity_reduction,
    )
    avoid_cost = avoidance_cost_wanyuan(total_avoidances, cost.avoidance_cost_wanyuan)
    residual_cat_rate_per_s = chosen_row["residual_catalog_events_per_satellite_year"] / env.year_s
    failure_rate = uncat_rate + residual_cat_rate_per_s + mission.intrinsic_failure_rate_per_s
    failures = annual_expected_failures(satellite_count, failure_rate, env.year_s)
    unit_replace = replacement_unit_cost_wanyuan(
        cost.satellite_cost_wanyuan,
        cost.launch_cost_wanyuan,
        cost.satellites_per_launch,
    )
    replace_cost = failures * unit_replace

    unit_reliability_life = float(np.exp(-failure_rate * env.year_s * mission.design_life_years))
    ground_conf = ground_backup_confidence(satellite_count, ground_spares=10, unit_reliability=unit_reliability_life)
    space_conf = space_backup_confidence(satellite_count, planes=20, space_spares=20, unit_reliability=unit_reliability_life)
    synthetic_counts = np.array([[1, 2, 1], [1, 1, 1], [0, 1, 1], [2, 2, 1]])
    synthetic_availability = coverage_availability(synthetic_counts)

    result = {
        "scenario": "smoke_parameterized_non_final",
        "single_satellite": {
            "catalog_density_km3": catalog_density,
            "uncatalog_density_km3": uncatalog_density,
            "uncatalog_collision_rate_per_s": uncat_rate,
            "uncatalog_collision_probability_per_year": annual_uncat_prob,
            "catalog_conjunction_events_per_year": conjunction_rate,
        },
        "constellation": {
            "satellite_count": satellite_count,
            "total_avoidances_per_year": total_avoidances,
            "capacity_loss_ratio": cap_loss,
            "avoidance_cost_wanyuan_per_year": avoid_cost,
            "expected_failures_per_year": failures,
            "replacement_cost_wanyuan_per_year": replace_cost,
        },
        "redundancy": {
            "unit_reliability_life": unit_reliability_life,
            "ground_confidence_10_spares": ground_conf,
            "space_confidence_20_spares_20_planes": space_conf,
            "synthetic_coverage_availability": synthetic_availability,
        },
    }

    _write_summary_csv(output_path / "q4_summary.csv", result)
    _write_sensitivity_csv(output_path / "q4_threshold_sensitivity.csv", sensitivity_rows)
    _write_report(output_path / "q4_run_report.txt", result)
    _plot_threshold_sensitivity(figure_path / "q4_threshold_sensitivity.png", sensitivity_rows)
    return result


def _write_summary_csv(path: Path, result: dict) -> None:
    rows = []
    for section, values in result.items():
        if isinstance(values, dict):
            for key, value in values.items():
                rows.append({"section": section, "metric": key, "value": value})
        else:
            rows.append({"section": "meta", "metric": section, "value": values})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["section", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)


def _write_sensitivity_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_report(path: Path, result: dict) -> None:
    lines = [
        "问题四参数化 smoke run（非最终数值结论）",
        "=" * 48,
        "本输出仅验证算法链路；最终数值需等待问题二最终构型、覆盖矩阵和问题三容量口径。",
        "",
    ]
    for section, values in result.items():
        lines.append(f"[{section}]")
        if isinstance(values, dict):
            for key, value in values.items():
                lines.append(f"{key}: {value}")
        else:
            lines.append(str(values))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _plot_threshold_sensitivity(path: Path, rows: list[dict]) -> None:
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False
    thresholds = [r["threshold"] for r in rows]
    avoidances = [r["total_avoidances_per_year"] for r in rows]
    p_trig = [r["p_trigger"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    ax.plot(thresholds, avoidances, marker="o", linewidth=2, label="年度避撞次数期望")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _pos: f"{x:.0e}"))
    ax.set_xlabel("避撞阈值 P_th")
    ax.set_ylabel("全星座年度避撞次数期望（smoke）")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax2 = ax.twinx()
    ax2.plot(thresholds, p_trig, marker="s", linestyle="--", color="tab:orange", label="触发比例")
    ax2.set_ylabel("触发比例")
    handles, labels = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles + handles2, labels + labels2, loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
