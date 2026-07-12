from __future__ import annotations

import csv
from pathlib import Path

import pytest


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_all_minimal_q2_csvs(root: Path) -> None:
    sensitivity = []
    monte_carlo = []
    for candidate, satellites, c1_base, c2_base in (
        ("single_S1302", 1302, 0.999, 0.72),
        ("double_S1480", 1480, 1.0, 0.965),
    ):
        for index, scenario in enumerate(("baseline", "altitude_525km", "altitude_575km", "radius_480km", "radius_530km")):
            sensitivity.append(
                {
                    "candidate": candidate,
                    "S": satellites,
                    "scenario": scenario,
                    "C1": c1_base - index * 0.0001,
                    "C2": c2_base - index * 0.002,
                }
            )
        for replicate in range(4):
            monte_carlo.append(
                {
                    "candidate": candidate,
                    "replicate": replicate,
                    "C1": c1_base - replicate * 0.0001,
                    "C2": c2_base - replicate * 0.001,
                }
            )
    _write_csv(root / "q2" / "sensitivity.csv", sensitivity)
    _write_csv(root / "q2" / "monte_carlo.csv", monte_carlo)


def _write_minimal_rows_for(question: str, root: Path) -> None:
    if question == "q3":
        sensitivity = [
            {"candidate": candidate, "scenario": scenario, "p30_all": value}
            for candidate, value in (("S1540", 0.84), ("S1680", 0.856), ("S1760", 0.861))
            for scenario in ("baseline", "processing_0ms", "processing_1ms", "isl_4500km", "isl_5500km")
        ]
        monte_carlo = [
            {"candidate": candidate, "replicate": replicate, "p30_all_bootstrap": value - 0.001 * replicate}
            for candidate, value in (("S1540", 0.84), ("S1680", 0.856), ("S1760", 0.861))
            for replicate in range(4)
        ]
    elif question == "q4":
        sensitivity = [
            {"candidate": candidate, "scenario": scenario, "annual_avoidances": scale * value}
            for candidate, scale in (("q2_single_S1302", 1.0), ("q2_double_S1480", 1.14), ("q3_saturation_S1680", 1.29))
            for scenario, value in (("baseline", 120.0), ("density_x0.5", 60.0), ("density_x2", 240.0))
        ]
        monte_carlo = [
            {"candidate": candidate, "replicate": replicate, "conjunctions": scale * (1800 + 20 * replicate), "avoidances": scale * (130 + 4 * replicate)}
            for candidate, scale in (("q2_single_S1302", 1.0), ("q2_double_S1480", 1.14), ("q3_saturation_S1680", 1.29))
            for replicate in range(4)
        ]
    else:
        raise AssertionError(f"unsupported question fixture: {question}")
    _write_csv(root / question / "sensitivity.csv", sensitivity)
    _write_csv(root / question / "monte_carlo.csv", monte_carlo)


def test_validation_runner_accepts_question_and_seed():
    from run_validation import parse_args

    args = parse_args(["--question", "q4", "--replicates", "10", "--seed", "2"])
    assert (args.question, args.replicates, args.seed) == ("q4", 10, 2)


def test_runner_writes_q4_outputs_in_quick_mode(tmp_path: Path):
    from run_validation import run_q4_validation

    summary = run_q4_validation(tmp_path, replicates=3, seed=7, quick=True)
    assert summary["question"] == "q4"
    assert (tmp_path / "q4" / "sensitivity.csv").is_file()
    assert (tmp_path / "q4" / "monte_carlo.csv").is_file()
    assert (tmp_path / "q4" / "summary.json").is_file()
    assert (tmp_path / "q4" / "sensitivity.png").is_file()


def test_runner_writes_q4_final_figure_in_quick_mode(tmp_path: Path):
    from run_validation import run_q4_validation

    run_q4_validation(tmp_path, replicates=3, seed=7, quick=True)
    assert (tmp_path / "figures" / "fig_q4_validation.png").is_file()


def test_standard_q3_validation_grid_matches_the_saturation_study():
    from q3_config import Q3Config
    from run_validation import _q3_mother_grid

    mother, fidelity = _q3_mother_grid(quick=False, config=Q3Config())
    assert (len(mother.times_s), len(mother.coverage_weights), len(mother.communication_ground_ecef_km)) == (289, 832, 30)
    assert len(fidelity.communication_point_indices) == 30


def test_final_figure_builder_writes_paper_resolution_q2_png(tmp_path: Path):
    from PIL import Image

    from final_figures import generate_final_figure

    _write_all_minimal_q2_csvs(tmp_path)
    path = generate_final_figure("q2", tmp_path)
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.width >= 1800 and image.height >= 1000
        assert image.info["dpi"] == pytest.approx((300, 300), abs=1)


def test_final_figure_builder_rejects_missing_required_q3_column(tmp_path: Path):
    from final_figures import generate_final_figure

    _write_csv(tmp_path / "q3" / "sensitivity.csv", [{"scenario": "baseline"}])
    _write_csv(tmp_path / "q3" / "monte_carlo.csv", [{"replicate": 0, "p30_all_bootstrap": 0.8}])
    with pytest.raises(ValueError, match="p30_all"):
        generate_final_figure("q3", tmp_path)


def test_final_figure_labels_abbreviate_long_scenarios_and_candidates():
    from final_figures import _candidate_label, _scenario_label

    assert _scenario_label("capacity_reduction_0.25") == "容损0.25"
    assert _candidate_label("q3_saturation_S1680") == "S1680"


@pytest.mark.parametrize("question", ["q3", "q4"])
def test_final_figure_builder_writes_q3_and_q4_pngs(tmp_path: Path, question: str):
    from final_figures import generate_final_figure

    _write_minimal_rows_for(question, tmp_path)
    path = generate_final_figure(question, tmp_path)
    assert path.name == f"fig_{question}_validation.png"
    assert path.is_file()
