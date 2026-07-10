"""CLI runner for Problem 4 parameterized smoke pipeline."""

from __future__ import annotations

import argparse

from q4_pipeline import run_smoke_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Problem 4 debris-robustness smoke pipeline.")
    parser.add_argument("--satellite-count", type=int, default=1000, help="Parameterized constellation size for smoke run; non-final.")
    parser.add_argument("--output-dir", default="results", help="Directory for CSV/TXT outputs.")
    parser.add_argument("--figure-dir", default="figures", help="Directory for figures.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_smoke_pipeline(
        output_dir=args.output_dir,
        figure_dir=args.figure_dir,
        satellite_count=args.satellite_count,
    )
    print("问题四 smoke run 完成（非最终数值结论）")
    print(f"scenario: {result['scenario']}")
    print(f"total_avoidances_per_year: {result['constellation']['total_avoidances_per_year']:.6g}")
    print(f"capacity_loss_ratio: {result['constellation']['capacity_loss_ratio']:.6g}")


if __name__ == "__main__":
    main()
