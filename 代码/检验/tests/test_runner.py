from __future__ import annotations

from pathlib import Path


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
